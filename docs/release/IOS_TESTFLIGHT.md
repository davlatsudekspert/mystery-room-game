# iOS / TestFlight — MYSTERY ROOM

## Qisqacha (oʻzbekcha)
- App Store Connect'dagi **"Mystery Room: Lost Institute"** yozuvi topildi. Uning Bundle ID'si **com.mysteryroom.forgotteninstitute**. Bu repodagi ID bilan **bir xil**, shuning uchun hech narsani oʻzgartirish shart emas.
- API kaliti ishlayapti. Faqat oʻqish (GET) soʻrovlari yuborildi, App Store Connect'da hech narsa oʻzgartirilmadi.
- iOS build yoʻli tayyor:
  - Avval ubuntu'da arzon tekshiruvlar oʻtadi: App Store Connect tekshiruvi, testlar, Godot eksporti va loyiha tekshiruvi.
  - Keyin macOS'da Xcode 26 bilan imzolangan IPA yigʻiladi.
  - 2026-10-09 da sinab koʻrildi: macOS'da App Store uchun imzolangan IPA muvaffaqiyatli yigʻildi (build 1). U yuklanmadi.
- **2026-10-09: birinchi test build TestFlight'ga yuklandi** (sizning ruxsatingiz bilan). Versiya **0.1.0**, build **2**. Apple uni tekshirib boʻldi: holati **VALID**, yaʼni testga tayyor. Tafsilotlar va keyingi qadamlaringiz pastdagi "TestFlight upload" boʻlimida.
- Workflow'da yuklash standart holatda **oʻchiq** turadi. Har bir yangi yuklash uchun sizning ruxsatingiz kerak. Testerlarni oʻzingiz qoʻshasiz.
- Test buildlarda `beta_unlock` yoqilgan: pullik boblar toʻlovsiz ochiladi. App Store'ga chiqariladigan buildda u **oʻchiq** boʻlishi shart.
- App Store'da oʻzbek tilidagi sahifa (lokalizatsiya) **yoʻq**: Apple roʻyxatida oʻzbek tili mavjud emas. Oʻyinning oʻzi oʻzbekcha toʻliq ishlaydi. Ilova ichida `uz.lproj` bor, shuning uchun App Store sahifasidagi "Tillar" qatorida oʻzbek tili koʻrinishi kutiladi.
- Sizdan kerak boʻladigan qarorlar: nom, subtitr, kategoriya, maxfiylik URL, yosh reytingi va App Privacy. Ular pastdagi roʻyxatda.
- **Xarid `full_game` (2026-10-10):** StoreKit 2 kodi tayyor, haqiqiy toʻlovlar **oʻchiq**. App Store Connect'da mahsulotni `ios-iap.yml` yaratadi (standart holatda faqat koʻrsatadi, `dry_run=true`). Xaridni sinash uchun `store_sandbox=true` bilan TestFlight build: TestFlight'dagi xaridlar har doim sandbox, pul yechilmaydi. Bunday buildni **App Review'ga yubormang**. Tafsilotlar: pastdagi "In-app purchase" boʻlimi.

## TestFlight upload (2026-10-09): build 0.1.0 (2) is in TestFlight
The owner approved one internal TestFlight build on 2026-10-09.

