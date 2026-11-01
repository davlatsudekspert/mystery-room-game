# Chapter 2 expansion models ("The Whole Building"), contract for the scene agent

Source design: `docs/CHAPTER2_EXPANSION.md`. Build: `tools/blender/build_lists/ch2x_*.txt` (run by `tools/blender/build_all.sh`;
single model: `blender -b --factory-startup -P tools/blender/models/<name>.py -- --no-render`). Shared helpers:
`tools/blender/lib_ch2x.py` (on top of `lib_ch2_arch.py`). Textures: `tools/textures/make_textures_ch2x.py`; Godot materials:
`tools/materials/make_ch2x_materials.py`. All numbers are Godot axes, metres, model space; front +Z; IA parts have the origin at the
pivot and identity rotation at rest (`docs/models/ch2.md` section 0). QA renders: `docs/previews/ch2_expansion/`.

## Status

| Group | State |
|---|---|
| R2 Pump Room (`room_pump`, `boiler`, `manifold_plate`, `pipe_run`, `book_lift_cage`, `mallet`, `weight_1/2/4/8`) | **built, exported, render-checked** |
| R3 Night Cell (`room_cell`, `cot`, `light_table`, `acetate_sheet_a/b/c`, `kettle_hotplate`, `cold_door`, `cell_diary`) | **built, exported, render-checked** (section "R3 Night Cell and hall additions") |
| R4 Cold Store (`room_cold`, `carriage_1..5`, `frost_window`, `cold_chest`, `film_can_1..4`) | **built, exported, render-checked** (section "R4 Cold Store" below) |
| Hall changes (`service_door`, `stair_stump`, `floor_plan_frame`) | **built, exported, render-checked** (same section) |
| Stage B (R5 `room_gallery`, `balcony_rail`, `roll_call_board`, `pa_horn`, `stair_wedge`; R6 `room_plate`, `enlarger`, `negative_strip`; R7 `room_office`, `strand_cabinet`, `tea_set`, `pass_key`, `projector_lamp`) | **built, exported, render-checked** (section "R5 Reading Gallery, R6 Plate Room, R7 Director's Office" below; the board is `roll_call_board`, not `roll_board`) |
| Hands (`hand_glove` rig, `wipe_cloth`) | `wipe_cloth` **built** (R3 section); `hand_glove` rig not started (`mallet` is done) |

## Built models (measured)

| Model | Tris | Budget in this repo | Doc estimate | Suggested placement (position, yaw) |
|---|---|---|---|---|
| `room_pump.glb` | about 16.5k | 22k | 12k | origin 0, yaw 0 |
| `boiler.glb` | 10.6k | 16k | 6k | (0, 0, -1.75), 0 |
| `manifold_plate.glb` | 12.3k | 13k | 3k + wheels | (3.5, 0, 1.35), -90 |
| `pipe_run.glb` | 10.3k | 11k | 5k | (-3.5, 0, 1.05), +90 |
| `book_lift_cage.glb` | 4.6k | 9k | 6k | (-4.40, 0, -1.50), +90 |
| `mallet.glb` | about 2k | 3k | 1k | on `mallet_mount` of the room |
| `weight_1/2/4/8.glb` | 0.8-1.1k each | - | - | on `hook_mount_0..3` of the cage |

The Pump Room total (shell + props, all visible) is about 57k tris, over the doc's rough 36k sum. The 150k scene limit still holds, but
`ModelUtil.merge_static` per group is expected and the manifold or `pipe_run` can be lowered if a phone budget needs it (the rivets, flange bolts
and glow bands are the cheap cuts). Draw calls are not measured here (no scene yet); each model is one mesh per part with a few material slots.

## Node names and pivots

**room_pump** (room coordinates, origin = room origin; interior x -3.5..3.5, z -3..3, ceiling 3.4)
`floor, wall_n, wall_e, wall_s, wall_w, ceiling, beams, pipe_rack, walkway, pump_unit, bench, stair_in, lift_frame, dressing, puddles`
(static), `IA_door_cell` (pivot (3.455, 0, -1.55), opens with +95 deg about +Y), `work_lamp` (pivot (0.5, 3.4, 0.2), sway about X/Z) with
children `work_lamp_bulb` and the empty `work_lamp_light`, empties `mallet_mount` (1.60, 0.86, 2.58), `light_boiler_glow` (0, 0.70, -0.55),
`light_fill` (-1.5, 2.6, 1.0). Openings: south stair x -2.2..-1.2; east door z -1.55..-0.65; west lift niche z -2.3..-0.7 (1.7 deep).

**boiler**: `boiler_body`, `IA_fire_door` (pivot (-0.285, 0.70, 1.150), opens with -100 deg about +Y), `fire_glow` (origin (0, 0.70, 1.118)),
`needle_boiler` (pivot (0.38, 1.42, 1.154), rest 225 deg = value 0, -27 deg per tick over 270 deg, about +Z), `water_level` (origin (-0.40, 1.16, 1.185),
scale Y 0..1), empty `light_origin_fire` (0, 0.70, 1.20).

**manifold_plate**: `manifold_body`, `IA_valve_0..5` (pivot (-0.80 + 0.32 k, 1.12, 0.255), rotate about +Z), `IA_ram_lever` (pivot (0.88, 0.98, 0.17), +70 deg about +Z active),
`needle_a`, `needle_b` (pivots (-0.55, 1.62, 0.066) and (0.55, 1.62, 0.066), rest 225 deg), `hazard_lamp` (-0.20, 1.62, 0.085, M_Emissive_Red),
`pressure_lamp` (0.20, 1.62, 0.085, M_Emissive_Warm), `diagram_plate` (quad, slot `M_Decal_PipeDiagram`, UV 0..1, centre (0, 1.32, 0.0405), 0.23 x 0.15; the variant diagram image is supplied by code).

