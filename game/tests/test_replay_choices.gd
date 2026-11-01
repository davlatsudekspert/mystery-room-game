extends TestBase
## A replay of Chapter 2 must not change Chapter 3's entry wing once Chapter 3 was started or completed
## (owner decision 2026-11-01, docs/CHAPTER2_EXPANSION.md section 10.6 / 17).


func _with_temp_profile(body: Callable) -> void:
	var old_profile := SaveSystem.profile_path
	var old_save := SaveSystem.save_path
	var old_data: Dictionary = GameState.profile
	SaveSystem.profile_path = "user://test_replay_profile.json"
	SaveSystem.save_path = "user://test_replay_save.json"
	body.call()
	for p in [SaveSystem.profile_path, SaveSystem.profile_path + ".bak", SaveSystem.profile_path + ".tmp"]:
		if FileAccess.file_exists(p):
			DirAccess.remove_absolute(p)
	SaveSystem.delete_game()
	SaveSystem.profile_path = old_profile
	SaveSystem.save_path = old_save
	GameState.profile = old_data


func _finish_ch2(choice: String, echoes: int) -> void:
	GameState.start_new("ch2")
	var l := GameState.logic as ArchiveLogic
	l.state["choice"] = choice
	l.state["echoes"] = ArchiveLogic.ECHOES.slice(0, echoes)
	GameState._on_chapter_complete()


func test_first_run_records_the_key() -> void:
	_with_temp_profile(func() -> void:
		GameState.profile = {"choices": {}, "completed": [], "achievements": [], "hints_used": 0}
		_finish_ch2("strand_key", 2)
		eq(str(GameState.profile["choices"]["ch2_key"]), "strand_key", "recorded")
		eq(int(GameState.profile["choices"]["ch2_echoes"]), 2, "echoes recorded")
		# Chapter 3 not started: a replay may still change the key
		_finish_ch2("leyla_key", 3)
		eq(str(GameState.profile["choices"]["ch2_key"]), "leyla_key", "replay before Chapter 3 may overwrite")
		eq(int(GameState.profile["choices"]["ch2_echoes"]), 3, "echoes follow")
	)


func test_replay_after_chapter3_started_keeps_the_key() -> void:
	_with_temp_profile(func() -> void:
		GameState.profile = {"choices": {}, "completed": [], "achievements": [], "hints_used": 0}
		_finish_ch2("strand_key", 3)
		GameState.start_new("ch3")
		check((GameState.profile["started"] as Array).has("ch3"), "ch3 recorded as started")
		_finish_ch2("leyla_key", 0)
		eq(str(GameState.profile["choices"]["ch2_key"]), "strand_key", "key unchanged after Chapter 3 started")
		eq(int(GameState.profile["choices"]["ch2_echoes"]), 3, "echoes unchanged")
		check((GameState.profile["completed"] as Array).has("ch2"), "ch2 still completed")
		# the entry wing Chapter 3 would pick
		var u := UndergroundLogic.new()
		u.setup_from_profile(GameState.profile["choices"])
		eq(str(u.state["entry"]), "choir", "Chapter 3 still enters by the choir")
	)


func test_replay_after_chapter3_completed_keeps_the_key() -> void:
	_with_temp_profile(func() -> void:
		GameState.profile = {"choices": {"ch2_key": "leyla_key", "ch2_echoes": 1, "ch3_trust": "strand"},
			"completed": ["ch1", "ch2", "ch3"], "achievements": [], "hints_used": 0}
		_finish_ch2("strand_key", 3)
		eq(str(GameState.profile["choices"]["ch2_key"]), "leyla_key", "key unchanged after Chapter 3 completed")
		eq(int(GameState.profile["choices"]["ch2_echoes"]), 1, "echoes unchanged")
		eq(str(GameState.profile["choices"]["ch3_trust"]), "strand", "other choices untouched")
	)


func test_started_list_survives_the_profile_file() -> void:
	_with_temp_profile(func() -> void:
		GameState.profile = {"choices": {}, "completed": [], "achievements": [], "hints_used": 0}
		GameState.start_new("ch3")
		SaveSystem.save_profile(GameState.profile)
		var back := SaveSystem.load_profile()
		check((back["started"] as Array).has("ch3"), "started kept on disk")
		check(not (SaveSystem.load_profile()["completed"] as Array).has("ch3"), "not completed")
	)
