class_name ArchiveTeaser
extends Node
## Chapter 2's cliffhanger and the hand-off to Chapter 3 (docs/ENGAGEMENT.md). After the key is chosen:
##   1. the key leaves its hook, the other is clamped (ArchiveVisuals), and a lift motor wakes under the vault floor:
##      the room shakes, the bulb stutters, dust falls;
##   2. a glimpse down the old freight-lift shaft under the archive: its lamps wake floor by floor, the cage climbs
##      with its work lamp, and the light of Level −2 breathes at the bottom while the transformer halls hum;
##   3. on black, "Somewhere below, a recorder clicks on", Leyla's 1998 voice with captions, and under the hiss a
##      second voice that should not be there;
##   4. the Chapter 3 card: the wing the chosen key opens, and one calm hand-off. When Chapter 3 is released and the
##      store is open it offers "Continue the story" (the store agent's PurchasePanel.open) next to "Not now"; when
##      the chapter is not out yet, or payments are off, it says the chapters are on their way. Either way the HUD's
##      chapter-complete card follows.
## Every taps-to-skip wait is short, the card never times out, and Back is swallowed (the room is _ending).
## The shaft is built from primitives and the shared materials only when the sequence starts, and freed after it.

signal finished

const SHAFT_X := 1.5
const SHAFT_Z := -4.6
const SHAFT_HALF := 1.1
const WALL_T := 0.16
const SHAFT_TOP := -0.3
const SHAFT_BOTTOM := -32.0
const SEGMENT_M := 3.95
## Shaft lamps, top to bottom: [y, wall] (wall 0 north, 1 east, 2 south, 3 west); every other one carries a light.
const LAMPS := [[-2.4, 0], [-6.2, 1], [-10.0, 3], [-13.8, 0], [-17.6, 1], [-21.4, 3], [-25.2, 0], [-29.0, 1]]
const CAGE_FROM := -27.5
const CAGE_TO := -16.0
const WARM := Color("ffc58a")
const DEEP := Color("8fe6ff")
## The shaft view (archive_room.gd adds it): from the landing sill, nearly straight down.
const VIEW_POS := Vector3(1.5, -0.45, -3.85)
const VIEW_TARGET := Vector3(1.58, -31.0, -5.0)

var room: Node3D
var running := false
var _shaft: Node3D
var _lamps: Array = [] # [bulb MeshInstance3D, OmniLight3D or null]
var _cage: Node3D
var _cables: Array[MeshInstance3D] = []
var _glow_light: OmniLight3D
var _glow_mat: StandardMaterial3D
var _cage_light: OmniLight3D
var _layer: CanvasLayer
var _root: Control
var _black: ColorRect
var _skip := false
var _breath_t := 0.0


func _init(r: Node3D) -> void:
	room = r
	name = "ArchiveTeaser"


func _hud() -> Node:
	return room.get("hud")


func _cam() -> RoomCamera:
	return room.get("cam")


# ====================================================================== the sequence
## The whole cliffhanger, from the key leaving its hook to the Chapter 3 card. `choice` is "strand_key" or
## "leyla_key". Emits `finished` when the player leaves the card (the room then shows the HUD's chapter card).
func play(choice: String) -> void:
	running = true
	var hud := _hud()
	hud.call("set_busy", true)
	# 1. the key comes away; a beat of silence, then the floor answers
	await _wait(1.3, false)
	AudioManager.sfx("vault_door_open", -3.0, 0.55)
	AudioManager.sfx("compressor_start", -4.0, 0.5)
	AudioManager.haptic(220)
	hud.call("caption", tr("cap2.rumble"), 4.0)
	_shake(1.9, 0.012)
	_dust_fall()
	_bulb_stutter()
	await _wait(2.6, false)
	# 2. the shaft
	_overlay()
	await _fade_black(1.0, 0.35)
	_build_shaft()
	var env: Environment = room.get("env")
	var fog := [env.fog_density, env.fog_light_color] if env else []
	if env:
		env.fog_density = 0.03
		env.fog_light_color = Color("0c1a20")
	_cam().go("shaft", true)
	AudioManager.ambience("amb_archive", false, 0.0, 1.5)
	AudioManager.ambience("amb_power_hum", true, -3.0, 3.0)
	_set_cage(CAGE_FROM)
	await _fade_black(0.0, 0.9)
	hud.call("caption", tr("cap2.shaft_lamps"), 4.0)
	_push_down(11.0)
	for i in LAMPS.size():
		if _skip:
			break
		_light_lamp(i)
		AudioManager.sfx("relay_click", -4.0 - 1.6 * i, 1.08 - 0.05 * i)
		await _wait(0.42, true)
	_wake_bottom()
	AudioManager.sfx("vault_bolts", -10.0, 0.45)
	_climb(CAGE_TO, 9.0)
	await _wait(1.2, true)
	hud.call("caption", tr("cap2.shaft_hum"), 4.5)
	await _wait(4.6, true)
	# 3. the recorder, on black
	hud.call("caption", "", 0.1)
	await _fade_black(1.0, 1.1 if not _skip else 0.3)
	_skip = false
	_cam().go("vault_inside", true)
	_free_shaft()
	if env and not fog.is_empty():
		env.fog_density = fog[0]
		env.fog_light_color = fog[1]
	await _recorder()
	# 4. the Chapter 3 card
	show_card(choice, false)


