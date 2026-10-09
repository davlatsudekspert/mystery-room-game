# Next Steps

How the work is organised (from 2026-10-09): the main session is the game director. Helper agents run in parallel; their results are reviewed and committed to `main`. If a session stops, the next one continues from this file, `DEVELOPMENT_STATUS.md`, `docs/GAMEPLAY_QA.md` and `docs/QUALITY_REPORT.md`.

| Track | Owner | Next |
|---|---|---|
| Game (3D, puzzles, story, UX) | director | Chapter 2 release, Chapter 3 scene, lighting and performance passes |
| Android / Google Play | agent 1 | Release AAB path, closed-testing plan (12 testers × 14 days check), tester invitation plan → `docs/release/GOOGLE_PLAY_TESTING.md` |
| iOS / TestFlight | agent 2 | Read-only check of the existing App Store Connect record "Mystery Room: Lost Institute" (no duplicate app), bundle id match, IPA build → `docs/release/IOS_TESTFLIGHT.md` |
| QA / gameplay | agent 3 | Real-scene playthroughs of every chapter on many variant seeds, softlock/save/load/endings, mobile text and touch |
| Visual / assets | agent 4 | Mobile UI text scaling and touch targets (in progress), then lighting, storytelling props, logo comparison |

**Waiting on the owner (one decision each):**
1. One-time approval to upload test builds to Google Play **Internal testing** and **TestFlight** (internal testers only). No external distribution or public release without a separate approval.
2. Inviting testers to closed testing (later, separately).

## Game
1. **Chapter 2 release:** finish the player review (agent), fix its findings, then set `released: true` for ch2 in `game/src/core/chapters.gd` and update `test_premium_rules`. Tester builds already open it through the `beta_unlock` export feature.
2. **Chapter 2 performance:** the hall view was 213 draw calls / 152k primitives. The shadowed pendant now uses a downward spot cone instead of a dual-paraboloid omni; re-measure, then look at visibility ranges for small props.
3. **Chapter 3:** the model contract `docs/models/ch3.md` (agent), then the Blender build agents (2–3 at a time), the scene, variants (docs/VARIANTS.md list) and a real-scene playthrough on both Chapter 2 key paths.
4. **Lighting (directive 1B):** before/after real renders of the over-bright spots (the splicer light box, the projector beam haze); storytelling props that never hide puzzle items (1C).
5. **Chapter 1:** a full player review on the rendered build after the UI audit; minute-by-minute pacing notes (30 s, 1, 2, 3, 5, 10 min).
6. **Real-device test:** `docs/TESTING_ON_DEVICE.md` with the first tester build.
7. **Logo rights:** the owner confirms where the logo artwork came from and that it may be used commercially (`docs/ASSET_LICENSES.md`).

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
