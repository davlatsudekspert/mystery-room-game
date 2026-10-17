extends Node
## Chaos player: plays a chapter like a messy real player (taps anything, with the wrong item in hand, hammers
## controls, opens hints and the bag, jumps between views, presses Back) and checks that the game never lets the
## player get stuck. The playthrough scripts only play the correct path; this one plays the wrong ones.
## Run: tools/chaos_run.sh --chapter=ch1 --seed=1 [--steps=400]   (adds the log check; prints the one summary line)
##  or: tools/qa_run.sh --log=<file> -- res://qa/chaos.tscn -- --chapter=ch2 --seed=3 --steps=400 [--out=<dir>]
##        --chapter=ch1|ch2|ch3|ch4  --seed=N (the run's dice and the game's puzzle variant)  --steps=N (default 400)
##        [--out=<dir>] (writes chaos_report.txt and a screenshot at the first violation)
##        [--warm=N] (solver steps played before the room opens; default by seed: a fresh game, 40 %, 75 % of the chapter)
##        [--size=WxH] (window size, default 640x360: the 1920x1080 canvas is scaled, so the layout is the same; 0x0 keeps the project's)
##        [--trace] (one line per tap: view, part, item, whether the room got it)
##        [--only=walkback|continue] (stress runs: every step jumps to a random view, maybe takes an item or taps, then presses Back until
##        the pause menu opens; or taps and then quits and Continues from the save)
##        [--to-finale] (the nudges go on up to the finale question, which the chaos then answers: the run ends with the chapter)
##        [--nudge=P] (chance per step that the solver makes 1–3 real moves, default 0.10, so the chaos reaches
##        later puzzles; it stops before the last two puzzles, so the chapter is never completed by it)
## Every action goes through the same paths as a finger: taps and drags are real touch events (TouchInput → the
## room's tap handling), HUD buttons are tapped at their centres, Back is the room's handle_back(). Only the view
## jumps (cam.go) and the solver's nudges are direct calls. The same seed draws the same dice, but what is in view
## depends on frame timing, so a run is not bit-identical: a violation's message and screenshot (--out) say where it was.
## Checks after every step (each violation is logged with chapter, seed, step, view, part and item in hand):
##   - input is never stuck: with no overlay open and nothing animating, the HUD is not busy and room touch is on;
##   - an item in hand never blocks: a tap on a reachable object where the item has no use sends it back to the bag;
##   - Back always does something, and from any view it leads out to the pause menu;
##   - a tap under an overlay never reaches the room;
##   - no soft-lock: logic.hint_goal() is never empty before the chapter is complete;
##   - the bag and the HUD agree with the logic (no duplicates, the prompt follows the item in hand);
##   - at the end, from the chaos state, the chapter's logic solver (tests/*_solver.gd) can still finish the chapter.
## Output: lines `VIOLATION …`, then `CHAOS_RESULT …` (tools/chaos_run.sh turns it into the summary line and adds the
## script errors it finds in the log) and `QA_DONE exit=N` (0 = no violation).

const SCENES := {"ch1": "res://src/rooms/lab7/lab7.tscn", "ch2": "res://src/rooms/archive/archive.tscn",
	"ch3": "res://src/rooms/underground/underground.tscn", "ch4": "res://src/rooms/array_hall/array_hall.tscn"}
## The finale answers each chapter's solver ends with (one is drawn per run).
const ENDINGS := {"ch1": ["take_lens", "leave_lens"], "ch2": ["leyla_key", "strand_key"], "ch3": ["leyla", "strand"],
	"ch4": ["take_lens", "leave_lens"]}
## The share of the solver's steps played before the room opens, by seed: 1 fresh game, 2 about 40 %, 3 about 75 %, then again.
const WARM := [0.0, 0.4, 0.75]
const BUSY_LIMIT := 60.0 # seconds: a cinematic or a camera move that lasts longer is a stuck input
const TAP_SETTLE := 0.3
## Overlay buttons the chaos player never presses (they leave the room).
const DENY_BUTTONS: Array[String] = ["ui.main_menu", "ui.settings"]

