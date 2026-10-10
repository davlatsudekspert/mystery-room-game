extends TestBase
## The bag and the room's taps (owner feedback, items 1 and 2): HUD containers never swallow a tap meant for the
## room, blocked_rects() lists exactly the controls that take taps, and the inventory folds away into a bag
## (bottom left) whose tray slides out above it, remembers the player's choice at room views, starts collapsed
## in close-ups and shows the item in hand.

## A 5.5" 16:9 phone at 480 dpi: its canvas (1920x1080) is the headless test window's, so taps land where the
## layout put things.
const PHONE := {"size": Vector2i(1920, 1080), "dpi": 480.0, "safe": Rect2i(0, 0, 1920, 1080)}


func _start(items: Array) -> HudTestRoom:
	SaveSystem.save_path = "user://test_hud_bag.json"
	Settings.path = "user://test_hud_settings.cfg" # the bag's choice is saved: not into the player's settings
	Settings.emulate = PHONE
	Settings.values["text_scale"] = 1.0
	Settings.values["inventory_open"] = false
	Settings.values["reduce_motion"] = false
	TranslationServer.set_locale("en")
	GameState.start_new("ch1")
	var l := GameState.logic as Lab7Logic
	for id: String in items:
		_give(l, id)
	var r := HudTestRoom.create(l, true)
	await r.attach()
	return r


## Puts an item into the pockets as the room's logic does (an item_added event through GameState).
static func _give(l: RoomLogic, id: String) -> void:
	l._begin()
	l._add_item(id)
	l._end()


func _finish(r: HudTestRoom) -> void:
	r.dispose()
	await (Engine.get_main_loop() as SceneTree).process_frame
	Settings.emulate = {}
	Settings.values["inventory_open"] = false
	DirAccess.remove_absolute(Settings.path)
	Settings.path = Settings.PATH
	SaveSystem.delete_game()
	SaveSystem.save_path = SaveSystem.SAVE_PATH


func _rect(c: Control) -> Rect2:
	return c.get_global_rect()


## Every control in the HUD (no overlay open) that is not IGNORE must be a button: containers, rules, banners,
## the meter and pictures let a tap through to the room.
func test_only_buttons_take_taps() -> void:
	var r := await _start(["notebook", "battery_cell", "uv_lamp_empty"])
	var hud := r.hud
	hud.call("set_bag_open", true, true)
	r.logic.select_item("battery_cell")
	hud.call("set_meter", 3)
	hud.call("message", "A message", 30.0)
	hud.call("caption", "A caption", 30.0)
	hud.call("set_caption", "obj.drawing")
	await r.wait(0.5)
	var root := hud.get("_root") as Control
	var takers := 0
	for n in root.find_children("*", "Control", true, false):
		var c := n as Control
		if c.mouse_filter != Control.MOUSE_FILTER_IGNORE and c.is_visible_in_tree():
			check(c is BaseButton, "«%s» (%s) takes taps but is not a button" % [c.name, c.get_class()])
			takers += 1
	check(takers >= 8, "the corner buttons, the bag, the slots and the item actions take taps (%d)" % takers)
	await _finish(r)


## A finger on a banner, the tray's rule or the meter reaches the room; on the bag or a slot it does not.
func test_taps_reach_the_room_beside_the_hud() -> void:
	var r := await _start(["notebook", "battery_cell"])
	var hud := r.hud
	var vr := (Engine.get_main_loop() as SceneTree).root.get_visible_rect()
	if vr.size != Vector2(1920, 1080):
		check(true, "skipped: the headless canvas is %s" % vr.size)
		await _finish(r)
		return
	hud.call("set_bag_open", true, true)
	hud.call("set_meter", 2)
	hud.call("message", "Something happens in the room.", 30.0)
	await r.wait(0.5)
	var spots := {
		"message banner": _rect(hud.get("_msg_plate")).get_center(),
		"tray rule": _rect(hud.get("_inv_rule")).get_center(),
		"meter": _rect(hud.get("_meter")).get_center(),
		"gap between slots": _rect(hud.get("_inv_scroll")).position + Vector2(20, _rect((hud.get("_inv_box") as Control).get_child(0)).size.y + 4),
		"open room": Vector2(960, 540),
	}
	for what: String in spots:
		var n := r.taps.size()
		await r.tap_screen(spots[what])
		check(r.taps.size() == n + 1, "a tap on the %s at %s reaches the room" % [what, spots[what]])
	var blocked := {"bag": _rect(hud.get("_bag_btn")).get_center(), "pause": _rect(hud.get("_pause_btn")).get_center()}
	for what: String in blocked:
		var n := r.taps.size()
		await r.tap_screen(blocked[what])
		check(r.taps.size() == n, "a tap on the %s stays in the HUD" % what)
	await _finish(r)


