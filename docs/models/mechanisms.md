# Mechanism models: parts and animation spec

These are the hero mechanisms and small items built by `tools/blender/models/*.py` and listed in `tools/blender/build_lists/mechanisms.txt`. They are exported to `game/assets/models/<name>.glb`.

## Conventions

All coordinates on this page are in **Godot terms**, local to the model root, in metres. The conversion is Godot = Blender (x, z, −y).

- **Front:** a model's front faces **+Z**.
- **Origin:** every `IA_*` part (and every other animated part) is its own node, with its origin at the pivot and an **identity rotation at rest**.
- **Angles:** angles are relative to the rest transform. This matches `Lab7Visuals._rot(node, axis, deg)`, which computes `rest.basis * Basis(axis, deg)`.
- **Sign:** a positive angle is counter-clockwise when you look down the +axis toward the origin.
  - About **+Y**, a positive angle turns +Z toward +X.
  - About **+X**, a positive angle turns +Z toward −Y, so a lever that points at the player moves **down**.
  - About **+Z**, a positive angle is counter-clockwise as the player sees it.

### Colliders
`ModelUtil.build_colliders` puts one AABB box on each mesh, and the first hit wins. So the static parts of hollow models are **split into slabs**:
- `safe_frame_l/r/t/b`, `safe_back`, `safe_shelf` and `safe_drawer`
- `panel_case_l/r/t/b/back`, plus separate fittings meshes

This way no static box covers the switches, the keys or the inside of the safe. Static parts that hang at an angle, such as `panel_door`, keep the rotation on their node, so their boxes stay tight.

## flip_clock.glb (3,419 tris, static)
| Part | Pivot | Motion |
|---|---|---|
| `clock_body` | (0, 0, 0), at the base centre | static |
| `clock_face` | (0, 0.081, 0.043) | static plane, faces +Z. Uses `M_Decal_ClockFace` with a planar UV at aspect 512:224. Shows 03:17 |

## gear_box.glb (5,932 tris)
The box measures 0.26 w × 0.18 d × 0.125 h. With the knobs and gears it is 0.268 × 0.211 × 0.141. Its origin is at the base centre.

| Part | Pivot | Axis | Rest → active |
|---|---|---|---|
| `IA_box_lid` | (0, 0.092, −0.093), on the back hinge | local **X** | 0° closed → **−105°** open (the front lifts; negative is correct) |
| `IA_gear_0..2` (children of the lid) | lid-local (−0.072 / 0 / +0.072, 0.036 / 0.042 / 0.036, 0.097). The middle wheel sits one deck higher | local **Y** | Each puzzle position is **60°**. At rest the pointer points toward −Z (the back), which is position 0. The lead uses −60° × k (clockwise from above). Neighbouring wheels never intersect at any angle |
| `IA_knob_0..2` | (−0.072 / 0 / +0.072, 0.052, 0.093), on the escutcheon face | local **Z** | Push: translate −Z by 3 mm, then back. Optionally turn 60° about Z |
| `battery_anchor` | empty at (0, 0.05, 0) | — | Seat for the battery cell. Lies along X |

## wall_safe.glb (5,823 tris)
- **Size:** 0.50 × 0.50, 0.30 deep. The handle sticks out 0.052.
- **Origin:** the centre of the front face of the frame, flush with the wall. Place it at (2.2, 1.25, 2.5) with yaw 180°.

