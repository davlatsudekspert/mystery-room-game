class_name ArchiveZones
extends Node
## Chapter 2 expansion ("The Whole Building", docs/CHAPTER2_EXPANSION.md sections 3, 7 and 11): the multi-room layer of
## the Archive scene. Each room of the plan is a *zone*: a Node3D far away from the hall (ZONE_OFFSET) that is built the
## first time it is needed, and shown only while it is the current room (the hall keeps its own nodes and is simply too
## far away to be drawn: the camera's far plane is 40 m, the zones are 60 m apart, so a zone costs nothing while the
## player is elsewhere). This class owns
## - the zone registry, lazy building (a zone class per room, ArchivePump so far; a marked placeholder for the rooms whose
##   models are not in yet, never shown while ArchiveLogic.EXPANSION_STAGE is 0),
## - transitions: any `room:<id>` event of the logic (enter_room, travel_to, from a door, the plan or a hint) switches
##   zone, environment and camera. From a tapped door the leaf opens and the camera walks through the doorway (head-bob,
##   soft steps), up or down a stair (steps on the iron treads) or rides the book lift's cage; a short crossfade at the
##   threshold hides the cut and the camera glides in on the other side (1.1 s all told, a tap skips it, reduce motion
##   makes it short and still). Without a tapped door (the plan, a hint) it is the old quick fade (0.4 s),
## - the hooks the room asks for per view / hotspot (zones register their own tables),
## - the reaction moments (section 11) as the scene plays them, honouring Settings "moments" (full / soft / off) and
##   waiting for the caption strip,
## - audio cues by id with fallbacks to the existing sounds (the sound designer pushes the real ids; see CUES).
## No puzzle logic lives here: it reads ArchiveLogic and shows its state.

const FAR_M := 60.0
## Where each room's zone origin lies (x, z); the hall is the existing scene at the origin.
const ZONE_OFFSET := {
	"hall": Vector3.ZERO, "pump": Vector3(60, 0, 0), "cell": Vector3(120, 0, 0), "cold": Vector3(180, 0, 0),
	"gallery": Vector3(60, 0, 60), "plate": Vector3(120, 0, 60), "office": Vector3(180, 0, 60),
}
## The view the camera lands in on entering a room (a root view: free look).
const ROOT_VIEW := {"hall": "hall", "pump": "pump", "cell": "cell", "cold": "cold", "gallery": "gallery", "plate": "plate",
	"office": "office"}
## Where the placeholder rooms' exit door leads (their real rooms replace these as the models arrive).
const BACK_ROOM := {"cell": "pump", "cold": "cell", "gallery": "pump", "plate": "gallery", "office": "gallery"}
## Per-room look (background, ambient colour, ambient energy, fog colour, fog density).
const MOOD := {
	"hall": ["0a0c0d", "2a3a36", 0.5, "1a2826", 0.014],
	"pump": ["0b0705", "6a4630", 0.62, "2a180e", 0.016],
	"cell": ["0b0806", "7a5a3a", 0.6, "2a1c10", 0.012],
	"cold": ["070b0f", "4a6a80", 0.6, "10202a", 0.02],
	"gallery": ["0c0b08", "6a5c44", 0.6, "2a2418", 0.012],
	"plate": ["0a0505", "4a1c18", 0.5, "200808", 0.012],
	"office": ["0a0c0d", "56625e", 0.6, "1a2220", 0.01],
}
## The zone classes (pure scene builders). A room without one gets the placeholder.
const BUILDERS := {
	"pump": "res://src/rooms/archive/archive_pump.gd",
	"cell": "res://src/rooms/archive/archive_cell.gd",
	"cold": "res://src/rooms/archive/archive_cold.gd",
	"gallery": "res://src/rooms/archive/archive_gallery.gd",
	"plate": "res://src/rooms/archive/archive_plate.gd",
	"office": "res://src/rooms/archive/archive_office.gd",
}

