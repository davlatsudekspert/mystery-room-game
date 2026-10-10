class_name UITheme
extends RefCounted
## Design tokens (docs/UI_UX.md, docs/ART_DIRECTION.md), the generated Godot Theme, and the screen-aware sizing
## that keeps text readable and targets tappable on phones:
##   - auto text scale: body text (26 canvas px) is raised until it is ~2.6 mm tall on the player's screen
##     (Android 16sp / iOS 17pt body text), from the screen's dpi and the canvas stretch. Titles are raised less,
##     so the hierarchy is compressed on small screens instead of everything getting huge.
##   - the player's Settings → Text size multiplies on top.
##   - touch targets are at least TOUCH_MM (inventory slots SLOT_MM) on the physical screen.
##   - safe area (notches, rounded corners, home indicator) in canvas units for every screen.

const INK := Color("0e0f12")
const PANEL := Color(0.055, 0.06, 0.07, 0.9)
const PANEL_DARK := Color(0.036, 0.039, 0.047) # dialog and settings panels (alpha set by panel_box)
const HAIRLINE := Color(0.79, 0.64, 0.37, 0.16) # thin brass separators between rows
const BRASS := Color("c9a35e")
const BRASS_HI := Color("e3c27a")
const CREAM := Color("ede3cf")
const MUTED := Color("b5ab97") # secondary text: ≥ 8:1 on panels, ≥ 4.5:1 on a 0.8-alpha plate over a white 3D frame
const DANGER := Color("b5523b")
const SUCCESS := Color("6fb39a")
const UV := Color("9c7bff")

const FONT_UI := "res://assets/fonts/NotoSans-Variable.ttf"
const FONT_DISPLAY := "res://assets/fonts/CormorantGaramond-SemiBold.ttf"
const FONT_DISPLAY_BOLD := "res://assets/fonts/CormorantGaramond-Bold.ttf"
const FONT_HAND := "res://assets/fonts/Caveat-Variable.ttf"

const BODY_PX := 26 # theme body size (canvas px at scale 1)
const BUTTON_PX := 34 # button text: display serif in small caps (a smaller x-height than the sans body text)
const BODY_CAP_MM := 3.0 # target cap height of body text at Settings → Text size "Normal" (readable at arm's length)
const CAP_EM := 0.714 # Noto Sans: cap height / em
const BODY_MM := BODY_CAP_MM / CAP_EM # target em height of body text on the physical screen (~4.2 mm)
const MIN_TEXT_MM := 3.0 # em height: nothing the player must read is smaller than this
const TITLE_PX := 72 # from BODY_PX up to here the boost tapers to TITLE_BOOST of the body's (titles still lead)
const TITLE_BOOST := 0.5
const AUTO_MAX := 3.2 # cap: very small/dense screens get scrolling, not ever-larger text
const TOUCH_MM := 9.0 # minimum touch target (~48 dp with margin)
const SLOT_MM := 9.0 # inventory slots (a full touch target since the tray folds away into the bag)
const MARGIN := 24.0 # breathing room between panels and the safe-area edge (canvas px)
const FALLBACK_DPI := 96.0
const BASE_CANVAS := Vector2(1920, 1080) # project.godot viewport size

static var _cache: Dictionary = {}


