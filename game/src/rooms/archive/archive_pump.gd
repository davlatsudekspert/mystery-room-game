class_name ArchivePump
extends RefCounted
## Chapter 2 expansion, room R2: the Pump Room (docs/CHAPTER2_EXPANSION.md sections 3, 7, 8 N1/N2, 11 M1; models and
## pivots in docs/models/ch2_exp.md). A zone of the Archive scene (ArchiveZones): the room shell, the boiler, the manifold
## with its six valve wheels, the pipe board, the book-lift cage and the mallet on the bench.
## It only renders ArchiveLogic's state and forwards taps to its actions:
## - N2 pipe routing: valve i opens edge i of this game's graph (`v_pipes`); the pipe board draws that graph, the small
##   diagram plate on the manifold shows it (zoom on tap); the flow (`pipes_reach`) lights the glow bands and the lamps;
##   with the mallet in the bag a tap on a pipe probes it (`n2_tap_pipe`: full / dead / cracked);
## - the way out: the south stair back to the hall and the door to the Night Cell;
## - M1 "the lamp that dies" (the work lamp sinks to an ember and flares back) on the first entry;
## - the mallet lying on the bench (`take("pump_mallet")`).
## The pipe board is drawn from the logic's graph, not from the model's nine fixed segments: the model's IA_pipe_* are
## hidden (the board, its junction boxes and its lamps stay). The N7 book-lift cage is shown closed; its puzzle is wired
## with the rest of Stage B (see docs/CHAPTER2_EXPANSION_STATUS.md).

const VIEWS: Array[String] = ["pump", "manifold", "boiler", "lift_door", "pipes", "bench"]
const HOTSPOT_VIEW := {"pump_manifold": "manifold", "pump_boiler": "boiler", "pump_pipes": "pipes", "pump_lift": "lift_door",
	"pump_bench": "bench", "pump_door": "pump", "pump_stair": "pump"}
const DEEPER := {}
const CAPTION := {"pump": "room2x.pump", "manifold": "obj2x.manifold", "boiler": "obj2x.boiler", "lift_door": "obj2x.lift",
	"pipes": "obj2x.pipe", "bench": "room2x.pump"}

## model -> [position, yaw degrees] in zone coordinates (docs/models/ch2_exp.md "suggested placement").
const PLACE := {
	"room_pump": [Vector3.ZERO, 0.0], "boiler": [Vector3(0, 0, -1.75), 0.0], "manifold_plate": [Vector3(3.5, 0, 1.35), -90.0],
	"pipe_run": [Vector3(-3.5, 0, 1.05), 90.0], "book_lift_cage": [Vector3(-4.40, 0, -1.50), 90.0],
}
## The pipe board's node slots (board coordinates, metres): the source stub, the coil, the vent, four junction boxes.
const SLOT_S := Vector2(-1.25, 0.9)
const SLOT_C := Vector2(1.25, 1.4)
const SLOT_H := Vector2(1.25, 0.4)
const SLOT_J: Array[Vector2] = [Vector2(-0.45, 1.4), Vector2(-0.45, 0.4), Vector2(0.4, 1.4), Vector2(0.4, 0.4)]
const BOARD_Z := 0.105
const VALVE_OPEN_DEG := 90.0
const NEEDLE_TICK_DEG := -27.0
const WORK_LAMP_ENERGY := 1.5

var room: Node3D
var zones: ArchiveZones
var root: Node3D
var logic: ArchiveLogic
var models: Dictionary = {}
var _positions: Array[Vector2] = []
var _edge_nodes: Array[Node3D] = [] # per valve: the pipe, its glow and its marker
var _glow: Array[MeshInstance3D] = []
var _marker: Array[MeshInstance3D] = []
var _diagram: ImageTexture
var _work_light: OmniLight3D
var _lamp_tween: Tween
var _fire_open := false
var _item_mallet: Node3D
var _tweens: Dictionary = {}
var _boiler_light: OmniLight3D


func _init(r: Node3D, z: ArchiveZones, zone_root: Node3D) -> void:
	room = r
	zones = z
	root = zone_root
	logic = r.get("logic")


