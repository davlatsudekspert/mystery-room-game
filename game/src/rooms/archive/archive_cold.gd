class_name ArchiveCold
extends RefCounted
## Chapter 2 expansion, room R4: the Cold Store (docs/CHAPTER2_EXPANSION.md sections 3, 8 N4-N6, 11 M3 M5 M6; models and pivots in
## docs/models/ch2_exp.md "R4 Cold Store"). A zone of the Archive scene (ArchiveZones): a film cellar with a bank of five
## compactus carriages on seven slots, a plan plate, a frosted window and, behind the right aisle, a chest.
## It only renders ArchiveLogic's state and forwards taps and drags to its actions:
## - N4 carriage aisle: one crank per carriage (`n4_crank`); the carriage rolls one slot along its rails (smooth, after the crank
##   has turned), or the crank clunks; an open aisle shows the shelves' far end (film cans) and, for the right one, the chest;
## - N5 frost window: three bands of frost over three finger-written signs. Drag across the pane to wipe, or tap a band (the
##   accessible way): the wipe mask of the `frost_reveal` shader is painted by the finger and committed to the logic
##   (`n5_wipe`) once a band is mostly clear. The signs are this game's (`v_symbols`);
## - N6 chest rings: three rings (`n6_turn_ring`; the next ring follows), the lid, the two blank crystals (`take("case_crystal_*")`)
##   and Leyla's note;
## - the plan plate shows which carriage hides the chest (tag with pips and a colour band, like the end tags on the carriages);
## - moments M3 (a shape passes behind the frost), M5 (steps above: dust) and M6 (the archivist's echo at the aisle end).
## The frost decals and the strip curtain carry no colliders and cast no shadows.

const VIEWS: Array[String] = ["cold", "cranks", "plan", "frost", "chest"]
const HOTSPOT_VIEW := {"cold_cranks": "cranks", "cold_plan": "plan", "cold_window": "frost", "cold_chest": "chest"}
const DEEPER := {}
const CAPTION := {"cold": "room2x.cold", "cranks": "obj2x.rail", "plan": "obj2x.rail_end", "frost": "obj2x.frost",
	"chest": "obj2x.chest"}

const WINDOW_POS := Vector3(3.845, 1.63, 2.20)
const SLOT_X0 := -3.0 # carriage slot i stands at x = SLOT_X0 + i
const CARRIAGE_Z := -1.0
const CHEST_Z := -3.14
const CRANK_Y := 1.15
const END_Z := 0.69 # the carriages' front end panels
const CAM_Z_MAX := 3.2 # the camera never leaves the room (its walls are solid boxes seen from outside)
const PLAN_SHIFT := -0.085 # the plan plate moves along the wall, clear of the pilaster at z 1.2 that covers its right edge
const MASK_W := 64
const MASK_H := 96
const BAND_ROWS := 32
const BRUSH_M := 0.075 # finger wipe radius on the pane
const PANE := Vector2(0.8, 1.2)
const BAND_DONE := 0.55 # share of a band that must be clear for a stroke to count
const LID_OPEN_DEG := -105.0
const INSIDE_LIFT := 0.16 # the open chest's floor lies near its rim, above the model's crystal and note mounts
const ROLL_DELAY := 0.5
const ROLL_SECONDS := 2.7
const RING_STEP_DEG := 60.0
const CAN_SLOTS: Array[int] = [0, 1, 2, 3, 4, 5, 6]

var room: Node3D
var zones: ArchiveZones
var root: Node3D
var logic: ArchiveLogic
var models: Dictionary = {}
var _tweens: Dictionary = {}
var _carriage: Array[Node3D] = []
var _crank: Array[Node3D] = []
var _slot_shown: Array[int] = [0, 1, 2, 3, 4]
var _crank_acc: Array[float] = [0.0, 0.0, 0.0, 0.0, 0.0]
var _rolling := 0
var _chest: Node3D
var _chest_slot := -1
var _chest_light: OmniLight3D
var _cans: Array[Node3D] = [] # film cans at the back of each slot (dressing)
var _crystal: Array[Node3D] = []
var _note: Node3D
var _ring_acc: Array[float] = [0.0, 0.0, 0.0]
var _window: Node3D
var _pane: MeshInstance3D
var _pane_mat: ShaderMaterial
var _mask: Image
var _mask_tex: ImageTexture
var _band_full: Array[bool] = [false, false, false]
var _stroke_last := Vector2(-1, -1)
var _stroke_ok := false
var _stroke_sound_at := 0
var _wipe_n := 0
var _breath: CPUParticles3D
var _dust: CPUParticles3D
var _plan_tex: ImageTexture
var _silhouette: MeshInstance3D
var _echo: Node3D
var _fitted_aisle := -1


func _init(r: Node3D, z: ArchiveZones, zone_root: Node3D) -> void:
	room = r
	zones = z
	root = zone_root
	logic = r.get("logic")


