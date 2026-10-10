# Monetization: Fair Premium

_Last updated: 2026-10-10. Owner decisions of 2026-10-10: one non-consumable product `full_game` unlocks Chapters 2–4
at **US$4.99** (the stores' automatic regional equivalents elsewhere). Apple's Paid Apps agreement, banking (USD) and
tax forms are active. **Real payments stay OFF** until the owner turns them on. The EU DSA trader status is deferred._

| Rule | Implementation |
|---|---|
| Chapter 1 free | `Chapters.LIST[0].product == ""`, so `Premium.can_play("ch1")` is always true |
| One-time full-game unlock | Product `full_game` (non-consumable) unlocks chapters 2–4 (`Premium.PRODUCTS`). Future chapters can join it or be sold separately (`product` field per chapter) |
| No ads, no subscriptions, no energy | None exist anywhere in the code. Hints are free and unlimited |
| Restore Purchases | A visible **Restore purchases** button in Settings **and** on the purchase screen (App Store guideline 3.1.1). It calls `Premium.restore_purchases()`; the answer (restored / none found / error) is shown |
| Real payments disabled | `Premium.REAL_PAYMENTS_ENABLED = false` (`game/src/autoload/premium.gd`). Release builds use `DisabledStoreProvider` unless the build carries the custom feature `store_sandbox` |

## State on 2026-10-10
| Part | State | Verified where |
|---|---|---|
| Purchase logic (`game/src/core/store/`, `Premium`) | Done: price, purchase, pending, cancel/errors, restore, acknowledgement, local entitlement, tester reset | Headless, `tests/test_store.gd` (12 tests with fake Play and StoreKit singletons). Full suite: 163 tests, 0 failures |
| Purchase screen (`src/ui/purchase_panel.gd`) | Done: localized price on the button, status line, Restore, Close; "Reset purchase (test)" in tester/debug builds only | Headless UI test; screenshots EN/RU/UZ (`qa/ui_screens.tscn --shots=purchase`) |
| Android build with billing | `android.yml` inputs `store_sandbox`, `include_billing` | **Local** release AAB (Gradle, throwaway key): the workflow's own verify step passed every check except the signer (expected: not the upload key). **Not yet run on CI or a phone** |
| iOS build with StoreKit | `ios.yml` input `store_sandbox` | **Local** Godot 4.7.2 Xcode export: plugin linked, init registered, StoreKit.framework, In-App Purchase capability; `verify_xcode_project.py --storekit` passed, and failed as intended without the flag. **The macOS archive (compile/link) and a device purchase are not yet run** |
| App Store Connect product | `ios-iap.yml` + `tools/ios/asc_iap.py` written, **not dispatched** | Against a local fake API only: dry run (0 writes), apply, re-apply (0 writes) |
| Google Play product | `play-iap.yml` + `tools/android/play_iap.py` written, **not dispatched** | Against a local fake API only: missing permission → exit 3, no merchant → exit 3, apply, re-apply (0 writes) |

## How it works
`Premium` (autoload) owns the entitlements file `user://entitlements.cfg` and talks to one `StoreProvider`.
Providers never touch the scene tree or the file; every answer is a signal (`product_info`, `purchase_result`,
`owned`, `revoked`, `restore_done`), and every message is a translation key (`store.*`, `ui.*`, EN/RU/UZ in
`localization/strings.csv`).

| Provider | When | Notes |
|---|---|---|
| `MockStoreProvider` | debug builds without a store | answers at once, nothing charged; QA can play pending/cancel/failure |
| `DisabledStoreProvider` | release builds while payments are off | no purchase screen; the chapter list keeps "Coming soon"; Restore says the store is not available yet |
| `GooglePlayStoreProvider` | Android, plugin present, and `REAL_PAYMENTS_ENABLED` or `store_sandbox` | GodotGooglePlayBilling JNI singleton. Connect → product details (price) + purchase list (silent sync). Every PURCHASED, unacknowledged purchase is acknowledged at once (Play refunds after 3 days); a failed acknowledgement is retried at the next purchase-list read (every start). PENDING grants nothing until Play reports PURCHASED. Tester reset consumes the test purchase |
| `AppStoreProvider` | iOS, plugin present, and `REAL_PAYMENTS_ENABLED` or `store_sandbox` | StoreKit 2 via the plugin's `request()` / `response`. Start: `Transaction.updates` listener, prices, unfinished transactions, current entitlements. Restore = `AppStore.sync()` then current entitlements. Unverified transactions are never granted; refunds/revocations remove the entitlement. A `store_sandbox` build installed from the App Store (receipt file `StoreKit/receipt`) stays disabled |

Selection is the pure function `Premium.choose_store()` (tested). Entitlements are granted additively and kept on the
device, so the game plays offline; only an explicit store revocation removes one. Validation is on-device (StoreKit 2
verifies the JWS; Play's purchase list comes from the Play Store app). There is no server.

### Build features (custom export features, added by the workflows on the runner only)
| Feature | Effect |
|---|---|
| `beta_unlock` | Tester builds: paid chapters open without a purchase (`Premium.tester_build()`), **except** in a `store_sandbox` build |
| `store_sandbox` | The real store runs although `REAL_PAYMENTS_ENABLED` is false: TestFlight sandbox, or Play with License testers. Paid chapters stay locked until bought. The workflows refuse `store_sandbox` together with `beta_unlock` |
| (either) | `Premium.tester_tools()`: renderer info in the version line, QA hooks |

"Reset purchase (test)" is shown in tester and debug builds only (`Premium.can_reset_purchase()`). On Android it
consumes the test purchase (buyable again); on iOS it clears the device only and tells the tester to clear the sandbox
account's purchase history in App Store Connect (Users and Access → Sandbox → Test Accounts).

## Plugins (free, MIT; never committed: added on the runner, pinned by SHA-256)
| Platform | Plugin | Version | License | Why |
|---|---|---|---|---|
| Android | [GodotGooglePlayBilling](https://github.com/godot-sdk-integrations/godot-google-play-billing) (godot-sdk-integrations, the official one) | 3.3.0 (2026-07-26), Play Billing Library 9.1.0, Android plugin v2 | MIT | Official, maintained, Godot 4.2+. Release zip SHA-256 `20d75623d6f337f08d8283c83098b73678d5f575e39247af5a8eb80588b18568` (its scripts are identical to tag 3.3.0) |
| iOS | [Godot iOS plugin for In-App purchase](https://github.com/hrk4649/godot_ios_plugin_iap) (hrk4649) | 0.4.0 (2026-06-19), built for Godot 4.7 | MIT | StoreKit 2 in Swift; `.gdip` + static xcframework (debug/release), so only iOS exports are affected; iOS 15 minimum like the game; the author tested Godot 4.7 + Xcode 26.5. Release zip SHA-256 `578800e79f2bcd8719eb00e4f80d036960518ec1b113c7b47626f95a8aeda87a` |

iOS options considered: the official `godot-ios-plugins/inappstore` (StoreKit **1**, and it needs a full Godot iOS
build to compile); Miguel de Icaza's GodotApplePlugins (StoreKit 2 GDExtension, MIT, very active, but iOS **17**
minimum and a SwiftGodot runtime); hyodotdev's godot-iap (needs a post-export embed script, 27 MB). The chosen plugin
is prebuilt against Godot **4.7.0** headers; we run 4.7.2. A C++ ABI change between patch releases is unlikely, and
the macOS archive will fail to link on a symbol mismatch, but a layout change would only show on a device. If it ever
crashes at start-up, rebuild it from source against 4.7.2 on the macOS runner (its `script/build.sh -G 4.7.2 -H` then
`generate_static_library.sh`) or switch to GodotApplePlugins (and raise the iOS minimum to 17).

`tools/store/add_store_plugins.py --android|--ios` downloads, checks the hash, unpacks and enables the plugin
(Android: `[editor_plugins]` in project.godot; iOS: `plugins/IOSInAppPurchase=true` in the iOS preset). `.gitignore`
keeps them out of the repository, so a build without billing cannot declare it by accident.

**What billing adds to the Android app:** `com.android.vending.BILLING`, plus `android.permission.INTERNET` and
`ACCESS_NETWORK_STATE`, which Google's billing library brings in (its `com.google.android.datatransport` dependency).
Today's builds have none of these. `android.yml`'s verify step allows them only when billing is included and requires
them then. Before shipping billing, the owner updates the Play **Data safety** form and the privacy policy wording:
purchases are processed by Google Play / Apple, and the game itself still collects nothing.

## Workflows (manual; the store ones are dry runs by default)
| Workflow | Inputs | Writes to a store? |
|---|---|---|
| `android.yml` | `store_sandbox` (default false; needs `build_type=release`, `beta_unlock=false`), `include_billing` (default false) | Only with `upload_to_play=true` (as before) |
| `ios.yml` | `store_sandbox` (default false; needs `beta_unlock=false`) | Only with `upload_to_testflight=true` (as before) |
| `ios-iap.yml` | `dry_run` (**true**), `territories` (app/all), `review_screenshot` (true: `docs/store/iap/full_game_review.png`) | Only with `dry_run=false`: creates/fixes `full_game` on our app. Never submits |
| `play-iap.yml` | `dry_run` (**true**), `home_currency` (USD) | Only with `dry_run=false`: creates/fixes `full_game` of our package |

`asc_iap.py` sets: NON_CONSUMABLE `full_game`, reference name "Full Game", review note; localizations en-US "Full
Game" / "Unlocks Chapters 2 to 4. One-time purchase.", ru «Полная игра» / «Открывает главы 2–4. Разовая покупка.»
(Uzbek is tried once; App Store Connect has no Uzbek locale); a price schedule based in the USA at the US$4.99 price
point (looked up through the API; Apple equalizes the rest); availability in the app's territories (the app's own
availability is not set up yet, so it reports that and leaves it until then, or use `territories=all`); the review
screenshot. It prints the state and what is still missing for "Ready to Submit".

`play_iap.py` first checks the service account's access and stops (exit 3) naming what is missing: the app permission
"Manage in-app products" (it has only "Release apps to testing tracks"), the payments (merchant) profile, or an
uploaded build that declares BILLING. Owner steps in Uzbek: `docs/release/GOOGLE_PLAY_TESTING.md` §11.

## Testing purchases (before any real payment)
**iOS (TestFlight, never charged):**
1. `ios-iap.yml` with `dry_run=true`, review the plan, then `dry_run=false` (director, after review).
2. `ios.yml` with `store_sandbox=true`, `beta_unlock=false`, `upload_to_testflight=true` (with the owner's approval).
3. Testers buy in the TestFlight build; TestFlight uses the sandbox automatically (no sandbox account needed).
   Check: price shown, purchase, Chapter 2 opens, Restore on a second device, Reset purchase (test).

**Android (internal track, License testers only):**
1. Owner: §11 of `GOOGLE_PLAY_TESTING.md` (permission, merchant profile, License testing list).
2. `android.yml` with `build_type=release`, `include_billing=true`, `beta_unlock=false`, `upload_to_play=true`,
   `play_status=draft` once, so Play knows the app declares BILLING.
3. `play-iap.yml` dry run, then `dry_run=false`.
4. `android.yml` with `store_sandbox=true`, `beta_unlock=false`, upload to `internal`. **Only accounts on the
   License testing list are not charged**; anyone else on the track pays real money.

## Turning real payments on later (exact steps)
1. Both products exist and are active: App Store Connect `full_game` "Ready to Submit" (`ios-iap.yml` result), Google
   Play `full_game` active (`play-iap.yml` result).
2. Sandbox purchase, restore and (Android) acknowledgement were tested on real devices with the `store_sandbox` builds
   above, in EN/RU/UZ.
3. The owner updates the privacy policy and the Play Data safety form (billing adds INTERNET; purchases are processed
   by the stores) and approves going live.
4. Set `const REAL_PAYMENTS_ENABLED := true` in `game/src/autoload/premium.gd`. Update `tests/test_store.gd`
   ("real payments stay off") and `tests/test_settings_premium.gd` in the same commit; run `tools/run_tests.sh`.
5. Build store releases with `beta_unlock=false` and `store_sandbox=false`: `android.yml` adds billing automatically
   when `REAL_PAYMENTS_ENABLED` is true (the verify step then requires BILLING); `ios.yml` adds StoreKit and the
   In-App Purchase capability automatically (the Xcode check then requires them). Never promote a test build.
6. App Store: attach `full_game` to the app version (version page → In-App Purchases) and submit both together (the
   owner submits; no workflow here submits anything).
7. Optional hardening later: Play purchase signature check with the app's licensing public key, and server-side
   validation if fraud appears.
