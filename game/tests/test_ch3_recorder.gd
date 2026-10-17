extends TestBase
## Leyla's recorder stops when the player walks away from the camp (owner, 2026-10-17: the recorder went on and on).
## The tape hiss and the reels stop with it; a rewind or Play at the recorder starts it again.


func test_walking_away_stops_the_tape() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	SaveSystem.save_path = "user://test_ch3_recorder.json"
	GameState.start_new("ch3")
	var room := (load("res://src/rooms/underground/underground.tscn") as PackedScene).instantiate()
	tree.root.add_child.call_deferred(room)
	for i in 4:
		await tree.process_frame
	var cam: RoomCamera = room.get("cam")
	cam.go("camp", true)
	room.call("_play_recording")
	await tree.create_timer(0.5).timeout
	check(AudioManager.sfx_loop_playing("tape_hiss"), "the tape hisses while it plays at the camp")
	var gen := int(room.get("_recording"))
	cam.go(String(cam.views.keys().filter(func(k: String) -> bool: return bool(cam.views[k]["root"]))[0]), true)
	await tree.create_timer(0.3).timeout
	check(not AudioManager.sfx_loop_playing("tape_hiss"), "walking away stops the hiss")
	check(int(room.get("_recording")) != gen, "and the playback")
	AudioManager.stop_all_ambience(0.0)
	AudioManager.stop_music(0.0)
	AudioManager.stop_sfx_loops(0.0)
	room.queue_free()
	await tree.process_frame
	SaveSystem.delete_game()
	SaveSystem.save_path = SaveSystem.SAVE_PATH