# ====================================================================== construction
func build() -> void:
	var shell := ModelUtil.spawn("room_cold", root, Transform3D.IDENTITY, "parts")
	_register("room_cold", shell, "")
	_register("frost_window", ModelUtil.spawn("frost_window", root, Transform3D(Basis(Vector3.UP, deg_to_rad(-90.0)), WINDOW_POS), "parts"), "cold_window")
	_window = models["frost_window"]
	for mi in ModelUtil.find_meshes(shell):
		if str(mi.name).begins_with("wall_") or str(mi.name) in ["ceiling", "ribs"]:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		elif str(mi.name) in ["frost_decals", "frost_patches", "strip_curtain"]:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			ArchiveKit.drop_colliders(mi) # frost decals and the strip curtain are not things: no taps, no blocked rays
	room.call("tune_shadows", _window)
	for k in ArchiveExpData.CARRIAGES:
		var c := ModelUtil.spawn("carriage_%d" % (k + 1), root, Transform3D(Basis.IDENTITY, Vector3(_slot_x(int(logic.state["aisle_pos"][k])), 0, CARRIAGE_Z)), "parts")
		_register("carriage_%d" % (k + 1), c, "cold_cranks")
		_carriage.append(c)
		_crank.append(ModelUtil.find(c, "IA_crank"))
		ArchiveKit.rename_part(_crank[k], "IA_crank_%d" % k)
		_slot_shown[k] = int(logic.state["aisle_pos"][k])
		for mi in ModelUtil.find_meshes(c):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_build_lights(shell)
	_build_pane()
	_build_plan(shell)
	_build_chest()
	_build_cans()
	_build_air()
	_build_exit()
	_define_views()
	zones.register("cold", VIEWS, HOTSPOT_VIEW, DEEPER, CAPTION)
	apply_state(false)


func _register(id: String, n: Node3D, hotspot: String) -> void:
	if n == null:
		return
	n.name = "cold_" + id
	models[id] = n
	(room.get("_roots") as Dictionary)[n] = "cold_" + id
	(room.get("models") as Dictionary)["cold_" + id] = n
	n.set_meta("hotspot", hotspot)


func _empty(shell: Node3D, nm: String) -> Vector3:
	var e := ModelUtil.find(shell, nm)
	return e.position if e != null else Vector3.ZERO


func _build_lights(shell: Node3D) -> void:
	# cold white over the bank, a fill at the front, a pale cyan glow at the window and nothing warm (docs/models/ch2_exp.md)
	for i in 3:
		ArchiveKit.omni(root, _empty(shell, "light_cold_%d" % i) + Vector3(0, -0.2, 0), Color("dce9ff"), 1.1, 5.2, 1.0)
	ArchiveKit.omni(root, Vector3(0.2, 2.3, 2.7), Color("cfe4ff"), 0.6, 6.5, 1.0)
	ArchiveKit.omni(root, _empty(shell, "light_window_fill") + Vector3(-0.3, 0, 0), Color("a8dcff"), 0.9, 3.4, 1.0)
	ArchiveKit.omni(root, Vector3(2.4, 2.0, 1.0), Color("d8e8ff"), 0.45, 3.0, 1.0) # the plan plate
	_chest_light = ArchiveKit.omni(root, Vector3(0, 1.1, -2.2), Color("d4e6ff"), 0.0, 3.0, 1.0)


func _define_views() -> void:
	var cam: RoomCamera = room.get("cam")
	var o := root.position
	cam.add_view("cold", o + Vector3(0.3, 1.55, 3.1), o + Vector3(-0.2, 1.3, -1.6), 68.0, true)
	var free: Rect2 = cam.hud_free_rect(room.get("hud"))
	# the cranks: the camera stands inside the room (CAM_Z_MAX) and widens its lens until every crank that can be where it is
	# stands inside the free area (the HUD leaves the corners); it is re-fitted whenever a carriage has come to rest
	var lo := INF
	var hi := -INF
	for k in _slot_shown.size():
		lo = minf(lo, _slot_x(_slot_shown[k]))
		hi = maxf(hi, _slot_x(_slot_shown[k]))
	lo -= 0.45
	hi += 0.45
	var vp := cam.get_viewport().get_visible_rect()
	var aspect := vp.size.x / maxf(1.0, vp.size.y)
	var fw := clampf(free.size.x / maxf(1.0, vp.size.x), 0.3, 1.0)
	var d := CAM_Z_MAX - END_Z
	var fov := clampf(rad_to_deg(2.0 * atan((hi - lo) * 0.5 / (d * aspect * fw))), 50.0, 84.0)
	var cx := (lo + hi) * 0.5
	cam.add_view("cranks", o + Vector3(cx, 1.4, CAM_Z_MAX), o + Vector3(cx, 1.2, END_Z), fov)
	var pf := cam.fit_rect(o + Vector3(3.7875, 1.55, 1.0 + PLAN_SHIFT), Vector3(-1, 0, 0), 0.25, 0.172, 42.0, free, 0.12)
	cam.add_view("plan", pf["pos"], pf["target"], 42.0)
	var ff := cam.fit_rect(o + WINDOW_POS, Vector3(-1, 0, 0), PANE.x * 0.5, PANE.y * 0.5, 50.0, free, 0.07)
	cam.add_view("frost", ff["pos"], ff["target"], 50.0)
	var chx := _slot_x(_chest_slot if _chest_slot >= 0 else 2)
	cam.add_view("chest", o + Vector3(chx, 1.85, -1.15), o + Vector3(chx, 0.3, -3.05), 44.0)