# ====================================================================== screen metrics
## Physical screen facts for the current window, in canvas units (the 1920x1080-based stretched canvas).
## Settings.emulate ({"size", "dpi", "safe"}) lets QA render a phone on a desktop.
static func metrics() -> Dictionary:
	var canvas := BASE_CANVAS
	var window := BASE_CANVAS
	var tree := Engine.get_main_loop() as SceneTree
	if tree != null and tree.root != null:
		var vr := tree.root.get_visible_rect().size
		if vr.x > 0.0 and vr.y > 0.0:
			canvas = vr
		window = Vector2(tree.root.size)
	var emu: Dictionary = Settings.emulate
	var screen := window
	var dpi := float(DisplayServer.screen_get_dpi())
	if emu.has("size"):
		screen = Vector2(emu["size"])
		dpi = float(emu.get("dpi", dpi))
		canvas = _expand(screen) # the canvas this screen would get (canvas_items stretch, aspect expand)
	elif DisplayServer.get_name() == "headless" or window.x < 320.0 or window.y < 180.0:
		screen = canvas # no physical screen (tests, exports): design sizes, no automatic boost
		dpi = FALLBACK_DPI
	if dpi < 50.0 or dpi > 1200.0:
		dpi = FALLBACK_DPI
	var px_per_canvas := screen.x / canvas.x
	var safe := Rect2(Vector2.ZERO, canvas)
	if emu.has("safe") or (OS.has_feature("mobile") and not emu.has("size")):
		# DisplayServer reports the screen's safe area; on desktop the window is not the screen, so it is ignored
		var s: Rect2i = emu["safe"] if emu.has("safe") else DisplayServer.get_display_safe_area()
		if s.size.x > 0 and s.size.y > 0:
			safe = Rect2(Vector2(s.position) / px_per_canvas, Vector2(s.size) / px_per_canvas).intersection(Rect2(Vector2.ZERO, canvas))
	return {"canvas": canvas, "screen": screen, "dpi": dpi, "px_per_canvas": px_per_canvas,
		"mm_per_px": px_per_canvas * 25.4 / dpi, "safe": safe}


## The stretched canvas for a window of this size (project: 1920x1080, canvas_items, aspect expand).
static func _expand(win: Vector2) -> Vector2:
	if win.x <= 0.0 or win.y <= 0.0:
		return BASE_CANVAS
	var aspect := win.x / win.y
	if aspect >= BASE_CANVAS.x / BASE_CANVAS.y:
		return Vector2(BASE_CANVAS.y * aspect, BASE_CANVAS.y)
	return Vector2(BASE_CANVAS.x, BASE_CANVAS.x / aspect)


## Millimetres on the physical screen per canvas px.
static func mm_per_px() -> float:
	return float(metrics()["mm_per_px"])


## Automatic text scale for this screen (1.0 on a desktop, ~1.6 on a 10" tablet, ~2.7 on a 6" phone).
static func auto_scale() -> float:
	var body_mm := BODY_PX * mm_per_px()
	return clampf(BODY_MM / body_mm, 1.0, AUTO_MAX)


## The player's Settings → Text size.
static func user_scale() -> float:
	return float(Settings.get_value("text_scale"))


## Overall body-text multiplier (auto × player).
static func scale() -> float:
	return auto_scale() * user_scale()


## Font size in canvas px for a design size (at 1920x1080, text scale 1). `user` overrides the player's
## Settings → Text size (the settings panel previews each step with it).
static func size(base: int, user: float = -1.0) -> int:
	var u := user_scale() if user <= 0.0 else user
	var a := auto_scale()
	# body sizes get the whole boost; from BODY_PX to TITLE_PX it tapers to TITLE_BOOST of it (monotonic: a
	# bigger design size is always a bigger size on screen, so titles keep leading body text)
	var t := clampf(float(base - BODY_PX) / float(TITLE_PX - BODY_PX), 0.0, 1.0)
	var w := 1.0 - (1.0 - TITLE_BOOST) * t
	var px := base * u * (1.0 + (a - 1.0) * w)
	# small print is lifted to MIN_TEXT_MM (bounded, in case a platform reports a nonsense dpi)
	var floor_px := minf(MIN_TEXT_MM / mm_per_px() * minf(1.0, u), base * u * 3.5)
	px = maxf(px, floor_px)
	# boosted sizes round up so they reach their physical target; design sizes stay exact
	return int(ceilf(px - 0.001)) if a > 1.0001 or px > base * u + 0.5 else int(roundf(px))


## Width multiplier for boxes that hold text (grows half as fast as the text; text can still wrap).
static func wscale() -> float:
	return 1.0 + (float(size(28)) / 28.0 - 1.0) * 0.5


## Canvas px for a physical size on this screen.
static func px_for_mm(mm: float) -> float:
	return ceilf(mm / mm_per_px())


