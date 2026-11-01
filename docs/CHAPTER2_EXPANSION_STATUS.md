# Chapter 2 expansion: scene status (running file)

Owner: the Godot scene engineer. Spec: `docs/CHAPTER2_EXPANSION.md`. Logic: `game/src/rooms/archive/archive_logic.gd`,
`archive_exp_data.gd`. Models: `docs/models/ch2_exp.md`. Audio: `docs/AUDIO_CH2X.md`.
`ArchiveLogic.EXPANSION_STAGE` is **0** and must stay 0 until ALL rooms are playable in the scene (a build from `main` must not
start a game it cannot finish). Every expansion node in the scene is built only when `logic.exp_active()`.

## Done (scene)

| Piece | File | Notes |
|---|---|---|
| Multi-room layer | `src/rooms/archive/archive_zones.gd` | zones 60 m apart (`ZONE_OFFSET`), built on first use, only the current zone visible and collidable; the hall keeps its nodes and is out of the camera's 40 m far plane while another room is shown (no draw calls). Any `room:<id>` logic event (door, plan, hint "Go to") fades 0.2 s out / 0.2 s in, switches zone, mood (`MOOD`), ambience (`amb_c2x_<room>`) and camera. Placeholder box rooms (marked `PLACEHOLDER`) for rooms without models. |
| Hall additions | `archive_hall_exp.gd` | real `service_door` (cover hatch, rotary dial, leaf), `stair_stump` (Stage B only), `floor_plan_frame`; two decoy hatches are primitives (`placeholder_hatch_*`); the rules notice moves up the east wall. Hall draw calls +6 (128 -> 134 at the start state). |
| Pump Room | `archive_pump.gd` | room_pump, boiler, manifold_plate, pipe_run, book_lift_cage (N7 by `ArchiveLift`), mallet on the bench; N2 valves, glow bands, lamps, needles, mallet probe, diagram card per variant, M1 moment. 6 views. 49 draw calls with HUD at most. |
| Plan overlay, hints, settings, trial, chapter card | `src/ui/hud.gd`, `settings_panel.gd`, `main_menu.gd` | `show_plan()` (item `floor_plan` and the hall wall frame), hint "Go to <room>", hint button/line honour `hints_allowed()`, Settings "hands" + "moments", Trial start button (only when `EXPANSION_STAGE >= 1`), chapter card shows Trial stamp and `ui2x.legacy_note`. |
| Hands phase 1 | `src/fx/hand_layer.gd`, `src/core/hold_table.gd` | floating item on the camera: UV lamp (beam follows the finger), mallet (swings on tap), cloth, receiver, keys. Rows in `HoldTable.ROWS`. |
| Book lift N7 | `archive_lift.gd` (+ `archive_rig.gd`) | One `ArchiveLift` per site (Pump niche floor -1, Gallery wall floor +1); the cage model is shown where `lift_floor` is and rides out of view when it moves. Load plate "LOAD n" drawn from `v_load` (tap = zoom), needle that tells heavy from light, scissor gate that folds when the cage is here, three floor buttons in the cage (flask, book, lamp) and the same on a call plate beside the shaft. Weights 1, 2, 4, 8 hang on a counterweight stand (see Deviations), loose ones stand in a row on the floor. Pressing another floor while the cage is here rides it: cage rises, fade, `lift_moved` sound + bell 3.6 s later, `enter_room`. Floor 0 (book button) leads to the hall. |
| Reading Gallery | `archive_gallery.gd` | room_gallery with window and table lights, balcony rail with the hall visible below, Records counter (three drawers, the clue slips in the middle one), roll-call board N8 (tap a tag to take it up, tap a hook or a hung tag to hang or swap; slips pinned under the hooks with a lamp each, tap a slip = reader), the key in the tray, PA horn + M4, stair wedge (pull the pin: chock slides, ladder falls, `pull_wedge`), the spiral stair down to the hall, pass door to the Office (key; a locked door rattles), plain door to the Plate Room, the lift's upper door. 8 views. |
| Plate Room | `archive_plate.gd` | room_plate with dark flecked linoleum (the model's own floor is the hall's green chequer), red safelights, enlarger N9 (strips on a pale sleeve on the bench, tap = load; zoom knob and focus ring tap one step and wrap; the paper shows the loaded strip's person blurred by the focus error, scaled by the zoom error, a fit frame on the easel, digits only on the right print), the print in the tray, `c2x_enlarger_fan` loop while in the room (`on_exit` hook added to `ArchiveZones.activate`). 3 views. |
| Director's Office | `archive_office.gd` | room_office with cool window light, green desk lamp, fire glow; strand_cabinet N10 (label drawn from `cabinet_label`, four wheels tap +1, doors swing when open, the spare `projector_lamp` stands inside: tap to take), tea set (cups lift on a tap), desk drawer, door back to the Gallery. 3 views (`office`, `cabinet`, `office_desk`; `desk` is the hall's own view id). |
| G2 and the stair | `archive_hall_exp.gd` | the stump taps climb to the Gallery once `wedge_out`; `lamp_dead` / `lamp_installed` sounds. The booth projector takes the lamp through the existing `use_item_on` flow (lever ticks and says so before). |
| Upper-floor art, moments | `archive_upper_art.gd` | all variant pictures are drawn in code and carry no words (load plate, slips as pictograms, strips with edge symbols, cabinet label, enlarger image, staff print). M4 is in the Gallery builder; M5 "steps above" is the Cold Store builder's (`moment_m5`). |
| Night Cell | `archive_cell.gd` (+ `archive_kit.gd`, shared helpers) | zone `cell`, 7 views (`cell`, `desk`, `light_table`, `cot`, `shelf`, `cold_door`, `cold_wheels`). **N3 light table** by taps and drags: the three acetate sheets lie stacked on the glass, each turns a quarter (tap the sheet, its round colour button, or drag it sideways) and flips (its tab, the flip button, or drag down); the window shows the cells clear on all three sheets (`n3_lit`; the sheets' own smoky cells do the AND, a dim bezel hides the two outer rows); solved = locked, digits stay lit. The box switches itself on with a three-flicker beat on the first look. **Cold door**: two digit wheels (tap +1, drag +-1), the cam handle, ice and coil glow from `thawed`, the leaf swings open on `cold_open`. Kettle (knobs, lifting, steam), diary page, pencil slip, cloth pick-up, wallpaper toned down in the scene. Lights from the model's `light_*` empties. |
| Cold Store | `archive_cold.gd` | zone `cold`, 5 views (`cold`, `cranks`, `plan`, `frost`, `chest`). **N4**: five carriages on the seven slots, crank turns one full turn, then the carriage rolls 2.7 s (ease in/out), clunk jolts it; the `cranks` camera is fitted to where the carriages stand (inside the room, lens widens) and the camera walks to the chest when the aisle opens. **N5**: `frost_reveal` shader wipe mask painted by the finger (drag, with sound) or by a band tap; a band counts when 70 % of its patches are clear; the signs are `v_symbols` and are only visible where wiped. **N6**: rings animate forward only, lid, two crystals (`take("case_crystal_*")`), the note. Plan plate shows the carriage tag that hides the chest. Film cans stand at the end of every other aisle. Breath mist in the root view. Moments M3 (silhouette behind the pane), M5 (dust), M6 (the archivist echo). |
| Pump Room (extra) | `archive_pump.gd` | view `cell_door` (first look = M2, the leaf shivers three times on the knock times of `knocks.ogg`), puddles no longer black |
| Items | `tools/blender/models/floor_plan.py`, `frost_sketch.py`, `ItemDB`, `hud.gd` | the plan item has a model (no bag warning), the frost sketch has a model and a reader page with this game's three signs |
| QA | `qa/exp_shots.gd`, `qa/playthrough_ch2.gd`, `qa/ui_screens.gd`, `tests/test_archive_upper_art.gd` | see below |

## Deviations from the model contract

- `service_door` has one site (z 2.95), but the logic draws `v_panel` in A/B/C. The variant changes the LETTER on the door's
  hatch (and the receiver table); the two decoy hatches carry the other letters. The door model is moved 7 cm into the hall so
  its dial clears the hall's dado rail.
- The pipe board draws each game's graph itself (nodes by `ArchivePump.layout`, zero crossings for all six graphs, tested);
  the model's nine candidate segments are hidden. A larger diagram card hangs beside the manifold (the model's plate is too small).

