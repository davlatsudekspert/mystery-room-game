# Chapter 2 models — interface contract (Records Archive B)

This page is the **contract** between the Chapter 2 Blender models and the game code
(`game/src/rooms/archive/`). The code finds parts **by exact name** and moves them with the
conventions below, so names, pivots, axes and rest poses are binding.
Puzzle data comes from `docs/CHAPTER2_DESIGN.md` and `game/src/rooms/archive/archive_logic.gd`.
Where this page and the design doc disagree on a placement, **this page wins** (it is newer); the
design doc is updated to match.

Each build group also writes its measured results (final pivots, sizes, tris, QA renders) to
`docs/models/ch2_<group>.md`. Those pages are merged here when the group is done.

## 0. Rules for every Chapter 2 model

**Tools.** Build with Blender 5.2 headless scripts in `tools/blender/models/<name>.py`. Use the
existing libraries:
- `mrlib`: materials, primitives, export;
- `lib_arch`: sweeps, mouldings, rounded rects, `import_glb` for QA scenes;
- `lib_mech`: lathe, knurls, text, gears, screws;
- `lib_props`: books, mouldings, tubes;
- `lib_devices`: `item_main`, `revolve`, text, crystal lens, centre of mass;
- `lib_echo`: human figures.

Read the existing Chapter 1 scripts of the same kind before you start. Examples:
- `wall_safe.py` and `door_lab7.py` for hinged parts;
- `radio.py` and `lumen_projector.py` for devices;
- `brass_key.py` and `crystal_lens.py` for items;
- `room_lab7.py` for architecture.

**Do not edit** existing `tools/blender/*.py` libraries. Put new helpers in a new module of your
own (`tools/blender/lib_ch2_<group>.py`).

**Run:**
```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render]
```
- The export goes to `game/assets/models/<name>.glb`.
- QA renders go to `qa/blender/ch2/<name>[_n].png`. Use Cycles, at most 32 samples, at most 960×640,
  2 threads; the machine is shared by several builders.
- List each script in your group's build list, `tools/blender/build_lists/ch2_<group>.txt`.

**Coordinates.**
- Godot = Blender (x, z, −y). Every number on this page is in **Godot axes, metres**.
- A model's **front faces +Z**. Yaw rotates the model about +Y, and the +Z front then points along
  the world direction given in the placement table. Yaw 90 → front faces world +X; yaw −90 → −X;
  yaw 180 → −Z. With yaw 180, model +X = world −X.
- **Origins:**
  - wall-mounted furniture: floor level (y = 0), at the centre of the back face, so it is placed
    on the wall plane;
  - free-standing furniture: floor level, at the footprint centre;
  - items: the centre of mass (see `docs/models/devices.md`);
  - `room_archive` and `vault_interior`: built directly in room coordinates, origin = room origin.

**Animated parts.**
- `IA_*` (tap targets) and every other animated part are **their own object**.
- The origin is at the pivot, with an **identity rotation at rest** (relative to the parent).
- Angles follow `docs/models/devices.md`. A positive angle is counter-clockwise looking down the
  +axis toward the origin. About +X, a positive angle tips +Y toward +Z (a back-hinged lid opens
  with a **negative** angle). About +Y, a door hinged on its left edge (seen from the front) opens
  toward the viewer with a **negative** angle.
- The code applies `rest.basis * Basis(axis, deg)` (`Lab7Visuals._rot`) or slides along a local
  axis (`_slide`).

**Mount empties (`*_mount`).**
- An empty marks where the code attaches an **item model** (`game/assets/models/<item>.glb`).
- The empty's transform **includes orientation**: the item, parented to the empty with an
  **identity** transform, must sit exactly right. That means its centre of mass is at the empty,
  it rests on the surface, and it faces the way described.
- Test it in your QA render by importing the item GLB at the empty. If the item GLB does not exist
  yet, use a proxy box of the item's size from §6.

**Colliders.** `ModelUtil.build_colliders` gives:
- an AABB box to every `IA_*` mesh up to 0.15 m;
- an exact trimesh to everything else.

The code also prefers the smallest `IA_*` hit within 0.18 m behind the first surface. Split static
bodies so that no static mesh covers a tap target from the camera views in §2. **Large interactive
parts** (doors, drawers) must not swallow the small controls mounted on them: make the controls
separate `IA_*` children.

**Names.** A name must never end in a Godot import hint, even before trailing digits:
`_col`, `_wheel`, `-rigid`, `_occ`, `_navmesh`, `_vehicle`, `-noimp`… Use `_handle`, `_knob` or
`_pulley` instead. `tools/blender/check_glb_names.py` must pass on your GLBs.

**Materials.** Use a slot name from the game library (`game/assets/materials/*.tres`); Godot swaps
the slot by name.

Existing slots:
- **Wood:** `M_Wood_Walnut`, `M_Wood_Mahogany`, `M_Wood_Panel`, `M_Wood_Floor`.
- **Walls and stone:** `M_Plaster_Wall`, `M_Plaster_Stained`, `M_Ceiling`, `M_Stone`.
- **Metals:** `M_Brass_Aged`, `M_Brass_Polished`, `M_Steel_Painted` (green-grey), `M_Steel_Dark`,
  `M_Chrome`, `M_Copper`.
- **Hard and soft materials:** `M_Bakelite`, `M_Lacquer_Black`, `M_Rubber`, `M_Leather`,
  `M_Fabric`, `M_Felt`, `M_Paper`, `M_Cork`, `M_Grille_Fabric`.
- **Glass:** `M_Glass`, `M_Glass_Frosted`, `M_Glass_Dark`, `M_Glass_Amber`, `M_Glass_Green`,
  `M_Crystal`.
- **Enamels:** `M_Enamel_Cream`, `_White`, `_Crimson`, `_Amber`, `_Green`, `_Cobalt`, `_Violet`.
- **Emissives:** `M_Emissive_Warm`, `M_Emissive_Red`, `M_Emissive_Lumen`.
- **Books:** `M_Book_Red`, `_Green`, `_Brown`, `_Blue`, `_Black`, `_Gold`.

New Chapter 2 slots are created by group F. In your script, create them with
`M.material(name, color=…, rough=…, metal=…)` using the preview colour in this table:

| Slot | Use | Preview colour, roughness, metallic |
|---|---|---|
| `M_Linoleum` | Floor: worn green/cream checker. The texture repeat is 0.6 m (2 × 2 tiles of 0.30 m) | 3E5A48, 0.55, 0 |
| `M_Paint_Green` | Lower walls to the dado: institutional green eggshell paint over plaster | 6F8C78, 0.6, 0 |
| `M_Concrete` | Pilasters, vault frame, tunnel, booth plinth | 8C8A84, 0.85, 0 |
| `M_Steel_Cream` | Cream-enamelled steel cabinets: tube station, compressor panel | D8CFB4, 0.4, 0.1 |
| `M_Screen` | Matte projection screen | E9E6DF, 0.95, 0 |
| `M_Velvet` | Crimson velvet linings: lens case, key cradle | 5A1420, 0.9, 0 |
| `M_Film` | Film base: dark amber, slightly translucent | 3A2414, 0.25, 0 (alpha 0.9) |
| `M_Tape` | Magnetic tape: brown | 4A2C1A, 0.35, 0 |
| `M_Cardboard` | Archive boxes | 9A7B55, 0.85, 0 |
| `M_Linen` | Ledger and box cloth spines | 8C7B5E, 0.8, 0 |

**Decals.**
- A decal is a separate quad or mesh with **UV 0..1**: u runs left → right and v bottom → top as the
  player sees it, not mirrored.
- Its slot is `M_Decal_<Name>`. The image comes from group F in
  `game/assets/textures/decals/ch2/`.
- For QA previews, pass `image=<abs path>` to `M.material` when the file exists. If it does not
  exist yet, render anyway and re-render at the end if it has appeared.
