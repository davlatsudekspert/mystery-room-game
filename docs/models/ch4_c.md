# Chapter 4 group C: the Array (measured results)

Contract: `docs/models/ch4.md` §0, §1, §2, §5, §11, §12. Models: `ring_rails`, `array_rings`, `mirror_tower`, `beam_segment`.
Scripts: `tools/blender/models/<name>.py`; helpers in `tools/blender/lib_ch4_cde.py` (new, additive: bmesh primitives, `toothed_ring`, QA helpers) on
top of `lib_ch4.py` and `lib_ch4_numerals.py`; build list `tools/blender/build_lists/ch4_c.txt`. Same pipeline and QA scene as groups A and B
(`ch4_a.md`, `ch4_b.md`): G-frame build, lean GLB, re-read and verify against §11, Cycles 24 samples 960 × 640, `shell_hall` + `bridge` + `catwalk` +
`shell_lift4` imported, the §1.5 lights as QA lights. Blender renders only.

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [--shots=1,2,3]
```

## Summary

| Model | Tris (budget) | Surfaces (cap) | Slots | GLB | QA renders (`qa/blender/ch4/`) |
|---|---|---|---|---|---|
| `ring_rails` | 5,207 (6,000) | 2 (2) | 2 | `game/assets/models/ring_rails.glb` | `ring_rails.png`, `_2` |
| `array_rings` | 11,984 (14,000) | 4 (4) | 1 | `game/assets/models/array_rings.glb` | `array_rings.png`, `_2`, `_3` |
| `mirror_tower` (×4) | 2,841 (4,000) | **8 in the file, 5 drawn** (3, see below) | 2 | `game/assets/models/mirror_tower.glb` | `mirror_tower.png`, `_2`, `_3` |
| `beam_segment` (≤ 5) | 8 (100) | 1 (1) | 1 | `game/assets/models/beam_segment.glb` | `beam_segment.png`, `_2` |

`check_glb_names.py` passes on all four GLBs. `floor_mark` (×8) of the design brief is **not built**: contract §13.4 moved the floor marks into `shell_hall`
(`hall_brass`: eight radial lines and the numerals 1–8 at r = 12.4).

## ring_rails.glb (5,207 tris, 2 surfaces)

One node `ring_rails`, origin (0, 0, 0) = the hall axis at floor level, identity. Bounds x ±11.019, y 0 … 0.14, z −11.019 … 11.500. Two surfaces:
`M_Steel_Dark` (the tracks, the sleepers, the clips) and `M_Brass_Aged` (the guide grooves and the numerals).

| Part | Numbers |
|---|---|
| Track (steel) | Four polygon rings at r = 10.5 / 8.5 / 6.5 / 4.5 with 64 / 48 / 40 / 32 segments (chord sag ≤ 24 mm, hidden under the ring's 0.8 beam). Section r ± 0.45, y 0 … 0.12, the edges chamfered (0.45 at y 0.08 → 0.39 at y 0.12) |
| Sleepers (steel) | 32 per track every 11.25° (offset 5.625°, so none stands on a mark azimuth): 1.12 radial × 0.24 tangential × 0.07 high; they stand 0.11 out of the band on both sides |
| Clips (steel) | A 0.07 × 0.07 clip block on every sleeper's outer end, y 0.07 … 0.14 |
| Guide groove (brass) | An inlaid strip 0.06 wide at each radius, y 0.1215 (hidden under the ring, shows when a ring is lifted or seen from a hatch with the ring turned away) |
| Numerals I … IV (brass) | `lib_ch4_numerals` glyphs 0.46 high, relief 0.022, lying on the floor, read from the south (top toward the Core), at radius r + 0.86 on the west side of the catwalk (x ≈ −1.5, between the catwalk's west rail and the wall) |

Notes for the scene: nothing moves; draw it with the R group. The trestles of `catwalk` (z = 11.4, 9.5, 7.5, 5.5) stand in the gaps between the tracks.

## array_rings.glb (11,984 tris, 4 surfaces)

Four nodes, one mesh object and one surface (`M_Steel_Dark`) each, **origin (0, 0, 0) = the hall axis, identity at position 0** — rotate the node about +Y:
**position p = −45° × p about +Y**. Each carries its child empty `tower_mount_n` at (0, 0.5, r_n), identity (the code parents the `mirror_tower` instance there).

| Node | r | Teeth (pitch) | Tris | Bounds y | `tower_mount` |
|---|---|---|---|---|---|
| `ring_1` | 10.5 | 96 (0.687 m) | 4,232 | 0.12 … 0.522 | (0, 0.5, 10.5) |
| `ring_2` | 8.5 | 80 (0.668 m) | 3,496 | 0.12 … 0.522 | (0, 0.5, 8.5) |
| `ring_3` | 6.5 | 56 (0.729 m) | 2,470 | 0.12 … 0.522 | (0, 0.5, 6.5) |
| `ring_4` | 4.5 | 40 (0.707 m) | 1,786 | 0.12 … 0.522 | (0, 0.5, 4.5) |

Geometry (per ring, radii measured from the ring's r): the beam spans −0.40 … +0.385 (0.785 wide), y 0.12 … 0.50.
- **Rack**: trapezoid teeth on the outer edge (root +0.30, tip +0.385, the root 0.56 and the tip 0.34 of the pitch wide) over y 0.12 … 0.40, then a stepped
  rim (+0.26, y 0.40 … 0.46) with a 4 cm chamfer to the flat top at y 0.50.
- **Inner side**: the top runs from +0.23 to −0.34, a chamfer, then a wall at −0.40 with two machined grooves (y 0.30 and 0.38).
- **Eight index notches** per ring, 0.20 wide, **0.27 deep**, full height, cut into the gaps at azimuths 0°, 45°, … 315° (the position azimuths: the
  slot floor is the inner ring at r + 0.03). An **arrow pad** (a raised triangle 0.30 long, 0.022 high) on the top points at every notch.
- Rivets: one row on the rim top every other tooth, a second row on the inner top every fourth tooth.
- The ring is built as an inner ring plus eight 45° outer segments (no booleans, no bottom face): it is not watertight underneath, which is never visible.

Notes for the scene:
- **Shadows**: the rings are the main shadow casters of the R group (they stand 0.5 high).
- A tower stands over the notch at its ring's mark 1 azimuth (180° at rest): the plinth is 0.7 wide and bridges the slot.
- The rings sit exactly on the tracks of `ring_rails` (y 0.12).

## mirror_tower.glb (2,841 tris, 8 surfaces in the file, 5 drawn)

Instanced four times at `tower_mount_1..4`. Origin = the plinth base centre on the ring top, front (+Z) radially outward at rest.

| Node | Material(s) | Tris | Pivot / notes |
|---|---|---|---|
| `tower_body` | `M_Brass_Aged` | 1,246 | Stepped plinth 0.70 × 0.70 × 0.18 with four corner bolts; the key shelf on the +Z side of the top (tray, a lip, two clips); the turned post Ø 0.12 (flared foot, two collars) from y 0.18 to 1.17; the numeral plate 0.30 × 0.26 on the post's +Z face (centre (0, 0.58, 0.06)) with two bolts. Bounds ±0.35, y 0 … 1.17 |
| `tower_head` | `M_Brass_Aged` + `M_Chrome` | 812 | **Origin (0, 1.30, 0)** = the post top / the mirror centre (world y 1.80 on a ring), identity at rest; yaw it about +Y. A brass hub on the post, a cross bar, two arms and trunnions, a brass bezel and back plate round a **chrome disc Ø 0.185 whose face looks up and +Z (normal (0, 0.707, 0.707))**. Bounds x ±0.17, y 1.17 … 1.40, z ±0.087 |
| `tower_numeral_1..4` | `M_Chrome` | 36 … 91 | Four own objects, **origin = the plate centre (0, 0.58, 0.075)**: the numeral I / II / III / IV in 0.014 relief, 0.17 high. The code shows ONE of the four |
| `IA_key` | `M_Brass_Aged` | 344 | **Origin (0, 0.19, 0.24)**: a key lying in the bracket, bow toward −Z (the post), shaft 0.20 long toward +Z, bits on the +X side. The tap is `take("tower_n")` |
| `beam_point` | empty | — | (0, 1.30, 0), the mirror centre |

**Surface count.** The contract says ≤ 3 surfaces, but its own parts list (body, head, key, four numeral variants) cannot be drawn in 3: the file holds 8
surfaces (body 1, head 2, key 1, numerals 4) and **5 are drawn per tower** (body, head brass + chrome, key, the one shown numeral; 4 after the key is taken)
= 20 for the four towers (the plan counted 12). If the `bridge` view is over its budget: hide `IA_key` and the numeral beyond 10 m (the towers are under the
catwalk and mostly seen through the hatches), then merge the head into one material (swap the yoke to `M_Chrome`: 1 surface).

Notes for the scene:
- **Hatch camera**: the key at z + 0.24 is hidden by the south coaming from the proposed `hatch_n` camera (z + 0.55). From **z + 0.35** (or nearer to the
  opening's centre) the key, the shelf and the post are in view (`mirror_tower.png`, which keeps the contract camera, shows the head, the post and the opening).
- The towers are under the catwalk deck (y 2.5) and the heads at y 1.8–1.95: they are seen through the open hatch lids and from the sides, not from above the deck.
- The chrome mirror reads black without a bright environment: give it a reflection probe or a rim light (the QA renders show it dark).

## beam_segment.glb (8 tris, 1 surface)

`beam_segment`, `M_Emissive_Lumen`, origin (0, 0, 0) = the start of the ribbon, identity. A unit ribbon along **+Z (z 0 … 1)** made of **two crossed quads
0.22 wide** (one horizontal, one vertical, crossing on the axis), each quad present with both faces (8 tris) so it shows from every side under back-face culling.
**UV 0..1**: u across the width, v along the length, so a soft-edged shader can replace the material. Scale Z by the segment length, aim +Z along the segment.
Bounds ±0.11, ±0.11, 0 … 1.

## Files and commands

`game/assets/models/{ring_rails,array_rings,mirror_tower,beam_segment}.glb(+.import)`, `qa/blender/ch4/*.png`, `tools/blender/models/*.py`,
`tools/blender/lib_ch4_cde.py`, `tools/blender/build_lists/ch4_c.txt`. Rebuild: `tools/blender/build_all.sh`; re-import: `godot --headless --path game --import`.
