class_name ArchiveCell
extends RefCounted
## Chapter 2 expansion, room R3: the Night Cell (docs/CHAPTER2_EXPANSION.md sections 3, 8 N3, 11 M2; models and pivots in
## docs/models/ch2_exp.md "R3 Night Cell and hall additions"). A zone of the Archive scene (ArchiveZones): Leyla's room with
## her cot, the kettle on its hotplate, a diary page, the cloth for N5, the light table and the insulated door to the Cold Store.
## It only renders ArchiveLogic's state and forwards taps and drags to its actions:
## - N3 light table: the three acetate sheets lie stacked on the glass. Tap a sheet (or the round turn button of its colour) to
##   turn it a quarter, tap its flip tab (or the flip button) to flip it, or drag it sideways (turn) / down (flip). The window
##   shows the cells that are clear on all three sheets (`n3_lit`); the sheets' own smoky cells block the light the way the
##   logic's AND does. A solved table locks (the digits stay lit);
## - the Cold Store door: two digit wheels (tap = +1, drag = +-1 per step), the cam handle, the frost, the coil's glow;
## - the kettle beat (knobs, lifting the kettle), the diary, the pencil slip on the lamp, the cloth (`take("cell_cloth")`).
## Moment M2 (the knocks) is played from the Pump Room (ArchivePump.moment_m2): it fires before the first entry.

const VIEWS: Array[String] = ["cell", "desk", "light_table", "cot", "shelf", "cold_door", "cold_wheels"]
const HOTSPOT_VIEW := {"cell_table": "light_table", "cell_desk": "desk", "cell_cot": "cot", "cell_shelf": "shelf", "cell_cold_door": "cold_door"}
const DEEPER := {"cold_door": ["cold_wheels"]}
const CAPTION := {"cell": "room2x.cell", "desk": "obj2x.diary", "light_table": "obj2x.light_table", "cot": "obj2x.cot", "shelf": "obj2x.shelf",
	"cold_door": "obj2x.cold_door", "cold_wheels": "obj2x.cold_door"}

## model -> [position, yaw degrees] in zone coordinates (docs/models/ch2_exp.md "Placements").
const PLACE := {
	"room_cell": [Vector3.ZERO, 0.0], "cot": [Vector3(-0.75, 0, -1.58), 0.0], "light_table": [Vector3(1.30, 0.76, -1.62), 0.0],
	"kettle_hotplate": [Vector3(-0.70, 0.86, 1.76), 180.0], "cell_diary": [Vector3(0.86, 0.778, -1.66), 12.0],
	"cold_door": [Vector3(2.20, 0, 0), -90.0],
}
const SHEETS: Array[String] = ["acetate_sheet_a", "acetate_sheet_b", "acetate_sheet_c"]
const SHEET_TINT: Array[Color] = [Color("2e0b10"), Color("0a1230"), Color("2e2004")] # crimson, cobalt, amber smoke (near black)
const SHEET_BUTTON: Array[Color] = [Color("c0283c"), Color("2f5fc4"), Color("e0a02a")]
const CLOTH_POS := Vector3(-0.30, 0.8775, 1.50)
const NOTE_POS := Vector3(0.93, 0.763, -1.40)
const CELL_PX := 16
const DRAG_STEP_PX := 34.0
const DOOR_OPEN_DEG := -100.0
const HANDLE_OPEN_DEG := -90.0
const WHEEL_STEP_DEG := 36.0
const KNOB_ON_DEG := -90.0

