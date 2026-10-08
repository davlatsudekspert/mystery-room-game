class_name GooglePlayStoreProvider
extends StoreProvider
## Placeholder for the GodotGooglePlayBilling plugin integration (docs/MONETIZATION.md).
## Intentionally inert until the Play Console product "full_game" exists and server-side validation is designed.


func purchase(_product: String) -> Dictionary:
	return {"ok": false, "message": "store_not_configured"}


func store_name() -> String:
	return "google_play"