# ====================================================================== construction
func build() -> void:
	for id: String in PLACE:
		var e: Array = PLACE[id]
		var n := ModelUtil.spawn(id, root, Transform3D(Basis(Vector3.UP, deg_to_rad(float(e[1]))), e[0]), "parts")
		if n == null:
			continue
		n.name = "pump_" + id
		models[id] = n
		(room.get("_roots") as Dictionary)[n] = "pump_" + id
		n.set_meta("hotspot", "")
		room.call("tune_shadows", n)
	(models.get("manifold_plate") as Node3D).set_meta("hotspot", "pump_manifold")
	(models.get("boiler") as Node3D).set_meta("hotspot", "pump_boiler")
	(models.get("pipe_run") as Node3D).set_meta("hotspot", "pump_pipes")
	(models.get("book_lift_cage") as Node3D).set_meta("hotspot", "pump_lift")
	var shell: Node3D = models["room_pump"]
	for mi in ModelUtil.find_meshes(shell):
		if str(mi.name).begins_with("wall_") or str(mi.name) in ["ceiling", "beams"]:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_build_exits(shell)
	_build_lights(shell)
	_build_pipe_board()
	_build_manifold()
	_build_boiler()
	_spawn_mallet(shell)
	_build_views()
	zones.register("pump", VIEWS, HOTSPOT_VIEW, DEEPER, CAPTION)
	_sway_lamp(shell)
	apply_state(false)


func _build_views() -> void:
	var cam: RoomCamera = room.get("cam")
	var o := root.position
	cam.add_view("pump", o + Vector3(-1.7, 1.7, 2.6), o + Vector3(0.4, 1.15, -1.5), 66.0, true)
	cam.add_view("manifold", o + Vector3(1.85, 1.3, 1.35), o + Vector3(3.5, 1.25, 1.35), 56.0)
	cam.add_view("boiler", o + Vector3(0.45, 1.45, 1.1), o + Vector3(0.0, 1.0, -1.75), 58.0)
	cam.add_view("lift_door", o + Vector3(-1.4, 1.45, -1.7), o + Vector3(-4.3, 1.15, -1.9), 58.0)
	cam.add_view("pipes", o + Vector3(-1.2, 0.98, 1.05), o + Vector3(-3.5, 0.95, 1.05), 54.0)
	cam.add_view("bench", o + Vector3(1.55, 1.5, 1.45), o + Vector3(1.6, 0.9, 2.6), 46.0)


func _build_exits(shell: Node3D) -> void:
	# the south stair leads back up to the hall, the east door to the Night Cell
	room.call("add_tap_area", root, Vector3(1.2, 2.4, 0.9), "pump_stair", "Stair_hall", Vector3(-1.7, 1.2, 2.55))
	var door := ModelUtil.find(shell, "IA_door_cell")
	if door != null:
		door.set_meta("hotspot", "pump_door")
		for b in door.get_children():
			if b is StaticBody3D:
				(b as StaticBody3D).set_meta("hotspot", "pump_door")


func _build_lights(shell: Node3D) -> void:
	var lamp := ModelUtil.find(shell, "work_lamp")
	_work_light = OmniLight3D.new()
	_work_light.light_color = Color("ffb36a")
	_work_light.light_energy = WORK_LAMP_ENERGY
	_work_light.omni_range = 6.0
	_work_light.omni_attenuation = 1.2
	_work_light.shadow_enabled = false
	_work_light.position = Vector3(0, -1.2, 0)
	_work_light.set_meta("base_energy", WORK_LAMP_ENERGY)
	if lamp != null:
		lamp.add_child(_work_light)
	else:
		root.add_child(_work_light)
	_boiler_light = OmniLight3D.new()
	_boiler_light.light_color = Color("ff7a30")
	_boiler_light.light_energy = 1.1
	_boiler_light.omni_range = 4.5
	_boiler_light.position = Vector3(0.0, 0.75, -0.3)
	root.add_child(_boiler_light)
	var fill := OmniLight3D.new()
	fill.light_color = Color("bfd6ff")
	fill.light_energy = 0.45
	fill.omni_range = 7.0
	fill.position = Vector3(-1.5, 2.6, 1.0)
	root.add_child(fill)
	for spot: Array in [[Vector3(-1.7, 1.7, 1.05), Color("ffd2a0"), 0.9], [Vector3(2.0, 1.9, 1.35), Color("ffd2a0"), 0.7]]:
		var plate_light := OmniLight3D.new() # the pipe board and the manifold are read from close up: a lamp in front of each
		plate_light.light_color = spot[1]
		plate_light.light_energy = float(spot[2])
		plate_light.omni_range = 3.6
		plate_light.position = spot[0]
		root.add_child(plate_light)
	var fill2 := OmniLight3D.new()
	fill2.light_color = Color("ffb878")
	fill2.light_energy = 0.5
	fill2.omni_range = 7.0
	fill2.position = Vector3(1.5, 2.8, -1.5)
	root.add_child(fill2)


