extends TestBase
## Chapter 2 expansion logic (docs/CHAPTER2_EXPANSION.md): gates G1/G2, N1-N10 actions, save migration, floor plan,
## open threads, hints, Trial mode, reaction moments. Old-save fixtures were written by the 1.0 code (commit 486e373).

const FIX := "res://tests/fixtures/"
const SEEDS: Array[int] = [0, 1, 2, 5, 777, 6143, 8216]


func _new(game_seed: int = 0, stage: int = 2, lens := false) -> ArchiveLogic:
	return ArchiveLogic.new_expanded(game_seed, stage, {"ch1_lens": "take_lens" if lens else "leave_lens", "ch1_shards": 5})


func _load_fixture(name: String) -> ArchiveLogic:
	var f := FileAccess.open(FIX + name + ".json", FileAccess.READ)
	check(f != null, "fixture " + name)
	var d: Dictionary = JSON.parse_string(f.get_as_text())
	var l := ArchiveLogic.new()
	check(l.from_dict(d["logic"]), "fixture %s loads" % name)
	return l


## Run the solver until `done` holds (or it is complete).
func _until(l: ArchiveLogic, done: Callable, choice := "leyla_key", max_steps := 900) -> bool:
	for _i in max_steps:
		if done.call() or l.is_complete():
			return true
		ArchiveSolver.step(l, choice)
	return done.call()


## A value as JSON sees it (ints and floats alike), for comparing a loaded save with the file it came from.
func _norm(v: Variant) -> String:
	return JSON.stringify(JSON.parse_string(JSON.stringify(v)))


# ------------------------------------------------------------------ stage constant and legacy default
func test_default_game_follows_the_stage_constant() -> void:
	var l := ArchiveLogic.new()
	eq(l.exp_active(), ArchiveLogic.EXPANSION_STAGE >= 1, "a new game is built with EXPANSION_STAGE")
	eq(ArchiveLogic.new_legacy().exp_stage(), 0, "new_legacy is the 1.0 chapter")
	check(not ArchiveLogic.new_legacy().has_item("floor_plan"), "no floor plan in the old chapter")
	var e := _new()
	check(e.exp_active() and e.exp_stage() == 2, "expansion game is stage 2")
	check(e.has_item("floor_plan"), "the building plan is in the bag from the start")
	eq(_new(0, 1).exp_stage(), 1, "stage 1 game")
	check(_new(0, 1).state["lamp_ok"], "Stage A alone ships with G2 pre-satisfied")
	check(not e.state["lamp_ok"], "Stage 2 game: the lamp is dead")


# ------------------------------------------------------------------ seed streams
func test_seed_streams_do_not_move_existing_variants() -> void:
	var f := FileAccess.open(FIX + "ch2_legacy_variants.json", FileAccess.READ)
	var old: Dictionary = JSON.parse_string(f.get_as_text())
	eq(old.size(), 61, "variants fixture has seeds 0-60")
	for sk: String in old:
		var seed := int(sk)
		for kind in ["legacy", "expanded"]:
			var l := ArchiveLogic.new_legacy() if kind == "legacy" else ArchiveLogic.new_expanded(0, 2)
			l.apply_seed(seed)
			for key: String in old[sk]:
				eq(_norm(l.state[key]), _norm(old[sk][key]), "seed %d %s: %s unchanged" % [seed, kind, key])


func test_variants_are_deterministic_and_vary() -> void:
	var a := _new(777)
	var b := _new(777)
	for key in ["v_panel", "v_pipes", "v_glyph", "v_sheets", "v_sheet_target", "v_bay", "v_symbols", "v_chest_start", "v_load",
			"v_board", "v_slips", "v_strips", "v_strip", "v_zoom", "v_pfocus", "v_digits", "aisle_pos", "sheets"]:
		eq(JSON.stringify(a.state[key]), JSON.stringify(b.state[key]), "%s repeats for one seed" % key)
	var panels := {}
	var graphs := {}
	var loads := {}
	var bays := {}
	for s in range(1, 80):
		var l := _new(s)
		panels[l.state["v_panel"]] = true
		graphs[l.state["v_pipes"]] = true
		loads[l.state["v_load"]] = true
		bays[l.state["v_bay"]] = true
		check(ArchiveExpData.LOADS.has(int(l.state["v_load"])), "seed %d: valid load" % s)
		eq((l.state["v_symbols"] as Array).size(), 3, "three distinct frost signs")
		var sy := {}
		for v: int in l.state["v_symbols"]:
			sy[v] = true
		eq(sy.size(), 3, "seed %d: signs differ" % s)
		var st := {}
		for v: int in l.state["v_strips"]:
			st[v] = true
		eq(st.size(), 4, "seed %d: four different strip symbols" % s)
		check(int(l.state["v_zoom"]) >= 1 and int(l.state["v_zoom"]) <= 3, "seed %d: zoom target" % s)
		check(int(l.state["v_pfocus"]) >= 2 and int(l.state["v_pfocus"]) <= 6, "seed %d: focus target" % s)
		var dg := {}
		for v: int in l.state["v_digits"]:
			dg[v] = true
		check(dg.size() >= 2, "seed %d: cabinet digits are not all the same" % s)
	eq(panels.size(), 3, "all three panels occur")
	eq(graphs.size(), 6, "all six pipe graphs occur")
	check(loads.size() >= 6, "loads vary (%d)" % loads.size())
	eq(bays.size(), 4, "all four bays occur")


