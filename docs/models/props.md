# Prop models: parts and animation spec

These props are built by `tools/blender/models/*.py` and listed in `tools/blender/build_lists/props.txt`. They are exported to `game/assets/models/<name>.glb`. Every script accepts `-- --no-render`. QA renders are in `qa/blender/<name>*.png`.

## Conventions

These are the same as `docs/models/mechanisms.md`. All coordinates on this page are **Godot** coordinates in metres, where Godot = Blender (x, z, −y).

- **Model-space props** (chalkboard, poster, desk lamp, evidence board, the echoes, the bookshelf and the lab bench) have their **front facing +Z**. Wall-mounted props have their **back plane at z = 0**.
- **Room-space props** (`shadow_lock`, `darkroom_props`) are placed at the room origin with an identity transform.
- **Angles** are relative to the node's rest transform. This matches `Lab7Visuals._rot(node, axis, deg)`, which computes `rest.basis * Basis(axis, deg)`.
- **Sign:** a positive angle is counter-clockwise when you look down the +axis.
  - About **+Y**, +Z turns toward +X.
  - About **+X**, +Y turns toward +Z.
  - About **+Z**, the rotation is counter-clockwise as seen from +Z.
- **Colliders:** each static cluster is its own compact mesh, so no AABB tap blocker covers an `IA_*` part.
- **Images:** GLBs are exported without embedded images (`lib_props.export_lean`). Godot swaps every material by slot name.

### New material slots added by this pass
These materials are in `game/assets/materials/` and are also written by `tools/materials/make_extra_materials.py`.

| Slot | Use |
|---|---|
| `M_Decal_Emblem` | `wall_emblem.png`, alpha scissor 0.4, so it receives shadows. Used for the painted emblem in the darkroom |
| `M_Lacquer_Black` | Poster frame |
| `M_Glass_Green` | Banker's-lamp shade. Opaque cased glass with a slight rim effect |
| `M_Chalk` | Chalk sticks and dust |
| `M_Glass_Amber` | Darkroom chemistry bottles |

`M_Cork` is now textured with a procedural cork (`tools/textures/fetch_textures.py`, folder `cork`, 0.5 m tile, `uv1_scale` 2). Its line was removed from `make_extra_materials.py`, so a rerun of that script will not overwrite it.

---

## shadow_lock.glb (15,600 tris, room space, puzzle P10)
**Placement:** at the room origin with an identity transform. The model fills the darkroom over x −4.67…−3.59, y 0…2.59 and z −1.60…0.40.

### Optics
These three points are collinear:
- `light_origin` at (−4.0, 1.080, 0.080)
- the gimbal centre S at (−4.0, 1.25, −0.60)
- the emblem centre C at (−4.0, 1.50, −1.60), on the north-wall surface

The beam is pitched up by 14.04°. The magnification |C−L| / |S−L| is 1.68 / 0.68 = 2.4706.

- **Aligned state:** the ring plane is parallel to the wall, so its shadow is an exact circle. The circle has a centre-line radius of 0.247 m and is centred on the socket. The rod draws the meridian, about 0.69 m long.
- **`emblem_paint`:** a 0.82 m square quad, 1.2 mm in front of the wall, using `M_Decal_Emblem`. It is scaled so that the circle and line in `wall_emblem.png` (155.5 px radius) lie exactly under that shadow. See `qa/blender/shadow_lock_2.png`.

### Lighting setup for the lead
- **Spot lamp:** `SpotLight3D.global_transform = light_origin.global_transform`. The light shines along its local −Z.
  - Use `spot_angle` ≈ 14°, which lights a circle of radius ≈ 0.42 m around the emblem, with shadows on.
  - The current `look_at_from_position((-4,1.25,0.12), …)` in `lab7_room.gd` does **not** pass through S, so the shadow would miss the socket.
- **Safelight:** put an `OmniLight3D` at `safelight_origin`, at (−4.55, 1.986, 0.167). It aims along its −Z, which is down 28° toward the north. The current code puts the light at (−3.6, 2.3, −0.6).
- **Keep the beam clear:** inside the cone between the lamp and the wall, only the stand's thin stem (below the ring, in the x = −4 plane) casts a shadow. That shadow lies on the lower meridian.