## Audio cue id -> sound ids (docs/AUDIO_CH2X.md): the first that exists is played, the rest are fallbacks.
const CUES := {
	"valve_wheel": ["c2x_valve_wheel"], "pipe_knock_full": ["c2x_mallet_full"], "pipe_knock_dead": ["c2x_mallet_dead"],
	"pipe_knock_cracked": ["c2x_mallet_cracked"], "steam_hiss": ["c2x_pipe_hazard"], "dial_click": ["dial_wind", "keypad_press"],
	"panel_swing": ["c2x_panel_open"], "panel_cold": ["c2x_panel_cold"], "svc_door_open": ["c2x_door_iron"],
	"fire_door": ["drawer_open"], "refused": ["c2x_refused"], "room_step": ["c2x_door_service"], "pipe_flow": ["c2x_pipe_flow"],
	"thaw": ["c2x_thaw"], "plan_unfold": ["c2x_plan_unfold"], "lamp_dead": ["c2x_lamp_fail"], "lamp_fit": ["c2x_lamp_fit"],
	"stair_steps": ["c2x_stair_steps"],
}
const MOMENT_SOUND := {"m1": "lamp_dip", "m2": "knocks", "m3": "frost_steps", "m4": "roll_call", "m5": "steps_above",
	"m6": "echo_chime"}
## Ambience bed per room (the hall keeps amb_archive).
const AMBIENCE := {"hall": "amb_archive", "pump": "amb_c2x_pump", "cell": "amb_c2x_cell", "cold": "amb_c2x_cold",
	"gallery": "amb_c2x_gallery", "plate": "amb_c2x_plate", "office": "amb_c2x_office"}
## Events that only say "no" (docs/AUDIO_CH2X.md).
## The hotspots whose taps walk through a door; the leaf (a part named IA_door*) opens first.
const DOOR_WALK := ["pump_door", "cell_cold_door", "cell_exit", "cold_exit", "gal_door_plate", "gal_door_office", "plate_door",
	"off_door", "east_wall"]
## The stairs: how far the camera climbs (m; a descent only dips, the floor is in the way).
const STAIR_RISE := {"pump_stair": 1.1, "gal_stair": -0.4, "stair_stump": 1.1}
const DOOR_OPEN_DEG := 95.0
const REFUSED := ["valves_locked_n2", "need_mallet", "sheets_locked", "cranks_locked", "need_aisle", "need_cloth", "no_pressure",
	"weights_locked", "room_locked", "travel_refused"]

var room: Node3D
var logic: ArchiveLogic
var zones: Dictionary = {} # room id -> {"root": Node3D, "builder": Object}
var hall_exp: ArchiveHallExp # what the new game adds to the hall (null in a 1.0 game)
var current := "hall"
var moving := false
## A caller that knows how the player travels sets it before enter_room (the book lift: {"kind": "lift", "rise": m}).
var walk_hint: Dictionary = {}
var _tweens: Array[Tween] = []
var _skipped := false
var _fade_layer: CanvasLayer
var _fade: ColorRect
var _view_room: Dictionary = {} # view id -> room id (the zone views the builders registered)
var _hotspot_view: Dictionary = {}
var _deeper: Dictionary = {}
var _caption: Dictionary = {}


func _init(r: Node3D) -> void:
	room = r
	logic = r.get("logic")
	name = "ArchiveZones"


func _ready() -> void:
	_fade_layer = CanvasLayer.new()
	_fade_layer.layer = 12 # over the HUD (10), under the scene manager's own fade
	add_child(_fade_layer)
	_fade = ColorRect.new()
	_fade.color = Color(0.02, 0.02, 0.025, 0.0)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade_layer.add_child(_fade)


# ====================================================================== registry and hooks
## The room a camera view belongs to ("hall" for every view of the existing scene).
func room_of_view(view: String) -> String:
	if _view_room.has(view):
		return str(_view_room[view])
	var table := zone_views()
	for id: String in table:
		if (table[id] as Array).has(view):
			return id
	return "hall"


func hotspot_view(hs: String) -> String:
	return str(_hotspot_view.get(hs, ""))


func deeper_views() -> Dictionary:
	return _deeper


