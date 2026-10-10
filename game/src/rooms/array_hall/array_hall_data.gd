class_name ArrayHallData
extends RefCounted
## Static tables of the Chapter 4 scene (docs/models/ch4.md §1.3, §2 and the measured pages ch4_a..ch4_h): what is placed
## where, which culling groups each model and view belongs to, the camera views and their captions. The room, the visuals
## and the QA tools read them.
## Culling groups: H hall shell, B bridge (desk, wheels, bay, lift), P Panel 0, K catwalk, R Array floor (rails, rings,
## towers, beams), I island (cage, glass tower, Core), S Sun apse, T Strand's booth, W watch room, E the kept echoes and
## the replay crowd.

## id -> [model, position, yaw degrees (front +Z = 0), hotspot, collider mode, culling groups]
const LAYOUT := {
	"shell_hall": ["shell_hall", Vector3.ZERO, 0.0, "", "static", "H"],
	"shell_lift4": ["shell_lift4", Vector3.ZERO, 0.0, "", "static", "BH"],
	"freight_lift": ["freight_lift", Vector3(0.0, 0.0, 16.4), 0.0, "lift", "parts", "B"],
	"bridge": ["bridge", Vector3.ZERO, 0.0, "bridge", "static", "B"],
	"catwalk": ["catwalk", Vector3.ZERO, 0.0, "catwalk", "parts", "K"],
	"master_desk": ["master_desk", Vector3(0.0, 2.5, 13.15), 0.0, "desk", "parts", "B"],
	"master_lever": ["master_lever", Vector3(1.28, 3.45, 13.15), 0.0, "desk", "parts", "B"],
	"keeper_knob": ["keeper_knob", Vector3(-1.12, 3.45, 13.15), 0.0, "desk", "parts", "B"],
	"handwheel_1": ["handwheel", Vector3(-3.6, 2.5, 12.45), 0.0, "wheels", "parts", "B"],
	"handwheel_2": ["handwheel", Vector3(-2.2, 2.5, 12.45), 0.0, "wheels", "parts", "B"],
	"handwheel_3": ["handwheel", Vector3(2.2, 2.5, 12.45), 0.0, "wheels", "parts", "B"],
	"handwheel_4": ["handwheel", Vector3(3.6, 2.5, 12.45), 0.0, "wheels", "parts", "B"],
	"panel0": ["panel0", Vector3(0.0, 0.0, 14.0), 180.0, "panel0", "parts", "P"],
	# the Array floor
	"ring_rails": ["ring_rails", Vector3.ZERO, 0.0, "", "none", "R"],
	"array_rings": ["array_rings", Vector3.ZERO, 0.0, "", "none", "R"],
	# the island (built in place, island frame at (0, 2.5, 0))
	"cage": ["cage", Vector3(0.0, 2.5, 0.0), 0.0, "island", "parts", "I"],
	"glass_tower": ["glass_tower", Vector3(0.0, 2.5, 0.0), 0.0, "island", "parts", "I"],
	"core_crystal": ["core_crystal", Vector3(0.0, 2.5, 0.0), 0.0, "core", "parts", "I"],
	"cradle": ["cradle", Vector3(0.0, 2.5, 0.0), 0.0, "core", "parts", "I"],
	"heart_drawer": ["heart_drawer", Vector3(0.0, 2.5, 0.0), 0.0, "drawer", "parts", "I"],
	# the Sun apse
	"sun_lamp": ["sun_lamp", Vector3(-13.0, 1.8, 0.0), 0.0, "apse", "parts", "S"],
	"sun_iris": ["sun_iris", Vector3(-11.8, 1.8, 0.0), 90.0, "iris", "parts", "S"],
	"sun_pedestal": ["sun_pedestal", Vector3(-12.0, 0.0, 2.4), 90.0, "sun_pedestal", "parts", "S"],
	# Strand's booth (the desk, box and orrery hang on the previous model's mounts: MOUNTED)
	"booth": ["booth", Vector3(0.0, 0.0, -13.0), 0.0, "booth", "parts", "T"],
	# the watch room (fixtures on the room's mounts)
	"watch_room": ["watch_room", Vector3(12.7, 0.0, 0.0), -90.0, "watch", "parts", "W"],
}
## id -> [model, parent model id, mount empty, hotspot]: models spawned on a mount of another model.
const MOUNTED := {
	"booth_desk": ["booth_desk", "booth", "desk_mount", "gear_box"],
	"strand_box4": ["strand_box4", "booth_desk", "box_mount", "gear_box"],
	"orrery": ["orrery", "strand_box4", "orrery_mount", "gear_box"],
	"roll_board": ["roll_board", "watch_room", "board_mount", "board"],
	"lockers4": ["lockers4", "watch_room", "lockers_mount", "locker"],
	"post_station4": ["post_station4", "watch_room", "post_mount", "post_station"],
}
## Parts whose hotspot differs from their model's: model -> {part -> hotspot}.
const PART_HOTSPOT := {
	"shell_lift4": {"leyla_chalk": "chalk_lift"},
	"bridge": {"catwalk_gate": "catwalk", "bridge_paint": "pier"},
	"panel0": {"leyla_chalk": "chalk_panel"},
	"cage": {"IA_gate_1": "gate_1", "IA_gate_2": "gate_2", "IA_gate_3": "gate_3", "IA_gate_4": "gate_4"},
	"glass_tower": {"IA_collar_digit_1": "collar", "IA_collar_digit_2": "collar", "IA_collar_digit_3": "collar",
		"IA_collar_digit_4": "collar"},
	"booth": {"IA_booth_gate": "booth_gate"},
	"watch_room": {"IA_watch_gate": "watch_gate"},
	"master_desk": {"chart_paper": "desk"},
}
## Models whose own mesh takes no tap: the booth's and the watch room's glass must let a tap reach the box, the lockers
## and the post station behind it (they get a few opaque tap strips instead, see ArrayHallRoom._enclosure_taps), and the
## cage lattice must not hide the Core. model -> [mesh names].
const NO_COLLIDER := {"booth": ["booth"], "watch_room": ["watch_room"], "cage": ["cage"]}
## The model that owns each group's walls, ceilings and trim: these never cast shadows.
const NO_SHADOW_PREFIX := ["hall_", "bay_", "oculus_shutter", "bridge_deck", "bridge_frame", "bridge_rail", "bridge_paint",
	"catwalk_", "ring_rails", "booth", "watch_room", "cage", "sun_lamp", "iris_frame", "lamp_proto", "tag_proto"]

