extends TestBase
## Fail-safe UI paths while a chapter is still being built (Chapter 4: logic and items first, the scene later):
## Continue never loads an empty scene path, and a document without a reader page opens nothing.

const MENU := "res://src/ui/main_menu.gd"


func test_continue_only_loads_a_playable_chapter() -> void:
	var menu: GDScript = load(MENU)
	check(bool(menu.call("playable", "ch1")), "Chapter 1 loads")
	check(not bool(menu.call("playable", "ch4")), "Chapter 4 (no scene yet, unreleased) does not")
	check(not bool(menu.call("playable", "no_such_chapter")), "an unknown chapter does not")
	for ch: Dictionary in Chapters.LIST:
		if str(ch.get("scene", "")) == "" or not bool(ch.get("released", false)):
			check(not bool(menu.call("playable", str(ch["id"]))), "%s is not offered to Continue" % ch["id"])


## Continue on a save of a chapter that cannot be loaded opens the chapter list instead of SceneManager.goto("").
func test_continue_on_an_unplayable_save_opens_the_chapter_list() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	var scene: PackedScene = load("res://src/ui/main_menu.tscn")
	var menu := scene.instantiate() as Control
	tree.root.add_child.call_deferred(menu)
	await tree.process_frame
	await tree.process_frame
	menu.call("_play", "ch4")
	await tree.process_frame
	check(not bool(SceneManager.get("_busy")), "no scene change was started")
	check((menu.get("_dim") as Control).visible, "the chapter list is open instead")
	menu.queue_free()
	await tree.process_frame


func test_documents_without_a_reader_page_open_nothing() -> void:
	SaveSystem.save_path = "user://test_ui_failsafe.json"
	GameState.start_new("ch1")
	var r := HudTestRoom.create(GameState.logic, false)
	await r.attach()
	for doc in ["log4", "letter4", "watch4", "note4", "parcel4", ""]:
		r.hud.call("show_document", doc)
		check(r.hud.get("_overlay") == null, "«%s» opens nothing" % doc)
	r.hud.call("show_document", "letter")
	check(r.hud.get("_overlay") != null, "a known document still opens")
	r.hud.call("_close_overlay")
	# an item whose document has no page yet: the inspect view offers no Read button
	for id in ["strand_log", "leyla_parcel"]:
		if not ItemDB.ITEMS.has(id):
			continue
		r.hud.call("show_inspect", id)
		var read := false
		for b in (r.hud.get("_overlay") as Node).find_children("*", "Button", true, false):
			read = read or (b as Button).text == "ui.read"
		check(not read, "%s: no Read button without a reader page" % id)
		r.hud.call("_close_overlay")
	r.dispose()
	await (Engine.get_main_loop() as SceneTree).process_frame
	SaveSystem.delete_game()
	SaveSystem.save_path = SaveSystem.SAVE_PATH
