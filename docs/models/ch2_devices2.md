# Chapter 2 projection-booth devices (group C2): measured results

Models: `booth_door.glb`, `film_projector.glb`, `slide_projector.glb`.

Scripts: `tools/blender/models/{booth_door,film_projector,slide_projector}.py`. Shared helpers:
`tools/blender/lib_ch2_devices2.py`. Build list: `tools/blender/build_lists/ch2_devices2.txt`.

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [-- --shot=1,3]
```

Each script exports the GLB, then reads the GLB back and checks the contract names, parents, pivots
and identity rest rotations against `docs/models/ch2.md` §5 (`verify OK` in the log). The projector
scripts also print the beam clearance through the booth window. `--shot=` renders only the listed QA
shots. All three GLBs pass `tools/blender/check_glb_names.py`.

## Conventions

All coordinates are **Godot terms, model-local, metres**, unless marked *world*. Godot = Blender
(x, z, −y). Front = +Z. Angles follow `docs/models/devices.md`: positive is counter-clockwise
looking down the +axis. The code applies `rest.basis * Basis(axis, deg)`. Every `IA_*` part and
every animated part is its own node, with its origin at the pivot and an identity rotation at rest.
All three models are placed with **yaw 180**, so local +X = world −X and local +Z = world −Z.

---

## booth_door.glb (5,649 tris; budget 6,000)

**Shape:** a panelled walnut door in a cream-painted casing. The leaf has two fielded lower panels
with a muntin, a wide lock rail and an upper panel with a round porthole. The porthole has a brass
ring on each face and 4 screws. There are ogee mouldings on both faces, a brass kick plate and a
brass D-pull on the hall face, and a brass push plate on the booth face.

The lock is a telephone dial on a brass escutcheon (4 screws and a service keyhole):
- a black bakelite bezel;
- a cream number plate with black 3D digits, each in a printed ring, and the Institute mark (ring +
  meridian) in the centre;
- a chrome finger wheel with polished hole mouths;
- a chrome finger stop.

The casing fills the doorway with 20 mm linings and stops. On the hall side it has a moulded
architrave with plinth blocks and a capped head; on the booth side, plain 45 mm boards. It also
carries a brass threshold, three butt-hinge knuckles and a jewel lamp in a bakelite housing on the
latch-side architrave.

**Size:** 1.004 (x) × 2.21 (y) × 0.161 (z).
- x ∈ [−0.502, 0.502]: the head cap. The architrave legs reach ±0.480 and the plinths ±0.486.
- y ∈ [0, 2.21].
- z ∈ [−0.115, +0.046]: from the booth-side boards to the head cap.

**Origin:** the doorway centre at floor level, on the hall-side wall plane. The wall occupies local
z ∈ [−0.10, 0].

**Placement:** (−1.55, 0, 2.0), yaw 180. The hinge is on local −X, which is world east (x = −1.17).

| Part | Pivot (model-local) | Axis | Rest → active | Notes |
|---|---|---|---|---|
| `booth_door_casing` | (0, 0, 0) | — | static | Linings, stops, threshold, architrave, plinths, head cap, booth boards, knuckles, lamp housing and bezel |
| `IA_booth_door` | (−0.380, 0, +0.008): the hinge-pin axis at floor level | local **+Y** | 0 → **−100°** | The free edge swings out into the hall. Leaf 0.754 × 2.054 × 0.045: x ∈ [−0.377, 0.377], y ∈ [0.020, 2.074], z ∈ [−0.045, 0]. The number plate, escutcheon, bezel, digits and finger stop are part of the leaf mesh (static on the leaf). The swing clears the casing at every angle: the nearest approach is the leaf face passing the architrave, more than 0.1 m out from the wall |
| `IA_rotary_dial` (child of the leaf) | model (0.27, 1.20, 0.01325); relative to the leaf (0.650, 1.200, 0.00525) | local **+Z** | dial n: **−(θₙ + 10°)**, then back to 0 | Chrome finger wheel, Ø 0.121, 3.5 mm thick, front face at z = 0.015. Ten holes Ø 0.018 on a radius of 0.043 |
| `IA_dial_hole_<d>`, d = 0..9 (children of the wheel) | the hole centre on the wheel mid-plane: (0.043 cos θ, 0.043 sin θ, 0) relative to the wheel | — | static child | The polished hole wall (Ø 0.018 × 0.0027). Its AABB is the tap disc: box 0.022 × 0.022 × 0.012 after the code's padding. Neighbouring boxes never cover another hole's circle. The digit stays fully visible |
| `booth_door_lamp` | (0.437, 1.30, 0.030) | — | emission by code | `M_Glass_Frosted` faceted jewel, Ø 0.019, on the latch-side architrave. It is visible in both the `booth_door` and `dial` views. The chrome bezel is in the casing, so only the jewel glows |

**Dial layout.** θ is counter-clockwise from +X, seen from the front (the hall). The finger stop is
at **−10°**.

| Digit | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 0 |
|---|---|---|---|---|---|---|---|---|---|---|
| Hole angle θ | 50° | 80° | 110° | 140° | 170° | 200° | 230° | 260° | 290° | 320° |
| Wheel turn (about +Z) | −60° | −90° | −120° | −150° | −180° | −210° | −240° | −270° | −300° | −330° |

- The digits sit on the fixed number plate. They are upright and black, DejaVu Sans Bold, cap
  height ≈ 10 mm, centred under their holes.
- In the `dial` view they are about 35 px tall on a 1080 px screen (`booth_door_2.png`).
- While the wheel turns, the holes that pass over the 90° gap show blank plate (`booth_door_5.png`).
- The solution 2-8-5 turns the wheel −90°, −270° and −180°.

**Colliders:**
- The wheel is ≤ 0.15, so it gets an AABB box (0.125 × 0.125 × 0.012). The holes get smaller boxes
  inside it at the same depth, and `raycast` prefers them.
- The leaf and the casing are trimeshes.

**Materials:** `M_Wood_Walnut`, `M_Enamel_Cream`, `M_Brass_Aged`, `M_Brass_Polished`, `M_Chrome`,
`M_Bakelite`, `M_Glass`, `M_Glass_Frosted`, `M_Steel_Dark`.

**Deviations from the contract:**
- **Leaf width:** 0.754 instead of 0.80, height 2.054. The contract asks the casing to fill the
  0.80 × 2.10 doorway. With 20 mm linings the clear width is 0.76, and the leaf sits in it with
  3 mm gaps.
- **Hinge pivot:** at local x = −0.380 (the lining face) instead of −0.40, and z = +0.008 (the pin
  axis, 8 mm proud of the hall face). This puts the pivot where a real butt hinge sits, so the
  −100° swing clears the lining and the architrave. The code only rotates about the node origin, so
  nothing in the code changes.
- **Push plate and pull:** the push plate is on the booth face, because the door is pushed open
  from inside. The hall face gets a brass D-pull below the dial and a kick plate.
- **Lamp:** it sits on the latch-side architrave at y = 1.30, not on the head, so that it is
  visible in the `dial` view. The `booth_door` view only sees y ≤ 1.78 at the door.
- **Booth-side boards:** only 45 mm wide. The booth's east wall inner face is 50 mm from the hinge
  jamb (world x −1.10).

**For group A (room):**
- The hall-side architrave and plinths cover world x ∈ [−2.036, −1.064].
- The head cap covers world x ∈ [−2.052, −1.048], up to y = 2.21. The enamel sign plate over the
  doorway must sit above y = 2.22.
- The room's panelling must not run into the architrave. In the composite renders with
  `room_archive.glb`, nothing intersects.

**QA renders** (`qa/blender/ch2/`, composited in `room_archive.glb` at the real placement):

| File | Shows |
|---|---|
| `booth_door.png` | The in-game `booth_door` view, closed, lamp red |
| `booth_door_2.png` | The in-game `dial` view: all ten digits legible, finger stop at −10° |
| `booth_door_3.png` | Open (−100°), lamp green, seen from the hall south-west: the booth face with the push plate, the doorway into the booth |
| `booth_door_4.png` | Hero: three-quarter view from the hall |
| `booth_door_5.png` | Dialling 5: the wheel turned −180°, hole 5 at the finger stop, blank plate under the holes passing the gap |
| `booth_door_6.png` | Open, from the in-game `booth_door` view (the code shows this view during the opening) |

---

## film_projector.glb (8,266 tris; budget 9,000)

**Shape:** a 1950s 16 mm cinema projector on a heavy cast pedestal.

**Body:**
- a green-grey hammertone body casting with a sloped front-top;
- a chrome lens mount boss and a black lens barrel with a chrome front bezel and glass;
- the scale/focus ring.

**Operator side (local −X): the film path on a satin-black threading panel:**
- two toothed sprockets with hold-down shoes;
- a chrome gate with an aperture, a latch knob and rivets;
- two loop rollers;
- a framing knob.

**Controls (also on the operator side):**
- the RUN lever on a black quadrant with a red (OFF) and a green (RUN) stop;
- the ◀ ▶ buttons on a chrome panel;
- a crimson **MERIDIAN-16** badge.

**Reels:** a feed arm rising over the front with a spindle, and a take-up arm reaching down behind
with an empty reel.

**Lamp house and power:**
- a black crinkle lamp house at the back left (+X), with a rounded top;
- 6 louvre slots with chrome hoods on the back;
- a mushroom chimney;
- an amber inspection window on its −X face;
- a motor housing on the +X side.

**Pedestal and cable:**
- a domed cast base on 3 levelling feet;
- a column with a chrome height clamp and T-handle;
- a tilt head with a bakelite knob;
- a cloth cable to a floor box.

**Size:** 0.47 (x) × 2.33 (y) × 0.768 (z).
- x ∈ [−0.235, 0.235]: the base.
- y up to 2.33: the feed arm.
- z ∈ [−0.455, 0.3125]: from the floor box behind to the lens front.
- Body casting: x ∈ [−0.055, 0.115], y ∈ [1.70, 2.08], z ∈ [−0.15, 0.17].

**Origin:** the pedestal centre on the floor.

**Placement:** (−2.9, 0, 2.65), yaw 180.
- World footprint: x ∈ [−3.135, −2.665], z ∈ [2.338, 3.105].
- The operator side faces world +X.

| Part | Pivot (model-local) | Axis | Rest → active | Notes |
|---|---|---|---|---|
| `projector_pedestal`, `projector_body`, `projector_lamphouse` | (0, 0, 0) | — | static | Split so the colliders stay tight |
| `IA_focus_ring` | (0, 1.95, 0.2365) | local **+Z** | **−30° × focus** (focus 0..8) | Back part: a black scale ring whose outer surface is a **45° cone facing up and back toward the operator**, r 0.0368 → 0.0462. Front part: a chrome ribbed grip (28 ribs), Ø 0.094. White digits 0–8 on the cone: digit k at **90° + 30°·k** (CCW from +X seen from the lens front). Each digit's "up" points along the cone toward the lens front, so it reads from behind or above. The fixed **index** is a raised chrome tab with a white wedge on top of the collar, at (0, 1.992, 0.204..0.214). After the rotation the top digit = focus (`film_projector_3.png`, focus 5). AABB box 0.094 × 0.094 × 0.043 |
| `IA_run_lever` | (−0.055, 1.885, −0.075) | local **+X** | 0 (OFF) → **+40°** (RUN) | At rest the chrome arm with its bakelite ball leans **20° back**, past the red stop. RUN leans it 20° forward, past the green stop. Arm length 0.082. AABB 0.029 × 0.115 × 0.058 |
| `IA_frame_prev` | (−0.0636, 1.765, −0.112): the button face centre | face normal −X | pressed: **+0.004 along +X** | ◀ raised white arrow pointing local −Z: the back, the viewer's left from the operator side. Bakelite cap Ø 0.0216, standing 6.6 mm proud of its chrome panel |
| `IA_frame_next` | (−0.0636, 1.765, −0.064) | face normal −X | pressed: +0.004 along +X | ▶ points local +Z (the front, the viewer's right) |
| `takeup_reel` | (−0.075, 1.655, −0.255) | local **+X** | spins | Empty 16 mm reel, Ø 0.18 × 0.0200: two chrome flanges with 3 kidney windows each, a hub and a few turns of leader (`M_Film`) |
| `feed_reel_mount` (empty) | (−0.075, 2.31, 0.07), rotation **−90° about +Y** (quaternion x, y, z, w = 0, −0.7071, 0, 0.7071) | — | — | `film_reel.glb` (its axle is its local +Z) parented with identity hangs on the feed spindle with its face toward the operator (−X). The code's spin about the reel's local +Z is a spin about the spindle. The real `film_reel.glb` (Ø 0.18 × 0.0206) clears the arm's spindle collar by 2.7 mm |
| `lamp_glow` | (0.03, 1.99, −0.215) | — | emission by code | One `M_Glass_Amber` mesh: the inspection window disc and the 6 strips behind the louvre slots. Dark amber when off; the lamp house is opaque behind it |
| `lens_origin` (empty) | (0, 1.95, **0.3125**) | beam along +Z | — | World (−2.9, 1.95, 2.3375) |

**Beam through the booth window.** The beam is a pyramid from the lens (aperture r 0.035) to the
whole screen rectangle (x ∈ [−3.7, −1.3], y ∈ [1.1, 2.7], z = −3.43), tested at both wall faces.

| Window edge used | West | East | Bottom | Top | Minimum |
|---|---|---|---|---|---|
| Contract opening x ∈ [−3.4, −2.1], y ∈ [1.65, 2.25] | 0.420 | 0.673 | **0.217** | 0.223 | 0.217 m |
| Real `booth_glass` (6 mm frame) | — | — | — | — | 0.211 m |
| Opening shrunk by a 0.04 frame | 0.380 | 0.633 | 0.177 | 0.183 | 0.177 m |

The game's beam cone (r 0.035 at the lens to 0.9 at the screen centre) is about 0.09 m across at the
window, so it clears with a large margin. The lens front is 0.237 m from the booth-side wall face.

**Camera view.** This is the most important issue for the code.
- The contract `projector` view, (−2.2, 1.75, 3.15) → (−2.9, 1.5, 2.6) FOV 50, looks below the
  projector. Projected into it, the lens, focus ring and RUN lever are above the frame edge
  (screen y = +1.07…+1.32), and so are the feed reel (+2.5…+2.9) and the lamp window.
  `film_projector.png` shows only the column, the take-up reel and the ◀ ▶ buttons.
- **Proposed view:** camera (−2.0, 2.25, 3.2) → (−2.88, 1.95, 2.52), FOV 54. The lens, focus ring
  and index, RUN lever, ◀ ▶ buttons, lamp window and both reels all fall inside the central 90 % of
  the frame at 16:9 and 19.5:9 (`film_projector_2.png`).
- The focus digits are about 9 mm high. They are legible only from about 0.45 m. For a drag-focus
  close-up, use (−2.62, 2.18, 2.72) → (−2.90, 1.99, 2.43), FOV 40 (`film_projector_3.png`).

**Materials:** `M_Steel_Painted`, `M_Steel_Dark`, `M_Chrome`, `M_Lacquer_Black`, `M_Bakelite`,
`M_Enamel_White`, `M_Enamel_Crimson`, `M_Enamel_Green`, `M_Glass`, `M_Glass_Amber`, `M_Film`,
`M_Fabric`.

**Deviations from the contract:**
- **Film path:** no threaded film. The film path is not toggled by the code, and a film strip would
  show without a reel.
- **Focus ring surface:** the digit band is conical, not cylindrical. That still makes it the ring's
  outer surface, and it is needed for legibility from the operator's side.
- **Lens:** the "lens centre ≈ 0.30" is the front glass at z = 0.3125.

**QA renders** (in `room_archive.glb`, with `projection_screen.glb`, `film_reel.glb` at the mount,
and the neighbours):

| File | Shows |
|---|---|
| `film_projector.png` | The contract `projector` view: reel on, RUN, focus 5 |
| `film_projector_2.png` | The proposed `projector` view, same state |
| `film_projector_3.png` | The focus ring close-up: digit 5 under the index tab |
| `film_projector_4.png` | Hero: the operator side, three-quarter from behind, lamp on |
| `film_projector_5.png` | From the hall through the booth window, lamp on |
| `film_projector_6.png` | Rest, in the proposed view: OFF, no reel, focus 1 |

---

## slide_projector.glb (4,709 tris; budget 5,000)

**Shape:** a 1950s lantern-slide projector.

**Lamp house:**
- black japanned, with two brass bands;
- brass louvre plates with 2 slots and polished hoods on each side;
- a lantern chimney with pierced vents and a brass mushroom cap;
- a rear door with a brass knob;
- a brass peep window and a brass MERIDIAN maker's plate on the −X side;
- a bakelite switch box with a red / green dot plate and a chrome bat toggle.

**Optics:**
- a brass condenser flange;
- an **open slide stage**: two brass guide plates with 84 mm windows on four posts and a bottom
  rail, through which a **walnut push-through carrier** with brass end caps slides across;
- a black lens board;
- a long brass objective with a rack and a knurled pinion knob.

**Stand:**
- a tilt head (yoke, bolt, brass wing nut) on a telescoping column (iron, chrome inner tube, brass
  height collar with a thumbscrew);
- a cast tripod with three curved legs on felt pads;
- a cloth cable to the floor.

**Size:** 0.366 (x) × 2.088 (y) × 0.535 (z).
- x ∈ [−0.183, 0.183].
- Chimney top at y = 2.088.
- z ∈ [−0.330, 0.205]: from the cable on the floor behind to the lens front.
- Body (lamp house): 0.21 × 0.196 × 0.19.
- Front to back, house to lens: 0.375.

**Origin:** the stand centre on the floor.

**Placement:** (−2.35, 0, 2.45), yaw 180.
- World footprint: x ∈ [−2.534, −2.166], within the required [−2.6, −2.1]; z ∈ [2.245, 2.780].

| Part | Pivot (model-local) | Axis | Rest → active | Notes |
|---|---|---|---|---|
| `lantern_stand`, `lantern_body` | (0, 0, 0) | — | static | |
| `IA_slide_gate` | (0, 1.85, 0.049) | — | static tap target | Walnut carrier 0.300 × 0.104 × 0.012 across the stage (z 0.043–0.055). A 0.072 through-window and a 0.084 rebate on the front half, lined in brass: the slide rests on the rear lip. Longer than 0.15, so it gets a trimesh collider |
| `slide_gate_mount` (empty) | (0, 1.85, 0.049), **identity** | — | — | The slide centre plane. World (−2.35, 1.85, 2.401). Per the contract, a `glass_slide.glb` with identity should stand there facing +Z, and the code rotates it about local +Z by −90° × steps. A 0.082 square slide rotated in place stays inside the 0.084 rebate. **See the open issue below** |
| `IA_slide_rot` | (−0.157, 1.85, 0.049) | local **+X** | **−90° × steps** (cosmetic) | Knurled brass knob on the carrier's −X end, Ø 0.025, with a white index line |
| `IA_slide_lamp` | (−0.1265, 1.790, −0.105) | local **+X** | 0 (OFF) → **+30°** (ON) | Chrome bat toggle on the −X switch box. At rest it leans **15° back**, toward the red dot. ON leans it 15° forward, toward the green dot |
| `lamp_glow` | (−0.105, 1.872, −0.112) | — | emission by code | One `M_Glass_Amber` mesh: the peep window and the strips behind the 4 louvre slots |
| `lens_origin` (empty) | (0, 1.85, **0.205**) | beam along +Z | — | World (−2.35, 1.85, 2.245) |

**Beam through the booth window.** Aperture r 0.027, to the same screen rectangle.

| Window edge used | West | East | Bottom | Top | Minimum |
|---|---|---|---|---|---|
| Contract opening | 0.966 | 0.179 | **0.142** | 0.337 | 0.142 m |
| Real `booth_glass` (6 mm frame) | — | — | — | — | 0.136 m |
| Opening shrunk by a 0.04 frame | 0.926 | 0.139 | 0.102 | 0.297 | 0.102 m |

**Clearances:**
- The film beam passes about 0.48 m west of the slide projector's objective (the only slide-projector part north of the film lens, world z < 2.34).
- The slide projector's lens front is 0.145 m from the booth wall.

**Camera view.** The contract `slide_projector` view frames everything: the knob, carrier ends,
toggle, peep window and lens are all inside the central 30 % of the frame. Only the chimney cap
touches the top edge.

**Materials:** `M_Lacquer_Black`, `M_Brass_Aged`, `M_Brass_Polished`, `M_Chrome`, `M_Steel_Dark`,
`M_Wood_Walnut`, `M_Bakelite`, `M_Felt`, `M_Enamel_White`, `M_Enamel_Crimson`, `M_Enamel_Green`,
`M_Glass`, `M_Glass_Amber`, `M_Fabric`.

**QA renders:**

| File | Shows |
|---|---|
| `slide_projector.png` | The in-game `slide_projector` view: slide in, lamp on, toggle ON |
| `slide_projector_2.png` | Hero: the whole stand, wide, from the booth's south-east corner |
| `slide_projector_3.png` | Close-up of the operator side: carrier end, rotation knob with its index line, peep window, toggle (ON) |
| `slide_projector_4.png` | Rest, in the `slide_projector` view: no slide, lamp off, toggle OFF |
| `slide_projector_5.png` | Hero: the head from the front-left: objective, stage plates, carrier with the slide, knob, switch box |

The slide inside the gate cannot be seen from the contract `slide_projector` camera, which looks from
behind and to the left: the lamp house and condenser hide the stage centre, as on a real lantern. From
that view the carrier, the knob and the glow show the state; the slide itself shows from the front or
side (`slide_projector_5.png`).

---

## Open issues for the lead

1. **`glass_slide.glb` orientation (group D2 vs the contract and the code).**
   - The exported item lies flat, front +Y, top edge −Z, per its script header.
   - The `slide_gate_mount` contract and `archive_visuals.gd` (`Basis(Vector3.BACK, …)`, rotation
     about the item's local +Z) need it **standing, front +Z**.
   - With the current item, the slide shows lying flat in the gate, and `slide_rot` would tilt it
     instead of turning it.
   - Either D2 re-exports the slide standing (front +Z, top +Y, so the slide cabinet mount lies it
     flat with −90° about X), or the code composes `Basis(Vector3.BACK, θ) * Basis(Vector3.RIGHT, PI / 2)`
     for the gate slide.
   - The QA renders apply that +90° about X to show the intended result.
2. **`projector` camera.** Use the proposed view above. The contract view does not show the lens,
   the focus ring, the RUN lever or the feed reel. The focus digits need the close-up view (or a
   zoom while dragging) to be read.
3. **`film_reel.glb` (D2) appearance.** Seen at the mount, it reads as an almost empty chrome reel:
   the film pack is hardly visible between its spokes. The orientation and fit are correct.
