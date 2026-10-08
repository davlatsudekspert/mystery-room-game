extends Control
## First launch: choose EN → RU → UZ (device language preselected, English fallback).


func _ready() -> void:
	theme = UITheme.build()
	set_anchors_preset(Control.PRESET_FULL_RECT)
	var bg := ColorRect.new()
	bg.color = UITheme.INK
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var c := CenterContainer.new()
	c.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(c)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 24)
	c.add_child(v)
	var t := UITheme.title("MYSTERY ROOM", 80)
	t.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	v.add_child(t)
	# The prompt is shown in all three languages so everyone can read it.
	var prompt := UITheme.label("Choose your language · Выберите язык · Tilni tanlang", 28, UITheme.MUTED)
	prompt.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	prompt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(prompt)
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
