extends TestBase
## A pinch in a close-up magnifies it around the fingers (owner, 2026-10-11: Panel 7's switches and numerals were too
## small to read on a phone). The point under the fingers stays there, the view never leaves the close-up's frame,
## magnification stops at MAG_MAX, and leaving the close-up resets it. Room views keep their field-of-view zoom.


func test_pinch_magnifies_a_closeup_around_the_fingers() -> void:
	GameState.start_new("ch1")
	var r := HudTestRoom.create(GameState.logic, true)
	await r.attach()
	var cam := r.cam
	cam.go("desk", true)
	await r.wait(0.1)
	var v: Dictionary = cam.views["desk"]
	var fov0 := float(v["fov"])
	check(absf(cam.fov - fov0) < 0.1, "a close-up starts as framed (%.1f)" % cam.fov)
	var vp := cam.get_viewport().get_visible_rect()
	var p := vp.position + vp.size * Vector2(0.7, 0.35) # off-centre: the right, upper part of the close-up
	var d := (v["pos"] as Vector3).distance_to(v["target"])
	var world := _on_focal_plane(cam, p, d)
	cam.zoom(2.0, p)
	await r.wait(0.6)
	check(absf(cam.magnification() - 2.0) < 0.01, "the pinch magnified 2x")
	check(cam.fov < fov0 * 0.6, "the view narrowed (%.1f -> %.1f)" % [fov0, cam.fov])
	var at := cam.unproject_position(world)
	check(at.distance_to(p) < vp.size.y * 0.01, "the point under the fingers stays there (%.1f px off)" % at.distance_to(p))
	cam.zoom(10.0, p)
	await r.wait(0.3)
	eq(cam.magnification(), RoomCamera.MAG_MAX, "it stops at MAG_MAX")
	cam.zoom(0.01, p)
	await r.wait(0.6)
	eq(cam.magnification(), 1.0, "pinching in returns to the framed view")
	cam.zoom(2.0, p)
	cam.back()
	await r.wait(1.2)
	eq(cam.magnification(), 1.0, "leaving the close-up resets it")
	cam.go("desk")
	await r.wait(1.2)
	check(absf(cam.fov - fov0) < 0.1, "coming back, it is framed again (%.1f)" % cam.fov)
	r.dispose()
	await (Engine.get_main_loop() as SceneTree).process_frame


func test_pan_stays_inside_the_frame() -> void:
	GameState.start_new("ch1")
	var r := HudTestRoom.create(GameState.logic, true)
	await r.attach()
	var cam := r.cam
	cam.go("desk", true)
	await r.wait(0.1)
	var vp := cam.get_viewport().get_visible_rect()
	var v: Dictionary = cam.views["desk"]
	var d := (v["pos"] as Vector3).distance_to(v["target"])
	var corner_world := _on_focal_plane(cam, vp.end - Vector2(1, 1), d)
	for i in 6: # pinch at the very corner, again and again
		cam.zoom(1.3, vp.end - Vector2(1, 1))
	await r.wait(0.8)
	var at := cam.unproject_position(corner_world)
	var tol := vp.size.y * 0.01 # the handheld sway
	check(at.x >= vp.end.x - tol and at.y >= vp.end.y - tol, "the view never slides past the close-up's own corner (%s on %s)" % [str(at), str(vp.size)])
	r.dispose()
	await (Engine.get_main_loop() as SceneTree).process_frame


## The point under screen point `p` on the plane square to the view at the close-up's target distance `d`.
func _on_focal_plane(cam: RoomCamera, p: Vector2, d: float) -> Vector3:
	var n := cam.project_ray_normal(p)
	return cam.project_ray_origin(p) + n * (d / n.dot(-cam.global_basis.z))
