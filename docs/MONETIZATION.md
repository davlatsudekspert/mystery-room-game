# Monetization: Fair Premium

| Rule | Implementation |
|---|---|
| Chapter 1 free | `Chapters.LIST[0].product == ""`, so `Premium.can_play("ch1")` is always true |
| One-time full-game unlock | Product `full_game` unlocks chapters 2–4. Future chapters can be added to the same product or sold separately (`product` field per chapter) |
| No ads, no subscriptions, no energy | None exist anywhere in the code. Hints are free and unlimited, with a three-step ladder |
| Restore Purchases | Settings has a **Restore purchases** button that calls `Premium.restore_purchases()` |
| Real payments disabled | `Premium.REAL_PAYMENTS_ENABLED = false`. Debug builds use `MockStoreProvider` and release builds use `DisabledStoreProvider` ("store not available yet") |

## Enabling real payments later
1. Create the in-app product `full_game` (non-consumable) in Google Play Console and App Store Connect.
2. Add the GodotGooglePlayBilling plugin (Android) and a StoreKit 2 plugin (iOS).
3. Implement `GooglePlayStoreProvider` and `AppStoreProvider` (currently inert stubs).
4. Add receipt or purchase-token validation. Server-side validation is recommended; a lightweight option is the platform's own on-device verification plus a signed entitlement cache.
5. Test with license testers (Play) and Sandbox accounts (Apple). Then set `REAL_PAYMENTS_ENABLED = true`.

Suggested price is a single unlock in the $3.99–$5.99 range, set per region by the stores' pricing tiers. The owner decides.
