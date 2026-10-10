class_name MenuBox
extends Node3D
## Renders MenuBoxLogic on Prof. Strand's gear box in the main-menu backdrop: knobs that push in, wheels that drop a
## notch (neighbours counter-turn), the idle life (a fidget every 7-12 s, a glint across the brass plate, rarely the
## lid lifting a few millimetres and settling with a muffled knock), the lid opening on the lamp cell with warm
## light spilling out, and the start transition (wheels spin into alignment, latch, lid, light).
## Phone GPU budget: no new shadowed light. The glow is an emissive material on the cell, one additive light card, and
## one unshadowed omni that exists only while the lid is open (none at safe graphics level 3). Everything animates in
## advance(delta) from numbers held in members: no tweens, no per-frame allocations.

signal start_goto # the loading flow should start now (once per start)
signal start_done

const LID_OPEN_DEG := 70.0
const KNOB_PUSH := 0.0035 # m a knob moves in
const KNOB_DOWN_S := 0.07
const KNOB_HOLD_S := 0.05
const KNOB_UP_S := 0.16
const WHEEL_DELAY_S := 0.035 # the wheel turns just after the knob bottoms out
const WHEEL_S := 0.17
const WHEEL_DEG := 60.0
const FRONT_NOTCH := 3 # the rest pose points at the back; the front mark is half a turn on
const FIDGET_FIRST_S := 3.5
const QUIET_AFTER_TOUCH_S := 14.0 # no fidgeting right after the player played with it
const LIFT_DEG := 0.85 # the lid lifts ~2.7 mm at its front edge
const LIFT_S := 1.0
const LID_KNOCK_T := 0.58
const GLINT_S := 2.6
const PLATE_POS := Vector3(0.0, 0.0329, 0.093) # brass plate centre in the lid's local space (hinge at the origin)
const PLATE_SIZE := Vector2(0.214, 0.136)
const TAP_PX := 44.0 # minimum tap radius, viewport px
const KNOB_R := 0.026
const WHEEL_R := 0.042
const GLOW_COLOR := Color("ffb15e")
const CELL_ANCHOR_UP := 0.075 # light card height above the base

var logic := MenuBoxLogic.new()
var model: Node3D
var _lid: Node3D
var _lid_rest := Basis.IDENTITY
var _gears: Array[Node3D] = []
var _gear_rest: Array[Basis] = []
var _knobs: Array[Node3D] = []
var _knob_rest: Array[Vector3] = []
var _cell_mat: StandardMaterial3D
var _card: MeshInstance3D
var _card_mat: StandardMaterial3D
var _glint: MeshInstance3D
var _glint_mat: StandardMaterial3D
var _light: OmniLight3D
var _safe := 0
var _rng := RandomNumberGenerator.new()

var _t := 0.0
var _still := false
var _since_touch := 99.0
var _next_fidget := FIDGET_FIRST_S
var _next_glint := 6.0
var _next_knock := 45.0
var _glint_t := -1.0
var _lift_t := -1.0
var _lift_knocked := false
var _idle_press := false
var _last_knob := 0
# per wheel: continuous angle in notches and the move it is making (from -> to over dur after delay)
var _w_ang := PackedFloat32Array([0.0, 0.0, 0.0])
var _w_from := PackedFloat32Array([0.0, 0.0, 0.0])
var _w_to := PackedFloat32Array([0.0, 0.0, 0.0])
var _w_t := PackedFloat32Array([9.0, 9.0, 9.0]) # time since the press; >= delay + dur = at rest
var _w_delay := PackedFloat32Array([0.0, 0.0, 0.0])
var _w_dur := PackedFloat32Array([WHEEL_S, WHEEL_S, WHEEL_S])
var _w_click := PackedFloat32Array([-99.0, -99.0, -99.0]) # dB of the click at the move's start (-99 = silent)
var _w_click_pitch := PackedFloat32Array([1.0, 1.0, 1.0])
var _k_t := PackedFloat32Array([9.0, 9.0, 9.0])
var _snd_latch := false
var _snd_lid := false
var _snd_close := false
var _lid_deg := 0.0
var _glow := 0.0
var _flood := 0.0
var _push := 0.0


