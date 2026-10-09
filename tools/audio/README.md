# Audio tools: MYSTERY ROOM, The Forgotten Institute

Every sound, ambience and music cue in `game/assets/audio/` is made by code in this folder.
The one exception is a single CC0 page-flip recording, which is layered into `page_turn`.
No paid services or AI audio tools are used. Re-running the generator gives the same files byte for byte.

```bash
pip install -r tools/audio/requirements.txt     # numpy, scipy, Pillow
python3 tools/audio/synth_all.py                 # regenerate all 82 files
python3 tools/audio/synth_all.py --only ui_tap,reveal --qa-dir /tmp/audio_qa   # a subset plus spectrogram PNGs
python3 tools/audio/synth_all.py --module archive,music_archive --readme      # one chapter's modules, merged into the table
python3 tools/audio/synth_all.py --list          # list registered sounds
```

The Chapter 1 set (40 files) took about 70 s on 4 cores. The Chapter 2 modules (42 files) took about 2 min with `--jobs 2`; `music_archive` alone is about 2 min of that.

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

`sounds/__init__.py` imports the Chapter 1 modules (`MODULES`). `synth_all.py` adds the Chapter 2 modules through its `EXTRA_MODULES` list.

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
| `sfx/film_projector_loop.ogg` | 22.25 s | no | peak -1.1 dBFS | 284 KB | synth | Film projector running at 24 fps under the film: claw clatter, motor, fan and shutter flutter (~22 s bed) |
| `sfx/film_projector_start.ogg` | 2.50 s | no | peak -1.5 dBFS | 34 KB | synth | 16 mm projector run lever: clack, motor and fan spin up, the claw clatter speeds up to 24 frames a second |
| `sfx/film_projector_stop.ogg` | 2.00 s | no | peak -1.0 dBFS | 23 KB | synth | Projector switched off: lever clack, the clatter slows and stops, motor and fan wind down |
| `sfx/gear_turn.ogg` | 0.68 s | no | peak -1.2 dBFS | 10 KB | synth | Strand's gear box knob: ratchet clicks and a gear settling into place |
| `sfx/grille_creak.ogg` | 1.65 s | no | peak -1.2 dBFS | 18 KB | synth | Vent grille swings open on a rusty hinge: frame unsticks, creak, light metal rattle |
| `sfx/hatch_open.ogg` | 2.33 s | no | peak -0.8 dBFS | 20 KB | synth | Floor hatch: iron ring clinks, the heavy lid lifts with a creak and a breath of air, falls back with a thud |
| `sfx/item_combine.ogg` | 1.15 s | no | peak -3.2 dBFS | 11 KB | synth | Two parts click together, then a bright celesta sparkle (items combined) |
| `sfx/item_pickup.ogg` | 0.83 s | no | peak -3.0 dBFS | 10 KB | synth | Quick leather/cloth rustle and a little music-box arpeggio (item taken) |
| `sfx/key_lift.ogg` | 1.22 s | no | peak -0.8 dBFS | 13 KB | synth | A heavy key lifted out of its cradle: catch releases, metal slides free, a faint ring |
| `sfx/key_turn.ogg` | 1.16 s | no | peak -1.1 dBFS | 14 KB | synth | Brass key slides into the lock past the pins and turns with a clack |
| `sfx/keypad_press.ogg` | 0.34 s | no | peak -0.9 dBFS | 7 KB | synth | Electromechanical safe key: bakelite plunger click and contact |
| `sfx/ledger_thump.ogg` | 1.24 s | no | peak -1.0 dBFS | 14 KB | synth | Heavy hollow ledger pulled out and opened: book thump, cover flap, hollow box with something inside |
| `sfx/lens_insert.ogg` | 0.58 s | no | peak -0.9 dBFS | 8 KB | synth | Crystal lens seats into its brass mount: soft scrape, click, glass ring |
| `sfx/locker_open.ogg` | 1.52 s | no | peak -1.0 dBFS | 17 KB | synth | Locker 9 unlocked: key clack, latch lifts, the thin steel door swings open and taps the next one |
| `sfx/locker_rattle.ogg` | 0.94 s | no | peak -0.9 dBFS | 11 KB | synth | Locked steel locker door tugged: thin metal clatter against the latch |
| `sfx/maglock_release.ogg` | 1.61 s | no | peak -1.0 dBFS | 13 KB | synth | Door maglock lets go: coil hum cuts out, armature clunk, door rattles |
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
| `sfx/rosette_press.ogg` | 0.50 s | no | peak -0.9 dBFS | 7 KB | synth | Carved wooden rosette pressed in: hollow wood click and a hidden latch |
| `sfx/safe_denied.ogg` | 0.95 s | no | peak -0.9 dBFS | 10 KB | synth | Wrong code: two low electric buzzes from the safe |
| `sfx/safe_open.ogg` | 2.32 s | no | peak -1.0 dBFS | 22 KB | synth | Heavy safe bolts retract with a clunk, then the steel door creaks open |
| `sfx/secret_panel.ogg` | 1.45 s | no | peak -1.0 dBFS | 16 KB | synth | Hidden walnut panel: latch release, smooth wooden slide, click into place |
| `sfx/shutter_slam.ogg` | 1.79 s | no | peak -0.8 dBFS | 20 KB | synth | Corrugated steel fire shutter crashes down; slats rattle; emergency relays click on aisle by aisle |
| `sfx/slide_clunk.ogg` | 0.40 s | no | peak -0.8 dBFS | 7 KB | synth | Glass slide pushed into (or out of) the slide projector gate: plastic-and-metal clunk with a spring |
| `sfx/slide_fan_loop.ogg` | 5.00 s | yes | peak -0.8 dBFS | 38 KB | synth | Slide projector running: cooling fan, blade hum and lamp transformer (seamless loop) |
| `sfx/splicer_click.ogg` | 0.26 s | no | peak -1.1 dBFS | 6 KB | synth | Film splicer: blade snaps down through the film and the clamp clicks |
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
| `ambience/amb_lab_dark.ogg` | 1:00.0 | yes | -24.2 LUFS | 867 KB | synth | Lab 7 in the dark: rain on the window, distant wind, low room tone, rare drips and creaks |
| `ambience/amb_power_hum.ogg` | 20.00 s | yes | -24.0 LUFS | 314 KB | synth | Restored power: subtle 50 Hz transformer hum with harmonics and faint electrical hiss |
| `music/music_archive.ogg` | 2:30.0 | yes | -20.0 LUFS | 2453 KB | synth | Archive underscore: A minor analog pads, tine e-piano, vibraphone, soft pluck arpeggio with tape echo and wow |
| `music/music_archive_finale.ogg` | 1:04.0 | yes | -20.0 LUFS | 1083 KB | synth | Vault finale: tender celesta theme with e-piano over warm F major strings, a borrowed minor iv, glass light |
| `music/music_lab.ogg` | 2:40.0 | yes | -20.0 LUFS | 1957 KB | synth | Gameplay underscore: low, sparse D-pedal pads, rare soft celesta, distant metallic swells |
| `music/music_menu.ogg` | 2:30.0 | yes | -20.0 LUFS | 2180 KB | synth | Main menu theme: slow evolving D minor pads, sparse celesta melody with echoes, deep hall |
| `music/stinger_chapter_complete.ogg` | 8.47 s | no | -20.0 LUFS | 124 KB | synth | Chapter complete: Bbmaj7 lifts to a warm D major add9 bloom; a last high 9th and a faint b6 linger |
<!-- ASSET-TABLE:END -->

## Known limitations

- Everything was checked by measurement and spectrogram, not by ear. Timbre choices, especially the door creak and the music voicings, deserve a listening pass on a phone speaker and on headphones.
- Phone speakers roll off below about 200 Hz. The heaviest impacts (`door_slam`, `safe_open`, `breaker_*`, `projector_fire`) keep much of their weight in the 50–150 Hz range, so they will sound lighter on phones.
- `amb_lab_dark` is a 60 s loop. Its rare events (four drips, three creaks) repeat every minute, which an attentive player may notice in a long session. `amb_archive` behaves the same way: three distant canisters, five pipe-tick clusters, two paper rustles, two creaks and one relay repeat every minute.
- The tape murmur has the rhythm and intonation of speech, but its vowel targets are random. It was checked by spectrogram only, and it deserves a listen to confirm it never resembles real words.