# ---------------------------------------------------------------------- the frost window
func _build_pane() -> void:
	_pane = ModelUtil.find(_window, "frost_glass") as MeshInstance3D
	ArchiveKit.drop_colliders(_pane)
	_mask = Image.create(MASK_W, MASK_H, false, Image.FORMAT_R8)
	_mask.fill(Color(0, 0, 0, 1))
	_mask_tex = ImageTexture.create_from_image(_mask)
	var src := ModelUtil.load_material("M_Decal_FrostPane") as ShaderMaterial
	_pane_mat = src.duplicate() as ShaderMaterial
	_pane_mat.set_shader_parameter("wipe_mask", _mask_tex)
	if _pane != null:
		_pane.material_override = _pane_mat
		_pane.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# this game's three signs: the model's frost_sign_k quads take the picture of the variant's symbol k
	for k in 3:
		var q := ModelUtil.find(_window, "frost_sign_%d" % k) as MeshInstance3D
		if q == null:
			continue
		ArchiveKit.drop_colliders(q)
		q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var m := ShaderMaterial.new()
		m.shader = _sign_shader()
		m.set_shader_parameter("sign", load("res://assets/textures/decals/ch2x/frost_sign_%d.png" % int(logic.state["v_symbols"][k])) as Texture2D)
		m.set_shader_parameter("wipe_mask", _mask_tex)
		m.set_shader_parameter("uv_scale", Vector2(0.22 / PANE.x, 0.22 / PANE.y))
		m.set_shader_parameter("uv_off", Vector2(0.5 + (k - 1) * 0.22 / PANE.x - 0.11 / PANE.x, 0.5 - (1 - k) * 0.4 / PANE.y - 0.11 / PANE.y))
		q.material_override = m
	# the model's clear pane lies flat (a sheet seen edge-on across the window): the frost pane replaces it
	var glass := ModelUtil.find(_window, "window_glass")
	ArchiveKit.drop_colliders(glass)
	if glass != null:
		glass.visible = false
	# the pane takes taps and drags (the model's mesh has none): one box over the glass
	var body := room.call("add_tap_area", _window, Vector3(PANE.x + 0.04, PANE.y + 0.04, 0.1), "cold_window", "IA_frost", Vector3(0, 0, 0.03)) as StaticBody3D
	body.name = "PaneTap"


## The finger-written sign under the frost: seen only where the pane has been wiped (the mask), so a thin patch of frost never
## gives a sign away. The quad's UV is mapped into the pane's UV (uv_off / uv_scale) to read the same mask the frost shader uses.
static var _sign_sh: Shader


static func _sign_shader() -> Shader:
	if _sign_sh == null:
		_sign_sh = Shader.new()
		_sign_sh.code = """shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled;
uniform sampler2D sign : source_color, filter_linear_mipmap;
uniform sampler2D wipe_mask : filter_linear;
uniform vec2 uv_scale = vec2(0.275, 0.183);
uniform vec2 uv_off = vec2(0.0);
void fragment() {
	vec4 s = texture(sign, UV);
	float w = texture(wipe_mask, uv_off + UV * uv_scale).r;
	ALBEDO = vec3(0.86, 0.95, 1.0);
	ALPHA = clamp(s.a * 1.2, 0.0, 1.0) * smoothstep(0.3, 0.7, w);
}
"""
	return _sign_sh


## The pane's UV (0..1, V 0 = top) under a screen point, or (-1, -1) when the ray misses the pane.
func _pane_uv(screen: Vector2) -> Vector2:
	var cam: RoomCamera = room.get("cam")
	var from := cam.project_ray_origin(screen)
	var dir := cam.project_ray_normal(screen)
	var gt := _pane.global_transform
	var plane := Plane(gt.basis.z.normalized(), gt.origin)
	var hit: Variant = plane.intersects_ray(from, dir)
	if hit == null:
		return Vector2(-1, -1)
	var local := gt.affine_inverse() * (hit as Vector3)
	var uv := Vector2((local.x + PANE.x * 0.5) / PANE.x, 0.5 - local.y / PANE.y)
	if uv.x < -0.02 or uv.x > 1.02 or uv.y < -0.02 or uv.y > 1.02:
		return Vector2(-1, -1)
	return uv


func _band_of(uv: Vector2) -> int:
	return clampi(int(uv.y * 3.0), 0, 2)


func _paint(uv: Vector2) -> void:
	var c := Vector2(uv.x * MASK_W, uv.y * MASK_H)
	var r := BRUSH_M / PANE.x * MASK_W
	for y in range(maxi(0, int(c.y - r) - 1), mini(MASK_H, int(c.y + r) + 2)):
		for x in range(maxi(0, int(c.x - r) - 1), mini(MASK_W, int(c.x + r) + 2)):
			var d := Vector2(x + 0.5, y + 0.5).distance_to(c)
			if d <= r:
				var v := clampf((r - d) / (r * 0.4), 0.0, 1.0)
				if v > _mask.get_pixel(x, y).r:
					_mask.set_pixel(x, y, Color(v, v, v, 1))


func _band_clear_share(b: int) -> float:
	var n := 0
	for y in range(b * BAND_ROWS, (b + 1) * BAND_ROWS):
		for x in MASK_W:
			if _mask.get_pixel(x, y).r >= 0.5:
				n += 1
	return float(n) / float(MASK_W * BAND_ROWS)