### Parts
| Part | Pivot (world) | Axis / sign | Rest → travel |
|---|---|---|---|
| `sculpture_ring` (r = 0.10 band, 12 enamel pips) | S (−4.0, 1.25, −0.60) | local **+Y** = world +Y | **Rest = +60°** about +Y from aligned. The basis is not identity. Absolute yaw = 60° + (s−2)·30° = s·30°. **Aligned only at absolute 0° (≡ 180°)**, which is s = 0. At s = 3 (90°) the ring is edge-on and its shadow is a vertical line |
| `sculpture_rod` (0.28 long, child of the ring) | ring-local (0, 0, +0.0115), on the ring axis, 11.5 mm toward the lamp | local **+Z**, which is the ring normal. It equals world +Z (the lamp→wall axis) whenever the ring is aligned | **Rest = +60°** about +Z. The top leans toward −X, counter-clockwise as seen from the lamp. Absolute tilt = s·30°. **Vertical only at s = 0** (or 180°). It is a nested gimbal: its two shoes ride on the ring band, so the rod and the ring never intersect at any state |
| `IA_ring_knob` | (−4.0, 1.027, −0.60). Knurled wheel on top of the stand head | local +Y | Tap target. Optional: spin it +30° per tap |
| `IA_rod_knob` | (−4.0, 0.987, −0.543). Knob on the head front | local +Z | Tap target. Optional: spin it +30° per tap. Its enamel index line points up |
| `IA_emblem_socket` | (−4.0, 1.50, −1.585). Brass ring, Ø 0.09, protruding 3 cm from the wall | — | Static tap target |
| `socket_lens` (child of the socket) | socket-local (0, 0, 0.0026). Crystal disc, Ø 0.0704, `M_Crystal` | — | Visible only when `lens_at == "socket"`. Its only material is crystal, so `_glow` overrides apply cleanly |
| `IA_cabinet_door` | hinge (−4.178, 0.55, −1.399), on the front-left edge at mid-height | local **+Y** | 0° closed → **−100°** open. Negative swings it out into the room. `CABINET_OPEN_DEG = -100` is correct |
| `shadow_cabinet` | body origin (−4.0, 0.55, −1.58). Size 0.36 w × 0.40 h × 0.18 d, back on the wall | — | Static |
| `cabinet_item_spot` | empty (−4.0, 0.55, −1.50), the interior centre (interior 0.324 w × 0.364 h × 0.16 d) | — | Spawn `mirror_item` here (0.22 × 0.26 m). It fits with 5 cm to spare. The current hinge offset (0.12, 0, −0.08) leaves it 6 mm inside the left side. Use hinge + (0.178, 0, −0.101) instead |
| `spot_lamp` | trunnion (−4.0, 1.0315, 0.274). Basis = 14.04° about +X | — | Static. Baby profile spot with shutters, iris, gel frame and lens |
| `spot_bulb` (child) | glowing disc behind the lens, `M_Emissive_Warm` | — | Toggle its emission with the lamp, as for `bulb` on the pendants |
| `light_origin` (child, empty) | (−4.0, 1.080, 0.080). Local −Z is the beam | — | See the lighting setup above |
| `safelight` | red filter glass, `M_Emissive_Red`. Origin (−4.55, 2.009, 0.211). Basis = 28° about −X | — | Toggle emission after ARRAY is live. It has a single material |
| `safelight_origin` (child, empty) | (−4.55, 1.986, 0.167) | — | Position for the OmniLight |
| `shadow_table`, `spot_stand`, `sculpture_stand`, `safelight_housing`, `emblem_paint` | static clusters | — | — |

**Logic note (`lab7_logic.gd`):** `shadow_aligned()` uses `s % 3 == 0`. With 30° steps that also accepts s = 3, which is 90°: the ring is edge-on and the rod horizontal. That state does **not** draw the emblem.
- Use `int(s[0]) == 0 and int(s[1]) == 0` instead.
- Optional: when the state wraps from 5 to 0, animate to +120° from rest (180° absolute, which looks identical) so that the knob keeps turning one way.

**Layout conflict (bookcase):** the bookcase is hinged at (−3.1, 0, −1.15) and opens −85° into the darkroom.
- While it swings, it sweeps a 1.16 m quadrant that contains the gimbal (1.05 m from the hinge).
- Once open, it parks over x −4.2…−3.1 and z −1.15…−0.69. That is between the sculpture and the emblem, so it blocks the beam and the `shadow` and `emblem` camera views.
- Suggested fix: open it **into Lab 7** about its **front-north edge**. Use a pivot node at (−2.74, 0, −1.15) and rotate it +85° about +Y. That swing only sweeps empty lab floor and clears the wall. The GLB does not need to change.

## chalkboard.glb (1,720 tris, static)
- **Size:** 1.73 w × 1.204 h × 0.098 d.
- **Origin:** on the back plane, at the horizontal centre of the slate's **bottom edge**. The slate spans x ±0.80, y 0…1.00 and z 0.022.
- **Placement:** (−3.0, 1.0, 1.05) with yaw 90. The slate face is then at world x = −2.978, y 1.0…2.0.