| Item | Result |
|---|---|
| Run | `iOS build` [37941801214](https://github.com/davlatsudekspert/mystery-room-game/actions/runs/37941801214) (#2), `main` @ `1a64c69`, inputs `upload_to_testflight=true`, `beta_unlock=true` |
| Gate | bundle id registered=YES, app record uses it=YES. App Store Connect had 0 builds, so the build number is 2 (`max(0 + 1, run number 2)`) |
| Tests | `tools/run_tests.sh`: 95 tests, 8226 checks, 0 failures |
| Xcode project | version 0.1.0, build 2, `custom_features="beta_unlock"`. `verify_xcode_project.py`: "RESULT: all checks passed" |
| macOS | Xcode 26.3 (17C529), iOS SDK 26.2. `** ARCHIVE SUCCEEDED **` (unsigned) |
| Upload | `-exportArchive` with `destination=upload` and cloud signing logged `Progress 87%: Upload succeeded.`, then `Uploaded MysteryRoom` and `** EXPORT SUCCEEDED **` at 14:13:13 UTC |
| App Store Connect | read-only check [37945371549](https://github.com/davlatsudekspert/mystery-room-game/actions/runs/37945371549) at 14:36 UTC: `build 2 uploaded 2026-10-09T07:14:23-07:00 VALID expired=False`. TestFlight version `0.1.0`. No tester groups. Next build number 3 |
| Signing assets | Team certificate counts are unchanged (DEVELOPMENT 1, DISTRIBUTION 2). The one App Store profile from run 37920931317 was reused (`IOS_APP_STORE ACTIVE`, expires 2027-10-08) |
| Testable until | about 2027-01-07 (TestFlight builds expire after 90 days) |

The job showed **failure**, but this was a false failure: the upload had already succeeded.
- After the upload, the step ran `ls -la "$RUNNER_TEMP/export"`. With `destination=upload`, xcodebuild writes no export folder, so `ls` exited 1.
- Fixed in `ios.yml` (commit `0bf16db`): the listing now runs only for `destination=export`. The xcodebuild exit code still decides success.
- The fix has **not been run yet**. No second build was started, because it would upload a needless build 3.
- "Verify the signed IPA" is skipped in upload mode by design: no local IPA exists. In this run the checks came from three places:
  - the static Xcode-project verification;
  - the same IPA checks in run 37920931317 (same pipeline, build 1);
  - Apple's server-side processing, which marked the build `VALID`.

What this build contains: Chapters 1 and 2. Chapter 2 opens without a purchase because of `beta_unlock`, and real payments stay disabled.

### Egasi uchun keyingi qadamlar (oʻzbekcha)
1. **Ichki testerlar (review kerak emas):** App Store Connect → Apps → "Mystery Room: Lost Institute" → **TestFlight** → chap tomondagi **Internal Testing** yonidagi **"+"**. Guruh yarating (masalan, "Ichki test") va testerlarni qoʻshing.
   - Faqat jamoangizdagi App Store Connect foydalanuvchilari qoʻshiladi (Users and Access'da roli bor odamlar), 100 kishigacha.
   - Agar build 2 guruhda koʻrinmasa, guruhning **Builds** boʻlimidan "+" bilan qoʻshing.
2. **Testerlar:** iPhone yoki iPad'ga App Store'dan **TestFlight** ilovasini oʻrnatadi. Keyin e-pochtadagi taklifni qabul qiladi va "Mystery Room"ni **Install** qiladi.
3. Agar build yonida **"Missing Compliance"** chiqsa: "None of the algorithms mentioned above" ni tanlang. Odatda bu soʻralmaydi, chunki javob ilovaning ichida bor.
4. **Keyinroq, tashqi testerlar uchun:** TestFlight → **Test Information** sahifasini toʻldiring: beta tavsifi, nimani sinash kerak va fikr uchun e-pochta. Matn qoralamasi `docs/store/testflight/TEST_INFORMATION.md` da.
   - Tashqi testerlarga beriladigan birinchi build Apple'ning Beta App Review tekshiruvidan oʻtadi.
   - Bu qadam faqat sizning alohida ruxsatingiz bilan qilinadi.
5. Build taxminan 2027-01-07 gacha ishlaydi. Yangi build kerak boʻlsa, yana ruxsat bering: keyingi build raqami 3 boʻladi.

## App Store Connect record (read-only check, 2026-10-09)
Source: `iOS App Store Connect check (read-only)` run [37920292331](https://github.com/davlatsudekspert/mystery-room-game/actions/runs/37920292331) (`tools/ios/asc_check.py`, GET requests only). Only MYSTERY ROOM records were printed. No other app of the account appears in the log.

| Field | Value |
|---|---|
| App id (Apple ID) | `6820786933` |
| Name | `Mystery Room: Lost Institute` (28 of 30 characters) |
| Bundle id | `com.mysteryroom.forgotteninstitute`: **matches the repo** |
| SKU | `MYSTERYROOM-FI-001` |
| Primary locale | `en-US` (the only locale; no `ru` yet) |
| Bundle id registration | Registered, platform `UNIVERSAL`, name "Mystery Room", App ID prefix = `IOS_TEAM_ID`. Capability: `IN_APP_PURCHASE`. No provisioning profiles yet |
| App info | state `PREPARE_FOR_SUBMISSION`; subtitle, privacy policy URL, categories and age rating are **not set** |
| Version | iOS `1.0`, `PREPARE_FOR_SUBMISSION`: description, keywords, support URL and copyright are empty |
| Builds / TestFlight | No builds, no TestFlight versions, no tester groups (before the upload; build 2 is now `VALID`, see above) |
| In-app purchases | None |
| Availability | Not set up yet (`appAvailabilityV2` → 404) |
| Team certificates | `DEVELOPMENT` 1, `DISTRIBUTION` 2. These are team-wide (other projects too). Counts only, no names |
| API key role | `GET /v1/certificates` → 200 and `GET /v1/users` → 200, so the key is **Admin or App Manager**. The API cannot report a key's own role or tell those two apart. Cloud-managed distribution signing needs Admin, and it **worked** on the macOS runner (below), so the permission is in place |

The `ASC_KEY_P8_BASE64` secret holds the base64 body of the `.p8` **without** its `-----BEGIN/END PRIVATE KEY-----` lines.
- The old workflow's `base64 --decode` would have written DER bytes, while xcodebuild expects the PEM `.p8`.
- `asc_check.py` now accepts this form and every other common one (PEM, base64 PEM, double base64, BOM, UTF-16).
- `--write-p8` writes a normal PKCS#8 PEM for xcodebuild. The owner does not need to change the secret.

## Build pipeline (`.github/workflows/ios.yml`, manual trigger only)
| Job | Runner | Steps |
|---|---|---|
| `xcode-project` | ubuntu-24.04 | 1. Read-only gate (`asc_check.py --gate`). The bundle id must be registered and used by the app record; otherwise Xcode's automatic signing could register a new App ID. The build number is `max(highest App Store Connect build + 1, run number)`.<br>2. `tools/run_tests.sh`.<br>3. Godot 4.7.2 iOS export (Xcode project only).<br>4. `tools/ios/verify_xcode_project.py`.<br>5. 1-day artifact |
| `ipa` (needs the first job) | macos-15 | 1. Selects the newest Xcode 26 (the image has 26.0.1–26.3; App Store Connect has required the iOS 26 SDK since 2026-04-28).<br>2. **Unsigned** `xcodebuild archive`.<br>3. `-exportArchive` with `method=app-store-connect`, `signingStyle=automatic`, `-allowProvisioningUpdates` and the API key. This signs with the cloud-managed Apple Distribution certificate.<br>4. `destination=export` by default; `upload` only when `upload_to_testflight=true`.<br>5. Verifies the IPA: codesign, App Store profile, bundle id, build number, export compliance, SDK, localizations |

Why the archive is unsigned:
- A signed archive with automatic signing asks for a **development** profile, and that profile needs a registered device ("Your team has no devices…").
- On each fresh runner it also mints a new "Apple Development: Created via API" certificate until Apple's certificate cap is reached.
- Signing only at export avoids both. Xcode then creates, automatically, only:
  - an App Store provisioning profile for `com.mysteryroom.forgotteninstitute`;
  - the team's cloud-managed Apple Distribution certificate, if none exists yet.
- Nothing is created by hand. If export ever fails with "maximum number of certificates", **do not revoke** other projects' certificates. The owner decides.

Inputs:
- `upload_to_testflight`: default **false**. Only after the owner's approval.
- `beta_unlock`: default **true** while we ship only TestFlight builds.
  - It adds the custom feature `beta_unlock` to the iOS preset **on the runner only**. The repo preset keeps `custom_features=""`.
  - `Premium.tester_build()` then opens the released paid chapters without a purchase. `REAL_PAYMENTS_ENABLED` stays false.
  - The verifier checks that the pck carries `beta_unlock` exactly when asked.
  - **An App Store release build must run with `beta_unlock=false`.** The verifier then requires that the pck carries no custom features.

## What was verified, and where
**Verified on Linux** (dev container, Godot 4.7.2 iOS export of the Xcode project, `verify_xcode_project.py`: all checks passed):
- **Project:** scheme `MysteryRoom`; bundle id; `MARKETING_VERSION 0.1.0`; `CURRENT_PROJECT_VERSION` = the build number given; `DEVELOPMENT_TEAM` set; `CODE_SIGN_STYLE Automatic`.
- **Devices and OS:** iPhone + iPad (`TARGETED_DEVICE_FAMILY 1,2`); iOS 15.0 minimum; `UIRequiredDeviceCapabilities = iphone-ipad-minimum-performance-a12` (A12 or newer).
- **Info.plist:**
  - `ITSAppUsesNonExemptEncryption = false`, so TestFlight does not ask the export-compliance question.
  - `UIRequiresFullScreen = true`, so no iPad multitasking orientation error (ITMS-90474).
  - Landscape only.
  - `UILaunchStoryboardName = Launch Screen` (dark custom background).
- **Purpose strings:** camera, microphone and photo library now carry non-empty EN/RU/UZ texts in `en/ru/uz.lproj/InfoPlist.strings`.
  - The Godot library references `requestRecordPermission`. An empty `NSMicrophoneUsageDescription` risks ITMS-90683.
  - The game never asks for these permissions.
- **Privacy manifest:** `PrivacyInfo.xcprivacy` is generated by Godot and is in the Resources phase.
  - `NSPrivacyTracking false`, no tracking domains, no collected data types.
  - Required-reason APIs: FileTimestamp `DDA9.1, C617.1`, SystemBootTime `35F9.1`, DiskSpace `E174.1, 85F4.1`.
- **Entitlements:** none.
- **Icons:** all 16 app icons, including the 1024×1024 one, are RGB **without alpha** at the right sizes.
- **Custom features:** the `beta_unlock` feature is present in the pck when set, and absent when not set.

**Verified on GitHub ubuntu runners:**
- the read-only App Store Connect check (runs 37919863916 and 37920292331);
- the gate, tests, export and project verification inside `iOS build` run 37920931317, job "Checks + Xcode project", 1 min 49 s:
  - gate passed, build number 1;
  - `tools/run_tests.sh` passed;
  - Godot export done, and `verify_xcode_project.py` reported "all checks passed", including `beta_unlock` in the pck;
  - 549 MB project tar, 231 MB artifact, kept for 1 day.

**Verified on a macOS runner** (`iOS build` run 37920931317, job "Archive + signed IPA", 1 min 44 s, upload off):
- **Toolchain:** Xcode 26.3 (`DTXcode 2630`, iOS SDK `iphoneos26.2`, which App Store Connect accepts).
- **Archive and export:** `** ARCHIVE SUCCEEDED **` (unsigned), then `** EXPORT SUCCEEDED **` with cloud signing.
- **IPA:** `MysteryRoom.ipa`, 150 MB, arm64; game data 164 MB.
- **Signature:** `codesign --verify --deep --strict` OK. `Authority=Apple Distribution`, chained to Apple WWDR and Apple Root CA.
- **Profile:** "iOS Team Store Provisioning Profile: com.mysteryroom.forgotteninstitute", an App Store profile with no device list.
  - `get-task-allow false`, `beta-reports-active true` (TestFlight-ready).
  - Expires 2027-10-08 17:53 UTC.
- **Info.plist:** `CFBundleIdentifier com.mysteryroom.forgotteninstitute`, `CFBundleShortVersionString 0.1.0`, `CFBundleVersion 1`, `ITSAppUsesNonExemptEncryption false`, `MinimumOSVersion 15.0`. `PrivacyInfo.xcprivacy` is in the bundle.
- **What this proves:**
  - The signature was made with no local signing identity on the runner, so it is **cloud-managed distribution signing**. The API key therefore has the permission it needs: Admin, in practice.
  - Xcode created only the App Store profile.
  - The profile's expiry is not one year from this run. It follows the certificate's expiry, so the Apple Distribution certificate already existed (from 2026-10-08) and was reused. This is an inference; no certificate list was printed.
- **Not yet run on macOS:** the step that prints the bundle's `.lproj` folders. It was added after this run.

**Known issue found by the export (not iOS-specific), now resolved:**
- Run 37920931317's export logged `ERROR: Failed loading resource: res://assets/textures/decals/ch2/tape_label_1996.png`. Its `.import` said `valid=false`.
- The `.import` was re-committed later. Run 37941801214's export (the uploaded build 2) logs no such error, only the usual three warnings.

**Verified by the upload (run 37941801214, check 37945371549):**
- the TestFlight upload ("Upload succeeded.");
- Apple's server-side binary validation (build 2 `VALID`).

**Unverified:**
- the game on a real iPhone or iPad (FPS, memory, Metal/MoltenVK);
- the `ios.yml` fix for the false failure in upload mode (commit `0bf16db`), until the next upload run.

### Runs and minutes
| Run | Workflow | Runner | Result | Wall time | Billed |
|---|---|---|---|---|---|
| [37919863916](https://github.com/davlatsudekspert/mystery-room-game/actions/runs/37919863916) | ASC check #1 | ubuntu | failed in my script: the key-encoding case above | 27 s | 1 min |
| [37920292331](https://github.com/davlatsudekspert/mystery-room-game/actions/runs/37920292331) | ASC check #2 | ubuntu | success | 35 s | 1 min |
| [37920931317](https://github.com/davlatsudekspert/mystery-room-game/actions/runs/37920931317) | iOS build #1 (upload off, beta_unlock on) | ubuntu, then macOS 15 | success: signed IPA, build 1 | ubuntu 1 min 49 s; macOS 1 min 44 s (run 3 min 45 s) | 2 ubuntu min + 2 macOS min (= 20 min of quota at 10×)* |

| [37941801214](https://github.com/davlatsudekspert/mystery-room-game/actions/runs/37941801214) | iOS build #2 (**upload on**, beta_unlock on) | ubuntu, then macOS 15 | upload succeeded, build 2. The job showed failure only because of `ls` on the missing export folder (fixed in `0bf16db`) | ubuntu 2 min 00 s; macOS 3 min 57 s (archive 2 min 20 s, export + upload 55 s; run 6 min 14 s) | 2 ubuntu min + 4 macOS min (= 40 min of quota at 10×)* |
| [37945371549](https://github.com/davlatsudekspert/mystery-room-game/actions/runs/37945371549) | ASC check #3 (after the upload) | ubuntu | success: build 2 `VALID` | 24 s | 1 min |

\* Estimated from the job durations (each job is rounded up to the minute; macOS counts 10×). The usage API returned 0 billable ms right after the runs. Total macOS so far: 2 runs, 6 billed min (= 60 min of quota).

## Metadata: record vs `docs/STORE_LISTING.md` (proposals only; nothing was changed)
- **Name:**
  - The record's "Mystery Room: Lost Institute" (28) is right.
  - `STORE_LISTING.md`'s "Mystery Room: The Forgotten Institute" is 37 characters, over the App Store's 30-character limit. It stays the in-game title.
  - The home-screen name is "Mystery Room".
- **Subtitle (≤ 30):** not set. Proposal: EN "A 3D escape-room mystery" (24); RU "Головоломка-побег в 3D" (22).
- **Locales:** only `en-US`. Proposal: add **Russian** with:
  - name "Mystery Room: Забытый институт" (exactly 30);
  - the RU description from `docs/store/PLAY_VA_APPSTORE_QOLLANMA.txt`;
  - keywords "побег,квест,головоломка,загадка,тайна,детектив,лаборатория,приключение,оффлайн,комната" (86).
- **Description:**
  - Use the guide's text ("The first two chapters are free. More chapters are coming."; Chapters 1–2 are free since 2026-10-10).
  - Do not use `STORE_LISTING.md`'s "One fair purchase unlocks the rest" while real payments are disabled. Metadata must describe what the build does (Guideline 2.3).
- **Required before App Store review** (not for internal TestFlight):
  - privacy policy URL `https://sites.google.com/view/mysteryroom-privacy`;
  - support URL (same site);
  - categories Games → Puzzle, then Adventure;
  - copyright;
  - age rating questionnaire;
  - App Privacy;
  - territories;
  - screenshots. iPhone 6.9" is needed; iPad 13" too, because the build supports iPad.
- **Uzbek:** App Store Connect has **no Uzbek localization**.
  - Apple's list of App Store localizations has 50 languages and no Uzbek. For the Uzbekistan storefront the default language is English (U.K.), with no additional languages ([App Store localizations](https://developer.apple.com/help/app-store-connect/reference/app-information/app-store-localizations)).
  - Uzbek players therefore see the English store page. Proposal:
    - (a) the EN (and RU) description says "Fully playable in English, Russian and Uzbek";
    - (b) the build ships `uz.lproj`, so the product page's **Languages** row lists Uzbek. That row is read from the binary's `.lproj` folders, not from store localizations ([Apple forums](https://developer.apple.com/forums/thread/836440)). The macOS verify step prints the bundle's localizations;
    - (c) the game picks Uzbek from the device language or the first-run language picker;
    - (d) optionally, one screenshot shows the Uzbek UI.

## In-app purchase `full_game` (2026-10-10)
Code, plugin choice and the enable-later steps: `docs/MONETIZATION.md`. Real payments stay off.

| Piece | How | State |
|---|---|---|
| Product in App Store Connect | `ios-iap.yml` → `tools/ios/asc_iap.py`. `dry_run` defaults to **true** (GET only). `dry_run=false` creates or fixes the NON_CONSUMABLE `full_game` on this app only: reference name "Full Game"; en-US and ru localizations (no Uzbek locale exists); US base price US$4.99 (price point looked up through the API; Apple sets the other territories); availability in the app's territories; the review screenshot `docs/store/iap/full_game_review.png` (2796×1290, the purchase screen as a store build shows it). It prints the state and what is still missing for "Ready to Submit". It never submits | Written; tested against a local fake API only; **not dispatched** |
| StoreKit in the build | `ios.yml` input `store_sandbox` (default false; needs `beta_unlock=false`). The ubuntu job adds the StoreKit 2 plugin (hrk4649/godot_ios_plugin_iap 0.4.0, MIT, SHA-256 pinned) and the custom feature `store_sandbox`; after the export `tools/ios/add_iap_capability.py` turns on the In-App Purchase capability; `verify_xcode_project.py --storekit` requires plugin, init, StoreKit.framework and capability (and their absence in other builds); the signed-IPA check compares StoreKit linkage | Godot export + checks verified locally (Linux). **The macOS archive with the plugin has not run yet** |
| Capability on the App ID | `IN_APP_PURCHASE` is already on the bundle id (read-only check of 2026-10-09). No new key or profile type is needed; the cloud-signed App Store profile covers it | — |

**Testing in TestFlight:** after `ios-iap.yml` created the product with a price, run `ios.yml` with `store_sandbox=true`, `beta_unlock=false`, `upload_to_testflight=true` (owner's approval). TestFlight purchases are always sandbox and never charged; testers use their own Apple Account. The first in-app purchase is reviewed only when it is submitted with an app version, which is not needed for sandbox tests.

**Never submit a `store_sandbox` build for App Review.** The App Store build must run with `beta_unlock=false` and `store_sandbox=false`; the Xcode check then requires a pck without custom features. As a second guard, a `store_sandbox` build that was installed from the App Store (receipt file `StoreKit/receipt`) keeps the store disabled.

## Owner checklist
1. **Agreements:** App Store Connect → Business → the Free Apps agreement is active. The API cannot read it.
2. **Export compliance:** answered in the binary (`ITSAppUsesNonExemptEncryption=false`). If App Store Connect still asks: "None of the algorithms mentioned above".
3. **App Privacy:** App Store Connect → the app → App Privacy → "Data Not Collected" → Publish. The game has no accounts, ads, analytics or network.
4. **Age rating:** Horror/Fear Themes: Infrequent/Mild; everything else None/No.
5. **TestFlight testers.** Nobody is added by us; the owner adds them.
   - **Internal testers:** up to 100 App Store Connect users of the team (people with an App Store Connect role, e.g. the owner). No Beta App Review. A build is testable once processing finishes.
   - **External testers:** up to 10,000, by e-mail or public link. They need Test Information (beta app description, what to test, feedback e-mail). The first build of a version goes to **Beta App Review**.
   - A build stays testable for 90 days ([TestFlight overview](https://developer.apple.com/help/app-store-connect/test-a-beta-version/testflight-overview)).
6. **Key role:** nothing to do. Cloud-managed distribution signing worked in run 37920931317, so the key has the needed (Admin) permission.

## One-click upload (director, only after the owner's explicit approval)
First used on 2026-10-09 (run 37941801214, build 2). Each new upload needs a new approval. Never re-run an old run: a re-run reuses its build number.

1. Optional, ubuntu, about 1 min: run `iOS App Store Connect check (read-only)` and confirm the record and bundle id are unchanged.
2. Start the upload:
   - GitHub → Actions → **iOS build** → Run workflow → branch `main`, **upload_to_testflight = ✓**, **beta_unlock = ✓** (TestFlight build).
   - Or with the MCP tool: `actions_run_trigger` `run_workflow`, `workflow_id: ios.yml`, `ref: main`, `inputs: {"upload_to_testflight": "true", "beta_unlock": "true"}`.
   - Cost: the ubuntu job plus one macOS job (see the run table; macOS minutes count 10×).
3. The log's "Export the IPA…" step shows `Progress …: Upload succeeded.`, `Uploaded MysteryRoom` and `** EXPORT SUCCEEDED **`.
   - The "Verify the signed IPA" step is skipped in upload mode.
   - App Store Connect then processes the build. Build 2 was `VALID` within 22 minutes of the upload.
4. Rerun the read-only check: the `builds` line shows the new build number and `processingState`.
5. The owner adds internal testers in App Store Connect → TestFlight. Testers install the **TestFlight** app on the iPhone and accept the invitation.
6. App Store release later: run with `beta_unlock = ☐`. Real payments stay off until the IAP products and store validation exist.