var chapter := "ch1"
var seed_n := 1
var steps := 400
var out_dir := ""
var warm_arg := -1
var nudge := 0.10
var only := "" # --only=walkback: every step jumps to a random view, maybe takes an item or taps, then walks Back out (a stress run)
var to_finale := false # --to-finale: the nudges go on to the finale question (the chaos then answers it)
var rng := RandomNumberGenerator.new()
var room: Node3D
var logic: RoomLogic
var cam: RoomCamera
var hud: Node
var touch: TouchInput
var ending := ""
var warm := 0
var step_n := 0
var steps_done := 0
var taps := 0
var held_taps := 0 # taps made with an item in hand
var delivered_taps := 0 # taps the room's TouchInput received (the others hit the HUD or a locked input)
var trace := false # --trace: one line per tap
var win_w := 640 # --size=WxH: the window (a small one renders much faster under software Vulkan; the canvas and layout are the same)
var win_h := 360
var violations := 0
var actions: Dictionary = {} # action name -> how often
var report: Array[String] = []
var _active: Dictionary = {} # state-type violation kinds currently failing (each episode counts once)
var _ctx_part := ""
var _ctx_item := ""
var _delivered := false # the room's TouchInput got the last tap
var _stop := false
var _shot_taken := false
var _overlay_steps := 0
var _back_log: Array[String] = [] # the last Back presses (UI signature before -> after), for a violation's message


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--chapter="):
			chapter = a.substr(10)
		elif a.begins_with("--seed="):
			seed_n = int(a.substr(7))
		elif a.begins_with("--steps="):
			steps = int(a.substr(8))
		elif a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--warm="):
			warm_arg = int(a.substr(7))
		elif a.begins_with("--nudge="):
			nudge = float(a.substr(8))
		elif a.begins_with("--size="):
			var wh := a.substr(7).split("x")
			win_w = int(wh[0])
			win_h = int(wh[1])
		elif a.begins_with("--only="):
			only = a.substr(7)
		elif a == "--to-finale":
			to_finale = true
		elif a == "--trace":
			trace = true
	_run.call_deferred()


func _log(line: String) -> void:
	report.append(line)
	print(line)


# ====================================================================== run
func _run() -> void:
	if not SCENES.has(chapter):
		print("chaos: unknown chapter %s (ch1, ch2, ch3 or ch4)" % chapter)
		print("QA_DONE exit=2")
		get_tree().quit(2)
		return
	if out_dir != "":
		DirAccess.make_dir_recursive_absolute(out_dir)
	if win_w > 0:
		get_window().size = Vector2i(win_w, win_h)
	_start_game()
	await _open_room()
	_log("chaos %s seed %d: %d steps, warm start %d solver steps, finale %s, bag %s" % [chapter, seed_n, steps, warm,
		ending, str(logic.inventory)])
	for i in steps:
		step_n = i + 1
		if _stop or logic.is_complete():
			break
		if not await _wait_idle():
			break
		await _chaos_step()
		_state_checks()
		steps_done += 1
		if steps_done % 10 == 0: # progress: tools/qa_run.sh kills a run whose log stops growing
			print("chaos %s seed %d: step %d of %d, %d taps, %d violations, view %s" % [chapter, seed_n, steps_done, steps,
				taps, violations, cam.current()])
	await _finish()


## A new game with this seed's puzzle variant and profile (lens and key choices), played on by the solver for the warm start.
func _start_game() -> void:
	rng.seed = seed_n
	GameState.variant_seed = seed_n # a fixed variant per seed (0 = the canonical answers)
	var lens := "take_lens" if rng.randi() % 2 == 0 else "leave_lens"
	var key := "strand_key" if rng.randi() % 2 == 0 else "leyla_key"
	var secret := seed_n % 3 == 0 # Chapter 3's 42nd-socket secret
	ending = ENDINGS[chapter][rng.randi() % 2]
	# one save file per process: runs in parallel must not load each other's
	SaveSystem.save_path = "user://qa_chaos_save_%d.json" % OS.get_process_id()
	SaveSystem.profile_path = "user://qa_chaos_profile_%d.json" % OS.get_process_id()
	GameState.profile = {"choices": {"ch1_lens": lens, "ch1_shards": 5 if secret else 2, "ch2_key": key,
		"ch2_echoes": 3 if secret else 1,
		"ch3_trust": "strand" if rng.randi() % 2 == 0 else "leyla", "ch3_true_ending": secret, "ch3_echoes": 4 if secret else 1}}
	GameState.start_new(chapter)
	logic = GameState.logic
	var total := _solver_length()
	var frac: float = WARM[maxi(0, seed_n - 1) % WARM.size()] if seed_n > 0 else 0.0
	if frac > 0.0:
		frac = clampf(frac + rng.randf_range(-0.05, 0.05), 0.0, 0.85)
	warm = warm_arg if warm_arg >= 0 else int(total * frac)
	for _i in warm:
		if _would_complete():
			break
		_solver_step(logic)
	logic.select_item("") # the solver may leave a tool in hand; the chaos player picks its own


