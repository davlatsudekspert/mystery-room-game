# Chapter 4 group D: the Reliquary (measured results)

Contract: `docs/models/ch4.md` §0, §1, §2, §6, §11, §12. Models: `cage`, `glass_tower`, `core_crystal`, `cradle`, `heart_drawer`.
Scripts: `tools/blender/models/<name>.py`; helpers in `tools/blender/lib_ch4_cde.py` (bmesh primitives, `gem2`, the island QA stand-ins) on top of
`lib_ch4.py` and `lib_ch4_numerals.py`; build list `tools/blender/build_lists/ch4_d.txt`. Same pipeline and QA scene as groups A–C: G-frame build, lean GLB,
re-read and verify against §11, Cycles 24 samples 960 × 640, the hall shell + bridge + catwalk + rings as the setting, the island platform as a QA
stand-in (a drum r 2.7 and a slab r 3.0, top at world y 2.5; not exported), the group D neighbours imported at (0, 2.5, 0), the 42 light sprites as small
emissive spheres. Blender renders only.

**ISLAND FRAME.** All five models are built **in the island frame and placed at (0, 2.5, 0), yaw 0**: the origin is the island centre on the platform top.
Every number below is island-local (add 2.5 to y for the world).

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [--shots=1,2,3]
```

## Summary

| Model | Tris (budget) | Surfaces (cap) | Slots | GLB | QA renders (`qa/blender/ch4/`) |
|---|---|---|---|---|---|
| `cage` | 10,323 (12,000) | 6 (6) | 2 | `game/assets/models/cage.glb` | `cage.png`, `_2`, `_3` |
| `glass_tower` | 8,760 (9,000) | 7 (7) | 3 | `game/assets/models/glass_tower.glb` | `glass_tower.png`, `_2`, `_3` |
| `core_crystal` | 1,884 (3,000) | 3 (3) | 3 | `game/assets/models/core_crystal.glb` | `core_crystal.png`, `_2`, `_3` |
| `cradle` | 1,382 (3,000) | 4 (4) | 3 (2) | `game/assets/models/cradle.glb` | `cradle.png`, `_2` |
| `heart_drawer` | 750 (4,000) | 7 (7) | 4 | `game/assets/models/heart_drawer.glb` | `heart_drawer.png`, `_2` |
| **Group D in the `bridge` view** | | 6 + 7 + 3 + 4 + 3 (drawer face, drawer, housing) = **23** | | | the plan counted 20 |

`check_glb_names.py` passes on all five GLBs. The group D surfaces of §11.2 (20) become 23 because `cradle` carries a third slot node (the lamp ring) and the
drawer has its frosted pane as a node of its own; the digit wheels and the lock plates are small and may be culled beyond 9 m as planned.

**View clearance (important).** The contract's `island`, `collar` and `core` cameras are at y 3.6–3.8, which is **inside the collar's band (world y 3.35 … 4.05)**:
the digit housing (a lock box 0.92 wide, y 3.35 … 4.05, z up to 1.375) stands between those cameras and the cradle, the drawer and the Core's lower half. The
collar ring itself is open in the middle (two rails and thin balusters) so side views see through it, but the housing is solid. Use cameras above y ≈ 4.4
(or beside the south axis) for the Core, the cradle and the drawer; the QA renders use `core` = (0, 4.7, 2.5) → (0, 4.0, 0), `cradle` = (0, 4.6, 2.4) → (0, 3.6, 0.5),
`drawer` = (0.5, 3.75, 2.4) → (0, 3.15, 0.7) (low, to the side of the housing: the drawer face is under the housing's y range).

## cage.glb (10,323 tris, 6 surfaces)

Island frame. Bounds x, z ±2.57, y 0 … 3.0.

| Node | Material(s) | Tris | Pivot / notes |
|---|---|---|---|
| `cage` | `M_Steel_Dark` + `M_Brass_Aged` | 8,504 | Origin (0, 0, 0), identity. **Steel**: a base ring (r 2.30 … 2.56, y 0 … 0.22, 96 segments) with 48 rivets; 20 posts every 15° (the four gate centres are open): 0.09 square, y 0.18 … 2.84, the eight **door posts** beside the gates 0.13. **Brass**: a crown ring (r 2.28 … 2.57, y 2.80 … 3.0), a pyramid finial on every post, 16 lattice panels between the posts (two verticals, two rails at y 1.0 and 1.9, an X in each of the three cells, eight-sided rosettes at the X crossings and hex rosettes where the verticals meet the rails), and over every gate a lintel (y 2.58), a threshold bar and a fixed transom X |
| `IA_gate_1..4` | `M_Brass_Aged` | 403 … 461 each | The four gates at azimuth **180° (S, on the catwalk side) / 270° (W) / 0° (N) / 90° (E)**, clockwise from the south. A lattice leaf 1.242 wide (the chord of ±15°, in the plane z = 2.318 for gate 1), y 0.22 … 2.55, 0.04 thick: stiles, rails, four verticals, an X in each of two cells, two hinge barrels, a **lock plate 0.30 × 0.46** at the free edge (centre 0.40 from the gate axis, y 1.20) carrying the numeral **I / II / III / IV** (0.15 high, 0.014 relief) over a **keyhole punched through the plate**. **Origin = the hinge axis** at the leaf's left edge seen from outside, y = 0: gate 1 (−0.621, 0, 2.318), gate 2 (−2.318, 0, −0.621), gate 3 (0.621, 0, −2.318), gate 4 (2.318, 0, 0.621); identity at rest. **Open = −95° about +Y** (outward) |
| `gate_key_mount_1..4` | empty | — | **Children of `IA_gate_n`** (they swing with it: the key stays in the lock), at the keyhole 0.06 proud of the chord plane: gate 1 (0.40, 1.098, 2.378). Frame: Euler (0, 180° − 90° (n − 1), 0): **item −Z (the bow of a flat key) points OUTWARD along the gate's normal, item +Y up** |

Notes for the scene:
- The cage is open at the top (the glass case is 3.5 high and the crystal reaches 2.2): the crown ring is the only top element.
- The lattice is the heaviest part of the island view: 10.3k tris, 6 draws; cull it (and the lock plates) with the island group.
- The doorway is 1.24 wide and 2.35 high: the player never walks in, the gates only open for the story and the finale.

## glass_tower.glb (8,760 tris, 7 surfaces)

Island frame. The Core stands inside (r 0.55 pedestal, crystal 2.2 high, cradle and drawer on the south side up to z 0.75).

| Node | Material(s) | Tris | Pivot / notes |
|---|---|---|---|
| `tower_glass` | `M_Glass` + `M_Steel_Dark` | 488 | **Origin (0, 0, 0)**, identity; it **sinks by sliding −3.6 along Y**. An octagonal case, circumradius 1.10 (Ø 2.2), y 0 … 3.5: eight glass panels (centres at azimuth 180° + 45° k, the south one faces the player; 0.77 wide, 0.014 thick, y 0.15 … 3.25), eight steel mullions at the vertices, a base rail, a transom at y 1.70, a top frame and a shallow pyramid cap whose apex is at y 3.5. Its outermost point is 1.105 from the axis, so it slides inside the collar (r ≥ 1.13) and the base ring's bore (r 1.12) |
| `glass_static` | `M_Brass_Aged` | 3,856 | Origin (0, 0, 0), identity, never moves. The **base ring** (r 1.12 … 1.60, y 0 … 0.26) with 16 rivets; **four posts** at azimuth 45° / 135° / 225° / 315° (r 1.24, y 0.26 … 1.66); the **collar** r 1.13 … 1.35, y 0.85 … 1.55 as a **bottom rail** (y 0.85 … 0.99), a **top rail** (y 1.41 … 1.55) and **42 balusters** (open in the middle so the cradle and the Core show through), open at the south by ± 17°; and the **digit housing** closing that gap: a lock box x ±0.46, y 0.85 … 1.55, back wall at z 1.10, front plate at z 1.355 … 1.375 with **four windows** (0.13 wide, y 1.16 … 1.245) over the wheels, an axle through them and four small pointer lugs above the windows |
| `IA_collar_digit_1..4` | `M_Brass_Aged` | 1,104 each | Four brass digit wheels **Ø 0.20 × 0.12** at x = −0.30 / −0.10 / +0.10 / +0.30, **y 1.20, z 1.22**, axis local X. **Origin = the axis**, identity = **digit 0 reads upright at the front**. A drum Ø 0.176 between two flanges Ø 0.20, and the digits 0 … 9 as **3D relief** (0.058 high, 0.019 proud) round the rim, digit d at +36° d about +X. **digit d = −36° d about +X** (the code turns the wheel so that d reaches the front, reading upright through its window) |

Notes for the scene:
- The housing's windows leave about 0.025 of depth in front of the digits; from a camera at y ≥ 3.9 and z ≈ 2.6 the digit (0.058 high) is fully visible.
- The collar's tap targets are the four wheels only; the rest is static.
- After the glass sinks, the collar, the posts, the base ring and the housing stay (the digits remain tappable only while `collar` is unsolved).

## core_crystal.glb (1,884 tris, 3 surfaces)

Island frame; the crystal centre is **(0, 1.6, 0)** = world (0, 4.1, 0).

| Node | Material | Tris | Pivot / notes |
|---|---|---|---|
| `core_pedestal` | `M_Brass_Aged` | 1,788 | Origin (0, 0, 0). r 0.55, 1.10 high: a stepped foot, a waist r 0.40 (y 0.21 … 0.84), a collar with 12 rivets, a top plate r 0.55 (y 1.01 … 1.07) and a socket cup (r 0.31 → 0.14, floor at y 0.99) holding the crystal's lower point, with **six setting claws** (up to y 1.30, then in over the crystal's shoulder to y 1.395). Bounds ±0.55, y 0 … 1.399 |
| `core_shell` | `M_Crystal` | 48 | **Origin = the crystal centre (0, 1.6, 0)**. The hexagonal crystal: a prism of circumradius 0.24 and 0.50 high, with rhombic terminations (a shoulder ring at 0.52 r turned by 30°, then the apex): **1.20 high, y 1.00 … 2.20**. Translucent; the code may raise its emission |
| `core_light` | `M_Emissive_Lumen` | 48 | **Origin = the crystal centre**. The inner core: a smaller faceted gem (r 0.105, 0.36 body, 0.30 tips, y 1.12 … 2.08) that the code drives; keep it out of the shadow pass |
| `core_center` | empty | — | (0, 1.6, 0): the OmniLight `core_glow` and the orbit centre |

**The 41 + 1 light sprites are not in the file** (they are a code `MultiMesh`; a node of their own would have been a 4th surface for a model capped at 3). The
QA renders show them as r 0.035 spheres on **three circles of radius 0.75 through the crystal centre, tilted 62° about X and spun 120° apart about Y, 14 each**
(the 42nd is the "Leyla" light): that is the layout the code can use (sprite size 0.07 per the contract), orbiting about +Y.

## cradle.glb (1,382 tris, 4 surfaces)

Island frame. The socket looks at the Core centre: its axis **n = (0, 0.4116, −0.9114)** (24.3° above the horizon).

| Node | Material(s) | Tris | Pivot / notes |
|---|---|---|---|
| `cradle_arm` | `M_Steel_Dark` + `M_Brass_Aged` | 652 | Origin (0, 0, 0). A steel base plate on the pedestal top (y 1.07 … 1.115, z 0.38 … 0.70) with four bolts and a gusset to the collar, a brass turned neck at z 0.60, a cross bar and two arms (x ±0.14 … 0.168) ending in trunnions into the socket's sides |
| `IA_cradle` | `M_Brass_Aged` | 474 | **Origin = the socket centre (0, 1.32, 0.62)**, identity rotation (the tilt is baked into the mesh). A ring Ø 0.23 with an **inner recess Ø 0.15** on the player side (the lens, Ø 0.0696 and 16 mm thick, sits in it) and a **ledge (hole Ø 0.06)** on the Core side, six screw heads. Tap target for `use_item_on("crystal_lens", "cradle")` |
| `cradle_ring` | `M_Glass_Dark` | 256 | Origin = the socket centre. A lamp ring r 0.117 … 0.142 round the socket: **the code turns its emission on** when the lens is seated (the lamp slot of the library, as `lamp_*` on `panel0`) |
| `lens_mount` | empty | — | (0, 1.3135, 0.6266) = the socket centre moved 7 mm toward the player. Euler XYZ (−24.3°, −180°, 0): **+Z = toward the Core** (the lens `crystal_lens` faces +Z in its own file, so it looks at the crystal), +Y ≈ up |
| `mark_mount` | empty | — | (0, 0.68, 0.705), identity (+Z out of the face): the projected mark on the drawer's frosted pane |

`cradle` uses three slots (brass, steel, glass dark): the lamp ring needs the library's lamp slot, which the contract's two-slot list did not have.

## heart_drawer.glb (750 tris, 7 surfaces)

Island frame; the drawer face is at (0, 0.68, 0.70).

| Node | Material(s) | Tris | Pivot / notes |
|---|---|---|---|
| `heart_housing` | `M_Brass_Aged` + `M_Steel_Dark` | 240 | Origin (0, 0, 0). A brass front frame (x ±0.35, y 0.43 … 0.93, z 0.70 … 0.745, with a bead and bolts) round the opening, steel side / top / bottom walls and two runners going back to z 0.20 (inside the pedestal) |
| `IA_heart_drawer` | `M_Brass_Aged` | 218 | **Origin = the drawer face centre (0, 0.68, 0.70)**, identity. A front panel (x ±0.30, y 0.51 … 0.85), a window frame, a pull bar on two posts, rivets, and a tray (floor, two walls, a back wall) running back to z = 0 (0.70 deep: its rear end stays inside the housing when open). **Open = slides +0.55 along +Z** (the code moves the node; its children come along). At full travel the front panel (top y 0.85) just clears the collar's lower rail (y 0.85) |
| `drawer_face` | `M_Glass_Frosted` | 44 | **Child of `IA_heart_drawer`**, origin (0, 0.68, 0.704): the frosted pane 0.40 × 0.20 (z 0.700 … 0.708). The mark falls here |
| `IA_heart_watch` / `IA_heart_letter` / `IA_heart_pawl` | `M_Velvet` | 160 / 12 … / … | **Children of `IA_heart_drawer`**; three velvet pads in the tray: watch (round Ø 0.13 at x = −0.185), letter (0.19 × 0.19 at x = 0), pawl (0.13 × 0.13 at x = +0.185), all centred at z = 0.44 (closed), tops at y 0.545. **Origin = the pad's top centre** |
| `watch_mount` / `letter_mount` / `pawl_item_mount` | empties | — | Identity, **children of their pad**, at the pad's top centre (items lie flat, hero face +Y) |

The letter pad is 0.19 square for `letter.glb` (0.162 × 0.166).

## Files and commands

`game/assets/models/{cage,glass_tower,core_crystal,cradle,heart_drawer}.glb(+.import)`, `qa/blender/ch4/*.png`, `tools/blender/models/*.py`,
`tools/blender/lib_ch4_cde.py`, `tools/blender/build_lists/ch4_d.txt`. Rebuild: `tools/blender/build_all.sh`; re-import: `godot --headless --path game --import`.