- Static labels and numbers are **3D text or engraved geometry** (fonts in `game/assets/fonts` and
  DejaVu), not decals, unless this page says otherwise.

**UVs.** World-scale UVs (1 UV unit = 1 m, `M.box_uv` / `lib_arch.finalize_uv`), as in Chapter 1.

**Budgets (triangles).**
- room ≤ 30k;
- a big furniture piece or device ≤ 9k;
- vault door ≤ 14k; vault interior ≤ 14k;
- small furniture ≤ 5k; an item ≤ 2.5k; an echo ≤ 14k.

The whole Chapter 2 scene must stay near 170k tris with everything visible. The booth and the vault
interior are hidden when not seen.

**Look.**
- `docs/ART_DIRECTION.md`: late-1970s Soviet-era research institute, brass and enamel, warm lamps
  against green-grey shadows.
- Archive B is the Institute's paper memory: card catalogues, pneumatic post, steel stacks, a
  projection booth and a bank-style vault. Everything is slightly worn and dusty.
- Model real-world detail: bevels, screws, hinges, labels, wear. A phone camera gets close.

## 1. Room layout (world, Godot coordinates)

- Interior: x ∈ [−5, 5], z ∈ [−3.5, 3.5], floor y = 0, ceiling y = 3.6.
- Walls are 0.2 m thick, outside the interior box.
- North is −Z. The player enters from the south-east.

| Model (file) | Group | Position | Yaw | Hotspot | Notes |
|---|---|---|---|---|---|
| `room_archive` | A | (0, 0, 0) | 0 | — | Shell, booth enclosure, ceiling tube run, emergency lamps, shutter, corridor stub |
| `archive_pendant` ×6 | A | (−3.0, 3.6, −2.0), (0.0, 3.6, −2.4), (3.0, 3.6, −2.0), (−2.8, 3.6, 1.4), (0.0, 3.6, 1.6), (3.0, 3.6, 1.4) | 0 | — | Origin = ceiling mount point |
| `vent_grille` | A | (−5.0, 2.55, 0.9) | 90 | grille | Origin = the centre of the grille's back plane on the wall plane (not the floor) |
| `floor_hatch` | A | (0.9, 0.0, 2.5) | 0 | hatch | Origin = lid centre, flush with the floor |
| `projection_screen` | A | (−2.5, 0, −3.5) | 0 | screen | Screen centre (−2.5, 1.9) |
| `library_ladder` | A | (−4.62, 0, 0.35) | 90 | — | Leans on the west wall under the grille (dressing) |
| `card_catalogue` | B | (−5.0, 0, −1.2) | 90 | catalogue | |
| `catalogue_tray` | B | in the open drawer | — | catalogue | Spawned by code at `cat_tray_mount_<i>` |
| `stacks_shelving` | B | (0.0, 0, 0.25) | 0 | stacks | Footprint x ∈ [−0.9, 0.9], z ∈ [−0.2, 0.7] |
| `archivist_desk` | B | (3.7, 0, −3.1) | 0 | desk | Top surface y = 0.76; footprint x ∈ [2.95, 4.45], z ∈ [−3.475, −2.725] |
| `reading_table` | B | (1.9, 0, 1.0) | 0 | reading | 1.4 × 0.8, top y = 0.76, with a banker's lamp |
| `lockers` | B | (0.6, 0, 3.5) | 180 | lockers | x ∈ [−0.6, 1.8], 2 rows × 6 |
| `routing_chart` | B | (5.0, 0, −0.35) | −90 | chart | Picture centre at y = 1.75 |
| `film_splicer` | B | (−3.9, 0, 3.5) | 180 | splicer | Booth bench along the south wall, x ∈ [−4.5, −3.3] |
| `slide_cabinet` | B | (−5.0, 0, 2.8) | 90 | slides | Booth west end |
| `lens_case` | B | (−3.75, 1.45, 3.37) | 180 | lens_case | On the booth shelf (built by A, top at y = 1.45) |
| `tube_station` | C | (5.0, 0, −1.4) | −90 | station | |
| `canister` | C | in `canister_mount` | — | station | Animated along the tube path by code |
| `compressor_panel` | C | (5.0, 0, 0.8) | −90 | compressor | |
| `card_punch` | C | (3.25, 0.76, −3.05) | 0 | punch | On the desk, front +Z; footprint ≤ 0.38 × 0.30 |
| `tape_deck` | C | (4.15, 0.76, −3.05) | 0 | deck | On the desk; footprint ≤ 0.48 × 0.38 |
| `booth_door` | C | (−1.55, 0, 2.0) | 180 | booth | Doorway x ∈ [−1.95, −1.15] in the booth's north wall |
| `film_projector` | C | (−2.9, 0, 2.65) | 180 | projector | Lens centre at y ≈ 1.95, firing through the booth window to the screen |
| `slide_projector` | C | (−2.35, 0, 2.45) | 180 | slide_projector | On its own stand; lens centre at y ≈ 1.85 |
| `vault_door` | D | (1.5, 0, −3.5) | 0 | vault | Door centre (1.5, 1.35) |
| `vault_interior` | D | (0, 0, 0) | 0 | vault | Built in room coordinates behind the north wall |
| `echo_archivist` | E | (−4.05, 0, −1.05) | −90 | — | At the catalogue, reaching into a right-column drawer |
| `echo_scientists` | E | (−0.8, 0, −1.7) | 50 | — | Two figures between the stacks and the screen wall, facing the hall |
| `echo_strand_standing` (exists) | — | (−3.6, 0, 2.45) | 180 | — | In the booth, watching through the window |
| `echo_leyla_standing` | E | (−4.15, 0, 2.62) | −90 | — | In the booth, pointing at slide drawer 2. The code walks her in from (−3.2, 0, 2.4) |

Reused Chapter 1 models:
- `chair` ×3: two at the reading table, one at the desk;
- `desk_lamp`: archivist desk, at (3.05, 0.76, −3.32);
- CC0 dressing from `docs/CC0_PROPS.md`, placed by the code.

### Fixed points shared by several models

**Ceiling tube run.** The canister travels on this path. Group A builds the glass tube along it.
Group C's station tube ends at T0, and group B's stacks terminal starts at T4.

| Empty in `room_archive` | Point (world) | Meaning |
|---|---|---|
| `tube_p0` | (4.80, 2.35, −1.40) | Top of the tube station's riser |
| `tube_p1` | (4.80, 3.25, −1.40) | Up the east wall |
| `tube_p2` | (0.00, 3.25, −1.40) | West along the ceiling |
| `tube_p3` | (0.00, 3.25, 0.25) | South to above the stacks |
| `tube_p4` | (0.00, 2.25, 0.25) | Down into the stacks terminal |

- **Tube:** glass, outer radius 0.045, inner 0.04, so a canister of radius 0.035 is visible inside.
- **Bends:** radius 0.25, with brass sleeves and collars about every 0.8 m.
- **Supports:** ceiling hangers and wall brackets.
- **Second line:** add a parallel decorative return tube 0.14 m to the side (south of the
  x-direction run, east of the z-direction run, entering the station at `tube_q0`
  (4.80, 2.35, −1.26)). Add at least one more decorative line that leaves through the north wall
  toward "the Director's office".

**Booth enclosure** (group A):
- **Booth walls:** north wall z ∈ [2.0, 2.1] for x ∈ [−5, −1.0]; east wall x ∈ [−1.1, −1.0] for
  z ∈ [2.0, 3.5].
- **Booth ceiling:** a slab at y ∈ [2.8, 2.9], with a low parapet on top (it is a room inside the
  room).
- **Interior:** x ∈ [−5, −1.1], z ∈ [2.1, 3.5], y ∈ [0, 2.8].
- **Projection window:** x ∈ [−3.4, −2.1], y ∈ [1.65, 2.25], glazed with `booth_glass`
  (`M_Glass`) and a brass frame.
- **Doorway:** x ∈ [−1.95, −1.15], y ∈ [0, 2.1], filled by `booth_door` (C), which brings its own
  casing.
