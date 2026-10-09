# Chapter 3 group H: light echoes (measured results)

Models: `echo_operator`, `echo_welder`, `echo_technicians`, `echo_strand_rail`, `echo_leyla_1998`.
Scripts: `tools/blender/models/<name>.py`; shared helpers in `tools/blender/lib_ch3_echoes.py` (on top of `lib_echo.py`
and `lib_ch2_echoes.py`, neither edited); build list `tools/blender/build_lists/ch3_h.txt`. Contract:
`docs/models/ch3.md` §0, §10 and §13.

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [-- --only <pose,...>]
```

**Pipeline.** Each pose is blocked with closed primitives in the lib_echo convention (Blender, Z up, facing +Y, +X =
the figure's right): a coat loft on a `Spine` (the Chapter 2 coat ring tables re-based on the pose's hip and neck
heights), sleeves on two-bone IK, trouser legs bent through hip → knee → ankle, shoes that can stand on their toes
(kneeling), props. The body is voxel-remeshed (3.4–3.7 mm), smoothed, filleted, sculpted (folds, flutes) and
decimated; the hands (lib_ch2_echoes `hand2`, remeshed on their own finer grid) and the head (lib_ch2_echoes
`build_head`, with each figure's hair and extras) are then **boolean-unioned into the body**, boolean crumbs are
dropped, and the shell is turned 180° about Z so the GLB faces Godot **+Z**. Result: **one closed 2-manifold mesh per
pose** (0 non-manifold and 0 boundary edges, 1 shell, checked on every pose), single slot **`M_Echo`**, no
`echo_head` parts. Poses (and the two technicians) are root-level objects at identity; the contact empties are
children of their pose. Each script re-reads its GLB and checks the node names, the material, every pose's tris,
the file tris and `check_glb_names` (all **PASS**).

**Contacts** are verified in the exported orientation: the script measures the distance from each contract
point to the pose's surface (a grip centre lies inside the fist, so its distance is the fist's inner radius).

All coordinates below are the figure's own frame: **Godot axes, metres, +Z forward, −X = the figure's right, origin
on the floor between the feet**.

## Summary

| File | Object | Tris (budget) | Surfaces | Notes |
|---|---|---|---|---|
| `echo_operator.glb` | `pose_idle` | 5,826 (6,000) | 1 | 29,010 in the file (30,000) |
| | `pose_reach` | 5,768 (6,000) | 1 | |
| | `pose_pull` | 5,900 (6,000) | 1 | |
| | `pose_knob` | 5,788 (6,000) | 1 | |
| | `pose_done` | 5,728 (6,000) | 1 | |
| `echo_welder.glb` | `pose_weld` | 8,492 (9,000) | 1 | + empty `torch_tip` |
| `echo_technicians.glb` | `tech_a` | 7,862 (8,000) | 1 | 15,494 in the file (16,000) |
| | `tech_b` | 7,632 (8,000) | 1 | |
| `echo_strand_rail.glb` | `pose_rail` | 8,834 (9,000) | 1 | 17,312 in the file (18,000) |
| | `pose_offer` | 8,478 (9,000) | 1 | + empty `fork_mount` |
| `echo_leyla_1998.glb` | `pose_touch_0` | LEYLA_T0 (8,000) | 1 | LEYLA_FILE in the file (40,000) |
| | `pose_touch_1` | LEYLA_T1 (8,000) | 1 | |
| | `pose_touch_2` | LEYLA_T2 (8,000) | 1 | |
| | `pose_kneel` | LEYLA_KN (8,000) | 1 | |
| | `pose_offer` | LEYLA_OF (8,000) | 1 | + empty `crystal_mount` |

One pose (one surface) is drawn at a time per figure, so the drawn budget is the per-pose number.

---

## echo_operator.glb — the 1979 operator (port views only)

A man of about 40 in a grey knee-length work coat (collar, lapels, patch pockets, a pencil in the breast pocket),
a 1970s flat-topped work cap with a short peak, and **headphones round his neck** (band behind the neck, the cups
resting on the collar). No pose depends on the lever: the code places him at `op_mount_<n>` or `op_mount_knob`.

| Pose | Contact (figure frame) | Measured | Stance |
|---|---|---|---|
| `pose_idle` | — | — | Looking up and to his left at the step globes (head yaw 38° left, pitch 22° up), arms relaxed. Feet centre **0.10 behind** the origin |
| `pose_reach` | right-hand grip **(−0.15, 1.22, 0.50)** (upright lever's ball) | grip centre inside the fist, 0.9 cm from the inner surface | Overhand grip (fingers over the top and the far side, thumb inside), leaning 12°; **left palm on the desk top at (0.235, 0.872, 0.30)**, 0.08 behind the desk's front edge |
| `pose_pull` | right-hand grip **(−0.15, 1.12, 0.29)** (the ball of a lever pulled 50°) | 1.0 cm | The same grip turned 50° with the lever; left palm on the desk top as in reach |
| `pose_knob` | right hand on the knob **(−0.15, 1.12, 0.40)** | the knob centre 2.7 cm in front of the palm (fingers over the knob's rim) | Hips back, leaning over the desk; feet centre **0.10 behind** the origin; **left palm on the desk top at (0.25, 0.872, 0.20)** |
| `pose_done` | — | — | A step back (feet centre **0.25 behind** the origin), head over his right shoulder toward the Choir rack (yaw 75° right) |

**Desk clearance** (measured, below y 0.82): idle reaches z +0.080, reach +0.190, pull +0.170, knob +0.085, done
+0.010. The desk front is at **+0.22** at `op_mount_<n>` (all poses clear) and at **+0.07** at `op_mount_knob`:
there `pose_knob`'s toes enter the desk front by **1.5 cm** at floor level (`pose_idle`'s by 1 cm, if the code shows
idle at the knob mount). The flat left palms rest on the desk top (y 0.86): they belong to the lever / knob mounts
they were made for.

**Context (QA):** the step-globe mast is 0.33 m to his left at lever 1; none of the poses touches it. The port
views were checked with a proxy desk (`control_desk.glb` did not exist yet): port A sees him at lever 2, port B at
lever 4 pulled, port C over the knob.

## echo_welder.glb — the kept echo `welder` (transformer_1)

A man in a hip-length leather welding jacket with a stand collar and placket, work trousers, field boots and
gauntlet gloves, his welding mask flipped down (filter-window recess, headgear band, pivot bosses). He kneels on his
right knee (right foot on its toes), the left foot planted forward, leaning in 21°; the gas torch in his right fist,
the nozzle bent down onto the seam; his left forearm rests on his left thigh and his left hand feeds a filler rod
toward the flame; two hoses run from the torch to the floor behind him.

| Object | Position | Notes |
|---|---|---|
| `pose_weld` | (0, 0, 0) | The figure (8,492 tris). Height to the helmet top 1.275 |
| **`torch_tip`** (empty, child of `pose_weld`) | **(−0.10, 0.62, 0.48)**, identity | The nozzle tip (the mesh reaches it: 0.0 cm). The code's sparks |

At `transformer_1` `echo_mount` (−0.10, 0, 0.93) facing −Z: world **(−11.52, 0, −1.20), yaw −90**; the tip meets the
base seam at transformer-local (0, 0.62, 0.45). QA `echo_welder_6.png` is the `port_b_mem` view.

## echo_technicians.glb — the kept echoes `tech_a`, `tech_b` (dead_0, dead_1)

| Object | Figure | Contact / gaze |
|---|---|---|
| `tech_a` | A woman in a knee-length lab coat (collar, lapels, pockets, buttons; the scientists' 1970s bob), a clipboard on her left palm (board, sheet, clip), a pen in her right hand on the sheet, her eyes on the vessel | She looks at about **(−0.05, 1.45, 0.20)** (the vessel front 0.20 ahead; the dead autoclave's gauge should sit near there, slightly to her right) |
| `tech_b` | A man in a lab coat crouching in a wide squat (left heel raised), the coat hanging behind him and lying over his thighs, his left forearm on his left knee, looking down | His right hand grips the top of a handwheel whose centre is **(−0.04, 0.40, 0.26)** (the rim top (−0.04, 0.44, 0.26) is 0.7 cm from the palm). Group D: a drain valve there (wheel Ø 0.08, facing him) makes the pose land |

Both have their origin between their feet; the code reparents them to `echo_mount` (0, 0, 0.62) facing −Z.
QA `echo_technicians_5.png` is the `port_a_mem` view with both placed.

## echo_strand_rail.glb — Strand in 1979 (kept echo `strand_rail`, finale)

The face, beard and receding fringe of `echo_strand_standing` (its `P_HEAD` and `hair_disp`, imported, not copied),
the long coat to below the knee, a slightly rounded back.

| Object | Contact | Measured |
|---|---|---|
| `pose_rail` | both forearms lie **along the rail top (y 1.0)** in the band **z 0.30 … 0.36**, hands loosely together over the middle, hips back, looking down into the shaft (head pitch −42°) | the sleeves rest on the rail top (lowest point over the band y 0.958: the drooping fingers on the shaft side) |
| `pose_offer` | his right fist holds the fork's stem upright at chest height; the left arm relaxed | — |
| **`fork_mount`** (empty, child of `pose_offer`) | **(−0.20, 1.30, 0.45)**, identity, inside the fist | 0.7 cm to the fist's inner surface. `strand_fork.glb` (origin = centre of mass on its stem) parented there stands upright: the stem in the fist, the ball foot below the little finger, the tines above the thumb (QA `echo_strand_rail_pose_offer_4.png`) |

QA `_pose_rail_5.png` is the `port_c_mem` view at `echo_rail_mount` inside the real `shell_gallery.glb`;
`_pose_offer_5.png` the `finale` view at `echo_strand_mount` with the fork.

## echo_leyla_1998.glb — Leyla in 1998 (seed library, socket 42, finale)

About 45: the head of `echo_leyla_standing` (its `hair_disp` and `bun`, imported) with age sculpting (nasolabial
folds, softer cheeks, a forehead line). A 1990s field coat to mid-thigh (stand collar, placket, belt, two bellows
chest pockets with flaps, two hip pockets), trousers and field boots.

| Object | Contact | Measured |
|---|---|---|
| `pose_touch_0` | left **middle fingertip** on the drawer front at **(+0.40, 1.50, +0.42)** (row 0) | 0.0 cm |
| `pose_touch_1` | at **(+0.40, 1.24, +0.42)** (row 1) | 0.1 cm |
| `pose_touch_2` | at **(+0.40, 0.98, +0.42)** (row 2) | 0.1 cm |
| `pose_kneel` | kneeling on her left knee, right foot forward (toes at z ≤ 0.43); **right palm flat on the socket at (−0.05, 1.15, 0.55)** | 0.2 cm |
| `pose_offer` | standing, right palm up and held out | the palm surface is at **(−0.20, 1.143, 0.45)**: 0.2 cm |
| **`crystal_mount`** (empty, child of `pose_offer`) | **(−0.20, 1.20, 0.45)**, identity | **0.0569 above the palm**: `nursery_crystal.glb` (origin = centre of mass, bottom 0.0569 below it) parented there stands on her palm (QA `_pose_offer_hand.png`) |

The touch poses depend on the row only, so any column's `echo_touch_mount_<c>` works. The reaching hand's
fingertip is placed exactly (the hand is built once, measured, and rebuilt at the corrected wrist).
QA: `_pose_touch_1_library.png` (the `seed_library` view, row 1 column 2 = drawer 6, the right seed),
`_pose_kneel_secret.png` (`secret` view), `_pose_offer_finale.png` (`finale` view with Strand's pose_offer).

## QA renders (`qa/blender/ch3/`)

Blender Cycles (≤ 32 samples, ≤ 960 × 640, 2 threads); QA material only, not Godot screenshots. "clay" = lit
grey-white, "ghost" = the Chapter 2 approximation of `echo.gdshader` (additive fresnel glow, back faces culled).

| Model | Renders |
|---|---|
| echo_operator | `echo_operator_<pose>.png` (clay), `_<pose>_ghost.png`, `_pose_reach_hand / _hand2`, `_pose_pull_hand / _hand2`, `_pose_knob_hand / _hand2` (contact close-ups with lever / knob proxies), `_pose_reach_port_a`, `_pose_pull_port_b`, `_pose_knob_port_c`, `_pose_idle_port_c_lever5`, `_pose_done_desk_view` (in context) |
| echo_welder | `echo_welder.png`, `_2` (clay), `_3` (torch and hands), `_4`, `_5` (ghost), `_6` (`port_b_mem` view at transformer_1) |
| echo_technicians | `echo_technicians_tech_a.png`, `_2`, `_3` (ghost), `_4` (clipboard); the same for `tech_b` (`_4` = the valve hand); `_5` (`port_a_mem` view) |
| echo_strand_rail | `echo_strand_rail_pose_rail.png`, `_2`, `_3` (ghost), `_5` (`port_c_mem`); `_pose_offer.png`, `_2`, `_3`, `_4` (fist and fork), `_5` (`finale`) |
| echo_leyla_1998 | `echo_leyla_1998_<pose>.png` (clay) and `_<pose>_ghost.png` for all five, `_pose_touch_<r>_hand` (fingertips on a drawer proxy), `_pose_kneel_hand`, `_pose_offer_hand` (with the nursery crystal), `_pose_touch_1_library`, `_pose_kneel_secret`, `_pose_offer_finale` |

## Deviations from the contract and choices

- **One closed mesh per pose:** the head and hands are boolean-unioned into the body (the Chapter 2 echoes kept a
  separate `echo_head`; §10 says none is needed). Boolean crumbs under 60 vertices are deleted.
- **"Origin between the feet" vs the operator's mounts.** The operator's mounts are fixed standing spots, so the
  origin stays there and the feet move: `pose_idle` and `pose_knob` stand **0.10 m behind** it, `pose_done` **0.25 m
  behind** ("a step back"). At `op_mount_knob` the desk front is only 0.07 ahead of the origin, so any standing figure
  meets it; `pose_knob` leans over from the hips and still puts its toes 1.5 cm into the desk front at floor level.
  If `control_desk` has a toe recess (≥ 0.03 deep) this disappears; otherwise group C could move `op_mount_knob`
  0.02 back (the hand then reaches 0.02 further, within the pose's slack).
- **Operator left hands** rest flat on the desk top in `pose_reach`, `pose_pull` and `pose_knob` (palm y 0.872): a
  hand hanging forward would have gone into the desk.
- **tech_b's valve and tech_a's gauge** are not in the contract: I chose a handwheel centre (−0.04, 0.40, 0.26) and
  a gaze target (−0.05, 1.45, 0.20); group D can place the dead autoclave's valve and gauge there.
- **`crystal_mount` sits 0.0569 above Leyla's palm** so the item model (origin at its centre of mass) stands on
  the palm instead of sinking into it. The contract calls the point "in her right palm"; the palm is under it.
- **Leyla 1998 has five poses** (three touch, kneel, offer), not six; the file is LEYLA_FILE tris against 40,000.
- **The welder's origin** is on the floor between his kneeling knee and his front foot (he has no "between the
  feet" while kneeling).

## Notes for the game code

- Show one pose object at a time (`set_present`), all others hidden; the empties follow their pose.
- `torch_tip`, `fork_mount`, `crystal_mount`: parent the spark emitter / `strand_fork` / the crystal with an
  **identity** transform.
- Shadows: echoes never cast (`RoomBase.tune_shadows`, §1.5).
