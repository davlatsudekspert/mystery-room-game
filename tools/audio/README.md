# Audio tools: MYSTERY ROOM, The Forgotten Institute

Every sound, ambience and music cue in `game/assets/audio/` is made by code in this folder.
The one exception is a single CC0 page-flip recording, which is layered into `page_turn`.
No paid services or AI audio tools are used. Re-running the generator gives the same files byte for byte.

```bash
pip install -r tools/audio/requirements.txt     # numpy, scipy, Pillow
python3 tools/audio/synth_all.py                 # regenerate all 40 files (~70 s on 4 cores)
python3 tools/audio/synth_all.py --only ui_tap,reveal --qa-dir /tmp/audio_qa   # a subset plus spectrogram PNGs
python3 tools/audio/synth_all.py --list          # list registered sounds
```

You also need `ffmpeg` with libvorbis (for encoding and loudness measurement) and `sox` (for verification decoding).
A full run (no `--only`) also rewrites the asset table below.

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
- `amb_lab_dark` is then rotated so the file starts at its calmest moment (`rotate_to_calm_point`). The Vorbis encoder codes the first and last frames independently, so a calm seam is safest.
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

## Godot notes

- **Looping:** Godot imports OGG with `loop = false`. For `amb_lab_dark`, `amb_power_hum`, `music_menu` and `music_lab`, do one of these:
  - Tick *Loop* in the Import dock and re-import.
  - Set `(stream as AudioStreamOggVorbis).loop = true` in `AudioManager`.

  `loop_offset` stays 0.
