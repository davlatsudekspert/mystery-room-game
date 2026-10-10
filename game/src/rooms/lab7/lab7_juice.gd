class_name Lab7Juice
extends RefCounted
## Tactile feedback for Lab 7's first touches (the notebook on the desk, the flip clock stopped at 03:17): small
## motions that answer a finger at once, so the first minute feels physical. Pure presentation: the game state is
## untouched (the room's logic has already moved on when these play).


## The notebook is taken: a ghost copy lifts off the desk toward the player, turns a little, shrinks and fades
## (the real one has left the room by logic). Call it just before the take.
static func lift_ghost(room: Node3D, src: Node3D) -> void:
	if src == null or not src.visible:
		return
	var g := src.duplicate() as Node3D
	for body in g.find_children("*", "StaticBody3D", true, false):
		body.free() # no tap areas on the ghost
	room.add_child(g)
	g.global_transform = src.global_transform
	var cam := room.get("cam") as Camera3D
	var toward := Vector3.UP * 0.1
	if cam != null:
		toward += (cam.global_position - g.global_position).normalized() * 0.16
	var meshes := ModelUtil.find_meshes(g)
	var tw := room.create_tween().set_parallel(true)
	tw.tween_property(g, "global_position", g.global_position + toward, 0.5).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tw.tween_property(g, "rotation:y", g.rotation.y + 0.7, 0.5).set_trans(Tween.TRANS_SINE)
	tw.tween_property(g, "scale", g.scale * 0.6, 0.5).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tw.tween_method(func(a: float) -> void:
		for mi in meshes:
			mi.transparency = a, 0.0, 1.0, 0.5).set_delay(0.12)
	tw.chain().tween_callback(g.queue_free)
	AudioManager.sfx("page_turn", -6.0, 1.1)


## The flip clock is tapped in its close-up: it rattles on the desk, as if something inside still tries to turn.
static func clock_nudge(room: Node3D, clock: Node3D) -> void:
	if clock == null:
		return
	var base := clock.rotation
	var up := clock.position.y
	var tw := room.create_tween()
	tw.tween_property(clock, "rotation:y", base.y + 0.045, 0.05)
	tw.parallel().tween_property(clock, "position:y", up + 0.003, 0.05)
	tw.tween_property(clock, "rotation:y", base.y - 0.035, 0.07)
	tw.parallel().tween_property(clock, "position:y", up, 0.07)
	tw.tween_property(clock, "rotation:y", base.y + 0.015, 0.06)
	tw.tween_property(clock, "rotation:y", base.y, 0.09)
	AudioManager.sfx("wheel_tick", -7.0, 0.75)
	AudioManager.haptic(15)
	room.get_tree().create_timer(0.11).timeout.connect(func() -> void: AudioManager.sfx("wheel_tick", -12.0, 0.6))
