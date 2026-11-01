extends TestBase
## The upper floor's pictures (docs/CHAPTER2_EXPANSION.md N7-N10) are drawn from this game's answers and carry no words.


func test_load_plate_and_floor_icons_are_drawn() -> void:
	for load in ArchiveExpData.LOADS:
		var tex := ArchiveUpperArt.lift_plate(load)
		check(tex != null and tex.get_width() == 400, "load %d: the plate is drawn" % load)
	for k in 3:
		check(ArchiveUpperArt.lift_icon(k) != null, "floor icon %d is drawn" % k)


func test_every_game_draws_its_slips_strips_and_label() -> void:
	for seed_i in 20:
		var l := ArchiveLogic.new_expanded(1000 + seed_i)
		var slips := l.board_slips()
		check(slips.size() >= ArchiveExpData.MIN_SLIPS and slips.size() <= ArchiveExpData.MAX_SLIPS, "seed %d: 4 to 6 slips" % seed_i)
		for sl: Array in slips:
			var img := ArchiveUpperArt.slip_image(sl, -1)
			check(img.get_width() == 240 and img.get_height() == 170, "seed %d: a slip is 240 x 170" % seed_i)
		var sheet := ArchiveUpperArt.slips_sheet(slips, l.board_slip_status())
		check(sheet != null and sheet.get_width() > 400, "seed %d: the reading sheet is drawn" % seed_i)
		for i in ArchiveExpData.STRIPS:
			var strip := ArchiveUpperArt.strip_texture(int(l.state["v_strips"][i]), [0, 1, 2, 3])
			check(strip != null and strip.get_width() == 1024, "seed %d: strip %d is drawn" % [seed_i, i])
		check(ArchiveUpperArt.cabinet_label(l.cabinet_label()) != null, "seed %d: the cabinet label is drawn" % seed_i)
		check(ArchiveUpperArt.staff_print(l.cabinet_label(), l.cabinet_digits()) != null, "seed %d: the print is drawn" % seed_i)


func test_a_wrong_focus_blurs_and_the_right_print_carries_digits() -> void:
	var sharp := ArchiveUpperArt.enlarger_image(2, 0, 1.0, []).get_image() # the picture alone: the digit strip is never blurred
	var soft := ArchiveUpperArt.enlarger_image(2, 8, 1.0, []).get_image()
	var blank := ArchiveUpperArt.enlarger_image(2, 0, 1.0, []).get_image()
	var with_digits := ArchiveUpperArt.enlarger_image(2, 0, 1.0, [1, 2, 3, 4]).get_image()
	var dsharp := 0.0
	var dsoft := 0.0
	for y in range(20, 100):
		for x in range(20, 140):
			dsharp += pow(sharp.get_pixel(x, y).get_luminance() - sharp.get_pixel(x + 1, y).get_luminance(), 2.0)
			dsoft += pow(soft.get_pixel(x, y).get_luminance() - soft.get_pixel(x + 1, y).get_luminance(), 2.0)
	check(dsharp > dsoft * 2.0, "a sharp print has steeper edges than a blurred one")
	check(with_digits.get_pixel(60, 90) != blank.get_pixel(60, 90) or with_digits.get_pixel(64, 92) != blank.get_pixel(64, 92) or with_digits.get_pixel(46, 99) != blank.get_pixel(46, 99), "the digits are pencilled only on the right print")
