# Chapter 4 models — interface contract (The Experiment, the Array Hall)

This page is the **contract** between the Chapter 4 Blender models and the game code (`game/src/rooms/array_hall/`,
room and visuals still to be written). The code finds parts **by exact name** and moves them with the conventions
below, so names, pivots, axes, rest poses and mounts are binding. Puzzle data comes from `docs/CHAPTER4_DESIGN.md` and
`game/src/rooms/array_hall/array_hall_logic.gd` (`ArrayHallLogic`). Where this page and the design doc disagree on a
placement, **this page wins** (it is newer); §13 lists the differences.

The format, the tools and every rule of `docs/models/ch3.md` §0 hold unchanged (G-frame helpers, `IA_*` parts with their
origin at the pivot and identity rest rotation, `*_mount` empties, colliders, materials ≤ 4 per GLB, world-scale UVs,
shader quads with UV 0..1, no words on a model). This page only adds what is new. Each build group writes its measured
results to `docs/models/ch4_<group>.md`.

## 0. Rules that are new or sharper in Chapter 4

**Look.** The Array Hall is the climax, so it is the grandest room of the game: a **1970s Soviet scientific vault** —
monumental brass and steel, board-formed concrete ribs, a green-painted dado, riveted girders, brass inlay, caged work
lamps, a round vault with an oculus. Worn but not ruined; dust on every top face. Light is the protagonist: the Core's
cyan-white glow, warm caged work lamps that wake ring by ring, and one cold shaft of daylight down the oculus once the
vent opens. Read the whole hall on a phone: big shapes, brass edges on everything tappable, numerals as 3D inlay.

**Index rule (names).** Everything the player sees numbered is named by its **player numeral, 1-based**, and the logic
id is that number minus 1 where the logic is 0-based: `IA_switch_1..5` (Panel 0, `toggle_switch(n − 1)`),
`handwheel` instances at `wheel_mount_1..4` (`turn_ring_wheel(n − 1, ±1)`), `ring_1..4`, `tower_mount_1..4`,
`IA_hatch_1..4`, `IA_gate_1..4` (`use_item_on("tower_key_n", "gate_n")` is already 1-based), `IA_leaf_1..6`
(`lift_leaf(n − 1)`), `IA_knob_1..4` (`press_knob(n − 1)`), `IA_collar_digit_1..4` (`turn_collar(n − 1, ±1)`),
`IA_locker_17`. The 20 Panel 0 traces are `trace_<s>_<line>` with s = 1..5 and line ∈ `lock | light | array | vent`
(the order of `v_panel[s*4 + line]`: LOCK 0, LIGHT 1, ARRAY 2, VENT 3).

**Name traps.** No name may end in a Godot import hint (`_col`, `_wheel`, `-rigid`, `_occ`, `_navmesh`, `_vehicle`,
`_noimp`…). Chapter 4 traps: the handwheel part is **`IA_handwheel`** (one word), the chronometer's jog wheel is
**`IA_scrub`**, the post number wheel is **`IA_post_number`**, the Sun's feed wheel is **`IA_feed`**. "collar" is fine.
`tools/blender/check_glb_names.py` runs in every script and in `build_all.sh`.

**Rotation signs** (Godot, as ch3 §0). Positive = counter-clockwise looking down the +axis toward the origin.
- About +X: positive tips +Y toward +Z. A lever lifted away from the operator and a back-hinged lid are **negative**.
- About +Y: a gate hinged on its left edge (seen from outside) opens outward with a **negative** angle.
- About +Z (a knob or wheel seen from the front): clockwise is **negative**.
- **Ring position p (0..7) ↔ azimuth** φ = 180° + 45° p, measured clockwise seen from above from north (−Z); a point at
  radius r is (r sin φ, y, −r cos φ). Mark = p + 1: mark 1 south (under the catwalk), 3 west (toward the Sun), 5 north,
  7 east. A ring turned to position p is rotated **−45° p about +Y** from its rest (the rest = position 0 = mark 1).

**Budgets.** The HUD costs about 60 draw calls, so a view of the hall may draw about **90 scene draw calls, shadows
included** (the project limit is 150 per view). Every surface cap in §11 is a hard cap for the model, and §11.2 sums the
hot views. The same rules as ch3: one surface per material per mesh object, every static part merged, repeats are one
mesh (rivets, ribs, tags), **MultiMesh for the 41 tags, the 42 lamps, the 41 + 1 rising lights and the echo crowd**,
tap-target parts have one material.

**Material slots.** Library slots only, no new `.tres` file: `M_Concrete`, `M_Paint_Green`, `M_Steel_Dark`,
`M_Steel_Painted`, `M_Brass_Aged`, `M_Brass_Polished`, `M_Chequer`, `M_Chrome`, `M_Glass`, `M_Glass_Dark`,
`M_Glass_Frosted`, `M_Bakelite`, `M_Enamel_Cream`, `M_Velvet`, `M_Crystal`, `M_Emissive_Lumen`, `M_Chalk`, `M_Echo`,
`M_Shader_Quad`, plus the Chapter 2 and 3 slots listed in `ch2.md` §0 and `ch3.md` §0. Lamps and jewels use their glass
slot (the code turns emission on).

## 1. Layout (world, Godot coordinates, metres)

### 1.1 Scale and layout sketch

Plan, north (−Z) up. One column = 1 m across, one row = 2 m deep. The wall is r = 14.

```
 x:   -16      -12       -8        -4         0        +4        +8       +12      +16
z-14                         . . . ' ' [ BOOTH y=2 ] ' ' . . .                   F  Strand's booth, stair E
z-12                 . '    ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' '    . .              ring I  r10.5   (mark 5 = N)
z-10             . '                                                  ' .
z -8          . '          ..'''''''  ring II r8.5  '''''''..               ' .
z -6        .'         .'                                    '.             '.
z -4      .'         .'      .''''  ring III r6.5  ''''.       '.             '.
z -2     /   .'     /      /      ___ ring IV r4.5 ___    \       \       '.   \
z  0   (SUN)[iris]  |       |     (      ( CORE )      )     |      |     [WATCH ROOM]|   E  watch room x 11.5..14
z +2     \          \       \       '--- island r3 ---'     /       /          /
z +4      '.         '.      '.             |              .'      .'         .'
z +6        '.         '.     '.            | catwalk     .'      .'         .'        hatches z = 10.5 8.5 6.5 4.5
z +8          ' .        ' ..   ' ..         |       .. '    .. '         . '
z+10             ' .                '''''''  |  '''''''                . '
z+12                ' . .     [ bridge deck y=2.5, rail z=11.95 ]    . . '              bridge x ±5.9, z 11.95..14.8
z+14                   ' ' '  [ pier + PANEL 0 ]  ' ' '                                 undercroft: Panel 0 on z=14.0
z+16          stair W |  <  [ lift cage 0,16.4 ]  >  | stair E                            south bay x ±6, back wall z=18.2
z+18          ___________________ bay back wall ___________________
```

Section through the north-south axis (x = 0), south on the left, not to scale in y:

```
 y=14.6 ........................ Gallery glass floor (shaft r1.5 from y=12)
 y=12.0                            oculus ring + shutter ( ) ( )                 vault apex
 y= 7.0  ─ wall top / brass cornice ┐                                  ┌─ wall top
 y= 5.8                  bay lintel ┘          booth roof y=4.7 ──┐   │
 y= 4.1                                  Core crystal (centre)    │ ┌─┴ booth floor y=2.0
 y= 2.5   [bridge]═══catwalk══════════════[island r3, y=2.5]        │ │
 y= 0.5                  ring tops y=0.5   (tower heads y=2.1)      │ │
 y= 0.0 ───────────────────────────────────────────────────────────┴─┴────
        z=18 bay | z=14 pier | rail z=11.95 | hatches 10.5 8.5 6.5 4.5 | z=3 island | z=0 | booth z=-13
```

Marks and rings (plan, clockwise seen from above, φ from north): mark 1 at φ 180 (south), 2 at 225, 3 at 270 (west, the
Sun), 4 at 315, 5 at 0 (north), 6 at 45, 7 at 90 (east), 8 at 135. Ring I is the outer (r 10.5), IV the inner (r 4.5).

