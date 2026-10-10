# Next Steps

How the work is organised (from 2026-10-09): the main session is the game director. Helper agents run in parallel; their results are reviewed and committed to `main`. If a session stops, the next one continues from this file, `DEVELOPMENT_STATUS.md`, `docs/GAMEPLAY_QA.md` and `docs/QUALITY_REPORT.md`.

**Running now (2026-10-09, afternoon):**
- main menu redesign in the owner's "The Room" direction (gear box hero, serif text items, entrance motion);
- Ch3 model group A (shells, lift, doors), and groups B+C (Choir Hall props, control desk, cabinets, ports);
- Ch3 room scene integration (`underground_room.gd`, `playthrough_ch3`): done for the built groups; as B, D, E and F land, rerun `playthrough_ch3` on both key paths (`--key=strand|leyla`), tap-map the new close-ups and re-measure the Choir views (choir_s 90 / desk 86 draw calls before group B);
- store listing (letter-style description, hero screenshots).

Next in the queue:
- UI follow-ups after the readability pass (done 2026-10-10: presets, contrast, reader, settings panel, HUD banners and column): a device check of the Large / Extra large presets on the owner's iPhone, then the Chapter 2 / 3 HUD details (the receiver meter at Extra large);
- Ch3 **model list complete** (2026-10-10: groups A to H built; E = `leyla_camp`, `field_recorder`, `oscillograph`, `crystal_shutter`, F = `gallery_console`, `memorial_wall`; measured notes `docs/models/ch3_e.md`, `ch3_f.md`): next, wire E and F into `underground_room.gd` (the mounts `cradle_mount`, `choice_mount`, `socket_42_mount` are the items' ORIGINS, see ch3_f.md; add a lamp over the console and one on the memorial arc) and rerun `playthrough_ch3` on both keys.

**Top priority:** the iOS crash on New Game (TestFlight build 2). Build 5 adds crash recovery (CrashGuard, safe graphics), the last stage in the menu, and the log in the Files app. See docs/TESTING_ON_DEVICE.md, "Device reports".

| Track | Owner | Next |
|---|---|---|
| Game (3D, puzzles, story, UX) | director | iOS crash, game feel (camera done: smooth follow, glide, arcs), Chapter 3 integration review |
| Android / Google Play | agent 1 | Release AAB path, closed-testing plan (12 testers × 14 days check), tester invitation plan → `docs/release/GOOGLE_PLAY_TESTING.md` |
| iOS / TestFlight | agent 2 | Read-only check of the existing App Store Connect record "Mystery Room: Lost Institute" (no duplicate app), bundle id match, IPA build → `docs/release/IOS_TESTFLIGHT.md` |
| QA / gameplay | agent 3 | Real-scene playthroughs of every chapter on many variant seeds, softlock/save/load/endings, mobile text and touch |
| Visual / assets | agent 4 | Mobile UI text scaling and touch targets (in progress), then lighting, storytelling props, logo comparison |

**Waiting on the owner (one decision each):**
1. One-time approval to upload test builds to Google Play **Internal testing** and **TestFlight** (internal testers only). No external distribution or public release without a separate approval.
2. Inviting testers to closed testing (later, separately).

## Game
1. **Chapter 2 release:** finish the player review (agent), fix its findings, then set `released: true` for ch2 in `game/src/core/chapters.gd` and update `test_premium_rules`. Tester builds already open it through the `beta_unlock` export feature.
2. **Chapter 2 performance:** done for the budget: the hall view is 144 draw calls / 86k primitives. Next is FPS on real phones: the debug build's FPS line, then `tap_map --breakdown` for any view that drops.
3. **Chapter 3:** the model contract `docs/models/ch3.md` (agent), then the Blender build agents (2–3 at a time), the scene, variants (docs/VARIANTS.md list) and a real-scene playthrough on both Chapter 2 key paths.
4. **Lighting (directive 1B):** before/after real renders of the over-bright spots (the splicer light box, the projector beam haze); storytelling props that never hide puzzle items (1C).
5. **Chapter 1:** a full player review on the rendered build after the UI audit; minute-by-minute pacing notes (30 s, 1, 2, 3, 5, 10 min).
6. **Real-device test:** `docs/TESTING_ON_DEVICE.md` with the first tester build.
7. **Logo rights:** the owner confirms where the logo artwork came from and that it may be used commercially (`docs/ASSET_LICENSES.md`).

## Chapter 4 — The Experiment (the Array Hall)
Design and logic are done (2026-10-10): `docs/CHAPTER4_DESIGN.md`, `game/src/rooms/array_hall/array_hall_logic.gd`, `game/tests/array_hall_solver.gd`, `game/tests/test_array_hall_puzzles.gd`, `tools/localization/strings_ch4.py`. The chapter is registered in `chapters.gd` with its logic and an empty scene path, `released: false`. Next, in order:
1. **Model contract** `docs/models/ch4.md` from the design's models section (groups A–I), then the Blender agents (two at a time; A first with the shared numerals).
2. **Scene** `game/src/rooms/array_hall/array_hall.tscn` + room code, in the Chapter 3 pattern: the views listed in the design, zone culling, the beam ribbons per `beam:k`, the replay crowd driven by the chronometer wheel, the snap-back staging. Set the `scene` path in `chapters.gd` when it exists.
3. **HUD reader cases** for the Chapter 4 documents (`show_document`: `log4`, `letter4`, `watch4`, `note4`, `parcel4` → `doc4.log`, `doc4.letter`, `doc4.watch`, `doc4.note`, `doc4.parcel`) and the item models named in `ItemDB` (`tower_key`, `strand_log`, `pocket_watch`, `reverse_pawl`, `leyla_parcel`).
4. Before the scene lands, give `main_menu.gd` Continue a guard: a saved `ch4` game with an empty scene path would call `SceneManager.goto("")` (only a dev save can contain one today; the chapter select and the chapter-complete card are already guarded by `Premium.can_play`). `HUD.show_document` has no arm for the five Chapter 4 ids, so "Read" does nothing until step 3.
5. `qa/playthrough_ch4` on both keys, both lens paths and both trust values, plus a variant seed; then `released: true` for ch3 and ch4 together with the bundle.

## Plugins to use (owner's choice, 2026-10-09)
The owner enables these on the claude.ai account; they load in a new session. Use them where they help the game:
- **Superpowers:**
  - `systematic-debugging` for any failing test, hang or crash;
  - `verification-before-completion` before reporting a task as done;
  - `brainstorming` and `writing-plans` for Chapter 4 and other new chapters;
  - `dispatching-parallel-agents` and `subagent-driven-development` for the model and QA agents.
- **Design (Anthropic):**
  - `design-critique` on real Godot screenshots;
  - `accessibility-review` for the phone UI (text size, contrast, touch targets);
  - `ux-copy` for hints, messages and store texts in EN/RU/UZ.
- **frontend-design (Anthropic):** store pages, artifacts and press kit pages.
- **Task Observer:** turns the owner's corrections into rules in `CLAUDE.md`. The isolation rules there (never touch NFCSTORE; no secrets in code) stay first and must never be weakened.
- **AI Skills (`find-skills`):** look up a fitting skill before starting an unfamiliar kind of task.
