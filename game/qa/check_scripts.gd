extends Node
## Loads every .gd file to surface parse/type errors (CI step). Exit 1 on any failure.


func _ready() -> void:
	var bad := 0
	var files := _collect("res://src") + _collect("res://qa") + _collect("res://tests")
	for f in files:
		var s: Script = load(f)
		if s == null or not s.can_instantiate():
			printerr("BROKEN " + f)
			bad += 1
	print("checked %d scripts, %d broken" % [files.size(), bad])
	get_tree().quit(1 if bad > 0 else 0)


func _collect(dir: String) -> Array[String]:
	var out: Array[String] = []
	var d := DirAccess.open(dir)
	if d == null:
		return out
	for f in d.get_files():
		if f.ends_with(".gd"):
			out.append(dir + "/" + f)
	for sub in d.get_directories():
		out.append_array(_collect(dir + "/" + sub))
	return out