## Root ids where Back returns to.
const MAIN_ROOT := "bridge"

## The 41 figures of the replay: ring radius and count (docs/models/ch4.md §9).
const CROWD_RINGS: Array = [[12.6, 14], [9.5, 11], [7.5, 8], [5.5, 5], [3.8, 3]]
## Arcs (azimuth degrees, clockwise from north) kept free of figures: the bay and the bridge (south), the Sun apse
## (west), the watch room (east) and the booth (north).
const CROWD_FREE_ARCS: Array = [[180.0, 38.0], [270.0, 15.0], [90.0, 17.0], [0.0, 13.0]]

## view -> [position, target, fov, root?, groups drawn, state key that adds groups ("" = none), groups it adds]
## Cameras above y 4.4 on the island (docs/models/ch4_d.md: the collar's digit housing stands between a lower camera and
## the cradle, the drawer and the Core's lower half); the hatch camera at z + 0.35 (ch4_c.md); the gear_box camera at
## (0, 3.6, -11.2) (the contract's stands on the booth's front glass, ch4_f.md).
const VIEWS := {
	# the lift bay and the bridge
	"lift_in": [Vector3(-0.15, 1.55, 17.15), Vector3(1.1, 1.3, 16.3), 70.0, false, "Bl", "", ""],
	"lift": [Vector3(1.55, 1.6, 16.5), Vector3(5.0, 2.2, 12.5), 64.0, true, "HBRIl", "", ""],
	"lift_chalk": [Vector3(-2.9, 1.55, 15.4), Vector3(-3.0, 1.5, 18.18), 46.0, false, "Bl", "", ""],
	"bay_hero": [Vector3(0.0, 1.7, 7.5), Vector3(0.0, 2.6, 15.5), 60.0, false, "HBRl", "", ""],
	"bridge_up": [Vector3(0.0, 4.4, 14.6), Vector3(0.0, 8.8, 0.0), 74.0, false, "HBKRIS", "", ""],
	"bridge": [Vector3(0.0, 4.4, 14.6), Vector3(0.0, 3.4, 0.0), 66.0, true, "HBKRISTW", "", ""],
	"desk": [Vector3(0.0, 4.35, 14.5), Vector3(0.0, 3.5, 13.1), 58.0, false, "B", "", ""],
	"chronometer": [Vector3(0.0, 4.5, 14.3), Vector3(0.0, 3.75, 13.2), 40.0, false, "B", "", ""],
	"handwheels": [Vector3(0.0, 4.9, 15.2), Vector3(0.0, 3.3, 9.0), 84.0, false, "HBKR", "", ""],
	"panel0": [Vector3(0.0, 1.2, 12.3), Vector3(0.0, 1.15, 14.0), 62.0, false, "PB", "", ""],
	# the catwalk and the hatches
	"catwalk": [Vector3(0.0, 3.9, 11.6), Vector3(0.0, 3.0, 3.0), 64.0, true, "HKRI", "", ""],
	"hatch_1": [Vector3(0.0, 3.35, 10.85), Vector3(0.0, 0.65, 10.45), 50.0, false, "KR", "", ""],
	"hatch_2": [Vector3(0.0, 3.35, 8.85), Vector3(0.0, 0.65, 8.45), 50.0, false, "KR", "", ""],
	"hatch_3": [Vector3(0.0, 3.35, 6.85), Vector3(0.0, 0.65, 6.45), 50.0, false, "KR", "", ""],
	"hatch_4": [Vector3(0.0, 3.35, 4.85), Vector3(0.0, 0.65, 4.45), 50.0, false, "KR", "", ""],
	# the island: cage, collar, Core, cradle and drawer
	"island": [Vector3(0.0, 5.0, 6.4), Vector3(0.0, 3.5, 0.0), 62.0, true, "HKRI", "", ""],
	"gate_1": [Vector3(0.40, 3.9, 4.18), Vector3(0.40, 3.62, 2.38), 46.0, false, "RI", "", ""],
	"gate_2": [Vector3(-4.18, 3.9, 0.40), Vector3(-2.38, 3.62, 0.40), 46.0, false, "RI", "", ""],
	"gate_3": [Vector3(-0.40, 3.9, -4.18), Vector3(-0.40, 3.62, -2.38), 46.0, false, "RI", "", ""],
	"gate_4": [Vector3(4.18, 3.9, -0.40), Vector3(2.38, 3.62, -0.40), 46.0, false, "RI", "", ""],
	"collar": [Vector3(0.0, 3.85, 2.7), Vector3(0.0, 3.7, 1.22), 40.0, false, "I", "", ""],
	"core": [Vector3(0.0, 4.9, 2.7), Vector3(0.0, 3.95, 0.3), 52.0, false, "I", "", ""],
	"drawer": [Vector3(0.5, 3.75, 2.4), Vector3(0.0, 3.15, 0.7), 46.0, false, "I", "", ""],
	# the Sun apse
	"apse": [Vector3(-5.5, 1.7, 0.3), Vector3(-12.5, 1.8, 0.0), 62.0, true, "HSR", "", ""],
	"sun_pedestal": [Vector3(-10.2, 1.5, 2.8), Vector3(-12.0, 1.1, 2.4), 46.0, false, "HS", "", ""],
	"iris": [Vector3(-8.8, 1.8, 0.0), Vector3(-11.8, 1.8, 0.0), 40.0, false, "HS", "", ""],
	# Strand's booth
	"booth": [Vector3(0.0, 1.7, -6.5), Vector3(0.0, 3.2, -13.0), 62.0, true, "HTt", "", ""],
	"booth_gate": [Vector3(-2.2, 1.55, -8.9), Vector3(0.4, 1.25, -11.3), 48.0, false, "HTt", "", ""],
	"gear_box": [Vector3(0.0, 3.6, -11.2), Vector3(0.0, 2.95, -13.4), 44.0, false, "Tt", "", ""],
	# the watch room
	"watch": [Vector3(6.5, 1.7, 0.0), Vector3(12.7, 1.5, 0.0), 64.0, true, "HWw", "", ""],
	"locker_17": [Vector3(9.8, 1.6, 2.0), Vector3(13.45, 0.6, 1.64), 40.0, false, "Ww", "", ""],
	"post_station": [Vector3(9.8, 1.5, -1.5), Vector3(13.5, 1.0, -2.95), 44.0, false, "Ww", "", ""],
	# cinematic only
	"rise_core": [Vector3(0.0, 2.9, 5.2), Vector3(0.0, 6.2, 0.0), 70.0, false, "HKRI", "", ""],
	"rise_up": [Vector3(0.0, 4.4, 2.4), Vector3(0.0, 12.4, 0.0), 72.0, false, "HKRI", "", ""],
	"finale": [Vector3(0.0, 4.9, 2.9), Vector3(0.0, 4.0, 0.2), 56.0, false, "HKRI", "", ""],
}

