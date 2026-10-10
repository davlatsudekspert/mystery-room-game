class_name ArchiveRoom
extends RoomBase
## Chapter 2 scene: Records Archive B, the projection booth and the vault.
## It assembles the room from the models in docs/models/ch2.md, routes taps to ArchiveLogic and lets
## ArchiveVisuals render the resulting state. Every visual is derived from logic.state.

## Render layer for meshes the reflection probe must not capture (emissive lamp linings).
const NO_PROBE_LAYER := 1 << 19

## model -> [position, yaw degrees (front +Z = 0), hotspot id, collider mode]
const LAYOUT := {
	"room_archive": [Vector3.ZERO, 0.0, "", "static"],
	"vent_grille": [Vector3(-5.0, 2.55, 0.9), 90.0, "grille", "parts"],
	"floor_hatch": [Vector3(0.9, 0.0, 2.5), 0.0, "hatch", "parts"],
	"projection_screen": [Vector3(-2.5, 0.0, -3.5), 0.0, "screen", "parts"],
	"library_ladder": [Vector3(-4.62, 0.0, 0.35), 90.0, "", "none"],
	"card_catalogue": [Vector3(-5.0, 0.0, -1.2), 90.0, "catalogue", "parts"],
	"stacks_shelving": [Vector3(0.0, 0.0, 0.25), 0.0, "stacks", "parts"],
	"archivist_desk": [Vector3(3.7, 0.0, -3.1), 0.0, "desk", "parts"],
	"reading_table": [Vector3(1.9, 0.0, 1.0), 0.0, "reading", "parts"],
	"lockers": [Vector3(0.6, 0.0, 3.5), 180.0, "lockers", "parts"],
	"routing_chart": [Vector3(5.0, 0.0, -0.35), -90.0, "chart", "parts"],
	"film_splicer": [Vector3(-3.9, 0.0, 3.5), 180.0, "splicer", "parts"],
	"slide_cabinet": [Vector3(-5.0, 0.0, 2.8), 90.0, "slides", "parts"],
	"lens_case": [Vector3(-3.75, 1.45, 3.37), 180.0, "lens_case", "parts"],
	"tube_station": [Vector3(5.0, 0.0, -1.4), -90.0, "station", "parts"],
	"compressor_panel": [Vector3(5.0, 0.0, 0.8), -90.0, "compressor", "parts"],
	"card_punch": [Vector3(3.25, 0.76, -3.05), 0.0, "punch", "parts"],
	"tape_deck": [Vector3(4.15, 0.76, -3.05), 0.0, "deck", "parts"],
	"booth_door": [Vector3(-1.55, 0.0, 2.0), 180.0, "booth_door", "parts"],
	"film_projector": [Vector3(-2.9, 0.0, 2.65), 180.0, "projector", "parts"],
	"slide_projector": [Vector3(-2.35, 0.0, 2.45), 180.0, "slide_projector", "parts"],
	"vault_door": [Vector3(1.5, 0.0, -3.5), 0.0, "vault", "parts"],
	"vault_interior": [Vector3.ZERO, 0.0, "vault_inside", "parts"],
}

## Extra instances and reused Chapter 1 / CC0 dressing: id -> [model, position, yaw, hotspot]
const EXTRA := {
	"pendant_0": ["archive_pendant", Vector3(-3.0, 3.6, -2.0), 0.0, ""],
	"pendant_1": ["archive_pendant", Vector3(0.0, 3.6, -2.4), 0.0, ""],
	"pendant_2": ["archive_pendant", Vector3(3.0, 3.6, -2.0), 0.0, ""],
	"pendant_3": ["archive_pendant", Vector3(-2.8, 3.6, 1.4), 0.0, ""],
	"pendant_4": ["archive_pendant", Vector3(0.0, 3.6, 1.6), 0.0, ""],
	"pendant_5": ["archive_pendant", Vector3(3.0, 3.6, 1.4), 0.0, ""],
	"chair_desk": ["chair", Vector3(3.55, 0.0, -2.35), 172.0, ""],
	"chair_read_a": ["chair", Vector3(1.55, 0.0, 1.62), 186.0, ""],
	"chair_read_b": ["chair", Vector3(2.35, 0.0, 0.42), -8.0, ""],
	"desk_lamp": ["desk_lamp", Vector3(3.05, 0.76, -3.32), 20.0, "desk"],
	"cc_magnifier": ["cc0/magnifying_glass_01/magnifying_glass_01", Vector3(2.25, 0.76, 1.12), 40.0, "reading"],
	"cc_spectacles": ["cc0/round_spectacles/round_spectacles", Vector3(1.45, 0.76, 0.86), -25.0, "reading"],
	"cc_books": ["cc0/book_encyclopedia_set_01/book_encyclopedia_set_01", Vector3(4.0, 0.76, -3.36), 0.0, "desk"],
}

## Echo figures: id -> [model, position, yaw]
const ECHO_FIGURES := {
	"catalogue": ["echo_archivist", Vector3(-4.05, 0.0, -1.05), -90.0],
	"stacks": ["echo_scientists", Vector3(-0.8, 0.0, -1.7), 50.0],
	"booth": ["echo_strand_standing", Vector3(-3.6, 0.0, 2.45), 180.0],
}
const LEYLA_ECHO_FROM := Vector3(-3.2, 0.0, 2.4)
const LEYLA_ECHO_TO := Vector3(-4.15, 0.0, 2.62)

const HOTSPOT_VIEW := {
	"catalogue": "catalogue", "grille": "grille", "stacks": "stacks", "reading": "reading", "hatch": "hatch",
	"lockers": "lockers", "station": "station", "chart": "chart", "compressor": "compressor", "desk": "desk",
	"punch": "punch", "deck": "deck", "vault": "vault", "screen": "screen", "booth_door": "booth_door",
	"projector": "projector", "splicer": "splicer", "slides": "slides", "slide_projector": "slide_projector",
	"lens_case": "lens_case", "vault_inside": "vault_inside", "aisle": "west",
}
const DEEPER := {
	"catalogue": ["cat_drawer", "cat_section"], "stacks": ["ledger"], "lockers": ["locker9"], "desk": ["punch", "deck"],
	"vault": ["vault_ports"], "screen": ["socket"], "booth_door": ["dial"],
}
const CAPTION := {
	"hall": "obj2.hall", "west": "obj2.hall", "booth": "obj2.booth", "catalogue": "obj2.catalogue",
	"cat_drawer": "obj2.catalogue", "cat_section": "obj2.catalogue", "compressor": "obj2.compressor", "station": "obj2.station", "chart": "obj2.chart",
	"desk": "obj2.desk", "punch": "obj2.punch", "deck": "obj2.deck", "lockers": "obj2.lockers", "locker9": "obj2.lockers",
	"stacks": "obj2.stacks", "grille": "obj2.grille", "ledger": "obj2.ledger", "reading": "obj2.reading",
	"hatch": "obj2.hatch", "booth_door": "obj2.booth_door", "dial": "obj2.booth_door", "splicer": "obj2.splicer",
	"projector": "obj2.projector", "slides": "obj2.slides", "slide_projector": "obj2.slide_projector",
	"lens_case": "obj2.booth", "screen": "obj2.screen", "socket": "obj2.screen", "vault": "obj2.vault",
	"vault_ports": "obj2.vault", "vault_inside": "obj2.vault_open", "shutter": "obj2.shutter",
}
## Views that are inside the projection booth (the booth interior is only drawn while one is active).
const CAT_VIEWS := ["catalogue", "cat_drawer", "cat_section"]
const BOOTH_VIEWS := ["booth", "projector", "splicer", "slides", "slide_projector", "lens_case"]
const VAULT_VIEWS := ["vault", "vault_ports", "vault_inside", "vault_mouth"]