**pipe_run**: board 3.0 x 1.8; nodes `s a b c d t h`; nine candidate segments `IA_pipe_sa, sb, ab, ac, bd, cd, ct, dh, th` (pivot = segment midpoint at z 0.10), each with the child
`glow_<ab>` (emissive bands, hide until the flow arrives). A variant graph is drawn by showing a subset. Lamps `hazard_lamp_h` (1.25, 0.60, 0.10) and `target_lamp_t` (1.25, 1.60, 0.10),
gauge needle `needle_src`. `s` = compressor stub (circle + arrow), `t` = Cold Store coil (zig-zag), `h` = vent to the hall (louvres).

**book_lift_cage**: `cage_body`, `IA_gate` (pivot (0, 0.98, 0.585), slide -0.62 along X to open), `IA_btn_flask|book|lamp` (pivots (-0.10|0.15|0.40, 1.28, -0.539), press -0.006 along Z),
`IA_hook` (pivot (0.705, 1.30, 0)), `load_plate` (quad, `M_Decal_LiftPlate`), empty `load_mount`, `hook_mount_0..3` at (0.755, 1.286, -0.36/-0.12/0.12/0.36), `needle_lift`.

**mallet** (item, origin at the centre of mass, handle along Blender +Y, head axis X). **weight_N** (item, ring at +Y Godot; disc axis along Godot Z; ring top above the origin: 1 = 0.085, 2 = 0.110, 4 = 0.141, 8 = 0.175 m).

## Materials added (slots, Godot .tres by `make_ch2x_materials.py`)
`M_Iron_Rust` (cast iron with rust bloom), `M_Wallpaper_Cell`, `M_Wool_Knit`, `M_Steel_Galv`, `M_Wallpaper_Office`, `M_Paint_Black`, `M_Frost`, `M_Acetate`, `M_Emissive_Table`,
`M_Emissive_Safelight`; existing `M_Chequer`, `M_Tile_Glazed` are reused. New decal slots (placeholder images by `tools/textures/make_decals_ch2x.py`, `.tres` written): `M_Decal_PipeDiagram`, `M_Decal_LiftPlate`.

## R3 Night Cell and hall additions (3D artist B)

Build list `tools/blender/build_lists/ch2x_cell.txt`; helpers `tools/blender/lib_ch2x_cell.py`; QA views `tools/blender/ch2x_cell_preview.py`
(`blender -b --factory-startup -P tools/blender/ch2x_cell_preview.py -- --shots=cell,cell2,desk_light,cot,shelf,door,west`), previews `docs/previews/ch2_expansion/cell_*.jpg` and
`hall_*.jpg` (packed from the QA PNGs by `tools/blender/ch2x_cell_pack_previews.py <png dir>`). Decals/materials: `tools/textures/make_decals_ch2x_cell.py`, `tools/materials/make_ch2x_cell_materials.py` (new slots `M_Decal_CellDrawing`, `M_Decal_FloorPlan`,
`M_Decal_Sheet`, `M_Decal_TableMask`; the sheet and mask images are alpha placeholders, the puzzle masks are drawn by code; `M_Decal_FloorPlan` is the same plan the document item uses).
Identity of the room (the "different from the Pump Room" rule): ochre diamond wallpaper over a walnut wainscot, planked floor with an oval wool rug, cream cast radiator under a
curtained window, cloth-shaded pendant and table lamp, shelves of jars and books, a coat on the hooks, a blue enamel kettle. No iron, no rivets.

### Measured (tris)
| Model | Tris | Budget set | Notes |
|---|---|---|---|
| `room_cell.glb` | 22.2k | 26k | 14 static objects, 28 nodes; about 30 unique materials, merge per material with `ModelUtil.merge_static` |
| `cot.glb` | 3.2k | 3.6k | |
| `light_table.glb` | 1.9k | 4.2k | |
| `acetate_sheet_a/b/c.glb` | 0.28k each | 0.7k | |
| `kettle_hotplate.glb` | 4.5k | 4.8k | |
| `cold_door.glb` | 8.9k | 9k | hero prop (each lock drum with numerals 1.1k, ice 1.3k) |
| `cell_diary.glb` | 1.4k | 1.8k | |
| `wipe_cloth.glb` | 1.3k | 1.5k | a Cold Store item |
| **Cell set total** (room + cot + table + 3 sheets + kettle + door + diary) | **43.0k** | 60k goal | |
| `service_door.glb` | 4.2k | 4.2k | the dial is 1.5k of it (hole liners are tap volumes, hide their meshes) |
| `stair_stump.glb` | 2.0k | 3.6k | |
| `floor_plan_frame.glb` | 0.6k | 0.9k | 2 materials, 2 draws |
| **Hall additions total** | **6.7k** | | hall draw calls: floor plan +2; stair stump +4 (3 materials + the ladder); service door +3 while the cover is closed (only `IA_cover_panel`: green, plaster, walnut rail), +9 once it is opened (show the rest then) |