### 1.2 Zones and openings

| Zone | Interior | Notes |
|---|---|---|
| **Hall** | r ≤ 14.0, floor y = 0, wall top y = 7.0, vault apex ring r 1.5 at y = 12.0, shaft to y = 14.6 | `shell_hall`. Array floor r ≤ 11.5, apron 11.5–14 |
| **South bay** | x ∈ [−6, 6], from the circle (z ≈ 12.65 at x = ±6) to the back wall z = 18.2, ceiling y = 6.2 | `shell_lift4`. The lift cage stands in it |
| **Lift** | `freight_lift` (Chapter 3 model, reused) at (0, 0, 16.4), yaw 0 | Cage interior x ∈ ±1.1, z ∈ [15.3, 17.5]; gates open west and east into the bay. Its roof frame (2.6) sits under the bay ceiling (6.2); a dark shaft opening above it is in `shell_lift4` |
| **Bridge** | deck y = 2.5, x ∈ [−5.9, 5.9], z ∈ [11.95, 14.8] | `bridge`. North rail at z = 11.95. Pier wall under it at z = 14.0, x ∈ [−3.2, 3.2], carries Panel 0 |
| **Panel 0** | (0, 0, 14.0), yaw 180, on the pier wall's north face, under the bridge | Design said (0, 0, 13.8): same place |
| **Catwalk** | x ∈ [−0.6, 0.6], z from 11.95 to 3.0, deck y = 2.5 (flush with the bridge) | Hatches over the rails at z = 10.5, 8.5, 6.5, 4.5 |
| **Island / Reliquary** | r ≤ 3.0, platform top y = 2.5 on a drum r 2.7 | Cage r 2.4 (3.0 high), glass tower Ø 2.2 (3.5 high), Core crystal centre (0, 4.1, 0), collar ring at y 3.35–4.05 |
| **Sun apse** | niche in the west wall, half-cylinder r 3.6 about (−13.6, 0, 0), height 4.6 | In `shell_hall`. Lamp centre (−13.0, 1.8, 0), iris at (−11.8, 1.8, 0), pedestal (−12.0, 0, 2.4) |
| **Strand's booth** | north, floor y = 2.0, x ∈ [−3.2, 3.2], z ∈ [−13.9, −11.9], roof y = 4.7 | Stair along the front from the stair gate (0, 0, −11.5) east to the door at x = 3.2 |
| **Watch room** | east, interior x ∈ [11.5, 13.9], z ∈ [−3.5, 3.5], grille at x = 11.5 | `watch_room` is a model of its own (the design had no model for the enclosure) |
| **Oculus** | Ø 3 at y = 12 | Shutter leaves slide apart when VENT goes live |

The beam axis is **y = 1.8** everywhere (Sun axis, iris centre, mirror heads: ring top 0.5 + 1.3). The last fold rises
from tower IV's mirror to the Core crystal centre (0, 4.1, 0).

### 1.3 Placement

Culling groups: **H** hall shell, **B** bridge (bridge, desk, lever, knob, wheels, bay), **P** Panel 0, **K** catwalk,
**R** Array floor (rails, rings, towers, beams), **I** island, **S** Sun apse, **T** booth, **W** watch room,
**E** echoes. A node in two groups is drawn when either is.

| Model (id) | Group | Position | Yaw | Cull | Notes |
|---|---|---|---|---|---|
| `shell_hall` | A | (0, 0, 0) | 0 | H | Room coordinates |
| `shell_lift4` | A | (0, 0, 0) | 0 | B + H | Room coordinates |
| `freight_lift` | A (Ch 3) | (0, 0, 16.4) | 0 | B | `IA_gate_west/east` as in Chapter 3 |
| `bridge` | A | (0, 0, 0) | 0 | B | Room coordinates |
| `catwalk` | A | (0, 0, 0) | 0 | K | Room coordinates |
| `master_desk` | B | (0, 2.5, 13.15) | 0 | B | Front (+Z) faces south: the operator stands south |
| `keeper_knob` | B | desk `keeper_mount` | 0 | B | |
| `master_lever` | B | desk `lever_mount` | 0 | B | |
| `handwheel` ×4 | B | bridge `wheel_mount_1..4` = (−3.6, 2.5, 12.45), (−2.2, …), (2.2, …), (3.6, …) | 0 | B | Front faces south (the player) |
| `panel0` | B | (0, 0, 14.0) | 180 | P | Origin on the wall plane; faces north |
| `ring_rails` | C | (0, 0, 0) | 0 | R | Room coordinates |
| `array_rings` | C | (0, 0, 0) | 0 | R | `ring_1..4` rotate about the hall axis |
| `mirror_tower` ×4 | C | at `tower_mount_1..4` | 0 | R | Front (+Z) = radially outward at rest |
| `beam_segment` ×≤ 5 | C | code | — | R | |
| `cage`, `glass_tower`, `core_crystal`, `cradle`, `heart_drawer` | D | (0, 2.5, 0) | 0 | I | Island frame; built in place |
| `sun_lamp` | E | (−13.0, 1.8, 0) | 0 | S | Lamp centre |
| `sun_iris` | E | (−11.8, 1.8, 0) | 90 | S | Front faces +X, into the hall |
| `sun_pedestal` | E | (−12.0, 0, 2.4) | 90 | S | Front faces +X |
| `booth` | F | (0, 0, −13.0) | 0 | T | Front faces south (the hall) |
| `booth_desk` | F | (0, 2.0, −13.4) | 0 | T | Desk back to the north wall |
| `strand_box4` | F | `booth_desk` `box_mount` | 0 | T | |
| `orrery` | F | `strand_box4` `orrery_mount` | 0 | T | |
| `watch_room` | G | (12.7, 0, 0) | −90 | W | Front faces −X (west, into the hall) |
| `roll_board` | G | `watch_room` `board_mount` | 0 | W | |
| `lockers` | G | `watch_room` `lockers_mount` | 0 | W | |
| `post_station4` | G | `watch_room` `post_mount` | 0 | W | |
| items | H | at their mounts | — | — | |
| echoes | I | at their mounts (§9) | — | zone of the mount | |

### 1.4 Fixed points

| Point | World | Owner |
|---|---|---|
| Ring I..IV radii | 10.5, 8.5, 6.5, 4.5; ring top y = 0.5 | `ring_rails`, `array_rings` |
| Tower I..IV at mark 1 | (0, 0.5, 10.5), (0, 0.5, 8.5), (0, 0.5, 6.5), (0, 0.5, 4.5) | `tower_mount_n` |
| Hatch n | (0, 2.5, 10.5 / 8.5 / 6.5 / 4.5), opening 0.9 × 0.9 | `catwalk` |
| Handwheel n axis | (−3.6 / −2.2 / 2.2 / 3.6, 3.8, 12.65), axis +Z | `handwheel` |
| Chronometer dial centre | desk-local (0, 1.2595, 0.0673) on the slope (world y 3.76, z 13.22) | `master_desk` |
| Core crystal centre | (0, 4.1, 0) | `core_crystal` `core_center` |
| Collar digits | (±0.30 / ±0.10, 3.70, 1.22) | `glass_tower` |
| Lens socket (cradle) | (0, 3.82, 0.62) | `cradle` `lens_mount` |
| Heart drawer face | (0, 3.18, 0.70) | `heart_drawer` |
| Sun lamp / iris / beam axis | (−13.0, 1.8, 0) / (−11.8, 1.8, 0) / y = 1.8 | `sun_lamp`, `sun_iris` |
| Booth gate | (0, 0, −11.5) | `booth` |
| Watch grille | (11.5, 0, 0) | `watch_room` |
| Locker 17 | `lockers`-local, see §8 | `lockers` |

### 1.5 Lights

At most **one shadowed light per zone**, a `SpotLight3D` only (as ch3 §1.5). Hidden groups' lights are off.

