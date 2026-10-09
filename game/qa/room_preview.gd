extends Node3D
## QA: assembles the Lab 7 layout with whatever models exist and renders review screenshots.
## Missing room shell → a clearly temporary plain shell (floor + walls) so lighting can be judged.
## Run: xvfb-run godot --path game res://qa/room_preview.tscn -- --out=<dir> [--powered]

const ROOM := preload("res://src/rooms/lab7/lab7_room.gd")
var out_dir := "res://../docs/previews"
var powered := false
var tree_lines: Array[String] = []


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		if a == "--powered":
			powered = true
	DirAccess.make_dir_recursive_absolute(out_dir)
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("0b0d10")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("2f3a38") if powered else Color("26383a")
	env.ambient_light_energy = 0.55 if powered else 0.5
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.glow_enabled = true
	env.glow_hdr_threshold = 1.1
	env.adjustment_enabled = true
	env.adjustment_contrast = 1.08
	env.adjustment_saturation = 0.92
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var placed: Array[String] = []
	var missing: Array[String] = []
	for id: String in ROOM.LAYOUT:
		var e: Array = ROOM.LAYOUT[id]
		var n := ModelUtil.spawn(id, self, Transform3D(Basis(Vector3.UP, deg_to_rad(e[1])), e[0]), "none")
		if n:
			placed.append(id)
		else:
			missing.append(id)
	for id: String in ROOM.EXTRA:
		var e: Array = ROOM.EXTRA[id]
		var n := ModelUtil.spawn(e[0], self, Transform3D(Basis(Vector3.UP, deg_to_rad(e[2])), e[1]), "none")
		if n:
			n.name = id
			placed.append(id)
		else:
			missing.append(id)
	if missing.has("room_lab7"):
		_temp_shell()
	_placeholders(missing)
	_lights()
	print("PLACED ", placed)
	print("MISSING ", missing)
	_dump_tree(self, 0)
	var f := FileAccess.open(out_dir + "/scene_tree.txt", FileAccess.WRITE)
	if f:
		f.store_string("Placed: %s\nMissing (still being modelled): %s\n\n%s\n" % [", ".join(placed), ", ".join(missing), "\n".join(tree_lines)])
	var cam := Camera3D.new()
	add_child(cam)
	cam.current = true
	var shots := [
		["overview_cutaway", Vector3(4.2, 7.2, 6.2), Vector3(-0.4, 0.4, -0.2), 52.0, true],
		["main_camera_east", Vector3(-0.6, 1.55, 0.4), Vector3(3.0, 1.2, 0.0), 64.0, false],
		["player_view_north", Vector3(0.2, 1.55, 0.25), Vector3(0.0, 1.35, -2.5), 64.0, false],
		["player_view_west", Vector3(0.6, 1.55, 0.3), Vector3(-3.0, 1.2, -0.2), 64.0, false],
		["player_view_south", Vector3(0.2, 1.55, -0.6), Vector3(0.0, 1.2, 2.5), 64.0, false],
		["desk_closeup", Vector3(-0.5, 1.48, -1.2), Vector3(-0.5, 0.8, -2.15), 52.0, false],
	]
	var suffix := "_powered" if powered else "_dark"
	for s: Array in shots:
		for cname in ["TempCeiling", "room_ceiling", "room_woodwork", "pendant_lamp", "pendant_lamp_2"]:
			var ceiling := find_child(cname, true, false) as Node3D
			if ceiling:
				ceiling.visible = not s[4] or cname == "room_woodwork" and false
		cam.fov = s[3]
		cam.look_at_from_position(s[1], s[2], Vector3.UP)
		for i in 12:
			await get_tree().process_frame
		await RenderingServer.frame_post_draw
		var img := get_viewport().get_texture().get_image()
		var p: String = out_dir + "/" + str(s[0]) + suffix + ".png"
		img.save_png(p)
		print("SAVED ", p)
	print("QA_DONE exit=0") # tools/qa_run.sh: the run finished even if the process then hangs on exit
	get_tree().quit()


func _dump_tree(n: Node, depth: int) -> void:
	if depth > 2:
		return
	tree_lines.append("  ".repeat(depth) + "%s (%s)" % [n.name, n.get_class()])
	for c in n.get_children():
		_dump_tree(c, depth + 1)