- **Shelf** on the south wall inside the booth: x ∈ [−4.6, −3.3], top at y = 1.45, depth 0.26 (from
  z 3.24 to 3.5), with film cans on it (keep x ∈ [−3.95, −3.55] free for the lens case).
- A bare bulb `booth_bulb` (emissive `M_Emissive_Warm`, toggled by code) hangs at
  (−3.0, 2.65, 2.85).

**Vault opening:**
- The room's north wall has a **rectangular opening** x ∈ [0.45, 2.55], y ∈ [0.30, 2.40]
  (2.1 × 2.1) through the 0.2 m wall.
- `vault_door`'s frame plate covers it from the room side: x ∈ [0.3, 2.7], y ∈ [0.15, 2.55]
  world, 0.10 thick, standing in front of the wall face.
- Its tunnel sleeve fills the wall thickness around the Ø 1.9 aperture.

**Other openings:**
- **Vent:** a 0.62 (z) × 0.37 (y) opening in the west wall at (−5, 2.55, 0.9), with a duct box
  behind it 0.35 deep (dark steel inside).
- **Floor hatch:** a 0.62 × 0.62 opening at (0.9, 0, 2.5) with a cavity 0.32 deep below it.
  `floor_hatch` (A) brings the frame, lid and liner, so the room just needs the hole and the void.

## 2. Camera views

These are the views the game will use; tune them in code. Render your QA shots **from these
viewpoints** (plus a hero shot), with the neighbouring models imported where they matter. The
interactive parts must be clearly visible and separately tappable from these views.

| View | Camera | Looks at | FOV |
|---|---|---|---|
| hall (root, free look) | (3.8, 1.65, 1.8) | (0.0, 1.3, −2.2) | 62 |
| west (root, free look) | (−1.8, 1.65, 1.0) | (−3.0, 1.5, −3.0) | 62 |
| booth (root, free look) | (−1.55, 1.6, 2.6) | (−4.6, 1.1, 2.9) | 62 |
| catalogue | (−3.55, 1.5, −1.2) | (−4.7, 1.0, −1.2) | 50 |
| cat_drawer | (−3.85, 1.55, −1.2) | (−4.4, 0.95, −1.2) | 42 |
| grille | (−3.7, 1.9, 0.9) | (−5.0, 2.55, 0.9) | 46 |
| stacks | (0.0, 1.5, 2.3) | (0.0, 1.1, 0.7) | 56 |
| ledger | (0.4, 1.3, 1.5) | (0.35, 1.0, 0.65) | 40 |
| reading | (1.9, 1.6, 2.35) | (1.9, 0.8, 1.0) | 52 |
| hatch | (1.5, 1.45, 3.0) | (0.9, 0.0, 2.5) | 50 |
| lockers | (0.6, 1.35, 1.5) | (0.6, 0.95, 3.5) | 56 |
| locker9 | (0.4, 0.95, 2.45) | (0.4, 0.55, 3.35) | 46 |
| station | (3.55, 1.55, −1.4) | (4.95, 1.2, −1.4) | 52 |
| chart | (3.9, 1.7, −0.35) | (5.0, 1.75, −0.35) | 44 |
| compressor | (3.65, 1.45, 0.8) | (5.0, 1.25, 0.8) | 52 |
| desk | (3.7, 1.6, −1.85) | (3.7, 0.8, −3.1) | 52 |
| punch | (3.25, 1.2, −2.35) | (3.25, 0.82, −3.05) | 40 |
| deck | (4.15, 1.2, −2.35) | (4.15, 0.82, −3.05) | 40 |
| vault | (1.5, 1.55, −0.9) | (1.5, 1.35, −3.5) | 56 |
| vault_ports | (1.5, 1.65, −2.3) | (1.5, 1.55, −3.4) | 50 |
| screen | (−2.5, 1.7, −0.5) | (−2.5, 1.9, −3.45) | 56 |
| socket | (−2.5, 1.2, −2.65) | (−2.5, 0.92, −3.38) | 40 |
| booth_door | (−1.55, 1.45, 0.75) | (−1.55, 1.2, 2.0) | 52 |
| dial | (−1.8, 1.25, 1.5) | (−1.82, 1.2, 2.0) | 36 |
| projector | (−2.2, 1.75, 3.15) | (−2.9, 1.5, 2.6) | 50 |
| splicer | (−3.9, 1.55, 2.55) | (−3.9, 0.95, 3.3) | 48 |
| slides | (−3.85, 1.3, 2.8) | (−4.8, 0.7, 2.8) | 48 |
| slide_projector | (−1.75, 1.95, 2.95) | (−2.35, 1.8, 2.45) | 44 |
| lens_case | (−3.75, 1.85, 2.8) | (−3.75, 1.47, 3.37) | 40 |
| vault_inside (finale) | (1.5, 1.55, −3.0) | (1.5, 1.3, −5.2) | 56 |

## 3. Group A — architecture

### room_archive.glb (≤ 30k tris)
Built in room coordinates. Split it into named meshes so Godot can cull and the colliders stay
sensible:
- `floor`, `ceiling`;
- `wall_n`, `wall_e`, `wall_s`, `wall_w`;
- `booth_walls`, `booth_ceiling`, `booth_glass`;
- `tube_run`, `tube_glass`;
- `corridor`, `trim`.

**Floor:**
- `M_Linoleum`, with UVs in metres so that tile edges align to x and z = multiples of 0.30;
- a worn path is in the texture;
- a thin brass threshold strip at the shutter.

**Walls:**
- **Lower:** `M_Paint_Green` from 0 to 1.40.
- **Dado rail** at 1.40: a walnut moulding (`lib_arch.profile_chair_rail`).
- **Upper:** `M_Plaster_Wall` cream.
- **Baseboard:** 0.15, dark walnut.
- **Crown moulding** at the ceiling.

**Pilasters** (`M_Concrete`, 0.40 wide × 0.12 deep, floor to ceiling, with a simple capital):
- north wall at x = −0.55;
- south wall at x = 2.35;
- east wall at z = 2.2;
- west wall at z = −2.7.

**Ceiling:** `M_Ceiling` with a shallow coffer grid or two beams. Keep them clear of the tube run
and the pendant positions.

**Fire shutter** (south wall opening x ∈ [2.9, 4.1], y ∈ [0, 2.3]):
- `fire_shutter`: corrugated steel slats, `M_Steel_Painted`, with a yellow/black hazard bottom bar
  (enamel amber + `M_Lacquer_Black`).
- Its **own object**, origin at its bottom-edge centre (3.5, 0, 3.45), rest = **down** (closed).
  The code raises it by +2.25 on y for the intro "before" shot.
- Static: the side guide rails, the coil box above (y 2.3–2.75), and a red relay lamp
  `shutter_lamp` (`M_Emissive_Red`) on the box.
- Behind it, a dark **corridor stub** x ∈ [2.9, 4.1], z ∈ [3.7, 7.0]: plaster walls, a far door
  silhouette.

**Emergency lamps:** ten caged bulkhead lamps on the walls at y = 2.95:
- north wall at x = −4.3, −0.55 (on the pilaster) and 3.2;
- east wall at z = −2.6, 0.0 and 2.6;
- south wall at x = 0.6 and 2.35;
- west wall at z = −2.7 and 0.25.

Each lamp has:
- a static body `elamp_<k>` (cast body, wire cage);
- an amber glass `elamp_glass_<k>` (`M_Glass_Amber`, own object, toggled emissive by code);
- an empty `elamp_light_<k>` at the bulb centre.

**Booth enclosure** (§1):
- dark walnut panelling (`M_Wood_Panel`, raised fields) to 1.2;
- `M_Paint_Green` above, with a cream enamel sign plate over the doorway (an emblem pictogram of a
  film reel, no words needed);
- a parapet of the booth roof;
- inside: plain plaster, the shelf with film cans (`film_can` meshes: flat cylinders Ø 0.36,
  `M_Steel_Dark`), a fire bucket, cable runs;
