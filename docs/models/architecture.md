# Architecture & furniture models: dimensions, parts and animation spec

Built by `tools/blender/models/<name>.py` (helpers: `tools/blender/mrlib.py`, `tools/blender/lib_arch.py`).
Every script is listed in `tools/blender/build_lists/architecture.txt` and supports `-- --no-render`:

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [-- --shot=N ...]
```

Output goes to `game/assets/models/<name>.glb`, and QA renders go to `qa/blender/<name>*.png`.
The GLBs carry base-colour materials only. The game swaps every `M_*` slot for `res://assets/materials/<slot>.tres` (`ModelUtil.apply_materials`).

## Conventions
- **Godot terms:** all coordinates below are in Godot terms, in metres, with **Godot = Blender (x, z, −y)**. Model-local means relative to the model root, and room means the Lab 7 scene.
- **Model front:** a model's front faces **+Z**, unless it says otherwise.
- **Pivots:** every animated part is its own node. Its origin is at the pivot, and its rotation is the **identity at rest**.
- **Angles:** angles are relative to the rest transform. This matches `Lab7Visuals._rot(node, axis, deg)`, which computes `rest.basis * Basis(axis, deg)`.
- **Sign:** a positive angle is counter-clockwise when you look down the +axis.
  - About **+Y**, a positive angle turns +Z toward +X, which is counter-clockwise seen from above.
  - About **+Z**, a positive angle turns +X toward +Y.

| Model | Tris | Size (Godot x × y × z) | Parts |
|---|---|---|---|
| `room_lab7` | 13,032 (budget 15k) | 8.20 × 3.67 × 5.53 (shell incl. darkroom) | static + `window_glass`, `darkroom_bulb`, `darkroom_light_origin` |
| `door_lab7` | 5,930 | 1.25 × 2.71 × 0.34 | `IA_door_leaf`, `IA_door_handle`, `maglock_lamp`, `door_frame` |
| `chair` | 3,680 | 0.44 × 0.94 × 0.53 | static |
| `filing_cabinet` | 3,798 | 0.50 × 1.32 × 0.60 (0.70 with the ajar drawer and pull) | static |
| `coat_rack` | 5,960 | 0.55 × 1.98 × 0.57 | static (`coat_rack_body`, `coat`) |
| `desk` *(earlier)* | 7,732 | 1.50 × 0.78 × 0.74 | see below |
| `pendant_lamp` *(earlier)* | 3,852 | 0.43 × 1.13 × 0.43 | `bulb`, `light_origin` |

---

## room_lab7.glb — static shell in ROOM coordinates
Place it at the origin with no rotation.

**Collider mode `static`:** every mesh gets a trimesh collider. The walls, ceiling and floor are **closed solids** of 0.2 m (the floor and ceiling slabs are 0.12 m and 0.15 m), so the directional moon light is blocked everywhere except through the window. Nothing outside the wall thickness is modelled.

**Objects (grouped by material):**

| Object | Contents | Material(s) |
|---|---|---|
| `room_walls` | lab and darkroom walls with the openings cut by boolean | `M_Plaster_Wall`; the darkroom faces use **`M_Plaster_Stained`**; the vent recess uses `M_Steel_Dark` |
| `room_floor` | one big parquet plane per room, with world UVs. The parquet continues through the bookcase opening | `M_Wood_Floor` |
| `room_ceiling` | ceiling slabs, plaster crown and 2 ceiling roses | `M_Ceiling` |
| `room_wainscot` | wainscot backing boards, raised fields, plain darkroom skirting | `M_Wood_Panel` |
| `room_woodwork` | panel mouldings, chair rail, baseboard, 2 beams + 4 corbels, window architrave, casement | `M_Wood_Walnut` |
| `room_stone` | window sill + bed moulding | `M_Stone` |
| `room_metal` | radiator, window bars, conduit, safe liner, junction box | `M_Steel_Painted` (radiator), `M_Steel_Dark` (the rest) |
| `room_copper` | radiator flow/return pipes, copper pipe | `M_Copper` |
| `room_brass` | vent grille, valves, couplings, window fittings | `M_Brass_Aged`, `M_Bakelite` |
| `window_glass` | 2 sash panes + fanlight, each 4 mm thick | `M_Glass` |
| `darkroom_fixture` | bakelite rose, cloth cord, socket | `M_Bakelite`, `M_Fabric`, `M_Brass_Aged` |
| `darkroom_bulb` | red darkroom **safelight** bulb. Origin at the bulb centre, **(−4.0, 2.29, −0.6)** | `M_Emissive_Red` |
| `darkroom_light_origin` | empty at (−4.0, 2.29, −0.6) | — |

