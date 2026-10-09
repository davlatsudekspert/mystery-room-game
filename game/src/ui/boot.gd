extends Node
## Entry point: first launch → language picker, otherwise the main menu.


func _ready() -> void:
	# the previous session died while loading or first drawing a scene: play on with safe graphics (CrashGuard)
	CrashGuard.read_previous()
	if CrashGuard.crashed_while_loading() and not bool(Settings.get_value("safe_graphics")):
		Settings.set_value("safe_graphics", true)
		CrashGuard.switched_to_safe = true
	CrashGuard.mark("boot")
	await get_tree().process_frame
	if Loc.is_first_launch():
		get_tree().change_scene_to_file("res://src/ui/language_select.tscn")
	else:
		get_tree().change_scene_to_file("res://src/ui/main_menu.tscn")
