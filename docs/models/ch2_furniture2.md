# Chapter 2 furniture, group B2: desk, reading table, booth furniture

These models are built by `tools/blender/models/<name>.py` and listed in
`tools/blender/build_lists/ch2_furniture2.txt`. Shared helpers live in `tools/blender/lib_ch2_furniture2.py`
(Godot-coordinate wrappers around `mrlib` / `lib_arch` / `lib_mech` / `lib_props`, a GLB verifier and the QA
scene helpers). Each model is exported to `game/assets/models/<name>.glb`; QA renders go to `qa/blender/ch2/`.

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [--shots view,open,...]
```

Every script ends with `verify_glb`: it re-reads the exported GLB and checks the required node names, the
identity rest rotation of the parts and mounts that need it, and the triangle budget. `check_glb_names.py`
passes on all five GLBs.

## Conventions

As in `docs/models/ch2.md` §0: all coordinates on this page are **Godot, model-local, metres**; a model's
front faces **+Z**; `IA_*` parts and mounts are their own nodes with the origin at the pivot. Positive angles
are counter-clockwise looking down the +axis (a back-hinged lid opens with a negative angle about +X).

Materials are game slots only. Decal slots keep UV 0..1 (u left→right, v bottom→top as the player sees it).
`box_uv` gives everything else world-scale UVs, and wood grain runs along each member.

| Model | Tris (budget) | Size x × y × z | Placement (contract) |
|---|---|---|---|
| `film_splicer.glb` | 7,917 (8,000) | 1.204 × 1.097 × 0.606 | (−3.9, 0, 3.5), yaw 180 |
| `slide_cabinet.glb` | 4,610 (5,000) | 0.512 × 1.05 × 0.478 (body offset, see below) | (−5.0, 0, 2.8), yaw 90 |
| `lens_case.glb` | 1,816 (2,500) | 0.243 × 0.072 × 0.139 | (−3.75, 1.45, 3.37), yaw 180 |
| `reading_table.glb` | 4,888 (5,000) | 1.40 × 1.153 × 0.815 (lamp flex hangs 1.5 cm past the back edge) | (1.9, 0, 1.0), yaw 0 |
| `archivist_desk.glb` | 5,674 (6,000) | 1.50 × 0.995 × 0.769 (pulls included) | (3.7, 0, −3.1), yaw 0 |

---

## film_splicer.glb (7,917 tris)

**Shape:** a fire-safe booth workbench. It has a cream-enamelled steel top with a dark rolled nosing on
green-grey square-tube legs, two steel drawers with chrome bar pulls and brass card holders, and a lower shelf
with two film cans and a carton. On the bench, left to right as the player sees it:
- a walnut **light box** with a dark steel bezel, chrome screws and a toggle switch, and its cloth flex
  dropping behind the bench;
- the four loose **film strips** on its opal glass;
- a black cast-iron **butt-splicing block**: a chrome film channel with four brass gate plates, engraved cut
  marks between the gates, hinged chrome pressure clamps standing open behind each gate, guide rollers at
  both ends, and a brass "35 mm" plate;
- behind the block, an open empty **reel can** with a slack curl of torn leader inside, its **lid propped
  against the wall** facing the player;
- at the back right, a **rewind** with a horizontal chrome spindle toward the player and a crank with a
  walnut grip at the back;
- dressing: a film-cement bottle (amber glass, knurled cap), scissors and a red china marker.

**Size:** the bench is 1.20 × 0.60, top y = 0.90, front edge at z = 0.604. The tallest part is the propped lid
(y 1.097). Nothing is above y 1.10, so it stays clear of the booth shelf (y 1.42 underside, model z < 0.26).
**Origin:** on the floor at the centre of the back face (the wall plane).

| Part | Pivot (model-local) | Axis | Rest → active / notes |
|---|---|---|---|
| `IA_frame_0..3` | centres (−0.465, 0.9503, 0.405), (−0.355, 0.9503, 0.262), (−0.255, 0.9503, 0.425), (−0.150, 0.9503, 0.275) | — | Loose strips on the light-box glass (top y 0.950), k = 0..3 left → right in two staggered rows. Each is a 0.15 (local X) × 0.05 (local Z) top quad with **UV 0..1** and `M_Decal_FilmStrip_<k>` (image top toward −Z, so it reads upright from the front), plus an `M_Film` underside quad. The decal carries the sprocket holes (alpha scissor). **The scatter is the node's rest rotation:** yaw −6°, +5°, −3°, +7° about +Y. The mesh is straight along local X, so `_apply_splicer`, which copies the `slot_mount_<s>` transform, lays the strip straight in the channel. These are the only parts whose rest rotation is not identity |
| `IA_slot_0..3` | (0.065 + 0.15·s, 0.931, 0.45): the gate-plate top centres | — | Static tap targets: brass plates 0.145 × 0.052 × 0.002 in the chrome channel (rails z 0.405–0.423 and 0.477–0.495, top y 0.9365). Pitch 0.15 = the strip length, so four placed strips butt end to end into one continuous film (x −0.010 … 0.590) |
| `slot_mount_0..3` (empties) | (0.065 + 0.15·s, 0.9318, 0.45), identity | — | A strip placed with identity lies flat on its gate plate, 0.7 mm above it, long axis along X, image upright |
| `splicer_reel_mount` (empty) | (0.45, 1.05, 0.266), identity | — | `film_reel.glb` (Ø 0.18 × 0.02, face +Z) sits on the rewind spindle: flange behind it at z 0.250–0.256, knurled nut in front at z 0.278–0.291. Reel bottom at y 0.96, above the bench. Checked with the real item |
| `light_box_glass` | (−0.31, 0.950, 0.335) | — | Opal glass 0.499 × 0.339 × 0.0065, `M_Glass_Frosted`; the code sets its emission |
| `reel_can_lid` | (0.20, 0.9998, 0.0354), identity (the tilt is baked into the mesh) | — | A pressed steel lid Ø 0.20 with a 10 mm lip. It leans 14° back from vertical: the lip's top edge touches the wall (z = 0), the bottom edge stands on the bench at z ≈ 0.05. **Top face:** a 36-gon disc, r 0.0994, with planar **UV 0..1** over its bounding square (the image circle fills the square) and `M_Decal_ReelCanLid`. u runs along +X; v runs up the lid (image top toward the wall/up). The disc faces (0, 0.24, 0.97), 20° off the splicer camera's line of sight |
| `bench`, `light_box`, `splice_block`, `rewind`, `reel_can`, `bench_dressing` | (0, 0, 0) | — | static, split so none covers a tap target from the splicer view |

**Puzzle check:** in the QA "placed" render the strips sit in the solution order f2, f0, f3, f1 (slots 0..3).
The lid pictogram and its "E.S. · 1979" tag read clearly from the contract splicer camera.

---

## slide_cabinet.glb (4,610 tris)

**Shape:** a walnut lantern-slide cabinet with a cove cornice and an overhanging top, a frieze rail with a
blank brass card holder, five shallow drawers on rails with dust boards behind them, a two-door panelled
cupboard below (turned knobs, an escutcheon), and a moulded base on a recessed plinth. Each drawer front
carries a pressed brass frame with a **cream enamel plaque and a raised black symbol**: 0 ring, 1 triangle,
**2 four-pointed star (✦)**, 3 square, 4 Greek cross. It also has two brass cup pulls. Inside each drawer is a
raised felt-lined tray (felt 6.2 cm above the drawer's bottom edge, so the drawer front does not hide the front row) with walnut dividers: 3 rows × 4 compartments of lantern slides in cream/buff card mounts with
dark (a few amber) glass windows, lying flat, with a few gaps and a little jitter.

**Size:** 0.46 w × 1.05 h × 0.45 d (top 0.512 × 0.478 with its overhang). **Origin:** on the floor, on the
wall plane, at the contract placement point. **The body is centred at local x = +0.135** (see the deviation).

| Part | Pivot (model-local) | Axis | Rest → active / notes |
|---|---|---|---|
| `IA_slide_drawer_<i>` | (0.135, y_i, 0.45), the drawer-front face centre, with y_i = 0.895, 0.785, 0.675, 0.565, 0.455 for i = 0..4 (drawer 0 at the top) | local **+Z** | Slides out **0.28**. Fronts are 0.418 × 0.10, flush with the carcass. Each drawer is **one mesh** (front, plaque, pulls, tray, slides), so `ModelUtil.set_emission` lights the whole drawer for Leyla's echo |
| `slide_mark_mount` (child of `IA_slide_drawer_2`) | local (−0.0475, 0.0134, −0.074); model (0.0875, 0.6884, 0.376); identity | — | The front-row compartment just left of centre, on the felt (felt top y 0.687). `glass_slide.glb` lies flat, face up, image top toward −Z (the drawer back). Its lowest point is 1.4 mm below its origin, checked with the real item |
| `carcass` | (0, 0, 0) | — | static |

**Deviation (layout).** The cabinet is 0.46 wide instead of 0.60, and its body is offset 0.135 along local +X
(world north). With the contract placement, a centred 0.60 cabinet spans world z 2.50–3.10. Its open drawers
(out to world x −4.27) would run into the film-splicer bench, which spans x ≥ −4.50 and z ≥ 2.896 (top, apron,
front leg). Moving the cabinet north alone hits room A's fire bucket on the booth's north wall
(x −4.74…−4.46, y 0.80…1.24, z 2.12…2.39). Now:
- the carcass spans world z 2.409–2.921, top overhang included (the bench is lower and further east);
- the open drawers span z 2.456–2.874: 2.2 cm clear of the bench and 1.6 cm clear of the bucket.
The cabinet now stands right in front of Leyla's echo at (−4.15, 0, 2.62).

**Camera.** With the contract slides camera, (−3.85, 1.3, 2.8) → (−4.8, 0.7, 2.8), the open drawer's front row
(where the mark slide lies) falls on the bottom edge of the frame, and the splicer bench fills the left
third. Suggested: **(−3.80, 1.32, 2.70) → (−4.62, 0.64, 2.68), FOV 48** (`slide_cabinet_4.png`). The
cabinet's centre is world z 2.665.

---

## lens_case.glb (1,816 tris)

**Shape:** a walnut case with rounded vertical corners and eight brass corner caps. It has a brass name plate
on the lid, two brass butt hinges at the back, and a brass hook catch over a staple at the front. Inside is a
crimson velvet insert with two round pockets (r 0.0295), each with a finger notch toward the hinge. The lid is
velvet padded.

**Size:** 0.24 × 0.070 × 0.13 (0.243 × 0.072 × 0.139 with the hardware). **Origin:** the centre of the
underside.

| Part | Pivot (model-local) | Axis | Rest → active / notes |
|---|---|---|---|
| `IA_case_lid` | (0, 0.048, −0.065): the hinge axis on the back top edge of the base | local **+X** | Open = **−105°** (`CASE_LID_DEG`). It swings up and back toward the wall and stops ≈ 8 mm short of it (measured in QA: lid back at world z 3.49x, wall at 3.50) |
| `crystal_mount_1` | (−0.055, 0.0381, 0.006), rotation **−90° about X** | — | Player's left pocket. `lumen_crystal.glb` (natural pose on edge, face +Z) lies **face up** with its grip tab toward −Z, into the finger notch. The pocket floor is at y 0.034, and the crystal's lowest point is 4.1 mm below its origin |
| `crystal_mount_2` | (+0.055, 0.0381, 0.006), rotation −90° about X | — | Player's right pocket, same |
| `case_base` | (0, 0, 0) | — | static |

**Deviation:** depth 0.13 instead of 0.16. At −105°, a 0.16-deep lid reaches 0.066 behind the hinge; the
case's back is only 0.05 from the booth wall (z 3.37 + 0.08), so the open lid would cut 1.6 cm into the wall.
At 0.13 deep, the back is at world z 3.435 and the open lid stays in front of the wall.

---

## reading_table.glb (4,888 tris)

**Shape:** a long walnut library table with a thick top and a moulded thumbnail edge. Aprons carry a beaded
lower edge and a shallow centre drawer (two brass knobs, an escutcheon). Four turned legs stand on an H
stretcher. Dressing:
- a **brass banker's lamp** at the back centre: a stepped base, a knurled collar, a crook stem, a green
  cased-glass shade (white inside) tilted 13° toward the reader, a bead pull chain, and a cloth flex over
  the back edge;
- two open ledgers with ruled ink entries and a red margin line;
- a closed pair of ledgers at the back right;
- a brass reading magnifier on a stand at the back left.

The spots the code uses for the CC0 magnifying glass, model (+0.35, 0.12), and the spectacles, model
(−0.45, −0.14), are kept free.

**Size:** 1.40 × 0.80, top y = 0.76; lamp top y 1.153. **Origin:** the footprint centre on the floor.

| Part | Pivot (model-local) | Notes |
|---|---|---|
| `lamp_shade` | (0, 1.124, −0.187), the shade apex | `M_Glass_Green` outside, `M_Enamel_White` inside; its own object |
| `bulb` | (0, 1.0811, −0.1771), the bulb centre | `M_Emissive_Warm`; the code sets its emission |
| `light_origin` (empty) | (0, 1.0811, −0.1771) | **World (1.90, 1.081, 0.823).** `archive_room.gd` puts the banker OmniLight at (1.9, 1.15, 1.25), 0.43 m in front of the lamp. Move it to `light_origin`, or to about (1.9, 1.0, 0.95) to light the ledgers in front of the lamp |
| `table`, `banker_lamp`, `table_dressing` | (0, 0, 0) | static |

---

## archivist_desk.glb (5,674 tris)

**Shape:** an institutional pedestal desk in `M_Wood_Panel`. It has a top with a rounded edge and a
**green writing inlay** framed by a dark groove line. The left pedestal has three drawers; the right has a
drawer over a panelled cupboard (knob, escutcheon). There is a centre drawer over the kneehole, a panelled
modesty board, raised fields on the pedestal sides, and recessed plinths. Brass cup pulls and brass card
holders are on every drawer.

A low **pigeonhole gallery** (4 × 2 cells, x ±0.25, depth 0.10, **top y 0.995**) holds paper stacks,
envelopes, a tied card bundle and a rolled drawing.

Dressing, laid out around the spots the code fills (model coords):

| Code-placed item | Footprint kept free |
|---|---|
| `card_punch` | x −0.64…−0.26, z −0.10…0.20 |
| `tape_deck` | x 0.21…0.69, z −0.14…0.24 |
| `desk_lamp` | around (−0.65, −0.22) |
| CC0 book set | x 0.30…0.84, z −0.32…−0.16 |

- **Two-tier chrome wire in/out trays** with papers: x −0.495…−0.295, z −0.37…−0.10.
- **Bakelite rotary telephone**: body 0.20 × 0.23 with the dial on its sloped front, handset on the cradle,
  coiled cord. At (−0.055, −0.14).
- **Rubber-stamp carousel** (six stamps) at (0.13, −0.19).
- **Blotter pad** with leather corners, three loose cards and a pencil: x −0.215…0.17, z 0.035…0.33.
- **Card-file box** with its lid propped open and a label holder, in the front-left corner at (−0.645, 0.29).

**Size:** 1.50 × 0.75 (+1.9 cm of pulls), top y = 0.76. **Origin:** the footprint centre on the floor.
**Parts:** none (no IA parts); static meshes `desk`, `gallery`, `desk_dressing`.

**Deviation:** the writing inlay uses `M_Book_Green` (dark green leather-cloth) instead of linoleum, because
the `M_Linoleum` slot is the floor's 0.6 m checker texture. It sits 0.4 mm proud of y 0.76, so items placed
at y 0.76 sink by an invisible 0.4 mm.

**Note for the code:** the CC0 book set at (4.0, 0.76, −3.36) runs from its origin toward +X, 0.54 long, so
it overhangs the desk's right edge (world x 4.45) by about 9 cm. x ≈ 3.88 keeps it on the desk, next to the
gallery.

---

## QA renders (`qa/blender/ch2/`)

QA_LIST_PLACEHOLDER
