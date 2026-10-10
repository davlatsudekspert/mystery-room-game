class_name StoreProvider
extends RefCounted
## Purchase backend interface (docs/MONETIZATION.md). Every answer arrives through a signal, so the real stores
## (asynchronous platform callbacks) and the mock (answers at once) look the same to Premium.
##
## `message` arguments are translation keys (store.* / ui.*): Premium and the purchase panel show tr(message).
## A provider never touches the scene tree and never writes the entitlement file; Premium does both.

enum Result { PURCHASED, PENDING, CANCELLED, FAILED }

## The store answered a product query: `price` is the store's localized price string ("$4.99", "449 ₽"), or ""
## while unknown.
signal product_info(product: String, price: String)
## The answer to purchase(product).
signal purchase_result(product: String, result: int, message: String)
## The store says the player owns `product` (start-up sync, restore, a pending payment that completed later, a
## purchase made outside the game). Premium grants it.
signal owned(product: String)
## The store says a previous purchase of `product` was refunded or revoked. Premium removes it.
signal revoked(product: String)
## The answer to restore(). `message` is ui.restored, store.restore_none or an error key.
signal restore_done(ok: bool, message: String)

## Every message key a provider may send (each has EN/RU/UZ text in localization/strings.csv).
const MESSAGES: Array[String] = ["ui.purchase_ok", "ui.restored", "ui.store_unavailable", "store.pending",
	"store.cancelled", "store.network", "store.billing_unavailable", "store.not_found", "store.already_owned",
	"store.unverified", "store.error", "store.busy", "store.restore_none", "store.restore_failed", "store.reset_done",
	"store.reset_sandbox_hint"]

## False makes signal handlers on platform singletons run immediately instead of at the next idle frame. Only the
## tests turn it off: on a device the plugins answer from their own threads, and a deferred call brings the answer
## back to the main thread.
var deferred := true


## Connects to the store, asks for the products' prices and silently checks what the player already owns.
func start(_products: PackedStringArray) -> void:
	pass


func purchase(product: String) -> void:
	purchase_result.emit(product, Result.FAILED, "store.error")


func restore() -> void:
	restore_done.emit(false, "ui.store_unavailable")


## Tester builds only (Premium.reset_purchase_for_testing): makes the product purchasable again where the store
## allows it. Returns the message to show.
func reset_for_testing(_product: String) -> String:
	return "store.reset_done"


## True when the game should offer the purchase screen (the store can be reached in this build).
func is_open() -> bool:
	return false


func store_name() -> String:
	return "none"


func _flags() -> int:
	return CONNECT_DEFERRED if deferred else 0