### Placements (yaw about +Y; yaw -90 makes the model front face -X)
**Night Cell origin = (6.2, 0, 0) in the Pump Room frame, yaw 0**: the cell's 0.25 m west wall then continues the Pump Room's east wall (a doorway 0.5 m deep). The leaf
`IA_door_cell` of `room_pump` swings into the cell and ends at cell (-1.85, -1.63); nothing stands there. All rows below are in CELL coordinates (the empties of `room_cell` carry the positions):

| Model | Empty in `room_cell` | Position | Yaw | Notes |
|---|---|---|---|---|
| `cot` | `cot_mount` | (-0.75, 0, -1.58) | 0 | head at -X, the long side faces the room |
| `light_table` | `light_table_mount` | (1.30, 0.76, -1.62) | 0 | on the desk top (y 0.76) |
| `acetate_sheet_a/b/c` (loose) | `acetate_mount_a/b/c` | a (1.70, 0.76, -1.52), b (-0.30, 0.872, 1.66), c (1.20, 1.652, -1.82) | 0 | as items before pick-up: lay them flat (rotate -90 about X); on the table use `sheet_mount_0..2` of `light_table` |
| `kettle_hotplate` | `kettle_mount` | (-0.70, 0.86, 1.76) | 180 | on the sideboard, front toward the room (-Z) |
| `cell_diary` | `diary_mount` | (0.82, 0.76, -1.62) | about 12 | lies flat on the desk (origin = its centre, so use y 0.778) |
| `cold_door` | `cold_door_mount` | (2.20, 0, 0) | -90 | east wall; local +X then points along world +Z, the hinge side (local -X) is the north side; opens INTO the cell |
| `wipe_cloth` | (Cold Store) | n/a | | item; origin = centre of mass, front face up |

Hall additions (HALL coordinates; yaw so that the model +Z points into the hall):

| Model | Position | Yaw | Notes |
|---|---|---|---|
| `service_door` | (5.0, 0, 2.95) | -90 | east wall south of the compressor panel (z 0.2..1.4) and of the pilaster (z 1.98..2.42); spans z 2.5..3.4; the framed rules notice on the east wall may have to move |
| `floor_plan_frame` | wall point (x, 0, z) | east wall -90, north 0, west 90, south 180 | origin on the floor at the centre of the back face; the frame centre is at y 1.55 |
| `stair_stump` | free floor spot of the scene agent's choice | any | origin = the column centre on the floor; footprint radius 0.95; needs 1.0 m clearance; 1.6 m high plus the ladder up to about 3.35 m (jammed against the hall ceiling at 3.6) |

### Node names and pivots (model space; IA parts and all animated parts have identity rotation at rest)
**room_cell** (room coordinates; interior x -2.2..2.2, z -2.0..2.0, ceiling 2.70; openings: west z -1.55..-0.65 y 0..2.1 doorway, east z -0.45..0.45 y 0..2.1 for the cold door)
static: `floor, wall_n, wall_e, wall_s, wall_w, ceiling, trim, rug, furniture, radiator, window, dressing`.
lamps: `lamp_ceiling` (pivot (0, 2.70, 0.20), static, may sway a little), `lamp_ceiling_glow` (bulb, M_Emissive_Warm, origin (0, 2.10, 0.20)), `lamp_desk` (pivot (2.0, 0.76, -1.72)),
`lamp_desk_glow` (bulb, origin (2.0, 1.10, -1.72)). Lights as empties: `light_lamp_ceiling` (0, 2.02, 0.20) warm 2700 K, `light_lamp_desk` (2.0, 1.10, -1.72), `light_fill` (-1.2, 1.9, 1.2),
`light_cot_fill` (-0.8, 1.2, -1.2). The room has no IA parts (the doorway leaf belongs to `room_pump`, the interactive things are the placed models).
Light recipe used in the previews: pendant 120 W-equivalent (amber FFB46B), desk lamp 22, table glow 10 (FFF1D0), fill 14, cot fill 8, cold fill at the door 6 (BFE0FF); world 0.05.
Suggested views (camera -> target, cell coordinates): `cell` (-2.05, 1.70, 1.80) -> (1.3, 0.70, -1.1); `cell2` (2.10, 1.75, 1.05) -> (-1.1, 0.75, -1.0); `desk_light` (1.25, 1.50, -0.35) -> (1.30, 0.85, -1.70);
`cot` (-0.15, 1.45, -0.05) -> (-0.85, 0.50, -1.60); `shelf` (-0.45, 1.45, 0.05) -> (-0.70, 1.00, 1.90); `door` (-0.30, 1.45, 0.10) -> (2.20, 1.10, 0.0).

**cot**: `cot_body`; `IA_cot_drawing` (the drawing: a 0.20 x 0.27 card leaning on the pillow, M_Decal_CellDrawing UV 0..1, origin at its centre (-0.74, 0.622, 0.072), tilt baked); empty `light_cot` (-0.55, 1.10, 0.10).

**light_table** (origin on the desk surface at the footprint centre; footprint 0.42 x 0.42; glass top 0.0585; window = 11 columns x 7 rows of 0.022 m = 0.242 x 0.154, centred on the glass at z 0.02):
`light_table_body`; `table_glow` (opal glass, M_Emissive_Table, origin (0, 0.0585, 0.02); hide or dim = lamp off); `table_mask` (quad 0.242 x 0.154 at y 0.0592, M_Decal_TableMask, UV 0..1, columns left to right = +X,
row 0 at the BACK edge (-Z); the code draws the lit cells, 7 rows x 11 columns row-major as `ArchiveExpData.glyph_window`); `IA_switch` (rocker on the back panel, pivot (0.145, 0.083, -0.1165), ON = -25 deg about +X);
`pilot_lamp` (M_Emissive_Warm, origin (0.095, 0.083, -0.1185)); `sheet_mount_0..2` (y 0.0615 + 0.003 k, z 0.02, each rotated -90 about +X so that a sheet model lies flat, front up); `light_table_light` (0, 0.20, 0.02).