var visuals: ArchiveVisuals
var _held_frame := -1 # splicer: the loose film strip the player picked up
var _cinematic := false
var _knob_acc := 0.0
var _drag_kind := ""


func _ready() -> void:
	if GameState.logic == null or not GameState.logic is ArchiveLogic:
		GameState.start_new("ch2")
	logic = GameState.logic
	GameState.in_game = true
	make_environment(Color("0a0c0d"), Color("2a3a36"), 0.5, Color("1a2826"), 0.014)
	# A soft halo on real light sources only: the shared 0.6 / 0.05 / 1.1 bloomed the pendant shades, the splicer's
	# light box and the projector lens into white patches
	env.glow_intensity = 0.4
	env.glow_bloom = 0.0
	env.glow_hdr_threshold = 1.35
	# this game's own index-card notches (docs/VARIANTS.md); the art is picked before anything is built
	var punch := int((logic as ArchiveLogic).state["v_punch"])
	DecalLoc.set_variants({"index_card": "_p%d" % punch} if punch > 0 else {})
	_build_models()
	_build_lights()
	build_camera()
	_build_views()
	visuals = ArchiveVisuals.new(self)
	add_child(visuals)
	build_input()
	build_hud()
	add_child(PerfGuard.new())
	GameState.events.connect(_on_events)
	visuals.apply_state(false)
	DecalLoc.apply(self)
	Loc.language_changed.connect(_on_language_changed)
	cam.go("hall", true)
	AudioManager.music("music_archive", 4.0)
	AudioManager.ambience("amb_archive", true, -4.0)
	if not capture_mode and _fresh_start():
		hud.call("play_intro")
	SceneManager.room_ready(self) # safe graphics before the first frame is drawn


func _exit_tree() -> void:
	GameState.in_game = false


## Views whose camera depends on the state are framed here first (used by the room and by QA tools).
func prepare_view(id: String) -> void:
	var s := (logic as ArchiveLogic).state
	if id == "cat_drawer":
		visuals.frame_cat_drawer(maxi(0, int(s["cat_drawer"])))
	elif id == "cat_section":
		visuals.frame_cat_section(maxi(0, int(s["cat_group"])))


func _on_language_changed(_code: String) -> void:
	DecalLoc.refresh()
	DecalLoc.apply(self)


func _fresh_start() -> bool:
	var s: Dictionary = (logic as ArchiveLogic).state
	return (s["taken"] as Dictionary).is_empty() and int(s["cat_drawer"]) < 0 and not s["pressure_ok"]


# ====================================================================== construction
func _build_models() -> void:
	for id: String in LAYOUT:
		var e: Array = LAYOUT[id]
		spawn(id, id, e[0], e[1], e[2], e[3])
	for id: String in EXTRA:
		var e: Array = EXTRA[id]
		spawn(id, e[0], e[1], e[2], e[3], "parts" if e[3] != "" else "none")
	# The shell's outer walls, ceiling and trim enclose every light, so their shadows are never seen:
	# skipping them saves the shadow pass a few thousand triangles on every frame.
	for mi in ModelUtil.find_meshes(models.get("room_archive")):
		var nm := str(mi.name)
		if nm.begins_with("wall_") or nm in ["ceiling", "trim", "corridor", "wall_dressing"]:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var echo_mat := ShaderMaterial.new()
	echo_mat.shader = load("res://src/fx/echo.gdshader")
	for id: String in ECHO_FIGURES:
		var e: Array = ECHO_FIGURES[id]
		var n := spawn("echo_" + id, e[0], e[1], e[2], "", "none")
		if n:
			_prepare_echo(n, echo_mat.duplicate() as ShaderMaterial)
			add_tap_area(n, Vector3(0.9, 1.8, 0.9), "", "Echo_" + id, Vector3(0, 0.9, 0))
			set_present(n, false)
	var leyla := spawn("echo_leyla", "echo_leyla_standing", LEYLA_ECHO_FROM, -90.0, "", "none")
	if leyla:
		_prepare_echo(leyla, echo_mat.duplicate() as ShaderMaterial)
		leyla.visible = false
	# the shelves' contents and the desk's book row each draw as one mesh (one surface per material)
	ModelUtil.merge_static(models.get("stacks_shelving"), "contents_")
	ModelUtil.merge_static(models.get("cc_books"), "book_encyclopedia")
	var dust := DustMotes.create(Vector3(4.5, 1.6, 3.2), 180)
	dust.position = Vector3(0, 1.7, 0)
	add_child(dust)
	_build_aisle_sign()


## The card catalogue stands on the west wall, hidden from the hall by the stacks. An enamel sign hangs over the
## aisle at the corner of the stacks and points the way; tapping it (or the far floor and walls) walks there.
const AISLE_SIGN_POS := Vector3(-1.05, 2.62, 0.8)
const WEST_OF_STACKS_X := -1.6 # a tap on the bare room beyond this from the hall walks to the west aisle


func _build_aisle_sign() -> void:
	var sign := Node3D.new()
	sign.name = "aisle_sign"
	add_child(sign)
	# face the hall camera (the plate's front is +Z)
	sign.look_at_from_position(AISLE_SIGN_POS, Vector3(3.8, AISLE_SIGN_POS.y, 1.8), Vector3.UP, true)
	sign.scale = Vector3.ONE * 1.25 # readable from the hall on a phone
	models["aisle_sign"] = sign
	_roots[sign] = "aisle_sign"
	sign.set_meta("hotspot", "aisle")
	var green: Material = load("res://assets/materials/M_Enamel_Green.tres")
	var cream: Material = load("res://assets/materials/M_Enamel_Cream.tres")
	var brass: Material = load("res://assets/materials/M_Brass_Aged.tres")
	var plate := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(0.82, 0.2, 0.018)
	plate.mesh = box
	plate.material_override = green
	sign.add_child(plate)
	var rim := MeshInstance3D.new() # a cream border line, as on enamel signs
	var rim_box := BoxMesh.new()
	rim_box.size = Vector3(0.79, 0.17, 0.001)
	rim.mesh = rim_box
	rim.material_override = cream
	rim.position = Vector3(0, 0, 0.0095)
	sign.add_child(rim)
	var inner := MeshInstance3D.new()
	var inner_box := BoxMesh.new()
	inner_box.size = Vector3(0.77, 0.15, 0.001)
	inner.mesh = inner_box
	inner.material_override = green
	inner.position = Vector3(0, 0, 0.0102)
	sign.add_child(inner)
	var text := Label3D.new()
	text.text = "obj2.sign_catalogue"
	text.font = load(UITheme.FONT_DISPLAY_BOLD)
	text.font_size = 80
	text.pixel_size = 0.00075
	text.modulate = Color("efe6cf")
	text.outline_size = 0
	text.position = Vector3(0.045, -0.004, 0.0112)
	text.double_sided = false
	sign.add_child(text)
	# an arrow on the left: round the stacks' south end, into the west aisle
	var head := MeshInstance3D.new()
	var prism := PrismMesh.new()
	prism.size = Vector3(0.06, 0.05, 0.002)
	head.mesh = prism
	head.material_override = cream
	head.rotation = Vector3(0, 0, deg_to_rad(90.0))
	head.position = Vector3(-0.335, 0, 0.0112)
	sign.add_child(head)
	var shaft := MeshInstance3D.new()
	var shaft_box := BoxMesh.new()
	shaft_box.size = Vector3(0.045, 0.014, 0.002)
	shaft.mesh = shaft_box
	shaft.material_override = cream
	shaft.position = Vector3(-0.29, 0, 0.0112)
	sign.add_child(shaft)
	for side in [-1.0, 1.0]:
		var chain := MeshInstance3D.new()
		var rod := CylinderMesh.new()
		rod.top_radius = 0.004
		rod.bottom_radius = 0.004
		rod.height = (3.6 - AISLE_SIGN_POS.y) / 1.25 - 0.1
		rod.radial_segments = 6
		chain.mesh = rod
		chain.material_override = brass
		chain.position = Vector3(side * 0.34, 0.1 + rod.height / 2.0, 0)
		sign.add_child(chain)
	for mi in ModelUtil.find_meshes(sign):
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_tap_area(sign, Vector3(0.9, 0.3, 0.12), "aisle", "IA_aisle_sign")


