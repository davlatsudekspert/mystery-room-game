# Chapter 1 — Laboratory 7: Room Layout & Model Specification (authoritative)

## Coordinates
- **Godot:** Y up, metres. The camera looks along −Z by default.
- **Blender:** Z up. Convert with **Blender (x, y, z) = Godot (x, −z, y)**.
- **Model orientation:** unless stated otherwise, each model is built at its own origin. Its **front faces Blender −Y**, which becomes Godot +Z after glTF export. Its base sits on Z = 0. Wall-mounted models have their **back plane at Blender Y = 0** and protrude toward −Y. The lead places and rotates the models in Godot.
- **Exception:** `room_lab7.glb` is built directly in room coordinates.

## Room shell (Godot coordinates)
- **Lab 7 interior:** x ∈ [−3, 3], z ∈ [−2.5, 2.5], floor y = 0, ceiling y = 3.4. Walls are 0.2 m thick (outside the interior box).
- **North wall (z = −2.5):** window opening x ∈ [0.95, 2.05], y ∈ [1.45, 2.85]. It has a deep reveal, a stone sill, a wooden casement with mullions, glass, and 4 iron bars on the outside face.
- **East wall (x = +3):** door opening z ∈ [0.4, 1.4], y ∈ [0, 2.2].
- **South wall (z = +2.5):** safe recess x ∈ [1.95, 2.45], y ∈ [1.0, 1.5], 0.30 deep, lined with dark steel.
- **West wall (x = −3):** bookshelf-door opening z ∈ [−1.15, −0.05], y ∈ [0, 2.15], through to the secret room. Vent grille at (−2.98, 2.9, 1.5), size 0.5 × 0.3.
- **Secret room ("Leyla's dark room"):** x ∈ [−4.8, −3.2], z ∈ [−1.6, 0.4], ceiling y = 2.6.
  - plain stained plaster walls
  - a bare-bulb fixture at (−4.0, 2.6, −0.6)
  - the floor continues the parquet
- **Wall finish:**
  - walnut wainscot panels (raised frames) from 0 to 1.05 m
  - chair rail
  - aged plaster above
  - crown moulding
  - baseboards
- **Ceiling:**
  - plaster
  - two walnut beams running E–W at z = −0.9 and z = +0.9
  - ceiling roses at the pendant positions
- **Dressing in the shell:**
  - cast-iron radiator under the window (centre x = 1.5)
  - metal conduit and copper pipes from Panel 7 (east wall) up along the wall and across the ceiling
  - a small pipe into the vent

## Furniture & prop placement (Godot coordinates; "faces" = direction the model's front points)
| Model | Position | Faces | Notes |
|---|---|---|---|
| desk | (−0.5, 0, −2.1) | +Z | 1.50 w × 0.78 h × 0.72 d. Rosette and compartment on its **east (+X) side** |
| chair | (−0.4, 0, −1.35) | −Z | rotated slightly |
| flip_clock | on desk (−1.0, 0.78, −2.25) | +Z | |
| notebook | on desk (−0.3, 0.78, −1.95) | | |
| desk_lamp | on desk (−1.15, 0.78, −2.3) | +Z | |
| filing_cabinet | (−2.6, 0, −2.2) | +Z | |
| bookshelf (hidden door) | back at x = −3.1, z ∈ [−1.15, −0.05] | +X | 1.10 w × 2.10 h × 0.36 d. **Hinge at its back-north-bottom corner**. Swings 85° into the secret room |
| gear_box | on bookshelf shelf at y ≈ 1.22 | +X | |
| chalkboard | west wall x = −2.97, centre z = 1.05, y ∈ [1.0, 2.0] | +X | 1.6 × 1.0 |
| lumen_projector | (−2.3, 0, 1.6), beam origin at height 1.15 | beam → +X | |
| mirror_stand A | (1.6, 0, 1.6), mirror centre at height 1.15 | | has its mirror |
| mirror_stand B | (1.6, 0, 0.12), mirror centre at height 1.15 | | empty bracket until the mirror item is mounted |
| light_sensor | east wall (2.97, 1.15, 0.12) | −X | |
| lab_bench | (−0.3, 0, 2.15) | −Z | 2.2 w × 0.92 h × 0.65 d |
| vial rack | on bench (−0.9, 0.92, 2.1) | | |
| radio | on bench (0.55, 0.92, 2.2) | −Z | |
| poster_frame | south wall (−0.3, 1.9, 2.48) | −Z | |
| wall_safe | south wall recess, centre (2.2, 1.25, 2.5) | −Z | front flush with the wall |
| panel7 | east wall (2.97, 1.45, −1.3) | −X | |
| door_lab7 | east wall opening, z centre 0.9 | −X | |
| coat_rack | (2.6, 0, −2.15) | | |
| pendant_lamp ×2 | (−0.6, 3.4, −0.6), (1.2, 3.4, 0.8) | | |
| secret room: evidence_board | west wall of secret room x = −4.78, z ∈ [−1.3, 0.1], y ∈ [1.0, 2.0] | +X | |
| secret room: shadow_lock | lamp at (−4.0, 1.2, 0.15) shining toward −Z. Sculpture at (−4.0, 1.25, −0.6). Emblem painted on the north wall (z = −1.6) at (−4.0, 1.5) | | |
| secret room: shadow cabinet | north wall (−4.0, 0.55, −1.58) | +Z | small wall cabinet with a door |

