extends TestBase
## The purchase system with fake platform singletons (docs/MONETIZATION.md): which store a build uses, Google Play
## Billing (prices, purchase, acknowledgement, pending, errors, restore, tester reset) and StoreKit 2 through the iOS
## plugin's request/response API, Premium's entitlement file, and the purchase screen.

const ENT := "user://test_store_ent.cfg"


## The GodotGooglePlayBilling JNI singleton (plugin 3.3.0): the same method names and signals.
class FakeBilling extends RefCounted:
	signal connected
	signal disconnected
	signal connect_error(code: int, debug_message: String)
	signal query_product_details_response(r: Dictionary)
	signal query_purchases_response(r: Dictionary)
	signal on_purchase_updated(r: Dictionary)
	signal acknowledge_purchase_response(r: Dictionary)
	signal consume_purchase_response(r: Dictionary)
	var calls: Array = []
	var launch_code := 0

	func initPlugin() -> void:
		calls.append(["initPlugin"])

	func startConnection() -> void:
		calls.append(["startConnection"])

	func queryProductDetails(ids: PackedStringArray, kind: String) -> void:
		calls.append(["queryProductDetails", Array(ids), kind])

	func queryPurchases(kind: String, _subs: bool) -> void:
		calls.append(["queryPurchases", kind])

	func purchase(id: String, _option: String, _offer: String, _personal: bool) -> Dictionary:
		calls.append(["purchase", id])
		return {"response_code": launch_code, "debug_message": ""}

	func acknowledgePurchase(token: String) -> void:
		calls.append(["acknowledgePurchase", token])

	func consumePurchase(token: String) -> void:
		calls.append(["consumePurchase", token])

	func names() -> Array:
		return calls.map(func(c: Array) -> String: return c[0])

	func count(name: String) -> int:
		return names().count(name)

	func details(price: String = "US$4.99") -> void:
		query_product_details_response.emit({"response_code": 0, "debug_message": "", "product_details": [
			{"product_id": "full_game", "title": "Full Game", "one_time_purchase_offer_details_list": [
				{"formatted_price": price, "price_amount_micros": 4990000, "price_currency_code": "USD"}]}],
			"unfetched_products": []})


static func play_purchase(state: int, acknowledged: bool, token: String = "tok-1") -> Dictionary:
	return {"product_ids": ["full_game"], "purchase_state": state, "purchase_token": token, "is_acknowledged": acknowledged,
		"order_id": "", "quantity": 1}


## The iOS plugin singleton "IOSInAppPurchase": request(name, args) → 0/1, signal response(name, data).
class FakeStoreKit extends RefCounted:
	signal response(name: String, data: Dictionary)
	var requests: Array = []
	var refuse := ""

	func request(name: String, args: Dictionary) -> int:
		requests.append([name, args])
		return 1 if name == refuse else 0

	func names() -> Array:
		return requests.map(func(r: Array) -> String: return r[0])


## Records what a provider tells Premium.
class Probe extends RefCounted:
	var events: Array = []

	func watch(p: StoreProvider) -> void:
		p.product_info.connect(func(id: String, price: String) -> void: events.append(["price", id, price]))
		p.purchase_result.connect(func(id: String, r: int, m: String) -> void: events.append(["result", id, r, m]))
		p.owned.connect(func(id: String) -> void: events.append(["owned", id]))
		p.revoked.connect(func(id: String) -> void: events.append(["revoked", id]))
		p.restore_done.connect(func(ok: bool, m: String) -> void: events.append(["restore", ok, m]))

	func has(e: Array) -> bool:
		return events.has(e)

	func last() -> Array:
		return events.back() if not events.is_empty() else []

	func clear() -> void:
		events.clear()


func _play() -> Array:
	var fb := FakeBilling.new()
	var p := GooglePlayStoreProvider.new(fb)
	p.deferred = false
	var probe := Probe.new()
	probe.watch(p)
	p.start(PackedStringArray(["full_game"]))
	return [fb, p, probe]


func _apple() -> Array:
	var sk := FakeStoreKit.new()
	var p := AppStoreProvider.new(sk)
	p.deferred = false
	var probe := Probe.new()
	probe.watch(p)
	p.start(PackedStringArray(["full_game"]))
	return [sk, p, probe]


