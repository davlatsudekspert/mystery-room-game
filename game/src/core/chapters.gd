class_name Chapters
extends RefCounted
## Data-driven chapter registry. Append a dictionary to add a chapter; no other code changes needed.

const LIST: Array[Dictionary] = [
	{"id": "ch1", "number": 1, "title": "chapter.ch1.title", "subtitle": "chapter.ch1.subtitle",
		"scene": "res://src/rooms/lab7/lab7.tscn", "logic": "res://src/rooms/lab7/lab7_logic.gd",
		"product": "", "released": true},
	{"id": "ch2", "number": 2, "title": "chapter.ch2.title", "subtitle": "chapter.ch2.subtitle",
		"scene": "res://src/rooms/archive/archive.tscn", "logic": "res://src/rooms/archive/archive_logic.gd",
		"product": "full_game", "released": false}, # released once the room scene passes its playthrough
	{"id": "ch3", "number": 3, "title": "chapter.ch3.title", "subtitle": "chapter.ch3.subtitle",
		"scene": "", "logic": "res://src/rooms/underground/underground_logic.gd",
		"product": "full_game", "released": false}, # logic only; the room scene comes next
	{"id": "ch4", "number": 4, "title": "chapter.ch4.title", "subtitle": "chapter.ch4.subtitle",
		"scene": "", "logic": "", "product": "full_game", "released": false},
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
