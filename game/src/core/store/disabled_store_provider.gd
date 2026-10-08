class_name DisabledStoreProvider
extends StoreProvider
## Release builds while REAL_PAYMENTS_ENABLED is false: the store politely reports "coming soon".


func purchase(_product: String) -> Dictionary:
	return {"ok": false, "message": "store_unavailable"}


func store_name() -> String:
	return "disabled"
