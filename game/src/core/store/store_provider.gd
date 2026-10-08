class_name StoreProvider
extends RefCounted
## Purchase backend interface. Implementations must be synchronous-safe for the mock and
## wrap async platform callbacks for real stores (to be completed when products are configured).


func purchase(_product: String) -> Dictionary:
	return {"ok": false, "message": "not_implemented"}


func restore() -> Array[String]:
	return []


func store_name() -> String:
	return "none"
