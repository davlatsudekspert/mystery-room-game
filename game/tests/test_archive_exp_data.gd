extends TestBase
## Chapter 2 expansion: every generated variant is fair (docs/CHAPTER2_EXPANSION.md sections 8 and 14). Brute force over
## the whole state space of each puzzle: exactly one solution, all clues consistent, nothing can lock.

const SEEDS := 120


func test_pipe_graphs_have_one_shortest_solution() -> void:
	eq(ArchiveExpData.PIPE_GRAPHS.size(), 6, "six verified graphs")
	var signatures := {}
	for gi in ArchiveExpData.PIPE_GRAPHS.size():
		var g: Array = ArchiveExpData.PIPE_GRAPHS[gi]
		eq(g.size(), 6, "graph %d: one edge per valve" % gi)
		var a := ArchiveExpData.pipe_analyse(g)
		eq((a["masks"] as Array).size(), 1, "graph %d: exactly one shortest solution" % gi)
		check(int(a["min"]) >= 2 and int(a["min"]) <= 4, "graph %d: shortest solution has 2-4 valves (%d)" % [gi, a["min"]])
		check(int(a["hazard"]) >= 10, "graph %d: opening the wrong valves can reach the hall vent" % gi)
		check(ArchiveExpData.pipe_reach(g, 63).has(ArchiveExpData.NODE_H), "graph %d: the vent is wired in" % gi)
		check(not g.has([0, 1]) and not g.has([1, 0]), "graph %d: no direct source-coil pipe" % gi)
		# no valve opens a pipe twice, no pipe joins a node to itself
		var seen := {}
		for e: Array in g:
			check(int(e[0]) != int(e[1]), "graph %d: no loop pipe" % gi)
			seen[str([mini(e[0], e[1]), maxi(e[0], e[1])])] = true
		eq(seen.size(), 6, "graph %d: six different pipes" % gi)
		signatures[str(g)] = true
		# the solution really solves, and the empty set does not
		var sol := ArchiveExpData.pipe_solution(gi)
		var mask := 0
		for v in sol:
			mask |= 1 << v
		check(ArchiveExpData.pipe_solves(g, mask), "graph %d: the listed solution solves" % gi)
		check(not ArchiveExpData.pipe_solves(g, 0), "graph %d: all valves closed does not" % gi)
	eq(signatures.size(), 6, "the six graphs differ")


func test_mallet_probe_reports_the_flow() -> void:
	var g: Array = ArchiveExpData.PIPE_GRAPHS[0]
	eq(ArchiveExpData.pipe_tap(g, 0, 0), "dead", "closed valve: dead pipe")
	var mask := 0
	for v in ArchiveExpData.pipe_solution(0):
		mask |= 1 << v
	var full := 0
	for e in 6:
		if ArchiveExpData.pipe_tap(g, mask, e) == "full":
			full += 1
	eq(full, ArchiveExpData.pipe_solution(0).size(), "every open pipe of the solution rings full")
	# an open pipe fed by pressure that touches the vent is cracked
	for gi in 6:
		var gg: Array = ArchiveExpData.PIPE_GRAPHS[gi]
		var found := false
		for m in 64:
			if ArchiveExpData.pipe_reach(gg, m).has(ArchiveExpData.NODE_H):
				for e in 6:
					if ArchiveExpData.pipe_tap(gg, m, e) == "cracked":
						found = true
		check(found, "graph %d: a leak to the vent can be heard as cracked" % gi)


func test_glyph_font_is_complete() -> void:
	for d in 10:
		var rows: Array = ArchiveExpData.DIGIT_ROWS[d]
		eq(rows.size(), 7, "digit %d has 7 rows" % d)
		for r: String in rows:
			eq(r.length(), 5, "digit %d rows are 5 wide" % d)
	var seen := {}
	for d in 10:
		seen[ArchiveExpData.bits_to_string(ArchiveExpData.glyph_window(d, 8))] = true
	eq(seen.size(), 10, "all ten digits look different")
	eq(ArchiveExpData.legible_patterns().size(), 100, "100 legible pairs")