## blocked_rects(): the corner buttons and the bag while the tray is in; the slots and the item actions too while
## it is out; never a banner or the meter. All inside the canvas.
func test_blocked_rects() -> void:
	var r := await _start(["notebook", "battery_cell", "uv_lamp_empty"])
	var hud := r.hud
	hud.call("set_meter", 4)
	hud.call("message", "A message", 30.0)
	await r.wait(0.4)
	var rects: Array[Rect2] = hud.call("blocked_rects")
	var want: Array[Rect2] = []
	for b in ["_back_btn", "_hint_btn", "_pause_btn", "_bag_btn"]:
		var c := hud.get(b) as Control
		if c.visible:
			want.append(c.get_global_rect())
	eq(rects.size(), want.size(), "tray in: only the corner buttons and the bag")
	for w in want:
		check(rects.has(w), "blocked_rects() has %s" % w)
	hud.call("set_bag_open", true, true)
	r.logic.select_item("notebook")
	await r.wait(0.5)
	rects = hud.call("blocked_rects")
	var slots := 0
	for s in (hud.get("_inv_box") as Control).get_children():
		if s is Button and rects.has((s as Control).get_global_rect()):
			slots += 1
	eq(slots, 3, "tray out: every slot is blocked")
	for s in (hud.get("_inv_box") as Control).get_children():
		var sz := (s as Control).size
		check(absf(sz.x - sz.y) < 1.0, "a slot is square (%s), even while its icon renders" % sz)
	check(rects.has((hud.get("_act_inspect") as Control).get_global_rect()), "the Inspect action is blocked")
	var msg := _rect(hud.get("_msg_plate"))
	var meter := _rect(hud.get("_meter"))
	var canvas := Rect2(Vector2.ZERO, Vector2(1920, 1080))
	for rr in rects:
		check(not rr.intersects(msg) or rr.intersection(msg).get_area() < 1.0, "a blocked rect %s lies on the message banner" % rr)
		check(not rr.encloses(meter), "the meter is not blocked")
		check(canvas.grow(1.0).encloses(rr), "%s inside the canvas" % rr)
	await _finish(r)


## The bag: collapsed by default; the player's choice at room views is remembered in Settings; close-ups start
## collapsed and the room view restores the choice; picking an item in a close-up folds the tray away and the bag
## shows the item in hand and how many items it holds.
func test_bag_open_close_and_memory() -> void:
	var r := await _start(["notebook", "battery_cell"])
	var hud := r.hud
	var tray := hud.get("_inv_panel") as Control
	var bag := hud.get("_bag_btn") as IconButton
	if bag == null or tray == null:
		check(false, "the HUD has a bag and a tray")
		await _finish(r)
		return
	check(not bool(hud.call("is_bag_open")) and not tray.visible, "collapsed by default")
	eq(bag.count, 2, "the collapsed bag counts its items")
	bag.emit_signal("pressed")
	await r.wait(0.35)
	check(bool(hud.call("is_bag_open")) and tray.visible and is_equal_approx(tray.modulate.a, 1.0), "the bag opens the tray")
	var span: Rect2 = hud.get("_inv_span")
	check(tray.position.distance_to(span.position) < 0.5, "the tray slid to rest at %s (is %s)" % [span.position, tray.position])
	eq(Settings.get_value("inventory_open"), true, "the choice at a room view is remembered")
	eq(bag.count, 0, "no count while the tray is out")
	# a close-up starts collapsed, without forgetting the room view's choice
	r.cam.go("desk", true)
	await r.wait(0.35)
	check(not bool(hud.call("is_bag_open")) and not tray.visible, "close-ups start collapsed")
	eq(Settings.get_value("inventory_open"), true, "the close-up does not change the remembered choice")
	# opened in the close-up, an item is picked: the tray folds away and the bag shows the item in hand
	bag.emit_signal("pressed")
	await r.wait(0.35)
	check(bool(hud.call("is_bag_open")), "the bag opens in a close-up")
	var slot := (hud.get("_inv_box") as Control).get_child(1) as Button
	if slot == null:
		check(false, "the second slot is a button")
		await _finish(r)
		return
	slot.emit_signal("pressed")
	eq(r.logic.selected, "battery_cell", "the slot picks the item")
	await r.wait(0.7)
	check(not bool(hud.call("is_bag_open")), "picking an item in a close-up folds the tray away")
	eq(bag.count, 2, "the bag still counts its items")
	check(bag.active == false, "the folded bag is not lit")
	eq(Settings.get_value("inventory_open"), true, "still remembered for the room view")
	# back at the room view: the player's choice again
	r.cam.go("hall", true)
	await r.wait(0.35)
	check(bool(hud.call("is_bag_open")), "the room view restores the open tray")
	bag.emit_signal("pressed")
	await r.wait(0.35)
	eq(Settings.get_value("inventory_open"), false, "closing at a room view is remembered too")
	await _finish(r)


