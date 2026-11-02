extends Node
## QA: the walking and look-around demo of version 1.1 (Chapter 2 expansion): a look-around drag, tap-to-go glides with
## footsteps, a walk through a door, up a stair and down in the book lift. Every step is a tap or a drag on the real scene.
## Run (movie): xvfb-run -a godot --path game --write-movie /tmp/nav.avi --fixed-fps 30 --resolution 1280x720 res://qa/nav_demo.tscn
## Run (stills): xvfb-run -a godot --path game res://qa/nav_demo.tscn -- --out=<dir> [--calm]
var room: Node3D
var out_dir := ""
var shots := 0
var zoom_only := false
var aim_only := false


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		if a == "--aimcheck":
			aim_only = true
		if a == "--zoom":
			zoom_only = true
		if a == "--calm":
			Settings.set_value("reduce_motion", true)
	GameState.variant_seed = 0
	SaveSystem.save_path = "user://qa_nav_save_%d.json" % OS.get_process_id()
	SaveSystem.profile_path = "user://qa_nav_profile_%d.json" % OS.get_process_id()
	GameState.profile = {"choices": {"ch1_lens": "leave_lens", "ch1_shards": 5}}
	GameState.start_new("ch2")
	var al := GameState.logic as ArchiveLogic
	al.begin_expansion(2)
	al.setup_from_profile(GameState.profile.get("choices", {}))
	al.apply_seed(int(al.state["seed"]))
	al.state["pump_open"] = true # the doors the demo walks through are open
	al.state["wedge_out"] = true
	al.state["lift_ok"] = true
	al.state["panel_found"] = true
	room = (load("res://src/rooms/archive/archive.tscn") as PackedScene).instantiate()
	room.set("capture_mode", true)
	get_tree().root.add_child.call_deferred(room)
	await _wait(1.5)
	if aim_only:
		await _aim_check()
	elif zoom_only:
		await _zoom_reader()
	else:
		await _script()
	print("QA_DONE exit=0")
	get_tree().quit()


func cam() -> RoomCamera:
	return room.get("cam")


func zones() -> ArchiveZones:
	return room.get("zones")


