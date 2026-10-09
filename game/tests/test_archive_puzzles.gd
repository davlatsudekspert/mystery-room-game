extends TestBase
## Chapter 2 puzzle logic: every puzzle, wrong inputs, both Chapter 1 lens paths, full solution.


func _new(lens: bool = false, shards: int = 0) -> ArchiveLogic:
	var l := ArchiveLogic.new()
	l.setup_from_profile({"ch1_lens": "take_lens" if lens else "leave_lens", "ch1_shards": shards})
	return l


func test_start_inventory_follows_chapter_1() -> void:
	var leave := _new(false)
	check(leave.has_item("leyla_badge"), "badge at start")
	check(not leave.has_item("crystal_lens"), "no lens on the leave path")
	var take := _new(true)
	check(take.has_item("crystal_lens"), "lens on the take path")
	eq(take.crystal_image("crystal_lens"), "mark", "the Ch1 lens carries Strand's mark")
	var fresh := ArchiveLogic.new() # no Chapter 1 save
	check(fresh.has_item("leyla_badge") and not fresh.has_item("crystal_lens"), "fresh game = leave path")


func test_catalogue() -> void:
	var l := _new()
	check(not l.can_take("index_card"), "card hidden at start")
	l.pull_card(7)
	check(not l.state["card_shown"], "no card without a drawer")
	l.open_cat_drawer(4)
	l.pick_divider(2)
	var ev := l.pull_card(7)
	check(ev.has("cat_card:0427"), "other cards can be read: %s" % str(ev))
	check(not l.can_take("index_card"), "a stranger's card cannot be taken")
	l.pick_divider(1)
	ev = l.pull_card(7)
	check(ev.has("cat_card_leyla"), "Leyla's card 0417")
	ev = l.take("index_card")
	check(ev.has("item_added:index_card") and ev.has("solved:catalogue"), "index card taken")
	l.open_cat_drawer(4) # closing the drawer keeps the card
	check(l.has_item("index_card"), "card kept")


func test_compressor_unique_solution() -> void:
	var solutions := 0
	for a in 5:
		for b in 5:
			for c in 5:
				if a + 2 * b == ArchiveLogic.PRESSURE_TARGET and 2 * a + c == ArchiveLogic.FLOW_TARGET:
					solutions += 1
	eq(solutions, 1, "exactly one valve setting")
	var l := _new()
	l.turn_valve(0)
	l.turn_valve(1)
	l.turn_valve(1)
	l.turn_valve(2)
	check(not l.state["pressure_ok"], "not yet")
	var ev := l.turn_valve(2)
	check(l.state["pressure_ok"] and ev.has("solved:compressor"), "1-2-2 gives pressure")
	ev = l.turn_valve(0)
	check(ev.has("valves_locked") and l.state["pressure_ok"], "valves lock once the pressure is right")
	l = _new()
	for _i in 5:
		l.turn_valve(0)
	eq(int(l.state["valves"][0]), 0, "valve wheels cycle 0..4")


func test_punch_and_dispatch() -> void:
	var l := _new()
	check(l.can_take("tray_card"), "blank card available")
	l.take("tray_card")
	check(not l.can_take("tray_card"), "one card at a time")
	var ev := l.toggle_punch_key(0)
	check(ev.has("punch_empty"), "punch needs a card")
	l.use_item_on("blank_card", "punch")
	l.toggle_punch_key(0) # wrong pattern
	l.pull_punch_lever()
	check(l.has_item("request_card") and not l.state["request_ok"], "punched, but wrong")
	l.use_item_on("request_card", "send_port")
	ev = l.send_canister()
	check(ev.has("tube_no_pressure"), "no pressure yet")
	for v in [[0, 1], [1, 2], [2, 2]]:
		for _k in v[1]:
			l.turn_valve(v[0])
	l.set_dest(1)
	ev = l.send_canister()
	check(ev.has("tube_returned_notfound") and not l.has_item("request_card"), "wrong card is kept by the stacks")
	check(l.can_take("tray_card"), "a new blank is available")
	l.take("tray_card")
	l.use_item_on("blank_card", "punch")
	for i in 8:
		if ArchiveLogic.PUNCH_CODE[i] == 1:
			l.toggle_punch_key(i)
	ev = l.pull_punch_lever()
	check(ev.has("solved:punch") and l.state["request_ok"], "correct pattern")
	l.use_item_on("request_card", "send_port")
	l.set_dest(5)
	ev = l.send_canister()
	check(ev.has("tube_returned_nodest") and l.has_item("request_card"), "sealed destination returns the card")
	l.use_item_on("request_card", "send_port")
	l.set_dest(ArchiveLogic.DEST_STACKS)
	ev = l.send_canister()
	check(ev.has("tube_returned_file") and l.state["file_delivered"], "file arrives")
	l.take("canister_file")
	l.take("canister_key")
	check(l.has_item("personnel_file") and l.has_item("locker_key"), "file and key")
	check(not l.can_take("tray_card"), "no more blanks needed")


