# CLAUDE.md — MYSTERY ROOM (mystery-room-game)

## Absolute rule: isolation
- This repository is the **only** place for MYSTERY ROOM work.
- **Never** read, modify, commit, push, build or deploy anything in NFCSTORE (`davlatsudekspert/nfcx`, typically `/home/user/nfcx`).
- Never copy its secrets, env vars, workflows or configs.
- Before any git write, verify: `git rev-parse --show-toplevel` → `/home/user/mystery-room-game`, and the remote → `davlatsudekspert/mystery-room-game`.

## Environment
- Containers are ephemeral. Run `tools/setup_env.sh` first. It installs Godot 4.7.2, Blender 5.2.2 LTS, export templates, lavapipe Vulkan, Inkscape and SoX.
- Commit and push after every meaningful step. Unpushed work is lost.
- The communication language with the owner is **Uzbek**. Code, comments and docs are in English.

## Commands
- Tests (headless): `tools/run_tests.sh`
- Runtime screenshots (software Vulkan under Xvfb): `tools/capture.sh`
- Rebuild 3D models: `tools/blender/build_all.sh`
- Rebuild audio: `python3 tools/audio/synth_all.py`
- Re-import the Godot project after asset changes: `godot --headless --path game --import`

## Conventions
- Use typed GDScript (`var x: int`, typed function signatures). Use tabs for indentation in `.gd` files.
- Puzzle logic lives in pure `RefCounted` classes (`game/src/core`, `game/src/rooms/*/..._logic.gd`) with **no scene access**. Scenes only render the logic state.
- Every user-facing string goes through `tr()` with a key in `game/localization/strings.csv` (en, ru, uz).
- Puzzle solutions must be language-neutral.
- Assets must be CC0 or original. Record every third-party asset in `docs/ASSET_LICENSES.md`.
- No paid services or assets, and no real payments until store validation (`REAL_PAYMENTS_ENABLED = false`).
- Never claim a test passed or a build works unless it was actually run. Update `DEVELOPMENT_STATUS.md` and `NEXT_STEPS.md` at the end of each phase.
