class_name ArchiveGallery
extends RefCounted
## Chapter 2 expansion, room R5: the Reading Gallery (docs/CHAPTER2_EXPANSION.md sections 3, 7, 8 N8, 11 M4; models and pivots
## in docs/models/ch2_exp.md). A zone of the Archive scene (ArchiveZones): the double-height room over the hall (a balcony
## rail with the hall visible below), the Records counter, the roll-call board, the old PA horn, the wedged library ladder
## over the spiral stair, the book lift's upper door, and the doors to the Plate Room and the Director's Office.
## It only renders ArchiveLogic's state and forwards taps to its actions:
## - N8 roll-call board: tap a staff tag to take it up, tap a hook (or another tag, which swaps) to hang it; the clue slips from
##   the counter drawer are pinned on the board once taken, each with a lamp that says whether it holds (`board_slip_status`);
##   when every slip agrees a key drops into the tray (`take("board_key")`);
## - the wedge: the pin is pulled (`pull_wedge`), the chock slides, the ladder falls over the stairwell, and the spiral stair
##   becomes a second way down to the hall;
## - M4 "roll call": the PA horn's lamp pulses to a count (two notes, then three) and stops, with the sound by ArchiveZones;
## - the office door opens with the pass key (a locked door only rattles and says so).
## The shell's floor ends at the balcony edge; `hall_below` is baked geometry (a card of the hall, not the live hall).

const VIEWS: Array[String] = ["gallery", "balcony", "counter", "board", "horn", "wedge", "lift_g", "lift_gpanel"]
const HOTSPOT_VIEW := {"gal_door_plate": "gallery", "gal_door_office": "gallery", "gal_rail": "balcony", "gal_counter": "counter",
	"gal_board": "board", "gal_horn": "horn", "gal_wedge": "wedge", "gal_stair": "wedge"}
const DEEPER := {}
const CAPTION := {"gallery": "room2x.gallery", "balcony": "room2x.hall", "counter": "obj2x.counter", "board": "obj2x.board",
	"horn": "obj2x.horn", "wedge": "obj2x.wedge", "lift_g": "obj2x.lift", "lift_gpanel": "obj2x.lift"}
const PLACE := {
	"room_gallery": [Vector3.ZERO, 0.0], "balcony_rail": [Vector3(0, 0, 1.60), 0.0], "roll_call_board": [Vector3(-1.0, 0, -3.0), 0.0],
	"pa_horn": [Vector3(-4.5, 3.35, 0.15), 90.0], "stair_wedge": [Vector3(3.15, 0, 1.00), 0.0],
	"book_lift_cage": [Vector3(2.70, 0, -2.37), 0.0],
}
const HOOK_X0 := -1.0
const HOOK_DX := 0.4
const HOOK_Y := 1.85
const TRAY_Y := 1.14
const DRAWER_OPEN := 0.35
const SLIPS_DRAWER := 1 # the clue slips lie in the middle drawer of the counter
const DOOR_OPEN_DEG := 95.0

var room: Node3D
var zones: ArchiveZones
var root: Node3D
var logic: ArchiveLogic
var rig: ArchiveRig
var lift: ArchiveLift
var models: Dictionary = {}
var _tags: Array[Node3D] = []
var _slips: Array[MeshInstance3D] = []
var _slip_sig: Array[String] = []
var _held := -1 # the tag taken up, not yet hung
var _drawer_open: Array[bool] = [false, false, false]
var _slips_item: Node3D
var _key_item: Node3D
var _horn_lamp: MeshInstance3D
var _horn_light: OmniLight3D
var _wedge_done := false


func _init(r: Node3D, z: ArchiveZones, zone_root: Node3D) -> void:
	room = r
	zones = z
	root = zone_root
	logic = r.get("logic")
	rig = ArchiveRig.new(r)


