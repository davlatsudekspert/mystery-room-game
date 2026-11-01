class_name ArchiveZones
extends Node
## Chapter 2 expansion ("The Whole Building", docs/CHAPTER2_EXPANSION.md sections 3, 7 and 11): the multi-room layer of
## the Archive scene. Each room of the plan is a *zone*: a Node3D far away from the hall (ZONE_OFFSET) that is built the
## first time it is needed, and shown only while it is the current room (the hall keeps its own nodes and is simply too
## far away to be drawn: the camera's far plane is 40 m, the zones are 60 m apart, so a zone costs nothing while the
## player is elsewhere). This class owns
## - the zone registry, lazy building (a zone class per room, ArchivePump so far; a marked placeholder for the rooms whose
##   models are not in yet, never shown while ArchiveLogic.EXPANSION_STAGE is 0),
## - transitions: any `room:<id>` event of the logic (enter_room, travel_to, from a door, the plan or a hint) fades to
##   black, switches zone, environment and camera, and fades back (0.4 s in all, shorter with reduce motion),
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
const BUILDERS := {"pump": "res://src/rooms/archive/archive_pump.gd"}

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
const REFUSED := ["valves_locked_n2", "need_mallet", "sheets_locked", "cranks_locked", "need_aisle", "need_cloth", "no_pressure",
	"weights_locked", "room_locked", "travel_refused"]

var room: Node3D
var logic: ArchiveLogic
var zones: Dictionary = {} # room id -> {"root": Node3D, "builder": Object}
var hall_exp: ArchiveHallExp # what the new game adds to the hall (null in a 1.0 game)
var current := "hall"
var moving := false
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
	return {"hall": ArchiveHallExp.VIEWS, "pump": ArchivePump.VIEWS}


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
	current = room_id
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
## The scene's reaction to the logic's `room:<id>` event: fade, switch, fade back. Taps are ignored meanwhile.
func transition(room_id: String) -> void:
	if moving or room_id == current:
		return
	moving = true
	var hud: Node = room.get("hud")
	hud.call("set_busy", true)
	var calm := bool(Settings.get_value("reduce_motion"))
	var t_out := 0.12 if calm else 0.2
	await _fade_to(1.0, t_out)
	var from := current
	ensure(room_id)
	activate(room_id)
	var cam: RoomCamera = room.get("cam")
	cam.go(str(ROOT_VIEW.get(room_id, "hall")), true)
	if from != room_id:
		_cue("room_step")
		_set_ambience(room_id)
	await _fade_to(0.0, 0.0 if calm else 0.2)
	hud.call("set_busy", false)
	moving = false
	var visuals: Node = room.get("visuals")
	if visuals != null:
		visuals.call("apply_state", false)
	_after_enter(room_id)


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


func _fade_to(a: float, seconds: float) -> void:
	if seconds <= 0.0:
		_fade.color.a = a
		return
	var tw := create_tween()
	tw.tween_property(_fade, "color:a", a, seconds)
	await tw.finished


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