## Reduce camera motion: the tray appears and goes without sliding (a fade only).
func test_bag_reduce_motion_does_not_slide() -> void:
	var r := await _start(["notebook"])
	Settings.values["reduce_motion"] = true
	var hud := r.hud
	var tray := hud.get("_inv_panel") as Control
	var span: Rect2 = hud.get("_inv_span")
	hud.call("set_bag_open", true, true)
	await r.wait(0.05)
	check(tray.position.distance_to(span.position) < 0.5, "no slide with Reduce camera motion (at %s)" % tray.position)
	Settings.values["reduce_motion"] = false
	await _finish(r)


## A found item flies from its banner into the bag, and the bag swells once as it lands; the first item also
## shows the tutorial line that says where the bag is.
func test_found_item_flies_to_the_bag() -> void:
	var r := await _start([])
	var hud := r.hud
	var bag := hud.get("_bag_btn") as IconButton
	if bag == null:
		check(false, "the HUD has a bag")
		await _finish(r)
		return
	_give(r.logic, "notebook") # emits item_added:notebook through GameState
	hud.call("message", tr("ui.item_added") % tr(ItemDB.name_key("notebook")))
	check((hud.get("_tips_shown") as Dictionary).has("inventory"), "the first item shows the bag tip")
	eq(tr("tut.inventory").contains("bag"), true, "the tip names the bag")
	await r.wait(0.75)
	var fly: Variant = hud.get("_fly")
	check(fly != null and is_instance_valid(fly), "the item is on its way into the bag")
	var grew := false
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < 1500:
		await (Engine.get_main_loop() as SceneTree).process_frame
		if bag.scale.x > 1.05:
			grew = true
	check(grew, "the bag pulses as the item lands")
	check(fly == null or not is_instance_valid(fly), "the flying icon is gone after landing")
	check(bag.scale.is_equal_approx(Vector2.ONE), "the bag is back to its size")
	await _finish(r)


## The bag is a full touch target on every phone and tablet, and the tray's slots are too.
func test_bag_and_slots_are_touch_targets() -> void:
	for dev: Dictionary in [PHONE, {"size": Vector2i(2556, 1179), "dpi": 460.0}, {"size": Vector2i(2048, 1536), "dpi": 264.0}]:
		Settings.emulate = dev
		var mm := UITheme.mm_per_px()
		check(UITheme.target(UITheme.HUD_BTN_PX) * mm >= UITheme.TOUCH_MM - 0.01, "%s: the bag is %.1f mm" % [dev["size"], UITheme.target(UITheme.HUD_BTN_PX) * mm])
		check(UITheme.target(UITheme.HUD_SLOT_PX, UITheme.SLOT_MM) * mm >= UITheme.TOUCH_MM - 0.01, "%s: a slot is %.1f mm" % [dev["size"], UITheme.target(UITheme.HUD_SLOT_PX, UITheme.SLOT_MM) * mm])
	Settings.emulate = {}