# ====================================================================== construction
func build() -> void:
	for id: String in PLACE:
		var e: Array = PLACE[id]
		var n := ModelUtil.spawn(id, root, Transform3D(Basis(Vector3.UP, deg_to_rad(float(e[1]))), e[0]), "parts")
		if n == null:
			continue
		n.name = "gallery_" + id
		models[id] = n
		(room.get("_roots") as Dictionary)[n] = "gallery_" + id
		(room.get("models") as Dictionary)["gallery_" + id] = n
		n.set_meta("hotspot", "")
		room.call("tune_shadows", n)
	var shell: Node3D = models["room_gallery"]
	for mi in ModelUtil.find_meshes(shell):
		if str(mi.name).begins_with("wall_") or str(mi.name) in ["ceiling", "beams", "floor", "hall_below", "sky_cards"]:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	ArchiveRig.hot(models["balcony_rail"], "gal_rail")
	ArchiveRig.hot(models["roll_call_board"], "gal_board")
	ArchiveRig.hot(models["pa_horn"], "gal_horn")
	ArchiveRig.hot(models["stair_wedge"], "gal_wedge")
	ArchiveRig.hot(ModelUtil.find(shell, "stair_in"), "gal_stair")
	ArchiveRig.hot(ModelUtil.find(shell, "IA_door_plate"), "gal_door_plate")
	ArchiveRig.hot(ModelUtil.find(shell, "IA_door_office"), "gal_door_office")
	for i in 3:
		ArchiveRig.hot(ModelUtil.find(shell, "IA_counter_drawer_%d" % i), "gal_counter")
	ArchiveRig.hot(ModelUtil.find(shell, "counter"), "gal_counter")
	# the tube terminal's hatch (the Records receiver of the pneumatic station) is scenery here: no tap volume of its own
	for body in ModelUtil.find(shell, "IA_tube_hatch").find_children("*", "StaticBody3D", true, false):
		body.queue_free()
	_build_lights(shell)
	_build_board()
	_build_counter(shell)
	_build_horn()
	_build_lift()
	_build_views()
	zones.register("gallery", VIEWS, HOTSPOT_VIEW, DEEPER, CAPTION)
	apply_state(false)


func _build_views() -> void:
	var cam: RoomCamera = room.get("cam")
	var o := root.position
	cam.add_view("gallery", o + Vector3(-3.9, 1.65, -0.5), o + Vector3(2.2, 1.2, 0.4), 68.0, true)
	cam.add_view("balcony", o + Vector3(0.2, 1.6, 1.45), o + Vector3(0.2, -3.2, 2.8), 72.0)
	cam.add_view("counter", o + Vector3(-1.9, 1.45, -0.2), o + Vector3(-4.0, 0.95, -0.2), 52.0)
	cam.add_view("board", o + Vector3(-1.0, 1.6, -0.45), o + Vector3(-1.0, 1.5, -3.0), 48.0)
	cam.add_view("horn", o + Vector3(-2.0, 2.3, 1.55), o + Vector3(-4.0, 3.3, 0.15), 50.0)
	cam.add_view("wedge", o + Vector3(1.5, 2.3, -0.3), o + Vector3(3.15, 0.35, 1.0), 50.0)
	cam.add_view("lift_g", o + Vector3(2.7, 1.55, 0.9), o + Vector3(2.7, 1.1, -2.6), 56.0)
	cam.add_view("lift_gpanel", o + Vector3(2.7, 1.45, -0.3), o + Vector3(2.7, 1.3, -2.5), 44.0)


func _build_lights(shell: Node3D) -> void:
	# sepia daylight through the arched windows (the sky cards only paint the glass), long shafts across the tables
	for nm in ["light_window_n", "light_window_s"]:
		var n := ModelUtil.find(shell, nm)
		if n != null:
			ArchiveRig.omni(root, n.position, Color("ffe2b0"), 2.2, 9.0)
	for nm in ["light_table_a", "light_table_b"]:
		var n := ModelUtil.find(shell, nm)
		if n != null:
			ArchiveRig.omni(root, n.position + Vector3(0, 0.25, 0), Color("ffe8bc"), 1.0, 3.6)
	ArchiveRig.omni(root, Vector3(-1.0, 2.5, -0.4), Color("ffe6c0"), 1.1, 4.2) # the board and the counter are read from close up
	ArchiveRig.omni(root, Vector3(-3.0, 2.4, 0.2), Color("ffe2b0"), 0.9, 4.0)
	ArchiveRig.omni(root, Vector3(2.7, 2.6, 0.3), Color("ffe6c0"), 1.0, 4.4) # the lift wall and the stair
	ArchiveRig.omni(root, Vector3(0, 2.2, 1.2), Color("cfe0ff"), 0.5, 6.0) # the light that comes up from the hall


