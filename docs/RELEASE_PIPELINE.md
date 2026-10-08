# Release Pipeline: Android & iOS

**Identifiers (unique to MYSTERY ROOM):**
- Android package / iOS bundle id: `com.mysteryroom.forgotteninstitute`
- Never reuse NFCSTORE ids, keys or workflows.

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
| `android.yml` (release) | ubuntu | Tests, then a Gradle **AAB** signed with the upload key from secrets. Optionally uploaded to **Google Play → Internal testing** as a draft |
| `ios.yml` | macOS 15 | Godot iOS export, Xcode archive with cloud signing, then an IPA, optionally uploaded to **TestFlight**. It stops at the first step if the secrets are missing |

## What the owner must provide (GitHub → Settings → Secrets and variables → Actions)

### Google Play
| Secret | How to get it |
|---|---|
| `ANDROID_KEYSTORE_BASE64` | Create an **upload key** once: `keytool -genkeypair -v -keystore upload.jks -alias upload -keyalg RSA -keysize 4096 -validity 10000`. Then `base64 -w0 upload.jks`. Keep `upload.jks` in a safe place; it must never be committed |
| `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD` | Chosen when creating the key |
| `PLAY_SERVICE_ACCOUNT_JSON` | Play Console → Setup → API access. Create a service account with the "Release manager" role for this app only, and download its JSON key |

Prerequisites:
1. A Google Play developer account. Google charges a **one-time $25 registration fee**, which requires the owner's decision.
2. The app is created in the Play Console with the package name above.
3. Play App Signing is enabled.
4. The first AAB is uploaded manually once. After that, the API can upload.

### Apple App Store / TestFlight (Xcode cloud signing: no Mac or .p12 needed)
| Secret | How to get it |
|---|---|
| `IOS_TEAM_ID` | developer.apple.com → Membership → Team ID |
| `ASC_KEY_ID`, `ASC_ISSUER_ID` | App Store Connect → Users and Access → Integrations → App Store Connect API → "+". The role must be **Admin** (cloud-managed distribution certificates require it) |
| `ASC_KEY_P8_BASE64` | Base64 of the downloaded `AuthKey_XXXX.p8`, from `base64 -i AuthKey_XXXX.p8` |

One-time setup in App Store Connect:
1. Register the bundle id `com.mysteryroom.forgotteninstitute` under developer.apple.com → Identifiers.
2. Create the app record (Apps → "+").

The workflow then:
1. exports the Godot Xcode project. This step is verified on Linux: scheme `MysteryRoom`, bundle id and team set, automatic signing, iOS 15.
2. archives it with `-allowProvisioningUpdates` and the API key, so Xcode manages certificates and profiles.
   - The archive is development-signed (`CODE_SIGN_IDENTITY="Apple Development"`).
   - Godot's Release config asks for "Apple Distribution" with automatic signing, which Xcode rejects as conflicting.
3. re-signs the archive in `-exportArchive` with the cloud-managed distribution certificate and uploads it to TestFlight (`destination=upload`).

## Status (verified in the dev container)
- ✅ Debug APK builds locally:
  - signed (`apksigner verify` OK)
  - arm64-v8a
  - **123 MB** after the mobile texture policy (`tools/build/texture_imports.py`)
- ⏳ Release AAB via Gradle: configured, not yet run, because it needs the Gradle download and the owner's upload key.
- 🔶 iOS:
  - The Xcode project export is verified on Linux.
  - The owner added `IOS_TEAM_ID` and the `ASC_*` secrets on 2026-10-08.
  - Archive, signing and upload need macOS, so they are unverified. The workflow **has not run yet**: it needs the App Store Connect app record and working Actions runners.
- ❌ No physical-device testing yet. FPS, load time and memory on real phones are **not measured**. Container figures come from a software renderer.
