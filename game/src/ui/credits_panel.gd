class_name CreditsPanel
extends RefCounted
## Settings -> About: the credits, then a Licenses page. Opened from SettingsPanel (one added button): it hides the
## settings panel, shows its own dialog in the same overlay, and brings the settings panel back when it is closed.
## The Licenses page shows, as the licences require: Godot's own licence (Engine.get_license_text()), the OFL of the two
## fonts, the MIT notices of the two purchase plugins, the third-party components bundled in Godot
## (Engine.get_copyright_info()) and the full licence texts (Engine.get_license_info()).

const DESIGN_W := 1150.0


## Shows the credits over `settings` (the SettingsPanel). Returns the dialog's root (QA and tests look inside it).
static func open(settings: Control) -> Control:
	var center := settings.get_parent() as Control # safe_center() around the settings panel
	var host := center.get_parent() as Control # the overlay it lives in (main menu panel host, pause overlay)
	if host == null:
		return null
	center.visible = false
	return show_credits(host, func() -> void:
		if is_instance_valid(center):
			center.visible = true)


## The credits page in `host`; `on_close` runs when it is closed.
static func show_credits(host: Control, on_close: Callable) -> Control:
	var d := UITheme.dialog(host, DESIGN_W, "ui.about", 50)
	var body: VBoxContainer = d["body"]
	body.add_theme_constant_override("separation", 6)
	for b: Dictionary in CreditsData.blocks():
		var text := str(b["text"])
		match int(b["kind"]):
			CreditsData.Kind.TITLE:
				body.add_child(_centered(UITheme.title(text, 54), false))
			CreditsData.Kind.SUBTITLE:
				body.add_child(_centered(_caps(text, 26, UITheme.BRASS), false))
				body.add_child(UIOrnament.rule())
			CreditsData.Kind.HEADING:
				body.add_child(_centered(_caps(text, 22, UITheme.MUTED), false))
			CreditsData.Kind.NAME:
				var l := UITheme.title(text, 38, true)
				l.add_theme_color_override("font_color", UITheme.CREAM)
				body.add_child(_centered(l, true))
			CreditsData.Kind.LINE:
				body.add_child(_centered(UITheme.label(text, 26, UITheme.MUTED), true))
			CreditsData.Kind.THANKS:
				var l := UITheme.title(text, 34, false)
				body.add_child(_centered(l, true))
			CreditsData.Kind.GAP:
				var g := Control.new()
				g.custom_minimum_size = Vector2(0, 14)
				body.add_child(g)
	var footer: HFlowContainer = d["footer"]
	var lic := UITheme.button("ui.licenses", 320)
	lic.pressed.connect(func() -> void:
		(d["root"] as Node).queue_free()
		show_licenses(host, func() -> void: show_credits(host, on_close)))
	footer.add_child(lic)
	var close := UITheme.button("ui.close", 260)
	close.pressed.connect(func() -> void:
		(d["root"] as Node).queue_free()
		on_close.call())
	footer.add_child(close)
	return d["root"]


## The Licenses page; `back` runs when it is left (Back button).
static func show_licenses(host: Control, back: Callable) -> Control:
	var d := UITheme.dialog(host, 1300.0, "ui.licenses", 46)
	var body: VBoxContainer = d["body"]
	body.add_theme_constant_override("separation", 10)
	var sections: Array[Array] = [
		["licenses.godot", "Godot Engine — MIT\n\n" + Engine.get_license_text()],
		["licenses.fonts", "Noto Sans — SIL Open Font License 1.1\n\n" + LicenseTexts.NOTO_SANS + "\n\n\nCormorant Garamond — SIL Open Font License 1.1\n\n" + LicenseTexts.CORMORANT],
		["licenses.plugins", "GodotGooglePlayBilling — MIT\n\n" + LicenseTexts.GODOT_GOOGLE_PLAY_BILLING
			+ "\n\n\nGodot iOS plugin for In-App purchase (godot_ios_plugin_iap) — MIT\n\n" + LicenseTexts.GODOT_IOS_PLUGIN_IAP
			+ "\n\n\nThe Google Play Billing Library is used under Google's Android Software Development Kit License"
			+ " (https://developer.android.com/studio/terms.html)."],
	]
	for s in sections:
		body.add_child(_heading(str(s[0])))
		body.add_child(_legal(str(s[1])))
	# the bundled third-party components of the engine, then the licence texts they refer to (built a frame later:
	# they are long and the page should appear first)
	body.add_child(_heading("licenses.components"))
	var comps := _legal("")
	body.add_child(comps)
	body.add_child(_heading("licenses.texts"))
	var texts := VBoxContainer.new()
	texts.add_theme_constant_override("separation", 10)
	body.add_child(texts)
	var fill := func() -> void:
		if not is_instance_valid(comps):
			return
		comps.text = components_text()
		var info := Engine.get_license_info()
		for k: String in info:
			texts.add_child(_legal(k + "\n\n" + str(info[k])))
	fill.call_deferred()
	var footer: HFlowContainer = d["footer"]
	var back_btn := UITheme.button("ui.back", 260)
	back_btn.pressed.connect(func() -> void:
		(d["root"] as Node).queue_free()
		back.call())
	footer.add_child(back_btn)
	return d["root"]


## "Name — © holders — License" for each third-party component Godot reports.
static func components_text() -> String:
	var lines := PackedStringArray()
	for c: Dictionary in Engine.get_copyright_info():
		for p: Dictionary in c.get("parts", []):
			var holders := ", ".join(PackedStringArray(p.get("copyright", [])))
			lines.append("%s — © %s — %s" % [c.get("name", ""), holders, p.get("license", "")])
	return "\n".join(lines)


static func _centered(l: Control, wrap: bool) -> Control:
	if l is Label:
		(l as Label).horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		(l as Label).autowrap_mode = TextServer.AUTOWRAP_WORD_SMART if wrap else TextServer.AUTOWRAP_OFF
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return l


static func _caps(text: String, size: int, color: Color) -> Label:
	var l := UITheme.label(text, size, color)
	l.add_theme_font_override("font", UITheme.caps_font(false, 2))
	l.uppercase = true
	return l


static func _heading(key: String) -> Control:
	var l := UITheme.label(key, 22, UITheme.BRASS_HI)
	l.add_theme_font_override("font", UITheme.caps_font(true, 2))
	l.uppercase = true
	l.add_theme_constant_override("line_spacing", 0)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 2)
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, 10)
	v.add_child(gap)
	v.add_child(l)
	v.add_child(UIOrnament.header_rule())
	return v


## Long legal text: small, in the UI sans (it covers every glyph the notices use), wrapped to the panel.
static func _legal(text: String) -> Label:
	var l := UITheme.label(text, 18, UITheme.MUTED)
	l.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	l.add_theme_font_override("font", UITheme.ui_font(400))
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l
