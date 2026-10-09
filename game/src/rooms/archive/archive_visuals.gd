class_name ArchiveVisuals
extends Node
## Renders ArchiveLogic state onto the Chapter 2 models: part poses, items in their places, lamps, the
## film/slide projection, the vault overlay and the cinematic moments. Everything visible is derived from
## logic.state (plus a few purely visual toggles such as an opened tray door), so a loaded save reproduces
## the scene. Axes and angles follow docs/models/ch2.md.

const CAT_DRAWER_TRAVEL := 0.40 # the whole tray clears the carcass, so the back sections can be seen
const DIVIDER_TILT_DEG := 20.0
const VALVE_STEP_DEG := -72.0
const GAUGE_STEP_DEG := -22.5
const DEST_STEP_DEG := -60.0
const PORT_FLAP_OPEN_DEG := 80.0
const TRAY_DOOR_OPEN_DEG := 75.0
const PUNCH_KEY_DOWN := -0.006
const LEVER_PULL_DEG := 55.0
const PUNCH_LEVER_DEG := 60.0
const PLAY_PRESS_DEG := -8.0
const VU_MAX_DEG := -80.0
const LOCKER_OPEN_DEG := -105.0
const GRILLE_OPEN_DEG := -100.0
const HATCH_OPEN_DEG := -105.0
const LEDGER_SLIDE := 0.20
const LEDGER_COVER_DEG := -110.0
const BOOTH_DOOR_OPEN_DEG := -100.0
const RUN_LEVER_DEG := 40.0
const FOCUS_STEP_DEG := -30.0
const SLIDE_DRAWER_TRAVEL := 0.28
const SLIDE_LAMP_DEG := 30.0
const CASE_LID_DEG := -105.0
const VAULT_DOOR_OPEN_DEG := -95.0
const VAULT_HANDLE_STEP_DEG := -120.0
const BOLT_TRAVEL := 0.08
const COLLAR_STEP_DEG := -45.0
const ZOOM_STEP_DEG := -40.0
const CLAMP_DROP := -0.03
const SHUTTER_OPEN_Y := 2.25
## Fallback tube path (docs/models/ch2.md §1) if the room model's empties are missing.
const TUBE_PATH := [Vector3(4.80, 2.35, -1.40), Vector3(4.80, 3.25, -1.40), Vector3(0.0, 3.25, -1.40),
	Vector3(0.0, 3.25, 0.25), Vector3(0.0, 2.25, 0.25)]
const DECALS := "res://assets/textures/decals/ch2/"
const TAPE_SPOTS := {"tape_1996": "grille_reel", "tape_1997": "ledger_reel", "tape_1998": "hatch_reel"}

var room: Node3D
var logic: ArchiveLogic
var rest: Dictionary = {} # node -> rest Transform3D
var tray_open := false # tube station receive tray door (visual only)
var case_open := false # booth lens case lid (visual only)
var held_frame := -1 # splicer strip picked up by the player
var _tweens: Dictionary = {}
var _items: Dictionary = {} # spot -> Node3D (take-able items in their places)
var _held: Dictionary = {} # key -> [model, Node3D] (items sitting in devices)
var _tray: Node3D # catalogue drawer contents
var _card_labels: Array[Label3D] = []
var _screen_mat: ShaderMaterial
var _disc_mat: ShaderMaterial
var _beams: Dictionary = {} # "film" / "slide" -> MeshInstance3D
var _flying := false
var _film_override := -1 # frame index forced by the film cinematic
var _secret_on := false
var _tape_playing := false
var _tape_t := 0.0
var _compressor_on := false
var _receiver_on := false
var _receiver_level := 0
var _beep_t := 0.0
var _static: AudioStreamPlayer
var _textures: Dictionary = {}


func _init(r: Node3D) -> void:
	room = r
	logic = r.get("logic")


func _ready() -> void:
	_record_rest()
	_spawn_take_items()
	_build_screen()
	_build_disc()
	_tray = ModelUtil.spawn("catalogue_tray", room, Transform3D.IDENTITY, "parts")
	if _tray:
		_tray.visible = false
		_record(_tray)
	_compressor_on = logic.state["pressure_ok"]


# ====================================================================== lookups
func model(id: String) -> Node3D:
	return (room.get("models") as Dictionary).get(id)


func part(model_id: String, name: String) -> Node3D:
	return ModelUtil.find(model(model_id), name)


func _record_rest() -> void:
	for m: Node3D in (room.get("models") as Dictionary).values():
		_record(m)


func _record(n: Node) -> void:
	if n is Node3D and not rest.has(n):
		rest[n] = (n as Node3D).transform
	for c in n.get_children():
		if c is Node3D and not (c is StaticBody3D):
			_record(c)


func _tex(path: String) -> Texture2D:
	if _textures.has(path):
		return _textures[path]
	var t: Texture2D = load(path) if ResourceLoader.exists(path) else null
	_textures[path] = t
	return t


# ====================================================================== items
func _spawn_item(spot: String, item_model: String, mount: Node3D) -> Node3D:
	if mount == null:
		return null
	var n := ModelUtil.spawn(item_model, mount, Transform3D.IDENTITY, "none")
	if n == null:
		return null
	n.name = "Item_" + spot
	_add_item_collider(n, "Item_" + spot)
	_items[spot] = n
	return n


func _add_item_collider(n: Node3D, part_name: String) -> void:
	var aabb := ItemIcons._aabb(n)
	var body := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = (aabb.size + Vector3.ONE * 0.03).max(Vector3.ONE * 0.06)
	cs.shape = box
	cs.position = n.global_transform.affine_inverse() * aabb.get_center() if n.is_inside_tree() else aabb.get_center()
	body.add_child(cs)
	body.set_meta("part", part_name)
	n.add_child(body)