func test_store_selection() -> void:
	var play: Array = [GooglePlayStoreProvider.SINGLETON]
	var ios: Array = [AppStoreProvider.SINGLETON]
	eq(Premium.choose_store(false, false, false, "android", play, false), "disabled", "payments off: release builds have no store")
	eq(Premium.choose_store(false, false, true, "android", play, false), "mock", "payments off: debug builds use the mock")
	eq(Premium.choose_store(false, true, false, "android", play, false), "google_play", "store_sandbox turns Play Billing on")
	eq(Premium.choose_store(false, true, false, "android", [], false), "disabled", "store_sandbox without the plugin: no store")
	eq(Premium.choose_store(false, true, false, "ios", ios, false), "app_store", "store_sandbox on TestFlight: StoreKit")
	eq(Premium.choose_store(false, true, false, "ios", ios, true), "disabled",
		"a store_sandbox build installed from the App Store never charges anyone")
	eq(Premium.choose_store(true, false, false, "ios", ios, true), "app_store", "real payments on: the App Store")
	eq(Premium.choose_store(true, false, false, "android", play, false), "google_play", "real payments on: Google Play")
	eq(Premium.choose_store(true, false, false, "ios", play, false), "disabled", "the other platform's plugin is not used")
	check(not Premium.REAL_PAYMENTS_ENABLED, "real payments stay off until the owner turns them on")
	check(Premium.unlocks_without_purchase(true, false), "beta_unlock opens the paid chapters")
	check(not Premium.unlocks_without_purchase(true, true), "a store_sandbox build keeps them locked: testers test the purchase")
	check(not Premium.unlocks_without_purchase(false, false), "store builds open nothing for free")
	eq(Premium.provider.store_name(), "mock", "this (debug) test run uses the mock store")


func test_play_price_purchase_and_acknowledge() -> void:
	var t := _play()
	var fb: FakeBilling = t[0]
	var p: GooglePlayStoreProvider = t[1]
	var probe: Probe = t[2]
	eq(fb.names(), ["initPlugin", "startConnection"], "init, then connect")
	fb.connected.emit()
	check(fb.calls.has(["queryProductDetails", ["full_game"], "inapp"]), "asks for the product details (price)")
	eq(fb.count("queryPurchases"), 1, "and silently reads what the player owns")
	fb.details()
	check(probe.has(["price", "full_game", "US$4.99"]), "the store's localized price string")
	eq(p.price("full_game"), "US$4.99")
	fb.query_purchases_response.emit({"response_code": 0, "purchases": []})
	p.purchase("full_game")
	check(fb.calls.has(["purchase", "full_game"]), "opens the Play purchase sheet")
	fb.on_purchase_updated.emit({"response_code": 0, "purchases": [play_purchase(1, false)]})
	check(probe.has(["owned", "full_game"]), "granted")
	check(probe.has(["result", "full_game", StoreProvider.Result.PURCHASED, "ui.purchase_ok"]), "purchase answered")
	check(fb.calls.has(["acknowledgePurchase", "tok-1"]), "acknowledged at once (Play refunds after 3 days otherwise)")
	fb.query_purchases_response.emit({"response_code": 0, "purchases": [play_purchase(1, false)]})
	eq(fb.count("acknowledgePurchase"), 1, "not acknowledged twice in one session")
	fb.acknowledge_purchase_response.emit({"response_code": 6, "token": "tok-1"})
	fb.query_purchases_response.emit({"response_code": 0, "purchases": [play_purchase(1, false)]})
	eq(fb.count("acknowledgePurchase"), 2, "a failed acknowledgement is retried at the next purchase-list read")
	fb.query_purchases_response.emit({"response_code": 0, "purchases": [play_purchase(1, true, "tok-2")]})
	eq(fb.count("acknowledgePurchase"), 2, "an acknowledged purchase is left alone")