## A touch target: at least `design_px` and at least `mm` millimetres on the physical screen.
static func target(design_px: float, mm: float = TOUCH_MM) -> float:
	return maxf(design_px, px_for_mm(mm))


## Safe-area insets in canvas px: x=left y=top z=right w=bottom.
static func safe_margins() -> Vector4:
	var m := metrics()
	var c: Vector2 = m["canvas"]
	var s: Rect2 = m["safe"]
	return Vector4(maxf(0.0, s.position.x), maxf(0.0, s.position.y), maxf(0.0, c.x - s.end.x), maxf(0.0, c.y - s.end.y))


## The usable canvas rect (inside the safe area, with MARGIN around it).
static func usable_rect(margin: float = MARGIN) -> Rect2:
	var m := metrics()
	return (m["safe"] as Rect2).grow(-margin)


## A panel width: the design width grown with the text, but never wider than the usable screen.
static func panel_width(design_w: float) -> float:
	return minf(design_w * wscale(), usable_rect().size.x)


## HUD geometry shared by the HUD and the layout test.
const HUD_PAD := 16.0
const HUD_BACK_PX := 104.0
const HUD_BTN_PX := 92.0
const HUD_TITLE_PX := 26 # the view title's design size (display small caps)
const HUD_SLOT_PX := 112.0
const HUD_COL_GAP := 8.0 # between the inventory slots and their vertical rule
const HUD_RULE_W := 14.0
const HUD_TEXT_W := 1440.0


## Side of the square 3D item viewer in the inspect view: up to 880 px, never taller than the usable screen,
## and a smaller share of the width when the text is large (the description column needs the room).
static func inspect_viewer_side() -> float:
	var u := usable_rect(40.0)
	var share := clampf(0.45 / wscale(), 0.28, 0.45)
	return minf(880.0, minf(u.size.y, u.size.x * share))


## Width of the inventory column on the left (a slot, the gap and the vertical rule).
static func hud_column_width() -> float:
	return target(HUD_SLOT_PX, SLOT_MM) + HUD_COL_GAP + HUD_RULE_W


## Width available to the HUD's message and prompt banners at the bottom: centred, clear of the inventory column
## on the left and the pause button on the right (symmetric, so the banners stay centred on the screen).
static func hud_text_width() -> float:
	var canvas: Vector2 = metrics()["canvas"]
	var safe := safe_margins()
	var side := maxf(safe.x, safe.z)
	var obstacle := maxf(hud_column_width(), target(HUD_BTN_PX))
	var bottom_w := canvas.x - 2.0 * (side + HUD_PAD + obstacle + 20.0)
	return minf(bottom_w, HUD_TEXT_W * wscale())


# ====================================================================== fonts
static func ui_font(weight: int = 500) -> Font:
	var key := "ui%d" % weight
	if not _cache.has(key):
		var fv := FontVariation.new()
		fv.base_font = load(FONT_UI)
		fv.variation_opentype = {"wght": weight}
		_cache[key] = fv
	return _cache[key]


static func display_font(bold: bool = false) -> Font:
	var key := "disp%d" % int(bold)
	if not _cache.has(key):
		var f: FontFile = load(FONT_DISPLAY_BOLD if bold else FONT_DISPLAY)
		var fv := FontVariation.new()
		fv.base_font = f
		fv.fallbacks = [load(FONT_UI)]
		_cache[key] = fv
	return _cache[key]


## The display serif in true small capitals (the font's `smcp` feature, which covers Latin and Cyrillic), with a
## little letter spacing: section headers, banner titles and button text.
static func caps_font(bold: bool = true, spacing: int = 1) -> Font:
	var key := "caps%d_%d" % [int(bold), spacing]
	if not _cache.has(key):
		var fv := FontVariation.new()
		fv.base_font = display_font(bold)
		fv.opentype_features = {TextServerManager.get_primary_interface().name_to_tag("smcp"): 1}
		fv.spacing_glyph = spacing
		fv.fallbacks = [load(FONT_UI)]
		_cache[key] = fv
	return _cache[key]