`darkroom_bulb` hangs on a 0.16 m cord from the ceiling point (−4.0, 2.6, −0.6). Toggle it with `ModelUtil.set_emission(...)` as you do for the pendant `bulb`. The current safelight OmniLight at (−3.6, 2.3, −0.6) is close to it, but you can move the light to the bulb if you want.

**New material slot `M_Plaster_Stained`:** I added `game/assets/materials/M_Plaster_Stained.tres`. It uses the plaster_wall textures with a yellow-brown tint (0.66, 0.58, 0.47) and normal 0.45.

### Shell geometry

**North wall (z = −2.5): window x [0.95, 2.05], y [1.45, 2.85]**
- **Reveal:** plaster reveal, 0.08 deep from the room face to the frame.
- **Architrave:** walnut architrave, 0.095 wide and 0.03 proud.
- **Stone sill:**
  - top at **y = 1.47**;
  - projects 0.14 m into the room (front edge at z = −2.36);
  - its horns run x [0.83, 2.17];
  - it carries the `cc_kettle` and `cc_compass` at y = 1.47.
- **Casement:** the frame sits at z [−2.66, −2.58]. Inside it are a transom at y 2.33–2.40, a mullion at x 1.47–1.53, two side-hung sashes with 2 × 3 panes each, and a 3-pane fanlight.
- **Window fittings:** a brass espagnolette and two stays.
- **Bars:** 4 iron bars at x = 1.17 / 1.39 / 1.61 / 1.83, z = −2.684, with r 0.012. Two flat ties at y 1.82 and 2.50.

**Radiator (under the window)**
- **Body:** centre x 1.5. The 12 sections span x [1.09, 1.91] and y [0.11, 0.79]. The front face is at **z = −2.295** and the back at −2.445.
- **Feet:** at x 1.115 and 1.885, with r 0.026.
- **Pipework:** an angle valve and copper flow at x 1.04, and a lockshield and return at x 1.96.

**East wall (x = +3): door opening z [0.4, 1.4], y [0, 2.2]**
- The opening is cut through the wall. The frame, casing and threshold are in `door_lab7`.
- The baseboard, chair rail and wainscot stop at z = 0.30 and z = 1.50, which is 0.10 m outside the opening, where the door casing and plinth blocks take over.

**South wall (z = +2.5): safe recess x [1.95, 2.45], y [1.0, 1.5]**
- **Recess:** 0.30 deep (to z = 2.80). Its inner faces are exactly on these bounds, with a 6 mm `M_Steel_Dark` liner outside them.
- **Flange:** a 0.03-wide steel flange, 16 mm proud.
- **Chair rail:** the chair rail is cut for x [1.92, 2.48].

**West wall (x = −3): bookcase opening z [−1.15, −0.05], y [0, 2.15]**
- The opening goes straight through, with an 8 mm soft plaster arris.
- **Vent:** a brass louvred vent centred (−2.98, 2.9, 1.5), 0.5 × 0.3. It has a 7 cm dark recess behind the louvres.

**Darkroom: x [−4.8, −3.2], z [−1.6, 0.4], ceiling 2.6**
- stained plaster;
- plain 0.12 m skirting;
- parquet floor.

**Wall finish (lab)**
- **Panels:** 0.012 walnut-panel backing from 0 to 1.0, with raised fields and ogee mouldings. The panels run y 0.26–0.88. On the N and S walls there are 10 per wall, centred so that one panel sits under the window centre.
- **Chair rail:** y 0.985–1.055, 0.03 proud.
- **Baseboard:** 0.17 high, 0.032 proud.
- **Crown:** plaster crown, 0.15 deep and 0.14 projection.

