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
- [ ] Load time from tapping New Game to the room.
- [ ] Phone temperature after 15 minutes. Battery drain per 15 minutes.
- [ ] Notch and rounded corners: no button is hidden.

## What to send back
For each issue, send:
- the phone model and Android/iOS version;
- the language used;
- a screenshot (with the FPS line in debug builds);
- what you did just before the issue.
