class_name ArchiveOffice
extends RefCounted
## Chapter 2 expansion, room R7: the Director's Office (docs/CHAPTER2_EXPANSION.md sections 3, 7, 8 N10; models and pivots in
## docs/models/ch2_exp.md): Strand's study kept as it was: bottle-green wallpaper, a desk with a green lamp, a marble fireplace,
## two cups of cold tea, and the cabinet with four digit wheels. A zone of the Archive scene (ArchiveZones).
## It only renders ArchiveLogic's state and forwards taps to its actions:
## - N10 cabinet: the label on the transom shows this game's symbol (the strip to print), each of the four wheels turns one digit
##   per tap (`n10_turn_wheel`, wrapping 9 -> 0); when they match the print's digits the doors swing open and the spare projector
##   lamp stands inside (`take("cabinet_lamp")`, the G2 key: fitted to the booth projector in the hall);
## - the tea set (the two cups lift on a tap), the desk drawer, and the door back to the Gallery.
## Reaching this room needs the pass key (the Gallery's door decides; this zone never checks).

const VIEWS: Array[String] = ["office", "cabinet", "office_desk"]
const HOTSPOT_VIEW := {"off_cabinet": "cabinet", "off_lamp": "cabinet", "off_tea": "office_desk", "off_desk": "office_desk", "off_door": "office"}
const DEEPER := {}
const CAPTION := {"office": "room2x.office", "cabinet": "obj2x.cabinet", "office_desk": "obj2x.tea"}
const PLACE := {"room_office": [Vector3.ZERO, 0.0], "strand_cabinet": [Vector3(2.67, 0, 0.30), -90.0], "tea_set": [Vector3(-0.55, 0.606, 0.95), 0.0]}
const DIGIT_DEG := 36.0
const DOOR_OPEN_DEG := 100.0

var room: Node3D
var zones: ArchiveZones
var root: Node3D
var logic: ArchiveLogic
var rig: ArchiveRig
var models: Dictionary = {}
var _lamp_item: Node3D
var _cups_up: Array[bool] = [false, false]
var _drawer_open := false


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
		n.name = "office_" + id
		models[id] = n
		(room.get("_roots") as Dictionary)[n] = "office_" + id
		(room.get("models") as Dictionary)["office_" + id] = n
		n.set_meta("hotspot", "")
		room.call("tune_shadows", n)
	var shell: Node3D = models["room_office"]
	for mi in ModelUtil.find_meshes(shell):
		if str(mi.name).begins_with("wall_") or str(mi.name) in ["ceiling", "floor", "rug", "sky_card"]:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	ArchiveRig.hot(models["strand_cabinet"], "off_cabinet")
	ArchiveRig.hot(models["tea_set"], "off_tea")
	ArchiveRig.hot(ModelUtil.find(shell, "IA_desk_drawer"), "off_desk")
	ArchiveRig.hot(ModelUtil.find(shell, "IA_door_gallery"), "off_door")
	ArchiveRig.hot(ModelUtil.find(shell, "desk"), "off_desk")
	_build_lights(shell)
	_build_cabinet()
	_build_views()
	zones.register("office", VIEWS, HOTSPOT_VIEW, DEEPER, CAPTION)
	apply_state(false)


func _build_views() -> void:
	var cam: RoomCamera = room.get("cam")
	var o := root.position
	cam.add_view("office", o + Vector3(-2.3, 1.6, 1.8), o + Vector3(1.2, 1.0, -0.6), 68.0, true)
	cam.add_view("cabinet", o + Vector3(1.05, 1.55, 0.3), o + Vector3(2.67, 1.4, 0.3), 46.0)
	cam.add_view("office_desk", o + Vector3(-1.5, 1.7, 1.6), o + Vector3(-0.4, 0.7, -0.2), 52.0)


func _build_lights(shell: Node3D) -> void:
	# cool white from the window, one green desk lamp, a little fire: no warm amber (that is the Night Cell's)
	var win := ModelUtil.find(shell, "light_window_n")
	ArchiveRig.omni(root, win.position if win != null else Vector3(0.4, 2.4, -2.1), Color("e6f0ff"), 1.8, 7.0)
	var lamp := ModelUtil.find(shell, "light_desk_lamp")
	ArchiveRig.omni(root, lamp.position if lamp != null else Vector3(0.05, 1.12, -1.25), Color("d8ffd0"), 1.1, 3.4)
	ArchiveRig.omni(root, Vector3(-0.5, 0.7, 2.0), Color("ffb070"), 0.5, 3.0) # the fireplace
	ArchiveRig.omni(root, Vector3(0.0, 2.9, 0.2), Color("dbe6ee"), 1.0, 7.5)
	ArchiveRig.omni(root, Vector3(1.8, 1.9, 0.3), Color("eef2ff"), 1.0, 3.6) # the cabinet is read from close up
	ArchiveRig.omni(root, Vector3(-0.8, 2.3, 1.0), Color("e8eeee"), 0.7, 4.0) # the tea table


