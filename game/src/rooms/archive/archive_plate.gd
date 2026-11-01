class_name ArchivePlate
extends RefCounted
## Chapter 2 expansion, room R6: the Plate Room (docs/CHAPTER2_EXPANSION.md sections 3, 7, 8 N9; models and pivots in
## docs/models/ch2_exp.md). A zone of the Archive scene (ArchiveZones): a darkroom with red safelights, glass plates in
## racks, a steel sink with trays, prints on a line, and the enlarger on its bench.
## It only renders ArchiveLogic's state and forwards taps to its actions:
## - N9 enlarger: four negative strips lie on the bench (tap one to load it into the carrier: `n9_load_strip`); the zoom knob
##   raises the head one step (`n9_zoom`), the focus ring turns one step (`n9_focus`), both wrap round at their ends; the
##   picture on the paper is drawn from this game's answers (ArchiveUpperArt.enlarger_image): blurred by the focus error,
##   scaled by the zoom error, with a fit frame printed on the easel, and the four pencilled digits only on the right print;
## - the print that develops in the tray (`print_ready`) can be read again from the tray;
## - the way out: the door to the Gallery;
## - the enlarger's fan loop (c2x_enlarger_fan) while the player is in the room.
## The floor is plain dark linoleum (the model's QA checker is replaced), the lights are red safelights plus the enlarger lamp.

const VIEWS: Array[String] = ["plate", "enlarger", "trays"]
const HOTSPOT_VIEW := {"plate_enl": "enlarger", "plate_strip_0": "enlarger", "plate_strip_1": "enlarger", "plate_strip_2": "enlarger",
	"plate_strip_3": "enlarger", "plate_door": "plate", "plate_trays": "trays", "plate_racks": "plate"}
const DEEPER := {}
const CAPTION := {"plate": "room2x.plate", "enlarger": "obj2x.enlarger", "trays": "obj2x.strips"}
const PLACE := {"room_plate": [Vector3.ZERO, 0.0], "enlarger": [Vector3(0.20, 0.90, -2.20), 0.0]}
const STRIP_AT: Array[Vector3] = [Vector3(-0.62, 0.925, -2.43), Vector3(-0.62, 0.925, -2.31), Vector3(-0.62, 0.925, -2.19), Vector3(-0.62, 0.925, -2.07)]
const ZOOM_STEP_M := 0.04
const KNOB_DEG := 55.0
const FOCUS_DEG := 40.0
const SLOT := Vector3(0.05, 0.69, 0.10) # the carrier, in enlarger coordinates (at zoom 0)
const DOOR_OPEN_DEG := 95.0

var room: Node3D
var zones: ArchiveZones
var root: Node3D
var logic: ArchiveLogic
var rig: ArchiveRig
var models: Dictionary = {}
var _strips: Array[Node3D] = []
var _enl_light: OmniLight3D
var _print_quad: MeshInstance3D
var _proj_mat: StandardMaterial3D
var _loaded := -2


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
		n.name = "plate_" + id
		models[id] = n
		(room.get("_roots") as Dictionary)[n] = "plate_" + id
		(room.get("models") as Dictionary)["plate_" + id] = n
		n.set_meta("hotspot", "")
		room.call("tune_shadows", n)
	var shell: Node3D = models["room_plate"]
	for mi in ModelUtil.find_meshes(shell):
		if str(mi.name).begins_with("wall_") or str(mi.name) in ["ceiling", "beams", "floor"]:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_linoleum(shell)
	ArchiveRig.hot(models["enlarger"], "plate_enl")
	ArchiveRig.hot(ModelUtil.find(shell, "IA_door_gallery"), "plate_door")
	ArchiveRig.hot(ModelUtil.find(shell, "trays"), "plate_trays")
	ArchiveRig.hot(ModelUtil.find(shell, "sink_bench"), "plate_trays")
	_build_lights(shell)
	_build_strips()
	_build_prints()
	_build_views()
	zones.register("plate", VIEWS, HOTSPOT_VIEW, DEEPER, CAPTION)
	apply_state(false)


## The model's floor uses the hall's green and cream chequered linoleum; a darkroom's is plain dark linoleum, flecked and a
## little glossy (it catches the safelights), drawn here.
func _linoleum(shell: Node3D) -> void:
	var floor_mesh := ModelUtil.find(shell, "floor") as MeshInstance3D
	if floor_mesh == null or floor_mesh.mesh == null:
		return
	var rng := RandomNumberGenerator.new()
	rng.seed = 4711
	var img := Image.create(256, 256, false, Image.FORMAT_RGB8)
	for y in 256:
		for x in 256:
			var v := 0.15 + rng.randf_range(-0.012, 0.012)
			if rng.randf() < 0.025:
				v += rng.randf_range(0.04, 0.09)
			img.set_pixel(x, y, Color(v * 1.05, v, v * 0.97))
	var m := StandardMaterial3D.new()
	m.albedo_texture = ImageTexture.create_from_image(img)
	m.roughness = 0.42
	m.metallic_specular = 0.6
	m.uv1_scale = Vector3(3.0, 3.0, 1.0)
	for i in floor_mesh.mesh.get_surface_count():
		floor_mesh.set_surface_override_material(i, m)


