class_name ArchiveLift
extends RefCounted
## Chapter 2 expansion N7, the book lift (docs/CHAPTER2_EXPANSION.md section 8, docs/models/ch2_exp.md "book_lift_cage").
## One ArchiveLift renders ONE site of the lift: the Pump Room's niche (floor -1) or the Reading Gallery's wall (floor +1).
## The cage model is the same everywhere; it is shown at the site whose floor is the logic's `lift_floor`, and it rides
## up or down out of view when the lift moves. What it draws and forwards (it holds no puzzle logic):
## - the load plate "LOAD n" (this game's `v_load`) on the cage, and a needle that tells heavy from light;
## - four iron weights 1, 2, 4, 8 (tap one to hang it on the counterweight stand or lift it off: `n7_toggle_weight`): hung
##   ones on the stand's pegs, loose ones standing in a row on the floor in front of it. The cage's own hook sits in a gap
##   too narrow for the weights (the niche is 0.1 m wider than the cage), so the stand carries them; it is only built at
##   the pump niche, where they are handled;
## - the cage gate (open while the cage is here), the three floor buttons inside the cage (flask, book, lamp = floors -1, 0,
##   +1) and the same three on a call plate beside the shaft (`n7_call`);
## - the ride: pressing another floor's button while the cage is here rides it: the cage rises or sinks out of view, the
##   fade takes the player to that floor's room (pump / hall / gallery) and the bell rings (`lift_moved`).

const FLOOR_ROOM := {-1: "pump", 0: "hall", 1: "gallery"}
const FLOOR_SUFFIX := {-1: "m1", 0: "z0", 1: "p1"}
const BTN_FLOOR := {"IA_btn_flask": -1, "IA_btn_book": 0, "IA_btn_lamp": 1}
const FLOOR_ORDER: Array[int] = [-1, 0, 1]
const RISE := 3.6 # metres between floors in the shaft
const WEIGHT_MODELS := ["weight_1", "weight_2", "weight_4", "weight_8"]
const NEEDLE_MAX_DEG := 70.0

var room: Node3D
var zones: ArchiveZones
var logic: ArchiveLogic
var rig: ArchiveRig
var floor_no := -1
var root: Node3D
var cage: Node3D
var zone_id := "pump"
var views: Dictionary = {} # "door", "weights", "panel" -> camera view id
var base_pos := Vector3.ZERO
var weights: Array[Node3D] = []
var rest_pos: Array[Vector3] = [] # where each loose weight stands (zone coordinates); empty = no weights at this site
var _pegs: Array[Vector3] = [] # the stand's four pegs (zone coordinates)
var _hung: Array[bool] = [false, false, false, false]
var _shown_floor := -9 # the cage floor last drawn
var _dy := 0.0
var _dy_tween: Tween
var _gate_tween: Tween
var _ride_to := -9
var _call_buttons: Array[Node3D] = []
var _plate_mat: StandardMaterial3D


func _init(r: Node3D, z: ArchiveZones) -> void:
	room = r
	zones = z
	logic = r.get("logic")
	rig = ArchiveRig.new(r)


func suffix() -> String:
	return str(FLOOR_SUFFIX[floor_no])


