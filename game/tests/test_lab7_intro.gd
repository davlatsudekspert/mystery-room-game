extends TestBase
## Chapter 1's opening (rain, key, cards, door, maglock) and the first moments: it fits the 20 s budget, locks input
## while it runs, a tap skips it to the settled state (door shut, lab in view, control back), and the notebook glows
## until it is taken.


func _tree() -> SceneTree:
	return Engine.get_main_loop() as SceneTree


func test_opening_fits_twenty_seconds() -> void:
	check(Lab7Intro.duration() <= 20.0, "the opening is at most 20 s (%.1f)" % Lab7Intro.duration())
	check(Lab7Intro.duration() >= 12.0, "and long enough for both cards to be read (%.1f)" % Lab7Intro.duration())


func test_opening_skips_to_a_settled_room_and_the_notebook_glows() -> void:
	SaveSystem.save_path = "user://test_lab7_intro.json"
	GameState.start_new("ch1")
	var room := (load("res://src/rooms/lab7/lab7.tscn") as PackedScene).instantiate()
	_tree().root.add_child.call_deferred(room)
	await _tree().process_frame
	await _tree().process_frame
	var intro: Lab7Intro = null
	for c in room.get_children():
		if c is Lab7Intro:
			intro = c
	check(intro != null, "a fresh chapter plays the opening")
	if intro == null:
		room.queue_free()
		return
	var cam: RoomCamera = room.get("cam")
	eq(cam.current(), "door", "it starts on the door")
	check(not (room.get("touch") as TouchInput).enabled, "input is locked while it plays")
	var leaf: Node3D = (room.get("visuals") as Lab7Visuals).part("door_lab7", "IA_door_leaf")
	var rest: Transform3D = (room.get("visuals") as Lab7Visuals).rest[leaf]
	check(not leaf.transform.basis.is_equal_approx(rest.basis), "the door starts ajar")
	intro.skip() # a tap
	for i in 6:
		await _tree().process_frame
	check((room.get("touch") as TouchInput).enabled, "a tap gives control back at once")
	eq(cam.current(), "lab", "the camera is on the lab")
	check(leaf.transform.basis.is_equal_approx(rest.basis), "the door is shut")
	var glints := room.find_children("*", "Node3D", true, false).filter(func(n: Node) -> bool: return n is FirstGlint)
	eq(glints.size(), 1, "one glow, on the notebook")
	var g: FirstGlint = glints[0]
	var quad: Node3D = g.get_child(0)
	await _tree().process_frame
	check(quad.visible, "the notebook glows")
	room.get("logic").take("notebook")
	await _tree().process_frame
	await _tree().process_frame
	check(not quad.visible, "and stops glowing once it is taken")
	AudioManager.stop_all_ambience(0.0)
	AudioManager.stop_music(0.0)
	room.queue_free()
	await _tree().process_frame
	SaveSystem.delete_game()
	SaveSystem.save_path = SaveSystem.SAVE_PATH


func test_a_loaded_game_plays_no_opening() -> void:
	SaveSystem.save_path = "user://test_lab7_intro.json"
	GameState.start_new("ch1")
	room_take_notebook()
	var room := (load("res://src/rooms/lab7/lab7.tscn") as PackedScene).instantiate()
	_tree().root.add_child.call_deferred(room)
	await _tree().process_frame
	await _tree().process_frame
	var found := false
	for c in room.get_children():
		found = found or c is Lab7Intro
	check(not found, "with progress made, no opening plays")
	AudioManager.stop_all_ambience(0.0)
	AudioManager.stop_music(0.0)
	room.queue_free()
	await _tree().process_frame
	SaveSystem.delete_game()
	SaveSystem.save_path = SaveSystem.SAVE_PATH


func room_take_notebook() -> void:
	GameState.logic.take("notebook")
