extends Node
## QA shots of Chapter 1's two staged reveals (docs/ENGAGEMENT.md), with the real Lab 7 scene and its own event
## handling: the bookcase swinging open on the darkroom (frames at 0.3, 0.9 and 1.8 s after the last book), and the
## ending from the moment the door's eye blazes to the open door and the choice (frames through the 1979 flashback
## and the corridor beyond the door). The solver plays everything before each beat.
## Run: tools/qa_run.sh -- res://qa/ch1_reveal_shots.tscn -- --out=<dir> [--seed=N]
## Exit 0 = both beats reached their state.

var out_dir := "/tmp/ch1_reveals"
var room: Node3D
var logic: Lab7Logic
var shot_n := 0
var fails := 0


func _ready() -> void:
	GameState.variant_seed = 0
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		if a.begins_with("--seed="):
			GameState.variant_seed = int(a.substr(7))
	DirAccess.make_dir_recursive_absolute(out_dir)
	SaveSystem.save_path = "user://qa_ch1_reveals_save.json"
	GameState.start_new("ch1")
	logic = GameState.logic
	# up to the radio signal: the bookcase is the next beat
	var g := 0
	while not logic.state["signal_heard"] and g < 400:
		Lab7Solver.step(logic, "leave_lens")
		g += 1
	room = (load("res://src/rooms/lab7/lab7.tscn") as PackedScene).instantiate()
	room.set("capture_mode", true)
	get_tree().root.add_child.call_deferred(room)
	await get_tree().process_frame
	await get_tree().process_frame
	await _settle(1.5)
	await run()


func _settle(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()


func shot(name: String) -> void:
	if DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	shot_n += 1
	var p := "%s/%02d_%s.png" % [out_dir, shot_n, name]
	get_viewport().get_texture().get_image().save_png(p)
	print("shot %s" % p.get_file())


func check(label: String, ok: bool) -> void:
	print(("✓ " if ok else "✗ ") + label)
	if not ok:
		fails += 1


func run() -> void:
	var s := logic.state
	var cam: RoomCamera = room.get("cam")
	# --- the bookcase: watched from the lab, where the player stands when the last volume is pulled
	cam.go("bookshelf")
	await _settle(1.2)
	await shot("bookcase_before_last_book")
	var books: Array = logic.beacon()
	for i in books.size():
		logic.pull_book(int(books[i]))
		if i < books.size() - 1:
			await _settle(0.5)
	check("bookcase open", s["shelf_open"])
	await _settle(0.3)
	await shot("bookcase_0_3s")
	await _settle(0.6)
	await shot("bookcase_0_9s")
	await _settle(0.9)
	await shot("bookcase_1_8s")
	await _settle(2.0)
	# --- the ending: play on to the last mirror click, from the door view a player would watch it in
	var g := 0
	while not (s["mirror_b_mounted"] and s["beam_on"]) and g < 400:
		Lab7Solver.step(logic, "leave_lens")
		g += 1
	while int(s["mirrors"][0]) != 5:
		logic.rotate_mirror(0, 1)
	await _settle(1.0)
	cam.go("lab")
	await _settle(1.0)
	while int(s["mirrors"][1]) != 1 and not s["door_open"]:
		logic.rotate_mirror(1, 1)
	check("door unlocked", s["door_open"])
	await _settle(2.2)
	await shot("ending_echo")
	var hud: Node = room.get("hud")
	var w := 0.0
	while cam.current() != "door" and w < 15.0:
		await _settle(0.2)
		w += 0.2
	await _settle(1.0)
	await shot("ending_door_opening")
	await _settle(1.4)
	await shot("ending_corridor_lamps")
	w = 0.0
	while hud.get("_overlay") == null and w < 10.0:
		await _settle(0.25)
		w += 0.25
	await _settle(0.6)
	await shot("ending_choice")
	check("the choice is offered", hud.get("_overlay") != null)
	hud.call("_close_overlay")
	logic.choose_ending("leave_lens")
	await _settle(2.5)
	await shot("ending_chapter_card")
	check("chapter complete", s["complete"])
	print("ch1 reveal checks failed: %d" % fails)
	SaveSystem.delete_game()
	print("QA_DONE exit=%d" % (0 if fails == 0 else 1))
	get_tree().quit(0 if fails == 0 else 1)