- the window with its brass frame and `booth_glass`;
- `booth_bulb`.

**Tube run (§1):**
- `tube_glass`: `M_Glass`, one mesh;
- `tube_run`: brass collars, elbows, hangers;
- empties `tube_p0..tube_p4`, `tube_q0`;
- a brass **wall junction box** where the run meets the north wall.

**Wall dressing** (static, cheap):
- a framed archive regulations notice (`M_Decal_ArchiveRules`, group F) by the entrance at
  (4.98, 1.6, 2.9) facing −X;
- a stopped wall clock above the vault frame at (1.5, 2.95, −3.48) showing 4:17 (the badge number,
  a quiet nod);
- radiator under the routing chart? No: keep the east wall below 0.6 free for the compressor's
  pipes;
- conduit runs to the lamps.

### archive_pendant.glb (≤ 2.5k)
- **Form:** an industrial enamel pendant. A dark green outside / white inside conical shade
  Ø 0.42, on a 0.55 m brass rod with a ceiling rose.
- **Origin:** the ceiling mount point; the shade hangs down to y ≈ −0.75.
- **Parts:** `bulb` (own object, `M_Emissive_Warm`, toggled by code); an empty `light_origin` at
  the bulb centre.

### vent_grille.glb (≤ 3k)
- **Frame:** a cast-iron frame 0.62 × 0.37 with 4 screws.
- **`IA_grille`:** a louvred grille leaf hinged on its **left** edge (seen from the room), pivot on
  that edge. Open = **−100° about local +Y** (it swings toward the room).
- **Duct:** a short duct liner 0.33 deep behind it (`M_Steel_Dark`).
- **`grille_reel_mount`:** the reel (`tape_reel.glb`) lies flat inside the duct, face up, about
  0.12 behind the grille.
- **Origin:** the frame centre on the wall plane (local z = 0 at the wall face; the duct goes to
  −z).

### floor_hatch.glb (≤ 3k)
- **Frame:** a steel frame 0.70 × 0.70 flush with the floor, with a cavity liner 0.30 deep.
- **`IA_hatch`:** the lid (0.60 × 0.60 chequer plate, `M_Steel_Dark` + `M_Steel_Painted`), hinged
  at its **back** (−Z) edge, with a recessed **ring pull** (`ring_pull`, child) near the front
  edge. Open = **−105° about local +X**.
- **`hatch_reel_mount`:** on the cavity floor.
- **Origin:** the lid centre at floor level.

### projection_screen.glb (≤ 4k)
- **Form:** a wall-mounted cinema screen with a black masking border, a walnut proscenium frame,
  and a roller box on top.
- **`screen_surface`:**
  - its own object, **2.40 × 1.60**, centred at local (0, 1.90, 0.07);
  - faces +Z, **UV 0..1** (u left → right, v bottom → top), `M_Screen`;
  - the code puts its projection shader on it.
- **`IA_screen_socket`:**
  - a brass crystal socket (Ø 0.09 cup with three claws), on a bracket under the screen frame
    (below its bottom edge), at local (0, 0.92, 0.12);
  - its mouth faces +Z, toward the booth.
- **`socket_mount`:** at the socket mouth; a `lumen_crystal` with identity stands on edge, disc
  facing +Z.
- **`socket_ring`:** its own object, a thin brass ring around the mouth. The code makes it glow
  while recording.
- **Origin:** the back centre on the floor (local z = 0 is the wall face).

### library_ladder.glb (≤ 2.5k)
A walnut library ladder 2.3 m, leaning on the wall (a dressing prop, no parts).

## 4. Group B — furniture

### card_catalogue.glb (≤ 9k)
**Form:**
- an oak/walnut library catalogue cabinet on a stand: body 0.64 w × 0.86 h × 0.48 d on a stand of
  four turned legs with a stretcher, 0.58 high, so the drawers sit between y ≈ 0.62 and 1.42;
- a brass-edged top with a sloped reading ledge;
- **10 drawers** in **2 columns × 5 rows**.

**Drawer layout:**
- Index **i = row × 2 + column**: row 0 is the top row, column 0 the left as seen from the front.
- So the fronts read `00 01 / 02 03 / 04 05 / 06 07 / 08 09`.
- Each front has:
  - a brass label holder with the number in 3D text (black on cream card, as `00`…`09`);
  - a brass cup pull;
  - a brass rod-lock nut below the pull.

**Parts:**
- **`IA_cat_drawer_<i>`:**
  - each drawer is one object;
  - pivot at its front-face centre;
  - **slides out along local +Z by 0.30** (the drawer box is 0.44 deep inside);
  - the interior must be visible from the cat_drawer view when it is out.
- **`cat_tray_mount_<i>`:** a child empty of each drawer, at the drawer's interior floor centre.
  `catalogue_tray.glb` attached with identity fits the drawer.
- **Static:** the carcass, split per row so no static box covers the open drawer.

### catalogue_tray.glb (≤ 5k)
The drawer contents. They are spawned into the open drawer, so the origin = the drawer floor
centre. Local axes: +Z points out of the drawer toward the player, X is across.

**Dividers.** `IA_divider_<g>`, g = 0..9:
- pressboard guide cards (`M_Cardboard`), 0.13 w × 0.10 h, standing across the drawer;
- spaced along z from the back (g = 0 at z = −0.17) to the front (g = 9 at z = +0.16);
- each has a **tab** 0.035 × 0.022 on top, in a staggered position: tab x = −0.045, 0, +0.045 for
  g % 3 = 0, 1, 2;
- the tab carries the 3D text `0–`, `1–` … `9–`;
- pivot at the divider's bottom centre, so the code can tilt it **+20° about local +X** (top toward
  the player) when picked.

**Cards.** `IA_card_<n>`, n = 0..9:
- plain cream index cards (`M_Paper`), 0.125 × 0.075, standing;
- at rest they form a compact block at the **back** of the tray, behind divider 0;
- each has a **blank tab** on top, staggered x = −0.05, −0.025, 0, +0.025, +0.05 for n % 5;
- pivot at each card's bottom centre;
- the code moves them behind the picked divider, fans them, and adds `Label3D` numbers on the tabs.

**Static:** a brass **rod** through the bottom holes, and a mass of thin card filler meshes behind
everything (`cards_filler`).

### stacks_shelving.glb (≤ 12k)
**Form:**
- double-sided steel stack, footprint 1.80 × 0.90, height 2.05;
- `M_Steel_Painted` uprights with perforations, `M_Steel_Dark` shelves;
- two bays per side, five shelves;
- both faces filled with archive boxes (`M_Cardboard` with box-label decal strips
  `M_Decal_BoxLabels`, group F atlas), bound ledgers (`M_Linen`, `M_Book_*`) and string-tied
  bundles;
- end panels with brass range-label frames showing the 3D text `B-3`;
- a **pneumatic terminal** on top centre: a brass receiving bell with a glass sight tube, where the
  ceiling tube arrives.

**`terminal_top`:** an empty at local (0, 2.25, 0), which is world `tube_p4`. The terminal also takes the
return tube, which drops 0.14 m east of it (local x = +0.14).

**South face (local +Z), right bay, middle shelf** (shelf top at y ≈ 0.95):
- **`IA_ledger`:** a thick ledger **lying flat**, fore-edge toward +Z, about 0.36 w × 0.07 h ×
  0.28 d, among similar flat ledgers;
- pivot at its bottom-front-centre;
- open step 1: it **slides out along local +Z by 0.20**;
- **`ledger_cover`:** the top board, a child of `IA_ledger`, hinged along its back edge;
- open step 2: −110° about local +X. The code does both together;
- under the cover, the page block is **hollowed** into a cavity;
- **`ledger_reel_mount`:** in the cavity.

The rest are static. Keep the ledger's neighbours as separate meshes so they don't hide it.

