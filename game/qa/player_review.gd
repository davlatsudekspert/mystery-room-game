extends Node
## Player-style review of Chapter 1. It plays like a first-time player, not like the solver:
## - the real intro;
## - looking around in the dark and tapping everything;
## - wrong codes and wrong items;
## - hints at every level, documents and inspect;
## - a language switch mid-game;
## - save → quit → continue;
## - the finale choice and the chapter screen.
## Every step leaves a screenshot and the exact HUD text the player saw (message, caption, view title),
## so a human can review the experience, not just the solution path.
## Run: xvfb-run -a godot --path game res://qa/player_review.tscn -- --out=<dir> [--lang=ru]
## Exit code 0 = no ✗ lines (a missing/unchanged message where one is required, a broken flow).

var out_dir := "/tmp/player_review"
var lang := "en"
var room: Node3D
var hud: Node
var logic: Lab7Logic
var report: Array[String] = []
var shot_n := 0
var _last_msg := ""
var _last_cap := ""


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		if a.begins_with("--lang="):
			lang = a.substr(7)
	DirAccess.make_dir_recursive_absolute(out_dir)
	SaveSystem.save_path = "user://qa_review_save.json"
	SaveSystem.profile_path = "user://qa_review_profile.json"
	SaveSystem.delete_game()
	GameState.profile = {}
	Loc.apply(lang)
	GameState.start_new("ch1")
	logic = GameState.logic
	await _load_room()
	await intro()
	await explore_dark()
	await mistakes()
	await hints_and_documents()
	await language_switch()
	await save_quit_continue()
	await finale()
	_finish()


# ====================================================================== helpers
func _load_room() -> void:
	room = (load("res://src/rooms/lab7/lab7.tscn") as PackedScene).instantiate()
	get_tree().root.add_child.call_deferred(room)
	await get_tree().process_frame
	await get_tree().process_frame
	hud = room.get("hud")
	logic = GameState.logic