var room: Node3D
var zones: ArchiveZones
var root: Node3D
var logic: ArchiveLogic
var models: Dictionary = {}
var _tweens: Dictionary = {}
var _sheet: Array[Node3D] = []
var _tab: Array[Node3D] = []
var _print_mat: Array[StandardMaterial3D] = []
var _rot_acc: Array[int] = [0, 0, 0]
var _flip_acc: Array[int] = [0, 0, 0]
var _flip_seen: Array[int] = [0, 0, 0]
var _mask_img: Image
var _mask_tex: ImageTexture
var _mask_mat: StandardMaterial3D
var _lit_shown := PackedByteArray()
var _table_on := false
var _table_seen := false
var _table_light: OmniLight3D
var _glow_tween: Tween
var _plate_on := true
var _steam: CPUParticles3D
var _cloth: Node3D
var _lifted := false
var _looked := false
var _drag_part := ""
var _drag_acc := Vector2.ZERO
var _drag_done := false


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
		n.name = "cell_" + id
		models[id] = n
		(room.get("_roots") as Dictionary)[n] = "cell_" + id
		(room.get("models") as Dictionary)["cell_" + id] = n
		n.set_meta("hotspot", "")
		room.call("tune_shadows", n)
	(models["cot"] as Node3D).set_meta("hotspot", "cell_cot")
	(models["light_table"] as Node3D).set_meta("hotspot", "cell_table")
	(models["cell_diary"] as Node3D).set_meta("hotspot", "cell_desk")
	(models["kettle_hotplate"] as Node3D).set_meta("hotspot", "cell_shelf")
	(models["cold_door"] as Node3D).set_meta("hotspot", "cell_cold_door")
	var shell: Node3D = models["room_cell"]
	for mi in ModelUtil.find_meshes(shell):
		if str(mi.name).begins_with("wall_") or str(mi.name) in ["ceiling", "trim"]:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_calm_wallpaper(shell)
	_build_lights(shell)
	_build_table()
	_build_kettle()
	_build_door()
	_build_extras()
	_build_views()
	zones.register("cell", VIEWS, HOTSPOT_VIEW, DEEPER, CAPTION)
	apply_state(false)


## The ochre diamond wallpaper is loud on a phone screen: the walls get a copy of its material with less contrast, saturation and
## brightness (the artist's texture stays as it is; this only tones it in the scene).
func _calm_wallpaper(shell: Node3D) -> void:
	var calm: BaseMaterial3D = null
	for mi in ModelUtil.find_meshes(shell):
		if not str(mi.name).begins_with("wall_"):
			continue
		for i in mi.mesh.get_surface_count():
			if mi.mesh.surface_get_material(i).resource_name != "M_Wallpaper_Cell":
				continue
			if calm == null:
				var src := ModelUtil.load_material("M_Wallpaper_Cell") as BaseMaterial3D
				if src == null:
					return
				calm = src.duplicate() as BaseMaterial3D
				var tex := src.albedo_texture
				if tex != null:
					var img := tex.get_image()
					if img != null:
						if img.is_compressed():
							img.decompress()
						img.clear_mipmaps()
						if maxi(img.get_width(), img.get_height()) > 512:
							img.resize(512, 512, Image.INTERPOLATE_BILINEAR)
						img.adjust_bcs(0.93, 0.62, 0.8)
						img.generate_mipmaps()
						calm.albedo_texture = ImageTexture.create_from_image(img)
				calm.normal_scale = 0.5
			mi.set_surface_override_material(i, calm)


func _empty(shell: Node3D, nm: String) -> Vector3:
	var e := ModelUtil.find(shell, nm)
	return e.position if e != null else Vector3.ZERO


func _build_lights(shell: Node3D) -> void:
	# warm and readable on a phone: the pendant carries the room, the desk lamp the light table, two soft fills for the cot and
	# the shelf, one cold spill from the Cold Store door (docs/models/ch2_exp.md light recipe, scaled for the Mobile renderer)
	ArchiveKit.omni(root, _empty(shell, "light_lamp_ceiling"), Color("ffb46b"), 1.7, 6.8, 1.0)
	ArchiveKit.omni(root, _empty(shell, "light_lamp_desk"), Color("ffd9a6"), 1.0, 2.9, 1.0)
	ArchiveKit.omni(root, _empty(shell, "light_fill"), Color("ffe3b8"), 0.55, 6.0, 1.0)
	ArchiveKit.omni(root, _empty(shell, "light_cot_fill"), Color("ffc890"), 0.55, 3.2, 1.0)
	ArchiveKit.omni(root, Vector3(1.9, 1.7, 0.0), Color("bfe0ff"), 0.35, 2.6, 1.0)
	# the shelf close-up and the light table are read from nearby: a lamp in front of each
	ArchiveKit.omni(root, Vector3(-0.6, 1.5, 1.0), Color("ffd2a0"), 0.5, 2.6, 1.0)