| Light | Type | Position → aim | Shadow |
|---|---|---|---|
| `shaft` (after VENT) | Spot 14°, range 16, cold `moon_cold` | (0, 12.2, 0) → (0, 0, 0) | **yes** (hall, one) |
| `core_glow` | Omni, range 9, `lumen` | (0, 4.1, 0) | no |
| `work_1..4` | Omni, range 7, warm, wake ring by ring | (0, 5.5, r_n) at mark 5, r = 10.5, 8.5, 6.5, 4.5 | no |
| `bridge_lamp` | Spot 60°, range 7, warm | (0, 5.9, 13.5) → (0, 3.5, 13.1) | no |
| `panel_lamp` | Omni, range 3, warm | (0, 2.0, 12.6) | no |
| `sun_arc` | Omni, range 12, white | (−12.4, 1.8, 0) | no |
| `booth_lamp`, `watch_lamp` | Omni, range 4 | inside | no |

## 2. Camera views (proposals; render QA from these)

Root views (free look) are marked R. Draw = culling groups (§1.3). FOV is vertical; the game is landscape 16:9.

| View | Camera | Looks at | FOV | Draw |
|---|---|---|---|---|
| `lift` (R, intro) | (1.55, 1.6, 16.5), just outside the cage's east gate | (5.0, 2.2, 12.5) | 64 | H, B, R (dark) |
| `bay_hero` | (0, 1.7, 7.5) | (0, 2.6, 15.5) | 60 | H, B |
| `lift_chalk` | (−2.9, 1.55, 15.4) | (−3.0, 1.5, 18.18) | 46 | B |
| `bridge` (R) | (0, 4.4, 14.6) | (0, 3.4, 0) | 66 | H, B, K, R, I, E |
| `desk` | (0, 4.35, 14.5) | (0, 3.5, 13.1) | 58 | B |
| `chronometer` | (0, 4.5, 14.3) | (0, 3.75, 13.2) | 40 | B |
| `handwheels` | (0, 4.9, 15.2), in the bay behind the bridge | (0, 3.3, 9.0) | 84 | B, K, R |
| `panel0` | (0, 1.2, 12.3), under the bridge | (0, 1.15, 14.0) | 62 | P, B |
| `catwalk` (R) | (0, 3.9, 11.6) | (0, 3.0, 3.0) | 64 | K, R, I |
| `hatch_1`..`hatch_4` | (0, 3.35, z_n + 0.55) | (0, 0.65, z_n − 0.05) | 50 | K, R |
| `island` (R) | (0, 3.8, 5.6) | (0, 3.2, 0) | 64 | I, K |
| `gate_1`..`gate_4` | outside gate n, 1.8 m, eye 3.9 | the lock face | 46 | I |
| `collar` | (0, 3.8, 2.6) | (0, 3.7, 1.22) | 40 | I |
| `core` | (0, 3.6, 2.3) | (0, 3.5, 0.3) | 52 | I |
| `apse` (R) | (−5.5, 1.7, 0.3) | (−12.5, 1.8, 0) | 62 | S, R |
| `sun_pedestal` | (−10.2, 1.5, 2.8) | (−12.0, 1.1, 2.4) | 46 | S |
| `iris` | (−8.8, 1.8, 0) | (−11.8, 1.8, 0) | 40 | S |
| `booth` (R) | (0, 1.7, −6.5) | (0, 3.2, −13) | 62 | T, H |
| `gear_box` | (0, 3.7, −11.9) | (0, 3.0, −13) | 44 | T |
| `watch` (R) | (6.5, 1.7, 0) | (12.7, 1.5, 0) | 64 | W |
| `locker_17` | (9.8, 1.6, 2.0) | locker 17 | 40 | W |
| `post_station` | (9.8, 1.5, -1.5) | the post station | 44 | W |

## 3. Group A — shell, circulation, shared art

### shell_hall.glb (≤ 16k tris, ≤ 9 surfaces)
Materials: `M_Concrete`, `M_Paint_Green`, `M_Steel_Dark`, `M_Brass_Aged`. Built in world coordinates.

**Mesh objects:** `hall_floor` (concrete disc r 14), `hall_walls` (concrete, with pilasters, recessed upper panels),
`hall_dado` (green panels 0–3.2), `hall_vault` (the dome with ribs), `hall_trim` (steel: oculus ring, rib caps, girder
bands), `hall_brass` (cornice bands, the floor inlay, the numerals), `oculus_shutter_a`, `oculus_shutter_b`.

