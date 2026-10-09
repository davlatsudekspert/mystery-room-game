extends TestBase
## Every button label must fit its button at the largest text scale (1.3) in EN, RU and UZ, and the UI must still
## fit when the automatic phone text scale (UITheme.auto_scale) is at its cap on the narrowest canvas.
## Russian is typically ~30% longer, so this catches clipped or overflowing buttons before they ship.
## (The rendered check of every screen, with clipping / off-screen / cutout detection, is qa/ui_screens.tscn.)

const BUTTONS := {
	# key: button minimum width used in the UI code (px at 1920x1080 reference, before UITheme.wscale())
	"ui.continue": 520, "ui.new_game": 520, "ui.chapters": 520, "ui.settings": 520, "ui.quit": 520,
	"ui.resume": 520, "ui.main_menu": 520, "ui.notebook": 520, "ui.read": 260, "ui.combine": 300,
	"ui.close": 240, "ui.hint_more": 340, "ui.take_lens": 380, "ui.leave_lens": 380, "ui.restore": 420,
	"ui.yes": 240, "ui.no": 240, "ui.play": 280, "ui.coming_soon": 280, "ui.on": 200, "ui.off": 200,
	"ui.privacy": 380,
}
## The narrowest container each button appears in: [design width of the panel, share of its inner width].
## "inspect" = the text column next to the 3D item viewer, "column" = one settings column.
const CONTAINERS := {
	"ui.continue": [800, 1.0], "ui.new_game": [800, 1.0], "ui.chapters": [800, 1.0], "ui.quit": [800, 1.0],
	"ui.settings": [620, 1.0], "ui.resume": [620, 1.0], "ui.main_menu": [620, 1.0], "ui.notebook": [620, 1.0],
	"ui.read": ["inspect", 1.0], "ui.combine": ["inspect", 1.0], "ui.close": ["inspect", 1.0],
	"ui.hint_more": [980, 1.0], "ui.take_lens": [1000, 1.0], "ui.leave_lens": [1000, 1.0],
	"ui.restore": [1500, 1.0], "ui.privacy": [1500, 1.0], "ui.yes": [900, 1.0], "ui.no": [900, 1.0],
	"ui.play": [1200, 0.4], "ui.coming_soon": [1200, 0.4], "ui.on": ["column", 0.5], "ui.off": ["column", 0.5],
}
const FLAT := ["ui.privacy"] # link-style buttons without a box: they may simply grow with their text
const PADDING := 52.0 # content margins left+right in UITheme.build()
const PANEL_MARGINS := 36.0 # UITheme.panel_box() content margins left+right
## A 5.5" 16:9 phone at 480 dpi: the narrowest landscape canvas (1920 px) with the auto scale at its cap.
const MAX_PHONE := {"size": Vector2i(1920, 1080), "dpi": 480.0, "safe": Rect2i(0, 0, 1920, 1080)}


func _set_screen(emulate: Dictionary, user_scale: float) -> void:
	Settings.emulate = emulate
	Settings.values["text_scale"] = user_scale


func _reset_screen() -> void:
	Settings.emulate = {}
	Settings.values["text_scale"] = 1.0
	TranslationServer.set_locale("en")


