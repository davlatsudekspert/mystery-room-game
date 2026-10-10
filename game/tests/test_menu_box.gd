extends TestBase
## The main-menu gear box: its rules (MenuBoxLogic), its state machine (idle -> knob -> aligned -> open -> closed),
## the start transition (the loading flow starts exactly once, a tap skips, reduce_motion is a short fade) and the
## tap path from the screen to a knob.

var _events: Array[String] = []


func _record(logic: MenuBoxLogic) -> void:
	_events.clear()
	logic.event.connect(func(ev: StringName, arg: int) -> void: _events.append("%s:%d" % [ev, arg]))


func _count(prefix: String) -> int:
	var n := 0
	for e in _events:
		if e.begins_with(prefix):
			n += 1
	return n


# ------------------------------------------------------------------ rules
func test_every_scramble_is_solved_by_its_presses_and_not_before() -> void:
	for si in MenuBoxLogic.SCRAMBLES.size():
		var l := MenuBoxLogic.new()
		l.scramble(si)
		check(not l.is_aligned(), "scramble %d starts unsolved" % si)
		var p: Array = MenuBoxLogic.SCRAMBLES[si]
		var total := int(p[0]) + int(p[1]) + int(p[2])
		eq(l.distance(), total, "scramble %d needs exactly its presses" % si)
		check(total >= 2 and total <= 4, "scramble %d is 2-4 taps" % si)
		var done := 0
		for k in 3:
			for n in int(p[k]):
				l.press(k)
				done += 1
				if done < total:
					check(not l.is_aligned() or l.phase == MenuBoxLogic.Phase.CLOSED, "scramble %d: not solved after %d of %d presses" % [si, done, total])
		eq(l.phase, MenuBoxLogic.Phase.OPENING, "scramble %d opens after the last press" % si)


func test_press_turns_its_wheel_forward_and_neighbours_back() -> void:
	var l := MenuBoxLogic.new()
	l.wheels = [2, 2, 2]
	l.press(1)
	eq(l.wheels, [1, 3, 1], "the middle knob: wheel 1 forward, its two neighbours back")
	l.press(0)
	eq(l.wheels, [2, 2, 1], "the left knob: wheel 0 forward, wheel 1 back, wheel 2 untouched")
	eq(MenuBoxLogic.dir(2, 0), 0, "the right knob does not reach wheel 0")


func test_every_state_is_solvable() -> void:
	var worst := 0
	for a in 6:
		for b in 6:
			for c in 6:
				var d := MenuBoxLogic.distance_of([a, b, c])
				worst = maxi(worst, d)
				check(d < 99, "state %d%d%d has a solution" % [a, b, c])
	check(worst <= 15, "at most 15 presses from anywhere (got %d)" % worst)


func test_idle_fidget_never_solves_the_box_and_keeps_it_near() -> void:
	var l := MenuBoxLogic.new()
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	for i in 200:
		var k := l.pick_idle_knob(rng.randf())
		if k < 0:
			l.scramble()
			continue
		l.press(k)
		check(l.phase == MenuBoxLogic.Phase.CLOSED, "a fidget never opens the box")
		check(l.distance() <= 6, "a fidget keeps it within 6 presses")


# ------------------------------------------------------------------ state machine
func test_idle_knob_aligned_open_closed() -> void:
	var l := MenuBoxLogic.new()
	l.scramble(0) # presses [1, 0, 1]
	_record(l)
	eq(l.phase, MenuBoxLogic.Phase.CLOSED, "idle")
	check(l.can_press(), "knobs take presses when idle")
	check(l.press(0), "first knob")
	has(_events, "press:0")
	check(not _events.has("aligned:1"), "one press is not enough")
	eq(l.phase, MenuBoxLogic.Phase.CLOSED, "still idle")
	check(l.press(2), "second knob")
	has(_events, "aligned:2")
	eq(l.phase, MenuBoxLogic.Phase.OPENING, "all three pointers at the front: the latch releases")
	check(not l.can_press(), "no presses while the lid moves")
	check(not l.press(1), "a press during the opening is ignored")
	l.tick(MenuBoxLogic.OPEN_S + 0.01)
	eq(l.phase, MenuBoxLogic.Phase.OPEN, "open")
	has(_events, "open:0")
	l.tick(MenuBoxLogic.HOLD_S + 0.01)
	eq(l.phase, MenuBoxLogic.Phase.CLOSING, "closes by itself after a few seconds")
	l.tick(MenuBoxLogic.CLOSE_S + 0.01)
	eq(l.phase, MenuBoxLogic.Phase.CLOSED, "closed")
	has(_events, "closed:0")
	check(not l.is_aligned(), "scrambled again, ready to be played")
	# a tap closes an open lid early
	l.scramble(0)
	l.press(0)
	l.press(2)
	l.tick(MenuBoxLogic.OPEN_S + 0.01)
	check(l.tap_anywhere(), "a tap while open")
	eq(l.phase, MenuBoxLogic.Phase.CLOSING, "closing on a tap")
	check(not l.tap_anywhere(), "a tap while closing does nothing")


