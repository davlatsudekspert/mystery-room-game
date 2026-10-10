class_name Lab7Intro
extends Node
## Chapter 1's opening, about 17 s to the first prompt, a tap skips it at any moment. Rain and a heavy key in a
## heavy lock under the first card ("Meridian Institute ... Sealed since 14 November 1979."), a distant roll of
## thunder, the second card (the parcel), then the room by moonlight: the door, ajar, drifts on a draught and swings
## shut with a slam (the lights flinch, the camera shudders, the phone buzzes), the maglock clicks and its red lamp
## stutters on, the camera turns to the lamp-lit desk and a calm line points at the glowing notebook.
## It runs in the room's own scene (the room is already built; the first thing drawn is the card, with the rain
## already falling, never a bare black screen). The other chapters keep the HUD's card intro.

const DOOR_AJAR_DEG := -38.0
const DOOR_DRIFT_DEG := -31.0
const CARD_IN_S := 1.0
const CARD_OUT_S := 0.6
const CARD1_HOLD_S := 3.2
const CARD2_HOLD_S := 4.6
const REVEAL_S := 1.0
const LAYER := 40

var room: Node3D
var hud: Node
var _layer: CanvasLayer
var _black: ColorRect
var _box: VBoxContainer
var _label: Label
var _hint: Label
var _tweens: Array[Tween] = []
var _skipped := false
var _finished := false
var _lamp_base := 0.0
var _flicker_bases: Dictionary = {}
var _glint: FirstGlint


## Starts the opening on a fresh Chapter 1 (called by the room once everything is built).
static func start(r: Node3D) -> Lab7Intro:
	var i := Lab7Intro.new()
	i.room = r
	i.hud = r.get("hud")
	r.add_child(i)
	i.run.call_deferred()
	return i


func _ready() -> void:
	_layer = CanvasLayer.new()
	_layer.layer = LAYER
	add_child(_layer)
	_black = ColorRect.new()
	_black.color = Color(0.03, 0.035, 0.04, 1.0)
	_black.set_anchors_preset(Control.PRESET_FULL_RECT)
	_black.mouse_filter = Control.MOUSE_FILTER_STOP
	_black.gui_input.connect(_on_input)
	_layer.add_child(_black)
	var safe := UITheme.safe_margins()
	var canvas: Vector2 = UITheme.metrics()["canvas"]
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	center.offset_left = safe.x + 120
	center.offset_right = -(safe.z + 120)
	center.offset_top = safe.y + 40
	center.offset_bottom = -(safe.w + 120)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_black.add_child(center)
	_box = VBoxContainer.new()
	_box.add_theme_constant_override("separation", int(26.0 * UIOrnament.scale_k()))
	_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_box.modulate.a = 0.0
	center.add_child(_box)
	_box.add_child(UIOrnament.rule(0.0, 24.0))
	_label = UITheme.title("", 44, false)
	_label.add_theme_color_override("font_color", UITheme.CREAM)
	_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_label.custom_minimum_size.x = minf(1200.0 * UITheme.wscale(), canvas.x - safe.x - safe.z - 240.0)
	_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fit_font(canvas, safe)
	_box.add_child(_label)
	_box.add_child(UIOrnament.rule(0.0, 24.0))
	_hint = UITheme.label("ui.tap_to_skip", 22, UITheme.MUTED)
	_hint.add_theme_font_override("font", UITheme.caps_font(false, 2))
	_hint.uppercase = true
	_hint.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hint.autowrap_mode = TextServer.AUTOWRAP_OFF
	_hint.offset_bottom = -(safe.w + 50)
	_hint.offset_top = _hint.offset_bottom - 40
	_hint.offset_left = -400
	_hint.offset_right = 400
	_hint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hint.modulate.a = 0.0
	_black.add_child(_hint)


## The largest display size at which the longer card still fits (Extra large text on a short screen).
func _fit_font(canvas: Vector2, safe: Vector4) -> void:
	var w := _label.custom_minimum_size.x
	var avail_h := canvas.y - safe.y - safe.w - 160.0 - 2.0 * (24.0 + 26.0 * UIOrnament.scale_k())
	var fs := UITheme.size(44)
	var floor_fs := UITheme.size(26)
	var f := _label.get_theme_font("font")
	for key in ["intro.1", "intro.2"]:
		while fs > floor_fs and f.get_multiline_string_size(tr(key), HORIZONTAL_ALIGNMENT_CENTER, w, fs).y > avail_h * 0.8:
			fs = maxi(floor_fs, int(fs * 0.92))
	_label.add_theme_font_size_override("font_size", fs)


