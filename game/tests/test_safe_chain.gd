extends TestBase
## Chapter 1's safe code chain: the UV page's symbols -> Strand's Table of Resonances poster (dots beside each
## symbol) -> digits. And Panel 7's notebook page, whose four lamp icons are drawn inline (language-neutral).

const LANGS := {"en": 1, "ru": 2, "uz": 3} # column in strings.csv
const PANEL_ICONS: Array[String] = ["panel_lock", "panel_light", "panel_array", "panel_vent"]


func _rows() -> Dictionary:
	var rows := {}
	var csv := FileAccess.open("res://localization/strings.csv", FileAccess.READ)
	if csv == null:
		return rows
	while not csv.eof_reached():
		var row := csv.get_csv_line()
		if row.size() >= 4:
			rows[row[0]] = row
	return rows


func test_poster_dots_match_the_logic() -> void:
	# tools/textures/make_decals.py draws the poster and the UV page's glyphs from its own GLYPH_DOTS table
	var src := FileAccess.get_file_as_string(ProjectSettings.globalize_path("res://") + "../tools/textures/make_decals.py")
	check(src != "", "make_decals.py is readable")
	var re := RegEx.create_from_string("\"(\\w+)\":\\s*(\\d)")
	var start := src.find("GLYPH_DOTS = {")
	var end := src.find("}", start)
	var py := {}
	for m in re.search_all(src.substr(start, end - start)):
		py[m.get_string(1)] = int(m.get_string(2))
	eq(py.size(), Lab7Logic.GLYPH_DOTS.size(), "the poster shows every glyph the logic knows")
	for g: String in Lab7Logic.GLYPH_DOTS:
		eq(py.get(g, -1), int(Lab7Logic.GLYPH_DOTS[g]), "the poster's dots for %s" % g)
		check(ResourceLoader.exists("res://assets/ui/glyphs/%s.png" % g), "UV page art for %s exists" % g)
	check(ResourceLoader.exists("res://assets/textures/decals/poster_resonance.jpg"), "poster picture exists")


func test_every_variant_code_is_the_dots_of_its_glyphs() -> void:
	for seed in range(1, 201):
		var l := Lab7Logic.new()
		l.apply_seed(seed)
		var code := ""
		for g: Variant in l.safe_glyphs():
			code += str(int(Lab7Logic.GLYPH_DOTS[str(g)]))
		eq(l.safe_code(), code, "seed %d: the code is the dot counts, in page order" % seed)


func test_safe_hints_point_at_the_poster_in_every_language() -> void:
	var rows := _rows()
	for lang: String in LANGS:
		var c: int = LANGS[lang]
		check((rows["hint.safe.1"] as PackedStringArray)[c].contains("Tabula Resonantiarum"), "%s: safe hint 1 names the poster" % lang)
		check((rows["hint.safe.2"] as PackedStringArray)[c].contains("0"), "%s: safe hint 2 says what no dots mean" % lang)
		check((rows["doc.notebook.p5_uv"] as PackedStringArray)[c] != "", "%s: the UV page line exists" % lang)


func test_notebook_panel_page_has_the_four_lamp_icons() -> void:
	var rows := _rows()
	for lang: String in LANGS:
		var text: String = (rows["doc.notebook.p4"] as PackedStringArray)[LANGS[lang]]
		for icon in PANEL_ICONS:
			check(text.contains("{%s}" % icon), "%s: notebook page 4 shows %s" % [lang, icon])
	for icon in PANEL_ICONS:
		check(ResourceLoader.exists("res://assets/ui/glyphs/%s.png" % icon), "%s art exists" % icon)