# ------------------------------------------------------------------ old saves keep the old flow
func test_old_save_fixtures_load_as_legacy_and_stay_solvable() -> void:
	for name in ["ch2_legacy_start", "ch2_legacy_mid_p4", "ch2_legacy_mid_p8", "ch2_legacy_mid_p11", "ch2_legacy_finished"]:
		var f := FileAccess.open(FIX + name + ".json", FileAccess.READ)
		var d: Dictionary = JSON.parse_string(f.get_as_text())
		check(not (d["logic"]["state"] as Dictionary).has("exp_ver"), name + ": really an old save (no exp_ver)")
		var l := _load_fixture(name)
		check(not l.exp_active(), name + ": legacy flow")
		eq(l.exp_stage(), 0, name + ": stage 0")
		check(l.state["lamp_ok"] and l.state["crystals_available"] and l.state["crystal_home"] == "case", name + ": no new gate")
		check(not l.has_item("floor_plan"), name + ": no floor plan item")
		eq(l.puzzle_ids().size(), 12, name + ": still 12 puzzles")
		# Continue state equals the saved one: every saved value survives
		for key: String in d["logic"]["state"]:
			eq(_norm(l.state[key]), _norm(d["logic"]["state"][key]), "%s: %s kept" % [name, key])
		eq(l.inventory, d["logic"]["inventory"] as Array, name + ": inventory kept")
		# and it still finishes, for either key, taking the crystals from the booth case
		if not l.is_complete():
			check(ArchiveSolver.solve(l, "strand_key"), name + ": solvable to the end")
		check(l.is_complete(), name + ": complete")
		# no new gate was ever met on the way
		check(not l.state["pump_open"] and not l.state["cold_open"], name + ": the new floors stay sealed")
		check(l.room_ids().size() > 0 and not l.room_open("pump"), name + ": pump room sealed in an old save")


func test_old_save_never_meets_a_new_gate() -> void:
	var l := _load_fixture("ch2_legacy_mid_p8") # booth open, reel not spliced yet
	check(l.state["booth_open"], "booth open in this fixture")
	check(l.can_take("case_crystal_1"), "the crystals are in the booth case as before")
	check(l.toggle_projector().has("projector_on"), "the projector lamp works")
	eq(l.profile_choices().keys().size(), 2, "profile choices are exactly the 1.0 ones for an old save")
	# unknown / missing expansion keys never raise a gate on a mid-game save loaded in an expansion-ready build
	var d: Dictionary = JSON.parse_string(FileAccess.open(FIX + "ch2_legacy_mid_p11.json", FileAccess.READ).get_as_text())
	var m := ArchiveLogic.new()
	m.from_dict(d["logic"])
	check(m.can_take("case_crystal_2") or m.state["taken"].get("case_crystal_2", false), "crystal 2 reachable or already taken")


func test_new_save_round_trips_and_keeps_its_stage() -> void:
	var l := _new(777)
	_until(l, func() -> bool: return l.state["thawed"])
	var json := JSON.stringify(l.to_dict())
	var r := ArchiveLogic.new()
	check(r.from_dict(JSON.parse_string(json)), "loads")
	check(r.exp_active() and r.exp_stage() == 2, "stays an expansion game")
	eq(JSON.stringify(r.to_dict()), json, "identical after reload")
	check(r.has_item("floor_plan"), "plan kept")
	check(not r.state["lamp_ok"], "gate kept (not reset to legacy)")
	eq(typeof(r.state["v_slips"][0]), TYPE_INT, "slips are ints after JSON")
	eq(typeof(r.state["sheets"][0]), TYPE_INT, "sheet orientations are ints after JSON")
	# a game saved at stage 1 is not pulled up to stage 2
	var a := _new(5, 1)
	var b := ArchiveLogic.new()
	b.from_dict(JSON.parse_string(JSON.stringify(a.to_dict())))
	eq(b.exp_stage(), 1, "stage 1 kept")


# ------------------------------------------------------------------ gates
func test_new_game_needs_the_new_gates() -> void:
	var l := _new(5)
	# G1: the crystals are not in the booth case
	l.state["booth_open"] = true
	check(not l.can_take("case_crystal_1"), "G1: no crystal in the booth case of a new game")
	check(l.take("case_crystal_1").has("nothing_happens"), "G1: taking is refused")
	# G2: the lamp is dead
	var ev := l.toggle_projector()
	has(ev, "lamp_dead", "G2")
	check(not l.state["projector_on"], "G2: the film cannot run")
	check(l.state["lamp_seen"], "the dead lamp is remembered (a thread)")
	l.state["lamp_ok"] = true
	has(l.toggle_projector(), "projector_on", "with a lamp the projector works")
	# gates cannot be skipped through the other puzzles
	var m := _new(5)
	check(m.n2_toggle_valve(0).has("nothing_happens"), "pipes need the pump room")
	check(m.n3_turn_sheet(0).has("nothing_happens"), "the light table needs the cell")
	check(m.n4_crank(0, 1).has("nothing_happens"), "carriages need the cold store")
	check(m.enter_room("cold").has("room_locked:cold"), "cold store is locked")
	check(m.enter_room("gallery").has("room_locked:gallery"), "gallery is locked")
	check(m.enter_room("office").has("room_locked:office"), "office is locked")
	check(m.enter_room("hall").has("room:hall"), "hall always opens")


func test_both_stages_solve_for_many_seeds_and_both_lens_paths() -> void:
	for stage in [1, 2]:
		for s in SEEDS:
			for lens in [false, true]:
				var l := _new(s, stage, lens)
				var ok := ArchiveSolver.solve(l, "strand_key" if s % 2 == 0 else "leyla_key", 900)
				check(ok, "stage %d seed %d lens %s: solved; goal=%s" % [stage, s, lens, l.hint_goal()])
				if not ok:
					continue
				var st := l.state
				check(st["pump_open"] and st["thawed"] and st["cold_open"] and st["aisle"] and st["chest_open"] and st["frost_seen"],
					"stage %d seed %d: the lower floor was played" % [stage, s])
				if stage == 2:
					check(st["lift_ok"] and st["board_ok"] and st["print_ok"] and st["cab_open"] and st["lamp_ok"] and st["pass_key"],
						"stage 2 seed %d: the upper floor was played" % s)
					check(l.room_seen("office") and l.room_seen("plate") and l.room_seen("gallery"), "seed %d: all rooms visited" % s)
				else:
					check(not l.room_ids().has("gallery"), "stage 1 has no gallery")
				eq(l.solved_count(), l.puzzle_ids().size(), "stage %d seed %d: progress reads full" % [stage, s])