func test_play_purchase_waits_for_connection_and_details() -> void:
	var t := _play()
	var fb: FakeBilling = t[0]
	var p: GooglePlayStoreProvider = t[1]
	var probe: Probe = t[2]
	p.purchase("full_game")
	eq(fb.count("purchase"), 0, "nothing launched before the product details arrived")
	p.purchase("full_game")
	check(probe.has(["result", "full_game", StoreProvider.Result.FAILED, "store.busy"]), "a second tap waits")
	fb.connected.emit()
	fb.details()
	eq(fb.count("purchase"), 1, "the waiting purchase starts once the details are in")
	# the product is not in the store yet (not created or not active in Play Console)
	var t2 := _play()
	var fb2: FakeBilling = t2[0]
	(t2[1] as GooglePlayStoreProvider).purchase("full_game")
	fb2.connected.emit()
	fb2.query_product_details_response.emit({"response_code": 0, "product_details": [],
		"unfetched_products": [{"product_id": "full_game"}]})
	check((t2[2] as Probe).has(["result", "full_game", StoreProvider.Result.FAILED, "store.not_found"]), "not found")
	# Play Billing cannot be reached at all (no Play Store, or an unsupported account)
	var t3 := _play()
	(t3[1] as GooglePlayStoreProvider).purchase("full_game")
	(t3[0] as FakeBilling).connect_error.emit(3, "billing unavailable")
	check((t3[2] as Probe).has(["result", "full_game", StoreProvider.Result.FAILED, "store.billing_unavailable"]),
		"a connection error answers the waiting purchase")


func test_play_pending_cancel_errors() -> void:
	var t := _play()
	var fb: FakeBilling = t[0]
	var p: GooglePlayStoreProvider = t[1]
	var probe: Probe = t[2]
	fb.connected.emit()
	fb.details()
	p.purchase("full_game")
	fb.on_purchase_updated.emit({"response_code": 0, "purchases": [play_purchase(2, false)]})
	check(probe.has(["result", "full_game", StoreProvider.Result.PENDING, "store.pending"]), "pending payment")
	check(not probe.has(["owned", "full_game"]), "a pending payment grants nothing")
	eq(fb.count("acknowledgePurchase"), 0, "and is not acknowledged")
	fb.on_purchase_updated.emit({"response_code": 0, "purchases": [play_purchase(1, false)]})
	check(probe.has(["owned", "full_game"]), "the payment completed later: granted")
	check(fb.calls.has(["acknowledgePurchase", "tok-1"]), "and acknowledged")
	for pair: Array in [[1, StoreProvider.Result.CANCELLED, "store.cancelled"], [12, StoreProvider.Result.FAILED, "store.network"],
			[2, StoreProvider.Result.FAILED, "store.network"], [3, StoreProvider.Result.FAILED, "store.billing_unavailable"],
			[4, StoreProvider.Result.FAILED, "store.not_found"], [5, StoreProvider.Result.FAILED, "store.error"],
			[6, StoreProvider.Result.FAILED, "store.error"]]:
		probe.clear()
		p.purchase("full_game")
		fb.on_purchase_updated.emit({"response_code": pair[0], "debug_message": ""})
		eq(probe.last(), ["result", "full_game", pair[1], pair[2]], "response code %d" % pair[0])
	probe.clear()
	fb.launch_code = 7
	p.purchase("full_game")
	check(probe.has(["owned", "full_game"]), "ITEM_ALREADY_OWNED when launching: granted")
	check(probe.has(["result", "full_game", StoreProvider.Result.PURCHASED, "store.already_owned"]), "already owned")
	probe.clear()
	fb.launch_code = 0
	p.purchase("full_game")
	fb.on_purchase_updated.emit({"response_code": 7})
	check(probe.has(["result", "full_game", StoreProvider.Result.PURCHASED, "store.already_owned"]), "already owned (update)")


func test_play_restore_and_tester_reset() -> void:
	var t := _play()
	var fb: FakeBilling = t[0]
	var p: GooglePlayStoreProvider = t[1]
	var probe: Probe = t[2]
	p.restore()
	fb.connected.emit() # the restore waited for the connection, which reads the purchases
	fb.query_purchases_response.emit({"response_code": 0, "purchases": [play_purchase(1, true, "tok-9")]})
	check(probe.has(["owned", "full_game"]), "restore grants an owned purchase")
	check(probe.has(["restore", true, "ui.restored"]), "restored")
	probe.clear()
	p.restore()
	fb.query_purchases_response.emit({"response_code": 0, "purchases": []})
	check(probe.has(["restore", true, "store.restore_none"]), "nothing to restore")
	probe.clear()
	p.restore()
	fb.query_purchases_response.emit({"response_code": 0, "purchases": [play_purchase(2, false)]})
	check(probe.has(["restore", true, "store.pending"]), "only a pending payment: says so")
	probe.clear()
	p.restore()
	fb.query_purchases_response.emit({"response_code": 12})
	check(probe.has(["restore", false, "store.restore_failed"]), "a failed read")
	eq(p.reset_for_testing("full_game"), "store.reset_done")
	check(fb.calls.has(["consumePurchase", "tok-9"]), "the tester reset consumes the test purchase (buyable again)")