func _prepare_echo(n: Node3D, mat: ShaderMaterial) -> void:
	for mi in ModelUtil.find_meshes(n):
		mi.material_override = mat
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func _build_lights() -> void:
	# Pendants: warm working light, dimmed during the film.
	for i in 6:
		var p := OmniLight3D.new()
		p.light_color = Color("ffc58a")
		p.light_energy = 1.25
		p.omni_range = 5.2
		p.omni_attenuation = 1.3
		var e: Array = EXTRA["pendant_%d" % i]
		p.position = (e[1] as Vector3) + Vector3(0, -0.85, 0)
		p.shadow_enabled = false
		p.set_meta("base_energy", p.light_energy)
		add_child(p)
		lights["pendant_%d" % i] = p
		if i == 1:
			# The one shadowed light: the shade throws a downward cone over the vault and the stacks. A spot
			# shadow is one pass over the casters inside its cone; the omni it replaced rendered a
			# dual-paraboloid shadow of nearly every caster in the room twice, every frame.
			p.light_energy = 1.0
			p.set_meta("base_energy", p.light_energy)
			var cone := SpotLight3D.new()
			cone.light_color = p.light_color
			cone.light_energy = 0.5
			cone.set_meta("base_energy", cone.light_energy)
			cone.spot_range = 5.0
			cone.spot_angle = 58.0
			cone.spot_angle_attenuation = 0.8
			cone.shadow_enabled = true
			add_child(cone)
			cone.look_at_from_position(p.position, p.position + Vector3(0, -1, 0.001), Vector3.FORWARD)
			lights["pendant_1_cone"] = cone
	# Emergency lamps: amber accents low on the walls (two real lights; the rest are emissive glass).
	for k in 2:
		var em := OmniLight3D.new()
		em.light_color = Color("ff9a3c")
		em.light_energy = 0.45
		em.omni_range = 3.0
		em.position = [Vector3(-4.7, 2.8, 0.25), Vector3(4.7, 2.8, 0.0)][k]
		add_child(em)
		lights["emergency_%d" % k] = em
	var desk := OmniLight3D.new()
	desk.light_color = Color("ffb46b")
	desk.light_energy = 1.0
	desk.omni_range = 2.4
	desk.position = Vector3(3.1, 1.2, -3.2)
	add_child(desk)
	lights["desk_lamp"] = desk
	var banker := OmniLight3D.new()
	banker.light_color = Color("ffd29a")
	banker.light_energy = 0.9
	banker.omni_range = 2.2
	banker.position = Vector3(1.9, 1.15, 1.25)
	add_child(banker)
	lights["banker"] = banker
	var booth := OmniLight3D.new()
	booth.light_color = Color("ffcf94")
	booth.light_energy = 0.0
	booth.omni_range = 3.4
	booth.position = Vector3(-3.0, 2.55, 2.85)
	add_child(booth)
	lights["booth"] = booth
	var beam := SpotLight3D.new() # the film/slide projection light on the screen
	beam.light_color = Color("f4f1e6")
	beam.light_energy = 0.0
	beam.spot_range = 8.0
	beam.spot_angle = 14.0
	add_child(beam)
	beam.look_at_from_position(Vector3(-2.9, 1.95, 2.3), Vector3(-2.5, 1.9, -3.45), Vector3.UP)
	lights["beam"] = beam
	var vault := OmniLight3D.new()
	vault.light_color = Color("cff6ff")
	vault.light_energy = 0.0
	vault.omni_range = 4.0
	vault.position = Vector3(1.5, 1.6, -4.4)
	add_child(vault)
	lights["vault"] = vault
	var fill := OmniLight3D.new() # follows the camera in close-ups so dark corners stay readable
	fill.light_color = Color("ffe2c2")
	fill.light_energy = 0.0
	fill.omni_range = 2.4
	fill.light_specular = 0.0 # a helper light: lift the shadows, never paint a hot spot on glossy enamel or glass
	fill.omni_attenuation = 1.3
	add_child(fill)
	lights["focus_fill"] = fill
	# The interior probe's captured light is also the room's bounce light (most of the walls' brightness). Glowing
	# lamp linings stay out of it (NO_PROBE_LAYER), or the whole floor brightens.
	var probe := ReflectionProbe.new()
	probe.size = Vector3(10, 3.6, 7)
	probe.position = Vector3(0, 1.8, 0)
	probe.update_mode = ReflectionProbe.UPDATE_ONCE
	probe.interior = true
	probe.cull_mask = ~NO_PROBE_LAYER & 0xFFFFF
	add_child(probe)