func test_puzzle_count_grows_with_the_stage() -> void:
	eq(ArchiveLogic.new_legacy().puzzle_ids().size(), 12, "legacy 12")
	eq(_new(0, 1).puzzle_ids().size(), 18, "Stage A: 12 + 6")
	eq(_new(0, 2).puzzle_ids().size(), 22, "Stage B: 12 + 10")
	eq(_new(0, 2).solved_count(), 0, "nothing solved at the start")


# ------------------------------------------------------------------ N1 .. N6
func _to_pump(l: ArchiveLogic) -> void:
	_until(l, func() -> bool: return l.state["pump_open"])


func test_n1_warm_wall() -> void:
	var l := _new(5)
	eq(l.receiver_strength("east_south"), 0, "no signal before the last reel (reels not found yet)")
	check(l.n1_open_panel(0).has("nothing_happens"), "panels need the coda first")
	_until(l, func() -> bool: return l.coda_heard() and l.state["taken"].get("hatch_reel", false))
	check(l.coda_heard(), "the coda sounds after the third reel")
	eq(l.receiver_strength("east_south"), 4, "the needle rises along the east wall")
	var right := int(l.state["v_panel"])
	var best := -1
	var best_p := -1
	for p in 3:
		var strength := l.receiver_strength("east_panel_" + ArchiveExpData.PANEL_LETTERS[p].to_lower())
		if strength > best:
			best = strength
			best_p = p
	eq(best_p, right, "the strongest panel is the door's")
	eq(best, 5, "full strength on it")
	var wrong := (right + 1) % 3
	has(l.n1_open_panel(wrong), "panel_cold:%d" % wrong, "a wrong panel is cold")
	check(not l.state["panel_found"], "nothing found")
	has(l.n1_open_panel(right), "panel_opened:%d" % right, "the right panel opens")
	# the dial: wrong number resets after 4 digits; 0417 opens
	for d in [1, 1, 1]:
		l.n1_dial(d)
	has(l.n1_dial(1), "n1_dial_wrong", "wrong 4 digits")
	eq(str(l.state["n1_dial"]), "", "dial reset")
	var ev: Array[String] = []
	for ch in "0417":
		ev = l.n1_dial(int(ch))
	has(ev, "pump_opened", "0417 opens the door")
	has(ev, "solved:warm", "N1 solved")
	eq(l.receiver_strength("east_south"), 0, "the cell door is no longer a target")
	check(l.room_open("pump") and l.room_open("cell"), "pump room and cell open")


func test_n2_pipes_mallet_and_hazard() -> void:
	for s in [1, 2, 3, 4, 5, 6, 7, 8]:
		var l := _new(s)
		_to_pump(l)
		check(l.n2_tap_pipe(0).has("need_mallet"), "tapping needs the mallet")
		l.take("pump_mallet")
		check(l.has_item("mallet"), "mallet in the bag")
		var g: Array = l.pipe_graph()
		# every valve open: the pressure leaks to the vent, and nothing thaws
		l.state["pipes"] = [1, 1, 1, 1, 1, 1]
		check(l.pipes_reach().has(ArchiveExpData.NODE_H), "seed %d: with every valve open the vent is reached" % s)
		check(not l.state["thawed"], "seed %d: with the vent open nothing thaws" % s)
		# probe every segment (free, no state change)
		var before := JSON.stringify(l.state)
		var cracked := 0
		for seg in 6:
			var ev := l.n2_tap_pipe(seg)
			check(ev.size() == 1 and ev[0].begins_with("tap:%d:" % seg), "tap event")
			if ev[0].ends_with("cracked"):
				cracked += 1
		eq(JSON.stringify(l.state), before, "probing changes nothing")
		check(cracked >= 1, "seed %d: the leak can be heard" % s)
		# the leak warns when a valve opens toward the vent; then set the real solution (closing all first)
		var warned := false
		for i in 6:
			l.state["pipes"] = [1, 1, 1, 1, 1, 1]
			l.state["pipes"][i] = 0
			if l.n2_toggle_valve(i).has("pipes_hazard"):
				warned = true
		check(warned, "seed %d: opening the last valve toward the vent warns" % s)
		l.state["pipes"] = [0, 0, 0, 0, 0, 0]
		var ev2: Array[String] = []
		for v in l.pipe_solution():
			ev2 = l.n2_toggle_valve(v)
		has(ev2, "thawed", "seed %d: the coil warms" % s)
		check(l.state["thawed"], "flag set")
		check(l.n2_toggle_valve(0).has("valves_locked_n2"), "valves lock once the coil is warm")
		check(g.size() == 6, "graph")


func test_n3_light_table_and_cold_door() -> void:
	for s in [1, 2, 3, 777]:
		var l := _new(s)
		_to_pump(l)
		check(not l.state["cell_digits_ok"], "not solved at the start")
		var p0 := l.n3_progress()
		eq(p0[2], l.n3_glyph().count(1), "digit cell count")
		var t: Array = l.state["v_sheet_target"]
		var last: Array[String] = []
		for i in 3:
			while int(l.state["sheets"][2 * i + 1]) != int(t[2 * i + 1]):
				last = l.n3_flip_sheet(i)
			while int(l.state["sheets"][2 * i]) != int(t[2 * i]):
				last = l.n3_turn_sheet(i)
		has(last, "light_digits", "seed %d: aligned sheets spell the digits" % s)
		var p1 := l.n3_progress()
		eq(p1[0], p1[2], "all digit cells lit")
		eq(p1[1], 0, "no stray light")
		eq(l.n3_lit(), l.n3_glyph(), "lit equals digits")
		check(l.n3_turn_sheet(0).has("sheets_locked"), "sheets lock once solved")
		# cold door: right digits before the thaw only report frozen
		var d: Array = l.light_digits()
		var ev: Array[String] = []
		for w in 2:
			for _k in int(d[w]):
				ev = l.cold_wheel(w)
		has(ev, "cold_frozen", "the ice holds")
		check(not l.state["cold_open"], "still closed")
		_until(l, func() -> bool: return l.state["thawed"])
		check(l.state["thawed"], "pipes solved")
		check(l.state["cold_open"], "the door opens by itself once the coil is warm and the wheels are right")
		check(l.room_open("cold"), "cold store open")