- **Walls:** r 14.0 inner face, up to y = 7.0, concrete pilasters 0.5 wide at φ = 7.5° + 15° k (24 positions, the 6 inside an
  opening are skipped, so 18 stand); green dado panels between them; brass bands at y 3.2 and 3.3; a brass cornice at y 6.8–7.0.
  Openings: the **south bay** φ ∈ [154.6°, 205.4°] (x ∈ [−6, 6]) up to y = 6.2 with a lintel above (the bay's reveal is
  `shell_lift4`'s) and the **west apse** niche (§1.2: half-cylinder r 3.6 about (−13.6, 0, 0), height 4.6, half-dome cap).
- **Vault:** from (r 14, y 7.0) rising to (r 1.5, y 12.0) in a shallow dome, 24 radial ribs and 4 concentric ring ribs,
  the underside concrete; each radial rib sits at a pilaster's azimuth (7.5° + 15° k) and carries a thin brass cap. The shaft above the oculus ring: a concrete tube r 1.5 from y 12.0 to 14.6.
- **Oculus:** a thick steel ring r 1.5–1.95 at y 11.9–12.1. **`oculus_shutter_a`/`_b`**: two half-discs r 1.6 at
  y = 11.85 with brass edge strips; origin at the hall axis (0, 11.85, 0). Closed = identity. **Open = a slides −1.7 m,
  b slides +1.7 m along X** (a is the west half, b the east half).
- **Floor inlay** (`hall_brass`): eight radial lines (width 0.07, from r 3.4 to 11.4) at the mark azimuths, brass
  rings r 3.3 and r 11.5 (0.07 wide), and the numerals **1–8** (3D, 0.55 high, from `shared_numerals`) at r = 12.4 on the
  apron, standing upright **radially (top outward)**. Concrete tooling lines on the apron.
- No lights, no collision, no gameplay parts. Empties: `portal_bay` (0, 3.0, 13.2, +Z toward the bay), `portal_apse`
  (−13.6, 2.0, 0, +Z toward −X).

### shell_lift4.glb (≤ 5k, ≤ 5)
Materials: `M_Concrete`, `M_Steel_Dark`, `M_Brass_Aged`, `M_Chalk`. Built in world coordinates.

**Mesh objects:** `bay_floor` (concrete, x ∈ [−6, 6], z from the circle to 18.2), `bay_walls` (the two side walls x = ±6,
the back wall z = 18.2, the ceiling at y 6.2 with a shaft opening x ∈ [−1.3, 1.3], z ∈ [15.1, 17.7], and a short dark
shaft above it), `bay_frame` (steel: the portal arch at the mouth, two ceiling beams, wall brackets, lamp cages; brass
rivets and a brass level plate in 3D), `leyla_chalk`.

- **`leyla_chalk`** (`M_Chalk`, flat strokes 2 mm proud): Leyla's sign — a crescent opening right and three dots — and the
  digits **1998**, 1.1 m wide in all, on the back wall at (−3.0, 1.5, 18.18) facing −Z. No words.
- Empties: `echo_mount_leyla_lift` at (−3.4, 0, 17.0), **yaw 0** (the figure faces +Z, toward the chalk on the back wall);
  `lift_light` at (0, 5.8, 16.4).
- The cage's gates face the bay sides; keep x ∈ [−4.7, 4.7], z ∈ [15.1, 17.8] clear of geometry except the cage.

### bridge.glb (≤ 10k, ≤ 7)
Materials: `M_Steel_Dark`, `M_Chequer`, `M_Brass_Aged`, `M_Steel_Painted`. Built in world coordinates.

**Mesh objects:** `bridge_deck` (chequer plate, no alpha, y = 2.5, x ∈ [−5.9, 5.9], z ∈ [11.95, 14.8]), `bridge_frame`
(girders under the deck, four columns at (±5.6, 0, 12.3) and (±5.6, 0, 14.5), the pier wall z 14.0–14.4 x ∈ [−3.2, 3.2],
the two stair flights, balustrade posts), `bridge_rail` (brass: north rail y = 3.55 with the wheel mount plates, side
rails, the stair handrails), `bridge_paint` (green painted pier wall face and stair stringers), `catwalk_gate`.

- **Stairs:** two straight flights along the bay side walls, x ∈ [4.9, 5.9] and [−5.9, −4.9], 14 steps of 0.179 × 0.243
  from the bay floor at z = 18.0 up to the deck's rear edge at z = 14.8.
- **North rail:** top y = 3.55, from x = −5.9 to 5.9 at z = 11.95 with a **gate opening x ∈ [−0.55, 0.55]**; four brass
  wheel plates under the wheels at x = −3.6, −2.2, 2.2, 3.6.
- **`catwalk_gate`** (own object, one material, `M_Brass_Aged`; the posts are in `bridge_rail`): a 1.1 wide, 1.1 high
  lattice gate leaf hinged on its west post; origin at the hinge
  (−0.55, 2.5, 11.95); closed = identity; **open = +95° about +Y** (swings north onto the catwalk). A brass lock lamp
  jewel on the leaf is part of the mesh. The code opens it at `solved:power`.
- Empties: `wheel_mount_1..4` at (−3.6 / −2.2 / 2.2 / 3.6, 2.5, 12.45), identity; `desk_mount` (0, 2.5, 13.15);
  `echo_mount_wheels_1` (−2.9, 2.5, 13.3) and `echo_mount_wheels_2` (2.9, 2.5, 13.3), **yaw 180** (the technicians face
  north to the wheels); `bridge_light` (0, 5.9, 13.5). The wheel plates at `wheel_mount_n` carry the Roman numerals
  **I..IV** (3D relief, 0.10 high, on the rail side of the mount).

### catwalk.glb (≤ 8k, ≤ 7)
Materials: `M_Chequer`, `M_Steel_Dark`, `M_Brass_Aged`. Built in world coordinates.

**Mesh objects:** `catwalk_deck` (chequer, x ∈ [−0.6, 0.6], z ∈ [3.0, 11.95], y = 2.5, with four square holes 0.9 × 0.9
centred at z = 10.5, 8.5, 6.5, 4.5), `catwalk_frame` (two longitudinal girders, cross-ties, trestles on feet at
z = 9.5, 7.5, 5.5, 11.0 — **in the gaps between the ring tracks**, never on a ring), `catwalk_rail` (brass: handrails
y 3.5 both sides, posts every 1.5 m, the end rail at the bridge gate), **`IA_hatch_1..4`**.

- **`IA_hatch_n`**: a chequer lid 0.98 × 0.98 × 0.03 with a pull-ring groove (a single material, `M_Chequer`). Origin at the **north hinge edge** (0, 2.5, z_n − 0.49);
  closed = identity (flat, over the opening); **open = −105° about +X** (back-hinged, the lid stands up toward the
  north). A tap on a closed lid with the ring out of reach gives `take("tower_n")` → `tower_out_of_reach`; with the ring at
  mark 1 the code opens the lid and the key becomes tappable.
- End of the catwalk at z = 3.0 meets the island platform (flush).

### shared_numerals.glb + lib_ch4_numerals.py (≤ 3k, a kit, not placed)
`tools/blender/lib_ch4_numerals.py` holds the 2D outlines of the Roman numerals **I II III IV V** (a blocky, bold,
serifed Soviet face: stroke 0.14 of the height) and the digits **0–9**, used by every Chapter 4 model so a numeral looks
the same everywhere (`numeral_loops(n, h)`, `numeral_inlay(...)`, `digit_inlay(...)`). The GLB is a kit/QA sheet:
`num_I..num_V` and `dig_0..dig_9`, one material (`M_Brass_Aged`), 1 m origin per object at the centre of the glyph, 0.25 high,
facing +Z. It is **not drawn** in the game (the numerals are baked as 3D relief in the models that need them).

## 4. Group B — the bridge desk

### master_desk.glb (≤ 12k, ≤ 8)
Materials: `M_Steel_Painted`, `M_Brass_Aged`, `M_Bakelite`, `M_Shader_Quad`. At (0, 2.5, 13.15), yaw 0. Origin = deck level,
centre of the footprint. Body x ∈ [−1.55, 1.55], z ∈ [−0.45, 0.46]; the operator stands at +Z. The wings (x ∈ [−1.55, −0.80]
and [1.00, 1.55]) are flat at y = 0.95. The console block between them has a **sloped panel** from the front edge (z 0.46,
y 0.95) up to (z −0.20, y 1.47) (38.2° from horizontal; up-normal **n = (0, 0.7855, 0.6189)**, up-slope direction
(0, 0.6189, −0.7855)) and a flat back shelf at y 1.47. A slope point is P(s, x) = (x, 0.95 + 0.6189 s, 0.46 − 0.7855 s),
s ∈ [0, 0.84]. The whole desk stays ≤ 1.65 high (the chart drum is the top) so the hall stays visible over it from the `bridge`
camera.

**Static** (`master_desk`, 3 surfaces): green-grey painted cabinet with raised panels and rivets, brass nosing and kick strip,
the dial (Ø 0.57 bezel, black bakelite face, brass tick marks, numerals and legend), the escapement bay's frame and recess,
the strip chart's frame with the minute numerals 0–7 and the paper roll drum on the back shelf (static), the jog wheel's brackets.

**Dial.** Centre P(0.5, 0) = (0, 1.2595, 0.0673); brass legend **03:1** in the lower middle, eight station numerals **0..7** (the last
digit of 03:10..03:17) at r 0.185, spaced 40° on a 280° arc, station p at **clockwise angle −140° + 40° p from 12 o'clock**, with
major and minor ticks.

**Parts:**
- **`chrono_hand`** (own object, brass): the hand and its hub, **origin = the dial centre lifted 0.016 along n** (0, 1.2675, 0.0543),
  built lying in the slope with its tip at 12 o'clock (up the slope). Its node rotation is identity at rest; the code turns it **about
  n = (0, 0.7855, 0.6189) in the desk frame**. Position p (0..7) = **(140° − 40° p)**, counter-clockwise seen from the front of the dial
  (p = 0 points lower left, p = 7 lower right).
- **`IA_scrub`**: knurled brass jog wheel r 0.12 × 0.10 wide on two bracket cheeks at the slope's lower lip, **origin (0, 1.07, 0.49), axis
  +X**. Position p = **−45° p about +X** (8 click stops, forward only; the code refuses backward). Tap or drag → `scrub()`.
- **`IA_chronometer`**: the escapement bay (a brass movement plate with an escape wheel, a train of gears, a bridge and an **empty pawl
  seat**: a ring boss with a spring post), 0.27 × 0.19 on the slope at **P(0.30, −0.62) = (−0.62, 1.1357, 0.2243)** (origin there).
  Used on it: `use_item_on("reverse_pawl", "chronometer")`.
  - **`pawl_mount`** (empty) on the seat at (−0.545, 1.142, 0.242), rotated **+38.2° about +X** (the slope normal): the `reverse_pawl`
    item lies flat on the seat there.
  - **`chrono_plate`**: the bay's hinged brass cover with a pull knob, **baked open** (−100° from flat, standing up from the bay's upper
    edge; identity at rest); **origin = the hinge (−0.62, 1.1976, 0.1458)**; the code **closes it at `pawl_fitted` = +100° about +X**.
- **`chart_paper`**: the strip chart's paper, 0.40 × 0.46 at P(0.475, 0.66) = (0.66, 1.244, 0.087) + 0.003 n, `M_Shader_Quad`, UV 0..1
  (u across the width = the minutes 0..7, left → right, 0.05 each; v up the slope = time). The shader draws the pen marks of `v_night`
  and the trace so the chart is readable without the replay. (The design's moving drum and pen are static meshes here: the pen mark is
  drawn by the shader.)