## On a device the plugin answers from another thread: the provider connects deferred and handles it next frame.
func test_play_answers_are_deferred() -> void:
	var fb := FakeBilling.new()
	var p := GooglePlayStoreProvider.new(fb)
	var probe := Probe.new()
	probe.watch(p)
	p.start(PackedStringArray(["full_game"]))
	fb.connected.emit()
	eq(fb.count("queryProductDetails"), 0, "not handled inside the plugin's emit")
	await (Engine.get_main_loop() as SceneTree).process_frame
	eq(fb.count("queryProductDetails"), 1, "handled on the main thread's next idle time")


func test_app_store_storekit2() -> void:
	var t := _apple()
	var sk: FakeStoreKit = t[0]
	var p: AppStoreProvider = t[1]
	var probe: Probe = t[2]
	eq(sk.names(), ["startUpdateTask", "products", "proceedUnfinishedTransactions", "transactionCurrentEntitlements"],
		"start: the update listener, prices, unfinished transactions, an ownership sync")
	eq(sk.requests[1][1], {"productIDs": ["full_game"]})
	sk.response.emit("products", {"request": "products", "result": "success", "products": [
		{"id": "full_game", "displayName": "Full Game", "displayPrice": "$4.99", "type": "Non-Consumable"}]})
	check(probe.has(["price", "full_game", "$4.99"]), "localized price")
	sk.response.emit("transactionCurrentEntitlements", {"result": "success", "transactions": []})
	check(not probe.has(["owned", "full_game"]), "nothing owned yet")
	p.purchase("full_game")
	eq(sk.requests.back(), ["purchase", {"productID": "full_game"}])
	sk.response.emit("purchase", {"request": "purchase", "result": "success", "productID": "full_game", "jwsRepresentation": "x"})
	check(probe.has(["owned", "full_game"]) and probe.has(["result", "full_game", StoreProvider.Result.PURCHASED, "ui.purchase_ok"]),
		"a verified purchase is granted")
	for pair: Array in [["pending", StoreProvider.Result.PENDING, "store.pending"], ["userCancelled", StoreProvider.Result.CANCELLED, "store.cancelled"],
			["unverified", StoreProvider.Result.FAILED, "store.unverified"]]:
		probe.clear()
		p.purchase("full_game")
		sk.response.emit("purchase", {"request": "purchase", "result": pair[0], "productID": "full_game"})
		eq(probe.events, [["result", "full_game", pair[1], pair[2]]], pair[0] + ": answered, nothing granted")
	probe.clear()
	p.purchase("full_game")
	sk.response.emit("purchase", {"request": "purchase", "result": "error", "error": "no productID:full_game"})
	eq(probe.last(), ["result", "full_game", StoreProvider.Result.FAILED, "store.not_found"], "unknown product")
	p.purchase("full_game")
	sk.response.emit("purchase", {"request": "purchase", "result": "error", "error": "The Internet connection appears to be offline."})
	eq(probe.last(), ["result", "full_game", StoreProvider.Result.FAILED, "store.error"], "StoreKit threw")
	probe.clear()
	sk.response.emit("purchase", {"request": "purchase", "result": "success", "productID": "full_game"})
	eq(probe.events, [["owned", "full_game"]], "Transaction.updates (Ask to Buy approved later): granted without a purchase answer")
	sk.response.emit("purchase", {"request": "purchase", "result": "revoked", "productID": "full_game"})
	check(probe.has(["revoked", "full_game"]), "a refund removes it")
	sk.refuse = "purchase"
	probe.clear()
	p.purchase("full_game")
	eq(probe.last(), ["result", "full_game", StoreProvider.Result.FAILED, "store.error"], "a refused request answers at once")


