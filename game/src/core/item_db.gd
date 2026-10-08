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
	"leyla_photo": {"model": "letter", "doc": "photo"},
	"mirror_item": {"model": "mirror_item"},
}


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
	return 70.0 if id in ["notebook", "strand_letter", "leyla_photo", "brass_key"] else 0.0


static func is_tool(id: String) -> bool:
	return ITEMS.get(id, {}).has("tool")
