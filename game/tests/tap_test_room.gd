class_name TapTestRoom
extends RoomBase
## A stand-in room for the tap-assist tests: RoomBase's own raycast, tap assist and tap handling over a handful of
## collider boxes, a camera 1 m in front of the origin looking at it, and a fake HUD that reports the blocked rects
## the test sets. Nothing is rendered; the boxes only exist for the physics ray.


class FakeHud extends Node:
	var rects: Array[Rect2] = []

	func blocked_rects() -> Array[Rect2]:
		return rects

	func set_view(_id: String, _root: bool, _caption: String) -> void:
		pass


var taps: Array[Dictionary] = [] # what interact() received: {hotspot, part}
var far_hotspots: Array[String] = [] # hotspots whose own view is another one: out of reach from here


static func create() -> TapTestRoom:
	var r := TapTestRoom.new()
	r.logic = RoomLogic.new()
	r.hud = FakeHud.new()
	r.add_child(r.hud)
	r.build_camera()
	r.cam.add_view("hall", Vector3(0, 0, 1), Vector3(0, 0, 0), 40.0, true)
	return r


## Adds the room under the scene root, puts the camera in place and lets the physics server see the boxes.
func attach() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.add_child.call_deferred(self)
	await tree.process_frame
	cam.go("hall", true)
	await settle()


## Two physics frames: boxes added since the last frame are in the ray queries after this.
func settle() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	await tree.physics_frame
	await tree.physics_frame
	await tree.process_frame


## A collider box. `part` "" is a plain surface (a wall, the furniture a control sits on).
func add_box(pos: Vector3, size: Vector3, part: String = "", hotspot: String = "t") -> StaticBody3D:
	var holder := Node3D.new()
	holder.position = pos
	add_child(holder)
	return add_tap_area(holder, size, hotspot, part)


func dispose() -> void:
	if is_inside_tree():
		get_parent().remove_child(self)
	queue_free()


func hotspot_view(hs: String) -> String:
	return "far" if far_hotspots.has(hs) else ""


func interact(hs: String, part: String, _r: Dictionary) -> void:
	taps.append({"hotspot": hs, "part": part})