### archivist_desk.glb (≤ 6k)
**Form:**
- an institutional oak pedestal desk 1.50 × 0.75, top at y = 0.76, with a green linoleum writing
  inlay;
- left pedestal with drawers, right pedestal with a cupboard;
- a raised back gallery with pigeonholes (keep the gallery top under y = 1.05 so it does not block
  the desk view).

**Dressing** (static), avoiding the punch and deck footprints in §1 and the desk lamp spot:
- in/out wire trays;
- a rubber-stamp carousel;
- a bakelite telephone;
- a card file;
- an ink blotter.

**Parts:** none (no IA parts).

### reading_table.glb (≤ 5k)
**Form:**
- a long walnut reading table 1.40 × 0.80, top y = 0.76;
- a green-shaded **banker's lamp** at the back centre;
- a few open ledgers and a magnifier stand.

**Parts:**
- `lamp_shade` (`M_Glass_Green`);
- `bulb`, its own object, `M_Emissive_Warm`;
- an empty `light_origin`.

### lockers.glb (≤ 9k)
**Form:**
- a bank of steel staff lockers, 2.40 w (six columns × 0.40) × 1.85 h × 0.45 d;
- a plinth 0.10, two rows of doors 0.86 high;
- `M_Steel_Painted` with louvres;
- each door has an enamel number plate (3D text 1–12), a small keyhole escutcheon and a latch
  handle.

**Numbering:** top row **1–6** left → right (seen from the front), bottom row **7–12**. So locker
**9** is the bottom row, third from the left.

**Parts:**
- **`IA_locker_<n>`**, n = 1..12:
  - each door hinged on its **left** edge, pivot on that edge at the door's mid height;
  - open = **−105° about local +Y**.
- **Locker 9 interior:** visible when open, with a coat hook and a shelf. Keep the other interiors
  simple and closed.
- **`receiver_mount`:** on the hook in locker 9. `pocket_receiver.glb` with identity hangs there by
  its strap, face +Z.

### routing_chart.glb (≤ 1.5k)
**Form:** an enamel-framed wall chart, image 0.50 w × 0.70 h, centred at local (0, 1.75, 0.02),
facing +Z, with a glass cover.

**Parts:** **`chart_image`**, UV 0..1, `M_Decal_RoutingChart`.

### film_splicer.glb (≤ 8k)
**Form:**
- a booth workbench 1.20 × 0.60, top y = 0.90, against the south wall;
- the front is local +Z, toward the north and the player;
- on it:
  - a **light box** (opal glass top, `M_Glass_Frosted`, own object `light_box_glass`, glows via
    code) on the left half;
  - a cast-iron **splicing block** with four **slots** in a row on the right half;
  - a rewind spindle;
  - a **reel can** with its lid propped against the wall;
  - a cement bottle and scissors (dressing).

**Parts:**
- **`IA_frame_<k>`**, k = 0..3: four loose film strips lying on the light box.
  - Each is 0.15 long (local X) × 0.05 wide, 35 mm-style with sprocket holes.
  - The middle part is a quad with **UV 0..1** and slot `M_Decal_FilmStrip_<k>`.
  - Pivot at the strip centre.
  - At rest they are scattered at slight angles, in the order k = 0, 1, 2, 3 from left to right.
  - The code moves them into the slots.
- **`IA_slot_<s>`**, s = 0..3: the four gate plates on the splicing block, left → right. Each is a
  small tap target.
- **`slot_mount_<s>`:** where a strip sits when placed: it lies flat, identity = the same
  orientation as the strip's rest pose without the scatter angle.
- **`splicer_reel_mount`:** on the rewind spindle; a `film_reel.glb` with identity stands on edge,
  face +Z.
- **`reel_can_lid`:** the lid, propped up, facing +Z. Its top face is a quad with UV 0..1 and slot
  `M_Decal_ReelCanLid` (sunrise → high sun pictogram).

### slide_cabinet.glb (≤ 5k)
**Form:**
- a narrow walnut lantern-slide cabinet, 0.60 w × 1.05 h × 0.45 d;
- **5 shallow drawers** stacked vertically, drawer 0 at the top, between y ≈ 0.40 and 0.95;
- a plinth;
- each drawer front has a brass pull and an enamel symbol plaque in 3D:
  - drawer 0 ○ (ring);
  - drawer 1 △;
  - **drawer 2 ✦** (four-pointed star);
  - drawer 3 □;
  - drawer 4 ✚.

**Parts:**
- **`IA_slide_drawer_<i>`:** slides out along local +Z by 0.28. Inside, rows of lantern slides in
  card mounts (static, cheap).
- **`slide_mark_mount`:** a child of `IA_slide_drawer_2`, at the front row; `glass_slide.glb` lies
  flat there, face up.

### lens_case.glb (≤ 2.5k)
**Form:** a small walnut case 0.24 × 0.07 × 0.16 with brass corners, lined with `M_Velvet`, with
two round recesses.

**Parts:**
- **`IA_case_lid`:** hinged at the back. Open = −105° about local +X.
- **`crystal_mount_1`, `crystal_mount_2`:** in the recesses; a `lumen_crystal` lies face up.

## 5. Group C — devices

### tube_station.glb (≤ 9k)
**Form** (front +Z; placed on the east wall facing −X, so local +X = world +Z):
- a cream-enamel (`M_Steel_Cream`) and brass pneumatic-post station, 0.90 w × 2.35 h overall;
- a counter cabinet 0.90 × 0.88 × 0.46 with a walnut top;
- an upper panel to 2.0 with the controls;
- the brass/glass riser tube in front of the panel up to `tube_p0` (local (0, 2.35, 0.20)).
- a second, return riser beside it at local x = +0.14, ending at local (0.14, 2.35, 0.20), which is
  world `tube_q0`.

**Parts:**
- **`IA_send_port`:**
  - the brass send-port housing on the riser at y ≈ 1.25, with a glass sight window;
  - a hinged **`port_flap`** (child; hinge at its bottom edge; open = +80° about local +X, top
    falls toward the player);
  - **`canister_mount`**: inside; the canister (long axis local +Y) stands there.
- **`IA_receive_tray`:**
  - a brass receiving box under the port at y ≈ 0.95 with a glass-fronted **`tray_door`** (child;
    hinged at its bottom edge; open = +75° about local +X);
  - inside: `return_mount` (canister lying horizontal along local X), `file_mount` (the
    `file_folder` lying flat) and `key_mount` (the `locker_key` lying flat).
- **`IA_dest_dial`:**
  - a 6-position brass selector knob (Ø 0.10) on the panel at y ≈ 1.55;
  - rotation **−60° × d about local +Z**;
  - the knob's pointer is at 12 o'clock at rest (d = 0).
  - Around it, a **decal ring** (`dest_ring`, quad or disc, UV 0..1 centred on the knob axis, slot
    `M_Decal_DestSymbols`, group F). It shows the 6 destination symbols at clock positions
    12, 2, 4, 6, 8, 10 for d = 0..5.
- **`IA_send_lever`:**
  - a big brass lever on the right side of the panel;
  - pull = **+55° about local +X** (top comes toward the player).
- **`IA_card_tray`:**
  - a walnut tray on the counter with a stack of blank request cards (`tray_cards`, static);
  - **`tray_card_mount`**: on top of the stack.
- **`lamp_status`:**
  - its own object, a jewel lamp above the dial;
  - the code colours it red (no pressure) or green;
  - a small engraved plate beside it shows a pictogram of a gauge.
- **Dressing:** a little brass pressure gauge on the riser (static, needle at 0).

### canister.glb (≤ 1.2k)
- **Form:** a pneumatic canister, Ø 0.07 × 0.22, brass body with leather/felt end bands and a
  hinged end cap.
- **Origin:** the centre; long axis = local +Y.
- **`canister_cap`:** its own object.

### compressor_panel.glb (≤ 9k)
**Form** (front +Z; placed on the east wall facing −X):
- a cream-enamel wall panel 1.10 w × 1.30 h centred at y = 1.30;
- below it, a small electric **compressor** on the floor: a tank, a motor, a belt guard;
- copper pipes rise from it into the panel.