func test_n3_guessing_the_wheels_also_opens_the_door() -> void:
	var l := _new(3)
	_until(l, func() -> bool: return l.state["thawed"])
	var d: Array = l.state["v_glyph"]
	var ev: Array[String] = []
	for w in 2:
		for _k in int(d[w]):
			ev = l.cold_wheel(w)
	has(ev, "cold_opened", "right wheels and a warm coil")
	check(l.state["cold_open"] and not l.state["cell_digits_ok"], "the table need not be solved by someone who knows the number")


func test_n4_carriages_and_aisles() -> void:
	var l := _new(5)
	_until(l, func() -> bool: return l.state["cold_open"])
	check(not l.state["aisle"], "aisle closed")
	var bay := l.aisle_bay()
	var pos0: Array = (l.state["aisle_pos"] as Array).duplicate()
	var route := l.aisle_route_from_here()
	check(route.size() >= ArchiveExpData.AISLE_MIN_ROUTE, "a real route (%d cranks)" % route.size())
	# a clunk reverses the crank
	var clunks := 0
	for k in 5:
		var pos: Array = l.state["aisle_pos"]
		var dir_wanted := int(l.state["crank_dir"][k])
		var tgt := int(pos[k]) + dir_wanted
		if tgt < 0 or tgt > 6 or pos.has(tgt):
			var ev := l.n4_crank(k)
			has(ev, "clunk:%d" % k, "blocked crank clunks")
			eq(int(l.state["crank_dir"][k]), -dir_wanted, "and reverses")
			eq(JSON.stringify(l.state["aisle_pos"]), JSON.stringify(pos0), "nothing moved")
			clunks += 1
			break
	check(clunks == 1, "a blocked crank was found")
	var last: Array[String] = []
	for m: Array in l.aisle_route_from_here():
		last = l.n4_crank(int(m[0]), int(m[1]))
	has(last, "aisle_found", "the right aisle opens")
	has(last, "solved:aisle", "N4 solved")
	has(last, "moment:m6", "the echo at the rail end")
	check(l.state["aisle"] and ArchiveExpData.aisle_open_at(l.state["aisle_pos"], bay), "state")
	check(l.n4_crank(0, 1).has("cranks_locked"), "cranks lock")
	eq((l.state["bonus_echoes"] as Array), ["aisle"], "a bonus echo, not one of the 3")
	eq(ArchiveLogic.ECHOES.size(), 3, "ECHOES unchanged")


func test_n4_every_crank_is_reversible_and_no_arrangement_locks() -> void:
	var l := _new(1)
	_until(l, func() -> bool: return l.state["cold_open"])
	var rng := RandomNumberGenerator.new()
	rng.seed = 99
	for _i in 300:
		if l.state["aisle"]:
			break
		var k := rng.randi_range(0, 4)
		var d: int = [-1, 1][rng.randi_range(0, 1)]
		var before := (l.state["aisle_pos"] as Array).duplicate()
		var ev := l.n4_crank(k, d)
		if ev.any(func(e: String) -> bool: return e.begins_with("crank:")):
			check(ArchiveExpData.aisle_neighbours(l.state["aisle_pos"]).has(before) or l.state["aisle"], "undoable")
		var pos: Array = l.state["aisle_pos"]
		for j in 4:
			check(int(pos[j]) < int(pos[j + 1]), "carriages never pass each other")
	check(l.state["aisle"] or ArchiveExpData.aisle_distance(l.state["aisle_pos"], l.aisle_bay()) >= 0, "still solvable")


func test_n5_frost_window_needs_the_cloth_and_the_aisle() -> void:
	var l := _new(5)
	_until(l, func() -> bool: return l.state["aisle"])
	check(l.n5_wipe(0).has("need_cloth"), "no cloth, no wiping")
	l.take("cell_cloth")
	var ev := l.n5_wipe(1)
	has(ev, "band_wiped:1:%d" % int(l.state["v_symbols"][1]), "the sign under the band")
	has(ev, "moment:m3", "the shadow on the frost")
	check(l.n5_wipe(1).has("band_clear:1"), "a wiped band stays wiped")
	check(not l.has_item("frost_sketch"), "not yet")
	l.n5_wipe(0)
	ev = l.n5_wipe(2)
	has(ev, "frost_done", "all three bands")
	has(ev, "solved:frost", "N5 solved")
	check(l.has_item("frost_sketch") and l.state["frost_seen"], "the sketch item re-reads the signs")
	check(not l.n5_wipe(0).has("moment:m3"), "the moment fires once")
	var early := _new(5)
	_until(early, func() -> bool: return early.state["cold_open"])
	early.take("cell_cloth")
	check(early.n5_wipe(0).has("need_aisle"), "the window is behind the shelves until the aisle opens")


func test_n6_chest_rings_and_the_g1_crystals() -> void:
	for s in [1, 2, 3, 4, 5]:
		var l := _new(s)
		_until(l, func() -> bool: return l.state["frost_seen"])
		check(not l.can_take("case_crystal_1"), "no crystals yet")
		var presses := ArchiveExpData.ring_route(l.state["rings"], l.chest_target())
		check(presses.size() >= ArchiveExpData.CHEST_MIN and presses.size() <= ArchiveExpData.CHEST_MAX, "seed %d: %d presses" % [s, presses.size()])
		eq(l.chest_presses().reduce(func(a: int, b: int) -> int: return a + b, 0), presses.size(), "hint counts add up")
		var ev: Array[String] = []
		for i: int in presses:
			ev = l.n6_turn_ring(i)
		has(ev, "chest_opened", "seed %d" % s)
		has(ev, "solved:chest", "N6 solved")
		check(l.state["crystals_available"] and l.can_take("case_crystal_1") and l.can_take("case_crystal_2"), "G1 satisfied: two crystals")
		check(l.n6_turn_ring(0).has("nothing_happens"), "chest stays open")
	var early := _new(4)
	_until(early, func() -> bool: return early.state["cold_open"])
	check(early.n6_turn_ring(0).has("chest_sealed"), "the chest is out of reach before the aisle")