func _box(name: String, size: Vector3, pos: Vector3, mat: String) -> void:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.name = name
	mi.position = pos
	mi.material_override = ModelUtil.load_material(mat)
	add_child(mi)


func _temp_shell() -> void:
	# TEMPORARY placeholder shell for layout/lighting review only (final shell is being modelled in Blender).
	_box("TempFloor", Vector3(6, 0.05, 5), Vector3(0, -0.025, 0), "M_Wood_Floor")
	_box("TempCeiling", Vector3(6, 0.05, 5), Vector3(0, 3.425, 0), "M_Ceiling")
	_box("TempWallN_L", Vector3(3.95, 3.4, 0.1), Vector3(-1.025, 1.7, -2.55), "M_Plaster_Wall")
	_box("TempWallN_R", Vector3(0.95, 3.4, 0.1), Vector3(2.525, 1.7, -2.55), "M_Plaster_Wall")
	_box("TempWallN_Below", Vector3(1.1, 1.45, 0.1), Vector3(1.5, 0.725, -2.55), "M_Plaster_Wall")
	_box("TempWallN_Above", Vector3(1.1, 0.55, 0.1), Vector3(1.5, 3.125, -2.55), "M_Plaster_Wall")
	_box("TempWallS", Vector3(6, 3.4, 0.1), Vector3(0, 1.7, 2.55), "M_Plaster_Wall")
	_box("TempWallE", Vector3(0.1, 3.4, 5), Vector3(3.05, 1.7, 0), "M_Plaster_Wall")
	_box("TempWallW", Vector3(0.1, 3.4, 5), Vector3(-3.05, 1.7, 0), "M_Plaster_Wall")
	_box("TempWainscotN", Vector3(6, 1.05, 0.12), Vector3(0, 0.525, -2.5), "M_Wood_Panel")
	_box("TempWainscotS", Vector3(6, 1.05, 0.12), Vector3(0, 0.525, 2.5), "M_Wood_Panel")
	_box("TempWainscotE", Vector3(0.12, 1.05, 5), Vector3(3.0, 0.525, 0), "M_Wood_Panel")
	_box("TempWainscotW", Vector3(0.12, 1.05, 5), Vector3(-3.0, 0.525, 0), "M_Wood_Panel")


