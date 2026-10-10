class_name HudTestRoom
extends RoomBase
## A stand-in room for the HUD tests: RoomBase itself (its Android back order, camera steps and HUD binding) with
## no models, the real HUD (src/ui/hud.gd) and the logic given. With `with_camera`, a RoomCamera with a room view
## ("hall", RoomBase's main root) and two close-ups ("desk", and "drawer" inside it).

var taps: Array[Vector2] = [] # world taps that reached the room (TouchInput.tapped)


## Builds the room under the scene root (deferred: the test runner is still inside the root's _ready), binds the
## HUD and waits a frame. `l` is the logic (GameState.logic, so the HUD hears its events).
static func create(l: RoomLogic, with_camera: bool = false) -> HudTestRoom:
	var r := HudTestRoom.new()
	r.logic = l
	r.touch = TouchInput.new()
	r.add_child(r.touch)
	r.touch.tapped.connect(func(p: Vector2) -> void: r.taps.append(p))
	if with_camera:
		r.build_camera()
		r.cam.add_view("hall", Vector3(0, 1.5, 2), Vector3(0, 1.2, 0), 60.0, true)
		r.cam.add_view("desk", Vector3(0, 1.3, 1), Vector3(0, 1.0, 0), 45.0)
		r.cam.add_view("drawer", Vector3(0, 1.0, 0.6), Vector3(0, 0.8, 0), 40.0)
	return r


func attach() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.add_child.call_deferred(self)
	await tree.process_frame
	build_hud()
	if cam != null:
		cam.go("hall", true)
	await tree.process_frame


func play_opening_camera() -> void:
	pass


## Waits `seconds` of real time (tweens run on process frames). Bails out when the room has left the tree, and
## after a frame limit, so a failing test fails fast instead of hanging the run.
func wait(seconds: float) -> void:
	var tree := Engine.get_main_loop() as SceneTree
	var t0 := Time.get_ticks_msec()
	var frames := 0
	var limit := int(seconds * 240.0) + 10
	while Time.get_ticks_msec() - t0 < int(seconds * 1000.0) and frames < limit:
		if not is_instance_valid(self) or not is_inside_tree():
			return
		await tree.process_frame
		frames += 1


## Waits, frame by frame, until `cond` is true; false when the room has left the tree or `max_seconds` of real time
## have gone by. The cap is generous and only a hang reaches it: the wait follows the game's own frames (tweens
## advance by frame time), so a loaded machine just takes longer instead of failing a fixed-delay check.
func wait_until(cond: Callable, max_seconds: float = 20.0) -> bool:
	var tree := Engine.get_main_loop() as SceneTree
	var t0 := Time.get_ticks_msec()
	while not cond.call():
		if not is_instance_valid(self) or not is_inside_tree() or Time.get_ticks_msec() - t0 > int(max_seconds * 1000.0):
			return false
		await tree.process_frame
	return true


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