func _build_views() -> void:
	var cam: RoomCamera = room.get("cam")
	var o := root.position
	cam.add_view("plate", o + Vector3(-0.9, 1.65, 2.1), o + Vector3(0.6, 1.1, -1.4), 68.0, true)
	cam.add_view("enlarger", o + Vector3(0.0, 1.5, -0.55), o + Vector3(0.0, 1.25, -2.2), 64.0)
	cam.add_view("trays", o + Vector3(1.0, 1.7, 0.5), o + Vector3(2.6, 0.8, -0.4), 56.0)


func _build_lights(shell: Node3D) -> void:
	for nm in ["light_safelight_a", "light_safelight_b", "light_safelight_c"]:
		var n := ModelUtil.find(shell, nm)
		if n != null:
			ArchiveRig.omni(root, n.position, Color("ff2a14"), 1.1, 6.0)
	ArchiveRig.omni(root, Vector3(0.0, 2.3, -1.2), Color("ff4a2a"), 0.7, 4.0) # the bench is worked at from close up
	ArchiveRig.omni(root, Vector3(1.8, 2.0, 0.3), Color("ff3a20"), 0.6, 4.0) # the trays
	_enl_light = ArchiveRig.omni(root, Vector3(0.25, 1.5, -2.1), Color("ffd8a0"), 0.0, 2.2)


# ---------------------------------------------------------------------- the strips
func _build_strips() -> void:
	# a pale sleeve under the four strips: film is dark and the bench is black, in red light nothing else would show them
	var pad := MeshInstance3D.new()
	var pm := BoxMesh.new()
	pm.size = Vector3(0.40, 0.006, 0.60)
	pad.mesh = pm
	pad.position = Vector3(-0.62, 0.915, -2.25)
	var padm := StandardMaterial3D.new()
	padm.albedo_color = Color("d9d2c0")
	padm.roughness = 0.9
	pad.material_override = padm
	pad.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(pad)
	for i in ArchiveExpData.STRIPS:
		var xf := Transform3D(Basis.IDENTITY, STRIP_AT[i])
		var n := ModelUtil.spawn("negative_strip", root, xf, "parts")
		if n == null:
			_strips.append(null)
			continue
		n.name = "plate_strip_%d" % i
		(room.get("models") as Dictionary)[n.name] = n
		var sym := int(logic.state["v_strips"][i])
		var frames := ModelUtil.find(n, "strip_frames") as MeshInstance3D
		if frames != null:
			var m := StandardMaterial3D.new()
			m.albedo_texture = ArchiveUpperArt.strip_texture(sym, _order_for(i))
			m.roughness = 0.5
			frames.material_override = m
		n.scale = Vector3.ONE * 1.5 # 0.30 m long: the edge symbol can be read from the bench view
		n.set_meta("rest", n.transform)
		ArchiveRig.hot(n, "plate_strip_%d" % i)
		_strips.append(n)


## Four staff members on strip i: every strip carries different people, the one at frame 0 is the strip's own subject.
func _order_for(i: int) -> Array:
	var sym := int(logic.state["v_strips"][i])
	var order: Array = [sym]
	for k in 6:
		var who := (sym + 1 + k) % 6
		if order.size() < 4 and who != sym:
			order.append(who)
	return order


func _build_prints() -> void:
	var trays := ModelUtil.find(models["room_plate"], "trays")
	_print_quad = ArchiveRig.picture(root, null, Vector2(0.22, 0.17), Vector3(2.62, 0.845, -0.55), Color(0.85, 0.82, 0.78), false)
	_print_quad.rotation_degrees.x = -90.0
	_print_quad.visible = false
	room.call("add_tap_area", _print_quad, Vector3(0.24, 0.19, 0.08), "plate_trays", "Print", Vector3.ZERO)
	if trays == null:
		return