## The recorder, on black: the click, Leyla's 1998 voice with captions over a tape-head trace, then a second voice
## under the hiss.
func _recorder() -> void:
	var col := _card_column()
	AudioManager.sfx("deck_play", -2.0, 0.9)
	AudioManager.sfx("tape_hiss", -10.0)
	var head := _text(tr("epi2.recorder"), 40, UITheme.CREAM, true)
	col.add_child(head)
	await _fade_in(head, 1.0)
	await _wait(3.0, true)
	await _fade_out(head, 0.5)
	head.queue_free()
	var who := UITheme.label(tr("tease2.voice_who"), 22, UITheme.MUTED)
	who.add_theme_font_override("font", UITheme.caps_font(false, 1))
	who.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	who.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	col.add_child(who)
	var lines := VBoxContainer.new() # the spoken line(s); a fixed height so the trace below never jumps
	lines.add_theme_constant_override("separation", 14)
	lines.custom_minimum_size = Vector2(0, UITheme.size(34) * 3.2)
	lines.alignment = BoxContainer.ALIGNMENT_CENTER
	lines.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_child(lines)
	var wave := TapeWave.new()
	wave.custom_minimum_size = Vector2(minf(560.0 * UITheme.wscale(), _canvas().x * 0.5), 64.0 * UITheme.wscale())
	wave.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	wave.level = 0.12
	col.add_child(wave)
	await _fade_in(who, 0.6)
	for key in ["tease2.voice_1", "tease2.voice_2", "tease2.voice_3"]:
		_skip = false
		AudioManager.sfx("tape_voice", -4.0, randf_range(0.97, 1.02))
		var line := _text(tr(key), 34, UITheme.CREAM, false)
		line.add_theme_font_override("font", UITheme.display_font(false))
		lines.add_child(line)
		wave.level = 1.0
		await _fade_in(line, 0.5)
		await _wait(2.6 + 0.03 * tr(key).length(), true)
		wave.level = 0.12
		await _fade_out(line, 0.4)
		line.queue_free()
	await _fade_out(who, 0.4)
	# the second voice: Strand, kept in the light, noticing someone beside her
	_skip = false
	AudioManager.sfx("tape_garble", -18.0, 0.62)
	AudioManager.sfx("reveal", -6.0, 0.5)
	var cap := _text(tr("tease2.second_cap"), 24, UITheme.MUTED, false)
	lines.add_child(cap)
	await _fade_in(cap, 0.6)
	await _wait(1.6, true)
	var voice := _text(tr("tease2.second_voice"), 40, Color("cfeef7"), false)
	voice.add_theme_font_override("font", UITheme.display_font(false))
	lines.add_child(voice)
	wave.color = Color("9fe3f2")
	wave.level = 0.55
	AudioManager.haptic(60)
	await _fade_in(voice, 0.9)
	await _wait(3.4, true)
	wave.level = 0.0
	AudioManager.sfx("deck_eject", -6.0, 0.7) # the tape runs out
	var tw := room.create_tween().set_parallel(true)
	tw.tween_property(cap, "modulate:a", 0.0, 0.8)
	tw.tween_property(voice, "modulate:a", 0.0, 0.8)
	tw.tween_property(wave, "modulate:a", 0.0, 0.8)
	await tw.finished
	col.get_parent().queue_free()


