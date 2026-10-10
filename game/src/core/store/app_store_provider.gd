class_name AppStoreProvider
extends StoreProvider
## App Store purchases with StoreKit 2, through the iOS plugin "Godot iOS plugin for In-App purchase" 0.4.0
## (hrk4649/godot_ios_plugin_iap, MIT; a .gdip + static xcframework built for Godot 4.7; docs/MONETIZATION.md).
## The plugin singleton "IOSInAppPurchase" has one method, request(name, args) → 0 when the request was accepted,
## and one signal, response(name, data), which it emits from a StoreKit task thread. The connection is deferred,
## so the answers are handled on the main thread.
##
## Requests used: startUpdateTask (Transaction.updates: a pending purchase approved later, a refund, a purchase on
## another device), products (localized price), purchase (Product.purchase(); the plugin finishes verified
## transactions), proceedUnfinishedTransactions, transactionCurrentEntitlements (ownership sync) and appStoreSync
## (the Restore Purchases button: AppStore.sync(), which may ask for the Apple Account password).

const SINGLETON := "IOSInAppPurchase"

var _sk: Object
var _products := PackedStringArray()
var _started := false
var _prices := {}
var _in_flight := ""
var _restoring := false


func _init(store_kit: Object = null) -> void:
	_sk = store_kit


func start(products: PackedStringArray) -> void:
	_products = products
	if _sk == null or _started:
		return
	_started = true
	_sk.connect("response", _on_response, _flags())
	_request("startUpdateTask", {})
	_request("products", {"productIDs": Array(products)})
	_request("proceedUnfinishedTransactions", {})
	_request("transactionCurrentEntitlements", {})


func purchase(product: String) -> void:
	if _sk == null:
		purchase_result.emit(product, Result.FAILED, "ui.store_unavailable")
		return
	if _in_flight != "":
		purchase_result.emit(product, Result.FAILED, "store.busy")
		return
	_in_flight = product
	if not _request("purchase", {"productID": product}):
		_in_flight = ""
		purchase_result.emit(product, Result.FAILED, "store.error")


func restore() -> void:
	if _sk == null:
		restore_done.emit(false, "ui.store_unavailable")
		return
	_restoring = true
	if not _request("appStoreSync", {}):
		_restoring = false
		restore_done.emit(false, "store.restore_failed")


## A sandbox purchase cannot be undone from the device: the entitlement is cleared on this device only, and the
## message tells the tester to clear the sandbox account's purchase history (otherwise the next start-up sync or
## Restore brings it back).
func reset_for_testing(_product: String) -> String:
	return "store.reset_sandbox_hint"


func is_open() -> bool:
	return _sk != null


func store_name() -> String:
	return "app_store"


func price(product: String) -> String:
	return str(_prices.get(product, ""))


## True when this iOS install came from the App Store (its receipt file is "receipt"; TestFlight and Xcode installs
## have "sandboxReceipt" or none). A store_sandbox build never turns real purchases on in an App Store install.
static func app_store_install(bundle_dir: String = "") -> bool:
	if bundle_dir == "":
		bundle_dir = OS.get_executable_path().get_base_dir()
	return FileAccess.file_exists(bundle_dir.path_join("StoreKit/receipt"))


func _request(name: String, args: Dictionary) -> bool:
	var ok := int(_sk.call("request", name, args)) == 0
	if not ok:
		_log("request %s was refused" % name)
	return ok


func _on_response(name: String, data: Dictionary) -> void:
	match name:
		"products":
			_on_products(data)
		"purchase":
			_on_purchase(data)
		"transactionCurrentEntitlements":
			_on_entitlements(data)
		"appStoreSync":
			if str(data.get("result", "")) == "success":
				if not _request("transactionCurrentEntitlements", {}) and _restoring:
					_restoring = false
					restore_done.emit(false, "store.restore_failed")
			elif _restoring:
				_log("App Store sync failed")
				_restoring = false
				restore_done.emit(false, "store.restore_failed")


func _on_products(data: Dictionary) -> void:
	if str(data.get("result", "")) != "success":
		_log("product query failed") # the purchase request fetches the product again by itself
		return
	for p: Variant in _array(data.get("products")):
		if not p is Dictionary:
			continue
		var id := str((p as Dictionary).get("id", ""))
		var price_text := str((p as Dictionary).get("displayPrice", ""))
		_prices[id] = price_text
		product_info.emit(id, price_text)


func _on_purchase(data: Dictionary) -> void:
	var product := str(data.get("productID", ""))
	var result := str(data.get("result", ""))
	# an answer without a product id is an error answer to the open purchase
	var mine := _in_flight != "" and (product == _in_flight or product == "")
	if product == "" and mine:
		product = _in_flight
	if mine:
		_in_flight = ""
	match result:
		"success":
			if _products.has(product):
				owned.emit(product)
			if mine:
				purchase_result.emit(product, Result.PURCHASED, "ui.purchase_ok")
		"revoked":
			if _products.has(product):
				revoked.emit(product)
			if mine:
				purchase_result.emit(product, Result.FAILED, "store.error")
		"pending":
			if mine:
				purchase_result.emit(product, Result.PENDING, "store.pending")
		"userCancelled":
			if mine:
				purchase_result.emit(product, Result.CANCELLED, "store.cancelled")
		"unverified":
			_log("unverified transaction for %s" % product)
			if mine:
				purchase_result.emit(product, Result.FAILED, "store.unverified")
		_:
			_log("purchase answer '%s'" % result)
			if mine:
				var err := str(data.get("error", ""))
				purchase_result.emit(product, Result.FAILED, "store.not_found" if err.begins_with("no productID") else "store.error")


func _on_entitlements(data: Dictionary) -> void:
	if str(data.get("result", "")) != "success":
		_log("entitlement check failed")
		if _restoring:
			_restoring = false
			restore_done.emit(false, "store.restore_failed")
		return
	var found := false
	for t: Variant in _array(data.get("transactions")):
		if not t is Dictionary:
			continue
		var d := t as Dictionary
		var id := str(d.get("productID", ""))
		if not _products.has(id) or d.has("error"): # "error" = StoreKit could not verify it: never granted
			continue
		if str(d.get("revocationDate", "")) != "":
			revoked.emit(id)
			continue
		found = true
		owned.emit(id)
	if _restoring:
		_restoring = false
		restore_done.emit(true, "ui.restored" if found else "store.restore_none")


static func _array(v: Variant) -> Array:
	return v if v is Array else []


func _log(text: String) -> void:
	print("Store(app_store): " + text)
