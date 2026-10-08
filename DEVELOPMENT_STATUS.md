# Development Status

_Last updated: 2026-10-08_

| Phase | Status | Verified evidence |
|---|---|---|
| 0 — Audit, architecture, story, art direction, puzzle graph | ✅ Done | `docs/` (STORY, PUZZLE_DESIGN, DESIGN_PILLARS, ART_DIRECTION, ARCHITECTURE, ROOM_LAYOUT) |
| 1 — Godot project + core logic + tests | ✅ Done | `tools/run_tests.sh`: **39 tests, 2296 checks, 0 failures**. 300-seed random-play fuzz shows no softlock or lost items |
| 2 — Assets: textures, fonts, audio, models | 🔶 In progress | ✅ 18 CC0 PBR textures + 62 materials · ✅ 3 OFL fonts (coverage checked) · ✅ 14 CC0 Poly Haven props · ✅ ~40 original synthesized sounds/music (agent finishing) · 🔶 Blender procedural models: 7 done (desk, bookshelf, lab bench, flip clock, gear box, pendant lamp, Leyla echo figure); room shell, door, safe, panel, projector, radio, mirrors and items are still being modelled |
| 3 — Interactive room & puzzles | 🔶 Playable vertical slice | `lab7.tscn` with HUD (inventory with 3D-rendered icons, inspect view, notebook with UV page, hints, pause, choice, chapter complete), touch camera, all 12 puzzles bound. **Runtime playthrough in the real 3D scene completes Chapter 1 (13/13 steps)**. 12 steps were done by actual 3D taps; the rest used logic fallbacks where models are still placeholders |
| 4 — Polish, UI, sound | ⏳ | — |
| 5 — Localization & tests | 🔶 Mostly | 296 keys EN→RU→UZ (validator: Uzbek Latin only, placeholders, font coverage). Layout-fit test at text scale 1.3 passes. **41 tests, 2485 checks, 0 failures** |
| 6 — Android build | 🔶 Debug APK built locally | Signed arm64 debug APK, `apksigner verify` OK, **123 MB**. Mobile texture policy applied (ETC2/ASTC, mipmaps, size limits). Not yet tested on a physical device |
| 7 — iOS preparation | 🔶 Prepared, unverified | iOS export preset + `ios.yml` workflow (macOS runner, TestFlight upload step). Cannot be built here (no macOS); not run (needs owner consent + Apple credentials) |
| 8 — Store & monetization | 🔶 Partly | Purchase abstraction (mock/disabled providers), real payments disabled; `docs/MONETIZATION.md`, `docs/STORE_LISTING.md` (EN/RU/UZ), `docs/RELEASE_PIPELINE.md` |

## Greybox (2026-10-08)
- `game/qa/room_preview.tscn` assembles every model that exists, using the real coordinates from `docs/ROOM_LAYOUT.md`.
- Missing models appear as **labelled placeholder boxes**. The room shell is a temporary plain shell with a window opening.
- Renders are in `docs/previews/`, in two lighting states each: `*_dark` (before power) and `*_powered`.

## Performance (software renderer in container: indicative only)
| Metric | Lab root (dark) | After power |
|---|---|---|
| Draw calls | 100 | 111 |
| Primitives | 155k | 162k |
| Scene build time | 5.0 s (llvmpipe) | |

Budget: ≤ 150 draw calls (OK), about 150k triangles (slightly over; to optimize when the final models land).

## Known limitations
- No GPU in the dev container. Screenshots are rendered with software Vulkan (lavapipe), so FPS measured here is not representative of phones.
- No macOS, so iOS builds cannot be verified in this environment.
- No physical Android device has been tested yet.
