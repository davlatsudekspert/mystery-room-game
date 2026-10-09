class_name ItemDB
extends RefCounted
## Static item table. Names/descriptions are translation keys: item.<id>.name / item.<id>.desc

const ITEMS := {
	"notebook": {"model": "notebook", "doc": "notebook"},
	"uv_lamp_empty": {"model": "uv_lamp"},
	"battery_cell": {"model": "battery_cell"},
	"uv_lamp": {"model": "uv_lamp", "tool": "uv"},
	"brass_key": {"model": "brass_key"},
	"crystal_lens": {"model": "crystal_lens"},
	"strand_letter": {"model": "letter", "doc": "letter"},
	"radio_valve": {"model": "radio_valve"},
	"breaker_handle": {"model": "breaker_handle"},
	"leyla_photo": {"model": "photo_print", "doc": "photo"},
	"mirror_item": {"model": "mirror_item"},
	# Chapter 2
	"leyla_badge": {"model": "leyla_badge", "doc": "badge"},
	"index_card": {"model": "index_card", "doc": "index_card"},
	"blank_card": {"model": "request_card"},
	"request_card": {"model": "request_card"},
	"personnel_file": {"model": "file_folder", "doc": "personnel_file"},
	"locker_key": {"model": "locker_key"},
	"pocket_receiver": {"model": "pocket_receiver", "tool": "receiver"},
	"tape_1996": {"model": "tape_reel", "doc": "tape_1996"},
	"tape_1997": {"model": "tape_reel", "doc": "tape_1997"},
	"tape_1998": {"model": "tape_reel", "doc": "tape_1998"},
	"film_reel": {"model": "film_reel"},
	"crystal_blank_1": {"model": "lumen_crystal"},
	"crystal_blank_2": {"model": "lumen_crystal"},
	"crystal_sign": {"model": "lumen_crystal"},
	"crystal_mark": {"model": "lumen_crystal"},
	"emblem_slide": {"model": "glass_slide"},
	"strand_key": {"model": "key_strand"},
	"leyla_key": {"model": "key_leyla"},
	# Chapter 3 (models are built with the Chapter 3 room; until then the inventory shows the item name)
	"key_diamond": {"model": "key_diamond"},
	"key_triangle": {"model": "key_triangle"},
	"key_circle": {"model": "key_circle"},
	"key_square": {"model": "key_square"},
	"resonance_meter": {"model": "resonance_meter", "tool": "meter"},
	"ecg_strip": {"model": "ecg_strip"},
	"strand_letters": {"model": "letter"},
	"seed_crystal": {"model": "seed_crystal"},
	"nursery_crystal": {"model": "nursery_crystal"},
	"cloudy_crystal": {"model": "nursery_crystal"},
}

const FLAT := ["notebook", "strand_letter", "leyla_photo", "brass_key", "leyla_badge", "index_card", "blank_card",
	"request_card", "personnel_file", "emblem_slide", "strand_key", "leyla_key", "locker_key", "key_diamond",
	"key_triangle", "key_circle", "key_square", "ecg_strip", "strand_letters"]


static func exists(id: String) -> bool:
	return ITEMS.has(id)


static func name_key(id: String) -> String:
	return "item.%s.name" % id


static func desc_key(id: String) -> String:
	return "item.%s.desc" % id


static func model_path(id: String) -> String:
	return "res://assets/models/%s.glb" % ITEMS.get(id, {}).get("model", id)


static func icon_path(id: String) -> String:
	return "res://assets/ui/items/%s.png" % id


static func document(id: String) -> String:
	return ITEMS.get(id, {}).get("doc", "")


## Extra rotation (degrees about X) so flat items face the camera in icons / inspect view.
static func view_tilt(id: String) -> float:
	return 70.0 if id in FLAT else 0.0


## (Not "is_tool": that name is taken by Script.is_tool() and a call through the class name hits it.)
static func is_tool_item(id: String) -> bool:
	return ITEMS.get(id, {}).has("tool")