func _build_cabinet() -> void:
	var cab: Node3D = models["strand_cabinet"]
	var label := ModelUtil.find(cab, "cabinet_label") as MeshInstance3D
	if label != null:
		var m := StandardMaterial3D.new()
		m.albedo_texture = ArchiveUpperArt.cabinet_label(int(logic.cabinet_label()))
		m.roughness = 0.5
		label.material_override = m
	var mount := ModelUtil.find(cab, "lamp_mount")
	_lamp_item = ModelUtil.spawn("projector_lamp", cab, Transform3D(Basis.IDENTITY, (mount.position if mount != null else Vector3(0, 0.952, 0)) + Vector3(0, 0.062, 0)), "none")
	if _lamp_item != null:
		_lamp_item.name = "Item_cabinet_lamp"
		_lamp_item.scale = Vector3.ONE * 1.6
		var body := StaticBody3D.new()
		var cs := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = Vector3(0.14, 0.2, 0.14)
		cs.shape = box
		body.add_child(cs)
		body.set_meta("part", "Item_cabinet_lamp")
		body.set_meta("hotspot", "off_lamp")
		_lamp_item.add_child(body)


# ====================================================================== state
func apply_state(animated: bool) -> void:
	var s := logic.state
	var cab: Node3D = models["strand_cabinet"]
	var shell: Node3D = models["room_office"]
	var wheels: Array = s["cab_wheels"]
	for i in 4:
		rig.rot(ModelUtil.find(cab, "IA_digit_%d" % i), Vector3.RIGHT, DIGIT_DEG * int(wheels[i]), animated, 0.25)
	var open: bool = bool(s["cab_open"])
	rig.rot(ModelUtil.find(cab, "IA_door_l"), Vector3.UP, -DOOR_OPEN_DEG if open else 0.0, animated, 0.8)
	rig.rot(ModelUtil.find(cab, "IA_door_r"), Vector3.UP, DOOR_OPEN_DEG if open else 0.0, animated, 0.8)
	var lamp_here: bool = open and not bool((s["taken"] as Dictionary).get("cabinet_lamp", false))
	if _lamp_item != null:
		room.call("set_present", _lamp_item, lamp_here)
	rig.slide(ModelUtil.find(shell, "IA_desk_drawer"), Vector3(0, 0, 0.3) if _drawer_open else Vector3.ZERO, animated, 0.35)
	var tea: Node3D = models["tea_set"]
	for k in 2:
		rig.slide(ModelUtil.find(tea, "IA_cup_%s" % ["a", "b"][k]), Vector3(0, 0.06, 0) if _cups_up[k] else Vector3.ZERO, animated, 0.3)


func on_enter() -> void:
	apply_state(false)


# ====================================================================== taps
## -> true when the tap was handled here.
func interact(hs: String, part: String) -> bool:
	var cam: RoomCamera = room.get("cam")
	var cur := cam.current()
	match hs:
		"off_cabinet":
			if cur != "cabinet":
				cam.go("cabinet")
			elif part.begins_with("IA_digit_"):
				logic.n10_turn_wheel(int(part.substr(9)), 1)
			else:
				_say("obj2x.cabinet")
			return true
		"off_lamp":
			if cur != "cabinet":
				cam.go("cabinet")
			elif logic.can_take("cabinet_lamp"):
				logic.take("cabinet_lamp")
			return true
		"off_tea":
			if cur != "office_desk":
				cam.go("office_desk")
			elif part.begins_with("IA_cup_"):
				var k := 0 if part.ends_with("a") else 1
				_cups_up[k] = not _cups_up[k]
				AudioManager.ui("ui_tap")
				apply_state(true)
			else:
				_say("obj2x.tea")
			return true
		"off_desk":
			if cur != "office_desk":
				cam.go("office_desk")
			elif part == "IA_desk_drawer":
				_drawer_open = not _drawer_open
				ArchiveZones.cue("fire_door", -4.0)
				if _drawer_open:
					(room.get("hud") as Node).call("message", room.tr("msg.empty_now"))
				apply_state(true)
			else:
				_say("obj2x.tea")
			return true
		"off_door":
			var door := ModelUtil.find(models["room_office"], "IA_door_gallery")
			rig.rot(door, Vector3.UP, 95.0, true, 0.5)
			ArchiveZones.cue("room_step")
			room.get_tree().create_timer(0.45).timeout.connect(func() -> void:
				if is_instance_valid(room):
					rig.rot(door, Vector3.UP, 0.0, false)
					logic.enter_room("gallery"))
			return true
	return false


func _say(key: String) -> void:
	(room.get("hud") as Node).call("message", room.tr(key))
	AudioManager.ui("ui_tap")


func feedback(e: String) -> bool:
	var name := e.get_slice(":", 0)
	match name:
		"cab_wheel":
			ArchiveZones.cue("c2x_cab_wheel", -2.0, randf_range(0.97, 1.05))
			return true
		"cab_opened":
			ArchiveZones.cue("c2x_cab_open")
			return true
	return false