func caption_for(view: String) -> String:
	return str(_caption.get(view, ""))


## A zone builder (or the hall extras) calls this to register what it adds to the room's hook tables.
func register(room_id: String, views: Array, hotspot_views: Dictionary, deeper: Dictionary, captions: Dictionary) -> void:
	for v: String in views:
		_view_room[v] = room_id
	_hotspot_view.merge(hotspot_views, true)
	for k: String in deeper:
		_deeper[k] = deeper[k]
	_caption.merge(captions, true)


## The views each zone registers (static, so a QA tool can jump to a view of a room that is not built yet).
static func zone_views() -> Dictionary:
	return {
		"hall": ArchiveHallExp.VIEWS,
		"pump": ArchivePump.VIEWS,
		"cell": ArchiveCell.VIEWS,
		"cold": ArchiveCold.VIEWS,
		"gallery": ArchiveGallery.VIEWS,
		"plate": ArchivePlate.VIEWS,
		"office": ArchiveOffice.VIEWS,
	}


## Makes the zone of `view` exist and current (QA tools and saves jump to a view without a transition).
func prepare_view(view: String) -> void:
	var rid := room_of_view(view)
	if rid == "hall":
		if current != "hall":
			activate("hall")
		return
	ensure(rid)
	if rid != current:
		activate(rid)
	var b := builder(rid)
	if b != null and b.has_method("on_view"):
		b.call("on_view", view) # a zone reacts to its camera views (the first look at the Cell door, the cranks' framing)


## A drag that starts on a part of the current zone (the frost window's finger wipe, the light table's sheets).
## -> true when the zone captures it; drag_moved() then gets every movement (relative px, finger position px).
func drag_started(part: String) -> bool:
	var b := builder(current)
	return b != null and b.has_method("drag_started") and bool(b.call("drag_started", part))


func drag_moved(rel: Vector2, pos: Vector2) -> void:
	var b := builder(current)
	if b != null and b.has_method("drag_moved"):
		b.call("drag_moved", rel, pos)


func builder(room_id: String) -> Object:
	return (zones.get(room_id, {}) as Dictionary).get("builder")


## Builds a room's zone on first use. -> the zone's root node (null for the hall).
func ensure(room_id: String) -> Node3D:
	if room_id == "hall":
		return null
	if zones.has(room_id):
		return zones[room_id]["root"]
	var root := Node3D.new()
	root.name = "Zone_" + room_id
	root.position = ZONE_OFFSET.get(room_id, Vector3(300, 0, 0))
	room.add_child(root)
	var b: Object = null
	if BUILDERS.has(room_id):
		b = (load(BUILDERS[room_id]) as GDScript).new(room, self, root)
		b.call("build")
	else:
		b = _build_placeholder(room_id, root)
	zones[room_id] = {"root": root, "builder": b}
	root.visible = false
	_set_colliders(root, false)
	return root


func activate(room_id: String) -> void:
	var left := current
	current = room_id
	if left != room_id: # a zone may stop what it started (the Plate Room's enlarger fan)
		var lb := builder(left)
		if lb != null and lb.has_method("on_exit"):
			lb.call("on_exit")
	for id: String in zones:
		var on: bool = id == room_id
		var root: Node3D = zones[id]["root"]
		root.visible = on
		_set_colliders(root, on)
	var mood: Array = MOOD.get(room_id, MOOD["hall"])
	var env: Environment = room.get("env")
	if env != null:
		env.background_color = Color(str(mood[0]))
		env.ambient_light_color = Color(str(mood[1]))
		env.ambient_light_energy = float(mood[2])
		env.fog_light_color = Color(str(mood[3]))
		env.fog_density = float(mood[4])
	var b := builder(room_id)
	if b != null and b.has_method("on_enter"):
		b.call("on_enter")


func _set_colliders(root: Node, on: bool) -> void:
	for body in root.find_children("*", "StaticBody3D", true, false):
		var sb := body as StaticBody3D
		if not on:
			sb.set_meta("layer_was", sb.collision_layer if sb.collision_layer != 0 else int(sb.get_meta("layer_was", 1)))
			sb.collision_layer = 0
		else:
			sb.collision_layer = int(sb.get_meta("layer_was", 1)) if sb.collision_layer == 0 else sb.collision_layer


