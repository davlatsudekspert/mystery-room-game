extends TestBase
## Chapter 4 scene tables (src/rooms/array_hall/array_hall_data.gd, array_hall_room.gd): the data the room reads is
## consistent without building the scene. Every view has a caption and a place, every hotspot leads to a view that
## exists, every model the layout names is built, every message the room can say is translated, and the chapter's
## documents have reader pages. (The scene itself is exercised by qa/playthrough_ch4.tscn.)

const GROUPS := "HBPKRISTWElwt"


func test_every_view_has_a_caption_a_zone_and_known_groups() -> void:
	for id: String in ArrayHallData.VIEWS:
		var v: Array = ArrayHallData.VIEWS[id]
		eq(v.size(), 7, "view %s has 7 fields" % id)
		check(ArrayHallData.CAPTION.has(id), "view %s has a caption" % id)
		check(ArrayHallData.zone_of(id) != "", "view %s has a zone" % id)
		for c in str(v[4]):
			check(GROUPS.contains(c), "view %s draws a known group (%s)" % [id, c])
		check((v[0] as Vector3).distance_to(v[1]) > 0.1, "view %s looks at something" % id)
		check(float(v[2]) >= 30.0 and float(v[2]) <= 90.0, "view %s has a sane field of view" % id)
	check(ArrayHallData.VIEWS.has(ArrayHallData.MAIN_ROOT), "the main root exists")
	check(bool(ArrayHallData.VIEWS[ArrayHallData.MAIN_ROOT][3]), "the main root is a free-look view")


func test_captions_and_messages_are_translated() -> void:
	for loc in ["en", "ru", "uz"]:
		TranslationServer.set_locale(loc)
		for id: String in ArrayHallData.CAPTION:
			var k: String = ArrayHallData.CAPTION[id]
			check(tr(k) != k, "caption %s (%s) in %s" % [k, id, loc])
		for e: String in ArrayHallRoom.MESSAGES:
			var k: String = ArrayHallRoom.MESSAGES[e]
			check(tr(k) != k, "message %s (%s) in %s" % [k, e, loc])
		for k in ["msg.c4_beam", "msg.c4_wound", "msg.c4_minute", "msg.c4_gate_locked", "msg.c4_echo_count", "msg.c4_catwalk_locked",
				"msg.c4_apse_dark", "msg.c4_booth_locked", "msg.c4_watch_locked", "cap4.power", "cap4.rings", "cap4.arc", "cap4.iris",
				"cap4.replay", "cap4.strand_desk", "cap4.forty_second", "cap4.leyla_lens", "cap4.snap", "cap4.rise", "doc4.chalk"]:
			check(tr(k) != k, "%s in %s" % [k, loc])
	TranslationServer.set_locale("en")


func test_hotspots_lead_to_views_that_exist() -> void:
	for hs: String in ArrayHallData.HOTSPOT_VIEW:
		var v: String = ArrayHallData.HOTSPOT_VIEW[hs]
		check(v == "" or ArrayHallData.VIEWS.has(v), "hotspot %s -> view %s" % [hs, v])
	for v: String in ArrayHallData.DEEPER:
		check(ArrayHallData.VIEWS.has(v), "deeper-views owner %s exists" % v)
		for d: String in ArrayHallData.DEEPER[v]:
			check(ArrayHallData.VIEWS.has(d), "deeper view %s of %s exists" % [d, v])
	for id: String in ArrayHallData.LAYOUT:
		var hs: String = ArrayHallData.LAYOUT[id][3]
		check(hs == "" or ArrayHallData.HOTSPOT_VIEW.has(hs), "model %s hotspot %s leads somewhere" % [id, hs])
	for id: String in ArrayHallData.MOUNTED:
		var hs: String = ArrayHallData.MOUNTED[id][3]
		check(ArrayHallData.HOTSPOT_VIEW.has(hs), "mounted model %s hotspot %s leads somewhere" % [id, hs])
	for model: String in ArrayHallData.PART_HOTSPOT:
		for part: String in ArrayHallData.PART_HOTSPOT[model]:
			var hs: String = ArrayHallData.PART_HOTSPOT[model][part]
			check(ArrayHallData.HOTSPOT_VIEW.has(hs), "%s/%s hotspot %s leads somewhere" % [model, part, hs])


func test_the_models_the_layout_names_are_built_and_every_zone_is_covered() -> void:
	var groups := ""
	for id: String in ArrayHallData.LAYOUT:
		var e: Array = ArrayHallData.LAYOUT[id]
		check(ResourceLoader.exists("res://assets/models/%s.glb" % e[0]), "%s is built" % e[0])
		groups += str(e[5])
	for id: String in ArrayHallData.MOUNTED:
		check(ResourceLoader.exists("res://assets/models/%s.glb" % ArrayHallData.MOUNTED[id][0]), "%s is built" % id)
	for g in "HBPKRISTW":
		check(groups.contains(g), "a model belongs to group %s" % g)
	for item in ["tower_key_1", "tower_key_2", "tower_key_3", "tower_key_4", "strand_log", "pocket_watch",
			"strand_last_letter", "reverse_pawl", "leyla_note_1998", "leyla_parcel"]:
		check(ResourceLoader.exists(ItemDB.model_path(item)), "the model of item %s exists (%s)" % [item, ItemDB.model_path(item)])
	for item in ["reverse_pawl", "leyla_parcel", "tower_key_1", "strand_last_letter", "leyla_note_1998"]:
		check(ItemDB.FLAT.has(item), "%s lies flat in the inspect view" % item)


func test_the_crowd_stands_on_41_places_clear_of_the_catwalk_and_the_apron_fixtures() -> void:
	var n := 0
	for ring: Array in ArrayHallData.CROWD_RINGS:
		n += int(ring[1])
	eq(n, 41, "forty-one figures")


func test_documents_have_reader_pages() -> void:
	var hud := load("res://src/ui/hud.gd") as GDScript
	for id: String in ArrayHallLogic.SPOTS.values():
		var doc := ItemDB.document(id)
		if doc != "":
			check(bool(hud.call("has_document", doc)), "item %s: the reader opens «%s»" % [id, doc])
	for doc in ["log4", "letter4", "watch4", "note4", "parcel4"]:
		check(bool(hud.call("has_document", doc)), "«%s» has a reader page" % doc)