func _sway_lamp(shell: Node3D) -> void:
	var lamp := ModelUtil.find(shell, "work_lamp")
	if lamp == null or bool(Settings.get_value("reduce_motion")):
		return
	var tw := room.create_tween().set_loops()
	tw.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_property(lamp, "rotation_degrees:x", 2.2, 2.6)
	tw.tween_property(lamp, "rotation_degrees:x", -2.2, 2.6)


func _spawn_mallet(shell: Node3D) -> void:
	var mount := ModelUtil.find(shell, "mallet_mount")
	if mount == null:
		return
	_item_mallet = ModelUtil.spawn("mallet", mount, Transform3D.IDENTITY, "none")
	if _item_mallet == null:
		return
	_item_mallet.name = "Item_pump_mallet"
	_item_mallet.rotation_degrees = Vector3(0, 90, 0) # lies along the bench
	var aabb := ItemIcons._aabb(_item_mallet)
	var body := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = (aabb.size + Vector3.ONE * 0.05).max(Vector3.ONE * 0.1)
	cs.shape = box
	cs.position = _item_mallet.global_transform.affine_inverse() * aabb.get_center() if _item_mallet.is_inside_tree() else aabb.get_center()
	body.add_child(cs)
	body.set_meta("part", "Item_pump_mallet")
	body.set_meta("hotspot", "pump_bench")
	_item_mallet.add_child(body)


# ---------------------------------------------------------------------- the pipe board
## Where the six nodes of a graph lie on the board: S, the coil and the vent stay on their stubs, the three junctions take
## three of the four junction boxes so that the pipes cross as little as possible (none, for every shipped graph).
static func layout(graph: Array) -> Array[Vector2]:
	var best: Array[Vector2] = []
	var best_cost := 1 << 30
	for a in 4:
		for b in 4:
			for c in 4:
				if a == b or b == c or a == c:
					continue
				var pos: Array[Vector2] = [SLOT_S, SLOT_C, SLOT_H, SLOT_J[a], SLOT_J[b], SLOT_J[c]]
				var cost := crossings(graph, pos) * 100 + _bends(graph, pos)
				if cost < best_cost:
					best_cost = cost
					best = pos
	return best


## Pairs of pipes that cross (shared end points do not count), plus pipes that run through a node that is not theirs.
static func crossings(graph: Array, pos: Array[Vector2]) -> int:
	var n := 0
	for i in graph.size():
		var e1: Array = graph[i]
		for j in range(i + 1, graph.size()):
			var e2: Array = graph[j]
			if e1[0] == e2[0] or e1[0] == e2[1] or e1[1] == e2[0] or e1[1] == e2[1]:
				continue
			if Geometry2D.segment_intersects_segment(pos[e1[0]], pos[e1[1]], pos[e2[0]], pos[e2[1]]) != null:
				n += 1
		for k in pos.size():
			if k == e1[0] or k == e1[1]:
				continue
			var cp := Geometry2D.get_closest_point_to_segment(pos[k], pos[e1[0]], pos[e1[1]])
			if cp.distance_to(pos[k]) < 0.13:
				n += 1
	return n


static func _bends(graph: Array, pos: Array[Vector2]) -> int:
	var len_sum := 0.0
	for e: Array in graph:
		len_sum += pos[e[0]].distance_to(pos[e[1]])
	return int(len_sum * 10.0)