## A tap on a hotspot of the expansion (the hall's east wall, a zone's parts). -> true when it was handled.
func interact(hs: String, part: String) -> bool:
	if hall_exp != null and hall_exp.interact(hs, part):
		return true
	for id: String in zones:
		var b: Object = zones[id]["builder"]
		if b != null and b.has_method("interact") and bool(b.call("interact", hs, part)):
			return true
	return interact_placeholder(hs)


## Re-draws the expansion's state (after any logic event).
func apply_state(animated: bool) -> void:
	if hall_exp != null:
		hall_exp.apply_state(animated)
	for id: String in zones:
		var b: Object = zones[id]["builder"]
		if b != null and b.has_method("apply_state"):
			b.call("apply_state", animated)


## Sound and per-event reactions of the expansion's rooms.
func feedback(e: String) -> void:
	if REFUSED.has(e.get_slice(":", 0)):
		_cue("refused")
		return
	if hall_exp != null and hall_exp.feedback(e):
		return
	for id: String in zones:
		var b: Object = zones[id]["builder"]
		if b != null and b.has_method("feedback") and bool(b.call("feedback", e)):
			return


# ====================================================================== transitions
## The scene's reaction to the logic's `room:<id>` event: a walk through the tapped door / stair / lift (or, without one,
## a quick fade), then the switch and the arrival. Taps skip it; input is locked meanwhile.
func transition(room_id: String) -> void:
	if moving or room_id == current:
		return
	moving = true
	_skipped = false
	_tweens.clear()
	var hud: Node = room.get("hud")
	hud.call("set_busy", true)
	var cam: RoomCamera = room.get("cam")
	cam.transitioning = true # QA tools and the room wait on it until the arrival is over
	var calm := bool(Settings.get_value("reduce_motion"))
	var plan := _walk_plan()
	var leaf: Node3D = null
	var leaf_rest := Transform3D.IDENTITY
	var from := current
	if plan.is_empty():
		await _fade_to(1.0, 0.12 if calm else 0.2)
	else:
		if plan["kind"] == "door":
			var opened := _open_leaf(str(plan.get("part", "")))
			if not opened.is_empty():
				leaf = opened["leaf"]
				leaf_rest = opened["rest"]
		await _walk_out(plan, cam, calm)
	if leaf != null:
		leaf.transform = leaf_rest # shut again; the room's state (apply_state below) opens it for good where it should stay open
	ensure(room_id)
	activate(room_id)
	cam.go(str(ROOT_VIEW.get(room_id, "hall")), true)
	cam.transitioning = true
	if from != room_id:
		if plan.is_empty():
			_cue("room_step")
		_set_ambience(room_id)
	if plan.is_empty() or calm or _skipped:
		await _fade_to(0.0, 0.0 if calm else (0.1 if _skipped else 0.2))
	else:
		await _walk_in(plan, cam)
	cam.end_walk()
	hud.call("set_busy", false)
	moving = false
	var visuals: Node = room.get("visuals")
	if visuals != null:
		visuals.call("apply_state", false)
	_after_enter(room_id)


## How the player gets to the next room: {} (fade), or {"kind": "door" / "stairs" / "lift", ...}. The last tapped door or
## stair says (taps older than 1.5 s do not count), or a caller's walk_hint.
func _walk_plan() -> Dictionary:
	if not walk_hint.is_empty():
		var h := walk_hint
		walk_hint = {}
		return h
	var lt: Dictionary = room.get("last_tap")
	if lt.is_empty() or Time.get_ticks_msec() - int(lt["ms"]) > 1500:
		return {}
	var hs := str(lt["hotspot"])
	room.set("last_tap", {})
	if STAIR_RISE.has(hs):
		return {"kind": "stairs", "pos": lt["pos"], "rise": float(STAIR_RISE[hs])}
	if DOOR_WALK.has(hs) or hs.begins_with("zone_back_"):
		return {"kind": "door", "pos": lt["pos"], "part": lt["part"]}
	return {}