func _spawn_take_items() -> void:
	_spawn_item("canister_file", "file_folder", part("tube_station", "file_mount"))
	_spawn_item("canister_key", "locker_key", part("tube_station", "key_mount"))
	_spawn_item("locker_receiver", "pocket_receiver", part("lockers", "receiver_mount"))
	for tape: String in TAPE_SPOTS:
		var spot: String = TAPE_SPOTS[tape]
		var n := _spawn_item(spot, "tape_reel", part(_tape_host(spot), spot + "_mount"))
		ItemDress.apply(tape, n)
	_spawn_item("splicer_reel", "film_reel", part("film_splicer", "splicer_reel_mount"))
	_spawn_item("case_crystal_1", "lumen_crystal", part("lens_case", "crystal_mount_1"))
	_spawn_item("case_crystal_2", "lumen_crystal", part("lens_case", "crystal_mount_2"))
	_spawn_item("slide_mark", "glass_slide", part("slide_cabinet", "slide_mark_mount"))


func _tape_host(spot: String) -> String:
	return {"grille_reel": "vent_grille", "ledger_reel": "stacks_shelving", "hatch_reel": "floor_hatch"}[spot]


## An item sitting in a device (not a take spot): one instance per key, re-spawned if its model changes.
func _held_item(key: String, item_id: String, mount: Node3D, show: bool, part_name: String = "") -> Node3D:
	var cur: Array = _held.get(key, [])
	var want := item_id if show else ""
	if not cur.is_empty() and cur[0] != want:
		(cur[1] as Node3D).queue_free()
		_held.erase(key)
		cur = []
	if want == "" or mount == null:
		return null
	if cur.is_empty():
		var n := ModelUtil.spawn(ItemDB.model_path(item_id), mount, Transform3D.IDENTITY, "none")
		if n == null:
			return null
		if part_name != "":
			_add_item_collider(n, part_name)
		ItemDress.apply(item_id, n, logic)
		if logic.item_glows(item_id) and item_id == "crystal_lens":
			_glow(n, true)
		_held[key] = [want, n]
		return n
	return cur[1]


# ====================================================================== main entry
func apply_state(animated: bool) -> void:
	var s := logic.state
	_apply_catalogue(animated)
	# compressor
	for i in 3:
		_rot(part("compressor_panel", "IA_valve_" + "abc"[i]), Vector3.BACK, VALVE_STEP_DEG * int(s["valves"][i]), animated, 0.3)
	_rot(part("compressor_panel", "needle_p"), Vector3.BACK, GAUGE_STEP_DEG * logic.pressure(), animated, 0.9)
	_rot(part("compressor_panel", "needle_f"), Vector3.BACK, GAUGE_STEP_DEG * logic.flow(), animated, 0.9)
	_lamp(part("tube_station", "lamp_status"), true, Color("4dff7a") if s["pressure_ok"] else Color("ff3b2f"))
	# tube station
	_rot(part("tube_station", "IA_dest_dial"), Vector3.BACK, DEST_STEP_DEG * int(s["dest"]), animated, 0.25)
	_rot(part("tube_station", "port_flap"), Vector3.RIGHT, PORT_FLAP_OPEN_DEG if s["canister"] != "" else 0.0, animated, 0.3)
	var can := _held_item("canister", "canister", part("tube_station", "canister_mount"), not _flying)
	if can:
		can.visible = not _flying
	_rot(part("tube_station", "tray_door"), Vector3.RIGHT, TRAY_DOOR_OPEN_DEG if tray_open else 0.0, animated, 0.35)
	# punch
	for i in 8:
		_slide(part("card_punch", "IA_punch_key_%d" % i), Vector3(0, PUNCH_KEY_DOWN if int(s["punch_keys"][i]) == 1 else 0.0, 0), animated, 0.08)
	var cip := part("card_punch", "card_in_punch")
	if cip:
		cip.visible = s["card_in_punch"]
	# tape deck
	_rot(part("tape_deck", "IA_speed"), Vector3.BACK, 45.0 - 30.0 * int(s["deck_speed"]), animated, 0.2)
	_held_item("deck_reel", s["deck_tape"], part("tape_deck", "deck_reel_mount"), s["deck_tape"] != "")
	# lockers + hiding places
	_rot(part("lockers", "IA_locker_%d" % ArchiveLogic.LOCKER_LEYLA), Vector3.UP, LOCKER_OPEN_DEG if s["locker_open"] else 0.0, animated, 0.9)
	_rot(part("vent_grille", "IA_grille"), Vector3.UP, GRILLE_OPEN_DEG if s["grille_open"] else 0.0, animated, 0.8)
	_slide(part("stacks_shelving", "IA_ledger"), Vector3(0, 0, LEDGER_SLIDE if s["ledger_open"] else 0.0), animated, 0.6)
	_rot(part("stacks_shelving", "ledger_cover"), Vector3.RIGHT, LEDGER_COVER_DEG if s["ledger_open"] else 0.0, animated, 0.8)
	_rot(part("floor_hatch", "IA_hatch"), Vector3.RIGHT, HATCH_OPEN_DEG if s["hatch_open"] else 0.0, animated, 1.1)
	# booth door + dial
	_rot(part("booth_door", "IA_booth_door"), Vector3.UP, BOOTH_DOOR_OPEN_DEG if s["booth_open"] else 0.0, animated, 1.6)
	_lamp(part("booth_door", "booth_door_lamp"), true, Color("4dff7a") if s["booth_open"] else Color("ff3b2f"))
	_apply_splicer(animated)
	# film projector
	_held_item("feed_reel", "film_reel", part("film_projector", "feed_reel_mount"), s["reel_on_projector"])
	_rot(part("film_projector", "IA_run_lever"), Vector3.RIGHT, RUN_LEVER_DEG if s["projector_on"] else 0.0, animated, 0.3)
	_rot(part("film_projector", "IA_focus_ring"), Vector3.BACK, FOCUS_STEP_DEG * int(s["focus"]), animated, 0.25)
	_lamp(part("film_projector", "lamp_glow"), s["projector_on"], Color("ffe2b0"))
	# slides
	for i in ArchiveLogic.SLIDE_DRAWERS:
		_slide(part("slide_cabinet", "IA_slide_drawer_%d" % i), Vector3(0, 0, SLIDE_DRAWER_TRAVEL if int(s["slide_drawer"]) == i else 0.0), animated, 0.5)
	var gate := _held_item("gate_slide", "emblem_slide", part("slide_projector", "slide_gate_mount"), s["slide_in"])
	if gate:
		_to(gate, Transform3D(Basis(Vector3.BACK, deg_to_rad(-90.0 * int(s["slide_rot"]))), Vector3.ZERO), animated, 0.3)
	_rot(part("slide_projector", "IA_slide_lamp"), Vector3.RIGHT, SLIDE_LAMP_DEG if s["slide_on"] else 0.0, animated, 0.15)
	_lamp(part("slide_projector", "lamp_glow"), s["slide_on"], Color("fff1d6"))
	# lens case
	_rot(part("lens_case", "IA_case_lid"), Vector3.RIGHT, CASE_LID_DEG if case_open else 0.0, animated, 0.6)
	# take-able items: present only while reachable and not taken
	for spot: String in _items:
		var reach := logic.can_take(spot) and not (_flying and spot.begins_with("canister_"))
		if spot.begins_with("canister_"):
			reach = reach and tray_open
		if spot.begins_with("case_crystal"):
			reach = reach and case_open
		room.call("set_present", _items[spot], reach)
	_apply_screen()
	_apply_vault(animated)
	_apply_echoes()
	_apply_lights(animated)


