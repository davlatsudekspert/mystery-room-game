# Google Play testing: MYSTERY ROOM (Android)

_Last updated: 2026-10-09. Package `com.mysteryroom.forgotteninstitute`. Sources [S1]–[S11] are listed at the end; all were read on 2026-10-09._

## Qisqacha (oʻzbekcha)
- **Holat:** debug APK va release AAB shu konteynerda yigʻildi va tekshirildi: paket nomi, versiya kodi, target SDK 36, faqat VIBRATE ruxsati, arm64-v8a, 16 KB moslik. GitHub'da release yigʻish hali boʻlmagan. 2026-10-08 dagi 5-yigʻishda `ANDROID_KEYSTORE_BASE64` secreti **boʻsh** edi.
- **Sizdan 1:** GitHub → Settings → Secrets and variables → Actions boʻlimiga 3 ta secret qoʻshing:
  - `ANDROID_KEYSTORE_BASE64`
  - `ANDROID_KEYSTORE_PASSWORD`
  - `ANDROID_KEY_ALIAS` = `mysteryroom-upload`

  Shundan keyin direktor bitta release yigʻishni **yuklashsiz** ishga tushiradi va tekshirilgan `.aab` faylni beradi.
- **Sizdan 2:** birinchi `.aab` ni Play Console → Тестирование → Внутреннее тестирование boʻlimiga **oʻzingiz qoʻlda** yuklaysiz. Birinchi yuklashni API orqali qilib boʻlmaydi.
- **Sizdan 3 (ixtiyoriy):** keyingi test buildlar avtomatik yuklanishi uchun:
  - `PLAY_SERVICE_ACCOUNT_JSON` secreti (7-boʻlim);
  - bir martalik ruxsat: «MYSTERY ROOM test buildlarini Internal va Closed testingga yuklashga ruxsat beraman».

  Production'ga hech narsa avtomatik yuklanmaydi.
- **12 tester / 14 kun qoidasi:** 2023-yil 13-noyabrdan keyin ochilgan shaxsiy akkauntlarga tegishli. Tekshirish: MYSTERY ROOM'ning «Панель управления» sahifasida Production yopiq boʻlsa va «Apply for production» vazifasi koʻrinsa, qoida shu ilovaga ham amal qiladi (4.1).
- **NFCSTORE testerlari:** Play Console'dagi email roʻyxatlar boshqa ilovalarda ham ishlatilishi mumkin. Lekin har bir tester MYSTERY ROOM'ning **oʻz havolasi** orqali qaytadan qoʻshilishi shart. Taklif matni EN/RU/UZ tillarida: 8-boʻlim.
- **Oʻzbek tili:** Play doʻkon sahifasini oʻzbek tilida qilib boʻlmaydi, rasmiy tillar roʻyxatida yoʻq. EN va RU sahifalar qilinadi. Oʻyinning oʻzi oʻzbekcha toʻliq ishlaydi.
- **beta_unlock:** test buildlarda testerlar pullik boblarni ham oʻynay oladi. Toʻlov kodi baribir oʻchiq. Doʻkonga chiqadigan production build faqat `beta_unlock=false` bilan yigʻiladi. Test relizini production'ga «Promote» qilmang.

---

## Internal testing is live (2026-10-10)
| | |
|---|---|
| Status | «Доступен внутренним тестировщикам», since 2026-10-10 11:14 (Tashkent) |
| Build | `com.mysteryroom.forgotteninstitute`, versionCode **7**, versionName 0.1.0, release name "0.1.0 (7)". This is CI run 7 (android.yml, release, beta_unlock): signed with the MYSTERY ROOM upload key, uploaded by hand as the app's first AAB |
| Testers | the list "MYSTERY ROOM internal" (39 people, chosen by the owner) |
| Opt-in link | https://play.google.com/apps/internaltest/4701293031736439424 (testers on the list open it on the phone, accept, then install from Play) |
| Console warnings | only the usual two: no deobfuscation file, no native debug symbols. No errors; App Signing was not asked again |
| Release notes | empty in this first release. Later releases take docs/release/whatsnew/ |
| Not touched | the NFCSTORE app, other tracks, store listing, pricing |

Next: the owner tests New Game on his own Android phone before sharing the link. iOS crashes there (Metal), and Android uses Vulkan, which is a different driver. Then create `PLAY_SERVICE_ACCOUNT_JSON` (§7), so that CI uploads every later test build itself.