**Parts and layout:**
- **Two gauges** at the top:
  - **P** (left, centre local (−0.25, 1.68, ·)) and **F** (right, (+0.25, 1.68, ·)), each with a
    face Ø 0.20;
  - a 3D scale **0–12**: the number v at angle **225° − 22.5° × v** (counter-clockwise from +X, as
    seen from the front);
  - big numbers at 0, 2, 4 … 12, and ticks for every integer;
  - a **green enamel wedge** at **P = 5** and **F = 4** (±0.35 units);
  - letters **P** and **F** on the faces.
- **Needles `needle_p`, `needle_f`:** their own objects, pivot at the gauge centre. At rest
  (identity) they point at **0** (225°); the code rotates them by **−22.5° × value about local +Z**.
- **Three valve handwheels** across the bottom: `IA_valve_a`, `IA_valve_b`, `IA_valve_c` at
  x = −0.32, 0, +0.32, y = 0.88.
  - Each is a cast red-enamel spoked handwheel Ø 0.16 on a brass stem.
  - Rotation **−72° × position about local +Z** (positions 0..4).
  - Each has a fixed brass dial ring with the engraved positions **0 1 2 3 4**: position k at angle
    90° − 72° × k (counter-clockwise from +X), with a pointer on the handwheel.
  - Each has a letter plate below it: **A, B, C**.
- **Piping-diagram plate** in the middle, between the gauges and the valves (y ≈ 1.20), built in
  3D: brass inlay lines on dark enamel. It shows:
  - from **A**: a **single** line to **P** and a **double** line to **F**;
  - from **B**: a **double** line to **P**;
  - from **C**: a **single** line to **F**.

  The lines must read unambiguously as single vs double: 2 parallel strips 6 mm apart. The letters
  A B C (bottom) and P F (top) are at the line ends.

  This plate is puzzle-critical (P = A + 2B, F = 2A + C).
- **`motor_pulley`:** its own object, the motor's pulley and fan; spins about local +X when
  running.
- **`compressor_tank`:** its own object, so the code can shudder it.

### card_punch.glb (≤ 6k)
**Form** (front +Z, on the desk):
- a 1950s keyboard card punch, 0.36 × 0.15 × 0.28, grey-green enamel and chrome;
- **8 keys** in a row on the front slope.

**Parts:**
- **`IA_punch_key_<i>`**, i = 0..7, left → right:
  - square bakelite caps with the 3D digits **1–8**;
  - pivot at the cap centre;
  - pressed/latched = **translate −0.006 along local Y**.
- **`IA_punch_slot`:** a card throat across the top-back, where a card stands half inserted.
- **`card_in_punch`:** its own object, a request card standing in the throat (hidden by code when
  empty). Use slot `M_Decal_RequestCard` on its face (UV 0..1, the card's print side facing +Z).
- **`IA_punch_lever`:**
  - a chrome lever on the right side;
  - pull = **+60° about local +X** (top comes toward the player).

### tape_deck.glb (≤ 8k)
**Form:**
- an open-reel tape recorder lying flat, 0.46 × 0.17 × 0.36, wood case with brushed-metal top
  deck;
- two spindles;
- a front control strip sloping toward the player.

**Parts:**
- **`IA_speed`:** a chicken-head knob on the front strip; rotation **(45° − 30° × i) about local
  +Z**, for i = 0..3. The 3D labels around it at those pointer positions read **2.4**, **4.75**,
  **9.5**, **19**: i = 0 is the far left, i = 3 the far right. The identity pointer points at 12
  o'clock (between 4.75 and 9.5).
- **`IA_play`:** a piano key; pressed = −8° about local +X.
- **`IA_eject`:** a smaller key; same press motion.
- **`spindle_l`, `spindle_r`:** their own objects; spin about local +Y.
- **`deck_reel_mount`:** on the left spindle; `tape_reel.glb` lies face up (identity → reel face
  +Y).
- **`takeup_reel`:** an empty take-up reel on the right spindle, child of `spindle_r`.
- **`vu_needle`:** the VU meter needle, its own object, pivot at its base. Rest = −40° deflection
  baked as identity at the meter's left stop; the code rotates it **clockwise (negative about local
  +Z) up to −80°**.
- **`vu_face`:** its own object (a cream face with 3D ticks), so the code can light it.
- **`tape_path`:** static guides and the head block between the spindles.

### booth_door.glb (≤ 6k)
**Form:** a panelled walnut door 0.80 × 2.05 with a painted casing (the casing fills the doorway
and the 0.1 m wall). It has:
- a small round porthole near the top;
- a brass push plate;
- a **rotary-dial lock** at y ≈ 1.20, near the free edge.

**Placement:** yaw 180, so local +X = world −X. The **hinge is on world east, local −X**.

**Parts:**
- **`IA_booth_door`:**
  - the leaf, pivot on the hinge edge at local x = −0.40;
  - open = **−100° about local +Y** (the leaf swings out toward the hall).
- **`IA_rotary_dial`:**
  - a telephone-style finger wheel Ø 0.12 (chrome rim, clear holes), a child of the leaf;
  - pivot at the dial centre, with a fixed **number plate** behind it (cream enamel, 3D digits)
    and a **finger stop**;
  - the hole for digit n (n = 1…9, then 0 as n = 10) is at angle **θ = 50° + (n − 1) × 30°**
    (counter-clockwise from +X, seen from the front), and the plate shows that digit through its
    hole;
  - the finger stop is at **θ = −10°**;
  - dialling n turns the finger wheel **clockwise by (θ_n + 10°)** (about local +Z, negative)
    and back.
- **`IA_dial_hole_<d>`**, d = 0..9:
  - a thin tap disc in each finger hole, a child of `IA_rotary_dial`, so the code knows which digit
    was touched;
  - the name uses the digit itself: `IA_dial_hole_0` is the 0 hole.
- **`booth_door_lamp`:** its own object, a small jewel lamp on the casing. The code shows red
  while locked and green when open.

### film_projector.glb (≤ 9k)
**Form:**
- a 1950s 16 mm cinema projector on a heavy cast pedestal;
- front (lens) = local +Z;
- the lens centre is at local (0, 1.95, ≈ +0.30);
- the feed arm on top front, the take-up arm at the back/bottom;
- the lamp house at the back left with vents;
- the **operator side (all controls) is local −X**. With yaw 180 that is world +X (east), the side
  the projector view sees: camera (−2.2, 1.75, 3.15) is east of and behind the projector.

**Parts:**
- **`feed_reel_mount`:** on the feed arm; a `film_reel.glb` with identity hangs there, its face
  along local ±X (the reel plane is the YZ plane).
- **`takeup_reel`:** an empty reel on the lower arm; spins about local +X.
- **`IA_run_lever`:** OFF at rest; RUN = **+40° about local +X**.
- **`IA_focus_ring`:**
  - a knurled ring on the lens barrel;
  - rotation **−30° × focus about local +Z** (focus 0..8);
  - the 3D digits **0–8** are on its outer surface: the digit k at polar angle **90° + 30° × k**
    (counter-clockwise from +X, seen from the lens front);
  - a fixed index mark on top of the barrel, so the digit at the top = current focus.
- **`IA_frame_prev`, `IA_frame_next`:** two push buttons with ◀ ▶ arrows (3D); pressed = translate
  −0.004 along their face normal (local −X).
- **`lamp_glow`:** its own object, emissive vents/window on the lamp house (code).
- **`lens_origin`:** an empty at the lens front centre; the beam runs along local +Z.

### slide_projector.glb (≤ 5k)
**Form:**
- a 1950s lantern-slide (magic-lantern-style) projector on a tall iron stand (column + tripod
  base);
- body ≈ 0.22 w × 0.20 h × 0.34 d;
- lens centre at local (0, 1.85, ≈ +0.20), front +Z.

