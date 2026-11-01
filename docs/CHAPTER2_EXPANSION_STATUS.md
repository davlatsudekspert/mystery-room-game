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
| Pump Room | `archive_pump.gd` | room_pump, boiler, manifold_plate, pipe_run, book_lift_cage (closed, N7 not wired), mallet on the bench; N2 valves, glow bands, lamps, needles, mallet probe, diagram card per variant, M1 moment. 6 views. 49 draw calls with HUD at most. |
| Plan overlay, hints, settings, trial, chapter card | `src/ui/hud.gd`, `settings_panel.gd`, `main_menu.gd` | `show_plan()` (item `floor_plan` and the hall wall frame), hint "Go to <room>", hint button/line honour `hints_allowed()`, Settings "hands" + "moments", Trial start button (only when `EXPANSION_STAGE >= 1`), chapter card shows Trial stamp and `ui2x.legacy_note`. |
| Hands phase 1 | `src/fx/hand_layer.gd`, `src/core/hold_table.gd` | floating item on the camera: UV lamp (beam follows the finger), mallet (swings on tap), cloth, receiver, keys. Rows in `HoldTable.ROWS`. |
| QA | `qa/exp_shots.gd`, `qa/playthrough_ch2.gd`, `qa/ui_screens.gd` | see below |

## Deviations from the model contract

- `service_door` has one site (z 2.95), but the logic draws `v_panel` in A/B/C. The variant changes the LETTER on the door's
  hatch (and the receiver table); the two decoy hatches carry the other letters. The door model is moved 7 cm into the hall so
  its dial clears the hall's dado rail.
- The pipe board draws each game's graph itself (nodes by `ArchivePump.layout`, zero crossings for all six graphs, tested);
  the model's nine candidate segments are hidden. A larger diagram card hangs beside the manifold (the model's plate is too small).

## Left to do

- N3-N6 rooms: Night Cell (models in repo: room_cell, cot, light_table, ..., cold_door), Cold Store (room_cold, carriages,
  frost_window, cold_chest), their zones (`BUILDERS` in `archive_zones.gd`), interactions, moments M2, M3, M5, M6.
- Stage B: Reading Gallery, Plate Room, Director's Office zones; N7 lift (cage, weights, call buttons), wedge pin on the
  stair, N8 board, N9 enlarger, N10 cabinet, M4. The `playthrough_ch2.gd` solver (`ArchiveSolver`) plays these at logic level.
- Hands: glove, poses, cloth wipe stroke, receiver needle in hand (phase 2).
- Flip `ArchiveLogic.EXPANSION_STAGE` to 2 and `EXPANSION_SCENE_READY` in `qa/playthrough_ch2.gd` when everything is playable.
- Audio hooks for N3-N10 events (ids in `docs/AUDIO_CH2X.md`), `c2x_enlarger_fan` loop, `c2x_stair_steps` on the spiral stair.