| Part | Notes |
|---|---|
| `chalk_slate` | Front face: `M_Decal_Chalkboard`, planar 0..1 UV. Aspect 1.6 : 1 = 1024 : 640, not mirrored. Other faces use `M_Chalkboard` |
| `chalk_frame` | Moulded walnut frame, backing board, chalk tray with brass brackets, two brass mirror plates |
| `chalk_items` | Three chalk sticks (one full, two broken), chalk flecks and crumbs, and a walnut-backed felt eraser on the tray. Tray top y = −0.028 |

## poster_frame.glb (408 tris, static)
- **Size:** 0.544 × 0.751 × 0.024.
- **Origin:** centre of the back plane.
- **Placement:** (−0.3, 1.9, 2.5) with yaw 180.

| Part | Notes |
|---|---|
| `poster_paper` | `M_Decal_Poster`, planar 0..1 UV over 0.50 × 0.707 (aspect 1024 : 1448), not mirrored. The sheet is slightly cockled |
| `poster_glass` | `M_Glass`, 1 cm in front of the paper |
| `poster_frame_body` | `M_Lacquer_Black` frame, hardboard back, turn buttons |

## desk_lamp.glb (3,390 tris)
- **Type:** 1950s brass banker's lamp with a green cased-glass shade.
- **Size:** 0.255 × 0.401 × 0.313, including the flex that runs back into a brass desk grommet.
- **Origin:** centre of the base underside.
- **Placement:** (−1.18, 0.78, −2.32) with yaw 25.

| Part | Notes |
|---|---|
| `bulb` | Child of `desk_lamp_body`, `M_Emissive_Warm`. Local (0, 0.324, 0.061) |
| `light_origin` | Empty at the bulb centre, local (0, 0.324, 0.061). With yaw 25° the world position is ≈ (−1.154, 1.104, −2.265). The current OmniLight is at (−1.05, 1.18, −2.15) |
| `lamp_shade` | Separate node, tilted 14° toward the reader. `M_Glass_Green` outside, `M_Enamel_White` inside with a white rim. You can tint or glow it on its own |
| `desk_lamp_body` | Stepped base, crook stem, socket, bead pull-chain, flex and grommet |

## evidence_board.glb (4,214 tris)
- **Size:** 1.40 × 1.00 × 0.036. The cork face is at z = 0.016.
- **Origin:** centre of the back plane.
- **Placement:** (−4.8, 1.5, −0.6) with yaw 90.

| Part | Notes |
|---|---|
| `photo_0` … `photo_7` | Paper cards, 0.11 × 0.135. Each has its own 0..1 UV (u → +X seen from the front, v → up, aspect 280 : 344, not mirrored) and uses `M_Decal_Photos`. `M_Decal_Photos.tres` only holds `photo_0.jpg`, so give each card `photo_k.jpg` as a material override. Grid layout: top row 0–3, bottom row 4–7 |
| `board` | Cork panel (`M_Cork`) and oak frame |
| `evidence_items` | Contents:<br>• three newspaper clippings about the "ventilation accident", with printed-line strips<br>• a typed staff list of 41 names, most struck through in red<br>• a November 1979 calendar leaf with the 14th circled<br>• a plan of the Array Hall<br>• index cards<br>• brass and crimson push pins<br>• `M_String_Red` string linking photos to the clippings, the plan and the date |

## darkroom_props.glb (7,934 tris, room space, ≤ 8k)
- **Placement:** room origin with an identity transform.
- **Kept clear:**
  - the lamp table and its beam
  - the north wall around x = −4 (emblem and cabinet)
  - the west wall (evidence board)
  - the floor under the wet bench, where the UV shard lies at (−4.55, 0.02, 0.15). The `darkroom_floor` camera ray to it is open; see `darkroom_props_4.png`
  - the `shadow` camera spot (−3.45, 1.6, 0.32)
  - the bookcase sweep quadrant