# ====================================================================== construction
## `cage_model` is the spawned book_lift_cage under `zone_root` (its position is the cage's place on this floor);
## `stand_at` the foot of the counterweight stand (zone coordinates, it faces +X; a site without one has no weights).
func add_site(floor_n: int, zone: String, zone_root: Node3D, cage_model: Node3D, view_ids: Dictionary, stand_at: Variant, call_plate: Transform3D) -> void:
	floor_no = floor_n
	zone_id = zone
	root = zone_root
	cage = cage_model
	views = view_ids
	base_pos = cage.position
	cage.set_meta("hotspot", "lift_" + suffix())
	_load_plate()
	if stand_at is Vector3:
		_build_stand(stand_at as Vector3)
		_build_weights()
	_build_call_plate(call_plate)
	var hs := {"lift_" + suffix(): views["door"], "lift_w_" + suffix(): views["weights"], "lift_b_" + suffix(): views["panel"]}
	var caps := {views["door"]: "obj2x.lift", views["weights"]: "obj2x.counterweight", views["panel"]: "obj2x.lift"}
	zones.register(zone, [views["door"], views["weights"], views["panel"]], hs, {}, caps)
	# the cage's buttons answer from the panel view; its gate, plate and body from the door view
	for n in ["IA_btn_flask", "IA_btn_book", "IA_btn_lamp", "needle_lift"]:
		_set_part_hotspot(n, "lift_b_" + suffix())
	apply_state(false)


func _set_part_hotspot(part_name: String, hs: String) -> void:
	var n := ModelUtil.find(cage, part_name)
	if n == null:
		return
	n.set_meta("hotspot", hs)
	for b in n.get_children():
		if b is StaticBody3D:
			(b as StaticBody3D).set_meta("hotspot", hs)


func _load_plate() -> void:
	var plate := ModelUtil.find(cage, "load_plate") as MeshInstance3D
	if plate == null:
		return
	_plate_mat = StandardMaterial3D.new()
	_plate_mat.albedo_texture = ArchiveUpperArt.lift_plate(logic.lift_load())
	_plate_mat.roughness = 0.5
	_plate_mat.metallic_specular = 0.3
	plate.material_override = _plate_mat
	plate.set_meta("hotspot", "lift_" + suffix())


## The counterweight stand: two posts and a crossbar at 1.5 m with four pegs, standing against the north wall beside the niche
## (its bar runs along +X, the pegs point toward +Z, into the room); the loose weights stand in a row on the floor in front.
func _build_stand(at: Vector3) -> void:
	var iron := ModelUtil.load_material("M_Iron_Rust")
	var dark := ModelUtil.load_material("M_Steel_Dark")
	var holder := Node3D.new()
	holder.name = "counterweight_stand"
	holder.position = at
	root.add_child(holder)
	var x0 := -0.27
	var x1 := 1.27
	for x in [x0, x1]:
		var post := MeshInstance3D.new()
		var pm := CylinderMesh.new()
		pm.top_radius = 0.035
		pm.bottom_radius = 0.04
		pm.height = 1.56
		post.mesh = pm
		post.position = Vector3(x, 0.78, 0)
		post.material_override = iron
		post.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		holder.add_child(post)
	var bar := MeshInstance3D.new()
	var bm := CylinderMesh.new()
	bm.top_radius = 0.025
	bm.bottom_radius = 0.025
	bm.height = x1 - x0 + 0.16
	bar.mesh = bm
	bar.rotation_degrees.z = 90.0
	bar.position = Vector3((x0 + x1) * 0.5, 1.56, 0)
	bar.material_override = dark
	bar.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	holder.add_child(bar)
	_pegs.clear()
	rest_pos.clear()
	var xs := [0.0, 0.34, 0.74, 1.14]
	for i in 4:
		var peg := MeshInstance3D.new()
		var gm := CylinderMesh.new()
		gm.top_radius = 0.016
		gm.bottom_radius = 0.016
		gm.height = 0.12
		peg.mesh = gm
		peg.rotation_degrees.x = 90.0
		peg.position = Vector3(float(xs[i]), 1.56, 0.06)
		peg.material_override = dark
		peg.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		holder.add_child(peg)
		_pegs.append(at + Vector3(float(xs[i]), 1.56, 0.06))
		rest_pos.append(at + Vector3(float(xs[i]), 0, 0.72))