func _build_pipe_board() -> void:
	var board: Node3D = models["pipe_run"]
	for nm in ["IA_pipe_sa", "IA_pipe_sb", "IA_pipe_ab", "IA_pipe_ac", "IA_pipe_bd", "IA_pipe_cd", "IA_pipe_ct", "IA_pipe_dh", "IA_pipe_th"]:
		room.call("set_present", ModelUtil.find(board, nm), false)
	# the model paints the nine candidate routes as pale guide lines; this game draws its own graph, so they go dark
	var bm := ModelUtil.find(board, "pipe_board") as MeshInstance3D
	if bm != null:
		for i in bm.mesh.get_surface_count():
			if bm.mesh.surface_get_material(i).resource_name == "M_Enamel_Cream":
				bm.set_surface_override_material(i, ModelUtil.load_material("M_Paint_Black"))
	var graph := logic.pipe_graph()
	_positions = layout(graph)
	var copper := ModelUtil.load_material("M_Copper")
	var glow_mat := StandardMaterial3D.new()
	glow_mat.albedo_color = Color("ff8a2c")
	glow_mat.emission_enabled = true
	glow_mat.emission = Color("ff8a2a")
	glow_mat.emission_energy_multiplier = 1.1
	glow_mat.roughness = 0.4
	for i in graph.size():
		var e: Array = graph[i]
		var p := _positions[e[0]]
		var q := _positions[e[1]]
		var holder := Node3D.new()
		holder.name = "pipe_edge_%d" % i
		var mid := (p + q) * 0.5
		holder.position = Vector3(mid.x, mid.y, BOARD_Z)
		holder.rotation = Vector3(0, 0, (q - p).angle())
		board.add_child(holder)
		var length := p.distance_to(q)
		var pipe := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.032
		cm.bottom_radius = 0.032
		cm.height = length
		cm.radial_segments = 10
		pipe.mesh = cm
		pipe.rotation = Vector3(0, 0, PI * 0.5) # the cylinder's axis along the holder's x
		pipe.material_override = copper
		pipe.name = "pipe"
		holder.add_child(pipe)
		var band := MeshInstance3D.new()
		var gm := CylinderMesh.new()
		gm.top_radius = 0.041
		gm.bottom_radius = 0.041
		gm.height = length * 0.97
		gm.radial_segments = 10
		band.mesh = gm
		band.rotation = Vector3(0, 0, PI * 0.5)
		band.material_override = glow_mat
		band.name = "glow"
		band.visible = false
		holder.add_child(band)
		_glow.append(band)
		# the valve's number: a brass disc with a digit, dark while the valve is shut
		var tag := MeshInstance3D.new()
		var tm := CylinderMesh.new()
		tm.top_radius = 0.07
		tm.bottom_radius = 0.07
		tm.height = 0.025
		tag.mesh = tm
		tag.rotation = Vector3(PI * 0.5, 0, 0)
		tag.position = Vector3(0, 0, 0.04)
		var tag_mat := StandardMaterial3D.new()
		tag_mat.albedo_color = Color("8a6e38")
		tag_mat.metallic = 0.7
		tag_mat.roughness = 0.45
		tag.material_override = tag_mat
		tag.name = "tag"
		holder.add_child(tag)
		_marker.append(tag)
		var num := Label3D.new()
		num.text = str(i + 1)
		num.font = load(UITheme.FONT_DISPLAY_BOLD)
		num.font_size = 64
		num.pixel_size = 0.0014
		num.modulate = Color("1a1208")
		num.outline_size = 0
		num.position = Vector3(0, 0, 0.056)
		num.rotation = Vector3(0, 0, -(q - p).angle())
		num.double_sided = false
		holder.add_child(num)
		# the tap target: a fat bar along the pipe (the mallet probes it)
		var body := StaticBody3D.new()
		var cs := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = Vector3(length, 0.15, 0.12)
		cs.shape = box
		body.add_child(cs)
		body.set_meta("part", "IA_pipe_%d" % i)
		body.set_meta("hotspot", "pump_pipes")
		holder.add_child(body)
		_edge_nodes.append(holder)
	# the three stubs: source (green), coil (cold blue), vent (red); the model's lamps sit above the last two
	for k in 3:
		var disc := MeshInstance3D.new()
		var dm := CylinderMesh.new()
		dm.top_radius = 0.11
		dm.bottom_radius = 0.11
		dm.height = 0.05
		disc.mesh = dm
		disc.rotation = Vector3(PI * 0.5, 0, 0)
		var p := _positions[k]
		disc.position = Vector3(p.x, p.y, BOARD_Z + 0.02)
		var m := StandardMaterial3D.new()
		m.albedo_color = [Color("2f6b3a"), Color("5f8fb8"), Color("9a2c22")][k]
		m.roughness = 0.5
		m.metallic = 0.3
		disc.material_override = m
		board.add_child(disc)
	for k in range(3, 6): # junction hubs on the boxes
		var hub := MeshInstance3D.new()
		var hm := CylinderMesh.new()
		hm.top_radius = 0.075
		hm.bottom_radius = 0.075
		hm.height = 0.05
		hub.mesh = hm
		hub.rotation = Vector3(PI * 0.5, 0, 0)
		hub.position = Vector3(_positions[k].x, _positions[k].y, BOARD_Z + 0.02)
		hub.material_override = ModelUtil.load_material("M_Brass_Aged")
		board.add_child(hub)
	for mi in ModelUtil.find_meshes(board):
		if mi.get_parent() != board:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


