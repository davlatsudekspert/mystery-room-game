class_name ArchiveHallExp
extends RefCounted
## Chapter 2 expansion: what the new game adds to the existing hall (docs/CHAPTER2_EXPANSION.md sections 3 and 7):
## - N1 "Warm Wall": three painted panels A / B / C on the east wall south of the compressor; the receiver's needle points
##   at the one that hides the door (the logic draws it per game, `v_panel`); behind it a brass plate with a ten-key dial
##   (Leyla's number); after it the service door opens on the stair down to the Pump Room;
## - the stair stump (the blocked spiral stair, Stage B only) and the building plan on the south wall.
## Models: `service_door` (with its cover hatch and rotary dial), `stair_stump` and `floor_plan_frame` (docs/models/ch2_exp.md);
## the two decoy hatches are still primitives (`placeholder_hatch_*`). The door has one site, so `v_panel` picks the LETTER on
## its hatch (and the receiver table); the decoys carry the other two letters.
## Nothing is built or shown unless the game is an expansion game (ArchiveLogic.exp_active()), so stage 0 is the old hall.
## No puzzle logic here: every tap calls the logic and the state is drawn from `logic.state`.

const VIEWS: Array[String] = ["east_south", "east_panel_a", "east_panel_b", "east_panel_c", "east_dial", "stair", "plan"]
const HOTSPOT_VIEW := {"east_wall": "east_south", "stair_stump": "stair", "plan_wall": "plan"}
const DEEPER := {"east_south": ["east_panel_a", "east_panel_b", "east_panel_c", "east_dial"]}
const CAPTION := {"east_south": "obj2x.east_wall", "east_panel_a": "obj2x.panel", "east_panel_b": "obj2x.panel",
	"east_panel_c": "obj2x.panel", "east_dial": "obj2x.door_plate", "stair": "obj2x.stair", "plan": "obj2x.plan"}
const WALL_X := 5.0
const DOOR_POS := Vector3(4.93, 0.0, 2.95) # docs/models/ch2_exp.md: east wall, spans z 2.5..3.4 (the contract's only site)
const STUMP_POS := Vector3(-3.3, 0.0, -2.0)
const PLAN_POS := Vector3(1.9, 0.0, 3.47)
## Decoy hatches (painted like the one over the door): site -> [position, yaw degrees (front +Z = into the hall), view position]
## The door has ONE site (the model's contract), so the game's variant `v_panel` picks which LETTER the door's hatch carries
## (and the receiver table moves with it); the other two letters hang on the decoys.
const DECOYS: Array = [
	[Vector3(5.0, 0.0, 1.675), -90.0],
	[Vector3(4.6, 0.0, 3.5), 180.0],
]
const HATCH_W := 0.5
const HATCH_H := 1.3

var room: Node3D
var zones: ArchiveZones
var logic: ArchiveLogic
var root: Node3D
var _door_model: Node3D
var _cover: Node3D
var _leaf: Node3D
var _frame: Node3D
var _lamp: MeshInstance3D
var _decoys: Array[Node3D] = []
var _stump: Node3D
var _plan: Node3D
var _letters: Array[String] = [] # letter index -> "door" | "decoy0" | "decoy1"


func _init(r: Node3D, z: ArchiveZones) -> void:
	room = r
	zones = z
	logic = r.get("logic")


