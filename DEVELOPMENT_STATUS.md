# Development Status

_Last updated: 2026-10-09_

| Phase | Status | Verified evidence |
|---|---|---|
| 0 — Audit, architecture, story, art direction, puzzle graph | ✅ Done | `docs/` (STORY, PUZZLE_DESIGN, DESIGN_PILLARS, ART_DIRECTION, ARCHITECTURE, ROOM_LAYOUT) |
| 1 — Godot project + core logic + tests | ✅ Done | `tools/run_tests.sh`: **92 tests, 8120 checks, 0 failures** (locally, 2026-10-09). The 300-seed random-play fuzz finds no softlock or lost item |
| 2 — Assets: textures, fonts, audio, models | ✅ Done for Chapter 1 | 36 procedural Blender models (room shell, door, furniture, devices, items, two light-echo figures) · 14 CC0 Poly Haven props · 20 texture sets / 71 materials · 3 OFL fonts (coverage checked) · 40 original synthesized sounds + 1 CC0 sound. GLB node names are checked against Godot import hints (`tools/blender/check_glb_names.py`) |
| 3 — Interactive room & puzzles | ✅ Chapter 1 playable end to end | `lab7.tscn` with HUD (inventory with 3D icons, inspect, notebook with UV page, hints, pause, choice, chapter complete) and a touch camera. **`qa/playthrough.tscn` completes Chapter 1 entirely through taps on the real 3D scene: 13/13 steps plus 5/5 optional Lumen shards, 0 logic fallbacks** (see "QA playthrough" below) |
| 4 — Polish, UI, sound | 🔶 In progress | State-aware captions, drag-to-tune radio, soft dust motes, 1979 flashback staging, bookcase reveal camera. **2026-10-09:**<br>• the owner's logo is integrated: EN/RU/UZ subtitle on the main menu, app icons (adaptive, monochrome, iOS, store 512), home-screen previews in `docs/previews/logo/`;<br>• the unpowered Chapter 1 lab gets a moonlight bounce, so its dark corners are readable (`docs/previews/ch1_dark_state_before_after.jpg`);<br>• a Brightness setting;<br>• a privacy-policy link in Settings;<br>• a premium main menu: the gear box as the lit hero on the desk (wheels turning, slow camera drift), serif text items with a gold rule, vignette and logo glow, a staggered entrance; phone-GPU safe (`docs/UI_UX.md` → Main menu, `docs/previews/ui/menu_before_after.jpg`) |
| 5 — Localization & tests | ✅ Done for Chapter 1 | 299 keys EN → RU → UZ. The validator checks Uzbek Latin only, placeholders and font coverage. Layout-fit test at text scale 1.3. UI screenshots in all three languages (`qa/ui_screens.tscn`) |
| 6 — Android build | 🔶 Ready for device testing | Debug APK from CI. Checked on the exported APK: target SDK 36 (the Play requirement since 2026-08-31), 16 KB native alignment, VIBRATE as the only permission, Vulkan optional with GL fallback, adaptive and monochrome icons, landscape. The back button never quits. PerfGuard scales the 3D resolution on slow phones. The upload key exists (outside the repo); the release AAB uses Gradle. **Not yet tested on a physical device**: see `docs/TESTING_ON_DEVICE.md` |
| 7 — iOS preparation | ✅ First TestFlight build | **2026-10-09:**<br>• build 0.1.0 (2), with `beta_unlock`, was uploaded to TestFlight (`ios.yml` run 37941801214) after the owner's approval;<br>• Apple processing: `VALID`;<br>• internal testers are added by the owner;<br>• details and the owner's next steps: `docs/release/IOS_TESTFLIGHT.md`.<br>The pipeline: ubuntu (ASC gate, tests, Godot Xcode export + static checks), then macOS (Xcode 26.3 / iOS 26.2 SDK, unsigned archive, cloud-signed App Store export) |
| 8 — Store & monetization | 🔶 Partly | Purchase abstraction (mock/disabled providers), real payments disabled. `docs/MONETIZATION.md`, `docs/STORE_LISTING.md` (EN/RU/UZ), `docs/RELEASE_PIPELINE.md` |