| Part | Pivot (model-local) | Axis | Rest → active |
|---|---|---|---|
| `IA_safe_door` | (−0.2235, 0, +0.0105): the **left** hinge axis seen from the front, at mid-height | local **Y** | 0° closed → **−110°** open. The door swings out toward the player and to the player's left, clear of the wall. This matches `SAFE_DOOR_OPEN_DEG = −110` |
| `IA_key_1..9`, `IA_key_0`, `IA_key_clear` (C), `IA_key_enter` (↵), children of the door | Key base centres. In model space, columns are at x = −0.139 / −0.093 / −0.047 and rows at y = +0.041 (1 2 3), +0.0015 (4 5 6), −0.038 (7 8 9), −0.0775 (C 0 ↵). The base plane is at z = +0.018 and the key tops are at +0.0255 | local **Z** | **Press:** translate −Z by **3 mm** over about 60 ms, then return. Keys are brass with cream enamel faces and black digits. C is crimson and ↵ is green |
| `safe_display` (child of the door) | Centre of the display face, at (−0.093, 0.096, 0.018) in model space | normal +Z | Smoked glass (`M_Glass_Dark`), 0.116 × 0.034. The current Label3D at local (0, 0, 0.004), font 48 × pixel 0.0006 (about 0.029 m em) fits "1 2 3 4", "_ _ _ _" and "OPEN" |
| `IA_safe_handle` (child of the door) | Axis at the door face, at (0.112, −0.028, 0.014) in model space | local **Z** | 4-spoke wheel. **Unlock = −90°**, which is clockwise as the player sees it. Play it before the door opens. The wheel has 90° symmetry, so you may leave it there |
| `safe_bolts` (child of the door) | (0.203, 0, −0.036) in model space | local **X** | Optional. Three chrome bolts on the free edge. **Retract:** translate −X by **0.024** together with the handle turn. They are hidden inside the frame while the door is closed |

