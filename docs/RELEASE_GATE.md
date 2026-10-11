# Release gate for every test build (the director runs it, every time)

No build reaches testers until every line below has been run and has passed. A failed line stops the build, and the failure is reported, not hidden.

1. **Clean HEAD:**
   - make a detached worktree of the commit to be built;
   - `tools/run_tests.sh` → 0 failures;
   - `qa/check_scripts.tscn` → 0 broken;
   - `check_glb_names.py` → 0 reserved names.
2. **Real 3D play** of every released chapter, run by the director himself on a seed that no agent used:
   - rendered `playthrough*.tscn` → 0 fallbacks and 0 taps under a HUD control;
   - Continue works mid-chapter;
   - every variant answer matches what is on screen.
3. **Phone layout:** tap_map `--hud-check` at phone61 (19.5:9) and tablet10 (4:3) → 0 failures for every changed view.
4. **Phone speed:** tap_map `--perf` → every view ≤ 150 draw calls with the HUD.
5. **Look:** the director views the key screenshots (openings, reveals, endings, new or changed views) the way a The Room player would. Anything dark, floating, clipped, unreadable or over-bright stops the build.
6. **Store safety:**
   - `REAL_PAYMENTS_ENABLED = false` unless the owner approved otherwise in writing;
   - unreleased chapters stay locked;
   - no secrets in the diff.
7. **CI:**
   - the `android.yml` verify step passes (package, versionCode, target SDK, permissions, upload-key signature);
   - the `ios.yml` Xcode project check passes (display name "Mystery Room", launch images);
   - App Store Connect shows the build VALID, and Play shows the upload done.
8. **Record:** the build, its contents and the evidence go into `docs/TESTING_ON_DEVICE.md` before the owner is told.
