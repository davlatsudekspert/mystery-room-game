class_name MockStoreProvider
extends StoreProvider
## Debug/testing store: answers at once, nothing is charged. Never used in release builds.
## `next_result` lets tests and QA play the other outcomes (pending, cancelled, failed).

var purchased: Array[String] = []
var price := "$4.99"
var next_result: int = Result.PURCHASED
var next_message := ""


func start(products: PackedStringArray) -> void:
	for p: String in products:
		product_info.emit(p, price)


func purchase(product: String) -> void:
	var result := next_result
	next_result = Result.PURCHASED
	if result == Result.PURCHASED:
		if not purchased.has(product):
			purchased.append(product)
		purchase_result.emit(product, result, "ui.purchase_ok")
		return
	var msg := next_message
	next_message = ""
	if msg == "":
		msg = {Result.PENDING: "store.pending", Result.CANCELLED: "store.cancelled"}.get(result, "store.error")
	purchase_result.emit(product, result, msg)


func restore() -> void:
	for p: String in purchased:
		owned.emit(p)
	restore_done.emit(true, "ui.restored" if not purchased.is_empty() else "store.restore_none")


func reset_for_testing(product: String) -> String:
	purchased.erase(product)
	return "store.reset_done"


func is_open() -> bool:
	return true


func store_name() -> String:
	return "mock"
