extends TestBase
## The credits (Settings -> About, Licenses, the end credits) and the first-launch language picker.


func _tree() -> SceneTree:
	return Engine.get_main_loop() as SceneTree


func _add(n: Node) -> void:
	_tree().root.add_child.call_deferred(n)
	await _tree().process_frame


func _all_text(root: Node) -> String:
	var s := ""
	for l in root.find_children("*", "Label", true, false):
		s += (l as Label).text + "\n"
	return s


func test_credits_names_stay_latin_and_headings_are_localized() -> void:
	var before := TranslationServer.get_locale()
	var headings: Dictionary = {}
	for code in ["en", "ru", "uz"]:
		TranslationServer.set_locale(code)
		var heading := ""
		for b in CreditsData.blocks():
			if int(b["kind"]) == CreditsData.Kind.NAME:
				for ch in str(b["text"]):
					check(ch.unicode_at(0) < 0x250 or ch == " ", "%s: the name «%s» is Latin" % [code, b["text"]])
			if int(b["kind"]) == CreditsData.Kind.HEADING and heading == "":
				heading = str(b["text"])
		check(not heading.begins_with("credits."), "%s: the heading is translated (%s)" % [code, heading])
		headings[code] = heading
	check(headings["en"] != headings["ru"] and headings["ru"] != headings["uz"], "three different headings")
	TranslationServer.set_locale(before)
	var names: Array[String] = []
	for b in CreditsData.blocks():
		if int(b["kind"]) == CreditsData.Kind.NAME:
			names.append(str(b["text"]))
	check(names.has("Yuldashali Abdurakhmonov") and names.has("Aliyorbek Toshtemirov"), "both creators are named")
	check(names.has("Godot Engine"), "the engine is credited")


func test_about_and_licenses_pages_show_the_required_texts() -> void:
	var host := Control.new()
	host.set_anchors_preset(Control.PRESET_FULL_RECT)
	await _add(host)
	var closed: Array[int] = [0]
	var about := CreditsPanel.show_credits(host, func() -> void: closed[0] += 1)
	await _tree().process_frame
	var text := _all_text(about)
	check(text.contains("Yuldashali Abdurakhmonov") and text.contains("Aliyorbek Toshtemirov"), "the credits name the creators")
	about.queue_free()
	var lic := CreditsPanel.show_licenses(host, func() -> void: pass)
	await _tree().process_frame
	await _tree().process_frame
	var lt := _all_text(lic)
	check(lt.contains(Engine.get_license_text().substr(0, 60)), "Godot's licence text (Engine.get_license_text) is on the page")
	check(lt.contains("SIL OPEN FONT LICENSE"), "the OFL of the fonts is on the page")
	check(lt.contains("GodotGooglePlayBilling") and lt.contains("godot_ios_plugin_iap"), "the purchase plugins' MIT notices are on the page")
	check(lt.contains("Hiroki Taira"), "with their copyright holders")
	check(lt.contains("Godot Engine contributors"), "(the Godot contributors)")
	var comps := CreditsPanel.components_text()
	check(comps.length() > 5000 and comps.contains("Godot Engine"), "the third-party components Godot bundles are listed (%d chars)" % comps.length())
	check(not Engine.get_copyright_info().is_empty(), "Engine.get_copyright_info has entries")
	host.queue_free()
	await _tree().process_frame


func test_end_credits_skip_by_tap_and_back_hand_over_once() -> void:
	for how in ["tap", "back", "end"]:
		var calls: Array[String] = []
		var cs := (load("res://src/ui/credits_scene.tscn") as PackedScene).instantiate() as CreditsScene
		cs.goto_fn = func(p: String) -> void: calls.append(p)
		await _add(cs)
		await _tree().process_frame
		await _tree().process_frame
		match how:
			"tap":
				var e := InputEventMouseButton.new()
				e.button_index = MOUSE_BUTTON_LEFT
				e.pressed = true
				cs._gui_input(e)
			"back":
				cs.handle_back()
			"end":
				cs.set("_t", CreditsScene.RISE_S + CreditsScene.HOLD_S + CreditsScene.OUT_S + 1.0)
		for i in 60:
			await _tree().process_frame
		if how == "end":
			cs.skip() # a tap after the end changes nothing
		for i in 30:
			await _tree().process_frame
		eq(calls.size(), 1, "%s: the hand-over happens once" % how)
		eq(calls[0] if not calls.is_empty() else "", CreditsScene.after_scene, "%s: to the scene it was given" % how)
		cs.queue_free()
		await _tree().process_frame


func test_language_picker_has_three_big_targets_and_prehighlights_the_device_language() -> void:
	var picker := (load("res://src/ui/language_select.tscn") as PackedScene).instantiate() as Control
	picker.set("detected_override", "ru")
	await _add(picker)
	await _tree().process_frame
	await _tree().process_frame
	var rows: Array = (picker.get("_rows") as Control).get_children()
	eq(rows.size(), 3, "three languages")
	var texts: Array[String] = []
	for r: MenuItem in rows:
		texts.append(r.text)
		check(r.custom_minimum_size.y >= UITheme.px_for_mm(9.0) - 1.0 or r.size.y >= UITheme.px_for_mm(9.0) - 1.0, "«%s» is at least 9 mm tall (%.0f px, 9 mm = %.0f px)" % [r.text, r.size.y, UITheme.px_for_mm(9.0)])
		check(r.size.x >= UITheme.px_for_mm(9.0), "and wide")
	eq(texts, ["English", "Русский", "Oʻzbekcha"], "EN, RU, UZ in this order, in their own names")
	check((rows[1] as MenuItem).primary and not (rows[0] as MenuItem).primary and not (rows[2] as MenuItem).primary, "the device language (ru) is the highlighted one")
	picker.queue_free()
	await _tree().process_frame
