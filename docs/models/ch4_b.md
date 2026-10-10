# Chapter 4 group B: the bridge desk (measured results)

Contract: `docs/models/ch4.md` §0, §1, §2 (views), §4, §10, §11, §12. Models: `master_desk`, `master_lever`, `keeper_knob`, `handwheel`, `panel0`.
Scripts: `tools/blender/models/<name>.py`; helpers in `tools/blender/lib_ch4.py` and `tools/blender/lib_ch4_numerals.py`; build list
`tools/blender/build_lists/ch4_b.txt`. Same pipeline and QA scene as group A (`docs/models/ch4_a.md`): G-frame build, lean GLB, re-read and
verify against §11, Cycles 32 samples 960 × 640, the model under test as built plus `shell_hall`, `bridge` and `shell_lift4` imported, the §1.5 lights
as QA lights. Blender renders only.

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [--shots=1,2,...]
```

QA stand-ins (not exported): the desk wing / console boxes for `master_lever` and `keeper_knob`; for `master_desk` the real `master_lever`, `keeper_knob`
and four `handwheel` GLBs at their mounts; a seed-0 oscillograph image (`qa/blender/ch4/preview/osc_screen.png`) and strip chart image
(`preview/chart_paper.png`, pen marks at the canonical Night minutes 4, 5, 6) on the two shader quads.

## Summary

| Model | Tris (budget) | Surfaces (cap) | Slots | GLB | QA renders (`qa/blender/ch4/`) |
|---|---|---|---|---|---|
| `master_desk` | 7,063 (12,000) | 8 (8) | 4 | `game/assets/models/master_desk.glb` | `master_desk.png`, `_2`, `_3`, `_4` |
| `master_lever` | 1,248 (3,000) | 2 (2) | 2 | `game/assets/models/master_lever.glb` | `master_lever.png`, `_2` |
| `keeper_knob` | 2,028 (4,500) | 4 (4) | 3 | `game/assets/models/keeper_knob.glb` | `keeper_knob.png`, `_2` |
| `handwheel` (×4) | 2,787 (3,500) | 2 (2) | 2 | `game/assets/models/handwheel.glb` | `handwheel.png`, `_2` |
| `panel0` | 9,908 (10,000) | 33 (40; ≤ 20 drawn) | 4 | `game/assets/models/panel0.glb` | `panel0.png`, `_2` |
| **Group B in the `bridge` view** | desk 7,063 + lever 1,248 + keeper 2,028 + 4 × 2,787 | 8 + 2 + 4 + 4 × 2 = **22** | | | |

`check_glb_names.py` passes on all five GLBs. With group A's 25 placed surfaces the bridge-level part of the `bridge` view is 8 (hall) + 5 (bridge)
+ 22 = **35 surfaces**, as planned in §11.2 (the hall's other groups are group C onward). `panel0` is not drawn in the `bridge` view (it is under the bridge, in
group P); in the `panel0` view the zone has 33 surfaces, of which the 20 traces draw only where `v_panel` = 1 (8 to 14 dots).

Conventions used on this page: the **desk frame** is the `master_desk` local frame (origin = deck level at the footprint centre, +Z toward the operator).
A point on the slope is **P(s, x) = (x, 0.95 + 0.6189 s, 0.46 − 0.7855 s)** (s along the slope from the front edge, 0 … 0.84), with up-normal
**n = (0, 0.7855, 0.6189)**.

---

## master_desk.glb (7,063 tris, 8 surfaces)

Body x ±1.55 (kick strip ±1.50), z −0.45 … 0.46, y 0 … 1.47 (the chart drum reaches 1.65). Wings flat at y = 0.95; the console block x −0.80 … 1.00 slopes
from the front edge (z 0.46, y 0.95) to (z −0.20, y 1.47) at 38.2°, then a back shelf at y = 1.47. Bounds (model space): x ±1.562, y 0 … 1.652,
z −0.45 … 0.55 (the jog wheel projects to 0.61).

| Node | Material(s) | Tris | Pivot / notes |
|---|---|---|---|
| `master_desk` | `M_Steel_Painted` + `M_Brass_Aged` + `M_Bakelite` (3 surfaces) | 3,896 | Cabinet, three raised front panels, rivets, brass nosing and kick strip. **Dial**: bezel Ø 0.64, black bakelite face Ø 0.57 at P(0.5, 0) = (0, 1.2595, 0.0673), eight station numerals **0–7** at r 0.185 (clockwise −140° + 40° p from 12 o'clock), major ticks at r 0.225 – 0.275 and two minor ticks between, the legend **03:1** (0.036 high) under the hub. **Bay frame** and bakelite recess at P(0.30, −0.62). **Chart frame** (0.46 × 0.56) with the minute numerals **0–7** in its lower border, and the static paper roll drum at (0.66, 1.56, −0.33) on the back shelf. The jog wheel's two bracket cheeks at x = ±0.085 |
| `chrono_hand` | `M_Brass_Aged` | 175 | **Origin (0, 1.2675, 0.0543)** = the dial centre + 0.016 n. Built lying in the slope, tip at 12 o'clock (up the slope), tail ball behind the hub. Turn about **n** (the slope normal), position p = (140° − 40° p) counter-clockwise seen from the front of the dial. Identity = pointing at 12 o'clock (between stations 3 and 4) |
| `IA_scrub` | `M_Brass_Aged` | 560 | Knurled jog wheel r 0.12 × 0.10 wide, **origin (0, 1.07, 0.49), axis +X**, axle and end caps. Position p = **−45° p about +X** (the top turns away from the operator). Bounds y 0.952 … 1.188, z 0.37 … 0.61 |
| `IA_chronometer` | `M_Brass_Aged` | 2,224 | **Origin = the bay centre P(0.30, −0.62) = (−0.62, 1.1357, 0.2243).** Movement plate 0.264 × 0.184, three gears (22, 12 and 16 teeth), posts, a bridge bar, and the **empty pawl seat** (a ring boss r 0.012 – 0.022 at in-plane (0.075, −0.012) with a spring post). Everything lies ≤ 0.026 above the slope |
| `chrono_plate` | `M_Brass_Aged` | 206 | The bay's cover: lid 0.28 × 0.20 at 0.030 – 0.042 above the slope on a skirt, a pull knob, a hinge barrel. **Origin = the hinge (−0.62, 1.1976, 0.1458)** on the bay's upper edge; **baked OPEN (−100° from flat)**, identity at rest. Close it with **+100° about +X** after `pawl_fitted` |
| `chart_paper` | `M_Shader_Quad` | 2 | 0.40 × 0.46 centred at P(0.475, 0.66) + 0.003 n = (0.66, 1.244, 0.087) (the opening of the chart frame). **UV 0..1**: u across the width (the minutes 0..7 left → right, 0.05 each, column i centred at x = 0.46 + 0.05 (i + 0.5)), v up the slope. The numerals in the frame's lower border sit under the columns. Bounds x 0.46 … 0.86 |

Empties (desk frame): `pawl_mount` (−0.545, 1.142, 0.2421) rotated **(38.2°, 0, 0)** (the slope normal; the `reverse_pawl` item lies flat on the seat); `keeper_mount`
(−1.12, 0.95, 0) and `lever_mount` (1.28, 0.95, 0), identity; `echo_mount_strand` (1.12, 0, 0.78) rotation (0, 180, 0); `desk_light` (0, 1.9, 0.5).

Notes for the scene:
- Turn `chrono_hand` about the **slope normal**, not a world axis: `hand.transform = hand.transform.rotated_local(n_local, ...)` with `n = Vector3(0, 0.7855, 0.6189)`
  (the node's origin is at the dial centre, so a rotation about n through the origin is right).
- The chart's pen mark, the trace and the minutes of `v_night` are drawn by the shader on `chart_paper`; the drum and the pen are static meshes.
- Closed cover: the lid's underside clears the movement by 4 mm (`master_desk_4.png`).
- The desk's top is the chart drum at y 1.65 (world 4.15), under the `bridge` camera (world y 4.4) so the hall stays visible over it.
- QA renders: `master_desk.png` the `desk` view (keeper at 7, dial at 03:14, jog wheel turned 4 stops, the open bay); `_2` the `chronometer` view; `_3` the bay open (the
  movement and the empty seat); `_4` the bay closed.

## master_lever.glb (1,248 tris, 2 surfaces)

Origin = the unit's base centre on the wing pad. Bounds: body x ±0.20, y 0 … 0.457, z ±0.275.

| Node | Material | Tris | Pivot / notes |
|---|---|---|---|
| `master_lever_body` | `M_Steel_Painted` | 400 | Base plate 0.40 × 0.55 × 0.03 with four bolts, two cheek plates (x ±0.07 … 0.095) whose lobe is a quadrant of radius 0.19 about the pivot, and an upper stop bar at 80° (−0.085, 0.437) |
| `IA_master_lever` | `M_Brass_Aged` | 848 | **Origin = the pivot (0, 0.24, −0.12).** Hub with bolt heads, flat blade 0.04 × 0.018 × 0.40, a knurled turned grip (0.38 – 0.545 from the pivot), a counterweight tail 0.14 with a ball. **Rest = down: the lever points +Z, 6° below horizontal** (baked; node rotation identity). **Lifted = −80° about +X.** Bounds y 0.155 … 0.272, z −0.334 … 0.422 |

Notes: the lever overhangs the pad by 0.15 at the front; the tip sits at (0, 0.18, 0.42) at rest, 0.28 above the pad. The 6° tilt was baked about the pivot before the origin moved
(a rotation applied after `K.part` would pivot about the wrong point). QA: `master_lever.png` at rest, `_2` lifted (−80°).

## keeper_knob.glb (2,028 tris, 4 surfaces)

Origin = the box's base centre on the wing pad. Box x ±0.31, z ±0.25, y 0 … 0.25 (foot ±0.33 × ±0.27); the leaning panel's top is y 0.57. Bounds x ±0.33, y 0 … 0.57, z ±0.27.

| Node | Material | Tris | Pivot / notes |
|---|---|---|---|
| `keeper_body` | `M_Steel_Painted` + `M_Brass_Aged` (2 surfaces) | 1,600 | The box, rivets, the raised collar plate (r 0.115 at (0, 0.125, 0.25)) with **13 brass ticks** (long every third) at −135° + 22.5° p clockwise from 12 o'clock and the numerals **0, 3, 6, 9, 12** at r 0.082, the panel leaning back 25° (centre (0, 0.404, −0.06), 0.58 × 0.34, normal (0, 0.4226, 0.9063)) with two side cheeks, the brass screen bezel (r 0.122 – 0.150) and four screws |
| `osc_screen` | `M_Shader_Quad` | 32 | Disc r 0.12, centre (0, 0.404, −0.06) + 0.0165 along the panel normal; **UV 0..1 over the bounding square** (u → +X, v up the panel). The beat envelope shader (`osc_wave`) draws on it |
| `IA_keeper` | `M_Brass_Aged` | 396 | **Origin (0, 0.125, 0.256)**, axis +Z. Knurled knob r 0.07 × 0.058 with a pointer ridge and dot, pointing at 12 o'clock at identity. Position p (0..12) = **(135° − 22.5° p) about +Z** (0 lower left … 12 lower right). Bounds z 0.256 … 0.32 |

Notes: the design's pilot lamp is dropped (a fifth surface; `keeper_on` shows as a flat beat on the screen). `K.screw` adds an `M_Steel_Dark` slot, so the screws are
domed rivets here. QA: `keeper_knob.png` the unit as seen from the operator with the knob at 7 and the seed-0 beat; `_2` the knob at 0 from the front-left.

## handwheel.glb (2,787 tris, 2 surfaces; four instances)

Origin = deck level at the footprint centre (the base plate is 0.46 × 0.46); front +Z toward the player. Bounds: base x ±0.34, y 0 … 1.652, z ±0.23; wheel x ±0.265, y 1.035 … 1.571, z 0.165 … 0.331.

| Node | Material | Tris | Pivot / notes |
|---|---|---|---|
| `handwheel_base` | `M_Steel_Painted` | 1,691 | Base plate with four bolts, a tapered column (z −0.05, to y 1.07), the head block, the **dial plate** (r 0.34, y 1.30, z 0.11 – 0.135) with 8 ticks at r 0.315 – 0.335, the numerals **1–8** (0.045 high, upright, at r 0.285, clockwise from 12 o'clock), the fixed pointer tab above the rim, the shaft boss |
| `IA_handwheel` | `M_Brass_Aged` | 1,096 | **Origin (0, 1.30, 0.20) = the axis, axis +Z.** Rim (major 0.245, tube r 0.02), six spokes, hub, a turned handle pin with a ball on the rim at 12 o'clock. k stops = **−45° k about +Z**; a positive delta turns it clockwise seen from the player. Identity = handle at 12 o'clock |

Notes: the wheel's centre is at 1.30 above the deck (world y 3.8), above the rail (3.55) so the dial reads over it; the dial plate is r 0.34, so the instances at x = ±2.2 and ±3.6
(1.4 apart) have 0.72 between plates. The wheel shows **its own turn count** (the logic does not store it); the dial's pointer tab is fixed, the handle moves. The numerals I–IV are on
the bridge's plates. QA: `handwheel.png` the `handwheels` view from the bay behind the bridge (wheel I at rest, II at 2 stops, III at 5, IV at 7); `_2` a closeup of I and II.

## panel0.glb (9,908 tris, 33 surfaces)

Origin = floor level at the centre of the back face (on the pier wall plane); face at z = 0.22 (bezel border to 0.25); placed at (0, 0, 14.0) yaw 180. Board x ±0.95, y 0.2 – 2.1, plinth ±0.98 to y 0.2, cap to 2.14.
Bounds: x ±0.98, y 0 … 2.14, z −0.02 … 0.27 (the main lever's guide plates and the switch tips reach 0.57 in front when pulled).

| Node(s) | Material | Tris | Pivot / notes |
|---|---|---|---|
| `panel_body` | `M_Steel_Painted` | 524 | Plinth, cabinet, raised bezel, corner bolts, cap |
| `panel_brass` | `M_Brass_Aged` | 4,498 | Four line **buses** (x = −0.30 / 0 / 0.30 / 0.60, y 0.40 – 1.60), five switch **wires** (y_s = 1.42 / 1.18 / 0.94 / 0.70 / 0.46, x −0.66 – 0.72), **Strand's plate** (1.14 × 0.14 at (0.15, 2.00)) with four filled discs r 0.034 over the lamps, four lamp bezels, the four **pictograms** at y = 1.70 (a padlock, the sun, concentric rings, three chevrons; 0.07 – 0.09 high), the numerals I–V at x = −0.85, five switch collars, the main lever's two guide arcs |
| `leyla_chalk` | `M_Chalk` | 1,002 | Her sign (0.13 high, centre (−0.80, 0.29)), **1998** (0.07 high) and **four tally strokes**, 2 mm proud, bottom left |
| `lamp_lock`, `lamp_light`, `lamp_array`, `lamp_vent` | `M_Glass_Dark` | 138 each | Domes r 0.035 at (−0.30 / 0 / 0.30 / 0.60, 1.86, 0.22); origin at the base; code emission |
| `IA_switch_1..5` | `M_Brass_Aged` | 212 each | Toggles; **origin (−0.74, y_s, 0.22)**, y_s = 1.42, 1.18, 0.94, 0.70, 0.46 for s = 1 … 5 (top to bottom, numerals I … V). Neutral = straight out +Z (identity). **Up (on) = −40° about +X, down (off) = +40°** |
| `IA_main_lever` | `M_Brass_Aged` | 352 | **Origin (0.84, 0.60, 0.24)**; stem 0.36 + ball, hub along X, tail. Rest = upright (+Y); **pulled = +60° about +X** (toward the player). Guide arcs radius 0.30 – 0.34 from 0° to 75° |
| `trace_<s>_<line>` ×20 | `M_Brass_Aged` | 96 each | Junction dots r 0.024 raised 4 mm at (x_line, y_s, 0.22). `s` = 1 … 5, `line` ∈ `lock`, `light`, `array`, `vent`; show where `v_panel[(s − 1) * 4 + line]` = 1 |

Empties (panel frame): `echo_mount_tech_panel` (0.8, 0, 1.0) rotation (0, 180, 0); `panel_light` (0, 2.4, 0.6).

Notes for the scene:
- Evidence layout: row s = switch s; column = line; the junction dot is where switch s feeds the line. The canonical `PANEL` matrix gives I → LOCK, ARRAY; II → LIGHT, VENT;
  III → LOCK, LIGHT, VENT; IV → ARRAY, VENT; V → LOCK, LIGHT (as the design table). QA hides the dots where `PANEL` = 0.
- Switch order is the top-down order of the numerals; the code applies +40° (down) at the start, −40° for a switch that is up.
- The first positions (switches at x = −0.78, numerals at −0.90) were under the bezel border (x −0.95 … −0.90); they were moved to −0.74 / −0.85.
- 33 surfaces: 1 body, 1 brass, 1 chalk, 4 lamps, 5 switches, 1 lever, 20 traces. A frame draws 13 – 26 of them (traces hidden where 0).
- Tris are close to the cap (9,908 of 10,000): the pictograms and the numerals are the bulk of `panel_brass`.
- QA: `panel0.png` the `panel0` view (switches I and II up, the four lamps lit, the canonical dots); `_2` the matrix closeup.

## Open points

- The keeper unit and the desk both rely on shader quads (`osc_screen`, `chart_paper`) whose shaders the room code writes (§10); the QA previews in `qa/blender/ch4/preview/` are stand-ins.
- The pawl item (`reverse_pawl`, group H) must be checked on `pawl_mount` once it exists: the seat is a ring boss at 0.004 – 0.016 above the plate and the empty's origin is 0.016 above the slope.
- The desk has no collider other than its `IA_*` parts (`IA_scrub`, `IA_chronometer`), as in Chapter 3.