func test_card_can_be_put_back() -> void:
	var l := _new()
	l.take("tray_card")
	l.use_item_on("blank_card", "punch")
	l.pull_punch_lever()
	check(not l.can_take("tray_card"), "holding a punched card")
	l.use_item_on("request_card", "card_tray")
	check(l.can_take("tray_card"), "after putting it back a fresh blank is available")


func test_locker_hunt_and_tapes() -> void:
	var l := _reach(_new(), "file")
	check(l.try_locker(3).has("locker_locked:3"), "other lockers stay shut")
	l.use_item_on("locker_key", "locker_9")
	l.take("locker_receiver")
	check(l.has_item("pocket_receiver"), "receiver")
	eq(l.receiver_strength("grille"), 5, "strong at the grille")
	eq(l.receiver_strength("vault"), 0, "nothing at the vault")
	l.open_hiding_place("grille")
	l.take("grille_reel")
	eq(l.receiver_strength("grille"), 0, "found reels stop transmitting")
	l.open_hiding_place("ledger")
	l.take("ledger_reel")
	var ev := l.open_hiding_place("hatch")
	check(ev.has("solved:hunt"), "all hiding places open")
	l.take("hatch_reel")
	l.use_item_on("tape_1996", "deck")
	ev = l.play_tape()
	check(ev.has("tape_garbled:tape_1996"), "wrong speed garbles")
	l.set_speed(ArchiveLogic.SPEED_RIGHT)
	ev = l.play_tape()
	check(ev.has("tape_clear:tape_1996") and ev.has("clicks:2"), "1996: two clicks")
	l.use_item_on("tape_1997", "deck")
	check(l.has_item("tape_1996"), "loading another reel swaps the first back")
	check(l.play_tape().has("clicks:8"), "1997: eight clicks")
	l.use_item_on("tape_1998", "deck")
	ev = l.play_tape()
	check(ev.has("clicks:5") and ev.has("solved:tape"), "1998: five clicks, all heard")
	l.eject_tape()
	check(l.has_item("tape_1998"), "eject returns the reel")


func test_booth_dial() -> void:
	var l := _new()
	for d in [2, 5, 8]:
		l.dial_digit(d)
	check(not l.state["booth_open"] and l.state["dial_input"] == "", "wrong code resets")
	for d in [2, 8, 5]:
		l.dial_digit(d)
	check(l.state["booth_open"], "285 opens the booth")


func test_splicing() -> void:
	var l := _new()
	check(l.splice_put(0, 0).has("nothing_happens"), "booth closed")
	l.state["booth_open"] = true
	l.splice_put(0, 0)
	l.splice_put(1, 1)
	l.splice_put(0, 1) # moving a placed frame swaps
	eq(int(l.state["splice"][0]), 1, "swap: slot 0 takes frame 1")
	eq(int(l.state["splice"][1]), 0, "swap: slot 1 takes frame 0")
	l.splice_lift(0)
	eq(int(l.state["splice"][0]), -1, "lift back to the bench")
	for slot in 4:
		l.splice_put(ArchiveLogic.SPLICE_ORDER[slot], slot)
	check(l.state["reel_repaired"], "longest shadow to shortest")
	var shadows: Array[int] = []
	for f in ArchiveLogic.SPLICE_ORDER:
		shadows.append(ArchiveLogic.SPLICE_SHADOWS[f])
	eq(str(shadows), "[4, 3, 2, 1]", "order follows shadow length")
	l.take("splicer_reel")
	check(l.has_item("film_reel"), "repaired reel")


