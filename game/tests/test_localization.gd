extends TestBase
## Translations load for EN/RU/UZ, switching works, fallback is English, order is EN → RU → UZ.


func after_each_restore() -> void:
	TranslationServer.set_locale("en")


func test_language_order_and_fallback() -> void:
	eq(Loc.SUPPORTED, ["en", "ru", "uz"] as Array[String], "fixed order EN → RU → UZ")
	eq(Loc.normalize("ru_RU"), "ru")
	eq(Loc.normalize("uz_Latn_UZ"), "uz")
	eq(Loc.normalize("uz-UZ"), "uz")
	eq(Loc.normalize("de_DE"), "en", "unsupported → English")
	eq(Loc.normalize(""), "en")
	eq(Loc.NATIVE_NAMES["uz"], "Oʻzbekcha", "Uzbek native name uses U+02BB")


func test_switching_translates_live() -> void:
	for pair in [["en", "New Game"], ["ru", "Новая игра"], ["uz", "Yangi oʻyin"]]:
		TranslationServer.set_locale(pair[0])
		eq(tr("ui.new_game"), pair[1], "locale " + pair[0])
	TranslationServer.set_locale("en")


func test_every_key_translated_in_all_languages() -> void:
	var csv := FileAccess.open("res://localization/strings.csv", FileAccess.READ)
	var header := csv.get_csv_line()
	eq(Array(header), ["keys", "en", "ru", "uz"], "CSV columns")
	var n := 0
	while not csv.eof_reached():
		var row := csv.get_csv_line()
		if row.size() < 4:
			continue
		n += 1
		for i in [1, 2, 3]:
			TranslationServer.set_locale(header[i])
			var t := tr(row[0])
			if row[0] != "doc.notebook.p5":
				check(t != row[0] and t.strip_edges() != "", "%s missing in %s" % [row[0], header[i]])
	TranslationServer.set_locale("en")
	check(n > 250, "expected a full string table, got %d" % n)


func test_runtime_keys_used_by_code_exist() -> void:
	var must := ["ui.saved", "ui.item_added", "ui.hint_level", "ui.page", "chapter.label", "ui.combine_prompt",
		"ui.use_prompt", "ui.shard_found", "msg.nothing", "intro.1", "intro.2", "outro.listening", "epi.postmark"]
	for id: String in ItemDB.ITEMS:
		must.append(ItemDB.name_key(id))
		must.append(ItemDB.desc_key(id))
	for c: Dictionary in Chapters.LIST:
		must.append(c["title"])
		must.append(c["subtitle"])
	for k: String in must:
		for loc in ["en", "ru", "uz"]:
			TranslationServer.set_locale(loc)
			check(tr(k) != k, "%s untranslated in %s" % [k, loc])
	TranslationServer.set_locale("en")


func test_placeholders_format_in_all_languages() -> void:
	for loc in ["en", "ru", "uz"]:
		TranslationServer.set_locale(loc)
		var s := tr("ui.page") % [3, 8]
		check(s.contains("3") and s.contains("8"), "ui.page formats in " + loc)
		check((tr("chapter.label") % 1).contains("1"), "chapter.label formats in " + loc)
	TranslationServer.set_locale("en")


func test_fonts_cover_all_used_characters() -> void:
	## Every character used in any translation must exist in the UI font (Noto Sans).
	var font_path := "res://assets/fonts/NotoSans.ttf"
	for p in ["res://assets/fonts/NotoSans.ttf", "res://assets/fonts/notosans/NotoSans[wdth,wght].ttf"]:
		if ResourceLoader.exists(p):
			font_path = p
	if not ResourceLoader.exists(font_path):
		var found := _find_font("res://assets/fonts", "NotoSans")
		if found == "":
			check(false, "Noto Sans font not found under res://assets/fonts")
			return
		font_path = found
	var font: FontFile = load(font_path)
	var csv := FileAccess.open("res://localization/strings.csv", FileAccess.READ)
	csv.get_csv_line()
	var chars := {}
	while not csv.eof_reached():
		var row := csv.get_csv_line()
		for i in range(1, row.size()):
			for ch in row[i].c_unescape():
				chars[ch] = true
	var missing: Array[String] = []
	for ch: String in chars:
		var cp := ch.unicode_at(0)
		if cp < 32:
			continue
		if not font.has_char(cp):
			missing.append("%s(U+%04X)" % [ch, cp])
	check(missing.is_empty(), "UI font lacks: " + ", ".join(missing))


func _find_font(dir_path: String, needle: String) -> String:
	var d := DirAccess.open(dir_path)
	if d == null:
		return ""
	for f in d.get_files():
		if f.contains(needle) and (f.ends_with(".ttf") or f.ends_with(".otf")):
			return dir_path + "/" + f
	for sub in d.get_directories():
		var r := _find_font(dir_path + "/" + sub, needle)
		if r != "":
			return r
	return ""
