class_name ArchiveRig
extends RefCounted
## Small animation and drawing helpers shared by the Chapter 2 expansion's zone builders (ArchiveLift, ArchiveGallery,
## ArchivePlate, ArchiveOffice): turn or slide a model part from its rest pose, switch a lamp, add a numeral label, drop a
## tap volume. A part's rest transform is remembered the first time it moves (meta "rest"). Pure scene helper, no logic.

var room: Node3D
var _tweens: Dictionary = {}


func _init(r: Node3D) -> void:
	room = r


## Rotate a part about `axis` (part space, applied after its rest basis) to `deg`, animated or at once.
func rot(n: Node3D, axis: Vector3, deg: float, animated: bool, dur: float = 0.4) -> void:
	if n == null:
		return
	var base := _rest(n)
	var target := Transform3D(base.basis * Basis(axis.normalized(), deg_to_rad(deg)), base.origin)
	_go(n, target, animated, dur)


## Move a part by `offset` (parent space) from its rest position.
func slide(n: Node3D, offset: Vector3, animated: bool, dur: float = 0.4) -> void:
	if n == null:
		return
	var base := _rest(n)
	_go(n, Transform3D(base.basis, base.origin + offset), animated, dur)


## Slide and rotate in one go (a part that does both must not be driven by rot() and slide() separately).
func pose(n: Node3D, offset: Vector3, axis: Vector3, deg: float, animated: bool, dur: float = 0.4) -> void:
	if n == null:
		return
	var base := _rest(n)
	_go(n, Transform3D(base.basis * Basis(axis.normalized(), deg_to_rad(deg)), base.origin + offset), animated, dur)


## Rest transform of a part (remembered on first use).
func _rest(n: Node3D) -> Transform3D:
	if not n.has_meta("rest"):
		n.set_meta("rest", n.transform)
	return n.get_meta("rest")


func _go(n: Node3D, target: Transform3D, animated: bool, dur: float) -> void:
	var k := n.get_instance_id()
	if _tweens.has(k) and (_tweens[k] as Tween).is_valid():
		(_tweens[k] as Tween).kill()
	if not animated or n.transform.is_equal_approx(target) or not n.is_inside_tree():
		n.transform = target
		return
	var from := n.transform
	var fq := from.basis.get_rotation_quaternion()
	var tq := target.basis.get_rotation_quaternion()
	var tw := room.create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tw.tween_method(func(t: float) -> void:
		if is_instance_valid(n):
			n.transform = Transform3D(Basis(fq.slerp(tq, t)), from.origin.lerp(target.origin, t)), 0.0, 1.0, dur)
	_tweens[k] = tw


## Is this part still moving?
func moving(n: Node3D) -> bool:
	return n != null and _tweens.has(n.get_instance_id()) and (_tweens[n.get_instance_id()] as Tween).is_valid() \
		and (_tweens[n.get_instance_id()] as Tween).is_running()


func lamp(n: Node3D, on: bool, color: Color, energy: float = 2.2) -> void:
	if n is MeshInstance3D:
		ModelUtil.set_emission(n as MeshInstance3D, on, color, energy)


## The bounds of a model's meshes in the model's own space (ItemIcons._aabb is global: wrong once the model stands in a zone).
static func local_aabb(n: Node3D) -> AABB:
	var out := AABB()
	var first := true
	for mi in ModelUtil.find_meshes(n):
		var xf := mi.transform
		var p := mi.get_parent()
		while p != n and p is Node3D:
			xf = (p as Node3D).transform * xf
			p = p.get_parent()
		var a := xf * mi.get_aabb()
		out = a if first else out.merge(a)
		first = false
	return out


## Gives a part (and its tap colliders) a hotspot id; its StaticBody children keep their `part` names.
static func hot(n: Node, hs: String) -> void:
	if n == null:
		return
	n.set_meta("hotspot", hs)
	for b in n.find_children("*", "StaticBody3D", true, false):
		(b as StaticBody3D).set_meta("hotspot", hs)


## A numeral (language-neutral, like the pump valves' digits) as a flat label on a surface.
func numeral(parent: Node3D, text: String, pos: Vector3, size_m: float, color: Color, rot_deg: Vector3 = Vector3.ZERO) -> Label3D:
	var l := Label3D.new()
	l.text = text
	l.font = load(UITheme.FONT_DISPLAY_BOLD)
	l.font_size = 96
	l.pixel_size = size_m / 96.0
	l.modulate = color
	l.outline_size = 0
	l.position = pos
	l.rotation_degrees = rot_deg
	l.double_sided = false
	parent.add_child(l)
	return l


## A flat picture quad (unshaded paper in lamplight: the room lamps beside it would burn a lit surface out).
static func picture(parent: Node3D, tex: Texture2D, size: Vector2, pos: Vector3, tint: Color = Color(0.78, 0.74, 0.66), unshaded: bool = true) -> MeshInstance3D:
	var quad := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = size
	quad.mesh = qm
	quad.position = pos
	var m := StandardMaterial3D.new()
	m.albedo_texture = tex
	m.albedo_color = tint
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA if tex != null else BaseMaterial3D.TRANSPARENCY_DISABLED
	if unshaded:
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	quad.material_override = m
	quad.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(quad)
	return quad


## A box-shaped warm light placed in a room.
static func omni(parent: Node3D, pos: Vector3, color: Color, energy: float, range_m: float) -> OmniLight3D:
	var l := OmniLight3D.new()
	l.light_color = color
	l.light_energy = energy
	l.omni_range = range_m
	l.shadow_enabled = false
	l.position = pos
	parent.add_child(l)
	return l
