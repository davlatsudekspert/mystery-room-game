extends TestBase
## Every button label must fit its button at the largest text scale (1.3) in EN, RU and UZ.
## Russian is typically ~30% longer, so this catches clipped or overflowing buttons before they ship.

const BUTTONS := {
	# key: button minimum width used in the UI code (px at 1920x1080 reference)
	"ui.continue": 520, "ui.new_game": 520, "ui.chapters": 520, "ui.settings": 520, "ui.quit": 520,
	"ui.resume": 520, "ui.main_menu": 520, "ui.notebook": 520, "ui.read": 260, "ui.combine": 300,
	"ui.close": 240, "ui.hint_more": 340, "ui.take_lens": 380, "ui.leave_lens": 380, "ui.restore": 460,
	"ui.yes": 240, "ui.no": 240, "ui.play": 280, "ui.coming_soon": 280, "ui.on": 220, "ui.off": 220,
}
const PADDING := 52.0 # content margins left+right in UITheme.build()


func test_buttons_fit_at_max_text_scale() -> void:
	var font: Font = UITheme.ui_font(500)
	var size := int(round(28 * 1.3))
	for loc in ["en", "ru", "uz"]:
		TranslationServer.set_locale(loc)
		for key: String in BUTTONS:
			var w := font.get_string_size(tr(key), HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
			var room := float(BUTTONS[key]) - PADDING
			check(w <= room, "%s [%s] '%s' is %.0f px > %.0f px" % [key, loc, tr(key), w, room])
	TranslationServer.set_locale("en")


func test_hud_messages_fit_two_lines() -> void:
	## Messages are shown in a 1440 px wide line; allow at most two lines at scale 1.3.
	var font: Font = UITheme.ui_font(500)
	var size := int(round(28 * 1.3))
	var csv := FileAccess.open("res://localization/strings.csv", FileAccess.READ)
	var header := csv.get_csv_line()
	while not csv.eof_reached():
		var row := csv.get_csv_line()
		if row.size() < 4 or not row[0].begins_with("msg."):
			continue
		for i in [1, 2, 3]:
			var w := font.get_string_size(row[i].c_unescape(), HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
			check(w <= 1440.0 * 2.0, "%s [%s] too long for two lines (%.0f px)" % [row[0], header[i], w])
