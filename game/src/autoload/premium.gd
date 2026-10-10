extends Node
## Entitlements and purchases behind a provider interface (docs/MONETIZATION.md).
## Chapters 1 and 2 are free; the one purchase "full_game" unlocks Chapters 3 and 4 (owner, 2026-10-10). Real payments stay DISABLED until the owner sets REAL_PAYMENTS_ENABLED = true after
## store validation. Tester builds with the custom export feature "store_sandbox" use the real store's sandbox:
## TestFlight purchases are always sandbox (never charged); on Google Play only License testers are not charged.

signal entitlements_changed
## The answer to purchase(). ok = the product is owned now. `message` is a translation key (store.* / ui.*).
signal purchase_finished(product: String, ok: bool, message: String)
## The answer to restore_purchases(). `message` is a translation key.
signal restore_finished(ok: bool, message: String)
## The store reported a product's localized price ("$4.99", "449 ₽"; "" while unknown).
signal price_changed(product: String, price: String)
## A purchase or a restore started ("full_game", "restore") or ended ("").
signal busy_changed(what: String)

const REAL_PAYMENTS_ENABLED := false
const PRODUCTS := {"full_game": {"chapters": ["ch3", "ch4"]}} # must match the "product" fields in Chapters.LIST
const PATH := "user://entitlements.cfg"

var provider: StoreProvider
var owned: Dictionary = {}
var path := PATH
var prices: Dictionary = {}
## What the store is busy with: a product id during a purchase, "restore" during a restore, "" when idle.
var busy := ""


func _ready() -> void:
	_load()
	use_provider(_pick_provider())


## Switches the purchase backend (start-up, and the tests' fake stores) and starts it: connect, prices, a silent
## ownership sync.
func use_provider(p: StoreProvider) -> void:
	if provider != null:
		for pair: Array in _provider_signals():
			if provider.is_connected(pair[0], pair[1]):
				provider.disconnect(pair[0], pair[1])
	provider = p
	prices = {}
	_set_busy("")
	for pair: Array in _provider_signals():
		provider.connect(pair[0], pair[1])
	provider.start(PackedStringArray(PRODUCTS.keys()))


func _provider_signals() -> Array:
	return [[&"product_info", _on_product_info], [&"purchase_result", _on_purchase_result], [&"owned", _on_owned],
		[&"revoked", _on_revoked], [&"restore_done", _on_restore_done]]


func _pick_provider() -> StoreProvider:
	var platform := "android" if OS.has_feature("android") else ("ios" if OS.has_feature("ios") else "other")
	var singletons: Array[String] = []
	for s: String in [GooglePlayStoreProvider.SINGLETON, AppStoreProvider.SINGLETON]:
		if Engine.has_singleton(s):
			singletons.append(s)
	var kind := choose_store(REAL_PAYMENTS_ENABLED, store_sandbox(), OS.is_debug_build(), platform, singletons,
		platform == "ios" and AppStoreProvider.app_store_install())
	print("Store: %s (real payments %s, store_sandbox %s)" % [kind, REAL_PAYMENTS_ENABLED, store_sandbox()])
	match kind:
		"google_play":
			return GooglePlayStoreProvider.new(Engine.get_singleton(GooglePlayStoreProvider.SINGLETON))
		"app_store":
			return AppStoreProvider.new(Engine.get_singleton(AppStoreProvider.SINGLETON))
		"mock":
			return MockStoreProvider.new()
	return DisabledStoreProvider.new()


## Which store this build uses: "google_play", "app_store", "mock" (debug builds) or "disabled".
## The real stores run only when REAL_PAYMENTS_ENABLED is true or the build carries the custom feature
## store_sandbox, and only when the platform's billing plugin is in the build. A store_sandbox build that somehow
## reached the App Store (its receipt says so) stays disabled, so a tester build never charges a real customer.
static func choose_store(real_enabled: bool, sandbox: bool, debug: bool, platform: String, singletons: Array,
		app_store_install: bool) -> String:
	if real_enabled or sandbox:
		if platform == "android" and singletons.has(GooglePlayStoreProvider.SINGLETON):
			return "google_play"
		if platform == "ios" and singletons.has(AppStoreProvider.SINGLETON):
			return "app_store" if real_enabled or not app_store_install else "disabled"
	return "mock" if debug else "disabled"


func has_entitlement(product: String) -> bool:
	return bool(owned.get(product, false))


func can_play(chapter_id: String) -> bool:
	var ch := Chapters.get_chapter(chapter_id)
	if ch.is_empty() or not ch.get("released", false):
		return false
	return owns_chapter(chapter_id)


