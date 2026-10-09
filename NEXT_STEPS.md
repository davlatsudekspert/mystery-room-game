# Next Steps

1. **Chapter 2 integration:**
   - finish the last models (`docs/models/CH2_MANIFEST.md`);
   - fix the tap problems the tap map shows (`qa/tap_map.tscn`);
   - run `qa/playthrough_ch2.tscn` with `--lens=take` and with `--lens=leave` until there are 0 fallbacks;
   - play it like a player: first 30 s, dry spells, hints, save/continue, both endings;
   - take real Godot screenshots (overview, mechanism close-ups, phone frame, dark/light);
   - then set `released: true` for ch2 in `game/src/core/chapters.gd`.
2. **Chapter 1 regression:** re-run `qa/playthrough.tscn` and `qa/player_review.tscn` after the lighting change. The review script now aims like a player: it taps visible parts and pulls the drawer by its side.
3. **Real-device test:** run the checklist in `docs/TESTING_ON_DEVICE.md` with the CI debug APK, then fix what shows up.
4. **Release signing:**
   - Android: the owner adds the 3 `ANDROID_*` secrets, then run `android.yml` with release and upload the first AAB by hand to Play internal testing.
   - iOS: the API key needs the Admin role.
5. **Play Console:** finish the remaining declarations and the store listing.
6. **Logo rights:** the owner confirms where the logo artwork came from and that it may be used commercially (`docs/ASSET_LICENSES.md`).
7. **Chapter 3:**
   - turn `docs/CHAPTER3_DESIGN.md` into the logic, solver and tests;
   - write the model contract `docs/models/ch3.md`;
   - start the build agents.
8. **Performance pass:** Chapter 1 has ~175–183k primitives against a 150k target. Use LODs and fewer shadow casters.