func _init() -> void:
	logic.event.connect(_on_event)


## Spawns the model under this node and finds its parts. Returns the model (null when the file is missing).
func setup(safe_level: int, seed_value: int = 0) -> Node3D:
	_safe = safe_level
	if seed_value != 0:
		_rng.seed = seed_value
	else:
		_rng.randomize()
	model = ModelUtil.spawn("gear_box", self, Transform3D.IDENTITY, "none")
	if model == null:
		return null
	_lid = ModelUtil.find(model, "IA_box_lid")
	if _lid != null:
		_lid_rest = _lid.basis
	for i in 3:
		var g := ModelUtil.find(model, "IA_gear_%d" % i)
		if g != null:
			_gears.append(g)
			_gear_rest.append(g.basis)
		var k := ModelUtil.find(model, "IA_knob_%d" % i)
		if k != null:
			_knobs.append(k)
			_knob_rest.append(k.position)
	_build_cell()
	_build_glint()
	_build_card()
	for i in 3:
		_w_ang[i] = float(logic.wheels[i])
		_w_from[i] = _w_ang[i]
		_w_to[i] = _w_ang[i]
	_apply_pose()
	return model


func _build_cell() -> void:
	var anchor := ModelUtil.find(model, "battery_anchor")
	if anchor == null:
		return
	var cell := ModelUtil.spawn("battery_cell", anchor, Transform3D.IDENTITY, "none")
	if cell == null:
		return
	_cell_mat = StandardMaterial3D.new()
	_cell_mat.albedo_color = Color("3a2a16")
	_cell_mat.emission_enabled = true
	_cell_mat.emission = GLOW_COLOR
	_cell_mat.emission_energy_multiplier = 0.0
	_cell_mat.roughness = 0.5
	for mi in ModelUtil.find_meshes(cell):
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		for s in mi.get_surface_override_material_count():
			mi.set_surface_override_material(s, _cell_mat)


## A diagonal soft stripe of light on a quad lying on the brass plate; sliding its UV moves the glint across.
func _build_glint() -> void:
	if _lid == null:
		return
	var g := Gradient.new()
	g.offsets = PackedFloat32Array([0.0, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0])
	g.colors = PackedColorArray([Color(1, 1, 1, 0), Color(1, 1, 1, 0), Color(1, 1, 1, 0.12), Color(1, 1, 1, 0.5),
		Color(1, 1, 1, 0.12), Color(1, 1, 1, 0), Color(1, 1, 1, 0)])
	var tex := GradientTexture2D.new()
	tex.gradient = g
	tex.width = 128
	tex.height = 32
	tex.fill_from = Vector2(0.25, 0.0)
	tex.fill_to = Vector2(0.75, 1.0) # slanted stripe
	_glint_mat = StandardMaterial3D.new()
	_glint_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_glint_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	_glint_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_glint_mat.albedo_texture = tex
	_glint_mat.albedo_color = Color(1.0, 0.82, 0.5, 1.0)
	_glint_mat.texture_repeat = false
	_glint_mat.uv1_offset = Vector3(1.0, 0.0, 0.0)
	_glint_mat.disable_receive_shadows = true
	var pm := PlaneMesh.new()
	pm.size = PLATE_SIZE
	pm.material = _glint_mat
	_glint = MeshInstance3D.new()
	_glint.mesh = pm
	_glint.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_glint.position = PLATE_POS
	_glint.visible = false
	_lid.add_child(_glint)