func _build_lift() -> void:
	var cage := models.get("book_lift_cage") as Node3D
	if cage == null:
		return
	lift = ArchiveLift.new(room, zones)
	lift.add_site(1, "gallery", root, cage, {"door": "lift_g", "weights": "lift_g", "panel": "lift_gpanel"}, null,
		Transform3D(Basis.IDENTITY, Vector3(1.5, 1.3, -2.99)))


# ---------------------------------------------------------------------- N8: the board
func _build_board() -> void:
	var b: Node3D = models["roll_call_board"]
	for k in ArchiveExpData.TAGS:
		var t := ModelUtil.find(b, "IA_tag_%d" % k)
		_tags.append(t)
		t.set_meta("rest", t.transform)
	for j in ArchiveExpData.HOOKS: # a tap volume per hook: a hung tag in front of it still wins by being nearer
		room.call("add_tap_area", b, Vector3(0.36, 0.44, 0.1), "gal_board", "Hook_%d" % j, Vector3(HOOK_X0 + HOOK_DX * j, 1.7, 0.03))
	room.call("add_tap_area", b, Vector3(2.4, 0.36, 0.12), "gal_board", "Tray", Vector3(0, 0.93, 0.05))
	for i in ArchiveExpData.HOOKS: # the slips are pinned under each hook once they are taken
		var q := ArchiveRig.picture(b, null, Vector2(0.34, 0.24), Vector3(HOOK_X0 + HOOK_DX * i, 1.3, 0.046), Color.WHITE, true)
		q.visible = false
		q.name = "slip_%d" % i
		room.call("add_tap_area", q, Vector3(0.34, 0.24, 0.05), "gal_board", "Slip_%d" % i, Vector3.ZERO)
		_slips.append(q)
		_slip_sig.append("")
	# the key that drops into the tray when every slip agrees
	_key_item = ModelUtil.spawn("pass_key", b, Transform3D(Basis(Vector3.RIGHT, deg_to_rad(90.0)), Vector3(0.0, 0.8, 0.12)), "none")
	if _key_item != null:
		_key_item.name = "Item_board_key"
		_key_item.scale = Vector3.ONE * 2.2
		var body := StaticBody3D.new()
		var cs := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = Vector3(0.22, 0.12, 0.1)
		cs.shape = box
		body.add_child(cs)
		body.set_meta("part", "Item_board_key")
		body.set_meta("hotspot", "gal_board")
		_key_item.add_child(body)
		_key_item.visible = false


