class_name Lab7Visuals
extends Node
## Renders Lab7Logic state onto the 3D models: part poses, item visibility, lamps, beam.
## Every visual is derived from logic.state, so loading a save reproduces the scene exactly.
## Axis/sign constants are calibrated against docs/models/*.md (Blender exports).

const WHEEL_STEP_DEG := 36.0
const WHEEL_AXIS := Vector3.RIGHT
const WHEEL_SIGN := 1.0
## The player reads the lock from the seated eye line (~30° above the axle), like a desk lock with an
## angled window, so each digit sits that far "up" the wheel; otherwise the next digit shows instead.
const WHEEL_VIEW_TILT_DEG := 30.0
const DRAWER_TRAVEL := 0.26
const GEAR_SIGN := -1.0
const LID_OPEN_DEG := -105.0
const SAFE_DOOR_OPEN_DEG := -110.0
const SWITCH_OFF_DEG := 0.0
const SWITCH_ON_DEG := -70.0
const LEVER_OFF_DEG := 0.0
const LEVER_ON_DEG := -80.0
const SHELF_OPEN_DEG := 85.0
const CABINET_OPEN_DEG := -100.0
const DOOR_OPEN_DEG := -95.0
const RING_SIGN := 1.0
const BOOK_TILT_DEG := 16.0

var room: Node3D
var logic: Lab7Logic
var rest: Dictionary = {} # part node -> rest Transform3D
var radio_hatch_open := false
var _tweens: Dictionary = {}
var _beam_root: Node3D
var _items: Dictionary = {} # spot -> Node3D
var _safe_label: Label3D
var _lamp_mats: Dictionary = {}
var _emblem_projection: Decal
var _door_opened := false


func _init(r: Node3D) -> void:
	room = r
	logic = r.get("logic")


func _ready() -> void:
	_record_rest()
	_attach_bookshelf_children()
	_spawn_container_items()
	_build_safe_display()
	_beam_root = Node3D.new()
	_beam_root.name = "Beam"
	room.add_child(_beam_root)
	_build_red_leak()


var _leak: Array[MeshInstance3D] = []


## Thin red light seams around the closed bookcase: the darkroom safelight leaking through the gaps.
func _build_red_leak() -> void:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.albedo_color = Color(1.0, 0.16, 0.08, 0.85)
	m.no_depth_test = false
	for e: Array in [[Vector3(-2.995, 1.075, -1.155), Vector2(0.012, 2.15)], [Vector3(-2.995, 1.075, -0.045), Vector2(0.012, 2.15)],
			[Vector3(-2.995, 2.152, -0.6), Vector2(1.1, 0.012)]]:
		var q := MeshInstance3D.new()
		var qm := QuadMesh.new()
		qm.size = e[1]
		q.mesh = qm
		q.material_override = m
		q.rotation.y = deg_to_rad(90)
		q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		room.add_child(q)
		q.position = e[0]
		q.visible = false
		_leak.append(q)


func _update_red_leak() -> void:
	var on: bool = logic.state["power_on"] and not logic.state["shelf_open"]
	for q in _leak:
		q.visible = on


func part(model: String, name: String) -> Node3D:
	return ModelUtil.find((room.get("models") as Dictionary).get(model), name)


func model(id: String) -> Node3D:
	return (room.get("models") as Dictionary).get(id)


func _record_rest() -> void:
	for m: Node3D in (room.get("models") as Dictionary).values():
		_record(m)


func _record(n: Node) -> void:
	if n is Node3D and (str(n.name).begins_with("IA_") or str(n.name) in ["main_handle", "dial_needle", "sculpture_ring", "sculpture_rod", "lens_installed", "valve_installed", "socket_lens", "mirror", "echo_head"]):
		rest[n] = (n as Node3D).transform
	for c in n.get_children():
		_record(c)


func _attach_bookshelf_children() -> void:
	# The gear box rides on the swinging bookcase.
	pass


func _spawn_item(spot: String, item_model: String, parent: Node3D, offset: Vector3, yaw: float = 0.0, scale: float = 1.0) -> void:
	if parent == null:
		return
	var n := ModelUtil.spawn(item_model, parent, Transform3D(Basis(Vector3.UP, deg_to_rad(yaw)).scaled(Vector3.ONE * scale), offset), "none")
	if n == null:
		return
	n.name = "Item_" + spot
	var aabb := AABB()
	for mi in ModelUtil.find_meshes(n):
		aabb = aabb.merge(mi.get_aabb()) if aabb.size != Vector3.ZERO else mi.get_aabb()
	var body := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = (aabb.size + Vector3.ONE * 0.03).max(Vector3.ONE * 0.06)
	cs.shape = box
	cs.position = aabb.get_center()
	body.add_child(cs)
	body.set_meta("part", "Item_" + spot)
	n.add_child(body)
	_items[spot] = n