## The player may play this chapter once it is released: it is free, its product is owned, or a beta_unlock build.
func owns_chapter(chapter_id: String) -> bool:
	var ch := Chapters.get_chapter(chapter_id)
	if ch.is_empty():
		return false
	var product: String = ch.get("product", "")
	return product == "" or has_entitlement(product) or tester_build()


## Test builds for Google Play internal/closed testing and TestFlight open every released chapter without any
## purchase: their export adds the custom feature "beta_unlock" (docs/RELEASE_PIPELINE.md). Store releases never
## carry it. A store_sandbox build tests the purchase itself, so there the paid chapters stay locked until bought.
func tester_build() -> bool:
	return unlocks_without_purchase(OS.has_feature("beta_unlock"), store_sandbox())


static func unlocks_without_purchase(beta_unlock: bool, sandbox: bool) -> bool:
	return beta_unlock and not sandbox


## The build's purchases go to the real store's sandbox (TestFlight, Play License testers): custom feature
## "store_sandbox", added only by the workflows' store_sandbox input.
func store_sandbox() -> bool:
	return OS.has_feature("store_sandbox")


## Builds handed to testers (beta_unlock or store_sandbox): diagnostics in the version line, the QA hooks.
func tester_tools() -> bool:
	return OS.has_feature("beta_unlock") or store_sandbox()


## "Reset purchase (test)" on the purchase screen: tester and debug builds only.
func can_reset_purchase() -> bool:
	return tester_tools() or OS.is_debug_build()


## True when this build offers the purchase screen (a store, real or mock, can be reached).
func store_open() -> bool:
	return provider != null and provider.is_open()


func price(product: String) -> String:
	return str(prices.get(product, ""))


func is_busy() -> bool:
	return busy != ""


## Starts a purchase. The answer comes through purchase_finished (at once for the mock store, after the store's
## own sheet for the real ones).
func purchase(product: String) -> void:
	if not PRODUCTS.has(product):
		purchase_finished.emit(product, false, "store.not_found")
		return
	if has_entitlement(product):
		purchase_finished.emit(product, true, "store.already_owned")
		return
	if busy != "":
		purchase_finished.emit(product, false, "store.busy")
		return
	_set_busy(product)
	provider.purchase(product)


## The visible "Restore purchases" button (Settings and the purchase screen; App Store guideline 3.1.1).
## The answer comes through restore_finished.
func restore_purchases() -> void:
	if busy != "":
		restore_finished.emit(false, "store.busy")
		return
	_set_busy("restore")
	provider.restore()


## Tester and debug builds: forgets the purchase on this device, and on Google Play consumes the test purchase so
## the same account can buy it again. Returns the message key to show ("" when not allowed).
func reset_purchase_for_testing(product: String = "full_game") -> String:
	if not can_reset_purchase():
		return ""
	var msg := provider.reset_for_testing(product)
	owned.erase(product)
	_save()
	entitlements_changed.emit()
	return msg


func _on_product_info(product: String, price_text: String) -> void:
	prices[product] = price_text
	price_changed.emit(product, price_text)


func _on_purchase_result(product: String, result: int, message: String) -> void:
	if busy == product:
		_set_busy("")
	var ok := result == StoreProvider.Result.PURCHASED
	if ok:
		_grant(product)
	purchase_finished.emit(product, ok, message)


func _on_owned(product: String) -> void:
	if PRODUCTS.has(product) and not has_entitlement(product):
		_grant(product)


func _on_revoked(product: String) -> void:
	if has_entitlement(product):
		owned.erase(product)
		_save()
		entitlements_changed.emit()


func _on_restore_done(ok: bool, message: String) -> void:
	if busy == "restore":
		_set_busy("")
	restore_finished.emit(ok, message)


func _set_busy(what: String) -> void:
	if busy != what:
		busy = what
		busy_changed.emit(what)


func _grant(product: String) -> void:
	owned[product] = true
	_save()
	entitlements_changed.emit()


func revoke_all_for_tests() -> void:
	owned = {}
	_save()


func _load() -> void:
	owned = {}
	var cfg := ConfigFile.new()
	if cfg.load(path) == OK:
		for p: String in PRODUCTS:
			if bool(cfg.get_value("owned", p, false)):
				owned[p] = true


func _save() -> void:
	var cfg := ConfigFile.new()
	for p: String in owned:
		cfg.set_value("owned", p, owned[p])
	cfg.save(path)
