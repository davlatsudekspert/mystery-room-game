# Chapter 2 expansion: scene status (running file)

Owner: the Godot scene engineer. Spec: `docs/CHAPTER2_EXPANSION.md`. Logic: `game/src/rooms/archive/archive_logic.gd`,
`archive_exp_data.gd`. Models: `docs/models/ch2_exp.md`. Audio: `docs/AUDIO_CH2X.md`.
**Update 1.1 (2026-11-01): `ArchiveLogic.EXPANSION_STAGE` is now 2** and `EXPANSION_SCENE_READY` is true in `qa/playthrough_ch2.gd`: every room is playable in the scene. Every expansion node in the scene is built only when `logic.exp_active()`.

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

## QA run for the Stage B scene (software Vulkan under Xvfb, 2026-11-01)

- `tools/run_tests.sh`: 307 tests, 42065 checks, 0 failures (includes `tests/test_archive_upper_art.gd`).
- `qa/playthrough_ch2.tscn --legacy` (1.0 chapter as an old save): exit 0, 86 taps, 0 fallbacks, 3 continue checks.
- `qa/playthrough_ch2.tscn --expansion=2` on the merged tree (Night Cell and Cold Store taps included): exit 0, 192 taps through the 3D
  scene, 0 logic fallbacks, 0 taps under a HUD control, 4 continue checks. N7-N10 and G2 alone (before the merge): 151 taps. Played by taps:
  the book lift ride, wedge, counter, board, enlarger, cabinet, the dead and the fitted lamp, the spiral stair down.
- `tap_map --hud-check` (`--expansion=2`, views of the new zones): 0 failures at phone20 and tablet10 for the Gallery (12 controls in
  8 views), Plate Room (3 in 3), Office (9 in 3, 2 banner warnings) and the Pump Room lift views (5 in 4).
- Draw calls with the HUD (`tap_map --perf --screen=phone20`): Gallery 23-60, Plate Room 18-39, Office 27-38, Pump Room views 34-67 (the
  lift views 34-58). The most expensive new view is the Gallery root view (60).
- Screenshots of every new view: `docs/previews/ch2_expansion/scene_*.jpg`.
- QA tools that save games use a private save directory per run since 2026-11-01 (they used to share
  `user://qa_ch2_save.json`).

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
- **View id `desk`** belongs to the hall: the Office's desk view is `office_desk`, the Night Cell's is `cell_desk`. The hall also owns
  `plan`: the Cold Store's plan plate view is `cold_plate`. A zone must never `add_view` an id the hall (or another zone) uses: the camera
  keeps ONE table of views, the last `add_view` wins.
- **Night Cell light table.** The sheets lie stacked on the glass, so a tap reaches the top sheet only: the top sheet turns / flips by a
  tap on it or on its tab and by drags, and every sheet has a round turn button and a round flip button (tape colour) on the desk in front
  of the box (six `IA_turn_i` / `IA_flipbtn_i`, original geometry, an icon drawn in code). The lower two sheets' own colliders are removed.
  The two outer rows of each sheet (outside the 7-row window) are dimmed by a bezel quad. The model's `M_Acetate` is cut to 7 % alpha in
  the scene (three milky layers washed the prints out). Blocked cells are drawn near black (alpha .94) so the lit digits read.
- **Night Cell diary and slip** are on their own view `cell_desk` (the table view is too tight to hold them); the pencilled slip is a
  small paper quad (`doc2x.light_note`).
