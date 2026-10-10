# Chapter 3 group C: desk, ports, cabinets (measured results)

Contract: `docs/models/ch3.md` §0, §1.3, §2, §5, §10 (operator contact points), §13. Models: `control_desk`,
`switch_cabinet` (×3), `interlock_plate`, `inspection_port` (×3). Scripts: `tools/blender/models/<name>.py`, shared
helpers in `tools/blender/lib_ch3_bc.py` (groups B and C; on top of `mrlib`, `lib_mech`, `lib_arch`, `lib_ch2_vault`,
`lib_ch3_a`, `lib_ch3_symbols`, none edited), build list `tools/blender/build_lists/ch3_c.txt`.

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [--shots=1,2,...]
```

Every script builds in Godot axes (the `lib_ch2_vault` G-frame), converts to Blender axes before parenting, exports
`game/assets/models/<name>.glb` with a lean material set (Godot swaps the `M_*` slots for its `.tres`) and **reads the
GLB back**: required node names, parents, model-space positions (1 mm), identity rest rotations, mount rotations,
triangles, surfaces (mesh nodes × primitives) and material slots against §13, plus `check_glb_names.py`. All four pass
(`VERIFY OK`); the two over-cap surface counts are explained under Deviations.

QA renders: Cycles, 32 samples, 960 × 640, 2 threads, the real `shell_choir.glb` and the west `blast_door.glb` imported,
the §1.5 Choir lights (shadowed key spot, six work omnis, the camera's `focus_fill`), cameras from the §2 views (Godot
position, target, vertical FOV). Blender renders only, not Godot screenshots. Jewels and lamps get a QA-only emissive
override where the code would light them; the operator is the real `echo_operator.glb` with the Chapter 2 ghost look.

All coordinates are **Godot, model-local, metres**; models face +Z; angles follow §0.

## Summary

| Model | Tris (budget) | Surfaces (cap) | Slots (≤ 4) | GLB | QA renders (`qa/blender/ch3/`) |
|---|---|---|---|---|---|
| `control_desk` | 8,921 (9,000) | **15 (14)**, 13 once the lockout tag is hidden | 4 | `game/assets/models/control_desk.glb` | `control_desk.png`, `_2` … `_9` |
| `switch_cabinet` (×3) | 3,442 (3,500) | 13 in the file, **8 drawn** per cabinet (cap 8) | 4 | `game/assets/models/switch_cabinet.glb` | `switch_cabinet.png`, `_2` … `_5` |
| `interlock_plate` | 370 (600) | 2 (2) | 2 | `game/assets/models/interlock_plate.glb` | `interlock_plate.png`, `_2` |
| `inspection_port` (×3) | 1,944 (2,000) | 3 (3) | 3 | `game/assets/models/inspection_port.glb` | `inspection_port.png`, `_2` … `_4` |

---

## control_desk.glb (8,921 tris, 15 surfaces)

**Shape.** A grey-green painted steel start-up desk, 2.60 × 0.80, top 0.86: a top slab with a rounded nosing, pressed
front panels with the Institute mark in brass between the stiles, louvred back covers with brass screws, a brass cable
gland at the back, and a **5.5 cm deep, 10 cm high toe recess** along the operator side (the operator's `pose_knob`
toes clear the front at `op_mount_knob`, 0.07 in front of the desk). On the top, a raised lever plinth with brass
quadrant cheeks, a brass axle with end nuts and the painted-in numerals 1–5 under the levers; the knob box at the west
end, a pulpit with a sloped top so port C sees over it, brass position marks ○ ▲ ● ■ with index ticks, the lockout
staple, the flag bracket and the breaker contacts; the step-counter mast at the operator's left front corner with
square brass collars carrying the numerals 1–5 on four sides; a brass-bezelled lamp pedestal.

**Placement.** Free-standing at (−8.0, 0, 0.5), yaw 180: the front (+Z) faces north. Static bounds x ±1.30,
y 0 … 2.10 (the mast finial), z −0.402 … 0.405. The back (south) edge is 0.86 high; the knob box reaches 1.30 at
x 0.92 … 1.22 only.

| Node | Pivot / position | Materials | Notes |
|---|---|---|---|
| `control_desk` | (0, 0, 0) | Steel_Painted, Brass_Aged | static, 4,775 tris |
| `IA_lever_1..5` | (x_n, 0.95, 0.12), x_n = (n − 3) × 0.36 | Brass_Aged | hub on the axle, tapered stem with the latch catch, Ø 0.05 ball grip 0.27 above the pivot; **pulled = +50° about local +X** (`control_desk_9.png`, lever 3) |
| `IA_master_knob` | (1.07, 1.12, 0.07) | Bakelite | Ø 0.09 chicken-head pointer knob on a brass escutcheon, pointer at ○ (12 o'clock) at rest; **position p = −90° × p about local +Z** (`_4`: p = 2 → ●) |
| `step_globes` | (−1.20, 1.64, 0.30) | Enamel_Cream | one mesh, five Ø 0.13 globes at y 1.30 + 0.17 (k − 1); **COLOR_0 R = 0.2 k on globe k** (read back from the GLB buffer: 0.2 / 0.4 / 0.6 / 0.8 / 1.0, normalised ushort VEC4) |
| `IA_desk_hook` | (−1.00, 0.70, 0.41) | Brass_Aged | plate with two screws, the arm out along +Z to z 0.447 with an upturned tip |
| `desk_hook_mount` | child of the hook, local (0, −0.0416, 0.02) → model (−1.00, 0.6584, 0.43) | — | rot (90, 0, 0): ◆ hangs by its bow, face +Z; the arm passes through the key's Ø 3.2 mm hole (hole 0.0424 above the key origin, `ch3_g.md`) (`_8`) |
| `desk_live_lamp` | (0.80, 1.00, 0.30) | Enamel_Cream | dome jewel on the pedestal; code: dark / green |
| `lockout_tag` | (1.07, 0.98, 0.08) | Enamel_Cream, Bakelite | cream tag 0.05 × 0.072 on a black wire from the staple, a black padlock relief; the code hides it once `desk_armed` |
| `breaker_flag` | (1.07, 1.30, 0.0) | Enamel_Cream, Bakelite | semaphore disc on a stem, black bar; **trip = +70° about local +X** (`_4`) |
| `spark_origin` | (1.07, 1.32, −0.05) | — | empty above the breaker contacts |
| `op_mount_1..5` | (x_n − 0.15, 0, 0.62) | — | rot (0, 180, 0): the operator faces the desk |
| `op_mount_knob` | (0.92, 0, 0.47) | — | rot (0, 180, 0) |

**§1.3 fixed points** (checked by the script at the placement): lever grips (−8.0 − (n − 3) × 0.36, 1.22, 0.38),
master knob (−9.07, 1.12, 0.43), step globes x −6.80 / z 0.20 at y 1.30 … 1.98. All exact.

**Port sight lines** (`control_desk_5/6/7.png`): port A sees levers 1–2 and the globes past the desk's east end;
port B (catwalk) sees the whole lever row and the operator at lever 3; port C (gantry, pitch 60°) looks down on the
knob box, the knob at ● and the operator's `pose_knob`. The operator's left palm rests on the desk top in all three.

QA: `control_desk.png` (`desk` view, dead desk, tag on, ◆ on the hook), `_2` (`desk` view live: tag gone, ◆ taken,
lamp green, levers 4 and 2 pulled, two globes lit), `_3` / `_4` (knob box at the start / knob ●, flag tripped,
all levers down, five globes), `_5` (`port_a`, step 2, `pose_reach` at lever 2), `_6` (`port_b`, step 5, `pose_pull`
at lever 3), `_7` (`port_c`, `pose_knob`), `_8` (the ◆ on the hook), `_9` (lever frame, lever 3 pulled).

---

## switch_cabinet.glb (3,442 tris, 13 surfaces in the file, 8 drawn)

**Shape.** A painted steel cabinet 0.70 × 1.90 × 0.45 on a recessed 0.10 plinth: a front door with a pressed border,
three hinges and brass screws, side louvres, a top cap with two brass cable glands and conduits. On the front: the
lock ledge (x −0.26 … 0.02, y 1.10 … 1.13, to z 0.58) on two gussets with the brass lock housing underneath, the key
box with its brass bezel, flap hinge knuckles and the hanging pin, the isolator's brass dial plate (painted IEC marks
**I** at 12 o'clock, **O** at 9, a travel arc between them) and boss, the lamp bezel.

**Placement.** South wall, yaw 180, at (−7.4 / −8.3 / −9.2, 0, 4.0) = I / II / III. Static bounds x ±0.365,
y 0 … 2.075, z 0 … 0.58.

| Node | Pivot / position | Materials | Notes |
|---|---|---|---|
| `switch_cabinet` | (0, 0, 0) | Steel_Painted, Brass_Aged | static, 2,098 tris |
| `IA_lock` | (−0.12, 1.13, 0.52) | Brass_Aged | barrel plug Ø 0.04 with its rose on the ledge top, a counterbored keyway; **OFF = −90° about local +Y** |
| `lock_key_mount` | child of `IA_lock`, local (0, 0.004, 0) → (−0.12, 1.134, 0.52) | — | rot (90, 0, 0): the key stands blade down, bow face +Z; the collar rests in the counterbore |
| `lock_sym_diamond/_triangle/_circle/_square` | (−0.205, 1.13, 0.52) | Brass_Aged | 0.05 relief inlays on the ledge top, "up" away from the viewer; the code shows the cabinet's own (I ▲, II ◆, III ●) |
| `IA_key_window` | (−0.12, 1.53, 0.51) | Glass | 0.12 × 0.16 flap with a knuckle and a lip; **open = −100° about local +X** |
| `held_key_mount` | (−0.12, 1.46, 0.47) | — | rot (90, 0, 0): the held key hangs on the pin (pin axis y 1.4995: the four keys' hole centres sit 0.0387 … 0.0424 above the mount) |
| `IA_isolator` | (0.15, 1.28, 0.47) | Bakelite | 0.18 bar handle with a ridge on a hub, pointer up at I; **OFF = +90° about local +Z** (points at O) |
| `iso_lamp` | (0.15, 1.62, 0.46) | Glass | opal jewel; code: green ON / red OFF |
| `num_1` / `num_2` / `num_3` | (0, 1.76, 0.455) | Brass_Aged | 0.13 × 0.072 plates with the Roman numeral pierced through; the code shows the cabinet's own |

Drawn per cabinet: static 2 + lock + window + isolator + lamp + one numeral + one symbol = **8**. The §1.3 points:
lock (x_n + 0.12, 1.13, 3.48), window (x_n + 0.12, 1.45, 3.50) at yaw 180.

QA: `switch_cabinet.png` (`switch_room`, all three ON with the held keys ● ▲ ■ behind the glass and the interlock plate
above II), `_2` (`cabinet_1`, start), `_3` (`cabinet_1` with ◆ in the lock turned OFF: lock turned, window open,
▲ free, lamp red), `_4` (lock and window close-up), `_5` (isolator at O and the numeral).

---

## interlock_plate.glb (370 tris, 2 surfaces)

| Node | Position | Materials | Notes |
|---|---|---|---|
| `interlock_plate` | (0, 0, 0) | Steel_Dark | frame 0.99 × 0.54 (y 2.0 … 2.6) with a backing tray, a bead holding the plate, four slotted screws, two wall lugs; z 0 … 0.031 |
| `plate_image` | (0, 2.30, 0.015) | Decal_InterlockPlate | 0.90 × 0.45 quad facing +Z, UV 0..1 (u → +X, v → +Y; checked from the mesh), group A's `interlock_plate.png` |

Wall-mounted at (−8.3, 0, 4.0), yaw 180, above cabinet II. QA: `interlock_plate.png` (`interlock_plate` view), `_2`
(oblique).

---

## inspection_port.glb (1,944 tris, 3 surfaces)

**Shape.** A ship's-porthole in aged brass: mounting plate Ø 0.40 with six slotted screws, a barrel Ø 0.30 × 0.15 with
a base flange and a hoop, the front bezel that holds the lens, a hinge knuckle on the left and a wing-nut dog on the
right; the blackened knurled ring with two grip lugs; the crystal lens.

**Placement.** Origin = the back of the mounting plate, front +Z. A (−4.5, 0.85, 2.6) yaw −90 on the east wall;
B (−12.0, 4.55, 1.9) yaw 110 on the catwalk post's plate; C (−8.6, 5.15, 1.9) yaw 180, pitch +60 under the gantry
trolley. Bounds r 0.20, z 0 … 0.174.

| Node | Pivot | Materials | Notes |
|---|---|---|---|
| `inspection_port` | (0, 0, 0) | Brass_Aged | static, 1,136 tris |
| `IA_port_ring` | (0, 0, 0.125) | Steel_Dark | knurled ring r 0.142 … 0.163, z 0.104 … 0.146; code: −30° about local +Z per tap |
| `IA_port_lens` | (0, 0, 0.16) | Crystal | lens Ø 0.22, z 0.151 … 0.170; code: emission pulse while the loop plays |

QA: `inspection_port.png` (port A from the hall), `_2` (ring turned one step, lens pulsing), `_3` (port B on the
catwalk post), `_4` (port C under the gantry).

---

## Deviations from the contract

1. **`control_desk` has 15 surfaces (cap 14).** The lockout tag (cream tag, black padlock) and the breaker flag (cream
   disc, black bar) are the contract's own two-colour parts, so each is two surfaces; everything else is one material
   per part and the static desk is two (paint + brass). Once `desk_armed` hides the tag the desk draws 13.
2. **`switch_cabinet` keeps 13 mesh nodes in the file** (three numerals, four lock symbols) and draws 8 per instance
   once the code hides the alternatives, as §5 asks. The check in the script is against the drawn count.
3. **Toe recess.** `control_desk`'s front is set back 5.5 cm below y 0.10 (contract: "keep the back edge low", the
   recess is group H's request so `pose_knob` clears the front at `op_mount_knob`).
4. **Desk numerals are painted, not extruded** (flat brass on the plinth, flat paint on the four faces of each collar):
   the extruded glyphs alone cost 2,500 tris. They remain 3D geometry, language-neutral.
5. **Inspection-port ring lugs:** two grip lugs were added to the knurled ring so the cosmetic −30° steps read.

## Notes for integration

- `control_desk`: `desk_hook_mount` is a child of `IA_desk_hook` (local (0, −0.0416, 0.02)); the other empties are
  root-level. The code's `step_globes` shader reads COLOR_0.r. `spark_origin` sits 2 cm above the contacts, between
  them. `op_mount_*` carry the 180° yaw themselves: parent `echo_operator` with identity.
- `switch_cabinet`: `lock_key_mount` is a child of `IA_lock` and turns with it (the trapped key turns visibly);
  `held_key_mount` is root-level. Hide `num_*` and `lock_sym_*` per `CABINET_TAKES` as §5 says.
- `inspection_port`: `IA_port_ring`'s pivot is on the port axis at z 0.125; the lens pivot at z 0.16.
- Lamps and jewels use their glass / enamel slot (no emissive slot), as §0 asks; `ModelUtil.set_emission` duplicates
  the material per mesh, so shared slots are safe.
- Godot `.import` files for these GLBs were written by the lead's import; this group did not run Godot.
