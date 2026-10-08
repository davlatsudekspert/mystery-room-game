extends Node
## Versioned JSON saves with atomic writes (temp file + rename) and a backup copy.
## Two files: the chapter save (puzzle state) and the profile (choices, completed chapters, achievements).

signal saved
signal save_failed

const SAVE_PATH := "user://save_v1.json"
const PROFILE_PATH := "user://profile_v1.json"
const VERSION := 1

var save_path := SAVE_PATH
var profile_path := PROFILE_PATH


func has_save() -> bool:
	return not load_game().is_empty()


func save_game(data: Dictionary) -> bool:
	var payload := data.duplicate(true)
	payload["version"] = VERSION
	payload["timestamp"] = Time.get_unix_time_from_system()
	var ok := _write_atomic(save_path, JSON.stringify(payload))
	if ok:
		saved.emit()
	else:
		save_failed.emit()
	return ok


## Returns {} when there is no valid save. Falls back to the .bak copy if the main file is corrupt.
func load_game() -> Dictionary:
	for p in [save_path, save_path + ".bak"]:
		var d := _read_json(p)
		if not d.is_empty() and int(d.get("version", 0)) >= 1:
			return _migrate(d)
	return {}


func delete_game() -> void:
	for p in [save_path, save_path + ".bak", save_path + ".tmp"]:
		if FileAccess.file_exists(p):
			DirAccess.remove_absolute(p)


func load_profile() -> Dictionary:
	var d := _read_json(profile_path)
	if d.is_empty():
		d = _read_json(profile_path + ".bak")
	var out := {"choices": {}, "completed": [], "achievements": [], "hints_used": 0}
	for k: String in out:
		if d.has(k) and typeof(d[k]) == typeof(out[k]):
			out[k] = d[k]
	return out


func save_profile(profile: Dictionary) -> bool:
	return _write_atomic(profile_path, JSON.stringify(profile))


func _migrate(d: Dictionary) -> Dictionary:
	# Future: upgrade older versions here. v1 is current.
	return d


func _read_json(p: String) -> Dictionary:
	if not FileAccess.file_exists(p):
		return {}
	var f := FileAccess.open(p, FileAccess.READ)
	if f == null:
		return {}
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	return parsed if typeof(parsed) == TYPE_DICTIONARY else {}


func _write_atomic(p: String, text: String) -> bool:
	var tmp := p + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(text)
	f.close()
	if FileAccess.file_exists(p):
		DirAccess.copy_absolute(p, p + ".bak")
	return DirAccess.rename_absolute(tmp, p) == OK
