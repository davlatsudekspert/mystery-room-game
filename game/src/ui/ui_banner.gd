class_name UIBanner
extends Control
## A centred HUD banner in the main menu's language: a small-caps serif title between two gold flourishes over a
## thin gold rule, a subtitle line below, on a soft dark translucent band whose ends fade out. Any part may be
## empty: a title alone names a room or an object, a subtitle alone carries a caption, a message or a prompt, and
## with an icon on the left it announces a found item. hud.gd sets the texts, calls fit(max_w) and places the
## banner by its top-left corner (no anchors). Everything is drawn in code, so it is crisp at any dpi.

const PAD_Y := 10.0
const FLOURISH := 56.0 # design px of rule on each side of the title
const BAND := Color(0.02, 0.022, 0.028)

var title_label: Label
var subtitle_label: Label
var icon: TextureRect
var band_alpha := 0.8 # over a white 3D frame: cream text 7:1, muted 4.9:1, brass 7:1
var _title_rect := Rect2()
var _fl := 0.0 # flourish length actually drawn (0 = none)
var _rule_y := -1.0 # the rule between title and subtitle (-1 = none)


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE


## Creates the labels: the title in display small caps (`title_sz`), the subtitle in the body font (`sub_sz`).
func setup(title_sz: int, sub_sz: int, sub_color: Color = UITheme.CREAM) -> void:
	icon = TextureRect.new()
	icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	icon.visible = false
	add_child(icon)
	title_label = UITheme.label("", title_sz, UITheme.BRASS_HI)
	title_label.add_theme_font_override("font", UITheme.caps_font(true, 2))
	title_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.7))
	title_label.add_theme_constant_override("outline_size", 3)
	title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	title_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_label.visible = false
	add_child(title_label)
	subtitle_label = UITheme.label("", sub_sz, sub_color)
	subtitle_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.75))
	subtitle_label.add_theme_constant_override("outline_size", 4)
	subtitle_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	subtitle_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	subtitle_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	subtitle_label.visible = false
	add_child(subtitle_label)


func set_title(t: String) -> void:
	title_label.text = t


func set_subtitle(t: String) -> void:
	subtitle_label.text = t


func set_icon(tex: Texture2D) -> void:
	icon.texture = tex


func _text_of(l: Label) -> String:
	return l.atr(l.text).strip_edges()


func has_text() -> bool:
	return _text_of(title_label) != "" or _text_of(subtitle_label) != ""


