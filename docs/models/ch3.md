# Chapter 3 models — interface contract (The Underground Facility, Level −2)

This page is the **contract** between the Chapter 3 Blender models and the game code
(`game/src/rooms/underground/`, room and visuals still to be written). The code finds parts **by exact
name** and moves them with the conventions below, so names, pivots, axes, rest poses and mounts are binding.
Puzzle data comes from `docs/CHAPTER3_DESIGN.md` and `game/src/rooms/underground/underground_logic.gd`
(`UndergroundLogic`). Where this page and the design doc disagree on a placement, **this page wins** (it is
newer); §15 lists the differences so the design doc can be updated.

Each build group writes its measured results (final pivots, sizes, tris, surfaces, QA renders) to
`docs/models/ch3_<group>.md`; they are merged here when the group is done. The lead copies
`tools/blender/ch2_manifest.py` to `tools/blender/ch3_manifest.py` with the `MODELS` table of §13 (group,
tri budget, required names) and writes `docs/models/CH3_MANIFEST.md`. A model's required names are every
`IA_*` part, every `*_mount`, every other empty, and every part its section says the code moves, lights,
toggles or replaces.

## 0. Rules for every Chapter 3 model

**Tools.** Blender 5.2 headless scripts in `tools/blender/models/<name>.py`. Use the existing libraries:
- `mrlib` (materials, primitives, export), `lib_arch` (sweeps, mouldings, `import_glb` for QA scenes),
  `lib_mech` (lathe, knurls, text, screws), `lib_props`, `lib_devices` (`item_main`, centre of mass),
  `lib_echo` (figures, `M_Echo`);
- the Chapter 2 group libraries as worked examples (`lib_ch2_*.py`).

Read the Chapter 2 script of the same kind first: `vault_door.py` (symbol plates, hinged door, rotating
collars), `card_catalogue.py` (drawers with mounts), `compressor_panel.py` (rotary handles), `tape_deck.py`
(piano keys, spindles), `film_splicer.py` (decal quads), `key_strand.py` (keys), `echo_scientists.py`
(two figures in one GLB).

**Do not edit** existing `tools/blender/*.py`. Put new helpers in `tools/blender/lib_ch3_<group>.py`.
**Shared symbols:** `tools/blender/lib_ch3_symbols.py` (group A, first deliverable) holds the 2D outlines of
◆ ▲ ● ■ ☼ ☾ ✦. Every 3D inlay and the decal generator use it, so a symbol looks the same everywhere:
- ✦ is the four-pointed star and ☾ the crescent **opening to the right**, exactly as `sym_plate()` in
  `tools/blender/models/vault_door.py` (story anchors from Chapter 2);
- ☼ is a disc with 8 rays;
- ▲ is equilateral, point up; ● is a disc; ■ is a square; ◆ is a square turned 45°.

**Run:**
```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render]
```
- The export goes to `game/assets/models/<name>.glb`.
- QA renders go to `qa/blender/ch3/<name>[_n].png`: Cycles, at most 32 samples, at most 960×640, 2 threads.
  Render from the §2 views that show the model (same position, target and FOV), plus one hero shot and one
  shot of every moved state (door open, lever pulled, drawer out).
- List each script in your group's build list, `tools/blender/build_lists/ch3_<group>.txt`.
- `python3 tools/blender/check_glb_names.py game/assets/models/<name>.glb` must pass.

**Coordinates.**
- Godot = Blender (x, z, −y). Every number on this page is in **Godot axes, metres**. North is −Z.
- A model's **front faces +Z**. Yaw rotates about +Y: yaw 90 → front faces world +X, yaw −90 → −X,
  yaw 180 → −Z. Model +X becomes world −Z at yaw 90, world +Z at yaw −90 and world −X at yaw 180.
- **Origins:**
  - wall-mounted: floor level (y = 0) at the centre of the back face, on the wall plane, unless the
    model section says otherwise (ports, meter case, recorder);
  - free-standing: floor level at the footprint centre;
  - items: the centre of mass (`docs/models/devices.md`, `docs/models/ch2_items.md`);
  - **room-coordinate models** (`shell_choir`, `shell_gallery`, `shell_nursery`, `shell_lift`,
    `array_below`, `strand_office`, `leyla_camp`, `memorial_wall`): origin = world origin, built in place.

**Animated parts.**
- `IA_*` (tap targets) and every other moving part are **their own object**, origin at the pivot,
  **identity rotation at rest** relative to the parent. Parts moved only by code have no `IA_` prefix.
- A positive angle is counter-clockwise looking down the +axis toward the origin:
  - about +X, positive tips +Y toward +Z, so a lever "pulled toward the player" is positive and a
    back-hinged lid opens with a **negative** angle;
  - about +Y, a door hinged on its left edge (seen from the front) opens toward the viewer with a
    **negative** angle;
  - about +Z, positive is counter-clockwise seen from the front.
- The code applies `rest.basis * Basis(axis, deg)` or slides along a local axis (the Chapter 2
  `ArchiveVisuals._rot` / `_slide`, copied into the Chapter 3 visuals). Every part below states its
  **pivot, axis, step and travel**.

**Mount empties (`*_mount`).**
- An empty marks where the code attaches an item model or an echo figure. Its transform **includes
  orientation**: the model, parented with an **identity** transform, must sit exactly right.
- Items keep the natural poses of §9 (flat items lie flat, hero face +Y, top edge toward −Z; standing
  items face +Z). Where a mount turns an item out of its natural pose, the section names the rotation.
- Echo mounts lie on the floor with +Z pointing the way the figure faces. Each echo pose has **contact
  points** in its own frame (§10). The group that builds the mount computes its position so that the
  contact point meets the named target (lever grip, drawer front, socket).
- Test every mount in the QA render with the item GLB, or a proxy box of the §9 size if it does not exist yet.

**Colliders.** `ModelUtil.build_colliders` gives a padded AABB box to every `IA_*` mesh up to 0.15 m and an
exact trimesh to everything else; the tap prefers the smallest `IA_*` hit within 0.18 m behind the first
surface. So:
- no static mesh may cover a tap target from the §2 views;
- big moving parts (doors, drawers, leaves) never swallow the controls mounted on them: controls are separate
  `IA_*` children;
- thin things (tubes, wires) get a wider `IA_*` target named in their section.

**Names.**
- No name may end in a Godot import hint, even before trailing digits, dots, underscores or dashes:
  `_col`, `_convcol`, `_colonly`, `_rigid`, `_occ`, `_navmesh`, `_vehicle`, `_wheel`, `_noimp`.
- Chapter 3 traps: the meter-case and drum-lock "wheels" are `IA_case_dial_<i>` and `IA_drum_<i>`, and a
  drawer column is never `_col` or `_col_3`; use the drawer index. ("collar" is fine.)
- Every name on this page is unique inside its GLB (`ModelUtil.find` returns the first match). Instances of
  one GLB (three cabinets, three ports) repeat names; the code scopes lookups to the instance.

**Materials.**
- **At most 4 material slots per GLB.** Decal and shader slots count. A model that would need a fifth is
  split: that is why the office, its desk, the growth log, the recorder and the oscillograph are separate
  models.
- Lamps and indicators need **no emissive slot**: they use their glass or enamel slot and the code turns
  emission on (`ModelUtil.set_emission` works on any `BaseMaterial3D`). `M_Emissive_*` is used only where
  this page says so.
- Use the library slots listed in `docs/models/ch2.md` §0, including the Chapter 2 additions
  (`M_Linoleum`, `M_Paint_Green`, `M_Concrete`, `M_Steel_Cream`, `M_Velvet`, `M_Tape`…).
- New Chapter 3 slots: group A adds them to `tools/materials/make_extra_materials.py`, writes the `.tres` and
  adds them to `mrlib.PREVIEW`. In your script, create them with `M.material(name, color=…, rough=…, metal=…)`:

| Slot | Use | Preview colour, roughness, metallic |
|---|---|---|
| `M_Tile_Glazed` | Nursery walls: cream-white glazed tiles 0.15 m, grey grout, texture repeat 0.6 m | D9D6CB, 0.25, 0 |
| `M_Rock` | Lift shaft, shaft throat, Array cavern: dark wet rock | 2B2926, 0.85, 0 |
| `M_Chequer` | Lift lobby floor: chequer plate (geometry or normal map, **no alpha**) | 5E605B, 0.45, 0.85 |
| `M_Porcelain` | Transformer bushings and insulators: brown glaze | 5A3320, 0.15, 0 |
| `M_Shader_Quad` | Placeholder on every shader-driven surface (§11); the code replaces it with a `ShaderMaterial` | 1A1F1E, 0.3, 0 |
| `M_Decal_*` | The decals of §12 | — |

**Decals.**
- A decal is a separate quad with **UV 0..1**: u runs left → right and v bottom → top as the player sees it,
  never mirrored. Its slot is `M_Decal_<Name>`. The images come from group A in
  `game/assets/textures/decals/ch3/`.
- A decal with words has language variants `<name>_ru.png` and `<name>_uz.png` next to `<name>.png`;
  `DecalLoc` swaps them at runtime (§12). No other decal may carry words.
- For QA previews, pass `image=<abs path>` to `M.material` when the file exists; otherwise render anyway and
  re-render once it appears.

**Shader quads.** Every piece of **puzzle evidence that varies per game** (§11) is drawn on a quad or disc
with **UV 0..1** and the slot `M_Shader_Quad`. Never bake an answer into a texture. For QA renders only,
preview such a quad with the seed-0 image from `qa/blender/ch3/preview/` (written by group A). The GLB keeps
`M_Shader_Quad`.

**UVs.** World-scale UVs (1 UV unit = 1 m, `M.box_uv` / `lib_arch.finalize_uv`), except decals and shader
quads (0..1).

**Static labels.** Numerals (digits, Roman numerals I II III, the IEC marks I/O, pips) and symbols are
**3D text or inlaid geometry**, never decals. They are language-neutral. Words never appear on a model.

**Budgets.**
- Triangles: the per-model budget in its section header and in §13.
- **Surfaces** (mesh objects × materials = draw calls before shadows): the cap in the section header.
  Merge every static part of a model into one mesh per material. Every `IA_*` part uses **one** material
  unless its line says otherwise. Repeated small things (rivets, cups, crystals, globes, glyphs) are merged
  into one mesh.
- Textures: §13.4.
- Per view: **≤ 150 draw calls and ≤ 120k primitives, shadow passes included** (§13.3). Chapter 2's hall
  measured 216 and ~161k.

**Look.**
- `docs/ART_DIRECTION.md`: scientific romance, light as the protagonist, tactile brass mechanisms, dust and
  time, restraint.
- **Choir Hall:** a 1970s heavy-electrical hall. Board-formed concrete, a green-painted dado, riveted dark
  steel, brass tubes, brown porcelain bushings. Warm caged work lamps; blue-white arcs once the hall starts.
- **Resonance Gallery:** a cold concrete drum with brass rail and inlays. The glass floor glows cyan-white
  (`lumen`) from the Array below. Quiet and cathedral-like.
- **Nursery:** cold white glazed tiles, chrome autoclaves with frosted windows, cool fluorescent light.
- **Leyla's camp:** warm and cluttered, a 1998 field camp (canvas cot, car batteries, a tape recorder).
- **Lift:** rock, riveted steel, caged lamps.
- Model real detail (bevels, screws, wear); a phone camera gets close.

## 1. Layout (world, Godot coordinates)

### 1.1 Zones and openings

| Zone | Interior | Notes |
|---|---|---|
| **Choir Hall** | x ∈ [−13.0, −4.5], z ∈ [−4.0, 4.0], y ∈ [0, 6.0] | Walls 0.3 thick outside the box. Catwalk deck y = 4.0 over x ∈ [−13.0, −12.0]; gantry beam at z = 1.9, y 5.45–5.75 |
| **Resonance Gallery** | r ≤ 4.0 around (0, 0, 0), y ∈ [0, 4.5] | Drum wall r ∈ [4.0, 4.5]. Its inner face is **flat** at x = ±3.70 for \|z\| ≤ 1.6 (the door bays) |
| **Shaft** | glass disc r ≤ 1.5, top y = 0 | Brass rim r 1.5–1.62. Below it a bell mouth flares to r 4.0 at y = −1.2, then the cavern down to y = −31; the Array at y = −30 |
| **Nursery** | x ∈ [4.5, 13.0], z ∈ [−4.0, 4.0], y ∈ [0, 4.0] | — |
| **Leyla's camp** (in the Nursery) | x ∈ [4.5, 7.6], z ∈ [−4.0, −1.2], y ∈ [0, 2.9] | South wall z ∈ [−1.2, −1.05], east wall x ∈ [7.6, 7.75], roof slab y 2.9–3.0 |
| **Lift lobby** | x ∈ [−6.6, 6.6], z ∈ [4.7, 7.4], y ∈ [0, 3.0] | Cage interior x ∈ [−1.1, 1.1], z ∈ [4.9, 7.1], floor y = 0.25 |

The design doc gives the halls as x ∈ [−13, −4] and [4, 13]; with a Gallery of radius 4.5 those overlap the
drum. Here the hall interior faces are at |x| = 4.5, so the drum is tangent to them.