func _on_input(event: InputEvent) -> void:
	if (event is InputEventMouseButton or event is InputEventScreenTouch) and event.pressed:
		skip()


## Jumps to the end state: door shut, lamp on, the lab in view, control back.
func skip() -> void:
	_skipped = true


func _tween() -> Tween:
	var tw := create_tween()
	_tweens.append(tw)
	return tw


## Waits `seconds`, or until a tap skips the opening. True when skipped.
func _wait(seconds: float) -> bool:
	var t := 0.0
	while t < seconds and not _skipped:
		await get_tree().process_frame
		t += get_process_delta_time()
	return _skipped


func run() -> void:
	hud.call("set_busy", true)
	_prep()
	var hint_tw := _tween()
	hint_tw.tween_property(_hint, "modulate:a", 0.8, 0.8).set_delay(1.2)
	hint_tw.tween_interval(6.0)
	hint_tw.tween_property(_hint, "modulate:a", 0.0, 1.0)
	AudioManager.sfx("intro_key", -4.0)
	if await _card("intro.1", CARD1_HOLD_S):
		_finish()
		return
	if await _wait(0.3):
		_finish()
		return
	AudioManager.sfx("intro_thunder", -13.0)
	if await _card("intro.2", CARD2_HOLD_S):
		_finish()
		return
	# --- the room: the door, ajar, drifts on a draught
	var reveal := _tween()
	reveal.tween_property(_black, "color:a", 0.0, REVEAL_S).set_trans(Tween.TRANS_SINE)
	reveal.tween_property(_hint, "modulate:a", 0.0, 0.2)
	_black.mouse_filter = Control.MOUSE_FILTER_STOP # still catches a skip tap, shows the room through
	AudioManager.sfx("door_open", -9.0, 0.9)
	_door(DOOR_DRIFT_DEG, 1.3, Tween.TRANS_SINE, Tween.EASE_IN_OUT)
	if await _wait(1.7):
		_finish()
		return
	# --- it swings shut: faster and faster, then the slam
	_door(0.0, 0.5, Tween.TRANS_QUAD, Tween.EASE_IN)
	if await _wait(0.5):
		_finish()
		return
	_slam()
	if await _wait(0.9):
		_finish()
		return
	# --- the maglock clicks, its red lamp stutters on
	AudioManager.sfx("maglock_release", -4.0, 0.8)
	_lamp_on(true)
	AudioManager.haptic(40)
	hud.call("caption", tr(room.get("logic").intro_caption_key()), 3.0)
	if await _wait(1.0):
		_finish()
		return
	_to_lab(false)
	hud.call("set_busy", false)
	_black.queue_free()
	_black = null
	_hand_over()
	_finished = true # a tap now is just play; nothing is left to skip
	await get_tree().create_timer(2.1).timeout
	_first_prompt()


## One card: fades in, holds, fades out. True when skipped meanwhile.
func _card(key: String, hold: float) -> bool:
	_label.text = tr(key)
	var tw := _tween()
	tw.tween_property(_box, "modulate:a", 1.0, CARD_IN_S).set_trans(Tween.TRANS_SINE)
	if await _wait(CARD_IN_S + hold):
		return true
	var out := _tween()
	out.tween_property(_box, "modulate:a", 0.0, CARD_OUT_S).set_trans(Tween.TRANS_SINE)
	return await _wait(CARD_OUT_S + 0.1)


# ====================================================================== the world
func _leaf() -> Node3D:
	return (room.get("visuals") as Lab7Visuals).part("door_lab7", "IA_door_leaf")


func _door_deg(deg: float) -> void:
	var leaf := _leaf()
	if leaf == null:
		return
	var rest: Dictionary = (room.get("visuals") as Lab7Visuals).rest
	if not rest.has(leaf):
		rest[leaf] = leaf.transform
	var base: Transform3D = rest[leaf]
	leaf.transform = Transform3D(base.basis * Basis(Vector3.UP, deg_to_rad(deg)), base.origin)


func _door(to_deg: float, seconds: float, trans: Tween.TransitionType, ease_type: Tween.EaseType) -> void:
	var from := _door_now
	var tw := _tween()
	tw.tween_method(func(d: float) -> void:
		_door_now = d
		_door_deg(d), from, to_deg, seconds).set_trans(trans).set_ease(ease_type)


var _door_now := DOOR_AJAR_DEG