func test_app_store_restore_and_sync() -> void:
	var t := _apple()
	var sk: FakeStoreKit = t[0]
	var p: AppStoreProvider = t[1]
	var probe: Probe = t[2]
	sk.response.emit("transactionCurrentEntitlements", {"result": "success", "transactions": [
		{"productID": "full_game", "id": "1", "ownershipType": "PURCHASED"}]})
	check(probe.has(["owned", "full_game"]), "start-up sync grants a purchase made before (re-install, other device)")
	probe.clear()
	p.restore()
	eq(sk.names().back(), "appStoreSync", "Restore purchases calls AppStore.sync()")
	sk.response.emit("appStoreSync", {"result": "success"})
	eq(sk.names().back(), "transactionCurrentEntitlements", "then reads the current entitlements")
	sk.response.emit("transactionCurrentEntitlements", {"result": "success", "transactions": [
		{"productID": "full_game", "id": "1"}, {"productID": "other_app_item", "id": "2"}]})
	eq(probe.events, [["owned", "full_game"], ["restore", true, "ui.restored"]], "restored; other products ignored")
	probe.clear()
	p.restore()
	sk.response.emit("appStoreSync", {"result": "success"})
	sk.response.emit("transactionCurrentEntitlements", {"result": "success", "transactions": [
		{"productID": "full_game", "id": "1", "error": "unverified"}]})
	eq(probe.events, [["restore", true, "store.restore_none"]], "an unverified transaction is never granted")
	probe.clear()
	p.restore()
	sk.response.emit("appStoreSync", {"result": "error", "error": "cancelled"})
	eq(probe.events, [["restore", false, "store.restore_failed"]], "sync failed or the sign-in was cancelled")
	probe.clear()
	sk.response.emit("transactionCurrentEntitlements", {"result": "success", "transactions": [
		{"productID": "full_game", "id": "1", "revocationDate": "2026-10-01T10:00:00Z"}]})
	eq(probe.events, [["revoked", "full_game"]], "a revoked entitlement is removed")
	eq(p.reset_for_testing("full_game"), "store.reset_sandbox_hint", "iOS: the tester is told how to clear the sandbox history")
	check(not AppStoreProvider.app_store_install("user://no_such_bundle"), "no receipt file: not an App Store install")


func test_premium_with_a_store() -> void:
	var keep := Premium.provider
	Premium.path = ENT
	Premium.revoke_all_for_tests()
	var t := _play()
	var fb: FakeBilling = t[0]
	var p: GooglePlayStoreProvider = t[1]
	Premium.use_provider(p) # start() again is a no-op for an already started provider
	fb.connected.emit()
	fb.details("UZS 59 900")
	eq(Premium.price("full_game"), "UZS 59 900", "Premium keeps the store's price")
	check(Premium.store_open(), "the purchase screen is offered")
	var answers: Array = []
	var on_answer := func(id: String, ok: bool, m: String) -> void: answers.append([id, ok, m])
	Premium.purchase_finished.connect(on_answer)
	Premium.purchase("full_game")
	eq(Premium.busy, "full_game", "busy while the Play sheet is open")
	Premium.purchase("full_game")
	eq(answers.back(), ["full_game", false, "store.busy"], "a second purchase waits")
	fb.on_purchase_updated.emit({"response_code": 1})
	eq(answers.back(), ["full_game", false, "store.cancelled"], "cancelled")
	check(not Premium.is_busy() and not Premium.has_entitlement("full_game"), "idle again, nothing granted")
	Premium.purchase("full_game")
	fb.on_purchase_updated.emit({"response_code": 0, "purchases": [play_purchase(1, false)]})
	eq(answers.back(), ["full_game", true, "ui.purchase_ok"], "bought")
	check(Premium.owns_chapter("ch3") and Premium.owns_chapter("ch4"), "Chapters 3 and 4 are unlocked")
	var cfg := ConfigFile.new()
	check(cfg.load(ENT) == OK and bool(cfg.get_value("owned", "full_game", false)), "the entitlement is saved on the device")
	Premium.owned = {}
	Premium._load()
	check(Premium.has_entitlement("full_game"), "and read back at the next start (offline play)")
	Premium.purchase("full_game")
	eq(answers.back(), ["full_game", true, "store.already_owned"], "buying again is not offered to the store")
	Premium.purchase("no_such_product")
	eq(answers.back(), ["no_such_product", false, "store.not_found"])
	eq(Premium.reset_purchase_for_testing(), "store.reset_done", "debug build: the tester reset works")
	check(not Premium.has_entitlement("full_game"), "and forgets the purchase on this device")
	Premium.purchase_finished.disconnect(on_answer)
	var restored: Array = []
	var on_restore := func(ok: bool, m: String) -> void: restored.append([ok, m])
	Premium.restore_finished.connect(on_restore)
	Premium.restore_purchases()
	eq(Premium.busy, "restore")
	fb.query_purchases_response.emit({"response_code": 0, "purchases": [play_purchase(1, true, "tok-3")]})
	eq(restored, [[true, "ui.restored"]], "restore answered")
	check(Premium.has_entitlement("full_game") and not Premium.is_busy(), "restored and idle")
	Premium.restore_finished.disconnect(on_restore)
	Premium.revoke_all_for_tests()
	DirAccess.remove_absolute(ENT)
	Premium.path = Premium.PATH
	Premium.use_provider(keep)