func _apply_catalogue(animated: bool) -> void:
	var s := logic.state
	var open := int(s["cat_drawer"])
	for i in 10:
		_slide(part("card_catalogue", "IA_cat_drawer_%d" % i), Vector3(0, 0, CAT_DRAWER_TRAVEL if open == i else 0.0), animated, 0.45)
	if _tray == null:
		return
	if open < 0:
		_tray.visible = false
		return
	var mount := part("card_catalogue", "cat_tray_mount_%d" % open)
	if mount and _tray.get_parent() != mount:
		_tray.reparent(mount, false)
		_tray.transform = Transform3D.IDENTITY
	_tray.visible = true
	var g := int(s["cat_group"])
	for d in 10:
		_rot(ModelUtil.find(_tray, "IA_divider_%d" % d), Vector3.RIGHT, DIVIDER_TILT_DEG if d == g else 0.0, animated, 0.25)
	for l in _card_labels:
		l.queue_free()
	_card_labels.clear()
	var leyla_taken: bool = s["taken"].get("index_card", false)
	# The picked section rises only in the close-up. In the tray view it stays down, so the raised cards never
	# hide the dividers behind them and the player can always pick another section.
	var cam: RoomCamera = room.get("cam")
	var raised := g >= 0 and cam != null and cam.current() == "cat_section"
	for n in 10:
		var card := ModelUtil.find(_tray, "IA_card_%d" % n)
		if card == null:
			continue
		var base: Transform3D = rest.get(card, card.transform)
		if not raised:
			_to(card, base, animated, 0.3)
			room.call("set_present", card, not (open == ArchiveLogic.CAT_DRAWER and n == ArchiveLogic.CAT_CARD
				and leyla_taken))
			continue
		var divider := ModelUtil.find(_tray, "IA_divider_%d" % g)
		var z := (divider.position.z if divider else 0.0) - 0.006 - n * 0.0026
		# The picked section rises out of the tray in two rows (cards 5–9 a step higher), so all ten staggered tabs
		# stand clear of the dividers in front and of each other, and each one can be tapped.
		var lift := 0.055 + (0.02 if n >= 5 else 0.0)
		var is_leyla := open == ArchiveLogic.CAT_DRAWER and g == ArchiveLogic.CAT_GROUP and n == ArchiveLogic.CAT_CARD
		if is_leyla and s["card_shown"]:
			lift = 0.11
		var target := Transform3D(base.basis, Vector3(base.origin.x, base.origin.y + lift, z))
		_to(card, target, animated, 0.3)
		room.call("set_present", card, not (is_leyla and leyla_taken))
		var lbl := Label3D.new()
		lbl.text = "%d%d" % [g, n] if not (is_leyla and s["card_shown"]) else "%02d%d%d" % [open, g, n]
		lbl.font_size = 64
		lbl.pixel_size = 0.00018
		lbl.modulate = Color("2b2118")
		lbl.outline_size = 0
		lbl.shaded = false
		lbl.double_sided = false
		var tab_x := [-0.05, -0.025, 0.0, 0.025, 0.05][n % 5] as float
		lbl.position = Vector3(tab_x, 0.081, 0.0008)
		card.add_child(lbl)
		_card_labels.append(lbl)


## The cat_drawer view follows the open drawer (each drawer sits at a different height/column).
func frame_cat_drawer(i: int) -> void:
	var cam: RoomCamera = room.get("cam")
	var cat := model("card_catalogue")
	var tray := _cat_tray_open_xform(i)
	if cat == null or tray == Transform3D():
		return
	# Look down into the pulled-out tray from just above its front edge, so the divider tabs fill the screen.
	var out := cat.global_basis.z.normalized()
	var c: Vector3 = tray * Vector3(0, 0.06, 0)
	cam.add_view("cat_drawer", c + out * 0.26 + Vector3(0, 0.34, 0), c - out * 0.03, 46.0)


