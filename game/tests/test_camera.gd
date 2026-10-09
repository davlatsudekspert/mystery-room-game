extends TestBase
## RoomCamera feel: free look follows the finger smoothly, a released swipe glides and stops, QA aiming snaps,
## and Back returns to the room view facing where the player last looked.


func _cam() -> RoomCamera:
	var cam := RoomCamera.new()
	# the test runner's own node (the root is still busy adding it while tests run inside its _ready)
	var root := (Engine.get_main_loop() as SceneTree).root
	root.get_child(root.get_child_count() - 1).add_child(cam)
	cam.add_view("room", Vector3(0, 1.6, 2), Vector3(0, 1.6, 0), 60.0, true)
	cam.add_view("desk", Vector3(1, 1.2, 0.5), Vector3(1, 0.8, 0), 45.0)
	cam.go("room", true)
	return cam


func _run_frames(cam: RoomCamera, seconds: float) -> void:
	for _i in int(seconds * 60.0):
		cam._follow(1.0 / 60.0)


func test_free_look_follows_smoothly() -> void:
	var cam := _cam()
	cam.free_look(Vector2(-100, 0)) # 16° to the left
	cam.release()
	cam._glide = Vector2.ZERO # no swipe speed: only the follow
	cam._follow(1.0 / 60.0)
	check(cam.yaw > 0.5 and cam.yaw < 16.0, "the view moves toward the finger, not all at once (yaw %.2f)" % cam.yaw)
	_run_frames(cam, 2.0)
	check(absf(cam.yaw - 16.0) < 0.05, "and arrives (yaw %.2f)" % cam.yaw)
	cam.zoom(1.5)
	_run_frames(cam, 2.0)
	check(absf(cam.fov - 40.0) < 0.1, "pinch zoom eases to its goal (fov %.2f)" % cam.fov)
	cam.free()


func test_released_swipe_glides_then_stops() -> void:
	var cam := _cam()
	cam.free_look(Vector2(-20, 0))
	cam.free_look(Vector2(-20, 0)) # a quick swipe
	cam.release()
	check(cam._glide.x > 0.0, "a quick release carries speed")
	_run_frames(cam, 3.0)
	var far := cam.yaw
	check(far > 6.4 + 1.0, "the view glides past where the finger stopped (yaw %.2f)" % far)
	_run_frames(cam, 3.0)
	check(absf(cam.yaw - far) < 0.5 and cam._glide.length() < 1.0, "and comes to rest")
	cam.free()


func test_aiming_snaps_and_back_faces_the_last_look() -> void:
	var cam := _cam()
	cam.yaw = -50.0
	cam.pitch = 10.0
	cam._apply_free_look() # how QA tools aim
	_run_frames(cam, 1.0)
	check(absf(cam.yaw + 50.0) < 0.01 and absf(cam.pitch - 10.0) < 0.01, "an aimed view does not drift")
	var facing := -cam.global_basis.z
	cam.go("desk", true)
	check(cam.back(), "back from the close-up")
	cam._tween.custom_step(5.0)
	check(not cam.transitioning, "the move back finishes")
	check((-cam.global_basis.z).distance_to(facing) < 0.01, "back in the room view, facing where the player looked")
	cam.free()
