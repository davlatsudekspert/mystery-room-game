extends Node
## Player settings persisted to user://settings.cfg.

signal changed(key: String)

const PATH := "user://settings.cfg"
const DEFAULTS := {
	"language": "", # "" until the player confirms a language on first launch
	"music_volume": 0.7,
	"sfx_volume": 0.9,
	"ambience_volume": 0.8,
	"text_scale": 1.0, # the player's multiplier on top of the automatic, screen-based size (UITheme.auto_scale)
	"haptics": true,
	"reduce_motion": false,
	"invert_look": false,
	"look_sensitivity": 1.0,
	"brightness": 1.0, # scene exposure multiplier (dark rooms on dim phone screens)
	"render_scale": 1.0, # 3D resolution chosen by PerfGuard on phones (not shown in the UI)
}
const TEXT_SCALES: Array[float] = [0.9, 1.0, 1.15, 1.3]

var values: Dictionary = DEFAULTS.duplicate()
var path := PATH
## Screen emulation for QA renders (never saved): {"size": Vector2i, "dpi": float, "safe": Rect2i} in device px.
## UITheme reads it instead of DisplayServer, so a desktop run can lay the UI out exactly as on a phone.
var emulate: Dictionary = {}


func _ready() -> void:
	load_settings()


func get_value(key: String) -> Variant:
	return values.get(key, DEFAULTS.get(key))


func set_value(key: String, v: Variant) -> void:
	if not DEFAULTS.has(key):
		push_warning("Unknown setting " + key)
		return
	if typeof(v) != typeof(DEFAULTS[key]) and not (typeof(DEFAULTS[key]) == TYPE_FLOAT and typeof(v) == TYPE_INT):
		push_warning("Bad type for setting " + key)
		return
	if key == "text_scale":
		v = clampf(float(v), 0.8, 1.5)
	elif key.ends_with("_volume") or key == "look_sensitivity":
		v = clampf(float(v), 0.0, 2.0 if key == "look_sensitivity" else 1.0)
	elif key == "render_scale":
		v = clampf(float(v), 0.5, 1.0)
	elif key == "brightness":
		v = clampf(float(v), 0.7, 1.6)
	values[key] = v
	save_settings()
	changed.emit(key)


func load_settings() -> void:
	values = DEFAULTS.duplicate()
	var cfg := ConfigFile.new()
	if cfg.load(path) != OK:
		return
	for key: String in DEFAULTS:
		var v: Variant = cfg.get_value("settings", key, DEFAULTS[key])
		if typeof(v) == typeof(DEFAULTS[key]) or (typeof(DEFAULTS[key]) == TYPE_FLOAT and typeof(v) == TYPE_INT):
			values[key] = v


func save_settings() -> void:
	var cfg := ConfigFile.new()
	for key: String in values:
		cfg.set_value("settings", key, values[key])
	cfg.save(path)


func reset_to_defaults() -> void:
	var lang: String = values["language"]
	values = DEFAULTS.duplicate()
	values["language"] = lang
	save_settings()
	for key: String in values:
		changed.emit(key)
