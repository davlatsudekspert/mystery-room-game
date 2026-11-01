class_name ArchiveHallExp
extends RefCounted
## Chapter 2 expansion: what the new game adds to the existing hall (docs/CHAPTER2_EXPANSION.md sections 3 and 7):
## - N1 "Warm Wall": three painted panels A / B / C on the east wall south of the compressor; the receiver's needle points
##   at the one that hides the door (the logic draws it per game, `v_panel`); behind it a brass plate with a ten-key dial
##   (Leyla's number); after it the service door opens on the stair down to the Pump Room;
## - the stair stump (the blocked spiral stair, Stage B only) and the building plan on the south wall.
## PLACEHOLDER ART (TODO(models)): everything here is built from primitives, marked in the node names (`placeholder_*`),
## until the Night Cell artist pushes `service_door`, `stair_stump` and `floor_plan_frame`; then only `_build_*` change.
## Nothing is built or shown unless the game is an expansion game (ArchiveLogic.exp_active()), so stage 0 is the old hall.
## No puzzle logic here: every tap calls the logic and the state is drawn from `logic.state`.

const VIEWS: Array[String] = ["east_south", "east_panel_a", "east_panel_b", "east_panel_c", "east_dial", "stair", "plan"]
const HOTSPOT_VIEW := {"east_wall": "east_south", "stair_stump": "stair", "plan_wall": "plan"}
const DEEPER := {"east_south": ["east_panel_a", "east_panel_b", "east_panel_c", "east_dial"]}
const CAPTION := {"east_south": "obj2x.east_wall", "east_panel_a": "obj2x.panel", "east_panel_b": "obj2x.panel",
	"east_panel_c": "obj2x.panel", "east_dial": "obj2x.door_plate", "stair": "obj2x.stair", "plan": "obj2x.plan"}
const WALL_X := 5.0
## The east wall is flat for z 1.4-1.95 and 2.35-3.45; a pilaster (z 1.95-2.35, 0.12 deep) stands between the first two panels.
const PANEL_Z: Array[float] = [1.68, 2.62, 3.18]
const PANEL_W := 0.5
const PANEL_SIZE := Vector3(0.03, 1.3, PANEL_W)
const PANEL_Y := 1.15
const STUMP_POS := Vector3(-4.2, 0.0, -2.75)
const PLAN_POS := Vector3(3.3, 1.6, 3.46)

var room: Node3D
var zones: ArchiveZones
var logic: ArchiveLogic
var root: Node3D
var _panels: Array[Node3D] = []
var _plate: Node3D
var _door: Node3D
var _opening: MeshInstance3D
var _stump: Node3D
var _plan: Node3D
var _tweens: Dictionary = {}


func _init(r: Node3D, z: ArchiveZones) -> void:
	room = r
	zones = z
	logic = r.get("logic")


## Called once by the room when the game is an expansion game.
func build() -> void:
	root = Node3D.new()
	root.name = "HallExp"
	room.add_child(root)
	_build_east_wall()
	_build_stump()
	_build_plan()
	var cam: RoomCamera = room.get("cam")
	var v := int(logic.state["v_panel"])
	cam.add_view("east_south", Vector3(3.3, 1.5, 1.2), Vector3(5.0, 1.2, 2.5), 64.0)
	for i in 3:
		cam.add_view("east_panel_" + "abc"[i], Vector3(3.5, 1.45, PANEL_Z[i]), Vector3(5.0, 1.35, PANEL_Z[i]), 44.0)
	cam.add_view("east_dial", Vector3(4.0, 1.27, PANEL_Z[v]), Vector3(5.0, 1.27, PANEL_Z[v]), 36.0)
	cam.add_view("stair", Vector3(-2.2, 1.55, -0.9), Vector3(-4.2, 0.9, -2.75), 58.0)
	cam.add_view("plan", Vector3(3.3, 1.6, 2.0), Vector3(3.3, 1.6, 3.46), 40.0)
	zones.register("hall", VIEWS, HOTSPOT_VIEW, DEEPER, CAPTION)


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