# ------------------------------------------------------------------ N7 .. N10
func _to(l: ArchiveLogic, field: String) -> void:
	_until(l, func() -> bool: return l.state[field])
	check(l.state[field], "reached " + field)


func test_n7_lift_and_the_wedge() -> void:
	for s in [1, 2, 3, 4]:
		var l := _new(s)
		_to(l, "thawed")
		check(l.n7_toggle_weight(0).has("nothing_happens") == false, "weights work once the pipes carry pressure")
		l.state["weights"] = [0, 0, 0, 0]
		var load := l.lift_load()
		check(l.n7_call(1).has("lift_stuck"), "the cage will not move unbalanced")
		var want := ArchiveExpData.weights_for(load)
		var ev: Array[String] = []
		for i in 4:
			if int(want[i]) == 1:
				ev = l.n7_toggle_weight(i)
				if i < 3 and ev.has("lift_balanced"):
					break
		has(ev, "lift_balanced", "seed %d: load %d balanced" % [s, load])
		has(ev, "solved:lift", "N7")
		check(l.n7_toggle_weight(0).has("weights_locked"), "weights lock")
		check(l.room_open("gallery"), "the gallery is reachable by the lift")
		has(l.n7_call(1), "lift_moved:1", "the cage moves")
		check(l.n7_call(5).has("nothing_happens"), "no such floor")
	var l2 := _new(1)
	check(l2.n7_toggle_weight(0).has("nothing_happens") or l2.n7_toggle_weight(0).has("no_pressure"), "no pressure, no counterweight")
	check(_new(1, 1).n7_toggle_weight(0).has("nothing_happens"), "Stage A has no lift")
	var g := _new(2)
	_to(g, "lift_ok")
	check(g.pull_wedge().has("nothing_happens"), "the pin is pulled from the gallery side, after a visit")
	g.enter_room("gallery")
	has(g.pull_wedge(), "wedge_out", "pin out")
	check(g.state["wedge_out"], "stair open")
	check(g.pull_wedge().has("nothing_happens"), "only once")
	# both directions: the stair alone opens the gallery for a player who is back in the hall
	var h := _new(2)
	h.state["wedge_out"] = true
	check(h.room_open("gallery"), "the stair opens the gallery too")


func test_n8_roll_call_board() -> void:
	for s in [1, 2, 3, 4, 5, 6]:
		var l := _new(s)
		_to(l, "lift_ok")
		l.enter_room("gallery")
		l.take("counter_slips")
		check(l.has_item("roll_slips"), "slips from the counter")
		var slips := l.board_slips()
		eq(slips.size() * 3, (l.state["v_slips"] as Array).size(), "slip triples")
		eq(l.board_slip_status().count(-1), slips.size(), "nothing decided yet")
		# a wrong full board reports board_wrong and which slips lie
		var wrong := (l.state["v_board"] as Array).duplicate()
		var t: Variant = wrong[0]
		wrong[0] = wrong[1]
		wrong[1] = t
		var ev: Array[String] = []
		for h in 6:
			ev.append_array(l.n8_hang(int(wrong[h]), h))
		has(ev, "board_wrong", "seed %d: all hung but a slip says otherwise" % s)
		check(not l.state["board_ok"] and l.board_slip_status().has(0), "not solved, and a slip is false")
		# lifting and re-hanging works; the right order solves
		l.n8_lift_tag(0)
		ev = []
		for h in 6:
			ev.append_array(l.n8_hang(int(l.state["v_board"][h]), h))
		has(ev, "board_ok", "seed %d" % s)
		has(ev, "solved:board", "N8")
		check(l.state["board_ok"] and not l.state["pass_key"], "the key is released, not yet taken")
		check(not l.room_open("office"), "the office needs the key in hand")
		l.take("board_key")
		check(l.has_item("pass_key") and l.state["pass_key"] and l.room_open("office"), "the pass key opens the office")
		check(l.n8_hang(0, 0).has("nothing_happens"), "the board stays solved")


func test_n8_swapping_two_hung_tags() -> void:
	var l := _new(2)
	_to(l, "lift_ok")
	l.enter_room("gallery")
	l.n8_hang(3, 0)
	l.n8_hang(4, 1)
	l.n8_hang(3, 1)
	eq(l.state["board"][1], 3, "tag 3 now on hook 1")
	eq(l.state["board"][0], 4, "tag 4 took hook 0")
	l.n8_hang(5, 1)
	eq(l.state["board"][1], 5, "a displaced tag leaves the board")
	check(not (l.state["board"] as Array).has(3), "and is back in the tray")