func test_sheet_transform_group() -> void:
	var rng := ArchiveExpData.stream(3, 1)
	var m := PackedByteArray()
	m.resize(121)
	for i in 121:
		m[i] = rng.randi_range(0, 1)
	eq(ArchiveExpData.sheet_transform(m, 4, 0), m, "four quarter turns return the sheet")
	eq(ArchiveExpData.sheet_transform(ArchiveExpData.sheet_transform(m, 0, 1), 0, 1), m, "mirroring twice returns it")
	var distinct := {}
	for o in 8:
		distinct[ArchiveExpData.sheet_transform(m, o & 3, o >> 2)] = true
	eq(distinct.size(), 8, "a generic sheet has 8 different orientations")


func test_light_table_is_fair_for_many_seeds() -> void:
	var digits_seen := {}
	for s in SEEDS:
		var lt := ArchiveExpData.gen_light_table(ArchiveExpData.stream(s, ArchiveExpData.SALT_GLYPH))
		check(not lt.is_empty(), "seed %d generates a light table" % s)
		if lt.is_empty():
			continue
		var d1: int = lt["digits"][0]
		var d2: int = lt["digits"][1]
		check(ArchiveExpData.GLYPH_DIGITS.has(d1) and ArchiveExpData.GLYPH_DIGITS.has(d2), "seed %d: unambiguous digits only" % s)
		digits_seen[d1] = true
		var sheets: Array = []
		for st: String in lt["sheets"]:
			eq(st.length(), 121, "sheet is 11 x 11")
			sheets.append(ArchiveExpData.string_to_bits(st))
		# the target orientation lights exactly the digits
		var t: Array = lt["target"]
		var lit := ArchiveExpData.light(ArchiveExpData.sheet_transform(sheets[0], t[0], t[1]),
			ArchiveExpData.sheet_transform(sheets[1], t[2], t[3]), ArchiveExpData.sheet_transform(sheets[2], t[4], t[5]))
		eq(lit, ArchiveExpData.glyph_window(d1, d2), "seed %d: aligned sheets draw exactly the digits" % s)
		# no other orientation of the 512 draws any legible pair but this one
		var scan := ArchiveExpData.scan_orientations(sheets)
		eq(scan["pairs"], [d1 * 10 + d2], "seed %d: the only legible pair in 512 orientations" % s)
		# the start is not solved
		var st: Array = lt["start"]
		var lit0 := ArchiveExpData.light(ArchiveExpData.sheet_transform(sheets[0], st[0], st[1]),
			ArchiveExpData.sheet_transform(sheets[1], st[2], st[3]), ArchiveExpData.sheet_transform(sheets[2], st[4], st[5]))
		check(lit0 != ArchiveExpData.glyph_window(d1, d2), "seed %d: starts unsolved" % s)
	check(digits_seen.size() >= 4, "the seeds use at least 4 different first digits (%d)" % digits_seen.size())
	# deterministic
	var a := ArchiveExpData.gen_light_table(ArchiveExpData.stream(9, ArchiveExpData.SALT_GLYPH))
	var b := ArchiveExpData.gen_light_table(ArchiveExpData.stream(9, ArchiveExpData.SALT_GLYPH))
	eq(JSON.stringify(a), JSON.stringify(b), "same seed, same table")


func test_aisle_state_graph_is_connected_and_every_start_is_fair() -> void:
	var states := ArchiveExpData.aisle_states()
	eq(states.size(), 21, "21 arrangements of 5 carriages in 7 slots")
	for s: Array in states:
		for v: Array in ArchiveExpData.aisle_neighbours(s):
			check(ArchiveExpData.aisle_neighbours(v).has(s), "every crank can be undone")
	# connected: every arrangement reaches every aisle target
	for bay in range(1, 5):
		for s: Array in states:
			check(ArchiveExpData.aisle_distance(s, bay) >= 0, "bay %d reachable from %s" % [bay, str(s)])
	var pool := ArchiveExpData.aisle_pool()
	check(pool.size() >= 8, "start pool has %d entries" % pool.size())
	var bays := {}
	for p: Array in pool:
		bays[int(p[0])] = true
		var d := ArchiveExpData.aisle_distance(p[1], int(p[0]))
		check(d >= ArchiveExpData.AISLE_MIN_ROUTE, "route of %d cranks is at least the minimum" % d)
		check(not ArchiveExpData.aisle_open_at(p[1], int(p[0])), "never starts open")
		eq(ArchiveExpData.aisle_route(p[1], int(p[0])).size(), d, "the route is a shortest one")
	eq(bays.size(), 4, "all four bays occur in the pool")
	# nothing opens a bay-0 aisle (no carriage in front of it)
	check(not ArchiveExpData.aisle_open_at([0, 2, 3, 4, 5], 0), "carriage 0 has no aisle in front")


