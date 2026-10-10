extends Node
## QA: the first-launch language picker, Settings -> About (credits and licenses) and the end credits, in one run.
##   tools/qa_run.sh -- res://qa/ui_extras_shots.tscn -- --out=<dir> [--only=lang,about,licenses,credits] [--window=WxH]
## The shimmer and the credits are shown at chosen moments (their clocks are set), not waited for.

var out_dir := "/tmp"
var only: PackedStringArray = ["lang", "about", "licenses", "credits"]
var win := Vector2i(1170, 540)


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--only="):
			only = a.substr(7).split(",", false)
		elif a.begins_with("--window="):
			var p := a.substr(9).split("x")
			win = Vector2i(int(p[0]), int(p[1]))
	DirAccess.make_dir_recursive_absolute(out_dir)
	get_window().size = win
	await _settle(0.3)
	Settings.set("emulate", {"size": Vector2i(2340, 1080), "dpi": 400.0, "safe": Rect2i(120, 0, 2220, 1080)})
	SaveSystem.save_path = "user://qa_ui_extras_save.json"
	if "lang" in only:
		await _lang()
	if "about" in only or "licenses" in only:
		await _about()
	if "credits" in only:
		await _credits()
	print("QA_DONE exit=0")
	get_tree().quit(0)


func _settle(seconds: float) -> void:
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < seconds * 1000.0:
		await get_tree().process_frame


func _shot(name: String) -> void:
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("%s/%s.png" % [out_dir, name])
	print("shot " + name)


func _lang() -> void:
	for code in ["en", "ru", "uz"]:
		TranslationServer.set_locale(code)
		var picker := (load("res://src/ui/language_select.tscn") as PackedScene).instantiate() as Control
		picker.set("detected_override", code)
		get_tree().root.add_child(picker)
		await _settle(0.5)
		if code == "en":
			await _shot("lang_en_entrance")
		await _settle(2.4)
		picker.set("_t", 2.87) # the shimmer mid-sweep
		await _shot("lang_%s" % code)
		picker.queue_free()
		await _settle(0.2)


func _about() -> void:
	for code in ["en", "ru", "uz"]:
		TranslationServer.set_locale(code)
		var host := Control.new()
		host.set_anchors_preset(Control.PRESET_FULL_RECT)
		var dim := ColorRect.new()
		dim.color = Color(0.03, 0.035, 0.04, 1.0)
		dim.set_anchors_preset(Control.PRESET_FULL_RECT)
		host.add_child(dim)
		get_tree().root.add_child(host)
		host.theme = UITheme.build()
		var sp := SettingsPanel.new()
		UITheme.safe_center(host).add_child(sp)
		await _settle(0.5)
		if code == "en":
			await _shot("settings_en")
		var d := CreditsPanel.open(sp)
		await _settle(0.8)
		if "about" in only:
			await _shot("about_%s" % code)
		if code == "en" and "licenses" in only:
			# the Licenses button is the first one in the footer
			var foot := d.find_children("*", "Button", true, false)
			for b: Button in foot:
				if b.text == "ui.licenses":
					b.pressed.emit()
			await _settle(1.5)
			await _shot("licenses_en")
			var scroll := host.find_children("*", "ScrollContainer", true, false)
			if not scroll.is_empty():
				(scroll[0] as ScrollContainer).scroll_vertical = 900
				await _settle(0.4)
				await _shot("licenses_en_2")
		host.queue_free()
		await _settle(0.2)


func _credits() -> void:
	for code in ["en", "ru", "uz"]:
		TranslationServer.set_locale(code)
		var cs := (load("res://src/ui/credits_scene.tscn") as PackedScene).instantiate() as Control
		cs.set("goto_fn", func(_p: String) -> void: print("credits done"))
		get_tree().root.add_child(cs)
		await _settle(0.6)
		var times: Array = [9.0, 22.0, 39.0] if code == "en" else [32.0]
		for t: float in times:
			cs.set("_t", t)
			await _settle(0.15)
			await _shot("credits_%s_%02d" % [code, int(t)])
		cs.queue_free()
		await _settle(0.2)
