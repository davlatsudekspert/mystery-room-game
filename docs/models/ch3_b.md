# Chapter 3 group B: Choir Hall props (measured results)

Contract: `docs/models/ch3.md` §0, §1.2–§1.3, §2, §4, §11 (`stair_quad`), §13. Models: `transformer` (×3),
`choir_rack`, `choir_tube`, `tube_bench`, `strand_office`, `office_desk`, `meter_case`. Scripts:
`tools/blender/models/<name>.py`, shared helpers in `tools/blender/lib_ch3_bc.py` (groups B and C; on top of `mrlib`,
`lib_mech`, `lib_arch`, `lib_ch2_vault`, `lib_ch3_a`, `lib_ch3_symbols`, none edited), build list
`tools/blender/build_lists/ch3_b.txt`.

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [--shots=1,2,...]
```

Every script builds in Godot axes (the `lib_ch2_vault` G-frame), converts to Blender axes before parenting, exports
`game/assets/models/<name>.glb` (lean materials: Godot swaps the `M_*` slots for its `.tres`) and **reads the GLB
back**: required node names, parents, model-space positions (1 mm), identity rest rotations, mount rotations,
triangles, surfaces (mesh nodes × primitives) and material slots against §13, the shader / decal quads' UV corners,
and `check_glb_names.py`. QA renders: Cycles, 32 samples, 960 × 640, 2 threads, inside the real `shell_choir.glb`
(with the west `blast_door.glb` in the tunnel mouth) under the §1.5 Choir lights, cameras from the §2 views;
neighbouring GLBs imported (`choir_tube` on the rack and bench mounts, `control_desk`, the keys, the strip, the meter,
`echo_welder` at `transformer_1`). Blender renders only, not Godot screenshots.

All coordinates are **Godot, model-local, metres**; models face +Z; angles follow §0.

## Summary

| Model | Tris (budget) | Surfaces (cap) | Slots (≤ 4) | GLB | QA renders (`qa/blender/ch3/`) |
|---|---|---|---|---|---|
| `transformer` (×3) | 4,408 (5,000) | 4 (4) | 3 | `transformer.glb` | `transformer.png`, `_2` … `_4` |
| `choir_rack` | 5,440 (6,000) | 13 (13) | 4 | `choir_rack.glb` | `choir_rack.png`, `_2` … `_5` |
| `choir_tube` | 2,352 (2,800) | 7 (7) | 1 | `choir_tube.glb` | `choir_tube.png`, `_2` |
| `tube_bench` | 1,438 (2,500) | 5 (5) | 3 | `tube_bench.glb` | `tube_bench.png`, `_2` |
| `strand_office` | TBD (9,000) | TBD (7) | 4 | `strand_office.glb` | `strand_office.png`, `_2` … `_5` |
| `office_desk` | TBD (5,000) | TBD (6) | 4 | `office_desk.glb` | `office_desk.png`, `_2` … `_4` |
| `meter_case` | TBD (2,500) | TBD (7) | 4 | `meter_case.glb` | `meter_case.png`, `_2`, `_3` |

---

## choir_tube.glb (2,352 tris, 7 surfaces, 1 slot)

Seven root-level objects **`IA_tube_<r>`**, r = the meter reading 1..7, all at the origin with identity (the code
spawns the GLB once and reparents each tube to `slot_mount_<k>`, `bench_mount_<j>` or the in-hand anchor with an
identity local transform). `M_Brass_Polished` only, 336 tris each.

| r | Tube length L | Bottom (y) | Notes |
|---|---|---|---|
| 1 … 7 | (8 − r) × 0.15 = 1.05 … 0.15 | −(0.0196 + L) = −1.0696 … −0.1696 | measured on the mesh |

- Origin = the top of the hanging eye (the hang point); the tube hangs along −Y.
- The eye is a Ø 0.017 brass ring (wire Ø 0.0056) in the XY plane: a peg passes through it along Z. Twelve major
  segments put a vertex exactly at 12 o'clock, so the eye top is **y = 0.0000**; the hole's inner top is **5.6 mm**
  below the hang point (the rack's pegs are placed from that number).
- Below the eye: a Ø 0.053 cap (top at y −0.0196), the Ø 0.05 body with one engraved ring 0.045 below the cap, and the
  bottom cap. No numbers.

QA: `choir_tube.png` (the seven tubes on a bar in reading order, longest left), `_2` (eye, cap and ring close-up).

---

## choir_rack.glb (5,440 tris, 13 surfaces)

**Shape.** Riveted dark steel: two channel posts (x ±1.35) on bolted foot plates with three wall brackets each, the
top channel (y 2.30 … 2.40, front face z 0.20) with a riveted lip, the kick rail at y 0.95 on stays out to the
0.35 m frame depth, a back board (y 1.05 … 2.30, z 0.04 … 0.07) in a flat-bar frame with riveted mullions between the
slots, the striker's bearing blocks and the hammer bracket. Brass: a hanger bracket per slot (a riveted strap on the
bar's face, a block under the bar and the peg with a flared tip), the lock-bar guides on the posts, the hammer's
toothed quadrant.

**Placement.** North wall at (−9.6, 0, −4.0), yaw 0. Static bounds x −1.44 … 1.46, y 0 … 2.47, z 0 … 0.35.

| Node | Pivot / position | Materials | Notes |
|---|---|---|---|
| `choir_rack` | (0, 0, 0) | Steel_Dark, Brass_Aged | static, 4,438 tris |
| `IA_slot_0..6` | (x_k, 1.725, 0.075), x_k = (k − 3) × 0.34 | Felt | 0.24 × 1.15 strips (y 1.15 … 2.30) on the back board, front at z 0.08; the slot's tap target |
| `slot_mount_0..6` | (x_k, 2.30, 0.20) | — | identity: the tube's eye top sits here; the brass peg (r 0.0045, axis y 2.2899, z 0.11 … 0.235, flared tip to 0.243) passes through the eye |
| `striker` | (0, 2.40, 0.30) | Felt | axle, two arms at x ±1.25, the Ø 0.044 felt roller at y 2.12; **strike = +15° about local +X** (the roller swings to z ≈ 0.228, into the tubes' front faces at 0.225) |
| `IA_hammer` | (1.42, 1.10, 0.22) | Brass_Aged | boss on the bracket, 0.385 stem with a catch, Ø 0.052 ball at y 1.50; **pull = +45° about local +X** |
| `rack_lock` | (0, 2.325, 0.2575) | Brass_Aged | bar x ±1.36, y 2.305 … 2.345, z 0.25 … 0.265 in the post guides, a wire loop at the centre; **slides −0.05 on local Y** once `choir_tuned`: it then sits in front of the eyes at peg height |
| `stair_quad` | (0, 3.00, 0.004) | Shader_Quad | 2.60 × 0.90 quad, UV corners (−1.3, 2.55) → (0, 0), (1.3, 3.45) → (1, 1): u → +X, v → +Y |

**§1.3 hang points** (world, yaw 0): (−9.6 + (k − 3) × 0.34, 2.30, −3.80), k = 0 … 6. Exact.

QA: `choir_rack.png` (`rack` view at the start: `TUBES_START` 4 · 7 2 · 5 ·, the chalk staircase preview above),
`_2` (`rack_close`), `_3` (`rack` view tuned: `CHOIR_TARGET` 4 6 2 7 1 5 3, hammer pulled, striker in, lock
dropped), `_4` (hangers, lock bar and roller close-up), `_5` (`choir` root view with the desk).

---

## transformer.glb (4,408 tris, 4 surfaces, 3 slots)

**Shape.** A grey-green painted oil transformer: a channel-iron skid, the base section with the bolted seam at
y 0.62 (hex bolts along the front and sides; x = 0 is left free for the welder's torch), the tank with riveted front
corner seams, a lid flange with lifting lugs, a drain boss, radiator fins on both sides (local ±X = along the west
wall) with header pipes and stubs, the conservator drum on two saddles with its filler cap and down pipe, three
painted bushing flanges and the lamp housing; three brown glazed porcelain bushings (sheds; the outer two to y 2.35,
the middle one to 2.17 so the feed bars pass over it); copper terminals, feed bars, the two Ø 0.015 rods of the
Jacob's ladder with ball ends, the middle terminal's strap to the lid, and the blank riveted rating plate.

**Placement.** Free-standing at (−12.45, 0, −3.0 / −1.3 / 0.4), yaw 90 (the front faces the hall, the fins face the
neighbours). Bounds x ±0.73, y 0 … 3.511 (the rod tips), z −0.475 … 0.50: **nothing above 3.6** (catwalk at 4.0).

| Node | Pivot / position | Materials | Notes |
|---|---|---|---|
| `transformer` | (0, 0, 0) | Steel_Painted, Porcelain, Copper | static, 4,290 tris |
| `hum_lamp` | (0.45, 1.50, 0.46) | Porcelain | glazed jewel in a painted housing on the front face (code tint; `set_emission` duplicates the material, so sharing the bushings' slot is safe) |
| `arc_base` | (0, 2.38, 0) | — | empty just above the ball terminals (ball gap **0.028** at y 2.355) |
| `arc_top` | (0, 3.48, 0) | — | empty just below the rod tips (rod-axis gap **0.36** at y 3.50) |
| `echo_mount` | (−0.10, 0, 0.93) | — | rot (0, 180, 0): `echo_welder` faces the tank; his `torch_tip` (−0.10, 0.62, 0.48) lands on the seam at (0, 0.62, 0.45), the tank's front face |

QA: `transformer.png` (the three along the west wall under the catwalk, lamps green), `_2` (`port_b_mem` view: the
welder kneeling at `transformer_1`, a spark glow at the torch tip), `_3` (bushings and ladder with a QA arc ribbon
between the rods), `_4` (`choir` root view).

---

## tube_bench.glb (1,438 tris, 5 surfaces)

**Shape.** A painted angle-iron bench 1.40 × 0.60 (top 0.86) with a three-plank top, stretchers, a lower shelf with
a crate, end braces; on the wall above it a tool board with four hooks, a tuning spanner, a tube hook and a wooden
mallet.

**Placement.** North wall at (−7.35, 0, −4.0), yaw 0; origin = the wall plane at floor level, centre.

| Node | Pivot / position | Materials | Notes |
|---|---|---|---|
| `tube_bench` | (0, 0, 0) | Steel_Painted, Wood_Floor | static, 1,366 tris; bounds x ±0.70, y 0 … 1.40 (the tool board), z 0 … 0.60 |
| `IA_bench_0..2` | (0, 0.875, z_j), z_j = 0.45, 0.32, 0.19 (front → back) | Felt | 1.15 × 0.08 cradle strips, y 0.86 … 0.89, with a shallow V groove (half-width 8 mm, 4 mm deep): a Ø 0.05 tube rests on the groove's edges with its axis at y 0.9137 |
| `bench_mount_0..2` | (−0.55, 0.915, z_j) | — | rot (0, 0, 90): the tube's −Y runs along +X, its eye standing at the left end |

QA: `tube_bench.png` (`bench` view, the spare tubes 6 1 3 front → back), `_2` (oblique close-up with the tool board).

---

## strand_office.glb (TBD tris, 7 surfaces)

**Shape.** Built in world coordinates. Walnut frame-and-panel dado to 0.90 (plinth, raised fields on both faces, cap
rail), brass mullions every ~0.7 m with brass transoms at 1.92 … 1.96 and head rails under the roof, clear glass
panes to 2.76, the door bay with wooden jambs outside the doorway (z 2.16 … 2.20 and 3.10 … 3.14), a head at 2.15 and a
transom light above, the corner post, the roof slab y 2.80 … 2.90 with a brass bead, brass hinge knuckles. Dressing:
a walnut four-drawer filing cabinet in the north-west corner (brass cup pulls and label frames, fronts facing east),
the wooden coat stand at (−10.55, 0, 3.7) with a brass ring and four hooks (Strand's coat itself is in
`office_desk.glb`), and the brass frame of the staff photo on the west wall.

| Node | Pivot / position | Materials | Notes |
|---|---|---|---|
| `strand_office` | (0, 0, 0) | Wood_Panel, Brass_Aged, Glass | static |
| `IA_office_door` | (−10.2, 0, 2.22) | Wood_Panel, Glass | leaf z 2.22 … 3.10, y 0 … 2.12, x −10.22 … −10.18: stiles, rails, a raised lower panel, glass above 0.96; **open = +100° about +Y** (the free edge swings to x −9.33, z 2.07, into the hall) |
| `IA_office_lock` | (−10.14, 1.05, 3.0), child of the door | Brass_Aged | box x −10.18 … −10.10, y 0.98 … 1.12, z 2.95 … 3.05 on the hall face; a raised ■ in a sunk border on its face, the key-slot escutcheon on its top, lever handles on both faces at z 2.86 |
| `office_key_mount` | (−10.14, 1.1168, 3.0), child of the lock | — | rot (90, 90, 0): `key_square` stands blade down, bow face toward +X; its collar face (0.0032 above its origin) rests on the box top at y 1.12 |
| `staff_photo` | (−12.98, 1.65, 2.95) | Decal_StaffPhoto | 0.60 × 0.40 quad facing +X; UV u → −Z (the viewer's right), v → +Y (checked) |

QA: `strand_office.png` (`office_door` view, closed, ■ in the lock), `_2` (`office` view, door open), `_3`
(`switch_room` view with the door open: the leaf stays out of frame), `_4` (`choir_s` root view), `_5` (hero from the
hall).

---

## office_desk.glb (TBD tris, 6 surfaces)

**Shape.** A walnut pedestal desk 1.30 × 0.65 (top 0.76): moulded top, two drawer pedestals with three drawers each
on the sitter's side (brass pulls), modesty panel, plinth. Dressing: a paper blotter with walnut corners and brass
studs, a brass ashtray, three books, a fountain pen; the brass lamp (turned base, stem, collar) at (0.50, 0.76, −0.15);
and Strand's cream lab coat (`M_Paper`) hanging on the office coat stand's north-west hook — built here in desk-local
coordinates (world (−10.663, 1.76, 3.587)) because `strand_office` has no cream slot.

**Placement.** (−12.6, 0, 2.95), yaw 90 (the front faces east, the back is 7.5 cm off the west wall).

| Node | Pivot / position | Materials | Notes |
|---|---|---|---|
| `office_desk` | (0, 0, 0) | Wood_Walnut, Brass_Aged, Paper | static |
| `IA_office_lamp` | (0.50, 1.11, −0.08) | Brass_Aged | ball joint, arm, bell shade (rim y 1.06, r 0.05, front at z −0.03) and the strip clip on the rim's front; pick-up target for the strip |
| `office_bulb` / `office_light` | (0.50, 1.085, −0.08) | Paper / — | frosted bulb inside the shade (code emission) and the light empty |
| `ecg_mount` | (0.50, 1.06, −0.02) | — | rot (90, 0, 0): `ecg_strip` hangs by its top edge, face toward +Z (east); its clip hole lands at (0.50, 1.0822, −0.0239), on the clip's pin |
| `letters_mount` | (0.10, 0.765, 0.05) | — | identity: `letter.glb` lies flat |
| `IA_note` | (0.33, 0.762, 0.18) | Decal_StrandNote | 0.15 × 0.11 quad facing +Y; UV u → +X, v → −Z (checked): upright for the sitter / the east |

QA: `office_desk.png` (`office` view), `_2` (`ecg_lamp` view: the strip on the shade rim with the seed-0 trace
preview), `_3` (the note and the letters), `_4` (the coat on the stand, from the office door).

---

## meter_case.glb (TBD tris, 11 surfaces)

**Shape.** A dark leather case 0.30 × 0.10 × **0.25** (body to 0.085, lid 0.085 … 0.10) with brass corner caps, feet,
hinge knuckles, a brass bezel plate round the three digit windows and the ☼ ☾ ✦ inlays above them, a leather strap
handle on the lid, a velvet tray inside.

**Placement.** On the office desk at (−12.62, 0.76, 3.30), yaw 90 (the front faces east); origin = the bottom centre.

| Node | Pivot / position | Materials | Notes |
|---|---|---|---|
| `meter_case` | (0, 0, 0) | Leather, Brass_Aged, Velvet | static |
| `IA_case_dial_0..2` | (x_i, 0.055, 0.11), x_i = −0.07, 0, 0.07 | Enamel_Cream, Leather | Ø 0.04 × 0.014 thumb drums, axis +X, 5 mm proud of the front through the windows; dark numerals 0–9 wrapped on the rim, 0 facing +Z at rest, digit d at `Basis(X, +36° d)·(0, 0, 1)`; **one step = −36° about local +X** |
| `IA_case_latch` | (0, 0.02, 0.127) | Brass_Aged | push catch on the front |
| `case_lid` | (0, 0.10, −0.125) | Leather | pivot at the back top edge; **open = −100° about local +X** |
| `meter_mount` | (0, 0.04, 0.025) | — | rot (−90, 0, 0): `resonance_meter` lies on its back, face up, top toward −Z, its back on the velvet at y 0.016; it spans z −0.112 … +0.101 inside the tray (±0.117) |

QA: `meter_case.png` (`meter_case` view, closed, 0 0 0), `_2` (code 4 2 6 set, lid open, the meter in its velvet),
`_3` (the windows close-up reading 4 2 6 under ☼ ☾ ✦).

---

## Deviations from the contract

TBD

## Notes for integration

TBD