## A tape-head trace under the captions: it moves while a voice speaks and lies almost flat in the hiss.
class TapeWave extends Control:
	var level := 0.0
	var color := Color("ede3cf")
	var _amp := 0.0
	var _t := 0.0

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _process(delta: float) -> void:
		_t += delta
		_amp = lerpf(_amp, level, clampf(delta * 6.0, 0.0, 1.0))
		queue_redraw()

	func _draw() -> void:
		var n := 72
		var pts := PackedVector2Array()
		for i in n + 1:
			var e := sin(PI * float(i) / n) # tapers to nothing at both ends
			var v := 0.55 * sin(i * 0.9 + _t * 13.0) + 0.3 * sin(i * 2.3 - _t * 21.0) + 0.15 * sin(i * 5.1 + _t * 34.0)
			pts.append(Vector2(size.x * i / n, size.y * (0.5 + 0.45 * _amp * e * v)))
		draw_polyline(pts, Color(color, 0.8), 2.0, true)
		draw_line(Vector2(0, size.y * 0.5), Vector2(size.x, size.y * 0.5), Color(color, 0.12), 1.0)


# ====================================================================== the Chapter 3 card
## The hand-off. `instant` = no fade (a save loaded after the chapter ended opens straight onto it).
## `store_state` forces "soon" / "unlock" / "play" for QA screenshots; "" reads Premium.
func show_card(choice: String, instant: bool, store_state: String = "") -> void:
	running = true
	_hud().call("set_busy", true)
	_overlay()
	if instant:
		_black.color.a = 0.94
	elif _black.color.a < 0.9:
		await _fade_black(0.94, 0.8)
	var col := _card_column()
	var state := store_state if store_state != "" else card_state()
	var label := UITheme.label(tr("chapter.label") % 3, 24, UITheme.MUTED)
	label.add_theme_font_override("font", UITheme.caps_font(false, 2))
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	col.add_child(label)
	var title := UITheme.title(tr("chapter.ch3.title"), 64)
	title.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	col.add_child(title)
	var rule := UIOrnament.rule()
	rule.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	rule.custom_minimum_size = Vector2(minf(560.0 * UITheme.wscale(), _canvas().x * 0.6), 22.0)
	col.add_child(rule)
	var tag := _text(tr("tease2.tag_leyla_key" if choice == "leyla_key" else "tease2.tag_strand_key"), 28, UITheme.CREAM, false)
	col.add_child(tag)
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, 18)
	col.add_child(gap)
	var line_key := {"soon": "tease2.coming_soon", "unlock": "tease2.unlock_line", "play": ""}[state] as String
	if line_key != "":
		var line := _text(tr(line_key), 24, UITheme.MUTED, false)
		col.add_child(line)
	var row := UITheme.button_row(24)
	col.add_child(row)
	if state == "unlock":
		var buy := UITheme.button("tease2.continue_story", 460)
		buy.pressed.connect(func() -> void:
			var pp := PurchasePanel.open(_root)
			pp.closed.connect(func() -> void:
				if Premium.can_play("ch3"):
					_leave())) # bought: the chapter card that follows offers Play
		row.add_child(buy)
		var later := UITheme.text_button("tease2.not_now", UITheme.MUTED)
		later.custom_minimum_size.y = UITheme.target(78)
		later.pressed.connect(_leave)
		row.add_child(later)
	else:
		var go := UITheme.button("ui.continue", 420)
		go.pressed.connect(_leave)
		row.add_child(go)
	for c: Node in col.get_children():
		if c is Control:
			(c as Control).modulate.a = 0.0 if not instant else 1.0
	if not instant:
		AudioManager.sfx("reveal", -8.0, 0.7)
		for c: Node in col.get_children():
			if c is Control:
				var tw := room.create_tween()
				tw.tween_property(c, "modulate:a", 1.0, 0.9)
				await _wait(0.28, false)


## What the card offers: "play" (Chapter 3 can be played: bought, or a tester build), "unlock" (released and the
## store can sell it), "soon" (not released yet, or no store: real payments off).
static func card_state() -> String:
	var ch3 := Chapters.get_chapter("ch3")
	if Premium.can_play("ch3"):
		return "play"
	if bool(ch3.get("released", false)) and Premium.store_open():
		return "unlock"
	return "soon"


func _leave() -> void:
	if _layer == null:
		return
	AudioManager.ui("ui_tap")
	var layer := _layer
	_layer = null
	var tw := room.create_tween()
	tw.tween_property(_root, "modulate:a", 0.0, 0.4)
	tw.tween_callback(layer.queue_free)
	running = false
	finished.emit()