## First manual upload (2026-10-09)
**Use the CI build (recommended).** After the owner added the three `ANDROID_*` secrets, `android.yml` run #6 (37942708580, release, `upload_to_play=false`, `beta_unlock=true`) built and verified the AAB on CI: versionCode **6**, versionName 0.1.0, targetSdk 36, VIBRATE only, signer SHA-256 = the upload key (`E5:D8:…:D1:3E`), `beta_unlock` present, 193,592,852 bytes. Download it from the run page → Artifacts → `mystery-room-android-release` (kept 7 days): https://github.com/davlatsudekspert/mystery-room-game/actions/runs/37942708580. Once versionCode 6 is on Play, the local versionCode 2 build below can no longer be uploaded and is only a fallback.

A release AAB for the first, manual Internal testing upload was built locally in the dev container. Nothing was uploaded, and no workflow was run.

| What | Value |
|---|---|
| File | `mystery-room-0.1.0-vc2-internal.aab` (handed to the owner by the director; not in the repo) |
| Source | `main` at `cbd51ab`, clean `git archive` snapshot. `tools/run_tests.sh` on it: 95 tests, 8226 checks, **0 failures** |
| versionCode / versionName | **2** / 0.1.0 |
| Size | **193,591,313 bytes** (≈ 193.6 MB). bundletool download estimate: arm64-v8a ≈ 167.1 MB, armeabi-v7a ≈ 168.5 MB |
| SHA-256 of the AAB file | `908b2e7266bade3f3d5e2cb2d29ad3683bbe36fe4c030bebfc2e7c0d63cd4894` |
| Test features | `beta_unlock` **on**: Chapter 2 opens without a purchase. `REAL_PAYMENTS_ENABLED = false` |
| How | Godot 4.7.2 `--install-android-build-template --export-release "Android AAB"`, Gradle heap 2 GB, 197 s. The upload keystore was read in place through the `GODOT_ANDROID_KEYSTORE_RELEASE_*` environment variables. The preset was edited only in the build copy, with the same `version/code` sed and `beta_unlock` awk as `android.yml` |

Verified: the `android.yml` verify step, run locally with `EXPECTED_VERSION_CODE=2` and `BETA_UNLOCK=true`, exited 0. Extra checks were run with `bundletool`, `keytool` and `jarsigner`.
- package `com.mysteryroom.forgotteninstitute`, versionCode 2, versionName 0.1.0;
- minSdk 24, targetSdk 36; not debuggable;
- the only permission is `VIBRATE`;
- ABIs arm64-v8a and armeabi-v7a; `PAGE_ALIGNMENT_16K`;
- `jarsigner -verify`: jar verified. The `keytool -printcert -jarfile` signer SHA-256 is **exactly** the upload key's `E5:D8:42:…:D1:3E`;
- `beta_unlock` is listed under `_custom_features` in `assetPackInstallTime/assets/project.binary`. This is the first real export with the `android.yml` preset edit, which closes that open point in sections 1 and 10.
- JDK 21's `jarsigner` warns "signed in JarFile but is not signed in JarInputStream" for every entry. AGP writes `META-INF/` at the end of the bundle; the earlier Gradle AAB shows the same warning, and the signature still verifies.

**Later CI builds** use versionCode = run number, so they will be **6 or higher** and Play accepts them after 2. versionCode 2 is now taken: never build another AAB with versionCode 2 or lower.

**Egasi uchun qadamlar (oʻzbekcha):**
1. Play Console → MYSTERY ROOM → Testing → Internal testing (Тестирование → Внутреннее тестирование) → **Create new release** (Создать выпуск).
2. Ilova imzosi soʻralsa, **Play App Signing**ni qabul qiling: kalitni Google boshqaradi (Google-managed key, «Use Google-generated key»). Boshqa kalit yuklamang: bizning upload kalitimiz faqat yuklash uchun.
3. `mystery-room-0.1.0-vc2-internal.aab` faylini yuklang. Play versiyani «2 (0.1.0)» deb koʻrsatishi kerak.
4. Release notes maydoniga EN matnini `docs/release/whatsnew/whatsnew-en-US` faylidan, RU matnini `whatsnew-ru-RU` faylidan qoʻying: `<en-US>…</en-US>` va `<ru-RU>…</ru-RU>` teglari ichida.
5. **Save** → **Review release** → **Start rollout to Internal testing**: ichki testerlarga chiqaring.
6. **Testers** yorligʻida testerlarning email manzillarini qoʻshing, saqlang va ularga taklif havolasini (opt-in link) yuboring.

