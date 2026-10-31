extends Node
## Promo capture (promo/README.md): loads a real room, brings the game to a state with the project's own solvers and
## then runs a step script (camera views, waits, solver steps) so a movie writer can record real footage.
## Run (movie): godot --path <project> --write-movie clip.avi --fixed-fps 30 res://qa/promo_capture.tscn -- \
##   --room=lab|archive --prep=<key> --steps="go:desk;wait:2;..." [--hud=0] [--keep=width]
## Steps (";" separated): go:<view>[:i] | wait:<s> | yaw:<deg>:<s> | pitch:<deg>:<s> | hud:on|off | notebook:<page> |
##   uvbtn | until:<state key> | solve:<n> | wheel:<i>:<n> | turnwheel:<n> | waitview:<view>:<max s> | fov:<deg> | quit
## Prep: lab:<n> (solver plays puzzles before P<n>) | archive:<state key> | archive:none

var room: Node3D
var logic: Variant
var room_name := "lab"
var steps := ""
var show_hud := true
var yaw_rate := 0.0
var yaw_left := 0.0
var pitch_rate := 0.0
var pitch_left := 0.0


func _ready() -> void:
	GameState.variant_seed = 0
	var prep := "lab:1"
	var keep := ""
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--room="):
			room_name = a.substr(7)
		if a.begins_with("--prep="):
			prep = a.substr(7)
		if a.begins_with("--steps="):
			steps = a.substr(8)
		if a.begins_with("--hud="):
			show_hud = a.substr(6) != "0"
		if a.begins_with("--keep="):
			keep = a.substr(7)
		if a.begins_with("--lang="):
			TranslationServer.set_locale(a.substr(7))
	SaveSystem.save_path = "user://qa_promo_save.json"
	SaveSystem.profile_path = "user://qa_promo_profile.json"
	GameState.qa_no_tips = true
	if room_name == "lab":
		GameState.start_new("ch1")
		logic = GameState.logic
		var n := int(prep.get_slice(":", 1))
		var ready := {2: "drawer_open", 3: "box_open", 4: "uv_desk", 40: "uv_lamp", 5: "safe_taken", 6: "compartment_taken",
			7: "power_on", 9: "signal_heard", 10: "shelf_open", 11: "mirror_taken", 12: "beam_on"}
		var g := 0
		while n > 1 and not _lab_ready(str(ready.get(n, ""))) and g < 300:
			g += 1
			Lab7Solver.step(logic, "leave_lens")
		logic.select_item("")
		room = (load("res://src/rooms/lab7/lab7.tscn") as PackedScene).instantiate()
	else:
		GameState.profile = {"choices": {"ch1_lens": "leave_lens", "ch1_shards": 5}}
		GameState.start_new("ch2")
		logic = GameState.logic
		var key := prep.get_slice(":", 1)
		var g := 0
		while key != "none" and not logic.state.get(key, false) and g < 600:
			g += 1
			ArchiveSolver.step(logic, "leyla_key")
		logic.select_item("")
		room = (load("res://src/rooms/archive/archive.tscn") as PackedScene).instantiate()
	room.set("capture_mode", true)
	get_tree().root.add_child.call_deferred(room)
	await get_tree().process_frame
	await get_tree().process_frame
	if keep == "width":
		(room.get("cam") as Camera3D).keep_aspect = Camera3D.KEEP_WIDTH
	if not show_hud:
		(room.get("hud") as CanvasLayer).visible = false
	await _settle(1.0)
	await run_steps()
	print("PROMO_DONE")
	get_tree().quit(0)


func _lab_ready(k: String) -> bool:
	var s: Dictionary = logic.state
	match k:
		"drawer_open": return s["drawer_open"] and logic.has_item("uv_lamp_empty")
		"box_open": return s["box_open"] and logic.has_item("battery_cell")
		"uv_desk": return logic.has_item("uv_lamp") and s["uv_page"]
		"uv_lamp": return logic.has_uv() and not s["uv_page"]
		"safe_taken": return s["safe_open"] and logic.has_item("radio_valve") and logic.has_item("brass_key")
		"compartment_taken": return logic.has_item("breaker_handle")
		"power_on": return s["power_on"]
		"signal_heard": return s["signal_heard"]
		"shelf_open": return s["shelf_open"]
		"mirror_taken": return logic.has_item("mirror_item") and s["emblem_recorded"] and s["lens_at"] == "inventory"
		"beam_on": return s["beam_on"]
	return true


func _settle(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()


func _process(delta: float) -> void:
	var c := room.get("cam") as RoomCamera if room != null else null
	if c == null:
		return
	if yaw_left > 0.0:
		var d := minf(yaw_left, absf(yaw_rate) * delta)
		c.set("_yaw_goal", float(c.get("_yaw_goal")) + d * signf(yaw_rate))
		yaw_left -= d
	if pitch_left > 0.0:
		var d2 := minf(pitch_left, absf(pitch_rate) * delta)
		c.set("_pitch_goal", float(c.get("_pitch_goal")) + d2 * signf(pitch_rate))
		pitch_left -= d2


func run_steps() -> void:
	var c := room.get("cam") as RoomCamera
	for raw in steps.split(";", false):
		var p := raw.strip_edges().split(":")
		print("step ", raw)
		match p[0]:
			"go": c.go(p[1], p.size() > 2 and p[2] == "i")
			"wait": await _settle(float(p[1]))
			"yaw":
				yaw_rate = float(p[1]) / float(p[2])
				yaw_left = absf(float(p[1]))
			"pitch":
				pitch_rate = float(p[1]) / float(p[2])
				pitch_left = absf(float(p[1]))
			"keep": c.keep_aspect = Camera3D.KEEP_WIDTH if p[1] == "width" else Camera3D.KEEP_HEIGHT
			"fov": c.set("_fov_goal", float(p[1]))
			"hud": (room.get("hud") as CanvasLayer).visible = p[1] == "on"
			"notebook": room.get("hud").call("_show_notebook", int(p[1]))
			"uvbtn":
				var o: Control = room.get("hud").get("_overlay")
				for b in o.find_children("*", "IconButton", true, false):
					if (b as Control).visible:
						(b as BaseButton).pressed.emit()
						break
			"until":
				var g := 0
				while not logic.state.get(p[1], false) and g < 600:
					g += 1
					if room_name == "lab":
						Lab7Solver.step(logic, "leave_lens")
					else:
						ArchiveSolver.step(logic, "leyla_key")
					await _settle(0.12)
			"solve":
				for _i in int(p[1]):
					if room_name == "lab":
						Lab7Solver.step(logic, "leave_lens")
					else:
						ArchiveSolver.step(logic, "leyla_key")
					await _settle(0.35)
			"wheel":
				logic.step_drawer_wheel(int(p[1]), int(p[2]))
			"turnwheel":
				for _i in (int(p[1]) if int(p[1]) > 0 else ArchiveLogic.WHEEL_TURNS):
					logic.turn_wheel()
					await _settle(0.3)
			"logic": logic.callv(p[1], Array(p.slice(2)).map(func(x: String) -> int: return int(x)))
			"choose":
				room.get("hud").call("_close_overlay")
				logic.choose_ending("leyla_key")
			"waitoverlay":
				var w2 := 0.0
				while room.get("hud").get("_overlay") == null and w2 < float(p[1]):
					await _settle(0.25)
					w2 += 0.25
			"state": print("STATE ", logic.state)
			"waitview":
				var w := 0.0
				while c.current() != p[1] and w < float(p[2]):
					await _settle(0.1)
					w += 0.1
			"quit": break
