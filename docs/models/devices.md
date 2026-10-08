# Device and inventory-item models: parts and animation spec

These models are built by `tools/blender/models/<name>.py` and listed in `tools/blender/build_lists/devices.txt`. Shared helpers live in `tools/blender/lib_devices.py`. Each model is exported to `game/assets/models/<name>.glb`.

Rebuild one model:

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render]
```

`tools/blender/models/items_lineup.py` is QA only. It renders `qa/blender/items_lineup.png` and exports nothing.

## Conventions

All coordinates on this page are in **Godot terms**, local to the model root, in metres. Godot = Blender (x, z, −y).

- **Front:** a model's front faces **+Z**.
- **Parts:** every `IA_*` part and every other animated part is its own node, with its origin at the pivot and an **identity rotation at rest**.
- **Angles:** angles are relative to the rest transform, which matches `Lab7Visuals._rot(node, axis, deg)` (`rest.basis * Basis(axis, deg)`).
- **Sign:** a positive angle is counter-clockwise when you look down the +axis toward the origin.
  - About **+X**, a positive angle turns +Y toward +Z, so an upright lever tips toward the front, and a back-hinged lid opens with a negative angle.
  - About **+Z**, a positive angle is counter-clockwise as the player sees the front.

**Colliders:** `ModelUtil.build_colliders` puts one AABB box on each mesh. So the static parts are split into tight meshes, and no static box covers an `IA_*` part by more than the 0.18 m window that `_raycast` allows.

**Materials:** every slot already exists in `game/assets/materials/`, except **`M_Glass_UV`**. It is new, and I added `M_Glass_UV.tres` for the violet Wood's-glass lens of the UV lamp. Its emission is off and can be enabled when the lamp is on.

---

## lumen_projector.glb (5,950 tris)

**Shape:** a brass lamp house with four brass V-fins over blackened gaps and a lantern chimney. It has a front flange engraved **LUMEN**, a barrel with three tuning rings under an index rail, a knurled focus collar, a bayonet lens socket and a throw lever with an OFF/ON quadrant. It sits on a trunnion yoke and pan head over a walnut tripod with brass ferrules and a spreader. A cloth cable runs from the rear cap to a brass floor outlet behind the tripod.

**Size:** 0.71 (x) × 1.29 (y) × 0.93 (z), with z running from −0.652 at the outlet behind to +0.279 at the lens. The origin is the tripod centre on the floor.

**Placement:** (−2.3, 0, 1.6) with yaw 90°. The model's +Z then points at world +X, and the outlet lands at world x ≈ −2.92, 8 cm in front of the west wall.

| Part | Pivot (Godot, model-local) | Axis | Rest → active |
|---|---|---|---|
| `IA_ring_0` (front, engraved **I**) | (0, 1.15, 0.120) | local **+Z** (the beam axis) | Rotation is **(k − 5) × 60°** with **RING_SIGN = +1**, where k is the colour index (0 crimson, 1 amber, 2 green, 3 cobalt, 4 violet, 5 white). k = 5 (white) is the rest pose. Each +1 step is +60°, counter-clockwise as seen from the front. Inner radius 0.0425, outer 0.059, width 0.024 |
| `IA_ring_1` (**II**) | (0, 1.15, 0.089) | local +Z | same |
| `IA_ring_2` (rear, **III**, next to the lamp house) | (0, 1.15, 0.058) | local +Z | same |
| `IA_lens_socket` | (0, 1.15, 0.271), the lens centre | — | Static tap target: a polished bayonet socket (outer radius 0.0545) with three lugs. When it is empty you see a black bore |
| `lens_installed` | (0, 1.15, 0.271) | — | Hidden until the lens is inserted. It is the same crystal + brass ring as `crystal_lens.glb`, 70 mm across, facing +Z. `_glow()` overrides all its surfaces, including the brass ring |
| `IA_projector_lever` | (0.088, 1.15, −0.205), on the right (+X) side | local **+X** | At rest the arm leans **25° back**, over the cream OFF dot. ON is **+35°**, so the arm ends 10° forward over the green ON dot. This matches the current `35.0 if beam_on` |
| `beam_origin` (empty) | (0, 1.15, 0.279), the crystal apex | — | The beam runs along local **+Z** (world +X when placed) at height 1.15 |
| `projector_house`, `projector_mount`, `projector_tripod`, `projector_cable` | (0, 0, 0) | — | static |

**Ring layout at rest.** Seen from the front, clockwise from 12 o'clock: white (index), crimson, amber, green, cobalt, violet. The segment for colour k carries **k + 1 raised brass notches**, centred in the segment: crimson 1, amber 2, green 3, cobalt 4, violet 5, white 6.

**Index.** A fixed blued pointer hangs from the brass index rail at 12 o'clock over each ring. The rail's top carries the engraved roman numerals I / II / III above rings 0 / 1 / 2.

From the in-game projector camera (front-right), the lens end appears on the left. Rings therefore read I, II, III from left to right.

---

## radio.glb (5,954 tris)

**Shape:** a 1950s walnut valve radio with a rounded top front edge and a recessed fascia framed by a brass inlay. It has a tan grille cloth behind four brass bars, with a MERIDIAN badge, and a curved dial glass (1.5 mm thick) over the printed dial. A gold right-hand panel carries the magic eye and the big knurled tuning knob. There is a volume knob on the right side, brass-capped feet, a back board with vents, and a mains cord that plugs into a round bakelite socket on the bench splashback. A top-back hatch opens onto the valve chassis, which holds two valves, an empty B9A socket, a can and a capacitor.

**Size:** the cabinet is 0.42 × 0.28 × 0.22. The overall box is 0.437 × 0.285 × 0.387: the volume knob adds 17 mm on +X, and the cord and wall socket reach z = −0.255.

**Origin:** the base centre.

**Placement:** (0.55, 0.92, 2.2) with yaw 180°. The wall socket's back sits at radio-local z = −0.255, which is exactly the lab bench splashback face.

| Part | Pivot (Godot, model-local) | Axis | Rest → active |
|---|---|---|---|
| `radio_dial` | Node at (0, 0, 0) with identity. The mesh is baked in model space: a quad centred at (0, 0.191, 0.0905), **0.288 wide (X) × 0.072 high**, facing +Z | — | Uses `M_Decal_RadioDial` with planar UV 0..1: u runs left→right along +X, v runs bottom→top, aspect 1024:256, not mirrored. Mesh AABB x ∈ [−0.144, +0.144], so `aabb.size.x = 0.288` |
| `dial_needle` | (−0.1267, 0.191, 0.0935): the needle line at **u = 0.06** (= −0.144 + 0.06 × 0.288), 3 mm in front of the dial | translate **+X** | dx = (u − 0.06) × 0.288. **Full travel u 0.06 → 0.94 is 0.2534 m.** The current `_update_radio` is correct as written. Dial value 36 (41 m band) → u = 0.3768 → dx = +0.0912; the QA render puts the needle on "41" |
| `IA_tuning_knob` | (0.139, 0.070, 0.106), on its axis at the fascia | local **+Z** | 66 mm across: a brass skirt with an index notch, a bakelite knurled grip (18 ribs) and a brass cap with a cream index line at 12 o'clock. Suggested animation: knob angle = **−9° × dial value**, about 2.5 turns full scale. Negative is clockwise as the player sees it, so the needle moving right reads as a clockwise turn |
| `IA_radio_hatch` | (0, 0.280, −0.0905), the hinge axis at the back edge of the top opening, along X | local **+X** | 0° closed → **−70°** open, as in the current code: the front edge lifts and the panel stands 70° up. The panel is 0.198 × 0.113, flush with the top. The opening spans x ±0.10, z ∈ [−0.0905, +0.024] |
| `IA_valve_socket` | (0.012, 0.2035, −0.058), the top centre of the B9A socket, which is the valve seat | — | Static tap target: a bakelite socket on a brass saddle with nine pin holes |
| `valve_installed` | (0.012, 0.2035, −0.058), the glass bottom on the socket | — | Hidden until installed. It is the same noval valve as `radio_valve.glb`, with single-surface glass, standing 61 mm tall |
| `valve_heater` (child of `valve_installed`) | identity | — | The cathode sleeve inside the anode, in `M_Copper`. On install with power, `ModelUtil.set_emission(valve_heater, true, Color(1.0, 0.55, 0.2), 3.0)` gives *"The valve warms up with an orange glow."* It hides with its parent |
| `magic_eye` | (0.139, 0.127, 0.1038), facing +Z | — | `M_Emissive_MagicEye` glass, 23.6 mm across, slightly domed. A separate static black cap and a brass bezel sit in front |
| `dial_glass` | (0, 0, 0) | — | static, `M_Glass`, curved 6.5 mm toward the viewer |
| `radio_body` | (0, 0, 0) | — | static |

**Hatch visibility.** The current radio camera at (0.55, 1.22, 1.62) is only 2 cm above the radio top, so the open hatch and the empty socket cannot be seen from it. Add a view of at least about 50° elevation for the hatch, for example camera **(0.55, 1.54, 1.92)** looking at **(0.54, 1.12, 2.23)** in room coordinates. From there the socket, the two neighbouring valves and the installed valve are clearly visible. The chassis sits only 7.6 cm under the opening for this reason.

---

## Inventory items

All items are **real-size**, with their **origin at the centre of mass**. The root mesh node is at identity, so scene origin = node origin = centre of mass. The centre of mass is computed for uniform density over the watertight shells; open paper and print sheets carry no mass.

Each item rests in its natural pose. The "bottom" column is the Godot y of its lowest point, so to rest an item on a surface at height h, place its origin at **h − bottom**.

| File | Tris | Size (Godot x × y × z) | Natural pose (identity) | Bottom (y) | Notes |
|---|---|---|---|---|---|
| `notebook.glb` | 1,886 | 0.176 × 0.027 × 0.279 (ribbon included) | Lies flat. Cover up (+Y), spine at −X, head (top edge) toward −Z, ribbon trailing out of the tail toward +Z | −0.0134 | Book 0.170 × 0.230 × 0.024. The desk LAYOUT y should be 0.78 + 0.0134 |
| `uv_lamp.glb` | 2,089 | 0.177 × 0.062 × 0.063 | Lies along X with the head at **+X** | −0.0309 | Child `uv_lens` (`M_Glass_UV`) has its origin at the lens centre, (0.0805, 0, 0), and faces +X. The body is 39.6 mm across, wide enough for the D cell |
| `battery_cell.glb` | 2,067 | 0.0345 × 0.0634 × 0.0345 | Stands upright with **+ up (+Y)** | −0.0307 | D cell (R20), 34 × 61.5 mm. **Gear box cradle:** the cell must lie along X. Either parent it to gear_box's `battery_anchor` with an identity transform, or keep the current spawn and use `Basis(Vector3.BACK, -PI / 2)` instead of yaw 90°. The latter maps +Y to +X; the origin goes on the cradle axis (0, 0.05, 0) |
| `brass_key.glb` | 1,918 | 0.069 × 0.0072 × 0.026 | Lies flat. Bow at −X, bit at +X hanging toward +Z | −0.0036 | 66 mm ornate key |
| `crystal_lens.glb` | 1,456 | 0.0696 × 0.0696 × 0.016 | Stands on edge with the disc facing **+Z** | −0.0348 | The current safe offset (y = −0.08 over the floor at −0.115) already stands it exactly on its rim |
| `breaker_handle.glb` | 2,423 | 0.136 × 0.035 × 0.035 | Lies along X, **ferrule at −X**, ball end at +X | −0.0173 | The square drive socket is in the ferrule end, facing −X; it slips over Panel 7's lever. The panel's own `main_handle` is a separate part |
| `letter.glb` | 1,031 | 0.162 × 0.0048 × 0.166 | Lies flat, back of the envelope up (+Y). The letter sticks out toward **−Z** | −0.0009 | Envelope 0.162 × 0.114. The wax seal carries the Institute's mark (a ring plus a meridian). Also used for `leyla_photo` |
| `radio_valve.glb` | 1,529 | 0.0216 × 0.0685 × 0.0216 | Stands upright on its pins, which point down | −0.0378 | Miniature noval (B9A, EL84-style). Its glass bottom is at y = −0.0305 |
| `mirror_item.glb` | 2,335 | 0.220 × 0.262 × 0.0215 | Stands upright. Mirror (`M_Chrome`) faces **+Z**, mounting pin down | −0.1505 | The pin tip is the lowest point. To lie it on its back, face up, rotate **−90° about X**; the back boss then rests at y = −0.0125 relative to the origin |

**Inspect and icon views.** `hud.show_inspect` and `ItemIcons` show each model's +Z face. The flat items (notebook, letter, brass_key) are seen nearly edge-on in their natural pose. Pre-rotate them with `Basis(Vector3.RIGHT, deg_to_rad(70))`, which brings the cover or face to the camera, for example as a per-item `inspect_rot` in `ItemDB`. All other items already present their hero face to +Z.

## QA renders (`qa/blender/`)

| Model | Renders |
|---|---|
| projector | `lumen_projector.png` (hero), `_2` (rings, lever, index rail), `_3` (lens, socket, LUMEN), `_4` (posed: rings crimson / cobalt / green, lever ON) |
| radio | `radio.png` (hero), `_2` (dial at rest with the needle at u = 0.06, magic eye, knob), `_3` (hatch open with the empty socket), `_4` (valve installed, tuned to 41 m) |
| items | `item_<name>.png` (plus `_2` for some items) and `items_lineup.png` |