func test_every_store_message_is_translated() -> void:
	for key: String in StoreProvider.MESSAGES + ["ui.buy", "ui.buy_for", "ui.unlock", "ui.unlock_desc", "ui.unlock_includes",
			"ui.owned", "ui.store_working", "ui.reset_purchase", "ui.restore"]:
		for loc in ["en", "ru", "uz"]:
			TranslationServer.set_locale(loc)
			check(tr(key) != key and tr(key).strip_edges() != "", "%s untranslated in %s" % [key, loc])
	TranslationServer.set_locale("ru")
	eq(PurchasePanel.buy_text(false, "449 ₽"), "Открыть за 449 ₽", "the price goes into the button text")
	TranslationServer.set_locale("en")
	eq(PurchasePanel.buy_text(false, ""), "Unlock", "no price yet")
	eq(PurchasePanel.buy_text(true, "$4.99"), "Unlocked")


## Which chapters the chapter list offers for sale (Chapters 1-2 free, 3-4 paid and unreleased for now).
func test_chapter_list_purchase_button() -> void:
	var menu: GDScript = load("res://src/ui/main_menu.gd")
	var released_paid := {"id": "chX", "product": "full_game", "released": true}
	var unreleased_paid := {"id": "ch3", "product": "full_game", "released": false}
	var free := Chapters.get_chapter("ch2")
	eq(menu.call("purchase_button", released_paid, false, true, false, false), "ui.buy", "a released paid chapter: Unlock")
	eq(menu.call("purchase_button", released_paid, false, false, false, false), "", "no store (payments off): Coming soon")
	eq(menu.call("purchase_button", unreleased_paid, false, true, false, false), "",
		"an unreleased chapter is never sold in a store build")
	eq(menu.call("purchase_button", unreleased_paid, false, true, true, false), "ui.buy",
		"store_sandbox test builds sell it, so the purchase can be tested before Chapters 3-4 ship")
	eq(menu.call("purchase_button", unreleased_paid, false, true, true, true), "ui.owned", "then show it as bought")
	eq(menu.call("purchase_button", free, true, true, true, false), "", "Chapter 2 is free: Play, nothing to buy")