## A soft additive glow above the cell (it also carries the "light pouring out" where the post glow is off).
func _build_card() -> void:
	var g := Gradient.new()
	g.offsets = PackedFloat32Array([0.0, 0.35, 1.0])
	g.colors = PackedColorArray([Color(1, 1, 1, 1), Color(1, 1, 1, 0.28), Color(1, 1, 1, 0)])
	var tex := GradientTexture2D.new()
	tex.gradient = g
	tex.width = 128
	tex.height = 128
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(1.0, 0.5)
	_card_mat = StandardMaterial3D.new()
	_card_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_card_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	_card_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_card_mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	_card_mat.albedo_texture = tex
	_card_mat.albedo_color = Color(GLOW_COLOR, 0.0)
	_card_mat.disable_receive_shadows = true
	var qm := QuadMesh.new()
	qm.size = Vector2(0.3, 0.3)
	qm.material = _card_mat
	_card = MeshInstance3D.new()
	_card.mesh = qm
	_card.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_card.position = Vector3(0.0, CELL_ANCHOR_UP, 0.0)
	_card.visible = false
	model.add_child(_card)


# ==================================================================== input
## A tap along the ray (camera ray, in world space). `px_m` = metres one viewport pixel covers per metre of distance.
## Returns true when it pressed a knob.
func tap_ray(from: Vector3, dir: Vector3, px_m: float) -> bool:
	if logic.phase != MenuBoxLogic.Phase.CLOSED:
		return false
	var best := -1
	var best_score := 1.0
	for i in _knobs.size():
		var s := _hit_score(from, dir, _knobs[i].global_position, KNOB_R, px_m)
		if s < best_score:
			best_score = s
			best = i
	for i in _gears.size():
		var s := _hit_score(from, dir, _gears[i].global_position, WHEEL_R, px_m)
		if s < best_score:
			best_score = s
			best = i
	if best < 0:
		return false
	touch(best)
	return true


## Distance of the ray from `c`, relative to the target radius (< 1 = hit); the radius never drops below TAP_PX.
static func _hit_score(from: Vector3, dir: Vector3, c: Vector3, radius: float, px_m: float) -> float:
	var t := (c - from).dot(dir)
	if t <= 0.0:
		return 99.0
	var r := maxf(radius, TAP_PX * px_m * t)
	return (c - (from + dir * t)).length() / r


## The player presses knob k (a tap on it or its wheel).
func touch(k: int) -> bool:
	_since_touch = 0.0
	_idle_press = false
	return logic.press(k)


func tap_anywhere() -> bool:
	_since_touch = 0.0
	return logic.tap_anywhere()


func begin_start(reduce_motion: bool) -> void:
	_since_touch = 0.0
	logic.begin_start(reduce_motion)


# ==================================================================== events
func _on_event(ev: StringName, arg: int) -> void:
	match ev:
		&"press":
			_last_knob = arg
			_k_t[arg] = 0.0
			var db := -15.0 if _idle_press else -8.0
			AudioManager.sfx("menu_click", db, 0.94 + 0.06 * arg)
			if not _idle_press:
				AudioManager.haptic(12)
		&"turn":
			_turn_wheel(arg, MenuBoxLogic.dir(_last_knob, arg))
		&"latch":
			if arg == 0:
				_snd_latch = false
				_snd_lid = false
				AudioManager.haptic(30)
		&"land":
			_land_wheel(arg)
		&"open":
			pass
		&"close":
			_snd_close = false
			for w in 3: # the wheels were scrambled again behind the lid
				_w_ang[w] = float(logic.wheels[w])
				_w_from[w] = _w_ang[w]
				_w_to[w] = _w_ang[w]
				_w_t[w] = 9.0
		&"start":
			_snd_latch = false
			_snd_lid = false
			if arg == 0:
				for w in 3:
					begin_spin(w, maxf(0.0, MenuBoxLogic.START_TIMES[w] - MenuBoxLogic.START_SPIN_S))
		&"goto":
			start_goto.emit()
		&"start_done":
			start_done.emit()


func _turn_wheel(w: int, d: int) -> void:
	if w >= _gears.size() or d == 0:
		return
	var own := w == _last_knob
	_w_from[w] = _w_ang[w]
	_w_to[w] = _w_to[w] + d # chained presses continue from where the last one is going
	_w_t[w] = 0.0
	_w_delay[w] = WHEEL_DELAY_S if own else WHEEL_DELAY_S + 0.03
	_w_dur[w] = WHEEL_S
	if not own:
		_w_click[w] = -15.0 if _idle_press else -11.0
		_w_click_pitch[w] = 1.12 + 0.05 * w
	else:
		_w_click[w] = -99.0
	if _still:
		_w_ang[w] = _w_to[w]
		_w_t[w] = 9.0


