extends TestBase
## The hint ladder (owner feedback, item 4: "hints only help a little"): level 1 nudges, 2 says more, 3 is the
## answer. The dialog names each step ("Hint 1 of 3", "Stronger hint (2/3)", "Show the answer (3/3)"), keeps the
## earlier levels above the new one (smaller, muted), and reopens a goal at the highest level reached.

const PHONE := {"size": Vector2i(1920, 1080), "dpi": 480.0, "safe": Rect2i(0, 0, 1920, 1080)}


## A logic whose hint goal the test sets (the real chapters only move forward).
class GoalLogic extends RoomLogic:
	var goal := "notebook"

	func hint_goal() -> String:
		return goal


func test_levels_are_remembered_per_goal_without_counting_again() -> void:
	SaveSystem.save_path = "user://test_hud_hints.json"
	GameState.start_new("ch1")
	var stub := GoalLogic.new()
	GameState.call("_attach", "ch1", stub)
	GameState.hints_used = 0
	eq(GameState.shown_hints().size(), 0, "nothing shown yet")
	eq(int(GameState.next_hint()["level"]), 1, "first hint")
	eq(int(GameState.next_hint()["level"]), 2, "stronger")
	var seen := GameState.shown_hints()
	eq(seen.size(), 2, "both levels are still there")
	eq(str(seen[0]["key"]), "hint.notebook.1", "level 1 first")
	eq(str(seen[1]["key"]), "hint.notebook.2", "then level 2")
	eq(GameState.hints_used, 2, "reading them again does not count")
	stub.goal = "drawer"
	eq(int(GameState.next_hint()["level"]), 1, "a new goal starts at the nudge")
	stub.goal = "notebook"
	eq(GameState.shown_hints().size(), 2, "back to the first goal: its two levels")
	eq(int(GameState.next_hint()["level"]), 3, "and the next one is the answer")
	eq(int(GameState.next_hint()["level"]), 3, "the answer stays the answer")
	GameState.start_new("ch1")
	SaveSystem.delete_game()
	SaveSystem.save_path = SaveSystem.SAVE_PATH


func test_levels_survive_save_and_continue() -> void:
	SaveSystem.save_path = "user://test_hud_hints.json"
	GameState.start_new("ch1")
	GameState.next_hint()
	GameState.next_hint()
	GameState.save_now()
	check(GameState.continue_saved(), "continue")
	eq(GameState.shown_hints().size(), 2, "the hints shown before the save are still shown")
	SaveSystem.delete_game()
	SaveSystem.save_path = SaveSystem.SAVE_PATH


func _rungs(hud: Node) -> Array[Control]:
	var out: Array[Control] = []
	var o: Variant = hud.get("_overlay")
	if o == null:
		return out
	for n in (o as Node).find_children("*", "VBoxContainer", true, false):
		if n.has_meta("hint_level") and not n.is_queued_for_deletion():
			out.append(n as Control)
	return out


func _more(hud: Node) -> Button:
	for b in (hud.get("_overlay") as Node).find_children("*", "Button", true, false):
		if (b as Button).text in ["ui.hint_more", "ui.hint_answer"]:
			return b
	return null


func test_dialog_climbs_the_ladder_and_reopens_at_the_top() -> void:
	SaveSystem.save_path = "user://test_hud_hints.json"
	Settings.emulate = PHONE
	TranslationServer.set_locale("en")
	GameState.start_new("ch1")
	var r := HudTestRoom.create(GameState.logic, true)
	await r.attach()
	var hud := r.hud
	GameState.hints_used = 0
	hud.call("show_hint")
	await r.wait(0.1)
	var rungs := _rungs(hud)
	eq(rungs.size(), 1, "the dialog opens at level 1")
	var more := _more(hud)
	check(more != null and more.text == "ui.hint_more" and tr(more.text).contains("(2/3)"), "the button offers a stronger hint (2/3)")
	if more == null or rungs.size() != 1:
		hud.call("_close_overlay")
		r.dispose()
		await (Engine.get_main_loop() as SceneTree).process_frame
		Settings.emulate = {}
		return
	var head := rungs[0].get_child(0) as Label
	eq(head.text, tr("ui.hint_level") % 1, "«Hint 1 of 3»")
	more.emit_signal("pressed")
	await r.wait(0.1)
	rungs = _rungs(hud)
	eq(rungs.size(), 2, "level 2 is added under level 1")
	if rungs.size() < 2:
		hud.call("_close_overlay")
		r.dispose()
		await (Engine.get_main_loop() as SceneTree).process_frame
		Settings.emulate = {}
		return
	var old_text := rungs[0].get_child(1) as Label
	var new_text := rungs[1].get_child(1) as Label
	check(old_text.get_theme_font_size("font_size") < new_text.get_theme_font_size("font_size"), "the earlier level is smaller")
	eq(old_text.get_theme_color("font_color"), UITheme.MUTED, "and muted")
	eq(new_text.text, tr("hint.%s.2" % GameState.logic.hint_goal()), "the new level reads level 2's text")
	check(more.text == "ui.hint_answer" and tr(more.text).contains("(3/3)"), "the button now shows the answer (3/3)")
	more.emit_signal("pressed")
	await r.wait(0.1)
	rungs = _rungs(hud)
	eq(rungs.size(), 3, "the answer is added under both")
	if rungs.size() == 3:
		eq((rungs[2].get_child(0) as Label).text, tr("ui.hint_level_answer"), "«Hint 3 of 3: the answer»")
	check(more.disabled and not more.visible, "nothing stronger than the answer")
	eq(GameState.hints_used, 3, "three hints read")
	hud.call("_close_overlay")
	await r.wait(0.1)
	hud.call("show_hint")
	await r.wait(0.1)
	eq(_rungs(hud).size(), 3, "asked again, the dialog opens at the answer with the earlier levels above")
	eq(GameState.hints_used, 3, "reopening does not count as a new hint")
	hud.call("_close_overlay")
	r.dispose()
	await (Engine.get_main_loop() as SceneTree).process_frame
	Settings.emulate = {}
	SaveSystem.delete_game()
	SaveSystem.save_path = SaveSystem.SAVE_PATH