# ---------------------------------------------------------------------- the counter and its drawers
func _build_counter(shell: Node3D) -> void:
	for i in 3:
		var d := ModelUtil.find(shell, "IA_counter_drawer_%d" % i)
		if d == null:
			continue
		var tray := MeshInstance3D.new() # the drawer's own box behind its front, so a pulled drawer is not a hole
		var tm := BoxMesh.new()
		tm.size = Vector3(0.34, 0.03, 0.66)
		tray.mesh = tm
		tray.position = Vector3(-0.17, 0.30, 0.0) # level with the top of the front: from above a pulled drawer shows its tray
		var m := StandardMaterial3D.new()
		m.albedo_color = Color("3a2a1c")
		m.roughness = 0.8
		tray.material_override = m
		tray.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		d.add_child(tray)
	var d1 := ModelUtil.find(shell, "IA_counter_drawer_%d" % SLIPS_DRAWER)
	_slips_item = Node3D.new()
	_slips_item.name = "Item_counter_slips"
	_slips_item.position = Vector3(-0.17, 0.335, 0.0)
	d1.add_child(_slips_item)
	var paper := StandardMaterial3D.new()
	paper.albedo_color = Color("d9ceb0")
	paper.roughness = 0.9
	for k in 3:
		var sheet := MeshInstance3D.new()
		var sm := BoxMesh.new()
		sm.size = Vector3(0.2, 0.012, 0.26)
		sheet.mesh = sm
		sheet.position = Vector3(0.0, 0.012 * k, 0.0)
		sheet.rotation_degrees.y = float(k - 1) * 7.0
		sheet.material_override = paper
		sheet.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_slips_item.add_child(sheet)
	var band := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.05, 0.05, 0.28)
	band.mesh = bm
	band.position = Vector3(0, 0.014, 0)
	var bmat := StandardMaterial3D.new()
	bmat.albedo_color = Color("7a2a20")
	band.material_override = bmat
	_slips_item.add_child(band)
	var body := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(0.3, 0.12, 0.34)
	cs.shape = box
	body.add_child(cs)
	body.set_meta("part", "Item_counter_slips")
	body.set_meta("hotspot", "gal_counter")
	_slips_item.add_child(body)
	_slips_item.rotation_degrees.z = 0.0


# ---------------------------------------------------------------------- the horn
func _build_horn() -> void:
	var horn: Node3D = models["pa_horn"]
	_horn_lamp = ModelUtil.find(horn, "horn_lamp") as MeshInstance3D
	var origin := ModelUtil.find(horn, "light_origin_horn")
	_horn_light = OmniLight3D.new()
	_horn_light.light_color = Color("ffcf90")
	_horn_light.light_energy = 0.0
	_horn_light.omni_range = 2.6
	_horn_light.shadow_enabled = false
	horn.add_child(_horn_light)
	_horn_light.position = origin.position if origin != null else Vector3(0, 0, 1.05)


# ====================================================================== state
func apply_state(animated: bool) -> void:
	var s := logic.state
	var shell: Node3D = models["room_gallery"]
	var taken: Dictionary = s["taken"]
	# doors stand open once the player went through them
	rig.rot(ModelUtil.find(shell, "IA_door_plate"), Vector3.UP, DOOR_OPEN_DEG if logic.room_seen("plate") else 0.0, animated, 0.6)
	rig.rot(ModelUtil.find(shell, "IA_door_office"), Vector3.UP, DOOR_OPEN_DEG if logic.room_seen("office") else 0.0, animated, 0.6)
	# the counter's drawers
	for i in 3:
		rig.slide(ModelUtil.find(shell, "IA_counter_drawer_%d" % i), Vector3(DRAWER_OPEN if _drawer_open[i] else 0.0, 0, 0), animated, 0.35)
	room.call("set_present", _slips_item, not bool(taken.get("counter_slips", false)))
	_apply_board(animated)
	_apply_wedge(animated)
	var key_here: bool = bool(s["board_ok"]) and not bool(taken.get("board_key", false))
	if _key_item != null:
		room.call("set_present", _key_item, key_here)
	if lift != null:
		lift.apply_state(animated)


func _apply_board(animated: bool) -> void:
	var s := logic.state
	var board: Array = s["board"]
	for k in _tags.size():
		var j := board.find(k)
		var off := Vector3.ZERO
		if j >= 0:
			off = Vector3((j - k) * HOOK_DX, 0, 0)
		else:
			off = Vector3(0, TRAY_Y - HOOK_Y, 0.0)
		if k == _held:
			off += Vector3(0, 0.06, 0.07)
		rig.pose(_tags[k], off, Vector3.RIGHT, -8.0 if k == _held else 0.0, animated, 0.3)
	# the slips pinned under the hooks, with their lamps
	var slips := logic.board_slips()
	var status := logic.board_slip_status()
	var have: bool = bool((s["taken"] as Dictionary).get("counter_slips", false))
	for i in _slips.size():
		var show := have and i < slips.size()
		_slips[i].visible = show
		room.call("set_present", _slips[i], show)
		if not show:
			continue
		var sig := "%s:%d" % [str(slips[i]), int(status[i])]
		if sig != _slip_sig[i]:
			_slip_sig[i] = sig
			var m := _slips[i].material_override as StandardMaterial3D
			m.albedo_texture = ImageTexture.create_from_image(ArchiveUpperArt.slip_image(slips[i], int(status[i]), 240, 170))


