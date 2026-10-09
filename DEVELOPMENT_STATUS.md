# Development Status

_Last updated: 2026-10-09_

| Phase | Status | Verified evidence |
|---|---|---|
| 0 — Audit, architecture, story, art direction, puzzle graph | ✅ Done | `docs/` (STORY, PUZZLE_DESIGN, DESIGN_PILLARS, ART_DIRECTION, ARCHITECTURE, ROOM_LAYOUT) |
| 1 — Godot project + core logic + tests | ✅ Done | `tools/run_tests.sh`: **41 tests, 2494 checks, 0 failures** (locally and on GitHub Actions). The 300-seed random-play fuzz finds no softlock or lost item |
| 2 — Assets: textures, fonts, audio, models | ✅ Done for Chapter 1 | 36 procedural Blender models (room shell, door, furniture, devices, items, two light-echo figures) · 14 CC0 Poly Haven props · 20 texture sets / 71 materials · 3 OFL fonts (coverage checked) · 40 original synthesized sounds + 1 CC0 sound. GLB node names are checked against Godot import hints (`tools/blender/check_glb_names.py`) |
| 3 — Interactive room & puzzles | ✅ Chapter 1 playable end to end | `lab7.tscn` with HUD (inventory with 3D icons, inspect, notebook with UV page, hints, pause, choice, chapter complete) and a touch camera. **`qa/playthrough.tscn` completes Chapter 1 entirely through taps on the real 3D scene: 13/13 steps plus 5/5 optional Lumen shards, 0 logic fallbacks** (see "QA playthrough" below) |
| 4 — Polish, UI, sound | 🔶 In progress | State-aware captions, drag-to-tune radio, soft dust motes, 1979 flashback staging, bookcase reveal camera. **2026-10-09:**<br>• the owner's logo is integrated: EN/RU/UZ subtitle on the main menu, app icons (adaptive, monochrome, iOS, store 512), home-screen previews in `docs/previews/logo/`;<br>• the unpowered Chapter 1 lab gets a moonlight bounce, so its dark corners are readable (`docs/previews/ch1_dark_state_before_after.jpg`);<br>• a Brightness setting;<br>• a privacy-policy link in Settings |
| 5 — Localization & tests | ✅ Done for Chapter 1 | 299 keys EN → RU → UZ. The validator checks Uzbek Latin only, placeholders and font coverage. Layout-fit test at text scale 1.3. UI screenshots in all three languages (`qa/ui_screens.tscn`) |
| 6 — Android build | 🔶 Ready for device testing | Debug APK from CI. Checked on the exported APK: target SDK 36 (the Play requirement since 2026-08-31), 16 KB native alignment, VIBRATE as the only permission, Vulkan optional with GL fallback, adaptive and monochrome icons, landscape. The back button never quits. PerfGuard scales the 3D resolution on slow phones. The upload key exists (outside the repo); the release AAB uses Gradle. **Not yet tested on a physical device**: see `docs/TESTING_ON_DEVICE.md` |
| 7 — iOS preparation | 🔶 Ready to run, unverified | The Xcode project export was verified on Linux (scheme `MysteryRoom`, bundle `com.mysteryroom.forgotteninstitute`, automatic signing, iOS 15). The owner has added `IOS_TEAM_ID` and the `ASC_*` secrets. `ios.yml` has not run yet: it needs the App Store Connect app record (Actions runners work again) |
| 8 — Store & monetization | 🔶 Partly | Purchase abstraction (mock/disabled providers), real payments disabled. `docs/MONETIZATION.md`, `docs/STORE_LISTING.md` (EN/RU/UZ), `docs/RELEASE_PIPELINE.md` |

## Chapter 2 (in progress)
- **Logic:** P1–P12, both Chapter 1 lens paths, and the solver and no-softlock tests in `tools/run_tests.sh`.
- **Room scene:** `archive.tscn`. A headless logic-flow run (`qa/playthrough_ch2.tscn`) got from the start to P11 with the models available at the time. Fallbacks came from models still missing and from three tap problems now under investigation: catalogue cards vs. dividers, splicer framing, slide drawers.
- **Models:** see `docs/models/CH2_MANIFEST.md` (34 of 41 ready on 2026-10-09).
- **Audio:** 42 sounds, the ambience and 2 music cues.
- **Decals:** 28 decals; the ones with words exist in EN, RU and UZ and are swapped at runtime by `DecalLoc`.
- **Not yet done:** the full 3D playthrough on both lens paths, and real Godot screenshots. Per-chapter status levels are in `docs/GAMEPLAY_QA.md`.

