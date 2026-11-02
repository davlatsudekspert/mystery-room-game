# Audio tools: MYSTERY ROOM, The Forgotten Institute

Every sound, ambience and music cue in `game/assets/audio/` is made by code in this folder.
The one exception is a single CC0 page-flip recording, which is layered into `page_turn`.
No paid services or AI audio tools are used. Re-running the generator gives the same files byte for byte.

```bash
pip install -r tools/audio/requirements.txt     # numpy, scipy, Pillow
python3 tools/audio/synth_all.py                 # regenerate all 95 files
python3 tools/audio/synth_all.py --only ui_tap,reveal --qa-dir /tmp/audio_qa   # a subset plus spectrogram PNGs
python3 tools/audio/synth_all.py --module archive,music_archive --readme      # one chapter's modules, merged into the table
python3 tools/audio/synth_all.py --module underground,music_underground --readme --jobs 2   # Chapter 3 (6 files)
python3 tools/audio/synth_all.py --list          # list registered sounds
```

The Chapter 1 set (40 files) took about 70 s on 4 cores. The Chapter 2 modules (42 files) took about 2 min with `--jobs 2`; `music_archive` alone is about 2 min of that.
The Chapter 3 modules (6 files) took about 1.6 min with `--jobs 2`; `music_underground` alone is about 1 min.

You also need `ffmpeg` with libvorbis (for encoding and loudness measurement) and `sox` (for verification decoding).
A full run (no `--only`/`--module`) also rewrites the asset table below. A partial run leaves it alone unless `--readme` is given, which replaces or adds only the rendered files' rows.

## Output format

| Kind | Folder | Format | Level target |
|---|---|---|---|
| UI feedback (`ui_*`, `hint`) | `sfx/` | OGG Vorbis q5, 44.1 kHz, mono | peak -6 dBFS |
| Item feedback (`item_*`) | `sfx/` | OGG Vorbis q5, 44.1 kHz, mono | peak -3 dBFS |
| Other one-shot SFX | `sfx/` | OGG Vorbis q5, 44.1 kHz, mono | peak -1 dBFS |
| Ambience loops | `ambience/` | OGG Vorbis q5, 44.1 kHz, stereo | -24 LUFS integrated, true peak <= -1 dBTP |
| Music (loops and stinger) | `music/` | OGG Vorbis q5, 44.1 kHz, stereo | -20 LUFS integrated, true peak <= -1 dBTP |

Peaks and loudness are measured on the **encoded** files: loudness with ffmpeg `loudnorm` (EBU R128), peaks after decoding.
No limiter or compressor is used anywhere. When a true peak would exceed the ceiling, the generator only lowers the gain.

## Pipeline (`synth_all.py`)

1. **Render.** Each sound function gets its own `numpy.random.Generator`, seeded from a fixed base seed plus the CRC32 of its name. The output is therefore deterministic, and changing one sound never changes another.
2. **Clean up.**
   - One-shots get a DC/subsonic high-pass at 15 Hz, a trailing-silence trim at -70 dB, a 1.5 ms raised-cosine fade-in and a 30 ms fade-out.
   - Loops get a zero-phase FFT high-pass instead, which keeps them periodic. They get no fades.
3. **Level.**
   - One-shots are peak-normalised.
   - Music and ambience are measured with `loudnorm` and gain-adjusted to their LUFS target.
