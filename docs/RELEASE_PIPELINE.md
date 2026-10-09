# Release Pipeline: Android & iOS

**Identifiers (unique to MYSTERY ROOM):**
- Android package / iOS bundle id: `com.mysteryroom.forgotteninstitute`
- Never reuse NFCSTORE ids, keys or workflows.
- Privacy policy (public, Google Sites): https://sites.google.com/view/mysteryroom-privacy. It is used for Google Play and App Store Connect. Apple also requires a link to it inside the app; see NEXT_STEPS.

## Current state
- GitHub Actions works again (2026-10-08 19:24 UTC). `tests.yml` and the `android.yml` debug build pass on GitHub-hosted runners. Earlier runs had ended after about 3 s with no runner while the account billing block was being lifted.
- Codemagic was evaluated and **cancelled** by the owner. Its config was removed; it can be recovered from commit `c7ffd7e`.
- Meanwhile, Android debug APKs are built and verified locally in the dev container.

## GitHub Actions workflows (`.github/workflows/`)
All workflows are **manual** (`workflow_dispatch`). Actions minutes in a private repository count against the account's free quota, and macOS minutes count 10×. Runs therefore happen only when the owner starts them.

| Workflow | Runner | What it does |
|---|---|---|
| `tests.yml` | ubuntu | Headless test suite (`tools/run_tests.sh`) |
| `android.yml` (debug) | ubuntu | Tests, then a debug APK signed with a throw-away debug key, uploaded as an artifact |
| `android.yml` (release) | ubuntu | A preflight names any missing secret. Then tests and a Gradle **AAB** signed with the upload key from secrets. The AAB is verified: package, versionCode = run number, targetSdk ≥ 36, permissions, arm64, not debuggable, signer = upload-key SHA-256, `beta_unlock` as requested. Optional upload (off by default) to **Internal testing** or **Closed testing (`alpha`)**, as a draft or rolled out, with EN/RU notes from `docs/release/whatsnew/`. `beta_unlock` input for tester builds. Owner checklist: [`docs/release/GOOGLE_PLAY_TESTING.md`](release/GOOGLE_PLAY_TESTING.md) |
| `ios-check.yml` | ubuntu | Read-only App Store Connect check (GET requests only): the MYSTERY ROOM app record, bundle id, localizations, builds and key-role probes |
| `ios.yml` | ubuntu, then macOS 15 | ubuntu: read-only App Store Connect gate, tests, Godot export of the Xcode project and its static checks. macOS (only if those pass): Xcode 26, unsigned archive, IPA signed at export with cloud signing. Optional **TestFlight** upload (off by default); `beta_unlock` input for tester builds |

## What the owner must provide (GitHub → Settings → Secrets and variables → Actions)

### Google Play
The upload key was created on 2026-10-08 and handed to the owner.
- Format: PKCS12, RSA 4096, alias `mysteryroom-upload`, valid until 2054.
- Certificate SHA-256: `E5:D8:42:A6:B8:0E:D2:50:FD:DD:EE:CA:92:64:ED:D7:A6:8B:E1:59:70:A3:AD:8C:06:A7:EC:9C:E8:37:D1:3E`
- It belongs to MYSTERY ROOM only and is never committed. The owner keeps the backup.
- If it is ever lost, Play App Signing lets the owner request an upload-key reset in Play Console.

| Secret | Value |
|---|---|
| `ANDROID_KEYSTORE_BASE64` | Base64 of `mystery-room-upload.keystore` (given to the owner) |
| `ANDROID_KEYSTORE_PASSWORD` | Keystore password (given to the owner). A PKCS12 key uses the same password |
| `ANDROID_KEY_ALIAS` | `mysteryroom-upload` |
| `PLAY_SERVICE_ACCOUNT_JSON` | Optional, only for automatic test-track uploads. It is the JSON key of a Google Cloud service account, invited in Play Console → Users and permissions with the app permission **"Release apps to testing tracks"** for MYSTERY ROOM only and no account permissions. Linking a Cloud project under "API access" is no longer needed. Steps: `docs/release/GOOGLE_PLAY_TESTING.md` §7 |

Prerequisites:
1. A Google Play developer account (the owner has one).
2. The app is created in the Play Console with the package name above.
3. Play App Signing is enabled.
4. The first AAB is uploaded manually once. After that, the API can upload.