## Chapter 2 (in progress)
- **Logic:** P1–P12, both Chapter 1 lens paths, and the solver and no-softlock tests in `tools/run_tests.sh`.
- **Room scene:** `archive.tscn` with 41/41 models (`docs/models/CH2_MANIFEST.md`).
- **Real 3D playthroughs** (`qa/playthrough_ch2.tscn`, taps through the room's raycast):
  - leave path: 86 taps, 0 fallbacks;
  - take path: 78 taps, 0 fallbacks;
  - variant seed 777: 94 taps, 0 fallbacks.
  Screenshots are in `docs/previews/ch2/`.
- **Audio:** 42 sounds, the ambience and 2 music cues.
- **Decals:** 28 decals; the ones with words exist in EN, RU and UZ and are swapped at runtime by `DecalLoc`.
- **Not yet done:** the player-style review (an agent is running it); then `released: true`.
- **Performance:** the hall view measures 144 draw calls / 86k primitives (budget 150 / 150k; was 213 / 152k). Dust no longer casts shadows: as a moving caster it forced a shadow-map redraw every frame. Shelf contents and the book row are merged into one mesh each. `tap_map --breakdown` lists what each model, mesh and shadow costs.

## Per-game puzzle variants (anti-walkthrough)
`docs/VARIANTS.md`. **On for players since 2026-10-09** (`GameState.variant_seed = -1`). Every new game draws its own answers, the evidence on screen follows them, and story anchors (03:17, 1979, 0417) stay fixed. The seed is saved with the game, and Continue keeps it (tested).
- **Chapter 1:** the gear-box start, the safe cipher glyphs (code = the poster's dots), the beacon numbers and the book order. Real-scene playthrough on seed 4242: safe 1204, books IV-II-VIII, 100 taps, 0 fallbacks; the evidence was checked on screen (`docs/previews/variants/`).
- **Chapter 2:** the gauge marks (valve answer), index-card notches (8 card arts × 3 languages), tape clicks and booth dial, splice order, focus mark and vault engraving (drawn in the shader). Real-scene playthrough on seed 777: 94 taps, 0 fallbacks.
- **Hints:** level-3 hints name the player's own answer.
- **Tests:** 60-seed tests (solvable, unique, saved, reproducible).
- **QA scripts** use seed 0 (canonical) unless given `--seed=N`.

## Tester builds
Exports with the custom feature `beta_unlock` open every released chapter without a purchase (`Premium.tester_build()`), so internal/closed testers and TestFlight testers can play Chapter 2+ while real payments stay disabled. Store releases never carry the feature.

## Organisation
The director plus parallel agents: Android/Google Play, iOS/TestFlight, QA and visual/UI. See `NEXT_STEPS.md`. Nothing is uploaded to a store and no tester is invited without the owner's approval.

## UI readability and redesign (2026-10-10)
The owner's iPhone screenshots showed text that was too small, too dim or too crowded, a settings panel that overflowed, and a plain HUD. Done (`docs/UI_UX.md` → Design tokens, Settings, HUD, Reader):
- **Text size:** three presets, Normal / Large / Extra large (1.0 / 1.25 / 1.5; old saves snap to the nearest). Body text now targets a **3.0 mm cap height** at Normal on any phone or tablet (auto scale up to 3.2×, about 2.7× on the owner's 460 dpi iPhone); nothing the player must read is below 3 mm em; titles keep leading body text. Panels drop to one column and scroll under edge fades, segmented controls stack, button rows wrap, and a newer HUD banner fades an older one it would cover, so nothing overlaps at Large or Extra large.
- **Contrast:** muted text lifted (b5ab97); every line over the 3D scene sits on a 0.8-alpha dark band or plate (≥ 4.5:1 even over a white frame).
- **Reader:** every document, note, diary page, photograph and worded decal opens full screen on a paper plate at reading size, in the current language; pictures pinch / double-tap to zoom. The poster, the chalkboard (Ch1) and the routing chart (Ch2) open in it on a second tap of their close-up; Ch3's note, letters and growth log use it too.
- **Settings panel:** dark plate with a hairline gold frame, LANGUAGE / SOUND / DISPLAY & COMFORT / OTHER sections, one row height (9 mm), switches with their state in words, thin gold sliders with readouts, segmented language and text size, a pinned footer, a body that scrolls under soft fades. Built headless in `test_layout.gd` on the iPhone, a 16:9 phone and a tablet at Normal and Extra large in EN / RU / UZ.
- **HUD:** banners (small-caps serif title between gold flourishes over a rule, subtitle below, soft dark band) for the view title, captions, messages, the prompt and "item found" (icon, name, description); the inventory as a column on the left beside a vertical gold rule, with Inspect / Combine beside the selected slot; bezel buttons: Back top left, Hint top right, Pause (roman II) bottom right; the intro between gold rules; dialogs with the title over a gold rule and small-caps buttons.
- **Verification:** `qa/ui_screens.tscn` on the iPhone profile (2556×1179 @ 460 dpi, 177 / 63 px insets) at Normal, Large and Extra large in EN / RU / UZ (0 layout issues), the headless layout tests, and a Chapter 1 playthrough. Previews: `docs/previews/ui/settings_before_after.jpg`, `hud_before_after.jpg`, `settings_phone_{en,ru,uz}.jpg`, `hud_item_found_{en,ru,uz}.jpg`.

## Chapter 3
Design: `docs/CHAPTER3_DESIGN.md`; model contract: `docs/models/ch3.md`. The logic is complete with per-game variants (102 tests). The scene (`game/src/rooms/underground/`) is integrated: layout, the 65 views with captions, zone culling and portal cards, lights, environment and zone tones, the lift-descent intro, hotspot routing for every puzzle, variant evidence surfaces, echoes, hints and Continue. `qa/playthrough_ch3` plays the whole chapter by real 3D taps on both Chapter 2 key paths; on 2026-10-10 every remaining fallback was for a model group not built yet (B, E, F and part of D). Draw calls are 27–90 per view without those groups. Unreleased (`released: false`). Details in `docs/GAMEPLAY_QA.md`, "Chapter 3".

## Chapter 4
Design: `docs/CHAPTER4_DESIGN.md` (the Array Hall: Panel 0, Strand's box, the Sun's arc and iris, the four coupled rings, the Reliquary around the Core, the chronometer replay and the minute-by-minute reversal of the Night; three endings from the Chapter 1–3 choices, four echoes, the parcel secret). Logic: `game/src/rooms/array_hall/array_hall_logic.gd` with per-game variants for every code-like puzzle (panel matrix, box start, green band, iris order, orrery marks, the Night's minutes, the keeper's note), a solver and 24 tests (every puzzle, wrong inputs, 60-seed variants, save round trips, all 16 profile combinations and the three endings, the fuzz, string completeness and the safe-registration check). Strings EN/RU/UZ in `tools/localization/strings_ch4.py`. Registered in `chapters.gd` with its logic and an empty scene path; `released: false` keeps it locked ("Coming soon") in the chapter select and off the chapter-complete card, because both only offer a chapter when `Premium.can_play` is true. No scene or models yet. Details in `NEXT_STEPS.md`, "Chapter 4".

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
- ✅ `ios.yml` uploaded build 0.1.0 (2) to TestFlight on 2026-10-09, and it is `VALID`.
  - It runs on macOS, where 1 minute counts as 10 against the free quota. Two runs so far used 6 macOS min (60 min of quota).
  - The upload job showed a false failure (an `ls` of a folder that does not exist in upload mode). It is fixed in `0bf16db`; the fix has not been run yet.

## Known limitations
- The dev container has no GPU. Screenshots use software Vulkan (lavapipe), so FPS measured here does not represent phones.
- There is no macOS here. The iOS archive, signing and upload were verified on GitHub macOS runners (runs 37920931317 and 37941801214).
- No physical Android or iOS device has been tested yet.
- Under heavy CPU load (several Blender builds at once), software Vulkan under Xvfb sometimes deadlocks or hangs on exit. Headless runs of the same scenes do not, so this is the container, not the game. Run QA scenes through `tools/qa_run.sh`, which uses the `QA_DONE` marker and restarts stalled runs.