# ---------------------------------------------------------------------- the manifold and its diagram
func _build_manifold() -> void:
	var man: Node3D = models["manifold_plate"]
	# the model's own diagram quad sits between the pipes (too small to read, partly hidden): this game hangs a larger card
	# on the wall beside the manifold, printed with its graph, and the tap opens it full size
	_diagram = ArchivePump.diagram_texture(logic.pipe_graph(), _positions)
	var small := ModelUtil.find(man, "diagram_plate")
	if small != null:
		small.visible = false
	var card := Node3D.new()
	card.name = "diagram_card"
	card.position = Vector3(3.47, 1.4, -0.12)
	card.rotation_degrees.y = -90.0
	root.add_child(card)
	var frame := MeshInstance3D.new()
	var fb := BoxMesh.new()
	fb.size = Vector3(0.56, 0.38, 0.02)
	frame.mesh = fb
	frame.material_override = ModelUtil.load_material("M_Steel_Dark")
	card.add_child(frame)
	var quad := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = Vector2(0.52, 0.339)
	quad.mesh = qm
	quad.position = Vector3(0, 0, 0.012)
	var m := StandardMaterial3D.new()
	m.albedo_texture = _diagram
	m.albedo_color = Color(0.72, 0.68, 0.6) # paper in lamplight: unshaded, or the lamps beside it burn it out
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	quad.material_override = m
	card.add_child(quad)
	room.call("add_tap_area", card, Vector3(0.6, 0.42, 0.12), "pump_manifold", "Plate_diagram", Vector3(0, 0, 0.04))
	for k in 3: # lamps along the manifold: the numbers on the brass plates under the wheels are read from here
		var l := OmniLight3D.new()
		l.light_color = Color("ffd2a0")
		l.light_energy = 0.5
		l.omni_range = 2.6
		l.position = Vector3(2.5, 1.0, 0.5 + 0.85 * k)
		root.add_child(l)