func _build_views() -> void:
	var V := cam.add_view
	V.call("hall", Vector3(3.8, 1.65, 1.8), Vector3(0.0, 1.3, -2.2), 62.0, true)
	V.call("west", Vector3(-1.8, 1.65, 1.0), Vector3(-3.0, 1.5, -3.0), 62.0, true)
	V.call("booth", Vector3(-1.55, 1.6, 2.6), Vector3(-4.6, 1.1, 2.9), 62.0, true)
	V.call("catalogue", Vector3(-3.55, 1.5, -1.2), Vector3(-4.7, 1.0, -1.2), 50.0)
	V.call("cat_drawer", Vector3(-3.85, 1.55, -1.2), Vector3(-4.4, 0.95, -1.2), 42.0)
	V.call("grille", Vector3(-3.7, 1.9, 0.9), Vector3(-5.0, 2.55, 0.9), 46.0)
	V.call("stacks", Vector3(0.0, 1.5, 2.3), Vector3(0.0, 1.1, 0.7), 56.0)
	V.call("ledger", Vector3(0.4, 1.3, 1.5), Vector3(0.35, 1.0, 0.65), 40.0)
	V.call("reading", Vector3(1.9, 1.6, 2.35), Vector3(1.9, 0.8, 1.0), 52.0)
	V.call("hatch", Vector3(1.7, 1.55, 1.65), Vector3(0.9, 0.0, 2.55), 50.0) # from the north-east: an open locker door stays behind the hatch
	V.call("lockers", Vector3(0.6, 1.35, 1.5), Vector3(0.6, 0.95, 3.5), 56.0)
	V.call("locker9", Vector3(0.8, 0.95, 2.45), Vector3(0.8, 0.58, 3.35), 46.0) # centred on locker 9 (x 0.6–1.0)
	V.call("station", Vector3(3.55, 1.55, -1.4), Vector3(4.95, 1.2, -1.4), 52.0)
	V.call("chart", Vector3(3.9, 1.7, -0.35), Vector3(5.0, 1.75, -0.35), 44.0)
	V.call("compressor", Vector3(3.65, 1.45, 0.8), Vector3(5.0, 1.25, 0.8), 52.0)
	V.call("desk", Vector3(3.7, 1.6, -1.85), Vector3(3.7, 0.8, -3.1), 52.0)
	V.call("punch", Vector3(3.25, 1.2, -2.35), Vector3(3.25, 0.82, -3.05), 40.0)
	V.call("deck", Vector3(4.15, 1.2, -2.35), Vector3(4.15, 0.82, -3.05), 40.0)
	V.call("vault", Vector3(1.5, 1.55, -0.9), Vector3(1.5, 1.35, -3.5), 56.0)
	V.call("vault_ports", Vector3(1.5, 1.65, -2.3), Vector3(1.5, 1.55, -3.4), 50.0)
	V.call("screen", Vector3(-2.5, 1.7, -0.5), Vector3(-2.5, 1.9, -3.45), 56.0)
	V.call("socket", Vector3(-2.5, 1.2, -2.65), Vector3(-2.5, 0.92, -3.38), 40.0)
	V.call("booth_door", Vector3(-1.55, 1.45, 0.75), Vector3(-1.55, 1.2, 2.0), 52.0)
	V.call("dial", Vector3(-1.8, 1.25, 1.5), Vector3(-1.82, 1.2, 2.0), 36.0)
	V.call("projector", Vector3(-2.1, 2.05, 2.95), Vector3(-2.86, 1.98, 2.6), 50.0) # the control side: lever, focus, frame keys, reels
	V.call("splicer", Vector3(-3.9, 1.55, 2.55), Vector3(-3.9, 0.95, 3.3), 48.0)
	V.call("slides", Vector3(-3.85, 1.3, 2.8), Vector3(-4.8, 0.7, 2.8), 48.0)
	V.call("slide_projector", Vector3(-1.75, 1.95, 2.95), Vector3(-2.35, 1.8, 2.45), 44.0)
	V.call("lens_case", Vector3(-3.75, 1.85, 2.8), Vector3(-3.75, 1.47, 3.37), 40.0)
	V.call("vault_inside", Vector3(1.5, 1.55, -3.0), Vector3(1.5, 1.3, -5.2), 56.0)
	# cinematic-only views
	V.call("tubes", Vector3(3.2, 1.6, 0.9), Vector3(1.6, 3.0, -1.1), 64.0)
	V.call("film", Vector3(-2.15, 1.6, 1.05), Vector3(-2.5, 1.9, -3.45), 58.0)
	V.call("vault_mouth", Vector3(1.5, 1.6, -1.6), Vector3(1.5, 1.4, -4.6), 58.0)
	V.call("shutter", Vector3(3.3, 1.6, 1.2), Vector3(3.5, 1.2, 3.5), 56.0)


# ====================================================================== hooks
func main_root() -> String:
	return "hall"


func hotspot_view(hs: String) -> String:
	if hs in ["projector", "splicer", "slides", "slide_projector", "lens_case"] and cam.current() == "hall":
		return "booth" if logic.state["booth_open"] else "booth_door"
	return HOTSPOT_VIEW.get(hs, "")


func deeper_views() -> Dictionary:
	return DEEPER


func view_caption(id: String) -> String:
	var s := logic.state
	if id in ["vault", "vault_ports"] and s["vault_open"]:
		return "obj2.vault_open"
	if id == "booth_door" and s["booth_open"]:
		return "obj2.booth"
	return CAPTION.get(id, "")


func use_target(hs: String, p: String) -> String:
	var sel := logic.selected
	match hs:
		"punch":
			return "punch"
		"station":
			if sel == "request_card" and p in ["IA_card_tray", "tray_cards"]:
				return "card_tray"
			return "send_port"
		"lockers":
			return "locker_%d" % _locker_of(p) if _locker_of(p) > 0 else "locker_0"
		"deck":
			return "deck"
		"projector":
			return "projector"
		"slide_projector":
			return "slide_projector"
		"screen":
			return "screen_socket"
		"booth_door", "aisle":
			# ways through: with an item in hand the player still walks on
			if hs == "aisle" or logic.state["booth_open"]:
				return ""
		"vault":
			if p.ends_with("_left") or p == "port_left_mount":
				return "port_left"
			if p.ends_with("_right") or p == "port_right_mount":
				return "port_right"
			return "_"
	return "_" if sel != "" else ""


func _locker_of(p: String) -> int:
	return int(p.substr(10)) if p.begins_with("IA_locker_") else 0


func tap_special(p: String, r: Dictionary) -> bool:
	if p.begins_with("Echo_"):
		var id := p.substr(5)
		if not logic.has_method("release_echo"):
			return false
		var ev: Array[String] = (logic as ArchiveLogic).release_echo(id)
		return not ev.has("nothing_happens")
	# walking: a tap on the bare floor or walls beyond the stacks goes to the west aisle, and back again
	if str(r.get("hotspot", "")) == "" and cam.is_root():
		var x: float = (r.get("pos", Vector3.ZERO) as Vector3).x
		if cam.current() == "hall" and x < WEST_OF_STACKS_X:
			cam.go("west")
			AudioManager.ui("ui_tap")
			return true
		if cam.current() == "west" and x > 1.2:
			cam.go("hall")
			AudioManager.ui("ui_tap")
			return true
	return false


func drag_part_started(p: String) -> bool:
	_knob_acc = 0.0
	_drag_kind = ""
	if p == "IA_focus_ring" and cam.current() == "projector":
		_drag_kind = "focus"
	elif p in ["IA_collar_left", "IA_collar_right", "IA_zoom_right"] and cam.current() == "vault_ports":
		_drag_kind = p
	return _drag_kind != ""


const DRAG_PX_PER_STEP := 26.0


func drag_part(rel: Vector2) -> void:
	_knob_acc += (rel.x - rel.y) / (DRAG_PX_PER_STEP * maxf(1.0, DisplayServer.screen_get_scale()))
	var steps := int(_knob_acc)
	if steps == 0:
		return
	_knob_acc -= steps
	var l := logic as ArchiveLogic
	match _drag_kind:
		"focus":
			l.turn_focus(steps)
		"IA_collar_left":
			l.turn_collar("rot_left", steps)
		"IA_collar_right":
			l.turn_collar("rot_right", steps)
		"IA_zoom_right":
			l.turn_collar("zoom_right", steps)


func go_back() -> void:
	if _ending or _cinematic:
		return
	if cam.is_root():
		if cam.current() != main_root():
			cam.go(main_root())
		return
	var cur := cam.current()
	if not cam.back() and cur in BOOTH_VIEWS:
		cam.go("booth")