- **`echo_mount_strand`** (empty, floor) at local (1.12, 0, 0.78), **yaw 180** (his right hand meets the lever grip).
- Empties: **`keeper_mount`** at (−1.12, 0.95, 0.0) and **`lever_mount`** at (1.28, 0.95, 0.0), identity; `desk_light` (0, 1.9, 0.5).

**Logic:** `IA_scrub` → `scrub()`; `IA_chronometer` accepts `reverse_pawl`.

### master_lever.glb (≤ 3k, ≤ 2)
Materials: `M_Steel_Painted`, `M_Brass_Aged`. At the desk `lever_mount` (1.28, 2.5 + 0.95, 13.15). Origin = the unit's base
centre on the wing pad. A base plate 0.40 × 0.55 with two cheek plates carrying the quadrant arc and two engraved stops, a
large brass knife-switch lever with a ball grip. The lever pivots at **(0, 0.24, −0.12)** (local), length 0.55.
- **`IA_master_lever`**: brass lever with a ball grip.
  **Rest = down: the lever points toward the operator along +Z**, 6° below horizontal baked into the mesh (the node
  rotation is identity); **lifted = −80° about +X** (the grip goes up and away). The code slams it down on `snap_back`.
- Tap/drag up → `lift_master()`.

### keeper_knob.glb (≤ 4.5k, ≤ 4)
Materials: `M_Steel_Painted`, `M_Brass_Aged`, `M_Shader_Quad`. At the desk `keeper_mount` (−1.12, 2.5 + 0.95, 13.15). Origin = the box's base
centre on the wing pad. A bench-instrument box 0.62 w × 0.50 d × 0.25 high with a raised numbered collar plate on its front face and,
above it, a panel leaning back 25° with the **oscillograph** (no lamp: `keeper_on` shows as a flat beat).
- **`osc_screen`**: round CRT face r 0.12 on the leaning panel (centre (0, 0.404, −0.06) + 0.0165 along the panel normal), UV 0..1 over its
  bounding square, `M_Shader_Quad`; a brass bezel is static. The shader draws the beat envelope from the beat |p − k| (§10).
- **`IA_keeper`**: knurled brass knob r 0.07 × 0.058 with a pointer ridge, **origin (0, 0.125, 0.256)** on the collar plate, axis local +Z.
  Pointer at 12 o'clock at identity. **Position p (0..12) = (135° − 22.5° p) about local +Z** (p = 0 lower left, 12 lower right, clockwise).
  Thirteen brass ticks (every third long) with the numerals 0, 3, 6, 9, 12 are engraved on the plate (static).
- Tap/drag → `turn_keeper(±1)`.

