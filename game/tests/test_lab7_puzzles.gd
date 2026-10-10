extends TestBase
## Unit tests for each Chapter 1 puzzle (docs/PUZZLE_DESIGN.md).

var l: Lab7Logic


func before_each() -> void:
	l = Lab7Logic.new()


func _ready_until(goal: String) -> void:
	## Advance with the solver until the hint system reports `goal` as current.
	for _i in 400:
		if Lab7Hints.current_goal(l) == goal or l.is_complete():
			return
		Lab7Solver.step(l, "leave_lens")


func test_drawer_needs_exact_code() -> void:
	l.take("notebook")
	for i in 4:
		for _k in [1, 2, 3, 4, 5][i]:
			l.step_drawer_wheel(i, 1)
	check(not l.state["drawer_open"], "wrong code must not open")
	check(not l.can_take("drawer_lamp"), "lamp unreachable while closed")
	l.state["drawer"] = [0, 3, 1, 6]
	var ev := l.step_drawer_wheel(3, 1)
	has(ev, "drawer_opened")
	has(ev, "solved:drawer")
	eq(l.step_drawer_wheel(0, 1), ["drawer_static"] as Array[String], "wheels freeze when open")


func test_drawer_wheels_wrap_both_ways() -> void:
	l.step_drawer_wheel(0, -1)
	eq(int(l.state["drawer"][0]), 9)
	l.step_drawer_wheel(0, 1)
	eq(int(l.state["drawer"][0]), 0)


func test_gearbox_minimal_solution() -> void:
	eq(Lab7Solver.gear_solution(l.state["gears"]), [2, 1, 3] as Array[int], "documented minimum")
	for _k in 2: l.press_gear(0)
	l.press_gear(1)
	for _k in 2: l.press_gear(2)
	check(not l.state["box_open"], "not yet")
	var ev := l.press_gear(2)
	has(ev, "box_opened")


func test_gearbox_solvable_from_any_reachable_state() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 11
	for _trial in 200:
		var g := Lab7Logic.new()
		for _k in rng.randi_range(0, 40):
			g.press_gear(rng.randi_range(0, 2))
		if g.state["box_open"]:
			continue
		var p := Lab7Solver.gear_solution(g.state["gears"])
		for i in 3:
			for _k in p[i]:
				g.press_gear(i)
		check(g.state["box_open"], "gear state %s unsolvable" % str(g.state["gears"]))


func test_combine_lamp_any_order_and_rejects_nonsense() -> void:
	l.inventory = ["battery_cell", "uv_lamp_empty", "notebook"] as Array[String]
	has(l.combine("notebook", "battery_cell"), "combine_failed")
	eq(l.inventory.size(), 3, "failed combine keeps items")
	var ev := l.combine("battery_cell", "uv_lamp_empty")
	has(ev, "combined:uv_lamp")
	has(ev, "solved:lamp")
	check(l.has_item("uv_lamp") and not l.has_item("battery_cell"), "result replaces inputs")


func test_uv_requires_working_lamp() -> void:
	l.take("notebook")
	has(l.uv_reveal("notebook_page"), "nothing_happens")
	l.inventory.append("uv_lamp")
	has(l.uv_reveal("notebook_page"), "uv_revealed:notebook_page")
	has(l.use_item_on("uv_lamp", "desk_mark"), "uv_revealed:desk_mark")


func test_safe_code_and_wrong_code() -> void:
	for c in "1234":
		l.safe_press(c)
	has(l.safe_press("E"), "safe_denied")
	eq(l.state["safe_input"], "", "input cleared after denial")
	for c in "72945":
		l.safe_press(c)
	eq(l.state["safe_input"], "7294", "max 4 digits")
	has(l.safe_press("E"), "safe_opened")
	for spot in ["safe_key", "safe_lens", "safe_letter", "safe_valve"]:
		check(l.can_take(spot), spot + " reachable")


func test_safe_code_matches_glyph_chart() -> void:
	## sun-wave-spiral-delta decoded with the poster dot counts.
	var dots := {"sun": 7, "crescent": 3, "wave": 2, "spiral": 9, "delta": 4, "eye": 0, "cross": 5,
		"diamond": 1, "fork": 8, "hourglass": 6}
	var code := ""
	for gid in ["sun", "wave", "spiral", "delta"]:
		code += str(dots[gid])
	eq(code, Lab7Logic.SAFE_CODE)