## Called once by the room when the game is an expansion game.
func build() -> void:
	root = Node3D.new()
	root.name = "HallExp"
	room.add_child(root)
	var v := int(logic.state["v_panel"])
	# which letter hangs where: the door's hatch carries letter v, the decoys the other two in order
	var others: Array[int] = []
	for i in 3:
		if i != v:
			others.append(i)
	_letters = ["", "", ""]
	_letters[v] = "door"
	_letters[others[0]] = "decoy0"
	_letters[others[1]] = "decoy1"
	_build_door(v)
	for k in 2:
		_build_decoy(k, others[k])
	_build_stump()
	_build_plan()
	# the framed rules notice hangs where the door's hatch is (docs/models/ch2_exp.md): it moves up the wall, above the hatch
	var notice := ModelUtil.find((room.get("models") as Dictionary).get("room_archive"), "rules_notice")
	if notice != null:
		notice.position.y += 1.15
	room.call("add_tap_area", root, Vector3(0.03, 2.1, 2.1), "east_wall", "East_wall", Vector3(4.985, 1.1, 2.45))
	var cam: RoomCamera = room.get("cam")
	cam.add_view("east_south", Vector3(3.3, 1.5, 1.2), Vector3(5.0, 1.2, 2.5), 64.0)
	for i in 3:
		cam.add_view("east_panel_" + "abc"[i], _panel_view_pos(i), _panel_view_target(i), 46.0)
	cam.add_view("east_dial", Vector3(4.55, 1.42, 3.12), Vector3(5.0, 1.42, 3.15), 34.0)
	cam.add_view("stair", Vector3(-1.4, 1.55, -0.2), STUMP_POS + Vector3(0, 0.9, 0), 58.0)
	cam.add_view("plan", Vector3(PLAN_POS.x, 1.55, 1.9), Vector3(PLAN_POS.x, 1.55, 3.4), 40.0)
	zones.register("hall", VIEWS, HOTSPOT_VIEW, DEEPER, CAPTION)


func _panel_site(i: int) -> Array:
	match _letters[i]:
		"door":
			return [DOOR_POS, -90.0]
		"decoy0":
			return DECOYS[0]
	return DECOYS[1]


func _panel_view_pos(i: int) -> Vector3:
	var site := _panel_site(i)
	var p: Vector3 = site[0]
	return p + Basis(Vector3.UP, deg_to_rad(float(site[1]))) * Vector3(0, 1.4, 1.25)


func _panel_view_target(i: int) -> Vector3:
	var site := _panel_site(i)
	return (site[0] as Vector3) + Vector3(0, 1.3, 0)


