class_name MenuBackground
extends Node3D
## Animated 3D backdrop for menus: the Lab 7 desk in moonlight with drifting dust and a slow dolly.

var _cam: Camera3D
var _t := 0.0


func _ready() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("07080a")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("223236")
	env.ambient_light_energy = 0.4
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.glow_enabled = true
	env.fog_enabled = true
	env.fog_light_color = Color("101a1c")
	env.fog_density = 0.05
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	ModelUtil.spawn("desk", self, Transform3D(Basis.IDENTITY, Vector3(0, 0, 0)), "none")
	ModelUtil.spawn("flip_clock", self, Transform3D(Basis(Vector3.UP, 0.15), Vector3(-0.5, 0.78, -0.15)), "none")
	ModelUtil.spawn("cc0/tea_set_01/tea_set_01", self, Transform3D(Basis(Vector3.UP, -0.3), Vector3(0.5, 0.78, -0.1)), "none")
	ModelUtil.spawn("cc0/round_spectacles/round_spectacles", self, Transform3D(Basis(Vector3.UP, 0.6), Vector3(-0.1, 0.78, 0.15)), "none")
	var lamp := OmniLight3D.new()
	lamp.light_color = Color("ffb46b")
	lamp.light_energy = 1.4
	lamp.omni_range = 2.4
	lamp.position = Vector3(-0.6, 1.25, -0.1)
	lamp.shadow_enabled = true
	add_child(lamp)
	var moon := DirectionalLight3D.new()
	moon.light_color = Color("7fa7d9")
	moon.light_energy = 0.6
	add_child(moon)
	moon.look_at_from_position(Vector3(1.5, 3.0, -3.0), Vector3.ZERO, Vector3.UP)
	var dust := DustMotes.create(Vector3(1.5, 0.8, 1.0), 90)
	dust.position = Vector3(0, 1.2, 0.3)
	add_child(dust)
	_cam = Camera3D.new()
	_cam.fov = 42.0
	add_child(_cam)


func _process(delta: float) -> void:
	_t += delta
	var a := sin(_t * 0.07) * 0.35
	_cam.position = Vector3(1.15 * sin(a) + 0.35, 1.32 + 0.04 * sin(_t * 0.2), 1.45 * cos(a))
	_cam.look_at(Vector3(-0.1, 0.82, -0.1), Vector3.UP)
