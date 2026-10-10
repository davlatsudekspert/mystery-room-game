class_name GooglePlayStoreProvider
extends StoreProvider
## Google Play Billing through the official GodotGooglePlayBilling plugin 3.3.0 (godot-sdk-integrations, MIT;
## Play Billing Library 9.1.0; Android plugin v2, docs/MONETIZATION.md). This talks to the plugin's JNI singleton
## directly, with the same calls as the plugin's own BillingClient.gd. The game therefore builds and runs without
## the plugin (it is added to the Gradle build only when billing is included), and the tests can pass a fake.
##
## Flow: startConnection → connected → queryProductDetails (price) + queryPurchases (silent ownership sync).
## purchase(): the plugin needs the product details first, so a purchase waits for them. Every PURCHASED purchase
## that is not acknowledged yet is acknowledged at once: Play refunds a purchase that stays unacknowledged for
## three days. A PENDING purchase (cash, bank transfer) grants nothing until Play reports it PURCHASED, either live
## (on_purchase_updated) or at a later start-up sync.

const SINGLETON := "GodotGooglePlayBilling"
const SIGNALS: Array[String] = ["connected", "disconnected", "connect_error", "query_product_details_response",
	"query_purchases_response", "on_purchase_updated", "acknowledge_purchase_response", "consume_purchase_response"]

# BillingClient.BillingResponseCode (Play Billing Library)
const OK := 0
const USER_CANCELED := 1
const SERVICE_UNAVAILABLE := 2
const BILLING_UNAVAILABLE := 3
const ITEM_UNAVAILABLE := 4
const DEVELOPER_ERROR := 5
const ERROR := 6
const ITEM_ALREADY_OWNED := 7
const ITEM_NOT_OWNED := 8
const NETWORK_ERROR := 12
const SERVICE_DISCONNECTED := -1
const FEATURE_NOT_SUPPORTED := -2
const SERVICE_TIMEOUT := -3
# Purchase.PurchaseState
const STATE_PURCHASED := 1
const STATE_PENDING := 2

var _billing: Object
var _products := PackedStringArray()
var _started := false
var _connected := false
var _connecting := false
var _details := {} # product → true once Play returned its details (the plugin needs them before purchase())
var _prices := {} # product → formatted price
var _want_purchase := "" # a purchase waiting for the connection or the product details
var _in_flight := "" # the product whose Play purchase sheet is open
var _restoring := false
var _tokens := {} # product → purchase token of an owned purchase (only for the tester reset; never printed)
var _acking := {} # purchase tokens acknowledged (or being acknowledged) in this session


func _init(billing: Object = null) -> void:
	_billing = billing


func start(products: PackedStringArray) -> void:
	_products = products
	if _billing == null or _started:
		return
	_started = true
	_billing.call("initPlugin")
	_billing.connect("connected", _on_connected, _flags())
	_billing.connect("disconnected", _on_disconnected, _flags())
	_billing.connect("connect_error", _on_connect_error, _flags())
	_billing.connect("query_product_details_response", _on_details, _flags())
	_billing.connect("query_purchases_response", _on_purchases, _flags())
	_billing.connect("on_purchase_updated", _on_purchase_updated, _flags())
	_billing.connect("acknowledge_purchase_response", _on_acknowledged, _flags())
	_billing.connect("consume_purchase_response", _on_consumed, _flags())
	_connect()


func purchase(product: String) -> void:
	if _billing == null:
		purchase_result.emit(product, Result.FAILED, "ui.store_unavailable")
		return
	if _in_flight != "" or _want_purchase != "":
		purchase_result.emit(product, Result.FAILED, "store.busy")
		return
	if _connected and _details.has(product):
		_launch(product)
		return
	_want_purchase = product
	if _connected:
		_billing.call("queryProductDetails", _products, "inapp")
	else:
		_connect()


func restore() -> void:
	if _billing == null:
		restore_done.emit(false, "ui.store_unavailable")
		return
	_restoring = true
	if _connected:
		_billing.call("queryPurchases", "inapp", false)
	else:
		_connect() # _on_connected queries the purchases


## Consumes the owned test purchase, so the same Play account can buy it again (Play keeps one-time products owned
## until they are consumed or refunded). Tester builds only.
func reset_for_testing(product: String) -> String:
	if _billing == null:
		return "ui.store_unavailable"
	var token := str(_tokens.get(product, ""))
	if token != "":
		_tokens.erase(product)
		_billing.call("consumePurchase", token)
	return "store.reset_done"


func is_open() -> bool:
	return _billing != null


func store_name() -> String:
	return "google_play"


func price(product: String) -> String:
	return str(_prices.get(product, ""))


func _connect() -> void:
	if _connected or _connecting:
		return
	_connecting = true
	_billing.call("startConnection")


func _launch(product: String) -> void:
	_in_flight = product
	var r: Variant = _billing.call("purchase", product, "", "", false)
	var code := int((r as Dictionary).get("response_code", ERROR)) if r is Dictionary else ERROR
	if code == OK:
		return # the Play purchase sheet is open; the answer comes through on_purchase_updated
	_in_flight = ""
	_log("purchase could not start, code %d" % code)
	if code == ITEM_ALREADY_OWNED:
		_already_owned(product)
	else:
		purchase_result.emit(product, Result.FAILED, message_for(code))


## Play says the player owns it already (bought on another device, or a re-install): grant it, and read the
## purchase list so an unacknowledged purchase is acknowledged.
func _already_owned(product: String) -> void:
	owned.emit(product)
	purchase_result.emit(product, Result.PURCHASED, "store.already_owned")
	if _connected:
		_billing.call("queryPurchases", "inapp", false)


