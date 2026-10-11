extends TestBase
## Chapter 1's opening (rain, key, cards, door, maglock) and the first moments: each card stays until it is read and
## the whole opening fits a 32 s budget in every language, it locks input while it runs, a tap on a card moves on to the
## next one, a tap after the cards skips to the settled state (door shut, lab in view, control back), and the notebook
## glows until it is taken.


func _tree() -> SceneTree:
	return Engine.get_main_loop() as SceneTree


func test_opening_reads_and_fits_its_budget() -> void:
	# the cards were 3.3 s and 5.3 s on screen, too fast to read on the owner's phone in Uzbek (2026-10-11)
	var was := TranslationServer.get_locale()
	for loc: String in ["en", "ru", "uz"]:
		TranslationServer.set_locale(loc)
		for key: String in ["intro.1", "intro.2"]:
			var text := TranslationServer.translate(key)
			var hold := Lab7Intro.card_hold(key, 0.0)
			check(hold >= text.length() / 12.0, "%s %s: on screen %.1f s for %d characters" % [loc, key, hold, text.length()])
		var d := Lab7Intro.duration()
		check(d <= 32.0 and d >= 15.0, "%s: the opening takes %.1f s untouched (a tap moves on)" % [loc, d])
	TranslationServer.set_locale(was)


func test_a_tap_on_a_card_moves_on() -> void:
	var intro := Lab7Intro.new()
	intro.set("_on_card", true)
	var tap := InputEventMouseButton.new()
	tap.button_index = MOUSE_BUTTON_LEFT
	tap.pressed = true
	intro.call("_on_input", tap)
	check(bool(intro.get("_advance")) and not bool(intro.get("_skipped")), "a tap on a card moves to the next beat")
	intro.set("_on_card", false)
	intro.call("_on_input", tap)
	check(bool(intro.get("_skipped")), "a tap after the cards skips the rest")
	intro.free()


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
	eq(cam.current(), "intro_door", "it starts on the door")
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
	var kids_before := room.get_child_count()
	room.call("_interact", "notebook", "", {}) # the tap that takes it
	check(bool(room.get("logic").state["taken"].get("notebook", false)), "tapping takes the notebook")
	check(room.get_child_count() == kids_before + 1, "a ghost of it lifts off the desk")
	var ghost: Node3D = room.get_child(room.get_child_count() - 1)
	eq(ghost.find_children("*", "StaticBody3D", true, false).size(), 0, "the ghost has no tap areas")
	await _tree().process_frame
	await _tree().process_frame
	check(not quad.visible, "the glow stops once it is taken")
	await _tree().create_timer(0.8).timeout
	check(not is_instance_valid(ghost) or ghost.is_queued_for_deletion(), "the ghost is gone after its lift")
	AudioManager.stop_all_ambience(0.0)
	AudioManager.stop_music(0.0)
	room.queue_free()
	await _tree().process_frame
	SaveSystem.delete_game()
	SaveSystem.save_path = SaveSystem.SAVE_PATH


func test_the_first_glowing_thing_takes_the_touch_in_two_taps() -> void:
	SaveSystem.save_path = "user://test_lab7_intro.json"
	GameState.start_new("ch1")
	var room := (load("res://src/rooms/lab7/lab7.tscn") as PackedScene).instantiate()
	_tree().root.add_child.call_deferred(room)
	await _tree().process_frame
	await _tree().process_frame
	for c in room.get_children():
		if c is Lab7Intro:
			c.skip()
	for i in 10:
		await _tree().process_frame
	var cam: RoomCamera = room.get("cam")
	cam.go("lab", true)
	for i in 4:
		await _tree().process_frame
	var nb: Node3D = (room.get("models") as Dictionary)["notebook"]
	room.call("_on_tap", cam.unproject_position(nb.global_position + Vector3(0, 0.03, 0)))
	for i in 70:
		await _tree().process_frame
	eq(cam.current(), "desk", "the first tap on the glowing notebook moves the camera to the desk")
	room.call("_on_tap", cam.unproject_position(nb.global_position + Vector3(0, 0.03, 0)))
	check(bool(room.get("logic").state["taken"].get("notebook", false)), "the second tap takes it (not the drawer lying right below it)")
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
