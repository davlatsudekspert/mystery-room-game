class_name PurchasePanel
extends Control
## The purchase screen for the one product, "full_game" (Chapters 2–4; docs/MONETIZATION.md): the title, what it
## unlocks, the store's localized price on the buy button, a status line (waiting, pending, errors, thanks), a
## visible Restore purchases button (App Store guideline 3.1.1) and Close. Tester and debug builds add
## "Reset purchase (test)". It covers its host with a dim layer, so it opens over the chapter list or the
## chapter-complete card. Every text goes through tr(); the store's messages are translation keys.

signal closed

const PRODUCT := "full_game"

var _buy: Button
var _restore: Button
var _reset: Button
var _status: Label
var _status_key := ""
var _status_good := false


## Opens the panel over `host` (full rect). Close (or Android back through the host) frees it.
static func open(host: Control) -> PurchasePanel:
	var p := PurchasePanel.new()
	host.add_child(p)
	return p


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	theme = UITheme.build()
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.55)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(dim)
	var d := UITheme.dialog(self, 1100, "ui.unlock", 46)
	var body: VBoxContainer = d["body"]
	for pair: Array in [["ui.unlock_desc", UITheme.CREAM], ["ui.unlock_includes", UITheme.MUTED]]:
		var l := UITheme.label(pair[0], 26, pair[1])
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		body.add_child(l)
	_status = UITheme.label("", 24, UITheme.MUTED)
	_status.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_status.custom_minimum_size = Vector2(0, UITheme.size(24) * 2.6) # two lines' room: the layout never jumps
	body.add_child(_status)
	var footer: HFlowContainer = d["footer"]
	footer.add_theme_constant_override("h_separation", 20)
	_buy = UITheme.button("ui.buy", 420)
	_buy.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED # the text carries the price
	_buy.pressed.connect(_on_buy)
	footer.add_child(_buy)
	_restore = UITheme.text_button("ui.restore")
	_restore.pressed.connect(_on_restore)
	footer.add_child(_restore)
	if Premium.can_reset_purchase():
		_reset = UITheme.text_button("ui.reset_purchase", UITheme.MUTED)
		_reset.pressed.connect(_on_reset)
		footer.add_child(_reset)
	var close := UITheme.button("ui.close", 260)
	close.pressed.connect(close_panel)
	footer.add_child(close)
	Premium.price_changed.connect(func(_p: String, _price: String) -> void: _refresh())
	Premium.purchase_finished.connect(_on_purchase_finished)
	Premium.restore_finished.connect(_on_restore_finished)
	Premium.entitlements_changed.connect(_refresh)
	Premium.busy_changed.connect(func(_what: String) -> void: _refresh())
	Loc.language_changed.connect(func(_code: String) -> void: _refresh())
	_refresh()


func close_panel() -> void:
	closed.emit()
	queue_free()


## The buy button's text: "Unlock for $4.99" once the store sent the price, "Unlocked" when owned.
static func buy_text(owned: bool, price: String) -> String:
	if owned:
		return TranslationServer.translate("ui.owned")
	if price != "":
		return TranslationServer.translate("ui.buy_for") % price
	return TranslationServer.translate("ui.buy")


func _refresh() -> void:
	if not is_instance_valid(_buy):
		return
	var owned := Premium.has_entitlement(PRODUCT)
	_buy.text = buy_text(owned, Premium.price(PRODUCT))
	_buy.disabled = owned or Premium.is_busy()
	_restore.disabled = Premium.is_busy()
	if owned and _status_key in ["", "ui.store_working", "store.pending"]:
		_set_status("ui.purchase_ok", true) # e.g. a pending payment that completed while the panel was open
	_status.text = tr(_status_key) if _status_key != "" else ""
	_status.add_theme_color_override("font_color", UITheme.BRASS_HI if _status_good else UITheme.CREAM)


func _set_status(key: String, good: bool = false) -> void:
	_status_key = key
	_status_good = good


func _on_buy() -> void:
	_set_status("ui.store_working")
	Premium.purchase(PRODUCT)
	_refresh()


func _on_restore() -> void:
	_set_status("ui.store_working")
	Premium.restore_purchases()
	_refresh()


func _on_reset() -> void:
	var msg := Premium.reset_purchase_for_testing(PRODUCT)
	if msg != "":
		_set_status(msg)
	_refresh()


func _on_purchase_finished(product: String, ok: bool, message: String) -> void:
	if product == PRODUCT:
		_set_status(message, ok)
		_refresh()


func _on_restore_finished(ok: bool, message: String) -> void:
	_set_status(message, ok and Premium.has_entitlement(PRODUCT))
	_refresh()