func test_compartment_needs_rosette_and_key() -> void:
	l.inventory.append("brass_key")
	has(l.use_item_on("brass_key", "desk_keyhole"), "nothing_happens", "keyhole hidden")
	has(l.press_rosette(), "keyhole_revealed")
	var ev := l.use_item_on("brass_key", "desk_keyhole")
	has(ev, "compartment_opened")
	check(not l.has_item("brass_key"), "key used up only on success")


func test_panel_needs_handle() -> void:
	has(l.toggle_main(), "main_no_handle")


func test_panel_vent_trips_breaker() -> void:
	l.state["handle_installed"] = true
	l.toggle_switch(0) # LOCK + VENT
	var ev := l.toggle_main()
	has(ev, "breaker_tripped")
	check(not l.state["main_on"], "main falls back off")
	check(not l.state["power_on"], "no power")


func test_panel_both_solutions_work() -> void:
	for combo in [[0, 1, 2], [0, 4]]:
		var p := Lab7Logic.new()
		p.state["handle_installed"] = true
		for i in combo:
			p.toggle_switch(i)
		var ev := p.toggle_main()
		has(ev, "power_restored", "combo %s" % str(combo))


func test_panel_live_toggle_into_vent_trips_and_success_locks() -> void:
	l.state["handle_installed"] = true
	l.toggle_switch(1)
	l.toggle_main()
	check(l.state["main_on"], "main on with LIGHT only")
	has(l.toggle_switch(0), "breaker_tripped", "LOCK+VENT while live trips")
	l.toggle_switch(0)
	l.toggle_switch(0)
	l.toggle_switch(2)
	has(l.toggle_main(), "power_restored")
	has(l.toggle_switch(3), "switches_locked")
	has(l.toggle_main(), "main_locked")


func test_radio_states() -> void:
	eq(l.radio_status(), "dead")
	l.state["power_on"] = true
	l.inventory.append("radio_valve")
	l.use_item_on("radio_valve", "radio")
	eq(l.radio_status(), "static")
	l.set_dial(Lab7Logic.RADIO_TARGET + 6)
	eq(l.radio_status(), "near")
	var ev := l.set_dial(Lab7Logic.RADIO_TARGET + 2)
	has(ev, "radio_signal")
	check(l.radio_clarity() > 0.99, "clear at tolerance edge")
	lacks(l.set_dial(Lab7Logic.RADIO_TARGET), "radio_signal", "signal event only once")


func test_books_use_last_three_pulls() -> void:
	for n in [5, 2, 6, 9, 2, 6]:
		l.pull_book(n)
	check(not l.state["shelf_open"], "not yet")
	has(l.pull_book(3), "shelf_opened")


func test_shadow_alignment_and_recording() -> void:
	l.state["shelf_open"] = true
	l.state["power_on"] = true
	l.state["lens_at"] = "inventory"
	l.inventory.append("crystal_lens")
	l.state["shadow"] = [3, 3]
	var ev := l.turn_sculpture(0)
	lacks(ev, "cabinet_opened", "90° edge-on ring draws no emblem")
	l.state["shadow"] = [5, 0]
	ev = l.turn_sculpture(0) # ring 5 -> 0 (wraps: 6 x 30° = half turn, ring is symmetric)
	has(ev, "cabinet_opened", "ring facing lamp + rod upright")
	lacks(ev, "emblem_recorded", "no lens in socket yet")
	ev = l.use_item_on("crystal_lens", "emblem_socket")
	has(ev, "emblem_recorded", "inserting while aligned records")
	has(l.remove_lens(), "lens_removed")
	check(l.state["emblem_recorded"], "recording kept after removal")


func test_projector_requirements_and_scatter() -> void:
	l.state["lens_at"] = "inventory"
	l.inventory.append("crystal_lens")
	has(l.pull_projector_lever(), "projector_no_power")
	l.state["power_on"] = true
	has(l.pull_projector_lever(), "projector_no_lens")
	l.use_item_on("crystal_lens", "projector")
	has(l.pull_projector_lever(), "projector_scatter")
	for i in 3:
		while int(l.state["rings"][i]) != Lab7Logic.RING_TARGET[i]:
			l.turn_ring(i)
	has(l.pull_projector_lever(), "beam_on")
	has(l.turn_ring(0), "rings_locked")
	has(l.remove_lens(), "beam_off", "removing lens turns beam off")
	check(not l.state["beam_on"], "beam off")


