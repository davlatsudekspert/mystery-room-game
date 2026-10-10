# Chapter 4 group G: the watch room (measured results)

Contract: `docs/models/ch4.md` §0, §1, §2, §8, §11, §12. Models: `watch_room`, `roll_board`, `lockers4` (the contract's `lockers`), `post_station4`.
Scripts: `tools/blender/models/<name>.py`; helpers in `tools/blender/lib_ch4_fgh.py` (the `MB` mesh builder, prisms, the six Chapter 2 pictogram outlines, the shell and back-face checks) and
`tools/blender/lib_ch4_mark.py` (the Institute's mark as two solids), on top of `lib_ch4.py`, `lib_ch4_cde.py` and `lib_ch4_numerals.py`; build list `tools/blender/build_lists/ch4_g.txt`.
Same pipeline as groups A–F (G-frame build, lean GLB, re-read and verify against §11, Cycles 24 samples 960 x 640). QA scenes: the hall shell with `watch_room` and the three fixtures
at their mounts (`watch_room`), and a plain wall and floor with soft point lights for the fixtures. Blender renders only.

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [--shots=1,2,...]
```

## Summary

| Model | Tris (budget) | Surfaces (cap) | Slots | GLB | QA renders (`qa/blender/ch4/`) |
|---|---|---|---|---|---|
| `watch_room` | 4,299 (8,000) | 5 (9) | 4 | `game/assets/models/watch_room.glb` | `watch_room.png`, `_2`, `_3` |
| `roll_board` | 3,868 (5,000) | 4 (5) | 4 | `game/assets/models/roll_board.glb` | `roll_board.png`, `_2` |
| `lockers4` | 4,812 (6,000) | 5 (8) | 2 | `game/assets/models/lockers4.glb` | `lockers4.png`, `_2` |
| `post_station4` | 7,019 (8,000) | 7 (12) | 4 | `game/assets/models/post_station4.glb` | `post_station4.png`, `_2` |
| **Group G in the `watch` view** | | **21** (watch room 4 + gate 1, board 2 + the two MultiMeshes, lockers 2 + door + 2 trays, post 3 + 4 parts); the tags and lamps are 2 `MultiMesh` draws | | | |

`check_glb_names.py` passes on all four GLBs. **`lockers.glb` is the Chapter 2 archive's bank of lockers (`docs/models/ch2.md`): the Chapter 4 bank is `lockers4.glb`** (24 doors, not 12); the scene must
load `lockers4`.

**The room frame.** `watch_room` is placed at **(12.7, 0, 0) with yaw −90**: local +Z = world −X (into the hall), local +X = world +Z (south). world = (12.7 − z_local, y, x_local). The three fixtures
are children of the room's mounts (same yaw), so each fixture's own front (+Z) faces the hall. The cabin is 7.0 wide (z_world ±3.5), 2.4 deep (world x 11.5 … 13.9) and 3.3 high.

## watch_room.glb (4,299 tris, 5 surfaces, 4 slots)

LOCAL FRAME: **origin = the floor at the cabin's centre, front = +Z**. Interior x ±3.5, z −1.2 (back wall) … +1.2 (the glazed front, world x 11.5), floor top y 0.03, ceiling y 3.30, roof 3.40.
Bounds (-3.62, 0, -1.3) … (3.62, 3.95, 1.56).

| Node | Material(s) | Tris | Pivot / notes |
|---|---|---|---|
| `watch_room` | `M_Steel_Dark` + `M_Glass` + `M_Chequer` + `M_Brass_Aged` | 2,781 | Origin (0, 0, 0), identity. **Steel**: the back wall and two side walls with raised panel frames, the ceiling slab with two beams and a lamp cage, the roof with a parapet, a vent box and a stack, the **front**: a riveted dado 0.03 … 0.65 (a low one: the hall camera at y 1.7 sees the board's lower row over it), six mullions (three each side) and two corner posts between y 0.65 and 2.55, the doorway (posts at x ±0.60, a lintel at y 2.40, a threshold and a track), a header fascia 2.55 … 3.30 with rivets and a lamp bracket over the door. **Glass**: 8 panes (4 on each side of the doorway, y 0.67 … 2.53) and the transom. **Chequer**: the floor (top y 0.03). **Brass**: cornices, the dado cap, a picture rail round the three inner walls, post caps and **the Institute's mark** in 6 mm relief (0.42 high) on the fascia |
| `IA_watch_gate` | `M_Brass_Aged` | 1,518 | **Origin = the hinge post (−0.54, 0.03, 1.2)** (world (11.5, 0.03, −0.54)), identity at rest. A brass post (y 0.03 … 2.34), a **lock box** (0.14 x 0.30 x 0.16) on the origin plane with a key plate and a slot on top and **Leyla's sign** (a crescent opening right and three dots) in 4 mm relief on its +Z face, and a collapsible lattice (x −0.49 … +0.54, y 0.20 … 2.20; rails, an end stile, 4 x 3 cells of crossed bars with hex rosettes on both faces). **OPEN = scale local X to 0.15 about the origin** (the grille is in the room's front plane, so its long axis is X, **not Z as in the booth**): the lattice folds against the post, the lock box squashes flat |
| `watch_key_mount` | empty | — | **Child of `IA_watch_gate`**, at the slot (−0.54, 1.535, 1.2), Euler (+90°, 0, 0): item −Z (the bow of `key_leyla`) → +Y, item +Y (its face) → +Z, as the booth's |
| `board_mount` | empty | — | (−0.85, 0.03, −1.2), identity: `roll_board`'s origin (the board is 2.4 wide: x −2.05 … 0.35) |
| `lockers_mount` | empty | — | (2.00, 0.03, −1.2), identity: `lockers4`'s origin (2.88 wide: x 0.56 … 3.44) |
| `post_mount` | empty | — | (−2.95, 0.03, −1.2), identity: `post_station4`'s origin (0.9 wide: x −3.40 … −2.50; its tube reaches the ceiling flange at y 3.30) |
| `echo_mount_clerk_post` | empty | — | (−2.95, 0.03, −0.35), **Euler (0, 180°, 0)**: the clerk stands 0.45 in front of the post station and faces it (toward −Z) |
| `watch_lamp` | empty | — | (0, 2.95, 0.1): the §1.5 OmniLight |

World positions of the mounts (x_world = 12.7 − z_local, z_world = x_local): board (13.9, 0.03, −0.85), lockers (13.9, 0.03, 2.00), post station (13.9, 0.03, −2.95) (so the post station is on the NORTH
side, the lockers on the SOUTH side, the board between them), the grille (11.5, ., −0.54 … +0.54), the clerk (13.55, 0.03, −2.95).

Notes for the scene:
- **The grille faces the `watch` camera** (the contract view (6.5, 1.7, 0) → (12.7, 1.5, 0)): the lattice, the lock box and Leyla's sign are seen from the front; the board is seen beyond it over the low dado.
- The inside is dark steel and chequer: the §1.5 `watch_lamp` should light the fixtures from the ceiling cage (0, 2.95, 0.1 local = world (12.6, 2.95, 0)).
- The glass is closed 12 mm boxes (`M_Glass`, transparent in the game); the cabin's back wall (z −1.2 local = world x 13.9) pokes ≤ 0.35 into the hall's concrete wall (the hall circle is at 13.55 at z = ±3.5): never visible.
- `IA_watch_gate` is 1.16 x 2.3 x 0.18: an exact trimesh collider.

## roll_board.glb (3,868 tris, 4 surfaces, 4 slots)

LOCAL FRAME: **origin = the floor under the board's centre, front = +Z** (panel back at z = 0, panel face z = 0.03). 2.40 x 1.50 (x ±1.2, y 0.25 … 1.75). Bounds (-1.22, 0, 0) … (1.22, 1.77, 0.1).

| Node | Material(s) | Tris | Pivot / notes |
|---|---|---|---|
| `roll_board` | `M_Wood_Walnut` + `M_Brass_Aged` | 3,568 | Origin (0, 0, 0), identity. The walnut panel on a plinth skirt with raised field strips; a brass frame (raised 15 mm) with corner rosettes; a **header band** with the Institute's mark (0.105, relief 4 mm) and two groups of four rivets; a bottom ledge with a lip; three hanging rails (4 mm) 0.06 above each row's hooks; **42 brass hooks** (a 22 mm plate on the panel, a square pin to z 0.07 and an upturned tip) and **42 hex lamp sockets** (r 0.0205) 0.115 above them; **Leyla's plaque** behind the 42nd slot (a brass plate 0.12 x 0.22, a larger socket and her sign in relief) |
| `tag_proto` | `M_Enamel_Cream` | 222 | **Origin = the first slot's hook centre (−1.04, 1.28, 0.05)** = the tag's hanging hole; the tag (0.100 x 0.070 x 0.003, a raised rim, a name bar, the lower corners cut) hangs below it (y −0.058 … +0.012), identity |
| `lamp_proto` | `M_Glass_Dark` | 78 | **Origin = the same point**; the jewel dome (Ø 0.030, 10.5 mm high) is **baked 0.115 above and 0.016 behind it** (in its socket), so **the same instance transform places the tag and the lamp of a slot** |
| `slot_origin` | empty | — | (−1.04, 1.28, 0.05) |

**MultiMesh recipe.** Slot i = 0..41: row = i div 14, col = i mod 14; instance transform = translation **(0.16 col, −0.30 row, 0)** (no rotation) added to the proto node's position, for BOTH protos.
`tag_proto` takes the 41 tags (slots 0..40: **the 42nd slot, i = 41 (row 2, col 13), has no tag**: the Leyla slot, an empty hook) and `lamp_proto` the 42 lamps (slot 41 is the Leyla lamp: lit last / never lit in the finale).
The lamp surface is `M_Glass_Dark`: the code turns emission on (`ModelUtil.set_emission`); the 41 lamps go out one by one in the finale. Hide the two prototype nodes themselves (or use them as instance 0).

## lockers4.glb (4,812 tris, 5 surfaces, 2 slots)

LOCAL FRAME: **origin = the floor at the centre of the BACK face (z = 0), front = +Z**. 2.88 w (x ±1.44) x 1.89 h x 0.47 d (carcass 0.43, doors to 0.45). Bounds (-1.46, 0, 0) … (1.46, 1.905, 0.47).
**Numbering: the top row is 1 … 12, the bottom row 13 … 24, both left → right seen from the front; locker 17 = bottom row, 5th from the left (x −0.48 … −0.24, y 0.10 … 0.95)**, the only hollow one.

| Node | Material(s) | Tris | Pivot / notes |
|---|---|---|---|
| `lockers4` | `M_Steel_Painted` + `M_Brass_Aged` | 4,504 | Origin (0, 0, 0), identity. The painted carcass (a plinth, a cornice, a middle rail, thin ribs between the doors) with solid blocks round locker 17's cavity (walls 12 mm, a floor, a ceiling, a back, **a shelf at y 0.50** 0.40 deep), and the other **23 doors** in brass (0.236 x 0.842 x 0.02: a raised panel, a pull handle on the right, a keyhole boss and the numeral (44 mm) in 1.6 mm relief on a small plate at the top) |
| `IA_locker_17` | `M_Brass_Aged` | 188 | Locker 17's door, the same design. **Origin = the hinge axis on the LEFT edge (−0.480, 0.525, 0.45)** (the 2 mm gap, the door's front plane), identity at rest; two hinge knuckles. **OPEN = −105° about +Y** (swings toward the viewer) |
| `IA_locker_note` | `M_Brass_Aged` | 60 | A shallow brass tray (0.14 x 0.19, rim 4 mm) on the shelf. **Origin = its top centre (−0.36, 0.516, 0.22)**; child `note_mount` at the origin, identity: `leyla_note_1998` lies flat |
| `IA_locker_parcel` | `M_Brass_Aged` | 60 | A tray 0.17 x 0.26 on the compartment floor. **Origin = its top centre (−0.36, 0.121, 0.22)**; child `parcel_mount`, **Euler (0, 90°, 0)**: `leyla_parcel` (0.20 x 0.12) lies with its long side along Z (the cavity is 0.216 wide) |

Notes for the scene:
- The doors are brass (one material for the tap target `IA_locker_17`) with a painted carcass; the numerals are relief, readable at the contract `locker_17` camera (9.8, 1.6, 2.0) (the bank is at world x 13.45 … 13.9, z 0.56 … 3.44).
- The compartment is dark inside: aim a small light (`watch_lamp` is 2 m away) or lift the ambient: the QA render `lockers4_2.png` uses a key light at the door.
- Items: `leyla_note_1998` (0.093 x 0.142) and `leyla_parcel` (0.206 x 0.126 x 0.092 with its twine) fit the trays; the parcel stands 0.092 high on a 0.50 clearance.

## post_station4.glb (7,019 tris, 7 surfaces, 4 slots)

LOCAL FRAME: **origin = the floor on the wall plane (z = 0) at the cabinet's centre, front = +Z**. Cabinet 0.90 w (x ±0.45) x 1.45 h x 0.40 d on a 0.10 plinth, panel face z = 0.40; the riser tube (Ø 0.10) at (0, ., 0.20)
up to the ceiling flange at y = 3.30. Bounds (-0.46, 0, -0.01) … (0.46, 3.3, 0.557).

| Node | Material(s) | Tris | Pivot / notes |
|---|---|---|---|
| `post_station4` | `M_Steel_Dark` + `M_Brass_Aged` + `M_Enamel_Cream` | 4,311 | Origin (0, 0, 0), identity. The dark steel cabinet (side vents, a recessed number-wheel collar), a brass bezel, a header band with the Institute's mark and rivets; the **destination ring plate** (r 0.185 about (−0.19, 1.00)) carrying the **six Chapter 2 pictograms as cream enamel relief** (3 mm, 0.060 high) at r 0.128, **d = 0 … 5 clockwise from 12 o'clock every 60°: the director's four-pointed star (12), a book (2), the laboratory flask (4), a film reel (6), a letter (8), a padlock (10)**, each with an index wedge; the number wheel's fixed pointer; the lever's quadrant (two cheeks, two stops at 0° and 50°) and pivot block; the **canister's tube mouth** (a hollow brass tube back to z 0.12 and a flared collar to z 0.46); a pressure gauge; the **riser tube** with three clamps and wall brackets and the ceiling flange |
| `IA_post_dial` | `M_Bakelite` | 420 | The destination knob Ø 0.11 with 8 grip flutes and a pointer ridge. **Origin = (−0.19, 1.00, 0.40)**, axis +Z; identity = d 0 (the star); **position d (0..5) = −60° x d about +Z** (the flask is d = 2) |
| `IA_post_number` | `M_Brass_Aged` | 1,160 | The number wheel: a brass disc Ø 0.21 with the digits **1 … 9** (39 mm, 3.2 mm relief) at r 0.071, **digit n at +40° x (n − 1) counter-clockwise from 12 o'clock, top outward**, a centre cap and two grip bosses. **Origin = (0.19, 1.00, 0.40)**, axis +Z; identity = 1 under the fixed pointer; **number n (1..9) = −40° x (n − 1) about +Z** |
| `IA_post_canister` | `M_Brass_Aged` | 792 | The brass carrier Ø 0.09 x 0.26 lying along Z in the mouth (beads at both ends and a mid band, domed ends), its front end 0.07 outside the collar. **Origin = its centre (0, 0.50, 0.34)**, identity. **The code slides it +0.35 along +Z** ("knocks back"); the empty tube mouth shows behind it |
| `canister_mount` | empty | — | **Child of `IA_post_canister`** at its centre, identity |
| `IA_post_send` | `M_Brass_Aged` | 336 | The send lever: an arm 0.30 with a ball grip on a pivot pin. **Origin = the pivot (0.375, 0.74, 0.425)**; rest = upright (+Y); **PULLED = +50° about +X** (toward the player; the quadrant's second stop) |

Notes for the scene:
- `turn_post_dial(±1)`: dial.rotation = −60° x `post_dial`; `turn_post_number(±1)`: wheel.rotation = −40° x (`post_number` − 1); `send_post()`: lever to +50°, then (success) the canister slides in and out of sight, or (`post_returned`) it slides +0.35 along +Z and stays.
- The pictograms are the Chapter 2 set (`dest_symbols.png`): the same six, the same clock positions, so the dial reads the same as the Archive's tube station.
- The tube rises 1.8 m above the cabinet: keep the §1 ceiling at y 3.3 (the watch room's ceiling); the hall's wall is behind it.

## Files and commands

`game/assets/models/{watch_room,roll_board,lockers4,post_station4}.glb(+.import)`, `qa/blender/ch4/*.png`, `tools/blender/models/*.py`, `tools/blender/lib_ch4_fgh.py`, `tools/blender/lib_ch4_mark.py`,
`tools/blender/build_lists/ch4_g.txt`. Rebuild: `tools/blender/build_all.sh`; re-import: `godot --headless --path game --import`.