## The zone a view stands in (for the room tone and the mood).
static func zone_of(view: String) -> String:
	match view:
		"lift_in", "lift", "lift_chalk", "bay_hero":
			return "lift"
		"bridge_up":
			return "bridge"
		"panel0":
			return "panel"
		"apse", "sun_pedestal", "iris":
			return "apse"
		"booth", "booth_gate", "gear_box":
			return "booth"
		"watch", "locker_17", "post_station":
			return "watch"
		"island", "collar", "core", "drawer", "gate_1", "gate_2", "gate_3", "gate_4", "rise_core", "rise_up", "finale":
			return "island"
		"catwalk", "hatch_1", "hatch_2", "hatch_3", "hatch_4":
			return "catwalk"
	return "bridge"


## hotspot -> the view where it is operated.
const HOTSPOT_VIEW := {
	"lift": "lift", "bridge": "bridge", "desk": "desk", "wheels": "handwheels", "panel0": "panel0", "chalk_lift": "lift_chalk", "chalk_panel": "",
	"catwalk": "catwalk", "island": "island", "gate_1": "gate_1", "gate_2": "gate_2", "gate_3": "gate_3",
	"gate_4": "gate_4", "collar": "collar", "core": "core", "drawer": "drawer", "apse": "apse", "iris": "iris",
	"sun_pedestal": "sun_pedestal", "booth": "booth", "booth_gate": "booth_gate", "gear_box": "gear_box",
	"watch": "watch", "watch_gate": "watch", "pier": "panel0", "board": "watch", "locker": "locker_17", "post_station": "post_station",
	"tower_1": "hatch_1", "tower_2": "hatch_2", "tower_3": "hatch_3", "tower_4": "hatch_4",
}
## view -> views "inside" it, from which the same hotspot is still directly operable.
const DEEPER := {
	"desk": ["chronometer"],
	"catwalk": ["hatch_1", "hatch_2", "hatch_3", "hatch_4"],
	"island": ["collar", "core", "drawer"],
	"booth": ["booth_gate"],
}
const CAPTION := {
	"bridge_up": "obj4.oculus", "lift_in": "obj4.lift", "lift": "obj4.lift", "lift_chalk": "obj4.lift", "bay_hero": "obj4.lift",
	"bridge": "obj4.bridge", "desk": "obj4.desk", "chronometer": "obj4.chronometer", "handwheels": "obj4.handwheels",
	"panel0": "obj4.panel0", "catwalk": "obj4.catwalk", "hatch_1": "obj4.hatch_1", "hatch_2": "obj4.hatch_2",
	"hatch_3": "obj4.hatch_3", "hatch_4": "obj4.hatch_4", "island": "obj4.island", "gate_1": "obj4.gate_1",
	"gate_2": "obj4.gate_2", "gate_3": "obj4.gate_3", "gate_4": "obj4.gate_4", "collar": "obj4.collar",
	"core": "obj4.core", "drawer": "obj4.core", "apse": "obj4.apse", "sun_pedestal": "obj4.sun_pedestal",
	"iris": "obj4.iris", "booth": "obj4.booth", "booth_gate": "obj4.booth", "gear_box": "obj4.gear_box",
	"watch": "obj4.watch", "locker_17": "obj4.locker", "post_station": "obj4.post_station",
	"rise_core": "obj4.oculus", "rise_up": "obj4.oculus", "finale": "obj4.core",
}

