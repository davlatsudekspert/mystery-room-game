class_name HudTestRoom
extends Node3D
## A stand-in room for the HUD tests: the logic, the touch input and the calls the HUD makes on its room, with the
## real HUD (src/ui/hud.gd) bound to it. With `with_camera`, a RoomCamera with a room view ("hall") and two
## close-ups ("desk", "drawer" inside it), and RoomBase's own Android back order (handle_back) on top of it.

var logic: RoomLogic
var touch: TouchInput
var hud: Node
var cam: RoomCamera
var taps: Array[Vector2] = [] # world taps that reached the room (TouchInput.tapped)
var pause_opened := 0
var _ending := false


## Builds the room under the scene root (deferred: the test runner is still inside the root's _ready), binds the
## HUD and waits a frame. `l` is the logic (GameState.logic, so the HUD hears its events).
static func create(l: RoomLogic, with_camera: bool = false) -> HudTestRoom:
	var r := HudTestRoom.new()
	r.logic = l
	r.touch = TouchInput.new()
	r.add_child(r.touch)
	r.touch.tapped.connect(func(p: Vector2) -> void: r.taps.append(p))
	if with_camera:
		r.cam = RoomCamera.new()
		r.add_child(r.cam)
		r.cam.add_view("hall", Vector3(0, 1.5, 2), Vector3(0, 1.2, 0), 60.0, true)
		r.cam.add_view("desk", Vector3(0, 1.3, 1), Vector3(0, 1.0, 0), 45.0)
		r.cam.add_view("drawer", Vector3(0, 1.0, 0.6), Vector3(0, 0.8, 0), 40.0)
	return r


func attach() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.add_child.call_deferred(self)
	await tree.process_frame
	hud = (load("res://src/ui/hud.gd") as GDScript).new()
	add_child(hud)
	hud.call("bind", self)
	if cam != null:
		cam.view_changed.connect(func(id: String) -> void: hud.call("set_view", id, cam.is_root(), ""))
		cam.go("hall", true)
	await tree.process_frame


func main_root() -> String:
	return "hall"


## RoomBase.go_back(): one camera step back.
func go_back() -> void:
	if cam == null:
		return
	if not cam.back() and cam.current() != main_root():
		cam.go(main_root(), true)


## RoomBase.handle_back() (Android back / Escape), as the rooms route it: the HUD first, then the camera, then
## the pause menu at the room view.
func handle_back() -> void:
	if hud.call("consume_back") or _ending:
		return
	if cam.is_root() and cam.current() == main_root():
		pause_opened += 1
		hud.call("show_pause")
		return
	go_back()


func play_opening_camera() -> void:
	pass


## Waits `seconds` of real time (tweens run on process frames).
func wait(seconds: float) -> void:
	var tree := Engine.get_main_loop() as SceneTree
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < int(seconds * 1000.0):
		await tree.process_frame


## Taps the screen at `p` (canvas px) as a finger would: a touch down and up, through the GUI.
func tap_screen(p: Vector2) -> void:
	var tree := Engine.get_main_loop() as SceneTree
	for down in [true, false]:
		var ev := InputEventScreenTouch.new()
		ev.index = 0
		ev.position = p
		ev.pressed = down
		tree.root.push_input(ev, true)
	await tree.process_frame


## Frees the room (the caller then waits a frame: a coroutine of a freed object never resumes).
func dispose() -> void:
	(Engine.get_main_loop() as SceneTree).paused = false
	queue_free()
