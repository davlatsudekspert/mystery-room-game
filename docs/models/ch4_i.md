# Chapter 4 group I: the light echoes (measured results)

Contract: `docs/models/ch4.md` §0, §1, §2, §9, §11, §12, §13.11. Models: `echo_crowd`, `echo_named`, `echo_strand_desk`, `echo_leyla_1998_lift`, `echo_leyla_1998_lens`, `echo_tech_panel`, `echo_tech_wheels`, `echo_clerk_post`.
Existing (untouched): the Chapter 2 / 3 echoes, in particular **`echo_leyla_1998.glb` (Chapter 3: poses `pose_touch_0..2`, `pose_kneel`, `pose_offer`) stays as it is**: the Chapter 4 Leyla is two new files.
Scripts: `tools/blender/models/<name>.py`; helpers `tools/blender/lib_ch4_echo.py` (the **low-poly figure kit** `lp_figure`, the retrying boolean union `make_pose`, the grip / contact reports and the QA ghost helpers) and
`tools/blender/lib_ch4_echo_staff.py` (the 1979 staff of the detailed figures: coats, trousers / stockings, fists, heads, the clerk's eyeshade) on top of `lib_echo.py`, `lib_ch2_echoes.py` and `lib_ch3_echoes.py` (never edited); build list
`tools/blender/build_lists/ch4_i.txt`. QA renders: `qa/blender/ch4/echo_<name>.png`, `_2` (and `_3`, `_4` for the two multi-figure files).

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [-- --only <poses>]
```

Everything is **ONE closed mesh per pose or figure with ONE material slot, `M_Echo`** (the scene puts the `echo.gdshader` ShaderMaterial on it as `material_override`), smooth normals, box UVs, origin on the floor between the feet, the figure faces **Godot +Z**, **−X = its right**.
Checked on every GLB: `check_glb_names.py` passes; a pure-numpy re-read of the GLBs (`python3 -I qa/blender/ch4/echo_check.py game/assets/models/echo_*.glb`: welded edges used exactly twice, signed volume > 0 = outward faces, material `M_Echo` only) reports **0 problems on all 36 meshes**.
The review renders show each figure with the in-game look (`game/src/fx/echo.gdshader` re-created in Cycles: back faces culled, additive fresnel rim, scanlines) on a near-black background, plus a context render from a contract camera.

## Summary

| Model | Tris (budget) | Meshes | Poses / figures | GLB | QA renders (`qa/blender/ch4/`) |
|---|---|---|---|---|---|
| `echo_crowd` | 448 / 450 / 450 (450 each, 1,400 file) = **1,348** | 3 | `pose_a`, `pose_b`, `pose_c` (one figure) | `echo_crowd.glb` (58 KB) | `echo_crowd.png` (the 3 poses), `_2` (33 instances on the rings, `bridge` camera) |
| `echo_named` | 24 x 1,198 – 1,200 (1,200 each, 29,000 file) = **28,798** | 24 | 8 figures x `_a`, `_b`, `_c` | `echo_named.glb` (1.0 MB) | `echo_named.png` (all `_a`), `_2` (`_b`), `_3` (`_c`), `_4` (`_a` from behind) |
| `echo_strand_desk` | **4,894** (5,000) | 1 | `echo_strand_desk` | `echo_strand_desk.glb` | `echo_strand_desk.png`, `_2` (at the desk, lever, over his shoulder) |
| `echo_leyla_1998_lift` | **7,400** (8,000) | 1 | `pose_lift` | `echo_leyla_1998_lift.glb` | `echo_leyla_1998_lift.png`, `_2` (`lift_chalk` camera) |
| `echo_leyla_1998_lens` | 5,234 + 5,236 + 5,308 = **15,778** (8,000 per pose, 16,000 file) | 3 | `pose_walk`, `pose_walk_b`, `pose_seat` | `echo_leyla_1998_lens.glb` | `echo_leyla_1998_lens.png` (the 3 poses), `_2` (at the cradle) |
| `echo_tech_panel` | **5,934** (6,000) | 1 | `echo_tech_panel` | `echo_tech_panel.glb` | `echo_tech_panel.png`, `_2` (at Panel 0) |
| `echo_tech_wheels` | 5,944 + 5,744 = **11,688** (6,000 each, 12,000 file) | 2 | `tech_a`, `tech_b` | `echo_tech_wheels.glb` | `echo_tech_wheels.png`, `_2` (`handwheels` camera) |
| `echo_clerk_post` | **5,998** (6,000) | 1 | `echo_clerk_post` | `echo_clerk_post.glb` | `echo_clerk_post.png`, `_2` (inside the watch room) |
| **Group I in the `bridge` view** | | | crowd 1 `MultiMesh` draw + named 1 merged mesh (the scene merges the eight per pose) + the kept echoes in their zone (1 each) | | |

## Decisions the scene agent must know

- **Pose names.** `echo_crowd`: `pose_a`, `pose_b`, `pose_c` (meshes, one `MultiMesh` each swap). `echo_named`: `<who>_<pose>` with `<who>` = `operator`, `welder`, `archivist`, `scientist_f`, `scientist_m`, `technician_f`, `technician_m`, `clerk` and pose `a` | `b` | `c`
  (24 root meshes). **A `MultiMesh` holds one mesh, so the eight distinct named figures cannot be one `MultiMesh` ("one `MultiMesh` per pose" of the contract): draw them as eight `MeshInstance3D`s, or merge the eight meshes of a pose into one mesh at load** (what
  `array_hall_visuals.gd` does with `SurfaceTool.append_from`: one draw per pose, all 24 meshes have exactly one surface). `echo_tech_panel`, `echo_strand_desk`, `echo_clerk_post`: one mesh named as the file. `echo_tech_wheels`: `tech_a`, `tech_b`.
  `echo_leyla_1998_lift`: `pose_lift`. `echo_leyla_1998_lens`: `pose_walk`, `pose_walk_b`, `pose_seat`.
- **What the three crowd / named poses mean** (the same three beats for every figure): **a** = at work (the early minutes), **b** = the next task (the middle minutes), **c** = **03:17, the flash**: the figure shields its eyes, the torso turned away, the weight thrown back. Show `c` while the chronometer is on the sealed minute
  (and the frozen end of the replay); the crowd's `pose_c` is also the pose that "turns to the Sun".
- **Crowd instancing.** One mesh per pose, origin on the floor, facing +Z: the instance transform is position + yaw (`atan2(-x, -z)` faces the Core) + a **non-uniform scale jitter** (height 0.92 – 1.07, width 0.94 – 1.06) so 33 copies do not read as clones; the crowd figure is deliberately unisex (a knee-length lab coat with a wide collar, flared trousers, a feathered shoulder-length cut with sideburns) and 1.72 m high. The 8 named ones are the ones nearest the catwalk
  (the scene's rule): they are seen **from behind and from the side** (they face the Core), so every named figure has a readable back (long coat, hair, headgear, stoop); `echo_named_4.png` shows the `_a` row from behind.
- **Draw calls.** The contract counted "echoes (3 `MultiMesh`)": crowd 1 + named 1 (merged) + the in-zone kept echoes. The 8 separate named figures would be +7 draws; merge them.
- **Mounts (figure frame, Godot axes; nothing is baked into the meshes except the pose).**
  - `echo_strand_desk` on `echo_mount_strand` (desk-local (1.12, 0, 0.78), yaw 180): the right fist is round the lever's knurled grip **in the DOWN position**, grip centre figure **(−0.160, 1.142, 0.443)** = desk-local (1.28, 1.142, 0.337) (empty `grip_right` there). **The contract's (−0.15, 1.12, 0.62) is 0.18 further from him than the built `master_lever` grip**;
    the lifted grip (−80° about +X) is at figure (−0.16, 1.64, 0.82), out of reach of this pose. The left palm lies flat on the console's slope at figure (0.37, 1.05, 0.44).
  - `echo_tech_panel` on `echo_mount_tech_panel` (panel-local (0.8, 0, 1.0), yaw 180 = **world (−0.8, 0, 13.0), yaw 0**, because panel0 itself stands at yaw 180): the right fist on the stem of `IA_main_lever` in its **PULLED** position, grip centre figure (−0.04, 0.75, 0.50) (empty `grip_right`); with the lever upright
    (rest) the ghost's hand is 0.3 m from it. The stem is 30° above horizontal and points at him.
  - `echo_tech_wheels`: `tech_a` on `echo_mount_wheels_1`, `tech_b` on `echo_mount_wheels_2` (both yaw 180). **Neither can reach a wheel from the mount** (axis figure (±0.70, 1.30, 0.65), nearest rim point 0.455 to the side), so both are frozen **reaching**: leaning in, the fingertips 2 – 4 cm from the rim point on the empties
    `rim_touch_tech_a` (−0.5425, 1.4877, 0.65) and `rim_touch_tech_b` (+0.5425, 1.4877, 0.65). `tech_a` (woman, bob) turns to her right toward wheel II, a clipboard in the left hand; `tech_b` (man, crop) turns to his left toward wheel III, the right hand on his hip.
  - `echo_clerk_post` on `echo_mount_clerk_post` (room-local (−2.95, 0.03, −0.35), yaw 180): right fist over the send lever's ball (rest, upright) at figure (−0.375, 1.05, 0.425) (empty `lever_grip`), left hand over the destination knob's front at (0.19, 1.00, 0.42) (empty `dial_touch`).
    **Correction to `ch4_g.md`: the clerk's world position is (13.05, 0.03, −2.95), yaw 90 (x = 12.7 − z_local = 12.7 + 0.35); 13.55 would put him inside the station (its front plane is x = 13.45). `array_hall_data.gd`'s fallbacks for `clerk_post` (x 13.55) and `tech_panel` (x +0.8 instead of −0.8) are wrong;** the code uses the mount empties first.
  - `echo_leyla_1998_lift` on `echo_mount_leyla_lift` (−3.4, 0, 17.0), yaw 0: she faces the chalk, which is at figure (0.40, 1.50, 1.18) (empty `chalk_target`); her left index finger points at it (fingertip (0.285, 1.424, 0.582), 0.61 m from the chalk centre). From the `lift_chalk` camera (−2.9, 1.55, 15.4) she stands between the camera and the chalk, seen from behind (`echo_leyla_1998_lift_2.png`).
  - `echo_leyla_1998_lens`: the lens (Ø 0.0696) stands on her **right palm, leaning back against her fingers, its face toward her**, in all three poses; the empties `lens_mount_walk`, `lens_mount_walk_b`, `lens_mount_seat` (children of their pose) sit at the lens centre with the orientation of `cradle`'s `lens_mount`, so `crystal_lens.glb` parented there stands on her palm.
    **`pose_seat`: lens centre figure (−0.10, 1.3135, 0.45), which is exactly the cradle's `lens_mount` (0, 3.8135, 0.6266) when her origin is at world (−0.10, 2.5, 1.0766), yaw 180** (she stands on the player's side of the cradle, 0.45 m from the socket; the lens's top rim is at y 1.345, the contract's hand point (−0.10, 1.35, 0.45)).
    The other reading of the contract's numbers (origin (0.10, 2.5, 0.17), yaw 0, on the Core side) would put her inside the pedestal (r 0.55, 1.1 high). The walk: alternate **`pose_walk` (left foot forward) and `pose_walk_b` (right foot forward)** about every 0.35 s while the code moves her, then `pose_seat`; the lens is on her palm at (−0.12, 1.15, 0.36) while she walks.
    There is no rig: the three key poses are enough for the 1 – 2 m between the Core and the cradle.
- **Hair, heads and the face.** The detailed figures (`echo_strand_desk`, both Leylas, the three technicians, the clerk) reuse the Chapter 2 / 3 heads (Strand's beard and fringe, Leyla's swept-back hair and bun a little older, the scientists' bob and side-parted hair, the welder's crop) at 1,300 – 1,850 triangles: a face reads as a face at 2 m but it is coarse
  (on Leyla a ring-shaped crease on the forehead shows in the fresnel look; it is inherited from the Chapter 3 face pipeline and is in the Chapter 3 originals too). The low-poly figures have no faces at all (a skull, a jaw, a nose, hair and headgear shapes).
- **Imported node names (checked with `godot --headless --path game -s qa/blender/ch4/echo_check.gd`).** All eight files load; every mesh has one surface and sits at the identity transform. In the single-figure files the mesh node carries the file's name (`echo_strand_desk`, `echo_tech_panel`, `echo_clerk_post`),
  so Godot names the imported ROOT `<file>2` (`echo_strand_desk2`): find the mesh by its name below the root (`ModelUtil.find(inst, "echo_strand_desk")`), not the root. The multi-pose files keep their pose names (`pose_a`, `welder_c`, `pose_walk_b`, `tech_a`, …) and the empties theirs (`grip_right`, `rim_touch_tech_a`, `lens_mount_seat`, `lever_grip`, `dial_touch`, `chalk_target`).
- **No texture, no vertex colour, no skeleton.** The scene's shader is the whole look. `M_Echo` must be overridden (`material_override`): the slot has no `.tres` of its own (`M_Echo_Fallback.tres` is the placeholder).
- Nothing tapped is in these meshes: the kept echoes (`tech_panel`, `tech_wheels`, `clerk_post`, `leyla_lift`) need the scene's tap areas (about 0.9 x 1.7 x 0.9 around the figure); the figures have no colliders.

## echo_crowd.glb (1,348 tris)

One unisex 1970s staff figure (knee-length lab coat with a wide collar, bell-bottom trousers, shoes, a feathered shoulder-length cut with sideburns), 1.72 m high, built by `lp_figure` (a coat loft from the Chapter 3 ring table, IK arms and legs, ellipsoid hands and shoes, a stylised head, voxel-united at 2 cm, decimated to 450). Feet exactly on y = 0.

| Node | Tris | Pose | Bounds (x, y, z) |
|---|---|---|---|
| `pose_a` | 448 | at ease: weight on one leg, a **clipboard hanging from the right hand**, the left hand in the coat pocket, head up | (−0.263, 0, −0.128) … (0.249, 1.718, 0.186) |
| `pose_b` | 450 | **reading**: the clipboard held at the chest in both hands (a 0.24 x 0.32 board), head bowed over it | (−0.308, 0, −0.143) … (0.295, 1.695, 0.349) |
| `pose_c` | 450 | **03:17**: torso turned 34° away, the right forearm across the eyes, the left arm bracing out, the weight on the back foot | (−0.294, 0, −0.214) … (0.441, 1.724, 0.268) |

## echo_named.glb (28,798 tris, 24 meshes)

Eight distinct silhouettes (heights, coats, headgear, props), all from the same kit; every mesh 1,198 – 1,200 tris, closed, feet on y = 0. Heights in the table are the `_a` pose.

| Who (earlier chapter) | Height | Silhouette | `_a` | `_b` | `_c` |
|---|---|---|---|---|---|
| `operator` (Ch. 3, the Choir Hall) | 1.81 | work coat, **flat cap with a peak, headphones round the neck** | looking up at the globes, the right hand in a pocket | leaning over the desk, the right hand on a lever, the left on the desk | both forearms up over the face |
| `welder` (Ch. 3) | 1.80 | **stocky, hip-length jacket, big gauntlets, heavy boots, the mask flipped up on the head** | the torch down in the right hand, the left on the hip | the right hand up to the mask, the left hand at the hip | right forearm across the eyes |
| `archivist` (Ch. 2) | 1.64 (stooped from 1.70) | **long coat to the calves, stooped, thin, receding hair, spectacles** | an open book held at the belly | a card raised to read, the left hand at the belly | the right arm up while stooping |
| `scientist_f` (Ch. 2) | 1.71 | woman, knee-length coat, the 1970s bob | an **archive box against the right hip** | the box held up in front | the box raised as a shield |
| `scientist_m` (Ch. 2) | 1.84 | the **tallest**, side-parted hair | reading an open ledger | the right arm out, pointing | both forearms up |
| `technician_f` (Ch. 3) | 1.61 | the **shortest**, hair in a bun | a clipboard held up, writing | one arm up (pointing at the ceiling), the clipboard at the side | the forearm across the eyes |
| `technician_m` (Ch. 3) | 1.70 | broad, cropped hair | a wrench hanging from the right hand, the left hand at the pocket | working at chest height with the wrench in both hands | the right forearm across the eyes |
| `clerk` (Ch. 4) | 1.77 | **slim, short jacket, green eyeshade** | a ledger under the left arm, a pen in the right hand | bent over a table, writing | both hands up over the face |

## echo_strand_desk.glb (4,894 tris)

Strand's Chapter 3 figure (the face, beard and fringe of `echo_strand_standing`, the long coat) at 1.72 m: body upright and leaning back, the torso turned 14° to the lever, the right arm nearly straight, the left palm flat on the console, the head turned to the lever and down. Bounds (−0.353, 0, −0.243) … (0.424, 1.715, 0.539).
Grip check (`lib_ch4_echo.grip_report`, samples along the lever's axis ±6 cm): none of the five samples lies inside the solid, the nearest surface is 0.5 – 1.2 cm from the grip centre (the fist closes round the 1.8 cm bar; the fingers clip it by up to 0.7 cm). `grip_right` (empty).

## echo_leyla_1998_lift.glb (7,400 tris) and echo_leyla_1998_lens.glb (15,778 tris)

Leyla in 1998, about 45: the face lineage of `echo_leyla_standing` a little older, a **field coat to mid-thigh with a stand collar, a belt and four patch pockets**, trousers and field boots (the functions of `echo_leyla_1998.py`, imported). `pose_lift` 7,400 (bounds (−0.267, 0, −0.159) … (0.321, 1.677, 0.582)): torso turned 16°, head 19° to her left, the left arm raised and pointing at the chalk.
The lens file: three poses of about 5,300 (head 1,700, body 2,750, hands 320 each): `pose_walk` 5,234 (left foot forward, the right heel raised, the lens on the right palm at the chest, the left arm swinging back), `pose_walk_b` 5,236 (the opposite stride, the left arm forward), `pose_seat` 5,308 (the right arm out with the lens at the cradle, the left palm cupped beside it).
The palm under the lens: the nearest surface is 0.2 cm from the lens's lowest rim point. Bounds: `pose_walk` (−0.314, 0, −0.369) … (0.252, 1.642, 0.437), `pose_walk_b` (−0.307, 0, −0.23) … (0.241, 1.642, 0.476), `pose_seat` (−0.328, 0, −0.186) … (0.222, 1.672, 0.528).

## echo_tech_panel.glb (5,934), echo_tech_wheels.glb (11,688), echo_clerk_post.glb (5,998)

1979 staff in the Chapter 2 / 3 coats: a **man** bent forward over the panel's low main lever (tech_panel; the scientists' side-parted hair; right fist round the stem, left hand braced on his thigh; bounds (−0.228, 0, −0.279) … (0.263, 1.66, 0.551)); a **woman** (`tech_a`, 5,944, bounds (−0.543, 0, −0.173) … (0.326, 1.658, 0.64)) and a **man** (`tech_b`, 5,744,
bounds (−0.422, 0, −0.181) … (0.568, 1.737, 0.664)) reaching toward the wheels; the **clerk** (5,998, bounds (−0.48, 0, −0.174) … (0.317, 1.742, 0.46)) in a short office jacket with a green **eyeshade** (a band and a stiff brim), the same side-parted hair, sending the post.
Contacts: `echo_tech_panel` grip report: four of five samples along the stem are outside the solid (one end sample 0.6 cm inside the fingers), nearest surface 1.3 cm from the grip centre; `echo_clerk_post`: 1.5 cm (lever ball), 1.3 cm (knob); `echo_tech_wheels`: fingertips 4.3 cm (`tech_a`) and 2.3 cm (`tech_b`) from the rim point.

## Lessons of this group

- **A hand-built figure at 450 tris is a kit job, not a sculpt.** Lofts and ellipsoids (the coat from the Chapter 3 ring tables, IK limbs, a head with a hair / headgear shape list) voxel-united at 1 – 2 cm and quadric-decimated with the head and hands weighted keep a silhouette that reads at 14 m; no face is needed.
  The union must be a voxel remesh (no hidden inner faces: the additive shader would show them) and the finished feet are snapped to y = 0.
- **The exact boolean of the detailed pipeline can return an EMPTY mesh for one specific pose** (seen at Strand's `yaw_chest` = −15° exactly; −14° and −16° are fine). `lib_ch4_echo.make_pose` (the Chapter 3 `make_pose` with a rolled-back, nudged retry) is used by every detailed figure; if it still fails, change a pose angle by 1°.
- **A legless figure is a union problem**: a coat that stops at the hip (the clerk's jacket) needs trousers that start under it (`man_legs(top_z=0.86)`), or the legs float as separate shells (`mesh_report` shows `shells: 3`).
- **A fist round a bar must be sized to the bar**: finger length / curl gives a loop radius of about 0.027 m for curls summing 140°; the wrist is `centre − F x 0.088 − N x 0.030`. `grip_report` samples the bar's axis and fails the grip if a sample is inside the solid.
- **Heads at 1,300 tris are coarse** (the lips and nose bridge show as bright creases under the fresnel look); 1,700 – 1,850 is the practical floor for a face seen at 2 m.
- Reach: a figure at a mount cannot touch a wheel 0.65 m ahead and 0.7 m to the side, nor the upright main lever 0.76 m ahead; frozen REACHING (fingertips within a few cm) reads better than a grip on air and is how the Chapter 4 echoes are posed.

## Files and commands

`game/assets/models/{echo_crowd,echo_named,echo_strand_desk,echo_leyla_1998_lift,echo_leyla_1998_lens,echo_tech_panel,echo_tech_wheels,echo_clerk_post}.glb(+.import)`, `qa/blender/ch4/echo_*.png`, `tools/blender/models/echo_{crowd,named,strand_desk,leyla_1998_lift,leyla_1998_lens,tech_panel,tech_wheels,clerk_post}.py`,
`tools/blender/lib_ch4_echo.py`, `tools/blender/lib_ch4_echo_staff.py`, `tools/blender/build_lists/ch4_i.txt`, `qa/blender/ch4/echo_check.py` (GLB geometry check) and `qa/blender/ch4/echo_check.gd` (Godot load check). Rebuild: `tools/blender/build_all.sh` (the three heaviest scripts take 1 – 2 minutes each with renders, 30 – 60 s with `--no-render`); re-import: `godot --headless --path game --import`.
