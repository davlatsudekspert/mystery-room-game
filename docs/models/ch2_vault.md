# Chapter 2 group D1: the vault (measured results)

Models: `vault_door`, `vault_interior`.
Scripts: `tools/blender/models/vault_door.py`, `tools/blender/models/vault_interior.py`; shared helpers
in `tools/blender/lib_ch2_vault.py`; build list `tools/blender/build_lists/ch2_vault.txt`.
Contract: `docs/models/ch2.md` §0, §1 (vault opening), §2 (views `vault`, `vault_ports`, `vault_inside`),
§6 (`vault_door`, `vault_interior`).

```
blender -b --factory-startup -P tools/blender/models/vault_door.py [-- --no-render] [--shots 1,2,..]
blender -b --factory-startup -P tools/blender/models/vault_interior.py [-- --no-render] [--shots 1,2,..]
```

Both scripts build their geometry directly in Godot axes (see the `lib_ch2_vault` docstring), convert to
Blender axes, export `game/assets/models/<name>.glb` and then read the GLB back: required node names,
parents, model-space positions (1 mm), identity rest rotations, mount rotations, triangle budget, and
`check_glb_names.py` (passes on both). `vault_door.py` also runs a numeric swing check (below). QA renders:
Cycles, 32 samples, 960 × 640, 2 threads, in `room_archive.glb` with the neighbouring GLBs imported.

All coordinates are **Godot, metres**. Angles follow `docs/models/devices.md` (positive = counter-clockwise
looking down the +axis toward the origin).

---

## vault_door.glb (TRIS_DOOR tris, budget 14,000)

**Shape.** A 1.88 m round bank-vault door in a cast-concrete portal. The square frame plate (2.4 × 2.4,
two-tier concrete with a steel angle border) carries a raised, green-grey enamelled steel lining ring
around the Ø 1.90 aperture, eight cast bolt keepers, a heavy external hinge on the left (two hinge
assemblies, brass finials), a brass maker's plate (MERIDIAN · № 2 · 1961, the Institute mark) and the
Institute medallion. The door face: a dark-steel bolt ring with eight chrome locking bolts riding on
chrome rails under chrome guide straps (brass bolt heads, black slots), a chrome edge line, a polished
brass inlay ring, and a green-grey enamel lock panel with the light lock — the frosted glass disc in a
polished brass bezel, two brass lens barrels with black "camera-lens" collars (cream ticks / digits),
glass light pipes in brass channels from each barrel to the bezel, ✦ / ☾ brass plates, and the 6-spoke
brass handwheel. The plug is stepped (r 0.94 / 0.932 / 0.89 / 0.83 from front to back) with bright
machined steps; the back face (seen when open) has a brass-ringed boltwork window (cam + 8 linkage
bars) and a brass time-lock case with three clock dials.

**Placement.** (1.5, 0, −3.5), yaw 0. Origin on the wall face, +Z into the room, door centre (0, 1.35).

**Size.** x −1.2 … 1.2, y 0.15 … 2.55, z −0.316 (time lock, closed) … +0.30 (keeper tops).

### Static: `vault_frame`

| Element | Measured (model space) |
|---|---|
| Frame plate | x ±1.2, y 0.15 … 2.55, z 0 … 0.10 (outer tier 0.07, raised field to 0.10); covers the wall opening x ±1.05, y 0.30 … 2.40 with 0.15 overlap on every side, no gap |
| Lining ring (raised, `M_Steel_Painted`) | r 0.95 … 1.12, top z 0.127 |
| Bore / tunnel sleeve | r 0.95 for z 0 … 0.115 (Ø 1.90 aperture), step to r 0.915 for z −0.12 … 0, step to r 0.86 for z −0.20 … −0.12. Step faces `M_Chrome`. The sleeve ends open at z −0.20 (r 0.86), where `vault_interior`'s tunnel continues |
| Keepers ×8 | at k·45°, radial r 0.956 … 1.08, z 0.127 … 0.30, socket axis z 0.223 (r 0.057, brass bush). The locked bolt ends reach 2.4 cm into them |
| Hinge (static half) | axis x −1.05, z 0.22; per assembly (y_h = 0.85 and 1.85): knuckles y_h ± (0.08 … 0.168) with brass finials, brackets x −1.112 … −0.988, z 0.10 … 0.22 |
| Maker's plate | 0.30 × 0.11 at (0.92, 2.43); medallion Ø 0.176 at (−0.90, 2.40) |

### Parts

