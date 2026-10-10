extends TestBase
## Android back (owner feedback, item 3: "when I pick an item to put it back, Back moves the camera instead").
## SceneManager hands the press to room.handle_back() (RoomBase here, with the real HUD), which asks
## hud.consume_back() first. One press undoes one thing, the nearest first: the open overlay, then Combine and the
## item in hand, then the open bag; only then does the camera step back, and at the room view the pause menu opens.

const PHONE := {"size": Vector2i(1920, 1080), "dpi": 480.0, "safe": Rect2i(0, 0, 1920, 1080)}


func _start() -> HudTestRoom:
	SaveSystem.save_path = "user://test_hud_back.json"
	Settings.path = "user://test_hud_back_settings.cfg"
	Settings.emulate = PHONE
	Settings.values["inventory_open"] = false
	Settings.values["reduce_motion"] = true # instant camera moves and tray: the order is what is tested
	TranslationServer.set_locale("en")
	GameState.start_new("ch1")
	var l := GameState.logic
	for id in ["notebook", "battery_cell", "uv_lamp_empty"]:
		l._begin()
		l._add_item(id)
		l._end()
	var r := HudTestRoom.create(l, true)
	await r.attach()
	return r


func _finish(r: HudTestRoom) -> void:
	r.dispose()
	await (Engine.get_main_loop() as SceneTree).process_frame
	Settings.emulate = {}
	Settings.values["inventory_open"] = false
	Settings.values["reduce_motion"] = false
	DirAccess.remove_absolute(Settings.path)
	Settings.path = Settings.PATH
	SaveSystem.delete_game()
	SaveSystem.save_path = SaveSystem.SAVE_PATH


## Waits until the camera has finished moving (a transition is a short tween).
func _settle_camera(r: HudTestRoom) -> void:
	for i in 120:
		if not r.cam.transitioning:
			break
		await r.wait(0.05)
	await r.wait(0.05)


func _overlay(r: HudTestRoom) -> Variant:
	return r.hud.get("_overlay")


func test_back_unwinds_overlay_item_bag_then_camera_then_pause() -> void:
	var r := await _start()
	var hud := r.hud
	r.cam.go("desk")
	await _settle_camera(r)
	eq(r.cam.current(), "desk", "at the close-up")
	hud.call("set_bag_open", true, true)
	r.logic.select_item("battery_cell")
	hud.call("show_hint")
	await r.wait(0.1)
	check(_overlay(r) != null, "a hint is open over everything")
	# 1. the overlay
	r.handle_back()
	await r.wait(0.1)
	check(_overlay(r) == null, "Back closes the hint first")
	eq(r.logic.selected, "battery_cell", "the item is still in hand")
	check(bool(hud.call("is_bag_open")), "the bag is still open")
	eq(r.cam.current(), "desk", "the camera has not moved")
	# 2. the item in hand
	r.handle_back()
	await r.wait(0.1)
	eq(r.logic.selected, "", "Back puts the item back")
	check(bool(hud.call("is_bag_open")), "the bag is still open")
	eq(r.cam.current(), "desk", "the camera has not moved")
	# 3. the bag
	r.handle_back()
	await r.wait(0.3)
	check(not bool(hud.call("is_bag_open")), "Back folds the tray into the bag")
	eq(r.cam.current(), "desk", "the camera has not moved")
	# 4. the camera
	r.handle_back()
	await _settle_camera(r)
	eq(r.cam.current(), "hall", "only now does Back move the camera")
	check(_overlay(r) == null, "no pause menu yet")
	# 5. the room view: pause, and Back again resumes
	r.handle_back()
	await r.wait(0.1)
	check(_overlay(r) != null, "at the room view Back opens the pause menu")
	r.handle_back()
	await r.wait(0.1)
	check(_overlay(r) == null, "Back closes the pause menu")
	await _finish(r)


## Combine first, then the item: two presses, and the camera stays.
func test_back_leaves_combine_before_the_item() -> void:
	var r := await _start()
	var hud := r.hud
	hud.call("set_bag_open", true, true)
	r.logic.select_item("uv_lamp_empty")
	(hud.get("_act_combine") as BaseButton).emit_signal("pressed")
	check(bool(hud.get("_combine_mode")), "Combine is waiting for a second item")
	check(bool(hud.call("consume_back")), "the HUD takes the press")
	check(not bool(hud.get("_combine_mode")), "Back leaves Combine")
	eq(r.logic.selected, "uv_lamp_empty", "and keeps the item in hand")
	check(bool(hud.call("consume_back")), "the HUD takes the second press")
	eq(r.logic.selected, "", "then puts the item back")
	check(bool(hud.call("consume_back")), "the third press folds the bag")
	check(not bool(hud.call("consume_back")), "with nothing left the press goes to the room")
	await _finish(r)


## Steps inside overlays follow their Close buttons: settings return to the pause menu, an enlarged photograph to
## the evidence board; the finale choice needs an answer; a cinematic swallows the press.
func test_back_inside_overlays() -> void:
	var r := await _start()
	var hud := r.hud
	hud.call("show_pause")
	await r.wait(0.1)
	var settings := _find_button(_overlay(r), "ui.settings")
	check(settings != null, "the pause menu has Settings")
	if settings != null:
		settings.emit_signal("pressed")
		await r.wait(0.2)
		check(_find_button(_overlay(r), "ui.resume") == null, "the settings panel is open")
		r.handle_back()
		await r.wait(0.2)
		check(_find_button(_overlay(r), "ui.resume") != null, "Back from settings returns to the pause menu")
	r.handle_back()
	await r.wait(0.1)
	check(_overlay(r) == null, "and Back again resumes")
	hud.call("show_document", "evidence")
	await r.wait(0.1)
	var photo: Button = null
	for b in (_overlay(r) as Node).find_children("*", "Button", true, false):
		if (b as Button).flat:
			photo = b
			break
	check(photo != null, "the evidence board has photographs")
	if photo != null:
		photo.emit_signal("pressed")
		await r.wait(0.1)
		r.handle_back()
		await r.wait(0.1)
		var flat := 0 # the board's eight photographs (the zoomed view has only its Close button)
		for b in (_overlay(r) as Node).find_children("*", "Button", true, false):
			flat += 1 if (b as Button).flat else 0
		check(flat >= 8, "Back from an enlarged photograph returns to the board")
	r.handle_back()
	await r.wait(0.1)
	check(_overlay(r) == null, "Back closes the board")
	hud.call("show_choice")
	await r.wait(0.1)
	r.handle_back()
	await r.wait(0.1)
	check(_overlay(r) != null, "the finale choice stays until it is answered")
	hud.call("_close_overlay")
	hud.call("set_busy", true)
	r.logic.select_item("notebook")
	check(bool(hud.call("consume_back")), "a cinematic swallows the press")
	eq(r.logic.selected, "notebook", "without touching the item in hand")
	hud.call("set_busy", false)
	await _finish(r)


func _find_button(root: Variant, key: String) -> Button:
	if root == null or not is_instance_valid(root):
		return null
	for b in (root as Node).find_children("*", "Button", true, false):
		if (b as Button).text == key and (b as Button).is_visible_in_tree():
			return b
	return null
