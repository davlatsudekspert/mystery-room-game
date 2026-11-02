extends Node
## Promo capture for the Chapter 2 expansion (promo/v1_1/README.md): a NEW expansion game with a given seed, brought to a state by the
## project's own solver (tests/archive_solver.gd), the real Archive scene, then a step script (camera views, walks through doors by
## real taps on the door parts, waits) so Godot's movie writer can record real footage. Not part of the game; lives in the scratch project.
## godot --path <pg> --write-movie clip.avi --fixed-fps 30 res://qa/promo_ch2.tscn -- --seed=9137 --until=pump_open --room=hall \
##   --steps="go:east_south;wait:2;tap:service_door:IA_service_door;waitroom:pump:8;wait:2" [--hud=0] [--keep=width] [--lang=ru]
## Steps (";"): go:<view>[:i] | jump:<room> | wait:<s> | yaw:<deg>:<s> | pitch:<deg>:<s> | keep:width|height | fov:<deg> | hud:on|off |
##   tap:<model>:<part> | tapat:<room>:x,y,z (zone coordinates) | waitroom:<room>:<max s> | plan | planclose | logic:<fn>:<args..> | cam:<view>:<x,y,z>:<tx,ty,tz>:<fov> | quit

var room: Node3D
var logic: ArchiveLogic
var steps := ""
var yaw_rate := 0.0
var yaw_left := 0.0
var pitch_rate := 0.0
var pitch_left := 0.0


func _ready() -> void:
	var until := ""
	var to_room := ""
	var show_hud := true
	var keep := ""
	GameState.variant_seed = 0
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--seed="):
			GameState.variant_seed = int(a.substr(7))
		elif a.begins_with("--until="):
			until = a.substr(8)
		elif a.begins_with("--room="):
			to_room = a.substr(7)
		elif a.begins_with("--steps="):
			steps = a.substr(8)
		elif a.begins_with("--hud="):
			show_hud = a.substr(6) != "0"
		elif a.begins_with("--keep="):
			keep = a.substr(7)
		elif a.begins_with("--lang="):
			TranslationServer.set_locale(a.substr(7))
	SaveSystem.save_path = "user://qa_promo_save_%d.json" % OS.get_process_id()
	SaveSystem.profile_path = "user://qa_promo_profile_%d.json" % OS.get_process_id()
	GameState.qa_no_tips = true
	GameState.profile = {"choices": {"ch1_lens": "leave_lens", "ch1_shards": 5}}
	GameState.start_new("ch2")
	logic = GameState.logic as ArchiveLogic
	logic.begin_expansion(2)
	logic.setup_from_profile(GameState.profile.get("choices", {}))
	logic.apply_seed(int(logic.state["seed"]))
	var guard := 0
	while until != "" and not bool(logic.state.get(until, false)) and guard < 900:
		guard += 1
		ArchiveSolver.step(logic, "leyla_key")
		ArchiveSolver.lower_floor(logic)
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
	if to_room != "" and to_room != "hall":
		(room.get("zones") as ArchiveZones).jump(to_room)
	if "--music=0" in OS.get_cmdline_user_args(): # the music bed is added in the edit; the take keeps ambience and effects
		AudioServer.set_bus_mute(AudioServer.get_bus_index("Music"), true)
	await _settle(1.2)
	print("PROMO_START frame=", Engine.get_process_frames())
	await run_steps()
	print("PROMO_DONE frame=", Engine.get_process_frames())
	SaveSystem.delete_game()
	get_tree().quit(0)