## The graph as the plate on the manifold prints it: ink on cream paper, the valve numbers on the pipes, the source as a
## filled disc, the coil as a ring with a zigzag, the vent as a ring with louvres (language-neutral, like the Panel 7 icons).
static func diagram_texture(graph: Array, pos: Array[Vector2]) -> ImageTexture:
	const W := 460
	const H := 300
	var img := Image.create(W, H, false, Image.FORMAT_RGBA8)
	img.fill(Color("e6dcc0"))
	var to_px := func(p: Vector2) -> Vector2:
		return Vector2(remap(p.x, -1.6, 1.6, 30.0, W - 30.0), remap(p.y, 0.1, 1.7, H - 30.0, 30.0))
	var ink := Color("2a2118")
	for i in graph.size():
		var e: Array = graph[i]
		_line(img, to_px.call(pos[e[0]]), to_px.call(pos[e[1]]), 4.0, ink)
	for i in graph.size():
		var e: Array = graph[i]
		var m: Vector2 = ((to_px.call(pos[e[0]]) as Vector2) + (to_px.call(pos[e[1]]) as Vector2)) * 0.5
		_disc(img, m, 19.0, Color("e6dcc0"))
		_ring(img, m, 19.0, 3.0, ink)
		_digit(img, m, i + 1, 3, ink)
	for k in pos.size():
		var c: Vector2 = to_px.call(pos[k])
		match k:
			0:
				_disc(img, c, 20.0, Color("2f6b3a"))
			1:
				_disc(img, c, 22.0, Color("e6dcc0"))
				_ring(img, c, 22.0, 4.0, Color("2c5f8a"))
				_line(img, c + Vector2(-14, 6), c + Vector2(-7, -8), 3.0, Color("2c5f8a"))
				_line(img, c + Vector2(-7, -8), c + Vector2(0, 8), 3.0, Color("2c5f8a"))
				_line(img, c + Vector2(0, 8), c + Vector2(7, -8), 3.0, Color("2c5f8a"))
				_line(img, c + Vector2(7, -8), c + Vector2(14, 6), 3.0, Color("2c5f8a"))
			2:
				_disc(img, c, 22.0, Color("e6dcc0"))
				_ring(img, c, 22.0, 4.0, Color("9a2c22"))
				for dy in [-9.0, 0.0, 9.0]:
					_line(img, c + Vector2(-12, dy), c + Vector2(12, dy), 3.0, Color("9a2c22"))
			_:
				_disc(img, c, 9.0, ink)
	return ImageTexture.create_from_image(img)


static func _line(img: Image, a: Vector2, b: Vector2, w: float, col: Color) -> void:
	var lo := Vector2(minf(a.x, b.x) - w, minf(a.y, b.y) - w).floor().max(Vector2.ZERO)
	var hi := Vector2(maxf(a.x, b.x) + w, maxf(a.y, b.y) + w).ceil().min(Vector2(img.get_width() - 1, img.get_height() - 1))
	for y in range(int(lo.y), int(hi.y) + 1):
		for x in range(int(lo.x), int(hi.x) + 1):
			var p := Vector2(x, y)
			if Geometry2D.get_closest_point_to_segment(p, a, b).distance_to(p) <= w * 0.5:
				img.set_pixel(x, y, col)


static func _disc(img: Image, c: Vector2, r: float, col: Color) -> void:
	for y in range(maxi(0, int(c.y - r) - 1), mini(img.get_height(), int(c.y + r) + 2)):
		for x in range(maxi(0, int(c.x - r) - 1), mini(img.get_width(), int(c.x + r) + 2)):
			if Vector2(x, y).distance_to(c) <= r:
				img.set_pixel(x, y, col)


static func _ring(img: Image, c: Vector2, r: float, w: float, col: Color) -> void:
	for y in range(maxi(0, int(c.y - r) - 1), mini(img.get_height(), int(c.y + r) + 2)):
		for x in range(maxi(0, int(c.x - r) - 1), mini(img.get_width(), int(c.x + r) + 2)):
			var d := Vector2(x, y).distance_to(c)
			if d <= r and d >= r - w:
				img.set_pixel(x, y, col)


const DIGITS := ["111101101101111", "010110010010111", "111001111100111", "111001111001111", "101101111001001",
	"111100111001111", "111100111101111", "111001001001001", "111101111101111", "111101111001111"]


static func _digit(img: Image, c: Vector2, d: int, scale: int, col: Color) -> void:
	var bits: String = DIGITS[clampi(d, 0, 9)]
	for row in 5:
		for colm in 3:
			if bits[row * 3 + colm] == "1":
				for sy in scale:
					for sx in scale:
						var x := int(c.x) + (colm - 1) * scale - scale / 2 + sx
						var y := int(c.y) + (row - 2) * scale - scale / 2 + sy
						if x >= 0 and y >= 0 and x < img.get_width() and y < img.get_height():
							img.set_pixel(x, y, col)


func _build_boiler() -> void:
	var b: Node3D = models["boiler"]
	var wl := ModelUtil.find(b, "water_level")
	if wl != null:
		wl.set_meta("rest_scale", wl.scale)