## The start transition: wheel w spins (at least half a turn) and lands on the front mark, click.
func begin_spin(w: int, delay: float) -> void:
	if w >= _gears.size():
		return
	var a := _w_ang[w]
	var rest := fposmod(-a, float(MenuBoxLogic.NOTCHES))
	var turn := rest if rest >= 3.0 else rest + float(MenuBoxLogic.NOTCHES)
	_w_from[w] = a
	_w_to[w] = a + turn
	_w_t[w] = -delay
	_w_delay[w] = 0.0
	_w_dur[w] = MenuBoxLogic.START_SPIN_S
	_w_click[w] = -99.0


func _land_wheel(w: int) -> void:
	AudioManager.sfx("menu_click", -3.0, 0.9 + 0.1 * w)
	AudioManager.haptic(8)


# ==================================================================== time
## Advances the animation. `still` = Settings "reduce_motion" (no fidgets, no easing of the wheels).
func advance(delta: float, still: bool = false) -> void:
	_t += delta
	_since_touch += delta
	if still != _still:
		_still = still
	logic.tick(delta)
	_idle(delta)
	_sounds()
	_step_knobs(delta)
	_step_wheels(delta)
	if _lift_t >= 0.0:
		_lift_t += delta
		if logic.phase != MenuBoxLogic.Phase.CLOSED:
			_lift_t = -1.0
	_lid_deg = _lid_angle()
	_update_glow(delta)
	_apply_pose()


func _idle(delta: float) -> void:
	if _still or logic.phase != MenuBoxLogic.Phase.CLOSED:
		return
	# the fidget: a knob pushes in, its wheel jumps a notch
	if _since_touch > QUIET_AFTER_TOUCH_S:
		_next_fidget -= delta
		if _next_fidget <= 0.0:
			_next_fidget = _rng.randf_range(7.0, 12.0)
			var k := logic.pick_idle_knob(_rng.randf())
			if k >= 0:
				_idle_press = true
				logic.press(k)
				_idle_press = false
	_next_glint -= delta
	if _next_glint <= 0.0 and _glint_t < 0.0:
		_next_glint = _rng.randf_range(15.0, 26.0)
		_glint_t = 0.0
	_next_knock -= delta
	if _next_knock <= 0.0 and _lift_t < 0.0 and _since_touch > 6.0:
		_next_knock = _rng.randf_range(55.0, 95.0)
		_lift_t = 0.0
		_lift_knocked = false


## Fixed-time sounds inside a phase (the latch and the lid after the last wheel lands, the lid closing).
func _sounds() -> void:
	match logic.phase:
		MenuBoxLogic.Phase.OPENING:
			if not _snd_latch and logic.phase_t >= 0.16:
				_snd_latch = true
				AudioManager.sfx("menu_latch", -6.0)
			if not _snd_lid and logic.phase_t >= 0.34:
				_snd_lid = true
				AudioManager.sfx("menu_lid_open", -7.0)
		MenuBoxLogic.Phase.CLOSING:
			if not _snd_close and logic.phase_t >= 0.42:
				_snd_close = true
				AudioManager.sfx("menu_lid_close", -9.0)
		MenuBoxLogic.Phase.STARTING:
			if _still:
				return
			if not _snd_latch and logic.start_t >= MenuBoxLogic.START_LATCH_T and not logic.skipped:
				_snd_latch = true
				AudioManager.sfx("menu_latch", -3.0)
				AudioManager.haptic(30)
			if not _snd_lid and logic.start_t >= MenuBoxLogic.START_LATCH_T + 0.16 and not logic.skipped:
				_snd_lid = true
				AudioManager.sfx("menu_lid_open", -4.0)


func _step_knobs(delta: float) -> void:
	for i in 3:
		if _k_t[i] < 9.0:
			_k_t[i] += delta