static func hand_font() -> Font:
	if not _cache.has("hand"):
		var fv := FontVariation.new()
		fv.base_font = load(FONT_HAND)
		fv.variation_opentype = {"wght": 500}
		fv.fallbacks = [load(FONT_UI)] # Caveat lacks ʻ (U+02BB) — Noto Sans covers it
		_cache["hand"] = fv
	return _cache["hand"]


# ====================================================================== styles
## A dark panel with a hairline gold frame and a soft shadow (dialogs, the settings panel).
static func panel_box(alpha: float = 0.94, radius: int = 6, border: float = 1.0) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(PANEL_DARK, alpha)
	sb.border_color = Color(BRASS, 0.6)
	sb.set_border_width_all(maxi(1, int(border)))
	sb.set_corner_radius_all(radius)
	sb.shadow_color = Color(0, 0, 0, 0.5)
	sb.shadow_size = 22
	sb.set_content_margin_all(24)
	return sb


## A hairline-only frame (no fill), drawn a few px inside a panel's edge for a double rule.
static func inner_frame(alpha: float = 0.22, radius: int = 3) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.draw_center = false
	sb.border_color = Color(BRASS, alpha)
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(radius)
	return sb


## A flat button drawn as text only (links, secondary actions): brass text, no box.
static func text_button(text: String, color: Color = BRASS_HI) -> Button:
	var b := button(text, 0)
	b.flat = true
	var sb := StyleBoxEmpty.new()
	sb.content_margin_left = 18
	sb.content_margin_right = 18
	for s in ["normal", "hover", "pressed", "hover_pressed", "disabled", "focus"]:
		b.add_theme_stylebox_override(s, sb)
	b.add_theme_color_override("font_color", color)
	b.add_theme_color_override("font_hover_color", CREAM)
	b.add_theme_color_override("font_pressed_color", CREAM)
	b.add_theme_color_override("font_hover_pressed_color", CREAM)
	return b


## Dark plate behind HUD captions/messages: keeps ≥ 4.5:1 contrast for CREAM text even over a white 3D frame.
## UIBanner draws its own band; it takes its horizontal padding from these margins (so the layout test and the
## banner agree on the text width).
static func caption_plate() -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.02, 0.022, 0.028, 0.8)
	sb.set_corner_radius_all(4)
	sb.content_margin_left = 32
	sb.content_margin_right = 32
	sb.content_margin_top = 8
	sb.content_margin_bottom = 8
	return sb


## A round grabber texture for sliders: a cream disc with a thin brass rim, sized for thumbs.
static func _grabber(d: int, col: Color, rim_col: Color = BRASS) -> Texture2D:
	var key := "grab%d_%s_%s" % [d, col.to_html(), rim_col.to_html()]
	if _cache.has(key):
		return _cache[key]
	var img := Image.create(d, d, false, Image.FORMAT_RGBA8)
	var c := (d - 1) * 0.5
	var r := d * 0.5 - 1.0
	var rim_w := maxf(1.5, d * 0.08)
	for y in d:
		for x in d:
			var dist := Vector2(x - c, y - c).length()
			var a := clampf(r - dist + 0.5, 0.0, 1.0)
			var rim := clampf(dist - (r - rim_w) + 0.5, 0.0, 1.0)
			img.set_pixel(x, y, Color(col.lerp(rim_col, rim), a))
	var tex := ImageTexture.create_from_image(img)
	_cache[key] = tex
	return tex


