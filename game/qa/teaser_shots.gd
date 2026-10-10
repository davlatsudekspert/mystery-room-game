extends Node
## QA for the Chapter 2 finale and cliffhanger (docs/ENGAGEMENT.md): the solver plays the chapter up to the unlocked
## vault, the real Archive scene is loaded, and the rest runs exactly as for a player: the optional receiver whisper at
## the vault door, the vault opening, the reel and the 42nd figure, the key choice, the lift shaft, the recorder and
## the Chapter 3 card, then the HUD's chapter card. A screenshot is saved at each beat, plus the Chapter 3 card in its
## three store states (coming soon / unlock / play) and the vault's answer to a recorded crystal.
## Run: tools/qa_run.sh -- res://qa/teaser_shots.tscn -- --out=<dir> [--key=strand|leyla] [--lens=take|leave] [--seed=N]
## Headless (no pixels, the same flow and checks): godot --headless --path game res://qa/teaser_shots.tscn -- --out=<dir>
## Exit 0 = every check passed.

var out_dir := "/tmp/teaser_shots"
var key := "leyla_key"
var lens := "leave"
var room: Node3D
var logic: ArchiveLogic
var shot_n := 0
var fails := 0


func _ready() -> void:
	GameState.variant_seed = 0
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		if a.begins_with("--key="):
			key = a.substr(6) + "_key"
		if a.begins_with("--lens="):
			lens = a.substr(7)
		if a.begins_with("--seed="):
			GameState.variant_seed = int(a.substr(7))
		if a.begins_with("--lang="):
			TranslationServer.set_locale(a.substr(7))
	DirAccess.make_dir_recursive_absolute(out_dir)
	SaveSystem.save_path = "user://qa_teaser_save.json"
	SaveSystem.profile_path = "user://qa_teaser_profile.json"
	GameState.profile = {"choices": {"ch1_lens": "take_lens" if lens == "take" else "leave_lens", "ch1_shards": 5}}
	GameState.start_new("ch2")
	logic = GameState.logic
	var g := 0
	while not logic.state["vault_unlocked"] and g < 600:
		ArchiveSolver.step(logic, key)
		g += 1
	logic.select_item("")
	room = (load("res://src/rooms/archive/archive.tscn") as PackedScene).instantiate()
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
	await _settle(0.15)
	if DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	shot_n += 1
	var p := "%s/%02d_%s.png" % [out_dir, shot_n, name]
	get_viewport().get_texture().get_image().save_png(p)
	print("shot %s" % p.get_file())


func perf(label: String) -> void:
	var rs := RenderingServer
	print("perf[%s]: draw calls %d, primitives %d" % [label,
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)])


func check(label: String, ok: bool) -> void:
	print(("✓ " if ok else "✗ ") + label)
	if not ok:
		fails += 1


func cam() -> RoomCamera:
	return room.get("cam")


func hud() -> Node:
	return room.get("hud")


func caption_text() -> String:
	var l: Variant = hud().get("_caption_line")
	return (l as Label).text if l is Label else ""


func run() -> void:
	var s := logic.state
	var teaser: ArchiveTeaser = room.get("teaser")
	check("solver reached the unlocked vault (%s path)" % lens, s["vault_unlocked"])
	# the vault answers a freshly recorded crystal (shown here on the vault door, where it happens)
	cam().go("vault")
	await _settle(1.0)
	(room.get("visuals") as ArchiveVisuals).vault_answer("right")
	await _settle(0.4)
	await shot("vault_answers_sign")
	# the optional whisper: the receiver in hand at the shut vault door, all three reels found
	logic.select_item("pocket_receiver")
	await _settle(1.0)
	check("receiver whisper at the vault door (caption: %s)" % caption_text(), caption_text() == tr("cap2.whisper"))
	check("achievement forty_two", (GameState.profile.get("achievements", []) as Array).has("forty_two"))
	await shot("receiver_whisper")
	logic.select_item("")
	await _settle(0.5)
	# open the vault: the room plays its finale
	for _i in ArchiveLogic.WHEEL_TURNS:
		logic.turn_wheel()
		await _settle(0.3)
	check("vault open", s["vault_open"])
	await _settle(2.4)
	await shot("vault_opening")
	var w := 0.0
	while cam().current() != "vault_reel" and w < 15.0:
		await _settle(0.25)
		w += 0.25
	await _settle(1.4)
	await shot("reel_41")
	perf("vault_reel")
	check("caption: the forty-one", caption_text() == tr("cap2.reel_41"))
	await _settle(4.0)
	await shot("reel_42_reveal")
	check("caption: the forty-second", caption_text() == tr("cap2.reel_42"))
	await _settle(2.6)
	await shot("reel_42_close")
	w = 0.0
	while hud().get("_overlay") == null and w < 20.0:
		await _settle(0.25)
		w += 0.25
	check("the key choice opens after the reel", hud().get("_overlay") != null)
	await shot("finale_choice")
	hud().call("_close_overlay")
	logic.choose_ending(key)
	check("choice %s → chapter complete" % key, s["complete"] and s["choice"] == key)
	await _settle(0.6)
	await shot("key_lifted")
	await _settle(1.6)
	await shot("rumble")
	w = 0.0
	while cam().current() != "shaft" and w < 10.0:
		await _settle(0.2)
		w += 0.2
	check("cut to the lift shaft", cam().current() == "shaft")
	await _settle(1.2)
	await shot("shaft_lamps")
	perf("shaft")
	await _settle(2.6)
	await shot("shaft_bottom")
	await _settle(3.0)
	await shot("shaft_cage")
	w = 0.0
	while cam().current() == "shaft" and w < 15.0:
		await _settle(0.2)
		w += 0.2
	await _settle(1.4)
	await shot("recorder_click")
	await _settle(4.4)
	await shot("recorder_voice")
	w = 0.0
	while not teaser.card_open() or _card_buttons(teaser).is_empty():
		await _settle(0.25)
		w += 0.25
		if w > 40.0:
			break
		if w == 9.0:
			await shot("recorder_second_voice")
	await _settle(2.6)
	await shot("ch3_card_" + ArchiveTeaser.card_state())
	check("the Chapter 3 card is up (store state %s)" % ArchiveTeaser.card_state(), teaser.card_open())
	check("the HUD's chapter card waits behind it", hud().get("_overlay") == null)
	teaser.leave()
	await _settle(2.0)
	check("leaving the card shows the chapter card", hud().get("_overlay") != null)
	await shot("chapter_complete")
	# the card in its other store states (the hand-off to PurchasePanel when Chapter 3 is out and the store is open)
	hud().call("_close_overlay")
	for st in ["unlock", "play", "soon"]:
		teaser.show_card(key, true, st)
		await _settle(1.0)
		await shot("ch3_card_state_" + st)
		check("card state %s has a button" % st, not _card_buttons(teaser).is_empty())
		teaser.leave()
		await _settle(0.6)
	print("teaser checks failed: %d" % fails)
	SaveSystem.delete_game()
	print("QA_DONE exit=%d" % (0 if fails == 0 else 1))
	get_tree().quit(0 if fails == 0 else 1)


func _card_buttons(teaser: ArchiveTeaser) -> Array:
	var root: Variant = teaser.get("_root")
	if not (root is Control) or not is_instance_valid(root):
		return []
	return (root as Control).find_children("*", "Button", true, false)
