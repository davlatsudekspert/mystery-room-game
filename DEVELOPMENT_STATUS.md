# Development Status

_Last updated: 2026-10-08_

| Phase | Status | Verified evidence |
|---|---|---|
| 0 — Audit, architecture, story, art direction, puzzle graph | ✅ Done | `docs/` (STORY, PUZZLE_DESIGN, DESIGN_PILLARS, ART_DIRECTION, ARCHITECTURE, ROOM_LAYOUT) |
| 1 — Godot project + core logic + tests | ✅ Done | `tools/run_tests.sh`: **41 tests, 2491 checks, 0 failures**. The 300-seed random-play fuzz finds no softlock or lost item |
| 2 — Assets: textures, fonts, audio, models | ✅ Done for Chapter 1 | 36 procedural Blender models (room shell, door, furniture, devices, items, two light-echo figures) · 14 CC0 Poly Haven props · 20 texture sets / 71 materials · 3 OFL fonts (coverage checked) · 40 original synthesized sounds + 1 CC0 sound. GLB node names are checked against Godot import hints (`tools/blender/check_glb_names.py`) |
| 3 — Interactive room & puzzles | ✅ Chapter 1 playable end to end | `lab7.tscn` with HUD (inventory with 3D icons, inspect, notebook with UV page, hints, pause, choice, chapter complete) and a touch camera. **`qa/playthrough.tscn` completes Chapter 1 entirely through taps on the real 3D scene: 13/13 steps plus 5/5 optional Lumen shards, 0 logic fallbacks** (see "QA playthrough" below) |
| 4 — Polish, UI, sound | 🔶 In progress | State-aware captions, drag-to-tune radio, soft dust motes, 1979 flashback staging, bookcase reveal camera. Lighting review continues |
| 5 — Localization & tests | ✅ Done for Chapter 1 | 299 keys EN → RU → UZ. The validator checks Uzbek Latin only, placeholders and font coverage. Layout-fit test at text scale 1.3. UI screenshots in all three languages (`qa/ui_screens.tscn`) |
| 6 — Android build | 🔶 Debug APK built locally | Signed arm64 debug APK, `apksigner verify` OK, ~123 MB, with the mobile texture policy (ETC2/ASTC, mipmaps, size limits). **Not yet tested on a physical device** |
| 7 — iOS preparation | 🔶 Ready to run, unverified | The Xcode project export was verified on Linux (scheme `MysteryRoom`, bundle `com.mysteryroom.forgotteninstitute`, automatic signing, iOS 15). The owner has added `IOS_TEAM_ID` and the `ASC_*` secrets. `ios.yml` has not run yet: it needs the App Store Connect app record, and GitHub Actions must start jobs again |
| 8 — Store & monetization | 🔶 Partly | Purchase abstraction (mock/disabled providers), real payments disabled. `docs/MONETIZATION.md`, `docs/STORE_LISTING.md` (EN/RU/UZ), `docs/RELEASE_PIPELINE.md` |

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
| Primitives | ~183k | ~175k |
| Video / texture memory | 412 / 357 MB | 422 / 361 MB |
| Scene build time | ~6 s (llvmpipe CPU renderer) | |

Budget: ≤ 150 draw calls (OK). Primitives are about 20% over the 150k target, and LOD/occlusion work is planned. The texture memory figure is for uncompressed desktop textures; phones use ETC2/ASTC.

## CI status
- `tests.yml`, `android.yml` and `ios.yml` are manual (`workflow_dispatch`), within the free quota only.
- On 2026-10-08 (18:40 and 18:46 UTC) the Android and Tests runs ended after 3 s with no runner assigned and no logs. That is the GitHub account billing lock signature, so the workflows themselves have not executed yet.

## Known limitations
- The dev container has no GPU. Screenshots use software Vulkan (lavapipe), so FPS measured here does not represent phones.
- There is no macOS here, so the iOS archive and upload steps cannot be verified in this environment (the Xcode project export can be).
- No physical Android or iOS device has been tested yet.
