extends TestBase
## The HUD on every screen shape the game ships for (owner feedback, item 6): 16:9, 19.5:9 (the owner's iPhone),
## 20:9 (a tall Android phone) and 4:3 (an iPad), at Normal, Large and Extra large, in EN, RU and UZ. With the
## busiest HUD there is (a long view title, the Chapter 2 meter, the bag open with five items and the item
## actions, the prompt, a found-item banner or the longest message, and a caption), no two HUD elements overlap,
## every one lies inside the safe area (notch, home indicator, Android bars), and every button is a full touch
## target (UITheme.TOUCH_MM).

const DEVICES := {
	"16:9 phone": {"size": Vector2i(1920, 1080), "dpi": 480.0, "safe": Rect2i(0, 0, 1920, 1080)},
	"19.5:9 iPhone": {"size": Vector2i(2556, 1179), "dpi": 460.0, "safe": Rect2i(177, 0, 2556 - 354, 1179 - 63)},
	"20:9 Android": {"size": Vector2i(2400, 1080), "dpi": 405.0, "safe": Rect2i(100, 0, 2300, 1080 - 56)},
	"4:3 iPad": {"size": Vector2i(2048, 1536), "dpi": 264.0, "safe": Rect2i(0, 0, 2048, 1536 - 40)},
}
const SIZES := [1.0, 1.25, 1.5]
const LANGS := ["en", "ru", "uz"]
const ITEMS := ["notebook", "uv_lamp", "battery_cell", "crystal_lens", "brass_key"]


func _longest(prefix: String) -> String:
	var best := ""
	var csv := FileAccess.open("res://localization/strings.csv", FileAccess.READ)
	csv.get_csv_line()
	while not csv.eof_reached():
		var row := csv.get_csv_line()
		if row.size() >= 4 and row[0].begins_with(prefix) and tr(row[0]).length() > tr(best).length():
			best = row[0]
	return tr(best).c_unescape()


## [name, rect] of every HUD element that shows: corner buttons, the bag, banners that are on, the meter, the
## visible part of each slot and the item actions.
func _elements(hud: Node) -> Array:
	var out: Array = []
	for prop in ["_back_btn", "_hint_btn", "_pause_btn", "_bag_btn", "_meter"]:
		var c := hud.get(prop) as Control
		if c != null and c.is_visible_in_tree():
			out.append([prop.substr(1), c.get_global_rect()])
	for prop in ["_top_plate", "_prompt_plate", "_msg_plate", "_cap_plate"]:
		var p := hud.get(prop) as UIBanner
		if p.is_visible_in_tree() and p.has_text() and bool(p.get_meta("on", true)):
			out.append([prop.substr(1), p.get_global_rect()])
	var tray := hud.get("_inv_panel") as Control
	if tray.is_visible_in_tree():
		var clip := (hud.get("_inv_scroll") as Control).get_global_rect()
		for s in (hud.get("_inv_box") as Control).get_children():
			var r := (s as Control).get_global_rect().intersection(clip)
			if r.size.y > 1.0:
				out.append(["slot", r])
		for b in (hud.get("_actions") as Control).get_children():
			if (b as Control).is_visible_in_tree():
				out.append(["action", (b as Control).get_global_rect()])
	return out


func _check_layout(hud: Node, tag: String) -> void:
	var safe: Rect2 = UITheme.metrics()["safe"]
	var mm := UITheme.mm_per_px()
	var els := _elements(hud)
	for e: Array in els:
		var r: Rect2 = e[1]
		check(safe.grow(1.0).encloses(r), "%s: %s %s is outside the safe area %s" % [tag, e[0], r, safe])
	for i in els.size():
		for j in range(i + 1, els.size()):
			var a: Rect2 = els[i][1]
			var b: Rect2 = els[j][1]
			check(not a.intersects(b) or a.intersection(b).get_area() <= 1.0, "%s: %s %s overlaps %s %s" % [tag, els[i][0], a, els[j][0], b])
	for prop in ["_back_btn", "_hint_btn", "_pause_btn", "_bag_btn", "_act_inspect", "_act_combine"]:
		var c := hud.get(prop) as Control
		if c != null and c.is_visible_in_tree():
			var side := minf(c.size.x, c.size.y) * mm
			check(side >= UITheme.TOUCH_MM - 0.05, "%s: %s is %.1f mm" % [tag, prop.substr(1), side])
	for s in (hud.get("_inv_box") as Control).get_children():
		if (s as Control).is_visible_in_tree():
			var side := minf((s as Control).size.x, (s as Control).size.y) * mm
			check(side >= UITheme.TOUCH_MM - 0.05, "%s: a slot is %.1f mm" % [tag, side])
			break
	var title := hud.get("_top_plate") as UIBanner
	check(title.visible and bool(title.get_meta("on", true)), "%s: the view title shows" % tag)
	check((hud.get("_prompt_plate") as UIBanner).visible, "%s: the prompt shows" % tag)


func test_hud_fits_every_screen_and_text_size() -> void:
	SaveSystem.save_path = "user://test_hud_layout.json"
	Settings.path = "user://test_hud_layout_settings.cfg"
	Settings.values["reduce_motion"] = true # the tray is at rest at once (the layout is the same)
	for dev: String in DEVICES:
		for user: float in SIZES:
			for loc: String in LANGS:
				Settings.emulate = DEVICES[dev]
				Settings.values["text_scale"] = user
				TranslationServer.set_locale(loc)
				GameState.start_new("ch1")
				var l := GameState.logic
				l._begin()
				for id: String in ITEMS:
					l._add_item(id)
				l._end()
				var r := HudTestRoom.create(l, true)
				await r.attach()
				var hud := r.hud
				var tag := "%s x%.2f [%s]" % [dev, user, loc]
				hud.call("set_bag_open", true, true)
				l.select_item("battery_cell")
				hud.call("set_meter", 3)
				hud.call("set_caption", "obj.drawing") # the longest view title
				# (a) an item found, then a caption
				hud.call("message", tr("ui.item_added") % tr(ItemDB.name_key("notebook")), 30.0)
				hud.call("caption", tr("cap2.vault_reel"), 30.0)
				await r.wait(0.08)
				_check_layout(hud, tag + " found+caption")
				# (b) a caption, then the longest message: the newer keeps its place
				hud.call("caption", tr("cap2.vault_reel"), 30.0)
				hud.call("message", _longest("msg."), 30.0)
				await r.wait(0.08)
				_check_layout(hud, tag + " caption+message")
				check(bool((hud.get("_msg_plate") as UIBanner).get_meta("on", false)), "%s: the newer message shows" % tag)
				# (c) the bag in, a close-up: only the corner buttons and the bag take room on the left
				r.cam.go("desk", true)
				hud.call("set_caption", "obj.drawing")
				await r.wait(0.05)
				_check_layout(hud, tag + " close-up")
				r.dispose()
				await (Engine.get_main_loop() as SceneTree).process_frame
	Settings.emulate = {}
	Settings.values["text_scale"] = 1.0
	Settings.values["reduce_motion"] = false
	Settings.values["inventory_open"] = false
	DirAccess.remove_absolute(Settings.path)
	Settings.path = Settings.PATH
	TranslationServer.set_locale("en")
	SaveSystem.delete_game()
	SaveSystem.save_path = SaveSystem.SAVE_PATH