- **Counterweight stand.** The model's hook (`IA_hook`, `hook_mount_0..3`) sits 4.5 cm from the niche wall: a weight disc (up to 29 cm)
  cannot hang there and the camera cannot see it. The weights hang on a small iron stand built from primitives against the north wall
  beside the niche (`counterweight_stand`), pegs facing the room; the cage's own hook stays as decoration.
- **Scissor gate.** `IA_gate` slid -0.62 m along X still hides the left half of the buttons, and sliding it fully leaves it floating
  outside the cage, so it is folded: scale X 0.3 against the cage's left post (`ArchiveLift._gate`).
- **Gallery lift.** `room_gallery` has no shaft, so the cage stands on the north wall at x 2.70 in front of the windows; the Gallery's
  `lift_g` / `lift_gpanel` views look at it, and a call plate hangs on the wall left of it.
- **Plate Room strips** lie on a pale paper sleeve beside the enlarger (not at the contract's `strip_mount_*`, which are on the drying
  table 3 m away): film is dark, the bench is black, and the strips must be in the enlarger's view. Scaled 1.5 on the bench, 1.0 in the carrier.
- **Enlarger knob and ring** are siblings of `IA_head` in the glb, not children; they are moved with the head by the code.
- **View id `desk`** belongs to the hall: the Office's desk view is `office_desk`.

## Left to do

- N3-N6 rooms: Night Cell (models in repo: room_cell, cot, light_table, ..., cold_door), Cold Store (room_cold, carriages,
  frost_window, cold_chest), their zones (`BUILDERS` in `archive_zones.gd`), interactions, moments M2, M3, M5, M6.
- Stage B scene is in (book lift, wedge/stair, Gallery, Plate Room, Office, G2, M4). Not done: a real item icon/model for
  `roll_slips` and `staff_print` (the bag shows the name; `ItemIcons` logs a missing-model warning), the hung weights are only visible
  from the `lift_weights` view, the lift's hall stop has no hall-side door (button 0 fades to the hall's root view).
- Hands: glove, poses, cloth wipe stroke, receiver needle in hand (phase 2).
- Flip `ArchiveLogic.EXPANSION_STAGE` to 2 and `EXPANSION_SCENE_READY` in `qa/playthrough_ch2.gd` when everything is playable.
- Audio hooks: N7-N10 events, the enlarger fan loop and the stair steps are wired (`archive_lift/gallery/plate/office/hall_exp`); the ids in `docs/AUDIO_CH2X.md` for any other expansion event are the other rooms' job.