func _apply_wedge(animated: bool) -> void:
	var wedge: Node3D = models["stair_wedge"]
	var out: bool = bool(logic.state["wedge_out"])
	var pin := ModelUtil.find(wedge, "IA_wedge_pin")
	var chock := ModelUtil.find(wedge, "IA_wedge_chock")
	var ladder := ModelUtil.find(wedge, "IA_wedge_ladder")
	if out and animated and not _wedge_done:
		rig.slide(pin, Vector3(0, 0.22, 0), true, 0.5)
		room.get_tree().create_timer(0.55).timeout.connect(func() -> void: rig.slide(chock, Vector3(0, 0, 0.35), true, 0.5))
		room.get_tree().create_timer(1.1).timeout.connect(func() -> void: rig.rot(ladder, Vector3.RIGHT, -78.0, true, 0.9))
	else:
		rig.slide(pin, Vector3(0, 0.22, 0) if out else Vector3.ZERO, false)
		rig.slide(chock, Vector3(0, 0, 0.35) if out else Vector3.ZERO, false)
		rig.rot(ladder, Vector3.RIGHT, -78.0 if out else 0.0, false)
	_wedge_done = out


func on_enter() -> void:
	apply_state(false)


# ====================================================================== taps
## -> true when the tap was handled here.
func interact(hs: String, part: String) -> bool:
	if lift != null and hs.begins_with("lift_") and lift.interact(hs, part):
		return true
	var cam: RoomCamera = room.get("cam")
	var cur := cam.current()
	match hs:
		"gal_door_plate":
			_open_door("plate", "IA_door_plate")
			return true
		"gal_door_office":
			_office_door()
			return true
		"gal_rail":
			if cur != "balcony":
				cam.go("balcony")
			else:
				_say("room2x.hall")
			return true
		"gal_counter":
			_tap_counter(part)
			return true
		"gal_board":
			_tap_board(part)
			return true
		"gal_horn":
			if cur != "horn":
				cam.go("horn")
			else:
				_say("obj2x.horn")
				_horn_blink(1)
			return true
		"gal_wedge":
			if cur != "wedge":
				cam.go("wedge")
			elif not logic.state["wedge_out"]:
				logic.pull_wedge()
			else:
				_say("obj2x.stair")
			return true
		"gal_stair":
			if cur != "wedge":
				cam.go("wedge")
			elif logic.state["wedge_out"]:
				ArchiveZones.cue("stair_steps")
				logic.enter_room("hall")
			else:
				_say("obj2x.wedge")
			return true
	return false


func _say(key: String) -> void:
	(room.get("hud") as Node).call("message", room.tr(key))
	AudioManager.ui("ui_tap")


func _open_door(room_id: String, part_name: String) -> void:
	var door := ModelUtil.find(models["room_gallery"], part_name)
	rig.rot(door, Vector3.UP, DOOR_OPEN_DEG, true, 0.5)
	ArchiveZones.cue("room_step")
	room.get_tree().create_timer(0.45).timeout.connect(func() -> void:
		if is_instance_valid(room):
			logic.enter_room(room_id))


func _office_door() -> void:
	if logic.room_open("office"):
		ArchiveZones.cue("c2x_door_pass")
		_open_door("office", "IA_door_office")
		return
	var door := ModelUtil.find(models["room_gallery"], "IA_door_office")
	var rest: Transform3D = door.get_meta("rest") if door.has_meta("rest") else door.transform
	door.set_meta("rest", rest)
	rig.rot(door, Vector3.UP, 2.0, true, 0.06) # the locked door only rattles
	room.get_tree().create_timer(0.12).timeout.connect(func() -> void: rig.rot(door, Vector3.UP, 0.0, true, 0.1))
	logic.enter_room("office") # says "that way is locked"