| Part | Parent | Pivot (model space) | Axis | Rest → active | Notes |
|---|---|---|---|---|---|
| `IA_vault_door` | — | (−1.05, 1.35, 0.22) = hinge axis | local +Y | 0 → **−95°** (swings into the room, free edge toward −X/+Z) | Ø 1.88, z −0.24 … +0.16 (+ back details to −0.316). Includes the hinge arms, bolt guides, plates, light-pipe channels, boltwork window, time lock |
| `IA_vault_handle` | door | (0, 0.98, 0.16) | local +Z | **−120° per tap** (3 taps = one turn) | 6 spokes, rim r 0.20, ball grips to r 0.26 (Ø 0.52), wheel plane z 0.248 |
| `bolt_0` … `bolt_7` | door | (0.86 cos k45°, 1.35 + 0.86 sin k45°, 0.223) | — | slide **0.08 inward** along −(cos k·45°, sin k·45°, 0) in the door's space | shaft r 0.05, brass head r 0.061, length 0.24 (locked r 0.74 … 0.98, unlocked 0.66 … 0.90) |
| `glass_disc` | door | (0, 1.62, 0.182) | — | — | 48-gon, r 0.222, faces +Z, **UV 0..1 over its bounding square** (u left → right, v bottom → top seen from the room); slot `M_Glass_Frosted` (replaced by the overlay shader) |
| `disc_bezel` | door | (0, 1.62, 0.16) | — | — | polished brass, r 0.2205 … 0.266, top z 0.20, 6 rivets |
| `IA_port_left` / `IA_port_right` | door | (∓0.55, 1.62, 0.16) | — | — | barrel r 0.0775 (flange r 0.088), mouth at z 0.281 (protrudes 0.121), bore r 0.054 down to a smoked lens at z 0.256; cream index stripe on top + index triangle on the lip at 12 o'clock |
| `port_left_mount` / `port_right_mount` | port | (∓0.55, 1.62, 0.268) | identity | — | crystal centre; `lumen_crystal` (7 mm) spans z 0.2645 … 0.2716, `crystal_lens` (16 mm, Ø 0.0696) z 0.260 … 0.276 — both fit (bore r 0.054, lens at 0.256) |
| `light_pipe_left` / `_right` | door | (∓0.367, 1.62, 0.1775) | — | — | glass rod (`M_Crystal`, r 0.0085) only, x ±0.262 … ±0.472, so `set_emission` lights just the rod |
| `IA_collar_left` | door | (−0.55, 1.62, 0.218) | local +Z | **−45° × steps** | r 0.078 … 0.132, z 0.188 … 0.248, knurled black ring; 8 cream ticks on the front face, tick n at 90° + 45°·n (CCW) so step n brings tick n to the top index; ticks 0 and 4 long with a cross bar |
| `IA_collar_right` | door | (0.55, 1.62, 0.205) | local +Z | **−45° × steps** | r 0.078 … 0.135, z 0.188 … 0.222, same ticks at r 0.104 … 0.130 (visible outside the zoom ring) |
| `IA_zoom_right` | door | (0.55, 1.62, 0.239) | local +Z | **−40° × zoom** | r 0.078 … 0.106, z 0.226 … 0.252, digits **0–4** at 90° + 40°·n (CCW), each reading upright at the top |

Mount empties: `port_left_mount`, `port_right_mount` (identity; the item faces +Z).

**Swing check.** Every door profile corner (and the retracted bolt ends) was swept 0 → −95° about the hinge
axis in plan at mid height: minimum clearance to the bore steps and keepers **8.6 mm**. This is why the
plug is stepped/tapered (r 0.94 → 0.83) and the bore steps down (0.95 → 0.915 → 0.86).

**Tap layering.** The ports, collars, zoom ring and handle are separate `IA_*` meshes on top of the door
mesh; from `vault_ports` the collars show as black rings 4–5 cm wide around the brass barrels, the zoom
ring as a 2.8 cm ring in front of the right collar.

### QA renders (`qa/blender/ch2/`)

| File | Shows |
|---|---|
| `vault_door.png` | hero, closed, three-quarter from the room |
| `vault_door_2.png` | in-game `vault` view (closed, locked) |
| `vault_door_3.png` | `vault_ports` view: lumen crystals in both ports with their glyphs, light pipes lit, start pose (left 2, right 5, zoom 0), disc overlay emulated |
| `vault_door_4.png` | `vault_ports` view, solved pose (left 0, right 2, zoom 3): overlay snaps into the engraving, bolts retracted, wheel turned |
| `vault_door_5.png` | bolts retracted (keepers empty) + handwheel, three-quarter |
| `vault_door_6.png` | **open (−95°)** from the `vault` view, `vault_interior.glb` visible through the aperture |
| `vault_door_7.png` | open, three-quarter: stepped plug, back face (boltwork window, time lock), hinge |