**Ceiling**
- **Beams:** two chamfered walnut beams running E–W at **z = ±1.05**, 0.17 wide, with their bottom at y = 3.18. Each beam end has a walnut corbel (y 2.90–3.18).
- **Roses:** 0.14 radius, at (−0.6, 3.4, −0.6) and (1.2, 3.4, 0.8). The pendant canopies sit in their flat centres.
- **Why ±1.05 and not ±0.9:** `pendant_lamp_2` hangs at z = 0.8. A beam centred on 0.9 would have swallowed its canopy and rose.

**Services**
- **Conduit:** a steel conduit (r 0.013, at z −1.22) and a copper pipe (r 0.009, at z −1.40) leave the top of Panel 7 at y 1.88.
  - They run up the east wall, at 0.03 / 0.025 off the plaster.
  - They offset diagonally under the crown and run west along the ceiling.
  - The conduit ends in a cast junction box at (−0.6, 3.35, −1.22).
- **Copper pipe:** the copper pipe continues to the west wall. It drops under the beam corbels to y = 2.86, runs south along the wall and enters the vent's north side through a brass gland.

**Clear zones kept for wall-mounted props** (no trim crosses them):

| Prop | Wall | Clear zone |
|---|---|---|
| Panel 7 | east | z [−1.65, −0.95], y [1.0, 1.9]; chair rail cut |
| chalkboard | west | z [0.25, 1.85], y [1.0, 2.0]; chair rail cut, so the board sits on the wainscot top at y 1.0 |
| poster | south | x −0.3, y ≈ 1.9 |
| light sensor | east | (3, 1.15, 0.12) |

### Notes for the lead

**Bookcase swing clearance**
With the documented hinge at (−3.1, 0, −1.15), a pure −85° yaw sweeps the bookcase's front-south corner (including its 0.05 cornice; radius ≈ 1.17 m) up to about **7 cm past the south jamb** (z ≈ +0.02, around 20° open). This is hidden inside the wall thickness most of the way.
- If it is visible, translate the case about 0.08 along +X during the first 25°.
- Or accept it: the corner passes behind the bookcase body itself.

**`radiator` shard (1.85, 0.08, −2.38)**
- The shard sits 9 mm from the right foot (x 1.859–1.911), under the body (bottom y 0.11) and 8.5 cm behind the front face.
- It is occluded by the sections from the `radiator` view.
- Suggested position: **(1.78, 0.05, −2.33)**. This is between the feet, just behind the front plane, and is visible from a low camera.

---

## door_lab7.glb — panelled institute door (east opening)

**Placement (current code):** `Vector3(3.0, 0, 0.9)`, yaw −90°.
- **Model origin:** the centre of the 1.0 m opening, at floor level, on the room-side wall plane.
- **Model axes:**
  - model **+X** → room **+Z (south)**;
  - model **+Z** (front) → room **−X**, facing into the lab;
  - model **−Z** → corridor (room +X).
- **Wall thickness:** occupies model z ∈ [−0.2, 0].

**Contents**
- **Frame:** mahogany jamb linings with stops, 1 m × 2.2 m. The clear leaf opening is x ±0.465, y < 2.165.
- **Architrave:** a walnut architrave, 0.11 wide, with plinth blocks of 0.23 at x ±(0.482 … 0.605). The room baseboard dies into them. The head is capped at y 2.285–2.321.
- **Threshold:** stone.
- **Hinges:** 3 brass hinge knuckles on the corridor face.
- **Maglock unit:** above the head cap, x [−0.30, 0.055], y [2.335, 2.425]. It has a cream "MAGNETIC LOCK" label, a chrome bezel, and an armoured cable that runs into the wall.
- **Leaf:**
  - 0.924 × 2.146 × 0.05 mahogany, with the grain running along each member;
  - 2 fielded lower panels;
  - a frosted upper light (`M_Glass_Frosted`) with sign-written gold **"7"** (black shadow line) and **"LABORATORY"** between two gold rules, all as real geometry on the room side;
  - a brass kick plate, finger plate, long lock plates and keyholes on both faces.

