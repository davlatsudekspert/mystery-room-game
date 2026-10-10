# Chapter 4 group A: shell and circulation (measured results)

Contract: `docs/models/ch4.md` §0, §1 (layout, placement), §2 (views), §3 (group A), §11, §12. Models: `shell_hall`,
`shell_lift4`, `bridge`, `catwalk`, `shared_numerals`. Scripts: `tools/blender/models/<name>.py`; shared helpers in
`tools/blender/lib_ch4.py` (on top of `lib_ch3_a`, `lib_ch3_d`, `lib_ch3_bc`, `lib_ch3_ef`; none of the older libraries were
edited) and `tools/blender/lib_ch4_numerals.py`; build list `tools/blender/build_lists/ch4_a.txt`.

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [--shots=1,2,...]
MR_S=10 MR_W=640 MR_H=427 blender ... -- --shots=1     # a fast low-res check (env: samples, width, height)
```

**Pipeline.** As group A of Chapter 3: every script builds in Godot axes (the G-frame), converts to Blender axes
before parenting, exports a lean GLB to `game/assets/models/<name>.glb`, **re-reads the GLB** and checks the required
node names, model-space positions (1 mm), identity rest rotations, triangles, surfaces (mesh nodes × primitives) and
material slots against §11, and runs `check_glb_names.py`. Renders: Cycles, 32 samples, 960 × 640, 2 threads, cameras
from §2 (Godot position, target, vertical FOV) in a QA scene made of the model under test as built plus the neighbouring GLBs
imported (`shell_hall` always, then `shell_lift4`, `freight_lift`, `bridge`), with the §1.5 lights as QA lights (the oculus
shaft spot, a Core stand-in glow, the four work lamps, the bridge lamp) and a camera fill. Blender renders only, no Godot
screenshots. Two QA-only tweaks: the hall floor's preview material has its normal map removed (a 28 m tiled floor seen at a
grazing angle goes black under the preview stone normal map in Cycles; the game uses its own `.tres`), and the oculus
shutters are posed open for the lit views.

All coordinates are **Godot, world, metres** (these are room-coordinate models: origin = the world origin, built in place).

## Summary

| Model | Tris (budget) | Surfaces (cap) | Slots | GLB | QA renders (`qa/blender/ch4/`) |
|---|---|---|---|---|---|
| `shell_hall` | 15,523 (16,000) | 8 (9) | 4 | `game/assets/models/shell_hall.glb` | `shell_hall.png`, `_2` |
| `shell_lift4` | 3,351 (5,000) | 5 (5) | 4 | `game/assets/models/shell_lift4.glb` | `shell_lift4.png`, `_2` |
| `bridge` | 7,195 (10,000) | 5 (7) | 4 | `game/assets/models/bridge.glb` | `bridge.png`, `_3`, `_4` |
| `catwalk` | 4,256 (8,000) | 7 (7) | 3 | `game/assets/models/catwalk.glb` | `catwalk.png`, `_2` |
| `shared_numerals` | 1,848 (3,000) | 15 (kit) | 1 | `game/assets/models/shared_numerals.glb` | `shared_numerals.png` |
| **Group A total (placed models)** | **30,325** | **25** | | | |

`check_glb_names.py` passes on all five GLBs. The placed models together are 25 surfaces; with `bridge`'s desk group (group B)
the `bridge` view stays inside the 90-draw-call plan of §11.2.

---

## shell_hall.glb (15,523 tris, 8 surfaces)

| Node | Material | Tris | Notes |
|---|---|---|---|
| `hall_floor` | `M_Concrete` | 658 | Disc r 14 in 7 rings × 48 segments (so tangents stay clean) plus the apse niche floor (the half disc west of the circle) |
| `hall_walls` | `M_Concrete` | 1,362 | Upper wall (y 3.35 – 6.7; 6.2 – 6.7 over the bay opening; 4.6 – 6.7 over the apse), skirting 0 – 0.25, a band 3.2 – 3.36, **18 pilasters** 0.5 × 0.38 at φ = 7.5° + 15° k (24 positions, the six inside the openings skipped), the apse niche wall (half cylinder r 3.6 about (−13.53, 0, 0), up to 4.6) and its flat ceiling |
| `hall_dado` | `M_Paint_Green` | 196 | Green panels 0.25 – 3.2 at r 13.96, with the niche's dado |
| `hall_vault` | `M_Concrete` | 4,200 | The dome (13 profile rings, 96 segments), the shaft tube r 1.5 from y 12 to 14.6 and its cap, **24 radial ribs** 0.34 × 0.42 hanging under the dome at φ = 7.5° + 15° k (so each continues a pilaster) |
| `hall_trim` | `M_Steel_Dark` | 5,888 | Oculus ring r 1.5 – 2.05 (y 11.85 – 12.18), four ring ribs at r 11, 8, 5, 3.2 following the dome, **16 ventilation grilles** (3.0 × 1.5 at y 3.9 – 5.4, one between each pair of pilasters not next to an opening; 7 bars each) |
| `hall_brass` | `M_Brass_Aged` | 2,971 | Stepped cornice (y 6.55 – 7.0), two thin wall bands, pilaster caps and bases, a 0.14 brass cap under each radial rib, the floor inlay: **8 radial lines** r 3.4 – 11.4 (0.07 wide), rings r 3.3 and r 11.5, the **digits 1–8** (0.55 high, lying flat at r 12.4, top outward) |
| `oculus_shutter_a` / `_b` | `M_Steel_Dark` | 124 each | Half discs r 1.6 at y 11.78 – 11.84 with underside ribs. **Origin (0, 11.78, 0)**, identity at rest. Open = a slides **−1.7 along X**, b **+1.7** |

Empties: `portal_bay` (0, 3.0, 13.2), identity; `portal_apse` (−13.6, 2.0, 0), rotation **(0, −90, 0)** (+Z toward −X).
Bounds: x −17.13 … 14.0, y 0 … 14.6, z −14.0 … 14.0.

Notes for the scene:
- The wall is a **skin** (one-sided, facing in); the bay's reveals are `shell_lift4`'s, the niche is in this model.
- The openings: south bay φ ∈ [154.62°, 205.38°] up to y 6.2 (the lintel above it belongs to this model, y 6.2 – 7.0); west apse
  φ ∈ [255.1°, 284.9°] up to y 4.6.
- The vault's radii: dome underside through (14, 7.0) and (1.5, 12.0), sphere centre at y = −9.875, so `dome_y(r) = −9.875 +
  √(21.93² − r²)` (`lib_ch4.dome_y`). Cast the `shaft` spot from (0, 12.2, 0).
- `hall_trim` is the biggest mesh (5.9k, 16 grilles with 7 bars each). If the hall needs trimming, drop the grilles behind the booth
  and the Sun apse first (they are the ones the cameras never face).
- QA renders: `shell_hall.png` is the `bridge` view from the bay mouth (Core stand-in, shutters open); `shell_hall_2.png` is a
  hero from the north apron looking up at the vault and the oculus.

## shell_lift4.glb (3,351 tris, 5 surfaces)

| Node | Material | Tris | Notes |
|---|---|---|---|
| `bay_floor` | `M_Concrete` | 25 | x ±6, from the hall circle to z 18.2 |
| `bay_walls` | `M_Concrete` | 47 | Side walls x = ±6, back wall z = 18.2 (y 0 – 6.2), the ceiling at y 6.2 with the shaft opening (x ±1.3, z 15.1 – 17.7) and the short shaft above it to y 9.0 with a cap |
| `bay_frame` | `M_Steel_Dark` + `M_Brass_Aged` (2 surfaces) | 1,993 | Portal arch (a lintel along the hall circle, y 5.7 – 6.2, and two jambs 0.56 × 0.34 at the opening's edges), two I-section ceiling beams at z 14.85 and 17.85 (rivets on the lower flange), skirting angles, **wall ribs** (flat bars every 1.2 – 2 m) and a band at y 3.1 – 3.3 round the three walls, two caged bulkhead lamps at (±5.85, 3.4, 16.0); brass level plate 0.34 × 0.46 on the back wall at (3.0, 1.55) with **a down arrow and no numeral** |
| `leyla_chalk` | `M_Chalk` | 1,286 | Her sign (crescent opening right + three dots, 0.55 high) and **1998** (digits 0.20 high, each jittered ±4°), an underline; strokes 2 mm proud, on the back wall at (−3.0, 1.5, 18.18), facing −Z |

Empties: `echo_mount_leyla_lift` (−3.4, 0, 17.0) yaw 0 (the figure faces the chalk); `lift_light` (0, 5.8, 16.4).
Bounds: x ±6.28, y 0 … 9.0, z 12.29 … 18.2.

Notes for the scene:
- The Chapter 3 `freight_lift` is placed at **(0, 0, 16.4)**, yaw 0 (QA-checked in `shell_lift4.png`). Fold both gates (scale Z 0.15) on arrival.
- The lift view must stand **outside** the cage: the contract's first `lift` camera (inside the cage) saw only its riveted walls.
  §2 now has `lift` at (1.55, 1.6, 16.5) → (5.0, 2.2, 12.5), plus `bay_hero` (0, 1.7, 7.5) → (0, 2.6, 15.5) and `lift_chalk`
  (−2.9, 1.55, 15.4) → (−3.0, 1.5, 18.18).
- `M_Chalk` has no QA preview colour in `mrlib.PREVIEW`; `lib_ch4.ensure_materials` creates it as `ECE6D6` (the `.tres` value).
- QA renders: `shell_lift4.png` the bay from the hall side (cage, portal, ribs, chalk, level plate); `shell_lift4_2.png` the chalk
  close-up.

## bridge.glb (7,195 tris, 5 surfaces)

| Node | Material | Tris | Pivot / notes |
|---|---|---|---|
| `bridge_deck` | `M_Chequer` | 1,188 | Deck slab y 2.44 – 2.5, x ±5.9, z 11.95 – 14.8; 26 stair treads (13 per flight) |
| `bridge_frame` | `M_Steel_Dark` | 4,436 | Front plate-girder fascia (y 1.5 – 2.44, 13 stiffeners, 80 rivets), rear girder, 10 cross beams, columns at (±5.5, ±3.3, z 12.25) and (±5.5, z 14.15 – 14.55), the four **numeral plates** 0.42 × 0.28 at (x_i, 2.5, 12.91), rail posts (gate posts at x = ±0.6), stair stringers and posts |
| `bridge_rail` | `M_Brass_Aged` | 959 | North rail top y 3.55 / mid 3.05 (gate opening x ±0.55), side pieces, rear rail, stair handrails (inner side, x = ±4.93), the brass numerals **I..IV** (0.16 high) on the plates, reading upright from the south |
| `bridge_paint` | `M_Steel_Painted` | 220 | The pier wall x ±3.2, z 14.0 – 14.4, y 0 – 2.44, plinth, cap and two raised panels (x ±1.25 … ±3.0). Panel 0 stands on its north face |
| `catwalk_gate` | `M_Brass_Aged` | 392 | Lattice leaf 1.0 × 1.05 (rails, 6 bars, brace, lock box with a lamp); **origin = the hinge (−0.55, 2.5, 11.95)**, identity closed; **open = +95° about +Y** (swings north onto the catwalk; the contract text had −95°, which swings south) |

Empties: `wheel_mount_1..4` (−3.6, −2.2, 2.2, 3.6; 2.5; 12.45) identity; `desk_mount` (0, 2.5, 13.15); `echo_mount_wheels_1` (−2.9, 2.5, 13.3)
and `_2` (2.9, 2.5, 13.3), rotation (0, 180, 0); `bridge_light` (0, 5.9, 13.5). Bounds: x ±5.91, y 0 … 3.6, z 11.89 … 18.03.

Stairs: 14 risers of 0.1786 (rise 2.5), 13 treads of run 0.246 from the bay floor at z = 18.0 up to the deck edge at z = 14.8, on
x ∈ [4.9, 5.9] and [−5.9, −4.9]. The stringer plate and the handrail are on the inner side (x = ±4.9).

Notes for the scene:
- The handwheel numerals live **here** (plates at `wheel_mount_n`), not on the `handwheel` GLB.
- The deck is chequer plate with no alpha; the fascia is the face seen from the hall (`bridge.png`).
- QA renders: `bridge.png` from the hall (catwalk gate swung open); `bridge_3.png` on the deck looking along the north rail;
  `bridge_4.png` the numeral plates I and II.

## catwalk.glb (4,256 tris, 7 surfaces)

| Node | Material | Tris | Pivot / notes |
|---|---|---|---|
| `catwalk_deck` | `M_Chequer` | 572 | Slab y 2.44 – 2.5, x ±0.6, z 2.94 – 11.95 with four 0.9 × 0.9 openings at z = 10.5, 8.5, 6.5, 4.5 |
| `catwalk_frame` | `M_Steel_Dark` | 3,188 | Two girders at x = ±0.5 – 0.58 (clear of the openings), cross ties, **trestles at z = 11.4, 9.5, 7.5, 5.5** (between the ring tracks, which occupy z ± 0.45 around the hatch z's), openings' coamings, hinge barrels at each opening's north edge, posts every 1.075 m, toe boards, 44 rivets, an end plate at z = 3.0 |
| `catwalk_rail` | `M_Brass_Aged` | 144 | Top rail y 3.5, mid rail y 3.0, both sides |
| `IA_hatch_1..4` | `M_Chequer` | 88 each | Lid 0.98 × 0.98 × 0.03 with a pull bar; **origin at the north hinge edge (0, 2.5, z_n − 0.49)**, identity closed (top y 2.53); **open = −105° about +X** (it stands up and leans north). z_n = 10.5 / 8.5 / 6.5 / 4.5 |

Bounds: x ±0.67, y 0 … 3.53, z 2.94 … 11.95. The lid bounds are (±0.49, 2.5 … 2.552, z_n ∓ 0.49).

Notes for the scene:
- The hatch camera in the contract (z_n + 0.9) looked into the deck slab. §2 now has `hatch_n` at (0, 3.35, z_n + 0.55) → (0, 0.65, z_n − 0.05),
  FOV 50: leaning over the opening.
- The lid is one chequer object with a pull bar; its tap target (`IA_hatch_n`) returns `take("tower_n")` → `tower_out_of_reach` while the
  ring is out of line.
- QA renders use stand-in towers (a ring, a plinth, a post, a chrome head, a key on the bracket shelf) to check the view down through the hatch;
  `catwalk.png` is the `catwalk` view with the lid of hatch 2 open; `catwalk_2.png` is `hatch_1`.

## shared_numerals.glb + lib_ch4_numerals.py (1,848 tris, 15 objects, kit)

`num_I … num_V` and `dig_0 … dig_9`, one material (`M_Brass_Aged`), each 0.25 high × 0.01 deep, centred on its own origin, facing +Z; the
node translations only lay the sheet out (`num_*` at x = 0.50 + 0.55 k, y = 0.40; `dig_*` at x = 0.20 + 0.40 k, y = 0). The Roman set is
drawn from polygons (stroke 0.17 of the height, serifs 0.36 wide × 0.075 thick, a solid V with a flat tip, IV = I + V, gap 0.10 of the
height); the digits are DejaVu Sans Bold at low resolution. `lib_ch4_numerals.py` exposes `roman_shapes`, `roman_obj` and `digit_obj`;
`shell_hall` (floor digits 1–8), `bridge` (I–IV), and the later Chapter 4 models use them. **Not drawn in the game.** QA: `shared_numerals.png`.

## Open points

- The hall's `hall_trim` and `hall_brass` are the two biggest meshes; both are single draw calls, so they only matter for primitives.
- The whole group has no collider: the code builds colliders only for `IA_*` parts (`IA_hatch_1..4` here), as in Chapter 3.
- `shell_hall` has no lights and no fog; the oculus shaft and the Core glow are the code's (§1.5).
