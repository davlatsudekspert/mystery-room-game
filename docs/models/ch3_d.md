# Chapter 3 group D: the Nursery (measured results)

Contract: `docs/models/ch3.md` §0, §1 (placement, receptors 0..2, the seed library's front plane), §2 (views), §6,
§9–§11, §13, §14. Models: `autoclave`, `autoclave_dead`, `growth_log`, `seed_library`, `growth_chart`, `prism_bench`,
`spectral_seal_door`. Scripts: `tools/blender/models/<name>.py`; shared helpers in `tools/blender/lib_ch3_d.py` (on
top of `lib_ch3_a.py` and the libraries it re-exports; none of the older libraries were edited); build list
`tools/blender/build_lists/ch3_d.txt`.

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [--shots=1,2,...]
MR_ECHO_Z=0.95 blender -b --factory-startup -P tools/blender/models/autoclave_dead.py -- --measure --shots=0
```

**Pipeline.** Every script builds in Godot axes (the group-A "G-frame"), converts to Blender axes before parenting,
exports a lean GLB to `game/assets/models/<name>.glb`, then **re-reads the GLB** and checks the required node names,
parents, model-space positions (1 mm), identity rest rotations, mount rotations, triangles, surfaces (mesh nodes ×
primitives) and material slots against §13, and runs `check_glb_names.py`. A `--no-render` run does only that;
otherwise it renders the QA shots: Cycles, 32 samples, 960 × 640, 2 threads, cameras from the §2 views (Godot
position, target and vertical FOV), `shell_nursery.glb` and the neighbouring GLBs imported. Shader quads carry the
seed-0 previews from `qa/blender/ch3/preview/`; lamps, jewels and the prism lamp get a QA-only emissive override
(the code turns emission on). Blender renders only, never Godot screenshots.

All coordinates are **Godot, model-local, metres**; models face +Z; angles follow §0 (positive = counter-clockwise
looking down the +axis toward the origin).

## Summary

| Model | Tris (budget) | Surfaces (cap) | Slots | GLB | QA renders (`qa/blender/ch3/`) |
|---|---|---|---|---|---|
| `autoclave` | 8,979 (9,000) | 12 (12) | 4 | `game/assets/models/autoclave.glb` | `autoclave.png`, `_2` … `_10` |
| `autoclave_dead` (×3) | 3,397 (3,500) | 3 (3) | 3 | `game/assets/models/autoclave_dead.glb` | `autoclave_dead.png`, `_2` … `_6` |
| `growth_log` | 486 (800) | 4 (4) | 4 | `game/assets/models/growth_log.glb` | `growth_log.png`, `_2`, `_3` |
| `seed_library` | 6,518 (7,000) | 17 (17) | 4 | `game/assets/models/seed_library.glb` | `seed_library.png`, `_2` … `_8` |
| `growth_chart` | (to fill) (800) | (3) | 3 | `game/assets/models/growth_chart.glb` | `growth_chart.png`, `_2`, `_3` |
| `prism_bench` | (to fill) (5,000) | (12) | 4 | `game/assets/models/prism_bench.glb` | `prism_bench.png`, `_2` … `_6` |
| `spectral_seal_door` | (to fill) (5,000) | (7) | 4 | `game/assets/models/spectral_seal_door.glb` | `spectral_seal_door.png`, `_2` … `_6` |

`check_glb_names.py` passes on all seven GLBs. Surfaces = mesh nodes × primitives in the GLB (draw calls before
shadows).

---

## autoclave.glb (8,979 tris, 12 surfaces)

**Shape.** A chrome pressure vessel Ø 0.85 (dished bottom at 0.285, cylinder y 0.36 … 1.95, dome to 2.10, a bolted
girth flange at 1.88, three lagging bands with buckles at the back, a top nozzle meeting the shell's frosted drop at
(0, 2.13, 0), a safety valve with lever and weight on the dome) on a dark steel frame (four square legs on foot
plates, a ring girder, low rails, lugs welded to the shell), steam / vent / drain pipes back to the wall (local
z −0.5), the manway neck and bolted flange with the hinge block, a pressure gauge (needle fixed) on the left, a brass
name plate with the Institute mark, the brass log hook on the right, and the control pedestal in front right with
the brass cam drum, its bearings, the lever quadrant, the remelt escutcheon (flame cut-out) and the lamp bezel.
Placement (8.4, 0, −3.5), yaw 0; footprint 1.00 × 1.00 (frame feet to ±0.387, pipes to z −0.5).

| Node | Pivot / position | Materials | Notes |
|---|---|---|---|
| `autoclave_body` | (0, 0, 0) | Chrome, Steel_Dark, Brass_Aged, Glass | static; the gauge glass is the Glass primitive; chamber r 0.20 to z 0.10 behind the flange, with the brass seat stand under `chamber_mount` |
| `IA_ac_door` | (−0.21, 1.20, 0.46) | Chrome | round door Ø 0.42 centred (0, 1.20, 0.45): ring with the window hole, hinge arm and knuckle, latch boss with a lever grip, 6 bolts; **open = −110° about local +Y** (`autoclave_3.png`, `_9`) |
| `growth_window` | (0, 1.20, 0.454) (child of the door) | Glass | porthole Ø 0.244; code: frost and the inner glow (`autoclave_7.png`) |
| `chamber_mount` | (0, 1.08, 0.30) | — | up +Y; the seed's collar bottom (origin − 0.0088, ch3_g.md) sits on the seat top y 1.0712. `nursery_crystal` (bottom −0.0569) stands 0.0481 higher on the same seat: the QA renders offset it by that |
| `IA_peg_0..2` | (0.20 / 0.30 / 0.40, 1.05, 0.62) | Brass_Aged | knurled pegs on the drum axis X; rest = hole 1 (30° above the front horizontal); **hole p = −24° × (p − 1) about local +X** (`autoclave_4.png`: 5-2-4) |
| `IA_start_lever` | (0.52, 0.95, 0.62) | Brass_Aged | boss, 0.25 arm, ball knob; **pull = +60° about local +X** against the brass quadrant (end stops at 0° and 60°) |
| `IA_remelt` | (0.20, 0.80, 0.81) | Brass_Aged | button Ø 0.033 with a flame relief; **press = −0.006 along local Z** (`autoclave_8.png`) |
| `ac_lamp` | (0.42, 0.97, 0.75) | Glass | jewel Ø 0.025; code: amber / green / red |
| `log_mount` | (0.30, 1.66, 0.40) | — | the hook pin's top; `growth_log` hangs with identity (its hanging hole's top edge is its origin) |
| `steam_origin` | (0, 1.45, 0.47) | — | empty |

The cam drum: brass Ø 0.16 × 0.30 on the pedestal (x 0.10 … 0.50, z 0.45 … 0.80, top 0.95), axis X through
(0.30, 1.05, 0.62); three columns (dark divider rings at x 0.25, 0.35) with six holes each at 30° + 24° (p − 1) above
the front horizontal, each hole marked with 1–6 dice pips to its right.

QA: `autoclave.png` (hero, log on its hook, lamp green), `_2` (the `autoclave` view, start state), `_3` (door open,
the seed on the seat), `_4` (`cam_drum` view at the target 5-2-4, lever pulled, lamp amber), `_5` (`cam_drum` at
the start), `_6` (`growth_log` view), `_7` (`grow` view: the clear crystal behind the glowing window), `_8` (remelt
pressed), `_9` (open door from the side, the grown crystal), `_10` (`nursery` root view).

---

## autoclave_dead.glb (3,397 tris, 3 surfaces, 3 slots)

The same silhouette as the autoclave without the pedestal, **one mesh object `autoclave_dead`** (M_Chrome,
M_Steel_Dark, M_Glass_Frosted): the vessel on its frame (the shared `lib_ch3_d.autoclave_shell(lite=True)`: a
9-ring vessel profile, 16-segment neck / flange / chamber, 16-segment bands and girder, sharp frame boxes, four
flange and six girth bolts, no dome lever), the door baked **ajar by 10°** (`ac_door(lite=True)`, a 5-ring section)
with a frosted dead window, a dead gauge, a drain line with a hand-wheel valve, rime on the top nozzle, a rime ring on
the valve and eight icicles under the girth flange, a steel name plate with the Institute mark in chrome. Bounds
(−0.459, 0, −0.50) … (0.459, 2.166, 0.696). Ids `dead_0..2` at (9.65 / 10.9 / 12.15, 0, −3.5).

| Node | Position | Notes |
|---|---|---|
| `autoclave_dead` | (0, 0, 0) | static, 3 primitives |
| **`echo_mount`** | **(0, 0, 0.95)**, rotation (0, 180, 0): +Z faces −Z (the vessel) | contract (0, 0, 0.62); measured, see below. `tech_a` / `tech_b` (`echo_technicians.glb`, origin between the feet) parent here with identity |

**Why 0.95.** The technicians were posed by group H against proxy boxes; against the real Ø 0.85 vessel (front at
z 0.425, frame to 0.468) the figures intersect it at the contract's mount. Measured with the exported meshes
(BVH triangle overlap, `--measure`): tech_a (standing, clipboard held 0.41 m ahead of her origin, reading the gauge)
vs the dead autoclave: **1,044** intersecting triangle pairs at z 0.62, **331** at 0.80, **116** at 0.88 (her hands
and clipboard against the ajar door's free edge), **0 at 0.95** (nearest vertex 2.7 cm). tech_b (crouching, right
hand on the valve wheel) at 0.95: 198 pairs, all inside a 7 × 3 × 4 cm box at the hand-wheel's rim top (world
(10.905 … 10.973, 0.405 … 0.431, −2.836 … −2.797) at `dead_1`) — his fingers closed round the rim, the grip group H
built (rim top 0.7 cm from the palm). Nothing else of him touches the model.

**Contact props for the technicians** (figure frame → model with the mount at 0.95, 180° about Y):
- tech_b's hand-wheel centre (−0.04, 0.40, 0.26) → **(0.04, 0.40, 0.69)**: a chrome wheel Ø 0.08 (rim tube Ø 0.01,
  four spokes, hub) facing +Z on a steel angle valve (body r 0.032 at z 0.635, bonnet, stem) fed by a drain line from
  the vessel at y 0.40; the outlet drops to a floor gully at z 0.635.
- tech_a's gaze: she looks 26° down through (−0.05, 1.45, 0.20) in her frame (ch3_h.md). With the mount at 0.95 that
  line meets the vessel shell 17 cm below a gauge on the shell, so the dead gauge sits on a **siphon stand-off
  stub**: a chrome Ø 0.02 stub from the shell at (0.08, 1.45) to z 0.654, a steel strut back to the shell, the
  gauge case (Ø 0.128, r 0.064) with its frosted glass face at **z 0.6865**, 0.26 m in front of her origin, centre
  (0.08, 1.45) — slightly to her right, on her line of sight (`autoclave_dead_3.png`). Its needle rests below zero.

QA: `autoclave_dead.png` (hero, the row of three with the working autoclave), `_2` (the `port_a_mem` view with
`tech_a` at `dead_0` and `tech_b` at `dead_1`, ghost look), `_3` (tech_a at the gauge from the side), `_4` (tech_b's
hand on the wheel), `_5` (the `nursery_w` root view), `_6` (the ajar door, frosted window and gauge, close).

---

## growth_log.glb (486 tris, 4 surfaces)

A walnut-veneer clipboard 0.23 × 0.32 × 0.006 with rounded corners and a Ø 0.010 hanging hole, a brass spring clip
(riveted base plate, rolled hinge, jaw over the page top, a lever tab with a hole), Leyla's page and the sketch quad.
**Origin = the hook point = the top edge of the hanging hole**; the board hangs down −Y (top edge 0.012 above the
origin, bottom at −0.308), face +Z. On the autoclave's `log_mount` with identity.

| Node | Position | Materials | Notes |
|---|---|---|---|
| `IA_growth_log` | (0, 0, 0) | Wood_Panel | the board, the tap target |
| `log_clip` | (0, −0.036, 0.0065) (child) | Brass_Aged | the clip, 290 tris |
| `log_page` | (0, −0.160, 0.0032) (child) | Decal_GrowthLog | 0.21 × 0.28 quad, bottom edge y −0.300; UV (0,0) bottom-left → (1,1) top-right, u → +X, v → +Y (checked from the mesh). `DecalLoc` swaps `growth_log_ru` / `_uz` |
| `log_sketch` | (0, −0.1992, 0.0037) (child) | Shader_Quad | 0.09 × 0.09 quad 0.5 mm above the page, centred on page (u 0.50, v 0.36) = the blank square's centre; UV 0..1; the code's `hex_glyph` shader (style 1, `v_sketch`), alpha 0 outside the hexagon so the page's printed arrow shows round it |

QA: `growth_log.png` (hero with the seed-0 sketch on the page), `_2` (straight on at the `growth_log` view distance),
`_3` (clip and hole). It also hangs on the autoclave in `autoclave.png`, `_2`, `_3`, `_6`.

---

## seed_library.glb (6,518 tris, 17 surfaces)

**Shape.** A walnut cabinet 1.50 w × 1.75 h × 0.45 d on a recessed plinth: the lower cupboard with two panelled
doors and brass pulls, a waist ledge with a velvet inset and a brass edge, the drawer face (y 0.845 … 1.70) with 12
openings in brass frames, bays with shelves and dividers behind them, raised fields on the sides, a stepped cornice,
and on top a gallery board with a velvet inset and nine turned walnut seed jars with brass lids. Carcass bounds
(−0.766, 0, 0) … (0.766, 1.93, 0.508). Wall-mounted at (13.0, 0, −0.6), yaw −90: the drawer-front plane z 0.45 is
world **x 12.55**; the carcass spans world z −1.35 … 0.15 (the §1.2 front plane), the twelve fronts z −1.245 … 0.045
(model +X → world +Z at yaw −90).

| Node | Pivot / position | Materials | Notes |
|---|---|---|---|
| `seed_library` | (0, 0, 0) | Wood_Walnut, Brass_Aged, Velvet | static |
| `IA_seed_drawer_<i>` (i = 4 r + c) | (x_c, y_r, 0.45), x_c = (c − 1.5) × 0.33, y_r = 1.50 − 0.26 r | Wood_Walnut | drawer box 0.30 × 0.22 × 0.40: front 18 mm, lower sides and back, a turned knob at y_r − 0.075 (to z 0.482), the turned seed cup inside; **open = slide +0.24 along local +Z** (`seed_library_2.png`) |
| `seed_mount_<i>` | (0, −0.05, **−0.22**) from the drawer pivot (child) | — | up +Y; `seed_crystal` stands in the cup (seat 0.0088 below the mount = the collar bottom). Contract −0.12: moved back, see Deviations |
| `glyph_panel` | (0, 0, 0) | Shader_Quad | ONE mesh of 12 quads 0.13 × 0.13 at (x_c, y_r + 0.02, 0.452); quad i's UVs cover u ∈ [c/4, (c + 1)/4], v ∈ [(2 − r)/3, (3 − r)/3] (read back from the mesh: the top-left quad at (−0.495, 1.52) has UV min (0, 0.667), the bottom-right at (0.495, 1.00) has (0.75, 0)) |
| `glyph_open` | (0, 0.02, 0.0025) from drawer 0's pivot (child of `IA_seed_drawer_0`) | Shader_Quad | one 0.13 × 0.13 quad, UV 0..1, origin at its centre; the code reparents it to the open drawer and sets its transform to (0, 0.02, 0.002) − AABB centre, so it rides on that drawer's front at the panel's cell position |
| `echo_touch_mount_<c>` | (x_c + 0.40, 0, 0.87), rotation (0, 180, 0) | — | Leyla faces the library; her `pose_touch_<r>` left middle fingertip (+0.40, y_r, +0.42 in her frame) lands on drawer (r, c)'s front |

**Touch check** (fingertip = the pose's most forward left-hand vertex, library-local, vs the drawer front centre):
`pose_touch_1` at column 2 → (+0.162, +1.2375, +0.4504): 0.3 cm left, 0.2 cm low, 0.4 mm in front of the front
plane; `pose_touch_0` at column 0 → (−0.4938, +1.5012, +0.4496): 0.1 cm right, 0.1 cm high, 0.4 mm behind;
`pose_touch_2` at column 3 → (+0.4924, +0.9813, +0.4497): 0.3 cm left, 0.1 cm high, 0.3 mm behind. All three touch
the glyph plate of their drawer (`seed_library_5/6/7.png`).

F_i (the `seed_drawer` view) = library-local (x_c, y_r, 0.69) once open; the view's camera F_i + (−0.30, 0.36, 0)
is world −X = in front of the open front.

QA: `seed_library.png` (the `seed_library` view, closed, the 12 seed-0 glyphs), `_2` (the `seed_drawer` view on
drawer 6 = row 1 column 2: `glyph_open` on its front, cell 6 blanked on the panel, the seed in its cup), `_3` (hero
with drawer 6 open), `_4` (the `seed_library` view with Leyla's `pose_touch_1` at `echo_touch_mount_2`: the leave
path's echo on drawer 6), `_5` / `_6` / `_7` (touch close-ups rows 0 / 2 / 1), `_8` (drawer 6 open from the side).

---

## growth_chart.glb

(to fill)

---

## prism_bench.glb

(to fill)

---

## spectral_seal_door.glb

(to fill)

---

## Deviations from the contract and choices

(to fill: the full list is written once the three remaining models are measured; the entries so far:)

1. **`autoclave_dead` `echo_mount` at (0, 0, 0.95)** instead of (0, 0, 0.62): the contract's point puts the
   technicians inside the Ø 0.85 vessel and its frame (measured above). The code takes the mount from the GLB
   (`part("dead_0", "echo_mount")`); `UndergroundData.MOUNT_FALLBACK` still holds the contract's z −2.88 for
   `tech_a` / `tech_b` and should read **z −2.55** (= −3.5 + 0.95) if the fallback is ever used.
2. **Dead gauge on a stand-off stub** (face 0.26 m in front of the vessel) so tech_a's fixed gaze line meets it.
3. **`seed_mount_<i>` 0.22 behind the drawer front** instead of 0.12: from the §2 `seed_drawer` camera the sight
   line over the 0.22 m drawer front's top edge reaches the seed's height only 0.173 behind the front; at 0.12 the
   seed is hidden and `Item_seed_<i>` cannot be tapped; at 0.22 its top clears the edge by 2.3 cm and its base by
   8 mm (`seed_library_2.png`). The code reads the mount from the GLB; the `seed_drawer` view is unchanged.
4. **`glyph_open` is a child of `IA_seed_drawer_0`** in the GLB (the contract leaves its parent open); the code
   reparents it anyway.
5. **`autoclave_dead` lite geometry** differs from the working autoclave in detail (fewer segments, bolts and the
   dome lever omitted) to meet 3,500 tris; the silhouette, bands, flange, frame and pipes are the same.

## Notes for integration

- `growth_log`'s origin is the top of its hanging hole: parent it to `log_mount` with identity.
- `seed_library`: slide `IA_seed_drawer_<i>` +0.24 along local Z; `seed_mount_<i>` and `glyph_open` follow their
  drawers. The glyph panel's `hidden` cell must be the open drawer's index, else its static quad shows inside the open
  box (`seed_library_8.png` shows the blanked case).
- `autoclave_dead`: `tech_a` at `dead_0`, `tech_b` at `dead_1`, both with identity under `echo_mount`.
