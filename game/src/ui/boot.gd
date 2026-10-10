extends Node
## Entry point: first launch → language picker, otherwise the main menu.


func _ready() -> void:
	# the previous session died while loading or first drawing a scene: play on with safe graphics (CrashGuard)
	CrashGuard.read_previous()
	CrashGuard.switched_to_safe = CrashGuard.update_safe_level()
	CrashGuard.mark("boot")
	await get_tree().process_frame
	# QA on the iOS Simulator (.github/workflows/ios-sim.yml): MR_QA=newgame plays the New Game path by itself and
	# prints whether the room's first seconds were drawn. Debug and tester builds only.
	if OS.get_environment("MR_QA") == "newgame" and (OS.is_debug_build() or Premium.tester_tools()):
		var qa := _QaNewGame.new()
		get_tree().root.add_child(qa)
		qa.run.call_deferred()
		return
	if Loc.is_first_launch():
		get_tree().change_scene_to_file("res://src/ui/language_select.tscn")
	else:
		get_tree().change_scene_to_file("res://src/ui/main_menu.tscn")


## The New Game path without a finger: main menu, New Game, then wait for the room to reach "play" (its first
## seconds drawn). Lives on the root so it survives the scene changes. Prints QA_NEWGAME_OK or QA_NEWGAME_FAIL.
class _QaNewGame extends Node:
	func run() -> void:
		print("QA_NEWGAME start: %s %s, safe level %d" % [RenderingServer.get_current_rendering_driver_name(),
			RenderingServer.get_current_rendering_method(), CrashGuard.safe_level()])
		get_tree().change_scene_to_file("res://src/ui/main_menu.tscn")
		await _wait(6.0)
		print("QA_NEWGAME menu: frames drawn %d" % Engine.get_frames_drawn())
		SaveSystem.delete_game()
		GameState.start_new("ch1")
		SceneManager.goto(Chapters.get_chapter("ch1")["scene"])
		var end := Time.get_ticks_msec() + 90000
		while Time.get_ticks_msec() < end and not CrashGuard.stage().begins_with("play:"):
			await _wait(1.0)
			print("QA_NEWGAME stage %s, frames drawn %d" % [CrashGuard.stage(), Engine.get_frames_drawn()])
		var ok := CrashGuard.stage().begins_with("play:")
		print("QA_NEWGAME_OK" if ok else "QA_NEWGAME_FAIL (stage %s)" % CrashGuard.stage())
		SaveSystem.delete_game()
		get_tree().quit(0 if ok else 1)

	func _wait(seconds: float) -> void:
		var end := Time.get_ticks_msec() + int(seconds * 1000.0)
		while Time.get_ticks_msec() < end:
			await get_tree().process_frame