**Parts:**
- **`IA_slide_gate`:** the slide carrier slot across the body.
- **`slide_gate_mount`:** at the gate centre. A `glass_slide.glb` with identity stands in the gate
  facing +Z. The code rotates the slide about local +Z by 90° × rotation.
- **`IA_slide_rot`:** a small knurled rotation knob on the carrier; rotation −90° × steps about
  local +X (cosmetic).
- **`IA_slide_lamp`:** a toggle switch on the side; ON = +30° about local +X.
- **`lamp_glow`:** its own emissive object.
- **`lens_origin`:** an empty at the lens front centre.

## 6. Group D — vault and items

### vault_door.glb (≤ 14k)
Origin at world (1.5, 0, −3.5) on the wall face; local z = 0 is the wall face, +Z is into the room.

**`vault_frame`** (static, `M_Concrete` and `M_Steel_Dark`):
- a square frame plate x ∈ [−1.2, 1.2], y ∈ [0.15, 2.55], z ∈ [0, 0.10], with a round aperture
  Ø 1.90 centred at (0, 1.35);
- a stepped steel lining;
- a **tunnel sleeve** through the wall, z ∈ [−0.20, 0];
- rivets;
- a brass maker's plate with the Institute's mark.

**`IA_vault_door`:**
- a round door Ø 1.88, 0.40 thick (z ∈ [−0.24, +0.16]);
- polished steel face (`M_Chrome` / `M_Steel_Dark` rings, brass trim);
- **hinge:** an external hinge arm on the left; pivot = the hinge axis at local
  (−1.05, *, +0.22), axis +Y;
- **open = −95° about local +Y** (it swings into the room);
- the hinge knuckles and arm are static parts of `vault_frame`, except the arm half that belongs to
  the door.

**Children of `IA_vault_door`** (all identity at rest, origins at their pivots, positions in door
model space below):
- **`IA_vault_handle`:** a 6-spoke brass handwheel Ø 0.52 at (0, 0.98) on the door face. Each tap
  turns it −120° about local +Z (3 taps = one turn).
- **`bolt_<k>`**, k = 0..7:
  - polished locking-bolt heads in slots around the door's front rim, at angle k × 45°
    (counter-clockwise from +X) on radius ≈ 0.86;
  - the origin is at the bolt's centre;
  - **unlocked = translate 0.08 radially inward** (the code computes the direction from k).
- **`glass_disc`:**
  - a frosted glass viewing disc Ø 0.44 at (0, 1.62), its own object;
  - faces +Z, **UV 0..1** across the disc's bounding square (u left → right, v bottom → top);
  - a brass bezel ring `disc_bezel` around it;
  - the code puts its overlay shader on it.
- **Ports**, one on each side of the disc at (−0.55, 1.62) and (+0.55, 1.62):
  - **`IA_port_left`**, **`IA_port_right`:** brass lens barrels Ø 0.15 protruding 0.12 from the
    door face, mouths facing +Z;
  - **`port_left_mount`**, **`port_right_mount`:** at the mouth centres; a `lumen_crystal` with
    identity stands in the mouth, face +Z;
  - **`light_pipe_left`**, **`light_pipe_right`:** glass rods in brass channels running from each
    port to the disc bezel. They are their own objects; the code makes them glow.
- **`IA_collar_left`:**
  - a knurled rotation collar around the left barrel, rotation **−45° × steps about local +Z**;
  - 8 engraved ticks, with the 0/4 ticks marked by a small upright line;
  - a fixed index on the barrel top.
- **`IA_collar_right`:** the same on the right barrel.
- **`IA_zoom_right`:**
  - a second, narrower collar in front of `IA_collar_right`, rotation **−40° × zoom about local
    +Z**;
  - 5 ticks numbered **0–4**.
- **Engraved brass plates** under the ports: **✦** (four-pointed star) under the left port and
  **☾** (crescent) under the right. Use 3D shapes, no text.

### vault_interior.glb (≤ 14k)
Built in **room coordinates**. The space is x ∈ [0.6, 2.4], z ∈ [−5.2, −3.7], y ∈ [0, 2.5]:
- steel-lined walls, a riveted ceiling and a concrete floor with a 0.4 m step down from the door
  sill;
- the tunnel continues from the door frame.

**Contents:**
- deposit-box walls on the side walls (static);
- a small steel table at (1.5, 0, −4.35) with **Leyla's field kit** (static): a canvas satchel, a
  torch, a thermos, a folded map, a notebook and a photograph;
- **`vault_projector`:** a small portable projector on the table, aimed at the back wall, with an
  empty `vault_lens_origin` and an emissive `vault_lamp_glow`;
- **`vault_reel_screen`:** a 0.90 × 0.60 pull-down screen on the back wall, centred
  (1.5, 1.85, −5.17), facing +Z, **UV 0..1**;
- **key cradle:** a velvet-lined (`M_Velvet`) brass plaque on the back wall centred
  (1.5, 1.15, −5.15), with two hooks:
  - `key_strand_mount` at (1.32, 1.18, −5.12), with `key_strand.glb` hanging face +Z;
  - `key_leyla_mount` at (1.68, 1.18, −5.12), with `key_leyla.glb`;
- **`cradle_clamp_left`, `cradle_clamp_right`:** their own objects; brass clamps that **slide
  −0.03 on local Y** to lock a key;
- **`vault_bulb`:** an emissive caged bulb at the ceiling (code);
- an empty **`vault_light`** at the bulb.

### Items (≤ 2.5k each)
Follow `docs/models/devices.md` "Inventory items" exactly:
- real size, origin at the centre of mass;
- natural pose, hero face +Z (flat items lie flat with the hero face up; list the inspect rotation
  they need);
- a QA render per item, plus the `items_lineup`-style sheet `qa/blender/ch2/items_ch2.png`.

| File | Description | Parts / decals |
|---|---|---|
| `leyla_badge.glb` | Laminated staff badge, 0.086 × 0.054, with a metal clip and a cord stub. Front shows the photo, the name and the number **0417** | `badge_face`: UV 0..1, `M_Decal_Badge` |
| `index_card.glb` | Cream index card, 0.125 × 0.075, with **8 edge positions along the top edge**, left → right as positions 1..8. **Notched (V-cut through the edge) at positions 1, 3, 4 and 7**, plain at 2, 5, 6 and 8, so the pattern is `1 0 1 1 0 0 1 0`. Small printed position numbers under each position | `card_face`: UV 0..1, `M_Decal_IndexCard` (typed text) |
| `request_card.glb` | Buff request card, same size, with a printed header and 8 numbered punch positions along the top | `card_face`: `M_Decal_RequestCard`. Holes `hole_<i>` (i = 0..7, dark discs, separate objects; the code shows the punched ones) |
| `file_folder.glb` | Manila personnel folder, 0.24 × 0.32, closed, with a string tie and a side tab | `folder_face`: UV 0..1, `M_Decal_FileCover` |
| `locker_key.glb` | Small steel locker key with a round brass tag stamped **9** (3D) | — |
| `pocket_receiver.glb` | Bakelite pocket receiver, 0.075 × 0.12 × 0.03: a meter window with a needle, a tuning thumbwheel (name it `tuning_knob`), a telescopic antenna and a leather strap loop | `needle` (own object). Identity points at 12 o'clock. The code rotates it by (40° − 16° × bars) about local +Z, bars 0..5. Meter face with 5 bar marks |
| `tape_reel.glb` | 5-inch plastic reel (Ø 0.127) wound with brown tape, a paper label on the hub side | `label`: UV 0..1, its own object; the code sets `M_Decal_TapeLabel_1996/1997/1998` |
| `film_reel.glb` | 16 mm metal film reel, Ø 0.18, three spokes, wound with film (`M_Film`) | — |
| `lumen_crystal.glb` | Blank Lumen crystal: a crystal disc Ø 0.05, 6 mm thick (`M_Crystal`) in a thin brass bezel with a small grip tab, standing on edge, face +Z | `crystal_face`: its own front disc, UV 0..1; the code shows the recorded image on it |
| `glass_slide.glb` | Lantern slide, 0.082 × 0.082, glass in a card mount with tape edges. The mark image is in the middle | `slide_image`: UV 0..1, `M_Decal_SlideMark` |
| `key_strand.glb` | Large ornate brass key, 0.14 long, with **Strand's mark** (ring + vertical meridian line) pierced in the bow | — |
| `key_leyla.glb` | Slender steel key, 0.11 long, with **Leyla's sign** (crescent + three dots) pierced in the bow | — |