## Makes a band's rows fully clear, sweeping left to right when `animated`.
func _fill_band(b: int, animated: bool) -> void:
	if _band_full[b]:
		return
	_band_full[b] = true
	if not animated:
		_mask.fill_rect(Rect2i(0, b * BAND_ROWS, MASK_W, BAND_ROWS), Color(1, 1, 1, 1))
		_mask_tex.update(_mask)
		return
	var tw := room.create_tween()
	tw.tween_method(func(t: float) -> void:
		_mask.fill_rect(Rect2i(0, b * BAND_ROWS, int(MASK_W * t), BAND_ROWS), Color(1, 1, 1, 1))
		_mask_tex.update(_mask), 0.0, 1.0, 0.5)
	tw.tween_callback(func() -> void:
		_mask.fill_rect(Rect2i(0, b * BAND_ROWS, MASK_W, BAND_ROWS), Color(1, 1, 1, 1))
		_mask_tex.update(_mask))


# ---------------------------------------------------------------------- the plan plate
func _build_plan(shell: Node3D) -> void:
	_plan_tex = ImageTexture.create_from_image(plan_image(logic.aisle_bay()))
	var plate := ModelUtil.find(shell, "plan_plate") as MeshInstance3D
	if plate != null:
		plate.material_override = ArchiveKit.decal_material(_plan_tex, false)
		plate.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		plate.position.z += PLAN_SHIFT
	var frame := ModelUtil.find(shell, "plan_frame") as Node3D
	if frame != null:
		frame.position.z += PLAN_SHIFT
	room.call("add_tap_area", root, Vector3(0.12, 0.5, 0.64), "cold_plan", "Plan_plate", Vector3(3.74, 1.55, 1.0 + PLAN_SHIFT))
	# the light well's glow card: bright white would swallow the pale signs under the frost, so it is a dimmer pale cyan
	var glow := ModelUtil.find(shell, "window_glow") as MeshInstance3D
	if glow != null:
		var gm := StandardMaterial3D.new()
		gm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		gm.albedo_color = Color(0.2, 0.32, 0.42)
		gm.cull_mode = BaseMaterial3D.CULL_DISABLED
		glow.material_override = gm


## The plan as the plate prints it: the five carriages' end tags in a row, the one that hides the chest framed, and the chest
## drawn at the aisle that opens in front of it (the gap on its left). No words; the tags are the ones on the carriages.
static func plan_image(bay: int) -> Image:
	var img := Image.create(512, 352, false, Image.FORMAT_RGBA8)
	img.fill(Color("e6dcc0"))
	var ink := Color("2a2118")
	var atlas_tex := load("res://assets/textures/decals/ch2x/carriage_tags.png") as Texture2D
	var atlas: Image = atlas_tex.get_image() if atlas_tex != null else null
	if atlas != null and atlas.is_compressed():
		atlas.decompress()
	if atlas != null:
		atlas.convert(Image.FORMAT_RGBA8)
	var tw := 78
	var th := 58
	var gap := 18
	var x0 := (512 - (5 * tw + 4 * gap)) / 2
	var ty := 40
	for k in 5:
		var x := x0 + k * (tw + gap)
		if atlas != null:
			var tag := atlas.get_region(Rect2i(256 * k, 0, 256, 192))
			tag.resize(tw, th, Image.INTERPOLATE_BILINEAR)
			img.blit_rect(tag, Rect2i(0, 0, tw, th), Vector2i(x, ty))
		else:
			img.fill_rect(Rect2i(x, ty, tw, th), Color("bdb59c"))
		# the carriage under its tag: a plan view, a dark block between its two rails
		img.fill_rect(Rect2i(x + 4, ty + th + 12, tw - 8, 92), Color(0.72, 0.68, 0.58))
		ArchiveKit.line(img, Vector2(x + 4, ty + th + 12), Vector2(x + tw - 4, ty + th + 12), 3.0, ink)
		ArchiveKit.line(img, Vector2(x + 4, ty + th + 104), Vector2(x + tw - 4, ty + th + 104), 3.0, ink)
		ArchiveKit.line(img, Vector2(x + 4, ty + th + 12), Vector2(x + 4, ty + th + 104), 3.0, ink)
		ArchiveKit.line(img, Vector2(x + tw - 4, ty + th + 12), Vector2(x + tw - 4, ty + th + 104), 3.0, ink)
	# the framed carriage and the aisle on its left
	var bx := x0 + bay * (tw + gap)
	var red := Color("a8321f")
	for d in 3:
		img.fill_rect(Rect2i(bx - 5 - d, ty - 5 - d, tw + 10 + 2 * d, 2), red)
		img.fill_rect(Rect2i(bx - 5 - d, ty + th + 3 + d, tw + 10 + 2 * d, 2), red)
		img.fill_rect(Rect2i(bx - 5 - d, ty - 5 - d, 2, th + 10 + 2 * d), red)
		img.fill_rect(Rect2i(bx + tw + 3 + d, ty - 5 - d, 2, th + 10 + 2 * d), red)
	var ax := bx - gap / 2
	for yy in range(ty + th + 20, ty + th + 104, 14): # the aisle: dashes down the gap
		ArchiveKit.line(img, Vector2(ax, yy), Vector2(ax, yy + 7), 3.0, red)
	ArchiveKit.arrow_head(img, Vector2(ax, ty + th + 128), Vector2(0, 1), 18.0, red)
	# the chest, drawn small and plain at the end of the aisle
	var cx := ax
	var cy := ty + th + 168
	img.fill_rect(Rect2i(cx - 34, cy - 4, 68, 34), Color("7a4f2a"))
	ArchiveKit.ring(img, Vector2(cx, cy - 4), 34.0, 8.0, Color("5a3a1e"), PI, TAU)
	for dx in [-17, 0, 17]:
		ArchiveKit.disc(img, Vector2(cx + dx, cy + 14), 6.0, Color("d8b660"))
	ArchiveKit.line(img, Vector2(30, 322), Vector2(482, 322), 3.0, ink) # the back wall
	return img