func _tap_counter(part: String) -> void:
	var cam: RoomCamera = room.get("cam")
	if cam.current() != "counter":
		cam.go("counter")
		return
	if part == "Item_counter_slips":
		if logic.can_take("counter_slips"):
			logic.take("counter_slips")
		return
	if part.begins_with("IA_counter_drawer_"):
		var i := int(part.substr(18))
		_drawer_open[i] = not _drawer_open[i]
		ArchiveZones.cue("fire_door", -4.0)
		if _drawer_open[i] and i != SLIPS_DRAWER:
			(room.get("hud") as Node).call("message", room.tr("msg.empty_now"))
		apply_state(true)
		return
	_say("obj2x.counter")


func _tap_board(part: String) -> void:
	var cam: RoomCamera = room.get("cam")
	if cam.current() != "board":
		cam.go("board")
		return
	if part == "Item_board_key":
		if logic.can_take("board_key"):
			logic.take("board_key")
		return
	if part.begins_with("Slip_"):
		(room.get("hud") as Node).call("show_document", "roll_slips")
		return
	if logic.state["board_ok"]:
		_say("obj2x.board")
		return
	var board: Array = logic.state["board"]
	if part.begins_with("IA_tag_"):
		var k := int(part.substr(7))
		var at := board.find(k)
		if _held == k:
			_held = -1
		elif _held >= 0 and at >= 0:
			var h := _held
			_held = -1
			logic.n8_hang(h, at)
			return
		else:
			_held = k
		AudioManager.sfx("c2x_tag_lift", -4.0)
		apply_state(true)
	elif part.begins_with("Hook_"):
		if _held >= 0:
			var h := _held
			_held = -1
			logic.n8_hang(h, int(part.substr(5)))
		else:
			_say("obj2x.board")
	elif part == "Tray":
		if _held >= 0 and board.has(_held):
			var h := _held
			_held = -1
			logic.n8_lift_tag(board.find(h))
		else:
			_held = -1
			apply_state(true)
	else:
		_say("obj2x.board")


# ====================================================================== feedback and the moment
func feedback(e: String) -> bool:
	if lift != null and lift.feedback(e):
		return true
	var name := e.get_slice(":", 0)
	match name:
		"wedge_out":
			ArchiveZones.cue("c2x_wedge_pull")
			return true
		"tag_hung":
			ArchiveZones.cue("c2x_tag_hook", -2.0)
			return true
		"tag_lifted":
			ArchiveZones.cue("c2x_tag_lift", -2.0)
			return true
		"board_wrong":
			ArchiveZones.cue("c2x_board_wrong")
			return true
		"board_ok":
			ArchiveZones.cue("c2x_board_ok")
			return true
	return false


func _horn_blink(n: int) -> void:
	if _horn_lamp == null:
		return
	var tw := room.create_tween()
	for _i in n:
		tw.tween_callback(func() -> void: _horn_pulse(true))
		tw.tween_interval(0.25)
		tw.tween_callback(func() -> void: _horn_pulse(false))
		tw.tween_interval(0.2)


func _horn_pulse(on: bool) -> void:
	rig.lamp(_horn_lamp, on, Color("ffb46b"), 3.0 if on else 0.4)
	if _horn_light != null:
		_horn_light.light_energy = 0.9 if on else 0.0


## M4 "roll call": the horn counts (two notes, then three) with its lamp and then falls quiet; the sound is the zones' cue.
func moment_m4(seconds: float, _sting: bool) -> void:
	var beats: Array[float] = [0.6, 1.3, 3.2, 3.9, 4.6]
	var tw := room.create_tween()
	var t := 0.0
	for b in beats:
		tw.tween_interval(maxf(0.0, b - t))
		tw.tween_callback(func() -> void: _horn_pulse(true))
		tw.tween_interval(0.35)
		tw.tween_callback(func() -> void: _horn_pulse(false))
		t = b + 0.35
	tw.tween_interval(maxf(0.0, seconds - t))
