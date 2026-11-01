class_name HoldTable
extends RefCounted
## Chapter 2 expansion, docs/CHAPTER2_EXPANSION.md section 12 (hands layer, phase 1): which selected items are shown in the
## hand layer, and how. Pure data: more items (Chapter 3 meter, keys, ...) and more rooms only add rows.
##   model   : item model (default ItemDB.model_path)
##   pos     : where the item rests, in the camera's local frame (metres, x right, y up, -z ahead) at the reference fov
##   rot     : Euler degrees of the model
##   scale   : model scale
##   audio   : tool name of the foley ids hand_pickup_/hand_equip_/hand_putaway_<tool> (docs/AUDIO_CH2X.md), "" = none
##   beam    : a UV-style cone from the item to the finger (the lamp)
##   strike  : the item swings when the room calls HandLayer.strike() (the mallet)
## An item with no row and not listed in NONE is a test failure (tests/test_hold_table.gd): every item is decided once.
## Items listed in NONE keep today's behaviour (the bag's icon, no hand).

const REF_FOV := 62.0
const ROWS := {
	"uv_lamp": {"pos": Vector3(0.26, -0.2, -0.55), "rot": Vector3(-70, 20, 10), "scale": 1.0, "audio": "uvlamp", "beam": true},
	"mallet": {"pos": Vector3(0.24, -0.19, -0.5), "rot": Vector3(-30, 0, 20), "scale": 1.0, "audio": "mallet", "strike": true},
	"wipe_cloth": {"pos": Vector3(0.22, -0.2, -0.45), "rot": Vector3(-60, 0, 0), "scale": 1.4, "audio": "cloth"},
	"pocket_receiver": {"pos": Vector3(0.24, -0.2, -0.5), "rot": Vector3(-55, 160, 0), "scale": 1.0, "audio": ""},
	"locker_key": {"pos": Vector3(0.22, -0.18, -0.42), "rot": Vector3(-60, 0, 0), "scale": 1.6, "audio": "keys"},
	"brass_key": {"pos": Vector3(0.22, -0.18, -0.42), "rot": Vector3(-60, 0, 0), "scale": 1.6, "audio": "keys"},
}
const NONE: Array[String] = [
	"notebook", "uv_lamp_empty", "battery_cell", "crystal_lens", "strand_letter", "radio_valve",
	"breaker_handle", "leyla_photo", "mirror_item", "leyla_badge", "index_card", "blank_card", "request_card",
	"personnel_file", "tape_1996", "tape_1997", "tape_1998", "film_reel", "crystal_blank_1", "crystal_blank_2",
	"crystal_sign", "crystal_mark", "emblem_slide", "strand_key", "leyla_key", "floor_plan", "frost_sketch",
	"roll_slips", "pass_key", "staff_print", "projector_lamp", "key_diamond", "key_triangle", "key_circle",
	"key_square", "resonance_meter", "ecg_strip", "strand_letters", "seed_crystal", "nursery_crystal",
	"cloudy_crystal", "tower_key_1", "tower_key_2", "tower_key_3", "tower_key_4", "strand_log", "pocket_watch",
	"strand_last_letter", "reverse_pawl", "leyla_note_1998", "leyla_parcel"
]


static func row(id: String) -> Dictionary:
	return ROWS.get(id, {})


static func has_hand(id: String) -> bool:
	return ROWS.has(id)


## Foley tool for an item ("" = none): any key maps to "keys".
static func audio_tool(id: String) -> String:
	if ROWS.has(id):
		return str(ROWS[id].get("audio", ""))
	if id.begins_with("key_") or id.ends_with("_key"):
		return "keys"
	return ""