# ---------------------------------------------------------------------- the chest and the cans
func _build_chest() -> void:
	_chest = ModelUtil.spawn("cold_chest", root, Transform3D(Basis.IDENTITY, Vector3(_slot_x(2), 0, CHEST_Z)), "parts")
	_register("cold_chest", _chest, "cold_chest")
	if _chest == null:
		return
	for k in 3:
		ArchiveKit.rename_part(ModelUtil.find(_chest, "IA_ring_%d" % k), "IA_ring_%d" % k)
	for k in 2:
		var mount := ModelUtil.find(_chest, "crystal_mount_%d" % k)
		var cr := ModelUtil.spawn("lumen_crystal", _chest, Transform3D(Basis.IDENTITY, (mount.position if mount != null else Vector3.ZERO) + Vector3(0, INSIDE_LIFT + 0.07, 0.02)), "none")
		if cr == null:
			_crystal.append(null)
			continue
		cr.name = "Item_case_crystal_%d" % (k + 1)
		cr.scale = Vector3.ONE * 1.6
		cr.rotation_degrees = Vector3(0, 0, 90) # lying on its side in the chest
		_crystal.append(cr)
		ArchiveKit.item_body(cr, "cold_chest", "Item_case_crystal_%d" % (k + 1), 0.1)
	var nm := ModelUtil.find(_chest, "note_mount")
	_note = Node3D.new()
	_note.name = "Note_cold"
	_note.position = (nm.position if nm != null else Vector3(0, 0.31, 0.15)) + Vector3(0, INSIDE_LIFT, 0.0)
	_note.rotation_degrees = Vector3(0, 8, 0)
	_chest.add_child(_note)
	var q := ArchiveKit.quad(_note, Vector2(0.11, 0.075), Vector3.ZERO, ArchiveKit.decal_material(_note_texture(), false), "paper")
	q.rotation_degrees.x = -90.0
	room.call("add_tap_area", _note, Vector3(0.16, 0.06, 0.12), "cold_chest", "Note_cold", Vector3(0, 0.02, 0))
	room.call("tune_shadows", _chest)


func _note_texture() -> ImageTexture:
	var img := Image.create(110, 75, false, Image.FORMAT_RGBA8)
	img.fill(Color("d9d0b8"))
	for k in 4:
		ArchiveKit.line(img, Vector2(10, 14 + k * 16), Vector2(98 - (k % 2) * 30, 14 + k * 16), 2.0, Color(0.25, 0.23, 0.22, 0.75))
	return ImageTexture.create_from_image(img)


## Film cans stand at the far end of every aisle but the chest's: a wrong aisle shows lore (docs/CHAPTER2_EXPANSION.md B4).
func _build_cans() -> void:
	for s in CAN_SLOTS:
		var holder := Node3D.new()
		holder.name = "cans_%d" % s
		holder.position = Vector3(_slot_x(s), 0, CHEST_Z + 0.1)
		root.add_child(holder)
		var y := 0.0
		for j in 3:
			var id := "film_can_%d" % ((s + j * 2) % 4 + 1)
			var can := ModelUtil.spawn(id, holder, Transform3D.IDENTITY, "none")
			if can == null:
				continue
			var ab := ItemIcons._aabb(can)
			var h := ab.size.y
			can.position = Vector3((j - 1) * 0.04, y + h * 0.5, 0.0)
			can.rotation_degrees.y = float((s * 37 + j * 71) % 90)
			y += h
			for mi in ModelUtil.find_meshes(can):
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_cans.append(holder)


func _build_exit() -> void:
	# the doorway in the west wall back to the Night Cell
	room.call("add_tap_area", root, Vector3(0.5, 2.2, 0.95), "cold_exit", "Exit_cell", Vector3(-3.72, 1.1, 2.2))


# ---------------------------------------------------------------------- the air: breath, dust
func _build_air() -> void:
	_breath = _puffs(18, 3.0, Vector3(0, 0.02, -0.22), 0.1, 0.16)
	_breath.position = Vector3(0, 1.55, 2.7)
	root.add_child(_breath)
	_dust = _puffs(14, 2.4, Vector3(0, -0.35, 0), 0.05, 0.1)
	_dust.position = Vector3(0, 3.1, -0.6)
	_dust.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	_dust.emission_box_extents = Vector3(1.6, 0.05, 1.0)
	_dust.one_shot = true
	_dust.emitting = false
	_dust.explosiveness = 0.6
	_dust.gravity = Vector3(0, -0.25, 0)
	_dust.direction = Vector3(0, -1, 0)
	_dust.spread = 8.0
	root.add_child(_dust)