## The door leaf (a part named IA_door* of the current zone) swings open. -> {"leaf", "rest"} or {}.
func _open_leaf(part: String) -> Dictionary:
	if not part.begins_with("IA_door") or not zones.has(current):
		return {}
	var leaf := (zones[current]["root"] as Node).find_child(part, true, false) as Node3D
	if leaf == null:
		return {}
	if not leaf.has_meta("rest"):
		leaf.set_meta("rest", leaf.transform)
	var rest: Transform3D = leaf.get_meta("rest")
	var open := Transform3D(rest.basis * Basis(Vector3.UP, deg_to_rad(DOOR_OPEN_DEG)), rest.origin)
	var tw := create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	var from_t := leaf.transform
	tw.tween_method(func(k: float) -> void:
		leaf.transform = Transform3D(from_t.basis.slerp(open.basis, k), from_t.origin.lerp(open.origin, k)), 0.0, 1.0,
		0.12 if bool(Settings.get_value("reduce_motion")) else 0.45)
	_tweens.append(tw)
	return {"leaf": leaf, "rest": rest}


## The walk out of the current room: through the doorway, up or down the stair, or in the cage of the lift. The fade to
## black starts in the last quarter second, so the cut is at the threshold.
func _walk_out(plan: Dictionary, cam: RoomCamera, calm: bool) -> void:
	var kind := str(plan["kind"])
	var cp := cam.global_position
	var fwd := -cam.global_basis.z
	fwd.y = 0.0
	if plan.has("pos"):
		var d: Vector3 = (plan["pos"] as Vector3) - cp
		d.y = 0.0
		if d.length() > 0.05:
			fwd = d
	fwd = fwd.normalized() if fwd.length() > 0.001 else Vector3.FORWARD
	var rise := float(plan.get("rise", 0.0))
	var end := cp
	var dur := 1.0
	var steps := 0
	match kind:
		"door":
			var p: Vector3 = plan["pos"]
			end = Vector3(p.x, cp.y, p.z) + fwd * 0.9
			var dist := cp.distance_to(end)
			dur = clampf(0.55 + dist * 0.1, 0.7, 1.05)
			steps = clampi(roundi(dist / RoomCamera.STRIDE_M), 2, 6)
			_cue("room_step")
		"stairs":
			var p: Vector3 = plan["pos"]
			end = Vector3(p.x, cp.y + rise, p.z) + fwd * 0.5
			dur = 1.1
			steps = 5
			_cue("c2x_stair_climb")
		"lift":
			end = cp + fwd * 0.8 + Vector3.UP * rise
			dur = 1.1
	var look := Basis.looking_at(fwd, Vector3.UP)
	if kind == "stairs" and rise > 0.0:
		look = look * Basis(Vector3.RIGHT, deg_to_rad(8.0))
	var total := minf(dur * (0.5 if calm else 1.0), RoomCamera.TRAVEL_MAX_S)
	_fade_in_at(total - (0.12 if calm else 0.25), 0.12 if calm else 0.25)
	if kind == "lift":
		# two moves in one: a step into the cage, then the ride (no bob)
		var mid := Transform3D(look, cp + fwd * 0.8)
		var t1 := cam.walk(mid, total * 0.4, 0 if calm else 1)
		await t1.finished
		if not _skipped:
			await cam.walk(Transform3D(look, end), total * 0.6, 0, Tween.EASE_IN_OUT).finished
	else:
		await cam.walk(Transform3D(look, end), dur, steps, Tween.EASE_IN_OUT).finished
	await _fade_wait()


