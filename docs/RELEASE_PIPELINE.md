# Release Pipeline: Android & iOS

**Identifiers (unique to MYSTERY ROOM):**
- Android package / iOS bundle id: `com.mysteryroom.forgotteninstitute`
- Never reuse NFCSTORE ids, keys or workflows.

## Workflows (`.github/workflows/`)
All workflows are **manual** (`workflow_dispatch`). Actions minutes in a private repository count against the account's free quota, and macOS minutes count 10×. Runs therefore happen only when the owner starts them.

| Workflow | Runner | What it does |
|---|---|---|
| `tests.yml` | ubuntu | Headless test suite (`tools/run_tests.sh`) |
| `android.yml` (debug) | ubuntu | Tests, then a debug APK signed with a throw-away debug key, uploaded as an artifact |
| `android.yml` (release) | ubuntu | Tests, then a Gradle **AAB** signed with the upload key from secrets. Optionally uploaded to **Google Play → Internal testing** as a draft |
| `ios.yml` | macOS 15 | Godot iOS export. With signing secrets: a signed IPA, optionally uploaded to **TestFlight**. Without them: the unsigned Xcode project as an artifact |

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

### Apple App Store / TestFlight
| Secret | How to get it |
|---|---|
| `IOS_TEAM_ID` | developer.apple.com → Membership |
| `IOS_DIST_CERT_P12_BASE64`, `IOS_DIST_CERT_PASSWORD` | Create an **Apple Distribution** certificate and export it as .p12 from Keychain (needs a Mac once). Then `base64 -i cert.p12` |
| `IOS_PROVISION_PROFILE_BASE64` | An App Store provisioning profile for the bundle id above, base64-encoded |
| `ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_KEY_P8_BASE64` | App Store Connect → Users and Access → Integrations → App Store Connect API. Create a key with the "App Manager" role |

Prerequisites:
1. Apple Developer Program membership, which costs **$99/year** and requires the owner's decision.
2. An app record in App Store Connect with the bundle id above.

## Status (verified in the dev container)
- ✅ Debug APK builds locally:
  - signed (`apksigner verify` OK)
  - arm64-v8a
  - **123 MB** after the mobile texture policy (`tools/build/texture_imports.py`)
- ⏳ Release AAB via Gradle: configured, not yet run, because it needs the Gradle download and the owner's upload key.
- ❌ iOS: cannot be built or verified here (no macOS/Xcode). The workflow is prepared but **has not been run**.
- ❌ No physical-device testing yet. FPS, load time and memory on real phones are **not measured**. Container figures come from a software renderer.