func _spawn_container_items() -> void:
	_spawn_item("drawer_lamp", "uv_lamp", part("desk", "IA_drawer_top"), Vector3(0.05, 0.035, -0.18), 80.0)
	var anchor := part("gear_box", "battery_anchor")
	if anchor:
		_spawn_item("box_cell", "battery_cell", anchor, Vector3.ZERO, 0.0)
	else:
		_spawn_item("box_cell", "battery_cell", model("gear_box"), Vector3(0, 0.05, 0), 0.0)
		var cell: Node3D = _items.get("box_cell")
		if cell:
			cell.basis = Basis(Vector3.BACK, -PI / 2)
	var safe := model("wall_safe")
	_spawn_item("safe_key", "brass_key", safe, Vector3(-0.12, -0.1, -0.12), 30.0)
	_spawn_item("safe_lens", "crystal_lens", safe, Vector3(0.0, -0.08, -0.16), 0.0)
	_spawn_item("safe_letter", "letter", safe, Vector3(0.1, -0.11, -0.14), -15.0)
	_spawn_item("safe_valve", "radio_valve", safe, Vector3(0.0, 0.08, -0.15), 0.0)
	_spawn_item("compartment_handle", "breaker_handle", part("desk", "IA_compartment"), Vector3(-0.08, 0.03, 0.0), 90.0)
	_spawn_item("compartment_photo", "photo_print", part("desk", "IA_compartment"), Vector3(-0.2, 0.022, 0.0), 90.0)
	var sl := model("shadow_lock")
	var spot := part("shadow_lock", "cabinet_item_spot")
	var cab := part("shadow_lock", "IA_cabinet_door")
	if sl and spot:
		_spawn_item("cabinet_mirror", "mirror_item", spot, Vector3.ZERO, 0.0)
	elif sl and cab:
		_spawn_item("cabinet_mirror", "mirror_item", sl, cab.position + Vector3(0.178, 0.0, -0.101), 0.0)


func _build_safe_display() -> void:
	var disp := part("wall_safe", "safe_display")
	_safe_label = Label3D.new()
	_safe_label.font_size = 48
	_safe_label.pixel_size = 0.0006
	_safe_label.modulate = Color("ff9a3c")
	_safe_label.outline_size = 0
	_safe_label.no_depth_test = false
	_safe_label.shaded = false
	if disp:
		disp.add_child(_safe_label)
		var aabb := (disp as MeshInstance3D).get_aabb() if disp is MeshInstance3D else AABB()
		_safe_label.position = aabb.get_center() + Vector3(0, 0, aabb.size.z * 0.5 + 0.003)
	else:
		room.add_child(_safe_label)
		_safe_label.global_position = Vector3(2.2, 1.48, 2.47)
		_safe_label.rotation.y = PI


