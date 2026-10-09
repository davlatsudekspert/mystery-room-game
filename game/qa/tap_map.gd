extends Node
## QA "tap map": renders camera views of a real chapter room and marks every tappable part in view.
## For each part it taps the projected centre of its collider through the room's own raycast and colours the mark:
##   green  = the tap reaches this part;
##   red    = the tap lands on another part (named on the image) — a player aiming at it would hit that instead;
##   grey   = the centre is off-screen or behind the camera.
## Run: xvfb-run -a godot --path game res://qa/tap_map.tscn -- --chapter=ch2 --views=cat_drawer,splicer --out=<dir>
##        [--steps=N] (solver steps first) [--do=open_cat_drawer:4,pick_divider:1] (logic calls with int args)
##        [--until=booth_open] (solver steps until that state key is true) [--lens=take|leave]
## Writes <view>.png and tap_map.txt (one line per red or grey part).

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
	for v in views:
		cam.go(v, true)
		await _settle(0.9)
		await _map(v)
	var f := FileAccess.open(out_dir + "/tap_map.txt", FileAccess.WRITE)
	f.store_string("\n".join(lines) + "\n")
	print("\n".join(lines))
	SaveSystem.delete_game()
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
		# the visible middle of the part: its mesh bounds (trimesh colliders sit at the mesh origin)
		var p := b.global_position
		var mi := b.get_parent() as MeshInstance3D
		if mi != null and mi.mesh != null:
			p = mi.global_transform * mi.mesh.get_aabb().get_center()
		elif b.get_child_count() > 0 and b.get_child(0) is Node3D:
			p = (b.get_child(0) as Node3D).global_position
		if cam.is_position_behind(p) or cam.global_position.distance_to(p) > 6.0:
			continue
		var sp := cam.unproject_position(p)
		if not rect.has_point(sp):
			continue
		var hit: Dictionary = room.call("raycast", sp)
		var got := ""
		if not hit.is_empty():
			got = str(room.call("resolve", hit)["part"])
		var ok := got == part
		marks.append({"pos": sp, "part": part, "ok": ok, "got": got})
		if not ok:
			lines.append("%s: %s → %s" % [view_id, part, got if got != "" else "(nothing)"])
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


class _Marks extends Control:
	var marks: Array[Dictionary] = []

	func _draw() -> void:
		var font := ThemeDB.fallback_font
		for m: Dictionary in marks:
			var c := Color(0.2, 1.0, 0.35) if m["ok"] else Color(1.0, 0.25, 0.2)
			draw_circle(m["pos"], 6.0, c)
			var label: String = m["part"] if m["ok"] else "%s→%s" % [m["part"], m["got"]]
			draw_string(font, m["pos"] + Vector2(8, 4), label.replace("IA_", ""), HORIZONTAL_ALIGNMENT_LEFT, -1, 13, c)