## On the other side: the camera comes in through the doorway (a short glide into the room's view) while the black lifts.
func _walk_in(plan: Dictionary, cam: RoomCamera) -> void:
	var fin := cam.global_transform
	var back := -fin.basis.z
	back.y = 0.0
	back = back.normalized() if back.length() > 0.001 else Vector3.BACK
	var start := fin
	start.origin = fin.origin - back * 0.7
	if str(plan["kind"]) == "stairs":
		start.origin.y -= 0.3 * signf(float(plan.get("rise", 1.0)))
	elif str(plan["kind"]) == "lift":
		start.origin = fin.origin
		start.origin.y += 0.25 * signf(float(plan.get("rise", 1.0)))
	cam.global_transform = start
	_fade_to_async(0.0, 0.3)
	await cam.walk(fin, 0.6, 0 if str(plan["kind"]) == "lift" else 1, Tween.EASE_OUT).finished
	await _fade_wait()


func _after_enter(room_id: String) -> void:
	var rest: Array[String] = []
	for m in _pending:
		if _moment_room(m) == room_id:
			play_moment(m)
		else:
			rest.append(m)
	_pending = rest


var _played: Dictionary = {}
var _pending: Array[String] = []


## The logic said `moment:<id>`: play it when the player is (or arrives) in the moment's room.
func on_moment(id: String) -> void:
	if moving or room_of_view((room.get("cam") as RoomCamera).current()) != _moment_room(id):
		_pending.append(id)
	else:
		play_moment(id)


func _moment_room(m: String) -> String:
	return {"m1": "pump", "m2": "pump", "m3": "cold", "m4": "gallery", "m5": "cold", "m6": "cold"}.get(m, "")


var _fade_tw: Tween


func _fade_to(a: float, seconds: float) -> void:
	_fade_to_async(a, seconds)
	await _fade_wait()


## Starts a fade without waiting for it.
func _fade_to_async(a: float, seconds: float, delay: float = 0.0) -> void:
	if _fade_tw != null and _fade_tw.is_valid():
		_fade_tw.kill()
	if seconds <= 0.0 and delay <= 0.0:
		_fade.color.a = a
		_fade_tw = null
		return
	_fade_tw = create_tween()
	if delay > 0.0:
		_fade_tw.tween_interval(delay)
	_fade_tw.tween_property(_fade, "color:a", a, maxf(seconds, 0.001))
	_tweens.append(_fade_tw)


func _fade_in_at(delay: float, seconds: float) -> void:
	_fade_to_async(1.0, seconds, maxf(delay, 0.0))


func _fade_wait() -> void:
	if _fade_tw != null and _fade_tw.is_valid() and _fade_tw.is_running():
		await _fade_tw.finished


## A tap while the room change is on (the touch input is off then): jump to the end of the walk and the fades.
func _unhandled_input(event: InputEvent) -> void:
	if not moving or _skipped:
		return
	if (event is InputEventScreenTouch and (event as InputEventScreenTouch).pressed) \
			or (event is InputEventMouseButton and (event as InputEventMouseButton).pressed):
		_skipped = true
		var cam: RoomCamera = room.get("cam")
		cam.skip_travel()
		for tw in _tweens:
			if tw != null and tw.is_valid() and tw.is_running():
				tw.custom_step(30.0)
		_tweens.clear()
		get_viewport().set_input_as_handled()


## Starts the scene's current room at once (a loaded save, QA tools): no fade.
func jump(room_id: String) -> void:
	ensure(room_id)
	activate(room_id)
	(room.get("cam") as RoomCamera).go(str(ROOT_VIEW.get(room_id, "hall")), true)
	_set_ambience(room_id)


# ====================================================================== reaction moments
## Plays one reaction moment (section 11): once per save (the logic's moments_seen decides), never over a caption, never
## when Settings "moments" is off; "soft" plays the picture and the caption without the sound sting.
func play_moment(id: String) -> void:
	if _played.has(id):
		return
	_played[id] = true
	var mode := str(Settings.get_value("moments"))
	if mode == "off":
		return
	var hud: Node = room.get("hud")
	var guard := 0
	while float(hud.call("caption_left")) > 0.0 and guard < 40:
		guard += 1
		await get_tree().create_timer(0.25).timeout
	if not is_instance_valid(room) or room_of_view((room.get("cam") as RoomCamera).current()) != _moment_room(id):
		return
	var b := builder(_moment_room(id))
	var seconds := float((ArchiveExpData.MOMENTS[id] as Dictionary).get("seconds", 3.0))
	if b != null and b.has_method("moment_" + id):
		b.call("moment_" + id, seconds, mode == "full")
	var cue_id := str(MOMENT_SOUND.get(id, ""))
	if cue_id != "": # Full plays the plain cue, Soft its _soft variant (Off returned above)
		AudioManager.sfx(cue_id if mode == "full" else cue_id + "_soft")
	var cap := logic.caption_key("moment:" + id)
	if cap != "":
		hud.call("caption", tr(cap), maxf(seconds, 3.5))