## Labelled greybox stand-ins for models that are still being built in Blender (Phase 2).
func _placeholders(missing: Array[String]) -> void:
	var P := {
		"door_lab7": ["EXIT DOOR (maglock)", Vector3(0.12, 2.2, 1.0), Vector3(2.94, 1.1, 0.9), Color("8a5a3a")],
		"wall_safe": ["WALL SAFE (keypad)", Vector3(0.5, 0.5, 0.12), Vector3(2.2, 1.25, 2.44), Color("4f5d55")],
		"panel7": ["PANEL 7 (circuits)", Vector3(0.22, 0.9, 0.7), Vector3(2.89, 1.45, -1.3), Color("55705f")],
		"lumen_projector": ["LUMEN PROJECTOR", Vector3(0.7, 0.35, 0.35), Vector3(-2.2, 1.15, 1.6), Color("b08d57")],
		"radio": ["VALVE RADIO", Vector3(0.42, 0.28, 0.22), Vector3(0.55, 1.06, 2.2), Color("5a3a24")],
		"chalkboard": ["CHALKBOARD", Vector3(0.05, 1.0, 1.6), Vector3(-2.97, 1.5, 1.05), Color("1e2421")],
		"poster_frame": ["POSTER: TABULA RESONANTIARUM", Vector3(0.6, 0.85, 0.03), Vector3(-0.3, 1.9, 2.48), Color("d9cbb0")],
		"mirror_stand": ["MIRROR STAND A", Vector3(0.25, 1.15, 0.25), Vector3(1.6, 0.6, 1.6), Color("b08d57")],
		"mirror_stand_b": ["MIRROR STAND B (empty)", Vector3(0.25, 1.15, 0.25), Vector3(1.6, 0.6, 0.12), Color("b08d57")],
		"light_sensor": ["LIGHT LOCK", Vector3(0.06, 0.26, 0.26), Vector3(2.97, 1.15, 0.12), Color("e3c27a")],
		"filing_cabinet": ["FILING CABINET", Vector3(0.5, 1.32, 0.6), Vector3(-2.6, 0.66, -2.2), Color("4f5d55")],
		"coat_rack": ["COAT RACK", Vector3(0.45, 1.85, 0.45), Vector3(2.35, 0.92, -2.25), Color("3b2416")],
		"chair": ["CHAIR", Vector3(0.48, 0.9, 0.48), Vector3(-0.35, 0.45, -1.3), Color("3b2416")],
		"desk_lamp": ["DESK LAMP", Vector3(0.18, 0.42, 0.18), Vector3(-1.18, 0.99, -2.32), Color("2f5a3a")],
		"notebook": ["NOTEBOOK", Vector3(0.17, 0.03, 0.23), Vector3(-0.28, 0.795, -1.98), Color("3a2418")],
	}
	for id: String in P:
		if not missing.has(id):
			continue
		var e: Array = P[id]
		var mi := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = e[1]
		mi.mesh = bm
		var m := StandardMaterial3D.new()
		m.albedo_color = e[3]
		m.roughness = 0.7
		mi.material_override = m
		mi.position = e[2]
		mi.name = "PLACEHOLDER_" + id
		add_child(mi)
		var lab := Label3D.new()
		lab.text = "[placeholder]\n" + str(e[0])
		lab.font_size = 34
		lab.pixel_size = 0.0022
		lab.outline_size = 10
		lab.modulate = Color("ffd27a")
		lab.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		lab.no_depth_test = true
		lab.position = e[2] + Vector3(0, (e[1] as Vector3).y * 0.5 + 0.12, 0)
		add_child(lab)
	# window: stone sill + glowing night backdrop (shell openings come with room_lab7.glb)
	if missing.has("room_lab7"):
		var sill := MeshInstance3D.new()
		var sb := BoxMesh.new()
		sb.size = Vector3(1.25, 0.06, 0.32)
		sill.mesh = sb
		sill.material_override = ModelUtil.load_material("M_Stone")
		sill.position = Vector3(1.5, 1.42, -2.4)
		add_child(sill)
		var win := MeshInstance3D.new()
		var q := QuadMesh.new()
		q.size = Vector2(1.1, 1.4)
		win.mesh = q
		var wm := StandardMaterial3D.new()
		wm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		wm.albedo_texture = load("res://assets/textures/decals/window_night.jpg")
		win.material_override = wm
		win.position = Vector3(1.5, 2.15, -2.49)
		add_child(win)
		for k in 4:
			var bar := MeshInstance3D.new()
			var cm := CylinderMesh.new()
			cm.top_radius = 0.012
			cm.bottom_radius = 0.012
			cm.height = 1.4
			bar.mesh = cm
			bar.material_override = ModelUtil.load_material("M_Steel_Dark")
			bar.position = Vector3(1.08 + k * 0.28, 2.15, -2.47)
			add_child(bar)


func _lights() -> void:
	var moon := DirectionalLight3D.new()
	moon.light_color = Color("7fa7d9")
	moon.light_energy = 0.8
	moon.shadow_enabled = true
	add_child(moon)
	var mag := OmniLight3D.new()
	mag.light_color = Color("ff3b2f")
	mag.light_energy = 0.9
	mag.omni_range = 1.8
	mag.position = Vector3(2.8, 2.3, 0.9)
	add_child(mag)
	moon.look_at_from_position(Vector3(1.5, 4.5, -5.5), Vector3(0.3, 0.0, 0.6), Vector3.UP)
	var desk := OmniLight3D.new()
	desk.light_color = Color("ffb46b")
	desk.light_energy = 1.3 if powered else 1.1
	desk.omni_range = 2.6
	desk.position = Vector3(-1.05, 1.18, -2.15)
	desk.shadow_enabled = true
	add_child(desk)
	if powered:
		for p in [Vector3(-0.6, 2.45, -0.6), Vector3(1.2, 2.45, 0.8)]:
			var l := OmniLight3D.new()
			l.light_color = Color("ffc58a")
			l.light_energy = 2.0
			l.omni_range = 6.5
			l.shadow_enabled = p.x < 0
			l.position = p
			add_child(l)