func _build_weights() -> void:
	var face := Basis.IDENTITY # the disc's axis (model Z) points along +Z: its face looks into the room
	for i in 4:
		var w := ModelUtil.spawn(WEIGHT_MODELS[i], root, Transform3D(face, _pegs[i]), "none")
		if w == null:
			weights.append(null)
			continue
		w.name = "lift_weight_%d" % i
		(room.get("models") as Dictionary)[w.name] = w # QA taps find a part through the room's model table
		var aabb := ArchiveRig.local_aabb(w)
		w.set_meta("top", aabb.end.y)
		w.set_meta("bottom", -aabb.position.y)
		var r := maxf(aabb.size.y, aabb.size.x) * 0.5
		for side in [1.0, -1.0]:
			rig.numeral(w, str(ArchiveExpData.WEIGHTS[i]), Vector3(0, (aabb.position.y + aabb.end.y) * 0.5 - r * 0.05, (aabb.end.z + 0.002) if side > 0.0 else (aabb.position.z - 0.002)),
				r * 1.15, Color("f2ead2"), Vector3(0, 0 if side > 0.0 else 180.0, 0))
		var body := StaticBody3D.new()
		var cs := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = Vector3(aabb.size.x + 0.06, aabb.size.y + 0.06, maxf(aabb.size.z, 0.04) + 0.05)
		cs.shape = box
		cs.position = aabb.get_center()
		body.add_child(cs)
		body.set_meta("part", "Weight_%d" % i)
		body.set_meta("hotspot", "lift_w_" + suffix())
		w.add_child(body)
		w.set_meta("hotspot", "lift_w_" + suffix())
		for mi in ModelUtil.find_meshes(w):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		weights.append(w)


## The call plate on the wall beside the shaft: three brass buttons with the floor pictograms (the cage has the same inside).
func _build_call_plate(xf: Transform3D) -> void:
	var plate := Node3D.new()
	plate.name = "lift_call_plate_" + suffix()
	plate.transform = xf
	root.add_child(plate)
	(room.get("models") as Dictionary)[plate.name] = plate
	var back := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.40, 0.15, 0.025)
	back.mesh = bm
	back.material_override = ModelUtil.load_material("M_Steel_Dark")
	back.position = Vector3(0, 0, 0.0125)
	back.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	plate.add_child(back)
	# the load notice above the buttons: the cage's own plate is a hand-span wide, this one is read from across the room
	var notice := ArchiveRig.picture(plate, ArchiveUpperArt.lift_plate(logic.lift_load()), Vector2(0.40, 0.20), Vector3(0, 0.2, 0.017), Color(0.92, 0.88, 0.8), false)
	notice.name = "load_notice"
	room.call("add_tap_area", notice, Vector3(0.42, 0.22, 0.05), "lift_" + suffix(), "load_plate", Vector3.ZERO)
	for i in 3:
		var x := -0.125 + 0.125 * i
		var btn := Node3D.new()
		btn.name = "Call_%d" % i
		btn.position = Vector3(x, -0.005, 0.03)
		plate.add_child(btn)
		var cyl := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.032
		cm.bottom_radius = 0.034
		cm.height = 0.02
		cyl.mesh = cm
		cyl.rotation_degrees.x = 90.0
		cyl.material_override = ModelUtil.load_material("M_Brass_Aged")
		cyl.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		btn.add_child(cyl)
		ArchiveRig.picture(btn, ArchiveUpperArt.lift_icon(i), Vector2(0.05, 0.05), Vector3(0, 0, 0.0115), Color(0.18, 0.14, 0.1), true)
		room.call("add_tap_area", btn, Vector3(0.1, 0.12, 0.08), "lift_b_" + suffix(), "Call_%d" % i, Vector3(0, 0, 0.02))
		_call_buttons.append(btn)


