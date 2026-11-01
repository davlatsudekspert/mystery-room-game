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
| R3 Night Cell (`room_cell`, `cot`, `light_table`, `acetate_sheet_a/b/c`, `kettle_hotplate`, `cold_door`, `cell_diary`) | not built (scripts for `cot` and `kettle_hotplate` were drafted but never saved) |
| R4 Cold Store (`room_cold`, `carriage` x5, `frost_window`, `cold_chest`, `film_can` x4) | not built |
| Hall changes (`service_door`, `stair_stump`, `floor_plan_frame`) | not built |
| Stage B (R5 gallery, R6 plate room, R7 office, `roll_board`, `pa_horn`, `balcony_rail`, `enlarger`, `negative_strip`, `strand_cabinet`, `tea_set`, `stair_wedge`, `pass_key`, `projector_lamp`) | not built |
| Hands (`hand_glove` rig, `wipe_cloth`) | not built (`mallet` is done) |

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

## Known gaps
- Stage-B and hands content is not started; Cell and Cold Store are not started. See the status table.