| Part | Pivot, model-local (room) | Axis | Rest → open / active |
|---|---|---|---|
| `door_frame` | (0, 0, 0) | — | static |
| `IA_door_leaf` | **hinge pin axis at floor level:** model (+0.466, 0, −0.203). In the room that is **(3.203, 0, 1.366)**: the leaf's model **+X edge**, which is the **south edge** in the room and the **right edge seen from the room**, on the corridor face | local **+Y** (vertical) | 0° closed → **−95°** open. Negative is clockwise from above, so the free (north) edge swings to room **+X**, out of the room into the corridor. A positive angle would drive it through the stop into the room |
| `IA_door_handle` | child of the leaf. Spindle axis at the leaf mid-plane: model (−0.397, 1.08, −0.170), room ≈ (3.170, 1.08, 0.503). Both levers point toward the hinge (model +X) | local **+Z** (the spindle, normal to the leaf) | 0° → **−40°**: the lever tips go **down**. This is the same as +40° about −Z. Press, then return before or while the leaf opens |
| `maglock_lamp` | model (0, 2.378, 0.075): the lens base centre on the box front. Room (2.925, 2.378, 0.9) | — | emissive red jewel (`M_Emissive_Red`). Set it to green with `ModelUtil.set_emission` when the door is open, as `lab7_visuals.gd` already does |

**Action needed:** `lab7_visuals.gd` has `const DOOR_OPEN_DEG := 95.0`. With the hinge on the south edge as specified, this must be **`-95.0`**. Otherwise the door opens into the room, through the stop. This was verified in `qa/blender/door_lab7_3.png`, which shows the leaf at −95° swung out into the corridor.

**Colliders (mode `parts`):** the AABB of `door_frame` spans the whole surround and contains the leaf. That is harmless, because every door mesh maps to the single `door` hotspot. The light sensor at z 0.12 is outside every door box.

---

## chair.glb — bentwood chair (Thonet No. 18 pattern), static
- **Size:** 0.44 w × 0.94 h × 0.53 d.
- **Origin:** the floor centre under the round seat. The seat top is at y 0.466, and the back bow reaches back to z = −0.32.
- **Construction:**
  - steam-bent walnut-stained frame: a continuous back bow that becomes the rear legs, an inner back loop, splayed front legs and a leg hoop at y 0.20 with brass screws;
  - a padded leather seat with a welt.
- **Placement:** the current placement (−0.35, 0, −1.3) with yaw 168° faces the desk. The chair has no arms, so it can be pushed toward the desk.

## filing_cabinet.glb — 4-drawer pressed-steel cabinet, static
- **Size:** 0.50 w × 1.32 h × 0.60 d. The drawer fronts are at model z = +0.30, and the flat top is at **y = 1.32** for `cc_bust`.
- **Origin:** the floor centre.
- **Materials:** green-grey `M_Steel_Painted`, with a recessed toe-kick.
- **Drawer fronts:** each has a brass card frame with a typed index card (bottom → top "S – Z", "M – R", "G – L", "A – F") and a brass bar pull. There is a cylinder lock at the top right.
- **Ajar drawer:** the third drawer from the bottom stands **7 cm ajar**. Inside it are 5 manila folders leaning on a follower block, matching "staff records, mostly empty".
- **Placement:** at the current placement (−2.6, 0, −2.2) the back is at z = −2.5, on the wall plane. The wainscot (≤ 3 cm) is hidden behind the cabinet.

## coat_rack.glb — bentwood coat stand with coat and hat, static
- **Size:** 0.55 × 1.98 × 0.57.
- **Origin:** the floor at the pole axis.
- **Stand:** a turned walnut pole to y 1.93, 4 scroll legs (feet r ≈ 0.31) and an umbrella ring at y 0.26.
- **Upper scroll hooks:** at **165°, 75°, −15°, −105°**. Angles are measured in the model's horizontal plane from +X toward −Z (the back), that is, counter-clockwise seen from above. Hanging point r 0.212, y 1.698.
- **Lower hooks:** at −90° (the front, which carries the coat) and +90°. Hanging point r 0.13, y 1.558.

**Gas-mask hook:** the 165° hook's hanging point is model **(−0.205, 1.698, −0.055)**.
- With the current placement (2.6, 0, −2.15) and yaw −30°, that is **room (2.450, 1.698, −2.300)**. This is exactly the `cc_gasmask` spot, and it is left free.

**Coat**
- **Description:** a long dark wool coat (`M_Fabric`) that hangs from the front lower hook. It has:
  - a collar;
  - draped folds and a wavy hem at y 0.60;
  - sleeves;
  - 4 bakelite buttons;
  - 2 pocket flaps.