## Echo mounts: id -> [model with the mount empty, empty name, culling group, fallback position, fallback yaw degrees].
const ECHO_MOUNTS := {
	"tech_panel": ["panel0", "echo_mount_tech_panel", "P", Vector3(0.8, 0.0, 13.0), 0.0],
	"tech_wheels_a": ["bridge", "echo_mount_wheels_1", "B", Vector3(-2.9, 2.5, 13.3), 180.0],
	"tech_wheels_b": ["bridge", "echo_mount_wheels_2", "B", Vector3(2.9, 2.5, 13.3), 180.0],
	"clerk_post": ["watch_room", "echo_mount_clerk_post", "W", Vector3(13.55, 0.03, -2.95), 90.0],
	"leyla_lift": ["shell_lift4", "echo_mount_leyla_lift", "B", Vector3(-3.4, 0.0, 17.0), 0.0],
	"strand_desk": ["master_desk", "echo_mount_strand", "B", Vector3(1.12, 2.5, 13.93), 180.0],
}
## The kept echoes of the logic: id -> [group, [figures], candidate models in the order of preference [[model, pose], ...]].
## The Chapter 4 figure (group I) comes first; the existing Chapter 3 echo figures stand in until it is built (the
## playthrough reports which). With several figures the pose is split on "|", one for each.
const ECHOES := {
	"tech_panel": ["P", ["tech_panel"], [["echo_tech_panel", "echo_tech_panel|tech_a"], ["echo_technicians", "tech_a"]]],
	"tech_wheels": ["B", ["tech_wheels_a", "tech_wheels_b"], [["echo_tech_wheels", "tech_a|tech_b"], ["echo_technicians", "tech_a|tech_b"]]],
	"clerk_post": ["W", ["clerk_post"], [["echo_clerk_post", "echo_clerk_post|pose_idle"], ["echo_archivist", ""]]],
	"leyla_lift": ["B", ["leyla_lift"], [["echo_leyla_1998_lift", "pose_lift"], ["echo_leyla_1998", "pose_offer"]]],
}
## Leyla, 1998, walking from the Core to the cradle (the leave path), and Strand's ghost at the master desk.
const LEYLA_WALK: Array = [["echo_leyla_1998_lens", "pose_seat|pose_walk"], ["echo_leyla_1998", "pose_offer"]]
const STRAND_GHOST: Array = [["echo_strand_desk", "echo_strand_desk"], ["echo_operator", "pose_reach"]]
## The Chapter 4 echo models (group I) a full build has; the playthrough reports the ones still missing.
const ECHO_MODELS: Array[String] = ["echo_crowd", "echo_named", "echo_strand_desk", "echo_leyla_1998_lift",
	"echo_leyla_1998_lens", "echo_tech_panel", "echo_tech_wheels", "echo_clerk_post"]