# ====================================================================== state
func apply_state(animated: bool) -> void:
	var s := logic.state
	var reach := logic.pipes_reach()
	var man: Node3D = models["manifold_plate"]
	var open_count := 0
	for i in 6:
		var open := int(s["pipes"][i]) == 1
		open_count += 1 if open else 0
		_rot(ModelUtil.find(man, "IA_valve_%d" % i), Vector3.BACK, VALVE_OPEN_DEG if open else 0.0, animated, 0.35)
		if i < _glow.size():
			var e: Array = logic.pipe_graph()[i]
			var lit := open and reach.has(int(e[0])) and reach.has(int(e[1]))
			_glow[i].visible = lit
			(_marker[i].material_override as StandardMaterial3D).albedo_color = Color("e0b84a") if open else Color("8a6e38")
	var hazard := reach.has(ArchiveExpData.NODE_H)
	var cold_ok: bool = reach.has(ArchiveExpData.NODE_C) and not hazard
	_lamp(ModelUtil.find(man, "hazard_lamp"), hazard, Color("ff3b2f"))
	_lamp(ModelUtil.find(man, "pressure_lamp"), reach.size() > 1 and not hazard, Color("ffb46b"))
	var board: Node3D = models["pipe_run"]
	_lamp(ModelUtil.find(board, "hazard_lamp_h"), hazard, Color("ff3b2f"))
	_lamp(ModelUtil.find(board, "target_lamp_t"), cold_ok or bool(s["thawed"]), Color("9fd8ff"))
	_needle(ModelUtil.find(man, "needle_a"), reach.size() - 1, animated)
	_needle(ModelUtil.find(man, "needle_b"), open_count, animated)
	_needle(ModelUtil.find(board, "needle_src"), reach.size() - 1, animated)
	var boiler: Node3D = models["boiler"]
	_needle(ModelUtil.find(boiler, "needle_boiler"), 4 if not s["thawed"] else 5, animated)
	var glow := ModelUtil.find(boiler, "fire_glow") as MeshInstance3D
	if glow != null:
		glow.visible = true
	_boiler_light.light_energy = 1.1 if not s["thawed"] else 1.5
	_rot(ModelUtil.find(boiler, "IA_fire_door"), Vector3.UP, -100.0 if _fire_open else 0.0, animated, 0.4)
	if _item_mallet != null:
		room.call("set_present", _item_mallet, not bool(s["taken"].get("pump_mallet", false)) and bool(s["pump_open"]))
	# the cell door stands open once the player went through it
	var door := ModelUtil.find(models["room_pump"], "IA_door_cell")
	_rot(door, Vector3.UP, 95.0 if zones != null and logic.room_seen("cell") else 0.0, animated, 0.6)


func _lamp(n: Node3D, on: bool, color: Color) -> void:
	if n is MeshInstance3D:
		ModelUtil.set_emission(n as MeshInstance3D, on, color, 2.2)


func _needle(n: Node3D, ticks: int, animated: bool) -> void:
	_rot(n, Vector3.BACK, NEEDLE_TICK_DEG * clampi(ticks, 0, 10), animated, 0.7)


func _rot(n: Node3D, axis: Vector3, deg: float, animated: bool, dur: float) -> void:
	if n == null:
		return
	if not n.has_meta("rest"):
		n.set_meta("rest", n.transform)
	var base: Transform3D = n.get_meta("rest")
	var target := Transform3D(base.basis * Basis(axis.normalized(), deg_to_rad(deg)), base.origin)
	var k := n.get_instance_id()
	if _tweens.has(k) and (_tweens[k] as Tween).is_valid():
		(_tweens[k] as Tween).kill()
	if not animated or n.transform.is_equal_approx(target):
		n.transform = target
		return
	var from := n.transform
	var fq := from.basis.get_rotation_quaternion()
	var tq := target.basis.get_rotation_quaternion()
	var tw := room.create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tw.tween_method(func(t: float) -> void:
		if is_instance_valid(n):
			n.transform = Transform3D(Basis(fq.slerp(tq, t)), from.origin), 0.0, 1.0, dur)
	_tweens[k] = tw


func on_enter() -> void:
	apply_state(false)