func test_ring_target_is_heaviest_first() -> void:
	var rho := {"crimson": 1.84, "cobalt": 1.26, "green": 0.79}
	var order := rho.keys()
	order.sort_custom(func(a: String, b: String) -> bool: return rho[a] > rho[b])
	var want: Array[int] = []
	for c in order:
		want.append(Lab7Logic.RING_COLORS.find(c))
	eq(want, Lab7Logic.RING_TARGET)


func test_beam_geometry() -> void:
	var tr := l.trace_beam()
	eq(tr["end"], "mirror_back", "mirror A starts facing away")
	l.state["mirrors"][0] = 5
	tr = l.trace_beam()
	eq(tr["end"], "wall", "north wall when B not mounted")
	var last: Vector2 = (tr["points"] as PackedVector2Array)[-1]
	check(is_equal_approx(last.y, -2.5) and is_equal_approx(last.x, 1.6), "hits north wall above A: %s" % str(last))
	l.state["mirror_b_mounted"] = true
	l.state["mirrors"][1] = 1
	tr = l.trace_beam()
	eq(tr["end"], "lock")
	eq(tr["bounces"], 2)


func test_lock_needs_recorded_emblem() -> void:
	l.state.merge({"power_on": true, "lens_at": "projector", "rings": [0, 3, 2], "mirror_b_mounted": true,
		"mirrors": [5, 1]}, true)
	var ev := l.pull_projector_lever()
	has(ev, "lock_waits_for_sign")
	check(not l.state["door_open"], "plain light does not open")
	l.remove_lens()
	l.state["emblem_recorded"] = true
	l.use_item_on("crystal_lens", "projector")
	ev = l.pull_projector_lever()
	has(ev, "door_unlocked")


func test_full_playthrough_both_endings() -> void:
	for choice in ["take_lens", "leave_lens"]:
		var p := Lab7Logic.new()
		check(Lab7Solver.solve(p, choice), "solver completes (%s)" % choice)
		eq(p.state["choice"], choice)
		eq(p.solved_count(), Lab7Logic.PUZZLE_IDS.size(), "all 12 puzzles solved")
		eq(p.has_item("crystal_lens"), choice == "take_lens", "lens ownership follows choice")


func test_shards_need_uv_and_darkroom_access() -> void:
	has(l.collect_shard("under_desk"), "nothing_happens")
	l.inventory.append("uv_lamp")
	has(l.collect_shard("under_desk"), "shard_collected:under_desk")
	has(l.collect_shard("under_desk"), "nothing_happens", "no double collect")
	has(l.collect_shard("darkroom"), "nothing_happens", "darkroom locked")
	l.state["shelf_open"] = true
	for id in Lab7Logic.SHARDS:
		l.collect_shard(id)
	eq((l.state["shards"] as Array).size(), 5)


# ------------------------------------------------------------------ per-game variants (docs/VARIANTS.md)
func test_variants_are_solvable_and_saved() -> void:
	var codes := {}
	for seed in range(1, 61):
		var l := Lab7Logic.new()
		l.apply_seed(seed)
		var g: Array = l.state["gears"]
		check(not (int(g[0]) == 0 and int(g[1]) == 0 and int(g[2]) == 0), "seed %d: the gear box is not open at the start" % seed)
		var glyphs: Array = l.safe_glyphs()
		check(glyphs.size() == 4, "seed %d: four cipher glyphs" % seed)
		var uniq := {}
		for x: Variant in glyphs:
			uniq[str(x)] = true
			check(ResourceLoader.exists("res://assets/ui/glyphs/%s.png" % str(x)), "seed %d: glyph art %s exists" % [seed, str(x)])
		check(uniq.size() == 4, "seed %d: the glyphs differ" % seed)
		check(l.beacon().size() == 3, "seed %d: three beacon numbers" % seed)
		codes[l.safe_code()] = true
		var loaded := Lab7Logic.new()
		loaded.from_dict(JSON.parse_string(JSON.stringify(l.to_dict())))
		check(loaded.safe_code() == l.safe_code() and loaded.beacon() == l.beacon() and loaded.state["gears"] == l.state["gears"],
			"seed %d survives save and load" % seed)
		check(Lab7Solver.solve(l, "leave_lens" if seed % 2 == 0 else "take_lens"), "seed %d: the solver finishes" % seed)
	check(codes.size() > 40, "safe codes really vary (%d distinct in 60)" % codes.size())


