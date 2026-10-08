extends Node
## QA: renders camera views of the real Lab 7 scene without playing (for framing/lighting work).
## Run: xvfb-run -a godot --path game res://qa/view_probe.tscn -- --out=<dir> [--from=p9]
##        [--views=coat,radiator] [--cam=name:x,y,z:tx,ty,tz:fov ...] [--select=uv_lamp]
## --from=pN lets the solver play the puzzles before N first (e.g. to see the open bookcase).

var out_dir := "/tmp"


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	var views: PackedStringArray = []
	var cams: Array[String] = []
	var from := 1
	var select := ""
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--views="):
			views = a.substr(8).split(",", false)
		elif a.begins_with("--cam="):
			cams.append(a.substr(6))
		elif a.begins_with("--from=p"):
			from = int(a.substr(8))
		elif a.begins_with("--select="):
			select = a.substr(9)
	SaveSystem.save_path = "user://qa_probe_save.json"
	GameState.start_new("ch1")
	var logic := GameState.logic as Lab7Logic
	var guard := 0
	while from > 1 and guard < 200 and not _reached(logic, from):
		guard += 1
		Lab7Solver.step(logic, "leave_lens")
	var room: Node3D = (load("res://src/rooms/lab7/lab7.tscn") as PackedScene).instantiate()
	room.set("capture_mode", true)
	get_tree().root.add_child(room)
	await _settle(1.5)
	if select != "":
		logic.select_item(select)
	var cam: RoomCamera = room.get("cam")
	for v in views:
		cam.go(v, true)
		await _settle(0.8)
		await _shot("view_" + v)
	for spec in cams:
		var p := spec.split(":")
		if p.size() < 3:
			continue
		var pos := _vec(p[1])
		var target := _vec(p[2])
		var fov := float(p[3]) if p.size() > 3 else 50.0
		cam.add_view("probe_" + p[0], pos, target, fov)
		cam.go("probe_" + p[0], true)
		await _settle(0.8)
		await _shot("cam_" + p[0])
	SaveSystem.delete_game()
	get_tree().quit()


func _reached(l: Lab7Logic, k: int) -> bool:
	var s := l.state
	var keys := {2: "drawer_open", 4: "uv_page", 6: "compartment_open", 7: "power_on", 9: "signal_heard",
		10: "shelf_open", 11: "emblem_recorded", 12: "beam_on", 13: "door_open"}
	return bool(s.get(keys.get(k, "complete"), false))


func _vec(t: String) -> Vector3:
	var c := t.split(",")
	return Vector3(float(c[0]), float(c[1]), float(c[2]))


func _settle(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var p := "%s/%s.png" % [out_dir, name]
	get_viewport().get_texture().get_image().save_png(p)
	print("shot ", p)