static func build() -> Theme:
	var t := Theme.new()
	t.default_font = ui_font(500)
	t.default_font_size = size(26)
	# buttons: display serif in small caps on a dark field with a hairline gold frame; pressed = a soft brass fill
	var btn := StyleBoxFlat.new()
	btn.bg_color = Color(0.05, 0.052, 0.062, 0.8)
	btn.border_color = Color(BRASS, 0.62)
	btn.set_border_width_all(1)
	btn.set_corner_radius_all(4)
	btn.content_margin_left = 26
	btn.content_margin_right = 26
	btn.content_margin_top = 8
	btn.content_margin_bottom = 8
	var hov := btn.duplicate() as StyleBoxFlat
	hov.border_color = BRASS_HI
	hov.bg_color = Color(0.10, 0.09, 0.075, 0.88)
	var prs := btn.duplicate() as StyleBoxFlat
	prs.bg_color = Color(BRASS, 0.3)
	prs.border_color = BRASS_HI
	var dis := btn.duplicate() as StyleBoxFlat
	dis.border_color = Color(MUTED, 0.3)
	dis.bg_color = Color(0.05, 0.05, 0.06, 0.55)
	t.set_stylebox("normal", "Button", btn)
	t.set_stylebox("hover", "Button", hov)
	t.set_stylebox("pressed", "Button", prs)
	t.set_stylebox("hover_pressed", "Button", prs)
	t.set_stylebox("disabled", "Button", dis)
	t.set_stylebox("focus", "Button", StyleBoxEmpty.new())
	t.set_color("font_color", "Button", CREAM)
	t.set_color("font_hover_color", "Button", BRASS_HI)
	t.set_color("font_pressed_color", "Button", BRASS_HI)
	t.set_color("font_hover_pressed_color", "Button", BRASS_HI)
	t.set_color("font_disabled_color", "Button", MUTED)
	t.set_font("font", "Button", caps_font(true))
	t.set_font_size("font_size", "Button", size(BUTTON_PX))
	t.set_color("font_color", "Label", CREAM)
	t.set_stylebox("panel", "PanelContainer", panel_box())
	t.set_stylebox("panel", "Panel", panel_box())
	# sliders: a thin track with a gold fill and a thumb-sized grabber (the whole row is the touch target)
	var track := int(round(2 + 1 * auto_scale()))
	var slider_bg := StyleBoxFlat.new()
	slider_bg.bg_color = Color(MUTED, 0.3)
	slider_bg.set_corner_radius_all(track)
	slider_bg.content_margin_top = track
	slider_bg.content_margin_bottom = track
	var slider_fill := slider_bg.duplicate() as StyleBoxFlat
	slider_fill.bg_color = BRASS
	t.set_stylebox("slider", "HSlider", slider_bg)
	t.set_stylebox("grabber_area", "HSlider", slider_fill)
	t.set_stylebox("grabber_area_highlight", "HSlider", slider_fill)
	var gd := int(round(maxf(24.0, px_for_mm(3.6))))
	t.set_icon("grabber", "HSlider", _grabber(gd, CREAM))
	t.set_icon("grabber_highlight", "HSlider", _grabber(gd, BRASS_HI, BRASS_HI))
	t.set_icon("grabber_disabled", "HSlider", _grabber(gd, MUTED, MUTED))
	# scroll bars: visible enough to say "there is more", thin enough not to steal space
	var sw := int(round(6 * auto_scale()))
	var bar := StyleBoxFlat.new()
	bar.bg_color = Color(MUTED, 0.18)
	bar.set_corner_radius_all(sw)
	bar.content_margin_left = sw
	bar.content_margin_right = 0
	var grab := bar.duplicate() as StyleBoxFlat
	grab.bg_color = Color(BRASS, 0.75)
	t.set_stylebox("scroll", "VScrollBar", bar)
	t.set_stylebox("grabber", "VScrollBar", grab)
	t.set_stylebox("grabber_highlight", "VScrollBar", grab)
	t.set_stylebox("grabber_pressed", "VScrollBar", grab)
	t.set_constant("h_separation", "HFlowContainer", 16)
	t.set_constant("v_separation", "HFlowContainer", 14)
	return t


# ====================================================================== widgets
## Every helper tags its node with the design size, so rescale() can re-apply a changed text size live.
static func title(text: String, sz: int = 56, bold: bool = true) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", display_font(bold))
	l.set_meta("ui_font_size", sz)
	l.add_theme_font_size_override("font_size", size(sz))
	l.add_theme_color_override("font_color", BRASS_HI)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


static func label(text: String, sz: int = 26, color: Color = CREAM) -> Label:
	var l := Label.new()
	l.text = text
	l.set_meta("ui_font_size", sz)
	l.add_theme_font_size_override("font_size", size(sz))
	l.add_theme_color_override("font_color", color)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