# ====================================================================== state
func apply_state(animated: bool) -> void:
	var s := logic.state
	var cage_floor := int(s["lift_floor"])
	var here := cage_floor == floor_no
	_apply_weights(animated)
	var gate := ModelUtil.find(cage, "IA_gate")
	var needle := ModelUtil.find(cage, "needle_lift")
	var diff := logic.counterweight() - logic.lift_load()
	rig.rot(needle, Vector3.BACK, clampf(diff * 9.0, -NEEDLE_MAX_DEG, NEEDLE_MAX_DEG) if int(s["lift_floor"]) == floor_no else 0.0, animated, 0.5)
	_gate(gate, here, animated and zones.current == zone_id)
	if cage_floor == _shown_floor:
		if _shown_floor == -9:
			_set_dy(0.0 if here else _off_dy(cage_floor))
			cage.visible = here
		return
	var prev := _shown_floor
	_shown_floor = cage_floor
	var visible_now := zones.current == zone_id
	if animated and visible_now and prev != -9 and (prev == floor_no or here):
		cage.visible = true
		if prev == floor_no: # leaves: rises or sinks out of view
			_tween_dy(0.0, _off_dy(cage_floor), 1.3, true)
		else: # arrives from where it was
			_set_dy(_off_dy(prev))
			_tween_dy(_off_dy(prev), 0.0, 1.3, false)
	else:
		_set_dy(0.0 if here else _off_dy(cage_floor))
		cage.visible = here


## The scissor gate folds up against the cage's left post when the cage is here (a part that folds is scaled, not slid out).
func _gate(gate: Node3D, open: bool, animated: bool) -> void:
	if gate == null:
		return
	var rest := rig._rest(gate)
	var x := rest.origin.x - 0.406 if open else rest.origin.x
	var sx := 0.3 if open else 1.0
	if _gate_tween != null and _gate_tween.is_valid():
		_gate_tween.kill()
	if not animated:
		gate.position.x = x
		gate.scale.x = sx
		return
	_gate_tween = room.create_tween().set_parallel(true).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_gate_tween.tween_property(gate, "position:x", x, 0.7)
	_gate_tween.tween_property(gate, "scale:x", sx, 0.7)


## How far the cage stands from this site when it is at `f` (it keeps riding along the shaft).
func _off_dy(f: int) -> float:
	return float(f - floor_no) * RISE


func _tween_dy(from: float, to: float, seconds: float, hide_after: bool) -> void:
	if _dy_tween != null and _dy_tween.is_valid():
		_dy_tween.kill()
	_dy_tween = room.create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_dy_tween.tween_method(_set_dy, from, to, seconds)
	if hide_after:
		_dy_tween.tween_callback(func() -> void:
			if is_instance_valid(cage):
				cage.visible = int(logic.state["lift_floor"]) == floor_no)


## Moves the cage (and the weights hung on it) to `dy` above or below its place on this floor.
func _set_dy(dy: float) -> void:
	_dy = dy
	cage.position = base_pos + Vector3(0, dy, 0)


func _hang_pos(i: int) -> Vector3:
	return _pegs[i] - Vector3(0, float(weights[i].get_meta("top")), 0)


func _rest_pos_of(i: int) -> Vector3:
	return rest_pos[i] + Vector3(0, float(weights[i].get_meta("bottom")) + 0.002, 0)


func _apply_weights(animated: bool) -> void:
	var s := logic.state
	for i in weights.size():
		var w := weights[i]
		if w == null:
			continue
		var on := int(s["weights"][i]) == 1
		var changed := on != _hung[i]
		_hung[i] = on
		var target := _hang_pos(i) if on else _rest_pos_of(i)
		if changed and animated and zones.current == zone_id:
			_fly(w, target)
		else:
			w.position = target


func _fly(w: Node3D, to: Vector3) -> void:
	var from := w.position
	var tw := room.create_tween()
	tw.tween_method(func(t: float) -> void:
		if is_instance_valid(w):
			w.position = from.lerp(to, t) + Vector3(0, 0.12 * sin(t * PI), 0), 0.0, 1.0, 0.45).set_trans(Tween.TRANS_SINE)


