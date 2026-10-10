class_name UndergroundData
extends RefCounted
## Static tables of the Chapter 3 scene (docs/models/ch3.md §1.2, §1.4, §2): what is placed where, which culling
## groups each model and view belongs to, the camera views and their captions. The room and the QA tools read them.
## Culling groups: C Choir, G Gallery, S shaft (the Array below), N Nursery, K Leyla's camp, L lift.

## id -> [model, position, yaw degrees (front +Z = 0), hotspot, collider mode, culling groups]
const LAYOUT := {
	"shell_choir": ["shell_choir", Vector3.ZERO, 0.0, "", "static", "C"],
	"shell_gallery": ["shell_gallery", Vector3.ZERO, 0.0, "", "static", "G"],
	"shell_nursery": ["shell_nursery", Vector3.ZERO, 0.0, "", "static", "N"],
	"shell_lift": ["shell_lift", Vector3.ZERO, 0.0, "", "static", "L"],
	"array_below": ["array_below", Vector3.ZERO, 0.0, "", "none", "S"],
	"freight_lift": ["freight_lift", Vector3(0.0, 0.0, 6.0), 0.0, "lift", "parts", "L"],
	"door_west": ["blast_door", Vector3(-3.70, 0.0, 0.0), 90.0, "door_west", "parts", "GC"],
	"door_east": ["blast_door", Vector3(3.70, 0.0, 0.0), -90.0, "door_east", "parts", "GN"],
	# Choir Hall (groups B, C)
	"transformer_0": ["transformer", Vector3(-12.45, 0.0, -3.0), 90.0, "", "static", "C"],
	"transformer_1": ["transformer", Vector3(-12.45, 0.0, -1.3), 90.0, "", "static", "C"],
	"transformer_2": ["transformer", Vector3(-12.45, 0.0, 0.4), 90.0, "", "static", "C"],
	"choir_rack": ["choir_rack", Vector3(-9.6, 0.0, -4.0), 0.0, "rack", "parts", "C"],
	"tube_bench": ["tube_bench", Vector3(-7.35, 0.0, -4.0), 0.0, "rack", "parts", "C"],
	"strand_office": ["strand_office", Vector3.ZERO, 0.0, "office", "parts", "C"],
	"office_desk": ["office_desk", Vector3(-12.6, 0.0, 2.95), 90.0, "office", "parts", "C"],
	"meter_case": ["meter_case", Vector3(-12.62, 0.76, 3.30), 90.0, "case", "parts", "C"],
	"office_chair": ["chair", Vector3(-11.8, 0.0, 3.55), 60.0, "", "none", "C"],
	"control_desk": ["control_desk", Vector3(-8.0, 0.0, 0.5), 180.0, "desk", "parts", "C"],
	"cabinet_0": ["switch_cabinet", Vector3(-7.4, 0.0, 4.0), 180.0, "cabinet_0", "parts", "C"],
	"cabinet_1": ["switch_cabinet", Vector3(-8.3, 0.0, 4.0), 180.0, "cabinet_1", "parts", "C"],
	"cabinet_2": ["switch_cabinet", Vector3(-9.2, 0.0, 4.0), 180.0, "cabinet_2", "parts", "C"],
	"interlock_plate": ["interlock_plate", Vector3(-8.3, 0.0, 4.0), 180.0, "plate", "parts", "C"],
	"port_a": ["inspection_port", Vector3(-4.5, 0.85, 2.6), -90.0, "port_a", "parts", "C"],
	"port_b": ["inspection_port", Vector3(-12.0, 4.55, 1.9), 110.0, "port_b", "parts", "C"],
	"port_c": ["inspection_port", Vector3(-8.6, 5.15, 1.9), 180.0, "port_c", "parts", "C"], # pitch +60 (PITCH)
	# Nursery (group D)
	"autoclave": ["autoclave", Vector3(8.4, 0.0, -3.5), 0.0, "autoclave", "parts", "N"],
	"dead_0": ["autoclave_dead", Vector3(9.65, 0.0, -3.5), 0.0, "", "static", "N"],
	"dead_1": ["autoclave_dead", Vector3(10.9, 0.0, -3.5), 0.0, "", "static", "N"],
	"dead_2": ["autoclave_dead", Vector3(12.15, 0.0, -3.5), 0.0, "", "static", "N"],
	"seed_library": ["seed_library", Vector3(13.0, 0.0, -0.6), -90.0, "seed_library", "parts", "N"],
	"growth_chart": ["growth_chart", Vector3(7.75, 0.0, -2.45), 90.0, "chart", "parts", "N"],
	"prism_bench": ["prism_bench", Vector3(6.1, 0.0, 0.4), 0.0, "prisms", "parts", "N"],
	"seal_door": ["spectral_seal_door", Vector3(6.1, 0.0, -1.05), 0.0, "seal", "parts", "NK"],
	# Leyla's camp (group E)
	"leyla_camp": ["leyla_camp", Vector3.ZERO, 0.0, "camp", "parts", "K"],
	"field_recorder": ["field_recorder", Vector3(4.95, 0.74, -1.45), 180.0, "recorder", "parts", "K"],
	"oscillograph": ["oscillograph", Vector3(4.97, 0.74, -1.72), 135.0, "recorder", "parts", "K"],
	"crystal_shutter": ["crystal_shutter", Vector3(4.5, 0.0, -2.6), 90.0, "shutter", "parts", "KG"],
	# Gallery (group F)
	"gallery_console": ["gallery_console", Vector3(0.0, 0.0, 2.6), 0.0, "console", "parts", "G"],
	"memorial_wall": ["memorial_wall", Vector3.ZERO, 0.0, "memorial", "parts", "G"],
}
## Set dressing (the Chapter 3 art pass, docs/GAMEPLAY_QA.md): id -> [model, culling groups]. Each is an original model
## built in world coordinates in place (tools/blender/models/ch3_dress_*.py), drawn without colliders or shadows, so nothing in
## it can take a tap or hide a hotspot. J = the camp's own views (camp, shutter, recorder): the Nursery views that look through
## the camp door never draw it, they already sit at the draw-call budget.
const DRESS := {
	"dress_camp": ["ch3_dress_camp", "J"],
	"dress_corridor": ["ch3_dress_corridor", "J"],
	"dress_memorial": ["ch3_dress_memorial", "G"],
}
## CC0 props (docs/CC0_PROPS.md, Poly Haven) placed as dressing: id -> [glb, position, yaw degrees, culling groups]. They are
## merged into one mesh by ModelUtil.merge_static. The gas mask's origin is its hook point.
const DRESS_CC0 := {
	"dress_gas_mask": ["res://assets/models/cc0/old_gas_mask/old_gas_mask.glb", Vector3(4.585, 1.80, -3.40), 90.0, "J"],
	"dress_compass": ["res://assets/models/cc0/seadogs_compass/seadogs_compass.glb", Vector3(6.09, 0.42, -2.93), 25.0, "J"],
}
## Extra rotation about the model's own X after the yaw (degrees): port C looks down from the gantry.
const PITCH := {"port_c": 60.0}
## Parts whose hotspot differs from their model's: model -> {part -> hotspot}.
const PART_HOTSPOT := {
	"shell_gallery": {"IA_glass_floor": "glass_floor", "IA_tunnel_shutter": "tunnel"},
	"shell_lift": {"IA_passage_w": "passage_w", "IA_passage_e": "passage_e"},
	"strand_office": {"IA_office_door": "office_door", "IA_office_lock": "office_door"},
}
## Parts drawn with other groups than their model (§1.2): model -> {part -> groups}. The room moves them out of
## the model's subtree so they can stay visible while the rest of the model is culled.
const PART_CULL := {"shell_nursery": {"camp_walls": "NK"}}
## The model that owns each group's walls, ceilings and trim: these never cast shadows (§1.5).
const NO_SHADOW_PREFIX := ["choir_walls", "choir_ceiling", "choir_trim", "gallery_drum", "gallery_ceiling",
	"nursery_walls", "nursery_ceiling", "nursery_pipes", "camp_walls", "lobby_walls", "lobby_ceiling", "lift_shaft",
	"cavern", "shaft_throat", "intro_shaft", "lamp_glass", "IA_glass_floor", "glass_rim", "catwalk", "gantry"]

