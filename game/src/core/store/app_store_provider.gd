class_name AppStoreProvider
extends StoreProvider
## Placeholder for the iOS StoreKit plugin integration (docs/MONETIZATION.md). Inert until configured.


func purchase(_product: String) -> Dictionary:
	return {"ok": false, "message": "store_not_configured"}


func store_name() -> String:
	return "app_store"
