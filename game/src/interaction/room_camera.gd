class_name RoomCamera
extends Camera3D
## View-stack camera for point-and-explore rooms.
## Root views allow free look (yaw 360°, clamped pitch, pinch zoom); focus views are fixed close-ups
## entered by tapping hotspots and left with Back. Transitions are tweened (or shortened with reduce_motion).

signal view_changed(id: String)

const PITCH_MIN := -38.0
const PITCH_MAX := 32.0
const FOV_MIN := 32.0
const FOV_MAX := 72.0

var views: Dictionary = {} # id -> {pos: Vector3, target: Vector3, fov: float, root: bool}
var stack: Array[String] = []
var yaw := 0.0
var pitch := 0.0
var zoom_fov := 60.0
var transitioning := false
var _base_basis := Basis.IDENTITY
var _tween: Tween


func add_view(id: String, pos: Vector3, target: Vector3, view_fov: float = 50.0, root: bool = false) -> void:
	views[id] = {"pos": pos, "target": target, "fov": view_fov, "root": root}


func current() -> String:
	return stack[-1] if not stack.is_empty() else ""


func is_root() -> bool:
	return not stack.is_empty() and bool(views[current()]["root"])


func depth() -> int:
	return stack.size()


func go(id: String, instant: bool = false) -> void:
	if not views.has(id) or (current() == id and not instant):
		return
	var v: Dictionary = views[id]
	if v["root"]:
		stack = [id]
		yaw = 0.0
		pitch = 0.0
		zoom_fov = v["fov"]
	else:
		var idx := stack.find(id)
		if idx >= 0:
			stack.resize(idx + 1)
		else:
			stack.append(id)
	_move_to(_view_transform(id), float(v["fov"]) if not v["root"] else zoom_fov, instant)
	view_changed.emit(id)


func back() -> bool:
	if stack.size() <= 1 or transitioning:
		return false
	stack.pop_back()
	var id := current()
	_move_to(_view_transform(id), views[id]["fov"] if not views[id]["root"] else zoom_fov, false)
	view_changed.emit(id)
	return true


func free_look(rel: Vector2) -> void:
	if not is_root() or transitioning:
		return
	var sens: float = 0.16 * float(Settings.get_value("look_sensitivity"))
	var inv := -1.0 if Settings.get_value("invert_look") else 1.0
	yaw = wrapf(yaw - rel.x * sens, -180.0, 180.0)
	pitch = clampf(pitch - rel.y * sens * inv, PITCH_MIN, PITCH_MAX)
	_apply_free_look()


func zoom(factor: float) -> void:
	if not is_root() or transitioning:
		return
	zoom_fov = clampf(zoom_fov / factor, FOV_MIN, FOV_MAX)
	fov = zoom_fov


func _apply_free_look() -> void:
	var b := _base_basis.rotated(Vector3.UP, deg_to_rad(yaw))
	b = b * Basis(Vector3.RIGHT, deg_to_rad(pitch))
	global_basis = b.orthonormalized()


func _view_transform(id: String) -> Transform3D:
	var v: Dictionary = views[id]
	var t := Transform3D(Basis.IDENTITY, v["pos"])
	t = t.looking_at(v["target"], Vector3.UP)
	if v["root"]:
		_base_basis = t.basis
	return t


func _move_to(t: Transform3D, target_fov: float, instant: bool) -> void:
	if _tween != null and _tween.is_valid():
		_tween.kill()
	if instant:
		global_transform = t
		fov = target_fov
		transitioning = false
		return
	transitioning = true
	var from := global_transform
	var from_q := from.basis.get_rotation_quaternion()
	var to_q := t.basis.get_rotation_quaternion()
	var from_fov := fov
	var dur := 0.25 if Settings.get_value("reduce_motion") else 0.65
	_tween = create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	_tween.tween_method(func(k: float) -> void:
		global_transform = Transform3D(Basis(from_q.slerp(to_q, k)), from.origin.lerp(t.origin, k))
		fov = lerpf(from_fov, target_fov, k), 0.0, 1.0, dur)
	_tween.tween_callback(func() -> void: transitioning = false)


## Small handheld sway so focus views feel alive (disabled by reduce_motion).
func _process(_delta: float) -> void:
	if transitioning or stack.is_empty() or Settings.get_value("reduce_motion"):
		return
	if not is_root():
		var t := Time.get_ticks_msec() / 1000.0
		var v: Dictionary = views[current()]
		var base := _view_transform(current())
		var sway := Vector3(sin(t * 0.5) * 0.002, sin(t * 0.7) * 0.0015, 0.0)
		global_transform = Transform3D(base.basis, base.origin + base.basis * sway)
		fov = v["fov"]