## Lays the banner out for its current texts, never wider than `max_w`: one-line texts hug their width, longer
## ones wrap at `max_w`. Sets `size` (and the minimum size) and places the labels and the icon.
func fit(max_w: float) -> void:
	var k := UIOrnament.scale_k()
	var pad_x := float(UITheme.caption_plate().content_margin_left)
	var pad_y := PAD_Y * k
	var ttext := _text_of(title_label)
	var stext := _text_of(subtitle_label)
	title_label.visible = ttext != ""
	subtitle_label.visible = stext != ""
	var has_icon := icon.texture != null
	icon.visible = has_icon
	var icon_px := roundf(2.6 * UITheme.size(28)) if has_icon else 0.0
	var icon_gap := 20.0 if has_icon else 0.0
	var inner_max := maxf(80.0, max_w - 2.0 * pad_x - icon_px - icon_gap)
	# the title: one line between flourishes when it fits, wrapped (without flourishes) otherwise
	var tw := 0.0
	var th := 0.0
	_fl = 0.0
	if title_label.visible:
		var f := title_label.get_theme_font("font")
		var fs := title_label.get_theme_font_size("font_size")
		var w := f.get_string_size(ttext, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x + 4.0
		if w <= inner_max:
			title_label.autowrap_mode = TextServer.AUTOWRAP_OFF
			tw = w
			th = f.get_height(fs)
			_fl = clampf((inner_max - tw) * 0.5 - 18.0 * k, 0.0, FLOURISH * k)
			if _fl < 14.0 * k:
				_fl = 0.0
		else:
			title_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			tw = inner_max
			th = f.get_multiline_string_size(ttext, HORIZONTAL_ALIGNMENT_CENTER, inner_max, fs).y
	var sw := 0.0
	var sh := 0.0
	if subtitle_label.visible:
		var f := subtitle_label.get_theme_font("font")
		var fs := subtitle_label.get_theme_font_size("font_size")
		var w := f.get_string_size(stext, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x + 4.0
		if w <= inner_max:
			subtitle_label.autowrap_mode = TextServer.AUTOWRAP_OFF
			sw = w
			sh = f.get_height(fs)
		else:
			subtitle_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			sw = inner_max
			sh = f.get_multiline_string_size(stext, HORIZONTAL_ALIGNMENT_CENTER, inner_max, fs).y
	var title_w := tw + (2.0 * (_fl + 18.0 * k) if _fl > 0.0 else 0.0)
	var text_w := maxf(title_w, sw)
	var rule_gap := 10.0 * k if (title_label.visible and subtitle_label.visible) else 0.0
	var block_h := th + sh + (rule_gap * 2.0 + 2.0 if rule_gap > 0.0 else 0.0)
	if title_label.visible and not subtitle_label.visible:
		block_h += 4.0 * k
	var text_x0 := pad_x + icon_px + icon_gap
	var w_total := roundf(text_x0 + text_w + pad_x)
	var h_total := roundf(maxf(block_h, icon_px) + 2.0 * pad_y)
	custom_minimum_size = Vector2(w_total, h_total)
	size = Vector2(w_total, h_total)
	var y := roundf((h_total - block_h) * 0.5)
	var cx := text_x0 + text_w * 0.5
	_title_rect = Rect2()
	if title_label.visible:
		title_label.position = Vector2(roundf(cx - tw * 0.5), y)
		title_label.size = Vector2(ceilf(tw), ceilf(th) + 2.0)
		_title_rect = Rect2(title_label.position, title_label.size)
		y += th
	_rule_y = -1.0
	if rule_gap > 0.0:
		_rule_y = roundf(y + rule_gap)
		y += rule_gap * 2.0 + 2.0
	if subtitle_label.visible:
		subtitle_label.position = Vector2(roundf(cx - sw * 0.5), y)
		subtitle_label.size = Vector2(ceilf(sw), ceilf(sh) + 2.0)
	if has_icon:
		icon.position = Vector2(pad_x, roundf((h_total - icon_px) * 0.5))
		icon.size = Vector2(icon_px, icon_px)
	queue_redraw()


func _grad(r: Rect2, from: Color, to: Color) -> void:
	if r.size.x <= 0.0 or r.size.y <= 0.0:
		return
	draw_polygon(PackedVector2Array([r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y)]),
		PackedColorArray([from, to, to, from]))


func _diamond(c: Vector2, dx: float, dy: float, col: Color) -> void:
	draw_colored_polygon(PackedVector2Array([c + Vector2(-dx, 0), c + Vector2(0, -dy), c + Vector2(dx, 0), c + Vector2(0, dy)]), col)


func _draw() -> void:
	var k := UIOrnament.scale_k()
	var gold := UITheme.BRASS
	# the band: solid in the middle, fading out toward both ends
	var fade := minf(80.0 * k, size.x * 0.16)
	var band := Color(BAND, band_alpha)
	var clear := Color(BAND, 0.0)
	_grad(Rect2(0, 0, fade, size.y), clear, band)
	draw_rect(Rect2(fade, 0, size.x - 2.0 * fade, size.y), band)
	_grad(Rect2(size.x - fade, 0, fade, size.y), band, clear)
	# hairlines along the top and bottom edges, fading with the band
	var half := size.x * 0.5
	for yy: float in [0.5, size.y - 1.5]:
		_grad(Rect2(fade * 0.5, yy, half - fade * 0.5, 1.0), Color(gold, 0.0), Color(gold, 0.42))
		_grad(Rect2(half, yy, half - fade * 0.5, 1.0), Color(gold, 0.42), Color(gold, 0.0))
	var th := maxf(1.0, roundf(1.4 * k))
	if title_label.visible and _fl > 0.0:
		# flourishes: a small diamond beside the title, then a rule running outward and fading away
		var ty := roundf(_title_rect.get_center().y)
		var dx := 5.0 * k
		var dy := 3.6 * k
		var lx := _title_rect.position.x - 12.0 * k
		var rx := _title_rect.end.x + 12.0 * k
		var hi := Color(UITheme.BRASS_HI, 0.95)
		_diamond(Vector2(lx - dx, ty), dx, dy, hi)
		_diamond(Vector2(rx + dx, ty), dx, dy, hi)
		var l_end := lx - 2.0 * dx - 4.0 * k
		var r_start := rx + 2.0 * dx + 4.0 * k
		_grad(Rect2(l_end - _fl, ty - th * 0.5, _fl, th), Color(gold, 0.0), Color(gold, 0.9))
		_grad(Rect2(r_start, ty - th * 0.5, _fl, th), Color(gold, 0.9), Color(gold, 0.0))
	if _rule_y >= 0.0:
		# the rule between the title and the subtitle: solid under the words, fading at both ends
		var rw := _title_rect.size.x + 2.0 * maxf(_fl * 0.8, 24.0 * k)
		var cx := _title_rect.get_center().x
		_grad(Rect2(cx - rw * 0.5, _rule_y, rw * 0.5, th), Color(gold, 0.0), Color(gold, 0.85))
		_grad(Rect2(cx, _rule_y, rw * 0.5, th), Color(gold, 0.85), Color(gold, 0.0))
