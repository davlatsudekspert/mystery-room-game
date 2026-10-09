# Chapter 3 group G: items (measured results)

Models: `key_diamond`, `key_triangle`, `key_circle`, `key_square`, `resonance_meter`, `ecg_strip`, `seed_crystal`,
`nursery_crystal` (also `cloudy_crystal`), `strand_fork` (finale prop). `strand_letters` reuses `letter.glb`.
Scripts: `tools/blender/models/<name>.py`; shared helpers in `tools/blender/lib_ch3_items.py` (the four keys are built by
`castell_key()` / `key_item()` there); build list `tools/blender/build_lists/ch3_g.txt`. Contract: `docs/models/ch3.md`
§0, §9 and §13; item rules in `docs/models/devices.md` "Inventory items" and `docs/models/ch2_items.md`.

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render]
blender -b --factory-startup -P tools/blender/models/items_lineup_ch3.py      # QA sheet only, exports nothing
```

Every script runs the Chapter 2 item pipeline (`lib_ch3_items.item_main`): build, finalize (box UVs, smoothing),
decal UVs, move the **centre of mass** to the origin (uniform density over the closed shells; the ECG strip, an
open paper sheet, is weighed by area), export `game/assets/models/<name>.glb`, then print the size, bottom and
tris in Godot axes, check the required parts (own objects, identity rotation), re-read the exported GLB and
check its tris, surfaces and material slots against §13, run `check_glb_names.py` on it and run the
**back-face check** (14 orthographic views with a red back-face override). Every item measured **0.00 %** red
in its worst view, and `check_glb_names` passes on all nine GLBs. Every material slot used has a `.tres` in
`game/assets/materials/` (`M_Decal_EcgPaper` is group A's).

All coordinates are **Godot, model-local, metres**. The root mesh node is at identity, so scene origin = node
origin = centre of mass. To rest an item on a surface at height h, put its origin at **h − bottom**.
Flat items lie flat, hero face up (+Y), their top edge toward −Z (`ItemDB.FLAT` already lists the four keys and
`ecg_strip`; the inspect tilt is 70° about +X). Standing items face +Z.

## Summary

| File | Tris (budget) | Surfaces | Materials | Size (x × y × z) | Natural pose | Bottom (y) |
|---|---|---|---|---|---|---|
| `key_diamond.glb` | 694 (1,200) | 2 | `M_Brass_Aged`, `M_Steel_Dark` | 0.0340 × 0.0144 × 0.0850 | Flat, bow toward −Z, blade toward +Z, bit out to +X | −0.0072 |
| `key_triangle.glb` | 649 (1,200) | 2 | same | 0.0340 × 0.0144 × 0.0850 | same | −0.0072 |
| `key_circle.glb` | 1,138 (1,200) | 2 | same | 0.0340 × 0.0144 × 0.0850 | same | −0.0072 |
| `key_square.glb` | 694 (1,200) | 2 | same | 0.0340 × 0.0144 × 0.0850 | same | −0.0072 |
| `resonance_meter.glb` | 2,447 (2,500) | **4** | **3**: `M_Bakelite`, `M_Enamel_Cream`, `M_Brass_Aged` | 0.0850 × 0.2129 × 0.0478 | Upright, face +Z, probe up | −0.0756 |
| `ecg_strip.glb` | 348 (400) | 2 | `M_Paper`, `M_Decal_EcgPaper` | 0.3200 × 0.0122 × 0.0500 | Flat, face up, bracketed edge toward −Z | −0.0041 |
| `seed_crystal.glb` | 562 (800) | 2 | `M_Crystal`, `M_Brass_Aged` | 0.0152 × 0.0244 × 0.0152 | Upright, a prism face toward +Z | −0.0088 |
| `nursery_crystal.glb` | 642 (1,500) | 2 | `M_Crystal`, `M_Brass_Aged` | 0.0448 × 0.1144 × 0.0407 | Upright, tip up, a prism face toward +Z | −0.0569 |
| `strand_fork.glb` | 1,030 (1,200) | 2 | `M_Chrome`, `M_Brass_Aged` | 0.0280 × 0.2400 × 0.0293 | Upright, stem down, tines up, U and mark face +Z | −0.0771 |

---

## The four isolator keys (`key_diamond`, `key_triangle`, `key_circle`, `key_square`)

**Shape:** one Castell-style blank, 85 mm from the bow top to the blade tip. The bow is a 3 mm brass plate shaped
as the symbol from `lib_ch3_symbols.shapes()` (◆ a square turned 45°, ▲ equilateral point up, ● a disc, ■ a
square), corners rounded 2.6–3 mm and then rescaled so **every bow is 34 mm across**; the same symbol is embossed
0.8 mm on the hero face (◆ 14 mm, ▲ 11 mm on the bow's incircle centre, ● and ■ 15 mm), and a Ø 3.2 mm hanging hole
is pierced near the bow top. Below it: a turned neck (Ø 9 mm), a collar (Ø 14.4 mm), the round brass shank
(Ø 12 mm) with a chamfered tip, and a flat dark-steel bit (2.4 mm) with two code cuts along the shank's last 22 mm,
sticking out 6.8 mm to +X.

| Part | Node origin | Notes |
|---|---|---|
| `key_<shape>` (root) | (0, 0, 0) | Bow, emboss, neck, collar, shank (`M_Brass_Aged`) |
| `key_bit` | see below | The steel bit (`M_Steel_Dark`), static |

**Mount points** (centre of mass at the origin). "Hanging" = the §4/§5 key mounts' basis **+90° about +X**
(blade down, bow up, bow face +Z), which maps (x, y, z) → (x, −z, y):

| Key | Hole centre: natural / hanging | Collar's blade-side face (stops on a lock face): natural / hanging | Blade tip: natural / hanging |
|---|---|---|---|
| ◆ | (0, 0, −0.0424) / (0, +0.0424, 0) | z −0.0084 / y +0.0084 | z +0.0356 / y −0.0356 |
| ▲ | (0, 0, −0.0409) / (0, +0.0409, 0) | z −0.0121 / y +0.0121 | z +0.0356 / y −0.0356 |
| ● | (0, 0, −0.0410) / (0, +0.0410, 0) | z −0.0055 / y +0.0055 | z +0.0385 / y −0.0385 |
| ■ | (0, 0, −0.0387) / (0, +0.0387, 0) | z −0.0032 / y +0.0032 | z +0.0408 / y −0.0408 |

x of every point is −0.0003 to −0.0004 (the bit's mass). For a key that **stands in a slot** (`lock_key_mount`,
`office_key_mount`, the lift's `gate_key_mount_*`), put the mount where the collar face should rest and offset
the key by the collar value, e.g. ◆ stands 0.0084 above its collar face. For a key that **hangs on a pin or hook**
(`held_key_mount`, `desk_hook_mount`), the pin goes through the hole: the hole centre is 0.0387–0.0424 above the
origin, and the hole is Ø 3.2 mm.

## resonance_meter.glb (2,447 tris, 4 surfaces, 3 materials)

**Shape:** black Bakelite case 85 × 150 × 40 mm (rounded). Upper front: a brass bezel (Ø 71 mm) round a cream
enamel dial with a scale arc, 7 major and 6 minor ticks and **3D numerals 1–7** on the reading angles, a brass
rest-stop pin just left of the rest position and a brass pivot cap. Below: a brass push button and Strand's mark
(`lib_ch3_symbols` "mark") inlaid in brass, four brass screws. On top: a brass ferrule and probe rod ending in a
small tuning fork. A leather wrist strap runs through a brass ring at the bottom left corner and lies folded
flat against the back, so the meter stands on its base.

| Part | Pivot (Godot) | Axis | Rest → active |
|---|---|---|---|
| `needle` | (+0.0001, +0.0105, +0.0203) | local **+Z** | Identity points at **polar 142.5°** (counter-clockwise from +X as the player sees the face), the left stop. Reading r = **−15° × r** about local +Z: r = 1 → 127.5°, r = 4 → 82.5°, r = 7 → 37.5°. Numeral r sits on that angle. QA `_2` (r = 4) and `_3` (r = 7) |
| `probe_tip` (empty) | (+0.0001, +0.1373, −0.0002) | — | Between the probe fork's tine tips |
| `resonance_meter` (root) | (0, 0, 0) | — | Case, dial, fittings, strap (static) |

**In the meter case** (`meter_mount`, basis −90° about +X: face up, top toward −Z): the back of the case is
**0.0239** below the origin, so the mount sits 0.0239 above the velvet.

## ecg_strip.glb (348 tris)

**Shape:** ECG chart paper 320 × 50 mm, 0.2 mm, still curled from the roll (both ends lift 12 mm), with a Ø 3 mm
clip hole at the centre of its top (bracketed) edge.

| Part | Node origin (Godot) | Notes |
|---|---|---|
| `ecg_strip` (root) | (0, 0, 0) | The back and the cut edges (`M_Paper`) |
| `strip_face` | (0, −0.0041, 0) | The printed face, own object. **UV 0..1 over the full 320 × 50 rectangle**: u left → right along the trace (☼ ☾ ✦), v from the bottom edge (0) to the bracketed top edge (1), never mirrored. Slot `M_Decal_EcgPaper`; `ItemDress` puts the trace shader on it. The clip hole is cut through it at **u 0.4953–0.5047, v 0.914–0.974** (centre u 0.5, v 0.944): `ecg_paper.png` keeps that spot clear (its ☾ ends at v ≈ 0.88) |

Clip hole centre: natural (0, −0.0039, −0.0222); at `ecg_mount` (basis +90° about +X: face toward +Z, top edge
up) it is at (0, +0.0222, −0.0039) from the mount, and the strip's top edge is 0.025 above the mount.

## seed_crystal.glb (562 tris)

A clear hexagonal crystal (Ø 12 mm across its corners, 20 mm long with a slightly off-centre point, the six columns
a little uneven), set in a turned brass **seed collar** (Ø 15.2 mm, 6.5 mm high, a bead and a lip; the crystal sits
in its 4.8 mm deep recess). Root `seed_crystal` = the crystal (`M_Crystal`), child `seed_collar` (`M_Brass_Aged`),
both static. Collar bottom y = −0.0088, collar top −0.0023, crystal point +0.0156.

## nursery_crystal.glb (642 tris) — also `cloudy_crystal`

A clear hexagonal crystal Ø 45 mm × 110 mm: the lower end tapers into the **same seed collar** (Ø 15.2 mm, the
foot), a long prism, an uneven rhombohedral point, and two small satellite crystals grown on the taper.

| Part | Node origin (Godot) | Notes |
|---|---|---|
| `nursery_crystal` (root) | (0, 0, 0) | The brass foot (seed collar), `M_Brass_Aged` |
| `crystal_body` | **(+0.0002, −0.0525, 0)** | Everything clear (`M_Crystal`), own object, identity. Its pivot is the centre of the crystal's base on the collar's seat: **scale crystal_body 0.15 → 1 about its own origin** and it grows out of the collar (at 0.15 it is a 6.7 × 16.5 mm crystal, the size of the seed). `ItemDress` swaps this object's material for `cloudy_crystal` |

Bottom (collar underside) y = **−0.0569**, top (apex) +0.0575. crystal_body alone: 0.110 high, 0.0448 × 0.0407.

## strand_fork.glb (1,030 tris)

Strand's polished steel tuning fork (`M_Chrome`), 240 mm overall: two tines 6 × 5.5 mm with a 7.5 mm gap on a U
yoke, a round turned stem Ø 7.6 mm, and a heavy brass ball foot (`M_Brass_Aged`, Ø 28 mm, a small flat to stand
on) with a flat medallion on its front carrying **Strand's mark** (ring + meridian) in polished steel. One root
object `strand_fork` (static).

The ball's weight puts the **centre of mass on the stem**: the round stem spans y **−0.0497 … +0.0379**, the origin
is in it, so a fist closed round the stem at the origin holds the fork (`echo_strand_rail` `fork_mount`, identity:
see `ch3_h.md`). Bottom (ball underside) y = −0.0771, tine tops +0.1629. At `choice_mount` it stands on its ball:
put the mount 0.0771 above the socket floor.

## QA renders (`qa/blender/ch3/`)

| Model | Renders |
|---|---|
| keys | `item_key_<shape>.png` (hero), `_2` (inspect view: 70° tilt) |
| resonance_meter | `item_resonance_meter.png` (hero), `_2` (dial, reading 4), `_3` (reading 7), `_4` (back: strap, probe) |
| ecg_strip | `item_ecg_strip.png` (hero, with group A's `ecg_paper.png`), `_2` (inspect view) |
| seed_crystal | `item_seed_crystal.png` (hero), `_2` (front) |
| nursery_crystal | `item_nursery_crystal.png` (hero), `_2` (front), `_3` (crystal_body at scale 0.15: the growth start) |
| strand_fork | `item_strand_fork.png` (hero), `_2` (the ball foot and the mark) |
| all | `items_ch3.png`: every item at its natural pose on a walnut table (the meter reads 4) |

## Deviations from the contract and choices

- **`resonance_meter` has 3 materials and 4 surfaces** (§13 caps items at 2 materials / 3 surfaces). A cream dial
  with black numerals and a needle, a black case and brass fittings need three slots; the needle must be its own
  object. Smallest version: `M_Bakelite` (case, numerals, ticks, needle, strap), `M_Enamel_Cream` (dial),
  `M_Brass_Aged` (bezel, cap, pin, button, mark, screws, probe, ring); no glass over the dial; the strap is
  black (`M_Bakelite`) rather than a fourth leather slot.
- **Every key has a Ø 3.2 mm hanging hole** near the bow top: the cabinet's `held_key_mount` ("hangs on a pin") and
  the desk's `desk_hook_mount` ("hangs by its bow") need something to hang from. It is inside the outline, so the
  silhouette stays the cue.
- **Bow size:** "34 mm across" is read as the width for all four bows (◆ therefore has 34 mm diagonals, ▲ a 34 mm
  side and 30.2 mm height); rounded corners are compensated so the width stays 34 mm.
- **The ECG clip hole** sits 2.8 mm below the top edge (the contract only says "top edge centre"), in the clear band
  above the ☾ of `ecg_paper.png`.
- **`strand_fork` origin:** the centre of mass, as for items; the heavy ball foot was sized so that it falls on the
  stem, which is what the echo's fist and `fork_mount` need.
- **`nursery_crystal` foot** is exactly the seed collar of `seed_crystal` (shared `lib_ch3_items.seed_collar`).

## Notes for the game code

- `ItemDB`: no change needed. `FLAT` already holds the four keys and `ecg_strip`; the meter, the seed and the
  crystals stand. `cloudy_crystal` → `nursery_crystal` with `crystal_body`'s material swapped.
- Growth: scale `crystal_body` (not the item root) from 0.15 to 1; its pivot is already at the crystal's base.
- The meter's needle angle for reading r is `rest.basis * Basis(Vector3.BACK, deg_to_rad(-15.0 * r))`.