## Root ids where the room starts (and Back returns to) per zone.
const ZONE_ROOT := {"choir": "choir", "gallery": "gallery", "nursery": "nursery"}

## view -> [position, target, fov, root?, groups drawn, state key that adds groups ("" = none), groups it adds]
## Views that frame a lobby passage mouth (choir_s, switch_room, desk, nursery_w) also draw L: with the lobby culled the
## opening showed the fogged background as a flat teal slab (rendered QA, 2026-10-10).
const VIEWS := {
	"lift_w": [Vector3(0.5, 1.6, 6.4), Vector3(-1.1, 1.35, 6.0), 62.0, true, "L", "", ""],
	"lift_e": [Vector3(-0.5, 1.6, 6.4), Vector3(1.1, 1.35, 6.0), 62.0, true, "L", "", ""],
	# Choir Hall
	"choir": [Vector3(-5.4, 1.65, 3.3), Vector3(-9.6, 1.5, -2.0), 62.0, true, "CL", "", ""],
	"choir_s": [Vector3(-5.6, 1.65, -2.9), Vector3(-10.6, 1.3, 2.6), 62.0, true, "CL", "", ""],
	"office_door": [Vector3(-9.0, 1.5, 2.65), Vector3(-10.2, 1.1, 2.75), 50.0, false, "C", "", ""],
	"office": [Vector3(-10.5, 1.6, 2.35), Vector3(-12.55, 0.85, 2.95), 56.0, false, "C", "", ""],
	"ecg_lamp": [Vector3(-12.0, 1.3, 2.3), Vector3(-12.62, 1.06, 2.45), 40.0, false, "C", "", ""],
	"meter_case": [Vector3(-12.05, 1.25, 3.3), Vector3(-12.6, 0.84, 3.3), 40.0, false, "C", "", ""],
	"switch_room": [Vector3(-8.3, 1.65, 1.75), Vector3(-8.3, 1.4, 4.0), 58.0, false, "CL", "", ""],
	"cabinet_0": [Vector3(-7.4, 1.45, 2.75), Vector3(-7.4, 1.3, 3.55), 50.0, false, "C", "", ""],
	"cabinet_1": [Vector3(-8.3, 1.45, 2.75), Vector3(-8.3, 1.3, 3.55), 50.0, false, "C", "", ""],
	"cabinet_2": [Vector3(-9.2, 1.45, 2.75), Vector3(-9.2, 1.3, 3.55), 50.0, false, "C", "", ""],
	"interlock_plate": [Vector3(-8.3, 2.05, 2.6), Vector3(-8.3, 2.3, 3.97), 40.0, false, "C", "", ""],
	"desk": [Vector3(-7.8, 1.85, -1.6), Vector3(-7.75, 1.2, 0.35), 60.0, false, "CL", "", ""],
	# hud-check at 19.5:9 (2026-10-10): the tube bench's three places sat 0.4 to 3 mm from the bottom edge (its table
	# top is below the eye line) and the master hammer 5 mm from the right edge. `rack` stands 0.9 m to the east and
	# looks level, so the whole rack and the bench places are on screen (bench places x 1600..1900, y 790..820 of 2340 x 1080);
	# `rack_close` moves 0.2 m east for the hammer.
	"rack": [Vector3(-8.7, 1.8, -1.0), Vector3(-8.7, 1.62, -3.65), 58.0, false, "C", "", ""],
	"rack_close": [Vector3(-9.4, 1.75, -2.4), Vector3(-9.4, 1.75, -3.8), 54.0, false, "C", "", ""],
	# hud-check at 4:3 (tablet10): the master hammer on the rack's right post, 0.83 m west of the bench's middle, sat 4.3 mm
	# from the left edge. The camera stands 0.2 m further west; the three places (x -7.9 .. -6.8) stay in view.
	"bench": [Vector3(-7.55, 1.6, -2.35), Vector3(-7.55, 0.9, -3.7), 50.0, false, "C", "", ""],
	"port_a": [Vector3(-4.8, 0.95, 2.5), Vector3(-7.4, 1.35, 0.5), 36.0, false, "C", "", ""],
	"port_b": [Vector3(-11.75, 4.65, 1.75), Vector3(-8.2, 1.15, 0.45), 34.0, false, "C", "", ""],
	"port_c": [Vector3(-8.6, 4.95, 1.8), Vector3(-8.3, 1.2, 0.4), 40.0, false, "C", "", ""],
	"port_a_mem": [Vector3(9.1, 1.6, 0.4), Vector3(10.3, 1.0, -2.45), 50.0, false, "N", "", ""],
	"port_b_mem": [Vector3(-10.0, 1.6, -0.9), Vector3(-11.45, 0.9, -1.3), 48.0, false, "C", "", ""],
	"port_c_mem": [Vector3(1.2, 1.65, 2.4), Vector3(-2.05, 1.35, -0.4), 50.0, false, "GS", "", ""],
	"blast_west_hall": [Vector3(-6.5, 1.6, 0.0), Vector3(-4.5, 1.25, 0.0), 56.0, false, "C", "door_west_open", "GS"],
	# Resonance Gallery
	"gallery": [Vector3(-2.7, 1.65, 2.2), Vector3(1.8, 1.0, -2.2), 62.0, true, "GS", "", ""],
	"gallery_w": [Vector3(2.7, 1.65, 2.2), Vector3(-1.8, 1.0, -2.2), 62.0, true, "GS", "", ""],
	"glass_floor": [Vector3(0.0, 1.55, 1.1), Vector3(0.0, -30.0, -0.6), 32.0, false, "GS", "", ""],
	"console": [Vector3(0.0, 1.55, 3.45), Vector3(0.0, 1.0, 2.55), 52.0, false, "GS", "", ""],
	"scope": [Vector3(0.0, 1.42, 3.0), Vector3(0.0, 1.25, 2.53), 34.0, false, "G", "", ""],
	"strand_plate": [Vector3(-0.42, 1.3, 3.1), Vector3(-0.42, 0.97, 2.76), 34.0, false, "G", "", ""],
	"cradle": [Vector3(0.0, 1.35, 3.15), Vector3(0.0, 1.0, 2.74), 38.0, false, "G", "", ""],
	# hud-check at 4:3: socket 42 (x 1.78) sat 1.7 mm from the right edge. 0.25 m east and 2 degrees wider keep the whole
	# arc on a phone and put the socket 17 mm inside the edge of a tablet.
	"memorial": [Vector3(0.25, 1.6, -1.2), Vector3(0.25, 1.45, -3.92), 62.0, false, "G", "", ""],
	"socket_42": [Vector3(1.35, 1.4, -2.6), Vector3(1.78, 1.15, -3.49), 40.0, false, "G", "", ""],
	"drum_west": [Vector3(-2.55, 1.45, 1.16), Vector3(-3.55, 1.3, 1.16), 46.0, false, "G", "", ""],
	"drum_east": [Vector3(2.55, 1.45, -1.16), Vector3(3.55, 1.3, -1.16), 46.0, false, "G", "", ""],
	"blast_west": [Vector3(-1.95, 1.6, 0.7), Vector3(-3.7, 1.3, 0.0), 56.0, false, "GS", "door_west_open", "C"],
	"blast_east": [Vector3(1.95, 1.6, -0.7), Vector3(3.7, 1.3, 0.0), 56.0, false, "GS", "door_east_open", "N"],
	"finale": [Vector3(0.0, 1.85, 3.75), Vector3(0.0, 1.15, 0.4), 66.0, false, "GS", "", ""],
	# Nursery and Leyla's camp
	"nursery": [Vector3(5.7, 1.65, 3.3), Vector3(10.6, 1.3, -2.6), 62.0, true, "NL", "camp_open", "K"],
	"nursery_w": [Vector3(12.2, 1.65, 2.9), Vector3(6.4, 1.2, -0.8), 62.0, true, "NL", "camp_open", "K"],
	"autoclave": [Vector3(8.4, 1.55, -1.55), Vector3(8.4, 1.15, -2.95), 54.0, false, "N", "", ""],
	"cam_drum": [Vector3(8.7, 1.35, -2.25), Vector3(8.7, 1.05, -2.88), 40.0, false, "N", "", ""],
	"growth_log": [Vector3(8.7, 1.55, -2.55), Vector3(8.7, 1.5, -3.1), 38.0, false, "N", "", ""],
	"chart": [Vector3(9.1, 1.6, -2.3), Vector3(7.8, 1.6, -2.45), 44.0, false, "N", "", ""],
	"seed_library": [Vector3(11.25, 1.45, -0.6), Vector3(12.55, 1.24, -0.6), 50.0, false, "N", "", ""],
	"seed_drawer": [Vector3(11.85, 1.6, -0.6), Vector3(12.25, 1.2, -0.6), 42.0, false, "N", "", ""], # framed per drawer
	# hud-check at 19.5:9: the four nudge buttons on the apron sat 2.6 mm from the bottom edge. Higher and further back,
	# looking down at the bench: buttons, prisms and the seal's three receptors all sit between the title and the banner.
	"prisms": [Vector3(6.1, 1.6, 2.1), Vector3(6.1, 0.75, 0.0), 56.0, false, "N", "camp_open", "K"],
	"seal": [Vector3(6.1, 1.3, -0.3), Vector3(6.1, 1.15, -0.97), 44.0, false, "N", "camp_open", "K"],
	"camp": [Vector3(7.25, 1.6, -1.5), Vector3(4.9, 1.2, -2.8), 62.0, false, "K", "shutter_open", "GS"],
	"shutter": [Vector3(6.55, 1.55, -2.6), Vector3(4.66, 1.6, -2.6), 50.0, false, "K", "shutter_open", "GS"],
	# from the north-east and higher than the first framing: the scope's screen faces that way, and its top no longer
	# hides the recorder's two ivory keys (their ◀◀ / ▶ were foreshortened to slivers from 25 degrees)
	"recorder": [Vector3(5.3, 1.38, -2.2), Vector3(5.0, 0.84, -1.68), 34.0, false, "K", "camp_open", "N"],
	# cinematic only
	"hall_start": [Vector3(-5.8, 2.2, 2.9), Vector3(-10.0, 2.4, -2.0), 64.0, false, "C", "", ""],
	"grow": [Vector3(8.4, 1.3, -2.3), Vector3(8.4, 1.2, -3.1), 40.0, false, "N", "", ""],
	"array_rise": [Vector3(0.0, 1.7, 3.6), Vector3(0.0, 2.6, -0.5), 66.0, false, "GS", "", ""],
	"secret": [Vector3(0.6, 1.5, -1.8), Vector3(1.7, 0.9, -3.3), 52.0, false, "G", "", ""],
}