`beta_unlock` (default **true**) adds the custom feature `beta_unlock` to the Android presets on the runner only, so testers can open paid chapters while real payments stay disabled (`Premium.tester_build()`).
- **A Play production build must use `beta_unlock=false`.** Build it fresh; never use "Promote release" from a test track to production.
- `android.yml` cannot target the production track.

### Apple App Store / TestFlight (Xcode cloud signing: no Mac or .p12 needed)
Full details, record facts and the owner checklist: [`docs/release/IOS_TESTFLIGHT.md`](release/IOS_TESTFLIGHT.md).

| Secret | How to get it |
|---|---|
| `IOS_TEAM_ID` | developer.apple.com → Membership → Team ID |
| `ASC_KEY_ID`, `ASC_ISSUER_ID` | App Store Connect → Users and Access → Integrations → App Store Connect API → "+". The role must be **Admin** (cloud-managed distribution certificates require it) |
| `ASC_KEY_P8_BASE64` | The `.p8` key, base64-encoded (`base64 -i AuthKey_XXXX.p8`). The stored secret is the key body without its BEGIN/END lines; `tools/ios/asc_check.py` accepts that and the other common forms |

App Store Connect (checked read-only on 2026-10-09):
- The app record "Mystery Room: Lost Institute" (app id `6820786933`, SKU `MYSTERYROOM-FI-001`, `en-US`) exists.
- It uses the registered bundle id `com.mysteryroom.forgotteninstitute`, the same as the repo.
- No builds yet.

`ios.yml` (manual; `upload_to_testflight` defaults to **false**):
1. **ubuntu** runs `asc_check.py --gate`.
   - It fails unless the bundle id is registered and used by the app record, so automatic signing never registers a new App ID.
   - Build number = max(highest App Store Connect build + 1, run number).
   - Then it runs the tests, the Godot export of the Xcode project and `tools/ios/verify_xcode_project.py`:
     - bundle id, version, team, automatic signing;
     - `ITSAppUsesNonExemptEncryption=false`, full screen, landscape;
     - purpose strings, privacy manifest;
     - icons without alpha;
     - `beta_unlock` present or absent as requested.
2. **macOS 15** selects Xcode 26 (the iOS 26 SDK has been required since 2026-04-28) and archives **unsigned**.
3. `-exportArchive` (`app-store-connect`, automatic signing, `-allowProvisioningUpdates` with the API key) signs with the cloud-managed Apple Distribution certificate.
   - No development certificate or registered device is needed.
   - The IPA is verified; with `upload_to_testflight=true` it is uploaded instead.
4. `beta_unlock` (default **true** for TestFlight builds) adds the custom feature `beta_unlock` to the iOS preset on the runner only. **An App Store release build must use `beta_unlock=false`.**

## Status (verified in the dev container)
- ✅ Debug APK builds locally (2026-10-09, commit `02e5776`):
  - signed v2 + v3 (`apksigner verify` OK);
  - arm64-v8a only;
  - targetSdk 36, minSdk 24;
  - `VIBRATE` is the only permission;
  - 16 KB aligned;
  - **192 MB**. It grew with the Chapter 2 content; run #5 on 2026-10-08 was 133 MB.
- ✅ Release AAB via Gradle builds locally (2026-10-09, signed with a throw-away test key, not the upload key):
  - **182 MB**;
  - estimated arm64 download ≈ 156 MB (bundletool);
  - `PAGE_ALIGNMENT_16K`;
  - the CI verify step ran on it and correctly rejected the non-upload-key signature.
- ⏳ Release AAB on GitHub Actions: **not run yet**. Run #5 (`37856877382`, a debug build) showed `ANDROID_KEYSTORE_BASE64` empty. It waits for the owner's 3 `ANDROID_*` secrets. Uploads to Play wait for the owner's approval.
- 🔶 iOS:
  - The App Store Connect record and bundle id match, verified on an ubuntu runner (read-only).
  - The Xcode project export and its static checks pass on Linux and on an ubuntu runner.
  - Archive and cloud signing on a macOS runner are verified (run 37920931317, upload off):
    - signed App Store IPA, 150 MB, build 1;
    - Xcode 26.3 with the iOS 26.2 SDK;
    - App Store profile; `codesign --verify` OK.
  - TestFlight upload: **not done**. It waits for the owner's approval.
- ❌ No physical-device testing yet. FPS, load time and memory on real phones are **not measured**. Container figures come from a software renderer.