## The card's Continue / Not now (QA presses it like a finger would).
func leave() -> void:
	_leave()


func card_open() -> bool:
	return _layer != null and is_instance_valid(_root)


# ====================================================================== overlay helpers
func _canvas() -> Vector2:
	return UITheme.metrics()["canvas"]


func _overlay() -> void:
	if _layer != null:
		return
	_layer = CanvasLayer.new()
	_layer.layer = 20 # above the HUD (its card follows once this closes)
	room.add_child(_layer)
	_root = Control.new()
	_root.theme = UITheme.build()
	_root.position = Vector2.ZERO
	_root.size = _canvas()
	_root.mouse_filter = Control.MOUSE_FILTER_STOP
	_layer.add_child(_root)
	_black = ColorRect.new()
	_black.color = Color(0.02, 0.025, 0.03, 0.0)
	_black.set_anchors_preset(Control.PRESET_FULL_RECT)
	_black.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_black)
	_root.gui_input.connect(func(ev: InputEvent) -> void:
		if (ev is InputEventScreenTouch and (ev as InputEventScreenTouch).pressed) or \
				(ev is InputEventMouseButton and (ev as InputEventMouseButton).pressed):
			_skip = true)


## A centred column inside the safe area for the black cards.
func _card_column() -> VBoxContainer:
	var safe := UITheme.safe_margins()
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	center.offset_left = safe.x + 120.0 * UITheme.wscale()
	center.offset_right = -(safe.z + 120.0 * UITheme.wscale())
	center.offset_top = safe.y + 40.0
	center.offset_bottom = -(safe.w + 40.0)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(center)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 18)
	col.custom_minimum_size = Vector2(minf(1300.0 * UITheme.wscale(), _canvas().x - safe.x - safe.z - 160.0), 0)
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	center.add_child(col)
	return col


func _text(t: String, sz: int, color: Color, title: bool) -> Label:
	var l := UITheme.title(t, sz, false) if title else UITheme.label(t, sz, color)
	l.add_theme_color_override("font_color", color)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _fade_black(a: float, seconds: float) -> void:
	var tw := room.create_tween()
	tw.tween_property(_black, "color:a", a, seconds)
	await tw.finished


func _fade_in(c: Control, seconds: float) -> void:
	c.modulate.a = 0.0
	var tw := room.create_tween()
	tw.tween_property(c, "modulate:a", 1.0, seconds)
	await tw.finished


func _fade_out(c: Control, seconds: float) -> void:
	var tw := room.create_tween()
	tw.tween_property(c, "modulate:a", 0.0, seconds)
	await tw.finished


## Waits `seconds`, or less once the player taps (when `skippable`).
func _wait(seconds: float, skippable: bool) -> void:
	var t := 0.0
	while t < seconds and not (skippable and _skip):
		await room.get_tree().process_frame
		t += room.get_process_delta_time()


# ====================================================================== the vault shakes
## A short handheld shake of the current close-up (its view position jitters and settles).
func _shake(seconds: float, amp: float) -> void:
	var cam := _cam()
	var id := cam.current()
	if not cam.views.has(id) or bool(Settings.get_value("reduce_motion")):
		return
	var base: Vector3 = cam.views[id]["pos"]
	var tw := room.create_tween()
	tw.tween_method(func(k: float) -> void:
		var a := amp * (1.0 - k) * (1.0 - k)
		cam.views[id]["pos"] = base + Vector3(randf_range(-a, a), randf_range(-a, a), randf_range(-a, a) * 0.5), 0.0, 1.0, seconds)
	tw.tween_callback(func() -> void: cam.views[id]["pos"] = base)


func _dust_fall() -> void:
	var p := DustMotes.create(Vector3(0.85, 0.05, 0.7), 140)
	p.one_shot = true
	p.explosiveness = 0.55
	p.lifetime = 3.2
	p.preprocess = 0.0
	var m := (p.process_material as ParticleProcessMaterial).duplicate() as ParticleProcessMaterial
	m.gravity = Vector3(0, -0.45, 0)
	p.process_material = m
	room.add_child(p)
	p.global_position = Vector3(SHAFT_X, 2.42, -4.45)
	p.emitting = true
	room.get_tree().create_timer(4.0).timeout.connect(p.queue_free)