- **Music start:** the loops are circular, so position 0 is mid-texture (the last chord's pad is still releasing). Fade music in over about 2 s, or let the `AudioManager` crossfade handle it.
- **Suggested playback levels:**
  - `amb_power_hum` is mastered to -24 LUFS like the rain bed. Its 100 Hz body is strong on headphones, so start it about 8–10 dB under `amb_lab_dark`, or duck the rain slightly when power comes back.
  - `breaker_on` and `power_on` already fade their own hum tails, so start the hum loop under them.
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
| `sfx/box_open.ogg` | 0.83 s | no | peak -1.0 dBFS | 10 KB | synth | Small lid springs open: latch click, coil-spring twang, lid knock |
| `sfx/breaker_on.ogg` | 2.53 s | no | peak -1.1 dBFS | 11 KB | synth | Main breaker lever thrown: big clunk, then transformer hum swells in |
| `sfx/breaker_trip.ogg` | 0.90 s | no | peak -0.8 dBFS | 13 KB | synth | Breaker trips: spark crackle, hum dies, lever snaps back with a clunk |
| `sfx/door_open.ogg` | 2.84 s | no | peak -0.9 dBFS | 28 KB | synth | Heavy old wooden door unlatches and swings open on a long, groaning creak |
| `sfx/door_slam.ogg` | 1.79 s | no | peak -1.2 dBFS | 15 KB | synth | Heavy wooden door slams shut; latch catches; the room rings briefly |
| `sfx/drawer_locked.ogg` | 0.79 s | no | peak -1.0 dBFS | 10 KB | synth | Locked desk drawer tugged: wooden rattle against the bolt |
| `sfx/drawer_open.ogg` | 1.38 s | no | peak -1.0 dBFS | 15 KB | synth | Wooden drawer slides open on dry runners and stops with a soft knock |
| `sfx/gear_turn.ogg` | 0.68 s | no | peak -1.2 dBFS | 10 KB | synth | Strand's gear box knob: ratchet clicks and a gear settling into place |
| `sfx/item_combine.ogg` | 1.15 s | no | peak -3.2 dBFS | 11 KB | synth | Two parts click together, then a bright celesta sparkle (items combined) |
| `sfx/item_pickup.ogg` | 0.83 s | no | peak -3.0 dBFS | 10 KB | synth | Quick leather/cloth rustle and a little music-box arpeggio (item taken) |
| `sfx/key_turn.ogg` | 1.16 s | no | peak -1.1 dBFS | 14 KB | synth | Brass key slides into the lock past the pins and turns with a clack |
| `sfx/keypad_press.ogg` | 0.34 s | no | peak -0.9 dBFS | 7 KB | synth | Electromechanical safe key: bakelite plunger click and contact |
| `sfx/lens_insert.ogg` | 0.58 s | no | peak -0.9 dBFS | 8 KB | synth | Crystal lens seats into its brass mount: soft scrape, click, glass ring |
| `sfx/maglock_release.ogg` | 1.61 s | no | peak -1.0 dBFS | 13 KB | synth | Door maglock lets go: coil hum cuts out, armature clunk, door rattles |
| `sfx/page_turn.ogg` | 0.69 s | no | peak -0.7 dBFS | 11 KB | synth + Kenney CC0 `bookFlip2.ogg` (RPG Audio) | A page of Leyla's notebook is turned (paper crinkle and air flap) |
| `sfx/power_on.ogg` | 2.77 s | no | peak -1.1 dBFS | 20 KB | synth | Power restored: relays click in sequence, lights and the Array hum up |
| `sfx/projector_charge.ogg` | 2.25 s | no | peak -1.1 dBFS | 16 KB | synth | Lumen Projector charging: rising electrical whine over a growing hum |
| `sfx/projector_fail.ogg` | 1.27 s | no | peak -1.4 dBFS | 15 KB | synth | Projector mistuned: the charge sputters, fizzles and dies with a pop |
| `sfx/projector_fire.ogg` | 3.12 s | no | peak -0.8 dBFS | 32 KB | synth | Projector fires through the crystal: bright resonant burst, long shimmering tail |
| `sfx/puzzle_solved.ogg` | 2.47 s | no | peak -0.9 dBFS | 20 KB | synth | Resonant bell-like D major add9 chord, gently arpeggiated (puzzle solved) |
| `sfx/reveal.ogg` | 1.64 s | no | peak -1.0 dBFS | 20 KB | synth | Soft glassy shimmer as UV light reveals hidden ink |
| `sfx/ring_turn.ogg` | 0.46 s | no | peak -1.1 dBFS | 7 KB | synth | Projector's brass colour ring turns one stop (click with a slight ring) |
| `sfx/rosette_press.ogg` | 0.50 s | no | peak -0.9 dBFS | 7 KB | synth | Carved wooden rosette pressed in: hollow wood click and a hidden latch |
| `sfx/safe_denied.ogg` | 0.95 s | no | peak -0.9 dBFS | 10 KB | synth | Wrong code: two low electric buzzes from the safe |
| `sfx/safe_open.ogg` | 2.32 s | no | peak -1.0 dBFS | 22 KB | synth | Heavy safe bolts retract with a clunk, then the steel door creaks open |
| `sfx/secret_panel.ogg` | 1.45 s | no | peak -1.0 dBFS | 16 KB | synth | Hidden walnut panel: latch release, smooth wooden slide, click into place |
| `sfx/switch_toggle.ogg` | 0.51 s | no | peak -1.1 dBFS | 7 KB | synth | Heavy bakelite toggle switch snapping over (clack) |
| `sfx/uv_on.ogg` | 1.03 s | no | peak -0.8 dBFS | 13 KB | synth | UV lamp switched on: small click and a faint ballast buzz |
| `sfx/wheel_tick.ogg` | 0.34 s | no | peak -1.1 dBFS | 7 KB | synth | Brass combination wheel moving one detent (crisp click) |
| `ambience/amb_lab_dark.ogg` | 1:00.0 | yes | -24.2 LUFS | 867 KB | synth | Lab 7 in the dark: rain on the window, distant wind, low room tone, rare drips and creaks |
| `ambience/amb_power_hum.ogg` | 20.00 s | yes | -24.0 LUFS | 314 KB | synth | Restored power: subtle 50 Hz transformer hum with harmonics and faint electrical hiss |
| `music/music_lab.ogg` | 2:40.0 | yes | -20.0 LUFS | 1957 KB | synth | Gameplay underscore: low, sparse D-pedal pads, rare soft celesta, distant metallic swells |
| `music/music_menu.ogg` | 2:30.0 | yes | -20.0 LUFS | 2180 KB | synth | Main menu theme: slow evolving D minor pads, sparse celesta melody with echoes, deep hall |
| `music/stinger_chapter_complete.ogg` | 8.47 s | no | -20.0 LUFS | 124 KB | synth | Chapter complete: Bbmaj7 lifts to a warm D major add9 bloom; a last high 9th and a faint b6 linger |
<!-- ASSET-TABLE:END -->

## Known limitations

- Everything was checked by measurement and spectrogram, not by ear. Timbre choices, especially the door creak and the music voicings, deserve a listening pass on a phone speaker and on headphones.
- Phone speakers roll off below about 200 Hz. The heaviest impacts (`door_slam`, `safe_open`, `breaker_*`, `projector_fire`) keep much of their weight in the 50–150 Hz range, so they will sound lighter on phones.
- `amb_lab_dark` is a 60 s loop. Its rare events (four drips, three creaks) repeat every minute, which an attentive player may notice in a long session.