func _settle(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()


func cam() -> RoomCamera:
	return room.get("cam")


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


# tap helpers: the same geometry as qa/playthrough_ch2.gd (the part's screen box, then a point of it that really resolves to the part)
func node_of(model: String, part: String) -> Node3D:
	var root: Node3D = (room.get("models") as Dictionary).get(model)
	if root == null:
		return null
	return root if part == "" else ModelUtil.find(root, part)


func _rect(n: Node3D, own_only: bool) -> Rect2:
	var meshes := ModelUtil.find_meshes(n)
	if own_only and n is MeshInstance3D:
		meshes = [n as MeshInstance3D]
	var r := Rect2()
	var first := true
	for mi in meshes:
		if not mi.is_visible_in_tree() and not own_only:
			continue
		var ab := mi.get_aabb()
		for k in 8:
			var wp := mi.global_transform * ab.get_endpoint(k)
			if cam().is_position_behind(wp):
				if own_only:
					return Rect2()
				continue
			var sp := cam().unproject_position(wp)
			if first:
				r = Rect2(sp, Vector2.ZERO)
				first = false
			else:
				r = r.expand(sp)
	return r


func _resolves_to(sp: Vector2, part: String) -> bool:
	var h: Dictionary = room.call("raycast", sp)
	return not h.is_empty() and str(room.call("resolve", h)["part"]) == part


func _tap_point(model: String, part: String) -> Vector2:
	var n := node_of(model, part)
	if n == null:
		return Vector2(-1, -1)
	var r := _rect(n, part != "" and not part.begins_with("Item_"))
	if r.size == Vector2.ZERO:
		return Vector2(-1, -1)
	var sp := r.get_center()
	var vs := get_viewport().get_visible_rect().size
	if sp.x < 0 or sp.y < 0 or sp.x > vs.x or sp.y > vs.y:
		return Vector2(-1, -1)
	if not part.begins_with("IA_") or _resolves_to(sp, part):
		return sp
	var best := sp
	var best_d := INF
	for gy in 7:
		for gx in 7:
			var p := r.position + r.size * Vector2(0.1 + 0.8 * gx / 6.0, 0.1 + 0.8 * gy / 6.0)
			if p.x < 0 or p.y < 0 or p.x > vs.x or p.y > vs.y:
				continue
			var d := p.distance_to(r.get_center())
			if d < best_d and _resolves_to(p, part):
				best = p
				best_d = d
	return best


func run_steps() -> void:
	var zones: ArchiveZones = room.get("zones")
	for raw in steps.split(";", false):
		var p := raw.strip_edges().split(":")
		print("step ", raw, " frame=", Engine.get_process_frames())
		match p[0]:
			"go":
				room.call("prepare_view", p[1])
				cam().go(p[1], p.size() > 2 and p[2] == "i")
			"jump":
				zones.jump(p[1])
			"wait": await _settle(float(p[1]))
			"yaw":
				yaw_rate = float(p[1]) / float(p[2])
				yaw_left = absf(float(p[1]))
			"pitch":
				pitch_rate = float(p[1]) / float(p[2])
				pitch_left = absf(float(p[1]))
			"keep": cam().keep_aspect = Camera3D.KEEP_WIDTH if p[1] == "width" else Camera3D.KEEP_HEIGHT
			"fov": cam().set("_fov_goal", float(p[1]))
			"hud": (room.get("hud") as CanvasLayer).visible = p[1] == "on"
			"aimmodel": # a view straight at a model (dist m in front of it, looking +z): aimmodel:<model>:<dist>:<fov>
				var mn := node_of(p[1], "")
				var box := AABB()
				var first := true
				for mi in ModelUtil.find_meshes(mn):
					var bb: AABB = mi.global_transform * mi.get_aabb()
					box = bb if first else box.merge(bb)
					first = false
				var cc := box.get_center()
				cam().add_view("qa_aim", cc + Vector3(0, 0, -float(p[2])), cc, float(p[3]), true)
				cam().go("qa_aim", true)
			"wipe": # a finger wipe over the first frost band (as qa/playthrough_ch2.gd does it)
				var win: Node3D = node_of("cold_frost_window", "")
				var left := cam().unproject_position(win.to_global(Vector3(-0.3, 0.4, 0.02)))
				var right := cam().unproject_position(win.to_global(Vector3(0.3, 0.4, 0.02)))
				room.set("drag_pos", left)
				room.call("drag_part_started", "IA_frost")
				for pass_i in 6:
					for t in 10:
						var q := left.lerp(right, float(t) / 9.0) if pass_i % 2 == 0 else right.lerp(left, float(t) / 9.0)
						q.y += (pass_i - 2.5) * 16.0
						room.set("drag_pos", q)
						room.call("drag_part", Vector2(12, 0))
						await get_tree().process_frame
			"seen":
				for rid in logic.room_ids():
					if not (logic.state["rooms_seen"] as Array).has(rid):
						(logic.state["rooms_seen"] as Array).append(rid)
			"plan": (room.get("hud") as Node).call("show_plan")
			"planclose": (room.get("hud") as Node).call("consume_back")
			"cam":
				var a := p[2].split(",")
				var b := p[3].split(",")
				cam().add_view(p[1], Vector3(float(a[0]), float(a[1]), float(a[2])), Vector3(float(b[0]), float(b[1]), float(b[2])), float(p[4]))
			"tap":
				var sp := _tap_point(p[1], p[2])
				print("tap ", p[1], "/", p[2], " at ", sp)
				if sp.x >= 0:
					room.call("_on_tap", sp)
			"tapat":
				var ro := p[1]
				var c3 := p[2].split(",")
				var o := (zones.zones[ro]["root"] as Node3D).global_position
				var sp2 := cam().unproject_position(o + Vector3(float(c3[0]), float(c3[1]), float(c3[2])))
				print("tapat ", p[1], " ", p[2], " -> ", sp2)
				room.call("_on_tap", sp2)
			"waitroom":
				var t := 0.0
				await _settle(0.4)
				while (str(logic.state["room"]) != p[1] or zones.moving) and t < float(p[2]):
					await _settle(0.1)
					t += 0.1
				print("room now ", logic.state["room"], " after ", t)
			"logic":
				var args: Array = []
				for k in range(2, p.size()):
					args.append(int(p[k]) if p[k].is_valid_int() else p[k])
				logic.callv(p[1], args)
			"quit":
				return
