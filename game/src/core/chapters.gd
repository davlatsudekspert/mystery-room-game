class_name Chapters
extends RefCounted
## Data-driven chapter registry. Append a dictionary to add a chapter; no other code changes needed.

const LIST: Array[Dictionary] = [
	{"id": "ch1", "number": 1, "title": "chapter.ch1.title", "subtitle": "chapter.ch1.subtitle",
		"scene": "res://src/rooms/lab7/lab7.tscn", "logic": "res://src/rooms/lab7/lab7_logic.gd",
		"product": "", "released": true},
	{"id": "ch2", "number": 2, "title": "chapter.ch2.title", "subtitle": "chapter.ch2.subtitle",
		"scene": "res://src/rooms/archive/archive.tscn", "logic": "res://src/rooms/archive/archive_logic.gd",
		"product": "full_game", "released": true}, # 3D playthroughs (both lens paths, variant seeds) + player review
	{"id": "ch3", "number": 3, "title": "chapter.ch3.title", "subtitle": "chapter.ch3.subtitle",
		"scene": "res://src/rooms/underground/underground.tscn", "logic": "res://src/rooms/underground/underground_logic.gd",
		"product": "full_game", "released": false}, # scene in integration (models arriving by group); unreleased
	{"id": "ch4", "number": 4, "title": "chapter.ch4.title", "subtitle": "chapter.ch4.subtitle",
		"scene": "", "logic": "res://src/rooms/array_hall/array_hall_logic.gd",
		"product": "full_game", "released": false}, # logic and tests done; the scene comes with the Ch4 models. Unreleased: the HUD only offers a chapter with released == true, so the empty scene path is never loaded
]


static func get_chapter(id: String) -> Dictionary:
	for c: Dictionary in LIST:
		if c["id"] == id:
			return c
	return {}


static func is_free(id: String) -> bool:
	return str(get_chapter(id).get("product", "x")) == ""


static func next_of(id: String) -> String:
	for i in LIST.size() - 1:
		if LIST[i]["id"] == id:
			return LIST[i + 1]["id"]
	return ""


static func new_logic(id: String) -> RoomLogic:
	var path: String = get_chapter(id).get("logic", "")
	if path == "":
		return null
	return (load(path) as GDScript).new()