func test_n9_enlarger_and_n10_cabinet() -> void:
	for s in [1, 2, 3, 4]:
		var l := _new(s)
		_to(l, "pass_key")
		l.enter_room("gallery")
		check(l.enter_room("plate").has("room:plate"), "plate room opens from the gallery")
		check(l.n9_load_strip(9).has("nothing_happens"), "no such strip")
		var right := int(l.state["v_strip"])
		var wrong := (right + 1) % 4
		# wrong strip: sharp and sized -> a print of someone else, no digits
		l.n9_load_strip(wrong)
		while int(l.state["en_zoom"]) < int(l.state["v_zoom"]):
			l.n9_zoom(1)
		var ev: Array[String] = []
		while int(l.state["en_focus"]) < int(l.state["v_pfocus"]):
			ev = l.n9_focus(1)
		has(ev, "print_other:%d" % wrong, "seed %d: a sharp print of someone else" % s)
		check(not l.state["print_ok"] and not l.has_item("staff_print"), "no digits on it")
		ev = l.n9_load_strip(right)
		has(ev, "print_ready", "seed %d: the right strip at the right settings" % s)
		has(ev, "solved:print", "N9")
		check(l.has_item("staff_print"), "the staff photo")
		eq(l.cabinet_label(), int(l.state["v_strips"][right]), "the cabinet label names the strip's symbol")
		# office and cabinet
		if not l.state["pass_key"]:
			l.take("board_key")
		l.enter_room("office")
		check(l.n10_turn_wheel(0, 1).size() > 0, "wheel turns")
		l.state["cab_wheels"] = [0, 0, 0, 0]
		var cd := l.cabinet_digits()
		for i in 4:
			for _k in int(cd[i]):
				ev = l.n10_turn_wheel(i)
		has(ev, "cab_opened", "N10")
		check(l.state["cab_open"], "cabinet open")
		check((l.state["bonus_echoes"] as Array).has("office"), "a second bonus echo")
		l.take("cabinet_lamp")
		check(l.has_item("projector_lamp"), "the spare lamp")
		var lamp_ev := l.use_item_on("projector_lamp", "projector")
		has(lamp_ev, "lamp_installed", "G2 satisfied")
		check(l.state["lamp_ok"] and not l.has_item("projector_lamp"), "lamp fitted")
		check(l.n10_turn_wheel(0).has("nothing_happens"), "cabinet stays open")


func test_n9_n10_need_the_rooms() -> void:
	var l := _new(2)
	check(l.n9_load_strip(0).has("nothing_happens"), "no enlarger without the plate room")
	check(l.n10_turn_wheel(0).has("nothing_happens"), "no cabinet without the office")


# ------------------------------------------------------------------ floor plan, travel, threads, markers
func test_floor_plan_states_travel_and_markers() -> void:
	var l := _new(5)
	var plan := l.plan_data()
	eq((plan["floors"] as Array), [-1, 0, 1], "three floors")
	eq((plan["rooms"] as Array).size(), 7, "seven rooms in Stage 2")
	eq(_new(5, 1).plan_data()["rooms"].size(), 4, "four rooms in Stage A")
	for r: Dictionary in plan["rooms"]:
		check(not r["pending"], "no marker for %s at the very start" % r["id"])
		if r["id"] == "hall":
			eq(r["status"], "visited", "hall visited")
			check(r["here"], "you are here")
		else:
			eq(r["status"], "locked", "%s locked" % r["id"])
	check(not l.can_travel("pump"), "cannot travel to a locked room")
	has(l.travel_to("pump"), "travel_refused:pump", "refused")
	# open the pump room: new, enter on foot, then travel works
	_to_pump(l)
	eq(l.room_status("pump"), "new", "open but never entered")
	check(not l.can_travel("pump"), "first visit is on foot, not by plan")
	has(l.travel_to("pump"), "travel_refused:pump", "no quick travel into a room never entered")
	var ev := l.enter_room("pump")
	has(ev, "room_new:pump", "first entry")
	has(ev, "moment:m1", "the lamp that dies")
	eq(l.room_status("pump"), "visited", "now visited")
	check(not l.enter_room("pump").has("room_new:pump"), "not new twice")
	check(not l.enter_room("pump").has("moment:m1"), "moment once")
	l.enter_room("hall")
	check(l.can_travel("pump"), "now quick travel works")
	has(l.travel_to("pump"), "travel:pump", "travelled")
	eq(l.state["room"], "pump", "you are in the pump room")
	# markers: the pump room is pending (manifold), the others are not, and no marker names a puzzle not yet met
	check(l.room_pending("pump"), "the manifold is waiting")
	for id in ["cold", "gallery", "plate", "office", "cell"]:
		check(not l.room_pending(id), "%s shows no marker before it was entered" % id)


func test_markers_never_leak_a_clue_that_was_not_met() -> void:
	var l := _new(777)
	var guard := 0
	while not l.is_complete() and guard < 900:
		guard += 1
		for r: String in l.room_ids():
			if l.room_pending(r):
				# a marker needs a seen reason: the room was entered, or its lock is the hall's own coda/lamp
				var reason: bool = l.room_seen(r) or r == "hall" or (r == "cold" and l.state["chest_open"]) \
					or (r == "gallery" and l.state["board_ok"]) or (r == "office" and l.state["cab_open"])
				check(reason, "marker on %s without having met it (step %d)" % [r, guard])
		ArchiveSolver.step(l, "leyla_key")
	check(l.is_complete(), "solved while checking")
	# at the very end nothing the player has not finished is left on any floor except optional pick-ups
	for r: String in ["cell", "cold", "plate", "office", "gallery"]:
		check(not l.room_pending(r) or r == "cell" or r == "pump", "%s has nothing left" % r)


func test_markers_say_that_not_what() -> void:
	var l := _new(5)
	# the plan data holds only booleans and ids, never a solution
	var plan := JSON.stringify(l.plan_data())
	for key in ["v_", "digits", "0417", "weights"]:
		check(not plan.contains(key), "plan data does not mention " + key)