func test_chest_rings_are_always_reachable_in_4_to_9_presses() -> void:
	var rng := ArchiveExpData.stream(11, 5)
	for _i in 40:
		var target := [rng.randi_range(0, 5), rng.randi_range(0, 5), rng.randi_range(0, 5)]
		var starts := ArchiveExpData.chest_starts(target)
		check(starts.size() >= 5, "target %s has %d fair starts" % [str(target), starts.size()])
		for s: Array in starts:
			var d := ArchiveExpData.ring_distance(s, target)
			check(d >= ArchiveExpData.CHEST_MIN and d <= ArchiveExpData.CHEST_MAX, "start %s: %d presses" % [str(s), d])
		if not starts.is_empty():
			var s0: Array = starts[0]
			var counts := ArchiveExpData.ring_counts(s0, target)
			var r := s0.duplicate()
			for i in 3:
				for _k in int(counts[i]):
					r = ArchiveExpData.ring_press(r, i)
			eq(r, target, "the listed presses reach the target")
	# a press moves two rings; six presses of the same ring return it
	var r0 := [2, 3, 4]
	var r := r0.duplicate()
	for _i in 6:
		r = ArchiveExpData.ring_press(r, 0)
	eq(r, r0, "six presses on one ring go round")


func test_lift_loads_need_binary_weights() -> void:
	for load in ArchiveExpData.LOADS:
		check(load >= 5 and load <= 14, "load %d in range" % load)
		check(not ArchiveExpData.WEIGHTS.has(load), "load %d is not a single weight" % load)
		eq(ArchiveExpData.weights_sum(ArchiveExpData.weights_for(load)), load, "weights balance %d" % load)
		var ways := 0
		for m in 16:
			var h := [m & 1, (m >> 1) & 1, (m >> 2) & 1, (m >> 3) & 1]
			if ArchiveExpData.weights_sum(h) == load:
				ways += 1
		eq(ways, 1, "exactly one way to balance %d" % load)


func test_roll_call_board_has_exactly_one_solution() -> void:
	var ends_total := 0
	for s in SEEDS:
		var bd := ArchiveExpData.gen_board(ArchiveExpData.stream(s, ArchiveExpData.SALT_BOARD))
		check(not bd.is_empty(), "seed %d generates a board" % s)
		if bd.is_empty():
			continue
		var slips: Array = bd["slips"]
		check(slips.size() >= ArchiveExpData.MIN_SLIPS and slips.size() <= ArchiveExpData.MAX_SLIPS, "seed %d: %d slips" % [s, slips.size()])
		eq(ArchiveExpData.count_solutions(slips), 1, "seed %d: exactly one of the 720 boards fits" % s)
		eq(ArchiveExpData.solve_slips(slips), bd["board"], "seed %d: it is the generated board" % s)
		var h := ArchiveExpData.hooks_of(bd["board"])
		var has_end := false
		for sl: Array in slips:
			check(ArchiveExpData.slip_true(sl, h), "seed %d: every slip is true for the board" % s)
			if int(sl[0]) == ArchiveExpData.SLIP_END_L or int(sl[0]) == ArchiveExpData.SLIP_END_R:
				has_end = true
		check(has_end, "seed %d: a slip fixes an end" % s)
		ends_total += 1
	eq(ends_total, SEEDS, "all seeds produced a board")