| Opening | Where | Size |
|---|---|---|
| West blast-door tunnel | z ∈ [−0.8, 0.8], y ∈ [0, 2.4], x from −3.70 (Gallery bay) to −4.5 (hall face) | Lining by `blast_door` |
| East blast-door tunnel | the same mirrored, x from 3.70 to 4.5 | Lining by `blast_door` |
| Shutter tunnel (Gallery ↔ camp) | z ∈ [−3.15, −2.05], y ∈ [0.30, 2.10], from the drum's inner face (x ≈ 2.46 at z = −3.15, ≈ 3.43 at z = −2.05) to the camp's west wall x = 4.5 | Lining by `shell_gallery`; `crystal_shutter` closes the camp end |
| Camp door | camp south wall, x ∈ [5.6, 6.6], y ∈ [0, 2.12] | `spectral_seal_door` |
| Choir ↔ lobby passage | x ∈ [−6.3, −4.8], z from 4.0 to 4.7, y ∈ [0, 2.6] | Lining by `shell_lift` |
| Nursery ↔ lobby passage | x ∈ [4.8, 6.3], z from 4.0 to 4.7, y ∈ [0, 2.6] | Lining by `shell_lift` |

### 1.2 Placement

Culling groups (§1.4): **C** Choir, **G** Gallery, **S** shaft, **N** Nursery, **K** camp, **L** lift.

| Model (id) | Group | Position | Yaw | Hotspot | Cull | Notes |
|---|---|---|---|---|---|---|
| `shell_choir` | A | (0, 0, 0) | 0 | — | C | Room coordinates |
| `shell_gallery` | A | (0, 0, 0) | 0 | glass_floor, tunnel | G | `IA_glass_floor`, `IA_tunnel_shutter` |
| `shell_nursery` | A | (0, 0, 0) | 0 | — | N (`camp_walls` also K) | |
| `shell_lift` | A | (0, 0, 0) | 0 | lift | L | `IA_passage_w`, `IA_passage_e` |
| `array_below` | A | (0, 0, 0) | 0 | — | S | Backdrop only |
| `freight_lift` | A | (0, 0, 6.0) | 0 | lift | L | Cage floor centre |
| `blast_door` (`door_west`) | A | (−3.70, 0, 0) | 90 | door_west | G + C | Front = Gallery side |
| `blast_door` (`door_east`) | A | (3.70, 0, 0) | −90 | door_east | G + N | Front = Gallery side |
| `transformer` (`transformer_0..2`) | B | (−12.45, 0, −3.0), (−12.45, 0, −1.3), (−12.45, 0, 0.4) | 90 | — | C | Welder echo at `transformer_1` |
| `choir_rack` | B | (−9.6, 0, −4.0) | 0 | rack | C | Rack x ∈ [−11.0, −8.2] |
| `choir_tube` | B | spawned once, tubes reparented (§4) | — | rack | C | 7 tubes |
| `tube_bench` | B | (−7.35, 0, −4.0) | 0 | rack | C | x ∈ [−8.05, −6.65], top y 0.86 |
| `strand_office` | B | (0, 0, 0) | 0 | office | C | Room coordinates; office x ∈ [−13.0, −10.2], z ∈ [1.2, 4.0] |
| `office_desk` | B | (−12.6, 0, 2.95) | 90 | office | C | Back to the west wall; top y 0.76 |
| `meter_case` | B | (−12.62, 0.76, 3.30) | 90 | case | C | On the office desk |
| `control_desk` | C | (−8.0, 0, 0.5) | 180 | desk | C | Footprint x ∈ [−9.3, −6.7], z ∈ [0.1, 0.9]; operator side north |
| `switch_cabinet` (`cabinet_0..2` = I, II, III) | C | (−7.4, 0, 4.0), (−8.3, 0, 4.0), (−9.2, 0, 4.0) | 180 | cabinet_0..2 | C | I is leftmost seen from the hall |
| `interlock_plate` | C | (−8.3, 0, 4.0) | 180 | plate | C | Image centre y 2.30, above cabinet II |
| `inspection_port` (`port_a`) | C | (−4.5, 0.85, 2.6) | −90 | port_a | C | East wall, low; origin = plate centre on the wall |
| `inspection_port` (`port_b`) | C | (−12.0, 4.55, 1.9) | 110 | port_b | C | On the catwalk handrail post |
| `inspection_port` (`port_c`) | C | (−8.6, 5.15, 1.9) | 180, **pitch +60°** | port_c | C | Under the gantry trolley; the code builds `Basis(UP, yaw) * Basis(RIGHT, pitch)` |
| `autoclave` | D | (8.4, 0, −3.5) | 0 | autoclave | N | The working one |
| `autoclave_dead` (`dead_0..2`) | D | (9.65, 0, −3.5), (10.9, 0, −3.5), (12.15, 0, −3.5) | 0 | — | N | Technician echoes at `dead_0`, `dead_1` |
| `growth_log` | D | at `autoclave` `log_mount` | — | autoclave | N | |
| `seed_library` | D | (13.0, 0, −0.6) | −90 | seed_library | N | Front plane x = 12.55, z ∈ [−1.35, 0.15] |
| `growth_chart` | D | (7.75, 0, −2.45) | 90 | chart | N | On the camp's east wall, outer face |
| `prism_bench` | D | (6.1, 0, 0.4) | 0 | prisms | N | Footprint x ∈ [5.45, 6.75], z ∈ [0.1, 0.7] |
| `spectral_seal_door` | D | (6.1, 0, −1.05) | 0 | seal | N + K | On the camp wall's south face |
| `leyla_camp` | E | (0, 0, 0) | 0 | camp | K | Room coordinates |
| `field_recorder` | E | (4.95, 0.74, −1.45) | 180 | recorder | K | On the camp table |
| `oscillograph` | E | (4.97, 0.74, −1.72) | 135 | recorder | K | Screen faces north-east |
| `crystal_shutter` | E | (4.5, 0, −2.6) | 90 | shutter | K + G | In the camp's west wall |
| `gallery_console` | F | (0, 0, 2.6) | 0 | console | G | Operator stands south, looks north over the shaft |
| `memorial_wall` | F | (0, 0, 0) | 0 | memorial | G | Room coordinates, north arc |
| echoes | H | at their mounts (§10) | — | — | zone of the mount | |

Reused models:
- `chair` (Chapter 1), pushed back in the office at (−11.8, 0, 3.55), yaw 60, clear of the office view;
- `letter` for `strand_letters` at `letters_mount`;
- `key_strand` / `key_leyla` at the lift `gate_key_mount_*` during the intro only.

### 1.3 Fixed points

| Point | World | Owner | Meaning |
|---|---|---|---|
| Lever n grip at rest | (−8.0 − (n − 3) × 0.36, 1.22, 0.38) | `control_desk` | Lever 1 is the east end |
| Master knob | (−9.07, 1.12, 0.43) | `control_desk` | West end |
| Step globes | (−6.80, 1.30 … 1.98, 0.20) | `control_desk` | The step counter |
| Choir slot k hang point | (−9.6 + (k − 3) × 0.34, 2.30, −3.80) | `choir_rack` | k = 0 is the west end |
| Cabinet n lock / window | (x_n + 0.12, 1.13, 3.48) / (x_n + 0.12, 1.45, 3.50) | `switch_cabinet` | x_n = −7.4, −8.3, −9.2 |
| Office lock | (−10.14, 1.05, 3.0) | `strand_office` | On the door, hall side |
| Drum lock, west / east | (−3.51, 1.35, 1.16) / (3.51, 1.35, −1.16) | `blast_door` | Gallery side, left of each opening |
| Console scope / cradle | (0, 1.25, 2.53) / (0, 0.98, 2.74) | `gallery_console` | |
| Socket 42 | (1.78, 1.15, −3.49) | `memorial_wall` | Bottom row, far right |
| Receptors 0..2 | (5.8 / 6.1 / 6.4, 1.15, −0.97) | `spectral_seal_door` | West → east |
| Shutter crystal hang points | (4.62, 2.02, −2.18 … −3.02) | `crystal_shutter` | Place 0 is the south end |
| Array centre | (0, −30, 0) | `array_below` | |

### 1.4 Culling groups and portal cards

The scene is one tree, but a phone draws only the groups a view needs. Every spawned model and every echo is
tagged with the group(s) in the Cull column; a node in two groups is drawn when either is.
- **Home groups:** every view in §2 lists its groups in the Draw column. The code hides every other group
  (`visible = false`, which also removes it from the shadow pass) and turns off the zone lights of hidden
  groups (§1.5).
- **Neighbours through an open opening:** a view draws a neighbour group only where §2 says so
  ("+N if door_east_open"). Elsewhere an open opening shows a **portal card** instead: an unshaded,
  double-sided quad of the opening's size, tinted with the far zone's light. The code builds it at the
  empty. Each card sits at the **far** end of its tunnel, as seen from the owner's zone, so the tunnel's depth
  still reads; its +Z points into the hidden zone. A closed opening shows its door.
- The camp door has no card. The camp is cheap, so the views that see that doorway draw K or N instead (§2).

| Portal empty | Owner (seen from) | World | +Z toward | Opening |
|---|---|---|---|---|
| `portal_w_c` | `shell_choir` | (−3.75, 1.2, 0), Gallery end of the west tunnel | +X (Gallery) | 1.6 × 2.4 |
| `portal_w_g` | `shell_gallery` | (−4.45, 1.2, 0), hall end of the west tunnel | −X (Choir) | 1.6 × 2.4 |
| `portal_e_g` | `shell_gallery` | (4.45, 1.2, 0), hall end of the east tunnel | +X (Nursery) | 1.6 × 2.4 |
| `portal_e_n` | `shell_nursery` | (3.75, 1.2, 0), Gallery end of the east tunnel | −X (Gallery) | 1.6 × 2.4 |
| `portal_shutter_g` | `shell_gallery` | (4.40, 1.2, −2.6), just behind the shutter leaves | +X (camp) | 1.1 × 1.8 |
| `portal_shutter_k` | `crystal_shutter` | (2.95, 1.2, −2.6), at the Gallery mouth | −X (Gallery) | 1.1 × 1.8 |

### 1.5 Lights

**At most one shadowed light per zone**, and only a `SpotLight3D` (one shadow pass). No omni shadows: a
dual-paraboloid omni costs two passes and a cube six. Chapter 2's two shadowed omnis are what doubled its
shadow geometry. A hidden group's lights are off.

| Zone | Light | Type | Position → aim | Shadow |
|---|---|---|---|---|
| Choir | `key_choir` | Spot 55°, range 10, warm | (−8.0, 5.6, 2.6) → (−8.6, 0, −1.2) | **yes** |
| Choir | `work_0..3` | Omni, range 5 | at `light_choir_0..3` | no |
| Choir | `office_lamp` | Omni, range 2.5 | `office_light` | no |
| Choir | `arcs` | Omni, range 4, blue-white, code flicker | (−12.3, 3.0, −1.3) | no |
| Gallery | `key_gallery` | Spot 60°, range 9, cool | (0, 4.4, 2.2) → (0, 0, −1.4) | **yes** |
| Gallery | `array_up` | Spot 40°, range 35, `lumen` | (0, −29, 0) → (0, 5, 0) | no |
| Gallery | `sconce_0..1` | Omni, range 4 | at `light_gallery_0`, `light_gallery_3` | no |
| Nursery | `key_nursery` | Spot 60°, range 8, cold | (9.8, 3.9, 0.2) → (9.8, 0, −3.4) | **yes** |
| Nursery | `fill_0..1` | Omni, range 5, cold | (6.8, 3.6, 1.2), (11.5, 3.6, 0.8) | no |
| Nursery | `prism_lamp` | Spot 25°, range 2.5 | (6.1, 1.0, 0.55) → (6.1, 1.15, −1.0) | no |
| Camp | `camp_lamp` | Omni, range 3, warm | `camp_light` | no |
| Lift | `cage_lamp` | Omni, range 3 | `cage_light` | no |

The code's camera-following `focus_fill` (as in Chapter 2) stays unshadowed. These mesh nodes never cast:
`*_walls`, `*_ceiling`, `*_trim`, `lift_shaft`, `cavern`, every glass, every echo, every mesh under 0.45 m
(`RoomBase.tune_shadows`).

## 2. Camera views

These are the views the game uses (`cam.add_view(id, pos, target, fov, root)`). Render your QA shots from
them. The interactive parts must be clearly visible and separately tappable from these views.
- Root views (free look) are marked R.
- Draw = the culling groups the view shows (§1.4).
- `glass_floor` looks 3° off vertical. `looking_at(target, UP)` handles that; no view may look exactly up
  or down.
- **The view id `seed_library` is fixed:** the logic's `look("seed_library")` triggers Leyla's echo on the
  leave path.

