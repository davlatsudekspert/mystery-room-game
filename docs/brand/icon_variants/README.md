# App icon variants (for the owner to choose)

The shipped icon is **not** changed. Nothing here is in `game/assets/`. The owner picks one; then it is copied in (see "Adopting a variant").

All three variants use the same artwork, the same gold and dark teal palette, the same background and the same glow. Only the emblem (the eye, the lens, the door and the light) is scaled up around the icon centre. There is no text in any icon. Regenerate everything with `python3 tools/ui/make_icon_variants.py` (it cuts the emblem from `docs/brand/logo_source.png` with the same code as `tools/ui/make_logo_variants.py`, and it checks that A is byte-identical to the shipped icon).

| | Emblem | iOS 1024 (RGB, no alpha) | Android adaptive (432) | Themed (432) |
|---|---|---|---|---|
| **A** current | x1.00 | `A_ios_1024.png` | `A_adaptive_fg_432.png`, `A_adaptive_bg_432.png` | `A_monochrome_432.png` |
| **B** +15 % | x1.15 | `B_ios_1024.png` | `B_adaptive_fg_432.png`, `B_adaptive_bg_432.png` | `B_monochrome_432.png` |
| **C** +20 % | x1.20 | `C_ios_1024.png` | `C_adaptive_fg_432.png`, `C_adaptive_bg_432.png` | `C_monochrome_432.png` |

Previews: `home_screen_preview.png` / `.jpg` (iPhone home screen at @3x, dark wallpaper, 180 px icons, plus a 120 px row), `android_launcher_preview.png` (circle and squircle masks, plus the themed icon), `small_sizes.png` (60 px and 120 px in real pixels, on dark and light, plus a 4x zoom of 60 px). The placeholder app tiles are drawn by the script (flat colours, abstract shapes, invented labels), with no real app logos.

## How each reads at small size

Measured on the renders (lens = the outer diameter of the gold ring round the glass sphere).

| | Lens at 1024 | Lens at 120 px | Lens at 60 px | Door-light core at 60 px |
|---|---|---|---|---|
| A | 457 px (44.6 % of the width) | 53.6 px | 26.8 px | 1.6 px |
| B | 526 px (51.3 %) | 61.6 px | 30.8 px | 1.8 px |
| C | 548 px (53.6 %) | 64.3 px | 32.1 px | 1.9 px |

- **A:** reads as "gold eye with a lit door", but the lens is only a bit more than a quarter of the 60 px icon and the door of light is under 2 px wide. At 60 px the fine ticks on the outer arc and the four small spikes turn into noise around a small centre.
- **B:** the lens, its gold ring and the door of light are clearly bigger and the cyan glow around the door survives at 60 px. The lids still have room, so the silhouette stays an eye. Looks calmer than A because the outer ornament takes less of the icon.
- **C:** the best raw numbers, but only 4 % more lens than B. The eye now fills the icon width, so it looks tight in the iOS mask and the side margins vanish.
- Judged on software renders only (nothing was run on a device). At 60 px all three read; B and C read clearly better than A.

## Edge cropping

The symbol is never cut: the lens, the door and the light, the gold ring, the lids and the bottom diamond stay whole in B and C. The script asserts that no emblem pixel is hard-cropped at the iOS icon edge (everything that runs past is faded), and that, for Android, every opaque foreground pixel lies inside the 72 dp window.