## The zone a view stands in (for Back, music and the room tone).
static func zone_of(view: String) -> String:
	if view.begins_with("lift"):
		return "lift"
	if view in ["port_a_mem", "port_b_mem", "port_c_mem"]:
		return "choir" # a memory seen through a Choir port
	var v: Array = VIEWS.get(view, [])
	if v.is_empty():
		return ""
	match str(v[4]).substr(0, 1):
		"C":
			return "choir"
		"G":
			return "gallery"
		"N", "K":
			return "nursery"
	return ""


const HOTSPOT_VIEW := {
	"rack": "rack", "office_door": "office_door", "office": "office", "case": "meter_case", "desk": "desk",
	"port_a": "port_a", "port_b": "port_b", "port_c": "port_c", "glass_floor": "glass_floor", "console": "console",
	"memorial": "memorial", "autoclave": "autoclave", "seed_library": "seed_library", "chart": "chart",
	"prisms": "prisms", "seal": "seal", "camp": "camp", "recorder": "recorder", "shutter": "shutter",
}
const DEEPER := {
	"rack": ["rack_close", "bench"], "office": ["ecg_lamp", "meter_case"], "console": ["scope", "strand_plate", "cradle"],
	"memorial": ["socket_42", "secret"], "blast_west": ["drum_west"], "blast_east": ["drum_east"],
	"autoclave": ["cam_drum", "growth_log", "grow"], "seed_library": ["seed_drawer"],
	"port_a": ["port_a_mem"], "port_b": ["port_b_mem"], "port_c": ["port_c_mem"], "camp": ["recorder", "shutter"],
	"switch_room": ["cabinet_0", "cabinet_1", "cabinet_2", "interlock_plate"],
}
const CAPTION := {
	"lift_w": "obj3.lift", "lift_e": "obj3.lift", "choir": "obj3.choir_hall", "choir_s": "obj3.choir_hall",
	"hall_start": "obj3.choir_hall", "office_door": "obj3.office", "office": "obj3.office", "ecg_lamp": "obj3.office",
	"meter_case": "obj3.office", "switch_room": "obj3.switch_room", "cabinet_0": "obj3.switch_room",
	"cabinet_1": "obj3.switch_room", "cabinet_2": "obj3.switch_room", "interlock_plate": "obj3.plate",
	"desk": "obj3.desk", "rack": "obj3.choir", "rack_close": "obj3.choir", "bench": "obj3.choir",
	"port_a": "obj3.port", "port_b": "obj3.port", "port_c": "obj3.port", "port_a_mem": "obj3.port",
	"port_b_mem": "obj3.port", "port_c_mem": "obj3.port", "blast_west_hall": "obj3.blast_door",
	"gallery": "obj3.gallery", "gallery_w": "obj3.gallery", "glass_floor": "obj3.glass_floor",
	"console": "obj3.console", "scope": "obj3.console", "strand_plate": "obj3.console", "cradle": "obj3.console",
	"memorial": "obj3.memorial", "socket_42": "obj3.memorial", "secret": "obj3.memorial",
	"drum_west": "obj3.blast_door", "drum_east": "obj3.blast_door", "blast_west": "obj3.blast_door",
	"blast_east": "obj3.blast_door", "finale": "obj3.gallery", "array_rise": "obj3.gallery",
	"nursery": "obj3.nursery", "nursery_w": "obj3.nursery", "autoclave": "obj3.autoclave", "cam_drum": "obj3.autoclave",
	"growth_log": "obj3.autoclave", "grow": "obj3.autoclave", "chart": "obj3.chart", "seed_library": "obj3.library",
	"seed_drawer": "obj3.library", "prisms": "obj3.prisms", "seal": "obj3.seal", "camp": "obj3.camp",
	"recorder": "obj3.camp", "shutter": "obj3.shutter",
}