| Cluster | Where | Contents |
|---|---|---|
| `wet_bench` | South-west corner, x −4.78…−4.33, z −0.22…0.38, top 0.86 | Bench, open underneath. Zinc lining. Three white-enamel developing trays with cobalt rims and liquid, plus a print in the developer. Bamboo tongs, graduated cylinder, amber stock bottle |
| `wall_shelf` | South wall above the bench, y 1.45 | Four amber bottles with labels and a bakelite darkroom timer |
| `dry_bench` + `enlarger` | South-east corner, x −3.64…−3.22, z 0.05…0.38 | Cabinet with doors and a box of photo paper. Enlarger with its column on the east wall, a lamphouse at y ≈ 1.26–1.43, bellows, lens and easel |
| `drying_line` | Wall to wall at z = 0.05, y 2.12, sagging 5 cm | Cord, brass screw-eyes, wooden pegs, a film strip with a weight clip |
| `print_0..3` | Hanging on the line at x −4.62 / −4.43 / −4.22 / −4.02 | `M_Decal_Photos`, 0.13 × 0.165. Own 0..1 UV. The image faces north (−Z) and is not mirrored. Suggested overrides: `photo_4..7.jpg` |
| `stool` | (−4.45, 0, −0.45) | Lab stool |
| `bucket` | (−4.60, 0, −1.42) | Galvanised bucket with water and a paddle |

## echo_strand_standing.glb (8,902 tris: body 6,202 + head 2,700)
- **Figure:** Prof. Emil Strand, about 1.73 m to the crown, slightly stooped. He wears a long coat to mid-calf, has a short beard and a receding fringe, and raises chalk to a board in front of him (−Z).
- **Size:** 0.70 w × 1.73 h × 0.66 d.
- **Material:** one material, `M_Echo`.
- **Mesh:** closed 2-manifold. The body has 2 shells (body and chalk); the head has 1.

| Part | Pivot | Notes |
|---|---|---|
| `echo_body` | Floor between the feet, (0, 0, 0) | The chalk tip touches a board plane 0.52 m in front, at local (0.13, 1.60, −0.52) |
| `echo_head` | Child of the body. Neck pivot at local (0, 1.47, −0.088) | Yaw about local +Y to turn his head. A positive angle turns him to his left (−X). At rest his head is pitched 9° up and yawed 7° toward the chalk |

**Placement at the Lab 7 chalkboard:** origin at (−2.458, 0, 0.95), yaw 90. The chalk then touches the slate at (−2.978, 1.60, 0.82). Use z = 0.95 rather than 1.18 so that his left side clears `lumen_projector` at (−2.3, 0, 1.6).

## echo_leyla_sitting.glb (rebuilt: 9,054 tris)
The head decimation is fixed: the old export had collapsed the skull and bun into a cone.
- **Cause:** `lib_echo.decimate`'s vertex-group weighting starves the cranium in Blender 5.2.
- **Fix:** the head now uses plain quadric collapse.

Parts and pivots are unchanged; see the script docstring.

---

## bookshelf.glb (from `bookshelf.py`)
- **Origin:** the hinge, at the back-north-bottom corner. In model space the case occupies x −1.10…0, y 0…2.10 and z 0…0.36, with the front at +Z.
- **Placement:** (−3.1, 0, −1.15) with yaw 90. To open it, rotate the whole model **−85° about +Y** (`SHELF_OPEN_DEG`). See the layout conflict under `shadow_lock` above.
- **Book levels** (top surface y): 0.15, 0.50, 0.85 (encyclopedia), 1.20 (the gear box sits in a clear 0.32 m spot at x −0.71…−0.39), 1.55.
- **`IA_book_1`…`IA_book_9`:** green volumes with gold numerals I–IX.
  - Origins at local (−0.74 + 0.0475·(k−1), 0.85, 0.332), on the bottom edge of the spine.
  - Tilt out with **+16° about local +X**. The top moves toward +Z, out of the shelf (`BOOK_TILT_DEG`).
- **Static nodes:** `bookshelf_case`, `bookshelf_books`, `bookshelf_props`.

## lab_bench.glb (from `lab_bench.py`)
- **Origin:** floor centre, front at +Z.
- **Size:** 2.2 × 0.92 × 0.65. The splashback and reagent shelf reach y 1.36.
- **Placement:** (−0.3, 0, 2.15) with yaw 180.
- **Clear zone for the radio:** bench-local x −1.08…−0.62, with z ≥ −0.16.
- **`vial_rack`:** at bench-local (0.6, 0.92, 0.05), which is room (−0.9, 0.92, 2.1).
- **`IA_vial_green` / `IA_vial_crimson` / `IA_vial_cobalt`:** left to right as seen from the front.
  - Origins at the vial centres, bench-local x 0.542 / 0.600 / 0.658, y 0.9985, z 0.05.
  - Each has children `vial_liquid_<c>` (`M_Liquid_*`) and `vial_label_<c>` (`M_Decal_VialLabel_*`, curved, arc-length UV with u toward +X seen from the front, aspect 2 : 1).
  - To lift a vial out of the rack, translate it +Y by about 0.12.
- **Static nodes:** `lab_bench`, `glassware`, `bench_props`, `microscope`, `residue`.
