extends Node
## Language selection: device detection, English fallback, live switching.

signal language_changed(code: String)

const SUPPORTED: Array[String] = ["en", "ru", "uz"]
const NATIVE_NAMES := {"en": "English", "ru": "Русский", "uz": "Oʻzbekcha"}


func _ready() -> void:
	var lang: String = Settings.get_value("language")
	apply(lang if lang != "" else detect_device_language())


static func detect_device_language() -> String:
	return normalize(OS.get_locale_language())


## Maps any locale ("ru_RU", "uz_Latn_UZ", "pt") to a supported code, defaulting to English.
static func normalize(locale: String) -> String:
	var code := locale.to_lower().replace("-", "_").get_slice("_", 0)
	return code if SUPPORTED.has(code) else "en"


func is_first_launch() -> bool:
	return str(Settings.get_value("language")) == ""


func current() -> String:
	return normalize(TranslationServer.get_locale())


func apply(code: String) -> void:
	TranslationServer.set_locale(normalize(code))
	language_changed.emit(normalize(code))


## Called when the player picks a language (first-launch picker or Settings).
func choose(code: String) -> void:
	var c := normalize(code)
	Settings.set_value("language", c)
	apply(c)