## Close-up of the raised section behind divider g: the card tabs are small, so the camera comes in until each
## tab is a comfortable finger target on a phone. Back returns to the tray.
func frame_cat_section(g: int) -> void:
	var cam: RoomCamera = room.get("cam")
	var cat := model("card_catalogue")
	var tray := _cat_tray_open_xform(int(logic.state["cat_drawer"]))
	var divider := ModelUtil.find(_tray, "IA_divider_%d" % g) if _tray else null
	if cat == null or tray == Transform3D() or divider == null:
		return
	var out := cat.global_basis.z.normalized()
	var rest_z: float = (rest.get(divider, divider.transform) as Transform3D).origin.z
	var focus: Vector3 = tray * Vector3(0, 0.135, rest_z - 0.02)
	cam.add_view("cat_section", focus + out * 0.16 + Vector3(0, 0.13, 0), focus - out * 0.01, 42.0)


## The tray's transform once drawer i is fully open. The tray rides on the drawer, which may still be sliding,
## so this is computed from the drawer's rest pose plus its travel.
func _cat_tray_open_xform(i: int) -> Transform3D:
	var cat := model("card_catalogue")
	var drawer := part("card_catalogue", "IA_cat_drawer_%d" % i)
	var mount := part("card_catalogue", "cat_tray_mount_%d" % i)
	if cat == null or drawer == null or mount == null or not drawer.is_ancestor_of(mount):
		return Transform3D()
	var open_pose: Transform3D = drawer.get_parent().global_transform * (rest.get(drawer, drawer.transform) as Transform3D)
	open_pose.origin += cat.global_basis.z.normalized() * CAT_DRAWER_TRAVEL
	return open_pose * (drawer.global_transform.affine_inverse() * mount.global_transform)


func _apply_splicer(animated: bool) -> void:
	var s := logic.state
	var sp: Array = s["splice"]
	for k in 4:
		var strip := part("film_splicer", "IA_frame_%d" % k)
		if strip == null:
			continue
		var base: Transform3D = rest.get(strip, strip.transform)
		var slot := sp.find(k)
		var target := base
		if slot >= 0:
			var mount := part("film_splicer", "slot_mount_%d" % slot)
			if mount:
				target = strip.get_parent().global_transform.affine_inverse() * mount.global_transform
		elif held_frame == k:
			target = Transform3D(base.basis, base.origin + Vector3(0, 0.025, 0))
		_to(strip, target, animated, 0.3)
	_lamp(part("film_splicer", "light_box_glass"), s["booth_open"], Color("fff4dc"))


func _apply_screen() -> void:
	if _screen_mat == null:
		return
	var s := logic.state
	var img := logic.screen_image()
	var film_on := img.begins_with("film:") or img == "mixed"
	var frame := int(s["frame"]) if _film_override < 0 else _film_override
	if _secret_on:
		_screen_mat.set_shader_parameter("image", _tex(DECALS + "film_secret.jpg"))
	elif film_on:
		_screen_mat.set_shader_parameter("image", _tex(DECALS + "film_frame_%d.jpg" % frame))
	_screen_mat.set_shader_parameter("image_on", 1.0 if (film_on or _secret_on) else 0.0)
	_screen_mat.set_shader_parameter("white", 1.0 if img == "white" else 0.0)
	var slide: bool = s["slide_on"] and s["slide_in"]
	_screen_mat.set_shader_parameter("slide_on", 1.0 if slide else 0.0)
	_screen_mat.set_shader_parameter("slide_rot", deg_to_rad(90.0 * int(s["slide_rot"])))
	var defocus := absf(float(int(s["focus"]) - ArchiveLogic.FOCUS_SHARP)) / 4.0
	_screen_mat.set_shader_parameter("blur", clampf(defocus, 0.0, 1.0) if not _secret_on else 0.0)
	_set_beam("film", s["projector_on"], part("film_projector", "lens_origin"))
	_set_beam("slide", slide, part("slide_projector", "lens_origin"))
	var beam_light: SpotLight3D = (room.get("lights") as Dictionary).get("beam")
	if beam_light:
		beam_light.light_energy = 1.4 if (s["projector_on"] or slide) else 0.0
	var ring := part("projection_screen", "socket_ring") as MeshInstance3D
	if ring:
		ModelUtil.set_emission(ring, s["socket"] != "", Color("cff6ff"), 2.0)
	var sock_item: String = s["socket"]
	var c := _held_item("socket", sock_item, part("projection_screen", "socket_mount"), sock_item != "", "Item_socket")
	if c and logic.crystal_image(sock_item) != "":
		ItemDress.glyph(c, logic.crystal_image(sock_item))


func _build_screen() -> void:
	var surf := part("projection_screen", "screen_surface") as MeshInstance3D
	if surf == null:
		return
	_screen_mat = ShaderMaterial.new()
	_screen_mat.shader = load("res://src/fx/screen_projection.gdshader")
	_screen_mat.set_shader_parameter("slide", _tex(DECALS + "glyph_mark.png"))
	surf.material_override = _screen_mat