func _on_connected() -> void:
	_connecting = false
	_connected = true
	_billing.call("queryProductDetails", _products, "inapp")
	_billing.call("queryPurchases", "inapp", false)


func _on_disconnected() -> void:
	# The plugin reconnects by itself (enableAutoServiceReconnection); otherwise the next request reconnects.
	_connected = false
	_connecting = false


func _on_connect_error(code: int, _debug_message: String) -> void:
	_connecting = false
	_connected = false
	_log("connection failed, code %d" % code)
	var msg := message_for(code)
	if _want_purchase != "":
		var p := _want_purchase
		_want_purchase = ""
		purchase_result.emit(p, Result.FAILED, msg)
	if _restoring:
		_restoring = false
		restore_done.emit(false, msg if msg == "store.billing_unavailable" else "store.restore_failed")


func _on_details(r: Dictionary) -> void:
	var code := int(r.get("response_code", ERROR))
	if code == OK:
		for d: Variant in _array(r.get("product_details")):
			if not d is Dictionary:
				continue
			var id := str((d as Dictionary).get("product_id", ""))
			var offers := _array((d as Dictionary).get("one_time_purchase_offer_details_list"))
			var p := str((offers[0] as Dictionary).get("formatted_price", "")) if not offers.is_empty() and offers[0] is Dictionary else ""
			_details[id] = true
			_prices[id] = p
			product_info.emit(id, p)
	else:
		_log("product details failed, code %d" % code)
	if _want_purchase != "":
		var want := _want_purchase
		_want_purchase = ""
		if _details.has(want):
			_launch(want)
		else:
			purchase_result.emit(want, Result.FAILED, message_for(code) if code != OK else "store.not_found")


func _on_purchase_updated(r: Dictionary) -> void:
	var code := int(r.get("response_code", ERROR))
	var product := _in_flight
	_in_flight = ""
	if code == OK:
		var states := _handle_all(_array(r.get("purchases")))
		if product == "":
			return # a pending payment completed, or a purchase made outside the game: already granted above
		match int(states.get(product, 0)):
			STATE_PURCHASED:
				purchase_result.emit(product, Result.PURCHASED, "ui.purchase_ok")
			STATE_PENDING:
				purchase_result.emit(product, Result.PENDING, "store.pending")
			_:
				purchase_result.emit(product, Result.FAILED, "store.error")
		return
	if product == "":
		_log("purchase update without an open purchase, code %d" % code)
		return
	if code == USER_CANCELED:
		purchase_result.emit(product, Result.CANCELLED, "store.cancelled")
	elif code == ITEM_ALREADY_OWNED:
		_already_owned(product)
	else:
		_log("purchase failed, code %d" % code)
		purchase_result.emit(product, Result.FAILED, message_for(code))


func _on_purchases(r: Dictionary) -> void:
	var code := int(r.get("response_code", ERROR))
	if code != OK:
		_log("purchase list failed, code %d" % code)
		if _restoring:
			_restoring = false
			restore_done.emit(false, "store.billing_unavailable" if code == BILLING_UNAVAILABLE else "store.restore_failed")
		return
	var states := _handle_all(_array(r.get("purchases")))
	if _restoring:
		_restoring = false
		var vals := states.values()
		if vals.has(STATE_PURCHASED):
			restore_done.emit(true, "ui.restored")
		elif vals.has(STATE_PENDING):
			restore_done.emit(true, "store.pending")
		else:
			restore_done.emit(true, "store.restore_none")


## Grants every PURCHASED purchase of our products and acknowledges the ones Play has not seen acknowledged.
## Returns product → purchase state.
func _handle_all(purchases: Array) -> Dictionary:
	var states := {}
	for p: Variant in purchases:
		if not p is Dictionary:
			continue
		var d := p as Dictionary
		var state := int(d.get("purchase_state", 0))
		var token := str(d.get("purchase_token", ""))
		for id: Variant in _array(d.get("product_ids")):
			var pid := str(id)
			if not _products.has(pid):
				continue
			if state == STATE_PURCHASED or not states.has(pid):
				states[pid] = state
			if state != STATE_PURCHASED:
				continue
			if token != "":
				_tokens[pid] = token
			if not bool(d.get("is_acknowledged", false)) and token != "" and not _acking.has(token):
				_acking[token] = true
				_billing.call("acknowledgePurchase", token)
			owned.emit(pid)
	return states


func _on_acknowledged(r: Dictionary) -> void:
	var code := int(r.get("response_code", ERROR))
	if code != OK:
		# not acknowledged: the next purchase-list read (next start, or Restore) tries again, well within 3 days
		_acking.erase(str(r.get("token", "")))
		_log("acknowledge failed, code %d (retried at the next start)" % code)


func _on_consumed(r: Dictionary) -> void:
	_log("test purchase consumed, code %d" % int(r.get("response_code", ERROR)))


## The message key for a Play Billing response code.
static func message_for(code: int) -> String:
	match code:
		OK:
			return "ui.purchase_ok"
		USER_CANCELED:
			return "store.cancelled"
		SERVICE_UNAVAILABLE, NETWORK_ERROR, SERVICE_TIMEOUT, SERVICE_DISCONNECTED:
			return "store.network"
		BILLING_UNAVAILABLE, FEATURE_NOT_SUPPORTED:
			return "store.billing_unavailable"
		ITEM_UNAVAILABLE:
			return "store.not_found"
		ITEM_ALREADY_OWNED:
			return "store.already_owned"
	return "store.error"


static func _array(v: Variant) -> Array:
	if v is Array:
		return v
	if v is PackedStringArray:
		return Array(v)
	return []


func _log(text: String) -> void:
	print("Store(google_play): " + text)