# ---------------------------------------------------------------------- N1: east wall
func _build_east_wall() -> void:
	var paints := [Color("5c6b5a"), Color("5a6670"), Color("6d6454")]
	# one tap area over the whole strip of wall: a tap from the hall walks the camera there
	var strip := Node3D.new()
	strip.name = "placeholder_east_strip"
	root.add_child(strip)
	room.call("add_tap_area", strip, Vector3(0.03, 1.9, 2.3), "east_wall", "East_wall", Vector3(4.985, 1.2, 2.42))
	for i in 3:
		var p := Node3D.new()
		p.name = "placeholder_panel_" + "abc"[i]
		p.position = Vector3(WALL_X - 0.06, PANEL_Y, PANEL_Z[i] - PANEL_W / 2.0) # hinge on the panel's north edge
		root.add_child(p)
		_box(p, PANEL_SIZE, Vector3(0, 0, PANEL_W / 2.0), _mat(paints[i], 0.9), "face")
		_box(p, Vector3(0.034, 1.34, PANEL_W + 0.04), Vector3(0.0, 0, PANEL_W / 2.0), _mat(Color("2a2a26"), 0.9), "frame").position.x = 0.008
		_label(p, "ABC"[i], Vector3(-0.02, 0.0, PANEL_W / 2.0), 0.3, Color("e8e2cf"), -90.0)
		room.call("add_tap_area", p, Vector3(0.08, 1.3, PANEL_W), "east_wall", "IA_panel_%d" % i, Vector3(-0.02, 0, PANEL_W / 2.0))
		_panels.append(p)
	var v := int(logic.state["v_panel"])
	# the plate behind the right panel: a brass slab with ten keys (digits are language-neutral)
	_plate = Node3D.new()
	_plate.name = "placeholder_plate"
	_plate.position = Vector3(WALL_X - 0.03, PANEL_Y, PANEL_Z[v])
	root.add_child(_plate)
	var brass := _mat(Color("b08a3c"), 0.45, 0.9)
	_box(_plate, Vector3(0.02, 0.52, PANEL_W), Vector3.ZERO, brass, "slab")
	for d in 10:
		var col := d % 5
		var row := d / 5
		var pos := Vector3(-0.02, 0.1 - 0.17 * row, -0.19 + 0.095 * col)
		_box(_plate, Vector3(0.025, 0.1, 0.085), pos, _mat(Color("2a2118"), 0.5, 0.2), "key_%d" % d)
		_label(_plate, str(d), pos + Vector3(-0.016, 0, 0), 0.06, Color("e9d9a8"), -90.0)
		room.call("add_tap_area", _plate, Vector3(0.05, 0.12, 0.092), "east_wall", "Dial_%d" % d, pos)
	# the service door: the plate's slab swings open on its north edge once the number was right
	_opening = _box(root, Vector3(0.02, 1.3, PANEL_W), Vector3(WALL_X - 0.03, PANEL_Y, PANEL_Z[v]), _mat(Color("050403"), 1.0), "placeholder_opening")
	_opening.visible = false
	_door = Node3D.new()
	_door.name = "placeholder_service_door"
	_door.position = Vector3(WALL_X - 0.06, PANEL_Y, PANEL_Z[v] - PANEL_W / 2.0)
	root.add_child(_door)
	_box(_door, Vector3(0.04, 1.3, PANEL_W), Vector3(0, 0, PANEL_W / 2.0), brass, "leaf")
	_label(_door, "TODO door", Vector3(-0.03, 0.0, PANEL_W / 2.0), 0.07, Color("1a1208"), -90.0)
	room.call("add_tap_area", _door, Vector3(0.1, 1.3, PANEL_W), "east_wall", "IA_svc_door", Vector3(-0.02, 0, PANEL_W / 2.0))


# ---------------------------------------------------------------------- stair stump, plan
func _build_stump() -> void:
	_stump = Node3D.new()
	_stump.name = "placeholder_stair_stump"
	_stump.position = STUMP_POS
	root.add_child(_stump)
	var iron := _mat(Color("3a3630"), 0.6, 0.6)
	var core := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.12
	cyl.bottom_radius = 0.12
	cyl.height = 2.8
	core.mesh = cyl
	core.position = Vector3(0, 1.4, 0)
	core.material_override = iron
	_stump.add_child(core)
	for k in 5:
		var step := _box(_stump, Vector3(0.7, 0.05, 0.28), Vector3.ZERO, iron, "step_%d" % k)
		step.position = Vector3(0, 0.25 + 0.2 * k, 0)
		step.rotation_degrees.y = 38.0 * k
		step.translate_object_local(Vector3(0.34, 0, 0))
	room.call("add_tap_area", _stump, Vector3(1.5, 2.8, 1.5), "stair_stump", "Stump", Vector3(0, 1.4, 0))