# ====================================================================== main entry
func apply_state(animated: bool) -> void:
	var s := logic.state
	# P1 drawer
	for i in 4:
		_rot(part("desk", "IA_drawer_digit_%d" % i), WHEEL_AXIS, WHEEL_SIGN * (int(s["drawer"][i]) * WHEEL_STEP_DEG - WHEEL_VIEW_TILT_DEG), animated, 0.12)
	_slide(part("desk", "IA_drawer_top"), Vector3(0, 0, DRAWER_TRAVEL if s["drawer_open"] else 0.0), animated)
	# P2 gear box
	for i in 3:
		_rot(part("gear_box", "IA_gear_%d" % i), Vector3.UP, GEAR_SIGN * int(s["gears"][i]) * 60.0, animated, 0.25)
	_rot(part("gear_box", "IA_box_lid"), Vector3.RIGHT, LID_OPEN_DEG if s["box_open"] else 0.0, animated, 0.8)
	# notebook on desk
	var nb := model("notebook")
	if nb:
		nb.visible = not s["taken"].get("notebook", false)
	# P4 safe
	_rot(part("wall_safe", "IA_safe_handle"), Vector3.BACK, -90.0 if s["safe_open"] else 0.0, animated, 0.5)
	_slide(part("wall_safe", "safe_bolts"), Vector3(-0.024 if s["safe_open"] else 0.0, 0, 0), animated)
	_rot(part("wall_safe", "IA_safe_door"), Vector3.UP, SAFE_DOOR_OPEN_DEG if s["safe_open"] else 0.0, animated, 1.2)
	if _safe_label:
		var inp: String = s["safe_input"]
		_safe_label.text = "OPEN" if s["safe_open"] else (" ".join(inp.split("")) + " _".repeat(4 - inp.length())).strip_edges()
	# P5 desk compartment
	_slide(part("desk", "IA_rosette"), Vector3(-0.006 if s["rosette"] else 0.0, 0, 0), animated)
	_slide(part("desk", "IA_secret_panel"), Vector3(0, -0.06 if s["rosette"] else 0.0, 0), animated)
	_slide(part("desk", "IA_compartment"), Vector3(0.20 if s["compartment_open"] else 0.0, 0, 0), animated)
	# items in containers
	for spot: String in _items:
		(_items[spot] as Node3D).visible = not s["taken"].get(spot, false)
	# P6 panel
	for i in 5:
		_rot(part("panel7", "IA_switch_%d" % i), Vector3.RIGHT, SWITCH_ON_DEG if int(s["switches"][i]) == 1 else SWITCH_OFF_DEG, animated, 0.12, true)
	var handle := part("panel7", "main_handle")
	if handle:
		handle.visible = s["handle_installed"]
	_rot(part("panel7", "IA_main_lever"), Vector3.RIGHT, LEVER_ON_DEG if (s["main_on"] or s["power_on"]) else LEVER_OFF_DEG, animated, 0.2, true)
	_rot(part("panel7", "gauge_needle"), Vector3.BACK, -79.0 if (s["main_on"] or s["power_on"]) else 0.0, animated, 1.4)
	var lamps := logic.lamps()
	for j in 4:
		_lamp(part("panel7", "lamp_%d" % j), lamps[j] == 1)
	# P7/P8 radio
	var valve := part("radio", "valve_installed")
	if valve:
		valve.visible = s["valve_installed"]
	var heater := part("radio", "valve_heater") as MeshInstance3D
	if heater:
		ModelUtil.set_emission(heater, s["valve_installed"] and s["power_on"], Color("ff8a2a"), 2.5)
	_rot(part("radio", "IA_tuning_knob"), Vector3.BACK, -9.0 * (int(s["dial"]) - Lab7Logic.RADIO_START), animated, 0.15)
	_rot(part("radio", "IA_radio_hatch"), Vector3.RIGHT, -70.0 if radio_hatch_open else 0.0, animated, 0.4)
	_update_radio(animated)
	# P9 bookcase door (pivot node at its front-north edge, swings into the lab)
	_rot(model("bookshelf_pivot"), Vector3.UP, SHELF_OPEN_DEG if s["shelf_open"] else 0.0, animated, 2.2, false, true)
	# P10 shadow sculpture, cabinet, socket
	_rot(part("shadow_lock", "sculpture_ring"), Vector3.UP, (int(s["shadow"][0]) - 2) * 30.0, animated, 0.35)
	_rot(part("shadow_lock", "sculpture_rod"), Vector3.BACK, (int(s["shadow"][1]) - 2) * 30.0, animated, 0.35)
	_rot(part("shadow_lock", "IA_cabinet_door"), Vector3.UP, CABINET_OPEN_DEG if s["cabinet_open"] else 0.0, animated, 0.9)
	var sock := part("shadow_lock", "socket_lens")
	if sock:
		sock.visible = s["lens_at"] == "socket"
		_glow(sock, s["emblem_recorded"])
	# P11 projector
	var lens := part("lumen_projector", "lens_installed")
	if lens:
		lens.visible = s["lens_at"] == "projector"
		_glow(lens, s["emblem_recorded"] and s["lens_at"] == "projector")
	for i in 3:
		_rot(part("lumen_projector", "IA_ring_%d" % i), Vector3.BACK, RING_SIGN * (int(s["rings"][i]) - 5) * 60.0, animated, 0.25)
	_rot(part("lumen_projector", "IA_projector_lever"), Vector3.RIGHT, 35.0 if s["beam_on"] else 0.0, animated, 0.3)
	# P12 mirrors
	_rot(part("mirror_stand", "IA_mirror_mount"), Vector3.UP, 90.0 - int(s["mirrors"][0]) * 45.0, animated, 0.35)
	_rot(part("mirror_stand_b", "IA_mirror_mount"), Vector3.UP, 90.0 - int(s["mirrors"][1]) * 45.0, animated, 0.35)
	var mb := part("mirror_stand_b", "mirror")
	if mb:
		mb.visible = s["mirror_b_mounted"]
	_update_beam()
	_update_red_leak()
	# door + maglock
	var mag := part("door_lab7", "maglock_lamp") as MeshInstance3D
	if mag:
		ModelUtil.set_emission(mag, true, Color("5dff8a") if s["door_open"] else Color("ff3b2f"), 3.0)
	var ml: OmniLight3D = (room.get("lights") as Dictionary).get("maglock")
	if ml:
		ml.light_color = Color("5dff8a") if s["door_open"] else Color("ff3b2f")
	if s["complete"] and not _door_opened:
		open_door(false)