- **iOS, B:** the emblem is 1106 px wide on the 1024 canvas, so only the points of the two side spikes run past the edge and fade over the last 40 px. Both corner orbs stay whole, with their gold ending 22 to 24 px inside the edge.
- **iOS, C:** 1155 px wide. The side spikes and the two corner orbs lie in the last 84 px, where they fade into the dark (the visible gold stops 43 px from the edge), and the two lid points almost touch the edge. This is the outer ornament the brief allows to crop, but the eye corners are no longer complete.
- **Android adaptive, B and C:** the foreground is 15 % / 20 % larger, so the lens ring (radius 75 px / 79 px of the 66 dp safe circle's 132 px) and the door are safe. Ornament beyond the safe radius fades out between radius 126 and 150 px (the launcher shows a 144 px radius), so the orbs and spike tips dissolve instead of showing a hard edge. In a circle mask the eye corners reach the mask edge, as the spike tips of A already do.
- **Themed (monochrome):** the lens, the lid height and the door grow by the same factor; the width of the almond stays, because it already fills the safe zone.
- Fine ornament stays moderate: the same artwork, with the outer arc and spikes fading at the sides instead of being drawn as more detail.

## Recommendation: B

Use **B**. It gives the owner what was asked (the lens and door +15 %, 31 px instead of 27 px at 60 px), keeps the whole eye including both corner orbs inside the icon, and changes nothing else in the design. **C** is marginally larger, but it gains only 4 % over B and costs the corner orbs and the side margin. A is not the best: its centre is the smallest of the three. If the owner prefers the most whole outline, A; if the owner wants the biggest centre at any cost, C.

Before the owner decides, check the phone: put B (and C if wanted) on a test build and look at the real home screen, because the preview is software-rendered and the wallpaper is only an example.

## Adopting a variant (not done)

For B, copy `B_ios_1024.png` to `game/assets/ui/icon.png`, `B_adaptive_fg_432.png` / `B_adaptive_bg_432.png` / `B_monochrome_432.png` to `game/assets/ui/icon_adaptive_fg.png` / `icon_adaptive_bg.png` / `icon_monochrome.png`, and a 512 px resize of `B_ios_1024.png` to `docs/store/graphics/icon_512.png`; then `godot --headless --path game --import`, and set the same scale in `tools/ui/make_logo_variants.py` so a later regeneration does not bring A back. The App Store icon is the 1024 PNG with no alpha (B and C are RGB).

## Display name

**Verdict: the home-screen name is "Mystery Room", with a real space, on iOS and on Android.** Nothing was changed, and nothing in App Store Connect was touched.

**iOS**
- `game/project.godot` line 6: `config/name="Mystery Room"`. Lines 7 to 11: `config/name_localized` sets `en`, `ru` and `uz` to "Mystery Room" (ru and uz had no entry before build 3, which is why build 2 showed "MysteryRoom").
- `game/export_presets.cfg`, iOS preset (`[preset.2]`): it has no separate display-name option. Godot's iOS export takes the name from `config/name` and `config/name_localized`. The bundle name `MysteryRoom` (no space) is only the Xcode target and product name.
- `tools/ios/verify_xcode_project.py` (line 59: `--display-name` defaults to "Mystery Room"; lines 119 to 127): for every `*.lproj` it requires `CFBundleDisplayName = "Mystery Room"` in `InfoPlist.strings`; it also prints the build setting `INFOPLIST_KEY_CFBundleDisplayName` (line 99). CI runs it in the ubuntu job of `.github/workflows/ios.yml` (line 135) and fails the build otherwise.
- `.github/workflows/ios.yml` lines 202 to 207: the macOS archive step prints what the phone reads. Read from the GitHub Actions logs of the iOS builds (runs 37949596736 for build 3, 37953235100 for build 4, 37953997927 for build 5, 37960263841 for build 6): in each of them the archive printed `Info.plist CFBundleDisplayName=Mystery Room`, then `en.lproj`, `ru.lproj` and `uz.lproj: CFBundleDisplayName=Mystery Room`, and the Xcode project check printed `INFOPLIST_KEY_CFBundleDisplayName=Mystery Room` and `CFBundleDisplayName ['Mystery Room'] (expected 'Mystery Room')` for en, ru and uz. Build 4's export step failed, so it was never uploaded to TestFlight, but its archive printed the same lines. Builds 3, 5 and 6 are the TestFlight uploads.
- `docs/TESTING_ON_DEVICE.md` records the fix for the "MysteryRoom" report.
- Not yet confirmed on a phone after build 3: the owner's next look at the home screen is the only proof of what iOS actually draws.

**Android**
- The launcher label is `android:label="@string/godot_project_name_string"` in the export template's manifest (`src/main/AndroidManifest.xml` in `android_source.zip` of Godot 4.7.2). The string is written at build time into `res/values/godot_project_name_string.xml` and one file per language folder (the template ships 42 files, the default plus 41 languages, with placeholders that the build overwrites).
- The file that sets it is `game/export_presets.cfg`: `package/name="Mystery Room"` in the Android preset (line 39) and in the Android AAB preset (line 101). If `package/name` were empty, Godot (as far as I know) falls back to `config/name` in `project.godot`. `config/name_localized` (en, ru, uz) is the per-language override, and it is also "Mystery Room".
- Evidence from the real build: the release AAB of the latest Android run (38031221278, 2026-10-10) has, in `base/resources.pb`, 42 string values for `godot_project_name_string`, all "Mystery Room", and none reading "MysteryRoom" or "godot-project-name". The CI step "Verify the AAB" does not check the label, so this check is manual.

**Truncation on the iOS home screen**
- iOS cuts a long label with an ellipsis when it is wider than the icon's label area (roughly 76 to 80 pt on current iPhones, from experience rather than an Apple specification; it depends on the glyph widths, not the character count). The usual rule of thumb is about 11 to 13 characters.
- "Mystery Room" is 12 characters with ordinary letter widths, so it is expected to fit, but it is near that limit. A look-alike font (Inter, wider than the iOS system font) measures it at about 82 pt at 12 pt size, so on a smaller or zoomed display it could still lose its last letter. This cannot be settled without a device; if it does truncate, set `config/name` and `config/name_localized` to a shorter name for the home screen only.
- The App Store Connect name is a different field and is not affected by any of this.
