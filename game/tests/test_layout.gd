extends TestBase
## Every button label must fit its button at the largest text scale (1.3) in EN, RU and UZ, and the UI must still
## fit when the automatic phone text scale (UITheme.auto_scale) is at its cap on the narrowest canvas.
## Russian is typically ~30% longer, so this catches clipped or overflowing buttons before they ship.
## (The rendered check of every screen, with clipping / off-screen / cutout detection, is qa/ui_screens.tscn.)

const BUTTONS := {
	# key: button minimum width used in the UI code (px at 1920x1080 reference, before UITheme.wscale())
	"ui.continue": 520, "ui.new_game": 520, "ui.chapters": 520, "ui.settings": 520, "ui.quit": 520,
	"ui.resume": 520, "ui.main_menu": 520, "ui.notebook": 520, "ui.read": 260, "ui.combine": 320,
	"ui.close": 240, "ui.hint_more": 340, "ui.take_lens": 380, "ui.leave_lens": 380, "ui.restore": 420,
	"ui.yes": 240, "ui.no": 240, "ui.play": 300, "ui.coming_soon": 300,
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
	"ui.play": [1200, 1.0], "ui.coming_soon": [1200, 1.0],
}
const FLAT := ["ui.privacy", "ui.restore"] # link-style buttons without a box: they grow with their text, or wrap
const PANEL_MARGINS := 48.0 # UITheme.panel_box() content margins left+right
## A 5.5" 16:9 phone at 480 dpi: the narrowest landscape canvas (1920 px) with the auto scale at its cap.
const MAX_PHONE := {"size": Vector2i(1920, 1080), "dpi": 480.0, "safe": Rect2i(0, 0, 1920, 1080)}
## The owner's iPhone: 2556x1179 at 460 dpi, with the notch insets (177 px left and right, 63 px at the bottom).
const IPHONE := {"size": Vector2i(2556, 1179), "dpi": 460.0, "safe": Rect2i(177, 0, 2556 - 354, 1179 - 63)}
const TABLET := {"size": Vector2i(2048, 1536), "dpi": 264.0, "safe": Rect2i(0, 0, 2048, 1536)}


func _set_screen(emulate: Dictionary, user_scale: float) -> void:
	Settings.emulate = emulate
	Settings.values["text_scale"] = user_scale


func _reset_screen() -> void:
	Settings.emulate = {}
	Settings.values["text_scale"] = 1.0
	TranslationServer.set_locale("en")


## The theme's button font, size and horizontal padding for the current screen (buttons are display small caps).
func _button_metrics() -> Dictionary:
	var t := UITheme.build()
	var sb := t.get_stylebox("normal", "Button")
	return {"font": t.get_font("font", "Button"), "size": t.get_font_size("font_size", "Button"),
		"pad": sb.get_margin(SIDE_LEFT) + sb.get_margin(SIDE_RIGHT)}