# ------------------------------------------------------------------ start transition
func test_start_hands_over_exactly_once_in_time() -> void:
	var l := MenuBoxLogic.new()
	_record(l)
	l.begin_start(false)
	check(l.is_starting(), "starting")
	eq(_count("goto"), 0, "no hand-over yet")
	var t := 0.0
	while t < MenuBoxLogic.START_END_T + 0.2:
		l.tick(1.0 / 60.0)
		t += 1.0 / 60.0
	eq(_count("goto"), 1, "the loading flow starts once")
	eq(_count("land"), 3, "three wheels click into place")
	eq(_count("latch"), 1, "the latch releases once")
	eq(_count("start_done"), 1, "done once")
	var order := ",".join(_events)
	check(order.find("land:0") < order.find("land:1") and order.find("land:1") < order.find("land:2")
			and order.find("land:2") < order.find("latch:1") and order.find("latch:1") < order.find("goto:0"), "order: click click click, latch, hand-over (%s)" % order)
	check(MenuBoxLogic.START_END_T >= 1.6 and MenuBoxLogic.START_END_T <= 2.0, "about 1.6-2.0 s in total")
	check(l.is_aligned(), "the wheels ended on the front mark")
	check(l.fade() > 0.99, "the frame is black at the end")
	l.begin_start(false)
	l.skip()
	eq(_count("goto"), 1, "a second start or a late skip never hands over twice")


func test_skip_hands_over_at_once_and_only_once() -> void:
	var l := MenuBoxLogic.new()
	_record(l)
	l.begin_start(false)
	for i in 12:
		l.tick(1.0 / 60.0)
	eq(_count("goto"), 0, "0.2 s in: not yet")
	check(l.tap_anywhere(), "a tap during the transition skips it")
	eq(_count("goto"), 1, "the hand-over happens now")
	l.skip()
	l.tap_anywhere()
	for i in 200:
		l.tick(1.0 / 60.0)
	eq(_count("goto"), 1, "and never again")
	eq(_count("land"), 0, "no clicks behind the fade after a skip")
	check(l.fade() >= 0.99, "black within the skip time")


func test_reduce_motion_is_a_fade_only() -> void:
	var l := MenuBoxLogic.new()
	_record(l)
	l.begin_start(true)
	eq(_count("goto"), 1, "the hand-over is immediate")
	for i in 300:
		l.tick(1.0 / 60.0)
	eq(_count("goto"), 1, "still once")
	eq(_count("land"), 0, "no wheels")
	eq(_count("latch"), 0, "no latch")
	eq(l.fade(), 0.0, "the loading flow's own fade does the work")


# ------------------------------------------------------------------ scene
func _tree() -> SceneTree:
	return Engine.get_main_loop() as SceneTree


## The test runner is still adding its own children when the first test starts: add deferred, then wait a frame.
func _add(n: Node) -> void:
	_tree().root.add_child.call_deferred(n)
	await _tree().process_frame


func test_box_renders_the_state_machine() -> void:
	var box := MenuBox.new()
	await _add(box)
	box.setup(0, 1)
	check(box.model != null, "the model loads")
	box.logic.scramble(0)
	box.touch(0)
	box.advance(0.05)
	check(float(box.get("_knob_rest").size()) == 3.0, "three knobs found")
	var knob_pos: Vector3 = (box.get("_knobs") as Array)[0].position
	var rest_pos: Vector3 = (box.get("_knob_rest") as Array)[0]
	check(knob_pos.z < rest_pos.z - 0.0005, "the knob pushed in")
	box.advance(0.6)
	var knob_back: Vector3 = (box.get("_knobs") as Array)[0].position
	check(knob_back.distance_to(rest_pos) < 0.0001, "and came back")
	check(box.get("_light") == null, "no light while closed")
	box.touch(2)
	eq(box.logic.phase, MenuBoxLogic.Phase.OPENING, "aligned: opening")
	box.advance(MenuBoxLogic.OPEN_S * 0.5)
	box.advance(MenuBoxLogic.OPEN_S * 0.6)
	eq(box.logic.phase, MenuBoxLogic.Phase.OPEN, "open")
	check(box.get("_light") != null, "the light exists while the lid is open")
	check((box.get("_light") as OmniLight3D).shadow_enabled == false, "and casts no shadow")
	check(absf(float(box.get("_lid_deg")) - MenuBox.LID_OPEN_DEG) < 0.5, "the lid is open about 70 degrees")
	box.tap_anywhere()
	box.advance(MenuBoxLogic.CLOSE_S + 0.05)
	eq(box.logic.phase, MenuBoxLogic.Phase.CLOSED, "closed again")
	check(float(box.get("_lid_deg")) < 0.01, "the lid is shut")
	box.advance(0.1)
	check(box.get("_light") == null, "the light is gone with the lid")
	box.queue_free()
	await _tree().process_frame