# ====================================================================== taps
## -> true when the tap was handled here.
func interact(hs: String, part: String) -> bool:
	var cam: RoomCamera = room.get("cam")
	var cur := cam.current()
	match hs:
		"pump_manifold":
			if part == "Plate_diagram":
				if cur != "manifold":
					cam.go("manifold")
				else:
					(room.get("hud") as Node).call("_show_zoom", _diagram, room.tr("obj2x.manifold"))
			elif cur != "manifold":
				cam.go("manifold")
			elif part.begins_with("IA_valve_"):
				logic.n2_toggle_valve(int(part.substr(9)))
			elif part == "IA_ram_lever":
				AudioManager.ui("ui_tap")
			else:
				_say("obj2x.manifold")
			return true
		"pump_pipes":
			if cur != "pipes":
				cam.go("pipes")
			elif part.begins_with("IA_pipe_"):
				logic.n2_tap_pipe(int(part.substr(8)))
			else:
				_say("obj2x.pipe")
			return true
		"pump_boiler":
			if cur != "boiler":
				cam.go("boiler")
			elif part == "IA_fire_door":
				_fire_open = not _fire_open
				ArchiveZones.cue("fire_door", -4.0)
				apply_state(true)
			else:
				_say("obj2x.boiler")
			return true
		"pump_lift":
			if cur != "lift_door":
				cam.go("lift_door")
			else:
				_say("obj2x.lift")
			return true
		"pump_bench":
			if cur != "bench":
				cam.go("bench")
			elif logic.can_take("pump_mallet"):
				logic.take("pump_mallet")
			else:
				_say("room2x.pump")
			return true
		"pump_door":
			if logic.room_open("cell"):
				logic.enter_room("cell")
			return true
		"pump_stair":
			logic.enter_room("hall")
			return true
	return false


func _say(key: String) -> void:
	(room.get("hud") as Node).call("message", room.tr(key))
	AudioManager.ui("ui_tap")


## Event feedback (the room's _on_events calls this for every event). -> true when the event was one of ours.
func feedback(e: String) -> bool:
	var name := e.get_slice(":", 0)
	match name:
		"pipe":
			ArchiveZones.cue("valve_wheel", -2.0, randf_range(0.92, 1.08))
			return true
		"pipes_hazard":
			ArchiveZones.cue("steam_hiss", -4.0)
			return true
		"thawed":
			ArchiveZones.cue("pipe_flow")
			room.get_tree().create_timer(1.0).timeout.connect(func() -> void: ArchiveZones.cue("thaw"))
			return true
		"tap":
			var parts := e.split(":")
			if parts.size() >= 3:
				ArchiveZones.cue("pipe_knock_" + parts[2], 0.0, randf_range(0.94, 1.06))
				_flash_pipe(int(parts[1]), parts[2])
			return true
	return false


func _flash_pipe(i: int, kind: String) -> void:
	if i < 0 or i >= _glow.size():
		return
	var g := _glow[i]
	var was := g.visible
	g.visible = true
	var mat := g.material_override as StandardMaterial3D
	var base_col := mat.albedo_color
	mat.albedo_color = {"full": Color("ffb45a"), "dead": Color("8a8a8a"), "cracked": Color("ff4a30")}.get(kind, base_col)
	room.get_tree().create_timer(0.35).timeout.connect(func() -> void:
		if is_instance_valid(g):
			g.visible = was
			mat.albedo_color = base_col)


# ====================================================================== moments
## M1 "the lamp that dies": the work lamp sinks to an ember (light and bulb), then flares back with a tick.
func moment_m1(seconds: float, _sting: bool) -> void:
	if _work_light == null:
		return
	if _lamp_tween != null and _lamp_tween.is_valid():
		_lamp_tween.kill()
	var base := WORK_LAMP_ENERGY
	var bulb := ModelUtil.find(models["room_pump"], "work_lamp_bulb") as MeshInstance3D
	_lamp_tween = room.create_tween()
	_lamp_tween.tween_property(_work_light, "light_energy", base * 0.04, seconds * 0.4).set_trans(Tween.TRANS_QUAD)
	_lamp_tween.tween_callback(func() -> void: _lamp(bulb, false, Color("ffb46b")))
	_lamp_tween.tween_interval(seconds * 0.25)
	_lamp_tween.tween_property(_work_light, "light_energy", base * 1.5, 0.12)
	_lamp_tween.parallel().tween_callback(func() -> void: _lamp(bulb, true, Color("ffb46b")))
	_lamp_tween.tween_property(_work_light, "light_energy", base, seconds * 0.25).set_trans(Tween.TRANS_SINE)
