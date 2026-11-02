#!/usr/bin/env python3
"""Writes qa/playthrough_ch2_rec.gd: a copy of game/qa/playthrough_ch2.gd with a recorder layer (step label, tap dot,
markers file). The original is only read. usage: make_rec.py <playthrough_ch2.gd> <out.gd>"""
import sys, re
src = open(sys.argv[1], encoding="utf-8").read()

def sub(old, new, count=1):
    global src
    assert src.count(old) >= 1, old
    src = src.replace(old, new, count)

# 1. step(): label + marker
sub('''func step(label: String, ok: bool) -> void:
	_log(("✓ " if ok else "✗ ") + label)''', '''func step(label: String, ok: bool) -> void:
	_log(("✓ " if ok else "✗ ") + label)
	_rec_step(label, ok)''')
# 2. shot(): no PNG, a marker only
sub('''func shot(name: String) -> void:
	await _settle(0.3)''', '''func shot(name: String) -> void:
	await _settle(0.3)
	_mark("shot", name)
	return''')
# 3. tap(): dot
sub('''	_note_hud(sp, "%s/%s" % [model, part])
	room.call("_on_tap", sp)
	await _settle(0.4)''', '''	_note_hud(sp, "%s/%s" % [model, part])
	_tap_dot(sp)
	_mark("tap", "%s/%s" % [model, part])
	room.call("_on_tap", sp)
	await _settle(0.4)''')
sub('''	var sp := cam().unproject_position(o + at)
	_note_hud(sp, label)
	room.call("_on_tap", sp)''', '''	var sp := cam().unproject_position(o + at)
	_note_hud(sp, label)
	_tap_dot(sp)
	_mark("tap", label)
	room.call("_on_tap", sp)''')
# 4. ready: build the recorder layer before the run
sub('''	await _load_room()
	_log("scene load+build''', '''	_rec_setup()
	await _load_room()
	_log("scene load+build''')
sub('''func _finish() -> void:''', '''func _finish() -> void:
	_mark("end", "")''')
src += '''

# ====================================================================== recorder layer (promo/v1_1, not in the original)
var _rec_layer: CanvasLayer
var _rec_label: Label
var _rec_dots: Array = []
var _rec_last := "start"
var _rec_markers: FileAccess


func _rec_setup() -> void:
	_rec_markers = FileAccess.open(out_dir + "/markers.tsv", FileAccess.WRITE)
	_rec_layer = CanvasLayer.new()
	_rec_layer.layer = 200
	get_tree().root.add_child(_rec_layer)
	var panel := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0, 0, 0, 0.62)
	sb.set_content_margin_all(5)
	sb.corner_radius_top_right = 6
	panel.add_theme_stylebox_override("panel", sb)
	panel.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	panel.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_rec_label = Label.new()
	_rec_label.add_theme_font_size_override("font_size", 15)
	_rec_label.add_theme_color_override("font_color", Color(1, 1, 1))
	_rec_label.text = "start"
	panel.add_child(_rec_label)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_rec_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_rec_layer.add_child(panel)
	set_process(true)


func _mark(kind: String, text: String) -> void:
	if _rec_markers != null:
		_rec_markers.store_line("%d\\t%s\\t%s" % [Engine.get_process_frames(), kind, text])
		_rec_markers.flush()


func _rec_step(label: String, ok: bool) -> void:
	_mark("step", ("OK " if ok else "FAIL ") + label)
	_rec_last = label.get_slice(" ", 0)
	var short := label
	if short.length() > 62:
		short = short.substr(0, 62) + "..."
	_rec_label.text = "done: " + short


func _tap_dot(sp: Vector2) -> void:
	var d := ColorRect.new()
	d.color = Color(1, 0.85, 0.2, 0.75)
	var sz := 34.0 * float(get_viewport().get_visible_rect().size.x) / 1920.0 + 14.0
	d.size = Vector2(sz, sz)
	d.position = sp - d.size * 0.5
	d.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sh := StyleBoxFlat.new()
	sh.bg_color = Color(1, 0.85, 0.2, 0.7)
	sh.set_corner_radius_all(int(sz))
	var p := Panel.new()
	p.add_theme_stylebox_override("panel", sh)
	p.size = d.size
	p.position = d.position
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_rec_layer.add_child(p)
	_rec_dots.append([p, 0.0])
	d.free()
'''
# dots fade in _process (the original has no _process)
src += '''

func _process(delta: float) -> void:
	for i in range(_rec_dots.size() - 1, -1, -1):
		var e: Array = _rec_dots[i]
		e[1] += delta
		var p: Control = e[0]
		p.modulate.a = clampf(1.0 - float(e[1]) / 0.5, 0.0, 1.0)
		if float(e[1]) >= 0.5:
			p.queue_free()
			_rec_dots.remove_at(i)
	if room != null and is_instance_valid(room) and _rec_label != null:
		var cs := cam()
		if cs != null:
			var st := _rec_label.text
			var d := st.find("   [")
			if d >= 0:
				st = st.substr(0, d)
			_rec_label.text = st + "   [" + str(logic.state.get("room", "")) + " / " + cs.current() + "]"
'''
open(sys.argv[2], "w", encoding="utf-8").write(src)