## Per-game puzzle variants (anti-walkthrough)
`docs/VARIANTS.md`. Every new game draws its own answers; the evidence on screen follows them, and story anchors (03:17, 1979, 0417) stay fixed. The seed is saved with the game.
- **Chapter 1:** the gear-box start, the safe cipher glyphs (code = the poster's dots) and the beacon numbers (= the encyclopedia volumes).
- **Chapter 2:** the gauge marks (valve answer), index-card notches (8 card arts × 3 languages), tape clicks and booth dial, splice order, focus mark and vault engraving (drawn in the shader).
- **Hints:** level-3 hints name the player's own answer.
- **Tests:** 60-seed tests (solvable, unique, saved, reproducible) plus a real-scene Chapter 2 playthrough on seed 777 (94 taps, 0 fallbacks).
- **Off for now:** players still get the canonical answers (`GameState.variant_seed = 0`) until the Chapter 1 seeded run and the Chapter 2 player review finish.

## Chapter 3
Design draft: `docs/CHAPTER3_DESIGN.md`.

## QA playthrough (real 3D scene, software renderer)
`xvfb-run -a godot --path game res://qa/playthrough.tscn -- --out=<dir>` taps the projected screen position of each part. The tap goes through the same raycast → hotspot → logic path a finger uses. A step only counts when the expected state change happens, and wrong-direction taps fail. Any logic fallback is reported as a failure.

The QA work fixed these problems:
- **Drawer wheels never turned.** Godot's importer turns nodes named `*_wheel_N` into `VehicleWheel3D` and renames them. The wheels are now `IA_drawer_digit_N`, and a name check guards every GLB.
- **Drawer digits showed the wrong number.** The digits are now tilted to the seated eye line, so the lock window shows the digit that is actually set.
- **Small controls could not be tapped.** The coarse boxes of large interactive parts swallowed the taps; large parts now use exact trimesh colliders.
- **Mirror taps flipped direction.** The direction flipped as the mirror turned. Each tap is now one 45° click. The radio knob can be dragged.
- **The bookcase reveal camera sat inside the swing arc.** The camera is now outside it. The shard on top of the bookcase now moves with it, and collected shards are removed.
- **Two shards were unreachable.** One was buried inside the desk pedestal, and the other was hidden behind Panel 7's door. Both are moved and their views reframed.
- **Chapter-complete stats collapsed into a vertical letter stack.** Fixed.
- **Leyla's photograph used the letter model.** It now has its own model.

## Performance (software renderer in the container: indicative only)
| Metric | Lab root (dark) | After power |
|---|---|---|
| Draw calls | 94 | 99 |
| Primitives (including shadow passes) | ~183k | ~175k |
| Video / texture memory | 412 / 357 MB | 422 / 361 MB |
| Scene build time | ~6 s (llvmpipe CPU renderer) | |

Budget: ≤ 150 draw calls (OK). Primitives are about 20% over the 150k target. The count includes the moon and spot-light shadow passes; one instance of every model is 245k triangles in total, and the darkroom set (~31k) is culled while unseen. LOD and shadow-caster trimming are planned. The texture memory figure is for uncompressed desktop textures; phones use ETC2/ASTC.

## CI status (GitHub Actions, free quota, manual triggers)
- After the billing block was lifted, the first runs at 18:40 and 18:46 UTC still got no runner. From 19:24 UTC jobs run normally.
- ✅ `tests.yml` run 37831728496: 41 tests, 2494 checks, 0 failures (about 25 s).
- ✅ `android.yml` debug runs 37831976693 and 37832359209 (latest, commit 2a23bad): tests plus a signed debug APK. The latest artifact is 101 MB zipped and is kept for 7 days. The debug key is generated per run, so uninstall the previous build before installing a newer one.
- ⏳ `android.yml` release (AAB + Play internal testing) waits for the upload keystore secrets.
- ⏳ `ios.yml` waits for the App Store Connect app record. It runs on macOS, where 1 minute counts as 10 against the free quota.

## Known limitations
- The dev container has no GPU. Screenshots use software Vulkan (lavapipe), so FPS measured here does not represent phones.
- There is no macOS here, so the iOS archive and upload steps cannot be verified in this environment (the Xcode project export can be).
- No physical Android or iOS device has been tested yet.
- Under heavy CPU load (several Blender builds at once), software Vulkan under Xvfb sometimes deadlocks or hangs on exit. Headless runs of the same scenes do not, so this is the container, not the game. Run QA scenes through `tools/qa_run.sh`, which uses the `QA_DONE` marker and restarts stalled runs.