## A soft additive cone from a projector lens to the screen centre.
func _set_beam(key: String, on: bool, lens: Node3D) -> void:
	var b: MeshInstance3D = _beams.get(key)
	if not on or lens == null:
		if b:
			b.visible = false
		return
	var screen := part("projection_screen", "screen_surface")
	var to := screen.global_position if screen else Vector3(-2.5, 1.9, -3.43)
	var from := lens.global_position
	var length := from.distance_to(to)
	if b == null:
		b = MeshInstance3D.new()
		var cyl := CylinderMesh.new()
		cyl.top_radius = 0.035
		cyl.bottom_radius = 0.9 if key == "film" else 0.75
		cyl.height = 1.0
		cyl.radial_segments = 20
		cyl.rings = 1
		cyl.cap_top = false
		cyl.cap_bottom = false
		b.mesh = cyl
		var m := ShaderMaterial.new()
		m.shader = load("res://src/fx/lumen_beam.gdshader")
		m.set_shader_parameter("color", Color(1.0, 0.96, 0.86, 1.0))
		m.set_shader_parameter("energy", 0.22)
		b.material_override = m
		b.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		room.add_child(b)
		_beams[key] = b
	b.visible = true
	var dir := (to - from).normalized()
	b.global_basis = Basis(Quaternion(Vector3.DOWN, dir)).scaled(Vector3(1, length, 1))
	b.global_position = (from + to) * 0.5


func _build_disc() -> void:
	var disc := part("vault_door", "glass_disc") as MeshInstance3D
	if disc == null:
		return
	_disc_mat = ShaderMaterial.new()
	_disc_mat.shader = load("res://src/fx/vault_overlay.gdshader")
	_disc_mat.set_shader_parameter("engraving", _tex(DECALS + "vault_engraving.png"))
	disc.material_override = _disc_mat


func _apply_vault(animated: bool) -> void:
	var s := logic.state
	for side in ["left", "right"]:
		var id: String = s["port_" + side]
		var n := _held_item("port_" + side, id, part("vault_door", "port_%s_mount" % side), id != "", "Item_port_" + side)
		var img := logic.crystal_image(id)
		if n and img != "" and id != "crystal_lens":
			ItemDress.glyph(n, img)
		var pipe := part("vault_door", "light_pipe_" + side) as MeshInstance3D
		if pipe:
			ModelUtil.set_emission(pipe, img != "", Color("cff6ff"), 2.5)
		if _disc_mat:
			_disc_mat.set_shader_parameter(side + "_on", 1.0 if img != "" else 0.0)
			if img != "":
				_disc_mat.set_shader_parameter(side + "_img", _tex(DECALS + "glyph_%s.png" % img))
	if _disc_mat:
		_disc_mat.set_shader_parameter("rot_left", deg_to_rad(45.0 * int(s["rot_left"])))
		_disc_mat.set_shader_parameter("rot_right", deg_to_rad(45.0 * int(s["rot_right"])))
		_disc_mat.set_shader_parameter("scale_right", 1.0 - 0.15 * int(s["zoom_right"]))
		_disc_mat.set_shader_parameter("unlocked", 1.0 if s["vault_unlocked"] else 0.0)
	_rot(part("vault_door", "IA_collar_left"), Vector3.BACK, COLLAR_STEP_DEG * int(s["rot_left"]), animated, 0.25)
	_rot(part("vault_door", "IA_collar_right"), Vector3.BACK, COLLAR_STEP_DEG * int(s["rot_right"]), animated, 0.25)
	_rot(part("vault_door", "IA_zoom_right"), Vector3.BACK, ZOOM_STEP_DEG * int(s["zoom_right"]), animated, 0.25)
	_rot(part("vault_door", "IA_vault_handle"), Vector3.BACK, VAULT_HANDLE_STEP_DEG * int(s["wheel"]), animated, 0.9)
	if not animated or not s["vault_unlocked"]:
		for k in 8:
			_bolt(k, s["vault_unlocked"], false)
	_rot(part("vault_door", "IA_vault_door"), Vector3.UP, VAULT_DOOR_OPEN_DEG if s["vault_open"] else 0.0, animated, 3.2)
	# the vault interior: keys on the cradle, the chosen one gone and the other clamped
	var choice: String = s["choice"]
	for k in ["strand", "leyla"]:
		var item := "%s_key" % k
		_held_item("key_" + k, item, part("vault_interior", "key_%s_mount" % k), choice != item)
	_slide(part("vault_interior", "cradle_clamp_left"), Vector3(0, CLAMP_DROP if choice == "leyla_key" else 0.0, 0), animated, 0.4)
	_slide(part("vault_interior", "cradle_clamp_right"), Vector3(0, CLAMP_DROP if choice == "strand_key" else 0.0, 0), animated, 0.4)


func _bolt(k: int, retracted: bool, animated: bool) -> void:
	var b := part("vault_door", "bolt_%d" % k)
	if b == null:
		return
	var a := deg_to_rad(45.0 * k)
	var inward := -Vector3(cos(a), sin(a), 0.0) * (BOLT_TRAVEL if retracted else 0.0)
	if not rest.has(b):
		rest[b] = b.transform
	var base: Transform3D = rest[b]
	_to(b, Transform3D(base.basis, base.origin + inward), animated, 0.35)


func bolts_cascade() -> void:
	for k in 8:
		get_tree().create_timer(0.12 * k).timeout.connect(func() -> void: _bolt(k, true, true))


func _apply_echoes() -> void:
	var s := logic.state
	var holding := logic.holds_crystal()
	for id: String in ArchiveLogic.ECHOES:
		var n: Node3D = model("echo_" + id)
		if n == null:
			continue
		var show: bool = holding and not (s["echoes"] as Array).has(id) and (id != "booth" or bool(s["booth_open"]))
		if n.visible != show:
			room.call("set_present", n, show)
			if show:
				_fade(n, 0.0, 0.85, 0.8)