## How many solver steps a fresh copy of this game needs to finish.
func _solver_length() -> int:
	var l := Chapters.new_logic(chapter)
	l.setup_from_profile(GameState.profile.get("choices", {}))
	l.apply_seed(seed_n)
	var n := 0
	while not l.is_complete() and n < 2000:
		_solver_step(l)
		n += 1
	return n


func _solver_step(l: RoomLogic) -> void:
	match chapter:
		"ch4":
			ArrayHallSolver.step(l as ArrayHallLogic, ending)
		"ch3":
			UndergroundSolver.step(l as UndergroundLogic, ending)
		"ch2":
			ArchiveSolver.step(l as ArchiveLogic, ending)
		_:
			Lab7Solver.step(l as Lab7Logic, ending)


## True when the solver's next step would finish the chapter (the chaos never completes it by itself).
func _would_complete() -> bool:
	var c := _copy_logic()
	_solver_step(c)
	return c.is_complete()


func _copy_logic() -> RoomLogic:
	var c := Chapters.new_logic(chapter)
	c.from_dict(JSON.parse_string(JSON.stringify(logic.to_dict())))
	return c


func _open_room() -> void:
	room = (load(SCENES[chapter]) as PackedScene).instantiate()
	room.set("capture_mode", true) # no intro cards: the chaos starts at the first view
	get_tree().root.add_child(room)
	await _settle(2.0)
	cam = room.get("cam")
	hud = room.get("hud")
	touch = room.get("touch")
	touch.tapped.connect(func(_p: Vector2) -> void: _delivered = true)


func _finish() -> void:
	# the end check: from the chaos state the solver must still finish the chapter
	var c := _copy_logic()
	var solved := logic.is_complete() or _solve(c)
	_ctx_part = ""
	_ctx_item = ""
	_check("unsolvable", solved, "the chapter solver cannot finish from this state; goal %s, state %s" % [c.hint_goal(),
		str(c.state)])
	var acts: Array[String] = []
	for k: String in actions:
		acts.append("%s %d" % [k, actions[k]])
	_log("chaos %s seed %d: actions %s; %d of %d taps reached the room" % [chapter, seed_n, ", ".join(acts),
		delivered_taps, taps])
	_log("CHAOS_RESULT chapter=%s seed=%d steps=%d taps=%d held=%d violations=%d" % [chapter, seed_n, steps_done, taps,
		held_taps, violations])
	if out_dir != "":
		var f := FileAccess.open(out_dir + "/chaos_report.txt", FileAccess.WRITE)
		if f != null:
			f.store_string("\n".join(report) + "\n")
	SaveSystem.delete_game()
	var qa_exit := 0 if violations == 0 else 1
	print("QA_DONE exit=%d" % qa_exit) # tools/qa_run.sh: the run finished even if the process then hangs on exit
	get_tree().quit(qa_exit)


func _solve(l: RoomLogic) -> bool:
	match chapter:
		"ch4":
			return ArrayHallSolver.solve(l as ArrayHallLogic, ending)
		"ch3":
			return UndergroundSolver.solve(l as UndergroundLogic, ending)
		"ch2":
			return ArchiveSolver.solve(l as ArchiveLogic, ending)
	return Lab7Solver.solve(l as Lab7Logic, ending)


# ====================================================================== violations
## A one-off event that went wrong (counted every time).
func _viol(kind: String, msg: String) -> void:
	violations += 1
	_log("VIOLATION %s chaos %s seed %d step %d view %s part %s item %s: %s" % [kind, chapter, seed_n, step_n,
		cam.current() if cam != null else "-", _ctx_part if _ctx_part != "" else "-", _ctx_item if _ctx_item != "" else "-", msg])
	if out_dir != "" and not _shot_taken and DisplayServer.get_name() != "headless":
		_shot_taken = true
		get_viewport().get_texture().get_image().save_png("%s/violation_%s_seed%d_step%d.png" % [out_dir, chapter, seed_n, step_n])


## A state that must hold: counted once per episode (it counts again after it was fine in between).
func _check(kind: String, ok: bool, msg: String) -> void:
	if ok:
		_active.erase(kind)
	elif not _active.has(kind):
		_active[kind] = true
		_viol(kind, msg)