func _wait(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()


func _idle() -> void:
	await _wait(0.1)
	var g := 0.0
	while (cam().transitioning or zones().moving) and g < 8.0:
		await _wait(0.1)
		g += 0.1


func _shot(name: String) -> void:
	if out_dir == "" or DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	shots += 1
	DirAccess.make_dir_recursive_absolute(out_dir)
	get_viewport().get_texture().get_image().save_png("%s/%02d_%s.png" % [out_dir, shots, name])


## One finger drags the view: `dyaw` / `dpitch` degrees over `secs`, released with the swipe's glide.
func _drag(dyaw: float, dpitch: float, secs: float) -> void:
	var sens := 0.16 * float(Settings.get_value("look_sensitivity"))
	var frames := maxi(2, int(secs * 30.0))
	var pos := get_viewport().get_visible_rect().size * 0.5
	room.call("_on_drag_started", pos)
	for i in frames:
		var k0 := float(i) / frames
		var k1 := float(i + 1) / frames
		var e0 := k0 * k0 * (3.0 - 2.0 * k0) # smoothstep: the finger speeds up and slows down
		var e1 := k1 * k1 * (3.0 - 2.0 * k1)
		var rel := Vector2(-(dyaw * (e1 - e0)) / sens, -(dpitch * (e1 - e0)) / sens)
		pos += rel
		room.call("_on_drag", rel, pos)
		await get_tree().process_frame
	cam().release()
	room.touch.drag_ended.emit(pos)


## The yaw / pitch that puts a tap body of `hotspot` (part `part`, "" = any) in the middle of the screen.
func _aim_for(hotspot: String, part: String) -> Vector2:
	var b := _body(hotspot, part)
	if b == null:
		return Vector2(cam().yaw, cam().pitch)
	var target := _centre(b)
	var c := cam()
	var y0 := c.yaw
	var p0 := c.pitch
	var centre := get_viewport().get_visible_rect().size * 0.5
	var best := INF
	var out := Vector2(y0, p0)
	for yaw in range(-180, 180, 5):
		for pitch in [-10.0, 0.0, 10.0]:
			c.yaw = float(yaw)
			c.pitch = pitch
			c.call("_apply_free_look")
			if c.is_position_behind(target):
				continue
			var d := c.unproject_position(target).distance_to(centre)
			if d < best:
				best = d
				out = Vector2(yaw, pitch)
	c.yaw = y0
	c.pitch = p0
	c.call("_apply_free_look")
	return out


## Where a tap on the part lands: the middle of its mesh when the collider hangs under one (a door's origin is its hinge).
func _centre(b: StaticBody3D) -> Vector3:
	var p := b.get_parent()
	if p is MeshInstance3D:
		var mi := p as MeshInstance3D
		return mi.global_transform * mi.get_aabb().get_center()
	return b.global_position


func _body(hotspot: String, part: String) -> StaticBody3D:
	for n in room.find_children("*", "StaticBody3D", true, false):
		var b := n as StaticBody3D
		if b.collision_layer == 0 or not b.is_visible_in_tree():
			continue
		if str(b.get_meta("hotspot", "")) != hotspot and str((b.get_parent() as Node).get_meta("hotspot", "")) != hotspot:
			continue
		if part == "" or str(b.get_meta("part", "")) == part:
			return b
	return null


## Look round to the part (a drag), then tap it.
func _tap(hotspot: String, part: String = "") -> void:
	await _idle()
	if cam().is_root():
		var a := _aim_for(hotspot, part)
		await _drag(wrapf(a.x - cam().yaw, -180.0, 180.0), a.y - cam().pitch, 0.9)
		await _wait(0.5)
	var b := _body(hotspot, part)
	if b == null:
		print("nav_demo: no tap body for ", hotspot, "/", part)
		return
	var sp := cam().unproject_position(_centre(b))
	room.call("_on_tap", sp)
	await _wait(0.1)


func _script() -> void:
	var al := GameState.logic as ArchiveLogic
	await _shot("hall_start")
	# 1. look around the hall (a one-finger drag, eased back to nothing by the swipe's glide)
	await _drag(-28.0, 3.0, 0.8)
	await _wait(0.4)
	await _drag(52.0, -3.0, 1.2)
	await _wait(0.4)
	# 2. tap the service door: the camera glides to it, a second tap walks through the doorway
	await _tap("east_wall", "IA_service_door")
	await _idle()
	await _shot("hall_door_view")
	await _tap("east_wall", "IA_service_door")
	await _wait(0.45)
	await _shot("door_walk_mid")
	await _idle()
	await _wait(0.3)
	await _shot("pump_arrived")
	# 3. look around the Pump Room
	await _drag(40.0, 0.0, 1.0)
	await _wait(0.3)
	await _drag(-55.0, 4.0, 1.2)
	await _wait(0.3)
	# 4. the stair back up to the hall
	await _tap("pump_stair")
	await _wait(0.5)
	await _shot("stair_mid")
	await _idle()
	await _wait(0.4)
	# 5. the stair stump: a glide to it, then the climb to the Gallery
	await _tap("stair_stump")
	await _idle()
	await _tap("stair_stump")
	await _idle()
	await _wait(0.3)
	await _shot("gallery_arrived")
	# 6. the Plate Room door and back
	await _tap("gal_door_plate")
	await _wait(0.5)
	await _shot("gallery_door_walk")
	await _idle()
	await _wait(0.5)
	await _tap("plate_door")
	await _idle()
	await _wait(0.3)
	# 7. the book lift down to the Pump Room
	var g: Object = zones().builder("gallery")
	if g != null and g.get("lift") != null:
		(g.get("lift") as ArchiveLift).press(-1, "IA_btn_flask")
	var t := 0.0
	while al.state["room"] != "pump" and t < 8.0:
		await _wait(0.1)
		t += 0.1
	await _wait(0.5)
	await _shot("lift_mid")
	await _idle()
	await _wait(0.8)
	await _shot("pump_after_lift")


## The enlarger print as the zoom reader shows it (tap the projected image): the four digits must read at once.
func _zoom_reader() -> void:
	var al := GameState.logic as ArchiveLogic
	var st: Dictionary = al.state
	zones().jump("plate")
	st["room"] = "plate"
	st["en_strip"] = st["v_strip"]
	st["en_zoom"] = st["v_zoom"]
	st["en_focus"] = st["v_pfocus"]
	zones().apply_state(false)
	await _wait(0.5)
	var pl: Object = zones().builder("plate")
	var tex: Texture2D = (pl.get("_proj_mat") as StandardMaterial3D).albedo_texture
	room.get("hud").call("_show_zoom", tex, room.tr("obj2x.enlarger"))
	await _wait(0.8)
	await _shot("enlarger_zoom_reader")


## Does one aim at a door reach it? For each door: jump to the room's root view, aim (the nearest of a 10 degree yaw grid, as
## the playthrough does), tap the middle of the door and report what the tap resolves to.
func _aim_check() -> void:
	var rows := [["plate", "plate_door", "IA_door_gallery"], ["gallery", "gal_door_plate", "IA_door_plate"],
		["gallery", "gal_door_office", "IA_door_office"], ["office", "off_door", "IA_door_gallery"], ["pump", "pump_door", "IA_door_cell"]]
	var bad := 0
	for r: Array in rows:
		zones().jump(r[0])
		await _wait(0.4)
		var a := _aim_for(r[1], r[2])
		cam().yaw = a.x
		cam().pitch = a.y
		cam().call("_apply_free_look")
		await _wait(0.3)
		var b := _body(r[1], r[2])
		var sp := cam().unproject_position(_centre(b)) if b != null else Vector2(-1, -1)
		var hit: Dictionary = room.call("raycast", sp)
		var res: Dictionary = room.call("resolve", hit) if not hit.is_empty() else {}
		var ok: bool = (not res.is_empty()) and str(res["hotspot"]) == str(r[1])
		bad += 0 if ok else 1
		print("aimcheck %s/%s: yaw %d pitch %d, screen %s, fov %.0f, hit %s -> %s" % [r[0], r[2], a.x, a.y, str(sp), cam().fov, str(res.get("hotspot", "nothing")) + "/" + str(res.get("part", "")), "OK" if ok else "MISS"])
	print("aimcheck: %d misses" % bad)