func _mat(color: Color, rough: float = 0.8, metal: float = 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.roughness = rough
	m.metallic = metal
	return m


func _box(parent: Node3D, size: Vector3, pos: Vector3, mat: Material, nm: String = "") -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.position = pos
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if nm != "":
		mi.name = nm
	parent.add_child(mi)
	return mi


func _label(parent: Node3D, text: String, pos: Vector3, size_m: float, color: Color, yaw: float) -> Label3D:
	var l := Label3D.new()
	l.text = text
	l.font = load(UITheme.FONT_DISPLAY_BOLD)
	l.font_size = 96
	l.pixel_size = size_m / 96.0
	l.modulate = color
	l.outline_size = 0
	l.position = pos
	l.rotation_degrees.y = yaw
	l.double_sided = false
	l.no_depth_test = false
	parent.add_child(l)
	return l


# ---------------------------------------------------------------------- N1: the door and its hatches
func _build_door(v: int) -> void:
	_door_model = ModelUtil.spawn("service_door", room, Transform3D(Basis(Vector3.UP, deg_to_rad(-90.0)), DOOR_POS), "parts")
	if _door_model == null:
		return
	_door_model.name = "service_door"
	(room.get("models") as Dictionary)["service_door"] = _door_model
	(room.get("_roots") as Dictionary)[_door_model] = "service_door"
	_door_model.set_meta("hotspot", "east_wall")
	room.call("tune_shadows", _door_model)
	_cover = ModelUtil.find(_door_model, "IA_cover_panel")
	_leaf = ModelUtil.find(_door_model, "IA_service_door")
	_frame = ModelUtil.find(_door_model, "service_door_frame")
	_lamp = ModelUtil.find(_door_model, "service_lamp") as MeshInstance3D
	for n in range(10): # the hole liners are tap volumes only
		var hole := ModelUtil.find(_door_model, "IA_dial_hole_%d" % n) as MeshInstance3D
		if hole != null:
			hole.visible = false
	if _cover != null:
		_letter_label(_cover, "ABC"[v], Vector3(0, -1.05, 0.02))
	_frame_set(false)


func _letter_label(parent: Node3D, text: String, pos: Vector3) -> void:
	_label(parent, text, pos, 0.3, Color("e8e2cf"), 0.0)


func _build_decoy(k: int, letter: int) -> void:
	var site: Array = DECOYS[k]
	var n := Node3D.new()
	n.name = "placeholder_hatch_%s" % "abc"[letter]
	n.position = site[0] + Basis(Vector3.UP, deg_to_rad(float(site[1]))) * Vector3(0, HATCH_H / 2.0 + 0.1, 0.03)
	n.rotation_degrees.y = float(site[1])
	root.add_child(n)
	_box(n, Vector3(HATCH_W, HATCH_H, 0.03), Vector3.ZERO, _mat(Color("4f6a56"), 0.9), "face")
	_box(n, Vector3(HATCH_W + 0.05, HATCH_H + 0.05, 0.02), Vector3(0, 0, -0.01), _mat(Color("2a2a26"), 0.9), "frame")
	_label(n, "ABC"[letter], Vector3(0, 0, 0.02), 0.3, Color("e8e2cf"), 0.0)
	room.call("add_tap_area", n, Vector3(HATCH_W, HATCH_H, 0.08), "east_wall", "IA_panel_%d" % letter, Vector3(0, 0, 0.02))
	_decoys.append(n)


func _frame_set(open: bool) -> void:
	if _frame != null:
		room.call("set_present", _frame, open)
	if _leaf != null:
		room.call("set_present", _leaf, open)


func _build_stump() -> void:
	_stump = ModelUtil.spawn("stair_stump", room, Transform3D(Basis.IDENTITY, STUMP_POS), "parts")
	if _stump == null:
		return
	_stump.name = "stair_stump"
	(room.get("models") as Dictionary)["stair_stump"] = _stump
	(room.get("_roots") as Dictionary)[_stump] = "stair_stump"
	_stump.set_meta("hotspot", "stair_stump")
	room.call("tune_shadows", _stump)


func _build_plan() -> void:
	_plan = ModelUtil.spawn("floor_plan_frame", room, Transform3D(Basis(Vector3.UP, deg_to_rad(180.0)), PLAN_POS), "parts")
	if _plan == null:
		return
	_plan.name = "floor_plan_frame"
	(room.get("models") as Dictionary)["floor_plan_frame"] = _plan
	(room.get("_roots") as Dictionary)[_plan] = "floor_plan_frame"
	_plan.set_meta("hotspot", "plan_wall")


# ---------------------------------------------------------------------- state
func apply_state(animated: bool) -> void:
	var s := logic.state
	if _door_model == null:
		return
	var found: bool = s["panel_found"] or s["pump_open"]
	_rot(_cover, Vector3.RIGHT, -75.0 if found else 0.0, animated)
	_frame_set(found)
	_rot(_leaf, Vector3.UP, -100.0 if s["pump_open"] else 0.0, animated)
	if _lamp != null:
		ModelUtil.set_emission(_lamp, not s["pump_open"], Color("ff3b2f"), 2.0)
	if _stump != null:
		room.call("set_present", _stump, logic.exp_stage() >= 2)
	var ladder := ModelUtil.find(_stump, "IA_wedge_ladder")
	if ladder != null:
		room.call("set_present", ladder, not s["wedge_out"])


var _tweens: Dictionary = {}


func _rot(n: Node3D, axis: Vector3, deg: float, animated: bool) -> void:
	if n == null:
		return
	if not n.has_meta("rest"):
		n.set_meta("rest", n.transform)
	var base: Transform3D = n.get_meta("rest")
	var target := Transform3D(base.basis * Basis(axis, deg_to_rad(deg)), base.origin)
	var k := n.get_instance_id()
	if _tweens.has(k) and (_tweens[k] as Tween).is_valid():
		(_tweens[k] as Tween).kill()
	if not animated or n.transform.is_equal_approx(target):
		n.transform = target
		return
	var from := n.transform
	var fq := from.basis.get_rotation_quaternion()
	var tq := target.basis.get_rotation_quaternion()
	var tw := room.create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tw.tween_method(func(t: float) -> void:
		if is_instance_valid(n):
			n.transform = Transform3D(Basis(fq.slerp(tq, t)), from.origin), 0.0, 1.0, 0.6)
	_tweens[k] = tw


## The finger wheel turns to the digit and runs back (the booth door's convention).
func _dial_spin(d: int) -> void:
	var w := ModelUtil.find(_door_model, "IA_rotary_dial")
	if w == null:
		return
	var n := 10 if d == 0 else d
	var theta := 50.0 + (n - 1) * 30.0
	_rot_quick(w, -(theta + 10.0), 0.25 + 0.02 * n)
	room.get_tree().create_timer(0.3 + 0.02 * n).timeout.connect(func() -> void: _rot_quick(w, 0.0, 0.35 + 0.035 * n))


func _rot_quick(n: Node3D, deg: float, dur: float) -> void:
	if not n.has_meta("rest"):
		n.set_meta("rest", n.transform)
	var base: Transform3D = n.get_meta("rest")
	var target := Transform3D(base.basis * Basis(Vector3.BACK, deg_to_rad(deg)), base.origin)
	var tw := room.create_tween()
	var from := n.transform.basis.get_rotation_quaternion()
	var tq := target.basis.get_rotation_quaternion()
	tw.tween_method(func(t: float) -> void:
		if is_instance_valid(n):
			n.transform = Transform3D(Basis(from.slerp(tq, t)), base.origin), 0.0, 1.0, dur)


# ---------------------------------------------------------------------- taps
## -> true when the tap was handled here.
func interact(hs: String, part: String) -> bool:
	var cam: RoomCamera = room.get("cam")
	var cur := cam.current()
	var v := int(logic.state["v_panel"])
	match hs:
		"east_wall":
			if part == "IA_cover_panel" or part.begins_with("IA_panel_"):
				var i := v if part == "IA_cover_panel" else int(part.substr(9))
				var view := "east_panel_" + "abc"[i]
				if logic.state["panel_found"]:
					cam.go("east_dial")
				elif cur != view:
					cam.go(view)
				else:
					logic.n1_open_panel(i)
			elif part.begins_with("IA_dial_hole_") or part == "IA_rotary_dial":
				if cur != "east_dial":
					cam.go("east_dial")
				elif part.begins_with("IA_dial_hole_"):
					var d := int(part.substr(13))
					_dial_spin(d)
					logic.n1_dial(d)
			elif part == "IA_service_door" or part.begins_with("service_door"):
				if logic.state["pump_open"]:
					logic.enter_room("pump")
				elif cur != "east_dial" and logic.state["panel_found"]:
					cam.go("east_dial")
			elif cur != "east_south" and cur not in DEEPER["east_south"]:
				cam.go("east_south")
			else:
				_say("obj2x.east_wall")
			return true
		"stair_stump":
			if cur != "stair":
				cam.go("stair")
			else:
				_say("obj2x.wedge" if not logic.state["wedge_out"] else "obj2x.stair")
			return true
		"plan_wall":
			if cur != "plan":
				cam.go("plan")
			else:
				ArchiveZones.cue("plan_unfold")
				(room.get("hud") as Node).call("show_plan")
			return true
	return false


func _say(key: String) -> void:
	(room.get("hud") as Node).call("message", room.tr(key))
	AudioManager.ui("ui_tap")


## Event feedback for N1 (the room's _on_events calls this for every event). -> true when the event was one of ours.
func feedback(e: String) -> bool:
	var name := e.get_slice(":", 0)
	match name:
		"panel_opened":
			ArchiveZones.cue("panel_swing")
			return true
		"panel_cold":
			ArchiveZones.cue("panel_cold")
			return true
		"n1_dial_wrong":
			AudioManager.sfx("dial_return")
			return true
		"pump_opened":
			ArchiveZones.cue("svc_door_open")
			return true
	return false
