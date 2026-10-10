# Testing on a phone

## Getting a build
| Platform | Build | How to install |
|---|---|---|
| Android (fastest) | **Debug APK** from GitHub Actions: Actions → "Android build" → latest green run → Artifacts → `mystery-room-android-debug` | Download the zip on the phone, open `mystery-room-debug.apk` and allow "Install unknown apps" for the browser or file manager. Each CI debug build has its own key, so **uninstall the previous build first** |
| Android (store-like) | **Release AAB** (signed with the upload key) | Play Console → the app → Testing → Internal testing → upload the AAB, add testers' e-mails, then open the opt-in link on the phone. Installs from the Play Store, updates automatically |
| iOS | `ios.yml` → TestFlight | Needs the App Store Connect app record and an Admin API key (see RELEASE_PIPELINE.md). Testers install the TestFlight app |

Debug builds show **"FPS NN · 3D NN%"** under the pause button. Take a screenshot of it in heavy scenes, such as the room overview, the darkroom and the finale.

## Checklist: report anything that is not ✅
**First launch**
- [ ] The app icon looks right on the home screen, including round and themed icons on Android 13+.
- [ ] The home-screen name reads **Mystery Room** (with the space) in every phone language.
- [ ] The launch screen shows the game logo on the dark menu colour, never the Godot engine logo.
- [ ] The language picker preselects the phone's language (EN, RU or UZ). Other languages fall back to English.
- [ ] The main menu works, settings are readable, and the version is shown at the bottom right.

**Controls**
- [ ] A tap on an object moves the camera closer, and a second tap uses or takes it.
- [ ] Drag looks around in the room view. Pinch zooms.
- [ ] The Android **back** button or gesture:
  - closes the open window;
  - otherwise steps back from a close-up;
  - in the room view, opens Pause;
  - in the main menu, asks before quitting. It must never close the game directly.
- [ ] The two-finger tap also goes back.
- [ ] Small controls are easy to hit: drawer digits, safe keys, radio knob (drag it), projector rings, mirrors.

**Play through Chapter 1** (20–30 min) with hints when stuck. Note:
- [ ] any puzzle that felt unfair or unclear, and which hint level solved it;
- [ ] any text cut off or overlapping, in each language you try;
- [ ] audio (music, effects, radio static and beacon) and vibration;
- [ ] **continue**: close the app mid-chapter (swipe it away), reopen it and choose Continue. You must be in the same place with the same items.

**Performance and comfort**
- [ ] FPS in the room overview, darkroom and finale. The "3D %" value drops automatically on slow phones, and the image gets slightly softer.
- [ ] Load time from tapping New Game to the room. The black screen in between says "Loading…"; note how long it stays.
- [ ] Phone temperature after 15 minutes. Battery drain per 15 minutes.
- [ ] Notch and rounded corners: no button is hidden.

## What to send back
For each issue, send:
- the phone model and Android/iOS version;
- the language used;
- a screenshot (with the FPS line in debug builds);
- what you did just before the issue.

In tester builds the main menu's version line also names the graphics driver and renderer (for example
`metal mobile`, `vulkan mobile` or `opengl3 gl_compatibility`). Include it in a screenshot with any rendering issue.

## Device reports
| Date | Device / build | Report | Status |
|---|---|---|---|
| 2026-10-09 | iPhone, TestFlight 0.1.0 (2) | The launch screen showed the Godot engine logo | Fixed in build 3: the export used Godot's default image because no launch images were set. The launch storyboard now shows the game logo (`game/platform/ios/launch@2x/3x.png`), and `tools/ios/verify_xcode_project.py` fails the build if it falls back again |
| 2026-10-09 | iPhone, TestFlight 0.1.0 (2) | The home-screen name read "MysteryRoom" | Fixed in build 3: `config/name_localized` gives "Mystery Room" to every language's InfoPlist.strings (ru/uz had none). The Xcode project check enforces it, and the archive step prints what the phone reads |
| 2026-10-09 | iPhone, TestFlight 0.1.0 (5) | New Game: "Loading…" stays, then a crash. Relaunch: menu reads `metal mobile · last stop: load:lab7 · safe`, and with safe graphics on it crashed again | Safe graphics were applied one frame too late (the scene change is drawn in the same frame). Build 6: rooms apply them in `_ready` (`SceneManager.room_ready`); the levels rise one per crash (1 no MSAA, 2 also no shadows/probes/particles, 3 also no decals/glow/sun shadow); "last stop" names the model or step |
| 2026-10-10 | iOS Simulator on GitHub (ios-sim.yml) | Cannot reproduce: GitHub's VMs give the Simulator no Metal device, so Godot falls back to OpenGL (software) | The workflow is kept as a smoke test (build, boot, menu, logs) only |
| 2026-10-09 | iPhone, TestFlight 0.1.0 (2) | New Game: black screen with the chapter music and nothing else | Open. The room had loaded (its music started), so the first frames were not drawn, or were drawn very late. Most likely the phone compiled the room's shaders on first run. Build 3 shows "Loading…" until the room's first frames are drawn, and names the renderer in the menu. Next: the owner's timing on build 3, then baking shaders for Metal at export (the Godot shader baker needs a macOS export) |
| 2026-10-10 | Android phone, Play internal 0.1.0 (7) | The main lever on Panel 7 could not be tapped: the bottom inventory bar took the taps. The four lamp icons were cut off at the top. The notebook's "LOCK, LIGHT, ARRAY" (UZ "Panjara") did not map to the icons. The hints felt too weak. Android Back moved the camera instead of putting the held item away. The UV page showed a hard pink rectangle | Fixed in Android 0.1.0 (10) and TestFlight build 7 (main fcd5684). The inventory folds into a bag (bottom left), and only buttons take taps (`HUD.blocked_rects()`). Panel 7 is framed whole at 16:9 / 19.5:9 / 20:9 / 4:3. Notebook page 4 shows the panel icons inline. Hints read "Hint N of 3" → "Show the answer (3/3)", and level 1 names the object (the safe's names the poster). Back unwinds overlay → held item → bag → camera. The UV light is soft. Verified by tap_map `--hud-check` (Ch1 36 views and Ch2 34 views, 0 failures) and the playthroughs (Ch1 seeds 4242/1337, Ch2 both lens paths: 0 fallbacks, 0 taps under a HUD control). Waiting for the owner's device check |
