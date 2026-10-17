extends TestBase
## Every hint goal of Chapters 1-4 names where its next step is, in all three languages, and the hint dialog says it.

const PHONE := {"size": Vector2i(1920, 1080), "dpi": 480.0, "safe": Rect2i(0, 0, 1920, 1080)}


func _csv() -> Dictionary:
	var keys := {}
	var f := FileAccess.open("res://localization/strings.csv", FileAccess.READ)
	check(f != null, "strings.csv exists")
	if f == null:
		return keys
	while not f.eof_reached():
		var row := f.get_csv_line()
		if row.size() >= 4:
			keys[row[0]] = row
	return keys


func test_every_goal_has_a_place_in_all_languages() -> void:
	var keys := _csv()
	var chapters := {
		"ch1": Lab7Hints.GOALS, "ch2": ArchiveHints.GOALS,
		"ch3": UndergroundLogic.GOALS, "ch4": ArrayHallLogic.GOALS,
	}
	for ch: String in chapters:
		var goals: Array[String] = chapters[ch]
		check(goals.size() > 0, ch + " has goals")
		for g in goals:
			var k := HintPlaces.place_key(g)
			check(k != "", "%s: goal %s has a place key" % [ch, g])
			check(keys.has(k), "place key exists: " + k)
			if keys.has(k):
				for col in [1, 2, 3]:
					check(str(keys[k][col]).strip_edges() != "", "empty translation %s col %d" % [k, col])
	check(keys.has("ui.hint_next_step"), "next-step line key")
	eq(HintPlaces.place_key("nonsense"), "", "unknown goal: no place")


func test_dialog_line_names_the_place() -> void:
	SaveSystem.save_path = "user://test_hint_places.json"
	Settings.emulate = PHONE
	TranslationServer.set_locale("en")
	GameState.start_new("ch1")
	var r := HudTestRoom.create(GameState.logic, true)
	await r.attach()
	var hud := r.hud
	eq(GameState.logic.hint_goal(), "notebook", "first goal")
	hud.call("show_hint")
	await r.wait(0.1)
	var found := false
	for l in (hud.get("_overlay") as Node).find_children("*", "Label", true, false):
		if (l as Label).text == "Next step: Leyla's desk":
			found = true
	check(found, "the dialog says «Next step: Leyla's desk»")
	hud.call("_close_overlay")
	r.dispose()
	await (Engine.get_main_loop() as SceneTree).process_frame
	Settings.emulate = {}
	GameState.start_new("ch1")
	SaveSystem.delete_game()
	SaveSystem.save_path = SaveSystem.SAVE_PATH