func release_echo(id: String) -> void:
	var n: Node3D = model("echo_" + id)
	if n == null:
		return
	room.call("set_present", n, true)
	_fade(n, 0.85, 0.0, 1.4)
	get_tree().create_timer(1.45).timeout.connect(func() -> void: room.call("set_present", n, false))


func selection_changed(id: String) -> void:
	_apply_echoes()
	_receiver_on = id == "pocket_receiver"
	receiver_view((room.get("cam") as RoomCamera).current())
	if id == "crystal_lens":
		var hud: Node = room.get("hud")
		hud.call("caption", tr("cap2.lens_hum"), 4.0)


func _apply_lights(animated: bool) -> void:
	var s := logic.state
	var L: Dictionary = room.get("lights")
	var booth: OmniLight3D = L.get("booth")
	if booth:
		var e: float = 1.1 if s["booth_open"] else 0.0
		if animated:
			room.create_tween().tween_property(booth, "light_energy", e, 1.2)
		else:
			booth.light_energy = e
	_lamp(part("room_archive", "booth_bulb"), s["booth_open"], Color("ffcf94"))
	for i in 6:
		_lamp(part("pendant_%d" % i, "bulb"), true, Color("ffc58a"))
	_lamp(part("reading_table", "bulb"), true, Color("ffd29a"))
	for k in 10:
		_lamp(part("room_archive", "elamp_glass_%d" % k), true, Color("ff9a3c"))
	var vault: OmniLight3D = L.get("vault")
	if vault and not animated:
		vault.light_energy = 1.6 if s["vault_open"] else 0.0
	_lamp(part("vault_interior", "vault_bulb"), s["vault_open"], Color("ffe2b0"))


## Draw the booth interior only while it can be seen; the vault interior only once it is open.
func update_visibility(view_id: String) -> void:
	var s := logic.state
	var booth_seen: bool = s["booth_open"] or view_id in ArchiveRoom.BOOTH_VIEWS
	for id in ["film_projector", "slide_projector", "film_splicer", "slide_cabinet", "lens_case"]:
		var n := model(id)
		if n:
			n.visible = booth_seen
	var vault_in := model("vault_interior")
	if vault_in:
		vault_in.visible = s["vault_open"] or view_id in ["vault_inside", "vault_mouth"]


# ====================================================================== receiver (hot / cold)
func receiver_view(view_id: String) -> void:
	_receiver_level = logic.receiver_strength(view_id) if _receiver_on else -1
	var hud: Node = room.get("hud")
	if hud and hud.has_method("set_meter"):
		hud.call("set_meter", _receiver_level)


func _receiver_audio(delta: float) -> void:
	if _static == null:
		_static = AudioStreamPlayer.new()
		_static.bus = "SFX"
		_static.stream = AudioManager.stream("sfx", "receiver_static")
		room.add_child(_static)
	if not _receiver_on or _receiver_level < 0:
		if _static.playing:
			_static.stop()
		return
	if not _static.playing and _static.stream:
		_static.play()
	_static.volume_db = linear_to_db(maxf(0.0001, 0.22 - 0.03 * _receiver_level))
	if _receiver_level <= 0:
		return
	_beep_t -= delta
	if _beep_t <= 0.0:
		_beep_t = 1.7 - 0.28 * _receiver_level
		AudioManager.sfx("receiver_beep", -16.0 + 2.5 * _receiver_level, 0.9 + 0.05 * _receiver_level)


# ====================================================================== per-frame motion
func _process(delta: float) -> void:
	_receiver_audio(delta)
	var s := logic.state
	if _tape_playing:
		_tape_t += delta
		for p in ["spindle_l", "spindle_r"]:
			var sp := part("tape_deck", p)
			if sp:
				sp.rotate_object_local(Vector3.UP, -delta * 4.0)
		var vu := part("tape_deck", "vu_needle")
		if vu and rest.has(vu):
			var amp := 0.45 + 0.35 * sin(_tape_t * 9.0) * sin(_tape_t * 2.3) + randf_range(-0.1, 0.1)
			vu.transform = Transform3D((rest[vu] as Transform3D).basis * Basis(Vector3.BACK, deg_to_rad(VU_MAX_DEG * clampf(amp, 0.0, 1.0))), (rest[vu] as Transform3D).origin)
	if s["projector_on"] and s["reel_on_projector"]:
		var feed: Array = _held.get("feed_reel", [])
		if not feed.is_empty():
			(feed[1] as Node3D).rotate_object_local(Vector3.BACK, -delta * 3.0)
		var tu := part("film_projector", "takeup_reel")
		if tu:
			tu.rotate_object_local(Vector3.RIGHT, -delta * 3.0)
	if _compressor_on:
		var pul := part("compressor_panel", "motor_pulley")
		if pul:
			pul.rotate_object_local(Vector3.RIGHT, delta * 18.0)
		var tank := part("compressor_panel", "compressor_tank")
		if tank and rest.has(tank):
			var j := Vector3(randf_range(-1, 1), randf_range(-1, 1), randf_range(-1, 1)) * 0.0012
			tank.transform = Transform3D((rest[tank] as Transform3D).basis, (rest[tank] as Transform3D).origin + j)


func compressor_running(on: bool) -> void:
	_compressor_on = on


