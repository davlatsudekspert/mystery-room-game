extends Node
## Entitlements and purchases behind a provider interface.
## Chapter 1 is always free. Real payments stay DISABLED until store products are configured and validated.

signal entitlements_changed
signal purchase_finished(product: String, ok: bool, message: String)

const REAL_PAYMENTS_ENABLED := false
const PRODUCTS := {"full_game": {"chapters": ["ch2", "ch3", "ch4"]}}
const PATH := "user://entitlements.cfg"

var provider: StoreProvider
var owned: Dictionary = {}
var path := PATH


func _ready() -> void:
	_load()
	provider = _pick_provider()


func _pick_provider() -> StoreProvider:
	if REAL_PAYMENTS_ENABLED:
		if Engine.has_singleton("GodotGooglePlayBilling"):
			return GooglePlayStoreProvider.new()
		if Engine.has_singleton("InAppStore") or Engine.has_singleton("StoreKit"):
			return AppStoreProvider.new()
	return MockStoreProvider.new() if OS.is_debug_build() else DisabledStoreProvider.new()


func has_entitlement(product: String) -> bool:
	return bool(owned.get(product, false))


func can_play(chapter_id: String) -> bool:
	var ch := Chapters.get_chapter(chapter_id)
	if ch.is_empty() or not ch.get("released", false):
		return false
	var product: String = ch.get("product", "")
	return product == "" or has_entitlement(product) or tester_build()


## Test builds for Google Play internal/closed testing and TestFlight open every released chapter without any
## purchase: their export adds the custom feature "beta_unlock" (docs/RELEASE_PIPELINE.md). Store releases never
## carry it, and no payment code runs either way.
func tester_build() -> bool:
	return OS.has_feature("beta_unlock")


func purchase(product: String) -> void:
	if not PRODUCTS.has(product):
		purchase_finished.emit(product, false, "unknown_product")
		return
	var res := provider.purchase(product)
	if res["ok"]:
		_grant(product)
	purchase_finished.emit(product, res["ok"], res["message"])


func restore_purchases() -> void:
	for product: String in provider.restore():
		_grant(product)
	entitlements_changed.emit()


func _grant(product: String) -> void:
	owned[product] = true
	_save()
	entitlements_changed.emit()


func revoke_all_for_tests() -> void:
	owned = {}
	_save()


func _load() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(path) == OK:
		for p: String in PRODUCTS:
			owned[p] = bool(cfg.get_value("owned", p, false))


func _save() -> void:
	var cfg := ConfigFile.new()
	for p: String in owned:
		cfg.set_value("owned", p, owned[p])
	cfg.save(path)
