extends TestBase
## Timed text stays long enough to read (owner, 2026-10-11: "the lines pass too fast, I can't keep up"). Messages and
## captions stay at least their caller's time and longer for long text, at about 12 characters a second.


func test_read_seconds() -> void:
	eq(UITheme.read_seconds("", 2.8), 2.8, "an empty line keeps the caller's time")
	check(UITheme.read_seconds("Locked.", 2.8) == 2.8, "a short line keeps the caller's time")
	var long := "Found items go into your bag, bottom left. Tap the bag to open it, an item to pick it up."
	var s := UITheme.read_seconds(long, 2.8)
	check(s >= long.length() / 12.0 and s <= long.length() / 12.0 + 2.0, "a long line gets about 12 chars/s (%.1f s)" % s)
	check(UITheme.read_seconds(long + long) > s, "a longer line stays longer")


func test_hud_caption_stays_until_read() -> void:
	GameState.start_new("ch1")
	var r := HudTestRoom.create(GameState.logic)
	await r.attach()
	var hud := r.hud
	var long := tr("tut.inventory")
	hud.call("caption", long, 2.0)
	var left: float = hud.call("caption_left")
	check(left > 2.0 and absf(left - UITheme.read_seconds(long)) < 0.3, "a long caption stays its read time (%.1f s)" % left)
	hud.call("caption", "", 0.1)
	eq(float(hud.call("caption_left")), 0.0, "a cleared caption has nothing left to read")
	r.dispose()
	await (Engine.get_main_loop() as SceneTree).process_frame


## Every scripted line sequence (tapes, recorders, the teaser) waits the read time before its next line replaces it.
func test_line_sequences_wait_for_the_reader() -> void:
	for p: String in ["res://src/rooms/archive/archive_visuals.gd", "res://src/rooms/underground/underground_room.gd",
			"res://src/rooms/archive/archive_teaser.gd"]:
		var src := FileAccess.get_file_as_string(p)
		check(src.contains("UITheme.read_seconds("), "%s waits by the read time" % p.get_file())
