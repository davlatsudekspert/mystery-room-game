class_name RoomLogic
extends RefCounted
## Base class for a room's pure puzzle logic (no scene-tree access, fully deterministic).
##
## Every player intent is a public method that returns the list of events it caused,
## e.g. ["drawer_opened", "item_added:uv_lamp_empty"]. Scenes react to events and
## always rebuild their visuals from `state`, so a loaded save renders identically.

signal changed(events: Array[String])

const SAVE_VERSION := 1

var state: Dictionary = {}
var inventory: Array[String] = []
var selected: String = ""
var _ev: Array[String] = []


func _init() -> void:
	reset()


func reset() -> void:
	state = default_state()
	inventory = []
	selected = ""


## Override: the full initial state. Only keys listed here are ever loaded from a save.
func default_state() -> Dictionary:
	return {}


## Override: combination recipes as [item_a, item_b, result].
func recipes() -> Array:
	return []


## Override: true once the room/chapter is finished.
func is_complete() -> bool:
	return false


# ------------------------------------------------------------------ inventory
func has_item(id: String) -> bool:
	return inventory.has(id)


func select_item(id: String) -> Array[String]:
	_begin()
	if id == "" or inventory.has(id):
		selected = id
		_emit("selected:" + id)
	return _end()


func combine(a: String, b: String) -> Array[String]:
	_begin()
	if a == b or not inventory.has(a) or not inventory.has(b):
		_emit("combine_failed")
		return _end()
	for r: Array in recipes():
		if (r[0] == a and r[1] == b) or (r[0] == b and r[1] == a):
			_remove_item(a)
			_remove_item(b)
			_add_item(r[2])
			selected = r[2]
			_emit("combined:" + r[2])
			_on_combined(r[2])
			return _end()
	_emit("combine_failed")
	return _end()


## ---------------------------------------------------------------- chapter hooks (HUD / GameState)
## Override: ordered puzzle ids for the progress stat.
func puzzle_ids() -> Array[String]:
	return []


## Override: how many of puzzle_ids() are solved.
func solved_count() -> int:
	return 0


## Override: the hint goal id for the current state ("" = none). Text keys: hint.<goal>.<1..3>.
func hint_goal() -> String:
	return ""


## Override: values to format into the hint text (level 3 names this game's own answer; docs/VARIANTS.md).
func hint_args(_goal: String, _level: int) -> Array:
	return []


## Override: derive this game's own puzzle answers from a seed (docs/VARIANTS.md). Seed 0 keeps the canonical
## answers, so tests and saves from before variants behave exactly as before. Called once for a NEW game.
func apply_seed(_seed: int) -> void:
	pass


## Override: finale options as [[option_id, label_key], ...]; choose_ending(option_id) applies one.
func choice_options() -> Array:
	return []


func choose_ending(_option: String) -> Array[String]:
	_begin()
	_emit("nothing_happens")
	return _end()


## Override: the finale question shown above the options.
func choice_prompt_key() -> String:
	return "ui.choice_prompt"


## Override: optional collectibles as [found, total, label_key] (total 0 = none in this chapter).
func collectibles() -> Array:
	return [0, 0, ""]


## Override: chapter-complete text lines (translation keys), in order.
func epilogue_keys() -> Array[String]:
	return []


## Override: values stored in profile.choices when the chapter is completed.
func profile_choices() -> Dictionary:
	return {}


## Override: apply earlier chapters' choices (profile.choices) to a NEW game of this chapter.
func setup_from_profile(_choices: Dictionary) -> void:
	pass


## Override: per-state item description (e.g. a crystal that now holds an image).
func item_desc_key(id: String) -> String:
	return "item.%s.desc" % id


## Override: true if the item glows in the inspect view (a recorded crystal).
func item_glows(_id: String) -> bool:
	return false


## Override: the intro cards shown on a fresh chapter start.
func intro_keys() -> Array[String]:
	return ["intro.1", "intro.2"]


## Override: the caption shown when the intro hands over control ("" = none).
func intro_caption_key() -> String:
	return "cap.maglock"


## Override: extra events after a successful combination (still inside the action).
func _on_combined(_result: String) -> void:
	pass


func _add_item(id: String) -> void:
	if not inventory.has(id):
		inventory.append(id)
		_emit("item_added:" + id)


func _remove_item(id: String) -> void:
	if inventory.has(id):
		inventory.erase(id)
		if selected == id:
			selected = ""
		_emit("item_removed:" + id)


# ------------------------------------------------------------------ events
func _begin() -> void:
	_ev = []


func _emit(e: String) -> void:
	_ev.append(e)


func _end() -> Array[String]:
	var out: Array[String] = _ev.duplicate()
	_ev = []
	if not out.is_empty():
		changed.emit(out)
	return out


# ------------------------------------------------------------------ persistence
func to_dict() -> Dictionary:
	return {
		"version": SAVE_VERSION,
		"state": state.duplicate(true),
		"inventory": inventory.duplicate(),
		"selected": selected,
	}


## Loads defensively: unknown keys are ignored, missing keys keep defaults,
## values whose type differs from the default are rejected.
func from_dict(d: Dictionary) -> bool:
	reset()
	if typeof(d.get("state")) != TYPE_DICTIONARY:
		return false
	var src: Dictionary = d["state"]
	for key: String in state.keys():
		if not src.has(key):
			continue
		var def_v: Variant = state[key]
		var v: Variant = src[key]
		if _compatible(def_v, v):
			state[key] = _coerce(def_v, v)
	var inv: Variant = d.get("inventory", [])
	if typeof(inv) == TYPE_ARRAY:
		for id: Variant in inv:
			if typeof(id) == TYPE_STRING and not inventory.has(id):
				inventory.append(id)
	var sel: Variant = d.get("selected", "")
	selected = sel if typeof(sel) == TYPE_STRING and inventory.has(sel) else ""
	return true


func _compatible(def_v: Variant, v: Variant) -> bool:
	var a := typeof(def_v)
	var b := typeof(v)
	if a == b:
		if a == TYPE_ARRAY:
			return (def_v as Array).size() == (v as Array).size() or (def_v as Array).is_empty()
		return true
	# JSON turns ints into floats
	return (a == TYPE_INT and b == TYPE_FLOAT) or (a == TYPE_FLOAT and b == TYPE_INT)


func _coerce(def_v: Variant, v: Variant) -> Variant:
	match typeof(def_v):
		TYPE_INT:
			return int(v)
		TYPE_FLOAT:
			return float(v)
		TYPE_ARRAY:
			var out: Array = []
			var proto: Variant = (def_v as Array)[0] if not (def_v as Array).is_empty() else null
			for x: Variant in v:
				var int_like := typeof(x) == TYPE_FLOAT and float(x) == floorf(float(x))
				if int_like and (proto == null or typeof(proto) == TYPE_INT):
					out.append(int(x))
				else:
					out.append(x)
			return out
		TYPE_DICTIONARY:
			return (v as Dictionary).duplicate(true)
	return v