static func _knob_depth(t: float) -> float:
	if t < KNOB_DOWN_S:
		return 1.0 - pow(1.0 - t / KNOB_DOWN_S, 2.0)
	if t < KNOB_DOWN_S + KNOB_HOLD_S:
		return 1.0
	var u := (t - KNOB_DOWN_S - KNOB_HOLD_S) / KNOB_UP_S
	if u >= 1.0:
		return 0.0
	return 1.0 - u * u * (3.0 - 2.0 * u)


func _step_wheels(delta: float) -> void:
	for w in 3:
		if _w_t[w] >= 9.0:
			continue
		var before := _w_t[w]
		_w_t[w] += delta
		var t := _w_t[w] - _w_delay[w]
		if before - _w_delay[w] < 0.0 and t >= 0.0 and _w_click[w] > -90.0:
			AudioManager.sfx("menu_click", _w_click[w], _w_click_pitch[w])
			_w_click[w] = -99.0
		if t <= 0.0:
			continue
		var p := t / _w_dur[w]
		if p >= 1.0:
			_w_ang[w] = _w_to[w]
			_w_t[w] = 9.0
		else:
			_w_ang[w] = _w_from[w] + (_w_to[w] - _w_from[w]) * _ease_wheel(p)


## Fast out of the knock, settling with a small overshoot: the pawl drops into the notch.
static func _ease_wheel(p: float) -> float:
	var c1 := 0.9
	var c3 := c1 + 1.0
	var q := p - 1.0
	return 1.0 + c3 * q * q * q + c1 * q * q


# ==================================================================== lid
func _lid_angle() -> float:
	var deg := 0.0
	if _still: # reduce_motion: the lid is simply open or shut
		match logic.phase:
			MenuBoxLogic.Phase.OPENING, MenuBoxLogic.Phase.OPEN:
				return LID_OPEN_DEG
		return 0.0
	match logic.phase:
		MenuBoxLogic.Phase.CLOSED:
			deg = _lift_angle()
		MenuBoxLogic.Phase.OPENING:
			deg = _open_curve(logic.phase_t / MenuBoxLogic.OPEN_S, 0.18, 0.7)
		MenuBoxLogic.Phase.OPEN:
			deg = LID_OPEN_DEG
		MenuBoxLogic.Phase.CLOSING:
			deg = _close_curve(logic.phase_t / MenuBoxLogic.CLOSE_S)
		MenuBoxLogic.Phase.STARTING:
			if _still:
				deg = 0.0
			else:
				var t := logic.start_t - MenuBoxLogic.START_LATCH_T
				# the same swing as the touch opening, played faster
				deg = _open_curve(t / (MenuBoxLogic.START_LID_S + 0.12), 0.14, 0.55) if t > 0.0 else 0.0
	return deg


## The lid pops off its latch (a degree or so), then swings up heavily and meets its stop with a small rebound.
static func _open_curve(p: float, pop_at: float, c1: float) -> float:
	if p <= 0.0:
		return 0.0
	if p >= 1.0:
		return LID_OPEN_DEG
	var pop := 1.4
	if p < pop_at:
		return pop * sin(0.5 * PI * p / pop_at)
	var q := (p - pop_at) / (1.0 - pop_at)
	var c3 := c1 + 1.0
	var u := q - 1.0
	var e := 1.0 + c3 * u * u * u + c1 * u * u # ease out back: fast, then settles with a rebound
	return pop + (LID_OPEN_DEG - pop) * e


## Closing: gravity speeds it up, it meets the box at 90 % of the time and rebounds a degree.
static func _close_curve(p: float) -> float:
	if p >= 1.0:
		return 0.0
	var main := LID_OPEN_DEG * (1.0 - pow(minf(p / 0.9, 1.0), 2.2))
	return main + 1.0 * sin(PI * clampf((p - 0.9) / 0.1, 0.0, 1.0))


