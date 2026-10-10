# Chapter 3 group E: Leyla's camp and the shutter (measured results)

Contract: `docs/models/ch3.md` §0, §1 (placement, hang points, the camp, portal cards, lights), §2 (views `camp`, `shutter`,
`recorder`), §7, §11 (E4 melody), §13, §14. Models: `leyla_camp`, `field_recorder`, `oscillograph`, `crystal_shutter`.
Scripts: `tools/blender/models/<name>.py`; shared helpers in `tools/blender/lib_ch3_ef.py` (on top of `lib_ch3_d.py`,
`lib_ch3_a.py` and the libraries they re-export; none of the older libraries were edited); build list
`tools/blender/build_lists/ch3_e.txt`.

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [--shots=1,2,...]
```

**Pipeline.** As group D: every script builds in Godot axes (the group-A "G-frame"), converts to Blender axes before
parenting, exports a lean GLB to `game/assets/models/<name>.glb`, then **re-reads the GLB** and checks the required node
names, parents, model-space positions (1 mm), identity rest rotations, mount rotations, triangles, surfaces and material
slots against §13, and runs `check_glb_names.py`. Renders: Cycles, 32 samples, 960 × 640, 2 threads, cameras from the §2
views, `shell_nursery.glb` (+ `shell_gallery.glb`, the blast doors and `array_below.glb` for the open-shutter shot) and the
neighbouring GLBs imported. Shader quads carry the seed-0 preview (`osc_screen.png`, `osc_screen_s3.png`); lamps and the
bulb get a QA-only emissive override. Blender renders only, never Godot screenshots.

All coordinates are **Godot, model-local, metres** (leyla_camp: world); models face +Z; angles follow §0.

## Summary

| Model | Tris (budget) | Surfaces (cap) | Slots | GLB | QA renders (`qa/blender/ch3/`) |
|---|---|---|---|---|---|
| `leyla_camp` | 8,134 (9,000) | 5 (6) | 4 | `game/assets/models/leyla_camp.glb` | `leyla_camp.png`, `_3`, `_4` |
| `field_recorder` | 2,459 (2,500) | 7 (7) | 4 | `game/assets/models/field_recorder.glb` | `field_recorder.png`, `_2`, `_3` |
| `oscillograph` | 1,674 (2,000) | 4 (4) | 4 | `game/assets/models/oscillograph.glb` | `oscillograph.png`, `_2` |
| `crystal_shutter` | 4,208 (5,000) | **12 (9)** | 3 | `game/assets/models/crystal_shutter.glb` | `crystal_shutter.png`, `_3` |

`check_glb_names.py` passes on all four. Surfaces = mesh nodes × primitives in the GLB (draw calls before shadows).

---

## leyla_camp.glb (8,134 tris, 5 surfaces)

**Room-coordinate model** (origin = world origin) inside the camp x 4.5 … 7.6, z −4.0 … −1.2, y 0 … 2.9. Bounds
(4.537, −0.014, −3.965) … (7.550, 2.900, −1.205): everything stays inside the walls of `shell_nursery.camp_walls`
(tile faces north z −3.965, west x 4.535; the south partition's inner face z −1.2). Origin of the mesh = (0, 0, 0).

| Node | Pivot / position | Materials | Notes |
|---|---|---|---|
| `leyla_camp` | (0, 0, 0) | Fabric, Wood_Panel, Steel_Dark, Paper | ONE static mesh with everything below |
| `camp_bulb` | (6.2, 2.55, −2.6) | Paper | the bare bulb (globe R 0.030 + neck), origin at its centre; **code: emission on** |
| `camp_light` | (6.2, 2.45, −2.6) | — | empty; the `camp_lamp` omni goes here |

**Contents (all in `leyla_camp`).**
- **Army cot** x 5.2 … 7.2, z −3.95 … −3.30, canvas at y 0.40 with a 3 cm sag: wooden rails and end bars, two crossed legs
  and a brace at each end, a rumpled sleeping bag (flattened sausage R 0.165), a pillow roll and a folded blanket at the foot.
  A **field coat** (body, skirt, sleeves, collar, two pockets with flaps, placket, four buttons) hangs on a peg board on
  the north wall over the cot's west end (x 5.55, y 0.98 … 1.97).
- **Rucksack** (body, flap, two side pockets, two straps with buckles, a bedroll with two bands) on a slatted crate in the
  north-west corner (x 4.65 … 5.10, z −3.92 … −3.57, crate top y 0.28).
- **Battery rig** in the north-east corner: a slatted crate x 7.00 … 7.55, z −3.20 … −2.50 (top y 0.30) with **three car
  batteries** (0.27 × 0.17 × 0.19: lid, three filler caps, two posts each, a strap), two jumpers, and **two supply cables**
  (R 0.0085) that run over the crate edge, across the floor to the table's east edge and end on the tabletop at
  (5.20, 0.748, −1.74) and (5.16, 0.748, −1.50), beside the oscillograph and the recorder.
- **Folding table** x 4.60 … 5.40, z −1.90 … −1.25, top y 0.74 (wooden top 0.026 thick, steel rim, two crossed steel leg
  pairs with feet, a stretcher rod at y 0.33). The contract's z range starts at −1.85: the oscillograph's rotated footprint
  reaches z −1.883, so the top is 5 cm longer.
- **Dressing:** a crate stack at x 7.15 … 7.55, z −2.35 … −1.95 (crate top y 0.30) carrying a thermos, a mug with a handle,
  four tape boxes in a leaning stack and a reel; a torch on the table's east end (x 5.30, z −1.47 …); a woven floor mat
  (x 5.55 … 7.00, z −3.26 … −2.62); **twelve blank sheets** with tacks pinned to the north (5), west (3) and south (4)
  walls; the ceiling rose, flex and bulb holder. No words or images.

**Clearances.** Nothing taller than 0.75 m stands in the sight lines of `camp` (7.25, 1.6, −1.5), `shutter` (6.55, 1.55, −2.6) or
`recorder` (5.3, 1.32, −2.55) (the coat and the pinned sheets hang on the walls; the bulb is above every frame); the door zone
x 5.5 … 6.7, z −1.9 … −1.2 is clear. The west wall's sheets keep z ≥ −1.95, clear of the shutter's architrave.

QA: `leyla_camp.png` (`camp` view, seal door open, recorder and oscillograph on the table, shutter closed), `_3` (hero: the
cot, the coat, the rucksack corner and the batteries from the table side), `_4` (the `shutter` view: the sight line is clear).

---

## field_recorder.glb (2,459 tris, 7 surfaces)

On the table at (4.95, 0.74, −1.45), yaw 180 (front faces north into the camp). Body 0.28 × 0.09 × 0.22 (z −0.11 … 0.11;
the deck block's top is y 0.088, the spindle nuts reach 0.1085); the two keys **overhang the front by 0.022** (z up to
0.132), as the contract's pivots (z 0.10) require.

| Node | Pivot / position | Materials | Notes |
|---|---|---|---|
| `field_recorder` | (0, 0, 0) | Leather, Chrome | static: leather-wrapped case with a key shelf and a notch under the keys; the chrome deck block with spindles, platters, nuts, head block, capstan, pinch roller, three tape guides; the riser front (z 0.075) with the VU window (leather face, chrome bezel, five chrome ticks) and two chrome knobs; a folding side handle; two front latches |
| `reel_l`, `reel_r` | (∓0.07, 0.095, −0.02) | Tape | 5-inch pancake reels (R 0.0635; a plain bottom flange, a top flange with three kidney windows, a wound pack R 0.050 on the hub); **spin about local +Y** (code); bounds y 0.093 … 0.1024 |
| `IA_rec_rewind` | (−0.03, 0.07, 0.10) | Bakelite | piano key 0.032 × 0.032 × 0.012, pivot at its back edge; **press = −8° about local +X** (the front dips 4.4 mm into the notch); raised ◀◀ (0.017 high, stretched 1.5 × along the key, 1.8 mm relief) |
| `IA_rec_play` | (0.02, 0.07, 0.10) | Bakelite | the same with ▶ |
| `rec_vu` | (0.092, 0.066, 0.0775) | Chrome | the VU needle (0.0185 long), pivot at its base on the riser face; **rest = the left stop, 35° counter-clockwise from vertical; the code swings it 0 … −70° about local +Z** |

**Materials per object** (the 7-surface cap): the body has two slots (Leather, Chrome); every moving part has one. The deck's
"leather" is the library's dark-brown `M_Leather`; there are no tape strands between the reels (they would need a fifth
primitive in the body).

QA: `field_recorder.png` (the `recorder` view: the scope in front, the recorder behind it with reels, keys and the VU window),
`_2` (hero from the front, play key pressed, needle at −40°), `_3` (the keys from above, close).

---

## oscillograph.glb (1,674 tris, 4 surfaces)

On the table at (4.97, 0.74, −1.72), yaw 135 (the screen faces north-east). Origin = the bottom centre. **Stepped case 0.20 w ×
0.15 h × 0.20 d** (z −0.05 … 0.15): a front block 0.15 high (z 0.085 … 0.15, the bakelite bezel with the screen window) and
a **low body 0.085 high** behind it with rounded rear corners (R 0.04) and five louvres on top; four bakelite knobs with
pointers on the bezel's right, a pilot jewel and a BNC-style socket on the left, rubber feet, a folded side handle.

| Node | Pivot / position | Materials | Notes |
|---|---|---|---|
| `oscillograph` | (0, 0, 0) | Steel_Cream, Bakelite, Glass_Dark | static |
| `osc_screen` | (0, 0.09, 0.151) | Shader_Quad | the CRT face 0.10 × 0.08, UV 0..1 (u → +X, v → +Y), `osc_wave.gdshader` |

The case is **smaller than the contract's 0.22 × 0.16 × 0.30** and stepped (deviation 1). Measured: from the `recorder` camera
(5.3, 1.32, −2.55) the sight lines to the recorder's keys clear the case by **16 mm** at the worst point (the script samples
200 points along both keys' rays against the footprint and heights; it fails below 10 mm).

QA: `oscillograph.png` (the `recorder` view, scope in front, keys visible behind it), `_2` (hero: the screen straight on with the
seed-0 size-3 waveform).

---

## crystal_shutter.glb (4,208 tris, 12 surfaces)

In the camp's west wall at (4.5, 0, −2.6), yaw 90. Frame 1.30 × 2.10, opening x −0.55 … 0.55, y 0.30 … 2.00; the architrave
stands 0.06 proud with rivets, the reveal lining holds the leaf slots (z −0.09 … −0.03), a threshold, a head channel, a kick
strip. Bounds (−0.65, 0, −0.14) … (0.65, 2.1, 0.135).

| Node | Pivot / position | Materials | Notes |
|---|---|---|---|
| `crystal_shutter` | (0, 0, 0) | Steel_Dark, Brass_Aged | static: architrave, apron with two ribs, reveal lining, threshold, head channel; brass kick strip, sill strip, the crystal bar (y 2.06, z 0.12, Ø 0.018) on two brackets with four hooks |
| `shutter_leaf_l` / `_r` | (∓0.28, 0.32, −0.06) | Steel_Dark | riveted leaves 0.56 × 1.72 × 0.06 with straps and a stile; **open = slide −0.58 / +0.58 along local X** into the wall pockets (leaves stay in z −0.09 … −0.0275) |
| `frame_mount_<p>` | (−0.42 + 0.28 p, 2.02, 0.12) | — | p = 0..3, hang points; world (4.62, 2.02, −2.18 … −3.02) |
| `IA_tcrystal_<s>` | at `frame_mount_<s−1>` (child, identity) | Brass_Aged, Crystal | s = 1..4: hexagonal crystal with pointed ends in a brass ferrule on a wire with an eye; body lengths 0.07 / 0.09 / 0.11 / 0.13, Ø 0.022 / 0.026 / 0.030 / 0.034, the body's top 0.08 below the hang point; origin = the top of the eye |
| `portal_shutter_k` | (0, 1.2, −1.55), rotation (0, 180, 0) | — | empty at world (2.95, 1.2, −2.6) |

QA: `crystal_shutter.png` (the `shutter` view, closed, crystals in the seed-0 order 3 4 2 1), `_3` (hero: the crystal bar and
the four crystals).

---

## Deviations from the contract and choices

1. **`oscillograph` is smaller and stepped** (0.20 × 0.15 × 0.20 instead of 0.22 × 0.16 × 0.30): at the contract's size and
   yaw 135 its back corner lies on the recorder's overhanging keys (0.27 m away), and the `recorder` camera looks over the
   scope at them. The first version (0.20 × 0.15 × 0.26 with a sloped top) still hid the keys in the render; the stepped body
   (0.085 behind the 0.15 front block) clears them by 16 mm. The screen quad is where the contract puts it.
2. **`crystal_shutter` has 12 surfaces, the cap is 9**: each `IA_tcrystal_<s>` has two primitives (a brass ferrule, wire and
   eye + the clear crystal), 4 × 2 + body 2 + leaves 2 = 12. A single material per crystal would have made the wire glass.
   The per-view budget (§13.3) is not at risk: the camp draws K only.
3. **`field_recorder` keys overhang** the body by 0.022 (contract pivots z 0.10, body to 0.11) and sit in a notch of the key
   shelf; the deck's top is y 0.088 (spindle nuts 0.1085), the contract's 0.09 height is the case + deck.
4. **`leyla_camp` table** is 0.65 × 0.80 (z −1.90 … −1.25) instead of z −1.85 …, to carry the oscillograph's rotated corner.
5. **`leyla_camp` bulb is `M_Paper`** (the camp's four slots are Fabric, Wood_Panel, Steel_Dark, Paper): the code's
   `ModelUtil.set_emission` duplicates the material per instance, so the paper sheets do not glow with it.
6. **Surfaces of `leyla_camp`**: 5 of 6 (body 4 + bulb 1).

## Notes for integration

- `camp_bulb`: emission on (warm white, ~7), and `camp_light` for the omni. The bulb is a separate node so only it glows.
- `field_recorder`: `reel_l` / `reel_r` spin about local +Y; `rec_vu` swings 0 … −70° about local +Z; keys press −8° about
  local +X (`IA_rec_rewind`, `IA_rec_play`). The scope must stay at yaw 135 and the recorder at yaw 180 (placement table).
- `crystal_shutter`: reparent `IA_tcrystal_<s>` to `frame_mount_<p>` from `v_frame` (identity); the QA shot `crystal_shutter_3.png`
  shows the hang. The leaves slide inside the wall slot only; do not move them in z.