func test_projector_records_the_sign() -> void:
	var l := _reach(_new(), "booth")
	for slot in 4:
		l.splice_put(ArchiveLogic.SPLICE_ORDER[slot], slot)
	l.take("splicer_reel")
	l.use_item_on("film_reel", "projector")
	var ev := l.toggle_projector()
	check(ev.has("film_played") and ev.has("leyla_echo"), "the film plays; leave path: Leyla's echo")
	eq(int(l.state["frame"]), ArchiveLogic.SIGN_FRAME, "holds the last frame")
	l.take("case_crystal_1")
	l.use_item_on("crystal_blank_1", "screen_socket")
	check(not l.state["sign_recorded"], "blurred: nothing recorded")
	l.step_frame(-1)
	for _i in 4:
		l.turn_focus(1)
	check(l.is_sharp(), "focus 5")
	check(not l.state["sign_recorded"], "wrong frame: nothing recorded")
	ev = l.step_frame(1)
	check(ev.has("recorded:sign") and l.state["socket"] == "crystal_sign", "sharp sign alone is recorded")
	l.take_from_socket()
	check(l.has_item("crystal_sign"), "sign crystal")
	ev = l.use_item_on("crystal_lens", "screen_socket")
	check(ev.has("nothing_happens") or ev.has("lens_refused"), "no lens on the leave path / lens refused")


func test_mark_from_slide_and_overlay() -> void:
	var l := _reach(_new(), "sign")
	check(not l.can_take("slide_mark"), "slide drawer closed")
	l.open_slide_drawer(1)
	check(not l.can_take("slide_mark"), "wrong drawer")
	l.open_slide_drawer(ArchiveLogic.SLIDE_MARK_DRAWER)
	l.take("slide_mark")
	l.use_item_on("emblem_slide", "slide_projector")
	l.toggle_slide_lamp()
	eq(l.screen_image(), "mixed", "film lamp still on: images overlap")
	l.toggle_projector()
	eq(l.screen_image(), "mark_tilted", "slide starts on its side")
	l.take("case_crystal_2")
	l.use_item_on("crystal_blank_2", "screen_socket")
	check(not l.state["mark_recorded"], "tilted: not recorded")
	var ev := l.rotate_slide()
	check(ev.has("recorded:mark"), "upright mark recorded")
	l.take_from_socket()
	# ports
	l.use_item_on("crystal_sign", "port_left")
	l.use_item_on("crystal_mark", "port_right")
	for _i in 8:
		l.turn_collar("rot_left")
	check(not l.state["vault_unlocked"], "swapped crystals never align")
	l.take_from_port("left")
	l.take_from_port("right")
	l.use_item_on("crystal_mark", "port_left")
	l.use_item_on("crystal_sign", "port_right")
	l.turn_collar("rot_left", 2) # 2 -> 4: upright (the mark is symmetric)
	check(l.overlay_left_ok(), "left upright at 4")
	for _i in 5:
		l.turn_collar("rot_right") # 5 -> 2
	for _i in 2:
		l.turn_collar("zoom_right")
	check(not l.state["vault_unlocked"], "zoom 2 is too small")
	ev = l.turn_collar("zoom_right")
	check(ev.has("vault_unlocked") and ev.has("solved:lock"), "exact overlay unlocks")
	check(l.turn_collar("rot_left").has("nothing_happens"), "collars lock after unlocking")
	l.turn_wheel()
	l.turn_wheel()
	ev = l.turn_wheel()
	check(ev.has("vault_opened"), "three turns open the vault")
	ev = l.choose_ending("leyla_key")
	check(ev.has("chapter_complete") and l.has_item("leyla_key"), "choice completes the chapter")
	eq(str(l.profile_choices()["ch2_key"]), "leyla_key", "choice recorded for Chapter 3")


func test_take_path_uses_the_ch1_lens() -> void:
	var l := _reach(_new(true), "sign")
	check(not l.state["echo_guided"], "no echo on the take path")
	l.use_item_on("crystal_lens", "port_left")
	l.use_item_on("crystal_sign", "port_right")
	l.turn_collar("rot_left", -2)
	for _i in 5:
		l.turn_collar("rot_right")
	for _i in 3:
		l.turn_collar("zoom_right")
	check(l.state["vault_unlocked"], "the Ch1 lens replaces the slide recording")


func test_echoes_need_a_crystal() -> void:
	var l := _new(true)
	check(l.release_echo("catalogue").has("nothing_happens"), "invisible without a crystal selected")
	l.select_item("crystal_lens")
	check(l.release_echo("catalogue").has("echo_released:catalogue"), "visible with the lens")
	check(l.release_echo("booth").has("nothing_happens"), "the booth echo waits for the booth")
	l.release_echo("stacks")
	l.state["booth_open"] = true
	check(l.release_echo("booth").has("all_echoes"), "all three released")
	eq(l.collectibles()[0], 3, "collectible count")


func test_secret_reel_with_five_shards() -> void:
	var l := _reach(_new(true, 5), "booth")
	for slot in 4:
		l.splice_put(ArchiveLogic.SPLICE_ORDER[slot], slot)
	l.take("splicer_reel")
	l.toggle_projector() # lamp first, then the reel
	var ev := l.use_item_on("film_reel", "projector")
	check(ev.has("film_played") and ev.has("secret_reel") and not ev.has("leyla_echo"), "secret reel; take path has no echo: %s" % str(ev))