func test_open_threads_never_exceed_three_and_close_with_their_puzzles() -> void:
	var l := _new(777)
	var worst := 0
	var guard := 0
	var ever := {}
	while not l.is_complete() and guard < 900:
		guard += 1
		ArchiveSolver.step(l, "leyla_key")
		var th := l.open_threads()
		worst = maxi(worst, th.size())
		for t: Dictionary in th:
			ever[t["id"]] = true
			check(not str(t["name"]).is_empty() and ArchiveExpData.ROOMS.any(func(r: Dictionary) -> bool: return r["id"] == t["room"]),
				"thread has a room and a name")
	check(worst <= 3, "at most 3 open threads at once (%d)" % worst)
	check(ever.size() >= 4, "the walk met several threads (%d)" % ever.size())
	eq(l.open_threads().size(), 0, "all closed at the end")
	# a fourth thread waits for a slot
	var m := _new(1)
	m.state["clicks_heard"] = ["tape_1996", "tape_1997", "tape_1998"]
	m.state["booth_open"] = true
	m.state["lamp_seen"] = true
	m.state["rooms_seen"] = ["cell"]
	m.state["pump_open"] = false
	m.select_item("") # triggers a refresh through _end
	var ids: Array = m.open_threads().map(func(t: Dictionary) -> String: return t["id"])
	eq(ids.size(), 3, "three shown")
	check(ids.has("warm_panel") and ids.has("blocked_stair"), "in order of first sight")
	m.state["pump_open"] = true # closes warm_panel
	m.select_item("")
	var ids2: Array = m.open_threads().map(func(t: Dictionary) -> String: return t["id"])
	check(ids2.size() == 3 and not ids2.has("warm_panel"), "a closed thread leaves the list and the waiting one joins")


# ------------------------------------------------------------------ hints
func test_hint_ladder_covers_every_new_step() -> void:
	var seen := {}
	for stage in [1, 2]:
		for s in [3, 777]:
			var l := _new(s, stage)
			for _i in 900:
				var g := l.hint_goal()
				seen[g] = true
				if g == "done":
					break
				ArchiveSolver.step(l, "leyla_key")
	for g in ["c2x_warm", "c2x_pipes", "c2x_light", "c2x_cold_door", "c2x_aisle", "c2x_take_cloth", "c2x_frost", "c2x_chest",
			"c2x_take_crystal", "c2x_lift", "c2x_board", "c2x_take_key", "c2x_print", "c2x_cabinet", "c2x_take_lamp",
			"c2x_install_lamp"]:
		check(seen.has(g), "the solver's walk shows the goal " + g)
		check(ArchiveHints.GOALS.has(g), "listed " + g)
		check(HintPlaces.place_key(g) != "", "place for " + g)


func test_hint_goals_for_the_expansion_follow_the_walk_in_order() -> void:
	var l := _new(5)
	var seen: Array[String] = []
	for _i in 900:
		var g := l.hint_goal()
		if seen.is_empty() or seen[-1] != g:
			seen.append(g)
		if g == "done":
			break
		ArchiveSolver.step(l, "leyla_key")
	eq(seen[-1], "done", "reaches done")
	var idx := -1
	for g in seen:
		if g == "done":
			continue
		var gi := ArchiveHints.GOALS.find(g)
		check(gi >= 0, "goal listed: " + g)
		check(gi >= idx, "goal order %s after index %d" % [g, idx])
		idx = maxi(idx, gi)
	# the lamp leads once the player has reached the projector with a dead lamp
	var m := _new(5)
	_until(m, func() -> bool: return m.state["reel_repaired"] and m.state["taken"].get("splicer_reel", false))
	check(m.hint_goal().begins_with("c2x_"), "with the reel in hand and a dead lamp, the hint is about the lamp chain: " + m.hint_goal())
	check(m.hint_goal() != "c2_project", "not 'project' while the lamp is dead")


func test_level_three_speaks_this_games_answer() -> void:
	var l := _new(5)
	eq(l.hint_args("c2x_warm", 2), [], "levels 1-2 have no args")
	var a := l.hint_args("c2x_warm", 3)
	eq(a, [l.panel_letter(), "0 4 1 7"], "panel and dial")
	eq(l.hint_args("c2x_pipes", 3).size(), 1, "valve list")
	eq(l.hint_args("c2x_light", 3).size(), 5, "three sheets and two digits")
	eq(l.hint_args("c2x_cold_door", 3), [int(l.state["v_glyph"][0]), int(l.state["v_glyph"][1])], "wheels")
	eq(l.hint_args("c2x_aisle", 3)[0], l.aisle_bay() + 1, "carriage number")
	eq(l.hint_args("c2x_frost", 3).size(), 3, "three signs")
	eq(l.hint_args("c2x_chest", 3).size(), 3, "three ring counts")
	eq(l.hint_args("c2x_lift", 3)[0], l.lift_load(), "load")
	eq(l.hint_args("c2x_board", 3).size(), 1, "board order")
	eq(l.hint_args("c2x_print", 3).size(), 3, "strip, zoom, focus")
	eq(l.hint_args("c2x_cabinet", 3).size(), 4, "four digits")
	# every level-3 string takes exactly its args
	var csv := FileAccess.open("res://localization/strings.csv", FileAccess.READ)
	var rows := {}
	while not csv.eof_reached():
		var r := csv.get_csv_line()
		if r.size() >= 4:
			rows[r[0]] = r
	for g in ArchiveHints.GOALS:
		if not g.begins_with("c2x_"):
			continue
		for lang in 3:
			for lvl in [1, 2, 3]:
				var k := "hint.%s.%d" % [g, lvl]
				check(rows.has(k), "string " + k)
				if rows.has(k):
					var n := str(rows[k][1 + lang]).count("%s") + str(rows[k][1 + lang]).count("%d")
					eq(n, l.hint_args(g, lvl).size(), "%s (%d): placeholders match the args" % [k, lang])


func test_hint_answers_actually_solve() -> void:
	# follow the level-3 answer literally for the numeric puzzles
	var l := _new(777)
	_to_pump(l)
	for v: String in str(l.hint_args("c2x_pipes", 3)[0]).split(", "):
		l.n2_toggle_valve(int(v) - 1)
	check(l.state["thawed"], "the listed valves thaw the coil")
	var d := _new(777)
	_until(d, func() -> bool: return d.state["aisle"])
	var ring_counts := d.hint_args("c2x_chest", 3)
	check(ring_counts.size() == 3, "ring counts (before the frost)")