## Portal cards (§1.4): empty -> [owner model, groups that draw it, state key of the opening, group seen through it,
## opening size, tint of the far zone].
const PORTALS := {
	"portal_w_c": ["shell_choir", "C", "door_west_open", "G", Vector2(1.6, 2.4), Color("6fb6c4")],
	"portal_w_g": ["shell_gallery", "G", "door_west_open", "C", Vector2(1.6, 2.4), Color("b88a52")],
	"portal_e_g": ["shell_gallery", "G", "door_east_open", "N", Vector2(1.6, 2.4), Color("b9c9cf")],
	"portal_e_n": ["shell_nursery", "N", "door_east_open", "G", Vector2(1.6, 2.4), Color("6fb6c4")],
	"portal_shutter_g": ["shell_gallery", "G", "shutter_open", "K", Vector2(1.1, 1.8), Color("c99a5c")],
	"portal_shutter_k": ["crystal_shutter", "K", "shutter_open", "G", Vector2(1.1, 1.8), Color("6fb6c4")],
}
## Where a portal empty sits if its model does not carry it (world position, yaw of its +Z).
const PORTAL_FALLBACK := {
	"portal_w_c": [Vector3(-3.75, 1.2, 0.0), 90.0], "portal_w_g": [Vector3(-4.45, 1.2, 0.0), -90.0],
	"portal_e_g": [Vector3(4.45, 1.2, 0.0), 90.0], "portal_e_n": [Vector3(3.75, 1.2, 0.0), -90.0],
	"portal_shutter_g": [Vector3(4.40, 1.2, -2.6), 90.0], "portal_shutter_k": [Vector3(2.95, 1.2, -2.6), -90.0],
}