| View | Camera | Looks at | FOV | Draw |
|---|---|---|---|---|
| `lift_w` (R, intro for the Choir entry) | (0.5, 1.6, 6.4) | (−1.1, 1.35, 6.0) | 62 | L |
| `lift_e` (R, intro for the Nursery entry) | (−0.5, 1.6, 6.4) | (1.1, 1.35, 6.0) | 62 | L |
| **Choir Hall** | | | | |
| `choir` (R) | (−5.4, 1.65, 3.3) | (−9.6, 1.5, −2.0) | 62 | C, L |
| `choir_s` (R) | (−5.6, 1.65, −2.9) | (−10.6, 1.3, 2.6) | 62 | C |
| `office_door` | (−9.0, 1.5, 2.65) | (−10.2, 1.1, 2.75) | 50 | C |
| `office` (once open) | (−10.5, 1.6, 2.35) | (−12.55, 0.85, 2.95) | 56 | C |
| `ecg_lamp` | (−12.0, 1.3, 2.3) | (−12.62, 1.06, 2.45) | 40 | C |
| `meter_case` | (−12.05, 1.25, 3.3) | (−12.6, 0.84, 3.3) | 40 | C |
| `switch_room` | (−8.3, 1.65, 1.75) | (−8.3, 1.4, 4.0) | 58 | C |
| `cabinet_0` / `_1` / `_2` | (x_n, 1.45, 2.75) | (x_n, 1.3, 3.55) | 50 | C |
| `interlock_plate` | (−8.3, 2.05, 2.6) | (−8.3, 2.3, 3.97) | 40 | C |
| `desk` | (−7.8, 1.85, −1.6) | (−7.75, 1.2, 0.35) | 60 | C |
| `rack` | (−9.6, 1.8, −1.25) | (−9.6, 2.1, −3.65) | 58 | C |
| `rack_close` | (−9.6, 1.75, −2.4) | (−9.6, 1.75, −3.8) | 54 | C |
| `bench` | (−7.35, 1.6, −2.35) | (−7.35, 0.9, −3.7) | 50 | C |
| `port_a` | (−4.8, 0.95, 2.5) | (−7.4, 1.35, 0.5) | 36 | C |
| `port_b` | (−11.75, 4.65, 1.75) | (−8.2, 1.15, 0.45) | 34 | C |
| `port_c` | (−8.6, 4.95, 1.8) | (−8.3, 1.2, 0.4) | 40 | C |
| `port_a_mem` (technicians) | (9.1, 1.6, 0.4) | (10.3, 1.0, −2.45) | 50 | N |
| `port_b_mem` (welder) | (−10.0, 1.6, −0.9) | (−11.45, 0.9, −1.3) | 48 | C |
| `port_c_mem` (Strand at the rail) | (1.2, 1.65, 2.4) | (−2.05, 1.35, −0.4) | 50 | G, S |
| `blast_west_hall` | (−6.5, 1.6, 0.0) | (−4.5, 1.25, 0.0) | 56 | C (+G, S if door_west_open) |
| **Gallery** | | | | |
| `gallery` (R) | (−2.7, 1.65, 2.2) | (1.8, 1.0, −2.2) | 62 | G, S |
| `gallery_w` (R) | (2.7, 1.65, 2.2) | (−1.8, 1.0, −2.2) | 62 | G, S |
| `glass_floor` (H1) | (0, 1.55, 1.1) | (0, −30.0, −0.6) | 32 | G, S |
| `console` | (0, 1.55, 3.45) | (0, 1.0, 2.55) | 52 | G, S |
| `scope` | (0, 1.42, 3.0) | (0, 1.25, 2.53) | 34 | G |
| `strand_plate` | (−0.42, 1.3, 3.1) | (−0.42, 0.97, 2.76) | 34 | G |
| `cradle` | (0, 1.35, 3.15) | (0, 1.0, 2.74) | 38 | G |
| `memorial` | (0, 1.6, −1.2) | (0, 1.45, −3.92) | 60 | G |
| `socket_42` | (1.35, 1.4, −2.6) | (1.78, 1.15, −3.49) | 40 | G |
| `drum_west` | (−2.55, 1.45, 1.16) | (−3.55, 1.3, 1.16) | 46 | G |
| `drum_east` | (2.55, 1.45, −1.16) | (3.55, 1.3, −1.16) | 46 | G |
| `blast_west` | (−1.95, 1.6, 0.7) | (−3.7, 1.3, 0.0) | 56 | G, S (+C if door_west_open) |
| `blast_east` | (1.95, 1.6, −0.7) | (3.7, 1.3, 0.0) | 56 | G, S (+N if door_east_open) |
| `finale` | (0, 1.85, 3.75) | (0, 1.15, 0.4) | 66 | G, S |
| **Nursery** | | | | |
| `nursery` (R) | (5.7, 1.65, 3.3) | (10.6, 1.3, −2.6) | 62 | N, L (+K if camp_open) |
| `nursery_w` (R) | (12.2, 1.65, 2.9) | (6.4, 1.2, −0.8) | 62 | N (+K if camp_open) |
| `autoclave` | (8.4, 1.55, −1.55) | (8.4, 1.15, −2.95) | 54 | N |
| `cam_drum` | (8.7, 1.35, −2.25) | (8.7, 1.05, −2.88) | 40 | N |
| `growth_log` | (8.7, 1.55, −2.55) | (8.7, 1.5, −3.1) | 38 | N |
| `chart` | (9.1, 1.6, −2.3) | (7.8, 1.6, −2.45) | 44 | N |
| `seed_library` | (11.25, 1.45, −0.6) | (12.55, 1.24, −0.6) | 50 | N |
| `seed_drawer` (framed per open drawer i) | F_i + (−0.30, 0.36, 0) | F_i + (0.10, −0.04, 0) | 42 | N |
| `prisms` | (6.1, 1.75, 1.65) | (6.1, 1.0, −0.55) | 56 | N (+K if camp_open) |
| `seal` | (6.1, 1.3, −0.3) | (6.1, 1.15, −0.97) | 44 | N (+K if camp_open) |
| `camp` (once open) | (7.25, 1.6, −1.5) | (4.9, 1.2, −2.8) | 62 | K |
| `shutter` | (6.55, 1.55, −2.6) | (4.66, 1.6, −2.6) | 50 | K (+G, S if shutter_open) |
| `recorder` | (5.3, 1.32, −2.55) | (5.0, 0.84, −1.55) | 46 | K (+N if camp_open: the doorway is in frame) |
| **Cinematic only** | | | | |
| `hall_start` | (−5.8, 2.2, 2.9) | (−10.0, 2.4, −2.0) | 64 | C |
| `grow` | (8.4, 1.3, −2.3) | (8.4, 1.2, −3.1) | 40 | N |
| `array_rise` | (0, 1.7, 3.6) | (0, 2.6, −0.5) | 66 | G, S |
| `secret` | (0.6, 1.5, −1.8) | (1.7, 0.9, −3.3) | 52 | G |

F_i is the open drawer i's front centre (§6). x_n = −7.4, −8.3, −9.2 for cabinets I, II, III.

**Port views (M7).** A port view shows the **1979 loop**. In it the desk's levers, knob and step globes
follow the loop, not the player's state; leaving the view re-applies the state.
- Each step lasts 2.5 s, with a 1 s flicker between steps. Step k pulls lever `v_startup[k − 1]` (§11).
  After step 5 the knob turns to ●, and the loop restarts.
- **What each port witnessed is fixed by geometry:** `PORT_LEVERS = {A: [1, 2], B: [3, 4], C: [5] + knob}`.
- In port X the globes always show the step. The operator echo is drawn, and lever n moves, **only during
  steps whose lever is in PORT_LEVERS[X]**; at the other steps the desk stays still and the operator is
  absent.
- The operator is never drawn outside port views.
- Tapping `IA_port_ring` in a port view switches to that port's memory view (`port_X_mem`) and back. There the
  kept echoes are visible through the port and tappable: `release_echo(id, true)`. Port A shows `tech_a`
  and `tech_b`, port B `welder`, port C `strand_rail`.

**Clearance checks** (computed against the §1 boxes; keep them true when you model):
- **Port sight lines.** From `port_a` / `port_b` / `port_c` the lines to their levers and to the globes are
  clear. The operator stands north of the desk and every port is south of it, so he is always behind the
  levers he pulls. The step tower sits at the desk's north-east corner; at the east end of the back edge it
  would hide lever 1 from port A.
- **Office door** (open +100°, it lies along z ≈ 2.1 for x ∈ [−10.2, −9.33]): it is outside the
  `switch_room`, `cabinet_*` and `office` frusta.
- **Autoclave door** (left-hinged, swings toward the viewer): the growth log hangs on the vessel's **right**
  side, above the control pedestal, so the open door never covers it.
- **Camp door** slides west on the wall's outer face; a swinging leaf would block the `camp` view.
- **Shutter leaves, blast-door leaves and lift gates** slide or fold into pockets.
- **Meter case lid** opens up and back, away from the `meter_case` view.
- **Key-window flaps** open up and out above the held key.
- **`glass_floor` view.** The rail (r 1.75), the glass rim and the bell mouth all stay outside the frustum:
  the nearest is the glass's south edge at 17.6° against a 16° half-FOV. All four ring symbols fall inside
  ±10°.
- **`finale` view.** The console (board top 1.48) stays under the sight line to the target and to both echoes.
- **`port_c_mem` view.** Aim at Strand's torso (y 1.35); his hips are behind the rail.
- **`nursery_w` view.** The target stays in front of the camp wall (z = −0.8).
- **Desk view vs the operator.** The operator's mounts overlap the desk view's sight lines, which is one reason
  he is drawn only in port views.

## 3. Group A — shell, lift, doors, shared art

### shell_choir.glb (≤ 18k tris, ≤ 14 surfaces)
Materials: `M_Concrete`, `M_Paint_Green`, `M_Steel_Dark`, `M_Glass_Frosted`. Built in world coordinates (§1.1).

**Mesh objects** (separate nodes, for culling and shadows):
- `choir_floor`, `choir_walls`, `choir_ceiling`;
- `catwalk`, `gantry`;
- `choir_trim`: cable trays, conduits, pilaster capitals, lamp bodies;
- `lamp_glass_0..5`.

**Floor:** concrete with green-painted walkway strips 0.08 wide around the desk area, the rack front and the
switch-room front.

**Walls:** board-formed concrete with a green dado from 0 to 1.5 m. Concrete pilasters 0.40 × 0.15:
- north wall at x = −11.6 and −6.2;
- south wall at x = −9.95;
- east wall at z = −2.0 and +1.6.