func _puffs(amount: int, lifetime: float, vel: Vector3, size_a: float, size_b: float) -> CPUParticles3D:
	var p := CPUParticles3D.new()
	p.amount = amount
	p.lifetime = lifetime
	p.preprocess = lifetime
	p.local_coords = false
	p.direction = vel.normalized()
	p.spread = 14.0
	p.initial_velocity_min = vel.length() * 0.7
	p.initial_velocity_max = vel.length() * 1.2
	p.gravity = Vector3.ZERO
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var qm := QuadMesh.new()
	qm.size = Vector2(size_a, size_a)
	p.mesh = qm
	p.scale_amount_min = 0.8
	p.scale_amount_max = 1.0 + size_b / maxf(size_a, 0.001)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	m.albedo_texture = ArchiveCell._soft_dot()
	m.vertex_color_use_as_albedo = true
	m.albedo_color = Color(0.9, 0.96, 1.0, 0.3)
	p.material_override = m
	var ramp := Gradient.new()
	ramp.set_color(0, Color(1, 1, 1, 0.0))
	ramp.add_point(0.3, Color(1, 1, 1, 0.45))
	ramp.set_color(ramp.get_point_count() - 1, Color(1, 1, 1, 0.0))
	p.color_ramp = ramp
	return p


# ====================================================================== state
func _slot_x(slot: int) -> float:
	return SLOT_X0 + float(slot)


func apply_state(animated: bool) -> void:
	var s := logic.state
	var pos: Array = s["aisle_pos"]
	var moved := false
	for k in _carriage.size():
		var slot := int(pos[k])
		if slot != _slot_shown[k]:
			_slot_shown[k] = slot
			_roll(k, _slot_x(slot), animated)
			moved = true
		elif not animated:
			_carriage[k].position.x = _slot_x(slot)
	if moved and not animated:
		_define_views()
	_update_chest(animated)
	for b in 3:
		if int(s["wiped"][b]) == 1:
			_fill_band(b, animated)
	_pane_mat.set_shader_parameter("reveal", 1.0)
	_update_rings(animated)


## Carriage k rolls to x: after the crank has turned a little, eased in and out, the rails' rumble underneath.
func _roll(k: int, x: float, animated: bool) -> void:
	var c := _carriage[k]
	var id := c.get_instance_id()
	if _tweens.has(id) and (_tweens[id] as Tween).is_valid():
		(_tweens[id] as Tween).kill()
	if not animated:
		c.position.x = x
		return
	_rolling += 1
	var tw := room.create_tween()
	tw.tween_interval(ROLL_DELAY)
	tw.tween_property(c, "position:x", x, ROLL_SECONDS).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_callback(func() -> void: _rolled())
	_tweens[id] = tw


func _rolled() -> void:
	_rolling = maxi(0, _rolling - 1)
	if _rolling > 0:
		return
	_define_views()
	var cam: RoomCamera = room.get("cam")
	if cam.current() in ["cranks", "chest"]:
		cam.refresh()
	_update_chest(true)
	if bool(logic.state["aisle"]) and cam.current() == "cranks" and not bool(logic.state["chest_open"]):
		cam.go("chest") # the aisle stands open: the camera walks down it to the chest


func _chest_slot_now() -> int:
	var bay := logic.aisle_bay()
	return int((logic.state["aisle_pos"] as Array)[bay]) - 1


func _update_chest(animated: bool) -> void:
	var s := logic.state
	var found := bool(s["aisle"])
	var slot := _chest_slot_now() if found else -1
	if slot != _chest_slot:
		_chest_slot = slot
		_fitted_aisle = slot
		if slot >= 0:
			_chest.position.x = _slot_x(slot)
			_define_views()
	var show := found and _rolling == 0
	room.call("set_present", _chest, show)
	_chest_light.light_energy = 0.9 if show else 0.0
	_chest_light.position = Vector3(_slot_x(maxi(slot, 0)), 1.1, -2.2)
	for i in _cans.size():
		_cans[i].visible = not (show and i == slot)
	ArchiveKit.rot(room, _tweens, ModelUtil.find(_chest, "IA_lid"), Vector3.RIGHT, LID_OPEN_DEG if s["chest_open"] else 0.0, animated, 1.0)
	for k in 2:
		if _crystal[k] != null:
			room.call("set_present", _crystal[k], bool(s["chest_open"]) and logic.can_take("case_crystal_%d" % (k + 1)))
	room.call("set_present", _note, bool(s["chest_open"]))


func _update_rings(animated: bool) -> void:
	var rings: Array = logic.state["rings"]
	for i in 3:
		var want := _ring_acc[i] + fposmod(float(int(rings[i])) * RING_STEP_DEG - _ring_acc[i], 360.0)
		_ring_acc[i] = want
		ArchiveKit.rot(room, _tweens, ModelUtil.find(_chest, "IA_ring_%d" % i), Vector3.BACK, want, animated, 0.22)