# ====================================================================== interactions
func interact(hs: String, p: String, r: Dictionary) -> void:
	var l := logic as ArchiveLogic
	var s := l.state
	var cur := cam.current()
	match hs:
		"catalogue":
			_interact_catalogue(p, r)
		"compressor":
			if cur != "compressor":
				cam.go("compressor")
			elif p.begins_with("IA_valve_"):
				l.turn_valve("abc".find(p.substr(9, 1)), 1)
			elif s["pressure_ok"]:
				hud.call("message", tr("msg.c2_valves_locked"))
			else:
				# a gauge, the plate or the tank: read the needles out
				var t: Array = s["v_targets"]
				hud.call("caption", tr("msg.c2_gauges") % [
					tr("msg.c2_on_mark" if l.pressure() == int(t[0]) else "msg.c2_off_mark"),
					tr("msg.c2_on_mark" if l.flow() == int(t[1]) else "msg.c2_off_mark")])
				AudioManager.ui("ui_tap")
		"station":
			_interact_station(p)
		"chart":
			if cur != "chart":
				cam.go("chart")
			else:
				hud.call("show_document", "routing_chart") # the chart full size in the reader, with its rule
				AudioManager.ui("ui_tap")
		"desk":
			if cur == "desk" or cur in ["punch", "deck"]:
				var px: float = (r["pos"] as Vector3).x
				cam.go("punch" if px < 3.7 else "deck")
			else:
				cam.go("desk")
		"punch":
			_interact_punch(p)
		"deck":
			_interact_deck(p)
		"lockers":
			_interact_lockers(p)
		"stacks":
			if p in ["IA_ledger", "ledger_cover"] or p.begins_with("Item_ledger"):
				if cur != "ledger":
					cam.go("ledger")
				elif not s["ledger_open"]:
					l.open_hiding_place("ledger")
				elif l.can_take("ledger_reel"):
					l.take("ledger_reel")
				else:
					_empty_now()
			elif cur == "hall" or cur == "west":
				cam.go("stacks")
			else:
				hud.call("message", tr("msg.c2_stacks_boxes"))
				AudioManager.ui("ui_tap")
		"grille":
			if cur != "grille":
				cam.go("grille")
			elif not s["grille_open"]:
				l.open_hiding_place("grille")
			elif l.can_take("grille_reel"):
				l.take("grille_reel")
			else:
				_empty_now()
		"hatch":
			if cur != "hatch":
				cam.go("hatch")
			elif not s["hatch_open"]:
				l.open_hiding_place("hatch")
			elif l.can_take("hatch_reel"):
				l.take("hatch_reel")
			else:
				_empty_now()
		"reading":
			if cur != "reading":
				cam.go("reading")
			else:
				hud.call("message", tr("msg.c2_reading_table"))
				AudioManager.ui("ui_tap")
		"booth_door":
			_interact_booth_door(p)
		"projector":
			_interact_projector(p)
		"splicer":
			_interact_splicer(p)
		"slides":
			_interact_slides(p)
		"slide_projector":
			_interact_slide_projector(p)
		"lens_case":
			if cur != "lens_case":
				cam.go("lens_case")
			elif not visuals.case_open:
				visuals.case_open = true
				visuals.apply_state(true)
				AudioManager.sfx("box_open", -2.0, 1.2)
			else:
				for spot in ["case_crystal_1", "case_crystal_2"]:
					if p == "Item_" + spot and l.can_take(spot):
						l.take(spot)
						return
				for spot in ["case_crystal_1", "case_crystal_2"]:
					if l.can_take(spot):
						l.take(spot)
						return
				_empty_now()
		"screen":
			if p in ["IA_screen_socket", "socket_ring"] or p.begins_with("Item_socket"):
				if cur != "socket":
					cam.go("socket")
				elif s["socket"] != "":
					l.take_from_socket()
				else:
					hud.call("message", tr("obj2.screen"))
			elif cur != "screen":
				cam.go("screen")
			else:
				# the screen itself: dark, blurred, or showing a picture
				var img := l.screen_image()
				if img == "":
					hud.call("message", tr("msg.c2_screen_dark"))
				elif img.begins_with("film:") and not l.is_sharp():
					hud.call("message", tr("msg.c2_blurred"))
				else:
					hud.call("caption", tr("cap2.projector"))
				AudioManager.ui("ui_tap")
		"vault":
			_interact_vault(p)
		_:
			pass


func _interact_catalogue(p: String, _r: Dictionary) -> void:
	var l := logic as ArchiveLogic
	var s := l.state
	var cur := cam.current()
	if p.begins_with("IA_cat_drawer_"):
		var i := int(p.substr(14))
		if cur not in CAT_VIEWS:
			cam.go("catalogue")
			return
		l.open_cat_drawer(i)
		return
	if p.begins_with("IA_divider_") and cur in ["cat_drawer", "cat_section"]:
		l.pick_divider(int(p.substr(11)))
		return
	if p.begins_with("IA_card_") and cur == "cat_drawer" and int(s["cat_group"]) >= 0:
		cam.go("cat_section") # the tabs are small from the tray view: come closer first
		return
	if p.begins_with("IA_card_") and cur == "cat_section":
		var n := int(p.substr(8))
		if s["card_shown"] and n == ArchiveLogic.CAT_CARD and l.can_take("index_card"):
			l.take("index_card")
		else:
			l.pull_card(n)
		return
	if p.begins_with("Item_index_card") and l.can_take("index_card"):
		l.take("index_card")
		return
	if cur not in CAT_VIEWS:
		cam.go("catalogue")
	elif int(s["cat_drawer"]) >= 0 and cur == "catalogue":
		cam.go("cat_drawer")
	else:
		hud.call("message", tr("msg.c2_catalogue_drawers"))
		AudioManager.ui("ui_tap")


func _interact_station(p: String) -> void:
	var l := logic as ArchiveLogic
	var s := l.state
	if cam.current() != "station":
		cam.go("station")
		return
	if p in ["IA_card_tray", "tray_cards"]:
		if l.can_take("tray_card"):
			l.take("tray_card")
		else:
			hud.call("message", tr("item.blank_card.desc"))
	elif p == "IA_dest_dial":
		l.step_dest(1)
	elif p == "IA_send_lever":
		l.send_canister()
	elif p in ["IA_receive_tray", "tray_door"] or p.begins_with("Item_canister"):
		if s["file_delivered"] and not visuals.tray_open:
			visuals.tray_open = true
			visuals.apply_state(true)
			AudioManager.sfx("box_open", -4.0, 1.3)
			return
		for spot in ["canister_file", "canister_key"]:
			if p == "Item_" + spot and l.can_take(spot):
				l.take(spot)
				return
		for spot in ["canister_file", "canister_key"]:
			if l.can_take(spot):
				l.take(spot)
				return
		_empty_now() # the receive tray: nothing has come back yet, or it was already taken
	else:
		# the send port, its flap or the station body: where the dispatch stands
		if s["canister"] != "":
			hud.call("message", tr("msg.c2_canister_loaded"))
		elif not s["pressure_ok"]:
			hud.call("message", tr("msg.c2_no_pressure"))
		else:
			hud.call("message", tr("msg.c2_tube_empty"))
		AudioManager.ui("ui_tap")