### handwheel.glb (×4; ≤ 3.5k, ≤ 2)
Materials: `M_Steel_Painted`, `M_Brass_Aged`. At `wheel_mount_n`. Origin = deck level at the footprint centre, front
(+Z) toward the player. A steel pedestal post (base plate with bolts, a tapered column) carrying a fixed **dial plate** (0.62
Ø, eight click-stop notches and numerals **1–8**, a fixed pointer notch at 12 o'clock) and the brass wheel in front of it.
- Wheel axis at **(0, 1.30, 0.20)** (world y 3.8 at the deck), axis +Z.
- **`IA_handwheel`**: brass rim Ø 0.52 (tube 0.035), six spokes, a hub boss with a numeral-free centre cap, and one
  turned handle pin on the rim so the turning shows. Origin at the axis, identity = handle at 12 o'clock.
  **Turned by k stops = −45° k about local +Z** (a positive delta turns it clockwise seen from the player). The wheel
  shows its **own** turn count, not its ring's position (wheel *i* also moves ring *i* + 1).
- Tap or drag → `turn_ring_wheel(n − 1, ±1)`. The base mesh carries no numeral (one GLB serves four positions); the
  numerals I–IV are on the bridge's wheel plates (`bridge.glb`).

### panel0.glb (≤ 10k, ≤ 40 surfaces; ≤ 20 drawn)
Materials: `M_Steel_Painted`, `M_Brass_Aged`, `M_Glass_Dark`, `M_Chalk`. At (0, 0, 14.0), yaw 180. Origin = floor level at
the centre of the back face, on the pier wall plane. A free-standing hall switchboard, 1.9 w × 1.9 h × 0.22 d (local
z ∈ [0, 0.22], front at z = 0.22), on a plinth; a raised bevelled bezel; a brass nameplate row.

**Layout (local x, y on the front face; the board spans x ∈ [−0.95, 0.95], y ∈ [0.2, 2.1]):**
- four **line lamps** in a row at y = 1.86, x = −0.30, 0.0, 0.30, 0.60 (LOCK, LIGHT, ARRAY, VENT) with 3D pictograms on small
  plaques at y = 1.70 below each: a padlock, a sun, concentric rings, a fan of chevrons;
- **Strand's plate** across the top (brass, 0.90 × 0.12 at (0.15, 2.00)): four filled discs Ø 0.07, one over each lamp;
- four vertical brass **buses**, one per line, at the lamp x, from y = 1.60 down to 0.40 (static inlay, 8 mm wide, 1.5 mm proud);
- five **switch rows**: the switch toggles in a column at x = −0.74, y_s = 1.42, 1.18, 0.94, 0.70, 0.46 (s = 1..5, top to bottom),
  Roman numerals I..V at x = −0.85, and a horizontal brass wire from x = −0.66 to 0.72 at each y_s;
- a **junction dot** where switch row s crosses line bus l if the switch feeds that line (the 20 `trace_*` objects);
- **`leyla_chalk`**: her crescent-and-three-dots sign, four tally strokes and the digits 1998 in `M_Chalk` flat strokes on the
  bezel's lower left, about 0.5 wide (x ∈ [−0.89, −0.40], y ∈ [0.22, 0.36]);
- **`IA_main_lever`** at the right edge, a big brass lever (stem 0.40) in a slotted quadrant, pivot (0.84, 0.60).

**Parts:**
- **`IA_switch_1..5`**: brass bat-handle toggles (stem 0.06, round tip), origin at the pivot on the panel face (−0.74, y_s,
  0.22); neutral = pointing straight out +Z at identity. **Up (on) = −40° about +X, down (off) = +40°.** The code sets +40° at
  the start (all off).
- **`IA_main_lever`**: origin at its pivot (0.84, 0.60, 0.24); rest = upright (+Y) and **pulled = +60° about +X** (toward the
  player); stays pulled once power is on.
- **`lamp_lock`**, **`lamp_light`**, **`lamp_array`**, **`lamp_vent`**: jewels Ø 0.07 (`M_Glass_Dark`, code emission) at
  (−0.30 / 0.0 / 0.30 / 0.60, 1.86, 0.22).
- **`trace_<s>_<line>`**: 20 objects, each a brass junction dot Ø 0.05 raised 3 mm with a tiny ring, at (x_line, y_s, 0.22);
  the code shows the dot when `v_panel[(s − 1) * 4 + line]` = 1. One material.
- Empties (panel-local): `echo_mount_tech_panel` at (0.8, 0, 1.0), **yaw 180** (in world the technician stands north of the
  panel and faces south, toward it); `panel_light` (0, 2.4, 0.6).

**Logic:** switches → `toggle_switch(n − 1)` (refused after `power`); main lever → `pull_main()`; lamps show `lines()`.

## 5. Group C — the Array (contract only)

### ring_rails.glb (≤ 6k, ≤ 2)
`M_Steel_Dark`, `M_Brass_Aged`. Built in place. Four circular steel tracks, track band r ± 0.45, y 0–0.12, on concrete sleepers every
11.25° with rail clips; a thin brass guide groove at each radius; a hand-painted Roman numeral I–IV (3D) at mark 1 beside
each track. The catwalk trestles stand in the gaps between the tracks.

### array_rings.glb (≤ 14k, ≤ 4)
`M_Steel_Dark`. Origin (0, 0, 0). Four rotating nodes **`ring_1..4`** (radii 10.5, 8.5, 6.5, 4.5), origin at the hall axis
(0, 0, 0), identity at position 0. Each is a geared rim beam 0.8 wide, y 0.12–0.50, with a toothed outer edge (rack teeth, pitch
about 0.7 m), eight deep **index notches** (at the position azimuths, φ = 180° + 45° k) and a riveted skin.
**Position p = −45° p about +Y.** Child empties **`tower_mount_1..4`** at (0, 0.5, r_n), identity (the code parents the
`mirror_tower` instance there). Rings are code-moved only (no `IA_`).

### mirror_tower.glb (×4; ≤ 4k, ≤ 3)
`M_Brass_Aged`, `M_Chrome`. Origin = the plinth base centre on the ring top. Front (+Z) radially outward at rest. A 0.7 plinth with a
shelf, a Ø 0.12 post to y = 1.3 (so the mirror head is at 1.8 world), the 45° mirror in a brass yoke; a numeral plate with
**four numeral variants `tower_numeral_1..4`** (own objects; the code shows one); a key bracket shelf on the south side of the plinth top.
- **`tower_head`**: the mirror yoke + 45° chrome mirror, pivot at the post top (0, 1.3, 0); the code yaws it about +Y so the
  beam turns toward the next tower.
- **`IA_key`**: the brass key lying in the bracket at (0, 0.19, 0.24); the code hides it once taken; the tap is `take("tower_n")`.
- Empties: `key_mount` is not needed (the key is baked), `beam_point` at the mirror centre (0, 1.3, 0).

### beam_segment.glb (≤ 100, 1)
`M_Emissive_Lumen`. A unit ribbon along +Z (0 to 1), two crossed quads 0.22 wide. The code scales/rotates ≤ 5 instances.

## 6. Group D — the Reliquary (contract only)

All in the island frame, origin (0, 2.5, 0), built in place.

- **`cage.glb`** (≤ 12k, ≤ 6; `M_Brass_Aged`, `M_Steel_Dark`): round brass lattice r 2.4, 3.0 high, base ring, crown ring;
  **`IA_gate_1..4`** at S (facing the catwalk), W, N, E (clockwise from south); each a lattice leaf with a brass lock face
  carrying the gate's numeral (3D) and a keyhole; origin at the hinge; **open = −95° about +Y** (outward); child empty
  **`gate_key_mount_n`** at the keyhole (the key stays there). Gate 1 is on the catwalk side.
- **`glass_tower.glb`** (≤ 9k, ≤ 7; `M_Glass`, `M_Steel_Dark`, `M_Brass_Aged`): **`tower_glass`** (Ø 2.2, 3.5 high, eight panels with
  steel mullions, a cap) — origin at its base (0, 0, 0), **sinks by sliding −3.6 along Y**; a static base ring and four
  posts; the brass **collar ring** r 1.13–1.35 at y 0.85–1.55 on four posts (the glass slides inside it); **`IA_collar_digit_1..4`**:
  four brass digit wheels 0.20 Ø × 0.12 at x = −0.30, −0.10, +0.10, +0.30, y = 1.20, z = 1.22 on the ring's south face, axis local
  X, digits 0–9 around the rim in 3D; origin at the axis; **digit d = −36° d about +X** (the front digit reads upright).
- **`core_crystal.glb`** (≤ 3k, ≤ 3; `M_Crystal`/`M_Emissive_Lumen`, `M_Brass_Aged`): a pedestal r 0.55, 1.1 high and the hexagonal
  crystal 1.2 high, pointed ends, centre (0, 1.6, 0) island-local (= world (0, 4.1, 0)); empty **`core_center`**; the 41 + 1
  lights are a code `MultiMesh` orbiting r 0.75 (three inclined bands), light sprite size 0.07.
- **`cradle.glb`** (≤ 3k, ≤ 4; `M_Brass_Aged`, `M_Steel_Dark`): a console arm on the pedestal's south face; **`IA_cradle`**: the lens
  socket ring (inner Ø 0.15) at (0, 1.32, 0.62); **`lens_mount`** (the `crystal_lens` lies in it: the empty's frame includes
  the tilt toward the crystal); **`cradle_ring`** (code glow); **`mark_mount`** on the drawer face below.
- **`heart_drawer.glb`** (≤ 4k, ≤ 7; `M_Brass_Aged`, `M_Glass_Frosted`, `M_Velvet`, `M_Steel_Dark`): a brass drawer unit under the cradle;
  **`IA_heart_drawer`** the drawer front with the frosted **`drawer_face`** (the mark falls here); slides **+0.55 along +Z** to open;
  inside three velvet pads **`IA_heart_watch`**, **`IA_heart_letter`**, **`IA_heart_pawl`** with item mounts `watch_mount`,
  `letter_mount`, `pawl_item_mount`.

## 7. Group E — the Sun apse (contract only)

- **`sun_lamp.glb`** (≤ 12k, ≤ 8; `M_Brass_Aged`, `M_Steel_Dark`, `M_Glass`, `M_Emissive_Lumen`): Ø 2.4 riveted brass sphere on a
  steel cradle (origin = the sphere centre), cooling fins, a 1.5 Ø glass port facing +X with two **carbon rods** `rod_a`,
  `rod_b` (own objects, brass-capped, Ø 0.10) on a common axis; `rod_b` slides toward `rod_a` as the gap closes:
  `rod_b`'s origin is its tip at the touching position, so **gap g (0..9) = `rod_b` slid `0.07 g` along +X** (g = 0 shorted, 9 the start); **`arc_glow`** (emissive disc between the rods, code
  intensity); empty `sun_light`.
- **`sun_iris.glb`** (≤ 5k, ≤ 7; `M_Brass_Aged`, `M_Steel_Dark`): a steel frame Ø 2.4 and six brass wedge leaves **`IA_leaf_1..6`**
  (60° plus 14° overlap each side), leaf k centred at clockwise **60° (k − 1)** from up. The leaf **slides radially outward by 0.95**
  to open (direction (sin, cos) of its angle in the XY plane of the iris frame) and latches. The **stack offset** along local +Z:
  `z = 0.012 × (5 − rank)` (rank 0 = top of the stack); the GLB ships with the canonical stack baked ([3, 6, 1, 5, 2, 4], top → bottom);
  the code overrides each leaf's `position.z` from `v_iris`.
- **`sun_pedestal.glb`** (≤ 6k, ≤ 7; `M_Steel_Painted`, `M_Brass_Aged`, `M_Bakelite`, `M_Enamel_Cream`): a waist-high pedestal with a
  slanted top; **`IA_feed`**: a brass hand wheel Ø 0.34, axis local +Z on the front, feed count w = 9 − g, **−27° w about +Z** (clockwise =
  feeding in; the start, g = 9, is the identity); the **ammeter** Ø 0.26 with a cream dial, ticks 0–10: **`ammeter_needle`** (pivot at the dial centre, identity = pointing 55° left of up, the cold stop;
  value n = **−11° n about +Z**, so 10 points 55° right of up) and **`ammeter_band`** (a green arc segment on the dial, pivot at the dial centre; the
  code rotates it to value 10 − g_target); **`IA_sun_lever`**: a bakelite-grip lever, rest OFF = upright (+Y), **ON = +50° about +X**.

## 8. Groups F and G — the booth and the watch room (contract only)

- **`booth.glb`** (≤ 10k, ≤ 9; `M_Steel_Dark`, `M_Glass`, `M_Chequer`, `M_Brass_Aged`): raised glass booth (floor y 2.0, x ∈ [−3.2, 3.2], z ∈
  [−13.9, −11.9], roof 4.7) on steel legs; glass on the front and sides; the stopped wall clock (**03:17**, hands baked, a mesh in
  the brass slot, not interactive); the stair along the front from `booth_gate` east to a door at x = 3.2. **`IA_booth_gate`**: a lattice
  gate at the stair foot (0, 0, −11.5) with a lock box and **`booth_key_mount`**; Strand's key opens it before power; open = scale local Z
  to 0.15 about the origin, as `IA_gate_west` in Chapter 3 (lattice folds against its post).
