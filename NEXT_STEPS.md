# Next Steps

1. **Real-device test**: run the checklist in `docs/TESTING_ON_DEVICE.md` with the CI debug APK, then fix what shows up.
2. **iOS on GitHub Actions**: run `ios.yml` once the App Store Connect app record exists. `tests.yml` and the `android.yml` debug build already pass.
3. **Release signing**:
   - Android: the upload key is created. The owner adds the 3 `ANDROID_*` secrets. Then run `android.yml` with release, upload the first AAB by hand to Play internal testing, and automate later uploads with a service account.
   - iOS: the API key needs the Admin role, because cloud-managed distribution certificates require it.
4. **Performance pass**: primitives ~175–183k, target 150k. Use mesh LODs on the heaviest props and simpler colliders where taps never happen.
5. **Lighting and polish pass**: the darkroom red mood, beam glow, finale timing. Add a short tutorial nudge if testers stall at the first drawer.
6. **Chapter 2** ("The Missing Scientist"): build on `docs/CHAPTER2_DESIGN.md` and the existing data hooks (`choices.ch1_lens`, `ch1_shards`).
