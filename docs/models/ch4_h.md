# Chapter 4 group H: the items (measured results)

Contract: `docs/models/ch4.md` §9 and §11 (item rules of `docs/models/ch3.md` §9: real size, origin at the centre of mass, flat items hero face +Y with the top edge toward −Z, standing items face +Z).
Models: `tower_key_1..4`, `strand_log`, `pocket_watch`, `strand_last_letter`, `reverse_pawl`, `leyla_note_1998`, `leyla_parcel`. Existing: `crystal_lens`, `key_strand`, `key_leyla` (unchanged).
Scripts: `tools/blender/models/<name>.py`; the shared builders are in `tools/blender/lib_ch4_items.py` (the four tower keys; it sets the soft QA light rig and the output folder) on top of
`lib_ch3_items.py` / `lib_ch2_items.py` (the item pipeline: build, finalize, move the centre of mass to the origin, export, re-read and check the budget, back-face check) and `lib_ch4_mark.py` (the mark as two
solids); build list `tools/blender/build_lists/ch4_h.txt`. QA renders: `qa/blender/ch4/item_<name>.png` and `_2` (a hero view and the inventory's inspect view: flat items tilted 70°), the icon
candidates `icon_<name>.png` (330 px, from the exported GLBs) and the sheets `items_ch4_icons_330.png` / **`items_ch4_icons_110.png`** (the same ten at the 110 px icon size).

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render]
blender -b --factory-startup -P tools/blender/models/items_lineup_ch4.py      # the icon renders (QA only, needs the exported GLBs)
```

## Summary

| Item | Tris (budget) | Surfaces (cap) | Slots | Pose | Size (m, Godot x y z) | Bottom | What | Extra nodes |
|---|---|---|---|---|---|---|---|---|
| `tower_key_1` | 750 (1,200) | 2 (3) | 2 | flat, bow −Z | 0.036 x 0.014 x 0.098 | bottom y -0.0070 | numeral I | `key_bit` (steel bit + numeral plaque) |
| `tower_key_2` | 824 (1,200) | 2 (3) | 2 | flat, bow −Z | 0.036 x 0.014 x 0.098 | bottom y -0.0070 | numeral II | `key_bit` (steel bit + numeral plaque) |
| `tower_key_3` | 890 (1,200) | 2 (3) | 2 | flat, bow −Z | 0.036 x 0.015 x 0.098 | bottom y -0.0080 | numeral III | `key_bit` (steel bit + numeral plaque) |
| `tower_key_4` | 799 (1,200) | 2 (3) | 2 | flat, bow −Z | 0.036 x 0.015 x 0.098 | bottom y -0.0080 | numeral IV | `key_bit` (steel bit + numeral plaque) |
| `strand_log` | 1,898 (2,600) | 3 (3) | 3 | flat, spine −X | 0.144 x 0.028 x 0.234 | bottom y -0.0140 | leather logbook | — |
| `pocket_watch` | 1,814 (2,600) | 2 (3) | 2 | standing, face +Z | 0.054 x 0.092 x 0.015 | bottom y -0.0270 | hunter-case watch | — |
| `strand_last_letter` | 854 (1,800) | 2 (3) | 2 | flat | 0.122 x 0.008 x 0.086 | bottom y -0.0020 | sealed folded letter | `ribbon` (ribbon + seal, crimson) |
| `reverse_pawl` | 1,368 (1,800) | 2 (3) | 2 | flat, hook +X | 0.094 x 0.010 x 0.041 | bottom y -0.0034 | brass pawl | `spring` (steel) |
| `leyla_note_1998` | 607 (1,800) | 2 (3) | 2 | flat | 0.093 x 0.002 x 0.142 | bottom y -0.0010 | folded note | `ink` (sign, 1998, lines) |
| `leyla_parcel` | 1,116 (2,600) | 3 (3) | 3 | flat | 0.205 x 0.091 x 0.126 | bottom y -0.0432 | kraft parcel | `twine` (twine + tag), `ink` (flask, 7) |

`check_glb_names.py` passes on all ten; every item passes the back-face check (the worst view of each is under 0.5 % red; `leyla_note_1998` shows its zero-thickness ink from below, which is never seen).
**`strand_log` and `leyla_parcel` use three slots** (leather / paper / brass; kraft / paper / ink): the documented exception to "≤ 2 materials", still 3 surfaces.

**Hero quality at 110 px** (`items_ch4_icons_110.png`): every item reads at the inventory's icon size. The tower keys are a **tower-shaped bow with a dark steel plaque and the numeral I … IV in brass relief** (the numeral is the only
difference at that size, plus the bit's code cuts); the log has the mark ringed in brass on dark leather; the watch is the only standing item with a chain; the letter is the only red-ribboned one; the pawl the only
dark-hooked brass arm; the note the only cream paper with the crescent; the parcel the only brown one with twine.

## Decisions the scene agent must know

- **`ItemDB` (`game/src/core/item_db.gd`) maps `tower_key_1..4` to a model called `tower_key`: there is no such file.** The four keys are `tower_key_1.glb` … `tower_key_4.glb` (the numeral is in the geometry); set `"model": "tower_key_n"` per id.
- `strand_last_letter` and `leyla_note_1998` currently point at `letter`: they have their own models now (`"model": "strand_last_letter"`, `"model": "leyla_note_1998"`); `letter.glb` stays Strand's Chapter 2 envelope.
- **`FLAT` lacks `reverse_pawl` and `leyla_parcel`** (both lie flat: hero face +Y; without the 70° inspect tilt they are seen edge-on); `pocket_watch` is the only standing item (face +Z), as listed.
- **Mounts.** Flat items go on identity mounts (`log_mount`, `letter_mount`, `pawl_item_mount`, `note_mount`; `parcel_mount` has its own yaw 90°). **`pocket_watch` is a standing item: on the heart drawer's velvet pad (`watch_mount`, identity, items lie flat) turn it by Euler (−90°, 0, 0)**
  (its face +Z → up, its pendant +Y → −Z), and lift it by its half thickness (0.0077) above the pad top. The tower keys sit in the gate locks at `gate_key_mount_n` (bow outward, as `ch4_d.md`).
- The inspect view: flat items are tilted 70° about +X; the 0.1 m keys and the 0.23 m log fill the same icon because the viewer scales to the bounding sphere.

## The items

| Item | Notes |
|---|---|
| `tower_key_n` | A Castell-style brass key 0.036 x 0.014 x 0.098: a 3.2 mm bow shaped like a **crenellated tower** (three merlons, a hanging eye Ø 3.8 mm), a raised **dark steel plaque** (0.029 x 0.0215) with the **Roman numeral I … IV** in 1.3 mm brass relief (15 mm high; the same glyphs as `mirror_tower`'s numeral plate), a thin brass band under the merlons, a turned neck and collar, a round brass shank Ø 12 mm with a chamfered tip and a flat steel bit of six slots whose cuts differ per key (I `010000`, II `010100`, III `101010`, IV `110101`). The root node is the brass; `key_bit` (steel: bit + plaque) is its child |
| `strand_log` | Dark leather boards 0.140 x 0.200, a rounded spine (radius 12.5 mm) with **four raised bands**, brass triangular corner pieces with rivets, a brass frame line, **Strand's mark in brass relief** (ring + meridian, 80 mm, a bold 1.9 x) on the front, a brass clasp tab with a keyhole plate on the fore-edge and a wrap strap, a cream page block whose three open edges are ridged (nine page lines each), a leather ribbon trailing from the tail. The spine is on the left, the head toward −Z |
| `pocket_watch` | A closed (hunter) brass case Ø 0.050 x 0.015 with a **reeded edge**, a stepped bezel, a flat lid with two engraved rings and **the Institute's mark in polished brass**, two hinge knuckles on the left, a pendant with a **fluted crown**, a bow ring and the first chain link. Standing, face +Z, the pendant up; origin at the centre of mass (the case centre is about 2 mm below it) |
| `strand_last_letter` | A cream letter folded in thirds (three loose leaves, a little turned), a **crimson ribbon** 8 mm wide round it lengthwise and a **poured crimson wax seal** Ø 0.026 with the mark in relief. No words. The root is the paper, `ribbon` is the ribbon + the seal |
| `reverse_pawl` | A brass ratchet pawl 0.093 long: a tapered arm, a **barbed hook cut the wrong way round** at +X, a turned pivot boss with a through hole, an arrow engraved along the arm pointing back toward the pivot, two rivets and a small steel return spring on a post (`spring`). It lies on the chronometer's pawl seat with the boss over the post |
| `leyla_note_1998` | A cream sheet (0.090 x 0.120) folded: the top third turned down, a torn left edge, a dog-eared corner, creases; in ink (`ink`, `M_Bakelite`): **Leyla's sign** (the crescent opening right and three dots), **1998** in her handwriting, four lines of unreadable scribble and a rule. Flat, the crease edge toward −Z |
| `leyla_parcel` | A parcel in brown kraft paper 0.20 x 0.12 x 0.08 with soft corners, a seam along the top, the envelope folds on both ends, **cream twine in two loops** crossing in a **bow** on the top (`twine`) and a **tag** hanging from the knot, with the **laboratory flask** (the Chapter 2 pictogram) and the number **7** in ink (`ink`): the address of the post dial. Flat on its large face |

## Files and commands

`game/assets/models/{tower_key_1..4,strand_log,pocket_watch,strand_last_letter,reverse_pawl,leyla_note_1998,leyla_parcel}.glb(+.import)`, `qa/blender/ch4/item_*.png`, `qa/blender/ch4/icon_*.png`, `qa/blender/ch4/items_ch4_icons_*.png`,
`tools/blender/models/*.py`, `tools/blender/lib_ch4_items.py`, `tools/blender/lib_ch4_mark.py`, `tools/blender/build_lists/ch4_h.txt`. Rebuild: `tools/blender/build_all.sh`; re-import: `godot --headless --path game --import`.