---

## vault_interior.glb (TRIS_INT tris, budget 14,000)

**Shape.** Leyla's hidden room. The tunnel continues from the door frame (bore r 0.86, z −3.70 … −3.86,
chrome flange on the vault side) into a 1.8 × 1.34 × 2.5 strongroom: green-grey riveted steel panels,
a dark riveted steel ceiling with two I-beams, a concrete floor with a rubber runner and a brass drain,
and two steel steps from the bore sill (y 0.49) down to the floor. Banks of safe-deposit boxes line both
side walls (dark steel doors with brass label holders, typed labels from the `M_Decal_BoxLabels` atlas and
two key escutcheons; one door on the right bank stands open with its box pulled out). Leyla's field kit
lies on a small steel table: a canvas satchel with leather straps and its shoulder strap hanging over
the table edge, a photograph propped against it, a green enamel thermos, a torch, a folded map with her
route in red, a notebook with a pencil, and a cardboard box on the shelf below. A cream portable 8 mm
projector on a tilt stand aims at the pull-down screen on the back wall. Under the screen, a brass-framed
crimson-velvet key cradle holds both keys, with Strand's mark and Leyla's sign engraved under them.

**Placement.** (0, 0, 0), yaw 0 (room coordinates). Bounds x 0.45 … 2.55, y −0.12 … 2.65,
z −5.35 … −3.70 (the outer shell is 0.15 thick around the interior x 0.6 … 2.4, z −5.2 … −3.86, y 0 … 2.5).

### Parts and empties

| Name | Type | Position (room) | Rotation | Notes |
|---|---|---|---|---|
| `vault_reel_screen` | mesh | (1.5, 1.85, −5.17) | identity | 0.90 × 0.60 quad facing +Z, **UV 0..1** (u left → right, v bottom → top); slot `M_Screen`, the code overrides it with the unshaded reel image |
| `vault_projector` | mesh (static) | origin (0, 0, 0) | identity | body, lens, reels, stand |
| `vault_lamp_glow` | mesh | origin at the lens front | identity | lens glass + four lamp-house vents, slot `M_Glass` (dark until `vault_reel(true)` enables emission; `M_Emissive_Warm` would glow from scene load) |
| `vault_lens_origin` | empty | LENS_POS | local +Z = beam to the screen centre (BEAM_DIR, pitch PITCH) | |
| `key_strand_mount` | empty | (1.32, 1.18, −5.12) | **+90° about X** | maps the item's flat pose (face +Y, bow −Z) to hanging: face +Z, bow up. `key_strand`'s hanging eye lands on the brass hook peg at y 1.249 |
| `key_leyla_mount` | empty | (1.68, 1.18, −5.12) | **+90° about X** | `key_leyla`'s oval bow rests on two brass pins under its shoulders (pin tops y 1.197) |
| `cradle_clamp_left` | mesh | (1.32, 1.2951, −5.1185) | identity | jaw above Strand's key (gap 3.5 cm); lock = slide **−0.03 on local Y** → 5 mm above the key |
| `cradle_clamp_right` | mesh | (1.68, 1.2663, −5.1185) | identity | same above Leyla's key |
| `vault_bulb` | mesh | (1.5, 2.33, −4.45) | identity | bulb glass only, `M_Emissive_Warm` (the code toggles it); cage + canopy are `bulb_fixture` |
| `vault_light` | empty | (1.5, 2.33, −4.45) | identity | bulb centre |

Static meshes: `vault_shell`, `vault_boxes`, `vault_table`, `field_kit`, `key_cradle`, `screen_roller`,
`bulb_fixture`.

### QA renders (`qa/blender/ch2/`)

| File | Shows |
|---|---|
| `vault_interior.png` | in-game `vault_inside` view: keys on the cradle, the reel image on the screen (`vault_reel.jpg`), projector lamp on |
| `vault_interior_2.png` | `vault_mouth` view through the open door |
| `vault_interior_3.png` | cradle close-up after choosing Strand's key... (see list below) |
| `vault_interior_4.png` | the field kit on the table |

---

## Deviations from the contract

DEVIATIONS

## Notes for the game code

NOTES