- **`booth_desk.glb`** (≤ 6k, ≤ 6; `M_Wood_Walnut`, `M_Brass_Aged`, `M_Leather`, `M_Steel_Painted`): Strand's desk 1.6 × 0.8, a green-shaded
  lamp, a coat on a stand, a stopped table clock; empty **`box_mount`** on the desk top at (0, 0.78, 0.0).
- **`strand_box4.glb`** (≤ 7k, ≤ 12; `M_Wood_Walnut`, `M_Brass_Aged`, `M_Bakelite`, `M_Paper`): walnut box 0.42 × 0.30 × 0.18; a brass
  top plate with four dials; four knobs **`IA_knob_1..4`** (knurled brass Ø 0.05 on the front, 6 detents, **step = −60° k about +Z**);
  four gears with pointers **`gear_pointer_1..4`** (pivots at the dial centres, identity = pointing at the mark, **step = −60° k about +Y**
  for a top-view dial); the lid **`IA_box_lid`** hinged at the back, **open = −110° about +X**; under the lid the pictogram plate
  (a wheel with an arrow to its neighbour, brass inlay). Inside: `orrery_mount` and the log pad **`IA_box_log`** with `log_mount`.
- **`orrery.glb`** (≤ 3.5k, ≤ 5; `M_Brass_Aged`, `M_Steel_Dark`, `M_Chrome`): a Ø 0.34 brass model of the Array: a base with the marks 1–8,
  four concentric rings (fixed), four towers **`orrery_tower_1..4`** each a node at the model centre with a tiny pylon at radius
  0.04 n along +Z (mark 1); **the code rotates tower n by −45° p about +Y** from `v_align`.