**Player viewpoints:**
- Lab centre: (0.2, 1.55, 0.2).
- Secret room: (−3.35, 1.5, −0.6), looking −X.

## Interactive part naming (MUST match exactly; Godot binds behaviour by name)
Each `IA_*` part is a **separate object** with its **origin at the pivot** (hinge axis, axle centre, slide start).
Decal materials (`M_Decal_*`) need explicit 0..1 UVs as described. All other faces get world-scale box UVs (`mrlib.finalize`).

| File | Parts |
|---|---|
| `room_lab7.glb` | static. Includes `window_glass`. **No `IA_*` parts** |
| `door_lab7.glb` | `IA_door_leaf` (origin on the hinge axis, at floor level; the hinge is on the south edge (Godot +Z side); the leaf opens into the corridor (+X)), `IA_door_handle`, `maglock_lamp` (material `M_Emissive_Red`). Frame casing is static. Frosted glass upper panel with a gold numeral **7** (text geometry) |
| `desk.glb` | `IA_drawer_top` (centre top drawer; origin at its front-bottom-centre; slides out along Godot +Z); `IA_drawer_digit_0..3` (4 brass combination wheels on the drawer front, left to right; axle along X; origin at axle centre; wheel rim faces use `M_Decal_DrawerDigits` with `mrlib.cylinder_uv(axis='X')`, oriented so the digit **0** is centred facing the viewer (Godot +Z) at rest); `IA_rosette` (carved rosette on the **east side** panel, upper rear area; origin at its centre); `IA_secret_panel` (thin panel below the rosette; slides down 6 cm to reveal the keyhole); `IA_keyhole` (brass escutcheon behind the panel); `IA_compartment` (shallow hidden drawer in the east side; origin at its outer face centre; slides out along Godot +X). Wheels and keyhole must be parented or positioned so they move correctly with the drawer and compartment (the lead animates `IA_drawer_top` and moves the wheels with it) |
| `flip_clock.glb` | `clock_face` (front plane, `M_Decal_ClockFace`, planar UV along Blender Y, texture aspect 512:224) |
| `gear_box.glb` | `IA_gear_0..2` (three brass gears visible on the top plate, meshing; each has a pointer; rotate about the vertical axis; origin at gear centre; **pointer at rest points toward Godot −Z (the back)** = position 0); `IA_knob_0..2` (front knobs below each gear); `IA_box_lid` (lid; origin on the back hinge) |
| `wall_safe.glb` | `IA_safe_door` (origin on the **left** hinge when facing the safe); `IA_key_0..9`, `IA_key_clear`, `IA_key_enter` (raised keys with engraved text geometry; 3 × 4 grid: 1 2 3 / 4 5 6 / 7 8 9 / C 0 ↵); `safe_display` (small dark glass window above the keys); `IA_safe_handle` (spoked wheel); interior shelf |
| `panel7.glb` | enclosure (0.70 w × 0.90 h × 0.22 d) with the door open about 100° (static). `panel_plate` (0.60 × 0.80 back plate, `M_Decal_PanelDiagram`, planar UV, texture aspect 900:1200). Plate-local coordinates (metres, origin at plate centre, x right, y up): lamps `lamp_0..3` at y = +0.30, x = −0.195, −0.065, +0.065, +0.195, with materials `M_Lamp_L`, `M_Lamp_G`, `M_Lamp_A`, `M_Lamp_V`; toggle switches `IA_switch_0..4` at y = −0.06, x = −0.22, −0.11, 0, +0.11, +0.22 (pivot on the horizontal axle; rest = down/OFF); main breaker `IA_main_lever` at (0, −0.27) (pivot; rest = down/OFF) plus a **separate** `main_handle` (bakelite grip, hidden until installed); `gauge_needle` in a small round gauge at (−0.22, +0.15)? (optional; keep clear of the traces) |
| `lumen_projector.glb` | brass apparatus on a wooden tripod. The beam axis is along the model's **front (Blender −Y)** at height 1.15. `IA_lens_socket`, `lens_installed` (crystal lens, hidden until inserted); `IA_ring_0..2` (three rings around the barrel, rotating about the beam axis; each has 6 enamel segments in order crimson, amber, green, cobalt, violet, white, with materials `M_Enamel_Crimson`, `M_Enamel_Amber`, `M_Enamel_Green`, `M_Enamel_Cobalt`, `M_Enamel_Violet`, `M_Enamel_White`, and 1–6 small raised notches respectively for colour-blind players; a fixed index mark on the barrel at 12 o'clock; at rest the **white** segment is under the index); `IA_projector_lever`; empty `beam_origin` at the lens front centre |
| `radio.glb` | 1950s valve radio: wooden cabinet, fabric speaker grille, curved glass dial window. `radio_dial` (plane, `M_Decal_RadioDial`, planar UV, aspect 1024:256); `dial_needle` (slides along the dial's X; at rest at the left end, u = 0.06); `IA_tuning_knob`; `IA_radio_hatch` (top-back hatch; origin at hinge); `IA_valve_socket`; `valve_installed` (hidden until inserted); `magic_eye` (small round tuning-indicator glass, material `M_Emissive_MagicEye`) |
| `mirror_stand.glb` | brass tripod stand. `IA_mirror_mount` (gimbal; rotates about the vertical axis; origin at the mount centre at height 1.15); `mirror` (round 0.22 m mirror, `M_Chrome` face and brass frame, child of the mount, separate so it can be hidden) |
| `light_sensor.glb` | brass photocell on a wall plate; `sensor_eye` (glass, `M_Emissive_Lumen`) |
| items (each its own file, origin at the centre of mass, sized realistically) | `notebook.glb`, `uv_lamp.glb` (lens part `uv_lens`), `battery_cell.glb`, `brass_key.glb`, `crystal_lens.glb`, `breaker_handle.glb`, `letter.glb` (folded letter + envelope with wax seal), `radio_valve.glb` (vacuum tube), `mirror_item.glb`, `lumen_shard.glb` (`M_Crystal`) |
| `bookshelf.glb` | walnut bookcase that is a hidden door. **Origin = hinge** at its back-north-bottom corner, which in model space is the back-left corner when facing the front. 5 shelves. Shelf 3 (y ≈ 1.20) keeps a 0.32 m wide clear spot in the middle for the gear box. Encyclopedia set `IA_book_1..9` (identical dark-green leather volumes with gold Roman numerals I–IX on the spines, in order) on shelf 2 (y ≈ 0.85); each book's origin is at its bottom-back edge so it can tilt out. Other books use `M_Book_Red`, `M_Book_Green`, `M_Book_Brown`, `M_Book_Blue` and `M_Book_Black` |
| `lab_bench.glb` | bench with cabinets and a dark top. `vial_rack` with `IA_vial_green`, `IA_vial_crimson`, `IA_vial_cobalt` in that left-to-right order, liquid materials `M_Liquid_*`, and paper labels `vial_label_<colour>` with `M_Decal_VialLabel_Crimson`/`_Cobalt`/`_Green` (planar UV, aspect 2:1). Also flasks, beakers, a retort stand, a burner and a microscope |
| `chalkboard.glb` | frame + board (`M_Decal_Chalkboard`, planar UV, aspect 1024:640) + chalk tray with chalk |
| `poster_frame.glb` | thin black frame + glass + paper (`M_Decal_Poster`, planar UV, aspect 1024:1448) |
| `desk_lamp.glb`, `pendant_lamp.glb` | each has a `bulb` object (`M_Emissive_Warm`) and an empty `light_origin` at the bulb centre |
| `chair.glb`, `filing_cabinet.glb`, `coat_rack.glb` (with a hanging coat and hat), `radiator` (inside the shell) | static |
| `evidence_board.glb` | cork board (1.4 × 1.0) with pinned photo cards (paper planes `photo_0..7`, material `M_Decal_Photos`, 0..1 UV each) and red string |
| `shadow_lock.glb` | small table; `spot_lamp` (old stage lantern) with an empty `light_origin`; gimbal sculpture: `IA_ring_knob` + `sculpture_ring` (brass ring, radius 0.10, rotates about the vertical axis), `IA_rod_knob` + `sculpture_rod` (brass rod 0.28 long, rotates about the lamp→wall axis). At rest both are misaligned: the ring is yawed 60° and the rod is tilted 60°. `shadow_cabinet` with `IA_cabinet_door` (origin on the hinge). Layout: model-local positions match the placement table, relative to the lamp |

## Decal textures (already generated; `game/assets/textures/decals/`)
| File | Content |
|---|---|
| `drawer_digits.png` | 1024×128. Digit *k* is centred at u = (k + 0.5)/10 |
| `clock_face.png` | 512×224. Shows `03 17` |
| `poster_resonance.jpg` | 1024×1448 |
| `chalkboard.jpg` | 1024×640 |
| `panel_diagram.jpg`, `panel_diagram_0..7.jpg` | 900×1200, matching plate coordinates; one plate per Panel 7 wiring (`panel_diagram.jpg` = wiring 0) |
| `radio_dial.jpg` | 1024×256 |
| `vial_label_{crimson,cobalt,green}.png` | 256×128 |
| `childs_drawing.jpg` | |
| `window_night.jpg` | |
| `wall_emblem.png` | |
| `uv_desk_mark.png` | |
| `notebook_page.jpg` | |

In Blender, decal materials can preview the texture with `mrlib.material(name, image=<abs path>)`.

## Budgets
| Category | Triangle budget |
|---|---|
| Hero props | ≤ 6k |
| Bookshelf with books | ≤ 12k |
| Lab bench with glassware | ≤ 12k |
| Room shell | ≤ 15k |
| Small items | ≤ 2.5k |

All hard edges are bevelled.