func test_idle_life_runs_by_itself_but_not_with_reduce_motion() -> void:
	var box := MenuBox.new()
	await _add(box)
	box.setup(0, 3)
	var pressed: Array[int] = [0]
	box.logic.event.connect(func(ev: StringName, _a: int) -> void:
		if ev == &"press":
			pressed[0] += 1)
	for i in 60 * 30: # thirty seconds
		box.advance(1.0 / 60.0)
	check(pressed[0] >= 2 and pressed[0] <= 5, "a fidget every 7-12 s (got %d in 30 s)" % pressed[0])
	eq(box.logic.phase, MenuBoxLogic.Phase.CLOSED, "the fidgets never open it")
	var still := MenuBox.new()
	await _add(still)
	still.setup(0, 3)
	var n2: Array[int] = [0]
	still.logic.event.connect(func(ev: StringName, _a: int) -> void:
		if ev == &"press":
			n2[0] += 1)
	for i in 60 * 30:
		still.advance(1.0 / 60.0, true)
	eq(n2[0], 0, "reduce_motion: no fidgets")
	box.queue_free()
	still.queue_free()
	await _tree().process_frame


func test_menu_start_calls_goto_once_and_skip_works() -> void:
	var calls: Array = []
	var menu := _menu(calls)
	await _add(menu)
	await _tree().process_frame
	var bg: MenuBackground = menu.get("_bg")
	bg.manual = true
	menu.call("_play", "ch1")
	check(bool(menu.get("_starting")), "starting")
	check(calls.is_empty(), "the loading flow has not started yet")
	check(CrashGuard.stage() == "menu", "the stage mark is still 'menu'")
	for i in int(MenuBoxLogic.START_END_T * 60.0) + 30:
		bg.advance(1.0 / 60.0)
	eq(calls.size(), 1, "goto ran exactly once")
	eq(calls[0][0], Chapters.get_chapter("ch1")["scene"], "with the chapter scene")
	eq(calls[0][1], 0.45, "and the normal fade")
	menu.queue_free()
	await _tree().process_frame
	# skip
	calls.clear()
	var menu2 := _menu(calls)
	await _add(menu2)
	await _tree().process_frame
	var bg2: MenuBackground = menu2.get("_bg")
	bg2.manual = true
	menu2.call("_play", "ch1")
	for i in 20:
		bg2.advance(1.0 / 60.0)
	eq(calls.size(), 0, "a third of a second in: not yet")
	menu2.call("_on_shield_input", _click())
	eq(calls.size(), 1, "a tap skips straight to the loading flow")
	menu2.call("_on_shield_input", _click())
	for i in 200:
		bg2.advance(1.0 / 60.0)
	eq(calls.size(), 1, "and goto never runs twice")
	menu2.call("_play", "ch1")
	eq(calls.size(), 1, "not even by a second Play")
	menu2.queue_free()
	await _tree().process_frame


func test_menu_start_with_reduce_motion_is_a_short_fade() -> void:
	var calls: Array = []
	var before: Variant = Settings.values.get("reduce_motion", false)
	Settings.values["reduce_motion"] = true
	var menu := _menu(calls)
	await _add(menu)
	await _tree().process_frame
	menu.call("_play", "ch1")
	eq(calls.size(), 1, "goto runs at once")
	eq(calls[0][1], 0.3, "with a short fade")
	menu.queue_free()
	await _tree().process_frame
	Settings.values["reduce_motion"] = before


func test_a_tap_on_a_knob_presses_it_and_a_tap_elsewhere_does_not() -> void:
	var calls: Array = []
	var menu := _menu(calls)
	await _add(menu)
	await _tree().process_frame
	var bg: MenuBackground = menu.get("_bg")
	bg.manual = true
	bg.advance(0.01)
	var cam: Camera3D = bg.get_viewport().get_camera_3d()
	check(cam != null, "the backdrop has a camera")
	var knobs: Array = bg.box.get("_knobs")
	var p := cam.unproject_position((knobs[1] as Node3D).global_position)
	check(bg.tap(p), "a tap on the middle knob presses it")
	eq(bg.box.logic.presses, 1, "one press counted")
	var wheel := cam.unproject_position((bg.box.get("_gears") as Array)[2].global_position)
	check(bg.tap(wheel), "a tap on a wheel presses its knob")
	eq(bg.box.logic.presses, 2, "two presses")
	check(not bg.tap(Vector2(2, 2)), "a tap in the corner does nothing")
	eq(bg.box.logic.presses, 2, "still two")
	menu.queue_free()
	await _tree().process_frame


func _menu(calls: Array) -> Control:
	var menu := (load("res://src/ui/main_menu.tscn") as PackedScene).instantiate() as Control
	menu.set("goto_fn", func(path: String, fade: float) -> void: calls.append([path, fade]))
	return menu


func _click() -> InputEventMouseButton:
	var e := InputEventMouseButton.new()
	e.button_index = MOUSE_BUTTON_LEFT
	e.pressed = true
	return e
