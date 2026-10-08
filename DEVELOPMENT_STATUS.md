# Development Status

_Last updated: 2026-10-08_

| Phase | Status | Verified evidence |
|---|---|---|
| 0 — Audit, architecture, story, art direction, puzzle graph | ✅ Done | `docs/` (STORY, PUZZLE_DESIGN, DESIGN_PILLARS, ART_DIRECTION, ARCHITECTURE, ROOM_LAYOUT) |
| 1 — Godot project + core logic + tests | ✅ Done | `tools/run_tests.sh`: **39 tests, 2296 checks, 0 failures**. 300-seed random-play fuzz shows no softlock or lost items |
| 2 — Assets: textures, fonts, audio, models | 🔶 In progress | ✅ 18 CC0 PBR textures + 62 materials · ✅ 3 OFL fonts (coverage checked) · ✅ 14 CC0 Poly Haven props · ✅ ~40 original synthesized sounds/music (agent finishing) · 🔶 Blender procedural models: 7 done (desk, bookshelf, lab bench, flip clock, gear box, pendant lamp, Leyla echo figure); room shell, door, safe, panel, projector, radio, mirrors and items are still being modelled |
| 3 — Interactive room & puzzles | 🔶 Started | Greybox assembled and rendered (`docs/previews/`). Camera, touch input, Lab7 scene, visuals binding, UV/beam/echo shaders written. HUD is in progress. **Not yet playable end-to-end in 3D** |
| 4 — Polish, UI, sound | ⏳ | — |
| 5 — Localization & tests | 🔶 Partly | 296 keys in EN/RU/UZ (validated). Layout overflow checks pending |
| 6 — Android build | ⏳ | — |
| 7 — iOS preparation | ⏳ | — |
| 8 — Store & monetization | 🔶 Partly | Purchase abstraction (mock/disabled providers), real payments disabled |

## Greybox (2026-10-08)
- `game/qa/room_preview.tscn` assembles every model that exists, using the real coordinates from `docs/ROOM_LAYOUT.md`.
- Missing models appear as **labelled placeholder boxes**. The room shell is a temporary plain shell with a window opening.
- Renders are in `docs/previews/`, in two lighting states each: `*_dark` (before power) and `*_powered`.

## Known limitations
- No GPU in the dev container. Screenshots are rendered with software Vulkan (lavapipe), so FPS measured here is not representative of phones.
- No macOS, so iOS builds cannot be verified in this environment.
- No physical Android device has been tested yet.