func _build_plan() -> void:
	_plan = Node3D.new()
	_plan.name = "placeholder_floor_plan_frame"
	_plan.position = PLAN_POS
	root.add_child(_plan)
	_box(_plan, Vector3(0.9, 0.6, 0.04), Vector3.ZERO, _mat(Color("4a3a24"), 0.7), "frame")
	_box(_plan, Vector3(0.82, 0.52, 0.01), Vector3(0, 0, -0.022), _mat(Color("d8cfb0"), 0.9), "paper")
	for k in 3: # three strips, the three floors of the plan
		_box(_plan, Vector3(0.7, 0.1, 0.004), Vector3(0, 0.16 - 0.16 * k, -0.03), _mat(Color("6a5c3c"), 0.9), "strip_%d" % k)
	_plan.rotation_degrees.y = 180.0
	room.call("add_tap_area", _plan, Vector3(1.0, 0.7, 0.2), "plan_wall", "Plan", Vector3.ZERO)


# ---------------------------------------------------------------------- state
func apply_state(animated: bool) -> void:
	var s := logic.state
	var v := int(s["v_panel"])
	for i in 3:
		var open: bool = (i == v and s["panel_found"]) or (i == v and s["pump_open"])
		_swing(_panels[i], -100.0 if open else 0.0, animated)
	room.call("set_present", _plate, bool(s["panel_found"]) and not bool(s["pump_open"]))
	_opening.visible = bool(s["pump_open"])
	room.call("set_present", _door, bool(s["pump_open"]))
	_swing(_door, -100.0 if s["pump_open"] else 0.0, animated)
	room.call("set_present", _stump, logic.exp_stage() >= 2)


func _swing(n: Node3D, deg: float, animated: bool) -> void:
	if n == null:
		return
	var k := n.get_instance_id()
	if _tweens.has(k) and (_tweens[k] as Tween).is_valid():
		(_tweens[k] as Tween).kill()
	if not animated or n.rotation_degrees.is_equal_approx(Vector3(0, deg, 0)):
		n.rotation_degrees = Vector3(0, deg, 0)
		return
	var tw := room.create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tw.tween_property(n, "rotation_degrees:y", deg, 0.55)
	_tweens[k] = tw


# ---------------------------------------------------------------------- taps
## -> true when the tap was handled here.
func interact(hs: String, part: String) -> bool:
	var cam: RoomCamera = room.get("cam")
	var cur := cam.current()
	match hs:
		"east_wall":
			if part.begins_with("IA_panel_"):
				var i := int(part.substr(9))
				var view := "east_panel_" + "abc"[i]
				if cur != view and not logic.state["panel_found"]:
					cam.go(view)
				elif logic.state["panel_found"]:
					cam.go("east_dial")
				else:
					logic.n1_open_panel(i)
			elif part.begins_with("Dial_"):
				if cur != "east_dial":
					cam.go("east_dial")
				else:
					ArchiveZones.cue("dial_click", -2.0, 0.9 + 0.02 * int(part.substr(5)))
					logic.n1_dial(int(part.substr(5)))
			elif part == "IA_svc_door":
				if logic.state["pump_open"]:
					logic.enter_room("pump")
			elif cur != "east_south" and cur not in DEEPER["east_south"]:
				cam.go("east_south")
			else:
				_say("obj2x.east_wall")
			return true
		"stair_stump":
			if cur != "stair":
				cam.go("stair")
			else:
				_say("obj2x.stair")
			return true
		"plan_wall":
			if cur != "plan":
				cam.go("plan")
			else:
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
		"panel_cold", "n1_dial_wrong":
			AudioManager.ui("ui_error")
			return true
		"pump_opened":
			ArchiveZones.cue("svc_door_open")
			return true
	return false
