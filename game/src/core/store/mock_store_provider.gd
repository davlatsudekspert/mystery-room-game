class_name MockStoreProvider
extends StoreProvider
## Debug/testing store: purchases succeed instantly, nothing is charged. Never used in release builds.

var purchased: Array[String] = []


func purchase(product: String) -> Dictionary:
	if not purchased.has(product):
		purchased.append(product)
	return {"ok": true, "message": "mock_ok"}


func restore() -> Array[String]:
	return purchased.duplicate()


func store_name() -> String:
	return "mock"
