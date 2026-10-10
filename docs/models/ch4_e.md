# Chapter 4 group E: the Sun apse (measured results)

Contract: `docs/models/ch4.md` §0, §1, §2, §7, §10, §11, §12. Models: `sun_lamp`, `sun_iris`, `sun_pedestal`.
Scripts: `tools/blender/models/<name>.py`; helpers in `tools/blender/lib_ch4_cde.py` on top of `lib_ch4.py` and `lib_ch4_numerals.py`; build list
`tools/blender/build_lists/ch4_e.txt`. Same pipeline and QA scene as groups A–D: G-frame build, lean GLB, re-read and verify against §11, Cycles 24 samples
960 × 640, the hall shell + bridge + catwalk + rings as the setting, the three Sun models placed together at their §1.3 positions, the §1.5 `sun_arc` light
(white, at (−12.4, 1.8, 0)) as a QA light. Blender renders only.

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [--shots=1,2]
```

## Summary

| Model | Tris (budget) | Surfaces (cap) | Slots | GLB | QA renders (`qa/blender/ch4/`) |
|---|---|---|---|---|---|
| `sun_lamp` | 9,812 (12,000) | 8 (8) | 4 | `game/assets/models/sun_lamp.glb` | `sun_lamp.png`, `_2` |
| `sun_iris` | 3,666 (5,000) | 7 (7) | 2 | `game/assets/models/sun_iris.glb` | `sun_iris.png`, `_2` |
| `sun_pedestal` | 5,743 (6,000) | 7 (7) | 5 (4) | `game/assets/models/sun_pedestal.glb` | `sun_pedestal.png`, `_2` |
| **Group E in the `apse` view** | | **22** | | | `sun_*` + `shell_hall` (the apse view draws S, R and nothing else) |

`check_glb_names.py` passes on all three GLBs.

## sun_lamp.glb (9,812 tris, 8 surfaces)

Local frame: **origin = the sphere centre**, placed at (−13.0, 1.8, 0), yaw 0; the glass port faces **+X** (into the hall); the floor is at local y = −1.8.
Bounds x −1.2 … 1.052, y −1.8 … 1.52, z ±1.75.

| Node | Material(s) | Tris | Pivot / notes |
|---|---|---|---|
| `sun_lamp` | `M_Brass_Aged` + `M_Steel_Dark` + `M_Glass` | 9,192 | Origin (0, 0, 0), identity. **Brass**: the sphere Ø 2.4 (a lathe about X, open at the port: θ ≤ 38.7° from +X, port radius 0.75) with **eight meridian straps** and **two latitude straps** (raised 11 mm, 64 mm wide) and about 120 rivets, the port **bezel** (r 0.70 … 0.98, x 0.90 … 1.04) with 16 bolts. **Steel**: the dark lining (r 1.17, faces inward, so the inside reads through the port), six cooling-fin rings round the back pole (x −0.78 … −1.10), a chimney on top (y 1.10 … 1.52), the **cradle** (two trunnions at z ±1.18 … 1.44, four splayed legs down to foot plates at y −1.8, braces, base rails) and the carriage rail for `rod_b` (y −0.47 … −0.43, x −0.30 … 0.92). **Glass**: the port disc r 0.752, x 0.925 … 0.945 |
| `rod_a` | `M_Steel_Dark` + `M_Brass_Aged` | 240 | **Origin = its tip at the touching position (−0.25, 0, 0)**. The fixed carbon rod toward −X: Ø 0.10 with a tapered tip, 0.55 long, a brass cap (to x = −0.90) and a holder block (to x = −1.10) on the lining |
| `rod_b` | `M_Steel_Dark` + `M_Brass_Aged` | 284 | **Origin = its tip at the touching position (−0.25, 0, 0)**, on the same axis. The moving carbon rod toward +X: 0.42 long, a brass cap, a carriage strut and shoe that ride on the rail. **gap g (0 … 9) = rod_b slid 0.07 g along +X** (g = 0 shorted, 9 the start): at g = 9 the cap's end is at x = 0.89, inside the glass (0.925) |
| `arc_glow` | `M_Emissive_Lumen` | 96 | **Origin = the disc centre (−0.25, 0, 0)**. A disc Ø 0.44 at the touching plane facing +X (both sides); the code drives its intensity; it may slide +0.035 g along +X to stay mid-gap |
| `sun_light` | empty | — | (−0.20, 0, 0), the OmniLight position for the arc |

Notes for the scene:
- The back half of the sphere (θ > 100°) and the cradle legs are seen from the apse only at a grazing angle: the draw is 3 surfaces for the static node plus 2 + 2 + 1.
- The iris frame (`sun_iris`, 0.2 in front of the bezel: the bezel's front face is at world x = −11.96, the iris back ring at −11.83) leaves a 0.13 slit that the arc's light leaks through, as the design wants.
- The apse niche is a half-cylinder r 3.6 about (−13.6, 0, 0): the lamp's cradle (z ±1.75) stands inside it.

## sun_iris.glb (3,666 tris, 7 surfaces)

**Iris frame**: origin = the iris centre, leaves in the XY plane, front = +Z; placed at (−11.8, 1.8, 0) with **yaw 90** so local +Z faces +X (into the hall).

| Node | Material | Tris | Pivot / notes |
|---|---|---|---|
| `iris_frame` | `M_Steel_Dark` | 2,328 | Origin (0, 0, 0), identity. A back ring (r 0.74 … 1.20, z −0.03 … 0), a **front bezel** (r 1.00 … 1.22, z 0.075 … 0.135) the leaves slide under, six radial **guide rails** (0.12 wide, r 1.2 … 1.92 on each leaf's centreline) with **end stops and latch brackets** at r 1.86 … 1.94, hold-down clips at r 1.35 and 1.62 and 24 rivets on the bezel. The rails and stops reach r 1.94: **the frame is Ø 2.4 at the ring and Ø 3.9 over the rails** (the contract's Ø 2.4 could not hold leaves that slide 0.95 out) |
| `IA_leaf_1..6` | `M_Brass_Aged` | 223 each | Six wedge leaves, each **88° = 60° + 14° overlap on each side**, outer radius 0.86, 10 mm thick, with a raised rim on the arc, a centre rib and a **pull knob at r 0.52** (the tap target). **Leaf k is centred at CLOCKWISE 60° (k − 1) from up (+Y) seen from the front.** **Origin = (0, 0, z_k), identity rotation**, the mesh built round that origin. Bounds: leaf 1 x ±0.597, y 0 … 0.86 |

**Stack**: `z = 0.012 × (5 − rank)`, rank 0 = the top of the stack. The GLB ships the **canonical stack [3, 6, 1, 5, 2, 4] (top → bottom)** baked:

| Leaf | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| rank | 2 | 4 | 0 | 5 | 3 | 1 |
| z (node position.z) | 0.036 | 0.012 | 0.060 | 0.000 | 0.024 | 0.048 |

The code overrides each leaf's `position.z` from `v_iris`. **A leaf opens by sliding 0.95 radially outward**: `position.xy = 0.95 × (sin a, cos a)` with a = 60° (k − 1) in the iris frame
(a leaf ends under the front bezel and out onto its rail, against its end stop). Closed, the six leaves cover the aperture (r ≤ 0.74) fully, the overlaps show
as steps of 12 mm: the stack order reads from the shading and the shadows (the knob of a lower leaf is never under an upper one).

## sun_pedestal.glb (5,743 tris, 7 surfaces)

Local frame: **origin = the floor at the footprint centre, front = +Z**; placed at (−12.0, 0, 2.4) with **yaw 90** (the front faces +X, into the hall). Bounds x ±0.34, y 0 … 1.425, z −0.28 … 0.431.

| Node | Material(s) | Tris | Pivot / notes |
|---|---|---|---|
| `sun_pedestal` | `M_Steel_Painted` + `M_Brass_Aged` + `M_Enamel_Cream` | 4,187 | Origin (0, 0, 0), identity. A plinth (0.68 × 0.56), a cabinet (0.60 × 0.48, y 0.10 … 0.86) with a raised door panel and hinges, a **slanted top shelf** (y 0.86 at the front edge → 1.00 at z = −0.04), an **instrument head** (y 1.00 … 1.40, front face z = −0.04) and brass trim. **Feed scale**: a cream disc Ø 0.54 (centre (0, 0.50), front z 0.264) with 10 ticks and the numerals **9 … 0 clockwise from 12 o'clock every 27°** (the GAP g the wheel's handle points at: the start, g = 9, is at the top), a brass rim and a fixed pointer notch at the top. **Ammeter**: a brass bezel Ø 0.30, a cream dial Ø 0.24 (centre (0, 1.20, −0.028)) with ticks 0 … 10 over −55° … +55° from up (every 11°, major at 0, 5, 10) and the numerals 0 2 4 6 8 10. A pivot block and two **quadrant cheeks with stops** (OFF at 0°, ON at 50°) for the lever |
| `IA_feed` | `M_Brass_Aged` | 1,072 | **Origin = its axis (0, 0.50, 0.30)**, axis +Z. A hand wheel Ø 0.34 (rim tube 0.02, five spokes, hub) with a **handle pin at 12 o'clock** (stem + ball), identity = the start (g = 9). **Feed count w = 9 − g = −27° w about +Z** (clockwise = feeding in); the pin then points at the numeral g |
| `ammeter_needle` | `M_Bakelite` | 96 | **Origin = the dial centre (0, 1.20, −0.028)**. Identity = pointing **55° LEFT of up** (the cold stop); **value n = −11° n about +Z** (n = 10 points 55° right of up). A tapered needle (0.098 long, tail 0.026) and a hub cap, 4 mm thick above the dial |
| `ammeter_band` | `M_Paint_Green` | 52 | **Origin = the dial centre**. An arc segment r 0.082 … 0.097, ±4.5° (0.8 of a unit), **built at the needle's identity angle**: the code rotates it by **−11° × (10 − g_target) about +Z**, the same law as the needle (g_target = 4 → value 6) |
| `IA_sun_lever` | `M_Bakelite` | 336 | **Origin = the pivot (0.21, 0.99, 0.12)**. A lever arm with a swelling grip (0.315 long) on a pivot pin; **rest OFF = upright (+Y); ON = +50° about +X** (toward the player; the grip ends at z 0.39) |

`sun_pedestal` uses five slots (the contract listed four): the green band needs `M_Paint_Green`.

## Files and commands

`game/assets/models/{sun_lamp,sun_iris,sun_pedestal}.glb(+.import)`, `qa/blender/ch4/*.png`, `tools/blender/models/*.py`, `tools/blender/lib_ch4_cde.py`,
`tools/blender/build_lists/ch4_e.txt`. Rebuild: `tools/blender/build_all.sh`; re-import: `godot --headless --path game --import`.