func _build_views() -> void:
	var cam: RoomCamera = room.get("cam")
	var o := root.position
	cam.add_view("cell", o + Vector3(-1.95, 1.62, 1.45), o + Vector3(0.35, 0.92, -0.85), 72.0, true)
	cam.add_view("desk", o + Vector3(1.12, 1.34, -0.82), o + Vector3(1.12, 0.78, -1.55), 52.0)
	cam.add_view("light_table", o + Vector3(1.3, 1.36, -1.18), o + Vector3(1.3, 0.8, -1.56), 38.0)
	cam.add_view("cot", o + Vector3(-0.15, 1.5, -0.05), o + Vector3(-0.85, 0.5, -1.6), 58.0)
	cam.add_view("shelf", o + Vector3(-0.45, 1.45, 0.25), o + Vector3(-0.55, 0.95, 1.85), 54.0)
	cam.add_view("cold_door", o + Vector3(-0.3, 1.45, 0.1), o + Vector3(2.2, 1.1, 0.05), 58.0)
	cam.add_view("cold_wheels", o + Vector3(1.55, 1.34, 0.285), o + Vector3(2.2, 1.27, 0.285), 30.0)


# ---------------------------------------------------------------------- the light table and its sheets
func _build_table() -> void:
	var table: Node3D = models["light_table"]
	# the box's light: warm white, small (the sheets are read against it)
	_table_light = ArchiveKit.omni(table, Vector3(0, 0.2, 0.02), Color("fff1d0"), 0.0, 1.5, 1.0)
	# the window mask: this game draws the lit cells onto the model's `table_mask` quad (dark where the light is blocked)
	_mask_img = Image.create(ArchiveExpData.GRID * CELL_PX, ArchiveExpData.WIN_ROWS * CELL_PX, false, Image.FORMAT_RGBA8)
	_mask_tex = ImageTexture.create_from_image(_mask_img)
	_mask_mat = ArchiveKit.decal_material(_mask_tex, true, 0, true)
	var mask := ModelUtil.find(table, "table_mask") as MeshInstance3D
	if mask != null:
		mask.material_override = _mask_mat
		mask.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for i in 3:
		var mount := ModelUtil.find(table, "sheet_mount_%d" % i)
		var s := ModelUtil.spawn(SHEETS[i], mount, Transform3D.IDENTITY, "parts")
		if s == null:
			continue
		s.name = "cell_" + SHEETS[i]
		models[SHEETS[i]] = s
		(room.get("_roots") as Dictionary)[s] = "cell_" + SHEETS[i]
		(room.get("models") as Dictionary)["cell_" + SHEETS[i]] = s
		s.set_meta("hotspot", "cell_table")
		var body := ModelUtil.find(s, "IA_sheet") as Node3D
		var tab := ModelUtil.find(s, "IA_flip_tab") as Node3D
		ArchiveKit.rename_part(body, "IA_sheet_%d" % i)
		ArchiveKit.rename_part(tab, "IA_flip_tab_%d" % i)
		_sheet.append(body)
		_tab.append(tab)
		var pr := ModelUtil.find(s, "sheet_print") as MeshInstance3D
		ArchiveKit.drop_colliders(pr)
		var tex := ImageTexture.create_from_image(_print_image(i))
		var mat := ArchiveKit.decal_material(tex, true, i + 1, true)
		_print_mat.append(mat)
		if pr != null:
			pr.material_override = mat
			pr.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		# the acetate itself is thin and clear: a milky layer on each of three sheets would wash the prints under it out
		for mi in ModelUtil.find_meshes(s):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			for k in mi.mesh.get_surface_count():
				if mi.mesh.surface_get_material(k).resource_name == "M_Acetate":
					var clear := (ModelUtil.load_material("M_Acetate") as StandardMaterial3D).duplicate() as StandardMaterial3D
					clear.albedo_color.a = 0.07
					clear.metallic_specular = 0.2
					mi.set_surface_override_material(k, clear)
	# the window shows 7 of the sheets' 11 rows: the two outer rows on each side are dimmed, like a bezel, so that only the
	# window's cells read as light
	var bezel := ArchiveKit.decal_material(_bezel_texture(), true, 10, false)
	var half_win := ArchiveExpData.WIN_ROWS * 0.022 * 0.5
	for sgn in [-1.0, 1.0]:
		var strip := ArchiveKit.quad(table, Vector2(0.27, 0.075), Vector3(0, 0.0725, 0.02 + sgn * (half_win + 0.0375)), bezel, "bezel")
		strip.rotation_degrees.x = -90.0
	# the six round buttons in front of the box: a turn button and a flip button per sheet, in the sheet's tape colour
	for i in 3:
		var cx := (i - 1) * 0.18
		_build_button(table, i, "IA_turn_%d" % i, Vector3(cx - 0.046, 0.012, 0.232), true)
		_build_button(table, i, "IA_flipbtn_%d" % i, Vector3(cx + 0.046, 0.012, 0.232), false)


