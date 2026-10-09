class_name CrashGuard
extends RefCounted
## Remembers how far the running session got, so a crash on a phone can be located and recovered from.
## The current stage is written to user:// before each risky step: "load:<scene>" while the scene loads and
## builds, "draw:<scene>" while the GPU draws its first seconds; a clean pause or quit overwrites it. When a
## launch finds either, the previous session died there: the game turns on safe graphics (Settings "safe_graphics":
## no positional light shadows, reflection probes or particles), and tester builds name the stage in the
## main menu. A crash report from the phone then says what failed; this keeps the game playable meanwhile.

const PATH := "user://session_stage.txt"
## Safe graphics levels. Each crash while loading or first drawing a scene raises the level by one at the next
## launch, so a tester's retries narrow down which feature the phone's GPU driver fails on:
##   1 = no MSAA anywhere;
##   2 = also no positional light shadows, reflection probes or particles;
##   3 = also no decals, glow or directional shadows.
## The Settings toggle "safe_graphics" (the player's own choice) means level 3.
const MAX_LEVEL := 3
## Raised when a build changes what the levels do: the next launch starts again from level 0 (a level reached
## on an older build says nothing about this one).
const EPOCH := 1

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


## A finer step inside the current stage (the model or part being built), so "last stop" names it.
static func detail(what: String) -> void:
	_write("%s %s" % [_stage, what])


static func safe_level() -> int:
	if bool(Settings.get_value("safe_graphics")):
		return MAX_LEVEL
	return clampi(int(Settings.get_value("safe_level")), 0, MAX_LEVEL)


## Called once at launch after read_previous(): resets levels from an older epoch, then raises the level after a
## crash while loading or drawing a scene. Returns true when the level was raised.
static func update_safe_level() -> bool:
	if int(Settings.get_value("safe_epoch")) != EPOCH:
		Settings.set_value("safe_epoch", EPOCH)
		Settings.set_value("safe_level", 0)
		Settings.set_value("safe_graphics", false)
	if not crashed_while_loading() or safe_level() >= MAX_LEVEL:
		return false
	Settings.set_value("safe_level", safe_level() + 1)
	return true


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
	return previous.begins_with("load:") or previous.begins_with("draw:")


static func _write(stage: String) -> void:
	var f := FileAccess.open(PATH, FileAccess.WRITE)
	if f != null:
		f.store_string("%s\t%d\n" % [stage, int(Time.get_unix_time_from_system())])
		f.close()
