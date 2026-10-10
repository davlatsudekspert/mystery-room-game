# Chapter 3 group F: the Gallery console and the memorial wall (measured results)

Contract: `docs/models/ch3.md` §0, §1 (placement, fixed points, culling), §2 (views `console`, `scope`, `strand_plate`, `cradle`,
`memorial`, `socket_42`, `finale`, `secret`), §8, §9 (item sizes), §10 (`pose_kneel`), §11 (H2 lissajous), §13, §14. Models:
`gallery_console`, `memorial_wall`. Scripts: `tools/blender/models/<name>.py`; shared helpers in `tools/blender/lib_ch3_ef.py`;
build list `tools/blender/build_lists/ch3_f.txt`.

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [--shots=1,2,...]
```

**Pipeline.** As groups D and E: G-frame build, GLB export, a re-read of the GLB (names, parents, positions to 1 mm, identity rest
rotations, mount rotations, triangles, surfaces, slots) and `check_glb_names.py`. Renders: Cycles, 32 samples, 960 × 640, 2 threads,
cameras from the §2 views, `shell_gallery.glb`, the two blast doors and `array_below.glb`; the scope and the plate carry the seed-0
previews (`scope_screen_live.png`, `strand_plate.png`); the lamps, the crystals and the glow rings get a QA-only emissive override. The
key spot of §1.5 does not reach the console (its cone is aimed at z −1.4 and the console stands at z 2.6) and the sconces are far
from the north arc, so the QA scenes add a stand-in lamp over each (see the integration notes). Blender renders only.

All coordinates are **Godot, model-local, metres** (memorial_wall: world); models face +Z.

## Summary

| Model | Tris (budget) | Surfaces (cap) | Slots | GLB | QA renders (`qa/blender/ch3/`) |
|---|---|---|---|---|---|
| `gallery_console` | 5,858 (8,000) | 12 (12) | 4 | `game/assets/models/gallery_console.glb` | `gallery_console.png`, `_2` |
| `memorial_wall` | 5,574 (6,000) | 5 (6) | 3 | `game/assets/models/memorial_wall.glb` | `memorial_wall.png`, `_2`, `_3` |

`check_glb_names.py` passes on both. The console's 12 surfaces are exactly the contract's: body 3 (Walnut, Brass, Glass_Dark) +
`scope_screen` + two knobs + cradle + ring + plate 2 (Brass, Shader_Quad) + two lamps.

---

## gallery_console.glb (5,858 tris, 12 surfaces)

At (0, 0, 2.6), yaw 0. Body 1.40 × 0.60 (x ±0.70, z ±0.30): plinth to y 0.08, a walnut cabinet whose top slopes from the front edge
(z 0.30, y 0.92) up to (z −0.06, y 1.02) (**15.5°**; the slope normal is (0, 0.9636, 0.2677)) and runs flat at 1.02 behind it; the
instrument board x ±0.66, y 1.02 … 1.48, z −0.12 … −0.07 (face z −0.07). Bounds (−0.708, 0, −0.30) … (0.708, 1.494, 0.329).

| Node | Pivot / position | Materials | Notes |
|---|---|---|---|
| `gallery_console` | (0, 0, 0) | Walnut, Brass, Glass_Dark | static: raised front and side panels, brass nosing, plinth strip and grille, two drawer pulls, the brass strip where slope meets board, the board cap and four board screws; the scope's brass bezel (R 0.119 … 0.147, 0.022 proud) with six screws and the dark glass margin (R 0.12 … 0.134); a **black enamel dial** (R 0.092, `M_Glass_Dark` is opaque glossy black) behind each knob, brass bosses, scale rings (R 0.0865 … 0.0905) and **numerals 1–5** (0.027 high, 2.8 mm relief) round each knob at 150 / 120 / 90 / 60 / 30°; a 0.070 × 0.052 **tube-rack** pictogram under X and a 0.030 × 0.062 **crystal** pictogram under Y (2 mm relief) on black plates 0.090 × 0.074 (brass on walnut did not read in the `console` view); the two lamp bezels; the **keystone pad** of the finale socket |
| `scope_screen` | (0, 1.25, −0.065) | Shader_Quad | disc Ø 0.24, 28 segments, UV 0..1 over the bounding square (measured: centre (0.5, 0.5), min 0, max 1), faces +Z |
| `IA_knob_x` / `IA_knob_y` | (−0.34, 1.20, −0.06) / (0.34, 1.20, −0.06) | Brass | knurled knob Ø 0.07 × 0.03 (20 segments), axis +Z, a raised pointer at 12 o'clock at rest (= value 3); **value v = (60° − 30° (v − 1)) about local +Z**; the numerals sit at the matching angles |
| `IA_cradle` | (0, 0.98, 0.14) | Brass | turned pedestal (R 0.064 at y 0.93, level seat top y **0.98**, R 0.031) with three claws (R 0.0036, 0.054 high, closing to R 0.0262); the seat stands 1.6 cm above the slope at the centre |
| `cradle_ring` | (0, 0.9659, 0.14) | Brass | flat ring R 0.072 … 0.080, 3.5 mm, lying **on the slope** (axis = the slope normal) round the pedestal; code glow |
| `IA_strand_plate` | (−0.42, 0.97, 0.16) | Brass, Shader_Quad | the plate's **face centre**, tilted onto the slope; face 0.18 × 0.14 with UV 0..1 (u → +X, v up the slope; measured corners (0,0) (1,0) (1,1) (0,1)); slab, frame 0.204 × 0.164 (4 mm), four domed screws, a tab below with **Strand's mark** (ring + meridian) in relief; bounds (−0.522, 0.893, 0.079) … (−0.318, 1.048, 0.271) |
| `lamp_choir` / `lamp_nursery` | (∓0.62, 1.42, −0.065) | Glass_Dark | jewels R 0.0165 in brass bezels; code tint |
| `cradle_mount` | **(0, 1.0369, 0.14)** | — | empty, identity: the **origin of a `nursery_crystal`** standing in the cradle (its bottom is 0.0569 below the origin, ch3_g.md) |
| `choice_mount` | **(0.42, 1.0571, 0.16)** | — | empty, identity: the origin of a **`strand_fork`** standing on the keystone pad (its ball is 0.0771 below the origin); a `nursery_crystal` there stands on the pad's boss (0.0202 high), see below |

**Mounts follow the items' origins.** `UndergroundVisuals._held_item` spawns the item with an identity transform *at the mount*, so a
mount is the item's origin, not the seat: `cradle_mount.y` = seat 0.98 + 0.0569. At the finale socket the pad's top is level at y 0.98
(like the cradle's seat) and carries a **boss Ø 0.017, 0.0202 high** (= 0.0771 − 0.0569): the fork's ball (bottom at the pad) swallows
the boss, a crystal's collar foot sits on its top; both then stand exactly. The contract's point (0.42, 0.98, 0.16) is the pad.

QA: `gallery_console.png` (the `console` view: the scope with the seed-0 figure, knobs with numerals, the plate, the cradle with a
nursery_crystal and the lit ring, the finale pad), `_2` (hero from the operator's left: plate, cradle and pad on the slope).

---

## memorial_wall.glb (5,574 tris, 5 surfaces)

**Room-coordinate model.** φ is measured from north (−Z) clockwise seen from above (φ > 0 = east = the viewer's right from the
Gallery). Bounds (−2.0, 0.95, −3.998) … (2.0, 2.15, −3.385).

| Node | Pivot / position | Materials | Notes |
|---|---|---|---|
| `memorial_wall` | (0, 0, 0) | Stone, Brass | **granite band** φ −30 … 30, face r 3.92, y 0.95 … 1.95 (15 segments of 4°, end caps), a **pictogram backing** y 1.95 … 2.15 (face r 3.935), three brass edge trims; **41 six-sided cups + 41 ledges** (below; the 42nd is `IA_socket_42`), and **42 relief figures** in the band (head hexagon + body, 8 mm, h 0.15): 41 at φ −27 … 22 (1.225° apart) and **one apart at φ 28.5** |
| `memorial_crystals` | (0, 0, 0) | Crystal | ONE mesh: 41 hexagonal crystals (Ø 0.03 across corners, 0.07 high, 24 tris each = 984), one per socket except row 2, column 13; bounds y 1.15 … 1.82; the code turns emission on for all |
| `IA_socket_42` | (1.78, 1.15, −3.49) | Brass | the empty cup + ledge at row 2, column 13; bounds (1.722, 1.126, −3.508) … (1.809, 1.162, −3.422) |
| `socket_42_ring` | (1.779, 1.185, −3.491) | Brass | ring R 0.050 … 0.058, 3 mm, on the granite round the socket (centre r 3.9185, φ 27°, y 1.185), axis toward the Gallery centre; code glow |
| `socket_42_mount` | **(1.7674, 1.2069, −3.4688)**, rotation (0, −27, 0) | — | the origin of a `nursery_crystal` in the cup: floor 1.15 + 0.0569; +Z faces the Gallery centre |
| `echo_kneel_mount` | (1.49, 0, −3.02), rotation (0, 153, 0) | — | Leyla 1998's `pose_kneel` origin |

**Sockets.** Rows 0..2 (top → bottom) at y 1.75 / 1.45 / 1.15, columns 0..13 at φ = −27° + c × 54° / 13 (4.154°, 0.284 m apart at
r 3.92). A cup is a 6-sided brass tulip (R 0.027 flaring up to the rim, inner R 0.019, 0.024 high, **floor at the row height**) whose
axis is on r 3.893 (touching the wall); it stands on a 0.066 × 0.062 × 0.012 ledge. The contract's "socket centre" (3.92 sin φ, y, −3.92 cos φ)
is the point **on the wall** at the seat height; for socket 42 it is (1.7797, 1.15, −3.4934), the contract's (1.78, 1.15, −3.49) and the origin
of `IA_socket_42`; the cup stands 2.7 cm in front of it. **Leyla's palm** (`pose_kneel`, right palm at (−0.05, 1.15, 0.55) in the
echo's frame) lands at (1.784, 1.15, −3.487) with the mount above: on the wall point, 5 mm from the contract's socket and inside the empty
cup's footprint (the ghost's palm overlaps the cup; `memorial_wall_3.png`).

QA: `memorial_wall.png` (the `memorial` view: the figure band, 41 lit crystals, the empty cup), `_2` (the `socket_42` view with a
nursery_crystal in the cup and the ring lit), `_3` (the `secret` view with Leyla 1998 kneeling at her mount).

---

## Deviations from the contract and choices

1. **Mount heights are the items' origins** (see above): `cradle_mount` (0, 1.0369, 0.14), `choice_mount` (0.42, 1.0571, 0.16),
   `socket_42_mount` y 1.2069. The contract's 0.98 / 0.98 / 1.15 are the seats / the pad / the socket's seat height.
2. **A boss on the finale pad** so one mount serves both finale objects (the fork and the crystal differ by 0.0202 in bottom).
3. **`cradle_ring` lies on the slope** (axis = the slope normal) rather than level, so it hugs the desk.
4. **The strand plate has a tab** (Strand's mark in relief) below its frame, because the frame is only 12 mm wide: plate bounds are
   0.204 × 0.164 + the 0.038 tab, face 0.18 × 0.14 as the contract.
5. **`memorial_wall`'s socket centre is the wall point**; the cup stands 0.027 in front of it (see Sockets).
6. **The granite band is `M_Stone`, the same slot as the drum wall**: it reads through its 8 cm projection, the brass trims and its shadow,
   not through colour (the slot list has no darker stone). Polished granite would be a new slot.
7. **No tube-rack / crystal "pictograms" outside the console**: the wall's figures are plain standing figures.

## Notes for integration

- **Light the console.** `key_gallery`'s cone (60°, aimed at (0, 0, −1.4)) misses the console at z 2.6: add a small unshadowed lamp
  over it (the QA scenes use a 140 W warm omni at (0, 2.1, 3.5) and a 40 W cool area over the slope). Likewise the memorial arc
  wants a lamp near (0, 2.7, −1.6) (QA: 260 W) or the stone reads dark.
- `IA_knob_*`: identity = value 3; rotate `Basis(+Z, 60° − 30° (v − 1))`. Numerals match.
- `IA_strand_plate`: the shader quad is the only `M_Shader_Quad` slot of that mesh (slot index 0); keep the aspect 9:7.
- `memorial_crystals` and `socket_42_mount`: the item crystal in the cup is larger (Ø 0.045 × 0.114) than the 41 wall crystals
  (0.03 × 0.07): it should read as the hero.
- `echo_kneel_mount`: the mount sits 0.55 m from the wall; the palm contact is the model's own (ch3_h.md).
