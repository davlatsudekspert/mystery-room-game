# Chapter 2 expansion audio ("The Whole Building")

91 sounds for the expansion in `docs/CHAPTER2_EXPANSION.md`: six room ambiences, puzzle and object sounds for N1-N10, the
six reaction-moment cues in Full and Soft, and hand-held item foley. Everything is original, synthesised by the modules
`tools/audio/sounds/c2x_amb.py`, `c2x_sfx.py`, `c2x_moments.py`, `c2x_hands.py` (registered in `tools/audio/synth_all.py`),
deterministic (a re-run gave byte-identical OGG for the 63 files compared). No recordings, no third-party material.

```bash
python3 tools/audio/synth_all.py --module c2x_amb,c2x_sfx,c2x_moments,c2x_hands --readme --jobs 4   # about 1-2 min
python3 tools/audio/measure_ch2x.py                                                                   # measurements below
godot --headless --path game --import
```

Files: `game/assets/audio/ambience/amb_c2x_<room>.ogg`, `game/assets/audio/sfx/<id>.ogg`. They load with the existing
`AudioManager` (`AudioManager.sfx("<id>")`, `AudioManager.sfx_loop(...)`, ambience layers by name). No game code was changed.

## What was measured, and what could not be

We cannot listen in this environment. The checks are numeric proxies from the **encoded** files (`tools/audio/measure_ch2x.py`),
so treat the sound design itself as **not yet auditioned by a human**: a listening pass on a phone speaker and on headphones is still needed.

- Ambiences: EBU R128 integrated loudness -24.0 LUFS (-24.1 for the pump bed), true peak -9.6 to -14.3 dBTP (limit -1), no limiter anywhere.
- One-shots: decoded sample peak -1.0 dBFS (Full moment cues -6, Soft moment cues -14, hand foley -6). No file reaches -0.1 dBFS (no clipping).
  `c2x_valve_wheel` peaks at -1.6 dBFS (the encoder trim loop kept the nearer-but-under-target result).
- No hiss in the high band: the share of energy above 6 kHz is -53 to -76 dB for the ambiences (limit -30 dB; for comparison the Chapter 2 hall bed measures -31 dB).
  All noise layers are band-limited (nothing above about 3.5 kHz); the only highs are short ticks and clicks.
  One-shot clicks (ring click, tag lift, cabinet wheel, keys) are as bright as the existing `collar_click` (spectral centroid 7 kHz); that is deliberate for clicks.