# ====================================================================== audio
func _set_ambience(room_id: String) -> void:
	for id: String in AMBIENCE:
		AudioManager.ambience(str(AMBIENCE[id]), id == room_id, -4.0 if id == "hall" else -6.0, 1.5)


## Plays the first existing sound of the cue's list (the real id once the sound designer pushed it).
func _cue(id: String, volume_db: float = 0.0, pitch: float = 1.0) -> void:
	cue(id, volume_db, pitch)


static func cue(id: String, volume_db: float = 0.0, pitch: float = 1.0) -> void:
	if id == "":
		return
	var names: Array = CUES.get(id, [id])
	for n: String in names:
		if AudioManager.stream("sfx", n) != null:
			AudioManager.sfx(n, volume_db, pitch)
			return


# ====================================================================== placeholder rooms
## A room whose models are not in yet: a plain box room with its name and a way back. Never reachable in a build
## where ArchiveLogic.EXPANSION_STAGE is 0 (the logic keeps the room sealed). TODO(models): replaced by the real zones.
func _build_placeholder(room_id: String, root: Node3D) -> Object:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color("3a3a3a")
	mat.roughness = 0.95
	var shell := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(6.0, 3.0, 6.0)
	shell.mesh = box
	shell.position = Vector3(0, 1.5, 0)
	var inside := mat.duplicate() as StandardMaterial3D
	inside.cull_mode = BaseMaterial3D.CULL_FRONT
	shell.material_override = inside
	root.add_child(shell)
	var lamp := OmniLight3D.new()
	lamp.position = Vector3(0, 2.4, 0)
	lamp.omni_range = 7.0
	lamp.light_energy = 1.2
	root.add_child(lamp)
	var label := Label3D.new()
	label.text = "%s\nPLACEHOLDER (TODO model)" % tr(str(_room_name(room_id)))
	label.font_size = 64
	label.pixel_size = 0.004
	label.position = Vector3(0, 1.6, -2.9)
	label.no_depth_test = true
	root.add_child(label)
	var exit_door := MeshInstance3D.new()
	var door_box := BoxMesh.new()
	door_box.size = Vector3(1.0, 2.0, 0.1)
	exit_door.mesh = door_box
	exit_door.position = Vector3(0, 1.0, 2.9)
	exit_door.material_override = mat
	root.add_child(exit_door)
	var back: String = BACK_ROOM.get(room_id, "pump")
	var area := room.call("add_tap_area", root, Vector3(1.2, 2.2, 0.4), "zone_back_" + back, "Exit_" + back, Vector3(0, 1.1, 2.8)) as StaticBody3D
	area.name = "Exit"
	var cam: RoomCamera = room.get("cam")
	cam.add_view(room_id, root.position + Vector3(0, 1.6, 2.0), root.position + Vector3(0, 1.3, -3.0), 64.0, true)
	register(room_id, [room_id], {"zone_back_" + back: room_id}, {}, {room_id: _room_name(room_id)})
	return null


func _room_name(room_id: String) -> String:
	for r: Dictionary in ArchiveExpData.ROOMS:
		if r["id"] == room_id:
			return r["name"]
	return ""


## Taps on a placeholder room's exit door. -> true when it was one.
func interact_placeholder(hs: String) -> bool:
	if not hs.begins_with("zone_back_"):
		return false
	logic.enter_room(hs.substr(10))
	return true