func _bulb_stutter() -> void:
	var L: Dictionary = room.get("lights")
	var v: OmniLight3D = L.get("vault")
	if v == null:
		return
	var base := v.light_energy
	var tw := room.create_tween()
	for i in 5:
		tw.tween_property(v, "light_energy", base * 0.2, 0.05)
		tw.tween_property(v, "light_energy", base * (1.2 if i % 2 == 0 else 0.9), 0.07 + 0.03 * i)
	tw.tween_property(v, "light_energy", base, 0.3)


# ====================================================================== the shaft
func _mat(path: String) -> Material:
	return load("res://assets/materials/%s.tres" % path)


func _box(parent: Node3D, nm: String, size: Vector3, pos: Vector3, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	var am := ArrayMesh.new() # an ArrayMesh, so ModelUtil.merge_static can fold a storey into one draw call
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, b.get_mesh_arrays())
	mi.mesh = am
	mi.material_override = mat
	mi.position = pos
	mi.name = nm
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	return mi


func _cyl(parent: Node3D, nm: String, r_top: float, r_bottom: float, h: float, pos: Vector3, mat: Material, seg: int = 12) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var c := CylinderMesh.new()
	c.top_radius = r_top
	c.bottom_radius = r_bottom
	c.height = h
	c.radial_segments = seg
	c.rings = 1
	mi.mesh = c
	mi.material_override = mat
	mi.position = pos
	mi.name = nm
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	return mi


