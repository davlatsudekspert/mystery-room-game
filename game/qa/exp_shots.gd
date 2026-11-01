extends Node
## QA for the Chapter 2 expansion's scene (docs/CHAPTER2_EXPANSION.md): builds a NEW expansion game, brings it to a state
## with the logic's solver, loads the real Archive scene and photographs views of the expansion's rooms.
## Run: xvfb-run -a godot --path game res://qa/exp_shots.tscn -- --out=<dir> --views=pump,manifold,boiler,pipes
##        [--stage=0|1|2] [--until=pump_open] [--do=n2_toggle_valve:0,...] [--item=mallet,...] [--room=pump] [--lang=ru]
##        [--seed=N] [--size=2400x1080] [--perf] (draw calls per view) [--plan] (also the floor-plan overlay)
##        [--select=item] (the item in hand) [--moments=full]
## Views of any zone work (the scene builds and shows the zone first, as prepare_view does for the other QA tools).
## Exit 0 when every view was photographed; a line per view with draw calls when --perf.

var out_dir := "/tmp/exp_shots"
var room: Node3D
var lines: Array[String] = []


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	var views: PackedStringArray = []
	var stage := 2
	var until := ""
	var calls: PackedStringArray = []
	var items: PackedStringArray = []
	var to_room := ""
	var perf := false
	var plan := false
	var bag := false
	var select := ""
	var probe := ""
	var tapat := ""
	var cams: Array[String] = []
	GameState.variant_seed = 0
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--views="):
			views = a.substr(8).split(",", false)
		elif a.begins_with("--stage="):
			stage = int(a.substr(8))
		elif a.begins_with("--until="):
			until = a.substr(8)
		elif a.begins_with("--do="):
			calls = a.substr(5).split(",", false)
		elif a.begins_with("--item="):
			items = a.substr(7).split(",", false)
		elif a.begins_with("--room="):
			to_room = a.substr(7)
		elif a.begins_with("--lang="):
			TranslationServer.set_locale(a.substr(7))
		elif a.begins_with("--seed="):
			GameState.variant_seed = int(a.substr(7))
		elif a.begins_with("--size="):
			var wh := a.substr(7).split("x")
			get_window().size = Vector2i(int(wh[0]), int(wh[1]))
		elif a.begins_with("--select="):
			select = a.substr(9)
		elif a.begins_with("--moments="):
			Settings.values["moments"] = a.substr(10)
		elif a.begins_with("--cam="):
			cams.append(a.substr(6)) # name:x,y,z:tx,ty,tz:fov (a view added for this run)
		elif a.begins_with("--tapat="):
			tapat = a.substr(8) # x,y,z in the zone of --room: after the last view, what a tap on that point would hit
		elif a.begins_with("--probe="):
			probe = a.substr(8) # x0,x1,y,z0,z1: rays along x at 0.2 m steps in z (what a tap there would hit)
		elif a == "--perf":
			perf = true
		elif a == "--plan":
			plan = true
		elif a == "--bag":
			bag = true
	DirAccess.make_dir_recursive_absolute(out_dir)
	SaveSystem.save_path = "user://qa_exp_save_%d.json" % OS.get_process_id()
	SaveSystem.profile_path = "user://qa_exp_profile_%d.json" % OS.get_process_id()
	GameState.profile = {"choices": {"ch1_lens": "leave_lens", "ch1_shards": 5}}
	GameState.start_new("ch2")
	var l := GameState.logic as ArchiveLogic
	if stage == 0:
		l.make_legacy() # the 1.0 hall, for the draw-call comparison
	else:
		l.begin_expansion(stage)
	l.setup_from_profile(GameState.profile.get("choices", {}))
	l.apply_seed(int(l.state["seed"]))
	var guard := 0
	while until != "" and not bool(l.state.get(until, false)) and guard < 800:
		guard += 1
		ArchiveSolver.step(l, "leyla_key")
		ArchiveSolver.lower_floor(l)
	for c in calls:
		var parts := c.split(":")
		var args: Array = []
		for k in range(1, parts.size()):
			args.append(int(parts[k]) if parts[k].is_valid_int() else parts[k])
		l.callv(parts[0], args)
	for it in items:
		if not l.has_item(it):
			l.inventory.append(it)
	if select != "":
		l.select_item(select)
	room = (load("res://src/rooms/archive/archive.tscn") as PackedScene).instantiate()
	room.set("capture_mode", true)
	get_tree().root.add_child(room)
	await _settle(1.5)
	var cam: RoomCamera = room.get("cam")
	var zones: ArchiveZones = room.get("zones")
	if to_room != "":
		zones.jump(to_room)
		await _settle(1.0)
	for o in cams: # after the room is built, so a zone's own add_view of the same name does not replace it
		var f := o.split(":")
		var p := f[1].split(",")
		var t := f[2].split(",")
		cam.add_view(f[0], Vector3(float(p[0]), float(p[1]), float(p[2])), Vector3(float(t[0]), float(t[1]), float(t[2])), float(f[3]))
	for v in views:
		room.call("prepare_view", v)
		cam.go(v, true)
		await _settle(1.2)
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("%s/%s.png" % [out_dir, v])
		lines.append("shot %s.png" % v)
		if perf:
			lines.append("perf[%s]: draw calls %d, primitives %d, objects %d" % [v,
				RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
				RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),
				RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME)])
	if tapat != "" and zones.zones.has(to_room):
		var tf := tapat.split(",")
		var zo := (zones.zones[to_room]["root"] as Node3D).global_position
		var sp := cam.unproject_position(zo + Vector3(float(tf[0]), float(tf[1]), float(tf[2])))
		var th: Dictionary = room.call("raycast", sp)
		var pk: Dictionary = room.call("pick", sp)
		lines.append("tapat %s -> screen %d,%d; ray %s; pick %s" % [tapat, int(sp.x), int(sp.y),
			str(room.call("resolve", th)) if not th.is_empty() else "nothing", str(room.call("resolve", pk)) if not pk.is_empty() else "nothing"])
	if probe != "":
		var f := probe.split(",")
		var space := room.get_world_3d().direct_space_state
		var z := float(f[3])
		while z <= float(f[4]):
			var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(float(f[0]), float(f[2]), z), Vector3(float(f[1]), float(f[2]), z)))
			if h.is_empty():
				lines.append("probe z=%.2f: nothing" % z)
			else:
				var col: Node = h["collider"]
				lines.append("probe z=%.2f: x=%.2f %s part=%s" % [z, (h["position"] as Vector3).x, col.get_parent().get_path(), str(col.get_meta("part", ""))])
			z += float(f[5]) if f.size() > 5 else 0.2
	if bag: # the bag open: every item's icon (a model that is missing shows its name and warns)
		(room.get("hud") as Node).call("set_bag_open", true)
		await _settle(3.0)
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("%s/bag.png" % out_dir)
		lines.append("shot bag.png")
	if plan:
		(room.get("hud") as Node).call("show_plan")
		await _settle(1.0)
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("%s/plan.png" % out_dir)
		lines.append("shot plan.png")
	print("\n".join(lines))
	SaveSystem.delete_game()
	print("QA_DONE exit=0")
	get_tree().quit(0)


func _settle(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()