# ------------------------------------------------------------------ Trial mode, moments, profile
func test_trial_mode_rules() -> void:
	var l := _new(5)
	check(l.hints_allowed() and l.hint_goal() != "", "normal mode has hints")
	check(l.set_mode("trial"), "chosen at New Game")
	check(l.trial_active() and not l.hints_allowed(), "no hints in the Trial")
	eq(l.hint_goal(), "", "the hint ladder is unreachable")
	check(not l.set_mode("nonsense"), "unknown mode refused")
	l.take("tray_card")
	check(not l.set_mode("normal"), "locked after the first step")
	check(ArchiveLogic.trial_offer_due(1500.0) and not ArchiveLogic.trial_offer_due(1499.0), "the offer comes after 25 minutes")
	# complete in the Trial: stamp, achievement, epilogue line, profile flag
	var t := _new(5)
	t.set_mode("trial")
	check(ArchiveSolver.solve(t, "leyla_key"), "the Trial is solvable without hints")
	check(t.trial_stamp(), "stamp")
	eq(t.achievements(), ["archivist_trial"] as Array[String], "achievement")
	check(t.epilogue_keys().has("epi2.trial"), "an extra epilogue line")
	eq(t.profile_choices()["ch2_trial"], true, "profile flag")
	check(t.profile_choices().has("ch2_bonus_echoes"), "bonus echoes recorded")
	# leaving the Trial gives hints back and loses the stamp
	var u := _new(5)
	u.set_mode("trial")
	has(u.trial_off(), "trial_off", "offer accepted")
	check(u.hints_allowed() and not u.trial_stamp(), "hints back, no stamp")
	check(u.trial_off().has("nothing_happens"), "only once")
	ArchiveSolver.solve(u, "leyla_key")
	eq(u.achievements(), [] as Array[String], "no achievement after leaving")
	# an old save has no Trial
	check(not ArchiveLogic.new_legacy().set_mode("trial"), "Trial belongs to the new game")


func test_trial_survives_the_save() -> void:
	var l := _new(5)
	l.set_mode("trial")
	var r := ArchiveLogic.new()
	r.from_dict(JSON.parse_string(JSON.stringify(l.to_dict())))
	check(r.trial_active(), "mode saved")


func test_moments_fire_once_and_by_rule() -> void:
	var l := _new(777)
	var m: Dictionary = ArchiveExpData.MOMENTS
	eq(m.size(), 6, "six moments")
	for id: String in m:
		check(float(m[id]["seconds"]) <= 9.0, "%s is short" % id)
		check(str(m[id]["caption"]) != "" and str(m[id]["cue"]) != "", "%s has a caption and a cue" % id)
	check(l.try_moment("m2").is_empty(), "the knock waits until the cell door exists")
	_to_pump(l)
	check(l.try_moment("m2").has("moment:m2"), "knock behind the door, before the first entry")
	check(l.try_moment("m2").is_empty(), "once")
	l.enter_room("pump")
	l.enter_room("cell")
	check(l.try_moment("m3").is_empty(), "unknown / unready moments do nothing")
	_to(l, "aisle")
	check(l.moment_seen("m6"), "the echo moment played when the aisle opened")
	var ev := l.enter_room("cold")
	has(ev, "moment:m5", "steps above on the first visit with the aisle open")
	check(not l.enter_room("cold").has("moment:m5"), "once")
	_to(l, "lift_ok")
	has(l.enter_room("gallery"), "moment:m4", "the roll call on arrival")
	for id in ["m1", "m2", "m4", "m5", "m6"]:
		check(l.moment_seen(id), id + " seen")
	check(not str(tr("cap2x.m4")).contains("42"), "the horn never says 42")


func test_profile_choices_keep_the_old_keys() -> void:
	var l := _new(5)
	l.state["choice"] = "strand_key"
	l.state["echoes"] = ["catalogue", "stacks", "booth"]
	var p := l.profile_choices()
	eq(p["ch2_key"], "strand_key", "ch2_key")
	eq(p["ch2_echoes"], 3, "ch2_echoes still counts only the three")
	l.state["bonus_echoes"] = ["aisle", "office"]
	eq(l.profile_choices()["ch2_bonus_echoes"], 2, "bonus echoes are separate")
	# Chapter 3 reads only the old keys
	var u := UndergroundLogic.new()
	u.setup_from_profile({"ch2_key": "strand_key", "ch2_echoes": 3, "ch1_shards": 5, "ch2_trial": true, "ch2_bonus_echoes": 2})
	eq(str(u.state["entry"]), "choir", "Chapter 3 entry unchanged by the new keys")
	check(u.state["secret"], "secret needs only the old counters")


func test_captions_exist_for_every_event_the_logic_can_emit() -> void:
	var csv := FileAccess.open("res://localization/strings.csv", FileAccess.READ)
	var keys := {}
	while not csv.eof_reached():
		var r := csv.get_csv_line()
		if r.size() >= 4:
			keys[r[0]] = r
	for base in ArchiveExpData.CAPTION_EVENTS:
		check(keys.has("cap2x." + base), "caption for event " + base)
	for k in ["tap_full", "tap_dead", "tap_cracked", "m1", "m2", "m3", "m4", "m5", "m6", "coda"]:
		check(keys.has("cap2x." + k), "caption cap2x." + k)
	var l := _new(1)
	eq(l.caption_key("pump_opened"), "cap2x.pump_opened", "event caption key")
	eq(l.caption_key("tap:3:cracked"), "cap2x.tap_cracked", "tap kinds")
	eq(l.caption_key("moment:m4"), "cap2x.m4", "moments")
	eq(l.caption_key("dial_n1:3"), "", "no caption for plain dial clicks")
	for r in ArchiveExpData.ROOMS:
		check(keys.has(r["name"]), "room name " + r["name"])
	for t in ArchiveExpData.THREADS:
		check(keys.has(t["name"]), "thread name " + t["name"])
	for it in ["floor_plan", "mallet", "wipe_cloth", "frost_sketch", "roll_slips", "pass_key", "staff_print", "projector_lamp"]:
		check(keys.has("item.%s.name" % it) and keys.has("item.%s.desc" % it), "item strings " + it)
		check(ItemDB.exists(it), "ItemDB row " + it)