# ====================================================================== tape deck
func play_tape(tape: String, clear: bool) -> void:
	stop_tape()
	_tape_playing = true
	_tape_t = 0.0
	_rot(part("tape_deck", "IA_play"), Vector3.RIGHT, PLAY_PRESS_DEG, true, 0.08)
	var hud: Node = room.get("hud")
	if not clear:
		AudioManager.sfx("tape_garble", -2.0)
		await get_tree().create_timer(2.6).timeout
		stop_tape()
		return
	AudioManager.sfx("tape_voice", -3.0)
	var text := tr("doc2." + tape)
	var lines := text.split(". ", false)
	var per := clampf(9.0 / maxf(1.0, lines.size()), 2.2, 4.0)
	for line in lines:
		if not _tape_playing:
			return
		hud.call("caption", line.strip_edges() + ("" if line.ends_with(".") else "."), per)
		await get_tree().create_timer(per).timeout
	var clicks := int(ArchiveLogic.TAPES.get(tape, 0))
	var dots := ""
	for i in clicks:
		if not _tape_playing:
			return
		AudioManager.sfx("tape_clicks", -2.0)
		dots += "• "
		hud.call("caption", tr("cap2.clicks") % dots.strip_edges(), 2.5)
		await get_tree().create_timer(0.42).timeout
	await get_tree().create_timer(0.8).timeout
	stop_tape()


func stop_tape() -> void:
	_tape_playing = false
	_rot(part("tape_deck", "IA_play"), Vector3.RIGHT, 0.0, true, 0.12)
	var vu := part("tape_deck", "vu_needle")
	if vu and rest.has(vu):
		_to(vu, rest[vu], true, 0.3)


# ====================================================================== dial, wheel, levers
func dial_spin(d: int) -> void:
	var w := part("booth_door", "IA_rotary_dial")
	if w == null:
		return
	var n := 10 if d == 0 else d
	var theta := 50.0 + (n - 1) * 30.0
	AudioManager.sfx("dial_wind", -2.0)
	_rot(w, Vector3.BACK, -(theta + 10.0), true, 0.25 + 0.02 * n)
	get_tree().create_timer(0.3 + 0.02 * n).timeout.connect(func() -> void:
		AudioManager.sfx("dial_return", -3.0)
		_rot(w, Vector3.BACK, 0.0, true, 0.35 + 0.035 * n))


func wheel_spin() -> void:
	if logic.state["vault_unlocked"]:
		return
	var h := part("vault_door", "IA_vault_handle")
	if h == null:
		return
	_rot(h, Vector3.BACK, -6.0, true, 0.08)
	get_tree().create_timer(0.1).timeout.connect(func() -> void: _rot(h, Vector3.BACK, 0.0, true, 0.2))


## Momentary lever pulls (the send lever, the punch lever) animate out and back.
func pull(model_id: String, part_name: String, deg: float) -> void:
	var lever := part(model_id, part_name)
	if lever == null:
		return
	_rot(lever, Vector3.RIGHT, deg, true, 0.15)
	get_tree().create_timer(0.35).timeout.connect(func() -> void: _rot(lever, Vector3.RIGHT, 0.0, true, 0.3))


# ====================================================================== pneumatic post
func _tube_points() -> Array[Vector3]:
	var pts: Array[Vector3] = []
	for i in 5:
		var e := part("room_archive", "tube_p%d" % i)
		pts.append(e.global_position if e else TUBE_PATH[i])
	return pts


## Fly the canister up the riser, across the ceiling to the stacks terminal and back into the tray.
func canister_flight(with_file: bool) -> void:
	var start := part("tube_station", "canister_mount")
	var tray := part("tube_station", "return_mount")
	pull("tube_station", "IA_send_lever", LEVER_PULL_DEG)
	_flying = true
	apply_state(true)
	var flyer := ModelUtil.spawn("canister", room, Transform3D.IDENTITY, "none")
	if flyer == null:
		await get_tree().create_timer(3.0).timeout
		_flying = false
		apply_state(true)
		return
	var pts := _tube_points()
	var curve := Curve3D.new()
	if start:
		curve.add_point(start.global_position)
	for p in pts:
		curve.add_point(p)
	var out_len := curve.get_baked_length()
	await _travel(flyer, curve, out_len / 6.5, false)
	AudioManager.sfx("canister_thump", -4.0, 0.8)
	await get_tree().create_timer(0.9).timeout
	AudioManager.sfx("tube_whoosh", -2.0, 0.92)
	var back := Curve3D.new()
	for i in range(pts.size() - 1, -1, -1):
		back.add_point(pts[i])
	if tray:
		back.add_point(tray.global_position + Vector3(0, 0.25, 0))
		back.add_point(tray.global_position)
	await _travel(flyer, back, back.get_baked_length() / 6.5, true)
	AudioManager.sfx("canister_thump")
	AudioManager.haptic(60)
	flyer.queue_free()
	_flying = false
	tray_open = false
	apply_state(true)


func _travel(n: Node3D, curve: Curve3D, seconds: float, ease_in: bool) -> void:
	var length := curve.get_baked_length()
	var tw := room.create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT if not ease_in else Tween.EASE_OUT)
	tw.tween_method(func(t: float) -> void:
		var d := t * length
		var p := curve.sample_baked(d)
		var ahead := curve.sample_baked(minf(length, d + 0.05))
		n.global_position = p
		if ahead.distance_to(p) > 0.001:
			n.global_basis = Basis(Quaternion(Vector3.UP, (ahead - p).normalized())), 0.0, 1.0, maxf(0.6, seconds))
	await tw.finished


# ====================================================================== film cinematic
func dim_for_film(on: bool) -> void:
	var L: Dictionary = room.get("lights")
	for i in 6:
		var p: OmniLight3D = L.get("pendant_%d" % i)
		if p:
			room.create_tween().tween_property(p, "light_energy", 0.18 if on else 1.25, 1.6)
	var env: Environment = room.get("env")
	if env:
		room.create_tween().tween_property(env, "ambient_light_energy", 0.25 if on else 0.5, 1.6)
	if not on:
		_film_override = -1
		apply_state(true)