**acetate_sheet_a/b/c** (item, built upright in XY, front +Z, origin = centre; 0.26 x 0.26 x 0.0015; edge tape and flip tab colours: a crimson, b cobalt, c amber; one clipped corner = the reference corner, top left when upright,
and a black wedge at the top edge): `IA_sheet` (root, origin (0, 0, 0); tap = rotate 90 deg CLOCKWISE seen from the front, i.e. -90 deg about its local +Z each tap, matching `ArchiveExpData.sheet_transform`), `sheet_print` (child quad
0.242 x 0.242 at z +0.001, M_Decal_Sheet alpha, UV 0..1 over the 11 x 11 cells, row 0 at the top; the code supplies the mask; the window rows are 2..8), `IA_flip_tab` (child, origin (0.1475, 0, 0) on the right edge; tap = flip =
180 deg about the sheet's local +Y, which mirrors left-right like `sheet_transform(flip = 1)`).

**kettle_hotplate** (origin on the support surface at the footprint centre; 0.42 x 0.27; plate top 0.075): `hotplate_body`; `IA_kettle` (pivot at the base (-0.105, 0.0775, 0); lift = +Y); `IA_knob_left` (pivot (-0.105, 0.040, 0.1345)),
`IA_knob_right` (pivot (0.105, 0.040, 0.1345)): turn about +Z, off = rest (pointer down), full on = -90 deg; `coil_glow` (left ring coils, M_Emissive_Warm, origin (-0.105, 0.0905, 0), hide when off); empty `steam_mount` (-0.255, 0.205, 0).

**cold_door** (origin = centre of the 0.90 x 2.10 opening at floor level on the room-side wall plane; the wall occupies z -0.25..0; front +Z): `cold_door_frame` (liner, architrave, stop with gasket, hinge knuckles, thermal plate x -0.90..-0.60 with the
serpentine copper coil, feed pipe up to y 2.70, return into the floor); `IA_cold_door` (leaf 0.836 x 2.06 x 0.11, origin = hinge axis (-0.44, 0, 0), opens with a NEGATIVE angle about +Y, -100 deg, toward the cell); children of the leaf:
`IA_cold_handle` (cam lever, pivot (0.335, 0.86, 0.040), rest up = locked, release = -90 deg about +Z), `IA_digit_a` (pivot (0.245, 1.28, 0.012)), `IA_digit_b` (pivot (0.325, 1.28, 0.012)): digit drums with the numerals 0-9,
digit k in front = rotate +36 deg x k about +X (k + 1 sits above k); `lock_lamp` (jewel, M_Emissive_Red, origin (0.285, 1.375, 0.056)); static extras: `coil_glow` (emissive bands on the coil, origin (-0.70, 1.10, 0.030); show while hot), `door_ice`
(frost lumps and icicles, M_Frost, origin (0, 1.05, 0.02); hide when thawed), empties `coil_mount` (-0.84, 2.70, 0.03) and `light_cold_door` (0, 2.0, 0.35).

**cell_diary** (item, lies flat, cover +Y, spine at -X, foot (ribbon) at +Z; 0.150 x 0.036 x 0.210): `IA_cell_diary` (origin = centre). **wipe_cloth** (item, flat, 0.15 x 0.11 x 0.02): `wipe_cloth`, empty `grip_mount` (0, 0.0165, 0).

**service_door** (origin = centre of the 0.90 x 2.10 opening at floor level on the hall-side wall plane; the wall occupies z -0.20..0): `service_door_frame` (casing, reveal liners, threshold, shaft with four steps going down); `IA_service_door`
(leaf, origin = hinge axis (-0.43, 0, -0.04), opens with -100 deg about +Y); child `IA_rotary_dial` (finger wheel, origin = dial centre (0.20, 1.42, 0.0095); hole n at theta = 50 + (n - 1) x 30 deg counter-clockwise from +X seen from the front,
radius 0.0445, finger stop at -10 deg; dialling n = rotate (theta_n + 10) deg clockwise; the same convention as `booth_door`'s dial) with children `IA_dial_hole_0..9` (liner tubes, origin = hole centre, tap volumes: hide the meshes);
`service_lamp` (origin (0, 2.175, 0.035), M_Emissive_Red); `IA_cover_panel` (the painted hatch that hides the door, origin = hinge line (0, 2.20, 0.0475), opens -75 deg about +X); empty `light_service` (0, 1.9, 0.5).

**stair_stump**: `stair_stump_body` (column, 8 chequer treads rising 0.18 each, brackets, balustrade, helical handrail, broken landing at y 1.62, rubble); `IA_wedge_ladder` (origin = its lower end on the landing (-0.55, 1.64, -0.05), identity; it leans up to the hall ceiling; slide it
or hide it when the stair opens from above); empty `light_stair_top` (0, 2.3, 0).

**floor_plan_frame** (wall-mounted): `floor_plan_frame`, `IA_floor_plan` (plan quad 0.59 x 0.37, origin (0, 1.55, 0.0195), M_Decal_FloorPlan, UV 0..1).

## R4 Cold Store (artist section, `tools/blender/build_lists/ch2x_cold.txt`)

Status: **built, exported, render-checked** (`room_cold`, `carriage_1..5`, `frost_window`, `cold_chest`, `film_can_1..4`). Helpers: `tools/blender/lib_cold.py`
(on `lib_ch2x.py`). Decals/images (PIL, original, language neutral): `tools/textures/make_decals_cold.py` into `game/assets/textures/decals/ch2x/`.
Materials: `tools/materials/make_ch2x_materials.py` (R4 block). QA: `blender -b --factory-startup -P tools/blender/ch2x_room_preview.py -- room=cold [--shots=cold,overview,aisle,frost,rail_end,chest,evap,door]`
(entry in `tools/blender/ch2x_rooms_cold.py`). Previews: `docs/previews/ch2_expansion/cold_room_{cold,overview,aisle,rail_end,frost,chest,evap,door}.jpg` (the room set placed with `carriage_slot`s 0 1 3 4 6 occupied), `cold_carriage_{front,aisle}.jpg`, `cold_chest_{closed,open}.jpg` (lid -105 deg, rings turned to symbols 2 and 5), `cold_frost_window_{frosted,wiped}.jpg` (middle band wiped), `cold_film_cans.jpg`, and the wipe-mask layout `cold_frost_uv.png`.

Identity (vs the other lower rooms): pale blue-grey galvanised zinc and white "ice" enamel, a vaulted ceiling with steel ribs, 7 tube lights (cold white
`M_Emissive_Cold`), frost and ice everywhere, one red accent (the carriage hand wheels, the door release, the rail stops) and one warm human object (a wool
parka). Light recipe for the scene: 3 cold-white OmniLights over the carriage bank (6500-7500 K, empties `light_cold_0..2` at y 2.95), one cold fill at the front,
one pale cyan glow at the window (`light_window_fill`), NO warm lights; fog `shadow_teal` to blue, breath mist from `breath_origin`.

### Measured
| Model | Tris | Budget | Placement |
|---|---|---|---|
| `room_cold.glb` | 6.1k | 16k | origin 0, yaw 0 |
| `carriage_1..5.glb` | 3.55 / 3.65 / 3.73 / 3.79 / 3.85k (18.6k all five) | 4.8k | origin = slot centre `carriage_slot_i`, yaw 0 |
| `cold_chest.glb` | 5.9k | 6.0k | `chest_mount_i`, yaw 0 |
| `frost_window.glb` | 1.3k | 3.2k | `window_mount` (3.845, 1.63, 2.20), **yaw -90** |
| `film_can_1..4.glb` | 1.03 / 1.23 / 1.26 / 1.29k | 1.8k | held items (origin at the centre, lid axis +Y) |
Room set total (room + 5 carriages + window + chest, no cans) about 32k tris, well under the 60k target; the carriage is the biggest block, cut candidates are the box/can contents. Materials per model: 2-11 slots (the carriage has 7, joined meshes, one object).

### room_cold nodes (room coordinates)
Interior x -3.8..3.8, z -3.4..3.4, walls 3.0 at the corners, barrel vault (axis along X) rising to 3.8 at z = 0. Static objects: `floor, wall_n, wall_s, wall_e, wall_w,
ceiling, ribs, rails, lamps, evaporator, door_frame, strip_curtain, dressing, frost_patches, frost_decals, well, plan_frame`; `window_glow` (emissive plane in the light well),
`plan_plate` (quad 0.50 x 0.344, slot `M_Decal_PlanPlate`, UV 0..1, centre (3.7875, 1.55, 1.00), faces -X; code draws the variant plan, placeholder `plan_plate.png`).
Empties: `carriage_slot_0..6` (x = -3 .. +3, z -1.00, y 0), `chest_mount_0..6` (x = slot, z -3.14), `window_mount`, `door_mount` (-3.80, 0, 2.20), `light_cold_0..2`,
`light_window_fill`, `breath_origin` (0, 1.55, 2.6), `evaporator_mount` (-1.65, 2.8, -2.7). Openings: west door z 1.75..2.65 (y 0..2.15) from the Night Cell (leaf = `cold_door` of the Cell set,
this room supplies jambs, gasket, threshold, release knob, PVC strip curtain); east window z 1.72..2.68 (y 0.95..2.31) with a light well behind it.
Carriage bank: 7 slots at 1.00 m pitch, rails (parts of `rails`) at z = -2.20 and +0.20 (top y 0.025), end stops at x = +-3.62. **Gaps**: 5 carriages in 7 slots.
Back strip z -3.40..-2.60 for the chest. Colliders: `ModelUtil` builds trimesh blockers for the big static meshes; the room's blockers are the walls and `dressing`.

### carriage_N nodes (N = 1..5, same node names; contents seeded by N)
Origin = floor, footprint centre (0.92 x 3.20 x 2.45), front end panel +Z. Slides along **X** (one slot = 1.00 m per crank). `carriage_body` (static, 7 slots);
`IA_crank` (pivot (0, 1.15, 1.69), identity rest, turn about +Z; red cast hand wheel with a black spinner knob, 3 spokes); `end_tag` (quad 0.20 x 0.12 at (0, 1.95, 1.6127), slot
`M_Decal_CarriageTags`, UV already on cell N of the 5-cell atlas: pips N + colour band red/blue/yellow/green/white); `light_carriage` (0, 2.2, 0). Shelf faces are the +X and -X
sides: 5 deck levels at y 0.32 0.76 1.20 1.64 2.08, 4 bays per side, archive boxes and film-can stacks (no interaction). Tap boxes for the scene: the end panel for the crank
(`IA_crank`), the shelf faces are blockers only.

### frost_window nodes (origin = pane centre in the glass plane, front +Z = into the room)
`window_frame` (static), `window_glass` (clear pane, `M_Glass`), `frost_sign_0..2` (quads 0.22 x 0.22 at z +0.004, slot `M_Decal_FrostSign`: the scene sets the texture
`decals/ch2x/frost_sign_<k>.png` of the variant), `frost_glass` (quad 0.80 x 1.20 at z +0.018, slot `M_Decal_FrostPane` = the wipe-reveal ShaderMaterial), empties `band_0..2` (0, +0.40|0|-0.40, 0.018), `light_window` (0, 0, -0.20).
**Wipe mask / UV layout**: `frost_glass` UV 0..1 covers the pane exactly (U left to right seen from the room, V 0 = TOP = row 0 of the image). Bands (0.40 high each): band 0 = V 0..1/3, band 1 = 1/3..2/3,
band 2 = 2/3..1. Sign k is centred in band k, shifted -0.22 / 0 / +0.22 along X (reading left to right = band order). Shader: `game/assets/materials/frost_reveal.gdshader`,
material `M_Decal_FrostPane.tres`; uniforms `wipe_mask` (R8 texture, white = wiped; paint it in pane UV space, suggested 64 x 96), `reveal` (0..1 global), `frost_tex`, `frost_tint`, `tiling`,
`edge_softness`. To wipe: update the mask `ImageTexture`, nothing else. Alternative "tap a band" = fill the band's rows of the mask. The plain `M_Frost` stays as a non-shader fallback. The slot is named `M_Decal_...` on
purpose: the build's world-scale UV pass skips `M_Decal_` slots, which keeps the 0..1 UV.
Placement in the room: `window_mount`, yaw -90; the wall opening is 0.96 x 1.36, the casing (0.10) covers its edge. The reveal reaches 0.22 behind the pane.

### cold_chest nodes (origin on the floor, footprint centre, front +Z, 0.90 x 0.52 x 0.62)
`chest_body` (static), `IA_lid` (pivot (0, 0.50, -0.26) hinge axis; open = **-105 deg about +X**), `IA_ring_0..2` (pivots (-0.26|0|+0.26, 0.27, 0.287), turn about +Z; drum symbols in
`M_Decal_ChestRings`: symbol k at angle 90 - 60 k deg clockwise from the TOP, k: 0 sun, 1 moon, 2 star, 3 triangle, 4 circle, 5 square = the Chapter 3 drum order; a ring shows symbol k at the top
when rotated by **+60 k deg about +Z** (counter-clockwise seen from the front); step = 60 deg), `crystal_mount_0|1` (-0.14|0.14, 0.31, 0), `note_mount` (0, 0.31, 0.15), `light_chest`
(0, 0.44, 0). The lid carries the Meridian stencil (`M_Decal_SafeStencil`, alpha) and a blank brass plate (`M_Decal_ChestPlate`); the inscription is code/`tr()`, the model has no text. A fixed red pointer wedge sits
over every ring (the symbol under it is the selected one).

### film_can_1..4 (held items)
Single objects, origin at the centre of mass, lid axis +Y, label slots `M_Decal_CanLabel_1..4` (numeral-only labels 35 / 16 / 8 / 9). 1 = big 35 mm can with canvas strap, 2 = 16 mm can with tape,
3 = small dented can, 4 = tall can with wire handle and paper tag. Diameters 0.30 / 0.20 / 0.13 / 0.20 m.

### Notes for the scene
- Do not bevel thin slabs (< 3 cm) in future edits of these scripts: custom normals turned thin bevelled casing boxes black. The window casing is bevel-free for that reason.
- The preview images were rendered with software Cycles; the room previews before the last `steel_galv` retune (door, evap, chest views) show the zinc slightly more metallic than the final `.tres` textures.
- Frost patches (`frost_decals`) are alpha quads 1.8 cm off the panel strips: give them no colliders and no shadows.

### Materials added for R4
`M_Enamel_Ice`, `M_Emissive_Cold`, `M_Decal_ChestRings`, `M_Decal_ChestPlate`, `M_Decal_SafeStencil` (alpha), `M_Decal_CarriageTags`, `M_Decal_PlanPlate`, `M_Decal_CanLabel_1..4`,
`M_Decal_FrostSign` (alpha), `M_Decal_FrostPatch` (alpha, soft frost blotches), `M_Decal_FrostPane` (ShaderMaterial). `steel_galv` was retuned (paler, half metal) so a closed room does not turn it black.

## Known gaps
- Stage-B and hands content is not started. Cold Store: no per-carriage lore cans are placed on the shelves (the four `film_can_N` are separate items for the scene to place); the Pump Room refrigerant line only ends at the evaporator (`evaporator_mount`); no sound or particles (breath mist is the scene's job at `breath_origin`). See the status table.

## R5 Reading Gallery, R6 Plate Room, R7 Director's Office (3D artist C, upper floor)

Build list `tools/blender/build_lists/ch2x_upper.txt`; helpers `tools/blender/lib_ch2x_upper.py` (on `lib_ch2x.py`: arched windows, wall boxes, bookcases,
banker lamp, chairs, framed busts); QA views `tools/blender/ch2x_upper_preview.py`
(`blender -b --factory-startup -P tools/blender/ch2x_upper_preview.py -- room=gallery|plate|office [--shots=a,b]`), previews are packed by
`tools/blender/ch2x_upper_pack.py` into `docs/previews/ch2_expansion/` (`gallery_*`, `plate_*`, `office_*`, and the cross-room
`room_identity_sheet.jpg` made by `tools/blender/ch2x_identity_sheet.py`). Decals: `tools/textures/make_decals_ch2x_upper.py`; materials:
`tools/materials/make_ch2x_upper_materials.py` (new slots `M_Decal_RollTags`, `M_Decal_CabinetLabel`, `M_Decal_Negatives`, `M_Decal_Prints`; all images are placeholders,
the variant images are swapped by code).
**Name change:** the Gallery board is `roll_call_board.glb`, not `roll_board.glb` (that name is the Chapter 4 Watch Room board and must not be overwritten).
Identity of the rooms (no two share a dominant colour and a prop type): **Gallery** = sepia daylight through tall arched windows, wood, green leather inlays and green lamp
shades, a double-height void with the hall below, a records counter with a brass grille; **Plate Room** = black walls over pale tile, deep red safelights, glass plates in
wooden racks, a steel sink with three trays, an enlarger bench, prints on a line; **Office** = bottle-green watered wallpaper, mahogany and leather, a marble fireplace, brass,
a green desk lamp, original silhouette portraits, a pale ghost circle where a clock used to hang (no clock in the room).

### Measured (tris)
| Model | Tris | Budget set | Suggested placement (position, yaw) |
|---|---|---|---|
| `room_gallery.glb` | 33.8k | 60k | origin 0, yaw 0 |
| `balcony_rail.glb` | 4.9k | 6k | (0, 0, 1.60), 0 (`rail_mount`) |
| `roll_call_board.glb` | 4.0k | 5k | (-1.0, 0, -3.0), 0 (`board_mount`) |
| `pa_horn.glb` | 3.7k | 4k | (-4.5, 3.35, 0.15), +90 (`horn_mount`) |
| `stair_wedge.glb` | 1.2k | 3.5k | (3.15, 0, 1.00), 0 (`wedge_mount`) |
| `room_plate.glb` | 19.1k | 40k | origin 0, yaw 0 |
| `enlarger.glb` | 4.4k | 6k | (0.20, 0.90, -2.20), 0 (`enlarger_mount`) |
| `negative_strip.glb` x4 | 22 | 400 | on `strip_mount_0..3` of the plate room, flat |
| `room_office.glb` | 40.8k | 50k | origin 0, yaw 0 |
| `strand_cabinet.glb` | 5.1k | 12k | (2.67, 0, 0.30), -90 (`cabinet_mount`) |
| `tea_set.glb` | 4.3k | 6k | (-0.55, 0.606, 0.95), 0 (`tea_mount`) |
| `pass_key.glb` (item) | 0.8k | 1.5k | on the desk; item origin = centre of mass, lies flat |
| `projector_lamp.glb` (item) | 1.1k | 1.8k | in the cabinet at `lamp_mount` (the lamp stands upright, its centre is 0.062 above `lamp_mount`) |
Room sets: Gallery 33.8 + 4.9 + 4.0 + 3.7 + 1.2 = 47.6k. Plate Room 19.1 + 4.4 + 4 x 0.02 = 23.6k. Office 40.8 + 5.1 + 4.3 + 1.9 = 52.1k (the glass-front bookcases with books
are the cost: about 14k; drop the book rows into one decal if a phone budget needs it). All under the ~60k goal. Draw calls are not measured (no scene yet).

### Node names and pivots (Godot axes; origin = pivot, identity at rest)
**room_gallery** (interior x -4.5..4.5, z -3..3, ceiling 4.2; the floor ends at the balcony edge z = 1.6, the void drops to the hall floor y = -4.2)
static: `floor, wall_n, wall_e, wall_s, wall_w, ceiling, beams, windows, sky_cards, counter, tables, chairs, lamps, bookcases, stair_in, hall_below, dressing`.
Interactive: `IA_door_plate` (north wall, pivot (-4.1, 0, -2.955), +95 deg about +Y opens into the Plate Room), `IA_door_office` (east wall, pivot (4.455, 0, -2.4), +95 deg opens into
the office; carries the tag-shaped brass keyhole plate at (4.41, 1.12, -1.62)), `IA_counter_drawer_0..2` (pivots (-3.78, 0.54, -1.0 / -0.2 / 0.6), slide +0.35 along +X),
`IA_tube_hatch` (pivot (-4.328, 1.35, 1.30), the tube terminal hotspot, swing about +Y or slide +0.04 along +X). Empties `board_mount`, `horn_mount`, `wedge_mount`, `rail_mount`,
`tube_mount`, `light_window_n`, `light_window_s`, `light_table_a`, `light_table_b`. `sky_cards` are bright emissive cards outside the windows (the daylight seen through them; they do not light the room,
the scene adds a warm sepia DirectionalLight/OmniLights). `hall_below` (hall floor, far wall, two enamel pendants with bulbs) is baked geometry, hide it with the zone.
**balcony_rail**: `rail_main`. **pa_horn**: `horn_body`, `horn_lamp` (pivot (0, 0.135, 0.20), M_Emissive_Warm pilot lamp), empty `light_origin_horn` (0, 0, 1.05).
**stair_wedge**: `wedge_body`, `IA_wedge_chock` (pivot (0, 0, 0.17), slide +0.35 along +Z after the pin is out), `IA_wedge_pin` (pivot (0, 0.215, 0.17), pull +0.22 along +Y),
`IA_wedge_ladder` (pivot (0, 0.02, 0), topples about +X 0 -> -78 deg, the top falls toward -Z over the stairwell).
**roll_call_board** (six hooks, six tags, 6 slip clips; board 2.50 x 1.36, x +-1.25, y 0.90..2.26): `roll_call_board_body`, `IA_tag_0..5` with pivot = hole centre of tag k hanging on hook k at rest
(-1.00 + 0.40 k, 1.85, 0.056); move tag to hook j by translating ((j-k) * 0.40, 0, 0). Tag 0.30 x 0.225 x 0.012. Empties `hook_0..5` (same points), `slip_mount_0..5` (-1.00 + 0.40 k, 1.30, 0.034), `light_origin_board`.
Portraits: quad `photo<k>` on each tag, slot `M_Decal_RollTags` (3 x 2 atlas, cell k, row 0 on top); the pip rows under the hooks (1..6 dots) are geometry, no text.

**room_plate** (interior x -3..3, z -2.6..2.6, ceiling 3.0): static `floor, wall_n/_e/_s/_w, ceiling, beams, bench, plate_racks, sink_bench, trays, drying_table, print_line, curtain, fan, safelights, dressing`;
`IA_door_gallery` (south wall, pivot (-1.7, 0, 2.555), +95 deg about +Y opens OUT to +Z). `safelights` are the red emissive lenses (M_Emissive_Safelight), the scene adds the red OmniLights at
`light_safelight_a` (-1.2, 2.7, -0.4), `_b` (1.3, 2.7, 0.9), `_c` (2.80, 2.1, -0.3) and a warm `light_enlarger` (0.25, 1.5, -2.1). Empties `enlarger_mount` (0.20, 0.90, -2.20), `paper_mount`,
`strip_mount_0..3` ((-1.62, 0.902, 0.10 + 0.09 k), strips lie along X). `print_line` has six peg-hung print quads, slot `M_Decal_Prints`.
**enlarger** (origin on the baseboard bottom centre): `enlarger_body`, `IA_head` (pivot = optical axis at the carrier (0.05, 0.70, 0.10); ZOOM: slide +Y 0.04 per step, 5 steps = 0.16),
`IA_zoom_knob` (pivot (-0.33, 0.74, -0.19), about +X, child of IA_head), `IA_focus_ring` (pivot (0.05, 0.375, 0.10), about +Y, 9 ticks every 40 deg, child of IA_head), empties `strip_slot`
(0.05, 0.6745, 0.10: the strip lies here, along X), `light_origin_enlarger` (0.05, 0.40, 0.10); quad `projected_image` (centre (0.05, 0.0345, 0.10), 0.20 x 0.15, slot `M_Decal_Prints`).
**negative_strip**: `strip_body` (M_Film), `strip_frames` (quad, slot `M_Decal_Negatives`, UV 0..1; the right-most 6 percent is the edge-symbol window). 0.200 x 0.045 x 0.0012, flat, centre = origin.

**room_office** (interior x -2.9..2.9, z -2.4..2.4, ceiling 3.2): static `floor, wall_n/_e/_s/_w, ceiling, window, sky_card, curtains, desk, chairs, tea_table, rug, fireplace, bookcases, portraits, dressing`;
`IA_door_gallery` (west wall, pivot (-2.855, 0, -0.70), +95 deg opens OUT to -X; the same tag-shaped keyhole on its inner face), `IA_desk_drawer` (centre drawer, pivot (0.4, 0.59, -0.83), slide +0.30 along +Z).
Empties `cabinet_mount` (2.67, 0, 0.30), `tea_mount` (-0.55, 0.606, 0.95), `light_desk_lamp` (0.05, 1.12, -1.25), `light_window_n`, `light_fire` (-0.5, 0.5, 2.1). The desk lamp is built into `desk` (green glass shade).
**strand_cabinet** (1.04 w x 0.46 d x 1.92 h, origin on the floor at the footprint centre): `cabinet_body`, `IA_door_l` (pivot (-0.485, 1.16, 0.243), -100 deg about +Y), `IA_door_r` (pivot (0.485, 1.16, 0.243), +100 deg),
`IA_digit_0..3` (pivots (-0.105 / -0.035 / 0.035 / 0.105, 1.64, 0.244), about +X, +36 deg per digit, slot `M_Decal_DrawerDigits`), quad `cabinet_label` (centre (-0.33, 1.64, 0.2742), 0.115 x 0.082, slot
`M_Decal_CabinetLabel`), empties `lamp_mount` (0, 0.952, 0), `light_origin_cabinet` (0, 1.0, 0.30). The lock plate and label sit on a fixed transom above the doors, so the doors open freely.
**tea_set**: `tea_body`, `IA_cup_a` (pivot (-0.12, 0.02, 0.07)), `IA_cup_b` (pivot (0.12, 0.02, 0.07)), optional lift +0.06 along +Y. **pass_key**: `pass_key_body` (bow = the roll-call tag shape).
**projector_lamp**: `projector_lamp_body` (upright, base down).

### Known gaps / notes
- The previews use QA lights only; the scene must add its own lights (listed above). Gallery windows rely on the `sky_cards` for the daylight look.
- The tags' portrait atlas, strip image, cabinet label symbol and print are placeholders (see decals above).
- `tools/blender/build_all.sh` rebuilds every repository model and rewrites tracked GLBs byte-wise; build only the list you need (`tools/blender/models/<name>.py -- --no-render`).
