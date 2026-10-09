extends Control
## First launch: choose EN → RU → UZ (device language preselected, English fallback).


func _ready() -> void:
	theme = UITheme.build()
	set_anchors_preset(Control.PRESET_FULL_RECT)
	var bg := ColorRect.new()
	bg.color = UITheme.INK
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var c := UITheme.safe_center(self)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 18)
	var max_h := UITheme.usable_rect().size.y
	c.add_child(UITheme.scroll_fit(v, null, max_h)) # never taller than the screen, whatever the text size
	var t := UITheme.title("MYSTERY ROOM", 80)
	t.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	t.autowrap_mode = TextServer.AUTOWRAP_OFF
	v.add_child(t)
	# The prompt is shown in all three languages (one per line, same EN → RU → UZ order) so everyone can read it.
	for line in ["Choose your language", "Выберите язык", "Tilni tanlang"]:
		var prompt := UITheme.label(line, 28, UITheme.MUTED)
		prompt.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
		prompt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		prompt.autowrap_mode = TextServer.AUTOWRAP_OFF
		v.add_child(prompt)
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, 12)
	v.add_child(gap)
	var detected := Loc.detect_device_language()
	for code in Loc.SUPPORTED:
		var b := UITheme.button(Loc.NATIVE_NAMES[code], 520)
		b.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
		if code == detected:
			b.add_theme_color_override("font_color", UITheme.BRASS_HI)
		b.pressed.connect(func() -> void:
			Loc.choose(code)
			SceneManager.goto("res://src/ui/main_menu.tscn"))
		var cc := CenterContainer.new()
		cc.add_child(b)
		v.add_child(cc)
