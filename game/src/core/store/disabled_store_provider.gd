class_name DisabledStoreProvider
extends StoreProvider
## Release builds while REAL_PAYMENTS_ENABLED is false (and no store_sandbox feature): no store code runs, and the
## game politely says the store is not available yet. The purchase screen is not offered.


func purchase(product: String) -> void:
	purchase_result.emit(product, Result.FAILED, "ui.store_unavailable")


func restore() -> void:
	restore_done.emit(false, "ui.store_unavailable")


func store_name() -> String:
	return "disabled"