func _interact_punch(p: String) -> void:
	var l := logic as ArchiveLogic
	if cam.current() != "punch":
		cam.go("punch")
		return
	if p.begins_with("IA_punch_key_"):
		l.toggle_punch_key(int(p.substr(13)))
	elif p == "IA_punch_lever":
		l.pull_punch_lever()
	elif not l.state["card_in_punch"]:
		hud.call("message", tr("msg.c2_punch_empty"))


func _interact_deck(p: String) -> void:
	var l := logic as ArchiveLogic
	if cam.current() != "deck":
		cam.go("deck")
		return
	match p:
		"IA_speed":
			l.step_speed(1)
		"IA_play":
			l.play_tape()
		"IA_eject":
			visuals.stop_tape()
			if l.state["deck_tape"] == "":
				hud.call("message", tr("msg.c2_deck_empty"))
				AudioManager.sfx("deck_eject", -10.0, 1.2)
			else:
				l.eject_tape()
		_:
			if l.state["deck_tape"] == "":
				hud.call("message", tr("msg.c2_deck_empty"))
				AudioManager.ui("ui_tap")


func _interact_lockers(p: String) -> void:
	var l := logic as ArchiveLogic
	var s := l.state
	var cur := cam.current()
	var n := _locker_of(p)
	if p.begins_with("Item_locker") or (n == ArchiveLogic.LOCKER_LEYLA and s["locker_open"]):
		if cur != "locker9":
			cam.go("locker9")
		elif l.can_take("locker_receiver"):
			l.take("locker_receiver")
		else:
			hud.call("message", tr("msg.c2_locker_empty"))
			AudioManager.ui("ui_tap")
		return
	if cur not in ["lockers", "locker9"]:
		cam.go("lockers")
		return
	if n > 0:
		l.try_locker(n)


func _interact_booth_door(p: String) -> void:
	var l := logic as ArchiveLogic
	var cur := cam.current()
	if l.state["booth_open"]:
		cam.go("booth")
		return
	if p.begins_with("IA_dial_hole_"):
		if cur != "dial":
			cam.go("dial")
			return
		var d := int(p.substr(13))
		visuals.dial_spin(d)
		l.dial_digit(d)
		return
	if p == "IA_rotary_dial":
		if cur != "dial":
			cam.go("dial")
		else:
			hud.call("message", tr("msg.c2_dial_lock"))
			AudioManager.ui("ui_tap")
		return
	if cur != "booth_door":
		cam.go("booth_door")
	else:
		hud.call("message", tr("obj2.booth_door"))
		AudioManager.sfx("drawer_locked", -6.0, 0.8)


func _interact_projector(p: String) -> void:
	var l := logic as ArchiveLogic
	var s := l.state
	if cam.current() != "projector":
		cam.go("projector")
		return
	match p:
		"IA_run_lever":
			l.toggle_projector()
		"IA_focus_ring":
			l.turn_focus(1 if int(s["focus"]) < ArchiveLogic.FOCUS_STEPS - 1 else -(ArchiveLogic.FOCUS_STEPS - 1))
		"IA_frame_prev":
			l.step_frame(-1)
		"IA_frame_next":
			l.step_frame(1)
		_:
			if not s["reel_on_projector"]:
				hud.call("message", tr("hint.c2_project.1"))


func _interact_splicer(p: String) -> void:
	var l := logic as ArchiveLogic
	var s := l.state
	if cam.current() != "splicer":
		cam.go("splicer")
		return
	if s["reel_repaired"]:
		if l.can_take("splicer_reel"):
			l.take("splicer_reel")
		else:
			hud.call("message", tr("msg.c2_splicer_box"))
			AudioManager.ui("ui_tap")
		return
	if p.begins_with("IA_frame_"):
		var k := int(p.substr(9))
		var slot := (s["splice"] as Array).find(k)
		if slot >= 0:
			l.splice_lift(slot)
		_held_frame = k if _held_frame != k else -1
		visuals.held_frame = _held_frame
		visuals.apply_state(true)
		AudioManager.sfx("card_flick", -4.0, randf_range(0.95, 1.05))
		return
	if p.begins_with("IA_slot_"):
		var slot2 := int(p.substr(8))
		if _held_frame >= 0:
			l.splice_put(_held_frame, slot2)
			_held_frame = -1
			visuals.held_frame = -1
		elif int(s["splice"][slot2]) >= 0:
			l.splice_lift(slot2)
		visuals.apply_state(true)
		return
	# the light box, the can or the table
	hud.call("message", tr("msg.c2_splicer_box"))
	AudioManager.ui("ui_tap")


func _interact_slides(p: String) -> void:
	var l := logic as ArchiveLogic
	if cam.current() != "slides":
		cam.go("slides")
		return
	if p.begins_with("IA_slide_drawer_"):
		l.open_slide_drawer(int(p.substr(16)))
	elif p.begins_with("Item_slide_mark") and l.can_take("slide_mark"):
		l.take("slide_mark")


func _interact_slide_projector(p: String) -> void:
	var l := logic as ArchiveLogic
	var s := l.state
	if cam.current() != "slide_projector":
		cam.go("slide_projector")
		return
	match p:
		"IA_slide_rot":
			l.rotate_slide()
		"IA_slide_lamp":
			l.toggle_slide_lamp()
		_:
			if s["slide_in"]:
				l.eject_slide()
			else:
				hud.call("message", tr("msg.c2_slide_gate_empty"))
				AudioManager.ui("ui_tap")


func _interact_vault(p: String) -> void:
	var l := logic as ArchiveLogic
	var s := l.state
	var cur := cam.current()
	if s["vault_open"]:
		cam.go("vault_inside")
		return
	if p == "IA_vault_handle":
		if cur != "vault":
			cam.go("vault")
		else:
			visuals.wheel_spin()
			l.turn_wheel()
		return
	var port_part := p in ["IA_port_left", "IA_port_right", "IA_collar_left", "IA_collar_right", "IA_zoom_right",
		"port_left_mount", "port_right_mount", "glass_disc", "disc_bezel"] or p.begins_with("Item_port")
	if port_part and cur != "vault_ports":
		cam.go("vault_ports")
		return
	match p:
		"IA_collar_left":
			l.turn_collar("rot_left", 1)
		"IA_collar_right":
			l.turn_collar("rot_right", 1)
		"IA_zoom_right":
			l.turn_collar("zoom_right", 1)
		"IA_port_left", "port_left_mount", "Item_port_left":
			if s["port_left"] != "":
				l.take_from_port("left")
			else:
				hud.call("message", tr("msg.c2_port_empty"))
				AudioManager.ui("ui_tap")
		"IA_port_right", "port_right_mount", "Item_port_right":
			if s["port_right"] != "":
				l.take_from_port("right")
			else:
				hud.call("message", tr("msg.c2_port_empty"))
				AudioManager.ui("ui_tap")
		"glass_disc", "disc_bezel":
			hud.call("message", tr("msg.c2_disc"))
			AudioManager.ui("ui_tap")
		_:
			if cur != "vault":
				cam.go("vault")
			else:
				# the door body or a bolt: shut until the overlay matches, then the wheel opens it
				hud.call("message", tr("msg.c2_vault_shut" if not s["vault_unlocked"] else "msg.c2_vault_unlocked"))
				AudioManager.sfx("locker_rattle", -8.0, 0.7)


