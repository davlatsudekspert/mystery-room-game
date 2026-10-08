# Next Steps

1. **Real-device test** of the debug APK: FPS, touch targets, load time, memory, audio, haptics. Then fix what shows up.
2. **GitHub Actions** (when jobs get runners again). Run `tests.yml` first, then the `android.yml` debug build, then `ios.yml` once the App Store Connect app record exists.
3. **Release signing**:
   - Android: create the upload keystore (owner decision pending) and add it as the `ANDROID_*` secrets, then build the release AAB and upload it to Play internal testing.
   - iOS: the API key needs the Admin role, because cloud-managed distribution certificates require it.
4. **Performance pass**: primitives ~175–183k, target 150k. Use mesh LODs on the heaviest props and simpler colliders where taps never happen.
5. **Lighting and polish pass**: the darkroom red mood, beam glow, finale timing. Add a short tutorial nudge if testers stall at the first drawer.
6. **Chapter 2** ("The Missing Scientist"): build on `docs/CHAPTER2_DESIGN.md` and the existing data hooks (`choices.ch1_lens`, `ch1_shards`).