# ====================================================================== helpers
func _key(n: Node, prop: String) -> String:
	return str(n.get_instance_id()) + prop


func _rot(n: Node3D, axis: Vector3, deg: float, animated: bool, dur: float, _bounce: bool = false, from_current: bool = false) -> void:
	if n == null:
		return
	if not rest.has(n):
		rest[n] = n.transform
	var base: Transform3D = rest[n]
	var target := Transform3D(base.basis * Basis(axis.normalized(), deg_to_rad(deg)), base.origin)
	_to(n, target, animated, dur)


func _slide(n: Node3D, offset: Vector3, animated: bool) -> void:
	if n == null:
		return
	if not rest.has(n):
		rest[n] = n.transform
	var base: Transform3D = rest[n]
	_to(n, Transform3D(base.basis, base.origin + base.basis * offset), animated, 0.6)


func _to(n: Node3D, target: Transform3D, animated: bool, dur: float) -> void:
	var k := _key(n, "xf")
	if _tweens.has(k) and (_tweens[k] as Tween).is_valid():
		(_tweens[k] as Tween).kill()
	if not animated or n.transform.is_equal_approx(target):
		n.transform = target
		return
	var from := n.transform
	var fq := from.basis.get_rotation_quaternion()
	var tq := target.basis.get_rotation_quaternion()
	var sc := from.basis.get_scale()
	var tw := room.create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tw.tween_method(func(t: float) -> void:
		n.transform = Transform3D(Basis(fq.slerp(tq, t)).scaled(sc), from.origin.lerp(target.origin, t)), 0.0, 1.0, dur)
	_tweens[k] = tw


func _lamp(mi: Node3D, on: bool) -> void:
	if mi == null or not mi is MeshInstance3D:
		return
	ModelUtil.set_emission(mi as MeshInstance3D, on, Color("ffb46b"), 3.5)


func _glow(n: Node3D, on: bool) -> void:
	for mi in ModelUtil.find_meshes(n):
		var m := StandardMaterial3D.new()
		m.albedo_color = Color(0.81, 0.96, 1.0, 0.55)
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.roughness = 0.05
		m.emission_enabled = on
		m.emission = Color("cff6ff")
		m.emission_energy_multiplier = 2.5
		mi.material_override = m if on else null


func set_power_emissives(on: bool) -> void:
	for id in ["pendant_lamp", "pendant_lamp_2", "desk_lamp"]:
		var b := part(id, "bulb") as MeshInstance3D
		if b:
			ModelUtil.set_emission(b, on or id == "desk_lamp", Color("ffc58a"), 4.0)
	var dial := part("radio", "radio_dial") as MeshInstance3D
	if dial:
		ModelUtil.set_emission(dial, on)
	var spot_bulb := part("shadow_lock", "spot_bulb") as MeshInstance3D
	if spot_bulb:
		ModelUtil.set_emission(spot_bulb, on, Color("fff1d6"), 4.0)
	var red_bulb := part("room_lab7", "darkroom_bulb") as MeshInstance3D
	if red_bulb:
		ModelUtil.set_emission(red_bulb, on, Color("ff2a1a"), 3.0)


