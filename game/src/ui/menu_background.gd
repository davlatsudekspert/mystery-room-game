class_name MenuBackground
extends Node3D
## Animated 3D backdrop of the main menu: Prof. Strand's brass gear box (Chapter 1) on Leyla's desk is the hero of
## the frame, warmly lit by the desk lamp in a dark room. The box is alive (MenuBox: it fidgets, glints, can be played
## and opens on a warm light; the start transition pushes the camera into that light), the lamp flickers faintly, and
## the camera drifts slowly around the box while always keeping it at the same place on screen (set_frame(): right of
## the menu column).
## Phone GPU budget (the menu must render on every phone): one shadowed omni (the lamp; unshadowed with safe
## graphics), one unshadowed directional fill, the dust motes (off with safe graphics), standard materials only:
## no reflection probes, decals, sky or custom 3D shaders.

const BOX_POS := Vector3(0.14, 0.78, 0.04)
const BOX_YAW_DEG := 8.0
const FOCUS_UP := 0.068 # the point kept on screen: the box centre, above its base
const BOX_SPAN := 0.34 # m: the box's apparent width (with its top and side in view) that set_frame() fits
const FOV_H := 36.0 # horizontal (KEEP_WIDTH): the box keeps its share of the width on any aspect ratio
const AZIMUTH := 32.0 # camera bearing, degrees right of the box front
const ELEVATION := 24.0
const PUSH_DIST := 0.34 # the start transition ends this share of the resting camera distance from the glow
const PUSH_ELEVATION := 30.0 # ... and looks this many degrees steeper down into the open box
const GLOW_FOCUS := Vector3(0.0, 0.09, 0.0) # the glow's point above the box origin
const LAMP_ENERGY := 1.0
const BRASS_METALLIC := 0.35 # no reflection probe here: half-metallic brass shows its gold under the lamp

signal start_goto # the start transition wants the loading flow now (once)

var _cam: Camera3D
var _lamp: OmniLight3D
var box: MenuBox
var manual := false # QA / tests drive advance() themselves
var _t := 0.0
var _screen := Vector2(0.7, 0.55) # where the box centre sits (fractions of the frame)
var _share := 0.28 # share of the frame width the box spans
static var _menu_mats: Dictionary = {}


func _ready() -> void:
	var safe := CrashGuard.safe_level() >= 2 # no shadow, no dust (CrashGuard levels)
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("050607")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("1f3034")
	env.ambient_light_energy = 0.35
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.glow_enabled = true
	env.glow_intensity = 0.7
	env.glow_bloom = 0.04
	env.glow_hdr_threshold = 1.0
	env.fog_enabled = true
	env.fog_light_color = Color("0c1416")
	env.fog_density = 0.07
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var desk := ModelUtil.spawn("desk", self, Transform3D(Basis.IDENTITY, Vector3.ZERO), "none")
	if desk != null:
		for mi in ModelUtil.find_meshes(desk):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF # the lamp's shadow pass skips the big desk
	box = MenuBox.new()
	box.name = "gear_box_menu"
	box.transform = Transform3D(Basis(Vector3.UP, deg_to_rad(BOX_YAW_DEG)), BOX_POS)
	add_child(box)
	var model := box.setup(CrashGuard.safe_level(), 0)
	box.start_goto.connect(func() -> void: start_goto.emit())
	if model != null:
		_half_metal(model)
	# storytelling around the hero, kept clear of it: the stopped clock, Leyla's tea and spectacles
	ModelUtil.spawn("flip_clock", self, Transform3D(Basis(Vector3.UP, deg_to_rad(36.0)), Vector3(-0.29, 0.78, -0.13)), "none")
	# (the tea set waits just right of the frame; the drift brings its cup to the edge now and then)
	ModelUtil.spawn("cc0/tea_set_01/tea_set_01", self, Transform3D(Basis(Vector3.UP, PI + 0.3), Vector3(0.56, 0.78, -0.26)), "none")
	ModelUtil.spawn("cc0/round_spectacles/round_spectacles", self, Transform3D(Basis(Vector3.UP, 0.9), Vector3(-0.06, 0.78, 0.26)), "none")
	_lamp = OmniLight3D.new()
	_lamp.light_color = Color("ffb46b")
	_lamp.light_energy = LAMP_ENERGY
	_lamp.omni_range = 1.1 # a tight pool: the box top is the brightest thing in the room
	_lamp.omni_attenuation = 2.0 # inverse square: the pool of light falls off fast around the box
	_lamp.position = BOX_POS + Vector3(-0.1, 0.5, 0.18) # above the box, a little toward the camera and the menu
	_lamp.shadow_enabled = not safe
	add_child(_lamp)
	var moon := DirectionalLight3D.new() # cool rim from behind (no shadow)
	moon.light_color = Color("79aec4")
	moon.light_energy = 0.5
	add_child(moon)
	moon.look_at_from_position(Vector3(1.5, 3.0, -3.0), Vector3.ZERO, Vector3.UP)
	if not safe:
		var dust := DustMotes.create(Vector3(0.6, 0.35, 0.45), 80)
		dust.position = BOX_POS + Vector3(-0.1, 0.32, 0.0)
		add_child(dust)
	_cam = Camera3D.new()
	_cam.keep_aspect = Camera3D.KEEP_WIDTH
	_cam.fov = FOV_H
	_cam.near = 0.05
	_cam.far = 20.0
	add_child(_cam)
	_place_camera(0.0)


