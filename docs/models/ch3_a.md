# Chapter 3 group A: shell, lift, doors and shared art (measured results)

Contract: `docs/models/ch3.md` §0–§3, §11–§14. Models: `blast_door`, `array_below`, `shell_gallery`,
`freight_lift`, `shell_lift`, `shell_choir`, `shell_nursery`. Shared art: `tools/blender/lib_ch3_symbols.py`, the
new material slots, `tools/textures/make_decals_ch3.py` (decals, symbol images, texture sets) and the seed-0
shader-quad previews.

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [--shots=1,2,...]
python3 tools/textures/make_decals_ch3.py [--only symbols,interlock_plate,...] [--no-sheet]
python3 tools/materials/make_extra_materials.py
```

Scripts: `tools/blender/models/<name>.py`, helpers in `tools/blender/lib_ch3_a.py` (on top of `mrlib`,
`lib_mech`, `lib_arch`, `lib_props`, `lib_ch2_vault`, `lib_ch2_arch`; none of those were edited), build list
`tools/blender/build_lists/ch3_a.txt`. Every script builds its geometry directly in Godot axes (the
`lib_ch2_vault` "G-frame"), converts to Blender axes before parenting, exports `game/assets/models/<name>.glb`
and then **reads the GLB back**: required node names, parents, model-space positions (1 mm), identity rest
rotations, mount rotations, triangles, surfaces (mesh nodes × primitives) and material slots against §13, and
`check_glb_names.py` (passes on all seven GLBs).

QA renders: Cycles, 32 samples, 960 × 640, 2 threads, cameras from the §2 views (Godot position, target and
vertical FOV), neighbouring group-A GLBs imported. **Blender QA renders only, not Godot screenshots.** In the
renders the lamp glasses, jewels and Array rings get a QA-only emissive override (the code turns emission on in
the game); shader quads show the seed-0 preview images.

All coordinates are **Godot, metres**; models face +Z; angles follow §0 (positive = counter-clockwise looking
down the +axis).


## Summary

| Model | Tris (budget) | Surfaces (cap) | Slots (≤ 4) | GLB | QA renders (`qa/blender/ch3/`) |
|---|---|---|---|---|---|
| `blast_door` (×2) | 8,863 (9,000) | 15 (15) | 4 | `game/assets/models/blast_door.glb` | `blast_door.png`, `_2` … `_6` |
| `array_below` | 5,466 (6,000) | **11 (10)** | 4 | `game/assets/models/array_below.glb` | `array_below.png`, `_2` |
| `shell_gallery` | 10,492 (12,000) | **12 (10)** | 4 | `game/assets/models/shell_gallery.glb` | `shell_gallery.png`, `_2` … `_7` |
| `freight_lift` | 6,597 (7,000) | 10 (10) | 4 | `game/assets/models/freight_lift.glb` | `freight_lift.png`, `_2` … `_4` |
| `shell_lift` | 5,404 (7,000) | **9 (8)** | 4 | `game/assets/models/shell_lift.glb` | `shell_lift.png`, `_2` … `_4` |
| `shell_choir` | 11,552 (18,000) | 14 (14) | 4 | `game/assets/models/shell_choir.glb` | `shell_choir.png`, `_2` … `_7` |
| `shell_nursery` | NURSERY_TRIS (14,000) | 12 (12) | 4 | `game/assets/models/shell_nursery.glb` | `shell_nursery.png`, `_2` … `_6` |

Surfaces = mesh nodes × primitives in the GLB (draw calls before shadows). The three over-cap counts are explained
under Deviations; each is the smallest count that keeps every named object of §3.

---

## Shared art

### `tools/blender/lib_ch3_symbols.py`
Pure math at import (no `bpy`), so the decal generator and every Blender script use the same outlines.
- `shapes(kind, h)` → non-overlapping filled shapes `[[outer, *holes], ...]`, bounding box centred on (0, 0), height
  `h`, +y up; `loops(kind, h)` flattens them for even-odd fills; `bounds(kind, h)`.
- Kinds: `sun` (disc r 0.255 h + 8 tapered rays 0.325 … 0.5 h, one straight up), `moon` and `star` (exactly the
  proportions of `vault_door.py` `sym_plate()`: crescent of R 0.028 / r 0.0235 / d 0.0125 scaled to the height,
  **opening to the right**; four-pointed star, inner radius 0.129 h, point up), `triangle` (equilateral, point up),
  `circle`, `square`, `diamond` (square turned 45°, equal diagonals); plus `mark` / `mark_ticks` (Strand's mark /
  the Institute mark: ring + meridian, Chapter 1's ten ticks) and `sign` (Leyla's sign, the Chapter 2 crescent with
  three dots) from the `make_decals_ch2.py` constants.
- `DRUM_ORDER` = sun, moon, star, triangle, circle, square (`DRUM_SYMBOLS` 0..5); `KEY_SHAPES`; `DECAL_FILE`,
  `DECAL_SLOT` (`M_Decal_Sym_<Name>`).
- `ring_icon(i, d)`: the drum lock's four concentric circles with circle i bold.
- Blender helpers (lazy imports): `inlay(name, kind, h, depth=0)` (flat inlay, or a relief with `depth`),
  `ensure_materials()` (every new slot, see below).
- `SLOTS`: the preview values of the new Chapter 3 slots. On import inside Blender they are added to
  `mrlib.PREVIEW` at run time (**mrlib.py itself is not edited**), so `M.material("M_Rock")` gets the right
  colour in any script that imported `lib_ch3_symbols`.

### Material slots (`tools/materials/make_extra_materials.py`, Chapter 3 section → `game/assets/materials/`)
| Slot | Godot material | Source |
|---|---|---|
| `M_Tile_Glazed` | ORMMaterial3D, uv1_scale 1.6667 (0.6 m repeat, 4 × 4 tiles of 0.15 m) | `textures/tile_glazed/` (procedural: cream glaze with per-tile tint, fine crazing on some tiles, pinholes, grime streaks, chipped corners; grey grout, recessed in the normal map) |
| `M_Rock` | ORMMaterial3D, uv1_scale 0.4167 (2.4 m repeat) | `textures/rock/` (procedural: fractured blocks from two warped Voronoi scales, iron stains, calcite, wet seeps with low roughness) |
| `M_Chequer` | ORMMaterial3D, metallic 1 × ORM blue (0.85 on clean steel), uv1_scale 3.3333 (0.30 m repeat, 10 × 10 lugs), anisotropic | `textures/chequer/` (procedural diamond tread plate: ±45° lugs, worn bright tops, dirt and rust in the valleys); normal map only, **no alpha** |
| `M_Porcelain` | StandardMaterial3D #5A3320, roughness 0.15, clearcoat 0.6 | — |
| `M_Shader_Quad` | StandardMaterial3D #1A1F1E, roughness 0.3 (placeholder; the code replaces it) | — |
| `M_Decal_Sym_Sun/Moon/Star/Triangle/Circle/Square/Diamond` | alpha scissor 0.5 | `decals/ch3/sym_*.png` |
| `M_Decal_InterlockPlate` | vitreous enamel, roughness 0.22 | `decals/ch3/interlock_plate.png` |
| `M_Decal_EcgPaper` | roughness 0.85 | `decals/ch3/ecg_paper.png` |
| `M_Decal_GrowthLog` | roughness 0.85 (DecalLoc swaps `_ru` / `_uz`) | `decals/ch3/growth_log.png` |
| `M_Decal_StrandNote` | roughness 0.85 (DecalLoc swaps `_ru` / `_uz`) | `decals/ch3/strand_note.png` |
| `M_Decal_StaffPhoto` | roughness 0.3 | `decals/ch2/film_frame_2.jpg` (the 41 staff) |

Re-running `make_extra_materials.py` rewrites every older `.tres` byte for byte (checked: no diff).

### Decals (`tools/textures/make_decals_ch3.py` → `game/assets/textures/decals/ch3/`)
| File | Size | Notes |
|---|---|---|
| `sym_sun/moon/star/triangle/circle/square/diamond.png` | 512² RGBA | white on transparent, symbol height 0.80 of the image (409.6 px), centred, from `lib_ch3_symbols` |
| `interlock_plate.png` | 1024 × 512 | cream enamel: top row Castell keys with ◆ ▲ ● ■ bows → a door (with a ■ on its lock); bottom row three rule panels: a key going down into a lock face → the isolator dial (I at 12, O at 9) with the bar turned to O and an anticlockwise arrow → the key window with its flap swung open and the next key coming out. Red arrows, blue-black print, chipped edges. **No words** |
| `ecg_paper.png` | 2048 × 320 | salmon grid (1 mm minor, 5 mm major at 6.4 px/mm), 1 s ticks on the top edge; pen brackets at u [0.06, 0.32], [0.38, 0.62], [0.68, 0.94] (bracket line at v 0.70, ticks down to v 0.615) with hand-inked ☼ ☾ ✦ centred above them at v ≈ 0.81 (top 4 mm left free for the clip hole). **No trace.** The free band for the trace shader is v 0.06 … 0.58; the preview uses baseline v 0.30 and peak height 0.27 |
| `chalk_grid.png` | 1024 × 352 RGBA | 7 chalk lines at v = (0.10 + 0.12 (h − 1)) / 0.90 from u 0.035 to 0.965, 7 column ticks at u = (x_k + 1.30) / 2.60 (v 0.02 … 0.068), faint rub haze. **No dots** |
| `growth_grid.png` | 768 × 1024 | Leyla's 1 cm graph paper (5 cm major); axes (vertical at u 0.10, horizontal at v 0.085, with arrow heads); the 6 ruled level lines at v = 0.12 + 0.13 (l − 1) with hand-written numerals 1–6 at u 0.062; dashed stage boundaries at u 0.39, 0.66, 0.93; seed / flame / crystal pictograms centred under the stages at v 0.04. **No curve** |
| `growth_log.png`, `_ru`, `_uz` | 768 × 1024 | notebook page (blue rules every 8 mm, red margin), date 14.III.1998, `doc3.growth_log` in Leyla's hand (Caveat; the Uzbek ʻ falls back to FreeSans); the blank pencil-ruled square u 0.22–0.78, v 0.15–0.57 (rules stop around it) with the **clockwise one-third-turn arrow** on r = 0.050 m (183 px) around (u 0.50, v 0.36), from 12 o'clock to 4 o'clock, with end ticks |
| `strand_note.png`, `_ru`, `_uz` | 512 × 384 | `doc3.note` in a slanted fountain-pen hand (Caveat, sheared), signed — S. / — С., an ink blot, memo-pad hairline |

QA sheets: `qa/blender/ch3/decals_ch3_sheet.jpg` (everything above + the three texture sets) and
`qa/blender/ch3/decals_ch3_lang_sheet.jpg` (EN | RU | UZ).

### Seed-0 shader-quad previews (`qa/blender/ch3/preview/`, not shipped)
`stair_quad.png` (chalk grid + dots 4 6 2 7 1 5 3), `strip_face.png` (ECG with peaks ☼ 4, ☾ 2, ✦ 6 plus one
peak in each gap and at each end), `glyph_panel.png` (4 × 3 atlas of the 12 glyphs in the §11 cell layout, style 0
engraved enamel, alpha 0 outside the hexagon) and `glyph_open.png` (drawer 6), `log_sketch.png` (001101, style 1
pencil, transparent outside the lines) and `growth_log_composed.jpg` (the sketch on the page inside the arrow),
`chart_image.png` (curve 5 2 4), `receptor_0..2.png` (start state P = Q = +2: only receptor 2 lit ▲ + ■ magenta;
rims yellow ▲●, yellow ▲●, blue ■ with cream symbols) and `receptor_*_solved.png` (P 0, Q −1),
`strand_plate.png` (3:2 engraved figure, 9:7 plate), `scope_screen.png` (start: a dot) and
`scope_screen_live.png` (3:2 locked), `osc_screen_s1..4.png` (cycles = 2 + 2 (5 − size)) and `osc_screen.png`
(= the melody's first note, size 3), `ring_symbols.png` (☾ ▲ ✦ ● as composed for the four rings), and
`previews_sheet.jpg`. The flat-topped hexagon follows §11 exactly (edge e clockwise from the top, outward normal
at 90° − 60° e, notch 0.30 of the edge wide and 0.22 of the apothem deep, circumradius 0.42 of the quad).

---

## blast_door.glb (8,863 tris, 15 surfaces)

**Shape.** A dark riveted steel portal plate with an amber / black chevron band (pointing up at the centre) on
the lintel and a raised lip round the 1.6 × 2.4 opening. Left of the opening, the drum-lock box: a hollow dark
steel case with four shrouded windows in polished brass bezels (with brass reading pointers), four brass ring
icons, the T-handle in a recess below and the lamp in a brass bezel above. Behind the frame, the steel tunnel
lining runs to the hall face, where a steel angle flange finishes the doorway. The leaf is green-grey painted
steel: on the Gallery face, a riveted edge band, a horizontal seam strip and a 1.05 m relief of the Institute
mark (ring, meridian and ten ticks); on the hall face, a five-spoke handwheel (Ø 0.66) on a hub, dog bars and
four braces. Two hanger trolleys run in the top rail.

**Placement.** West (−3.70, 0, 0) yaw 90; east (3.70, 0, 0) yaw −90. Origin = the bay face at floor level.

| Node | Pivot / position (model) | Materials | Notes |
|---|---|---|---|
| `door_frame` | (0, 0, 0) | Steel_Dark, Enamel_Amber, Brass_Aged | plate x ±1.5, y 0 … 3.0, z 0 … 0.10 (+ lip to 0.12); box x −1.40 … −0.92, y 0.85 … 1.80, front plate z 0.232 … 0.240 with windows 0.084 × 0.046 at (−1.16, y_i); bezels to z 0.247; ring icons Ø 0.075 at x −0.99; top rail y 2.60 … 2.66 and the pocket housing x 0.83 … 2.85, z −0.47 … −0.03 (inward-facing box, hidden in the wall mass) |
| `IA_door_tunnel` | (0, 0, −0.40) | Steel_Dark | walls x ±0.80 … ±0.83, ceiling y 2.40 … 2.43, floor plates (y 0.012) with tread bars, z 0 … −0.80; **slots**: pocket side z −0.46 … −0.05 (leaf + handwheel), closed side z −0.34 … −0.05 (into a receiving channel to x −0.94); hall flange 0.10 wide at z −0.80 … −0.82 |
| `IA_blast_door` | (0, 0, −0.195) | Steel_Painted | leaf x ±0.9, y 0 … 2.55 (trolleys to 2.60), z −0.32 … −0.07; handwheel to z −0.44; **open = slide +1.9 local X** |
| `IA_drum_0..3` | (−1.16, 1.545 − 0.13 i, 0.19) | Brass_Aged, Steel_Dark | Ø 0.100 × 0.080 (+ hubs), knurled end rims, symbol band r 0.0485; symbols 0.034 high, flat dark-steel inlays bent onto the band, symbol s at `Basis(X, +60° s)·(0, 0, 1)`; **step = −60° about local +X** (checked in `blast_door_3.png`: drums set to 1 3 2 4 read ☾ ▲ ✦ ●) |
| `IA_drum_handle` | (−1.16, 0.98, 0.21) | Brass_Aged | boss on axis X, stem up 0.08, T-bar 0.076 at y 1.065; **pull = +45° about local +X** (the top tips out of the recess toward the player) |
| `drum_lamp` | (−1.16, 1.72, 0.25) | Enamel_Amber | dome jewel r 0.0145 to z 0.2595 |

QA (`blast_door*.png`, model local coords with a proxy concrete bay): hero (sealed, amber lamp); `drum_west` at
the start (all ☼); `drum_west` at the target with the handle pulled (lamp green); `blast_west` closed;
`blast_west` open (leaf in the pocket); `blast_west_hall` (the handwheel side). The doors also appear in the
Gallery renders.

---

## array_below.glb (5,466 tris, 11 surfaces)

| Node | Position | Materials | Notes |
|---|---|---|---|
| `shaft_throat` | (0, 0, 0) | Rock | bell mouth r 1.62 / y −0.10 → r 4.0 / y −1.20 (7 profile rings, 40 sectors); **steepest face 59.9° from vertical** (measured on the mesh; contract ≥ 50°) |
| `cavern` | (0, 0, 0) | Rock, Brass_Aged | inward-facing jittered dome r 4 → 14 down to the floor y −31 (22 sectors); brass: the throat's three hoops + 48 studs, ring pylons (8 under the two outer rings, 6 under the inner two), 8 floor spokes, the central dais |
| `ring_0..3` | (0, −30, 0) | Emissive_Lumen | tori r 7.0 / 5.4 / 3.8 / 2.2, tube r 0.225 (48 / 40 / 32 / 24 × 6 segments) |
| `ring_sym_0..3` | (−4.95, −29.70, 4.95), (3.82, −29.70, 3.82), (−2.69, −29.70, −2.69), (1.56, −29.70, −1.56) | Shader_Quad | 1.5 / 1.5 / 1.2 / 1.2 m quads facing +Y, UV corners (0,0)(1,0)(1,1)(0,1) with u → +X, v → −Z (checked from the mesh) |
| `array_center` | (0, −30, 0) | — | empty |
| `rise_top` | (0, 2.6, 0) | — | empty |

QA: `array_below.png` (from inside the cavern) and `array_below_2.png` (the `glass_floor` camera without the
glass) with dormant rings and the ring symbols of seed 0.

---

## shell_gallery.glb (10,492 tris, 12 surfaces)

**Shape.** A cold concrete drum: a 2.5 cm plinth, two pour-joint grooves (y 1.40, 3.05) and a stepped cornice
(to 0.14 proud at the top) swept along the inner face; the door bays are flat at x = ±3.70 for |z| ≤ 1.6 (with
the 3.4 cm return to the circle at z = ±1.6). Flat ceiling at 4.5 with 12 radial ribs (φ = 15° + 30° k, 0.18 ×
0.30) on corbels and a ring beam r 1.45 … 1.75 with a brass band underneath. Stone floor with brass inlay
circles at r 2.4 and 3.6, the glass disc in a brass L-rim with 24 rivets, a brass handrail ring (top y 1.0, a
lower rail at 0.45, 12 turned posts with flanged feet). Five brass uplight sconces (wall plate, arm, cup) with
glass chimneys. The shutter tunnel mouth has a brass frame on the drum face and a brass sill.

| Node | Position | Materials | Notes |
|---|---|---|---|
| `gallery_drum` | (0,0,0) | Concrete | openings: door bays |z| < 0.8, y < 2.4; shutter φ 38.05° … 59.17°, y 0.30 … 2.10; memorial arc φ −30° … 30° plain |
| `gallery_ceiling` | (0,0,0) | Concrete | y 4.5; ribs y 4.20 … 4.50; corbels y 3.95 … 4.20; ring beam bottom y 4.12 |
| `gallery_floor` | (0,0,0) | Stone | r 1.62 → the drum face (and the bays to x ±3.70) |
| `IA_glass_floor` | (0,0,0) | Glass | r 1.5, y −0.08 … 0 |
| `glass_rim` | (0,0,0) | Brass_Aged | rim r 1.49 … 1.62 (1 cm support ledge under the glass at y −0.082, top y 0.006); **also every other static brass part of the Gallery** (floor inlays, sconce bodies, shutter frame + sill, ring-beam band) |
| `gallery_rail` | (0,0,0) | Brass_Aged | ring r 1.75, top y 1.0; posts at φ = 15° + 30° k |
| `IA_tunnel_shutter` | (4.0, 0.30, −2.6) | Concrete | floor y 0.30, ceiling y 2.10, walls z −3.15 / −2.05, from the drum face (x 2.46 / 3.43) to x 4.5, two board-form lift lines |
| `lamp_glass_0..4` | at the bulbs (below) | Glass | φ 125°, 160°, 200°, 235°, 315° |
| `light_gallery_0..4` | (3.072, 2.76, 2.151), (1.283, 2.76, 3.524), (−1.283, 2.76, 3.524), (−3.072, 2.76, 2.151), (−2.652, 2.76, −2.652) | — | bulb centres (sconce wall points at y 2.7) |
| `echo_rail_mount` | (−2.05, 0, −0.40) | — | yaw 79 |
| `echo_strand_mount` | (−2.30, 0, 1.00) | — | yaw 40 |
| `echo_leyla_mount` | (2.30, 0, 1.00) | — | yaw −40 |
| `portal_w_g` / `portal_e_g` / `portal_shutter_g` | (−4.45, 1.2, 0) / (4.45, 1.2, 0) / (4.40, 1.2, −2.6) | — | yaw −90 / 90 / 90 (+Z toward −X / +X / +X) |

QA (`shell_gallery*.png`, both blast doors and `array_below` imported): `gallery`, `gallery_w`, `glass_floor`,
a high hero, `finale`, `blast_east`, `secret`.

---

## freight_lift.glb (6,597 tris, 10 surfaces)

**Shape.** Origin = the cage floor centre at lobby level, world (0, 0, 6.0). A dark steel deck (top y 0.25) with
welded tread bars; green-grey riveted panel walls north and south to 1.35 with two stiffeners and vertical bars
above to the roof; brass grab rails; dark angle corner posts; a roof frame at 2.6 with a crosshead, yoke, a 0.68 m
sheave and two ropes up the shaft to y 12; the hoist guide rails on the shaft walls (local z ±1.15) from y 2.75 to
12; painted lintels with brass level plates (raised dark "−2", U+2212) over both gates facing into the cage; gate
tracks and jambs; a frosted bulb in a wire guard.

| Node | Pivot (model) | Materials | Notes |
|---|---|---|---|
| `freight_cage` | (0,0,0) | Steel_Dark, Steel_Painted, Brass_Aged | static |
| `IA_gate_west` / `IA_gate_east` | (∓1.1, 0.25, −0.95) | Steel_Painted | 11 pickets, 3 tiers of X straps, top/bottom rails, rollers, a pull handle at the free end; lattice z −0.95 … +0.95, y 0.27 … 2.35. **Open = scale local Z to 0.15** (checked: `freight_lift_2.png` shows the east gate folded against its north post) |
| `IA_gate_lock_west` | (−1.0, 1.15, 0.92) | Brass_Aged, Steel_Dark | box 0.06 × 0.15 × 0.10 on a bracket to the south post, key slot on top, Strand's mark (ring + meridian, 0.062 high) inlaid on the face toward +X |
| `gate_key_mount_west` | lock + (0, 0.117, 0) → (−1.0, 1.267, 0.92) | — | child of the lock; basis maps item −Z (bow) → +Y and item +Y (face) → +X (euler XYZ 90°, 90°, 0°; quaternion (0.5, 0.5, −0.5, 0.5)); the blade tip sits ~3 cm inside the slot (`freight_lift_4.png` shows `key_strand` in place) |
| `IA_gate_lock_east` | (1.0, 1.15, 0.92) | Brass_Aged, Steel_Dark | Leyla's sign inlaid on the face toward −X |
| `gate_key_mount_east` | (1.0, 1.267, 0.92) | — | item −Z → +Y, item +Y → −X (euler 90°, −90°, 0°) |
| `cage_bulb` | (0, 2.36, 0) | Glass_Frosted | code emission |
| `cage_light` | (0, 2.36, 0) | — | empty |

QA: `lift_w` (west gate shut, Strand's key in its lock), `lift_e` (east gate folded open, Leyla's key), a hero
from the lobby with the west gate open, the west lock close-up.

---

## shell_lift.glb (5,404 tris, 9 surfaces)

| Node | Position | Materials | Notes |
|---|---|---|---|
| `lobby_floor` | (0,0,0) | Chequer | x ±6.6, z 4.7 … 7.4 at y 0, **plus the two bridge ramps** (x ±1.15 at y 0.25 → ±2.15 at y 0, z 5.2 … 6.8) with curbs and toe strips |
| `lobby_walls` | (0,0,0) | Concrete | plinth, lift lines at 1.2 / 2.4, cornice step; pilasters at x ±3.2 (both long walls), lintel bands over the passages; openings x [−6.3, −4.8] and [4.8, 6.3], y < 2.6 in the north wall |
| `lobby_ceiling` | (0,0,0) | Concrete | y 3.0 with the shaft opening x ±1.25, z 4.85 … 7.15, a 0.3 m reveal collar, beams at x ±1.25 … ±1.55 and ±3.2 |
| `lift_shaft` | (0,0,0) | Rock | four rock panels (displaced grid) y 3.3 … 12 and a rock cap at 12 |
| `IA_passage_w` / `IA_passage_e` | (∓5.55, 0, 4.35) | Steel_Dark | floor plate, side and ceiling linings, riveted angle frames on the hall face (z 4.0) and the lobby face (z 4.7) |
| `intro_shaft` | (0, 0, 6.0) | Rock, Steel_Dark | rock walls x ±1.45 and z 4.75 / 7.25, y −6 … 3 (relief ±0.07 m), guide rails north and south, ten caged bulkhead lamps (two columns of five at y −5.1, −3.3, −1.5, 0.3, 2.1, z 6.0) |
| `intro_bulbs` | (0, 0, 0) **local to `intro_shaft`** | Steel_Dark | the ten bulbs; **child of `intro_shaft`**, so sliding / hiding `intro_shaft` moves / hides them too |

QA: lobby hero, lobby looking west to the cage, the intro (`lift_w` camera, intro shaft slid +4.0 with lit
bulbs), looking up the shaft.

---

## shell_choir.glb (11,552 tris, 14 surfaces)

**Shape.** Board-formed concrete walls (one 0.15 m sawtooth board per step, a deeper pour-lift groove every
1.5 m) over a green-painted dado to 1.5 m with a painted cap line and a plinth; concrete pilasters 0.40 × 0.15
(north x −11.6 / −6.2, south x −9.95, east z −2.0 / +1.6) with riveted steel bearing caps (y 5.05 … 5.25); a
concrete floor with green walkway strips 0.08 wide (around the desk x −9.85 … −6.15, z −0.55 … 1.55; the rack and
bench front z −2.75; the switch-room front z 3.0 with returns to the wall; the transformer-bay limit x −11.6);
a concrete ceiling at 6.0 with two 0.4 × 0.58 beams along x at z −2.0 and 3.2 on haunches.

| Node | Materials | Notes |
|---|---|---|
| `choir_walls` | Concrete, Paint_Green | openings: east wall |z| < 0.8, y < 2.4 (tunnel mouth, finished by `blast_door`'s hall flange); south wall x −6.3 … −4.8, y < 2.6 (finished by `IA_passage_w`) |
| `choir_floor` | Concrete, Paint_Green | y 0 (strips at 0.003) |
| `choir_ceiling` | Concrete | y 6.0; beams y 5.42 … 6.0 |
| `catwalk` | Steel_Dark | deck x −13.0 … −12.0, top y 4.0, with the ladder opening x −12.95 … −12.45, z −4.0 … −3.40; tread bars; toe board on x −12.0 (to 4.12); edge channel; brackets with struts at z −3.85, −2.15, −0.45, 1.25, 2.75 (between the transformers; strut at x −12.45 is at y 3.71, above the 3.6 limit); handrail posts at z −3.95, −3.1, −2.1, −1.1, −0.1, 0.9, **1.9**, 2.9, 3.95 (x −12.03), rails at y 5.0 and 4.52; the **port_b mounting plate** 0.44 × 0.44 whose front plane passes through (−12.0, 4.55, 1.9) facing yaw 110 (normal (0.940, 0, −0.342)), clamped to the post; the ladder x −12.88 / −12.52, rungs every 0.30, stiles to y 5.0 |
| `gantry` | Steel_Dark | I-beam x −13.0 … −4.5 at z 1.9 (flanges y 5.45 … 5.47 and 5.73 … 5.75, 0.18 wide), web stiffeners, riveted corbels with struts at both walls; trolley at x −8.6 (four wheels on the bottom flange), drop plate to y 5.30, and the **port_c mounting plate** 0.42 × 0.42 in the port's back plane through (−8.6, 5.15, 1.9) (yaw 180, pitch +60: normal (0, −0.866, −0.5)) |
| `choir_trim` | Steel_Dark | cable trays at y 4.6 (north wall x −11.9 … −4.65, east wall z −3.9 … 3.9) with brackets and cables, conduits down to each lamp, pilaster caps, the six caged bulkhead lamp bodies (cast housing, three guard hoops, ring, junction box) |
| `lamp_glass_0..5` | Glass_Frosted | at the bulbs |
| `light_choir_0..5` | — | (−12.3, 3.4, −3.88), (−7.4, 3.4, −3.88), (−11.6, 3.4, 3.88), (−7.4, 3.4, 3.88), (−4.62, 3.4, −2.8), (−4.62, 3.4, 2.2) |
| `portal_w_c` | — | (−3.75, 1.2, 0), yaw 90 |

QA (`shell_choir*.png`, the west blast door, `shell_lift` and `freight_lift` imported): `choir`, `choir_s`,
`hall_start`, `port_b`, `port_c`, `blast_west_hall`, the catwalk / gantry.

---

## shell_nursery.glb (NURSERY_TRIS tris, 12 surfaces)

NURSERY_SECTION

---

## Deviations from the contract

1. **Surfaces over the cap in three models** (all other caps met):
   - `shell_gallery` 12 (cap 10): the five `lamp_glass_*` objects alone are 5; the other seven named objects are
     one surface each (all static brass of the Gallery is merged into `glass_rim`; the sconce bodies and floor
     inlays would otherwise have added a brass surface to `gallery_drum` / `gallery_floor`).
   - `array_below` 11 (cap 10): 4 rings + 4 symbol quads + `shaft_throat` + `cavern` = 10 with one material each;
     the brass (throat hoops, pylons, spokes, dais) needs one more surface. It lives in `cavern`, so
     `shaft_throat` stays rock only.
   - `shell_lift` 9 (cap 8): `intro_shaft` needs rock + steel (its lamp cages and rails), and `intro_bulbs` must be
     separate. During normal play the lobby draws 7 surfaces; during the intro (lobby hidden) 3.
2. **Bridge ramps moved from `freight_lift` to `shell_lift`'s `lobby_floor`** (chequer plate). As part of the
   cage they would have stuck through `intro_shaft`'s rock walls (x ±1.45) during the descent; in the lobby they
   hide with it. `freight_lift` instead carries the hoist guide rails up the shaft (static), so `lift_shaft` is
   rock only.
3. **`intro_bulbs` is a child of `intro_shaft`** (the contract does not say), so the code's slide and hide of
   `intro_shaft` take the bulbs along.
4. **Drum inlays use a second material.** "Every `IA_*` part uses one material unless its line says otherwise":
   the drum line asks for dark-steel symbol inlays on brass drums, so each `IA_drum_<i>` has Brass_Aged +
   Steel_Dark (8 surfaces for the four drums). To stay at 15 surfaces, `door_frame` is dark steel + brass + amber
   (the black chevron stripes are Steel_Dark) and the leaf is one material (Steel_Painted, the mark in relief).
   The gate locks likewise use brass + dark steel for the inlaid mark / sign.
5. **Gallery rim and the `glass_floor` view.** The contract's check (the glass's south edge at 17.6° against a
   16° half-FOV) only looks straight south. At a 3:2 (and wider phone) aspect the rim's south-east and
   south-west arcs (x ≈ ±0.6, z ≈ 1.45) fall inside the frame's bottom corners: measured by projecting the GLB
   vertices into the 960 × 640 camera, the rim reaches the bottom edge there (`shell_gallery_3.png`). The support
   ledge under the glass was trimmed to 1 cm (r 1.49) so nothing of the rim shows *inside* the glass circle. If the
   corners must be clean, the view needs a narrower FOV or a camera nearer the glass.
6. **Drum wall outer face** (r 4.5) is not modelled: every opening through the drum is lined (door tunnels by
   `blast_door`, the shutter tunnel by `IA_tunnel_shutter`), so no outer face is visible.
7. **`mrlib.PREVIEW` not edited**: the new slots' preview values are injected at run time by
   `lib_ch3_symbols` (the brief forbids editing existing `tools/blender/*.py`).
8. **Door bays**: the flat bay face meets the circle with a 3.4 cm return at z = ±1.6 (the circle is at x 3.666
   there, the bay at 3.70), as the contract's numbers imply.

## Notes for integration

- **Shadow names** (§1.5): `gallery_drum` is not `*_walls`, so it casts by name unless `tune_shadows` treats it;
  `glass_rim` carries the sconce bodies (it should not need to cast).
- `blast_door`: the code should slide `IA_blast_door` along its local +X (pocket side). The tunnel's pocket-side
  slot also clears the hall-side handwheel (to z −0.44).
- `freight_lift` gates fold by local Z scale about their origin; nothing else is parented to them.
- `gate_key_mount_*` are children of the lock boxes (lock local (0, 0.117, 0)).
- `shell_lift`: `intro_shaft` origin (0, 0, 6.0); slide it +Y (0 … 9). The intro bulbs share the M_Steel_Dark
  resource with the lamp cages: give `intro_bulbs` its own material override before turning emission on.
- `array_below`: the code gives `ring_sym_<r>` an unshaded emissive material per symbol (`sym_<name>.png`).
- Every lamp glass / bulb / jewel uses its glass or enamel slot (no emissive slot), as §0 asks.
- Godot `.import` files for the new textures were made by the director's import; this group did not run Godot.
