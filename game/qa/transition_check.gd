extends Node
## Save / Continue across the free Chapter 1 → Chapter 2 hand-off, and back into a finished chapter (headless).
##   1. Chapter 1 is solved (seed --seed, take path) and saved; the game "restarts": Continue loads the finished Lab 7,
##      which opens on the chapter card again, whose Play button starts Chapter 2 (as the player's tap does).
##   2. Chapter 2 starts with the Chapter 1 choices (the lens, the shards); midway it is saved, the scene is freed and
##      Continue rebuilds it from the save: the state is identical and the intro does not replay.
##   3. Chapter 2 is finished (Strand's key) and saved; Continue opens the vault with the Chapter 3 card; leaving it
##      shows the chapter card.
## Run: godot --headless --path game res://qa/transition_check.tscn [-- --seed=4242]
## Exit 0 = every check passed.

var fails := 0
var _finished := false # set by the last line of run(): a script error midway must not pass as success


func check(label: String, ok: bool) -> void:
	print(("✓ " if ok else "✗ ") + label)
	if not ok:
		fails += 1


func _settle(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()


func _buttons(root: Node) -> Array:
	return [] if root == null else root.find_children("*", "Button", true, false)


func _button(root: Node, text_key: String) -> Button:
	for b: Button in _buttons(root):
		if b.text == text_key or b.text == tr(text_key):
			return b
	return null


func _ready() -> void:
	var seed := 4242
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--seed="):
			seed = int(a.substr(7))
	GameState.variant_seed = seed
	SaveSystem.save_path = "user://qa_transition_save.json"
	SaveSystem.profile_path = "user://qa_transition_profile.json"
	SaveSystem.delete_game()
	GameState.profile = {}
	SaveSystem.save_profile(GameState.profile)
	await get_tree().process_frame # the root is still adding its children during _ready
	await run()
	check("every step ran to the end", _finished)
	SaveSystem.delete_game()
	print("transition checks failed: %d" % fails)
	print("QA_DONE exit=%d" % (0 if fails == 0 else 1))
	get_tree().quit(0 if fails == 0 else 1)


func run() -> void:
	# ---------------------------------------------------------------- 1. Chapter 1 finished, Continue
	check("Chapter 2 is free and released (Premium.can_play)", Premium.can_play("ch2"))
	GameState.start_new("ch1")
	var l1 := GameState.logic as Lab7Logic
	check("Chapter 1 solved (seed %d, take the lens)" % GameState.variant_seed, Lab7Solver.solve(l1, "take_lens"))
	GameState.save_now()
	var choices: Dictionary = SaveSystem.load_profile().get("choices", {})
	check("profile on disk: ch1_lens = take_lens, ch1_shards = %s" % str(choices.get("ch1_shards", "-")),
		str(choices.get("ch1_lens", "")) == "take_lens")
	GameState.logic = null
	check("Continue loads the saved Chapter 1", GameState.continue_saved() and GameState.chapter_id == "ch1" and GameState.logic.is_complete())
	var lab: Node = (load("res://src/rooms/lab7/lab7.tscn") as PackedScene).instantiate()
	get_tree().root.add_child(lab)
	get_tree().current_scene = lab
	await _settle(2.0)
	var hud: Node = lab.get("hud")
	var card: Node = hud.get("_overlay")
	check("a finished Lab 7 opens on the chapter card (not an empty room)", card != null)
	var play := _button(card, "ui.play")
	check("the chapter card offers Play for Chapter 2", play != null)
	check("the door view behind it shows the corridor", lab.get("_corridor") != null)
	if play == null:
		return
	play.pressed.emit()
	var w := 0.0
	while not (get_tree().current_scene is ArchiveRoom) and w < 20.0:
		await _settle(0.25)
		w += 0.25
	var room := get_tree().current_scene as ArchiveRoom
	check("Play loads the Archive (Chapter 2)", room != null and GameState.chapter_id == "ch2")
	if room == null:
		return
	await _settle(1.0)
	var l2 := GameState.logic as ArchiveLogic
	check("Chapter 2 starts with the lens from Chapter 1 (take path)", l2.state["has_lens"] and l2.has_item("crystal_lens"))
	check("Chapter 2 knows the Chapter 1 shards (%d)" % int(l2.state["ch1_shards"]), int(l2.state["ch1_shards"]) == int(choices.get("ch1_shards", -1)))
	check("Chapter 2 saved at once under its own id", GameState.saved_chapter() == "ch2")
	# ---------------------------------------------------------------- 2. midway save, free, Continue
	var g := 0
	while not l2.state["booth_open"] and g < 400:
		ArchiveSolver.step(l2, "strand_key")
		g += 1
	await _settle(1.5) # cinematics started by the events finish
	GameState.save_now()
	var before := JSON.stringify(l2.to_dict())
	room.queue_free()
	await _settle(0.3)
	GameState.logic = null
	check("Continue loads Chapter 2 midway", GameState.continue_saved() and GameState.chapter_id == "ch2")
	var l2b := GameState.logic as ArchiveLogic
	check("the continued state equals the saved state", JSON.stringify(l2b.to_dict()) == before)
	room = (load("res://src/rooms/archive/archive.tscn") as PackedScene).instantiate() as ArchiveRoom
	get_tree().root.add_child(room)
	get_tree().current_scene = room
	await _settle(1.5)
	check("no intro after Continue; the hall view", (room.get("cam") as RoomCamera).current() == "hall" and not bool((room.get("hud") as Node).get("_busy")))
	# ---------------------------------------------------------------- 3. Chapter 2 finished, Continue
	room.queue_free()
	await _settle(0.3)
	check("Chapter 2 solved to the end (Strand's key)", ArchiveSolver.solve(l2b, "strand_key"))
	GameState.save_now()
	choices = SaveSystem.load_profile().get("choices", {})
	check("profile on disk: ch2_key = strand_key, ch1_lens kept", str(choices.get("ch2_key", "")) == "strand_key" and str(choices.get("ch1_lens", "")) == "take_lens")
	GameState.logic = null
	check("Continue loads the finished Chapter 2", GameState.continue_saved() and GameState.logic.is_complete())
	room = (load("res://src/rooms/archive/archive.tscn") as PackedScene).instantiate() as ArchiveRoom
	get_tree().root.add_child(room)
	get_tree().current_scene = room
	await _settle(2.0)
	var teaser := room.get("teaser") as ArchiveTeaser
	check("a finished Archive opens on the Chapter 3 card (state %s)" % ArchiveTeaser.card_state(), teaser.card_open())
	teaser.leave()
	await _settle(1.0)
	var card2: Node = (room.get("hud") as Node).get("_overlay")
	check("leaving it shows the chapter card", card2 != null)
	room.queue_free()
	await _settle(0.3)
	_finished = true