func _build_button(table: Node3D, i: int, part: String, pos: Vector3, turn: bool) -> void:
	var holder := Node3D.new()
	holder.name = part
	holder.position = pos
	table.add_child(holder)
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.03
	cm.bottom_radius = 0.034
	cm.height = 0.016
	cm.radial_segments = 20
	mi.mesh = cm
	var m := StandardMaterial3D.new()
	m.albedo_color = SHEET_BUTTON[i]
	m.roughness = 0.45
	m.metallic = 0.2
	mi.material_override = m
	mi.position = Vector3(0, 0.008, 0)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	holder.add_child(mi)
	var icon := ArchiveKit.quad(holder, Vector2(0.048, 0.048), Vector3(0, 0.0165, 0), ArchiveKit.decal_material(_button_icon(turn), true), "icon")
	icon.rotation_degrees.x = -90.0
	room.call("add_tap_area", holder, Vector3(0.08, 0.05, 0.08), "cell_table", part, Vector3(0, 0.02, 0))


func _bezel_texture() -> ImageTexture:
	var img := Image.create(8, 8, false, Image.FORMAT_RGBA8)
	img.fill(Color(0.03, 0.02, 0.015, 0.78))
	return ImageTexture.create_from_image(img)


## The icon on a button: a turning arrow (turn) or two facing arrows (flip), white on the button's colour.
func _button_icon(turn: bool) -> ImageTexture:
	var img := Image.create(64, 64, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var ink := Color(1, 1, 1, 0.95)
	if turn:
		ArchiveKit.ring(img, Vector2(32, 32), 19.0, 5.0, ink, 0.4, TAU - 1.1)
		ArchiveKit.arrow_head(img, Vector2(32 + 19.0 * cos(TAU - 1.1), 32 + 19.0 * sin(TAU - 1.1)), Vector2(sin(TAU - 1.1), -cos(TAU - 1.1)) * -1.0, 15.0, ink)
	else:
		ArchiveKit.line(img, Vector2(10, 32), Vector2(54, 32), 5.0, ink)
		ArchiveKit.arrow_head(img, Vector2(8, 32), Vector2(-1, 0), 14.0, ink)
		ArchiveKit.arrow_head(img, Vector2(56, 32), Vector2(1, 0), 14.0, ink)
		ArchiveKit.line(img, Vector2(32, 14), Vector2(32, 50), 3.0, Color(1, 1, 1, 0.55))
	return ImageTexture.create_from_image(img)


## Sheet i's own smoke: its blocked cells (bit 0) dark in the sheet's tape colour, its clear cells (bit 1) see-through.
func _print_image(i: int) -> Image:
	var bits := logic.n3_sheet(i)
	var tint := SHEET_TINT[i]
	var blocked := Color(tint.r, tint.g, tint.b, 0.94)
	var clear := Color(1, 1, 1, 0.0)
	var img := Image.create(ArchiveExpData.GRID * CELL_PX, ArchiveExpData.GRID * CELL_PX, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	for r in ArchiveExpData.GRID:
		for c in ArchiveExpData.GRID:
			var rect := Rect2i(c * CELL_PX, r * CELL_PX, CELL_PX, CELL_PX)
			if bits[r * ArchiveExpData.GRID + c] == 0:
				img.fill_rect(rect, blocked)
			else:
				img.fill_rect(rect, clear)
				# a faint grid on the clear glass, so the cells can be counted
				img.fill_rect(Rect2i(rect.position.x, rect.position.y, CELL_PX, 1), Color(1, 1, 1, 0.16))
				img.fill_rect(Rect2i(rect.position.x, rect.position.y, 1, CELL_PX), Color(1, 1, 1, 0.16))
	return img


## The window as the light makes it: lit cells bright warm white, blocked cells dark.
func _mask_image(lit: PackedByteArray) -> Image:
	return ArchiveKit.cell_image(lit, ArchiveExpData.GRID, ArchiveExpData.WIN_ROWS, CELL_PX, Color("fff0c4"), Color(0.05, 0.035, 0.02, 0.9), 1)


# ---------------------------------------------------------------------- the kettle beat
func _build_kettle() -> void:
	var k: Node3D = models["kettle_hotplate"]
	var mount := ModelUtil.find(k, "steam_mount")
	_steam = CPUParticles3D.new()
	_steam.amount = 10
	_steam.lifetime = 2.4
	_steam.preprocess = 2.4
	_steam.local_coords = false
	_steam.direction = Vector3.UP
	_steam.spread = 12.0
	_steam.gravity = Vector3(0, 0.05, 0)
	_steam.initial_velocity_min = 0.06
	_steam.initial_velocity_max = 0.12
	_steam.scale_amount_min = 0.7
	_steam.scale_amount_max = 1.2
	_steam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var qm := QuadMesh.new()
	qm.size = Vector2(0.07, 0.07)
	_steam.mesh = qm
	var sm := StandardMaterial3D.new()
	sm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	sm.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	sm.albedo_texture = _soft_dot()
	sm.vertex_color_use_as_albedo = true
	sm.albedo_color = Color(1, 1, 1, 0.22)
	_steam.material_override = sm
	var ramp := Gradient.new()
	ramp.set_color(0, Color(1, 1, 1, 0.0))
	ramp.add_point(0.25, Color(1, 1, 1, 0.55))
	ramp.set_color(ramp.get_point_count() - 1, Color(1, 1, 1, 0.0))
	_steam.color_ramp = ramp
	_steam.scale_amount_curve = _grow_curve()
	(mount if mount != null else k).add_child(_steam)
	_cloth = ModelUtil.spawn("wipe_cloth", root, Transform3D(Basis(Vector3.UP, deg_to_rad(20.0)), CLOTH_POS), "none")
	if _cloth != null:
		_cloth.name = "Item_cell_cloth"
		(room.get("models") as Dictionary)["cell_wipe_cloth"] = _cloth
		room.call("tune_shadows", _cloth)
		ArchiveKit.item_body(_cloth, "cell_shelf", "Item_cell_cloth", 0.06)


func _grow_curve() -> Curve:
	var c := Curve.new()
	c.add_point(Vector2(0, 0.5))
	c.add_point(Vector2(1, 1.6))
	return c


static func _soft_dot() -> GradientTexture2D:
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	var t := GradientTexture2D.new()
	t.gradient = g
	t.fill = GradientTexture2D.FILL_RADIAL
	t.fill_from = Vector2(0.5, 0.5)
	t.fill_to = Vector2(1.0, 0.5)
	t.width = 64
	t.height = 64
	return t


# ---------------------------------------------------------------------- the Cold Store door
func _build_door() -> void:
	var d: Node3D = models["cold_door"]
	# open, the doorway takes the tap that walks through it (the closed leaf is its own tap target)
	var doorway := room.call("add_tap_area", d, Vector3(0.9, 2.0, 0.7), "cell_cold_door", "Doorway", Vector3(0, 1.05, 0.25)) as StaticBody3D
	doorway.name = "DoorwayTap"
	# the digit drums are polished brass: with no reflections in the room that reads black, so they get a matte brass
	var brass := StandardMaterial3D.new()
	brass.albedo_color = Color("c9a45a")
	brass.metallic = 0.15
	brass.roughness = 0.55
	for nm in ["IA_wheel_a", "IA_wheel_b"]:
		var w := ModelUtil.find(d, nm) as MeshInstance3D
		if w == null:
			continue
		for k in w.mesh.get_surface_count():
			if w.mesh.surface_get_material(k).resource_name == "M_Brass_Polished":
				w.set_surface_override_material(k, brass)


func _build_extras() -> void:
	# the exit: the doorway in the west wall leads back to the Pump Room
	room.call("add_tap_area", root, Vector3(0.5, 2.1, 0.95), "cell_exit", "Exit_pump", Vector3(-2.15, 1.05, -1.1))
	# a pencilled slip on the desk by the lamp (docs/CHAPTER2_EXPANSION.md B3): the light table's first hint, read on a tap
	var slip := Node3D.new()
	slip.name = "light_note"
	slip.position = NOTE_POS
	slip.rotation_degrees = Vector3(0, -14, 0)
	root.add_child(slip)
	var q := ArchiveKit.quad(slip, Vector2(0.11, 0.075), Vector3.ZERO, ArchiveKit.decal_material(_slip_texture(), false), "paper")
	q.rotation_degrees.x = -90.0
	room.call("add_tap_area", slip, Vector3(0.16, 0.05, 0.12), "cell_desk", "IA_note_light", Vector3(0, 0.02, 0))


func _slip_texture() -> ImageTexture:
	var img := Image.create(110, 75, false, Image.FORMAT_RGBA8)
	img.fill(Color("d9cdb0"))
	for k in 4:
		ArchiveKit.line(img, Vector2(10, 14 + k * 16), Vector2(98 - (k % 2) * 28, 14 + k * 16 + (k % 2) * 2), 2.0, Color(0.25, 0.23, 0.22, 0.75))
	return ImageTexture.create_from_image(img)


# ====================================================================== state
func apply_state(animated: bool) -> void:
	_pose_sheets(animated)
	_update_table(animated)
	_update_door(animated)
	_update_kettle(animated)
	if _cloth != null:
		room.call("set_present", _cloth, logic.can_take("cell_cloth"))


func _pose_sheets(animated: bool) -> void:
	var sh: Array = logic.state["sheets"]
	for i in _sheet.size():
		var want_rot := _rot_acc[i] + posmod(int(sh[2 * i]) * 90 - _rot_acc[i], 360)
		var fl := int(sh[2 * i + 1])
		var want_flip := _flip_acc[i] + (180 if fl != (_flip_acc[i] / 180) % 2 else 0)
		_rot_acc[i] = want_rot
		_flip_acc[i] = want_flip
		var b := Basis(Vector3.BACK, -deg_to_rad(float(want_rot))) * Basis(Vector3.UP, deg_to_rad(float(want_flip)))
		ArchiveKit.pose(room, _tweens, _sheet[i], b, Vector3.ZERO, animated, 0.34)
		_flip_seen[i] = fl


func _update_table(animated: bool) -> void:
	var table: Node3D = models["light_table"]
	if bool(logic.state["cell_digits_ok"]):
		_table_on = true # a solved table (or a loaded save) is simply on
	var lit := logic.n3_lit()
	if lit != _lit_shown:
		_lit_shown = lit
		_mask_img = _mask_image(lit)
		_mask_tex.update(_mask_img)
	var glow := ModelUtil.find(table, "table_glow") as MeshInstance3D
	if glow != null:
		glow.visible = _table_on
	var mask := ModelUtil.find(table, "table_mask") as MeshInstance3D
	if mask != null:
		mask.visible = _table_on
	_lamp(ModelUtil.find(table, "pilot_lamp") as MeshInstance3D, _table_on, Color("ffb46b"))
	ArchiveKit.rot(room, _tweens, ModelUtil.find(table, "IA_switch"), Vector3.RIGHT, -25.0 if _table_on else 0.0, animated, 0.2)
	if _glow_tween == null or not _glow_tween.is_valid():
		_table_light.light_energy = (0.9 if bool(logic.state["cell_digits_ok"]) else 0.6) if _table_on else 0.0


func _lamp(mi: MeshInstance3D, on: bool, color: Color) -> void:
	if mi != null:
		ModelUtil.set_emission(mi, on, color, 2.2)


func _update_door(animated: bool) -> void:
	var d: Node3D = models["cold_door"]
	var s := logic.state
	var open := bool(s["cold_open"])
	var wheels: Array = s["cold_wheels"]
	ArchiveKit.rot(room, _tweens, ModelUtil.find(d, "IA_cold_door"), Vector3.UP, DOOR_OPEN_DEG if open else 0.0, animated, 1.1)
	ArchiveKit.rot(room, _tweens, ModelUtil.find(d, "IA_cold_handle"), Vector3.BACK, HANDLE_OPEN_DEG if open else 0.0, animated, 0.4)
	ArchiveKit.rot(room, _tweens, ModelUtil.find(d, "IA_wheel_a"), Vector3.RIGHT, WHEEL_STEP_DEG * int(wheels[0]), animated, 0.25)
	ArchiveKit.rot(room, _tweens, ModelUtil.find(d, "IA_wheel_b"), Vector3.RIGHT, WHEEL_STEP_DEG * int(wheels[1]), animated, 0.25)
	var ice := ModelUtil.find(d, "door_ice")
	if ice != null:
		ice.visible = not bool(s["thawed"])
	var coil := ModelUtil.find(d, "coil_glow")
	if coil != null:
		coil.visible = bool(s["thawed"]) and not open
	var lamp := ModelUtil.find(d, "lock_lamp") as MeshInstance3D
	if lamp != null:
		ModelUtil.set_emission(lamp, true, Color("52d36a") if open else Color("ff3b2f"), 2.2)
	var doorway := ModelUtil.find(d, "DoorwayTap")
	room.call("set_present", doorway, open)


func _update_kettle(animated: bool) -> void:
	var k: Node3D = models["kettle_hotplate"]
	ArchiveKit.rot(room, _tweens, ModelUtil.find(k, "IA_knob_left"), Vector3.BACK, KNOB_ON_DEG if _plate_on else 0.0, animated, 0.3)
	ArchiveKit.rot(room, _tweens, ModelUtil.find(k, "IA_knob_right"), Vector3.BACK, 0.0, animated, 0.3)
	var coil := ModelUtil.find(k, "coil_glow")
	if coil != null:
		coil.visible = _plate_on
	_steam.emitting = _plate_on
	ArchiveKit.pose(room, _tweens, ModelUtil.find(k, "IA_kettle"), Basis.IDENTITY, Vector3(0, 0.06 if _lifted else 0.0, 0), animated, 0.25)


func on_enter() -> void:
	apply_state(false)
	if not _looked and logic.room_seen("cell"):
		_looked = true
		(room.get("hud") as Node).call("caption", room.tr("cap2x.cell_look"), 5.0)


## A camera view of this room came up: the light box switches itself on the first time the table is looked at.
func on_view(view: String) -> void:
	if view == "light_table" and not _table_seen:
		_table_seen = true
		if not _table_on:
			_switch_on_beat()


func _switch_on_beat() -> void:
	ArchiveZones.cue("c2x_lightbox_on", -3.0)
	if _glow_tween != null and _glow_tween.is_valid():
		_glow_tween.kill()
	_table_on = true
	_update_table(true)
	_glow_tween = room.create_tween()
	for k in 3: # the starter flickers three times, then the box settles
		_glow_tween.tween_property(_table_light, "light_energy", 0.05, 0.05)
		_glow_tween.tween_property(_table_light, "light_energy", 0.8, 0.09)
		_glow_tween.tween_interval(0.12)
	_glow_tween.tween_property(_table_light, "light_energy", 0.6, 0.3)


# ====================================================================== taps and drags
## -> true when the tap was handled here.
func interact(hs: String, part: String) -> bool:
	var cam: RoomCamera = room.get("cam")
	var cur := cam.current()
	match hs:
		"cell_table":
			if cur != "light_table":
				cam.go("light_table")
			elif part.begins_with("IA_sheet_") or part.begins_with("IA_turn_"):
				logic.n3_turn_sheet(int(part.get_slice("_", 2)))
			elif part.begins_with("IA_flip_tab_"):
				logic.n3_flip_sheet(int(part.get_slice("_", 3)))
			elif part.begins_with("IA_flipbtn_"):
				logic.n3_flip_sheet(int(part.get_slice("_", 1)))
			elif part == "IA_switch":
				_toggle_table()
			else:
				_say("obj2x.light_table")
			return true
		"cell_desk":
			if cur != "desk":
				cam.go("desk")
			elif part == "IA_cell_diary":
				_read("doc2x.diary", "obj2x.diary")
			elif part == "IA_note_light":
				_read("doc2x.light_note", "obj2x.light_table")
			else:
				_say("obj2x.light_table")
			return true
		"cell_cot":
			if cur != "cot":
				cam.go("cot")
			elif part == "IA_cot_drawing":
				(room.get("hud") as Node).call("_show_picture", "res://assets/textures/decals/ch2x/cell_drawing.png", room.tr("obj2x.cot"))
			else:
				_say("obj2x.cot")
			return true
		"cell_shelf":
			if cur != "shelf":
				cam.go("shelf")
			elif part == "Item_cell_cloth" and logic.can_take("cell_cloth"):
				logic.take("cell_cloth")
			elif part == "IA_kettle":
				_lifted = not _lifted
				AudioManager.ui("ui_tap")
				_update_kettle(true)
			elif part.begins_with("IA_knob_"):
				_plate_on = not _plate_on
				AudioManager.ui("ui_tap")
				_update_kettle(true)
			else:
				_say("obj2x.kettle")
			return true
		"cell_cold_door":
			if cur != "cold_door" and cur != "cold_wheels":
				cam.go("cold_door")
			elif logic.state["cold_open"] and part in ["Doorway", "IA_cold_door", "IA_cold_handle"]:
				logic.enter_room("cold")
			elif part.begins_with("IA_wheel_"):
				if cur == "cold_door":
					cam.go("cold_wheels") # from the whole door a first tap steps in to the wheels, the next ones turn them
				else:
					logic.cold_wheel(0 if part.ends_with("_a") else 1, 1)
			elif part == "IA_cold_handle" or part == "IA_cold_door":
				_try_handle()
			else:
				_say("obj2x.cold_door")
			return true
		"cell_exit":
			logic.enter_room("pump")
			return true
	return false


func _try_handle() -> void:
	var d: Node3D = models["cold_door"]
	ArchiveKit.rot(room, _tweens, ModelUtil.find(d, "IA_cold_handle"), Vector3.BACK, -14.0, true, 0.1)
	room.get_tree().create_timer(0.16).timeout.connect(func() -> void: _update_door(true))
	ArchiveZones.cue("c2x_cold_frozen", -4.0)
	var hud: Node = room.get("hud")
	if bool(logic.state["thawed"]):
		hud.call("message", room.tr("msg.nothing")) # thawed, but the wheels are not set
	else:
		hud.call("message", room.tr("cap2x.cold_frozen"))


func _toggle_table() -> void:
	_table_on = not _table_on
	AudioManager.ui("ui_tap")
	if _table_on:
		ArchiveZones.cue("c2x_lightbox_on", -6.0)
	_update_table(true)


func _read(doc_key: String, title_key: String) -> void:
	(room.get("hud") as Node).call("_show_paper", room.tr(doc_key), room.tr(title_key))


func _say(key: String) -> void:
	(room.get("hud") as Node).call("message", room.tr(key))
	AudioManager.ui("ui_tap")


## A drag that starts on a sheet (sideways = turn, down = flip) or on a door wheel (up / down = +1 / -1 per step).
func drag_started(part: String) -> bool:
	var cam: RoomCamera = room.get("cam")
	_drag_part = ""
	_drag_acc = Vector2.ZERO
	_drag_done = false
	if cam.current() == "light_table" and (part.begins_with("IA_sheet_") or part.begins_with("IA_flip_tab_")):
		_drag_part = part
		ArchiveZones.cue("c2x_sheet_slide", -6.0)
	elif cam.current() in ["cold_door", "cold_wheels"] and part.begins_with("IA_wheel_") and not bool(logic.state["cold_open"]):
		_drag_part = part
	return _drag_part != ""


func drag_moved(rel: Vector2, _pos: Vector2) -> void:
	_drag_acc += rel
	var step := DRAG_STEP_PX * maxf(1.0, DisplayServer.screen_get_scale())
	if _drag_part.begins_with("IA_wheel_"):
		var steps := int(-_drag_acc.y / step)
		if steps != 0:
			_drag_acc.y += steps * step
			logic.cold_wheel(0 if _drag_part.ends_with("_a") else 1, steps)
		return
	if _drag_done:
		return
	var i := int(_drag_part.get_slice("_", 2)) if _drag_part.begins_with("IA_sheet_") else int(_drag_part.get_slice("_", 3))
	if absf(_drag_acc.x) >= step and absf(_drag_acc.x) >= absf(_drag_acc.y):
		_drag_done = true
		logic.n3_turn_sheet(i)
	elif _drag_acc.y >= step:
		_drag_done = true
		logic.n3_flip_sheet(i)


# ====================================================================== feedback
## Event feedback (the room's _on_events calls this for every event). -> true when the event was one of ours.
func feedback(e: String) -> bool:
	var parts := e.split(":")
	match parts[0]:
		"sheet":
			if parts.size() >= 4:
				var i := int(parts[1])
				ArchiveZones.cue("c2x_sheet_flip" if int(parts[3]) != _flip_seen[i] else "c2x_sheet_turn", -2.0)
			return true
		"lit":
			return true
		"light_digits":
			ArchiveZones.cue("c2x_light_digits")
			_pulse_table()
			return true
		"cold_wheel":
			ArchiveZones.cue("c2x_cab_wheel", -2.0, randf_range(0.96, 1.05))
			return true
		"cold_frozen":
			ArchiveZones.cue("c2x_cold_frozen", -2.0)
			_try_handle_shake()
			return true
		"cold_opened":
			ArchiveZones.cue("c2x_door_cold")
			return true
	return false


func _try_handle_shake() -> void:
	var d: Node3D = models["cold_door"]
	ArchiveKit.rot(room, _tweens, ModelUtil.find(d, "IA_cold_handle"), Vector3.BACK, -10.0, true, 0.08)
	room.get_tree().create_timer(0.14).timeout.connect(func() -> void: _update_door(true))


func _pulse_table() -> void:
	if _glow_tween != null and _glow_tween.is_valid():
		_glow_tween.kill()
	_glow_tween = room.create_tween()
	_glow_tween.tween_property(_table_light, "light_energy", 1.6, 0.5)
	_glow_tween.tween_property(_table_light, "light_energy", 0.9, 1.2)