- **Pocket flaps:** model **(±0.12, 1.09, 0.26)**. The pocket bags are just inside, at (±0.12, 1.06, 0.24).
- **Pocket positions in the room:** with the current placement,
  - the left (−X) pocket is ≈ **(2.37, 1.07, −1.98)**;
  - the right pocket is ≈ (2.58, 1.07, −1.88).
- **Current `coat_pocket` shard:** (2.52, 1.12, −2.02) sits about 0.1 m inside the coat body.

**Hat:** a dark grey felt fedora (`M_Felt`) on the finial, tilted, with its brim at about y 1.86.

**Colliders (mode `parts`)**
- The `coat` mesh is separate from `coat_rack_body`. Its AABB front is at model z = +0.308 (the hem flare).
- For a shard tap box of 0.12 to win the "first hit", centre the shard at the flap surface: model z ≥ 0.25, which is the left pocket position above.

---

## desk.glb *(built earlier, same pipeline; summary)*
- **Size:** 1.50 × 0.78 × 0.74.
- **Origin:** the floor centre.
- **East side:** model +X holds the rosette and the compartment.

| Part | Pivot (model-local) | Motion |
|---|---|---|
| `IA_drawer_top` | (0, 0.628, 0.353): the bottom-centre of the drawer front | slide along **+Z** |
| `IA_drawer_digit_0..3` | children of the drawer. Axles at x −0.033 / −0.011 / +0.011 / +0.033, y 0.678, z 0.3395 | local **+X**: **+k × 36°** shows digit k. Digit 0 faces the viewer at rest |
| `IA_rosette` | (0.725, 0.7025, −0.1425) | press: translate −X by 6 mm |
| `IA_compartment` | (0.735, 0.555, −0.1425) | slide along **+X** |
| `IA_secret_panel` | child of the compartment, (0.7383, 0.596, −0.1425) | slide along **−Y** by 0.06 |
| `IA_keyhole` | child of the compartment, (0.7362, 0.596, −0.1425) | static |

## pendant_lamp.glb *(built earlier)*
- **Origin:** the ceiling attachment point. The lamp hangs down 1.13 m.
- **`bulb`:** `M_Emissive_Warm`.
- **`light_origin`:** an empty at (0, −1.086, 0), the bulb centre.

---

## QA renders (`qa/blender/`)

| Model | Renders |
|---|---|
| `room_lab7` | `room_lab7.png` is the **player point** (0.2, 1.55, 0.2) looking toward the window wall. The others are `_2` (door/east wall/safe), `_3` (west wall with the bookcase in place, vent and pipe), `_4` (darkroom), `_5` (ceiling: beams, roses, conduit, with pendants), `_6` (window/sill close-up), `_7` (vent detail), `_8` (radiator valves) and `_9` (safe recess) |
| `door_lab7` | `door_lab7.png` (closed, in the room), `_2` (glass numeral + lever), `_3` (**open, −95°**, handle pressed) and `_4` (maglock) |
| `chair` | `chair.png`, `chair_2.png` |
| `filing_cabinet` | `filing_cabinet.png`, `filing_cabinet_2.png` (card holder close-up) |
| `coat_rack` | `coat_rack.png`, `_2` (back three-quarter view, gas-mask hook), `_3` (coat and hat close-up) |

## Pipeline notes (`lib_arch.py` additions)
- **`prepare_tinted`:** QA preview for `M_Plaster_Stained`.
- **Joinery geometry:** `frame_matrix`, `raised_field`, `rect_path`, `catmull` and `resample_radii`.
- **`text_lowpoly`:** sign and label lettering at low curve resolution. A glyph is 20–60 tris instead of hundreds.
- **`grain_uv`:** rotates box-UVs 90° on vertical wooden members, so stiles, jambs, legs and casing legs show vertical grain.
- **`hint`, `lathe_s`, `cyl_s`, `torus_s`, `sphere_s`, `presmooth`, `finalize_uv`:** per-part smoothing. Round 6–12-sided parts are smoothed at 60–80°, while boxes keep 35°, so chamfers stay crisp. Joined objects keep these flags.