## 1. Verified on 2026-10-09 (evidence)
| What | Result | How it was checked |
|---|---|---|
| Actions run #5 "Android build" (id `37856877382`, 2026-10-08 22:59 UTC, success, ~80 s) | It was a **debug** build. "Export debug APK" ran, while "Android SDK 36", "Export release AAB" and "Upload to Google Play" were *skipped*. The log shows `KS_B64: ` with an **empty** value, so `ANDROID_KEYSTORE_BASE64` **did not exist** at that time. GitHub masks an existing secret as `***`. Output: debug APK of 133,411,646 bytes | Job `113583077825` steps and log (GitHub MCP) |
| Other secrets | The debug path never references `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS` or `PLAY_SERVICE_ACCOUNT_JSON`, so the logs cannot show whether they exist. Listing secret names through the API is blocked from this container. No release run has happened since | — |
| **Debug APK, local** (commit `02e5776`, clean `git archive` snapshot, Godot 4.7.2, export 28 s, peak 724 MB RSS) | `mystery-room-debug.apk`:<br>• **191,896,132 bytes**;<br>• package `com.mysteryroom.forgotteninstitute`;<br>• versionCode 42 (the CI substitution `version/code=<run number>` applied with 42 as a test value);<br>• versionName 0.1.0;<br>• minSdk 24, targetSdk 36;<br>• native code **arm64-v8a** only;<br>• the only permission is `VIBRATE`; no `INTERNET`, no `AD_ID`;<br>• `apksigner verify`: v2 + v3 OK, signer `CN=Android Debug`;<br>• `zipalign -c -P 16` OK; ELF LOAD alignment `0x4000` (16 KB) | `apksigner`, `aapt2 dump badging`, `aapt2 dump xmltree`, `zipalign`, `readelf` (build-tools 36.1.0) |
| Why the APK grew from 133 MB to 192 MB | Chapter 2 content since run #5: textures 79 → 149, models 96 → 137, sounds 40 → 82 imported files. Only mobile texture formats (ETC2/ASTC) are packed, with no desktop duplicates | APK content listing |
| **Release AAB, local Gradle build** (same snapshot, `--install-android-build-template --export-release "Android AAB"`, Gradle heap capped at 2 GB, 130 s) | `mystery-room-release.aab`:<br>• **182,261,100 bytes**;<br>• package correct, versionCode 42, minSdk 24, targetSdk 36;<br>• only `VIBRATE`; not debuggable;<br>• ABIs arm64-v8a + armeabi-v7a;<br>• `PAGE_ALIGNMENT_16K`.<br>Download size estimated by bundletool: **arm64-v8a ≈ 155.8 MB**, armeabi-v7a ≈ 157.2 MB | `bundletool 1.18.2` `dump manifest`, `dump config`, `build-apks` + `get-size total --dimensions=ABI` |
| The new CI verification step | Run on that AAB exactly as written in `android.yml`. Everything parsed. It correctly **rejected** the bundle because the local build was signed with a *throw-away test key* (SHA-256 `6E:6D:…:C2:56`) and not with the upload key, and it exited 1. `beta_unlock: false (requested: false)` | Step script extracted from the YAML and run locally |
| Upload key | The documented SHA-256 `E5:D8:42:…:D1:3E` matches the signer of an older local AAB (2026-10-08 23:17, versionCode 1). That bundle is **stale**: it has old content and versionCode 1. **Do not upload** `build/android/mystery-room-release.aab` from 2026-10-08 | `keytool -printcert -jarfile` (public certificate only) |
| Play requirements | **Target API:** new apps and updates must target API 36 since 2026-08-31 [S1].<br>**16 KB pages:** updates that lack 16 KB support are blocked from 2027-02-01 [S10].<br>**Size limits:** base module 500 MB, each asset pack 1.5 GB; above 200 MB, users on mobile data see a non-blocking size dialog [S4] | Official pages |

**Not verified:**
- the release build on GitHub Actions (blocked by the missing secrets);
- the `beta_unlock` step on a real export: the local test of the preset edit was blocked by this session's permission policy, so the first CI run checks it (section 9, step 4);
- any Play Console screen;
- any physical device.

## 2. What the owner must do or approve
1. **Add 3 repository secrets.** GitHub → `davlatsudekspert/mystery-room-game` → Settings → Secrets and variables → Actions → *New repository secret*:
   - `ANDROID_KEYSTORE_BASE64`: the base64 text of the MYSTERY ROOM upload keystore;
   - `ANDROID_KEYSTORE_PASSWORD`: its password;
   - `ANDROID_KEY_ALIAS`: `mysteryroom-upload`.

   Never paste these anywhere else.
2. **Tell the director that the secrets are added.** The director then starts **one** `android.yml` run with `build_type=release`, `upload_to_play=false` and `beta_unlock=true`. It costs about 5–10 ubuntu minutes from the free quota.
   - The run fails in seconds and names any missing secret.
   - Otherwise it proves package, versionCode, target SDK, permissions, ABI, the `beta_unlock` state and the upload-key fingerprint before it publishes the artifact.