# ====================================================================== taps
## -> true when the tap was ours.
func interact(hs: String, part: String) -> bool:
	var cam: RoomCamera = room.get("cam")
	var cur := cam.current()
	if hs == "lift_" + suffix():
		if cur != views["door"]:
			cam.go(views["door"])
		elif part == "load_plate":
			(room.get("hud") as Node).call("_show_zoom", _plate_mat.albedo_texture, room.tr("obj2x.lift"))
		elif part == "IA_hook":
			_say("obj2x.counterweight")
		else:
			_say("obj2x.lift")
		return true
	if hs == "lift_w_" + suffix():
		if part.begins_with("Weight_"):
			logic.n7_toggle_weight(int(part.substr(7)))
		else:
			_say("obj2x.counterweight")
		return true
	if hs == "lift_b_" + suffix():
		var k := -9
		if BTN_FLOOR.has(part):
			k = int(BTN_FLOOR[part])
		elif part.begins_with("Call_"):
			k = FLOOR_ORDER[int(part.substr(5))]
		if k == -9:
			_say("obj2x.lift")
		else:
			press(k, part)
		return true
	return false


func press(k: int, part: String) -> void:
	_press_anim(part)
	var here := int(logic.state["lift_floor"]) == floor_no
	if k == int(logic.state["lift_floor"]):
		ArchiveZones.cue("c2x_lift_bell", -6.0)
		return
	_ride_to = k if here else -9
	var ev := logic.n7_call(k)
	if not ev.has("lift_moved:%d" % k):
		_ride_to = -9


func _press_anim(part: String) -> void:
	var btn: Node3D = ModelUtil.find(cage, part) if part.begins_with("IA_") else ModelUtil.find(root, part)
	if btn == null:
		return
	var rest: Vector3 = btn.position
	var tw := room.create_tween()
	tw.tween_property(btn, "position:z", rest.z - 0.006 if part.begins_with("IA_") else rest.z - 0.008, 0.07)
	tw.tween_property(btn, "position:z", rest.z, 0.12)


func _say(key: String) -> void:
	(room.get("hud") as Node).call("message", room.tr(key))
	AudioManager.ui("ui_tap")


# ====================================================================== events
## Sound and the ride (the room's event handler calls this for every event). -> true when the event was one of ours.
func feedback(e: String) -> bool:
	var name := e.get_slice(":", 0)
	match name:
		"weight":
			var parts := e.split(":")
			ArchiveZones.cue("c2x_weight_hang" if parts.size() > 2 and parts[2] == "1" else "c2x_weight_off", -2.0, randf_range(0.95, 1.05))
			return true
		"lift_balanced":
			ArchiveZones.cue("c2x_lift_balanced")
			return true
		"counter_heavy":
			ArchiveZones.cue("c2x_counter_heavy", -6.0)
			return true
		"counter_light":
			ArchiveZones.cue("c2x_counter_light", -6.0)
			return true
		"lift_stuck":
			ArchiveZones.cue("c2x_lift_stuck")
			return true
		"lift_moved":
			var k := int(e.get_slice(":", 1))
			var mine := zones.current == zone_id or _ride_to == k # only the site the player stands at answers
			if mine:
				ArchiveZones.cue("c2x_lift_move", -3.0)
				room.get_tree().create_timer(3.6).timeout.connect(func() -> void: ArchiveZones.cue("c2x_lift_bell", -3.0))
			if _ride_to == k:
				_ride_to = -9
				_ride(k)
			return mine
	return false


## The player rides the cage: after it has left the view the fade takes them to the floor's room.
func _ride(k: int) -> void:
	var hud: Node = room.get("hud")
	hud.call("set_busy", true)
	await room.get_tree().create_timer(1.5).timeout
	hud.call("set_busy", false)
	if is_instance_valid(room) and logic.room_open(str(FLOOR_ROOM[k])):
		logic.enter_room(str(FLOOR_ROOM[k]))
