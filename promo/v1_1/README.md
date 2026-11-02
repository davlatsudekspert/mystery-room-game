# MYSTERY ROOM: Lost Institute 1.1 - promo videos ("New floors")

Made only from the real game (Godot 4.7.2 movie writer under Xvfb, software Vulkan), the game's own audio, an offline synthetic English
narration and a synthesized sting. **No file of `game/` was changed or added**: the capture scripts live here (`godot/`) and are copied
into a scratch project (`make_scratch.sh`: symlinks to `game/`, its own `project.godot`, a private `qa/`). Nothing of NFCSTORE was touched.
The MP4 / ZIP files are NOT committed (`.gitignore`); texts, `.srt`, covers, scripts and logs are.

## Deliverables (all in `promo/v1_1/`; sizes and facts from ffprobe)

### A. Owner review (private, not for YouTube)
| File | Facts |
|---|---|
| `OWNER_REVIEW_chapter2_full_seedA_1280x720.mp4` | 1280x720, 30 fps, H.264 yuv420p, AAC 48 kHz stereo (the game's own audio incl. music), 450.0 s, 155.9 MB |
| `OWNER_REVIEW_seed_comparison_A_vs_B.mp4` | 1920x720, 30 fps, H.264, AAC, 33.8 s, 17.4 MB |
| `review_report_seedA.txt`, `review_markers_seedA.tsv` | the playthrough's own report (every step, 177 taps, 0 fallbacks) and the frame-exact markers used for the labels |

* Review video = `qa/playthrough_ch2.gd` (the real Chapter 2 expansion playthrough, real taps through the 3D scene) with `--seed=9137 --no-continue`
  (the quit-and-Continue checks are skipped: they rebuild the room and add nothing to watch). Result of the run: exit 0, 177 taps, 0 logic fallbacks,
  0 taps under a HUD control. The whole run is 511 s of game time, so **nothing was sped up**. **Cut at 450 s on purpose**: the chapter-complete card
  (443.9 s) is the last thing shown; the cliffhanger and the "Chapter 3 (soon)" card (444-511 s) are not in the file (Chapters 3-4 are not released).
  The raw 511 s recording was deleted to free disk; `encode_review.sh` / `record_playthrough.sh` rebuild it (about 1.5 h of software rendering).
* Labels: top left "Now: <step>" (the puzzle step being played; it names the answers used, e.g. "N2 valves 1,3,4,5"), bottom left "tap: <model/part>" after each tap.
  They are burned in from the recorder's markers (`review_labels.py`) because the in-game overlay layer of the recording copy did not render (found after the 90 min run).
  Step names are named when the step completes, so the label shows the step that is being played.
* Comparison clip: the same views in two new games, seed A = 9137 (left) and seed B = 3 (right): panel letter (hall), pipe graph / valves (Pump Room), light table digits
  (Night Cell), carriage start slots and the plan plate (Cold Store), chest rings, cabinet code (Office), plus the Chapter 1-2 codes (booth dial, compressor valves, request-card punch).
  Seeds were chosen with `godot/seed_probe.gd` (`seed_probe_output.txt` and the values on screen come from the logic itself): panel B/A, pipe graph #4/#3, light digits 11/31,
  carriage slots 13456/01234, chest signs 321/534, cabinet 4076/6537, booth 743/414, valves 102/422, punch 10011100/01010011. The footage is the real scene
  at each seed (initial puzzle state), not a solved state. It shows answers: private.

### B. YouTube package (no walkthrough, no solved states, no Chapter 3/4)
| File | Facts |
|---|---|
| `trailer_new_floors_16x9.mp4` (+ `_ru`, `_uz`) | 1920x1080, 30 fps, H.264 yuv420p, AAC 48 kHz stereo, 100.5 s, ~87 MB each; about -15.9 LUFS integrated, sample peak -0.8 dBFS |
| `short_new_floors_9x16.mp4` (+ `_ru`, `_uz`) | 1080x1920 (native vertical render, not a crop), 30 fps, H.264, AAC, 44.1 s, ~27.7 MB each; about -16.3 LUFS, peak -1.5 dBFS |
| `trailer_new_floors_16x9_en/ru/uz.srt`, `short_new_floors_9x16_en/ru/uz.srt` | one cue per narration line (times of `timeline.json`) |
| `youtube_thumbnail_1280x720.png`, `shorts_cover_1080x1920.png` | real frames (frost window with the silhouette; Cold Store shelves) + large title; English only |
| `YOUTUBE_TEXTS.md`, `NARRATION_SCRIPT.md` | titles (<100), descriptions, chapters, tags (<500), hashtags in EN/RU/UZ; timed script |
| `mystery_room_1_1_youtube.zip` | exactly the files above (16 files, 347 MB); the owner-review files are NOT in it |

Each video exists in three burned-in variants: English voice + English subtitles (no suffix), + Russian subtitles (`_ru`), + Uzbek subtitles (`_uz`); never two subtitle languages at once.
The trailer has: title card (0-4.6 s), hall, the in-game Building plan screen, the service-door walk-through, Pump Room (pipe diagram, manifold, the door knock moment), Night Cell light table,
the cold-door walk-through into the Cold Store, the frost wipe with the silhouette moment, the book lift, the Reading Gallery board and balcony, the Plate Room enlarger, the Director's Office
cabinet, end card "Search: Mystery Room: Lost Institute" with "Chapters 1 and 2 are free" (no URL, no price). Puzzle shots are beginnings: pipes dead, sheets unaligned, board empty, cabinet closed;
the frost shot shows one band wiped (one sign), nothing else of that puzzle.

## Sources of every clip (scene `game/src/rooms/archive/archive.tscn` via `godot/promo_ch2.tscn`, a NEW expansion game, `GameState.variant_seed` = seed)
Command shape (`render_clip.sh`; exact commands and wall times: `render_log.txt`):

    xvfb-run -a godot --path $PROMO_WORK/pg_clip_WxH --write-movie clip.avi --fixed-fps 30 --resolution WxH res://qa/promo_ch2.tscn -- \
        --seed=9137 --until=<solver state> --room=<start room> --steps="<steps>" --hud=0 --music=0

`--until` brings the game to a state with the project's own solver (`tests/archive_solver.gd`), `--music=0` mutes the Music bus (the music bed is added in the edit). The first 37 frames
(1.2 s) of a clip are the scene settling and are trimmed. Walk-throughs are real taps on the door parts (`tap:` / `tapat:`), so the game's own door walk plays.

| Clip (1920x1080 `L_*`, 1080x1920 `P_*`) | seed | state (`--until`) / room | Steps (see `build_clips.sh` for the exact strings) |
|---|---|---|---|
| L_hall / P_hall | 9137 | new game / hall | slow yaw pan (portrait: camera `keep_aspect` width) |
| L_plan | 9137 | pump_open / hall | pan, then the HUD Building plan screen (`show_plan`, rooms marked seen) |
| L_door / P_door | 9137 | pump_open / hall | view east_south, tap the service door, walk into the Pump Room |
| L_pump / P_pump | 9137 | pump_open / pump | views pipes, manifold, cell_door (first look = knock moment) |
| L_cell / P_cell | 9137 | pump_open / cell | pan, views light_table, cold_door |
| L_cold_walk / P_cold_walk | 9137 | cold_open / cell | view cold_door, tap the doorway, walk into the Cold Store, views cranks |
| L_frost | 9137 | aisle / cold | cloth taken, view frost, finger wipe over band 1 (silhouette moment) |
| L_lift | 9137 | thawed / pump | views lift_door, lift_weights, lift_panel |
| L_gallery / P_gallery | 9137 | lift_ok / gallery | views gallery, board, balcony |
| L_plate / P_plate | 9137 | lift_ok / plate | views enlarger, trays |
| L_office | 9137 | pass_key / office | pan, views cabinet, office_desk |
| CMP_* (960x540, A/B) | 9137 / 3 | hall, pump_open, cold_open, aisle, pass_key | one puzzle view each (`build_compare.sh`) |
| L_door2 | 9137 | lift_ok / gallery | rendered, NOT used: the Plate Room door tap did not walk (the camera view did not reach the door) |

Review recording: `record_playthrough.sh A 9137 1280x720` -> `$PROMO_WORK/rec_A` (`qa/playthrough_ch2_rec`, generated by `godot/make_rec.py` from the unchanged `qa/playthrough_ch2.gd`).

## Audio (origin and licence)
| Use | Source | Licence / origin |
|---|---|---|
| Room ambience, door steps, lift, enlarger, moment cues (knocks, frost steps) in the clips | the game's own audio of each take (`AudioManager`), recorded by the movie writer | original, synthesized by `tools/audio/synth_all.py` (`docs/AUDIO_CH2X.md`) |
| Music bed | `game/assets/audio/music/music_archive.ogg` (the Chapter 2 theme), 0.5 gain, ducked by the voice | original, synthesized; `docs/ASSET_LICENSES.md` |
| Narration | piper (MIT) + voice `en_GB-cori-high` (https://huggingface.co/rhasspy/piper-voices, dataset LibriVox, public domain), `--length-scale 1.18`, sox post (low cut, light reverb) | offline synthetic speech, no paid service (`build_voice.sh`, `narration_lines.txt`) |
| Sting before the end card | sox sine synthesis (`build_voice.sh`) | original, not a project asset |
| Fonts on cards and subtitles | Cormorant Garamond Bold, Noto Sans (from `game/assets/fonts`) | SIL OFL 1.1 |
Mix: clip audio x2, music 50 %, `sidechaincompress` under the voice, `loudnorm` I=-16 LUFS TP=-1.5, AAC 192 kbit/s. No Chapter 3/4 audio.

## Build commands
    export PROMO_WORK=/tmp/promo_work
    promo/v1_1/build_voice.sh                 # narration + sting (piper venv is created in $PROMO_WORK/piper)
    promo/v1_1/build_clips.sh                 # trailer / Short clips (about 5 min per 1080p clip on 4 cores; ~1.5 h in all)
    promo/v1_1/build_compare.sh && python3 promo/v1_1/build_compare.py
    python3 promo/v1_1/build_videos.py        # trailer + Short, EN/RU/UZ, .srt, timeline.json (ffmpeg commands: ffmpeg_log.txt)
    promo/v1_1/build_covers.sh
    promo/v1_1/record_playthrough.sh A 9137 && promo/v1_1/encode_review.sh
    (cd promo/v1_1 && zip -j mystery_room_1_1_youtube.zip <the 16 files listed above>)

## Checks done
Contact sheets and full-size frames of every clip and of the finished videos were looked at: title and end cards, the Building plan screen, Russian and Uzbek subtitles (the Uzbek modifier
apostrophe renders), the walk-throughs, thumbnails and covers, labels of the review video. No debug UI, no Chapter 3/4 content, no solved puzzle state, no black frames except the
0.3 s fades (blackdetect: one deliberate fade of 0.9 s before the Short's end card). ffprobe facts above are from the final files.
Fixed on the way: a recorder label layer that did not render (labels now burned in), the frost wipe that did nothing without the cloth (cloth taken first), a floor-plan view that framed the
lockers (replaced by the hall pan + the plan screen), segments longer than their clips (durations re-set), voice lines that overlapped (a check now refuses a build), a Short cover with a
cut-off title and a distorted close-up.

## Honest status: what is missing
* **The narration was not heard by a human.** Nobody here can listen: only levels, ducking, clipping and sync were checked by measurement. Listen before publishing; if it is wrong, record the lines of `NARRATION_SCRIPT.md` and rebuild.
* The game audio in the clips is the real in-game mix but the music is added in the edit; effects/ambience crossfades are 0.3 s dips at the cuts. The audio balance was not judged by ear.
* **Russian and Uzbek subtitle texts are not natively reviewed.** The Uzbek game name "Unutilgan institut" follows the owner (the game's own string is "Unutilgan institut").
* The thumbnail and the Shorts cover exist in English only.
* One Short only (44 s), not a series. Footage is software-rendered (llvmpipe) game footage, not a phone recording; no hands/touch indicator in the YouTube videos.
* The Building plan screen is shown as the game draws it (dim; most rooms "locked" at that state): honest, but small text. The door walk-through into the Plate Room was not captured (L_door2 failed).
* "About an hour for Chapter 2" is an estimate; no human playtest has measured it (bot play of the whole chapter takes 8.5 min of game time).
* The seed-comparison clip shows the initial state of each puzzle with the answers as captions from the logic; it does not show them being solved.
* `render_log.txt` also holds two test renders (`t_door`) and a killed first recording attempt; `ffmpeg_log.txt` has every encode command.