- **`watch_room.glb`** (≤ 8k, ≤ 9; `M_Steel_Dark`, `M_Glass`, `M_Chequer`, `M_Brass_Aged`): a cabin x ∈ [11.5, 13.9] with a back wall, a
  glass window, a floor; **`IA_watch_gate`**: a steel lattice grille door on the west face (x = 11.5) with a lock box and
  **`watch_key_mount`** (Leyla's key opens it before power); empties `board_mount`, `lockers_mount`, `post_mount`,
  `echo_mount_clerk_post`.
- **`roll_board.glb`** (≤ 5k, ≤ 5; `M_Wood_Walnut`, `M_Brass_Aged`, `M_Enamel_Cream`, `M_Glass_Dark`): 2.4 × 1.5 board with 3 rows of 14 hook
  slots (the 42nd is empty); prototype meshes **`tag_proto`** (a cream enamel tag 0.10 × 0.07) and **`lamp_proto`** (a jewel Ø 0.03)
  that the code turns into two `MultiMesh`es (41 tags, 42 lamps), and an empty `slot_origin` at the first slot (−1.04, 1.28, 0.05),
  step (0.16, −0.30). The 42nd slot is the Leyla slot.
- **`lockers.glb`** (≤ 6k, ≤ 8; `M_Steel_Painted`, `M_Brass_Aged`, `M_Paper`): two rows of 12 lockers; **`IA_locker_17`** (hinged on the left, **open
  = −105° about +Y**); inside **`IA_locker_note`** and **`IA_locker_parcel`** (pads) with `note_mount`, `parcel_mount`.
- **`post_station4.glb`** (≤ 8k, ≤ 12; `M_Brass_Aged`, `M_Steel_Dark`, `M_Bakelite`, `M_Enamel_Cream`): a pneumatic post station: destination dial **`IA_post_dial`**
  with the six Chapter 2 pictograms as 3D inlay (director's ✦, book, flask, film, letter, lock) — position d = **−60° d about +Z**; number wheel
  **`IA_post_number`** (1–9, step −40° about +Z); canister **`IA_post_canister`** in a tube mouth, slides **+0.35 along +Z** when sent;
  **`IA_post_send`** lever (rest up, **pulled = +50° about +X**); the tube rising into the ceiling; `canister_mount`.

## 9. Groups H and I — items and echoes (contract only)

Items: the ch3 §9 rules (real size, origin at the centre of mass, flat items hero face +Y with the top edge toward −Z, standing items
face +Z). `tower_key_1..4` (≤ 1.2k each, flat, bow toward −Z; a Castell-style key with the numeral I–IV in relief), `strand_log` (a bound
logbook 0.20 × 0.14 × 0.025, flat), `pocket_watch` (Ø 0.05, a brass hunter case engraved with the Institute mark, standing),
`strand_last_letter` (reuse `letter.glb` with a seal), `reverse_pawl` (a brass pawl 0.08 long, flat), `leyla_note_1998` (a folded
paper, flat), `leyla_parcel` (a brown-paper parcel with string, 0.20 × 0.12 × 0.08, flat). Existing: `crystal_lens`, `key_strand`,
`key_leyla`.

Echoes (`lib_echo`, one slot `M_Echo`, poses as root objects, origin between the feet, facing +Z):
- `echo_crowd` (≤ 1.4k file, 450 per pose, 3 poses `pose_a/b/c`): a simplified standing figure; the code draws **33** with one `MultiMesh`
  and switches the pose per minute.
- `echo_named` (≤ 29k file, 1.2k per figure per pose, 3 poses): **8** detailed figures as one `MultiMesh` per pose (foreground).
  Positions of the 41: 14 on the apron r 12.6, 11 at r 9.5, 8 at r 7.5, 5 at r 5.5, 3 at r 3.8, evenly spaced and staggered, all
  facing the Core; the 8 named ones are the ones nearest the catwalk.
- `echo_strand_desk` (≤ 5k): Strand reaching for the master lever; origin on `echo_mount_strand`; contact point: right grip at
  (−0.15, 1.12, 0.62) relative to the figure (lever grip lifted or down).
- `echo_leyla_1998` (≤ 16k file, ≤ 8k per pose): **`pose_lift`** (1998, at the lift, looks at the chalk) and **`pose_walk`** /
  **`pose_seat`** (walks from the Core to the cradle and seats the lens at (0, 3.82, 0.62); right hand at (−0.10, 1.35, 0.45)).
- `echo_tech_panel`, `echo_clerk_post` (≤ 6k each), `echo_tech_wheels` (≤ 12k file, two figures `tech_a`, `tech_b`, 6k each).

## 10. Variants: evidence rendered from the state (no answer baked)

| Puzzle | State key | Surface | How it is drawn |
|---|---|---|---|
| P1 Panel 0 | `v_panel` (20 ints) | `trace_<s>_<line>` ×20 | The code shows the junction dot where `v_panel[(s − 1) * 4 + line]` = 1 |
| P2 box | `BOX_START` | `gear_pointer_1..4` | Pointer k at `−60° × value` |
| P3 arc | `gap_target()` | `ammeter_band` | Rotated to the needle value 10 − g |
| P4 iris | `iris_order()` | `IA_leaf_1..6` `position.z` | `z = 0.012 × (5 − rank)` |
| P5 orrery | `align_target()` | `orrery_tower_1..4` | `−45° × p` each; the towers on the rings are at `rings` |
| P8 chart | `night()` | `chart_paper` shader | Pen marks at the minutes (m_sun, m_rings, m_keeper) and 03:17 |
| P11 beat | `note_target()` | `osc_screen` shader | Envelope frequency ∝ \|keeper − k\|; never the answer itself |

## 11. Budgets

### 11.1 Per model

| Model | Group | Tris ≤ | Surfaces ≤ | Materials |
|---|---|---|---|---|
| `shell_hall` | A | 16,000 | 9 | 4 |
| `shell_lift4` | A | 5,000 | 5 | 4 |
| `bridge` | A | 10,000 | 7 | 4 |
| `catwalk` | A | 8,000 | 7 | 3 |
| `shared_numerals` | A | 3,000 | kit | 1 |
| `master_desk` | B | 12,000 | 8 | 4 |
| `master_lever` | B | 3,000 | 2 | 2 |
| `keeper_knob` | B | 4,500 | 4 | 3 |
| `handwheel` (×4) | B | 3,500 | 2 | 2 |
| `panel0` | B | 10,000 | 40 (≤ 20 drawn) | 4 |
| `ring_rails` | C | 6,000 | 2 | 2 |
| `array_rings` | C | 14,000 | 4 | 1 |
| `mirror_tower` (×4) | C | 4,000 | 3 | 2 |
| `beam_segment` | C | 100 | 1 | 1 |
| `cage` | D | 12,000 | 6 | 2 |
| `glass_tower` | D | 9,000 | 7 | 3 |
| `core_crystal` | D | 3,000 | 3 | 3 |
| `cradle` | D | 3,000 | 4 | 2 |
| `heart_drawer` | D | 4,000 | 7 | 4 |
| `sun_lamp` | E | 12,000 | 8 | 4 |
| `sun_iris` | E | 5,000 | 7 | 2 |
| `sun_pedestal` | E | 6,000 | 7 | 4 |
| `booth` | F | 10,000 | 9 | 4 |
| `booth_desk` | F | 6,000 | 6 | 4 |
| `strand_box4` | F | 7,000 | 12 | 4 |
| `orrery` | F | 3,500 | 5 | 3 |
| `watch_room` | G | 8,000 | 9 | 4 |
| `roll_board` | G | 5,000 | 5 | 4 |
| `lockers` | G | 6,000 | 8 | 3 |
| `post_station4` | G | 8,000 | 12 | 4 |
| each item | H | as ch3 §9 | ≤ 3 | ≤ 2 |
| `echo_crowd` | I | 1,400 file / 450 drawn × 33 | 3 | 1 |
| `echo_named` | I | 29,000 file / 1,200 drawn × 8 | 3 | 1 |
| `echo_strand_desk`, `echo_tech_panel`, `echo_clerk_post` | I | 5,000–6,000 | 1 | 1 |
| `echo_leyla_1998`, `echo_tech_wheels` | I | 16,000 / 12,000 file | 2 | 1 |

### 11.2 Per view (target ≤ 90 scene draw calls with shadows, ≤ 120k primitives)

Estimates at the caps with frustum culling; the scene measures them in the playthrough (`RenderingServer`). The hot view is
`bridge`:

| Group in `bridge` | Surfaces |
|---|---|
| hall shell 8 + bridge 5 + desk 8 + lever 2 + keeper 4 + 4 wheels 8 | 35 |
| catwalk 7 + rails 1 + rings 4 + towers 4 × 3 + beams ≤ 5 | 29 |
| island: cage 6 + glass tower 7 + Core 2 + cradle 2 + drawer 3 (the collar digits, gates' locks may be culled beyond 9 m) | 20 |
| echoes (3 `MultiMesh`) | 3 |
| shadow casters (catwalk, bridge, rings only) | ~6 |
| **Total** | **~93** |

If it is over, in this order: hide the hatch lids and the key meshes beyond 10 m, merge the bridge's static parts with
`ModelUtil.merge_static`, drop the shadow caster list to the rings. The other views (`desk`, `panel0`, `island`, `apse`, `booth`,
`watch`) draw one zone each (30–60).

### 11.3 Textures
No new texture is needed for groups A and B: the chalk is geometry, the numerals are relief, the strip chart and the oscilloscope use
shader quads. Tiling sets 1K (`M_Concrete`, `M_Paint_Green`), as ch3 §13.4.

## 12. Groups, deliverables and order of work

Every group delivers `tools/blender/models/<name>.py` (+ `lib_ch4_<group>.py`), the build list
`tools/blender/build_lists/ch4_<group>.txt`, the GLBs in `game/assets/models/`, QA renders in `qa/blender/ch4/`
(Cycles ≤ 32 samples, ≤ 960 × 640, 2 threads, from the §2 views) and the measured page `docs/models/ch4_<group>.md`.

| Group | Models |
|---|---|
| **A** shell and circulation | `shell_hall`, `shell_lift4`, `bridge`, `catwalk`, `shared_numerals` (+ `lib_ch4.py`, `lib_ch4_numerals.py`) |
| **B** the bridge desk | `master_desk`, `master_lever`, `keeper_knob`, `handwheel`, `panel0` |
| **C** the Array | `ring_rails`, `array_rings`, `mirror_tower`, `beam_segment` |
| **D** the Reliquary | `cage`, `glass_tower`, `core_crystal`, `cradle`, `heart_drawer` |
| **E** the Sun apse | `sun_lamp`, `sun_iris`, `sun_pedestal` |
| **F** Strand's booth | `booth`, `booth_desk`, `strand_box4`, `orrery` |
| **G** the watch room | `watch_room`, `roll_board`, `lockers`, `post_station4` |
| **H** items | `tower_key_1..4`, `strand_log`, `pocket_watch`, `reverse_pawl`, `leyla_note_1998`, `leyla_parcel` (+ reuse) |
| **I** echoes | `echo_crowd`, `echo_named`, `echo_strand_desk`, `echo_leyla_1998`, `echo_tech_panel`, `echo_tech_wheels`, `echo_clerk_post` |

Order: A first (everything else is QA-rendered inside `shell_hall`); then B, C, D in any order; E–I in parallel.

## 13. Differences from `CHAPTER4_DESIGN.md` and notes for the logic and the room code

1. **Deck height.** The bridge deck is y = 2.5, flush with the catwalk (the design had 2.0 and 2.5). The desk eye height keeps the
   hall visible over the desk (the desk is ≤ 1.5 high).
2. **The lift.** The cage is the Chapter 3 `freight_lift`, moved to (0, 0, 16.4) (design: 15.5) so the bridge and the pier fit in front
   of it; its gates open west and east into the south bay, which `shell_lift4` builds. The bridge is reached by two stairs inside the
   bay.
3. **Panel 0** stands on a pier wall under the bridge at z = 14.0 (design: 13.8). Its traces are `trace_<s>_<line>` dots, not full
   routes; wires and buses are static.
4. **Floor marks** are inlays in `shell_hall` (the design also listed a group C `floor_mark`; dropped).
5. **New models:** `watch_room` (the enclosure and the grille `IA_watch_gate`), `ring_rails`, `beam_segment`, `array_rings` (one GLB with four
   rotating nodes), `mirror_tower` (one GLB, four instances).
6. **Hotspot ids:** `IA_chronometer` for `use_item_on(…, "chronometer")`, `IA_cradle` for `"cradle"`, `IA_gate_n` for `"gate_n"`,
   `IA_booth_gate` for `"booth_gate"`, `IA_watch_gate` for `"watch_gate"`, `IA_post_canister` for `"post_canister"`; pick-ups:
   `IA_key` on each tower → `take("tower_n")`, `IA_box_log` → `box_log`, `IA_heart_watch/letter/pawl` → `heart_*`,
   `IA_locker_note` / `IA_locker_parcel` → `locker_*`.
7. **Handwheel numerals** I–IV are on the bridge's wheel plates (dark steel plates with brass numerals, lying on the deck in front of each
   mount), not on the `handwheel` GLB (one GLB serves four positions). The wheel's own dial plate carries the stops 1–8.
8. **Built-model changes found while modelling** (groups A and B; the measured pages `ch4_a.md` and `ch4_b.md` have the numbers):
   - the catwalk gate opens **+95°** about +Y (north, onto the catwalk); the cage gates open −95° (outward);
   - the cameras `lift`, `hatch_n`, `handwheels`, `chronometer` and `panel0` of §2 were moved so they actually see their subject (the first
     `lift` camera was inside the cage; `hatch_n` looked into the deck slab; the four wheels do not fit a 78° view from the desk);
   - the hall has **18 pilasters** (every 15°, offset 7.5°) and 24 radial ribs on the same azimuths, 16 ventilation grilles;
   - the master desk's slope is 38.2° (from (z 0.46, y 0.95) to (z −0.20, y 1.47)) and its jog wheel, dial, bay and chart are placed on it
     with the formula P(s, x) of §4; the chart drum and the pen are static (the shader draws the pen mark); the keeper unit has no lamp;
   - Panel 0's switches stand at x = −0.74 and its numerals at x = −0.85 (the bezel took the first positions).
