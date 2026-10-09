extends Node
## QA "tap map": renders camera views of a real chapter room and marks every tappable part in view.
## It taps a 5×5 grid over the part's own screen area through the room's raycast and colours the mark:
##   green  = at least 3 sample points reach the part;
##   orange = only 1–2 do (a small or mostly covered target);
##   red    = none do; the part most often hit instead is named.
## Run: xvfb-run -a godot --path game res://qa/tap_map.tscn -- --chapter=ch2 --views=cat_drawer,splicer --out=<dir>
##        [--steps=N] (solver steps first) [--do=open_cat_drawer:4,pick_divider:1] (logic calls with int args)
##        [--until=booth_open] (solver steps until that state key is true) [--lens=take|leave]
##        [--perf] (no tap marks: log draw calls / primitives / objects per view instead)
## Writes <view>.png and tap_map.txt (one line per orange or red part).

var out_dir := "/tmp/tap_map"
var room: Node3D
var lines: Array[String] = []


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	var chapter := "ch2"
	var views: PackedStringArray = []
	var steps := 0
	var calls: PackedStringArray = []
	var lens := "leave"
	var until := ""
	GameState.variant_seed = 0 # canonical answers unless --seed=N (players get a random seed per game)
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--chapter="):
			chapter = a.substr(10)
		elif a.begins_with("--views="):
			views = a.substr(8).split(",", false)
		elif a.begins_with("--steps="):
			steps = int(a.substr(8))
		elif a.begins_with("--do="):
			calls = a.substr(5).split(",", false)
		elif a.begins_with("--lens="):
			lens = a.substr(7)
		elif a.begins_with("--until="):
			until = a.substr(8)
		elif a.begins_with("--seed="):
			GameState.variant_seed = int(a.substr(7))
	DirAccess.make_dir_recursive_absolute(out_dir)
	SaveSystem.save_path = "user://qa_tapmap_save.json"
	SaveSystem.profile_path = "user://qa_tapmap_profile.json"
	GameState.profile = {"choices": {"ch1_lens": "take_lens" if lens == "take" else "leave_lens", "ch1_shards": 5}}
	GameState.start_new(chapter)
	var logic := GameState.logic
	for i in steps:
		if chapter == "ch2":
			ArchiveSolver.step(logic as ArchiveLogic, "leyla_key")
		else:
			Lab7Solver.step(logic as Lab7Logic, "leave_lens")
	var guard := 0
	while until != "" and not bool(logic.state.get(until, false)) and guard < 600:
		guard += 1
		if chapter == "ch2":
			ArchiveSolver.step(logic as ArchiveLogic, "leyla_key")
		else:
			Lab7Solver.step(logic as Lab7Logic, "leave_lens")
	for c in calls:
		var parts := c.split(":")
		var args: Array = []
		for k in range(1, parts.size()):
			args.append(int(parts[k]))
		logic.callv(parts[0], args)
	var scene := "res://src/rooms/archive/archive.tscn" if chapter == "ch2" else "res://src/rooms/lab7/lab7.tscn"
	room = (load(scene) as PackedScene).instantiate()
	room.set("capture_mode", true)
	get_tree().root.add_child(room)
	await _settle(1.5)
	var cam: RoomCamera = room.get("cam")
	var perf_only := OS.get_cmdline_user_args().has("--perf")
	for v in views:
		if room.has_method("prepare_view"):
			room.call("prepare_view", v)
		cam.go(v, true)
		await _settle(0.9)
		if perf_only:
			await RenderingServer.frame_post_draw
			lines.append("perf[%s]: draw calls %d, primitives %d, objects %d" % [v,
				RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
				RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),
				RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME)])
			get_viewport().get_texture().get_image().save_png("%s/%s.png" % [out_dir, v]) # a clean shot, no marks
			continue
		await _map(v)
	var f := FileAccess.open(out_dir + "/tap_map.txt", FileAccess.WRITE)
	f.store_string("\n".join(lines) + "\n")
	print("\n".join(lines))
	SaveSystem.delete_game()
	print("QA_DONE exit=0") # tools/qa_run.sh: the run finished even if the process then hangs on exit
	get_tree().quit()