- Seamless loops: every ambience is built from whole-cycle tones, FFT-built (periodic) noise and circularly mixed events and reverb tails.
  Encoded-file seam checks (jump ratio must be below 1.0; a step the size of the file's own 99.9th-percentile step is 1.0):
  pump 0.44, cell 0.44, cold 0.30, gallery 0.38, plate 0.80, office 0.33; `c2x_enlarger_fan` 0.69. Level jump across the seam 0.07-1.08 dB, except the gallery
  at 3.18 dB (percentile 89: ordinary for that bed, which breathes by several dB in its slow air swells; it is not a click).
- Mono-sum (a phone speaker): the hums use the same frequency in both channels, nothing cancels. The mono file is -3.9 to -6.2 dB below the stereo file, the same range as the
  Chapter 3 beds (-3.4 to -5.9); the checker flags anything below -7 dB.
- Each ambience is clearly different: the spectral distance between any two beds is at least 10 dB RMS over 1/3-octave bands (pump-cell 25.7, cell-gallery 27.3, plate-pump 24.2,
  pump-gallery 10.8, cold-office 10.3 are the closest pairs), and they differ in rhythm: pump irregular ticks and drips, cell 2 clock ticks per second, cold still and tonal,
  gallery very slow, plate 2.5 timer ticks per second, office a 0.6 s mantel clock and wind gusts.

Ambience distance matrix (dB RMS, 1/3-octave spectrum):

| | pump | cell | cold | gallery | plate | office |
|---|---|---|---|---|---|---|
| pump | 0 | 25.7 | 11.8 | 10.8 | 24.2 | 14.8 |
| cell | 25.7 | 0 | 20.9 | 27.3 | 16.4 | 18.7 |
| cold | 11.8 | 20.9 | 0 | 12.5 | 18.3 | 10.3 |
| gallery | 10.8 | 27.3 | 12.5 | 0 | 24.7 | 14.2 |
| plate | 24.2 | 16.4 | 18.3 | 24.7 | 0 | 13.0 |
| office | 14.8 | 18.7 | 10.3 | 14.2 | 13.0 | 0 |

## What the scene should play

Ambience (one bed per room, crossfade like the other chapters; the Hall keeps `amb_archive`):

| Room | Ambience id |
|---|---|
| `pump` | `amb_c2x_pump` |
| `cell` | `amb_c2x_cell` |
| `cold` | `amb_c2x_cold` |
| `gallery` | `amb_c2x_gallery` |
| `plate` | `amb_c2x_plate` |
| `office` | `amb_c2x_office` |

Reaction moments (event `moment:<id>`, `ArchiveExpData.MOMENTS`). Settings "Eerie moments": Full plays the plain id, **Soft plays `<id>_soft`**, Off plays nothing.
The Full cues peak at -6 dBFS and the Soft ones at -14 dBFS; with the ambience at -24 LUFS neither is more than +6 dB over the room bed at the default volumes.
Files run up to 0.8 s past the moment's `seconds` (tail), and some cues start with a deliberate quiet lead-in (the first sound of `steps_above` is at 0.5 s).

| Moment | Cue id (Full) | Soft id | Length | What happens |
|---|---|---|---|---|
| m1 first entry to the Pump Room | `lamp_dip` | `lamp_dip_soft` | 4.0 s | lamp hum sinks in pitch and level to an ember, flares back, bulb tick (Full only) |
| m2 first look at the Cell door | `knocks` | `knocks_soft` | 3.8 s | three muffled knocks from inside, then a kettle ticking |
| m3 first frost band wiped | `frost_steps` | `frost_steps_soft` | 4.7 s | a soft whoosh passes behind the pane (Full adds two far steps and a faint squeak) |
| m4 arrival in the Gallery | `roll_call` | `roll_call_soft` | 9.2 s | PA horn sounds a count in tones only (two notes, then three), stops, long soft hiss; no voice |
| m5 Cold Store with the aisle open | `steps_above` | `steps_above_soft` | 5.8 s | four slow footfalls cross the ceiling (Full adds dust ticks) |
| m6 correct aisle opened | `echo_chime` | `echo_chime_soft` | 5.6 s | three soft glass notes E, B, F sharp in a dark hall (Soft: two) |

Puzzle and object events (`ArchiveLogic._emit` names; `:` parts are arguments). Existing sounds are reused where they already fit.

| Event | Play |
|---|---|
| `panel_opened:i` | `c2x_panel_open` |
| `panel_cold:i` | `c2x_panel_cold` |
| `dial_n1:d` / `n1_dial_wrong` | existing `dial_wind` / `dial_return` |
| `pump_opened` | `c2x_door_iron` (then `puzzle_solved` for `solved:warm`) |
| `pipe:i:v` (valve wheel toggled) | `c2x_valve_wheel` |
| `pipes_hazard` | `c2x_pipe_hazard` |
| `thawed` | `c2x_pipe_flow` then about 1.0 s later `c2x_thaw` (then `puzzle_solved`) |
| `tap:seg:full` / `tap:seg:dead` / `tap:seg:cracked` | `c2x_mallet_full` / `c2x_mallet_dead` / `c2x_mallet_cracked` (pitch_scale 0.94-1.06 per segment for variety) |
| `valves_locked_n2`, `need_mallet`, `sheets_locked`, `cranks_locked`, `need_aisle`, `need_cloth`, `no_pressure`, `weights_locked`, `room_locked`, `travel_refused` | `c2x_refused` |
| light table opened first time | `c2x_lightbox_on` |
| drag a sheet | `c2x_sheet_slide`; turn button `c2x_sheet_turn`; flip tab `c2x_sheet_flip` (`sheet:i:rot:flip`) |
| `light_digits` | `c2x_light_digits` |
| `cold_wheel:i:v` | `c2x_cab_wheel` |
| `cold_frozen` | `c2x_cold_frozen` |
| `cold_opened` | `c2x_door_cold` |
| `crank:k:target` | `c2x_crank`, then `c2x_carriage_roll` 1.2 s later |
| `clunk:k` | `c2x_carriage_clunk` |
| `aisle_found` | `c2x_aisle_found` (m6 comes as its own moment) |
| `band_wiped:b:s` / `band_clear:b` | `c2x_frost_wipe_<1 + b % 4>` (use 1-4 in rotation so repeats differ); `frost_done` -> `c2x_frost_done` |
| `ring:i:v` | `c2x_ring_click` |
| `chest_sealed` / `chest_opened` | `c2x_chest_sealed` / `c2x_chest_unlock` |
| `weight:i:1` / `weight:i:0` | `c2x_weight_hang` / `c2x_weight_off` |
| `counter_heavy` / `counter_light` | `c2x_counter_heavy` / `c2x_counter_light` |
| `lift_balanced` | `c2x_lift_balanced` |
| `lift_stuck` | `c2x_lift_stuck` |
| `lift_moved:f` | `c2x_lift_move`, then `c2x_lift_bell` 3.6 s later (arrival) |
| `wedge_out` | `c2x_wedge_pull` |
| travelling by the spiral stair | `c2x_stair_climb` (version 1.1 walk, five quick steps, played by `ArchiveZones.transition`; the long `c2x_stair_steps` stays in the catalogue); stairwell and lift-hall doors `c2x_door_service` |
| camera travel over 1.5 m (any chapter) | `c2x_step_soft_a` / `c2x_step_soft_b` at the bottom of each head-bob dip, -10 dB, pitch 0.94-1.06 (`RoomCamera`) |
| walking through a tapped door (Chapter 2 rooms) | `c2x_door_service` at the start, then the same steps |
| `tag_hung:t:h` / `tag_lifted:h` | `c2x_tag_hook` / `c2x_tag_lift` |
| `board_wrong` / `board_ok` | `c2x_board_wrong` / `c2x_board_ok`; opening the gallery pass door with the key `c2x_door_pass` |
| `strip_loaded:i` | `c2x_strip_load` |
| `enl_zoom:z` / `enl_focus:f` | `c2x_enlarger_knob` / `c2x_enlarger_focus` |
| exposing a print | `c2x_enlarger_lamp`; `AudioManager.sfx_loop("c2x_enlarger_fan", true, -14.0)` while the enlarger view is up (the loop stops with the scene) |
| `print_ready` | `c2x_print_ready` |
| `cab_wheel:i:v` | `c2x_cab_wheel` |
| `cab_opened` | `c2x_cab_open` |
| `lamp_dead` | `c2x_lamp_fail` |
| `lamp_installed` | `c2x_lamp_fit` |
| opening the floor plan | `c2x_plan_unfold` |

Hands (section 12): play on lift, equip (item selected for use) and put away. Map ItemDB ids to the four tools: `wipe_cloth` -> `cloth`, `mallet` -> `mallet`,
`uv_lamp` -> `uvlamp`, any key (`pass_key`, `ch2_key`, `key_*`) -> `keys`. Ids: `hand_pickup_<tool>`, `hand_equip_<tool>`, `hand_putaway_<tool>`
(12 files). Other held items can layer `hand_leather_creak` under their own pickup sound.

## All sounds

Level is peak (one-shots) or integrated loudness (ambiences). "length" includes the reverb tail. `>6k share` is the energy above 6 kHz relative to the total.

| id | file | length | level | >6k share | loop | purpose |
|---|---|---|---|---|---|---|
| `amb_c2x_pump` | `ambience/amb_c2x_pump.ogg` | 48.00 s | -24.1 LUFS, TP -11.3 | -76 | yes | Pump Room: boiler roar (40-380 Hz, flame flutter), 50 Hz mains hum, iron pipe expansion ticks, drips, a far pipe knock (no noise above 3.5 kHz) |
| `amb_c2x_cell` | `ambience/amb_c2x_cell.ogg` | 48.00 s | -24.0 LUFS, TP -12.4 | -53 | yes | Night Cell: a quiet warm room, kettle simmer (soft bubbles, 0.5-3 kHz), a small clock ticking twice a second, a faint low pipe hum |
| `amb_c2x_cold` | `ambience/amb_c2x_cold.ogg` | 48.00 s | -24.0 LUFS, TP -14.3 | -72 | yes | Cold Store: refrigeration compressor hum (50 Hz series), a slow fan band, glassy ice creaks, a far carriage rumble |
| `amb_c2x_gallery` | `ambience/amb_c2x_gallery.ogg` | 48.00 s | -24.0 LUFS, TP -9.6 | -76 | yes | Reading Gallery: a big quiet space, very low air, distant ventilation with two narrow drifting tones, far wood creaks and a few dust ticks, long reverb |
| `amb_c2x_plate` | `ambience/amb_c2x_plate.ogg` | 48.00 s | -24.0 LUFS, TP -12.8 | -56 | yes | Plate Room (darkroom): a 100 Hz safelight buzz, water dripping into a tray, an enlarger timer ticking 2.5 times a second, a faint tap trickle |
| `amb_c2x_office` | `ambience/amb_c2x_office.ogg` | 48.00 s | -24.0 LUFS, TP -12.9 | -59 | yes | Director's Office: a deep mantel clock (tock every 0.6 s), wind gusting at the window glass, a green desk-lamp hum and a floorboard |
| `c2x_panel_open` | `sfx/c2x_panel_open.ogg` | 1.48 s | peak -1.0 dBFS | -29 | no | Warm Wall: a painted panel on the east wall swings open (latch tick, dry hinge, soft thud) |
| `c2x_panel_cold` | `sfx/c2x_panel_cold.ogg` | 0.71 s | peak -1.0 dBFS | -62 | no | Warm Wall: a cold panel is rapped, a dull flat knock with no answer |
| `c2x_door_iron` | `sfx/c2x_door_iron.ogg` | 3.21 s | peak -1.0 dBFS | -29 | no | Pump Room door found behind the panel: bolt clank, a long iron hinge groan, a heavy stop |
| `c2x_door_cold` | `sfx/c2x_door_cold.ogg` | 3.00 s | peak -0.9 dBFS | -78 | no | Cold Store door opens: the rubber seal peels (soft sigh), the latch lets go, cold air moves out |
| `c2x_cold_frozen` | `sfx/c2x_cold_frozen.ogg` | 0.75 s | peak -1.1 dBFS | -28 | no | Frozen door: the wheel will not turn, an ice crunch and a dull thud against the seal |
| `c2x_door_service` | `sfx/c2x_door_service.ogg` | 2.21 s | peak -1.1 dBFS | -25 | no | Service door (stairwell, lift hall): a light steel latch and a short hinge squeak, soft close |
| `c2x_door_pass` | `sfx/c2x_door_pass.ogg` | 2.38 s | peak -0.9 dBFS | -20 | no | Pass door in the gallery: the pass key slides in, turns, the bolt draws back and the door unlatches |
| `c2x_valve_wheel` | `sfx/c2x_valve_wheel.ogg` | 1.29 s | peak -1.6 dBFS | -24 | no | Manifold valve wheel turned: a big iron wheel squeaks over a notch, a breath of pressure, a click |
| `c2x_pipe_flow` | `sfx/c2x_pipe_flow.ogg` | 2.17 s | peak -1.0 dBFS | -88 | no | Pressure reaches the coil: a low thrum, rushing water in the pipe, gurgles, tapering off (1.9 s) |
| `c2x_pipe_hazard` | `sfx/c2x_pipe_hazard.ogg` | 2.23 s | peak -0.8 dBFS | -24 | no | Wrong route: the vent to the hall hisses, the pipe rattles and a warning ping rings (calm, nothing is lost) |
| `c2x_thaw` | `sfx/c2x_thaw.ogg` | 3.39 s | peak -1.1 dBFS | -27 | no | The Cold Store door thaws: ice ticks and cracks, running drips, a long settling creak |
| `c2x_mallet_full` | `sfx/c2x_mallet_full.ogg` | 1.25 s | peak -1.0 dBFS | -68 | no | Mallet on a pipe that carries pressure: a full, low, long tone (about 130 Hz) |
| `c2x_mallet_dead` | `sfx/c2x_mallet_dead.ogg` | 0.50 s | peak -1.1 dBFS | -47 | no | Mallet on a dead pipe: a short, high, empty tink (about 620 Hz) |
| `c2x_mallet_cracked` | `sfx/c2x_mallet_cracked.ogg` | 1.19 s | peak -0.9 dBFS | -32 | no | Mallet on a cracked pipe next to the hazard: a rattling buzz that decays unevenly |
| `c2x_lightbox_on` | `sfx/c2x_lightbox_on.ogg` | 1.86 s | peak -0.9 dBFS | -67 | no | Light table: a tube starter flickers three times and the box settles to a warm glow with a faint 100 Hz hum |
| `c2x_sheet_slide` | `sfx/c2x_sheet_slide.ogg` | 0.79 s | peak -1.1 dBFS | -22 | no | An acetate sheet slides across the glass of the light table: smooth plastic friction and a tiny flex |
| `c2x_sheet_turn` | `sfx/c2x_sheet_turn.ogg` | 0.58 s | peak -1.1 dBFS | -13 | no | A sheet is turned a quarter: a short slide and a soft plastic tick as it seats |
| `c2x_sheet_flip` | `sfx/c2x_sheet_flip.ogg` | 0.70 s | peak -1.1 dBFS | -12 | no | A sheet is flipped over by its tab: a soft flap of acetate, then two taps on the glass |
| `c2x_light_digits` | `sfx/c2x_light_digits.ogg` | 3.09 s | peak -1.0 dBFS | -36 | no | The two digits light up on the table: a soft, warm two-note glass chime over a gentle glow swell |
| `c2x_crank` | `sfx/c2x_crank.ogg` | 2.50 s | peak -1.0 dBFS | -17 | no | Compactus crank: a handle turned with a ratchet clicking faster, a gear grind (1.4 s) |
| `c2x_carriage_roll` | `sfx/c2x_carriage_roll.ogg` | 3.95 s | peak -1.1 dBFS | -56 | no | A heavy shelf carriage rolls one slot along its rails: a low rumble with rail-joint beats, a stop |
| `c2x_carriage_clunk` | `sfx/c2x_carriage_clunk.ogg` | 1.51 s | peak -0.9 dBFS | -33 | no | The carriage will not move (no gap beside it): a dull steel clunk and a short rattle of the rails |
| `c2x_aisle_found` | `sfx/c2x_aisle_found.ogg` | 3.14 s | peak -1.2 dBFS | -81 | no | The right aisle opens: the shelves part and a long breath of still, cold air with a faint low chime |
| `c2x_frost_wipe_1` | `sfx/c2x_frost_wipe_1.ogg` | 0.84 s | peak -1.1 dBFS | -19 | no | Frost window, wipe variant 1: a cloth drags across fine ice crystals (crisp, medium) |
| `c2x_frost_wipe_2` | `sfx/c2x_frost_wipe_2.ogg` | 1.05 s | peak -1.1 dBFS | -22 | no | Frost window, wipe variant 2: a longer, softer stroke with a glass squeak at the turn |
| `c2x_frost_wipe_3` | `sfx/c2x_frost_wipe_3.ogg` | 0.65 s | peak -0.9 dBFS | -17 | no | Frost window, wipe variant 3: a short quick wipe, grittier |
| `c2x_frost_wipe_4` | `sfx/c2x_frost_wipe_4.ogg` | 1.18 s | peak -1.0 dBFS | -26 | no | Frost window, wipe variant 4: a slow low-pitched stroke, damp and heavy, with a squeak |
| `c2x_frost_done` | `sfx/c2x_frost_done.ogg` | 2.18 s | peak -1.0 dBFS | -20 | no | The last band is clear: loose ice flakes fall and tinkle on the sill |
| `c2x_ring_click` | `sfx/c2x_ring_click.ogg` | 0.38 s | peak -1.1 dBFS | -9 | no | Chest ring turned one symbol: a firm brass detent click with a small ring (the next ring follows) |
| `c2x_chest_sealed` | `sfx/c2x_chest_sealed.ogg` | 0.54 s | peak -1.0 dBFS | -12 | no | The chest is still sealed: the lid is tried, a short rattle against the lock |
| `c2x_chest_unlock` | `sfx/c2x_chest_unlock.ogg` | 3.08 s | peak -1.0 dBFS | -31 | no | The rings line up: three tumbler clicks, a deep latch release, the lid creaks open with a faint glass rustle |
| `c2x_weight_hang` | `sfx/c2x_weight_hang.ogg` | 1.56 s | peak -1.0 dBFS | -27 | no | A cast-iron counterweight is hung on the hook: a metal clank and the hook swinging |
| `c2x_weight_off` | `sfx/c2x_weight_off.ogg` | 1.33 s | peak -1.2 dBFS | -20 | no | A counterweight is lifted off the hook: a quick scrape and a light clink |
| `c2x_lift_balanced` | `sfx/c2x_lift_balanced.ogg` | 2.38 s | peak -1.1 dBFS | -61 | no | Load and counterweight are equal: the weights swing level, the cable settles with a low relief creak |
| `c2x_counter_heavy` | `sfx/c2x_counter_heavy.ogg` | 2.18 s | peak -0.9 dBFS | -38 | no | The counterweight is too heavy: the cable groans taut and the weights knock the frame |
| `c2x_counter_light` | `sfx/c2x_counter_light.ogg` | 1.53 s | peak -0.7 dBFS | -23 | no | The counterweight is too light: a slack cable clink and a small hollow tap |
| `c2x_lift_stuck` | `sfx/c2x_lift_stuck.ogg` | 2.14 s | peak -0.9 dBFS | -43 | no | The book lift is not balanced: the cage jolts against its stops with a short motor strain |
| `c2x_lift_bell` | `sfx/c2x_lift_bell.ogg` | 2.07 s | peak -1.0 dBFS | -60 | no | Lift bell: a small brass arrival bell, one clear ding with a short ring |
| `c2x_lift_move` | `sfx/c2x_lift_move.ogg` | 4.91 s | peak -1.1 dBFS | -37 | no | The book lift travels one floor: a motor hum rising, cable and weight clanks passing, a settling clunk (3.6 s) |
| `c2x_wedge_pull` | `sfx/c2x_wedge_pull.ogg` | 2.59 s | peak -1.1 dBFS | -25 | no | The wedge pin is pulled from the blocked spiral stair: wood squeals out of a tight fit, a knock, a clatter down the steps |
| `c2x_step_soft_a` | `sfx/c2x_step_soft_a.ogg` | 1.48 s | peak -1.0 dBFS | n/a | no | One soft footstep on the old floor (camera travel, left foot): a dull low thud and a quiet scuff of the sole |
| `c2x_step_soft_b` | `sfx/c2x_step_soft_b.ogg` | 1.47 s | peak -1.1 dBFS | n/a | no | One soft footstep on the old floor (camera travel, right foot): slightly lighter and a little higher than the left |
| `c2x_stair_climb` | `sfx/c2x_stair_climb.ogg` | 2.43 s | peak -0.9 dBFS | n/a | no | A short climb on the iron stair (camera travel): five quick steps on steel treads, each with a faint ring |
| `c2x_stair_steps` | `sfx/c2x_stair_steps.ogg` | 4.08 s | peak -1.1 dBFS | -28 | no | Climbing the iron spiral stair: six slow footsteps on steel treads, each with a soft ring |
| `c2x_tag_hook` | `sfx/c2x_tag_hook.ogg` | 0.59 s | peak -1.0 dBFS | -16 | no | A staff tag is hung on a board hook: a brass hook tick and the tag swinging against wood |
| `c2x_tag_lift` | `sfx/c2x_tag_lift.ogg` | 0.36 s | peak -1.2 dBFS | -9 | no | A staff tag is lifted off its hook: a light tick and a small slide |
| `c2x_board_ok` | `sfx/c2x_board_ok.ogg` | 2.14 s | peak -1.0 dBFS | -24 | no | The tags hang in the right order: a soft rattle of all six, a wood clack and a tiny key dropping into the tray |
| `c2x_board_wrong` | `sfx/c2x_board_wrong.ogg` | 0.79 s | peak -1.0 dBFS | -39 | no | The tags do not agree with the slips: a dull wooden rattle, nothing happens |
| `c2x_enlarger_lamp` | `sfx/c2x_enlarger_lamp.ogg` | 1.60 s | peak -0.9 dBFS | -25 | no | Enlarger lamp: a switch click, a thump of the transformer and a warm lamp glow that holds a moment, then a click off |
| `c2x_enlarger_knob` | `sfx/c2x_enlarger_knob.ogg` | 0.40 s | peak -1.1 dBFS | -8 | no | Enlarger zoom or head knob turned a step: a small geared detent click and a brief ring |
| `c2x_enlarger_focus` | `sfx/c2x_enlarger_focus.ogg` | 0.83 s | peak -1.1 dBFS | -16 | no | Enlarger focus ring: a smooth knurled ring turning, fine ticks, a soft end stop |
| `c2x_enlarger_fan` | `sfx/c2x_enlarger_fan.ogg` | 4.00 s | peak -1.2 dBFS | -90 | yes | Enlarger lamp-house fan (seamless 4 s loop for sfx_loop): a small fan with a 20 Hz blade beat over a soft 100 Hz hum |
| `c2x_strip_load` | `sfx/c2x_strip_load.ogg` | 0.72 s | peak -0.8 dBFS | -9 | no | A negative strip is slid into the carrier: a smooth film slide and a small click as the carrier closes |
| `c2x_print_ready` | `sfx/c2x_print_ready.ogg` | 2.03 s | peak -1.2 dBFS | -56 | no | The print develops in the tray: paper slips into the liquid, a gentle slosh, a few drops (1.8 s) |
| `c2x_cab_wheel` | `sfx/c2x_cab_wheel.ogg` | 0.35 s | peak -1.2 dBFS | -14 | no | Cabinet digit wheel advances one number: a crisp brass tick with a tiny barrel click |
| `c2x_cab_open` | `sfx/c2x_cab_open.ogg` | 1.92 s | peak -1.1 dBFS | -35 | no | Strand's cabinet opens: the last wheel seats, a latch drops, a wooden drawer slides out and a lamp glass rolls and clinks |
| `c2x_lamp_fail` | `sfx/c2x_lamp_fail.ogg` | 1.00 s | peak -1.0 dBFS | -55 | no | The booth projector lamp is dead: a dull filament tink, a weak electrical sigh dropping in pitch |
| `c2x_lamp_fit` | `sfx/c2x_lamp_fit.ogg` | 2.14 s | peak -0.8 dBFS | -32 | no | The new projector lamp is fitted: a glass bulb turned into the socket, a clink, the filament warming up in pitch and a soft tick |
| `c2x_refused` | `sfx/c2x_refused.ogg` | 0.72 s | peak -1.0 dBFS | -64 | no | A closed room or lift floor is tried: two dull wooden taps, calm, no alarm |
| `c2x_plan_unfold` | `sfx/c2x_plan_unfold.ogg` | 0.98 s | peak -1.0 dBFS | -19 | no | The floor plan is unfolded: crisp paper creases and a soft rustle |
| `lamp_dip` | `sfx/lamp_dip.ogg` | 3.98 s | peak -5.9 dBFS | -58 | no | M1 lamp that dies (3.5 s): the work lamp's transformer hum sinks in pitch and level to an ember, then flares back with a small bulb tick |
| `lamp_dip_soft` | `sfx/lamp_dip_soft.ogg` | 3.99 s | peak -14.0 dBFS | -71 | no | M1 lamp that dies, Soft: the same hum dip, shallower and rounder, no tick |
| `knocks` | `sfx/knocks.ogg` | 3.81 s | peak -6.0 dBFS | -53 | no | M2 knocks behind the door (4 s): three soft muffled wooden knocks from inside the Cell, then a kettle ticking as it cools |
| `knocks_soft` | `sfx/knocks_soft.ogg` | 3.81 s | peak -14.0 dBFS | -51 | no | M2 knocks, Soft: the same, quieter and more muffled, kettle ticks fainter |
| `frost_steps` | `sfx/frost_steps.ogg` | 4.74 s | peak -5.9 dBFS | -83 | no | M3 shadow on the frost (4 s): a soft muffled whoosh as something passes behind the pane, two far footsteps, a faint squeak |
| `frost_steps_soft` | `sfx/frost_steps_soft.ogg` | 4.74 s | peak -14.0 dBFS | -76 | no | M3 shadow on the frost, Soft: only the soft whoosh, lower |
| `roll_call` | `sfx/roll_call.ogg` | 9.21 s | peak -6.0 dBFS | -41 | no | M4 roll call (9 s): an old PA horn sounds two spoken-rhythm tone phrases (a count: two notes, then three) with crackle, then stops; a long soft hiss and a click. No voice, tones only |
| `roll_call_soft` | `sfx/roll_call_soft.ogg` | 8.94 s | peak -13.9 dBFS | -49 | no | M4 roll call, Soft: the same count in a rounder horn, no crackle, a shorter fainter hiss, no click |
| `steps_above` | `sfx/steps_above.ogg` | 5.77 s | peak -5.9 dBFS | -57 | no | M5 steps above (5 s): four slow footfalls cross the ceiling, each with a plank creak and a little dust |
| `steps_above_soft` | `sfx/steps_above_soft.ogg` | 5.77 s | peak -13.9 dBFS | -70 | no | M5 steps above, Soft: lower, rounder footfalls, no dust |
| `echo_chime` | `sfx/echo_chime.ogg` | 5.57 s | peak -6.0 dBFS | -44 | no | M6 echo at the rail end (5 s): three soft swelled glass notes (E, B, F sharp) answering in a long dark hall |
| `echo_chime_soft` | `sfx/echo_chime_soft.ogg` | 4.88 s | peak -14.0 dBFS | -45 | no | M6 echo at the rail end, Soft: two notes, rounder |
| `hand_pickup_cloth` | `sfx/hand_pickup_cloth.ogg` | 0.43 s | peak -6.0 dBFS | -80 | no | Hand: the wipe cloth is picked up, a soft cloth rustle and a light glove grip |
| `hand_equip_cloth` | `sfx/hand_equip_cloth.ogg` | 0.34 s | peak -6.2 dBFS | -37 | no | Hand: the cloth is shaken out and gripped, a short airy flick and a cloth pat |
| `hand_putaway_cloth` | `sfx/hand_putaway_cloth.ogg` | 0.60 s | peak -6.1 dBFS | -81 | no | Hand: the cloth is folded away, a longer soft rustle and a muffled pat of the pocket |
| `hand_pickup_mallet` | `sfx/hand_pickup_mallet.ogg` | 0.29 s | peak -5.9 dBFS | -63 | no | Hand: the mallet is lifted, a wooden handle on a leather palm, a soft knock of the head |
| `hand_equip_mallet` | `sfx/hand_equip_mallet.ogg` | 0.26 s | peak -6.1 dBFS | -60 | no | Hand: the mallet is set in the grip, a glove squeeze and a small hollow wooden tock |
| `hand_putaway_mallet` | `sfx/hand_putaway_mallet.ogg` | 0.30 s | peak -6.2 dBFS | -81 | no | Hand: the mallet goes away, a dull wood-on-leather thud and a short slide |
| `hand_pickup_uvlamp` | `sfx/hand_pickup_uvlamp.ogg` | 0.27 s | peak -6.1 dBFS | -17 | no | Hand: the UV lamp is picked up, a small clink of the casing against the glove and a rubber grip |
| `hand_equip_uvlamp` | `sfx/hand_equip_uvlamp.ogg` | 0.56 s | peak -6.2 dBFS | -88 | no | Hand: the UV lamp is switched on, a switch click and a faint rising electronic hum |
| `hand_putaway_uvlamp` | `sfx/hand_putaway_uvlamp.ogg` | 0.52 s | peak -6.0 dBFS | -54 | no | Hand: the UV lamp is switched off and put away, a falling hum, a click and a soft case thud |
| `hand_pickup_keys` | `sfx/hand_pickup_keys.ogg` | 0.37 s | peak -5.8 dBFS | -10 | no | Hand: the key ring is lifted, a bright short jingle of several keys |
| `hand_equip_keys` | `sfx/hand_equip_keys.ogg` | 0.26 s | peak -5.9 dBFS | -10 | no | Hand: a key is taken from the ring and held, a short two-key clink and a clasp tick |
| `hand_putaway_keys` | `sfx/hand_putaway_keys.ogg` | 0.44 s | peak -5.8 dBFS | -38 | no | Hand: the keys slide into a pocket, a muffled jingle and a cloth pat |
| `hand_leather_creak` | `sfx/hand_leather_creak.ogg` | 0.28 s | peak -6.1 dBFS | -65 | no | Hand: a generic glove-on-leather creak to layer under any other held item (e.g. lift a book or a lens) |

## Left undone / known limits

- Not auditioned by a human (see above). Likely tuning after a listen: the balance inside the Pump and Cell beds, the brightness of the metal ticks on a phone speaker.
- Stereo images are placement only; one-shots are mono (the project convention), reverb is baked in.
- The mallet tones are fixed (131 Hz full, 622 Hz dead, buzzing cracked); the scene may vary `pitch_scale` slightly per pipe segment.
- `roll_call` is tones only, by request (no spoken numbers). It counts two phrases (a two-note and a three-note one) and stops; the visual caption carries the "forty / forty-one".