# ====================================================================== state
func apply_state(animated: bool) -> void:
	var s := logic.state
	var enl: Node3D = models["enlarger"]
	var zoom := int(s["en_zoom"])
	var focus := int(s["en_focus"])
	var strip := int(s["en_strip"])
	var lift := Vector3(0, ZOOM_STEP_M * zoom, 0)
	rig.slide(ModelUtil.find(enl, "IA_head"), lift, animated, 0.3)
	rig.pose(ModelUtil.find(enl, "IA_zoom_knob"), lift, Vector3.RIGHT, KNOB_DEG * zoom, animated, 0.3)
	rig.pose(ModelUtil.find(enl, "IA_focus_ring"), lift, Vector3.UP, FOCUS_DEG * focus, animated, 0.3)
	# the strips: the loaded one lies in the carrier, the others on the bench
	for i in _strips.size():
		var n := _strips[i]
		if n == null:
			continue
		var target: Vector3 = (enl.position + SLOT + lift + Vector3(0, 0.005, 0)) if i == strip else STRIP_AT[i]
		if animated and zones.current == "plate" and n.position.distance_to(target) > 0.001:
			room.create_tween().tween_property(n, "position", target, 0.4).set_trans(Tween.TRANS_SINE)
		else:
			n.position = target
		n.scale = Vector3.ONE * (1.0 if i == strip else 1.5)
	# the lamp and the picture on the paper
	var proj := ModelUtil.find(enl, "projected_image") as MeshInstance3D
	if proj != null:
		proj.visible = strip >= 0
		if strip >= 0:
			var img := logic.enlarger_image()
			var blur := mini(absi(focus - int(s["v_pfocus"])) * 2, 12)
			var scl := 1.0 + 0.22 * float(zoom - int(s["v_zoom"]))
			var digits: Array = logic.cabinet_digits() if img["digits"] else []
			if _proj_mat == null:
				_proj_mat = StandardMaterial3D.new()
				_proj_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
				proj.material_override = _proj_mat
			_proj_mat.albedo_texture = ArchiveUpperArt.enlarger_image(int(img["strip"]), blur, scl, digits)
			_proj_mat.albedo_color = Color(0.92, 0.86, 0.8)
	if _enl_light != null:
		_enl_light.light_energy = 1.1 if strip >= 0 else 0.0
	if strip != _loaded and _loaded != -2 and strip >= 0 and animated:
		ArchiveZones.cue("c2x_enlarger_lamp")
	_loaded = strip
	if _print_quad != null:
		var done: bool = bool(s["print_ok"])
		room.call("set_present", _print_quad, done)
		if done and _print_quad.material_override != null and (_print_quad.material_override as StandardMaterial3D).albedo_texture == null:
			(_print_quad.material_override as StandardMaterial3D).albedo_texture = ArchiveUpperArt.staff_print(int(logic.cabinet_label()), logic.cabinet_digits())


func on_enter() -> void:
	apply_state(false)
	AudioManager.sfx_loop("c2x_enlarger_fan", true, -14.0)


func on_exit() -> void:
	AudioManager.sfx_loop("c2x_enlarger_fan", false)


# ====================================================================== taps
## -> true when the tap was handled here.
func interact(hs: String, part: String) -> bool:
	var cam: RoomCamera = room.get("cam")
	var cur := cam.current()
	if hs.begins_with("plate_strip_"):
		if cur != "enlarger":
			cam.go("enlarger")
		else:
			logic.n9_load_strip(int(hs.substr(12)))
		return true
	match hs:
		"plate_enl":
			if cur != "enlarger":
				cam.go("enlarger")
			elif part == "IA_zoom_knob":
				logic.n9_zoom(1 if int(logic.state["en_zoom"]) < ArchiveExpData.ENL_ZOOM_STEPS - 1 else -(ArchiveExpData.ENL_ZOOM_STEPS - 1))
			elif part == "IA_focus_ring":
				logic.n9_focus(1 if int(logic.state["en_focus"]) < ArchiveExpData.ENL_FOCUS_STEPS - 1 else -(ArchiveExpData.ENL_FOCUS_STEPS - 1))
			elif part == "projected_image" and _proj_mat != null and _proj_mat.albedo_texture != null:
				(room.get("hud") as Node).call("_show_zoom", _proj_mat.albedo_texture, room.tr("obj2x.enlarger"))
			else:
				_say("obj2x.enlarger")
			return true
		"plate_door":
			var door := ModelUtil.find(models["room_plate"], "IA_door_gallery")
			rig.rot(door, Vector3.UP, DOOR_OPEN_DEG, true, 0.5)
			ArchiveZones.cue("room_step")
			room.get_tree().create_timer(0.45).timeout.connect(func() -> void:
				if is_instance_valid(room):
					rig.rot(door, Vector3.UP, 0.0, false)
					logic.enter_room("gallery"))
			return true
		"plate_trays":
			if cur != "trays":
				cam.go("trays")
			elif part == "Print":
				(room.get("hud") as Node).call("show_document", "staff_print")
			else:
				_say("obj2x.strips")
			return true
	return false


func _say(key: String) -> void:
	(room.get("hud") as Node).call("message", room.tr(key))
	AudioManager.ui("ui_tap")


func feedback(e: String) -> bool:
	var name := e.get_slice(":", 0)
	match name:
		"enl_zoom":
			ArchiveZones.cue("c2x_enlarger_knob", -2.0)
			return true
		"enl_focus":
			ArchiveZones.cue("c2x_enlarger_focus", -2.0)
			return true
		"print_other":
			ArchiveZones.cue("c2x_enlarger_knob", -6.0)
			return true
		"print_ready":
			ArchiveZones.cue("c2x_print_ready")
			return true
	return false