**Openings:** the west-door tunnel mouth (§1.1; the tunnel itself is `blast_door`'s) and the lobby passage
x ∈ [−6.3, −4.8] in the south wall.

**Catwalk:**
- deck y = 4.0 over x ∈ [−13.0, −12.0], z ∈ [−4.0, 4.0], dark steel plate with no alpha and a toe board;
  cantilevered on wall brackets every 1.5 m (no posts in front of the transformers);
- handrail on x = −12.0, y 4.0–5.0, posts every 1.0 m; the post at z = 1.9 carries a mounting plate for
  `port_b`;
- a steel ladder at x ∈ [−12.9, −12.5], z = −3.95, from the floor to the deck.

**Gantry:**
- a crane I-beam across x ∈ [−13.0, −4.5] at z = 1.9 (flanges y 5.45–5.75), on wall corbels;
- a trolley block at x = −8.6 with a drop plate to y = 5.30 for `port_c`.

**Ceiling:** y = 6.0, two deep beams running along x at z = −2.0 and z = 3.2 (clear of the gantry).

**Lamps:** six caged bulkhead lamps at y = 3.4:
- north wall at x = −12.3 and −7.4;
- south wall at x = −11.6 (above the office roof) and −7.4;
- east wall at z = −2.8 and 2.2.

Each lamp has its body in `choir_trim`, its glass `lamp_glass_<k>` (own object, code emission) and an empty
`light_choir_<k>` at the bulb.

**Empties:** `portal_w_c` (§1.4).

### shell_gallery.glb (≤ 12k, ≤ 10)
Materials: `M_Concrete`, `M_Stone`, `M_Brass_Aged`, `M_Glass`.

**Drum:** interior r = 4.0, outer face r = 4.5 (modelled only where seen through openings). The inner face is
flat at x = ±3.70 for |z| ≤ 1.6 (door bays). Ceiling y = 4.5: flat concrete with 12 radial ribs and a ring
beam r = 1.6 above the shaft.

**Mesh objects:**
- `gallery_floor`: `M_Stone` ring r ∈ [1.62, 4.0] with brass inlay circles at r = 2.4 and 3.6;
- **`IA_glass_floor`**: the glass disc r = 1.5, top y = 0, 0.08 thick, `M_Glass`. It is the hotspot for the
  look-down view;
- `glass_rim`: brass ring r 1.5–1.62 with 24 rivets;
- `gallery_rail`: brass tube handrail ring r = 1.75, top y = 1.0, with 12 posts at φ = 15° + 30° k
  (φ measured from north, clockwise), so no post sits at N, E, S or W;
- `gallery_drum`, `gallery_ceiling`;
- **`IA_tunnel_shutter`**: the concrete lining of the shutter tunnel (§1.1) with a brass rim on the Gallery
  mouth;
- `lamp_glass_0..4`: brass sconces at y = 2.7, φ = 125°, 160°, 200°, 235°, 315°, with empties
  `light_gallery_0..4`.

**Memorial arc:** φ ∈ [−30°, 30°] is left plain (`memorial_wall` covers it).

**Empties:**
- **`echo_rail_mount`** (−2.05, 0, −0.40), yaw 79 (faces the shaft);
- **`echo_strand_mount`** (−2.30, 0, 1.00), yaw 40;
- **`echo_leyla_mount`** (2.30, 0, 1.00), yaw −40;
- `portal_w_g`, `portal_e_g`, `portal_shutter_g` (§1.4).

### shell_nursery.glb (≤ 14k, ≤ 12)
Materials: `M_Tile_Glazed`, `M_Linoleum`, `M_Steel_Cream`, `M_Glass_Frosted`.

**Mesh objects:**
- `nursery_floor`: `M_Linoleum`, without the camp area;
- `nursery_walls`: tiles to the ceiling;
- `nursery_ceiling`: cream steel panels;
- `nursery_pipes`: frosted, lagged pipes along the north wall at y 2.6–3.2, dropping to each autoclave;
- **`camp_walls`** (groups N and K): the camp's partitions per §1.1, cream-painted steel; the roof slab
  y 2.9–3.0; the camp's own floor patch in worn `M_Linoleum`; the doorway x ∈ [5.6, 6.6], y ∈ [0, 2.12];
  the shutter opening in the west wall (§1.1);
- `lamp_glass_0..4`: fluorescent fittings at y = 3.9, at (9.3, −2.2), (12.0, −2.2), (6.0, 1.6), (9.3, 1.6)
  and (12.0, 1.6), with empties `light_nursery_0..4`.

**Openings:** the east-door tunnel mouth at x = 4.5 and the lobby passage x ∈ [4.8, 6.3].

**Empties:** `portal_e_n` (§1.4).

### shell_lift.glb (≤ 7k, ≤ 8)
Materials: `M_Concrete`, `M_Rock`, `M_Chequer`, `M_Steel_Dark`.

**Mesh objects:**
- `lobby_floor` (chequer), `lobby_walls`;
- `lobby_ceiling`, with the shaft opening x ∈ [−1.25, 1.25], z ∈ [4.85, 7.15];
- `lift_shaft`: rock walls above the cage up to y = 12, with hoist rails;
- **`IA_passage_w`**, **`IA_passage_e`**: the steel-framed linings of the two passages (§1.1). They are the
  hotspot for the lift.

**`intro_shaft`** (own object, code): an open rock box around the cage just outside both gates
(x = ±1.45, z ∈ [4.75, 7.25], y from −6.0 to 3.0) with 2 × 5 steel lamp cages. Its bulbs are a separate
object, **`intro_bulbs`** (`M_Steel_Dark`; the code turns emission on). During the intro descent the code
hides the lobby, shows `intro_shaft` and slides it **+Y by up to 9.0** so the lamps pass upward, then hides
it on arrival.

### array_below.glb (≤ 6k, ≤ 10)
Materials: `M_Rock`, `M_Brass_Aged`, `M_Emissive_Lumen`, `M_Shader_Quad`. Built in world coordinates.

- `shaft_throat`: a brass-banded bell mouth under the glass rim, from r = 1.62 at y = −0.1 to r = 4.0 at
  y = −1.2. It flares at least 50° from vertical, so it never shows in the `glass_floor` view.
- `cavern`: an inward-facing rock dome r = 14 from y = −1.2 down to the floor at y = −31. Low-poly, nearly
  black; the fog does the rest.
- **`ring_0..3`** (own objects, outer → inner): emissive rings (`M_Emissive_Lumen`) at y = −30.0, radii
  7.0, 5.4, 3.8, 2.2, tube Ø 0.45, on brass pylons (static). The code dims them while dormant.
- **`ring_sym_0..3`**: one flat quad per ring, centred on the ring line at y = −29.70, face +Y. UV 0..1 with
  u → +X and v → −Z, so north is "up" in the `glass_floor` view. Slot `M_Shader_Quad`; the code assigns the
  ring's symbol (§11).

| Quad | Centre | Size |
|---|---|---|
| `ring_sym_0` | (−4.95, −29.70, 4.95) | 1.5 m |
| `ring_sym_1` | (3.82, −29.70, 3.82) | 1.5 m |
| `ring_sym_2` | (−2.69, −29.70, −2.69) | 1.2 m |
| `ring_sym_3` | (1.56, −29.70, −1.56) | 1.2 m |

- Empties: **`array_center`** (0, −30, 0) and **`rise_top`** (0, 2.6, 0). The code draws the 41 rising lights
  as one `MultiMesh` between them.

### freight_lift.glb (≤ 7k, ≤ 10)
Materials: `M_Steel_Dark`, `M_Steel_Painted`, `M_Brass_Aged`, `M_Glass_Frosted`. Origin = cage floor centre
at world (0, 0, 6.0).

**Cage** (static): interior local x, z ∈ [−1.1, 1.1]; floor at y = 0.25; riveted panel walls north and south;
corner posts; roof frame at 2.6 with the hoist sheave; static bridge ramps (1.0 long) from the cage floor
down to the lobby at both gates. A brass level plate shows **−2** in 3D numerals.

**Parts:**
- **`IA_gate_west`**: a collapsible lattice gate on the west face (`M_Steel_Painted`).
  - Origin at the north post, local (−1.1, 0.25, −0.95); the lattice extends +Z to +0.95, 2.1 high.
  - **Open = scale local Z to 0.15** about the origin: it folds against the north post.
- **`IA_gate_east`**: the same at local (+1.1, 0.25, −0.95).
- **`IA_gate_lock_west`**: a brass lock box on the inside of the west gate's south post at (−1.0, 1.15, 0.92),
  with **Strand's mark** (ring + meridian) inlaid.
  - **`gate_key_mount_west`** on its top: the Chapter 2 key stands blade down, bow up, bow face toward +X
    (into the cage). Used in the intro only.
- **`IA_gate_lock_east`** at (1.0, 1.15, 0.92), with **Leyla's sign**; **`gate_key_mount_east`** has its bow
  face toward −X.
- `cage_bulb` (own object, code emission) and the empty `cage_light`.

**Logic:**
- a key used on a gate lock → `use_item_on(key, "lift_gate_west" | "lift_gate_east")`;
- the gates have no logic state: the entry side's gate is shown open after the intro (from `entry`), the
  other stays shut.

### blast_door.glb (×2; ≤ 9k, ≤ 15)
Materials: `M_Steel_Painted`, `M_Steel_Dark`, `M_Brass_Aged`, `M_Enamel_Amber`.
- Front +Z = the Gallery side. Origin = the bay face at floor level.
- West: (−3.70, 0, 0), yaw 90. East: (3.70, 0, 0), yaw −90.

**Static parts:**
- `door_frame`: a plate x ∈ [−1.5, 1.5], y ∈ [0, 3.0], z ∈ [0, 0.12] around the opening
  x ∈ [−0.8, 0.8], y ∈ [0, 2.4]; amber/black chevrons on the lintel; rivets;
- the top rail and a pocket housing to local x = +2.8, hidden in the wall mass;
- the drum-lock box, left of the opening: x ∈ [−1.40, −0.92], y ∈ [0.85, 1.80], front at z = 0.24; dark
  steel with brass window bezels; one window per drum, shrouded so only the front symbol shows.

**Parts:**
- **`IA_door_tunnel`**: the tunnel lining from z = 0 to z = −0.80, floor plate included. It is the walk-through
  target once open.
- **`IA_blast_door`**: the leaf 1.8 × 2.55 × 0.25 at local z ∈ [−0.32, −0.07]; **open = slide +1.9 along local
  +X** into the pocket.
  - Gallery face: rivets and a large relief of the Institute's mark.
  - Hall face: a big handwheel (static, part of the leaf).
- **`IA_drum_<i>`** (i = 0..3; 0 = top = **outer** ring):
  - brass drums Ø 0.10 × 0.08, axis local +X, centres (−1.16, 1.545 − 0.13 i, 0.19);
  - 6 symbols as dark steel inlays, in `DRUM_SYMBOLS` order: 0 ☼, 1 ☾, 2 ✦, 3 ▲, 4 ●, 5 ■;
  - at rest symbol 0 faces +Z; symbol s sits at `Basis(X, +60° × s) * (0, 0, 1)` on the drum;
  - one step (+1) = **−60° about local +X** (the next symbol rolls up from below).
- **Ring icons** (static): beside each drum at local x = −0.99, a 3D brass inlay Ø 0.075 of four concentric
  circles with circle i bold (i = 0 outer). This is how the player knows drum i belongs to ring i.
- **`IA_drum_handle`**: a brass T-handle at (−1.16, 0.98, 0.21), pivot at its base; **pull = +45° about local
  +X**, momentary (code).
- **`drum_lamp`**: a jewel at (−1.16, 1.72, 0.25). Code: dark on the door that is not `sealed_door()`, amber
  while sealed, green once open.

**Logic:**
- on the door `sealed_door()`: drums → `turn_drum(i, 1)`, handle → `pull_drum_handle()`;
- on the other door's lock: a message only;
- leaf open ⇔ `door_west_open` / `door_east_open`.

### Shared art (group A, first)
- `tools/blender/lib_ch3_symbols.py` (§0).
- New material slots (§0).
- The decals of §12, written by `tools/textures/make_decals_ch3.py` into
  `game/assets/textures/decals/ch3/`. It reuses the helpers and style of `make_decals_ch2.py` (original
  procedural art, PIL + numpy).
- The QA previews in `qa/blender/ch3/preview/`: the seed-0 evidence for every shader quad of §11.

## 4. Group B — Choir Hall

### transformer.glb (×3; ≤ 5k, ≤ 4)
Materials: `M_Steel_Painted`, `M_Steel_Dark`, `M_Porcelain`, `M_Copper`. Free-standing, front +Z (faces into
the hall), origin at the footprint centre.

**Form:**
- a tank 1.20 w × 0.90 d × 1.75 h on a 0.12 plinth, with cooling fins on both sides and a bolted base seam;
- a conservator drum on top;
- three brown porcelain bushings up to y = 2.35;
- a riveted, blank rating plate;
- **Jacob's ladder:** two copper rods from the outer bushings rising and diverging, gap 0.03 at y = 2.35
  and 0.36 at y = 3.50, centred at x = 0, z = 0. **Nothing above y = 3.6** (the catwalk deck is at 4.0).

**Parts:**
- empties **`arc_base`** (0, 2.38, 0) and **`arc_top`** (0, 3.48, 0): the code spawns the climbing arc;
- **`hum_lamp`**: a jewel at (0.45, 1.50, 0.46) (code tint);
- **`echo_mount`** (−0.10, 0, 0.93), facing −Z (the tank). Used on `transformer_1` only: there the welder's
  `torch_tip` touches the base seam at (0, 0.62, 0.45).

### choir_rack.glb (≤ 6k, ≤ 13)
Materials: `M_Steel_Dark`, `M_Brass_Aged`, `M_Felt`, `M_Shader_Quad`. Wall-mounted at (−9.6, 0, −4.0).

**Frame:** posts at x = ±1.35, a top bar at y = 2.35 (front face z = 0.20), a bottom rail at y = 0.95,
depth 0.35, brass hanger brackets.

**Slots** k = 0..6, left → right from the front, at x_k = (k − 3) × 0.34. Hang point (x_k, 2.30, 0.20).
- **`IA_slot_<k>`**: a felt backing strip 0.24 × 1.15 behind the hang point (y 1.15–2.30, z = 0.08). It is the
  slot's tap target: the tubes are too thin to tap.
- **`slot_mount_<k>`** at the hang point: a tube parented with identity hangs straight down.
- Brass hooks at each hang point (static).

**Moving parts:**
- **`striker`**: a felt-padded bar across all slots at y = 2.12, z = 0.30, hanging on two arms from a pivot
  axis at y = 2.40, z = 0.30. **Strike = +15° about local +X** and back (code): the bar swings back into the
  tubes.
- **`IA_hammer`**: the master-hammer lever on the right post at (1.42, 1.10, 0.22), pivot at its base;
  **pull = +45° about local +X**, momentary.
- **`rack_lock`**: a brass locking bar over the hooks; **slides −0.05 on local Y** once `choir_tuned`.

**`stair_quad`** (the chalk staircase): a quad on the wall above the rack, x ∈ [−1.30, 1.30],
y ∈ [2.55, 3.45], z = 0.004.
- UV 0..1, u → +X, v → +Y; slot `M_Shader_Quad` (preview `chalk_grid.png` plus the seed-0 dots).
- The shader's geometry: column k centred at u = (x_k + 1.30) / 2.60; line h (h = 1..7) at
  y = 2.65 + 0.12 (h − 1), i.e. v = (0.10 + 0.12 (h − 1)) / 0.90.

**Logic:**
- tap `IA_slot_<k>` or the tube hanging there → `tap_tube(k)`;
- with the meter selected → `measure_tube(k)`;
- `IA_hammer` → `strike_hammer()`.

### choir_tube.glb (≤ 2.8k total, 7 surfaces)
Material: `M_Brass_Polished` only.
- Seven root-level objects **`IA_tube_<r>`**, r = meter reading 1..7.
- Each tube: length L = (8 − r) × 0.15 (r = 1 → 1.05 m … r = 7 → 0.15 m), Ø 0.05, brass end caps, a hanging
  eye at the top, and one engraved ring near the top. **No numbers:** the length and the meter are the cues.
- Origin = the top of the eye (the hang point); the tube hangs along local −Y.
- The code spawns this GLB once and reparents each tube to its place: `slot_mount_<k>`, `bench_mount_<j>`,
  or the "in hand" anchor 0.45 m in front of the camera, lower right.

### tube_bench.glb (≤ 2.5k, ≤ 5)
Materials: `M_Steel_Painted`, `M_Wood_Floor`, `M_Felt`. Back to the north wall at (−7.35, 0, −4.0);
1.40 × 0.60, top y = 0.86.

**Parts:**
- **`IA_bench_<j>`** (j = 0..2, front → back): felt V-cradles 1.15 long along local X at z_j = 0.45, 0.32,
  0.19, y 0.86–0.89.
- **`bench_mount_<j>`** at each cradle's left end (−0.55, 0.915, z_j), with basis **+90° about local +Z**: the
  tube's −Y axis points along +X, lying in the cradle.

**Dressing** (static): a tool rack and a felt mallet.

**Logic:** `IA_bench_<j>` → `tap_tube(7 + j)`.

### strand_office.glb (≤ 9k, ≤ 7)
Materials: `M_Glass`, `M_Wood_Panel`, `M_Brass_Aged`, `M_Decal_StaffPhoto`. Built in world coordinates.

**Partitions:**
- east at x = −10.2 (z ∈ [1.2, 4.0]) and north at z = 1.2 (x ∈ [−13.0, −10.2]);
- walnut panelling to 0.9 m, clear glass in brass mullions up to 2.8 m, a wooden roof slab at y 2.8–2.9;
- a doorway in the east partition: z ∈ [2.2, 3.1], y ∈ [0, 2.15].

**Parts:**
- **`IA_office_door`**: leaf 0.88 × 2.12 (panel below, glass above), hinged on its north edge; pivot
  (−10.2, 0, 2.22); **open = +100° about +Y** (it swings out into the hall).
- **`IA_office_lock`** (child of the door): a brass lock box on the hall face at the free edge,
  (−10.14, 1.05, 3.0), with a key slot on its top and a ■ inlay.
  - **`office_key_mount`** on the slot: `key_square` stands blade down, bow up, bow face toward +X (the hall).

**Dressing** (static):
- a filing cabinet in the north-west corner (x ∈ [−12.95, −12.45], z ∈ [1.3, 1.8]);
- a coat stand with Strand's lab coat at (−10.55, 0, 3.7);
- a framed staff photo on the west wall: quad `staff_photo`, 0.60 × 0.40, centred (−12.98, 1.65, 2.95),
  facing +X, UV 0..1, `M_Decal_StaffPhoto` (Chapter 2's `film_frame_2.jpg`, the 41 staff).

**Logic:**
- door → `toggle_office()`; `key_square` used on it → `use_item_on("key_square", "office_door")`;
- tap the lock with the key in it and the door closed → `take_office_key()`.

### office_desk.glb (≤ 5k, ≤ 6)
Materials: `M_Wood_Walnut`, `M_Brass_Aged`, `M_Paper`, `M_Decal_StrandNote`.
- Free-standing, front +Z = the sitter's side; at (−12.6, 0, 2.95), yaw 90.
- 1.30 w × 0.65 d, top y = 0.76.

**Parts:**
- A brass desk lamp at local (0.50, 0.76, −0.15); its shade centre is about (0.50, 1.12, −0.05).
  - **`IA_office_lamp`**: the lamp head (shade and arm), the pick-up target for the strip.
  - **`office_bulb`**: a frosted bulb (`M_Paper`, code emission); empty **`office_light`**.
- **`ecg_mount`**: on the shade's front rim at (0.50, 1.06, −0.02). The `ecg_strip` hangs clipped by its top
  edge, face toward local +Z (east, toward the `ecg_lamp` view): basis **+90° about local +X**.
- **`letters_mount`** (0.10, 0.765, 0.05): `strand_letters` (`letter.glb`) lies flat.
- **`IA_note`**: Strand's note, a 0.15 × 0.11 quad lying on the desk at (0.33, 0.762, 0.18). UV 0..1 with
  u → local +X and v → local −Z, so it reads upright from the east. Slot `M_Decal_StrandNote` (localized).

**Dressing:** a blotter, an ashtray, a few books, a fountain pen.

**Logic:**
- `IA_office_lamp` or the strip → `take("office_lamp")`;
- the letters (spawned `Item_` node) → `take("office_letters")`;
- `IA_note` → show `doc3.note`.

### meter_case.glb (≤ 2.5k, ≤ 7)
Materials: `M_Leather`, `M_Brass_Aged`, `M_Velvet`, `M_Enamel_Cream`.
- On the office desk at (−12.62, 0.76, 3.30), yaw 90 (the front faces east). Origin = the case's bottom
  centre.
- Case 0.30 w × 0.10 h × 0.20 d. On the front, three digit windows at x = −0.07, 0, +0.07, y = 0.055, with a
  brass symbol inlay above each: ☼, ☾, ✦ from left to right.

**Parts:**
- **`IA_case_dial_<i>`** (i = 0..2): cream enamel thumb drums Ø 0.04 × 0.014, axis local +X, centres
  (x_i, 0.055, 0.085).
  - Digits 0–9 in black 3D numerals; at rest 0 faces +Z; digit d sits at `Basis(X, +36° × d) * (0, 0, 1)`.
  - One step (+1) = **−36° about local +X**.
- **`IA_case_latch`**: a brass latch at (0, 0.02, 0.102).
- **`case_lid`**: hinged at the back top edge, pivot (0, 0.10, −0.10); **open = −100° about local +X** (code,
  when `case_open`).
- **`meter_mount`** (0, 0.04, 0) in the velvet recess: the `resonance_meter` lies on its back, face up, top
  toward −Z. Basis **−90° about local +X**.

**Logic:**
- dials → `turn_case_wheel(i, 1)`;
- latch → `try_case()`;
- the meter → `take("meter_case")`.

## 5. Group C — desk, ports, cabinets

### control_desk.glb (≤ 9k, ≤ 14)
Materials: `M_Steel_Painted`, `M_Brass_Aged`, `M_Bakelite`, `M_Enamel_Cream`.
- Free-standing at (−8.0, 0, 0.5), yaw 180. Its front (+Z, the operator side) faces north.
- Body 2.60 w × 0.80 d (local x ∈ [−1.30, 1.30], z ∈ [−0.40, 0.40]), top y = 0.86. Keep the back (south) edge
  low (≤ 0.90): the ports see the levers over it.

**Parts:**
- **`IA_lever_<n>`** (n = 1..5, left → right from the operator):
  - a brass stem with a brass ball grip, one material, in a raised quadrant along the front;
  - pivot (x_n, 0.95, 0.12) with x_n = (n − 3) × 0.36; the grip centre is 0.27 above the pivot;
  - rest = upright; **pulled = +50° about local +X** (top toward the operator). The code keeps a lever down
    while `levers[n − 1] == 1`.
- **`IA_master_knob`**: a bakelite pointer knob Ø 0.09 on the knob box (local x ∈ [0.92, 1.22],
  y ∈ [0.86, 1.30], face at z = 0.06), centre (1.07, 1.12, 0.07), axis local +Z.
  - Brass engravings: 0 ○ at 12 o'clock, 1 ▲ at 3, 2 ● at 6, 3 ■ at 9.
  - Position p = **−90° × p about local +Z**.
- **`step_globes`**: one mesh of five opal globes Ø 0.13 (`M_Enamel_Cream`) on a mast at the operator's left
  front corner, (−1.20, ·, 0.30). This is the step counter.
  - Globe k (1 = bottom) is centred at y = 1.30 + 0.17 (k − 1); the mast top is at 2.10.
  - **Vertex colour R = 0.2 × k** on globe k: the code's shader lights the globes with k ≤ lit.
  - Brass collars between the globes carry the 3D numerals 1–5 on four sides.
- **`IA_desk_hook`**: a brass hook on the front face at (−1.00, 0.70, 0.41).
  - **`desk_hook_mount`**: the ◆ key hangs by its bow, blade down, face +Z: basis **+90° about local +X**.
- **`desk_live_lamp`**: a jewel at (0.80, 1.00, 0.30). Code: dark while dead, green while `desk_live()`.
- **`lockout_tag`**: a cream enamel tag with a black 3D padlock, hanging from the knob box at
  (1.07, 0.98, 0.08). The code hides it once `desk_armed`.
- **`breaker_flag`**: a cream semaphore flag with a black bar, on the knob box top at (1.07, 1.30, 0.0), pivot
  at its base. **Trip = +70° about local +X** (it falls toward the operator); the code resets it after 1.2 s.
  Empty **`spark_origin`** at (1.07, 1.32, −0.05).
- **`op_mount_<n>`** (n = 1..5) at (x_n − 0.15, 0, 0.62) and **`op_mount_knob`** at (0.92, 0, 0.47): floor
  empties for `echo_operator`, **rotated 180° about Y** so the echo faces the desk. With the §10 contact
  points, the right hand meets lever n's grip, or the knob.

**Logic:**
- levers → `pull_lever(n)`;
- knob → `turn_knob(1)`;
- hook → `take("desk_hook")`; ◆ used on it → `use_item_on("key_diamond", "desk_hook")`.

### switch_cabinet.glb (×3; ≤ 3.5k, ≤ 8)
Materials: `M_Steel_Painted`, `M_Brass_Aged`, `M_Glass`, `M_Bakelite`.
- Wall-mounted on the south wall, yaw 180, at (−7.4 / −8.3 / −9.2, 0, 4.0) = cabinets I / II / III.
- Body 0.70 w × 1.90 h × 0.45 d on a 0.10 plinth; front face at z = 0.45.
- From the front: lock ledge and key window on the left, isolator on the right.

**Parts:**
- **`IA_lock`**: a brass barrel plug in a lock ledge (the ledge: x ∈ [−0.26, 0.02], y 1.10–1.13, protruding to
  z = 0.58). Barrel centre (−0.12, 1.13, 0.52), axis local +Y. **OFF = −90° about local +Y**: the code turns
  it with the isolator, so the key visibly turns and is trapped.
  - **`lock_key_mount`** (child of `IA_lock`) at (0, 0.004, 0): the key stands blade down in the slot, bow up,
    bow face +Z. Basis **+90° about local +X**.
  - **`lock_sym_diamond`**, **`lock_sym_triangle`**, **`lock_sym_circle`**, **`lock_sym_square`**: 3D brass
    inlays (0.05) on the ledge top around the keyhole. The code shows only the cabinet's own, from
    `CABINET_TAKES`: I ▲, II ◆, III ●.
- **`IA_key_window`**: a top-hinged glass flap 0.12 × 0.16 on a small key box at (−0.12, 1.45, 0.50). Pivot on
  its top edge (−0.12, 1.53, 0.51); **open = −100° about local +X**. The code opens it while the isolator is
  OFF.
  - **`held_key_mount`** inside the box at (−0.12, 1.46, 0.47): the held key hangs on a pin, blade down,
    face +Z. Basis **+90° about local +X**.
- **`IA_isolator`**: a bakelite rotary bar handle 0.18 long on a brass boss at (0.15, 1.28, 0.47), axis local
  +Z. ON (rest) = vertical; **OFF = +90° about local +Z**. The brass dial plate behind it has the IEC marks
  **I** at 12 o'clock and **O** at 9 o'clock.
- **`iso_lamp`**: an opal glass jewel at (0.15, 1.62, 0.46). Code: green ON, red OFF.
- **`num_1`**, **`num_2`**, **`num_3`**: brass Roman-numeral plates I, II, III at (0, 1.76, 0.455). The code
  shows the cabinet's own.

**Logic:**
- `IA_isolator` → `turn_isolator(n)`;
- `IA_lock` → `take_cabinet_key(n, "in")`; `IA_key_window` → `take_cabinet_key(n, "held")`;
- a key used on either → `use_item_on(key, "cabinet_<n>")`.

### interlock_plate.glb (≤ 0.6k, ≤ 2)
Materials: `M_Steel_Dark`, `M_Decal_InterlockPlate`.
- Wall-mounted at (−8.3, 0, 4.0), yaw 180.
- **`plate_image`**: a 0.90 × 0.45 quad centred (0, 2.30, 0.015), UV 0..1, facing +Z.
- A steel frame with four screws.

### inspection_port.glb (×3; ≤ 2k, ≤ 3)
Materials: `M_Brass_Aged`, `M_Crystal`, `M_Steel_Dark`.
- Origin = the back of the mounting plate (on the wall or post plane), front +Z.
- A brass porthole: mounting plate Ø 0.40, barrel Ø 0.30 × 0.15, a knurled ring, a crystal lens Ø 0.22 at
  z = 0.16.

**Parts:**
- **`IA_port_lens`**: the crystal disc. Code: an emission pulse while the 1979 loop plays.
- **`IA_port_ring`**: the knurled ring. Code: −30° about local +Z per tap (cosmetic). It switches between the
  port view and its memory view (§2).

**Placements** (§1.2): A on the east wall; B on the catwalk post; C under the gantry with pitch +60°.

**Logic:** none. The lens → `cam.go("port_X")`; the ring → `port_X_mem` and back.

## 6. Group D — Nursery

### autoclave.glb (≤ 9k, ≤ 12)
Materials: `M_Chrome`, `M_Steel_Dark`, `M_Brass_Aged`, `M_Glass`. Free-standing at (8.4, 0, −3.5), yaw 0,
footprint 1.00 × 1.00.

**Form** (static):
- a vertical chrome pressure vessel Ø 0.85 (y 0.35–1.95, domed top to 2.10) on a steel frame;
- lagging bands, a pressure gauge (needle fixed), pipes to the wall;
- a **control pedestal** in front, right: x ∈ [0.10, 0.50], z ∈ [0.45, 0.80], top y = 0.95;
- the **cam drum** housing on the pedestal top: a brass drum Ø 0.16 × 0.30, axis local X, centre
  (0.30, 1.05, 0.62). Each of its three columns has six holes, marked with 1–6 engraved pips, running from
  the front (hole 1, 30° above the front horizontal) over the top to the back (hole 6, 150°).

**Parts:**
- **`IA_ac_door`**: a round door Ø 0.42 centred (0, 1.20, 0.45), hinged on its left edge. Pivot
  (−0.21, 1.20, 0.46); **open = −110° about local +Y** (toward the viewer).
  - **`growth_window`** (child): a glass porthole Ø 0.24. The code drives the frost and the inner glow.
- **`chamber_mount`**: on a pedestal inside the chamber at (0, 1.08, 0.30), up +Y. The seed or the crystal
  stands there in its natural pose, visible through the window and through the open door.
- **`IA_peg_<i>`** (i = 0..2 = stages 1..3, left → right): brass pegs at x = 0.20, 0.30, 0.40, each pivoting
  about the drum axis (local +X through (·, 1.05, 0.62)). At rest = hole 1; hole p = **−24° × (p − 1) about
  local +X**.
- **`IA_start_lever`**: a brass lever on the pedestal's right side, pivot (0.52, 0.95, 0.62);
  **pull = +60° about local +X**. The code holds it down during the 8 s growth, then lets it return.
- **`IA_remelt`**: a brass push button with a flame pictogram on the pedestal front (0.20, 0.80, 0.81);
  **press = −0.006 along local Z**.
- **`log_mount`**: a hook bracket on the vessel's **right** front, (0.30, 1.66, 0.40). The `growth_log` hangs
  there with identity.
- **`ac_lamp`**: a jewel on the pedestal at (0.42, 0.97, 0.75). Code: amber while growing, green for clear,
  red for cloudy.
- Empty **`steam_origin`** at (0, 1.45, 0.47).

**Logic:**
- door → `toggle_autoclave()`;
- seed or cloudy crystal used on it → `use_item_on(item, "autoclave")`;
- the chamber's item → `take("autoclave")`;
- pegs → `turn_peg(i, 1)`; lever → `pull_start_lever()`; button → `remelt()`.

### autoclave_dead.glb (×3; ≤ 3.5k, ≤ 3)
Materials: `M_Chrome`, `M_Steel_Dark`, `M_Glass_Frosted`.
- The same silhouette as the autoclave, without the pedestal. Everything static and merged per material;
  frosted dead windows; one door baked ajar by 10°.
- **`echo_mount`** (0, 0, 0.62), facing −Z.
- Ids `dead_0..2` (§1.2).

### growth_log.glb (≤ 0.8k, ≤ 4)
Materials: `M_Wood_Panel`, `M_Brass_Aged`, `M_Decal_GrowthLog`, `M_Shader_Quad`.
- A clipboard 0.23 × 0.32 with a brass clip, hanging from a top hole.
- Origin = the hook point; the board hangs down local −Y, face +Z.

**Parts:**
- **`IA_growth_log`**: the board, the tap target.
- **`log_page`**: a 0.21 × 0.28 quad, UV 0..1, `M_Decal_GrowthLog` (localized words, a blank square for the
  sketch, and the fixed **clockwise one-third-turn arrow** around that square).
- **`log_sketch`**: a 0.09 × 0.09 quad 0.5 mm above the page, centred on the blank square (page u = 0.50,
  v = 0.36). UV 0..1, `M_Shader_Quad`: the hex glyph from the state (§11). The shader writes alpha 0
  outside the hexagon, so the page's arrow around it shows through.

**Logic:** tap → the `growth_log` view, then show `doc3.growth_log`.

### seed_library.glb (≤ 7k, ≤ 17)
Materials: `M_Wood_Walnut`, `M_Brass_Aged`, `M_Velvet`, `M_Shader_Quad`.
- Wall-mounted on the east wall at (13.0, 0, −0.6), yaw −90 (front faces −X).
- Carcass 1.50 w × 1.75 h × 0.45 d on a plinth, with seed jars on the top shelf (static).
- Brass frames on the carcass face around each drawer opening; nothing brass on the drawers themselves
  (one material each).

**Drawers:** 3 rows × 4 columns, index **i = 4 r + c** (r = 0 top, c = 0 left from the front). So drawer 6 is
"row 2, column 3" in the design doc's 1-based words.
- Fronts 0.30 w × 0.22 h, centred x_c = (c − 1.5) × 0.33, y_r = 1.50 − 0.26 r; front plane z = 0.45.

**Parts:**
- **`IA_seed_drawer_<i>`**: a drawer box 0.30 × 0.22 × 0.40 with a turned walnut knob (one material). Pivot at
  the front-face centre; **open = slide +0.24 along local +Z**.
- **`seed_mount_<i>`** (child of the drawer) at (0, −0.05, −0.12) from the pivot: a velvet cup where
  `seed_crystal` stands upright.
- **`glyph_panel`**: ONE mesh of 12 square quads 0.13 × 0.13, one on each closed drawer front at
  (x_c, y_r + 0.02, 0.452).
  - UVs: quad i covers the cell u ∈ [c/4, (c + 1)/4], v ∈ [(2 − r)/3, (3 − r)/3], with u → local +X and v → +Y.
  - Slot `M_Shader_Quad`: the code's `hex_glyph` shader draws glyph i in cell i and blanks the open drawer's
    cell.
- **`glyph_open`**: a single 0.13 × 0.13 quad, UV 0..1, `M_Shader_Quad`. The code parents it to the open
  drawer's front and gives it that drawer's glyph.
- **`echo_touch_mount_<c>`** (c = 0..3): floor empties at (x_c + 0.40, 0, 0.87), rotated 180° about Y (Leyla
  faces the library). With `pose_touch_<r>` her left fingertips touch drawer (r, c) (§10).

F_i, used by the `seed_drawer` view, is drawer i's front centre once open: library-local (x_c, y_r, 0.69).

**Logic:**
- drawer → `open_seed_drawer(i)`;
- the seed in the open drawer → `take("seed_drawer")`;
- a seed used on the library → `use_item_on("seed_crystal", "seed_library")`;
- arriving at the `seed_library` view → `look("seed_library")`.

### growth_chart.glb (≤ 0.8k, ≤ 3)
Materials: `M_Steel_Cream`, `M_Glass`, `M_Shader_Quad`.
- On the camp's east wall at (7.75, 0, −2.45), yaw 90.
- An enamel frame 0.66 × 0.86 with a glass cover.
- **`chart_image`**: a 0.60 × 0.80 quad centred (0, 1.60, 0.02), UV 0..1, `M_Shader_Quad`
  (preview `growth_grid.png` plus the seed-0 curve).

### prism_bench.glb (≤ 5k, ≤ 12)
Materials: `M_Steel_Dark`, `M_Brass_Aged`, `M_Crystal`, `M_Bakelite`.
- Free-standing at (6.1, 0, 0.4), yaw 0. The front (+Z, the player's side) faces south; the fans leave the
  back (−Z) toward the seal 1.4 m north.
- An optical bench 1.30 × 0.60, top 0.86.

**Parts:**
- Lamp house (static, bakelite, **top ≤ 0.98** so the `prisms` view sees over it) at the front centre
  (0, ·, 0.18), with two slit windows aimed at the prisms.
  - **`prism_lamp`**: its lens strip (`M_Crystal`, code emission).
- **`IA_prism_p`** (left, P) and **`IA_prism_q`** (right, Q): each a brass turntable Ø 0.18 (y 0.86–0.90)
  with a glass equilateral prism (side 0.06, height 0.12) on a 0.04 pedestal. Two materials, two surfaces
  each.
  - Pivots (∓0.28, 0.88, −0.08).
  - Position v ∈ −2..2: **−12° × v about local +Y**. Identity = v 0; +1 moves the fan one receptor to the
    right.
  - Five tick marks on the bench around each turntable; the centre tick is longer.
- **`IA_p_left`**, **`IA_p_right`**, **`IA_q_left`**, **`IA_q_right`**: bakelite nudge buttons with brass ◀ ▶
  inlays on the front edge, under each turntable at (∓0.28 ∓ 0.06, 0.80, 0.30).
  **Press = −0.004 along local Z**; left = −1, right = +1.
- Empties **`fan_origin_p`**, **`fan_origin_q`** at each prism's exit face centre (∓0.28, 1.00, −0.12). The
  code draws the three bands of each fan from there (§11).

**Logic:** buttons → `turn_prism("p" | "q", ±1)`. Tapping a turntable steps toward the nearer end stop.

### spectral_seal_door.glb (≤ 5k, ≤ 7)
Materials: `M_Steel_Painted`, `M_Steel_Dark`, `M_Brass_Aged`, `M_Shader_Quad`.
- On the south face of the camp wall: origin (6.1, 0, −1.05), yaw 0 (front faces the bench).
- Opening local x ∈ [−0.50, 0.50], y ∈ [0, 2.10].
- Frame and top rail static; the rail spans x ∈ [−1.60, 0.60] so the leaf can park to the west.

**Parts:**
- **`IA_camp_door`**: a riveted steel leaf 1.04 × 2.12 × 0.06 at z ∈ [0.02, 0.08]. **Open = slide −1.05 along
  local X**: it parks in front of the wall, west of the doorway.
- **`receptor_<i>`** (i = 0..2, left → right = west → east; children of the leaf): discs Ø 0.16 in brass
  bezels at (−0.30 + 0.30 i, 1.15, 0.085), facing +Z. UV 0..1 over each disc's bounding square;
  `M_Shader_Quad` (§11).

**Logic:**
- nothing to operate here (the prisms do the work);
- leaf open ⇔ `camp_open`; afterwards the doorway leads to the `camp` view.

## 7. Group E — camp and shutter

### leyla_camp.glb (≤ 9k, ≤ 6)
Materials: `M_Fabric`, `M_Wood_Panel`, `M_Steel_Dark`, `M_Paper`.
- Built in world coordinates inside the camp (§1.1). The walls are `shell_nursery`'s `camp_walls`.

**Contents:**
- an army cot along the north wall (x ∈ [5.2, 7.2], z ∈ [−3.95, −3.30]) with a sleeping bag, a rucksack and a
  1990s field coat;
- a battery rig in the north-east corner (x ∈ [7.0, 7.55], z ∈ [−3.20, −2.50]): car batteries on a crate,
  with cables running to the table;
- a folding table against the south wall (x ∈ [4.6, 5.4], z ∈ [−1.85, −1.25], top y = 0.74);
- dressing: crates, a thermos and mug, a torch, a stack of tape boxes, blank papers pinned to the wall. No
  words or images.

**Parts:**
- **`camp_bulb`**: a bare bulb hanging at (6.2, 2.55, −2.6) (code emission); empty **`camp_light`**.

### field_recorder.glb (≤ 2.5k, ≤ 7)
Materials: `M_Leather`, `M_Chrome`, `M_Bakelite`, `M_Tape`.
- A 1990s portable reel-to-reel, 0.28 × 0.09 × 0.22, lying flat on the camp table at (4.95, 0.74, −1.45),
  yaw 180 (front faces into the camp). Origin = the bottom centre.

**Parts:**
- **`reel_l`**, **`reel_r`**: 5-inch reels with tape on spindles at (∓0.07, 0.095, −0.02); they **spin about
  local +Y** (code).
- **`IA_rec_rewind`** at (−0.03, 0.07, 0.10) and **`IA_rec_play`** at (0.02, 0.07, 0.10): piano keys with ◀◀
  and ▶ pictograms in 3D, pivot at their back edge. **Press = −8° about local +X**.
- **`rec_vu`**: a needle, pivot at its base, rest at the left stop. While playing, the code swings it from 0
  to −70° about local +Z.

**Logic:**
- play → `play_recorder()`;
- rewind → replays the recording from the start (code only, no logic state).

### oscillograph.glb (≤ 2k, ≤ 4)
Materials: `M_Steel_Cream`, `M_Bakelite`, `M_Glass_Dark`, `M_Shader_Quad`.
- A portable oscilloscope 0.22 w × 0.16 h × 0.30 d on the camp table at (4.97, 0.74, −1.72), yaw 135.
  Origin = the bottom centre. The screen faces north-east, so both the `shutter` and the `recorder` views
  read it.
- **`osc_screen`**: the CRT face 0.10 × 0.08 at (0, 0.09, 0.151), UV 0..1, `M_Shader_Quad` (§11).
- Knobs static.

### crystal_shutter.glb (≤ 5k, ≤ 9)
Materials: `M_Steel_Dark`, `M_Brass_Aged`, `M_Crystal`.
- In the camp's west wall at (4.5, 0, −2.6), yaw 90 (front faces +X into the camp). Origin = the wall plane at
  the frame's bottom centre.
- Frame 1.30 w × 2.10 h; opening x ∈ [−0.55, 0.55], y ∈ [0.30, 2.00]. Behind it the tunnel runs to the
  Gallery.

**Parts:**
- **`shutter_leaf_l`**, **`shutter_leaf_r`**: riveted leaves 0.56 × 1.72 meeting at x = 0.
  **Open = slide −0.58 / +0.58 along local X** into pockets (code, when `shutter_open`).
- **Crystal bar** (static): a brass bar across the frame top at y = 2.06, z = 0.12, with four hooks.
- **`frame_mount_<p>`** (p = 0..3, left → right from the front): hang points at (−0.42 + 0.28 p, 2.02, 0.12).
  A crystal parented with identity hangs from its wire.
- **`IA_tcrystal_<s>`** (s = 1..4 = size rank, 1 smallest): hexagonal tuning crystals with pointed ends, each
  on a fine brass wire loop.
  - Body lengths 0.07, 0.09, 0.11, 0.13 and Ø 0.022, 0.026, 0.030, 0.034; the body starts 0.08 below the hang
    point.
  - Origin = the top of the wire loop (the hang point); the crystal hangs along local −Y.
  - In the GLB, crystal s sits at `frame_mount_<s − 1>`. The code reparents them from the state (§11).
- Empty `portal_shutter_k` at local (0, 1.2, −1.55), i.e. world (2.95, 1.2, −2.6) at the tunnel's Gallery
  mouth, +Z toward local −Z (§1.4).

**Logic:** crystal s → `tap_crystal(pos)`, where pos is the frame place it hangs at.

## 8. Group F — Gallery console and memorial wall

### gallery_console.glb (≤ 8k, ≤ 12)
Materials: `M_Wood_Walnut`, `M_Brass_Aged`, `M_Glass_Dark`, `M_Shader_Quad`.
- At (0, 0, 2.6), yaw 0. The front (+Z) faces south: the operator stands south of it and looks north across
  the shaft.
- Body 1.40 w × 0.60 d. A sloped desk runs from the front edge (z = 0.30, y = 0.92) up to (z = −0.06,
  y = 1.02). Behind it stands a vertical instrument board: z ∈ [−0.12, −0.07], y ∈ [1.02, 1.48].

**Parts:**
- **`scope_screen`**: a round CRT face Ø 0.24 centred (0, 1.25, −0.065), facing +Z. UV 0..1 over its bounding
  square, `M_Shader_Quad`. A brass bezel with `M_Glass_Dark` glass (static).
- **`IA_knob_x`** (left, the Choir) at (−0.34, 1.20, −0.06) and **`IA_knob_y`** (right, the Nursery) at
  (0.34, 1.20, −0.06):
  - knurled brass knobs Ø 0.07, axis local +Z, identity pointer at 12 o'clock;
  - value v (1..5) = **(60° − 30° × (v − 1)) about local +Z**;
  - brass numerals 1–5 engraved around each knob at 150°, 120°, 90°, 60°, 30°;
  - a 3D tube-rack pictogram under X and a crystal pictogram under Y.
- **`IA_cradle`**: a three-claw brass cradle on the slope centre at (0, 0.98, 0.14).
  - **`cradle_mount`** in it: the crystal stands upright.
  - **`cradle_ring`**: a thin ring around the cradle; the code makes it glow while a crystal is cradled.
- **`IA_strand_plate`**: Strand's brass plate 0.18 × 0.14 on the slope at (−0.42, 0.97, 0.16).
  - Its top face is UV 0..1 (u → +X, v → up the slope), `M_Shader_Quad`: the engraved figure (§11).
  - A frame with four screws and Strand's mark in 3D.
- **`choice_mount`**: a brass keystone socket on the slope at (0.42, 0.98, 0.16). The finale object
  (`strand_fork` or `nursery_crystal`) stands upright there.
- **`lamp_choir`** (−0.62, 1.42, −0.065) and **`lamp_nursery`** (0.62, 1.42, −0.065): jewels
  (`M_Glass_Dark`, code tint). Choir lamp on ⇔ `hall_started`; Nursery lamp on ⇔ `shutter_open`.

**Logic:**
- knobs → `turn_freq("x" | "y", ±1)`: a tap steps toward the nearer end stop; a drag goes both ways;
- a crystal used on the cradle → `use_item_on(item, "cradle")`;
- the cradled item → `take_from_cradle()`.

### memorial_wall.glb (≤ 6k, ≤ 6)
Materials: `M_Stone`, `M_Brass_Aged`, `M_Crystal`. Built in world coordinates.
- A curved polished-granite band on the drum's north arc φ ∈ [−30°, 30°], face at r = 3.92, y ∈ [0.95, 1.95].
- Above it, a brass pictogram band (y 1.95–2.15): 41 small standing figures and one apart at the right end,
  in 3D relief. No words.

**Sockets:** 42 brass cups on small ledges.
- Rows ρ = 0..2 (top → bottom) at y = 1.75, 1.45, 1.15.
- Columns c = 0..13 at φ_c = −27° + c × 54°/13 (west → east = left → right seen from the Gallery).
- Socket centre: (3.92 sin φ_c, y_ρ, −3.92 cos φ_c).

**Parts:**
- **`memorial_crystals`**: ONE mesh of the 41 crystals (every socket except row 2, column 13): small clear hex
  crystals 0.03 × 0.07 standing in their cups. The code turns emission on for all of them at once.
- **`IA_socket_42`**: the empty cup at row 2, column 13, (1.78, 1.15, −3.49).
  - **`socket_42_mount`**: a crystal stands upright in it, facing the Gallery centre.
  - **`socket_42_ring`**: a brass ring around it; the code makes it glow when `secret`.
- **`echo_kneel_mount`**: (1.49, 0, −3.02), yaw 153 (facing the socket). There Leyla 1998's `pose_kneel` palm
  meets the socket.

**Logic:**
- a crystal used on the socket → `use_item_on(item, "socket_42")`;
- the socketed item → `take_from_socket_42()`.

## 9. Group G — items

Follow `docs/models/devices.md` "Inventory items" and `docs/models/ch2_items.md`:
- real size, origin at the centre of mass;
- report the size, the bottom (y) and the tris, and run the back-face check;
- one QA render per item plus `qa/blender/ch3/items_ch3.png` (an `items_lineup`-style sheet);
- **flat items** lie flat, hero face +Y, top edge toward −Z (`ItemDB.FLAT` lists them; the inspect view tilts
  them 70°); **standing items** face +Z.

| File (≤ tris) | Pose | Description | Parts / slots |
|---|---|---|---|
| `key_diamond` / `key_triangle` / `key_circle` / `key_square` (≤ 1.2k each) | Flat, bow toward −Z, blade toward +Z (as `key_strand`) | Castell-style brass isolator key, 0.085 long: a round shank Ø 0.012 with a flat steel bit, and a flat bow 0.034 across shaped ◆ / ▲ / ● / ■, with the same shape embossed on its face. One blank, four bows; the silhouette is the cue | `M_Brass_Aged`, `M_Steel_Dark` |
| `resonance_meter` (≤ 2.5k) | Upright, face +Z (as `pocket_receiver`) | Strand's handheld meter, 0.085 × 0.15 × 0.04, bakelite: a round dial window with a cream scale 1–7 in 3D numerals, a brass probe rod on top ending in a small fork, a leather wrist strap | **`needle`** (own object, pivot at its base): identity at the left stop, pointing at polar 142.5°; reading r = **−15° × r about local +Z** (r = 1 → 127.5°, r = 7 → 37.5°); numerals at those angles. Empty **`probe_tip`** |
| `ecg_strip` (≤ 0.4k) | Flat, face up, the bracketed edge toward −Z | ECG paper strip 0.32 × 0.05, slightly curled, with a clip hole in the top edge centre | **`strip_face`**: UV 0..1 (u along the trace, left → right as it reads ☼ ☾ ✦), slot `M_Decal_EcgPaper`; `ItemDress` puts the trace shader on it (§11). Edges `M_Paper` |
| `seed_crystal` (≤ 0.8k) | Upright, face +Z | A tiny clear hexagonal seed crystal 0.012 Ø × 0.020 in a brass collar | `M_Crystal`, `M_Brass_Aged` |
| `nursery_crystal` (≤ 1.5k) | Upright, tip up, face +Z | A clear hexagonal crystal Ø 0.045 × 0.11 with a pointed tip, on a small brass foot (the seed collar) | **`crystal_body`** (own object, `M_Crystal`). For `cloudy_crystal`, `ItemDress` swaps it to a milky material. Report the bottom: the code grows it from the base (scale 0.15 → 1 over 8 s, origin offset by the bottom) |
| `strand_fork` (≤ 1.2k) | Upright, stem down, tines up, face +Z | Strand's steel tuning fork, 0.24 long, with a brass ball foot carrying his mark | `M_Chrome`, `M_Brass_Aged`. A finale prop, not an inventory item |

`strand_letters` reuses `letter.glb`. The `cloudy_crystal` item uses the `nursery_crystal` model (already in
`ItemDB`).

## 10. Group H — echoes

Use `lib_echo` and the Chapter 2 echoes:
- the same pipeline, the single slot `M_Echo`, the proportions and the ghost QA renders;
- a figure is one smooth mesh per **pose object**;
- poses are root-level objects of one GLB; the code shows one at a time (`set_present`) and crossfades
  through the 1 s flicker;
- origin = between the feet, facing +Z;
- **no `echo_head` parts** are needed (the poses are static).

**Contact points** are in the figure's own frame (metres, +Z forward, −X = the figure's right).

| File (≤ tris) | Figure | Pose objects and contact points |
|---|---|---|
| `echo_operator` (≤ 30k file, ≤ 6k per pose) | The 1979 operator: work coat, cap, headphones round the neck | **`pose_idle`**: looking up at the globes. **`pose_reach`**: right-hand grip at (−0.15, 1.22, 0.50). **`pose_pull`**: right-hand grip at (−0.15, 1.12, 0.29), the grip of a lever pulled 50°. **`pose_knob`**: right hand on the knob at (−0.15, 1.12, 0.40). **`pose_done`**: a step back, head turned toward the Choir. The code places him at `op_mount_<n>` / `op_mount_knob` (§5) |
| `echo_welder` (≤ 9k) | 1979 maintenance welder, mask flipped down, kneeling on one knee | One pose, **`pose_weld`**, holding a torch: empty **`torch_tip`** at (−0.10, 0.62, 0.48) for the code's sparks. At `transformer_1` `echo_mount` |
| `echo_technicians` (≤ 16k file, ≤ 8k each) | Two 1979 technicians in lab coats | **`tech_a`**: a woman reading the dead autoclave's gauge with a clipboard. **`tech_b`**: a man crouching at its valve. Root-level figures, each with its origin between its feet; the code reparents them to `dead_0` / `dead_1` `echo_mount`. Ids match the logic (`tech_a`, `tech_b`) |
| `echo_strand_rail` (≤ 18k file, ≤ 9k per pose) | Strand, 1979, the face of `echo_strand_standing` | **`pose_rail`**: both forearms on the rail at y = 1.0, z = +0.30…0.36, looking down into the shaft; at `echo_rail_mount`. **`pose_offer`**: standing, right arm out at chest height, the finale pose at `echo_strand_mount`; empty **`fork_mount`** in his right fist at (−0.20, 1.30, 0.45) (the fork stands upright) |
| `echo_leyla_1998` (≤ 40k file, ≤ 8k per pose) | Leyla in 1998: older (about 45), the face lineage of `echo_leyla_standing`, a 1990s field coat | **`pose_touch_0/1/2`**: left fingertips on a drawer at (+0.40, y, +0.42), y = 1.50, 1.24, 0.98 for rows 0, 1, 2; at `echo_touch_mount_<c>`. **`pose_kneel`**: kneeling, right palm on the socket at (−0.05, 1.15, 0.55); at `echo_kneel_mount`. **`pose_offer`**: standing, holding her crystal out; at `echo_leyla_mount`; empty **`crystal_mount`** in her right palm at (−0.20, 1.20, 0.45) (the crystal stands upright) |

**Visibility** (code):
- **Operator:** port views only (§2).
- **Kept echoes** (`welder` at `transformer_1`, `tech_a` / `tech_b` at `dead_0` / `dead_1`, `strand_rail` at
  `echo_rail_mount` in `pose_rail`):
  - on the take path, while a crystal is selected, in their own zone (`echo_visible(id)`);
  - on both paths, in the port memory views (`echo_visible(id, true)`);
  - gone once released.
- **Leyla at the library:** `echo_leyla_1998` in `pose_touch_<r>` after `leyla_echo:<i>`, with
  r = i / 4 and c = i % 4.
- **Finale:** `pose_offer` for both when `array_awake`.
- **Secret:** `pose_kneel` on `secret_echo`.

## 11. Variants: evidence rendered from the state

`docs/VARIANTS.md` builds Chapter 3's variants in from the start. **No answer is ever baked.**
- Each evidence surface is drawn from a state key.
- Until the logic provides a key, the scene reads `state.get(key, <constant>)`, so seed 0 equals today's
  canonical answers.
- The `v_*` keys below are what the scene expects. **`underground_logic.gd` has none of them yet** (§15).

| Puzzle | State key (to add) | Fallback now | Surface | How it is drawn |
|---|---|---|---|---|
| W3 Choir staircase | `v_choir`: 7 ints, the reading per slot (a permutation of 1..7) | `CHOIR_TARGET` | `choir_rack` `stair_quad` | `stair_chalk.gdshader`: `heights[7]`, the grid from `chalk_grid.png`, dot k on column k at line `heights[k]` (§4 geometry). The tube start is already state (`tubes`) |
| W4 lever order | `v_startup`: 5 ints, the lever per step (a permutation of 1..5) | `STARTUP` | Port views | The 1979 loop (§2): step k pulls lever `v_startup[k − 1]`; port X shows only `PORT_LEVERS[X]`. `step_globes.gdshader`: `lit` = the step |
| W2 heart strip | `v_heart`: 3 ints 2..9, the peaks in ☼ ☾ ✦ (also the case code) | `CASE_CODE` | `ecg_strip` `strip_face`, wherever it appears (lamp, inspect, icon) | `ecg_trace.gdshader`: `peaks` (ivec3). Brackets are printed at u ∈ [0.06, 0.32], [0.38, 0.62], [0.68, 0.94]. Exactly `peaks[b]` full QRS peaks evenly spaced inside bracket b, plus **one** peak in each gap and at each end, so counting the whole strip never gives a bracket's number. Low P/T waves everywhere |
| E1 seed | `v_glyphs`: 12 six-character strings; `v_seed_right`: int; `v_sketch`: string | `SEED_GLYPHS`, `SEED_RIGHT`, `SEED_SKETCH` | `seed_library` `glyph_panel` and `glyph_open`; `growth_log` `log_sketch` | `hex_glyph.gdshader`: a **flat-topped** regular hexagon (circumradius 0.42 of the quad). Edge e (0..5) runs clockwise from the top; edge e's outward normal is at 90° − 60° e (counter-clockwise from +u). Char e = '1' → a V-notch at the edge midpoint, 0.30 of the edge wide and 0.22 of the apothem deep. Uniforms `bits[12]`, `hidden` (the open drawer, −1 = none) and `style` (0 = engraved enamel plate, 1 = pencil on the log). Alpha is 0 outside the hexagon. This matches `rotate_glyph` (a clockwise third shifts edge e to e + 2). The turning arrow is fixed art on `growth_log.png` |
| E2 growth curve | `v_curve`: 3 ints 1..6, the plateau heights (= peg target) | `PEGS_TARGET` | `growth_chart` `chart_image` | `growth_curve.gdshader`: `levels` (ivec3) on the printed 6-line grid (`growth_grid.png`: line l at v = 0.12 + 0.13 (l − 1); stage s spans u ∈ [0.12 + 0.27 s, 0.39 + 0.27 s]). The curve rises from the axis to level 0, holds, steps to level 1, holds, steps to level 2, holds, then falls. Pencil-ink line with a slight hand wobble |
| E3 prism rims | `v_rims`: 3 bitmasks (▲ 1, ● 2, ■ 4); P and Q follow from them | `RIMS` | `spectral_seal_door` `receptor_<i>` | `seal_receptor.gdshader`: `rim` (bitmask), `light` (the bitmask from `receptor_light(p, q)`), `accepted`. The rim ring (r 0.38–0.50) takes the additive colour of `rim` (▲ red, ● green, ■ blue: yellow, magenta, cyan, white) **and** shows one cream symbol per bit (`sym_*.png`). The centre shows the incoming light's additive colour and its symbols in a row. The fans are code meshes from `fan_origin_*` to receptor v + k, or onto the door or wall when out of range |
| E4 melody | `v_frame`: 4 ints, frame place → size; `v_melody`: 4 ints, by size | `FRAME_SIZES`, `MELODY` | `crystal_shutter` `IA_tcrystal_<s>` placement; recorder; `osc_screen` | The code reparents crystal `v_frame[p]` to `frame_mount_<p>`. The recorder plays `v_melody`. `osc_wave.gdshader`: `cycles` = 2 + 2 × (5 − size), so denser waves mean a higher, smaller crystal |
| H1 ring symbols | `v_rings`: 4 ints 0..5, outer → inner (= the drum target) | `DRUM_TARGET` | `array_below` `ring_sym_<r>` | One decal per symbol, composed at runtime: the code gives quad r an unshaded, emissive material with `sym_<name>.png` for `v_rings[r]` |
| H2 Lissajous target | `v_freq`: 2 ints (a, b), the target X and Y; only coprime pairs with no equal-ratio twin in 1..5 | `[FREQ_X, FREQ_Y]` | `gallery_console` `IA_strand_plate` | `lissajous.gdshader`, `mode = engraved`: x = sin(a t + π/2), y = sin(b t), t ∈ [0, 2π], as a dark groove with a brass highlight. The live `scope_screen` uses the same shader with the knob values, `mode = phosphor`, and `live = scope_live()` (a dot when not live) |

The shaders live in `game/src/fx/` and are written by the room code, not the model groups. The port memory
views use `port_frost.gdshader` (an edge vignette, no gameplay role). Hints (level 3) also read the `v_*`
keys.

## 12. Language-neutral art and decals

**No words in any texture** except the localized decals below. Symbols, numerals, pips, the IEC I/O marks,
arrows and pictograms are art.
- Strings stay in `tools/localization/strings_ch3.py` and reach the player through `tr()`: `doc3.note` and
  `doc3.growth_log` are shown as document text when the note or log is tapped.
- No `Label3D` is required by this contract. If the code adds one, its text goes through `tr()`.

`tools/textures/make_decals_ch3.py` (group A) writes `game/assets/textures/decals/ch3/`:

| File | Size | Content | Slot |
|---|---|---|---|
| `sym_sun.png`, `sym_moon.png`, `sym_star.png`, `sym_triangle.png`, `sym_circle.png`, `sym_square.png`, `sym_diamond.png` | 512², RGBA | One symbol each, from `lib_ch3_symbols`: white on transparent, centred, height 0.80 of the image | `M_Decal_Sym_<Name>` (code uses them for the ring symbols and the seal) |
| `interlock_plate.png` | 1024 × 512 | Cream enamel plate. Top row: the key pictograms ◆ → ▲ → ● → ■ → a door. Bottom row, the rule in three pictogram panels: key into a lock face → isolator handle turned to O → the next key released from its window. No words | `M_Decal_InterlockPlate` |
| `ecg_paper.png` | 2048 × 320 | Salmon ECG grid paper with three hand-drawn pen brackets at u ∈ [0.06, 0.32], [0.38, 0.62], [0.68, 0.94], with ☼, ☾, ✦ above them. **No trace** | `M_Decal_EcgPaper` |
| `chalk_grid.png` | 1024 × 352, RGBA | The chalk grid of `stair_quad` on transparent: 7 faint column ticks and 7 lines at the §4 positions. **No dots** | shader input |
| `growth_grid.png` | 768 × 1024 | Leyla's graph paper: 6 horizontal lines (§11), three stage columns with small pictograms at the bottom (seed, flame, crystal), an axis arrow. **No curve** | shader input |
| `growth_log.png`, `_ru`, `_uz` | 768 × 1024 | A page of Leyla's log in her hand with `doc3.growth_log` in that language. A blank square at u 0.22–0.78, v 0.15–0.57 (0.118 m) for the sketch. Inside it, a **clockwise one-third-turn arrow** is drawn on a circle of radius 0.050 m around the centre (u 0.50, v 0.36), outside the hexagon's 0.038 m circumradius | `M_Decal_GrowthLog` |
| `strand_note.png`, `_ru`, `_uz` | 512 × 384 | `doc3.note` ("My heart keeps the count.") in Strand's hand, in that language | `M_Decal_StrandNote` |
| (reuse) `decals/ch2/film_frame_2.jpg` | — | The 41 staff, for the office photo | `M_Decal_StaffPhoto` |

**QA previews**, not shipped: `qa/blender/ch3/preview/` holds the seed-0 images for `stair_quad`,
`strip_face`, the glyph panel, `log_sketch`, `chart_image`, the receptors at the start state,
`IA_strand_plate` (3:2), `scope_screen` and `osc_screen`.

## 13. Budgets

### 13.1 Per model

| Model | Group | Tris ≤ | Surfaces ≤ | Materials |
|---|---|---|---|---|
| `shell_choir` | A | 18,000 | 14 | 4 |
| `shell_gallery` | A | 12,000 | 10 | 4 |
| `shell_nursery` | A | 14,000 | 12 | 4 |
| `shell_lift` | A | 7,000 | 8 | 4 |
| `array_below` | A | 6,000 | 10 | 4 |
| `freight_lift` | A | 7,000 | 10 | 4 |
| `blast_door` (×2) | A | 9,000 | 15 | 4 |
| `transformer` (×3) | B | 5,000 | 4 | 4 |
| `choir_rack` | B | 6,000 | 13 | 4 |
| `choir_tube` | B | 2,800 | 7 | 1 |
| `tube_bench` | B | 2,500 | 5 | 3 |
| `strand_office` | B | 9,000 | 7 | 4 |
| `office_desk` | B | 5,000 | 6 | 4 |
| `meter_case` | B | 2,500 | 7 | 4 |
| `control_desk` | C | 9,000 | 14 | 4 |
| `switch_cabinet` (×3) | C | 3,500 | 8 | 4 |
| `interlock_plate` | C | 600 | 2 | 2 |
| `inspection_port` (×3) | C | 2,000 | 3 | 3 |
| `autoclave` | D | 9,000 | 12 | 4 |
| `autoclave_dead` (×3) | D | 3,500 | 3 | 3 |
| `growth_log` | D | 800 | 4 | 4 |
| `seed_library` | D | 7,000 | 17 | 4 |
| `growth_chart` | D | 800 | 3 | 3 |
| `prism_bench` | D | 5,000 | 12 | 4 |
| `spectral_seal_door` | D | 5,000 | 7 | 4 |
| `leyla_camp` | E | 9,000 | 6 | 4 |
| `field_recorder` | E | 2,500 | 7 | 4 |
| `oscillograph` | E | 2,000 | 4 | 4 |
| `crystal_shutter` | E | 5,000 | 9 | 3 |
| `gallery_console` | F | 8,000 | 12 | 4 |
| `memorial_wall` | F | 6,000 | 6 | 3 |
| each item (§9) | G | as listed | ≤ 3 | ≤ 2 |
| `echo_operator` | H | 30,000 file / 6,000 drawn | 1 | 1 |
| `echo_welder` | H | 9,000 | 1 | 1 |
| `echo_technicians` | H | 16,000 file / 8,000 each | 2 | 1 |
| `echo_strand_rail` | H | 18,000 file / 9,000 drawn | 1 | 1 |
| `echo_leyla_1998` | H | 40,000 file / 8,000 drawn | 1 | 1 |

The manifest checks the file tris (5 % slack). For echoes it checks the file budget; the per-pose budget is
reported in `ch3_echoes.md`.

### 13.2 Draw-call rules
- One surface per material per mesh object. Merge all static geometry of a model per material.
- One material per `IA_*` part, except the prism turntables (2).
- Repeats are one mesh: 41 memorial crystals, 5 globes, 12 glyphs, rivets, sockets.
- Code effects stay cheap: 2 fan meshes, 3 arc ribbons, 1 `MultiMesh` for the rising lights, ≤ 6 portal
  quads.
- Hide what a view does not need (§1.4) and turn shadows off as in §1.5.

### 13.3 Per view (target ≤ 150 draw calls, ≤ 120k primitives, shadows included)
Estimates from the caps above (everything in the zone at its cap), with frustum culling and the one shadow
pass. **Measure** them in the Chapter 3 playthrough with
`RenderingServer.get_rendering_info(RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME / ..._PRIMITIVES_IN_FRAME)`, as
`qa/playthrough_ch2.gd` does, and record them in `docs/GAMEPLAY_QA.md`.

| View | Groups | Surfaces in zone | Est. draw calls | Est. primitives |
|---|---|---|---|---|
| `choir` | C, L | ~135 | ~95 + 25 shadow = **~120** | ~70k + 25k |
| `choir_s` | C | ~126 | ~90 + 25 = **~115** | ~65k + 25k |
| `port_b` | C | ~126 | ~85 + 25 = **~110** | ~60k + 25k |
| `gallery` | G, S | ~70 (+ portals) | ~60 + 15 = **~75** | ~45k + 15k |
| `finale` | G, S + 2 echoes | ~72 | ~55 + 15 = **~70** | ~55k + 15k |
| `nursery` | N, L | ~95 | ~75 + 20 = **~95** | ~50k + 20k |
| `camp` | K | ~30 | ~25 | ~20k |

### 13.4 Textures
- Tiling material sets: 1K. 2K only for the Choir floor and walls (`M_Concrete`) if the shared set already
  is.
- Decals: as in §12. Nothing larger than 2048.
- VRAM-compressed (ETC2/ASTC); normal maps only on the tiling sets.
- Each shader quad samples at most one base texture.

## 14. Groups, deliverables and order of work

Every group delivers:
- the scripts `tools/blender/models/<name>.py` and `tools/blender/lib_ch3_<group>.py`;
- the build list `tools/blender/build_lists/ch3_<group>.txt`;
- the GLBs in `game/assets/models/`;
- the QA renders in `qa/blender/ch3/` (§0);
- the measured page `docs/models/ch3_<group>.md`.

| Group | Name | Models |
|---|---|---|
| **A** | shell, lift, doors, shared art | `shell_choir`, `shell_gallery`, `shell_nursery`, `shell_lift`, `array_below`, `freight_lift`, `blast_door`; plus `lib_ch3_symbols.py`, the new material slots, `make_decals_ch3.py`, the decals of §12 and the QA previews |
| **B** | Choir Hall | `transformer`, `choir_rack`, `choir_tube`, `tube_bench`, `strand_office`, `office_desk`, `meter_case` |
| **C** | desk, ports, cabinets | `control_desk`, `switch_cabinet`, `interlock_plate`, `inspection_port` |
| **D** | Nursery | `autoclave`, `autoclave_dead`, `growth_log`, `seed_library`, `growth_chart`, `prism_bench`, `spectral_seal_door` |
| **E** | camp and shutter | `leyla_camp`, `field_recorder`, `oscillograph`, `crystal_shutter` |
| **F** | Gallery console and wall | `gallery_console`, `memorial_wall` |
| **G** | items | the §9 items and `items_ch3.png` |
| **H** | echoes | `echo_operator`, `echo_welder`, `echo_technicians`, `echo_strand_rail`, `echo_leyla_1998` |

**Order of work:**
1. **A first:** `lib_ch3_symbols.py`, the material slots and the decals; G and H can start at the same time.
2. **Then B–F in parallel.** C needs H's operator contact points (§10) only as numbers, which are fixed here.
3. Import neighbouring GLBs (or proxy boxes) in your QA scenes: the ports with the desk, the cabinets with
   the keys, the prisms with the seal, the library with Leyla's touch pose, the memorial with the kneel pose.
4. Run `tools/blender/check_glb_names.py` and `tools/blender/ch3_manifest.py`.
5. Then the room code integrates and runs the tap map and playthrough.

## 15. Notes for the logic and the room code

These are the points where this contract, the design doc and `underground_logic.gd` do not yet line up.
1. **Variants.** `docs/VARIANTS.md` says Chapter 3 has variants from the start, but `UndergroundLogic` has no
   `apply_seed` and no `v_*` keys; every answer is a constant. The scene needs the nine keys of §11. When the
   lever order varies, `PORT_VIEWS` must be derived from `v_startup` and the fixed `PORT_LEVERS`.
2. **Remelt.** The design's open point wants the autoclave door to open by itself after a remelt, but
   `remelt()` leaves `ac_closed` true. Either the logic opens it (`ac_closed = false`, `autoclave_opened`), or
   the player must open it. The scene must not fake a state change.
3. **Lift gates.** They have no state (`gate_open` is only an event). The scene shows the entry gate open
   after the intro, derived from `entry`.
4. **Drum locks.** There is one `drums` state, for `sealed_door()` only. The other door's drum lock is drawn at
   rest and is inert. On the Nursery path the east blast door never opens (the shutter is the way in); on the
   Choir path the west door's drum lock is never used.
5. **Kept echoes "through a port".** `echo_visible(id, true)` needs a view in which each echo can be seen and
   tapped; the three port memory views (§2) provide it.
6. **Finale.** `choose_ending` is a UI choice with no placed-object state. The scene shows the chosen object
   at `choice_mount` from `choice`.
7. **Operator poses.** The design's "5 poses at the desk" cannot be per-lever once the order varies. This page
   uses five generic poses and six desk mounts.
8. **Design text vs logic.** H2's evidence column names W4 and E2 only; the logic (`scope_live`) and the
   dependency graph also need E4 (`shutter_open`).
9. **Kept echoes on the take path.** The design says that on the leave path the kept echoes show only through
   the ports; the logic also allows the ports on the take path. The scene follows the logic.
10. **Space.** The design's hall extents overlap the Gallery drum. This page moves the hall interior faces to
    |x| = 4.5 and adds flat door bays at x = ±3.70.