## Echo mounts when their model is not built yet (docs/models/ch3.md §3–§10, ch3_h.md): world position, yaw.
const MOUNT_FALLBACK := {
	"welder": [Vector3(-11.52, 0.0, -1.20), -90.0], # transformer_1 echo_mount
	"tech_a": [Vector3(9.65, 0.0, -2.88), 180.0], # dead_0 echo_mount
	"tech_b": [Vector3(10.9, 0.0, -2.88), 180.0], # dead_1 echo_mount
	"strand_rail": [Vector3(-2.05, 0.0, -0.40), 79.0],
	"strand_offer": [Vector3(-2.30, 0.0, 1.00), 40.0],
	"leyla_offer": [Vector3(2.30, 0.0, 1.00), -40.0],
	"leyla_kneel": [Vector3(1.49, 0.0, -3.02), 153.0],
}
## The echo figures: id -> [model, pose shown, culling group]
const ECHOES := {
	"welder": ["echo_welder", "pose_weld", "C"],
	"tech_a": ["echo_technicians", "tech_a", "N"],
	"tech_b": ["echo_technicians", "tech_b", "N"],
	"strand_rail": ["echo_strand_rail", "pose_rail", "G"],
}

## Fixed points (§1.3) used when a model's own part is missing.
const RECEPTOR_X: Array[float] = [5.8, 6.1, 6.4]
const RECEPTOR_Y := 1.15
const RECEPTOR_Z := -0.97
const SOCKET_42 := Vector3(1.78, 1.15, -3.49)