## An extra tap area around a small part that is hard to hit (phone61: a part under 9 mm is a trip hazard):
## model id -> {part -> [size, offset]} (see ArrayHallRoom._tap_pads).
const TAP_PADS := {
	"mirror_tower_1": {"IA_key": [Vector3(0.34, 0.28, 0.42), Vector3(0, 0, 0.0)]},
	"mirror_tower_2": {"IA_key": [Vector3(0.34, 0.28, 0.42), Vector3(0, 0, 0.0)]},
	"mirror_tower_3": {"IA_key": [Vector3(0.34, 0.28, 0.42), Vector3(0, 0, 0.0)]},
	"mirror_tower_4": {"IA_key": [Vector3(0.34, 0.28, 0.42), Vector3(0, 0, 0.0)]},
}

## Tower heads (docs/models/ch4_c.md): ring radius per tower, the beam axis and the Core.
const RING_RADIUS: Array[float] = [10.5, 8.5, 6.5, 4.5]
const BEAM_Y := 1.8
const CORE_CENTRE := Vector3(0.0, 4.1, 0.0)
const SUN_IRIS := Vector3(-11.8, 1.8, 0.0)
const SUN_LAMP := Vector3(-13.0, 1.8, 0.0)
const OCULUS := Vector3(0.0, 12.0, 0.0)
## Roll board: the first slot's origin, the step per column and per row (ch4_g.md).
const BOARD_STEP := Vector3(0.16, -0.30, 0.0)
const BOARD_COLS := 14
const BOARD_SLOTS := 42