static func button(text: String, min_w: int = 320) -> Button:
	var b := Button.new()
	b.text = text
	b.set_meta("ui_min_w", min_w)
	b.custom_minimum_size = Vector2(round(min_w * wscale()), target(78))
	b.focus_mode = Control.FOCUS_NONE
	b.pressed.connect(func() -> void: AudioManager.ui("ui_tap"))
	return b


## A row of buttons that wraps onto a second line instead of running off a narrow screen.
static func button_row(sep: int = 16) -> HFlowContainer:
	var h := HFlowContainer.new()
	h.alignment = FlowContainer.ALIGNMENT_CENTER
	h.add_theme_constant_override("h_separation", sep)
	h.add_theme_constant_override("v_separation", 14)
	return h


## Re-applies the text size and button widths below `root` (live preview of Settings → Text size).
static func rescale(root: Node) -> void:
	if root is Control:
		var c := root as Control
		if c.has_meta("ui_font_size"):
			c.add_theme_font_size_override("font_size", size(int(c.get_meta("ui_font_size"))))
		if c.has_meta("ui_min_w"):
			c.custom_minimum_size = Vector2(round(int(c.get_meta("ui_min_w")) * wscale()), target(78))
	for ch in root.get_children():
		rescale(ch)


## Wraps `content` in a vertical ScrollContainer that is exactly as tall as the content until the panel it sits
## in would exceed `max_panel_h`; then it scrolls. (A plain ScrollContainer would collapse to zero height inside
## a CenterContainer, and a plain VBox would push buttons off a short screen.)
static func scroll_fit(content: Control, panel: Control, max_panel_h: float) -> ScrollContainer: # panel may be null
	var s := ScrollContainer.new()
	s.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	s.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	s.size_flags_horizontal = Control.SIZE_EXPAND_FILL # height = custom_minimum_size (fit below); no vertical expand
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	s.add_child(content)
	var fit := func() -> void:
		if not is_instance_valid(s) or (panel != null and not is_instance_valid(panel)):
			return
		var others := 0.0 if panel == null else panel.get_combined_minimum_size().y - s.get_combined_minimum_size().y
		var want := minf(content.get_combined_minimum_size().y, max_panel_h - others)
		if absf(s.custom_minimum_size.y - want) > 0.5:
			s.custom_minimum_size.y = maxf(want, 0.0)
	content.minimum_size_changed.connect(fit)
	content.resized.connect(fit)
	fit.call_deferred()
	return s


## A full-screen CenterContainer inside the safe area (plus MARGIN), added to `host`.
static func safe_center(host: Control, margin: float = MARGIN) -> CenterContainer:
	var safe := safe_margins()
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	center.offset_left = safe.x + margin
	center.offset_top = safe.y + margin
	center.offset_right = -(safe.z + margin)
	center.offset_bottom = -(safe.w + margin)
	host.add_child(center)
	return center


## A dialog panel centred in `host` inside the safe area: a scrolling body (with the optional title on top) and
## a fixed footer row for the buttons.
## -> {"panel": PanelContainer, "body": VBoxContainer, "footer": HFlowContainer, "root": CenterContainer}
static func dialog(host: Control, design_w: float, title_key: String = "", title_size: int = 50) -> Dictionary:
	var center := safe_center(host)
	var p := PanelContainer.new()
	p.custom_minimum_size = Vector2(panel_width(design_w), 0)
	center.add_child(p)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	p.add_child(v)
	var body := VBoxContainer.new()
	body.add_theme_constant_override("separation", 14)
	if title_key != "":
		var head := VBoxContainer.new() # title over a gold rule; scrolls with the body (a short screen gives the room to the content)
		head.add_theme_constant_override("separation", 2)
		head.add_child(title(title_key, title_size))
		head.add_child(UIOrnament.rule())
		body.add_child(head)
	var max_h := usable_rect().size.y
	v.add_child(scroll_fit(body, p, max_h))
	var footer := button_row()
	v.add_child(footer)
	return {"panel": p, "body": body, "footer": footer, "root": center}
