class_name CrashGuard
extends RefCounted
## Remembers how far the running session got, so a crash on a phone can be located and recovered from.
## The current stage is written to user:// before each risky step (loading a scene and drawing its first
## frames); a clean pause or quit overwrites it. When a launch finds a "load:" stage, the previous session
## died while loading or first drawing a scene: the game turns on safe graphics (Settings "safe_graphics":
## no positional light shadows, reflection probes or particles), and tester builds name the stage in the
## main menu. A crash report from the phone then says what failed; this keeps the game playable meanwhile.

const PATH := "user://session_stage.txt"

## The stage the previous session ended in ("" = it ended cleanly). Read once at launch by read_previous().
static var previous := ""
## This launch turned safe graphics on because of previous (the main menu says so once).
static var switched_to_safe := false
static var _stage := ""


static func stage() -> String:
	return _stage


static func mark(stage: String) -> void:
	_stage = stage
	_write(stage)


## The app goes to the background or quits: whatever happens next is not a crash of this stage.
static func paused() -> void:
	_write("paused")


static func resumed() -> void:
	_write(_stage)


## Called once at launch, before the first mark().
static func read_previous() -> String:
	previous = ""
	if FileAccess.file_exists(PATH):
		var stage := FileAccess.get_file_as_string(PATH).get_slice("\t", 0).strip_edges()
		if stage not in ["", "paused", "menu"]:
			previous = stage
	return previous


static func crashed_while_loading() -> bool:
	return previous.begins_with("load:")


static func _write(stage: String) -> void:
	var f := FileAccess.open(PATH, FileAccess.WRITE)
	if f != null:
		f.store_string("%s\t%d\n" % [stage, int(Time.get_unix_time_from_system())])
		f.close()