## 7. Group E — echoes
Use `lib_echo` and follow `echo_leyla_sitting.py` and `echo_strand_standing.py`:
- the same pipeline, material `M_Echo`, proportions, quality bar and QA ghost renders;
- each figure is one smooth mesh, except where a part must move.

| File | Pose | Parts |
|---|---|---|
| `echo_leyla_standing.glb` | Leyla (same face and hair as the sitting echo), standing, turned slightly. Her **right arm points forward-down** at a drawer 0.55 m in front of her and 0.7 m high. Her left hand is at her side. Coat/lab coat as in Chapter 1. Origin = between her feet; she faces +Z | `echo_head` (own object, pivot at the neck) |
| `echo_archivist.glb` | An older archivist in a grey work coat, sleeve protectors, spectacles. He stands at a catalogue drawer (0.45 m in front, drawer at 1.0 m), fingers walking the cards. Origin between his feet, facing +Z | `echo_head` |
| `echo_scientists.glb` | Two figures in 1979 lab coats, side by side, 0.7 m apart. A woman holds an archive box against her hip, a man reads an open ledger. They half-turn to each other. Origin = the midpoint between them on the floor, both facing roughly +Z | `echo_head_a`, `echo_head_b` |

## 8. Group F — decals, glyphs, materials
`tools/textures/make_decals_ch2.py` writes into `game/assets/textures/decals/ch2/`. It is
original procedural art (PIL + numpy), reusing the helpers and style of
`tools/textures/make_decals.py` (aged paper, ink).

Materials:
- Extend `tools/materials/make_extra_materials.py` with every new slot in §0 and every
  `M_Decal_*` below;
- write the `.tres`;
- add the new slots to `mrlib.PREVIEW`.

Puzzle data must match `archive_logic.gd`.

| File | Size | Content |
|---|---|---|
| `glyph_mark.png` | 512², RGBA | **Strand's mark**, matching the Chapter 1 emblem (`decals/wall_emblem.png`: a ring with a vertical meridian line). White on transparent, centred, ring outer diameter = 0.80 of the image. Symmetric under 180° |
| `glyph_sign.png` | 512², RGBA | **Leyla's sign**: a crescent opening to the right, with three dots in a vertical row inside its opening. White on transparent, centred, height ≈ 0.80. Not symmetric under 180° |
| `vault_engraving.png` | 512², RGBA | The engraving target, built **programmatically** from the glyphs: the mark at scale 1, upright, plus the sign **rotated 90° clockwise** and scaled **0.55**, both centred. Thin engraved lines (alpha ~0.6), as on etched glass |
| `film_frame_0..5.jpg` | 1200 × 800 | 1979 film frames, black-and-white with grain, scratches and gate weave. 0: the Array Hall (a vast hall with a ring machine of light). 1: Strand demonstrates light memory (a figure before a glowing disc). 2: the staff photo, 41 people in rows in the light. 3: Leyla draws her sign on the light glass (a woman's silhouette, the sign half-drawn). 4: the crowd raises hands toward the light. **5: Leyla's sign alone**, white on dark, centred, filling 60% of the height, sharp |
| `film_secret.jpg` | 1200 × 800 | 13 Nov 1979: Strand alone at the ring machine, the hall empty |
| `vault_reel.jpg` | 1200 × 800 | The Array Hall staff photo: **41 silhouettes in the light**, and at the far right edge a **42nd** figure in a 1990s coat, younger and alone: Leyla, 1998 |
| `routing_chart.png` | 600 × 840 | Enamel chart "PNEUMATIC POST", pictograms only for the solution. Rows: memo (folded note) → ✦; **request card (a card with a row of holes, the same look as the request card) → 📖 book**; sample vial → ⚗ flask; film can → 🎞 film; sealed envelope → ✉. Bottom: 🔒 with a red "sealed" bar |
| `dest_symbols.png` | 512², RGBA | The ring of 6 destination symbols around an empty centre, at clock positions 12 (✦ star), 2 (book), 4 (flask), 6 (film), 8 (envelope), 10 (padlock), drawn like the chart pictograms, cream enamel on a dark brass ring |
| `badge.png` | 860 × 540 | Institute staff badge: emblem, photo of Leyla (procedural portrait as in Chapter 1's photos), RAHIMOVA L., Dept. of Light Physics, № **0417**, issue year 1976 |
| `index_card.png` | 1250 × 750 | Typewritten catalogue card: № 0417, RAHIMOVA, Leyla, researcher, file in Stacks B-3, pencil note "req. via tube". The 8 positions along the top edge numbered 1–8, with the notches drawn **exactly** at 1, 3, 4 and 7 (matching the model's notch positions: centres at u = (k − 0.5)/8 for k = 1..8) |
| `request_card.png` | 1250 × 750 | Buff request form, "REQUEST — ARCHIVE B" header, 8 numbered punch circles along the top at u = (k − 0.5)/8 |
| `file_cover.png` | 1200 × 1600 | Manila folder: PERSONNEL — RAHIMOVA L. — 0417, a red stamp, a coffee ring |
| `tape_label_1996/1997/1998.png` | 512² | Round hub labels in Leyla's hand: "L.R. 1996" and a big **4.75** (likewise 1997, 1998) |
| `film_strip_0..3.png` | 900 × 300 | One 35 mm film strip each, sprocket holes top and bottom, three frames. The middle frame shows the **sundial obelisk** with a shadow of length **3, 1, 4, 2** units for strips 0, 1, 2, 3 (the unit fixed: 1 = 12% of the frame width; the sun's position consistent with shadow length) |
| `reel_can_lid.png` | 800² | A round can lid with a painted pictogram strip: **sunrise** at left (low sun, long shadow) → **high sun** at right (short shadow), with an arrow. No words needed |
| `slide_mark.png` | 512² | A lantern slide image: the mark, black on clear glass, a tape border |
| `archive_rules.jpg` | 700 × 1000 | "ARCHIVE B — RULES" notice (decorative; EN text is fine, it is not a clue) |
| `box_labels.jpg` | 1024² | Atlas of 4 × 8 archive-box label strips (typed codes like "B-3 / 1974 / 112") |
| `linoleum` texture set | 1024² | `game/assets/textures/linoleum/albedo.jpg` (+ normal, orm). 2 × 2 checker of 0.30 m tiles, worn, scuffed, waxed; it tiles seamlessly |

## 9. Group G — audio
Extend `tools/audio/synth_all.py` and the `tools/audio/sounds/` modules with original procedural
sounds, following the existing format and loudness. Sounds:
- shutter slam;
- emergency relay clicks;
- compressor start and wheeze, compressor loop;
- valve squeak;
- pneumatic whoosh plus canister thump;
- punch key clack, punch lever chunk;
- catalogue drawer slide, card flick;
- locker open and locker rattle;
- grille creak, hatch open, ledger thump;
- receiver static loop and receiver beep;
- tape deck: play clunk, tape hiss loop, garbled wow, end clicks, eject;
- rotary dial wind and return (per digit), booth door unlatch;
- splicer click, projector start, projector run loop, projector stop;
- slide projector clunk and fan hum loop;
- crystal record shimmer;
- vault collar click, vault bolts cascade, vault wheel, vault door groan;
- key lift;
- `music_archive` (calm, mysterious, analog), `music_archive_finale`, `amb_archive` (room tone
  with distant tubes and ticking).