func test_buttons_fit_at_max_text_scale() -> void:
	_set_screen({}, 1.5) # desktop: no automatic boost; Extra large text
	var m := _button_metrics()
	var font: Font = m["font"]
	var size: int = m["size"]
	eq(size, int(round(UITheme.BUTTON_PX * 1.5)), "no auto boost without a dense screen")
	for loc in ["en", "ru", "uz"]:
		TranslationServer.set_locale(loc)
		for key: String in BUTTONS:
			if key in FLAT:
				continue
			var w := font.get_string_size(tr(key), HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
			var room := roundf(float(BUTTONS[key]) * UITheme.wscale()) - float(m["pad"])
			check(w <= room, "%s [%s] '%s' is %.0f px > %.0f px" % [key, loc, tr(key), w, room])
	_reset_screen()


func _container_inner(spec: Variant) -> float:
	if spec is String and spec == "inspect":
		var u := UITheme.usable_rect(40.0)
		return u.size.x - 40.0 - UITheme.inspect_viewer_side() - 40.0 # hud.gd show_inspect(): 60 px side margins, 40 px gap
	if spec is String and spec == "column":
		return (UITheme.panel_width(SettingsPanel.DESIGN_W) - PANEL_MARGINS - 48.0) * 0.5
	return UITheme.panel_width(float(spec)) - PANEL_MARGINS


func test_buttons_fit_on_phone_at_max_auto_scale() -> void:
	## Buttons grow with their text, and rows wrap (UITheme.button_row), so the limit is the container:
	## no single button may be wider than the narrowest panel or column it appears in.
	for user in [1.0, 1.5]:
		_set_screen(MAX_PHONE, user)
		check(UITheme.auto_scale() >= 2.5, "the 480 dpi phone gets a large automatic boost (%.2f)" % UITheme.auto_scale())
		var m := _button_metrics()
		var font: Font = m["font"]
		var size: int = m["size"]
		for loc in ["en", "ru", "uz"]:
			TranslationServer.set_locale(loc)
			for key: String in BUTTONS:
				if key in FLAT:
					continue # text links wrap onto several lines when they must
				var w := font.get_string_size(tr(key), HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
				var need := maxf(roundf(float(BUTTONS[key]) * UITheme.wscale()), w + float(m["pad"]))
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
	## Messages are shown in a 1440 px wide line; allow at most two lines at Extra large on a desktop.
	_set_screen({}, 1.5)
	var font: Font = UITheme.ui_font(500)
	var size := UITheme.size(28)
	for m: Array in _msg_widths("msg."):
		var w := font.get_string_size(m[2], HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
		check(w <= 1440.0 * 2.0, "%s [%s] too long for two lines (%.0f px)" % [m[0], m[1], w])
	_reset_screen()


func test_hud_messages_fit_on_phone_at_max_auto_scale() -> void:
	## On the densest phone: four lines at Normal, six at Extra large for the longest message (the banner grows
	## upward; the 3D view stays visible above it).
	for pair in [[1.0, 4], [1.5, 6]]:
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
	## Phones and tablets: body text reaches a 3 mm cap height at Normal, nothing is below MIN_TEXT_MM, touch
	## targets >= 9 mm, inventory slots >= 8 mm; titles still lead body text; Large / Extra large multiply.
	for dev: Dictionary in [IPHONE, {"size": Vector2i(1920, 1080), "dpi": 400.0}, MAX_PHONE, TABLET]:
		_set_screen(dev, 1.0)
		var mm := UITheme.mm_per_px()
		var tag := "%s @ %.0f dpi" % [dev["size"], dev["dpi"]]
		check(UITheme.size(26) * mm * UITheme.CAP_EM >= UITheme.BODY_CAP_MM - 0.05, "%s: body cap height %.2f mm" % [tag, UITheme.size(26) * mm * UITheme.CAP_EM])
		check(UITheme.size(18) * mm >= UITheme.MIN_TEXT_MM - 0.05, "%s: smallest text %.2f mm" % [tag, UITheme.size(18) * mm])
		check(UITheme.target(92) * mm >= UITheme.TOUCH_MM - 0.01, "%s: touch target %.1f mm" % [tag, UITheme.target(92) * mm])
		check(UITheme.target(112, UITheme.SLOT_MM) * mm >= 8.0, "%s: inventory slot %.1f mm" % [tag, UITheme.target(112, UITheme.SLOT_MM) * mm])
		check(UITheme.size(80) > UITheme.size(50) and UITheme.size(50) > UITheme.size(34) and UITheme.size(34) > UITheme.size(26), "%s: titles lead body text (%d > %d > %d > %d)" % [tag, UITheme.size(80), UITheme.size(50), UITheme.size(34), UITheme.size(26)])
		var normal := UITheme.size(26)
		Settings.values["text_scale"] = 1.25
		var large := UITheme.size(26)
		Settings.values["text_scale"] = 1.5
		var xl := UITheme.size(26)
		check(large > normal and xl > large, "%s: Large (%d) and Extra large (%d) grow on Normal (%d)" % [tag, large, xl, normal])
		check(xl * mm <= 8.0, "%s: Extra large body text %.1f mm stays usable" % [tag, xl * mm])
	# a desktop window: no boost, the design sizes stay
	_set_screen({"size": Vector2i(1920, 1080), "dpi": 96.0}, 1.0)
	check(is_equal_approx(UITheme.auto_scale(), 1.0), "desktop auto scale")
	eq(UITheme.size(26), 26, "desktop body size")
	_reset_screen()


## Walks a built panel: every button and slider is a full touch target, no label is clipped or wider than its
## box, and every text stays inside the panel horizontally (the body may scroll vertically).
func _check_panel_controls(panel: Control, tag: String) -> void:
	var pr := panel.get_global_rect()
	for n in panel.find_children("*", "Control", true, false):
		var c := n as Control
		if not c.is_visible_in_tree():
			continue
		var r := c.get_global_rect()
		if c is Button:
			var b := c as Button
			var want := UITheme.target(78)
			check(r.size.y >= want - 0.5, "%s: button «%s» is %.0f px tall, a touch target is %.0f" % [tag, tr(b.text), r.size.y, want])
			if b.text != "" and b.autowrap_mode == TextServer.AUTOWRAP_OFF:
				var sb := b.get_theme_stylebox("normal")
				var room := r.size.x - sb.get_margin(SIDE_LEFT) - sb.get_margin(SIDE_RIGHT)
				var w := b.get_theme_font("font").get_string_size(b.atr(b.text), HORIZONTAL_ALIGNMENT_LEFT, -1, b.get_theme_font_size("font_size")).x
				check(w <= room + 2.0, "%s: button text «%s» is %.0f px wide in %.0f px" % [tag, b.atr(b.text), w, room])
		elif c is HSlider:
			check(r.size.y >= UITheme.target(64, 8.0) - 0.5, "%s: slider is %.0f px tall" % [tag, r.size.y])
		elif c is Label and (c as Label).text.strip_edges() != "":
			var l := c as Label
			var text := l.atr(l.text)
			check(l.get_visible_line_count() >= l.get_line_count(), "%s: label «%s» shows %d of %d lines" % [tag, text.left(40), l.get_visible_line_count(), l.get_line_count()])
			if l.autowrap_mode == TextServer.AUTOWRAP_OFF:
				var w := l.get_theme_font("font").get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, l.get_theme_font_size("font_size")).x
				check(w <= r.size.x + 2.0, "%s: label «%s» is %.0f px wide in a %.0f px box" % [tag, text.left(40), w, r.size.x])
			check(r.position.x >= pr.position.x - 1.0 and r.end.x <= pr.end.x + 1.0, "%s: label «%s» sticks out of the panel sideways" % [tag, text.left(40)])


## The settings panel, built for real (headless) on the owner's iPhone, the narrowest 16:9 phone and a 10" tablet,
## at the default and the largest text size, in EN, RU and UZ: it stays inside the usable screen, its footer
## never overlaps the body, and its controls are full touch targets with nothing clipped.
func test_settings_panel_fits_the_screen() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	var devices := {"iphone": IPHONE, "phone55": MAX_PHONE, "tablet10": TABLET}
	for dev: String in devices:
		for user in [1.0, 1.5]:
			for loc in ["en", "ru", "uz"]:
				_set_screen(devices[dev], float(user))
				TranslationServer.set_locale(loc)
				var tag := "settings %s x%.2f [%s]" % [dev, user, loc]
				var canvas: Vector2 = UITheme.metrics()["canvas"]
				var host := Control.new()
				host.size = canvas
				tree.root.add_child.call_deferred(host) # the runner itself is still inside the root's _ready
				await tree.process_frame
				var sp := SettingsPanel.new()
				UITheme.safe_center(host).add_child(sp)
				for i in 3: # build, the deferred body fit, the scroll container's layout
					await tree.process_frame
				if sp.get("_footer") == null or not sp.is_inside_tree():
					check(false, "%s: the panel did not build" % tag)
					host.queue_free()
					continue
				var usable := UITheme.usable_rect()
				var r := sp.get_global_rect()
				check(usable.grow(1.0).encloses(r), "%s: panel %s outside the usable rect %s" % [tag, r, usable])
				var footer := sp.get("_footer") as Control
				var body := sp.get("_scroll_host") as Control
				var header := sp.get("_header") as Control
				check(footer.get_global_rect().position.y >= body.get_global_rect().end.y - 0.5, "%s: the footer overlaps the body" % tag)
				check(body.get_global_rect().position.y >= header.get_global_rect().end.y - 0.5, "%s: the body overlaps the header" % tag)
				check(body.size.y >= UITheme.target(78) * 2.0, "%s: the body has only %.0f px" % [tag, body.size.y])
				_check_panel_controls(sp, tag)
				host.queue_free()
				await tree.process_frame
	_reset_screen()


## HUD geometry at Normal and Extra large on the owner's iPhone and the narrowest 16:9 phone: the inventory
## column, the bottom banners and the corner buttons never overlap each other, and the banners keep a usable width.
func test_hud_elements_do_not_collide() -> void:
	for dev: Dictionary in [IPHONE, MAX_PHONE]:
		for user in [1.0, 1.5]:
			_set_screen(dev, float(user))
			var tag := "hud %s x%.2f" % [dev["size"], user]
			var canvas: Vector2 = UITheme.metrics()["canvas"]
			var safe := UITheme.safe_margins()
			var pad := UITheme.HUD_PAD
			var btn := UITheme.target(UITheme.HUD_BTN_PX)
			var back := UITheme.target(UITheme.HUD_BACK_PX)
			var col_top := safe.y + pad + back + 16.0
			var column := Rect2(safe.x + pad, col_top, UITheme.hud_column_width(), canvas.y - safe.w - pad - col_top)
			var pause := Rect2(canvas.x - safe.z - pad - btn, canvas.y - safe.w - pad - btn, btn, btn)
			var hint := Rect2(canvas.x - safe.z - pad - btn, safe.y + pad, btn, btn)
			var back_r := Rect2(safe.x + pad, safe.y + pad, back, back)
			var band_w := UITheme.hud_text_width()
			var band := Rect2((canvas.x - band_w) * 0.5, canvas.y - safe.w - pad - 300.0, band_w, 300.0) # a tall message
			check(not column.intersects(band), "%s: the inventory column %s overlaps the message band %s" % [tag, column, band])
			check(not pause.intersects(band), "%s: the pause button overlaps the message band" % tag)
			check(not column.intersects(back_r) and not column.intersects(pause), "%s: the column overlaps a corner button" % tag)
			check(not hint.intersects(back_r), "%s: hint and back overlap" % tag)
			check(band_w >= 600.0, "%s: the message band is only %.0f px wide" % [tag, band_w])
			check(column.size.y >= 3.0 * UITheme.target(UITheme.HUD_SLOT_PX, UITheme.SLOT_MM), "%s: the column has room for fewer than three slots (%.0f px)" % [tag, column.size.y])
			# the longest view titles fit the top band in two lines of display small caps at Normal, three at XL
			var caps := UITheme.caps_font(true, 2)
			var fs := UITheme.size(UITheme.HUD_TITLE_PX)
			var top_w := canvas.x - 2.0 * (maxf(safe.x, safe.z) + pad + maxf(btn, back) + 20.0) - 64.0
			var lines := 2 if user < 1.1 else 3
			for loc in ["en", "ru", "uz"]:
				TranslationServer.set_locale(loc)
				for key in ["obj.drawing", "obj.poster", "obj2.chart", "obj.chalkboard"]:
					var w := caps.get_string_size(tr(key), HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
					check(w <= top_w * lines * 0.92, "%s [%s]: title «%s» needs more than %d lines (%.0f px in %.0f)" % [tag, loc, tr(key), lines, w, top_w])
	_reset_screen()


func test_safe_area_insets() -> void:
	# a left camera cutout of 120 device px on a 1920 px wide screen = 120 canvas px
	_set_screen({"size": Vector2i(1920, 1080), "dpi": 400.0, "safe": Rect2i(120, 0, 1800, 1050)}, 1.0)
	var s := UITheme.safe_margins()
	check(is_equal_approx(s.x, 120.0) and is_equal_approx(s.w, 30.0) and is_zero_approx(s.z), "insets %s" % s)
	check(UITheme.usable_rect().position.x >= 120.0, "usable rect starts right of the cutout")
	_reset_screen()