3. **Upload the first AAB by hand.** Download the run's `mystery-room-android-release` artifact, then Play Console → Тестирование → Внутреннее тестирование → *Create new release*.
   - Accept Play App Signing ("Use Google-generated key").
   - Upload the `.aab` and add the release notes from section 9.
   - Save, review, then *Start rollout*.
   - The API cannot do this very first upload: the upload action's documentation requires one manual upload first [S11].
4. **Optional, for one-run updates:**
   - create `PLAY_SERVICE_ACCOUNT_JSON` (section 7);
   - give this **one-time approval** (in Uzbek, for example): *«MYSTERY ROOM test buildlarini GitHub Actions orqali Google Play Internal va Closed testing treklariga yuklashga ruxsat beraman. Production'ga emas.»*

   Without it, every test build is uploaded by hand as in step 3.

## 3. Release path audit (`android.yml`, `export_presets.cfg`)
| Item | Finding | Change |
|---|---|---|
| Package id | `com.mysteryroom.forgotteninstitute` in both Android presets and in `PACKAGE_NAME`. It matches the APK and the AAB | None. CI now **asserts** it in the AAB |
| Release signing | Godot reads `GODOT_ANDROID_KEYSTORE_RELEASE_PATH/USER/PASSWORD`. The keystore is written from the secret on the runner only. The old check `jarsigner -verify … \| tail -1` could never fail the step: there is no `pipefail`, and `jarsigner` exits 0 on an unsigned jar | The verify step fails unless `jarsigner` reports "jar verified" **and** the signer's SHA-256 equals the documented upload-key fingerprint |
| Debug keystore in release | A throw-away debug key is created on every run and used only for the debug APK | The fingerprint check proves the AAB is not debug-signed. CI also fails on `android:debuggable="true"` |
| versionCode | `version/code=` is set to `github.run_number`. Debug runs also use up numbers, which is harmless. The next run is #6 | CI **asserts** that the AAB's versionCode equals the run number. Never use *Re-run* on a run that uploaded: a re-run keeps the same number and Play rejects it |
| versionName | Fixed at `0.1.0` | Optional input `version_name` (validated `N.N[.N[.N]]`) |
| min / target SDK | 24 / 36. Play requires 36 for new apps and updates since 2026-08-31 [S1] | CI **asserts** targetSdk ≥ 36 |
| 64-bit | arm64-v8a is in both presets. The AAB also carries armeabi-v7a | None (owner decision, see risks) |
| 16 KB pages | ELF `0x4000`, `zipalign -P 16` OK, `PAGE_ALIGNMENT_16K` (AGP 8.6.1 ≥ 8.5.1 [S10]) | None |
| Size | Estimated arm64 download ≈ 155.8 MB. Play's limits are 500 MB for the base module and 1.5 GB for each asset pack [S4] | None. Watch the 200 MB mobile-data dialog [S4] |
| Permissions | `VIBRATE` only. There is no `INTERNET` permission, so the game cannot transmit data, which matches the privacy policy | CI fails on any permission outside `VIBRATE` (and AndroidX's own `…DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION`) |
| Missing secrets | Previously discovered only after checkout and about a minute of tests | **Preflight** step, first in the job, names missing secrets (names only) |
| Upload action | `r0adkll/upload-google-play@v1` was a moving tag, and it receives the Play credentials | Pinned to commit `e738b9dd8f2476ea806d921b64aacd24f34515a5` (= v1.1.5, the current v1) |
| Track / status | Before: internal + draft only | Inputs `play_track` (`internal` / `alpha` = Closed testing) and `play_status` (`draft` / `completed`). Release notes come from `docs/release/whatsnew/`. Release name = `"<versionName> (<versionCode>)"` |
| `beta_unlock` | The director's requirement: `Premium.tester_build()` = `OS.has_feature("beta_unlock")` lets testers open paid chapters while real payments stay disabled | Input `beta_unlock` (default **true**). On the runner only, `custom_features="beta_unlock"` is added to the two Android presets. CI asserts that the exported `project.binary` contains the feature exactly when requested. The repository preset never carries it |
| Real payments | `REAL_PAYMENTS_ENABLED := false` in `game/src/autoload/premium.gd`. No billing plugin and no ads SDK | None |

## 4. Play Console path: internal → closed → production
### 4.1 Does the 12-tester / 14-day rule apply?
The rule: "personal developer accounts created after November 13, 2023" must run "a closed test" with "a minimum of 12 testers who have been opted in continuously for at least 14 days" before production. Until then, the Production and Pre-registration pages stay disabled [S2].

Check, in this order:
1. **Account type.** It is Personal or Organization; an organization account needs a D-U-N-S number [S8]. Look under Play Console → Developer account → About you / Account details. The help page names these pages but does not show the exact label.
2. **Creation date.** Use the date of the US$25 registration payment, from the receipt e-mail or the Google payments order history.
3. **The deciding check: MYSTERY ROOM's own Dashboard** (Панель управления).
   - If Production is greyed out and the Dashboard offers *Apply for production* after a closed test, the rule applies **to this app**.
   - The help page does not say whether the rule is per app or once per account [S2]. Another app in the same account being live is therefore **not** proof that MYSTERY ROOM is exempt.

### 4.2 Internal testing (owner and close helpers, up to 100 testers)
- Path: Test and release → Testing → Internal testing → Testers tab → *Create email list* → select it → feedback URL or e-mail → copy the link → *Save changes* [S3].
- New bundles reach internal testers "within minutes" [S3]. The very first publish of a test can take "several hours" before the link works [S3].
- **Important:** "A user who opts into your app's internal test is no longer eligible to receive an open or closed test." To join the closed test, that person must first opt out of the internal test [S3].
  - People who will count toward the 12 should therefore join the **closed** test directly, or leave internal testing first.
- Internal-only apps do not need the Data safety form [S9]. A closed test does.

### 4.3 Closed testing (the 14-day test)
1. Finish the store listing and every App content item first (sections 5 and 6). Closed tracks go through review; internal tests "might not be" reviewed [S3].
2. Test and release → Testing → Closed testing → the default track (API name `alpha`) → *Manage track* → Testers tab [S3].
3. Choose **Email** (select lists) or **Google Groups** (`name@googlegroups.com`; "only members of the specified Google Groups can join" [S3]).
4. Enter the feedback channel, which is shown on the opt-in page [S3]. Copy the opt-in link and save.
5. Create a release on this track with the AAB, then roll it out.
   - The opt-in link works only once the app status is "Published" [S3].
6. Send the invitation (section 8).
   - "Each tester needs to opt in using the link" [S3].
   - Testers need a Google Account [S3].
7. Keep **15–20** testers opted in for 14+ days. Twelve is the minimum; the margin covers drop-outs. Testers who opt out before 14 days do not count. A tester who leaves and rejoins needs 14 **consecutive** days [S2].

### 4.4 Apply for production
Dashboard → *Apply for production* [S2]. The questions cover:
- the closed test: recruitment, tester engagement, a feedback summary;
- the app: audience, value, expected installs;
- production readiness: what changed after the test.

Review "usually takes seven days or less" [S2]. Collect feedback during the test (section 9), so these answers are factual.

## 5. App content declarations (must match the privacy policy)
Privacy policy: https://sites.google.com/view/mysteryroom-privacy. In short: no data collected, progress stays on the device, the game works offline, it uses vibration only, it is not directed at children under 13, and any future purchases go through the stores.

| Declaration (Контент приложения) | Answer | Why it is true |
|---|---|---|
| Data safety (Безопасность данных) | "Does your app collect or share any of the required user data types?" → **No**. Even apps that collect nothing must submit the form [S9] | "Collect" means "transmitting data from your app off a user's device" [S9]. The manifest has no `INTERNET` permission (verified in the APK and the AAB). Progress stays in `user://` and backup is disabled (`allowBackup=false`). The privacy link opens the user's browser |
| Ads (Реклама) | **No**, the app has no ads | No ads SDK |
| Advertising ID | **No**, not used | No `com.google.android.gms.permission.AD_ID` in the manifest (verified) |
| App access (Доступ к приложению) | All functionality is available without special access | No accounts or logins |
| Content rating (IARC) | The owner reported it as submitted. Answers are in `docs/store/PLAY_VA_APPSTORE_QOLLANMA.txt` §1.4 (fear: yes, mild; purchases: **no** while payments are disabled) | Update the questionnaire **before** real payments are switched on |
| Target audience (Целевая аудитория) | 13–15, 16–17, 18+. Not under 13. "Appeals to children": No | Matches policy item 5 |
| News, COVID-19, government, financial features, health | No / none | — |

**Change rule:** any future analytics, crash upload or "send stats" feature must update the privacy policy and Data safety **before** that build reaches any closed or production track (see `docs/BUSINESS_STRATEGY.md`, the Phase B table).

## 6. Store listing (EN / RU; Uzbek is not available on Play)
- Use the texts in `docs/store/PLAY_VA_APPSTORE_QOLLANMA.txt` §1.3: title ≤ 30, short description ≤ 80, full description ≤ 4,000 characters.
  - Default language **English (United States) – en-US**.
  - Translation **Russian – ru-RU**.
  - While payments are disabled, use the "Chapter 1 is free. More chapters are coming." version, not "One fair purchase unlocks the rest" (`docs/STORE_LISTING.md`).
- **Uzbek:** Play Console's list of store-listing languages has 86 entries with codes. It includes Kazakh – kk, Kyrgyz – ky-KG and Russian – ru-RU, but **no Uzbek** [S5] (checked in the page source on 2026-10-09).
  - The UZ title and descriptions therefore cannot be entered.
  - Users who view an untranslated listing "can choose to view an automated translation" [S5].
  - The EN and RU descriptions already say the game is fully playable in Uzbek.
  - The UZ texts stay ready for the App Store or for a future Play update.
- Release notes ("What's new") use the same language list: EN and RU go to Play, and the UZ notes go to testers by message (section 9).
- Graphics: `docs/store/graphics/` (icon 512, feature graphic 1024×500, 8 screenshots).

## 7. `PLAY_SERVICE_ACCOUNT_JSON`: what it enables and how to create it
**What it enables:** the workflow's last step uploads the verified AAB to **Internal testing** or **Closed testing (`alpha`)**, with EN/RU release notes, as a draft or rolled out. One run then does the whole update.
- Without it, the AAB is downloaded from the run artifacts and uploaded by hand.
- It cannot create apps. With the permission below, it cannot touch production or other apps.

**Create it.** No paid Google Cloud service is used. If Cloud asks for a billing account, stop and ask the director:
1. https://console.cloud.google.com → create a project, for example `mysteryroom-play-ci`.
2. APIs & Services → Library → **Google Play Android Developer API** → *Enable* [S6].
3. IAM & Admin → Service accounts → *Create service account*, for example `mysteryroom-play-upload`. Grant **no** Cloud roles.
4. That service account → Keys → *Add key* → *JSON*. The downloaded file is a password: do not e-mail it and do not put it in the repository.
5. **Play Console** → Users and permissions → *Invite new users* → the service account's e-mail (`…@…iam.gserviceaccount.com`) [S6][S7].
   - **Account permissions:** none.
   - **App permissions** → *Add app* → **MYSTERY ROOM only** → tick only **"Release apps to testing tracks"**. It allows creating and rolling out testing-track releases, "doesn't allow production publishing" [S7].
   - Do **not** give Admin, "Release to production…", financial or any other app's permissions → *Invite user*.
   - Linking a Cloud project on the old "API access" page is no longer needed [S6].
6. GitHub → Settings → Secrets and variables → Actions → `PLAY_SERVICE_ACCOUNT_JSON` = the whole JSON text. Then delete the downloaded file, or keep it offline.

**Revoke:** remove the user in Play Console → Users and permissions, and delete the key in Google Cloud.

**If the first upload fails with a permission error:** check the app-level permission. New service-account access is often reported to take some time to become active. That is an unverified observation, so retry later rather than widening the permissions.

## 8. Inviting NFCSTORE's existing testers to MYSTERY ROOM (owner-side only)
Nothing here touches NFCSTORE's files, repository, builds or data. Every step happens in **MYSTERY ROOM's** own pages in Play Console.

1. **Reuse the list or group, which lives at the account level.**
   - Email lists: "You can use the same list for future tests on any of your apps" [S3]. In MYSTERY ROOM → Closed testing → Testers → **Email**, tick the existing list.
   - Recommended instead: create a new list "MYSTERY ROOM closed test" with the same addresses. Editing a shared list changes it for every app that uses it, and a separate list keeps the two businesses apart.
   - **Google Group:** if that test used a group, enter the same `…@googlegroups.com` address in MYSTERY ROOM's closed track [S3].
   - Tester e-mails are personal data. Keep them only in Play Console or Groups, never in this repository or in chats with tools.
2. **Every tester opts in again** through **MYSTERY ROOM's own opt-in link** (Testers tab → copy link). "Each tester needs to opt in using the link" [S3]. Being a tester of another app does not enrol anyone here.
3. **What counts toward "12 testers for 14 days" [S2]:**
   - testers who **opted in to MYSTERY ROOM's closed test** and stayed opted in **continuously for at least 14 days**;
   - testers who opt out before 14 days **do not count**; leaving and rejoining needs 14 consecutive days;
   - MYSTERY ROOM's internal testers are not described as counting, and an internal tester is not eligible for the closed test until they leave internal testing [S3]. Put helpers in the closed test.
   - The requirement is a closed test "for their app" [S2], so count only testers opted in to **MYSTERY ROOM's** closed test.
4. **Send the invitation** (replace `<OPT-IN LINK>` and `<FEEDBACK>` with, for example, a Telegram group or an e-mail address):

**EN**
> Subject: Help test MYSTERY ROOM, a new puzzle game for Android
>
> Hi! Thank you for helping me test an app before. I am now testing my new game, MYSTERY ROOM: The Forgotten Institute, a 3D escape-room mystery (offline, no ads, in English, Russian and Uzbek). Google Play requires a closed test, and I would be very grateful if you joined. This is a separate test.
> 1. On your Android phone, open this link while signed in with the Google account you use on Google Play (this e-mail address): <OPT-IN LINK>
> 2. Tap the button to join the test, then install the game from Google Play using the link on the same page.
> 3. Please stay in the test for at least 14 days in a row: do not leave the test, keep the game installed and open it a few times.
> 4. Tell me what you think: <FEEDBACK>
>
> The game collects no data. After the 14 days you can leave the test at any time. Thank you!

**RU**
> Тема: Помогите протестировать MYSTERY ROOM — новую игру-головоломку для Android
>
> Здравствуйте! Спасибо, что раньше помогали тестировать моё приложение. Сейчас я тестирую новую игру — MYSTERY ROOM: The Forgotten Institute, 3D-квест в жанре «комната-побег» (работает без интернета, без рекламы, на русском, узбекском и английском). Google Play требует закрытого тестирования, и я буду очень благодарен, если вы присоединитесь. Это отдельный тест.
> 1. Откройте эту ссылку на Android-телефоне под тем аккаунтом Google, который используется в Google Play (этот e-mail): <ССЫЛКА>
> 2. Нажмите кнопку участия в тестировании, затем установите игру из Google Play по ссылке на той же странице.
> 3. Пожалуйста, оставайтесь в тесте не меньше 14 дней подряд: не выходите из теста, не удаляйте игру и иногда открывайте её.
> 4. Напишите своё мнение: <КАНАЛ ДЛЯ ОТЗЫВОВ>
>
> Игра не собирает никаких данных. После 14 дней вы можете выйти из теста в любой момент. Спасибо!

**UZ**
> Mavzu: MYSTERY ROOM — Android uchun yangi jumboq oʻyinini sinashga yordam bering
>
> Assalomu alaykum! Avval ilovamni sinashda yordam berganingiz uchun rahmat. Hozir yangi oʻyinim — MYSTERY ROOM: The Forgotten Institute'ni sinayapman. Bu 3D sirli «qochish xonasi» oʻyini: internetsiz ishlaydi, reklamasiz, oʻzbek, rus va ingliz tillarida. Google Play yopiq test oʻtkazishni talab qiladi, qoʻshilsangiz juda minnatdor boʻlaman. Bu alohida test.
> 1. Android telefoningizda Google Play'da ishlatadigan Google hisobingiz (shu email) bilan ushbu havolani oching: <HAVOLA>
> 2. Testga qoʻshilish tugmasini bosing, soʻng oʻsha sahifadagi havola orqali oʻyinni Google Play'dan oʻrnating.
> 3. Iltimos, kamida 14 kun ketma-ket testda qoling: testdan chiqmang, oʻyinni oʻchirmang va uni bir necha marta oching.
> 4. Fikringizni yozing: <FIKR-MULOHAZA KANALI>
>
> Oʻyin hech qanday maʼlumot toʻplamaydi. 14 kundan keyin xohlagan paytda testdan chiqishingiz mumkin. Rahmat!

## 9. Updating the test build (procedure the director can repeat)
Prerequisites:
- steps 1–3 of section 2 are done;
- for one-run uploads, `PLAY_SERVICE_ACCOUNT_JSON` exists and the owner's approval is on record.

1. **Code ready.** `tools/run_tests.sh` passes locally, and the commit is pushed to `main`.
2. **Release notes.** Edit `docs/release/whatsnew/whatsnew-en-US` and `whatsnew-ru-RU` (≤ 500 characters each; Play has no Uzbek), then commit and push.
   - Send the UZ text to testers in the feedback chat.
   - Current notes, the first test build (a template for the next ones):
     - **EN:** Test build. Please play Chapter 1 "The Locked Laboratory" to the end and tell us: where you got stuck and which hint helped, any text that is cut off, and how smoothly it runs on your phone (model and Android version). Thank you for testing!
     - **RU:** Тестовая сборка. Пройдите, пожалуйста, Главу 1 «Запертая лаборатория» до конца и напишите нам: где вы застряли и какая подсказка помогла, есть ли обрезанный текст и насколько плавно игра идёт на вашем телефоне (модель и версия Android). Спасибо за помощь!
     - **UZ (Telegram / e-mail only):** Test versiyasi. Iltimos, 1-bob «Qulflangan laboratoriya»ni oxirigacha oʻynang va bizga yozing: qayerda qotib qoldingiz va qaysi maslahat yordam berdi, kesilib qolgan matn bormi, oʻyin telefoningizda qanchalik silliq ishlaydi (model va Android versiyasi). Sinaganingiz uchun rahmat!
3. **One workflow run.** Actions → "Android build" → *Run workflow* on `main`. Or use the GitHub MCP `actions_run_trigger` (`run_workflow`, `workflow_id: android.yml`, `ref: main`). Inputs:
   - `build_type: release`, `upload_to_play: true`;
   - `play_track: alpha` during the 14-day closed test (`internal` for internal-only builds);
   - `play_status: draft` (the owner presses *Start rollout*) or `completed` (rolls out at once; closed tracks still go through Google's review);
   - `version_name`, for example `0.1.1` (raise it with every build);
   - `beta_unlock: true` for test builds.
4. **Check the run log.**
   - Preflight lists the secrets as `true`.
   - The verify step prints `package=com.mysteryroom.forgotteninstitute`, `versionCode=<run number>`, `targetSdk=36`, `permissions: android.permission.VIBRATE`, `ABIs: arm64-v8a …`, `signer SHA-256: E5:D8:42:…:D1:3E` and `beta_unlock … true (requested: true)`.
   - The upload step is green.
5. **If something fails:** fix it and start a **new** run, never *Re-run* (re-runs keep the old versionCode). "Version code already used" means a new run is needed.
6. **Testers** get the update automatically through Google Play; the 14-day count is about opt-in, not about builds.
7. **Log it** in the table below.

**Production (later):**
- Build a **fresh** AAB with `beta_unlock=false`; the verify step must print `beta_unlock … false`.
- Upload it to production by hand: this workflow cannot target production.
- **Never** use *Promote release* from a test track to production: test bundles carry `beta_unlock`.

| Date | Run # = versionCode | versionName | Track / status | beta_unlock | Notes |
|---|---|---|---|---|---|
| — | — | — | — | — | No release run yet (secrets missing on 2026-10-08) |
| 2026-10-09 | 2 (local build, not CI) | 0.1.0 | internal / first manual upload by the owner | true | Built from `cbd51ab` with the upload key; AAB SHA-256 `908b2e72…4cd4894`. See "First manual upload (2026-10-09)" |

## 10. Risks and open points
- **Secrets and the first release run are unverified on CI.** The local Gradle build used JDK 21; CI uses JDK 17, which AGP 8.6.1 supports.
  - The template asks for NDK `29.0.14206865` for symbol stripping. The local build succeeded without any NDK.
  - On the runner, AGP may download the NDK or skip stripping. Either way the libraries are already release builds.
- **armeabi-v7a in the AAB.** 32-bit-only phones are low-end. The game was never run on one (the debug APK is arm64 only), and 3D performance there is likely poor.
  - Recommendation for the owner and director: drop `architectures/armeabi-v7a` from the "Android AAB" preset before the closed test, so testers and buyers get only the tested ABI.
  - Not changed here: it is a reach decision, and another agent is editing `export_presets.cfg` right now.
- **Size.** About 156 MB per arm64 device today. Chapters 3–4 may cross 200 MB, after which mobile-data users see a size dialog [S4]. Still far below the 500 MB and 1.5 GB limits.
- **beta_unlock.** The preset edit on the runner was not executed locally (blocked by this session's permission policy). The verify step catches a mismatch on the first release run, before any upload.
  - Production safety relies on the rules in section 9: a fresh `beta_unlock=false` build, and no *Promote release*.
- **First upload by hand.** It is required [S11], so "one run does the upload" applies from the second build on.
- **Node 20 deprecation warnings** (`actions/cache@v4`, `setup-java@v4`, `upload-artifact@v4`). They still run, on Node 24. Upgrading them later is optional and was not tested.

## Sources
| Tag | Official page |
|---|---|
| S1 | Android Developers — Meet Google Play's target API level requirement: https://developer.android.com/google/play/requirements/target-sdk |
| S2 | Play Console Help — App testing requirements for new personal developer accounts: https://support.google.com/googleplay/android-developer/answer/14151465 |
| S3 | Play Console Help — Set up an open, closed, or internal test: https://support.google.com/googleplay/android-developer/answer/9845334 |
| S4 | Play Console Help — Optimize your app's size and stay within Google Play app size limits: https://support.google.com/googleplay/android-developer/answer/9859372 |
| S5 | Play Console Help — Translate and localize your app (list of available languages): https://support.google.com/googleplay/android-developer/answer/9844778 |
| S6 | Google Play Developer API — Getting started: https://developers.google.com/android-publisher/getting_started |
| S7 | Play Console Help — Add developer account users and manage permissions: https://support.google.com/googleplay/android-developer/answer/9844686 |
| S8 | Play Console Help — Choose a developer account type: https://support.google.com/googleplay/android-developer/answer/13634885 |
| S9 | Play Console Help — Provide information for Google Play's Data safety section: https://support.google.com/googleplay/android-developer/answer/10787469 |
| S10 | Android Developers — Support 16 KB page sizes: https://developer.android.com/guide/practices/page-sizes |
| S11 | r0adkll/upload-google-play README (the upload action used by the workflow; not a Google page): https://github.com/r0adkll/upload-google-play |