## The rare lift: the lid rises ~2.7 mm at the front, hangs, drops and knocks; a smaller rebound; still.
func _lift_angle() -> float:
	if _lift_t < 0.0:
		return 0.0
	var a := 0.0
	if _lift_t < 0.2:
		var u := _lift_t / 0.2
		a = LIFT_DEG * (1.0 - (1.0 - u) * (1.0 - u))
	elif _lift_t < LID_KNOCK_T - 0.14:
		a = LIFT_DEG * (1.0 + 0.03 * sin(_lift_t * 38.0)) # a hint of a tremble while it hangs
	elif _lift_t < LID_KNOCK_T:
		var u := (_lift_t - (LID_KNOCK_T - 0.14)) / 0.14
		a = LIFT_DEG * (1.0 - u * u)
	elif _lift_t < LID_KNOCK_T + 0.09:
		var u := (_lift_t - LID_KNOCK_T) / 0.09
		a = 0.22 * sin(PI * u)
	if _lift_t >= LID_KNOCK_T and not _lift_knocked:
		_lift_knocked = true
		AudioManager.sfx("menu_knock", -9.0)
	if _lift_t >= LIFT_S:
		_lift_t = -1.0
		return 0.0
	return a


# ==================================================================== light
func _update_glow(delta: float) -> void:
	var g := clampf(_lid_deg / LID_OPEN_DEG, 0.0, 1.0)
	_glow = g * g * (3.0 - 2.0 * g)
	_flood = 0.0
	_push = 0.0
	if logic.phase == MenuBoxLogic.Phase.STARTING and not _still:
		var t := logic.start_t
		_flood = smoothstep(1.15, 1.75, t)
		_push = smoothstep(0.98, 1.78, t)
	# glint
	if _glint != null:
		if _glint_t >= 0.0 and not _still:
			_glint_t += delta
		_update_glint()
	# the light only exists while the lid is open
	if _glow > 0.002:
		if _light == null and _safe < 3:
			_light = OmniLight3D.new()
			_light.light_color = Color("ffbf73")
			_light.omni_range = 0.55
			_light.omni_attenuation = 1.6
			_light.light_specular = 0.4
			_light.shadow_enabled = false
			_light.position = Vector3(0.0, 0.1, 0.0)
			model.add_child(_light)
		if _light != null:
			_light.light_energy = 2.4 * _glow + 3.0 * _flood
	elif _light != null:
		_light.queue_free()
		_light = null
	if _cell_mat != null:
		_cell_mat.emission_energy_multiplier = 2.6 * _glow + 3.0 * _flood
	if _card != null:
		_card.visible = _glow > 0.002
		if _card.visible:
			_card_mat.albedo_color = Color(GLOW_COLOR, clampf(0.55 * _glow + 0.35 * _flood, 0.0, 1.0))


func _update_glint() -> void:
	if _glint_t < 0.0 or _glint_t > GLINT_S:
		_glint.visible = false
		if _glint_t > GLINT_S:
			_glint_t = -1.0
		return
	var p := _glint_t / GLINT_S
	p = p * p * (3.0 - 2.0 * p) * 0.35 + p * 0.65 # a slow, slightly eased sweep
	_glint_mat.uv1_offset.x = lerpf(0.78, -0.78, p)
	var fade := sin(PI * clampf(p, 0.0, 1.0))
	_glint_mat.albedo_color.a = clampf(fade * 1.4, 0.0, 1.0) * 0.8
	_glint.visible = true


## 0..1: how far the start transition has pushed the camera toward the glow.
func push() -> float:
	return _push


func flood() -> float:
	return _flood


func glow() -> float:
	return _glow


## QA: shows the glint at a given point of its sweep (0..1) without waiting for it.
func show_glint(p: float) -> void:
	_glint_t = clampf(p, 0.0, 1.0) * GLINT_S


func _apply_pose() -> void:
	for i in _gears.size():
		_gears[i].basis = _gear_rest[i] * Basis(Vector3.UP, -deg_to_rad(WHEEL_DEG) * (_w_ang[i] + FRONT_NOTCH))
	for i in _knobs.size():
		_knobs[i].position = _knob_rest[i] + Vector3(0.0, 0.0, -KNOB_PUSH * _knob_depth(_k_t[i]))
	if _lid != null:
		_lid.basis = _lid_rest * Basis(Vector3.RIGHT, -deg_to_rad(_lid_deg))