func _settle(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()


func _map(view_id: String) -> void:
	var cam: Camera3D = room.get("cam")
	var rect := get_viewport().get_visible_rect()
	var marks: Array[Dictionary] = []
	for body in room.find_children("*", "StaticBody3D", true, false):
		var b := body as StaticBody3D
		if b.collision_layer == 0 or not b.is_visible_in_tree():
			continue
		var part := str(b.get_meta("part", ""))
		if part == "":
			continue
		var mi := b.get_parent() as MeshInstance3D
		var r := _screen_rect(cam, mi) if mi != null and mi.mesh != null else Rect2()
		if r.size == Vector2.ZERO or not rect.intersects(r):
			continue
		# sample the part's own screen area like a player tapping what they see
		var hits := 0
		var total := 0
		var centroid := Vector2.ZERO
		var others: Dictionary = {}
		var inner := r.grow_individual(-r.size.x * 0.1, -r.size.y * 0.1, -r.size.x * 0.1, -r.size.y * 0.1)
		for gy in 5:
			for gx in 5:
				var sp := inner.position + inner.size * Vector2((gx + 0.5) / 5.0, (gy + 0.5) / 5.0)
				if not rect.has_point(sp):
					continue
				total += 1
				var hit: Dictionary = room.call("raycast", sp)
				var got := "" if hit.is_empty() else str(room.call("resolve", hit)["part"])
				if got == part:
					hits += 1
					centroid += sp
				else:
					others[got] = int(others.get(got, 0)) + 1
		if total == 0:
			continue
		# a far part hidden behind walls or furniture is simply not in view: skip it, so the report lists only
		# parts a player could aim at (a near part blocked by scenery is still reported)
		if hits == 0 and others.keys() == [""] and cam.global_position.distance_to(mi.global_position) > 1.2:
			continue
		var pos := centroid / hits if hits > 0 else r.get_center()
		var top := ""
		var best := 0
		for k: String in others:
			if int(others[k]) > best:
				best = int(others[k])
				top = k
		# parts that carry a 3D label (card tabs, divider tabs): the label is where a player taps
		for lbl in mi.find_children("*", "Label3D", false, false):
			var lp := (lbl as Node3D).global_position
			if cam.is_position_behind(lp) or not rect.has_point(cam.unproject_position(lp)):
				continue
			var lh: Dictionary = room.call("raycast", cam.unproject_position(lp))
			var lgot := "" if lh.is_empty() else str(room.call("resolve", lh)["part"])
			if lgot != part:
				lines.append("%s: tapping the label «%s» of %s hits %s" % [view_id, (lbl as Label3D).text, part,
					lgot if lgot != "" else "(nothing)"])
			elif hits < 3:
				hits = 3 # its label is a sure target, even if most of its body is covered
		marks.append({"pos": pos, "part": part, "hits": hits, "got": top})
		if hits < 3:
			lines.append("%s: %s reachable at %d/%d sample points (mostly hits %s)" % [view_id, part, hits, total,
				top if top != "" else "(nothing)"])
	var layer := CanvasLayer.new()
	layer.layer = 100
	var canvas := _Marks.new()
	canvas.marks = marks
	canvas.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(canvas)
	add_child(layer)
	await _settle(0.3)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("%s/%s.png" % [out_dir, view_id])
	layer.queue_free()


func _screen_rect(cam: Camera3D, mi: MeshInstance3D) -> Rect2:
	var ab := mi.mesh.get_aabb()
	var r := Rect2()
	for k in 8:
		var wp := mi.global_transform * ab.get_endpoint(k)
		if cam.is_position_behind(wp):
			return Rect2()
		var sp := cam.unproject_position(wp)
		r = Rect2(sp, Vector2.ZERO) if k == 0 else r.expand(sp)
	return r


class _Marks extends Control:
	var marks: Array[Dictionary] = []

	func _draw() -> void:
		var font := ThemeDB.fallback_font
		for m: Dictionary in marks:
			var h: int = m["hits"]
			var c := Color(0.2, 1.0, 0.35) if h >= 3 else (Color(1.0, 0.7, 0.1) if h > 0 else Color(1.0, 0.25, 0.2))
			draw_circle(m["pos"], 5.0, c)
			var label: String = str(m["part"]).replace("IA_", "")
			if h < 3:
				label += " %d→%s" % [h, str(m["got"]).replace("IA_", "")]
			draw_string(font, m["pos"] + Vector2(7, 4), label, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, c)