func _build_shaft() -> void:
	if _shaft != null:
		return
	_shaft = Node3D.new()
	_shaft.name = "teaser_shaft"
	room.add_child(_shaft)
	var concrete := (_mat("M_Concrete") as BaseMaterial3D).duplicate() as BaseMaterial3D
	concrete.uv1_triplanar = true
	concrete.uv1_scale = Vector3.ONE * 0.6
	var steel := _mat("M_Steel_Dark")
	var painted := _mat("M_Steel_Painted")
	var amber := _mat("M_Enamel_Amber")
	var h := SHAFT_HALF
	var t := WALL_T
	# the walls in storey-high pieces (each piece only meets the lamps near it), merged per storey
	var y := SHAFT_TOP
	var k := 0
	while y > SHAFT_BOTTOM + 0.01:
		var seg_h := minf(SEGMENT_M, y - SHAFT_BOTTOM)
		var cy := y - seg_h * 0.5
		var g := Node3D.new()
		g.name = "storey_%d" % k
		_shaft.add_child(g)
		_box(g, "s_n", Vector3(2 * h + 2 * t, seg_h, t), Vector3(SHAFT_X, cy, SHAFT_Z - h - t * 0.5), concrete)
		_box(g, "s_s", Vector3(2 * h + 2 * t, seg_h, t), Vector3(SHAFT_X, cy, SHAFT_Z + h + t * 0.5), concrete)
		_box(g, "s_w", Vector3(t, seg_h, 2 * h), Vector3(SHAFT_X - h - t * 0.5, cy, SHAFT_Z), concrete)
		_box(g, "s_e", Vector3(t, seg_h, 2 * h), Vector3(SHAFT_X + h + t * 0.5, cy, SHAFT_Z), concrete)
		# a steel landing band at every storey: depth you can count
		var by := y - 0.35
		_box(g, "s_band_n", Vector3(2 * h, 0.12, 0.05), Vector3(SHAFT_X, by, SHAFT_Z - h + 0.025), painted)
		_box(g, "s_band_s", Vector3(2 * h, 0.12, 0.05), Vector3(SHAFT_X, by, SHAFT_Z + h - 0.025), painted)
		_box(g, "s_band_w", Vector3(0.05, 0.12, 2 * h), Vector3(SHAFT_X - h + 0.025, by, SHAFT_Z), painted)
		_box(g, "s_band_e", Vector3(0.05, 0.12, 2 * h), Vector3(SHAFT_X + h - 0.025, by, SHAFT_Z), painted)
		ModelUtil.merge_static(g, "s_")
		y -= seg_h
		k += 1
	# the landing sill in the foreground: steel with an amber edge
	_box(_shaft, "sill", Vector3(2 * h, 0.06, 0.32), Vector3(SHAFT_X, SHAFT_TOP - 0.03, SHAFT_Z + h - 0.16), steel)
	_box(_shaft, "sill_edge", Vector3(2 * h, 0.065, 0.05), Vector3(SHAFT_X, SHAFT_TOP - 0.028, SHAFT_Z + h - 0.345), amber)
	# guide rails on the east and west walls
	var rail_h := SHAFT_TOP - SHAFT_BOTTOM
	for sx in [-1.0, 1.0]:
		_box(_shaft, "rail", Vector3(0.05, rail_h, 0.1), Vector3(SHAFT_X + sx * (h - 0.06), SHAFT_TOP - rail_h * 0.5, SHAFT_Z), steel)
	# lamps: a caged bulb under a small shade on a backplate
	for i in LAMPS.size():
		var ly: float = LAMPS[i][0]
		var wall: int = LAMPS[i][1]
		var n: Vector3 = [Vector3(0, 0, 1), Vector3(-1, 0, 0), Vector3(0, 0, -1), Vector3(1, 0, 0)][wall]
		var at := Vector3(SHAFT_X, ly, SHAFT_Z) - n * (h - 0.11)
		at.x += 0.35 if wall in [0, 2] else 0.0
		at.z += -0.3 if wall in [1, 3] else 0.0
		_box(_shaft, "plate", Vector3(0.14, 0.2, 0.14) * (Vector3.ONE - n.abs() * 0.85), at - n * 0.07, steel)
		_cyl(_shaft, "shade", 0.025, 0.075, 0.06, at + Vector3(0, 0.07, 0), steel)
		var bulb := MeshInstance3D.new()
		var sp := SphereMesh.new()
		sp.radius = 0.045
		sp.height = 0.09
		sp.radial_segments = 10
		sp.rings = 6
		bulb.mesh = sp
		var bm := StandardMaterial3D.new()
		bm.albedo_color = Color(0.35, 0.3, 0.25)
		bm.emission_enabled = true
		bm.emission = WARM
		bm.emission_energy_multiplier = 0.0
		bulb.material_override = bm
		bulb.position = at + Vector3(0, 0.02, 0)
		bulb.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_shaft.add_child(bulb)
		var light: OmniLight3D = null
		if i % 2 == 0:
			light = OmniLight3D.new()
			light.light_color = WARM
			light.light_energy = 0.0
			light.omni_range = 5.5
			light.omni_attenuation = 1.3
			light.shadow_enabled = false
			light.position = at + n * 0.25
			_shaft.add_child(light)
		_lamps.append([bulb, light])
	# the cage: roof, crosshead, hitch, corner posts and a work lamp on top
	_cage = Node3D.new()
	_cage.name = "cage"
	_shaft.add_child(_cage)
	var cw := 2 * h - 0.22
	_box(_cage, "roof", Vector3(cw, 0.07, cw), Vector3.ZERO, painted)
	_box(_cage, "hatch", Vector3(0.62, 0.025, 0.62), Vector3(-0.35, 0.045, 0.3), steel)
	_box(_cage, "crosshead", Vector3(cw, 0.16, 0.16), Vector3(0, 0.11, 0), steel)
	_cyl(_cage, "hitch", 0.08, 0.08, 0.1, Vector3(0, 0.24, 0), steel)
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			_box(_cage, "post", Vector3(0.07, 2.3, 0.07), Vector3(sx * (cw * 0.5 - 0.04), -1.15, sz * (cw * 0.5 - 0.04)), painted)
	var lamp := MeshInstance3D.new()
	var ls := SphereMesh.new()
	ls.radius = 0.06
	ls.height = 0.12
	lamp.mesh = ls
	var lm := StandardMaterial3D.new()
	lm.albedo_color = Color(0.4, 0.35, 0.3)
	lm.emission_enabled = true
	lm.emission = Color("ffd9a0")
	lm.emission_energy_multiplier = 2.0
	lamp.material_override = lm
	lamp.position = Vector3(0.45, 0.12, -0.45)
	lamp.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_cage.add_child(lamp)
	_cage_light = OmniLight3D.new()
	_cage_light.light_color = Color("ffd9a0")
	_cage_light.light_energy = 1.8
	_cage_light.omni_range = 6.5
	_cage_light.omni_attenuation = 1.2
	_cage_light.position = Vector3(0.45, 0.45, -0.45)
	_cage.add_child(_cage_light)
	for i in 4:
		var c := _cyl(_shaft, "cable", 0.011, 0.011, 1.0, Vector3.ZERO, steel, 6)
		_cables.append(c)
	# the bottom: a pit floor and the cold light of Level −2 breathing through the gate below
	_box(_shaft, "pit", Vector3(2 * h, 0.2, 2 * h), Vector3(SHAFT_X, SHAFT_BOTTOM - 0.1, SHAFT_Z), concrete)
	var disc := MeshInstance3D.new()
	var dm := CylinderMesh.new()
	dm.top_radius = 0.95
	dm.bottom_radius = 0.95
	dm.height = 0.02
	dm.radial_segments = 32
	disc.mesh = dm
	_glow_mat = StandardMaterial3D.new()
	_glow_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_glow_mat.albedo_color = Color(DEEP, 1.0) * 0.0
	disc.material_override = _glow_mat
	disc.position = Vector3(SHAFT_X, SHAFT_BOTTOM + 0.02, SHAFT_Z)
	disc.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_shaft.add_child(disc)
	_glow_light = OmniLight3D.new()
	_glow_light.light_color = DEEP
	_glow_light.light_energy = 0.0
	_glow_light.omni_range = 11.0
	_glow_light.omni_attenuation = 1.1
	_glow_light.position = Vector3(SHAFT_X, SHAFT_BOTTOM + 1.4, SHAFT_Z)
	_shaft.add_child(_glow_light)