func _settle(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()


func shot(name: String) -> void:
	await _settle(0.25)
	await RenderingServer.frame_post_draw
	shot_n += 1
	var p := "%s/%02d_%s.png" % [out_dir, shot_n, name]
	get_viewport().get_texture().get_image().save_png(p)
	report.append("    [shot %s]" % p.get_file())


func cam() -> RoomCamera:
	return room.get("cam")


## What the player currently reads on the HUD (only visible text counts).
func seen() -> String:
	var parts: Array[String] = []
	var top := hud.get("_top_caption") as Label
	if top and top.text != "":
		parts.append("title «%s»" % tr(top.text))
	var m := hud.get("_message") as Label
	if m and m.modulate.a > 0.05 and m.text != "":
		parts.append("message «%s»" % m.text)
	var c := hud.get("_caption_line") as Label
	if c and c.modulate.a > 0.05 and c.text != "":
		parts.append("caption «%s»" % c.text)
	var p := hud.get("_prompt") as Label
	if p and p.visible and p.text != "":
		parts.append("prompt «%s»" % p.text)
	return ", ".join(parts)


func _msg_text() -> String:
	var m := hud.get("_message") as Label
	return m.text if m and m.modulate.a > 0.05 else ""


func note(line: String) -> void:
	report.append(line)
	print(line)


## Record a player action and what the game answered. `expect_message` = the action must show a message.
func did(action: String, expect_message: bool = false) -> void:
	await _settle(0.45)
	var s := seen()
	var msg := _msg_text()
	note("  • %s → view %s; %s" % [action, cam().current(), s if s != "" else "(no text)"])
	if expect_message and msg == "":
		note("✗ no feedback message for: " + action)
	_last_msg = msg
	(hud.get("_message") as Label).modulate.a = 0.0 # so the next action's message is detected as new


func check(label: String, ok: bool) -> void:
	note(("✓ " if ok else "✗ ") + label)


func model(id: String) -> Node3D:
	return (room.get("models") as Dictionary).get(id)


func _rect_of(n: Node3D) -> Rect2:
	var r := Rect2()
	var first := true
	for mi in ModelUtil.find_meshes(n):
		if not mi.is_visible_in_tree():
			continue
		var ab := mi.get_aabb()
		for k in 8:
			var wp := mi.global_transform * ab.get_endpoint(k)
			if cam().is_position_behind(wp):
				continue
			var sp := cam().unproject_position(wp)
			if first:
				r = Rect2(sp, Vector2.ZERO)
				first = false
			else:
				r = r.expand(sp)
	return r


func _centre_of(n: Node3D) -> Vector3:
	var ab := AABB()
	var first := true
	for mi in ModelUtil.find_meshes(n):
		var b := mi.global_transform * mi.get_aabb()
		ab = b if first else ab.merge(b)
		first = false
	return ab.get_center()


## Free-look the root camera toward a world point, like a player dragging to look around.
func look_toward(p: Vector3) -> void:
	var c := cam()
	var dir := (p - c.global_position).normalized()
	var base: Dictionary = c.views[c.current()]
	var t := Transform3D(Basis.IDENTITY, base["pos"]).looking_at(base["target"], Vector3.UP)
	var fwd0 := -t.basis.z
	var yaw := rad_to_deg(atan2(fwd0.x, fwd0.z) - atan2(dir.x, dir.z))
	var pitch := rad_to_deg(asin(clampf(dir.y, -1.0, 1.0)) - asin(clampf(fwd0.y, -1.0, 1.0)))
	c.yaw = wrapf(-yaw, -180.0, 180.0)
	c.pitch = clampf(pitch, RoomCamera.PITCH_MIN, RoomCamera.PITCH_MAX)
	c.call("_apply_free_look")
	if not _on_screen(p):
		# the analytic aim can miss (a camera still settling, a steep target): sweep like a player turning round
		var best_yaw := c.yaw
		var best_d := INF
		for step in 36:
			c.yaw = wrapf(step * 10.0 - 180.0, -180.0, 180.0)
			c.call("_apply_free_look")
			if c.is_position_behind(p):
				continue
			var d := c.unproject_position(p).distance_to(get_viewport().get_visible_rect().get_center())
			if d < best_d:
				best_d = d
				best_yaw = c.yaw
		c.yaw = best_yaw
		c.call("_apply_free_look")
	await _settle(0.3)


func _on_screen(p: Vector3) -> bool:
	return not cam().is_position_behind(p) and get_viewport().get_visible_rect().grow(-40.0).has_point(cam().unproject_position(p))


## Tap the screen point of a world position (or a node's projected centre).
func tap_at(p: Vector3) -> void:
	if cam().is_position_behind(p):
		note("  (target behind the camera)")
		return
	room.call("_on_tap", cam().unproject_position(p))
	await _settle(0.95)


func tap_part(model_id: String, part: String) -> void:
	var n := ModelUtil.find(model(model_id), part) if part != "" else model(model_id)
	if n == null:
		note("✗ part missing: %s/%s" % [model_id, part])
		return
	var mi := n as MeshInstance3D
	var c := (mi.global_transform * mi.get_aabb()).get_center() if mi else _centre_of(n)
	await tap_at(c)


func back() -> void:
	room.call("handle_back")
	await _settle(0.9)


func to_root() -> void:
	for i in 6:
		if cam().is_root():
			break
		room.call("go_back")
		await _settle(0.8)
	if cam().current() != "lab":
		cam().go("lab")
		await _settle(0.9)


# ====================================================================== 1. intro
func intro() -> void:
	note("== Intro (first launch, %s)" % lang)
	await _settle(1.4)
	await shot("intro_1")
	note("  intro card 1: «%s»" % tr("intro.1"))
	await _settle(6.2)
	await shot("intro_2")
	note("  intro card 2: «%s»" % tr("intro.2"))
	var t := 0.0
	while bool(hud.get("_busy")) and t < 20.0:
		await _settle(0.25)
		t += 0.25
	check("intro ends and hands control to the player", not bool(hud.get("_busy")))
	await _settle(0.6)
	await shot("after_intro")
	await did("after the intro")
	await _settle(2.0)
	await shot("first_view_tutorial")
	await did("first view")


# ====================================================================== 2. explore in the dark
const EXPLORE := ["desk", "flip_clock", "filing_cabinet", "bookshelf", "gear_box", "chalkboard", "lumen_projector",
	"lab_bench", "radio", "poster_frame", "wall_safe", "panel7", "coat_rack", "door_lab7", "light_sensor",
	"mirror_stand", "mirror_stand_b", "evidence_board"]


func explore_dark() -> void:
	note("== Exploring in the dark: look at each thing and tap it")
	for id: String in EXPLORE:
		await to_root()
		var n := model(id)
		if n == null or not n.is_visible_in_tree():
			note("  (%s not visible from the room)" % id)
			continue
		await look_toward(_centre_of(n))
		var before := cam().current()
		var hv: Dictionary = room.get_script().get_script_constant_map().get("HOTSPOT_VIEW", {})
		var expected: String = hv.get(str(n.get_meta("hotspot", "")), "")
		await tap_at(_centre_of(n))
		await did("tap " + id)
		if expected != "" and cam().current() != before and cam().current() != expected:
			note("  ! the middle of %s opened «%s», not its own view «%s»" % [id, cam().current(), expected])
			await to_root()
			await look_toward(_centre_of(n))
		if cam().current() == before or (expected != "" and cam().current() != expected):
			# the middle of a model's bounds can be empty space (a mirror on a thin stand): a player taps the
			# part they can see, so try each of the object's tap areas before calling it unreachable
			var reached := ""
			for body in n.find_children("*", "StaticBody3D", true, false):
				var cs := body.get_child(0) as Node3D
				var p := cs.global_position if cs else (body as Node3D).global_position
				if cam().is_position_behind(p) or not get_viewport().get_visible_rect().has_point(cam().unproject_position(p)):
					continue
				await tap_at(p)
				if cam().current() != before and (expected == "" or cam().current() == expected):
					reached = str(body.get_meta("part", body.name))
					break
				if not cam().is_root():
					await to_root()
					await look_toward(_centre_of(n))
			if reached != "":
				note("  (tapping the %s of %s reaches it)" % [reached, id])
			else:
				note("  ! tapping %s from the room did not move the camera (blocked by something in front?)" % id)
		await shot("look_" + id)
	await to_root()


# ====================================================================== 3. mistakes and dead ends
func mistakes() -> void:
	note("== Wrong attempts (every one must answer with feedback)")
	var s := logic.state
	# the door
	cam().go("door")
	await _settle(0.9)
	await tap_part("door_lab7", "IA_door_leaf")
	await did("tap the sealed door", true)
	# the drawer without the code
	cam().go("desk")
	await _settle(0.9)
	cam().go("drawer")
	await _settle(0.9)
	# pull it by the side of its front, not the code wheels in the middle
	var drawer := ModelUtil.find(model("desk"), "IA_drawer_top") as MeshInstance3D
	if drawer:
		var ab := drawer.get_aabb()
		await tap_at(drawer.global_transform * (ab.position + ab.size * Vector3(0.12, 0.5, 0.5)))
	await did("pull the locked drawer", true)
	await shot("drawer_locked_message")
	# safe: a wrong code
	await to_root()
	cam().go("safe")
	await _settle(0.9)
	for k in ["1", "2", "3", "4", "enter"]:
		await tap_part("wall_safe", "IA_key_" + k)
	await did("enter 1234 on the safe", true)
	await shot("safe_wrong_code")
	check("wrong safe code keeps the safe closed and clears the input", not s["safe_open"] and str(s["safe_input"]) == "")
	# radio and projector without power
	await to_root()
	cam().go("radio")
	await _settle(0.9)
	await tap_part("radio", "IA_tuning_knob")
	await did("turn the dead radio", true)
	await to_root()
	cam().go("projector")
	await _settle(0.9)
	await tap_part("lumen_projector", "IA_projector_lever")
	await did("pull the projector lever (no power, no lens)", true)
	# panel without the handle
	await to_root()
	cam().go("panel")
	await _settle(0.9)
	await tap_part("panel7", "IA_switch_0")
	await did("flip a breaker switch before the power is back")
	await tap_part("panel7", "IA_main_lever")
	await did("pull the main lever without its handle", true)
	await shot("panel_no_handle")
	if int(s["switches"][0]) == 1:
		logic.toggle_switch(0) # leave the panel as found
	# mirror B: empty bracket
	await to_root()
	cam().go("mirror_b")
	await _settle(0.9)
	await tap_part("mirror_stand_b", "IA_mirror_mount")
	await did("tap the empty mirror bracket", true)
	# the notebook, then use it on the door (wrong item)
	await to_root()
	cam().go("desk")
	await _settle(0.9)
	await tap_part("notebook", "")
	await did("pick up the notebook", true)
	check("notebook is in the inventory", logic.has_item("notebook"))
	await shot("notebook_taken_inventory")
	logic.select_item("notebook")
	await _settle(0.3)
	await shot("item_selected_prompt")
	await to_root()
	cam().go("door")
	await _settle(0.9)
	await tap_part("door_lab7", "IA_door_leaf")
	await did("use the notebook on the door", true)
	logic.select_item("")
	await to_root()


# ====================================================================== 4. hints, documents, inspect
func hints_and_documents() -> void:
	note("== Hints at the start (goal %s)" % logic.hint_goal())
	hud.call("show_hint")
	await _settle(0.5)
	await shot("hint_level1")
	note("  hint 1: «%s»" % tr("hint.%s.1" % logic.hint_goal()))
	var more := _find_button(hud.get("_overlay"), "ui.hint_more")
	for lvl in [2, 3]:
		if more:
			more.emit_signal("pressed")
			await _settle(0.4)
			await shot("hint_level%d" % lvl)
			note("  hint %d: «%s»" % [lvl, tr("hint.%s.%d" % [logic.hint_goal(), lvl])])
	check("hint button disabled at level 3", more != null and more.disabled)
	await back()
	await _settle(0.5)
	check("back closes the hint panel", hud.get("_overlay") == null)
	note("== Documents")
	for page in [0, 1, 2, 3, 4, 5, 6, 7]:
		hud.call("_show_notebook", page)
		await _settle(0.4)
		await shot("notebook_p%d" % (page + 1))
	hud.call("_close_overlay")
	hud.call("show_inspect", "notebook")
	await _settle(1.0)
	await shot("inspect_notebook")
	hud.call("_close_overlay")
	await _settle(0.3)
	await did("documents closed")


func _find_button(root: Node, text_key: String) -> Button:
	if root == null:
		return null
	if root is Button and ((root as Button).text == text_key or (root as Button).text == tr(text_key)):
		return root
	for c in root.get_children():
		var b := _find_button(c, text_key)
		if b:
			return b
	return null


# ====================================================================== 5. language switch mid-game
func language_switch() -> void:
	note("== Language switch mid-game")
	for code in ["ru", "uz", lang]:
		Loc.apply(code)
		await _settle(0.4)
		cam().go("desk")
		await _settle(0.9)
		await shot("lang_%s_desk" % code)
		await did("language %s, desk view" % code)
		hud.call("show_pause")
		await _settle(0.5)
		await shot("lang_%s_pause" % code)
		hud.call("_close_overlay")
		await to_root()


# ====================================================================== 6. save → quit → continue
func save_quit_continue() -> void:
	note("== Play on to the power, then quit and continue")
	var guard := 0
	while not logic.state["power_on"] and guard < 200:
		guard += 1
		Lab7Solver.step(logic, "take_lens")
	logic.select_item("")
	await _settle(3.0)
	await to_root()
	await shot("powered_before_quit")
	var before := JSON.stringify(logic.to_dict())
	check("save written", GameState.save_now())
	room.queue_free()
	await _settle(0.5)
	GameState.logic = null
	check("continue loads the save", GameState.continue_saved())
	check("continued state equals the saved state", JSON.stringify(GameState.logic.to_dict()) == before)
	await _load_room()
	await _settle(1.5)
	check("no intro replays on continue", not bool(hud.get("_busy")))
	await shot("continued_room")
	for v in ["drawer", "safe", "panel", "desk_side", "gearbox"]:
		cam().go(v)
		await _settle(1.0)
		await shot("continued_" + v)
	await to_root()


# ====================================================================== 7. finale
func finale() -> void:
	note("== Play to the finale, choose, read the chapter screen")
	var guard := 0
	while not logic.state["door_open"] and guard < 300:
		guard += 1
		Lab7Solver.step(logic, "take_lens")
	var w := 0
	while w < 120 and hud.get("_overlay") == null:
		w += 1
		await _settle(0.25)
		if w == 12:
			await shot("finale_flashback")
	await shot("finale_choice")
	await did("the finale choice")
	var take := _find_button(hud.get("_overlay"), "ui.take_lens")
	check("choice offers 'take the lens'", take != null)
	await back()
	check("back does not dismiss the finale choice", hud.get("_overlay") != null)
	if take:
		take.emit_signal("pressed")
	else:
		logic.choose_ending("take_lens")
	await _settle(3.0)
	await shot("chapter_complete")
	check("chapter complete", logic.state["complete"])
	var o: Node = hud.get("_overlay")
	var texts: Array[String] = []
	_collect_texts(o, texts)
	note("  chapter screen: " + " | ".join(texts))


func _collect_texts(n: Node, out: Array[String]) -> void:
	if n == null:
		return
	if n is Label and (n as Label).visible and (n as Label).text != "":
		out.append(tr((n as Label).text))
	if n is Button and (n as Button).text != "":
		out.append("[%s]" % tr((n as Button).text))
	for c in n.get_children():
		_collect_texts(c, out)


func _finish() -> void:
	var f := FileAccess.open(out_dir + "/player_review.txt", FileAccess.WRITE)
	f.store_string("\n".join(report) + "\n")
	SaveSystem.delete_game()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SaveSystem.profile_path))
	var bad := report.filter(func(l: String) -> bool: return l.begins_with("✗")).size()
	print("player review: %d problems" % bad)
	var qa_exit: int = 0 if bad == 0 else 1
	print("QA_DONE exit=%d" % qa_exit) # tools/qa_run.sh: the run finished even if the process then hangs on exit
	get_tree().quit(qa_exit)
