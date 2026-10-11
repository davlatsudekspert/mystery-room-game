extends TestBase
## An item that does nothing says why. The owner held the crystal lens at the radio and saw only "Nothing happens."
## (2026-10-11): now an item with no use at a target names itself ("Crystal lens doesn't fit here."), while the
## right item at the wrong moment still says "Nothing happens." and gives nothing away.


func test_chapter1_wrong_item_names_itself() -> void:
	var l := Lab7Logic.new()
	l.inventory.append("crystal_lens")
	var ev := l.use_item_on("crystal_lens", "radio")
	check(ev.has("not_for_here") and ev.has("nothing_happens"), "the lens has no use at the radio: %s" % str(ev))
	l.inventory.append("brass_key")
	ev = l.use_item_on("brass_key", "desk_keyhole") # the right key, before the rosette is pressed
	check(ev.has("nothing_happens") and not ev.has("not_for_here"), "the right key too early is only 'nothing happens': %s" % str(ev))
	ev = l.use_item_on("crystal_lens", "emblem_socket") # the right socket, before the bookcase is open
	check(not ev.has("not_for_here"), "the lens at its socket too early does not say 'not here': %s" % str(ev))


func test_chapter2_wrong_item_names_itself() -> void:
	var l := ArchiveLogic.new()
	l.inventory.append("locker_key")
	var ev := l.use_item_on("locker_key", "deck")
	check(ev.has("not_for_here"), "the locker key has no use at the tape deck: %s" % str(ev))


func test_chapter3_wrong_item_names_itself() -> void:
	var l := UndergroundLogic.new()
	l.inventory.append("cloudy_crystal")
	var ev := l.use_item_on("cloudy_crystal", "seed_library")
	check(ev.has("not_for_here"), "a cloudy crystal does not go back into the seed library: %s" % str(ev))
	l.inventory.append("seed_crystal")
	ev = l.use_item_on("seed_crystal", "seed_library")
	check(not ev.has("not_for_here"), "the seed crystal belongs there (only the moment may be wrong): %s" % str(ev))


func test_message_text() -> void:
	var was := TranslationServer.get_locale()
	for loc: String in ["en", "ru", "uz"]:
		TranslationServer.set_locale(loc)
		var name := TranslationServer.translate(ItemDB.name_key("crystal_lens"))
		var msg := RoomBase.no_use_text("crystal_lens", ["not_for_here", "nothing_happens"])
		check(msg.contains(name) and msg != TranslationServer.translate("msg.nothing"), "%s: names the item: %s" % [loc, msg])
		eq(RoomBase.no_use_text("crystal_lens", ["nothing_happens"]), str(TranslationServer.translate("msg.nothing")), "%s: wrong moment" % loc)
	TranslationServer.set_locale(was)