func show_film_frame(i: int) -> void:
	_film_override = i
	_apply_screen()


func show_secret_frame(on: bool) -> void:
	_secret_on = on
	_apply_screen()


## Leave path: Leyla's echo walks from the projector to the slide cabinet and points at drawer 2.
func leyla_echo_walk() -> void:
	var echo: Node3D = model("echo_leyla")
	if echo == null:
		await get_tree().create_timer(3.0).timeout
		return
	echo.global_position = ArchiveRoom.LEYLA_ECHO_FROM
	echo.visible = true
	_fade(echo, 0.0, 0.9, 1.0)
	AudioManager.sfx("reveal", -4.0, 0.8)
	await get_tree().create_timer(1.0).timeout
	var tw := room.create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_property(echo, "global_position", ArchiveRoom.LEYLA_ECHO_TO, 2.6)
	await tw.finished
	var drawer := part("slide_cabinet", "IA_slide_drawer_%d" % ArchiveLogic.SLIDE_MARK_DRAWER) as MeshInstance3D
	if drawer:
		ModelUtil.set_emission(drawer, true, Color("cff6ff"), 1.2)
	await get_tree().create_timer(2.2).timeout
	_fade(echo, 0.9, 0.0, 1.4)
	await get_tree().create_timer(1.4).timeout
	echo.visible = false
	if drawer:
		ModelUtil.set_emission(drawer, false)


# ====================================================================== intro, finale
func shutter_drop() -> void:
	var sh := part("room_archive", "fire_shutter")
	if sh == null or not rest.has(sh):
		return
	var base: Transform3D = rest[sh]
	sh.transform = Transform3D(base.basis, base.origin + Vector3(0, SHUTTER_OPEN_Y, 0))
	var tw := room.create_tween()
	tw.tween_interval(0.25)
	tw.tween_property(sh, "transform", base, 0.32).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tw.tween_property(sh, "transform", Transform3D(base.basis, base.origin + Vector3(0, 0.03, 0)), 0.06)
	tw.tween_property(sh, "transform", base, 0.08)
	tw.tween_callback(func() -> void:
		(room.get("hud") as Node).call("message", tr("msg.c2_shutter"))
		room.call("intro_impact"))


func emergency_flicker() -> void:
	for k in 10:
		var g := part("room_archive", "elamp_glass_%d" % k) as MeshInstance3D
		if g == null:
			continue
		var tw := room.create_tween()
		tw.tween_interval(0.25 + 0.12 * k)
		for i in 3:
			tw.tween_callback(func() -> void: ModelUtil.set_emission(g, false))
			tw.tween_interval(0.07)
			tw.tween_callback(func() -> void: ModelUtil.set_emission(g, true, Color("ff9a3c"), 3.0))
			tw.tween_interval(0.05 + 0.03 * i)


func open_vault() -> void:
	var L: Dictionary = room.get("lights")
	var v: OmniLight3D = L.get("vault")
	update_visibility("vault_mouth")
	apply_state(true)
	if v:
		room.create_tween().tween_property(v, "light_energy", 1.8, 2.4)


func vault_reel(on: bool) -> void:
	var scr := part("vault_interior", "vault_reel_screen") as MeshInstance3D
	if scr:
		var m := StandardMaterial3D.new()
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.albedo_texture = _tex(DECALS + "vault_reel.jpg")
		m.albedo_color = Color(1.0, 0.97, 0.9) if on else Color(0.1, 0.1, 0.1)
		scr.material_override = m
	_lamp(part("vault_interior", "vault_lamp_glow"), on, Color("fff1d6"))


# ====================================================================== helpers
func _rot(n: Node3D, axis: Vector3, deg: float, animated: bool, dur: float) -> void:
	if n == null:
		return
	if not rest.has(n):
		rest[n] = n.transform
	var base: Transform3D = rest[n]
	_to(n, Transform3D(base.basis * Basis(axis.normalized(), deg_to_rad(deg)), base.origin), animated, dur)


func _slide(n: Node3D, offset: Vector3, animated: bool, dur: float = 0.5) -> void:
	if n == null:
		return
	if not rest.has(n):
		rest[n] = n.transform
	var base: Transform3D = rest[n]
	_to(n, Transform3D(base.basis, base.origin + base.basis * offset), animated, dur)


func _to(n: Node3D, target: Transform3D, animated: bool, dur: float) -> void:
	var k := str(n.get_instance_id())
	if _tweens.has(k) and (_tweens[k] as Tween).is_valid():
		(_tweens[k] as Tween).kill()
	if not animated or n.transform.is_equal_approx(target):
		n.transform = target
		return
	var from := n.transform
	var fq := from.basis.get_rotation_quaternion()
	var tq := target.basis.get_rotation_quaternion()
	var sc := target.basis.get_scale()
	var tw := room.create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tw.tween_method(func(t: float) -> void:
		if is_instance_valid(n):
			n.transform = Transform3D(Basis(fq.slerp(tq, t)).scaled(sc), from.origin.lerp(target.origin, t)), 0.0, 1.0, dur)
	_tweens[k] = tw


func _lamp(n: Node3D, on: bool, color: Color) -> void:
	if n is MeshInstance3D:
		ModelUtil.set_emission(n as MeshInstance3D, on, color, 3.0)


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


func _fade(n: Node3D, from: float, to: float, dur: float) -> void:
	var meshes := ModelUtil.find_meshes(n)
	room.create_tween().tween_method(func(v: float) -> void:
		for mi in meshes:
			var m := mi.material_override as ShaderMaterial
			if m:
				m.set_shader_parameter("intensity", v), from, to, dur)
