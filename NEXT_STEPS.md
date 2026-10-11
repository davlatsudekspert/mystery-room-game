# Next Steps

How the work is organised (from 2026-10-09): the main session is the game director. Helper agents run in parallel; their results are reviewed and committed to `main`. If a session stops, the next one continues from this file, `DEVELOPMENT_STATUS.md`, `docs/GAMEPLAY_QA.md` and `docs/QUALITY_REPORT.md`.

**State on 2026-10-11 (afternoon):**
- Test builds out: Android 0.1.0 (13) on Play internal testing and TestFlight build 10 (main 7fbc21f), after the full release gate. They fix the owner's three reports of the day: the Chapter 2/3 tape hiss that kept playing over everything (a looping file played as a one-shot), Normal text 20% smaller with the settings panel fitting a 20:9 phone, and "Crystal lens doesn't fit here." for an item with no use at a target (docs/TESTING_ON_DEVICE.md).

**State on 2026-10-11 (morning):**
- Test builds out: Android 0.1.0 (12) on Play internal testing and TestFlight build 9, built from main 43b1f35 after the full release gate (docs/RELEASE_GATE.md; evidence in docs/TESTING_ON_DEVICE.md). **Chapter 3 is open to testers** (`beta_unlock`; in the store it needs `full_game`, payments stay off). Chapter 4 stays locked.
- The gate found and fixed: the Chapter 2 aisle sign stopped on a script error (`merge_static` on primitive meshes); `tap_map --hud-check` without `--views` checked 0 views and still printed 0 failures (now `--views=all`, and a check of no views fails); the perf loop was killed by the qa_run watchdog (now prints progress). Ch1 and Ch2 playthroughs now quit and Continue three times each.
- Next: the Chapter 4 gamer-eye review and its open items (small parts, the "forty-one" text, Leyla's chalk mark, coarse cage/tower texture, audio); Chapter 3 open items (ECG bracket signs, audio, the tubes → interlock stretch).

**State on 2026-10-10 (evening):**
- Test builds out: Android 0.1.0 (10) on Play internal testing (completed, 39 testers) and TestFlight build 7 (VALID). Both carry the fixes for the owner's Chapter 1 phone report: the bag, taps through the HUD, Panel 7 framing, the Back order, the hint ladder, the UV light, the notebook icons and the safe clue chain. Verified on main: Ch1 playthroughs (seeds 4242 and 1337) and Ch2 (both lens paths) with 0 fallbacks and 0 taps under a HUD control; tap_map `--hud-check` with 0 failures on 36 Ch1 and 34 Ch2 views; 151 tests, 0 failures.
- Chapter 3: every model is built (groups A–H) and integrated, with 0 fallbacks on both key paths (strand 102 taps, leyla 100) and Continue passing. Draw calls are at most 145 (choir_s) with the HUD.
- Chapter 4: design, logic, solver and tests are done (24 tests, 16 profile combinations to 3 endings). The model contract is `docs/models/ch4.md`.
- Apple: the Paid Apps agreement, banking and tax forms are active. Price decision: `full_game` $4.99.

**Owner requests tracker (2026-10-10; keep it current, nothing may drop):**
| Request | State |
|---|---|
| Text readability, Normal / Large / XL, overlap-free HUD | done |
| Inventory bag, taps through the HUD, Android Back order, 3-level hints, soft UV page | done (Android 10 / TF 7) |
| Panel 7 framing, notebook icons, safe → poster clue | done |
| Panel 7 different on every phone (wiring variants) | done (8 wirings; Android 11 / TF 8) |
| Home-screen name "Mystery Room" (iOS and Android) | done |
| App icon A / B / C | waiting: the owner's choice (B recommended) |
| Six localization terms | waiting: the owner (LOCALIZATION_REVIEW.md) |
| Bloom and dark spots in Ch1 and Ch2, mechanism feedback | done |
| iOS black screen on New Game | iOS starts at safe level 1 (no MSAA); the 3 crashes Apple shows are on build 5; waiting for the owner's iPhone test of TF 9 |
| Menu gear box alive and opening (The Room style) | done (Android 11 / TF 8) |
| Premium language screen, captivating first 3 minutes | done (Android 11 / TF 8) |
| Credits (Yuldashali Abdurakhmonov & Aliyorbek Toshtemirov) and licenses | done (Android 11 / TF 8) |
| Chapters 1–2 free, full_game ($4.99) → Chapters 3–4 | done (code, docs, App Store Connect texts) |
| Chapters 1–2 "better than The Room", Chapter 2 cliffhanger | done (engagement pass and cliffhanger; Android 11 / TF 8) |
| HUD draw calls | done (3–8 calls) |
| Chapter 3: models, scene, dressing | done; gamer-eye review done; open to testers (Android 12 / TF 9) |
| Chapter 4: design, logic, tests | done; models A–I and the scene done (16 profiles → 3 endings, 0 fallbacks); unreleased until its gamer-eye review |
| Release gate before every test build | done (docs/RELEASE_GATE.md; first full run for Android 12 / TF 9) |
| Google Play product, License testing, service-account permission | waiting: the owner (bank verification pending) |
| Apple Small Business Program, EU DSA trader status | waiting: the owner, before release |
| Weekly store statistics report | after the public release |
| Google Play closed testing | approved by the owner 2026-10-11; release 0.1.0 (13) in Google's review; 12 testers × 14 days still to run (docs/release/GOOGLE_PLAY_TESTING.md) |
| TestFlight external testing | prompt ready (docs/store/CLAUDE_PROMPT_TESTFLIGHT_EXTERNAL.txt), build 10; waiting for the owner's assistant |
| Production, public release | each needs a separate approval |

**QA fixes (2026-10-10):**
- Done:
  - Chapter 3 ring marks are proper outlines (lib_ch3_symbols holes; 7 models rebuilt).
  - Glass-floor signs are about 8.5 mm on a phone.
  - Chapter 2 hall: 153 → 133 draw calls.
  - Tap assist: Chapter 3 controls under 9 mm, 54 → 7.
- Done 2026-10-11 (Chapter 3 player-experience pass, `docs/ENGAGEMENT.md` → "Chapter 3"): the shutter crystals and the prism buttons have their own tap boxes and the shutter view is reframed (tap-size: 0 controls under 9 mm with the assist at their best view); the glass-floor signs are cream with a dark rim on dark glass. The same pass fixed a seed-library coin flip in every per-game variant, Continue on a finished save, and staged the first look, the recorder, the door roll and the Array's answer. Its verdict: ready for closed testers.
- The Chapter 3 release candidate is ready for closed testing (hud-check 0 failures on phone and tablet, rendered strand and leyla runs with 0 fallbacks, Continue passes, 300-game logic sweep clean). It is not yet ready for a public release until a phone check of the desk levers, the hook key and Continue.

**Running now:**
- Ch3 set dressing (camp, shutter corridor, memorial gallery, grime): Sonnet agent;
- Ch4 models, groups A and B (shell, bridge, catwalk, master desk, panel 0): Sonnet agent;
- store purchases: done on main (2026-10-10, `docs/MONETIZATION.md`). StoreKit 2 + Play Billing providers, purchase screen, `store_sandbox` builds; `ios-iap.yml` and `play-iap.yml` written with `dry_run` default true and **not dispatched**; REAL_PAYMENTS_ENABLED stays false.

**Next in the queue:**
1. The owner's device check of Android (10) and TestFlight 7. On iOS: does New Game reach the room? If not, get a screenshot of the menu's "safe N / last stop" line.
2. HUD draw calls: the HUD costs about 60 draw calls in every view, which leaves choir_s 5 calls of margin. Batch the HUD (shared StyleBoxes, fewer separate CanvasItems, no per-button shader) before Chapter 4's hall.
3. Chapter 4: models C–I, then the scene (`array_hall_room.gd`, views, culling, lights) and `playthrough_ch4` across the 16 profile paths.
4. Chapter 3 release candidate: a rendered playthrough on both paths after the set dressing, the phone-brightness check, then `released: true`.
5. The store purchase flow (`docs/MONETIZATION.md` → "Testing purchases"): `ios-iap.yml` dry run → review → `dry_run=false`; `ios.yml store_sandbox=true beta_unlock=false` (first macOS run with the StoreKit plugin) → TestFlight sandbox test. Play: after the owner's §11 steps (`docs/release/GOOGLE_PLAY_TESTING.md`), one `android.yml include_billing=true` draft upload, `play-iap.yml` dry run → apply, then a `store_sandbox` build for License testers only.

**Waiting on the owner:**
1. The app icon variant: A, B or C. B is recommended (`docs/brand/icon_variants/`).
2. Six localization terms (`docs/LOCALIZATION_REVIEW.md`).
3. Google Play: the payments profile and bank account (the helper is on it), License testing, and the service-account permission for in-app products.
4. Apple Small Business Program enrolment (15% commission), at developer.apple.com.
5. EU DSA trader status, before any EU release.
6. Closed testing invitations, production and public release: each needs a separate approval.
7. The Chapter 2 cliffhanger (`docs/ENGAGEMENT.md` → "For the owner's judgment"):
   - keep Strand's line on Leyla's tape, or end on hers?
   - record real voices for the tape;
   - the wording of the Chapter 3 card's hand-off, and whether its price shows on the card.

## Launch: Instagram and YouTube in EN, RU and UZ (owner, 2026-10-11)
- At release, post on Instagram and YouTube in all three languages. The owner posts from their own accounts; nothing is posted by us.
- To prepare: a 30–60 s trailer per language (gameplay captured with Godot's movie writer, so picture and sound are the game's own; on-screen text and captions in that language), 3–5 short vertical clips (Reels / Shorts) of the strongest moments (UV page, the beam lock, the tape voices, the Array waking), a cover image, and the post texts in EN/RU/UZ.
- Only original or CC0 material (music and sound from the game itself).

## Game
00. **Player-behaviour QA before the next release (owner, 2026-10-11: "no errors, a real puzzle, not too easy"):** the solver only walks the right path. Add a chaos pass per chapter: every tap target in every view in random order, with a random item in hand, wrong codes, back and forth, a hint at every step; it must never block, soft-lock or log an error. Then a fresh-eyes player review per chapter (texts, where one gets lost, difficulty: no answer given away without a hint). The hint dialog should name where the next step is (a short place name per goal, EN/RU/UZ).
0. **Small parts, read without a pinch (owner, 2026-10-11):** Panel 7's switches (~3.5 mm), I–V numerals (1.6 mm) and traces (0.3 mm) on a 20:9 phone. A pinch now magnifies every close-up up to 2.5×; next, make the plate itself readable: larger switch plates, lamps and numerals and thicker traces (tools/blender panel7 + tools/textures/make_decals.py panel, tap areas in lab7_room.gd), then the same audit for every close-up with small parts (`tap_map --tap-size`, Ch4's small parts).
1. **Chapter 2 release:** finish the player review (agent), fix its findings, then set `released: true` for ch2 in `game/src/core/chapters.gd` and update `test_premium_rules`. Tester builds already open it through the `beta_unlock` export feature.
2. **Chapter 2 performance:** done for the budget: the hall view is 144 draw calls / 86k primitives. Next is FPS on real phones: the debug build's FPS line, then `tap_map --breakdown` for any view that drops.
3. **Chapter 3:** the model contract `docs/models/ch3.md` (agent), then the Blender build agents (2–3 at a time), the scene, variants (docs/VARIANTS.md list) and a real-scene playthrough on both Chapter 2 key paths.
4. **Lighting (directive 1B):** before/after real renders of the over-bright spots (the splicer light box, the projector beam haze); storytelling props that never hide puzzle items (1C).
5. **Chapter 1:** a full player review on the rendered build after the UI audit; minute-by-minute pacing notes (30 s, 1, 2, 3, 5, 10 min).
   - First minutes: check on a real phone how long the loading black lasts between the menu transition and the first card (the container cannot tell), whether the knob taps on the menu box feel right with a thumb, and the haptics on the slam; then play the end credits after the Chapter 4 finale (`CreditsScene.play(...)`, not wired yet).
6. **Real-device test:** `docs/TESTING_ON_DEVICE.md` with the first tester build. Engagement questions for the first playtest are in `docs/ENGAGEMENT.md` (the mirrors, the vault after the clunk, the whisper, the cliffhanger: watched through or tapped past).
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