# ------------------------------------------------------------------ Panel 7: the wiring varies (docs/VARIANTS.md)
const ROMAN_JOIN := ["I", "II", "III", "IV", "V"]


func _answer_text(sw: Array) -> String:
	return ", ".join(sw.map(func(v: Variant) -> String: return ROMAN_JOIN[int(v)]))


## A fresh game wired as pool entry n, the switches raised as in `combo`, then the main lever.
func _raise(n: int, combo: Array) -> Array[String]:
	var p := Lab7Logic.new()
	p.state["v_panel"] = Lab7Logic.flat_panel(Lab7Logic.PANEL_POOL[n])
	p.state["handle_installed"] = true
	for i: Variant in combo:
		p.toggle_switch(int(i))
	return p.toggle_main()


func test_panel_pool_entries_are_valid() -> void:
	var pool := Lab7Logic.PANEL_POOL
	check(pool.size() >= 6 and pool.size() <= 8, "about 6 to 8 wirings (%d)" % pool.size())
	eq(Lab7Logic.flat_panel(pool[0]), Lab7Logic.new().state["v_panel"], "entry 0 is the canonical wiring a fresh game has")
	var hints := {}
	var seen := {}
	for n in pool.size():
		var w := Lab7Logic.flat_panel(pool[n])
		check(Lab7Logic.panel_valid(w), "entry %d passes panel_valid" % n)
		check(not seen.has(str(w)), "entry %d is not a duplicate" % n)
		seen[str(w)] = true
		eq(Lab7Logic.panel_rank(w), 4, "entry %d has rank 4" % n)
		var sols := Lab7Logic.panel_solutions(w)
		eq(sols.size(), 2, "entry %d has exactly two answers" % n)
		check((sols[0] as Array).size() >= 2 and (sols[0] as Array).size() <= 4, "entry %d: shortest answer of 2-4 switches" % n)
		check(not hints.has(str(sols[0])), "entry %d: its hint answer %s is new in the pool" % [n, str(sols[0])])
		hints[str(sols[0])] = true
		# both answers really restore the power, and the VENT lamp stays dark
		for sol: Array in sols:
			has(_raise(n, sol), "power_restored", "entry %d answer %s" % [n, str(sol)])
		# every other combination fails: no power (wrong lamps lit, or VENT trips the breaker)
		for mask in 32:
			var combo: Array = []
			for i in 5:
				if (mask >> i) & 1 == 1:
					combo.append(i)
			if sols.has(combo):
				continue
			var ev := _raise(n, combo)
			lacks(ev, "power_restored", "entry %d wrong combination %s" % [n, str(combo)])
		# the naive tries do not work
		var all_up: Array = [0, 1, 2, 3, 4]
		lacks(_raise(n, all_up), "power_restored", "entry %d raising everything" % n)
		if n > 0:
			check(not sols.has([0, 1, 2]), "entry %d: raising I, II and III (the old answer) is no answer" % n)
	check(Lab7Logic.panel_solutions(Lab7Logic.flat_panel(pool[0])).has([0, 1, 2]), "the canonical wiring keeps I, II, III")
	check(Lab7Logic.panel_solutions(Lab7Logic.flat_panel(pool[0])).has([0, 4]), "the canonical wiring keeps I, V")
	# the validator rejects a wiring that breaks a rule
	check(not Lab7Logic.panel_valid(Lab7Logic.flat_panel([[1, 0, 0, 1], [1, 0, 0, 1], [0, 0, 1, 1], [1, 1, 0, 0], [0, 1, 1, 1]])), "two alike switches")
	check(not Lab7Logic.panel_valid(Lab7Logic.flat_panel([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [1, 1, 1, 0]])), "rank 4 but lamps with one switch")
	check(not Lab7Logic.panel_valid(Lab7Logic.flat_panel([[1, 1, 0, 0], [0, 1, 1, 0], [1, 0, 1, 0], [0, 0, 0, 1], [1, 1, 1, 1]])), "rank 3")
	check(not Lab7Logic.panel_valid([1, 0, 0]), "wrong size")