- **Cold door wheels** take taps (+1) and drags (+-1); a tap near the lock on the closed leaf steps in to `cold_wheels` (the wheels sit
  in a recess the leaf's mesh covers). Their `M_Brass_Polished` is swapped for a matte brass (no reflections in the room = black).
- **Wallpaper.** `M_Wallpaper_Cell` is copied at runtime with its texture's contrast / saturation / brightness reduced (`adjust_bcs`).
- **Cold Store frost window.** The model's `window_glass` lies flat (a white line across the pane) and is hidden; `window_glow` (the
  light well's card) is dimmed to a pale cyan so the pale signs read through the wiped pane; the three sign quads use a small shader that
  shows a sign only where the wipe mask is clear (thin patches in the frost never give a sign away).
- **Cold Store plan plate** is moved 8.5 cm along the wall (z 0.915): a pilaster in the wall model covers the right edge of the contract's
  position. Its picture is drawn in code from the logic's `v_bay` with the carriage tag atlas (`ArchiveCold.plan_image`).
- **Cranks view.** The camera backs through the south wall for the wide shot of all five cranks (the wall is hidden and its colliders are
  switched off while the `cranks` view is up); it is re-fitted to where the carriages stand whenever they have come to rest.
- **Chest interior.** The open chest's floor lies near its rim: the crystals and the note are lifted 0.23 / 0.16 m above the model's
  `crystal_mount_*` / `note_mount`.
- **Frost sketch** has a model for the bag icon (`frost_sketch.glb`, original) and a reader page drawn by `ArchiveCold.sketch_texture`.

## Left to do

- Night Cell and Cold Store (N3-N6, M2, M3, M5, M6) are in the scene and played by taps in `qa/playthrough_ch2.gd`
  (`_n3_n6_taps`). Not done there: the glove / cloth stroke in hand (hands phase 2), a hold-to-wipe cloth that follows the finger
  (the pane is wiped by a finger drag or a band tap; the cloth in hand only floats), the kettle has no tick sound of its own (it
  is in the cell's ambience), the lore cans are dressing (no tap), the lid of the chest is not tappable (rings open it).
- Stage B scene is in (book lift, wedge/stair, Gallery, Plate Room, Office, G2, M4). Not done: a real item icon/model for
  `roll_slips` and `staff_print` (the bag shows the name; `ItemIcons` logs a missing-model warning), the hung weights are only visible
  from the `lift_weights` view, the lift's hall stop has no hall-side door (button 0 fades to the hall's root view).
- Hands: glove, poses, cloth wipe stroke, receiver needle in hand (phase 2).
- Flip `ArchiveLogic.EXPANSION_STAGE` to 2 and `EXPANSION_SCENE_READY` in `qa/playthrough_ch2.gd` when everything is playable.
- Audio hooks: N7-N10 events, the enlarger fan loop and the stair steps are wired (`archive_lift/gallery/plate/office/hall_exp`); the ids in `docs/AUDIO_CH2X.md` for any other expansion event are the other rooms' job.

## Update 1.1: switch-on and polish (2026-11-01)

- `EXPANSION_STAGE = 2`; Trial start button shows on the Chapter 2 row for a new game; old saves (fixtures `tests/fixtures/ch2_legacy_*.json`) load into the legacy flow (tests pass); the chapter card counts `puzzle_ids()`. Legacy 1.0 tests now build their game with `ArchiveLogic.new_legacy()`.
- Version name / short version 1.1 in `export_presets.cfg` (codes untouched).
- QA harness: every QA scene saves to a per-pid file and `tools/qa_run.sh` gives each run its own `XDG_DATA_HOME` (`docs/GAMEPLAY_QA.md`). `tap_map --views=all` now includes the expansion's rooms.
- Polish, each with before / after shots in `docs/previews/ch2_expansion/polish_1_1/` (`before_*.png`, `after_*.png`; the enlarger "after" shot was taken with a tighter camera that was reverted, so only its digit strip applies; after_pipes is at fov 48, shipped 51):
  light table controls (bakelite turn knob + brass flip knob per sheet on a brass escutcheon with a tape-colour stripe, between the table's feet, 1.12 scale); procedural non-repeating frost (`frost_reveal.gdshader`, wipe mask unchanged); "Pinch to zoom." once ever (`Settings zoom_tip_seen`); Pump pipes view (lift cage culled while it is up, fov 51); counterweight rack (iron uprights, hooks with lips, plank shelf, numbered label strip, work lamp) and a calm painted `iron_rust` wall (texture regenerated, metallic 0.7); models `roll_slips`, `staff_print`; enlarger print: digits 5 px blocks on a pale strip (tap the print for the zoom reader).
- Not changed: the enlarger camera stays wide (the zoom knob and focus ring must be in view); the print is read in the zoom overlay.

## Open after 1.1
- Hands phase 2 (glove rig, cloth wipe stroke in hand, receiver needle in hand).
- Native RU / UZ review of the new strings (all 16 hint goals, moments, Trial texts).
- Human playtests (5): they decide the length claim ("about an hour" until then).
- Cold Store cloth hold-to-wipe, kettle tick, chest lid tap, lift hall door (see "Left to do" above; those lines are historic).

### QA numbers, update 1.1 tree (2026-11-01, software Vulkan under Xvfb)
- `tools/run_tests.sh`: 307 tests, 42065 checks, 0 failures.
- `playthrough_ch2 --expansion=2` (default): EN seed 9137 177 taps, RU seed 2468 193 taps, UZ seed 8921 190 taps: exit 0, 0 logic fallbacks, 4 continue checks each, 0 failed, 0 taps under a HUD control (RU also 0 on the first try; EN and UZ showed a one-off "plate door back" fallback before the harness aimed at the door twice).
- `playthrough_ch2 --legacy` seed 3333: exit 0, 89 taps, 0 fallbacks, 3 continue checks.
- Chapter 1 playthrough seed 4242: exit 0, 100 taps, 0 fallbacks, 3 continue checks. Chapter 3 (`--key=strand --seed=2024`, reads the ch2 choices): exit 0, 111 taps, 0 fallbacks.
- `tools/chaos_run.sh --chapter=ch2 --seed=11 --steps=400`: 400 steps, 314 taps, 176 item-in-hand taps, 0 violations, 0 script errors.
- `tap_map --chapter=ch2 --views=all --hud-check`: phone20 181 controls in 79 views, 0 failures, 34 banner warnings; tablet10 178 controls in 79 views, 0 failures, 30 banner warnings. (The six light-table knobs are bare tap boxes, not measured by this tool; their boxes are 6.9 cm = about 7 mm raw on phone20 and clear 9 mm with the tap assist like the other small controls; IA_switch and the sheet tab were measured: 11.5 mm / 11.0 mm with assist.)
- `tap_map --perf --screen=phone20` (HUD on): max 131 draw calls (hall root), Cell 85, Echo stacks 90; all Chapter 2 views <= 150.
- `ui_screens` android20 EN/RU/UZ: 100 shots, 0 layout issues. iphone EN/RU/UZ: 100 shots, 0 layout issues (the first iphone run stalled three times in the Xvfb watchdog, an environment hang; the rerun passed).