## A container the player has already emptied: say so instead of ignoring the tap.
func _empty_now() -> void:
	hud.call("message", tr("msg.empty_now"))
	AudioManager.ui("ui_tap")


# ====================================================================== per-frame
func _process(_delta: float) -> void:
	var fill: OmniLight3D = lights["focus_fill"]
	fill.global_position = cam.global_position + cam.global_basis * Vector3(0.12, 0.18, 0.05)


# ====================================================================== events → feedback
func view_changed_hook(id: String) -> void:
	var fill: OmniLight3D = lights["focus_fill"]
	var e := 0.0 if cam.is_root() else (1.3 if id in ["catalogue", "cat_drawer", "grille", "hatch", "locker9", "ledger", "lens_case", "slides"] else 0.9)
	if id == "cat_section":
		e = 0.45 # the fill sits close to the raised cream cards; more washes the numbers out
	create_tween().tween_property(fill, "light_energy", e, 0.6)
	if id in CAT_VIEWS:
		visuals.apply_state(true) # the picked section rises in the close-up and settles back in the tray view
	visuals.update_visibility(id)
	visuals.receiver_view(id)


func _on_events(ev: Array[String]) -> void:
	var film := false
	for e in ev:
		_feedback(e)
		if e == "film_played":
			film = true
	visuals.apply_state(true)
	hud.call("set_caption", view_caption(cam.current()))
	if film:
		_play_film(ev.has("secret_reel"), ev.has("leyla_echo"))


func _feedback(e: String) -> void:
	var l := logic as ArchiveLogic
	var name := e.get_slice(":", 0)
	var arg := e.get_slice(":", 1) if e.contains(":") else ""
	match name:
		"item_added":
			AudioManager.sfx("item_pickup")
			AudioManager.haptic(15)
			hud.call("message", tr("ui.item_added") % tr(ItemDB.name_key(arg)))
			visuals.receiver_view(cam.current()) # a reel just taken no longer counts on the receiver
		"cat_drawer":
			AudioManager.sfx("drawer_card_slide", -2.0, randf_range(0.95, 1.05))
			if int(arg) >= 0:
				visuals.frame_cat_drawer(int(arg))
				cam.go("cat_drawer")
			elif cam.current() in ["cat_drawer", "cat_section"]:
				cam.go("catalogue")
		"cat_group":
			AudioManager.sfx("card_flick", -2.0)
			visuals.frame_cat_section(int(arg))
			if cam.current() == "cat_section":
				cam.refresh()
			else:
				cam.go("cat_section")
		"cat_card":
			AudioManager.sfx("card_flick", -3.0, 1.1)
			hud.call("message", tr("msg.c2_card_other") % arg)
		"cat_card_leyla":
			AudioManager.sfx("reveal", -2.0, 1.1)
			hud.call("message", tr("msg.c2_card_leyla"))
		"valve":
			AudioManager.sfx("valve_squeak", -3.0, randf_range(0.9, 1.1))
			if not l.state["pressure_ok"]:
				# say what the needles do, so a wrong setting is never silent
				var t: Array = l.state["v_targets"]
				hud.call("caption", tr("msg.c2_gauges") % [
					tr("msg.c2_on_mark" if l.pressure() == int(t[0]) else "msg.c2_off_mark"),
					tr("msg.c2_on_mark" if l.flow() == int(t[1]) else "msg.c2_off_mark")])
		"pressure_ok":
			AudioManager.sfx("compressor_start")
			hud.call("message", tr("msg.c2_pressure_ok"))
			hud.call("caption", tr("cap2.compressor"))
			visuals.compressor_running(true)
		"valves_locked":
			hud.call("message", tr("msg.c2_valves_locked"))
		"punch_empty":
			hud.call("message", tr("msg.c2_punch_empty"))
			AudioManager.ui("ui_error")
		"card_in_punch":
			AudioManager.sfx("card_flick", -2.0, 0.9)
		"punch_key":
			AudioManager.sfx("punch_key", -2.0, randf_range(0.96, 1.04))
		"card_punched":
			visuals.pull("card_punch", "IA_punch_lever", ArchiveVisuals.PUNCH_LEVER_DEG)
			AudioManager.sfx("punch_lever")
			hud.call("message", tr("msg.c2_card_punched"))
		"card_returned":
			AudioManager.sfx("card_flick", -2.0)
			hud.call("message", tr("msg.c2_card_returned"))
		"canister_loaded":
			AudioManager.sfx("canister_thump", -6.0, 1.3)
			hud.call("message", tr("msg.c2_canister_loaded"))
		"dest":
			AudioManager.sfx("collar_click", -3.0, 0.9)
		"tube_no_pressure":
			visuals.pull("tube_station", "IA_send_lever", ArchiveVisuals.LEVER_PULL_DEG)
			hud.call("message", tr("msg.c2_no_pressure"))
			AudioManager.sfx("switch_toggle", -6.0, 0.7)
		"tube_empty":
			visuals.pull("tube_station", "IA_send_lever", ArchiveVisuals.LEVER_PULL_DEG)
			hud.call("message", tr("msg.c2_tube_empty"))
		"tube_sent":
			pass
		"tube_returned_nodest", "tube_returned_notfound", "tube_returned_file":
			_fly_canister(name)
		"locker_locked":
			AudioManager.sfx("locker_rattle", -2.0, randf_range(0.95, 1.05))
			hud.call("message", tr("msg.c2_locker_locked"))
		"locker_opened":
			AudioManager.sfx("locker_open")
			hud.call("message", tr("msg.c2_locker_open"))
			cam.go("locker9")
		"opened":
			match arg:
				"grille":
					AudioManager.sfx("grille_creak")
					hud.call("message", tr("msg.c2_grille"))
				"ledger":
					AudioManager.sfx("ledger_thump")
					hud.call("message", tr("msg.c2_ledger"))
				"hatch":
					AudioManager.sfx("hatch_open")
					hud.call("message", tr("msg.c2_hatch"))
		"speed":
			AudioManager.sfx("collar_click", -2.0, 1.2)
		"tape_loaded":
			AudioManager.sfx("deck_eject", -4.0, 0.8)
		"tape_ejected":
			AudioManager.sfx("deck_eject")
		"deck_empty":
			hud.call("message", tr("msg.c2_deck_empty"))
		"tape_garbled":
			AudioManager.sfx("deck_play")
			visuals.play_tape(arg, false)
			hud.call("message", tr("msg.c2_garbled"))
		"tape_clear":
			AudioManager.sfx("deck_play")
			visuals.play_tape(arg, true)
		"dial":
			pass
		"dial_wrong":
			hud.call("message", tr("msg.c2_dial_wrong"))
		"booth_opened":
			_open_booth()
		"splice":
			AudioManager.sfx("splicer_click", -2.0, randf_range(0.95, 1.05))
		"splice_lift":
			AudioManager.sfx("card_flick", -4.0)
		"splice_wrong":
			AudioManager.sfx("splicer_click", -4.0, 0.7)
			hud.call("message", tr("msg.c2_splice_wrong"))
		"reel_repaired":
			AudioManager.sfx("splicer_click", 0.0, 0.8)
			hud.call("message", tr("msg.c2_reel_repaired"))
		"reel_threaded":
			AudioManager.sfx("lens_insert", -2.0, 0.8)
		"projector_on":
			AudioManager.sfx("film_projector_start")
		"projector_empty":
			hud.call("message", tr("msg.c2_projector_empty"))
		"projector_off":
			AudioManager.sfx("film_projector_stop")
			hud.call("message", tr("msg.c2_projector_off"))
		"frame":
			AudioManager.sfx("splicer_click", -6.0, 1.3)
		"focus":
			AudioManager.sfx("collar_click", -6.0, 1.1)
		"crystal_seated":
			AudioManager.sfx("lens_insert")
		"lens_refused":
			hud.call("message", tr("msg.c2_lens_refused"))
			AudioManager.ui("ui_error")
		"socket_full", "port_full":
			hud.call("message", tr("msg.c2_socket_full"))
			AudioManager.ui("ui_error")
		"socket_emptied", "port_emptied":
			AudioManager.sfx("lens_insert", -2.0, 1.2)
		"recorded":
			AudioManager.sfx("crystal_record")
			SceneManager.flash(Color(0.8, 0.96, 1.0, 0.45), 0.05, 0.9)
			hud.call("message", tr("msg.c2_recorded_sign" if arg == "sign" else "msg.c2_recorded_mark"))
		"slide_drawer":
			AudioManager.sfx("drawer_card_slide", -4.0, 1.2)
			if int(arg) == ArchiveLogic.SLIDE_MARK_DRAWER:
				hud.call("message", tr("msg.c2_slide_drawer"))
		"slide_inserted", "slide_ejected":
			AudioManager.sfx("slide_clunk")
		"slide_rot":
			AudioManager.sfx("collar_click", -3.0)
		"slide_lamp":
			AudioManager.sfx("switch_toggle", -2.0)
		"port_filled":
			AudioManager.sfx("lens_insert")
		"port_blank":
			hud.call("message", tr("msg.c2_port_blank"))
		"collar":
			AudioManager.sfx("collar_click", -2.0, randf_range(0.95, 1.05))
		"vault_unlocked":
			AudioManager.sfx("vault_bolts")
			AudioManager.haptic(140)
			hud.call("message", tr("msg.c2_vault_unlocked"))
			hud.call("caption", tr("cap2.bolts"))
			visuals.bolts_cascade()
		"wheel_locked":
			hud.call("message", tr("msg.c2_wheel_locked"))
			AudioManager.sfx("locker_rattle", -2.0, 0.6)
		"wheel":
			AudioManager.sfx("vault_wheel", -2.0, 0.9 + 0.08 * int(arg))
		"vault_opened":
			_play_finale()
		"echo_released":
			AudioManager.sfx("reveal", 0.0, 1.2)
			hud.call("caption", tr("echo2." + arg), 4.5)
			hud.call("message", tr("msg.c2_echo_count") % (l.state["echoes"] as Array).size())
			visuals.release_echo(arg)
		"all_echoes":
			GameState.unlock_achievement("echoes_of_the_archive")
		"selected":
			visuals.selection_changed(arg)
		"solved":
			AudioManager.sfx("puzzle_solved", -5.0)
		"chapter_complete":
			hud.call("show_chapter_complete")
		"nothing_happens":
			pass