func test_panel_seed_picks_deterministically() -> void:
	var l := Lab7Logic.new()
	l.apply_seed(0)
	eq(l.panel_variant(), 0, "seed 0 keeps the canonical wiring")
	var reached := {}
	for seed in range(1, 401):
		var a := Lab7Logic.new()
		a.apply_seed(seed)
		var b := Lab7Logic.new()
		b.apply_seed(seed)
		eq(a.state["v_panel"], b.state["v_panel"], "seed %d picks the same wiring twice" % seed)
		var n := a.panel_variant()
		check(n >= 0, "seed %d draws a pool wiring" % seed)
		reached[n] = true
	eq(reached.size(), Lab7Logic.PANEL_POOL.size(), "400 seeds reach every wiring")
	# the other Chapter 1 answers of a seed did not move when Panel 7 joined the draw
	var s4242 := Lab7Logic.new()
	s4242.apply_seed(4242)
	eq(s4242.safe_code(), "1204", "seed 4242 safe code")
	eq(s4242.beacon(), [4, 2, 8], "seed 4242 beacon")


func test_panel_wiring_is_saved_and_old_saves_stay_canonical() -> void:
	for seed in range(1, 41):
		var a := Lab7Logic.new()
		a.apply_seed(seed)
		a.toggle_switch(a.panel_solution()[0])
		var b := Lab7Logic.new()
		check(b.from_dict(JSON.parse_string(JSON.stringify(a.to_dict()))), "seed %d loads" % seed)
		eq(b.state["v_panel"], a.state["v_panel"], "seed %d keeps its wiring" % seed)
		eq(b.panel_variant(), a.panel_variant(), "seed %d keeps its decal" % seed)
		eq(b.panel_solution(), a.panel_solution(), "seed %d keeps its answer" % seed)
		eq(b.lamps(), a.lamps(), "seed %d lamps" % seed)
	# a save from before the wiring varied has no wiring: it is the canonical one
	var old := Lab7Logic.new()
	var d := old.to_dict()
	(d["state"] as Dictionary).erase("v_panel")
	var loaded := Lab7Logic.new()
	loaded.from_dict(JSON.parse_string(JSON.stringify(d)))
	eq(loaded.panel_variant(), 0, "an old save is the canonical wiring")


func test_panel_hint_names_this_games_answer() -> void:
	for n in Lab7Logic.PANEL_POOL.size():
		var p := Lab7Logic.new()
		p.state["v_panel"] = Lab7Logic.flat_panel(Lab7Logic.PANEL_POOL[n])
		var sols := Lab7Logic.panel_solutions(p.state["v_panel"])
		eq(p.panel_solution(), sols[0], "entry %d: the hint answer is the shortest" % n)
		var args := p.hint_args("circuits", 3)
		eq(args, [_answer_text(sols[0])], "entry %d: level 3 speaks the player's own answer" % n)
		eq(p.hint_args("circuits", 1), [], "level 1 stays as it is")
		eq(p.hint_args("circuits", 2), [], "level 2 stays as it is")
		# the hint's answer, followed to the letter, lights the lamps
		has(_raise(n, p.panel_solution()), "power_restored", "entry %d: the hint's answer works" % n)
	# the text: one placeholder in each language, and it formats
	var csv := FileAccess.open("res://localization/strings.csv", FileAccess.READ)
	check(csv != null, "strings.csv exists")
	if csv == null:
		return
	var row: PackedStringArray = []
	while not csv.eof_reached():
		var r := csv.get_csv_line()
		if r.size() >= 4 and r[0] == "hint.circuits.3":
			row = r
	check(row.size() >= 4, "hint.circuits.3 exists")
	for col in [1, 2, 3]:
		if row.size() >= 4:
			var text := str(row[col])
			eq(text.count("%s"), 1, "hint.circuits.3 col %d has one %%s" % col)
			check(not (text % ["I, V"]).contains("%"), "hint.circuits.3 col %d formats" % col)
			check((text % ["I, V"]).contains("I, V"), "hint.circuits.3 col %d shows the answer" % col)


func test_panel_solver_reads_the_answer_from_the_state() -> void:
	for n in Lab7Logic.PANEL_POOL.size():
		var p := Lab7Logic.new()
		p.state["v_panel"] = Lab7Logic.flat_panel(Lab7Logic.PANEL_POOL[n])
		check(Lab7Solver.solve(p, "leave_lens"), "entry %d: the solver finishes Chapter 1" % n)