func _prep() -> void:
	var cam: RoomCamera = room.get("cam")
	cam.go("door", true)
	_door_now = DOOR_AJAR_DEG
	_door_deg(DOOR_AJAR_DEG)
	_lamp_on(false)
	var lights: Dictionary = room.get("lights")
	for k in ["desk_lamp", "pendant_0", "pendant_1"]:
		if lights.has(k):
			_flicker_bases[k] = (lights[k] as Light3D).light_energy


## The door meets its frame: slam, a flinch of the lights, a shudder of the camera, the phone buzzes.
func _slam() -> void:
	_door_now = 0.0
	_door_deg(0.0)
	AudioManager.sfx("door_slam")
	AudioManager.haptic(120)
	var cam: RoomCamera = room.get("cam")
	var shake := _tween()
	shake.tween_method(func(k: float) -> void:
		var a := (1.0 - k) * (1.0 - k)
		cam.h_offset = sin(k * 71.0) * 0.045 * a
		cam.v_offset = sin(k * 53.0 + 1.0) * 0.03 * a, 0.0, 1.0, 0.55)
	shake.tween_callback(func() -> void:
		cam.h_offset = 0.0
		cam.v_offset = 0.0)
	var lights: Dictionary = room.get("lights")
	for k: String in _flicker_bases:
		var l: Light3D = lights[k]
		var base: float = _flicker_bases[k]
		var seq := _tween()
		seq.tween_property(l, "light_energy", base * 0.2, 0.05)
		seq.tween_property(l, "light_energy", base * 1.1, 0.06)
		seq.tween_property(l, "light_energy", base * 0.5, 0.05)
		seq.tween_property(l, "light_energy", base, 0.25)


## The maglock lamp: dark, or stuttering on to its steady red (the lamp's own state is the room's: red while sealed).
func _lamp_on(on: bool) -> void:
	var mag := (room.get("visuals") as Lab7Visuals).part("door_lab7", "maglock_lamp") as MeshInstance3D
	var ml: OmniLight3D = (room.get("lights") as Dictionary).get("maglock")
	if ml != null and _lamp_base == 0.0:
		_lamp_base = ml.light_energy
	if mag == null:
		return
	if not on:
		ModelUtil.set_emission(mag, false)
		if ml != null:
			ml.light_energy = 0.0
		return
	var tw := _tween()
	var steps := [0.3, 0.0, 1.0, 0.35, 1.0]
	for s: float in steps:
		tw.tween_callback(func() -> void:
			ModelUtil.set_emission(mag, s > 0.0, Color("ff3b2f"), Lab7Visuals.LAMP_GLASS_ENERGY * s)
			if ml != null:
				ml.light_energy = _lamp_base * s)
		tw.tween_interval(0.07)


func _to_lab(instant: bool) -> void:
	var cam: RoomCamera = room.get("cam")
	cam.h_offset = 0.0
	cam.v_offset = 0.0
	cam.go("lab", instant)


## The glowing notebook, from now on until it is taken.
func _hand_over() -> void:
	var nb: Node3D = (room.get("models") as Dictionary).get("notebook")
	if nb == null:
		return
	_glint = FirstGlint.attach(nb, 0.035, func() -> bool:
		return bool((room.get("logic").state["taken"] as Dictionary).get("notebook", false)))
	_glint.show_glow()


func _first_prompt() -> void:
	if hud != null and is_instance_valid(hud):
		hud.call("caption", tr("tut.first"), 6.0)


## The end state, reached by a skip: everything settled at once.
func _finish() -> void:
	if _finished:
		return
	_finished = true
	for tw in _tweens:
		if tw != null and tw.is_valid():
			tw.kill()
	_door_now = 0.0
	_door_deg(0.0)
	var lights: Dictionary = room.get("lights")
	for k: String in _flicker_bases:
		(lights[k] as Light3D).light_energy = _flicker_bases[k]
	var mag := (room.get("visuals") as Lab7Visuals).part("door_lab7", "maglock_lamp") as MeshInstance3D
	if mag != null:
		ModelUtil.set_emission(mag, true, Color("ff3b2f"), Lab7Visuals.LAMP_GLASS_ENERGY)
	var ml: OmniLight3D = lights.get("maglock")
	if ml != null:
		ml.light_energy = _lamp_base
	_to_lab(true)
	hud.call("set_busy", false)
	hud.call("caption", tr(room.get("logic").intro_caption_key()), 3.0)
	_hand_over()
	if _black != null:
		var tw := create_tween()
		tw.tween_property(_black, "color:a", 0.0, 0.35)
		tw.tween_callback(_black.queue_free)
		_black.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_black = null
	get_tree().create_timer(2.0).timeout.connect(_first_prompt)