func test_full_solution_both_paths() -> void:
	for lens in [false, true]:
		var l := _new(lens, 5)
		check(ArchiveSolver.solve(l, "strand_key"), "solver finishes (lens=%s)" % lens)
		eq(l.solved_count(), ArchiveLogic.PUZZLE_IDS.size(), "all puzzles counted solved (lens=%s)" % lens)
		eq(l.hint_goal(), "done", "hints end at done")


## Play the solver until a milestone.
func _reach(l: ArchiveLogic, milestone: String) -> ArchiveLogic:
	var flag: String = {"file": "file_delivered", "booth": "booth_open", "sign": "sign_recorded"}[milestone]
	var guard := 0
	while not l.state[flag] and guard < 300:
		ArchiveSolver.step(l, "leyla_key")
		guard += 1
	if milestone == "file":
		l.take("canister_file")
		l.take("canister_key")
	if milestone == "sign":
		ArchiveSolver._fetch(l, "crystal_sign")
	return l


# ------------------------------------------------------------------ per-game variants (docs/VARIANTS.md)
func test_variants_are_solvable_and_saved() -> void:
	var seen_codes := {}
	for seed in range(1, 61):
		var l := ArchiveLogic.new()
		l.apply_seed(seed)
		check(l.valve_solution().size() == 3, "seed %d: the gauge marks have a valve solution" % seed)
		check(l.booth_code().length() == 3 and not l.booth_code().contains("0"), "seed %d: three clicks of 1–9" % seed)
		check(l.focus_sharp() != ArchiveLogic.FOCUS_START, "seed %d: the picture is not sharp at the start" % seed)
		var shadows: Array = l.state["v_shadows"].duplicate()
		shadows.sort()
		check(shadows == [1, 2, 3, 4], "seed %d: each frame has its own shadow length" % seed)
		seen_codes[l.booth_code()] = true
		# the same seed gives the same game, and a save keeps it
		var again := ArchiveLogic.new()
		again.apply_seed(seed)
		check(again.booth_code() == l.booth_code() and again.splice_order() == l.splice_order(), "seed %d is reproducible" % seed)
		var loaded := ArchiveLogic.new()
		loaded.from_dict(JSON.parse_string(JSON.stringify(l.to_dict())))
		check(loaded.booth_code() == l.booth_code() and loaded.focus_sharp() == l.focus_sharp()
			and loaded.valve_solution() == l.valve_solution(), "seed %d survives save and load" % seed)
		check(ArchiveSolver.solve(l, "leyla_key" if seed % 2 == 0 else "strand_key"), "seed %d: the solver finishes" % seed)
	check(seen_codes.size() > 30, "booth codes really vary between games (%d distinct in 60)" % seen_codes.size())


func test_valve_target_pool_unique() -> void:
	var pool := ArchiveLogic.valve_target_pool()
	check(pool.size() >= 6, "at least 6 gauge-mark pairs (got %d)" % pool.size())
	check(pool.has([ArchiveLogic.PRESSURE_TARGET, ArchiveLogic.FLOW_TARGET]), "the canonical marks are in the pool")


func test_vault_variant_reachable() -> void:
	for seed in range(1, 41):
		var l := ArchiveLogic.new()
		l.apply_seed(seed)
		check(l.vault_rot_target() != ArchiveLogic.ROT_RIGHT_START and l.vault_rot_target() != 0,
			"seed %d: the right image starts off its target" % seed)
		check(l.vault_zoom_target() >= 1 and l.vault_zoom_target() < ArchiveLogic.ZOOM_STEPS, "seed %d: zoom target in range" % seed)


func test_punch_variant_matches_card_art() -> void:
	for seed in range(1, 41):
		var l := ArchiveLogic.new()
		l.apply_seed(seed)
		var k := int(l.state["v_punch"])
		check(k >= 1 and k < ArchiveLogic.PUNCH_PATTERNS.size(), "seed %d: a non-canonical notch pattern" % seed)
		check(ResourceLoader.exists("res://assets/textures/decals/ch2/index_card_p%d.png" % k), "seed %d: its card art exists" % seed)
		for lang in ["ru", "uz"]:
			check(ResourceLoader.exists("res://assets/textures/decals/ch2/index_card_p%d_%s.png" % [k, lang]), "seed %d: %s card art exists" % [seed, lang])
