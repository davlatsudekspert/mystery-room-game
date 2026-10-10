# Chapter 4 group F: Strand's booth (measured results)

Contract: `docs/models/ch4.md` §0, §1, §2, §8, §10, §11, §12. Models: `booth`, `booth_desk`, `strand_box4`, `orrery`.
Scripts: `tools/blender/models/<name>.py`; helpers in `tools/blender/lib_ch4_fgh.py` (new, additive: the `MB` mesh builder, prisms, pictogram outlines, spoked gears, fluted knobs, the
shell and back-face checks) and `tools/blender/lib_ch4_mark.py` (the Institute's mark as two solids), on top of `lib_ch4.py` and `lib_ch4_cde.py`; build list
`tools/blender/build_lists/ch4_f.txt`. Same pipeline as groups A–E: G-frame build, lean GLB, re-read and verify against §11, then Cycles 24 samples 960 × 640. QA scenes: the hall shell
(shutters open) with the neighbours as the setting for `booth` (the §1.5 hall lights plus a `booth_lamp`), a neutral walnut table with soft point lights for `strand_box4` and `orrery`.
Blender renders only.

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [--shots=1,2,...]
```

**New checks (every script of groups F and G prints them):** a *shell check* (every closed shell of every mesh must have a positive signed volume, i.e. outward normals; none is inverted)
and a *back-face render check* (the isolated model is rendered from 14 directions with a view-layer override that paints back faces red; the worst view must stay under 0.5 %): both
guard against Godot culling inside-out faces. Boxes are built **with** bottoms (a model seen from below, e.g. the booth from the hall's eye height, must not show its inside).

## Summary

| Model | Tris (budget) | Surfaces (cap) | Slots | GLB | QA renders (`qa/blender/ch4/`) |
|---|---|---|---|---|---|
| `booth` | 5,637 (10,000) | 5 (9) | 4 | `game/assets/models/booth.glb` | `booth.png`, `_2` (gate and lock with Strand's key), `_3` (the clock), `_4` (gate open) |
| `booth_desk` | 3,525 (6,000) | 4 (6) | 4 | `game/assets/models/booth_desk.glb` | `booth_desk.png`, `_2` |
| `strand_box4` | 6,902 (7,000) | 12 (12) | 4 | `game/assets/models/strand_box4.glb` | `strand_box4.png`, `_2`, `_3` |
| `orrery` | 3,152 (3,500) | 5 (5) | 2 | `game/assets/models/orrery.glb` | `orrery.png`, `_2` |
| **Group F in the `booth` / `gear_box` views** | | **20** drawn closed (booth 4 + gate 1, desk 4, box: body 2 + lid 1 + 4 knobs + 4 gears); +6 once the box is open (the pad and the orrery's 5) | | | |

`check_glb_names.py` passes on all four GLBs. The booth is drawn with group T; the box and the orrery only matter in the `gear_box` view (the rest of the hall is culled).

## booth.glb (5,637 tris, 5 surfaces, 4 slots)

LOCAL FRAME: **origin = (0, 0, −13.0) world, yaw 0, front = +Z**. Floor y = 2.0, roof y = 4.7, x ±3.2, z −0.9 (back, against the hall wall) … +1.1 (the front glass, world −11.9).
Bounds (-3.34, 0, -0.97) … (3.4, 5.16, 2.41) (the roof vent reaches y 5.16).

| Node | Material(s) | Tris | Pivot / notes |
|---|---|---|---|
| `booth` | `M_Steel_Dark` + `M_Glass` + `M_Chequer` + `M_Brass_Aged` | 4,895 | Origin (0, 0, 0), identity. **Steel**: six legs (0.16 square, base and cap plates) with X braces, floor beams (web + flanges), the riveted fascia (front rivet row of 33), corner posts and 7 mullions, the dado (a continuous panel with a raised frame in each bay and a rivet row), the back wall panel, the roof slab with a vent box and a stack, the door frame, the stair (two **channel stringers** 0.24 deep under the nosing line with trestle legs, 11 risers), the landing beams and legs, balustrade posts and mid rails, the **south gate post** at (0, 0, 2.3 local), a ceiling lamp. **Glass**: 7 front panes (0.8 wide, y 2.59 … 4.49), the door pane, four side panes (all 12 mm boxes, closed). **Chequer**: the floor slab (top y 2.0), eleven treads, the landing. **Brass**: a cornice band round the roof edge, the dado cap rail, corner caps, tread nosings, two sloped handrails (0.045 square) and the landing rail, door hardware, the lamp ring and the **stopped wall clock 03:17**: bezel Ø 0.70, a dark steel dial Ø 0.59, twelve hour bars (the 12, 3, 6, 9 longer), hour and minute hands (hour at 98.5°, minute at 102° clockwise from 12), centred at (0, 3.95, −0.86 local) on the back wall |
| `IA_booth_gate` | `M_Brass_Aged` | 742 | **Origin = the north post (0, 0, 1.5 local) = world (0, 0, −11.5)**, identity at rest. A brass post 1.14 high, a lock box (0.10 x 0.26 x 0.14 under a 0.12 x 0.16 key plate, centred ON the origin plane z 1.5) with Strand's mark in 4 mm relief on its +Z face and a key slot on top (two lips 5 mm apart, a rim), a collapsible lattice 0.75 long (z 1.55 … 2.3) and 0.8 high (y 0.16 … 0.96): top, bottom and middle rails, an end stile, 2 x 3 cells of crossed bars with hex rosettes on both faces. **OPEN = scale local Z to 0.15 about the origin** (the lattice folds against the post, the lock box squashes flat: it stays where it is) |
| `booth_key_mount` | empty | — | **Child of `IA_booth_gate`**, at the slot (0, 1.465, 1.5 local), Euler (+90°, 0, 0): the item's −Z (the bow of `key_strand`) points +Y (up), the item's +Y (the face) points +Z (toward the hall). `key_strand` (0.14 long, origin = its centre of mass) then stands in the slot with the tip 6 cm inside the lock box and the top of the bow 8 cm above it |
| `booth_lamp` | empty | — | (0, 4.25, 0.10 local): the §1.5 OmniLight |
| `desk_mount` | empty | — | (0, 2.0, −0.4 local): `booth_desk`'s origin (world (0, 2.0, −13.4)) |

**Stair and door.** The stair runs EAST along the front in a lane 0.8 wide (local z 1.5 … 2.3, world −11.5 … −10.7), foot at x = 0 (the gate), 11 steps of 0.1818 x 0.22 up to the landing
(x 2.42 … 3.4, y 2.0). The booth's front wall is at z = 1.1: the 0.4 between it and the lane is open (a service gap under the dado). The **door is in the front wall at the east end
(x 2.4 … 3.2)**, reached from the landing (the contract said "a door at x = 3.2": the east wall has no stair). It is a glazed steel door with a brass push plate and pull bar, closed.

Notes for the scene:
- **The gate is seen edge-on from the contract `booth` camera** (x = 0, the leaf lies in the plane x = 0). Use a second view for the tap: `booth_gate` (−2.2, 1.55, −8.9) → (0.4, 1.25, −11.3), FOV 48 (`booth_2.png`: the gate with Strand's key in the lock), or just let the lock box (brass on dark steel, Strand's mark facing +Z) be the target: it is part of `IA_booth_gate`.
- **The `gear_box` camera of §2 (0, 3.7, −11.9) stands ON the front glass** (world z −11.9): use (0, 3.6, −11.2), looking at (0, 2.95, −13.4), FOV 44; the dado is 0.55 high, so the desk top (y 2.78) is seen over it.
- The glass is closed boxes (no alpha): `M_Glass` is transparent in the game. `IA_booth_gate` is bigger than 0.15 m, so `ModelUtil` gives it an exact trimesh collider: the tap lands on a bar, the post or the lock box (the lattice is open between them).
- Draw cost: 5 surfaces (4 + the gate). The clock is part of the brass surface.

## booth_desk.glb (3,525 tris, 4 surfaces, 4 slots)

LOCAL FRAME: **origin = the floor at the centre of the desk footprint, front = +Z**, placed at (0, 2.0, −13.4), yaw 0. Bounds (-1.775, 0, -0.44) … (0.84, 1.78, 0.448).

| Node | Material(s) | Tris | Pivot / notes |
|---|---|---|---|
| `booth_desk` | `M_Wood_Walnut` + `M_Brass_Aged` + `M_Leather` + `M_Steel_Painted` | 3,525 | Origin (0, 0, 0), identity. **Walnut**: a 1.64 x 0.84 top at y 0.74 … 0.78 with an overhang, two pedestals (3 raised-panel drawers each) on a plinth, the centre drawer and a modesty panel. **Leather**: the writing field 1.30 x 0.62 (y 0.78 … 0.784), a ledger turned 12° at the front left, and **the coat**: a long coat (shoulders 0.48, hem 0.65, two hanging sleeves, a collar and a belt, lofted ellipses) on the coat stand. **Brass**: drawer pulls (a bar on two posts) and keyholes, the field's edge, the coat stand (pole to y 1.76, three feet, four crown hooks, a hanger), the lamp's base and arm, an inkwell with a pen, a paperweight and the **table clock** (a round case Ø 0.20 with a painted dial, hands stopped at 03:17). **Steel painted**: the banker's lamp shade (green-grey), the clock dial |
| `box_mount` | empty | — | **(0, 0.78, 0.0)**, identity: `strand_box4`'s origin (the base centre) |
| `lamp_light` | empty | — | (−0.58, 1.28, −0.21): under the lamp shade, for the §1.5 `desk` light |

The desk is 4 slots, 1 object (4 surfaces); the coat stands 1.38 left of the desk centre (x −1.38, z −0.16), so the booth floor (x ±3.2) has room for it.

## strand_box4.glb (6,902 tris, 12 surfaces, 4 slots)

LOCAL FRAME: **origin = the base centre of the box on the desk top** (the desk's `box_mount`), front = +Z, placed at (0, 2.78, −13.4), yaw 0. **0.48 x 0.34 x 0.19** (x ±0.24, z ±0.17; the
body 0.15 + the lid 0.04): the contract said 0.42 x 0.30 x 0.18; the orrery inside is Ø 0.26 and needs a body 0.30 deep. Bounds (-0.248, 0, -0.189) … (0.248, 0.166, 0.178) (body only).

| Node | Material(s) | Tris | Pivot / notes |
|---|---|---|---|
| `strand_box4` | `M_Wood_Walnut` + `M_Brass_Aged` | 1,736 | Origin (0, 0, 0), identity. The **hollow** walnut body (floor, four walls 14 mm, two stepped base mouldings, a lower and a top moulding frame, two raised front panels), brass **escutcheons** (a stepped disc r 0.034 / 0.030) behind each knob with **six detent ticks** (60° apart, the 12 o'clock one longer), four brass corner brackets, the **body's hinge knuckles** at the back, a brass **stand for the orrery** (a flared base, a turned neck, top at y 0.05) and a brass frame round the log pad |
| `IA_box_lid` | `M_Brass_Aged` | 1,350 | **Origin = the hinge axis (0, 0.158, −0.181)**, along X; identity closed. A brass lid (a shell + a stepped top plate) with a front hasp, two hinge knuckles, 24 rivets, **four posts and four fixed target indices** (an arrowhead pointing at its gear, 4 mm beyond the needle's tip), **Strand's mark** in the front strip (z +0.14) and the **pictogram "a wheel with an arrow to its neighbour"** (two gears and an arrow, 3.5 mm relief) in the rear strip (z −0.134). **OPEN = −110° about +X**: the lid stands up and leans back (its front edge ends at y 0.48, z −0.33); the four gears travel with it |
| `gear_pointer_1..4` | `M_Bakelite` | 583 each | **Children of `IA_box_lid`.** Origin = the gear centre at **(x_k, 0.19, z_k)**: x = −0.12675, −0.0423, +0.0423, +0.12675 and z = 0.04425, −0.00425, 0.04425, −0.00425 (a zig-zag: neighbours are 0.0975 apart and mesh; gears 2 and 4 run 5 mm higher, so the teeth interleave without touching). A 12-tooth wheel (r 0.0425 / 0.0545) with **six spokes** (the six positions), a hub and a **needle** (a bold arrow, tip at r 0.072) lying on top. Identity = the needle points at its fixed index (toward −Z). **Position k (0..5) = −60° k about +Y** (clockwise seen from above) |
| `IA_knob_1..4` | `M_Brass_Aged` | 360 each | Fluted brass push-knobs Ø 0.050 (12 flutes, a domed cap, a skirt, a pointer ridge at 12 o'clock). **Origin = (x_k, 0.075, 0.174)** on the escutcheon, axis +Z, the same x as the gear above it. **Position k (0..5) = −60° k about +Z** (clockwise from the player); the ticks round the escutcheon are the six stops |
| `IA_box_log` | `M_Paper` | 44 | The blotting-paper pad for the log, x 0.07 … 0.22, z ±0.13, top at y 0.044. **Origin = its top centre (0.145, 0.044, 0)** |
| `log_mount` | empty | — | **Child of `IA_box_log`, identity**: `strand_log` lies flat on the pad (hero face +Y, top edge −Z, 0.14 wide x 0.20 high: it fits, the pad is 0.15 x 0.26) |
| `orrery_mount` | empty | — | **(−0.08, 0.05, 0.0)**, identity: `orrery`'s origin on the brass stand |

Notes for the scene:
- **`press_knob(i)`** turns knob i and the code turns the gears: pointer k = −60° x `box[k]` about +Y, with `box[k]` in 0..5; the rule (a knob drives its gear and the next) is on the lid's rear strip. The lid is **`box_open`** at all-zero: open it by −110° about +X over ~1 s; the knobs refuse afterwards.
- The pictogram sits on the lid's top (visible from the start); the contract's "under the lid" would only show once the box is open. `IA_box_lid` is an IA part, but nothing taps it (the box opens by itself).
- Brass-on-brass: the needles are black bakelite on purpose (they read against the lid), the gears have their six spokes so the 60° steps read even if the needle is hidden.
- Surfaces: closed = body 2 + lid 1 + knobs 4 + gears 4 = 11 (+ the pad 1 once the lid is open). The 12 of the cap is the file's count.

## orrery.glb (3,152 tris, 5 surfaces, 2 slots)

LOCAL FRAME: **origin = the centre of the underside of the base**, +Y up, **mark 1 toward +Z** (the front of the box); placed at the box's `orrery_mount`. Base Ø 0.262 (the hall's wall r 14 at 1 : 107). Bounds (-0.131, -0.0, -0.131) … (0.131, 0.03, 0.131).

| Node | Material(s) | Tris | Pivot / notes |
|---|---|---|---|
| `orrery` | `M_Brass_Aged` | 1,872 | Origin (0, 0, 0), identity. The chamfered base (y 0 … 0.008), **four fixed ring tracks** at r = 0.098 / 0.0793 / 0.0607 / 0.042 (the hall's 10.5 / 8.5 / 6.5 / 4.5 m, 0.00933 m per metre; y 0.008 … 0.0105), **eight radial index lines** to the marks, the island r 0.028 with a pedestal and a Core bead, and the **numerals 1–8** (14.5 mm, 1.8 mm relief, lying flat, top outward as on the hall's apron) at r 0.116. Mark p + 1 lies at azimuth 180° + 45° p (mark 1 front, 3 left, 5 back, 7 right) |
| `orrery_tower_1..4` | `M_Steel_Dark` | 200 / 280 / 360 / 440 | **Origin = the model centre (0, 0, 0)**, identity = the tower on its ring's mark 1 at (0, ., r_n): I 0.098, II 0.0793, III 0.0607, IV 0.042. A turned pylon (foot, stem) carrying **n small discs** (I = 1 … IV = 4): the tower's number. **The code rotates tower n by −45° x p about +Y** (p = 0..7 from `v_align`); the pylon stays on its ring |

The orrery sits 0.05 above the box floor: its top (y 0.09) is far below the lid. The contract's "a pylon at radius 0.04 n" put tower I inside tower IV; the hall's ring I is the outer one, so the model matches the hall.

## Files and commands

`game/assets/models/{booth,booth_desk,strand_box4,orrery}.glb(+.import)`, `qa/blender/ch4/*.png`, `tools/blender/models/*.py`, `tools/blender/lib_ch4_fgh.py`, `tools/blender/lib_ch4_mark.py`,
`tools/blender/build_lists/ch4_f.txt`. Rebuild: `tools/blender/build_all.sh`; re-import: `godot --headless --path game --import`.