# ====================================================================== radio
func _update_radio(animated: bool) -> void:
	var needle := part("radio", "dial_needle")
	var dial := part("radio", "radio_dial") as MeshInstance3D
	if needle and dial and rest.has(needle):
		var aabb := dial.get_aabb()
		var u := 0.06 + 0.88 * float(logic.state["dial"]) / 100.0
		var left := aabb.position.x
		var width := aabb.size.x
		var base: Transform3D = rest[needle]
		var rest_u := 0.06
		var dx := (u - rest_u) * width
		var target := Transform3D(base.basis, base.origin + Vector3(dx, 0, 0))
		_to(needle, target, animated, 0.15)
		left = left # keep for clarity
	var eye := part("radio", "magic_eye") as MeshInstance3D
	if eye:
		var c := logic.radio_clarity()
		ModelUtil.set_emission(eye, c > 0.0, Color(0.35 + 0.2 * c, 1.0, 0.5), 0.6 + 3.0 * c)


var _beacon_player: AudioStreamPlayer
var _static_player: AudioStreamPlayer


func radio_tick() -> void:
	AudioManager.sfx("ring_turn", -10.0, 1.6)


func _process(_delta: float) -> void:
	_radio_audio()


func _radio_audio() -> void:
	# Static fades into Strand's beacon as the dial nears 41 m; the magic eye pulses with the beacon.
	var status := logic.radio_status()
	if _static_player == null:
		_static_player = AudioStreamPlayer.new()
		_static_player.bus = "SFX"
		var st := AudioManager.stream("ambience", "amb_lab_dark")
		_static_player.stream = _make_noise()
		room.add_child(_static_player)
	if status == "dead":
		if _static_player.playing:
			_static_player.stop()
		return
	var clarity := logic.radio_clarity()
	var near_radio := (room.get("cam") as RoomCamera).current() in ["radio", "bench"]
	if not _static_player.playing:
		_static_player.play()
	_static_player.volume_db = linear_to_db(maxf(0.0001, (1.0 - clarity) * (0.5 if near_radio else 0.12)))
	# beacon pulses 2-6-3, generated as short beeps on a 7.2 s cycle
	var t := fmod(Time.get_ticks_msec() / 1000.0, 7.2)
	var on := _beacon_on(t)
	var eye := part("radio", "magic_eye") as MeshInstance3D
	if clarity > 0.0 and eye:
		ModelUtil.set_emission(eye, true, Color(0.4, 1.0, 0.55), (0.6 + 3.0 * clarity) * (1.6 if on else 0.6))
	if on and clarity > 0.05 and not _beep_playing:
		_beep(clarity * (1.0 if near_radio else 0.3))
	_beep_playing = on


var _beep_playing := false


static func _beacon_on(t: float) -> bool:
	# groups: 2 pulses @0.0, 6 pulses @1.4, 3 pulses @4.6 ; pulse 0.18 s on, 0.17 off
	var groups := [[0.0, 2], [1.4, 6], [4.6, 3]]
	for g: Array in groups:
		var start: float = g[0]
		var n: int = g[1]
		if t >= start and t < start + n * 0.35:
			return fmod(t - start, 0.35) < 0.18
	return false


func _beep(level: float) -> void:
	var p := AudioStreamPlayer.new()
	p.bus = "SFX"
	var gen := AudioStreamGenerator.new()
	gen.mix_rate = 22050.0
	gen.buffer_length = 0.25
	p.stream = gen
	p.volume_db = linear_to_db(maxf(0.0001, level * 0.5))
	room.add_child(p)
	p.play()
	var pb := p.get_stream_playback() as AudioStreamGeneratorPlayback
	var frames := int(22050 * 0.16)
	for i in frames:
		var env := minf(1.0, minf(i / 200.0, (frames - i) / 400.0))
		var v := sin(TAU * 880.0 * i / 22050.0) * 0.5 * env
		pb.push_frame(Vector2(v, v))
	room.get_tree().create_timer(0.3).timeout.connect(p.queue_free)


func _make_noise() -> AudioStreamWAV:
	var rate := 22050
	var n := rate * 2
	var data := PackedByteArray()
	data.resize(n * 2)
	var rng := RandomNumberGenerator.new()
	rng.seed = 41
	var lp := 0.0
	for i in n:
		lp = lp * 0.6 + rng.randf_range(-1.0, 1.0) * 0.4
		var crackle := 3.0 if rng.randf() < 0.002 else 1.0
		var v := clampi(int(lp * 9000.0 * crackle), -32767, 32767)
		data.encode_s16(i * 2, v)
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = rate
	w.data = data
	w.loop_mode = AudioStreamWAV.LOOP_FORWARD
	w.loop_end = n
	return w