## The purchase screen with the mock store: price on the button, a visible Restore purchases, the tester reset;
## the chapter list offers Play for the free Chapters 1-2 and sells nothing that is not released.
func test_purchase_screen() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	Premium.path = ENT
	Premium.revoke_all_for_tests()
	var keep := Premium.provider
	var mock := MockStoreProvider.new()
	mock.price = "$4.99"
	Premium.use_provider(mock)
	var menu := (load("res://src/ui/main_menu.tscn") as PackedScene).instantiate() as Control
	tree.root.add_child.call_deferred(menu) # the root may still be adding the test runner's children
	await tree.process_frame
	await tree.process_frame
	menu.call("_show_chapters")
	await tree.process_frame
	var host: Control = menu.get("_panel_host")
	check(_find(host, "ui.buy") == null, "nothing to buy in the list: Chapter 2 is free, Chapters 3-4 are not released")
	check(_find(host, "ui.play") != null and not _find(host, "ui.play").disabled, "Chapter 2 offers Play without a purchase")
	menu.call("_show_purchase")
	await tree.process_frame
	var panel := _first_panel(host)
	check(panel != null, "the purchase screen opens")
	var buy: Button = panel.get("_buy")
	eq(buy.text, "Unlock for $4.99", "the price is on the button")
	check(_find(panel, "ui.restore") != null, "Restore purchases is visible on the purchase screen")
	check(_find(panel, "ui.reset_purchase") != null, "debug build: Reset purchase (test) is there")
	mock.next_result = StoreProvider.Result.PENDING
	buy.pressed.emit()
	eq((panel.get("_status") as Label).text, "Your payment is pending. The chapters unlock as soon as the store confirms it.")
	check(not Premium.has_entitlement("full_game"), "pending: nothing granted")
	buy.pressed.emit()
	check(Premium.has_entitlement("full_game"), "bought")
	eq(buy.text, "Unlocked")
	check(buy.disabled, "nothing more to buy")
	(_find(panel, "ui.reset_purchase") as Button).pressed.emit()
	check(not Premium.has_entitlement("full_game") and not buy.disabled, "the tester reset makes it buyable again")
	(_find(panel, "ui.restore") as Button).pressed.emit()
	check(not Premium.has_entitlement("full_game"), "the reset consumed the test purchase: nothing to restore")
	eq((panel.get("_status") as Label).text, "No previous purchase was found for this account.")
	buy.pressed.emit()
	Premium.owned = {} # a new device: the purchase is only in the store
	(_find(panel, "ui.restore") as Button).pressed.emit()
	check(Premium.has_entitlement("full_game"), "Restore purchases brings it back")
	eq((panel.get("_status") as Label).text, "Purchases restored.")
	(_find(panel, "ui.close") as Button).pressed.emit()
	await tree.process_frame
	await tree.process_frame
	check(_first_panel(host) == null and _find(host, "ui.play") != null, "Close goes back to the chapter list")
	menu.queue_free()
	await tree.process_frame
	Premium.revoke_all_for_tests()
	DirAccess.remove_absolute(ENT)
	Premium.path = Premium.PATH
	Premium.use_provider(keep)


## A disabled store (release builds while real payments are off) keeps the old screens: no Unlock, no purchase screen.
func test_disabled_store_offers_no_purchase() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	var keep := Premium.provider
	Premium.path = ENT
	Premium.revoke_all_for_tests()
	Premium.use_provider(DisabledStoreProvider.new())
	check(not Premium.store_open(), "no purchase screen")
	var answers: Array = []
	var on_answer := func(_ok: bool, m: String) -> void: answers.append(m)
	Premium.restore_finished.connect(on_answer)
	Premium.restore_purchases()
	eq(answers, ["ui.store_unavailable"], "Restore says the store is not available yet")
	Premium.restore_finished.disconnect(on_answer)
	var menu := (load("res://src/ui/main_menu.tscn") as PackedScene).instantiate() as Control
	tree.root.add_child.call_deferred(menu) # the root may still be adding the test runner's children
	await tree.process_frame
	await tree.process_frame
	menu.call("_show_chapters")
	await tree.process_frame
	var host: Control = menu.get("_panel_host")
	check(_find(host, "ui.buy") == null, "no Unlock button")
	var soon := _find(host, "ui.coming_soon")
	check(soon != null and soon.disabled, "Chapter 3 says Coming soon")
	check(_find(host, "ui.play") != null, "Chapters 1-2 offer Play")
	menu.queue_free()
	await tree.process_frame
	DirAccess.remove_absolute(ENT)
	Premium.path = Premium.PATH
	Premium.use_provider(keep)


func _find(root: Node, text_key: String) -> Button:
	for c in root.find_children("*", "Button", true, false):
		if (c as Button).text == text_key or (c as Button).text == TranslationServer.translate(text_key):
			return c as Button
	return null


func _first_panel(root: Node) -> PurchasePanel:
	for c in root.find_children("*", "", true, false):
		if c is PurchasePanel:
			return c as PurchasePanel
	return null