func _free_shaft() -> void:
	if _shaft != null:
		_shaft.queue_free()
	_shaft = null
	_lamps.clear()
	_cables.clear()
	_cage = null
	_glow_light = null
	set_process(false)
	AudioManager.ambience("amb_power_hum", false, 0.0, 2.0)
	AudioManager.ambience("amb_archive", true, -4.0, 2.0)


func _set_cage(cy: float) -> void:
	if _cage == null:
		return
	_cage.position = Vector3(SHAFT_X, cy, SHAFT_Z)
	var top := SHAFT_TOP
	var from := cy + 0.28
	var len := top - from
	for i in _cables.size():
		var c := _cables[i]
		c.scale = Vector3(1, len, 1)
		c.position = Vector3(SHAFT_X - 0.09 + 0.06 * i, from + len * 0.5, SHAFT_Z + 0.02 * (i % 2))


func _climb(to: float, seconds: float) -> void:
	if _cage == null:
		return
	var from := _cage.position.y
	AudioManager.sfx("vault_wheel", -14.0, 0.45)
	var tw := room.create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_method(_set_cage, from, to, seconds)


func _light_lamp(i: int) -> void:
	var pair: Array = _lamps[i]
	var bulb := pair[0] as MeshInstance3D
	var light := pair[1] as OmniLight3D
	var m := bulb.material_override as StandardMaterial3D
	var tw := room.create_tween()
	# relay-style: a stutter, then on
	tw.tween_property(m, "emission_energy_multiplier", 1.6, 0.05)
	tw.tween_property(m, "emission_energy_multiplier", 0.2, 0.06)
	tw.tween_property(m, "emission_energy_multiplier", 2.0, 0.2)
	if light:
		var tl := room.create_tween()
		tl.tween_property(light, "light_energy", 1.0, 0.05)
		tl.tween_property(light, "light_energy", 0.1, 0.06)
		tl.tween_property(light, "light_energy", 1.5, 0.3)


func _wake_bottom() -> void:
	_breath_t = 0.0
	set_process(true)


func _process(delta: float) -> void:
	if _glow_light == null:
		set_process(false)
		return
	_breath_t += delta
	var rise := clampf(_breath_t / 2.5, 0.0, 1.0)
	var breath := 0.65 + 0.35 * sin(_breath_t * 1.6)
	_glow_light.light_energy = 2.2 * rise * breath
	_glow_mat.albedo_color = Color(DEEP.r, DEEP.g, DEEP.b) * (0.75 * rise * breath)


## A slow push down the shaft while the lamps wake (skipped with reduce motion).
func _push_down(seconds: float) -> void:
	var cam := _cam()
	if not cam.views.has("shaft") or bool(Settings.get_value("reduce_motion")):
		return
	var tw := room.create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_method(func(k: float) -> void:
		if cam.views.has("shaft"):
			cam.views["shaft"]["pos"] = VIEW_POS + Vector3(0.0, -1.1 * k, -0.18 * k), 0.0, 1.0, seconds)
	tw.tween_callback(func() -> void:
		if cam.views.has("shaft"):
			cam.views["shaft"]["pos"] = VIEW_POS)