func on_enter() -> void:
	_define_views()
	apply_state(false)
	_breath.emitting = true


func on_view(view: String) -> void:
	_breath.emitting = view == "cold"
	if view in ["cranks", "chest"]:
		_define_views() # the framing follows where the carriages stand now (the camera has already started; refresh settles it)
		(room.get("cam") as RoomCamera).refresh()


# ====================================================================== taps and drags
## -> true when the tap was handled here.
func interact(hs: String, part: String) -> bool:
	var cam: RoomCamera = room.get("cam")
	var cur := cam.current()
	match hs:
		"cold_cranks":
			if cur != "cranks":
				cam.go("cranks")
			elif part.begins_with("IA_crank_"):
				logic.n4_crank(int(part.get_slice("_", 2)))
			else:
				_say("obj2x.rail")
			return true
		"cold_plan":
			if cur != "plan":
				cam.go("plan")
			else:
				(room.get("hud") as Node).call("_show_zoom", _plan_tex, room.tr("obj2x.rail_end"))
			return true
		"cold_window":
			if cur != "frost":
				cam.go("frost")
			elif part == "IA_frost":
				_tap_pane()
			else:
				_say("obj2x.frost")
			return true
		"cold_chest":
			if cur != "chest":
				cam.go("chest")
			elif part.begins_with("IA_ring_"):
				logic.n6_turn_ring(int(part.get_slice("_", 2)))
			elif part.begins_with("Item_case_crystal_"):
				logic.take("case_crystal_" + part.substr(part.length() - 1))
			elif part == "Note_cold":
				(room.get("hud") as Node).call("_show_paper", room.tr("doc2x.cold_note"), room.tr("obj2x.chest"))
			else:
				_say("obj2x.chest")
			return true
		"cold_exit":
			logic.enter_room("cell")
			return true
	return false


func _say(key: String) -> void:
	(room.get("hud") as Node).call("message", room.tr(key))
	AudioManager.ui("ui_tap")


## A tap on the pane wipes the band under the finger (the way without a drag).
func _tap_pane() -> void:
	var uv := _pane_uv(room.get("tap_pos"))
	var band := _band_of(uv) if uv.x >= 0.0 else 1
	logic.n5_wipe(band)


## A drag that starts on the pane is a finger wiping it.
func drag_started(part: String) -> bool:
	if part != "IA_frost" or (room.get("cam") as RoomCamera).current() != "frost":
		return false
	_stroke_last = Vector2(-1, -1)
	var uv := _pane_uv(room.get("drag_pos"))
	_stroke_ok = bool(logic.state["aisle"]) and logic.has_item("wipe_cloth")
	if not _stroke_ok:
		logic.n5_wipe(_band_of(uv) if uv.x >= 0.0 else 1) # says why not (the shelves, the cloth)
	return true


func drag_moved(_rel: Vector2, pos: Vector2) -> void:
	if not _stroke_ok:
		return
	var uv := _pane_uv(pos)
	if uv.x < 0.0:
		_stroke_last = Vector2(-1, -1)
		return
	var a := _stroke_last if _stroke_last.x >= 0.0 else uv
	var steps := maxi(1, int(a.distance_to(uv) / 0.02))
	for i in range(1, steps + 1):
		_paint(a.lerp(uv, float(i) / float(steps)))
	_stroke_last = uv
	_mask_tex.update(_mask)
	var now := Time.get_ticks_msec()
	if now - _stroke_sound_at > 420:
		_stroke_sound_at = now
		_wipe_n += 1
		ArchiveZones.cue("c2x_frost_wipe_%d" % (1 + _wipe_n % 4), -6.0)
	for b in 3:
		if int(logic.state["wiped"][b]) == 0 and _band_clear_share(b) >= BAND_DONE:
			logic.n5_wipe(b) # the band is clear: the logic records it, apply_state finishes the rest of the band


# ====================================================================== feedback
## Event feedback (the room's _on_events calls this for every event). -> true when the event was one of ours.
func feedback(e: String) -> bool:
	var parts := e.split(":")
	match parts[0]:
		"crank":
			var k := int(parts[1])
			var dir := signi(int(parts[2]) - _slot_shown[k])
			_spin_crank(k, 1.0 if dir >= 0 else -1.0)
			ArchiveZones.cue("c2x_crank", -2.0)
			room.get_tree().create_timer(1.2).timeout.connect(func() -> void: ArchiveZones.cue("c2x_carriage_roll", -4.0))
			return true
		"clunk":
			var k := int(parts[1])
			ArchiveZones.cue("c2x_carriage_clunk")
			_jolt(k)
			return true
		"aisle_found":
			ArchiveZones.cue("c2x_aisle_found")
			return true
		"aisle_lore":
			return true
		"band_wiped":
			ArchiveZones.cue("c2x_frost_wipe_%d" % (1 + int(parts[1]) % 4), -2.0)
			return true
		"frost_done":
			ArchiveZones.cue("c2x_frost_done")
			return true
		"ring":
			ArchiveZones.cue("c2x_ring_click", -1.0, randf_range(0.97, 1.04))
			return true
		"chest_sealed":
			ArchiveZones.cue("c2x_chest_sealed")
			return true
		"chest_opened":
			ArchiveZones.cue("c2x_chest_unlock")
			return true
	return false


