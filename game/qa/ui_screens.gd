extends Node
## QA: renders the menus and in-game overlays in EN, RU and UZ to check layout/fonts on a real frame.
## Run: xvfb-run godot --path game res://qa/ui_screens.tscn -- --out=<dir>

var out_dir := "/tmp"


func _ready() -> void:
	_run.call_deferred() # the root is still busy adding children during _ready


func _run() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
	SaveSystem.save_path = "user://qa_ui_save.json"
	for lang in ["en", "ru", "uz"]:
		TranslationServer.set_locale(lang)
		Settings.values["text_scale"] = 1.0
		# --- first-launch language picker, main menu, settings, chapters
		if lang == "en": # the picker shows all three languages at once
			var picker: Control = (load("res://src/ui/language_select.tscn") as PackedScene).instantiate()
			get_tree().root.add_child(picker)
			await _settle(1.0)
			await _shot("language_select")
			picker.queue_free()
			await _settle(0.2)
		var menu: Control = (load("res://src/ui/main_menu.tscn") as PackedScene).instantiate()
		get_tree().root.add_child(menu)
		await _settle(1.5)
		await _shot("%s_main_menu" % lang)
		menu.call("_show_settings")
		await _settle(0.6)
		await _shot("%s_settings" % lang)
		menu.call("_show_chapters")
		await _settle(0.6)
		await _shot("%s_chapters" % lang)
		menu.queue_free()
		await _settle(0.3)
		# --- in-game overlays
		GameState.start_new("ch1")
		var l := GameState.logic as Lab7Logic
		for i in 30:
			Lab7Solver.step(l, "leave_lens")
		var room: Node3D = (load("res://src/rooms/lab7/lab7.tscn") as PackedScene).instantiate()
		room.set("capture_mode", true)
		get_tree().root.add_child(room)
		await _settle(2.0)
		var hud: Node = room.get("hud")
		await _shot("%s_hud_inventory" % lang)
		hud.call("show_hint")
		await _settle(0.5)
		await _shot("%s_hint" % lang)
		hud.call("show_pause")
		await _settle(0.5)
		await _shot("%s_pause" % lang)
		hud.call("show_inspect", "crystal_lens")
		await _settle(1.0)
		await _shot("%s_inspect" % lang)
		hud.call("_show_notebook", 1)
		await _settle(0.5)
		await _shot("%s_notebook" % lang)
		hud.call("show_document", "letter")
		await _settle(0.5)
		await _shot("%s_letter" % lang)
		hud.call("_close_overlay")
		hud.call("show_choice")
		await _settle(0.8)
		await _shot("%s_choice" % lang)
		hud.call("_close_overlay")
		hud.call("show_chapter_complete")
		await _settle(1.2)
		await _shot("%s_chapter_complete" % lang)
		hud.call("_close_overlay")
		Settings.values["text_scale"] = 1.3
		hud.call("show_hint")
		await _settle(0.5)
		await _shot("%s_hint_textscale130" % lang)
		Settings.values["text_scale"] = 1.0
		room.queue_free()
		await _settle(0.5)
	SaveSystem.delete_game()
	get_tree().quit()


func _settle(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("%s/%s.png" % [out_dir, name])