**Inside the safe** (model-local; it is empty, so add items to it):
- The opening is x, y ∈ ±0.217.
- The door's back face is at z = −0.068 when closed, and the back wall is at z = −0.272.
- **Floor:** the felt top of the internal deposit drawer, at **y = −0.115**. It is usable over x ∈ ±0.21, z ∈ [−0.27, −0.09].
- **Shelf:** the felt top is at **y = +0.035**, over z ∈ [−0.27, −0.09].
- The lead's current item offsets already fit:
  - key, lens and letter go on the floor (their y is −0.115 plus half the item's height);
  - the valve goes on the shelf.

## panel7.glb (5,968 tris)
- **Cabinet:** 0.70 w × 0.90 h × 0.22 d. The back is at z = 0.
- **Origin:** the centre of the back plane, at the cabinet's mid-height. Place it at (3.0, 1.45, −1.3) with yaw −90°.
- **Plate coordinates** are model (x, y). The plate's front face is at **z = +0.034**.

| Part | Pivot (model-local) | Axis | Rest → active |
|---|---|---|---|
| `panel_plate` | (0, 0, 0.034), faces +Z | — | `M_Decal_PanelDiagram`. Its exact UV is u = (x + 0.30)/0.60, v = (y + 0.40)/0.80. It is upright and not mirrored, so plate coordinates match the 900×1200 image 1:1 |
| `lamp_0..3` | (−0.195 / −0.065 / +0.065 / +0.195, +0.30, 0.034) | — | Faceted jewel domes 35 mm across. They use `M_Lamp_L/G/A/V`. Each one is the **jewel only**, a single surface, so `_lamp()` / `set_emission` lights just the glass. The chrome bezels are static |
| `IA_switch_0..4` | (−0.22 / −0.11 / 0 / +0.11 / +0.22, −0.06, 0.0465), on the toggle axle | local **X** | **Rest 0° = OFF:** the lever points at the player, 35° below horizontal. **ON = −70°:** the lever is 35° above horizontal. A cream dot on each base marks the ON side |
| `IA_main_lever` | (0, −0.27, 0.053), on the breaker shaft | local **X** | **Rest 0° = OFF:** the fork is 40° below horizontal, toward "0". **ON = −80°:** 40° above, toward "1" |
| `main_handle` (child of `IA_main_lever`) | Grip centre, lever-local (0, −0.048, 0.057) | — | Bakelite grip between the fork eyes. Toggle its visibility only; it moves with the lever. The bare eyes show that the handle is missing |
| `gauge_needle` | (−0.25, +0.143, 0.0455) | local **Z** | **Rest = 0 V**, with the needle at the upper left. **Angle = −90° × V / 250**, so 220 V = **−79°**, turning clockwise. The red band starts at 220 V. Tween it when the power comes on |
| `panel_door` | Hinge at (−0.357, 0, 0.234) | Y | Static. It is open at −100° on the left side (north in the room). Its far edge reaches about 0.93 m from the wall at world (2.07, −1.78) |

> **The lead must update these constants.** The rest pose is DOWN = OFF, as `ROOM_LAYOUT.md` requires, so the symmetric ±35°/±40° values in `lab7_visuals.gd` are wrong for this model. Use:
> - `SWITCH_OFF_DEG = 0.0`
> - `SWITCH_ON_DEG = -70.0`
> - `LEVER_OFF_DEG = 0.0`
> - `LEVER_ON_DEG = -80.0`
>
> With the current values, OFF would show the lever pointing up.

**Gauge position:** the gauge is at (−0.25, +0.15), 3 cm left of the nominal (−0.22, +0.15). At −0.22 a 6 cm gauge would cover the trace for lamp L at x = −0.195 and the junction at y ≈ +0.135. At −0.25 it is clear of every trace.

## mirror_stand.glb (3,993 tris)
- **Shape:** a brass tripod 0.50 across, 1.27 tall.
- **Origin:** the base centre. Place it at (1.6, 0, 1.6). The second instance (B) is at (1.6, 0, 0.12).

| Part | Pivot | Axis | Rest → active |
|---|---|---|---|
| `IA_mirror_mount` (turntable + U-fork gimbal) | (0, **1.15**, 0), the mirror centre on the column axis | local **Y** | At rest (0°) the mirror's normal points toward **+Z**. A positive angle turns the normal toward +X, counter-clockwise from above. Each step is **45°**: 8 engraved ticks on the turntable line up with the fixed red index at the front of the bearing. The lead's −45° × k is consistent with this |
| `mirror` (child of the mount) | (0, 0, 0), local to the mount (the mirror centre) | — | Round mirror 0.22 m across. The chrome face points +Z and the back is brass, engraved with the Institute emblem. It hangs on trunnion pins in the fork. **Hide it on stand B** until the mirror is mounted. The empty fork is the bracket |
| `stand_base` | — | — | static |

## light_sensor.glb (3,736 tris)
- **Size:** a wall plate 0.30 × 0.30 with a brass housing **0.256** across. The rim face is 0.064 off the wall. A braided cable leaves the housing downward and goes into the wall below the plate.
- **Origin:** the centre of the back plane, on the eye axis. Place it at (3.0, 1.15, 0.12) with yaw −90°, so the eye sits at the beam height.

| Part | Pivot | Notes |
|---|---|---|
| `sensor_eye` | (0, 0, **0.050**), facing +Z | Ground-glass disc (`M_Glass_Frosted`), 0.170 across. The 8-blade iris leaves an aperture about **0.163** across. When the beam arrives, glow it (for example `set_emission(..., Color("cff6ff"))`). `ROOM_LAYOUT.md` suggested `M_Emissive_Lumen`; the brief asked for frosted glass |
| `sensor_body` | static | Includes the housing, the overlapping brass iris blades, and a selenium cell behind the glass. The Institute emblem (a ring plus a meridian at 12 and 6 o'clock) is inlaid in cream enamel on the rim |

## lumen_shard.glb (96 tris)
- **Shape:** a quartz-like cluster of 4 terminated crystals with a broken base. It measures 0.056 × 0.033 × 0.024, lying on its side.
- **Material:** a single mesh, `lumen_shard`, using `M_Crystal` with faceted shading.
- **Origin:** the centre of mass. The **lowest point is 0.011 below the origin**, so to rest it on a surface, place the origin at surface y + 0.011. The current floor spots use y = 0.02, which makes it float 9 mm.

## Materials
- **New slot `M_Glass_Dark`**, used for `safe_display`. Its resource is `game/assets/materials/M_Glass_Dark.tres`.
- **Other slots:** everything else uses existing slots.
  - `M_Felt` lines the safe's shelf and drawer top.
  - `M_Enamel_Cream` is used for the key faces, the emblem inlay and the gauge dial.