# ====================================================================== waiting
func _settle(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()


func _overlay() -> Control:
	var o: Variant = hud.get("_overlay")
	return o as Control if o != null and is_instance_valid(o) else null


## The HUD is locked (a cinematic), the room runs one, or the camera is moving.
func _busy_now() -> bool:
	return _flag(hud, "_busy") or _flag(room, "_cinematic") or cam.transitioning


## A bool property of a node that may not have it (Chapter 1's room has no _cinematic).
func _flag(n: Node, prop: String) -> bool:
	var v: Variant = n.get(prop)
	return v is bool and v


## Waits until the player could act again. false (a violation) when input never comes back.
func _wait_idle() -> bool:
	var t := 0.0
	while _busy_now() and _overlay() == null and t < BUSY_LIMIT:
		await _settle(0.25)
		t += 0.25
	if _overlay() != null:
		return true
	if _busy_now():
		_viol("stuck", "input never came back after %d s: HUD busy %s, room cinematic %s, camera moving %s" % [int(BUSY_LIMIT),
			str(hud.get("_busy")), str(room.get("_cinematic")), str(cam.transitioning)])
		return false
	if not touch.enabled:
		await _settle(1.0)
		if not touch.enabled and _overlay() == null and not _busy_now():
			_viol("stuck", "room touch input is off with no overlay open and nothing animating")
			return false
	if get_tree().paused:
		_viol("stuck", "the game is paused with no overlay open")
		return false
	return true


# ====================================================================== one chaos step
func _chaos_step() -> void:
	if _overlay() != null:
		await _step_overlay()
		return
	_overlay_steps = 0
	if only == "continue":
		await _act_tap(rng.randi_range(1, 3))
		if _overlay() == null:
			await _act_continue()
		return
	if only == "walkback":
		await _act_view()
		if rng.randf() < 0.5:
			await _pick_item()
		if rng.randf() < 0.4:
			await _act_tap(1)
		if _overlay() == null:
			await _act_walkback()
		return
	if rng.randf() < nudge:
		await _act_nudge()
	var r := rng.randf()
	if r < 0.44:
		await _act_tap(1)
	elif r < 0.54:
		await _act_view()
	elif r < 0.62:
		await _act_tap(rng.randi_range(3, 9)) # hammers one control: a wrong code, a dial turned over and over
	elif r < 0.67:
		await _act_drag()
	elif r < 0.73:
		await _act_hint()
	elif r < 0.80:
		await _act_back()
	elif r < 0.84:
		await _act_walkback()
	elif r < 0.89:
		await _act_bag()
	elif r < 0.905:
		await _act_continue()
	else:
		await _act_item()


func _count(action: String) -> void:
	actions[action] = int(actions.get(action, 0)) + 1
	if trace:
		print("step %d: %s | %s" % [step_n, action, _ui_sig()])


## The solver makes a few real moves, so the chaos reaches later puzzles (never the last one).
func _act_nudge() -> void:
	if logic.solved_count() >= logic.puzzle_ids().size() - 2 and not to_finale:
		return # the last two puzzles end in the finale: the chaos stays in front of them, the end check finishes them
	_count("nudge")
	for _i in rng.randi_range(1, 3):
		if _would_complete():
			break
		_solver_step(logic)
	await _settle(0.4)


## Walks the camera to a random view of the room (some are framed from the state first, as the room does).
func _act_view() -> void:
	var ids: Array = cam.views.keys()
	var id: String = ids[rng.randi_range(0, ids.size() - 1)]
	_count("view")
	_ctx_part = "-> " + id
	if room.has_method("prepare_view"):
		room.call("prepare_view", id)
	cam.go(id)
	if rng.randf() < 0.85: # the rest tap on while the camera is still moving
		await _settle(0.2)
		var t := 0.0
		while cam.transitioning and t < BUSY_LIMIT:
			await _settle(0.2)
			t += 0.2
		if cam.transitioning:
			_viol("stuck", "the camera never arrived at %s" % id)
	else:
		await _settle(0.1)


## A tap on something in view: a part (or scenery with a hotspot), sometimes after picking an item, sometimes at a
## random point; `times` > 1 hammers the same point.
func _act_tap(times: int) -> void:
	_count("tap" if times == 1 else "hammer")
	if not logic.inventory.is_empty() and rng.randf() < 0.45:
		await _pick_item()
	elif logic.selected != "" and rng.randf() < 0.1:
		_count("put_away")
		await _press_back()
	var target := _pick_target() if rng.randf() < 0.92 else {}
	var sp: Vector2
	var part := ""
	if target.is_empty():
		var vp := get_viewport().get_visible_rect()
		sp = vp.position + Vector2(rng.randf(), rng.randf()) * vp.size
	else:
		sp = target["point"]
		part = target["part"]
	for _i in times:
		await _tap_room(sp, part)
		if _overlay() != null or _stop:
			break


## A drag from a part (a knob, the radio dial) or from empty space (looking around).
func _act_drag() -> void:
	_count("drag")
	var target := _pick_target()
	var vp := get_viewport().get_visible_rect()
	var from: Vector2 = target["point"] if not target.is_empty() else vp.position + Vector2(rng.randf(), rng.randf()) * vp.size
	_ctx_part = str(target.get("part", ""))
	_ctx_item = logic.selected
	var delta := Vector2.from_angle(rng.randf() * TAU) * rng.randf_range(40.0, 320.0)
	var pos := get_viewport().get_final_transform() * from
	_touch(0, pos, true)
	await get_tree().process_frame
	for _i in 6:
		var step := delta / 6.0 * get_viewport().get_final_transform().get_scale()
		pos += step
		var d := InputEventScreenDrag.new()
		d.index = 0
		d.position = pos
		d.relative = step
		Input.parse_input_event(d)
		Input.flush_buffered_events()
		await get_tree().process_frame
	_touch(0, pos, false)
	await _settle(TAP_SETTLE)


## Opens the hint dialog from the HUD, asks for more hints, closes it (with Back or its Close button).
func _act_hint() -> void:
	_count("hint")
	_ctx_part = "HUD/Hint"
	var btn: Control = hud.get("_hint_btn")
	if not btn.is_visible_in_tree() or _busy_now():
		return
	await _tap_control(btn)
	await _settle(0.4)
	if _overlay() == null:
		_viol("hint", "the Hint button did not open the hint dialog")
		return
	for _i in rng.randi_range(0, 3):
		var more := _overlay_buttons()
		if more.size() < 2 or _overlay() == null:
			break
		await _tap_control(more[0]) # "Another hint" (the first button of the footer)
		await _settle(0.25)
	if rng.randf() < 0.5:
		await _press_back()
	else:
		var btns := _overlay_buttons()
		if not btns.is_empty():
			await _tap_control(btns[btns.size() - 1]) # Close
			await _settle(0.3)
	_check("hint_close", _overlay() == null, "the hint dialog did not close")
	if _overlay() != null:
		await _press_back()


## Back, one to four times (the Android back key / Escape).
func _act_back() -> void:
	_count("back")
	for _i in rng.randi_range(1, 4):
		await _press_back()
		if _stop:
			break


## Back until the pause menu opens: from any view, Back must lead out of the room's views, then Resume closes it.
func _act_walkback() -> void:
	_count("walkback")
	var presses := 0
	while _overlay() == null and presses < 14:
		await _press_back()
		presses += 1
		await _wait_idle()
	_ctx_part = "Back x%d" % presses
	if _overlay() == null:
		_viol("back_out", "Back pressed %d times never opened the pause menu (view %s, busy %s, ending %s); last presses: %s" % [
			presses, cam.current(), str(_flag(hud, "_busy")), str(_flag(room, "_ending")), " | ".join(_back_log)])
		return
	if _overlay() != null and not bool(_overlay().get_meta("locked", false)):
		await _press_back()
		_check("pause_close", _overlay() == null, "Back did not close the pause menu")


## Quit and Continue from whatever state the chaos left: the save is written, the room freed and rebuilt from the save.
## The rebuilt room must hold the same state and take input again (the playthroughs do this only on the right path).
func _act_continue() -> void:
	_count("continue")
	_ctx_part = "Continue"
	_ctx_item = logic.selected
	var before := JSON.stringify(logic.to_dict(), "", true)
	var saved := GameState.save_now()
	room.queue_free()
	await get_tree().process_frame
	await get_tree().process_frame
	var loaded := saved and GameState.continue_saved()
	if not loaded:
		GameState.logic = logic # carry on with the game in memory
	logic = GameState.logic
	await _open_room()
	await _settle(1.0)
	if not loaded:
		_viol("continue", "Continue could not load the save the game had just written (saved %s)" % str(saved))
	elif JSON.stringify(logic.to_dict(), "", true) != before:
		_viol("continue", "the state after Continue differs from the state that was saved")
	_check("continue_input", touch.enabled and not _flag(hud, "_busy"), "input is locked in the room rebuilt by Continue")
	if not logic.is_complete():
		_check("continue_hint", logic.hint_goal() != "", "no hint goal after Continue")


## Opens or closes the bag from its HUD button.
func _act_bag() -> void:
	_count("bag")
	_ctx_part = "HUD/Bag"
	var btn: Control = hud.get("_bag_btn")
	if not btn.is_visible_in_tree():
		return
	var was := bool(hud.call("is_bag_open"))
	var pressed := [0]
	var probe := func() -> void: pressed[0] += 1
	(btn as BaseButton).pressed.connect(probe)
	var rect := btn.get_global_rect()
	await _tap_control(btn)
	await _settle(0.4)
	(btn as BaseButton).pressed.disconnect(probe)
	_check("bag", bool(hud.call("is_bag_open")) != was or _busy_now(),
		"the Bag button did not %s the bag (it was pressed %d times; button %s, disabled %s; close-up %s; item in hand %s)" % [
		"close" if was else "open", pressed[0], str(rect), str((btn as BaseButton).disabled), str(hud.get("_closeup")),
		logic.selected])


## Picks an item; then sometimes looks at it (a second tap on its slot) or combines it with another.
func _act_item() -> void:
	_count("item")
	await _pick_item()
	if logic.selected == "":
		return
	var r := rng.randf()
	if r < 0.3 and logic.inventory.size() > 1:
		var combine: Control = hud.get("_act_combine")
		if combine.is_visible_in_tree():
			_count("combine")
			await _tap_control(combine)
			await _settle(0.2)
			var other: String = logic.inventory[rng.randi_range(0, logic.inventory.size() - 1)]
			hud.call("_on_slot", other)
			await _settle(0.3)
	elif r < 0.4:
		_count("inspect")
		var insp: Control = hud.get("_act_inspect")
		if insp.is_visible_in_tree():
			await _tap_control(insp)
			await _settle(0.4)


## Takes a random item of the bag into the hand (opening the bag first, as a player must).
func _pick_item() -> void:
	if logic.inventory.is_empty():
		return
	var id: String = logic.inventory[rng.randi_range(0, logic.inventory.size() - 1)]
	if not bool(hud.call("is_bag_open")):
		var btn: Control = hud.get("_bag_btn")
		if not btn.is_visible_in_tree() or _overlay() != null:
			return
		await _tap_control(btn)
		await _settle(0.4)
	if not bool(hud.call("is_bag_open")) or _overlay() != null:
		return
	_count("pick_item")
	hud.call("_on_slot", id)
	await _settle(0.5) # in a close-up the bag folds 0.3 s after a pick (HUD._collapse_after_pick): let it finish


# ====================================================================== overlays
## An overlay is open (a document, the hint dialog, pause, the inspect viewer, the finale choice): close it with Back,
## press one of its buttons, or tap around it (that must never reach the room).
func _step_overlay() -> void:
	var o := _overlay()
	_overlay_steps += 1
	if bool(o.get_meta("locked", false)):
		await _answer_locked(o)
		return
	var r := rng.randf()
	if r < 0.5 or _overlay_steps > 5:
		_count("overlay_back")
		await _press_back()
	elif r < 0.75:
		_count("overlay_tap")
		await _tap_under_overlay(o)
	else:
		_count("overlay_button")
		var btns := _overlay_buttons()
		if btns.is_empty():
			await _press_back()
		else:
			_ctx_part = "overlay/" + str((btns[0] as Button).text)
			await _tap_control(btns[rng.randi_range(0, btns.size() - 1)])
			await _settle(0.35)


## A tap on the dimmed room under an overlay: the logic and the room must not change.
func _tap_under_overlay(o: Control) -> void:
	var vp := get_viewport().get_visible_rect()
	var sp := vp.position + Vector2(rng.randf(), rng.randf()) * vp.size
	for b in _denied_buttons(o):
		if b.get_global_rect().grow(12.0).has_point(sp):
			return # a finger there would leave the room (Main menu, Settings): not what this action is for
	var before := JSON.stringify(logic.to_dict())
	var view := cam.current()
	_ctx_part = "under overlay"
	await _send_tap(sp)
	await _settle(TAP_SETTLE)
	if is_instance_valid(o) and _overlay() == o and (JSON.stringify(logic.to_dict()) != before or cam.current() != view):
		_viol("leak", "a tap under the open overlay reached the room")


## The finale question (or the chapter-complete card) needs an answer: choose one, as a player does.
func _answer_locked(o: Control) -> void:
	var btns := _overlay_buttons()
	_count("finale")
	if btns.is_empty() or logic.is_complete():
		_stop = true # the chapter-complete card (its buttons leave the room): the chaos run is over
		return
	var b: Button = btns[rng.randi_range(0, btns.size() - 1)]
	_ctx_part = "finale/" + b.text
	var pressed := [false]
	b.pressed.connect(func() -> void: pressed[0] = true)
	var rect := b.get_global_rect()
	await _tap_control(b)
	await _settle(1.0)
	if is_instance_valid(o) and _overlay() == o: # (a freed overlay equals null)
		_viol("finale", "the finale button did nothing (button %s, pressed %s, complete %s, busy %s)" % [str(rect), str(pressed[0]),
			str(logic.is_complete()), str(hud.get("_busy"))])
		_stop = true
		return
	var t := 0.0
	while not logic.is_complete() and t < 10.0:
		await _settle(0.5)
		t += 0.5
	if not logic.is_complete():
		_viol("finale", "the finale choice %s did not complete the chapter" % b.text)
		_stop = true


## The buttons the chaos player never touches (they leave the room or change the settings).
func _denied_buttons(o: Control) -> Array[Button]:
	var out: Array[Button] = []
	for n in o.find_children("*", "Button", true, false):
		var b := n as Button
		if b.is_visible_in_tree() and DENY_BUTTONS.has(b.text):
			out.append(b)
	return out


## The visible, enabled buttons of the open overlay that stay in the room, in tree order.
func _overlay_buttons() -> Array[Button]:
	var out: Array[Button] = []
	var o := _overlay()
	if o == null:
		return out
	for n in o.find_children("*", "Button", true, false):
		var b := n as Button
		if b.is_visible_in_tree() and not b.disabled and not DENY_BUTTONS.has(b.text):
			out.append(b)
	return out


# ====================================================================== back
func _ui_sig() -> String:
	var o := _overlay() # a new overlay in place of the old one counts (Back from a zoomed photo reopens the evidence board)
	return str([o.get_instance_id() if o != null else 0, logic.selected, hud.call("is_bag_open"), cam.current(),
		cam.stack.size(), hud.get("_combine_mode")])


## One press of Back. It must change something unless the HUD is locked or the camera is moving.
func _press_back() -> void:
	var sig := _ui_sig()
	var locked := _busy_now() or _flag(room, "_ending")
	_ctx_part = "Back"
	_ctx_item = logic.selected
	room.call("handle_back")
	await _settle(0.35)
	if trace:
		print("  back: %s -> %s" % [sig, _ui_sig()])
	_back_log.append("%s -> %s (locked %s)" % [sig, _ui_sig(), str(locked)])
	if _back_log.size() > 6:
		_back_log.pop_front()
	if not locked and _ui_sig() == sig:
		_viol("back", "Back did nothing (view %s, no overlay, nothing in hand, bag shut)" % cam.current())


# ====================================================================== taps
## Picks a tap target in view: usually an interactive part (IA_*, Item_*, …), now and then scenery that has a
## hotspot (tapping it moves the camera). {} when nothing in view can be hit. -> {point, part, hotspot, body}
func _pick_target() -> Dictionary:
	var vp := get_viewport().get_visible_rect()
	var blocked: Array[Rect2] = []
	blocked.assign(hud.call("blocked_rects"))
	var bodies := room.find_children("*", "StaticBody3D", true, false)
	_shuffle(bodies)
	var want_part := rng.randf() < 0.88
	for _pass in 2:
		var looked := 0
		for n in bodies:
			var b := n as StaticBody3D
			if b.collision_layer == 0:
				continue
			var part := str(b.get_meta("part", ""))
			if (part != "") != want_part:
				continue
			if not b.is_visible_in_tree():
				continue
			looked += 1
			if looked > 400:
				break
			var r := _screen_rect(b)
			if r.size == Vector2.ZERO or not vp.intersects(r):
				continue
			var hs := str(room.call("resolve", {"collider": b, "position": b.global_position}).get("hotspot", ""))
			if part == "" and hs == "":
				continue
			r = r.intersection(vp)
			for k in 8:
				var sp := r.get_center() if k == 0 else r.position + r.size * Vector2(rng.randf_range(0.1, 0.9), rng.randf_range(0.1, 0.9))
				if _under(sp, blocked):
					continue
				var hit: Dictionary = room.call("raycast", sp)
				if not hit.is_empty() and hit.get("collider") == b:
					return {"point": sp, "part": part if part != "" else "(" + hs + ")", "hotspot": hs, "body": b}
		want_part = not want_part # nothing of that kind in view: try the other
	return {}


func _under(p: Vector2, rects: Array[Rect2]) -> bool:
	for r in rects:
		if r.has_point(p):
			return true
	return false


func _shuffle(a: Array) -> void:
	for i in range(a.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var t: Variant = a[i]
		a[i] = a[j]
		a[j] = t


## The screen rectangle of a tap body: its box collider's corners, or its mesh's bounds. Empty when behind the camera.
func _screen_rect(b: StaticBody3D) -> Rect2:
	var xf := Transform3D.IDENTITY
	var ab := AABB()
	var found := false
	for c in b.get_children():
		if not (c is CollisionShape3D):
			continue
		var cs := c as CollisionShape3D
		if cs.disabled or cs.shape == null:
			continue
		if cs.shape is BoxShape3D:
			var sz := (cs.shape as BoxShape3D).size
			xf = cs.global_transform
			ab = AABB(-sz * 0.5, sz)
			found = true
		else:
			var mi := b.get_parent() as MeshInstance3D
			if mi != null and mi.mesh != null:
				xf = mi.global_transform
				ab = mi.mesh.get_aabb()
				found = true
		break
	if not found:
		return Rect2()
	var r := Rect2()
	for k in 8:
		var wp := xf * ab.get_endpoint(k)
		if cam.is_position_behind(wp):
			return Rect2()
		var sp := cam.unproject_position(wp)
		r = Rect2(sp, Vector2.ZERO) if k == 0 else r.expand(sp)
	return r


## True when this tap, made now, must send the item in hand back to the bag: the item is not a tool, the tapped part
## belongs to a hotspot within reach and has a use target (RoomBase.use_selected). Echoes, shards and tubes are
## handled before that (tap_special / the shard tap).
func _expects_step_aside(sp: Vector2) -> bool:
	var sel := logic.selected
	if sel == "" or ItemDB.is_tool_item(sel) or cam.transitioning or _overlay() != null or not touch.enabled:
		return false
	if _flag(room, "_ending"):
		return false
	var hit: Dictionary = room.call("pick", sp)
	if hit.is_empty():
		return false
	var r: Dictionary = room.call("resolve", hit)
	var p: String = r["part"]
	var hs: String = r["hotspot"]
	if hs == "" or p.begins_with("Echo_") or p.begins_with("Shard_") or p.begins_with("IA_tube_"):
		return false
	if not bool(room.call("in_reach" if room.has_method("in_reach") else "_in_reach", hs)):
		return false
	var target: String = room.call("use_target" if room.has_method("use_target") else "_use_target", hs, p)
	return target != ""


## A tap on the room at `sp` (a point in the viewport), checking the item-in-hand rule.
func _tap_room(sp: Vector2, part: String) -> void:
	var sel := logic.selected
	_ctx_part = part
	_ctx_item = sel
	var expect := _expects_step_aside(sp)
	_delivered = false
	taps += 1
	if sel != "":
		held_taps += 1
	await _send_tap(sp)
	await _settle(TAP_SETTLE)
	delivered_taps += int(_delivered)
	if trace:
		print("  tap %d step %d view %s part %s item %s at %d,%d: room got it %s, item now %s" % [taps, step_n, cam.current(),
			part, sel if sel != "" else "-", sp.x, sp.y, str(_delivered), logic.selected if logic.selected != "" else "-"])
	if expect and _delivered and logic.selected == sel:
		_viol("item_blocks", "a tap with %s in hand on a reachable object left the item in hand (it has no use there and must step aside)" % sel)
		await _press_back()


## Taps the middle of a HUD control.
func _tap_control(c: Control) -> void:
	if c == null or not c.is_visible_in_tree():
		return
	_delivered = false
	await _send_tap(c.get_global_rect().get_center())
	if _delivered and _overlay() == null:
		_viol("hud_leak", "a tap on the HUD control %s also reached the room" % c.name)


## A real touch: press and release one frame apart, at a point of the viewport (canvas) coordinates.
func _send_tap(sp: Vector2) -> void:
	var pos := get_viewport().get_final_transform() * sp
	_touch(0, pos, true)
	await get_tree().process_frame
	_touch(0, pos, false)
	await get_tree().process_frame


func _touch(index: int, pos: Vector2, pressed: bool) -> void:
	var e := InputEventScreenTouch.new()
	e.index = index
	e.position = pos
	e.pressed = pressed
	Input.parse_input_event(e)
	Input.flush_buffered_events()


# ====================================================================== checks after a step
func _state_checks() -> void:
	if not logic.is_complete():
		_check("softlock", logic.hint_goal() != "", "hint_goal() is empty before the chapter is complete")
	var seen: Dictionary = {}
	var dup := ""
	for id in logic.inventory:
		if seen.has(id):
			dup = id
		seen[id] = true
	_check("dup_item", dup == "", "item %s is in the bag twice" % dup)
	_check("sel_item", logic.selected == "" or logic.inventory.has(logic.selected),
		"the item in hand (%s) is not in the bag" % logic.selected)
	var prompt := hud.get("_prompt") as Label
	if prompt != null:
		_check("prompt", (prompt.text != "") == (logic.selected != ""),
			"the HUD prompt (%s) does not follow the item in hand (%s)" % [prompt.text, logic.selected])
	if _overlay() == null and not _busy_now() and not cam.is_root():
		var back: Control = hud.get("_back_btn")
		_check("back_btn", back.visible, "no Back button in the close-up %s" % cam.current())
