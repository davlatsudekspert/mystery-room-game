class_name FirstGlint
extends Node3D
## A soft, slowly pulsing glow on the first thing the player should touch (the notebook on the desk in Lab 7).
## One additive billboard (no light, no shadow, no collider: taps go through it). It fades in when shown and goes
## out for good when `done` says the thing was taken.

const PERIOD_S := 2.6
const SIZE_M := 0.22

var _mat: StandardMaterial3D
var _quad: MeshInstance3D
var _t := 0.0
var _on := false
var _fade := 0.0
var _done: Callable


## Puts the glow on `target` (`lift` metres above its origin); `done` returns true once it should stay off.
static func attach(target: Node3D, lift: float, done: Callable) -> FirstGlint:
	var g := FirstGlint.new()
	g._done = done
	target.add_child(g)
	g.position = Vector3(0.0, lift, 0.0)
	g._build()
	return g


func _build() -> void:
	var grad := Gradient.new()
	grad.offsets = PackedFloat32Array([0.0, 0.3, 1.0])
	grad.colors = PackedColorArray([Color(1, 1, 1, 1), Color(1, 1, 1, 0.3), Color(1, 1, 1, 0)])
	var tex := GradientTexture2D.new()
	tex.gradient = grad
	tex.width = 128
	tex.height = 128
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(1.0, 0.5)
	_mat = StandardMaterial3D.new()
	_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	_mat.albedo_texture = tex
	_mat.albedo_color = Color(1.0, 0.8, 0.46, 0.0)
	_mat.disable_receive_shadows = true
	var qm := QuadMesh.new()
	qm.size = Vector2(SIZE_M, SIZE_M)
	qm.material = _mat
	_quad = MeshInstance3D.new()
	_quad.mesh = qm
	_quad.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_quad.visible = false
	add_child(_quad)


func show_glow() -> void:
	_on = true
	_quad.visible = true


func hide_glow() -> void:
	_on = false
	_quad.visible = false


func _process(delta: float) -> void:
	if not _on:
		return
	if _done.is_valid() and bool(_done.call()):
		hide_glow()
		return
	_t += delta
	_fade = minf(1.0, _fade + delta)
	var pulse := 0.5 + 0.5 * sin(_t * TAU / PERIOD_S)
	_mat.albedo_color.a = _fade * (0.22 + 0.34 * pulse)