## Frames the box: its centre at `screen` (fractions of the frame, from the top left), `share` of the frame wide.
func set_frame(screen: Vector2, share: float) -> void:
	_screen = screen
	_share = clampf(share, 0.12, 0.5)
	_place_camera(_t)


func _process(delta: float) -> void:
	if not manual:
		advance(delta)


## One step of the backdrop (the box, the lamp, the camera). _process calls it; QA and tests call it with a fixed
## step when `manual` is set.
func advance(delta: float) -> void:
	_t += delta
	var still := bool(Settings.get_value("reduce_motion"))
	box.advance(delta, still)
	if still:
		_lamp.light_energy = LAMP_ENERGY
		_place_camera(0.0)
	else:
		# a faint, irregular flicker (never a strobe)
		var f := 1.0 + 0.03 * sin(_t * 7.3) * sin(_t * 2.1 + 0.5) + 0.012 * sin(_t * 17.9)
		_lamp.light_energy = LAMP_ENERGY * f
		_place_camera(_t)


## A tap at `vp_pos` (this SubViewport's pixels): presses a knob under the finger, or closes an open lid.
## Returns true when the box did something.
func tap(vp_pos: Vector2) -> bool:
	if box.logic.phase != MenuBoxLogic.Phase.CLOSED:
		return box.tap_anywhere()
	var vp_w := maxf(1.0, get_viewport().get_visible_rect().size.x)
	var px_m := 2.0 * tan(deg_to_rad(FOV_H) * 0.5) / vp_w # metres one pixel covers, per metre of distance
	return box.tap_ray(_cam.project_ray_origin(vp_pos), _cam.project_ray_normal(vp_pos), px_m)


## New Game / Continue: wheels spin into line, the lid opens, the camera pushes into the light (see MenuBoxLogic).
func begin_start() -> void:
	box.begin_start(bool(Settings.get_value("reduce_motion")))


## 0..1: how black the transition has made the frame.
func fade() -> float:
	return box.logic.fade()


## The camera orbits the box slowly (bearing, height and distance drift on long, unrelated periods) and is aimed
## so that the box centre lands exactly on `_screen`: yaw and pitch only, the horizon stays level.
func _place_camera(t: float) -> void:
	var push := box.push() if box != null else 0.0
	var pe := push * push * (3.0 - 2.0 * push) # the start transition: in toward the glow
	var bearing := deg_to_rad(AZIMUTH + BOX_YAW_DEG + 7.0 * sin(t * TAU / 46.0))
	var el := deg_to_rad(ELEVATION + 2.5 * sin(t * TAU / 33.0 + 1.0) + PUSH_ELEVATION * pe)
	var tan_h := tan(deg_to_rad(FOV_H) * 0.5)
	var dist := BOX_SPAN / (2.0 * tan_h * _share) * (1.0 + 0.03 * sin(t * TAU / 39.0 + 2.0)) * lerpf(1.0, PUSH_DIST, pe)
	var focus := (BOX_POS + Vector3(0.0, FOCUS_UP, 0.0)).lerp(box.to_global(GLOW_FOCUS), pe)
	var screen := _screen.lerp(Vector2(0.5, 0.5), pe)
	var pos := focus + Vector3(sin(bearing) * cos(el), sin(el), cos(bearing) * cos(el)) * dist
	var vp := get_viewport().get_visible_rect().size
	var aspect := vp.x / maxf(1.0, vp.y)
	# the focus must appear at camera-space direction (a, b, -1)
	var a := (2.0 * screen.x - 1.0) * tan_h
	var b := (1.0 - 2.0 * screen.y) * tan_h / aspect
	var u := (focus - pos).normalized()
	var pitch := asin(clampf(u.y * sqrt(a * a + b * b + 1.0) / sqrt(1.0 + b * b), -1.0, 1.0)) - atan(b)
	var zp := b * sin(pitch) - cos(pitch)
	var yaw := atan2(-u.x, -u.z) - atan2(-a, -zp)
	_cam.position = pos
	_cam.rotation = Vector3(pitch, yaw, 0.0)


## Brass reflects only the black background without a reflection probe; a half-metallic copy for this scene
## keeps its gold body colour under the lamp (shared copies, standard materials).
func _half_metal(root: Node) -> void:
	for mi in ModelUtil.find_meshes(root):
		for i in mi.get_surface_override_material_count():
			var m := mi.get_surface_override_material(i)
			if m is BaseMaterial3D and m.resource_name.begins_with("M_Brass"):
				if not _menu_mats.has(m.resource_name):
					var d := (m as BaseMaterial3D).duplicate() as BaseMaterial3D
					d.metallic = BRASS_METALLIC
					_menu_mats[m.resource_name] = d
				mi.set_surface_override_material(i, _menu_mats[m.resource_name])
