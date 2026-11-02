extends Node
## QA: renders camera views of the real Lab 7 scene without playing (for framing/lighting work).
## Run: xvfb-run -a godot --path game res://qa/view_probe.tscn -- --out=<dir> [--from=p9]
##        [--echo [--headyaw=-55]] [--hide=cc_bust] [--views=coat,radiator] [--cam=name:x,y,z:tx,ty,tz:fov ...] [--select=uv_lamp]
## --from=pN lets the solver play the puzzles before N first (e.g. to see the open bookcase).

var out_dir := "/tmp"


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	var views: PackedStringArray = []
	var cams: Array[String] = []
	var from := 1
	var select := ""
	var head_yaw := -55.0 # --headyaw=N: how far Leyla turns her head (the finale turns her -55)
	var hide_models: PackedStringArray = [] # --hide=cc_bust,...: model ids hidden for a cleaner frame (store art)
	var echo_on := false # --echo: the Chapter 1 finale's 1979 flashback look (warm room, Leyla's echo at the desk)
	GameState.variant_seed = 0 # canonical answers unless --seed=N (players get a random seed per game)
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--views="):
			views = a.substr(8).split(",", false)
		elif a.begins_with("--cam="):
			cams.append(a.substr(6))
		elif a.begins_with("--from=p"):
			from = int(a.substr(8))
		elif a.begins_with("--seed="):
			GameState.variant_seed = int(a.substr(7))
		elif a.begins_with("--hide="):
			hide_models = a.substr(7).split(",", false)
		elif a.begins_with("--headyaw="):
			head_yaw = float(a.substr(10))
		elif a == "--echo":
			echo_on = true
		elif a.begins_with("--select="):
			select = a.substr(9)
	DirAccess.make_dir_recursive_absolute(out_dir)
	SaveSystem.save_path = "user://qa_probe_save_%d.json" % OS.get_process_id()
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
	for h in hide_models:
		var hm: Node3D = room.get("models").get(h)
		if hm:
			hm.visible = false
	if echo_on:
		_flashback(room, head_yaw)
		await _settle(0.6)
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
	print("QA_DONE exit=0") # tools/qa_run.sh: the run finished even if the process then hangs on exit
	get_tree().quit()


func _flashback(room: Node3D, head_yaw: float = -55.0) -> void:
	var env: Environment = room.get("env")
	env.ambient_light_color = Color("6a5034")
	env.ambient_light_energy = 1.1
	var lights: Dictionary = room.get("lights")
	lights["desk_lamp"].light_energy = 2.6
	room.get("visuals").call("flashback_1979", true)
	var echo: Node3D = room.get("models").get("echo_leyla")
	echo.visible = true
	var head := ModelUtil.find(echo, "echo_head")
	if head:
		head.rotation.y = deg_to_rad(head_yaw) # she turns to look at the player
	var hud: Node = room.get("hud")
	if hud is CanvasItem or hud is CanvasLayer:
		hud.set("visible", false) # clean frames for store art
	for mi in ModelUtil.find_meshes(echo):
		var m := mi.material_override as ShaderMaterial
		if m and m.next_pass is ShaderMaterial:
			m = m.next_pass as ShaderMaterial
		if m:
			m.set_shader_parameter("intensity", 1.0)


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
	print("shot ", p, "  draw calls ", RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME))
