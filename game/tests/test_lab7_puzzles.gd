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
