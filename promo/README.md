# MYSTERY ROOM: Lost Institute - promo videos

Three YouTube videos made only from the real game (rendered by the real project with Godot's movie writer), the game's own
original audio, a synthesized sting and an offline synthetic English narration. Nothing in the game or its code was changed;
the only addition outside `promo/` is the capture scene `game/qa/promo_capture.{gd,tscn}` (a QA helper like the other `game/qa/*` scenes).

## Status (honest)

| File | Facts (ffprobe) | State |
|---|---|---|
| `video1_teaser_9x16.mp4` (+ `_ru`, `_uz`) | 1080x1920, 30 fps, H.264 yuv420p, AAC 48 kHz stereo, 20.0 s, ~-15 LUFS | built, frames checked |
| `video2_can_you_solve_it_9x16.mp4` (+ `_ru`, `_uz`) | same, 30.0 s, ~-16 LUFS | built, frames checked |
| `video3_trailer_16x9.mp4` (+ `_ru`, `_uz`) | 1920x1080, 30 fps, H.264 yuv420p, AAC, 60.0 s, ~-16 LUFS | built, frames checked |
| `*_en.srt`, `*_ru.srt`, `*_uz.srt` for each video | cue = narration line | done |
| `shorts_cover_1080x1920.png`, `youtube_thumbnail_1280x720.png` | real game frame + title | done |
| `YOUTUBE_TEXTS.md`, `NARRATION_SCRIPT.md` | EN/RU/UZ titles, descriptions, hashtags; timed narration | done |

Each video exists in three burned-in variants: English voice + English subtitles (no suffix), English voice + Russian subtitles
(`_ru`), English voice + Uzbek subtitles (`_uz`); never two subtitle languages at once.
The MP4 files (213 MB together) are NOT committed (limit 120 MB; `promo/.gitignore` ignores them). They are in the container at
`/home/user/mystery-room-game/promo/` and are rebuilt by the scripts below.

What is missing / below professional quality (please read):
* **Narration voice was not judged by ear.** The agent that built this cannot listen to audio. The voice is piper `en_GB-cori-high`
  (neural, offline). It was chosen for its licence and its calm British female delivery; its naturalness in the final mix was only
  checked by measurement (levels, ducking, no clipping), not by listening. The owner must listen before publishing. If it sounds
  wrong, record the lines from `NARRATION_SCRIPT.md` with another tool and rebuild (`build_videos.py` takes `voice/<id>.wav`).
* No real-phone footage: every shot is software-rendered (llvmpipe) game footage with camera moves of the game's own views; no touch
  indicators and no hands. The game HUD is hidden (only the notebook page in the UV shot shows its own reader chrome).
* The sound effects are placed by time against the known camera/logic events, not recorded from the game's own playback, so a few
  may be 0.1-0.3 s off. Puzzle shots are staged: wheels/switches are moved with the game's logic calls and cut before any answer.
  Panel 7's lamps do not light in the clip (they were not refreshed by the direct logic calls); no solved state is shown.
* The Panel 7 / gear box / drawer shots show unsolved states only (drawer wheels show 0120 or 0000, never the code).
* Chapter 2 cliffhanger: only the dark lift-shaft view and the vault door opening are used; the reel/silhouettes, the key choice,
  the voices, the recorder and every later-chapter card are not used.
* Disk of the build container is small (~1 GB free): intermediates are re-encoded and deleted as they are made.

## Source clips (all real game scenes, `game/qa/promo_capture.tscn`, rendered by `build_clips.sh` -> `render_clip.sh`)

Command shape (per clip; the exact steps are in `build_clips.sh`, the executed commands and wall times in `render_log.txt`):

    xvfb-run -a godot --path <scratch project> --write-movie clip.avi --fixed-fps 30 res://qa/promo_capture.tscn -- \
        --room=lab|archive --prep=<state> --steps="..." --hud=0

`<scratch project>` is `$PROMO_WORK/pg_WxH`: symlinks to `game/`, but with its own `project.godot` (viewport = clip size, the window
override removed, MJPEG quality 0.6) because the movie writer records the project viewport size. The first second of each clip
is the room settling and is trimmed. (`render_log.txt` also holds the early test renders and the first two finale attempts that
were stopped when the disk filled up.)

| Clip | Room / state (solver `prep`) | Shot | Used in | Rendered |
|---|---|---|---|---|
| l_dark_{L,P} | Laboratory 7, start | slow look around the dark lab, desk lamp, moonlit window | V1, V3 | 8 s |
| l_drawer_{L,P} | Lab 7, start | the drawer's four wheels turn (to 0120, not the code) | V2, V3 | 5.4 s |
| l_gearbox_L | Lab 7, start | gear box knobs | V3 | 5.6 s |
| l_uv_{L,P} | Lab 7, UV lamp ready | Leyla's notebook, the UV light strikes and the cipher glows | V1, V2, V3 | 7 s |
| l_panel_{L,P} | Lab 7, breaker handle taken | Panel 7 close-up, switches toggled | V2, V3 | 6.1 s |
| l_powered_L | Lab 7, power restored | look around the powered lab, radio | not used in the final cut | 10 s |
| l_darkroom_{L,P} | Lab 7, darkroom open | red darkroom, evidence board | V1, V3 | 10 s |
| l_beam_{L,P} | Lab 7, mirror beam on | the lab with the beam set | V2, V3 | 6.5 s |
| a_hall_{L,P} | Records Archive B, start | archive hall, vault door | V2, V3 | 8 s |
| a_catalogue_L, a_compressor_L, a_deck_{L,P} | Archive, start | card catalogue, compressor, tape deck | not used in the final cut (available) | 5.5 s |
| a_finale_{L,P} | Archive, vault unlocked | wheel turned, vault opens (2.0-7.5 s), lift shaft from 30.3 s | V1 (shaft), V3 (both) | 40.4 s |

Footage that is rendered but not in a final cut is kept in `$PROMO_WORK/clips` for re-edits. Framing: 16:9 clips are native
1920x1080; 9:16 clips are native 1080x1920 renders (not crops). Room views use the camera property `keep_aspect = KEEP_WIDTH`
(wide view); close-ups keep the game's vertical FOV, which gives a tight but well framed vertical close-up.

## Audio (all from the project itself; licences from `docs/ASSET_LICENSES.md`)

Every file under `game/assets/audio/` is synthesized by `tools/audio/synth_all.py` (original) - except `page_turn`, which mixes in one
CC0 Kenney recording (`bookFlip2.ogg`, "RPG Audio", https://kenney.nl/assets/rpg-audio, CC0 1.0).

| File | Use |
|---|---|
| `music/music_lab.ogg` | music bed (V1, V2 from 20 s in, V3 first 40 s) |
| `music/music_archive.ogg` | V3 music from ~36 s (crossfade) |
| `ambience/amb_lab_dark.ogg` | ambience under all three |
| `sfx/intro_thunder`, `uv_on`, `page_turn`, `wheel_tick`, `switch_toggle`, `gear_turn`, `vault_wheel`, `vault_bolts`, `vault_door_open`, `receiver_static` | effects (V1: thunder, uv_on, page_turn; V2: wheel_tick, uv_on, switch_toggle; V3: all) |
| sting (`build_voice.sh`, sox) | original synthesized sub boom + dark pad + shimmer, before the title card; not a project asset |
| narration | piper (MIT) with voice `en_GB-cori-high` (https://huggingface.co/rhasspy/piper-voices, model card: dataset LibriVox recordings, "License: public domain"); synthetic speech, generated offline; no paid service |

No Chapter 3/4 audio (`amb_choir`, `amb_gallery`, `amb_nursery`, `amb_lift`, `music_underground*`, `music_array_hall*`) is used.
Mix: music 55 %, ambience 30 %, ducked by `sidechaincompress` under the voice, effects and sting on top, `loudnorm` to about -16 LUFS,
true peak <= -1.5 dBTP, AAC 192 kbit/s.

## Build commands

    export PROMO_WORK=/tmp/promo_work
    tools/setup_env.sh                                   # Godot 4.7.2 (already present in this container)
    promo/build_clips.sh                                 # all clips (PAR=2 for two parallel renders; keep the finale alone: big AVI)
    promo/build_voice.sh                                 # narration (piper) + sting
    python3 promo/build_videos.py [v1] [v2] [v3]         # videos, .srt files (ffmpeg commands: promo/ffmpeg_log.txt)
    promo/build_covers.sh                                # Shorts cover + thumbnail

`build_videos.py` details: each clip segment is trimmed, scaled/cropped to the target size, faded (0.25 s dips) and concatenated;
title cards are `drawtext` (Cormorant Garamond Bold, OFL, from `game/assets/fonts`); subtitles are an ASS file burned with libass
(Noto Sans Bold, OFL; 74 px on 9:16, 68 px on 16:9, white on a dark box, safe margins, 9:16 subtitles sit at ~70 % height clear of
the Shorts UI); H.264 `-preset slow -crf 21 -maxrate 6M/9M`, yuv420p, 30 fps, AAC. No watermark. The on-screen search line is the
placeholder "Search: Mystery Room: Lost Institute" (no store link exists yet; none was invented).

## Checks done (frames looked at)

Contact sheets and single frames of every video (EN) and of RU/UZ variants: text readable and inside the safe area, no black
frames except the intended fades/end cards, no debug UI, no solved codes. Fixed along the way: the title was cut off on 9:16 (font
too large), the subtitle overlapped the end-card search line on 9:16 (card moved up), subtitle size raised, file size cut (crf 17 gave 40 MB per
30 s Short). Not checked: playback on a real phone, the voice by ear.