# ====================================================================== books, beam, door, echo
func tilt_book(n: int) -> void:
	var b := part("bookshelf", "IA_book_%d" % n)
	if b == null:
		return
	if not rest.has(b):
		rest[b] = b.transform
	var base: Transform3D = rest[b]
	var out := Transform3D(base.basis * Basis(Vector3.RIGHT, deg_to_rad(BOOK_TILT_DEG)), base.origin)
	var tw := room.create_tween()
	tw.tween_property(b, "transform", out, 0.18)
	tw.tween_interval(0.25)
	tw.tween_property(b, "transform", base, 0.3)


func scatter_flash() -> void:
	var l: OmniLight3D = (room.get("lights") as Dictionary)["lumen"]
	var tw := room.create_tween()
	tw.tween_property(l, "light_energy", 2.5, 0.08)
	tw.tween_property(l, "light_energy", 0.3, 0.12)
	tw.tween_property(l, "light_energy", 1.6, 0.06)
	tw.tween_property(l, "light_energy", 0.0, 0.5)


func _update_beam() -> void:
	for c in _beam_root.get_children():
		c.queue_free()
	var lumen: OmniLight3D = (room.get("lights") as Dictionary)["lumen"]
	if not logic.state["beam_on"] and not logic.state["door_open"]:
		lumen.light_energy = 0.0
		return
	lumen.light_energy = 1.4
	var tr := logic.trace_beam()
	var pts: PackedVector2Array = tr["points"]
	var y := 1.15
	var bm := ShaderMaterial.new()
	bm.shader = load("res://src/fx/lumen_beam.gdshader")
	for i in pts.size() - 1:
		var a := Vector3(pts[i].x, y, pts[i].y)
		var b := Vector3(pts[i + 1].x, y, pts[i + 1].y)
		if i == 0:
			a.x += 0.32 # start at the projector's lens, not its pivot
		var len := a.distance_to(b)
		if len < 0.01:
			continue
		var mi := MeshInstance3D.new()
		var cyl := CylinderMesh.new()
		cyl.top_radius = 0.018
		cyl.bottom_radius = 0.022
		cyl.height = len
		cyl.radial_segments = 12
		cyl.rings = 1
		cyl.cap_top = false
		cyl.cap_bottom = false
		mi.mesh = cyl
		mi.material_override = bm
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_beam_root.add_child(mi)
		var mid := (a + b) * 0.5
		mi.global_position = mid
		var dir := (b - a).normalized()
		mi.global_basis = Basis(Quaternion(Vector3.UP, dir))
		var hit := OmniLight3D.new()
		hit.light_color = Color("cff6ff")
		hit.light_energy = 0.9
		hit.omni_range = 0.9
		_beam_root.add_child(hit)
		hit.global_position = b - dir * 0.05
	# projected emblem on the light lock
	if tr["end"] == "lock" and logic.state["emblem_recorded"]:
		var d := Decal.new()
		d.texture_albedo = load("res://assets/textures/decals/wall_emblem.png")
		d.texture_emission = d.texture_albedo
		d.emission_energy = 3.0
		d.modulate = Color("cff6ff")
		d.size = Vector3(0.17, 0.1, 0.17)
		_beam_root.add_child(d)
		d.global_position = Vector3(2.948, y, 0.12)
		d.global_rotation = Vector3(0, 0, deg_to_rad(90))


## Finale flashback: "for a moment the laboratory is 1979 again" — Leyla's desk is closed up as she
## left it (the echo sits where the open drawer would be). `false` restores the present.
func flashback_1979(on: bool) -> void:
	if on:
		_slide(part("desk", "IA_drawer_top"), Vector3.ZERO, true)
		_slide(part("desk", "IA_compartment"), Vector3.ZERO, true)
	else:
		apply_state(true)


func open_door(animated: bool = true) -> void:
	_door_opened = true
	_rot(part("door_lab7", "IA_door_leaf"), Vector3.UP, DOOR_OPEN_DEG, animated, 2.4)


func fade_echo(echo: Node3D, from: float, to: float, dur: float) -> void:
	var meshes := ModelUtil.find_meshes(echo)
	room.create_tween().tween_method(func(v: float) -> void:
		for mi in meshes:
			var m := mi.material_override as ShaderMaterial
			if m:
				m.set_shader_parameter("intensity", v), from, to, dur)