func _spin_crank(k: int, dir: float) -> void:
	_crank_acc[k] += 360.0 * dir
	ArchiveKit.rot(room, _tweens, _crank[k], Vector3.BACK, -_crank_acc[k], true, 1.2)


func _jolt(k: int) -> void:
	var c := _carriage[k]
	var x := c.position.x
	var tw := room.create_tween()
	for d: float in [0.02, -0.015, 0.01, 0.0]:
		tw.tween_property(c, "position:x", x + d, 0.05)
	ArchiveKit.rot(room, _tweens, _crank[k], Vector3.BACK, -_crank_acc[k] - 28.0, true, 0.08)
	room.get_tree().create_timer(0.14).timeout.connect(func() -> void: ArchiveKit.rot(room, _tweens, _crank[k], Vector3.BACK, -_crank_acc[k], true, 0.12))


# ====================================================================== moments
## M3 "shadow on the frost": a slow dark shape passes behind the pane, right to left, and is gone.
func moment_m3(seconds: float, _sting: bool) -> void:
	if _silhouette == null:
		_silhouette = ArchiveKit.quad(_window, Vector2(0.46, 1.1), Vector3(0.6, -0.05, -0.2), ArchiveKit.decal_material(_silhouette_texture(), true, 5), "silhouette")
	_silhouette.visible = true
	_silhouette.position = Vector3(0.62, -0.05, -0.2)
	var m := _silhouette.material_override as StandardMaterial3D
	m.albedo_color = Color(1, 1, 1, 0.0)
	var tw := room.create_tween()
	tw.tween_property(m, "albedo_color:a", 0.8, seconds * 0.2)
	tw.parallel().tween_property(_silhouette, "position:x", -0.62, seconds * 0.85).set_trans(Tween.TRANS_SINE)
	tw.parallel().tween_property(m, "albedo_color:a", 0.0, seconds * 0.2).set_delay(seconds * 0.65)
	tw.tween_callback(func() -> void: _silhouette.visible = false)


func _silhouette_texture() -> ImageTexture:
	var img := Image.create(64, 160, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var dark := Color(0.02, 0.03, 0.05, 1.0)
	ArchiveKit.disc(img, Vector2(32, 34), 15.0, dark)
	ArchiveKit.line(img, Vector2(32, 48), Vector2(32, 54), 14.0, dark)
	for y in range(56, 160): # shoulders and a long coat
		var half := 14.0 + minf(float(y - 56), 14.0) * 1.3 if y < 72 else 32.0 - float(y - 72) * 0.04
		img.fill_rect(Rect2i(int(32.0 - half), y, int(half * 2.0), 1), dark)
	img.fill_rect(Rect2i(0, 0, 1, 1), Color(0, 0, 0, 0))
	# a soft edge: the pane is frosted, the shape is not sharp
	img.resize(32, 80, Image.INTERPOLATE_BILINEAR)
	img.resize(64, 160, Image.INTERPOLATE_BILINEAR)
	return ImageTexture.create_from_image(img)


## M5 "steps above": dust trickles from the vault between four slow footfalls.
func moment_m5(_seconds: float, sting: bool) -> void:
	if not sting:
		return
	var tw := room.create_tween()
	var at := 0.0
	for t: float in [0.5, 1.7, 2.9, 4.1]:
		tw.tween_interval(t - at)
		at = t
		tw.tween_callback(func() -> void:
			_dust.restart()
			_dust.emitting = true)


## M6 "echo at the aisle end": the archivist's echo stands in the opened aisle, turns a can in its hands and fades.
func moment_m6(seconds: float, _sting: bool) -> void:
	var guard := 0
	while _rolling > 0 and guard < 60:
		guard += 1
		await room.get_tree().create_timer(0.25).timeout
	if _chest_slot < 0:
		return
	var x := _slot_x(_chest_slot)
	var mat := ShaderMaterial.new()
	mat.shader = load("res://src/fx/echo.gdshader")
	_echo = ModelUtil.spawn("echo_archivist", root, Transform3D(Basis(Vector3.UP, deg_to_rad(8.0)), Vector3(x, 0, -2.15)), "none")
	if _echo == null:
		return
	for mi in ModelUtil.find_meshes(_echo):
		mi.material_override = mat
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var can := ModelUtil.spawn("film_can_2", root, Transform3D(Basis.IDENTITY, Vector3(x + 0.18, 1.02, -1.95)), "none")
	if can != null:
		for mi in ModelUtil.find_meshes(can):
			mi.material_override = mat
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mat.set_shader_parameter("intensity", 0.0)
	var tw := room.create_tween()
	tw.tween_method(func(v: float) -> void: mat.set_shader_parameter("intensity", v), 0.0, 0.9, seconds * 0.25)
	if can != null:
		tw.parallel().tween_property(can, "rotation_degrees:y", 360.0, seconds * 0.7)
	tw.tween_interval(seconds * 0.4)
	tw.tween_method(func(v: float) -> void: mat.set_shader_parameter("intensity", v), 0.9, 0.0, seconds * 0.35)
	tw.tween_callback(func() -> void:
		if is_instance_valid(_echo):
			_echo.queue_free()
		if can != null and is_instance_valid(can):
			can.queue_free())