func test_buttons_fit_at_max_text_scale() -> void:
	_set_screen({}, 1.3) # desktop / tablet: no automatic boost
	var font: Font = UITheme.ui_font(500)
	var size := UITheme.size(28)
	eq(size, int(round(28 * 1.3)), "no auto boost without a dense screen")
	for loc in ["en", "ru", "uz"]:
		TranslationServer.set_locale(loc)
		for key: String in BUTTONS:
			if key in FLAT:
				continue
			var w := font.get_string_size(tr(key), HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
			var room := roundf(float(BUTTONS[key]) * UITheme.wscale()) - PADDING
			check(w <= room, "%s [%s] '%s' is %.0f px > %.0f px" % [key, loc, tr(key), w, room])
	_reset_screen()


func _container_inner(spec: Variant) -> float:
	if spec is String and spec == "inspect":
		var u := UITheme.usable_rect(40.0)
		var side := minf(880.0, minf(u.size.y, u.size.x * 0.45))
		return u.size.x - 40.0 - side - 40.0 # hud.gd show_inspect(): 60 px side margins, 40 px gap
	if spec is String and spec == "column":
		return (UITheme.panel_width(SettingsPanel.DESIGN_W) - PANEL_MARGINS - 48.0) * 0.5
	return UITheme.panel_width(float(spec)) - PANEL_MARGINS


func test_buttons_fit_on_phone_at_max_auto_scale() -> void:
	## Buttons grow with their text, and rows wrap (UITheme.button_row), so the limit is the container:
	## no single button may be wider than the narrowest panel or column it appears in.
	for user in [1.0, 1.3]:
		_set_screen(MAX_PHONE, user)
		check(is_equal_approx(UITheme.auto_scale(), UITheme.AUTO_MAX), "the 480 dpi phone reaches the auto cap")
		var font: Font = UITheme.ui_font(500)
		var size := UITheme.size(28)
		for loc in ["en", "ru", "uz"]:
			TranslationServer.set_locale(loc)
			for key: String in BUTTONS:
				var w := font.get_string_size(tr(key), HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
				var need := maxf(roundf(float(BUTTONS[key]) * UITheme.wscale()), w + PADDING)
				var spec: Array = CONTAINERS[key]
				var room := _container_inner(spec[0]) * float(spec[1])
				check(need <= room, "%s [%s] x%.2f needs %.0f px, its container has %.0f px" % [key, loc, user, need, room])
	_reset_screen()


func _msg_widths(csv_prefix: String) -> Array:
	var out: Array = []
	var csv := FileAccess.open("res://localization/strings.csv", FileAccess.READ)
	var header := csv.get_csv_line()
	while not csv.eof_reached():
		var row := csv.get_csv_line()
		if row.size() < 4 or not row[0].begins_with(csv_prefix):
			continue
		for i in [1, 2, 3]:
			out.append([row[0], header[i], row[i].c_unescape()])
	return out


func test_hud_messages_fit_two_lines() -> void:
	## Messages are shown in a 1440 px wide line; allow at most two lines at scale 1.3.
	_set_screen({}, 1.3)
	var font: Font = UITheme.ui_font(500)
	var size := UITheme.size(28)
	for m: Array in _msg_widths("msg."):
		var w := font.get_string_size(m[2], HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
		check(w <= 1440.0 * 2.0, "%s [%s] too long for two lines (%.0f px)" % [m[0], m[1], w])
	_reset_screen()


func test_hud_messages_fit_on_phone_at_max_auto_scale() -> void:
	## On the densest phone: two lines at the default text size, three at the largest (the plate grows upward,
	## the 3D view stays visible above it).
	for pair in [[1.0, 2], [1.3, 3]]:
		_set_screen(MAX_PHONE, float(pair[0]))
		var font: Font = UITheme.ui_font(500)
		var size := UITheme.size(28)
		var line := UITheme.hud_text_width() - UITheme.caption_plate().get_minimum_size().x
		for m: Array in _msg_widths("msg."):
			var w := font.get_string_size(m[2], HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
			# word wrapping loses part of each line; 0.9 keeps the estimate honest
			check(w <= line * 0.9 * int(pair[1]), "%s [%s] x%.2f: %.0f px > %d lines of %.0f px" % [m[0], m[1], pair[0], w, pair[1], line])
	_reset_screen()


func test_auto_scale_reaches_readable_sizes() -> void:
	# 6" 16:9 phone at 400 dpi: body text ~2.6 mm, touch targets >= 9 mm, inventory slots >= 8 mm
	_set_screen({"size": Vector2i(1920, 1080), "dpi": 400.0}, 1.0)
	var mm := UITheme.mm_per_px()
	check(UITheme.size(26) * mm >= 2.55, "body text %.2f mm on a 400 dpi phone" % (UITheme.size(26) * mm))
	check(UITheme.size(18) * mm >= UITheme.MIN_TEXT_MM - 0.05, "smallest text %.2f mm" % (UITheme.size(18) * mm))
	check(UITheme.target(92) * mm >= UITheme.TOUCH_MM - 0.01, "touch target %.1f mm" % (UITheme.target(92) * mm))
	check(UITheme.target(112, UITheme.SLOT_MM) * mm >= 8.0, "inventory slot %.1f mm" % (UITheme.target(112, UITheme.SLOT_MM) * mm))
	check(UITheme.size(80) <= 80, "display titles are not boosted")
	# the player's text size still multiplies on top
	Settings.values["text_scale"] = 1.3
	check(UITheme.size(26) > int(round(26 * UITheme.auto_scale())), "Text size multiplies the auto scale")
	# 10" tablet at 264 dpi and a desktop window: no boost, the design sizes stay
	_set_screen({"size": Vector2i(2048, 1536), "dpi": 264.0}, 1.0)
	check(is_equal_approx(UITheme.auto_scale(), 1.0), "tablet auto scale %.2f" % UITheme.auto_scale())
	eq(UITheme.size(26), 26, "tablet body size")
	_set_screen({"size": Vector2i(1920, 1080), "dpi": 96.0}, 1.0)
	check(is_equal_approx(UITheme.auto_scale(), 1.0), "desktop auto scale")
	_reset_screen()


func test_safe_area_insets() -> void:
	# a left camera cutout of 120 device px on a 1920 px wide screen = 120 canvas px
	_set_screen({"size": Vector2i(1920, 1080), "dpi": 400.0, "safe": Rect2i(120, 0, 1800, 1050)}, 1.0)
	var s := UITheme.safe_margins()
	check(is_equal_approx(s.x, 120.0) and is_equal_approx(s.w, 30.0) and is_zero_approx(s.z), "insets %s" % s)
	check(UITheme.usable_rect().position.x >= 120.0, "usable rect starts right of the cutout")
	_reset_screen()