# ====================================================================== sequences
## The canister shoots up the riser, along the ceiling to the stacks and back down into the receive tray.
func _fly_canister(result: String) -> void:
	_cinematic = true
	hud.call("set_busy", true)
	var back_view := cam.current()
	AudioManager.sfx("tube_whoosh")
	hud.call("caption", tr("cap2.whoosh"))
	cam.go("tubes")
	await visuals.canister_flight(result == "tube_returned_file")
	match result:
		"tube_returned_nodest":
			hud.call("message", tr("msg.c2_nodest"))
		"tube_returned_notfound":
			hud.call("message", tr("msg.c2_notfound"))
		"tube_returned_file":
			hud.call("message", tr("msg.c2_file"))
	cam.go(back_view if back_view != "" else "station")
	await get_tree().create_timer(0.7).timeout
	hud.call("set_busy", false)
	_cinematic = false


func _open_booth() -> void:
	_cinematic = true
	hud.call("set_busy", true)
	AudioManager.sfx("booth_unlatch")
	hud.call("message", tr("msg.c2_booth_open"))
	await get_tree().create_timer(0.6).timeout
	cam.go("booth_door")
	visuals.apply_state(true)
	await get_tree().create_timer(1.6).timeout
	hud.call("set_busy", false)
	_cinematic = false
	cam.go("booth")


## The 1979 film plays on the big screen: lights dim, the beam crosses the dusty air, the frames run with
## captions and the last frame (Leyla's sign) holds. Then the secret reel (Ch1 shards = 5) and Leyla's echo
## (leave path) follow.
func _play_film(secret: bool, echo: bool) -> void:
	_cinematic = true
	hud.call("set_busy", true)
	visuals.dim_for_film(true)
	AudioManager.sfx("film_projector_loop", -4.0)
	cam.go("film")
	await get_tree().create_timer(1.2).timeout
	for i in 4:
		visuals.show_film_frame(i)
		hud.call("caption", tr("film.%d" % (i + 1)), 3.0)
		await get_tree().create_timer(3.3).timeout
	visuals.show_film_frame(ArchiveLogic.SIGN_FRAME)
	await get_tree().create_timer(2.2).timeout
	if secret:
		visuals.show_secret_frame(true)
		hud.call("caption", tr("film.secret"), 6.5)
		await get_tree().create_timer(6.8).timeout
		visuals.show_secret_frame(false)
	visuals.apply_state(true)
	if not (logic as ArchiveLogic).is_sharp():
		hud.call("message", tr("msg.c2_blurred"))
	if echo:
		cam.go("booth")
		await get_tree().create_timer(0.9).timeout
		hud.call("caption", tr("cap2.leyla_echo"), 6.0)
		await visuals.leyla_echo_walk()
	visuals.dim_for_film(false)
	cam.go("projector")
	await get_tree().create_timer(0.8).timeout
	hud.call("set_busy", false)
	_cinematic = false


func play_opening_camera() -> void:
	## Called by the HUD intro: the shutter drops behind you, emergency lamps flicker on aisle by aisle.
	cam.go("shutter", true)
	visuals.shutter_drop()
	await get_tree().create_timer(1.8).timeout
	cam.go("hall")


## The HUD intro calls this instead of Chapter 1's door slam.
func intro_impact() -> void:
	AudioManager.sfx("shutter_slam")
	AudioManager.haptic(160)
	visuals.emergency_flicker()


func _play_finale() -> void:
	_ending = true
	logic.select_item("")
	hud.call("set_busy", true)
	AudioManager.sfx("vault_door_open")
	cam.go("vault_mouth")
	await get_tree().create_timer(0.4).timeout
	visuals.open_vault()
	AudioManager.music("music_archive_finale", 2.0)
	await get_tree().create_timer(3.2).timeout
	cam.go("vault_inside")
	await get_tree().create_timer(1.4).timeout
	visuals.vault_reel(true)
	hud.call("caption", tr("cap2.vault_reel"), 7.5)
	await get_tree().create_timer(7.8).timeout
	hud.call("set_busy", false)
	hud.call("show_choice")