4. **Encode.** `ffmpeg -c:a libvorbis -q:a 5` with `-fflags +bitexact -flags:a +bitexact`, which fixes the Ogg serial and drops the encoder tag, so the output is byte-reproducible.
5. **Verify.** The OGG is decoded with SoX (libvorbisfile honours granule positions, so the sample count is exact; ffmpeg's native decoder is not).
   - The decoded peak is checked. Vorbis moves peaks by a fraction of a dB, so up to six gain trims are tried and the best one is kept, never more than 0.3 dB over target.
   - The loudness and true peak are re-measured.
   - Loops get a seam check (below).
   - With `--qa-dir`, a waveform and log-frequency spectrogram PNG is written, plus `report.json`, which includes the loudest-100-ms RMS of every file as a mixing aid.

### Seamless loops

Loops are built **circularly**, so the wrap point is not special:

- Noise is synthesised in the frequency domain, so its period is exactly the loop length.
- Control curves (rain intensity, gusts) come from periodic spectra.
- Grains, notes and events are mixed with wrap-around (`add_circular`).
- Every continuous oscillator uses `periodic_freq()`, which gives a whole number of cycles per loop. LFO rates are multiples of 1/L.
- IIR filters run in steady state (two passes, keep the second).
- Reverb tails that ring past the end are overlap-added back onto the start (`wrap_tail`, which is circular convolution).
- `amb_lab_dark` and `amb_archive` are then rotated so the file starts at its calmest moment (`rotate_to_calm_point`). The Vorbis encoder codes the first and last frames independently, so a calm seam is safest.
- `loops.crossfade_loop()` (render extra tail and equal-power crossfade it over the start) is available for material that cannot be built circularly. The current loops do not need it.
- Steady, low-frequency beds (the Chapter 3 hums) have tiny normal sample steps, so the codec's own error at the file edges can reach the size of one (their first encodes measured 0.85-1.2 against a limit of 1). `synth_all.render()` therefore re-seats a loop whose encoded seam ratio is 0.8 or more: the loop is circular, so it tries up to 16 other, deterministic start points (golden-ratio fractions of the loop) and keeps the cleanest encoded seam, never one that breaks the true-peak ceiling. `amb_choir`, `amb_lift` and `amb_nursery` are re-seated this way; every Chapter 1 and 2 loop measures below 0.45 and is untouched (re-rendered files are byte-identical to the committed ones).

The seam check on each encoded loop compares two things:
- The last→first sample jump against the file's own 99.9th-percentile sample step. A ratio below 1 is indistinguishable from normal motion.
- The RMS change across the seam against 400 points inside the file.

The run fails (exit code 1) if a loop fails either check.

## Module map

| Module | Contents |
|---|---|
| `synth/core.py` | constants, seeded RNG, mixing (`add_at`, `add_circular`), pan, fades, DC removal, normalisation |
| `synth/osc.py` | sine, polyBLEP saw and pulse, triangle, additive, FM, vibrato |
| `synth/env.py` | ADSR, T60 decays, attack/decay, breakpoint curves (linear, cosine, exponential), swells |
| `synth/filters.py` | RBJ-cookbook biquads, Butterworth, time-varying biquad, circular IIR, zero-phase FFT filters |
| `synth/noise.py` | white, FFT-shaped coloured noise (pink, brown, any slope), Poisson events, dust/crackle, smooth random curves |
| `synth/reverb.py` | synthesised IRs: band-split decorrelated noise with per-band RT60 plus early reflections; presets `lab`, `corridor`, `plate`, `ui_plate`, `hall`, `hall_dark`, `room_amb`; FFT convolution |
| `synth/modal.py` | modal synthesis: mode recipes (bar, tine, bell, glass, wood, metal, random inharmonic), struck rendering with contact pulses, resonator banks for friction and creaks |
| `synth/granular.py` | Poisson grain clouds and explicit event scattering, with wrap-around |
| `synth/music.py` | pitch helpers, music box, celesta, bell, glass, evolving pad voice, drone, bowed metal, loop-aware `Track` |
| `synth/loops.py` | `wrap_tail`, `crossfade_loop`, `rotate_to_calm_point`, `periodic_freq`, `seam_report` |
| `synth/export.py`, `synth/qa.py`, `synth/samples.py` | WAV/OGG and loudness I/O, spectrogram PNGs, CC0 source loading |
| `sounds/kit.py` | shared sound-design blocks: tick, knock, clank, thump, friction, stick-slip creak, hum, relay, buzz, spark, whoosh, drop |
| `sounds/ui.py`, `mechanisms.py`, `electrical.py`, `story.py`, `ambience.py`, `music_tracks.py` | the sound definitions (`@sound(...)` registry) |
| `sounds/archive.py` | Chapter 2, Records Archive B: shutter, compressor and pneumatic post, catalogue and card punch, lockers and hiding places, receiver, tape deck (with the speech-like murmur engine), rotary dial, film and slide projectors, crystals, vault, `amb_archive`, and the Chapter 2 room IRs (`archive`, `vault`, `booth`, `amb`) |
| `sounds/music_archive.py` | `music_archive` and `music_archive_finale` (reuses the pad, bass, celesta and master helpers of `music_tracks.py`) |
| `sounds/underground.py` | Chapter 3, Underground Facility: `amb_choir`, `amb_gallery`, `amb_nursery`, `amb_lift` (hum builder on loop-periodic partials, narrow resonating bands, sympathetic glass tones, the four room IRs, `_settle`) |
| `sounds/array_hall.py`, `sounds/music_array_hall.py` | Chapter 4, Array Hall: `amb_array_hall`, `amb_array_core`, `amb_array_rooms` (reuse the Chapter 3 hum / band / settle builders; hum on A, the Core's note) and `music_array_hall`, `music_array_hall_reversal` (A Dorian, bell pairs a few cents apart, 48 BPM pulse) |
| `sounds/music_underground.py` | `music_underground` and `music_underground_finale` (reuses the e-piano, wow and pad helpers of `music_archive.py`; adds the crystal tube bell, the low pulse, the overtone choir and the bowed glass) |

`sounds/__init__.py` imports the Chapter 1 modules (`MODULES`). `synth_all.py` adds the Chapter 2 and 3 modules through its `EXTRA_MODULES` list.

## Godot notes

- **Looping:** Godot imports OGG with `loop = false`. For `amb_lab_dark`, `amb_power_hum`, `music_menu` and `music_lab`, do one of these:
  - Tick *Loop* in the Import dock and re-import.
  - Set `(stream as AudioStreamOggVorbis).loop = true` in `AudioManager`.

  `loop_offset` stays 0.
- **Chapter 2 loops:**
  - `AudioManager.music()` and `AudioManager.ambience()` set `loop = true` at runtime, so `music_archive`, `music_archive_finale` and `amb_archive` need nothing.
  - `music_archive_finale` is a seamless 64 s loop, not a one-off cue, because `AudioManager.music()` loops every music stream. It builds up to its peak (F6 over Fmaj7/A at 32–40 s) and thins out on C7sus4, which falls back into the opening Fmaj9.
  - `receiver_static` is played by a plain `AudioStreamPlayer` in `archive_visuals.gd`. Its `.ogg.import` therefore ships with `loop=true`; the optional loops `compressor_loop`, `slide_fan_loop` and `tape_hiss` do too.
  - `film_projector_loop` is a 22 s one-shot bed (fade-in 1.2 s, fade-out 2.5 s), not a loop, because the room plays it once through `AudioManager.sfx()`.
- **Chapter 3 (Underground Facility) audio:**
  - `underground_room.gd` asks for `amb_choir`, `amb_gallery`, `amb_nursery` and `amb_lift` (one per zone, `ZONE_TONE`) and for `music_underground` / `music_underground_finale`; each falls back to a Chapter 1-2 track only if the file is missing. `AudioManager` sets `loop = true` at runtime, so the `.import` files keep the default `loop=false`.
  - The four ambiences are 60 s loops at -24 LUFS, like `amb_archive`, but **none has a noise bed**. Each is a tonal bed (a hum built only from E and its fifth, so it agrees with the score; in the gallery, narrow bands a few Hz wide at E and B pitches) plus sparse details. The only noise is band-limited (the gallery's bands, the rumbles below 260 Hz) or confined to short events (the nursery's four steam puffs of about 3 s at 1.1-5.2 kHz, cooling ticks, creak friction). By comparison `amb_archive` holds a steady bed from 50 Hz to 5 kHz.
  - Above 1 kHz the choir, gallery and lift hold only the upper partials of their rare glass tones, drips, contactors and creaks. The nursery adds its lamp buzz (up to about 1.7 kHz), the steam puffs and the ticks. On phone speakers the 100-660 Hz hum partials carry the beds; the 41-82 Hz fundamentals do not.
  - `music_underground` is a 160 s loop (8 sections x 20 s at 48 BPM), `music_underground_finale` an 80 s loop (8 x 10 s). Neither has a hiss layer; the tape character is wow and flutter only. `music_underground` has no pulse and no arpeggio in its first and last 20 s, so the loop point falls in its calmest part. The finale's pulse is shifted off the loop point for the same reason.
  - The low pulse (every 2.5 s, in the 2nd to the 7th of the 8 sections of `music_underground`) keeps 2nd and 3rd harmonics at 165-250 Hz so a phone speaker still carries it. It is mixed dry (not through the hall) so every hit stays distinct.
- **Music start:** the loops are circular, so position 0 is mid-texture (the last chord's pad is still releasing). Fade music in over about 2 s, or let the `AudioManager` crossfade handle it.
- **Suggested playback levels:**
  - `amb_power_hum` is mastered to -24 LUFS like the rain bed. Its 100 Hz body is strong on headphones, so start it about 8–10 dB under `amb_lab_dark`, or duck the rain slightly when power comes back.
  - `breaker_on` and `power_on` already fade their own hum tails, so start the hum loop under them.
- **Chapter 2 levels and timing:**
  - `tape_voice` measures -16.0 LUFS integrated, close to `puzzle_solved` (-16.3), so with the room's -3 dB it sits just above the -20 LUFS music. `tape_garble` measures -15.1 LUFS.
  - In `amb_archive` the clock ticks peak about 20 dB above the 1–5 kHz bed. They should be audible but not prominent at the room's -4 dB.
  - `shutter_slam` hits about 35 ms in, after a few slat ticks (the room calls it when the shutter lands). Its tail carries six faint emergency relays at 0.3–0.9 s.
  - In `vault_bolts` the eight bolt clunks are 0.12 s apart from t ≈ 0.09 s, in step with `bolts_cascade()`. The final lock clunk is at 1.06 s.
  - `film_projector_start` fades out over its last 0.9 s while `film_projector_loop`, which starts at the same moment, fades in.
  - `dial_return` has six governor pulses 0.1 s apart and stops at 0.6 s.
  - `tape_clicks` is a single click (0.48 s with its tail). The room repeats it every 0.42 s.
- **Sequencing:** `projector_charge` ends at full charge (2.25 s) so that `projector_fire` or `projector_fail` can follow with no gap. The rest of the Lumen Projector sequence is `ring_turn` → `projector_charge` → `projector_fire` → `maglock_release` → `door_open` → `stinger_chapter_complete`.

## CC0 source material

| File | Used in | Origin |
|---|---|---|
| `sources/kenney/rpg-audio/bookFlip2.ogg` (byte-identical to the pack) | `page_turn` (layered with a synthesised crinkle and air flap) | Kenney "RPG Audio", https://kenney.nl/assets/rpg-audio, CC0 1.0. The pack's `License.txt` is kept beside it. |

The register is in `docs/ASSET_LICENSES.md`.
Other Kenney files were auditioned by spectrogram and rejected: `doorClose_4`, `doorOpen_2` and `metalLatch` decode above 0 dBFS (clipped masters).

## Asset table

<!-- ASSET-TABLE:START -->
| File | Duration | Loop | Level | Size | Source | Description |
|---|---|:-:|---|---|---|---|
| `sfx/hint.ogg` | 1.41 s | no | peak -6.0 dBFS | 8 KB | synth | Soft glassy ping with a shimmering tail (hint available/shown) |
| `sfx/ui_close.ogg` | 0.66 s | no | peak -6.0 dBFS | 8 KB | synth | Falling two-note celesta with a soft swish (panel closes) |
| `sfx/ui_error.ogg` | 0.65 s | no | peak -6.0 dBFS | 6 KB | synth | Two muted, falling wood-block notes (gentle 'not quite') |
| `sfx/ui_open.ogg` | 0.71 s | no | peak -6.0 dBFS | 9 KB | synth | Rising two-note celesta with a soft swish (panel/inventory opens) |
| `sfx/ui_tap.ogg` | 0.09 s | no | peak -6.1 dBFS | 4 KB | synth | Soft wooden tick for buttons and taps |
| `sfx/ui_toast.ogg` | 0.69 s | no | peak -6.2 dBFS | 6 KB | synth | Warm marimba fourth for notifications/toasts |
| `sfx/booth_unlatch.ogg` | 1.93 s | no | peak -1.0 dBFS | 19 KB | synth | Booth door lock releases: solenoid clunk, bolt slides back, the door creaks ajar and bumps its stop |
| `sfx/box_open.ogg` | 0.83 s | no | peak -1.0 dBFS | 10 KB | synth | Small lid springs open: latch click, coil-spring twang, lid knock |
| `sfx/breaker_on.ogg` | 2.53 s | no | peak -1.1 dBFS | 11 KB | synth | Main breaker lever thrown: big clunk, then transformer hum swells in |
| `sfx/breaker_trip.ogg` | 0.90 s | no | peak -0.8 dBFS | 13 KB | synth | Breaker trips: spark crackle, hum dies, lever snaps back with a clunk |
| `sfx/c2x_aisle_found.ogg` | 3.14 s | no | peak -1.2 dBFS | 13 KB | synth | The right aisle opens: the shelves part and a long breath of still, cold air with a faint low chime |
| `sfx/c2x_board_ok.ogg` | 2.15 s | no | peak -1.0 dBFS | 22 KB | synth | The tags hang in the right order: a soft rattle of all six, a wood clack and a tiny key dropping into the tray |
| `sfx/c2x_board_wrong.ogg` | 0.79 s | no | peak -1.0 dBFS | 9 KB | synth | The tags do not agree with the slips: a dull wooden rattle, nothing happens |
| `sfx/c2x_cab_open.ogg` | 1.92 s | no | peak -1.1 dBFS | 17 KB | synth | Strand's cabinet opens: the last wheel seats, a latch drops, a wooden drawer slides out and a lamp glass rolls and clinks |
| `sfx/c2x_cab_wheel.ogg` | 0.34 s | no | peak -1.2 dBFS | 7 KB | synth | Cabinet digit wheel advances one number: a crisp brass tick with a tiny barrel click |
| `sfx/c2x_carriage_clunk.ogg` | 1.51 s | no | peak -0.9 dBFS | 14 KB | synth | The carriage will not move (no gap beside it): a dull steel clunk and a short rattle of the rails |
| `sfx/c2x_carriage_roll.ogg` | 3.95 s | no | peak -1.1 dBFS | 16 KB | synth | A heavy shelf carriage rolls one slot along its rails: a low rumble with rail-joint beats, a stop |
| `sfx/c2x_chest_sealed.ogg` | 0.54 s | no | peak -1.0 dBFS | 8 KB | synth | The chest is still sealed: the lid is tried, a short rattle against the lock |
| `sfx/c2x_chest_unlock.ogg` | 3.08 s | no | peak -1.0 dBFS | 29 KB | synth | The rings line up: three tumbler clicks, a deep latch release, the lid creaks open with a faint glass rustle |
| `sfx/c2x_cold_frozen.ogg` | 0.75 s | no | peak -1.1 dBFS | 8 KB | synth | Frozen door: the wheel will not turn, an ice crunch and a dull thud against the seal |
| `sfx/c2x_counter_heavy.ogg` | 2.18 s | no | peak -0.9 dBFS | 16 KB | synth | The counterweight is too heavy: the cable groans taut and the weights knock the frame |
| `sfx/c2x_counter_light.ogg` | 1.53 s | no | peak -0.7 dBFS | 16 KB | synth | The counterweight is too light: a slack cable clink and a small hollow tap |
| `sfx/c2x_crank.ogg` | 2.50 s | no | peak -1.0 dBFS | 29 KB | synth | Compactus crank: a handle turned with a ratchet clicking faster, a gear grind (1.4 s) |
| `sfx/c2x_door_cold.ogg` | 3.00 s | no | peak -0.9 dBFS | 16 KB | synth | Cold Store door opens: the rubber seal peels (soft sigh), the latch lets go, cold air moves out |
| `sfx/c2x_door_iron.ogg` | 3.21 s | no | peak -1.0 dBFS | 26 KB | synth | Pump Room door found behind the panel: bolt clank, a long iron hinge groan, a heavy stop |
| `sfx/c2x_door_pass.ogg` | 2.38 s | no | peak -0.9 dBFS | 22 KB | synth | Pass door in the gallery: the pass key slides in, turns, the bolt draws back and the door unlatches |
| `sfx/c2x_door_service.ogg` | 2.21 s | no | peak -1.1 dBFS | 19 KB | synth | Service door (stairwell, lift hall): a light steel latch and a short hinge squeak, soft close |
| `sfx/c2x_enlarger_fan.ogg` | 4.00 s | yes | peak -1.2 dBFS | 14 KB | synth | Enlarger lamp-house fan (seamless 4 s loop for sfx_loop): a small fan with a 20 Hz blade beat over a soft 100 Hz hum |
| `sfx/c2x_enlarger_focus.ogg` | 0.83 s | no | peak -1.1 dBFS | 11 KB | synth | Enlarger focus ring: a smooth knurled ring turning, fine ticks, a soft end stop |
| `sfx/c2x_enlarger_knob.ogg` | 0.40 s | no | peak -1.1 dBFS | 7 KB | synth | Enlarger zoom or head knob turned a step: a small geared detent click and a brief ring |
| `sfx/c2x_enlarger_lamp.ogg` | 1.60 s | no | peak -0.9 dBFS | 10 KB | synth | Enlarger lamp: a switch click, a thump of the transformer and a warm lamp glow that holds a moment, then a click off |
| `sfx/c2x_frost_done.ogg` | 2.18 s | no | peak -1.0 dBFS | 24 KB | synth | The last band is clear: loose ice flakes fall and tinkle on the sill |
| `sfx/c2x_frost_wipe_1.ogg` | 0.84 s | no | peak -1.1 dBFS | 11 KB | synth | Frost window, wipe variant 1: a cloth drags across fine ice crystals (crisp, medium) |
| `sfx/c2x_frost_wipe_2.ogg` | 1.05 s | no | peak -1.1 dBFS | 13 KB | synth | Frost window, wipe variant 2: a longer, softer stroke with a glass squeak at the turn |
| `sfx/c2x_frost_wipe_3.ogg` | 0.65 s | no | peak -0.9 dBFS | 10 KB | synth | Frost window, wipe variant 3: a short quick wipe, grittier |
| `sfx/c2x_frost_wipe_4.ogg` | 1.18 s | no | peak -1.0 dBFS | 14 KB | synth | Frost window, wipe variant 4: a slow low-pitched stroke, damp and heavy, with a squeak |
| `sfx/c2x_lamp_fail.ogg` | 1.00 s | no | peak -1.0 dBFS | 10 KB | synth | The booth projector lamp is dead: a dull filament tink, a weak electrical sigh dropping in pitch |
| `sfx/c2x_lamp_fit.ogg` | 2.14 s | no | peak -0.8 dBFS | 14 KB | synth | The new projector lamp is fitted: a glass bulb turned into the socket, a clink, the filament warming up in pitch and a soft tick |
| `sfx/c2x_lift_balanced.ogg` | 2.38 s | no | peak -1.1 dBFS | 18 KB | synth | Load and counterweight are equal: the weights swing level, the cable settles with a low relief creak |
| `sfx/c2x_lift_bell.ogg` | 2.07 s | no | peak -1.0 dBFS | 14 KB | synth | Lift bell: a small brass arrival bell, one clear ding with a short ring |
| `sfx/c2x_lift_move.ogg` | 4.91 s | no | peak -1.1 dBFS | 31 KB | synth | The book lift travels one floor: a motor hum rising, cable and weight clanks passing, a settling clunk (3.6 s) |
| `sfx/c2x_lift_stuck.ogg` | 2.14 s | no | peak -0.9 dBFS | 15 KB | synth | The book lift is not balanced: the cage jolts against its stops with a short motor strain |
| `sfx/c2x_light_digits.ogg` | 3.08 s | no | peak -0.9 dBFS | 20 KB | synth | The two digits light up on the table: a soft, warm two-note glass chime over a gentle glow swell |
| `sfx/c2x_lightbox_on.ogg` | 1.86 s | no | peak -0.9 dBFS | 12 KB | synth | Light table: a tube starter flickers three times and the box settles to a warm glow with a faint 100 Hz hum |
| `sfx/c2x_mallet_cracked.ogg` | 1.19 s | no | peak -0.9 dBFS | 18 KB | synth | Mallet on a cracked pipe next to the hazard: a rattling buzz that decays unevenly |
| `sfx/c2x_mallet_dead.ogg` | 0.50 s | no | peak -1.1 dBFS | 7 KB | synth | Mallet on a dead pipe: a short, high, empty tink (about 620 Hz) |
| `sfx/c2x_mallet_full.ogg` | 1.25 s | no | peak -0.9 dBFS | 8 KB | synth | Mallet on a pipe that carries pressure: a full, low, long tone (about 130 Hz) |
| `sfx/c2x_panel_cold.ogg` | 0.71 s | no | peak -1.0 dBFS | 7 KB | synth | Warm Wall: a cold panel is rapped, a dull flat knock with no answer |
| `sfx/c2x_panel_open.ogg` | 1.48 s | no | peak -1.0 dBFS | 14 KB | synth | Warm Wall: a painted panel on the east wall swings open (latch tick, dry hinge, soft thud) |
| `sfx/c2x_pipe_flow.ogg` | 2.17 s | no | peak -1.0 dBFS | 11 KB | synth | Pressure reaches the coil: a low thrum, rushing water in the pipe, gurgles, tapering off (1.9 s) |
| `sfx/c2x_pipe_hazard.ogg` | 2.23 s | no | peak -0.8 dBFS | 19 KB | synth | Wrong route: the vent to the hall hisses, the pipe rattles and a warning ping rings (calm, nothing is lost) |
| `sfx/c2x_plan_unfold.ogg` | 0.98 s | no | peak -1.0 dBFS | 13 KB | synth | The floor plan is unfolded: crisp paper creases and a soft rustle |
| `sfx/c2x_print_ready.ogg` | 2.03 s | no | peak -1.2 dBFS | 14 KB | synth | The print develops in the tray: paper slips into the liquid, a gentle slosh, a few drops (1.8 s) |
| `sfx/c2x_refused.ogg` | 0.72 s | no | peak -1.0 dBFS | 7 KB | synth | A closed room or lift floor is tried: two dull wooden taps, calm, no alarm |
| `sfx/c2x_ring_click.ogg` | 0.38 s | no | peak -1.1 dBFS | 7 KB | synth | Chest ring turned one symbol: a firm brass detent click with a small ring (the next ring follows) |
| `sfx/c2x_sheet_flip.ogg` | 0.70 s | no | peak -1.1 dBFS | 9 KB | synth | A sheet is flipped over by its tab: a soft flap of acetate, then two taps on the glass |
| `sfx/c2x_sheet_slide.ogg` | 0.79 s | no | peak -1.1 dBFS | 10 KB | synth | An acetate sheet slides across the glass of the light table: smooth plastic friction and a tiny flex |
| `sfx/c2x_sheet_turn.ogg` | 0.58 s | no | peak -1.1 dBFS | 9 KB | synth | A sheet is turned a quarter: a short slide and a soft plastic tick as it seats |
| `sfx/c2x_stair_climb.ogg` | 2.43 s | no | peak -0.9 dBFS | 20 KB | synth | A short climb on the iron stair (camera travel): five quick steps on steel treads, each with a faint ring |
| `sfx/c2x_stair_steps.ogg` | 4.08 s | no | peak -1.1 dBFS | 32 KB | synth | Climbing the iron spiral stair: six slow footsteps on steel treads, each with a soft ring |
| `sfx/c2x_step_soft_a.ogg` | 1.48 s | no | peak -1.0 dBFS | 9 KB | synth | One soft footstep on the old floor (camera travel, left foot): a dull low thud and a quiet scuff of the sole |
| `sfx/c2x_step_soft_b.ogg` | 1.47 s | no | peak -1.1 dBFS | 9 KB | synth | One soft footstep on the old floor (camera travel, right foot): slightly lighter and a little higher than the left |
| `sfx/c2x_strip_load.ogg` | 0.72 s | no | peak -0.8 dBFS | 10 KB | synth | A negative strip is slid into the carrier: a smooth film slide and a small click as the carrier closes |
| `sfx/c2x_tag_hook.ogg` | 0.59 s | no | peak -1.0 dBFS | 8 KB | synth | A staff tag is hung on a board hook: a brass hook tick and the tag swinging against wood |
| `sfx/c2x_tag_lift.ogg` | 0.36 s | no | peak -1.2 dBFS | 7 KB | synth | A staff tag is lifted off its hook: a light tick and a small slide |
| `sfx/c2x_thaw.ogg` | 3.39 s | no | peak -1.1 dBFS | 33 KB | synth | The Cold Store door thaws: ice ticks and cracks, running drips, a long settling creak |
| `sfx/c2x_valve_wheel.ogg` | 1.29 s | no | peak -1.6 dBFS | 14 KB | synth | Manifold valve wheel turned: a big iron wheel squeaks over a notch, a breath of pressure, a click |
| `sfx/c2x_wedge_pull.ogg` | 2.60 s | no | peak -1.1 dBFS | 26 KB | synth | The wedge pin is pulled from the blocked spiral stair: wood squeals out of a tight fit, a knock, a clatter down the steps |
| `sfx/c2x_weight_hang.ogg` | 1.56 s | no | peak -1.0 dBFS | 14 KB | synth | A cast-iron counterweight is hung on the hook: a metal clank and the hook swinging |
| `sfx/c2x_weight_off.ogg` | 1.33 s | no | peak -1.2 dBFS | 14 KB | synth | A counterweight is lifted off the hook: a quick scrape and a light clink |
| `sfx/canister_thump.ogg` | 0.91 s | no | peak -1.1 dBFS | 10 KB | synth | Leather-banded brass canister drops into the receive tray: padded thump and rattle |
| `sfx/card_flick.ogg` | 0.54 s | no | peak -1.0 dBFS | 9 KB | synth | Thumb flicks through a few index cards (quick papery riffle) |
| `sfx/collar_click.ogg` | 0.53 s | no | peak -1.1 dBFS | 8 KB | synth | Brass collar or selector turned one detent: firm click with a small ring |
| `sfx/compressor_loop.ogg` | 4.00 s | yes | peak -1.0 dBFS | 49 KB | synth | Compressor running steadily: piston chug, motor hum, breathing air (seamless loop) |
| `sfx/compressor_start.ogg` | 3.90 s | no | peak -1.0 dBFS | 44 KB | synth | Archive compressor starts: contactor clack, belt squeal, motor and piston chug spin up, air wheezes |
| `sfx/crystal_record.ogg` | 2.90 s | no | peak -0.8 dBFS | 27 KB | synth | A crystal records the image: rising glassy shimmer that locks into a bright A chime and glows out |
| `sfx/deck_eject.ogg` | 0.77 s | no | peak -1.1 dBFS | 10 KB | synth | Tape reel lifted off / dropped onto the deck spindle: latch pop, hub clatter, slide |
| `sfx/deck_play.ogg` | 0.86 s | no | peak -1.1 dBFS | 9 KB | synth | Reel-to-reel Play key: heavy key clunk, pinch roller engages, motor spins up |
| `sfx/dial_return.ogg` | 0.85 s | no | peak -0.9 dBFS | 12 KB | synth | Rotary dial spins back: buzzing governor, pulse-contact ticks, soft stop |
| `sfx/dial_wind.ogg` | 0.56 s | no | peak -0.8 dBFS | 10 KB | synth | Rotary dial wound round by a finger: ratchety friction and the finger-stop clink |
| `sfx/door_open.ogg` | 2.84 s | no | peak -0.9 dBFS | 28 KB | synth | Heavy old wooden door unlatches and swings open on a long, groaning creak |
| `sfx/door_slam.ogg` | 1.79 s | no | peak -1.2 dBFS | 15 KB | synth | Heavy wooden door slams shut; latch catches; the room rings briefly |
| `sfx/drawer_card_slide.ogg` | 1.56 s | no | peak -1.1 dBFS | 16 KB | synth | Long oak catalogue drawer slides out on its runners, cards whisper inside, the stop catches |
| `sfx/drawer_locked.ogg` | 0.79 s | no | peak -1.0 dBFS | 10 KB | synth | Locked desk drawer tugged: wooden rattle against the bolt |
| `sfx/drawer_open.ogg` | 1.38 s | no | peak -1.0 dBFS | 15 KB | synth | Wooden drawer slides open on dry runners and stops with a soft knock |
| `sfx/echo_chime.ogg` | 5.57 s | no | peak -6.0 dBFS | 25 KB | synth | M6 echo at the rail end (5 s): three soft swelled glass notes (E, B, F sharp) answering in a long dark hall |
| `sfx/echo_chime_soft.ogg` | 4.88 s | no | peak -14.0 dBFS | 21 KB | synth | M6 echo at the rail end, Soft: two notes, rounder |
| `sfx/film_projector_loop.ogg` | 22.25 s | no | peak -1.1 dBFS | 284 KB | synth | Film projector running at 24 fps under the film: claw clatter, motor, fan and shutter flutter (~22 s bed) |
| `sfx/film_projector_start.ogg` | 2.50 s | no | peak -1.5 dBFS | 34 KB | synth | 16 mm projector run lever: clack, motor and fan spin up, the claw clatter speeds up to 24 frames a second |
| `sfx/film_projector_stop.ogg` | 2.00 s | no | peak -1.0 dBFS | 23 KB | synth | Projector switched off: lever clack, the clatter slows and stops, motor and fan wind down |
| `sfx/frost_steps.ogg` | 4.74 s | no | peak -5.9 dBFS | 20 KB | synth | M3 shadow on the frost (4 s): a soft muffled whoosh as something passes behind the pane, two far footsteps, a faint squeak |
| `sfx/frost_steps_soft.ogg` | 4.74 s | no | peak -14.1 dBFS | 18 KB | synth | M3 shadow on the frost, Soft: only the soft whoosh, lower |
| `sfx/gear_turn.ogg` | 0.68 s | no | peak -1.2 dBFS | 10 KB | synth | Strand's gear box knob: ratchet clicks and a gear settling into place |
| `sfx/grille_creak.ogg` | 1.65 s | no | peak -1.2 dBFS | 18 KB | synth | Vent grille swings open on a rusty hinge: frame unsticks, creak, light metal rattle |
| `sfx/hand_equip_cloth.ogg` | 0.34 s | no | peak -6.2 dBFS | 6 KB | synth | Hand: the cloth is shaken out and gripped, a short airy flick and a cloth pat |
| `sfx/hand_equip_keys.ogg` | 0.26 s | no | peak -5.9 dBFS | 6 KB | synth | Hand: a key is taken from the ring and held, a short two-key clink and a clasp tick |
| `sfx/hand_equip_mallet.ogg` | 0.26 s | no | peak -6.1 dBFS | 5 KB | synth | Hand: the mallet is set in the grip, a glove squeeze and a small hollow wooden tock |
| `sfx/hand_equip_uvlamp.ogg` | 0.56 s | no | peak -6.2 dBFS | 5 KB | synth | Hand: the UV lamp is switched on, a switch click and a faint rising electronic hum |
| `sfx/hand_leather_creak.ogg` | 0.28 s | no | peak -6.1 dBFS | 6 KB | synth | Hand: a generic glove-on-leather creak to layer under any other held item (e.g. lift a book or a lens) |
| `sfx/hand_pickup_cloth.ogg` | 0.43 s | no | peak -6.0 dBFS | 6 KB | synth | Hand: the wipe cloth is picked up, a soft cloth rustle and a light glove grip |
| `sfx/hand_pickup_keys.ogg` | 0.38 s | no | peak -5.8 dBFS | 7 KB | synth | Hand: the key ring is lifted, a bright short jingle of several keys |
| `sfx/hand_pickup_mallet.ogg` | 0.29 s | no | peak -5.9 dBFS | 6 KB | synth | Hand: the mallet is lifted, a wooden handle on a leather palm, a soft knock of the head |
| `sfx/hand_pickup_uvlamp.ogg` | 0.27 s | no | peak -6.1 dBFS | 6 KB | synth | Hand: the UV lamp is picked up, a small clink of the casing against the glove and a rubber grip |
| `sfx/hand_putaway_cloth.ogg` | 0.60 s | no | peak -6.1 dBFS | 6 KB | synth | Hand: the cloth is folded away, a longer soft rustle and a muffled pat of the pocket |
| `sfx/hand_putaway_keys.ogg` | 0.44 s | no | peak -5.8 dBFS | 6 KB | synth | Hand: the keys slide into a pocket, a muffled jingle and a cloth pat |
| `sfx/hand_putaway_mallet.ogg` | 0.30 s | no | peak -6.2 dBFS | 5 KB | synth | Hand: the mallet goes away, a dull wood-on-leather thud and a short slide |
| `sfx/hand_putaway_uvlamp.ogg` | 0.52 s | no | peak -6.0 dBFS | 5 KB | synth | Hand: the UV lamp is switched off and put away, a falling hum, a click and a soft case thud |
| `sfx/hatch_open.ogg` | 2.33 s | no | peak -0.8 dBFS | 20 KB | synth | Floor hatch: iron ring clinks, the heavy lid lifts with a creak and a breath of air, falls back with a thud |
| `sfx/intro_key.ogg` | 3.07 s | no | peak -0.9 dBFS | 29 KB | synth | Chapter 1 opening: a heavy brass key slides into a heavy old lock, grinds round and the bolt drops |
| `sfx/intro_thunder.ogg` | 4.75 s | no | peak -0.9 dBFS | 26 KB | synth | Chapter 1 opening: a long, distant roll of thunder behind the rain |
| `sfx/item_combine.ogg` | 1.15 s | no | peak -3.2 dBFS | 11 KB | synth | Two parts click together, then a bright celesta sparkle (items combined) |
| `sfx/item_pickup.ogg` | 0.83 s | no | peak -3.0 dBFS | 10 KB | synth | Quick leather/cloth rustle and a little music-box arpeggio (item taken) |
| `sfx/key_lift.ogg` | 1.22 s | no | peak -0.8 dBFS | 13 KB | synth | A heavy key lifted out of its cradle: catch releases, metal slides free, a faint ring |
| `sfx/key_turn.ogg` | 1.16 s | no | peak -1.1 dBFS | 14 KB | synth | Brass key slides into the lock past the pins and turns with a clack |
| `sfx/keypad_press.ogg` | 0.34 s | no | peak -0.9 dBFS | 7 KB | synth | Electromechanical safe key: bakelite plunger click and contact |
| `sfx/knocks.ogg` | 3.81 s | no | peak -6.0 dBFS | 15 KB | synth | M2 knocks behind the door (4 s): three soft muffled wooden knocks from inside the Cell, then a kettle ticking as it cools |
| `sfx/knocks_soft.ogg` | 3.81 s | no | peak -14.0 dBFS | 14 KB | synth | M2 knocks, Soft: the same, quieter and more muffled, kettle ticks fainter |
| `sfx/lamp_dip.ogg` | 3.98 s | no | peak -5.9 dBFS | 12 KB | synth | M1 lamp that dies (3.5 s): the work lamp's transformer hum sinks in pitch and level to an ember, then flares back with a small bulb tick |
| `sfx/lamp_dip_soft.ogg` | 3.99 s | no | peak -14.0 dBFS | 12 KB | synth | M1 lamp that dies, Soft: the same hum dip, shallower and rounder, no tick |
| `sfx/ledger_thump.ogg` | 1.24 s | no | peak -1.0 dBFS | 14 KB | synth | Heavy hollow ledger pulled out and opened: book thump, cover flap, hollow box with something inside |
| `sfx/lens_insert.ogg` | 0.58 s | no | peak -0.9 dBFS | 8 KB | synth | Crystal lens seats into its brass mount: soft scrape, click, glass ring |
| `sfx/locker_open.ogg` | 1.52 s | no | peak -1.0 dBFS | 17 KB | synth | Locker 9 unlocked: key clack, latch lifts, the thin steel door swings open and taps the next one |
| `sfx/locker_rattle.ogg` | 0.94 s | no | peak -0.9 dBFS | 11 KB | synth | Locked steel locker door tugged: thin metal clatter against the latch |
| `sfx/maglock_release.ogg` | 1.61 s | no | peak -1.0 dBFS | 13 KB | synth | Door maglock lets go: coil hum cuts out, armature clunk, door rattles |
| `sfx/menu_click.ogg` | 0.42 s | no | peak -0.8 dBFS | 7 KB | synth | Menu gear box: a knob pushed in and its brass wheel dropping one notch (soft click) |
| `sfx/menu_knock.ogg` | 0.70 s | no | peak -1.0 dBFS | 6 KB | synth | Menu gear box: a muffled knock from inside as the lid settles, as if something wants out |
| `sfx/menu_latch.ogg` | 0.47 s | no | peak -1.1 dBFS | 7 KB | synth | Menu gear box: the latch releases (clack, small spring, low clunk) |
| `sfx/menu_lid_close.ogg` | 0.93 s | no | peak -1.1 dBFS | 10 KB | synth | Menu gear box: the lid comes down and settles with a soft wooden thud and a small latch click |
| `sfx/menu_lid_open.ogg` | 2.11 s | no | peak -1.0 dBFS | 15 KB | synth | Menu gear box: the lid swings up on its hinge and stops with a soft knock, a warm light swells |
| `sfx/page_turn.ogg` | 0.69 s | no | peak -0.7 dBFS | 11 KB | synth + Kenney CC0 `bookFlip2.ogg` (RPG Audio) | A page of Leyla's notebook is turned (paper crinkle and air flap) |
| `sfx/power_on.ogg` | 2.77 s | no | peak -1.1 dBFS | 20 KB | synth | Power restored: relays click in sequence, lights and the Array hum up |
| `sfx/projector_charge.ogg` | 2.25 s | no | peak -1.1 dBFS | 16 KB | synth | Lumen Projector charging: rising electrical whine over a growing hum |
| `sfx/projector_fail.ogg` | 1.27 s | no | peak -1.4 dBFS | 15 KB | synth | Projector mistuned: the charge sputters, fizzles and dies with a pop |
| `sfx/projector_fire.ogg` | 3.12 s | no | peak -0.8 dBFS | 32 KB | synth | Projector fires through the crystal: bright resonant burst, long shimmering tail |
| `sfx/punch_key.ogg` | 0.61 s | no | peak -1.0 dBFS | 8 KB | synth | Card-punch key pressed down: hard key clack with a little spring |
| `sfx/punch_lever.ogg` | 1.15 s | no | peak -1.0 dBFS | 13 KB | synth | Card-punch lever pulled: ratchet, the dies chunk through the card, the lever springs back |
| `sfx/puzzle_solved.ogg` | 2.47 s | no | peak -0.9 dBFS | 20 KB | synth | Resonant bell-like D major add9 chord, gently arpeggiated (puzzle solved) |
| `sfx/receiver_beep.ogg` | 0.56 s | no | peak -0.9 dBFS | 6 KB | synth | Leyla's pocket receiver: short transistor beep from a tiny speaker |
| `sfx/receiver_static.ogg` | 6.00 s | yes | peak -1.2 dBFS | 38 KB | synth | Pocket receiver static: soft hiss with a drifting band, crackles and a faint heterodyne whistle (seamless loop) |
| `sfx/relay_click.ogg` | 0.66 s | no | peak -1.1 dBFS | 9 KB | synth | Old emergency relays pulling in: two quick clicks and a faint contactor buzz |
| `sfx/reveal.ogg` | 1.64 s | no | peak -1.0 dBFS | 20 KB | synth | Soft glassy shimmer as UV light reveals hidden ink |
| `sfx/ring_turn.ogg` | 0.46 s | no | peak -1.1 dBFS | 7 KB | synth | Projector's brass colour ring turns one stop (click with a slight ring) |
| `sfx/roll_call.ogg` | 9.21 s | no | peak -6.0 dBFS | 75 KB | synth | M4 roll call (9 s): an old PA horn sounds two spoken-rhythm tone phrases (a count: two notes, then three) with crackle, then stops; a long soft hiss and a click. No voice, tones only |
| `sfx/roll_call_soft.ogg` | 8.94 s | no | peak -13.9 dBFS | 41 KB | synth | M4 roll call, Soft: the same count in a rounder horn, no crackle, a shorter fainter hiss, no click |
| `sfx/rosette_press.ogg` | 0.50 s | no | peak -0.9 dBFS | 7 KB | synth | Carved wooden rosette pressed in: hollow wood click and a hidden latch |
| `sfx/safe_denied.ogg` | 0.95 s | no | peak -0.9 dBFS | 10 KB | synth | Wrong code: two low electric buzzes from the safe |
| `sfx/safe_open.ogg` | 2.32 s | no | peak -1.0 dBFS | 22 KB | synth | Heavy safe bolts retract with a clunk, then the steel door creaks open |
| `sfx/secret_panel.ogg` | 1.45 s | no | peak -1.0 dBFS | 16 KB | synth | Hidden walnut panel: latch release, smooth wooden slide, click into place |
| `sfx/shutter_slam.ogg` | 1.79 s | no | peak -0.8 dBFS | 20 KB | synth | Corrugated steel fire shutter crashes down; slats rattle; emergency relays click on aisle by aisle |
| `sfx/slide_clunk.ogg` | 0.40 s | no | peak -0.8 dBFS | 7 KB | synth | Glass slide pushed into (or out of) the slide projector gate: plastic-and-metal clunk with a spring |
| `sfx/slide_fan_loop.ogg` | 5.00 s | yes | peak -0.8 dBFS | 38 KB | synth | Slide projector running: cooling fan, blade hum and lamp transformer (seamless loop) |
| `sfx/splicer_click.ogg` | 0.26 s | no | peak -1.1 dBFS | 6 KB | synth | Film splicer: blade snaps down through the film and the clamp clicks |
| `sfx/steps_above.ogg` | 5.77 s | no | peak -5.9 dBFS | 42 KB | synth | M5 steps above (5 s): four slow footfalls cross the ceiling, each with a plank creak and a little dust |
| `sfx/steps_above_soft.ogg` | 5.77 s | no | peak -13.9 dBFS | 21 KB | synth | M5 steps above, Soft: lower, rounder footfalls, no dust |
| `sfx/switch_toggle.ogg` | 0.51 s | no | peak -1.1 dBFS | 7 KB | synth | Heavy bakelite toggle switch snapping over (clack) |
| `sfx/tape_clicks.ogg` | 0.48 s | no | peak -1.1 dBFS | 7 KB | synth | One click recorded at the end of a reel (a sharp tap with a little mic thump), through the deck speaker |
| `sfx/tape_garble.ogg` | 2.60 s | no | peak -0.8 dBFS | 25 KB | synth | Tape at the wrong speed: chipmunk-fast, warbling, slurring murmur with hiss |
| `sfx/tape_hiss.ogg` | 6.00 s | yes | peak -1.2 dBFS | 29 KB | synth | Tape deck running with no signal: hiss, capstan flutter and a faint hum (seamless loop) |
| `sfx/tape_voice.ogg` | 9.20 s | no | peak -1.1 dBFS | 76 KB | synth | Leyla's tape diary: a muffled, speech-like murmur (no real words) with hiss, wow and hum through the deck speaker |
| `sfx/tube_whoosh.ogg` | 1.97 s | no | peak -1.0 dBFS | 23 KB | synth | Pneumatic post: the canister is sucked into the glass tube and rushes away through the ceiling run |
| `sfx/uv_on.ogg` | 1.03 s | no | peak -0.8 dBFS | 13 KB | synth | UV lamp switched on: small click and a faint ballast buzz |
| `sfx/valve_squeak.ogg` | 0.81 s | no | peak -1.0 dBFS | 11 KB | synth | Brass valve wheel turned a notch: short metal squeak and a breath of air |
| `sfx/vault_bolts.ogg` | 3.01 s | no | peak -0.8 dBFS | 25 KB | synth | Vault light lock accepted: eight heavy bolts retract around the door in a rolling cascade |
| `sfx/vault_door_open.ogg` | 5.42 s | no | peak -1.1 dBFS | 44 KB | synth | The round vault door swings open: seal breaks with a sigh of air, massive hinge groans, deep rumble, it settles |
| `sfx/vault_wheel.ogg` | 2.47 s | no | peak -1.2 dBFS | 20 KB | synth | Spoked vault wheel heaved round: heavy gear grind, ratchet clunks, a final clunk |
| `sfx/wheel_tick.ogg` | 0.34 s | no | peak -1.1 dBFS | 7 KB | synth | Brass combination wheel moving one detent (crisp click) |
| `ambience/amb_archive.ogg` | 1:00.0 | yes | -24.1 LUFS | 747 KB | synth | Records Archive B: deep room tone, the Array humming far below, a slow clock, ticking pipes, distant canisters in the tubes |
| `ambience/amb_array_core.ogg` | 1:00.0 | yes | -24.0 LUFS | 288 KB | synth | The Core: its own note A held with octave and fifth, a narrow shimmer, slow glass answers (no noise bed) |
| `ambience/amb_array_hall.ogg` | 1:00.0 | yes | -24.0 LUFS | 313 KB | synth | Array Hall: a deep mains hum on A, faint breathing air over the rings, rare glass-tower answers, a far contactor and a ring settling (no noise bed) |
| `ambience/amb_array_rooms.ogg` | 1:00.0 | yes | -24.0 LUFS | 372 KB | synth | Booth and watch room: a lamp transformer's hum, the floor's A beneath it, a wall clock, a pencil, a pipe (no noise bed) |
| `ambience/amb_c2x_cell.ogg` | 48.00 s | yes | -24.0 LUFS | 463 KB | synth | Night Cell: a quiet warm room, kettle simmer (soft bubbles, 0.5-3 kHz), a small clock ticking twice a second, a faint low pipe hum |
| `ambience/amb_c2x_cold.ogg` | 48.00 s | yes | -24.0 LUFS | 286 KB | synth | Cold Store: refrigeration compressor hum (50 Hz series), a slow fan band, glassy ice creaks, a far carriage rumble |
| `ambience/amb_c2x_gallery.ogg` | 48.00 s | yes | -24.0 LUFS | 220 KB | synth | Reading Gallery: a big quiet space, very low air, distant ventilation with two narrow drifting tones, far wood creaks and a few dust ticks, long reverb |
| `ambience/amb_c2x_office.ogg` | 48.00 s | yes | -24.0 LUFS | 428 KB | synth | Director's Office: a deep mantel clock (tock every 0.6 s), wind gusting at the window glass, a green desk-lamp hum and a floorboard |
| `ambience/amb_c2x_plate.ogg` | 48.00 s | yes | -24.0 LUFS | 560 KB | synth | Plate Room (darkroom): a 100 Hz safelight buzz, water dripping into a tray, an enlarger timer ticking 2.5 times a second, a faint tap trickle |
| `ambience/amb_c2x_pump.ogg` | 48.00 s | yes | -24.1 LUFS | 299 KB | synth | Pump Room: boiler roar (40-380 Hz, flame flutter), 50 Hz mains hum, iron pipe expansion ticks, drips, a far pipe knock (no noise above 3.5 kHz) |
| `ambience/amb_choir.ogg` | 1:00.0 | yes | -24.0 LUFS | 298 KB | synth | Choir Hall: a low transformer hum on E, faint crystal-tube resonances singing in sympathy, two far contactors (no noise bed) |
| `ambience/amb_gallery.ogg` | 1:00.0 | yes | -24.0 LUFS | 366 KB | synth | Resonance Gallery: air singing across the glass floor in narrow bands, faint crystal answers from the memorial wall, a distant drip into the deep hall (no noise bed) |
| `ambience/amb_lab_dark.ogg` | 1:00.0 | yes | -24.2 LUFS | 867 KB | synth | Lab 7 in the dark: rain on the window, distant wind, low room tone, rare drips and creaks |
| `ambience/amb_lift.ogg` | 1:00.0 | yes | -24.0 LUFS | 234 KB | synth | Freight lift shaft: the hoist's power hum on E, slow shaft air with a faint low whistle, rare cable creaks (no noise bed) |
| `ambience/amb_nursery.ogg` | 1:00.0 | yes | -24.0 LUFS | 463 KB | synth | Nursery: a warm low hum, three growth-lamp buzzes beating slowly, soft steam puffs and cooling ticks from the autoclaves (no noise bed) |
| `ambience/amb_power_hum.ogg` | 20.00 s | yes | -24.0 LUFS | 314 KB | synth | Restored power: subtle 50 Hz transformer hum with harmonics and faint electrical hiss |
| `music/music_archive.ogg` | 2:30.0 | yes | -20.0 LUFS | 2453 KB | synth | Archive underscore: A minor analog pads, tine e-piano, vibraphone, soft pluck arpeggio with tape echo and wow |
| `music/music_archive_finale.ogg` | 1:04.0 | yes | -20.0 LUFS | 1083 KB | synth | Vault finale: tender celesta theme with e-piano over warm F major strings, a borrowed minor iv, glass light |
| `music/music_array_hall.ogg` | 2:40.0 | yes | -20.0 LUFS | 2176 KB | synth | Array Hall underscore: slow A Dorian pads, tube bells in pairs a few cents apart (the beat), a low pulse at 48 BPM, an overtone organ on A and tape wow |
| `music/music_array_hall_reversal.ogg` | 1:20.0 | yes | -20.0 LUFS | 1095 KB | synth | Array Hall reversal: the night's chords fall as the pulse doubles, descending bell runs and climbing bowed glass, a flash on Esus4, then the lights rising into a held A |
| `music/music_lab.ogg` | 2:40.0 | yes | -20.0 LUFS | 1957 KB | synth | Gameplay underscore: low, sparse D-pedal pads, rare soft celesta, distant metallic swells |
| `music/music_menu.ogg` | 2:30.0 | yes | -20.0 LUFS | 2180 KB | synth | Main menu theme: slow evolving D minor pads, sparse celesta melody with echoes, deep hall |
| `music/music_underground.ogg` | 2:40.0 | yes | -20.0 LUFS | 2142 KB | synth | Underground underscore: slow E Dorian pads, glass-tube bells with a shimmering twin, a low pulse at 48 BPM, an overtone choir and tape wow |
| `music/music_underground_finale.ogg` | 1:20.0 | yes | -20.0 LUFS | 1117 KB | synth | Underground finale: the Array answers; a tender bell theme with e-piano over warm E major strings, a held E, lights rising, a borrowed minor iv |
| `music/stinger_chapter_complete.ogg` | 8.47 s | no | -20.0 LUFS | 124 KB | synth | Chapter complete: Bbmaj7 lifts to a warm D major add9 bloom; a last high 9th and a faint b6 linger |
<!-- ASSET-TABLE:END -->

## Known limitations

- Everything, the Chapter 3 files included, was checked by measurement and spectrogram, not by ear. Timbre choices, especially the door creak and the music voicings, deserve a listening pass on a phone speaker and on headphones.
- Phone speakers roll off below about 200 Hz. The heaviest impacts (`door_slam`, `safe_open`, `breaker_*`, `projector_fire`) keep much of their weight in the 50–150 Hz range, so they will sound lighter on phones.
- `amb_lab_dark` is a 60 s loop. Its rare events (four drips, three creaks) repeat every minute, which an attentive player may notice in a long session. `amb_archive` behaves the same way: three distant canisters, five pipe-tick clusters, two paper rustles, two creaks and one relay repeat every minute.
- The tape murmur has the rhythm and intonation of speech, but its vowel targets are random. It was checked by spectrogram only, and it deserves a listen to confirm it never resembles real words.
