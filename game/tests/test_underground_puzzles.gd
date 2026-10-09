extends TestBase
## Chapter 3 puzzle logic: every puzzle, wrong inputs, both wing orders, both Chapter 1 lens paths,
## the 42nd-socket secret, both trust endings and a save round trip.


func _new(key: String = "strand_key", lens: bool = false, shards: int = 0, echoes: int = 0) -> UndergroundLogic:
	var l := UndergroundLogic.new()
	l.setup_from_profile({"ch2_key": key, "ch1_lens": "take_lens" if lens else "leave_lens",
		"ch1_shards": shards, "ch2_echoes": echoes})
	return l


## Play the solver until a state flag is true.
func _reach(l: UndergroundLogic, flag: String, choice: String = "leyla") -> UndergroundLogic:
	var guard := 0
	while not l.state[flag] and guard < 600:
		UndergroundSolver.step(l, choice)
		guard += 1
	check(l.state[flag], "reached " + flag)
	return l


func test_profile_sets_the_entry_wing() -> void:
	var a := _new("strand_key")
	eq(str(a.state["entry"]), "choir", "Strand's key -> Choir Hall")
	check(a.has_item("strand_key") and a.zone_open("choir") and not a.zone_open("nursery"), "only the Choir Hall")
	eq(a.intro_keys()[0], "intro3.strand_key")
	var b := _new("leyla_key")
	eq(str(b.state["entry"]), "nursery", "Leyla's key -> Nursery")
	check(b.has_item("leyla_key") and b.zone_open("nursery") and not b.zone_open("choir"), "only the Nursery")
	check(not b.zone_open("gallery"), "the Gallery sleeps at the start")
	var fresh := UndergroundLogic.new()
	fresh.setup_from_profile({}) # no earlier save
	check(fresh.state["entry"] == "nursery" and fresh.has_item("leyla_key") and not fresh.state["has_lens"], "fresh default")
	check(not fresh.state["secret"], "no secret without earlier saves")
	var ev := a.use_item_on("strand_key", "lift_gate_east")
	check(ev.has("gate_wrong_key"), "the other lift gate stays shut")
	check(a.use_item_on("strand_key", "lift_gate_west").has("gate_open"), "own gate open")
	check(a.pull_lever(1).has("desk_dead"), "the desk is locked out at the start")
	check(a.turn_prism("p", -1).has("nothing_happens"), "the Nursery is sealed")
	check(a.turn_drum(0).has("nothing_happens"), "the Gallery is sealed")


func test_interlock_forward_and_backward() -> void:
	var l := _new()
	check(l.toggle_office().has("office_locked"), "office locked")
	check(l.turn_isolator(1).has("isolator_no_key"), "no key, no turn")
	check(l.take_cabinet_key(1, "held").has("key_trapped"), "held key trapped while ON")
	l.take("desk_hook")
	check(l.has_item("key_diamond"), "diamond key from the desk hook")
	var ev := l.use_item_on("key_diamond", "cabinet_0")
	check(ev.has("key_wrong_lock") and l.has_item("key_diamond"), "wrong lock refuses, key kept")
	check(l.use_item_on("key_diamond", "office_door").has("key_wrong_lock"), "office takes the square")
	l.use_item_on("key_diamond", "cabinet_1")
	check(l.take_cabinet_key(1, "in").has("item_added:key_diamond"), "input key free while ON")
	l.use_item_on("key_diamond", "cabinet_1")
	check(l.turn_isolator(1).has("isolator_off:1"), "II OFF")
	check(l.take_cabinet_key(1, "in").has("key_trapped"), "input key trapped while OFF")
	l.take_cabinet_key(1, "held")
	check(l.has_item("key_triangle"), "triangle free")
	check(l.turn_isolator(1).has("isolator_held_missing"), "II cannot go ON without its key")
	l.use_item_on("key_triangle", "cabinet_0")
	l.turn_isolator(0)
	l.take_cabinet_key(0, "held")
	l.use_item_on("key_circle", "cabinet_2")
	l.turn_isolator(2)
	l.take_cabinet_key(2, "held")
	ev = l.use_item_on("key_square", "office_door")
	check(ev.has("office_opened") and ev.has("solved:interlock"), "the square opens the office")
	check(l.take_office_key().has("key_trapped"), "office key trapped while open")
	check(not l.desk_live(), "desk dead with isolators OFF")
	# backward
	check(l.toggle_office().has("office_closed"), "close")
	check(l.toggle_office().has("office_opened"), "reopens while the key is in")
	l.toggle_office()
	l.take_office_key()
	check(l.has_item("key_square"), "square free")
	check(l.turn_isolator(0).has("isolator_held_missing"), "I needs the circle back first")
	l.use_item_on("key_square", "cabinet_2")
	l.turn_isolator(2)
	l.take_cabinet_key(2, "in")
	l.use_item_on("key_circle", "cabinet_0")
	l.turn_isolator(0)
	l.take_cabinet_key(0, "in")
	l.use_item_on("key_triangle", "cabinet_1")
	ev = l.turn_isolator(1)
	check(ev.has("desk_live") and ev.has("solved:restore"), "all ON arms the desk: %s" % str(ev))
	l.take_cabinet_key(1, "in")
	l.use_item_on("key_diamond", "desk_hook")
	check(l.state["desk_hook"] and l.desk_live(), "diamond back on the hook, desk live")


func test_heart_strip_meter_case() -> void:
	var l := _new()
	check(l.turn_case_wheel(0).has("nothing_happens"), "case behind the office door")
	for _i in 40:
		if l.state["office_open"]:
			break
		UndergroundSolver.forward(l)
	check(l.state["office_open"], "office open")
	check(not l.can_take("meter_case"), "case locked")
	check(l.try_case().has("case_locked"), "latch feedback")
	l.take("office_lamp")
	l.take("office_letters")
	check(l.has_item("ecg_strip") and l.has_item("strand_letters"), "strip and letters")
	for _i in 4:
		l.turn_case_wheel(0)
	for _i in 2:
		l.turn_case_wheel(1)
	for _i in 5:
		l.turn_case_wheel(2)
	check(not l.state["case_open"], "6th peak missing")
	var ev := l.turn_case_wheel(2)
	check(ev.has("case_opened") and ev.has("solved:heart"), "4-2-6 opens the case")
	l.take("meter_case")
	check(l.has_item("resonance_meter"), "meter")
	check(l.turn_case_wheel(0).has("nothing_happens"), "open case ignores the wheels")


func test_choir_measure_and_tune() -> void:
	var l := _new()
	check(l.measure_tube(0).has("nothing_happens"), "no meter, no reading")
	l.state["taken"]["meter_case"] = true
	l.inventory.append("resonance_meter")
	eq(l.measure_tube(0), ["meter:4"] as Array[String], "slot 1 reads 4")
	eq(l.measure_tube(8), ["meter:1"] as Array[String], "bench tube reads 1")
	eq(UndergroundLogic.tube_length(1), 7, "the longest tube reads 1")
	check(l.measure_tube(1).has("nothing_happens"), "empty slot")
	check(l.strike_hammer().has("choir_discord"), "out of tune at the start")
	check(l.tap_tube(1).has("nothing_happens"), "empty hand, empty slot")
	check(l.tap_tube(2).has("tube_lifted:2"), "lift the 7")
	check(l.tap_tube(3).has("tube_swapped:3"), "swap 7 and 2")
	check(l.tap_tube(2).has("tube_placed:2"), "hang the 2")
	for pair in [[7, 1], [8, 4], [9, 6]]:
		l.tap_tube(pair[0])
		l.tap_tube(pair[1])
	eq(l.rack(), [4, 6, 2, 7, 1, 5, 3], "staircase")
	var ev := l.strike_hammer()
	check(ev.has("choir_chord") and ev.has("solved:choir"), "clean chord")
	check(l.tap_tube(0).has("rack_locked"), "a tuned Choir stays put")


func test_startup_sequence_and_breaker() -> void:
	var l := _new()
	l.state["choir_tuned"] = true
	check(l.pull_lever(4).has("desk_dead"), "locked out until the isolation cycle")
	l.state["interlock_done"] = true
	l.state["desk_armed"] = true
	l.pull_lever(4)
	l.pull_lever(2)
	var ev := l.pull_lever(1)
	check(ev.has("breaker_trip") and int(l.state["step"]) == 0, "wrong lever trips and resets")
	eq(l.state["levers"], [0, 0, 0, 0, 0], "all levers drop")
	for n in [4, 2]:
		l.pull_lever(n)
	ev = l.turn_knob(1)
	l.turn_knob(1)
	check(int(l.state["step"]) == 0 and int(l.state["knob"]) == 0, "knob to ● too early trips")
	for n in UndergroundLogic.STARTUP:
		l.pull_lever(n)
	l.turn_knob(-1)
	ev = l.turn_knob(-1)
	check(ev.has("hall_started") and ev.has("solved:startup"), "4 2 5 1 3 then ●")
	check(ev.has("blast_door_open:west") and ev.has("gallery_awake"), "first wing: west door, Gallery awake")
	check(l.zone_open("gallery") and l.state["door_west_open"], "Gallery reachable")
	check(l.pull_lever(1).has("hall_running"), "running")
	# port data covers every step once
	var seen := {}
	var views := l.port_views()
	eq(views, {"A": {2: 2, 4: 1}, "B": {1: 4, 5: 3}, "C": {3: 5}}, "canonical port views")
	for p: String in views:
		for c: int in views[p]:
			seen[c] = views[p][c]
	eq(seen.size(), 5, "every counter step visible from one port")
	for c: int in seen:
		eq(int(seen[c]), int(l.startup()[c - 1]), "port view step %d" % c)


func test_isolator_off_drops_a_half_startup() -> void:
	var l := _new()
	l.state["interlock_done"] = true
	l.state["desk_armed"] = true
	l.pull_lever(4)
	l.take("desk_hook")
	l.use_item_on("key_diamond", "cabinet_1")
	var ev := l.turn_isolator(1)
	check(ev.has("levers_dropped") and int(l.state["step"]) == 0, "desk dies, levers drop")
	check(l.pull_lever(4).has("desk_dead"), "dead while an isolator is OFF")


func test_choir_untuned_cannot_start() -> void:
	var l := _new()
	l.state["interlock_done"] = true
	l.state["desk_armed"] = true
	for n in UndergroundLogic.STARTUP:
		l.pull_lever(n)
	l.turn_knob(1)
	var ev := l.turn_knob(1)
	check(ev.has("choir_discord") and ev.has("breaker_trip") and not l.state["hall_started"], "discord trips")


func test_seed_glyphs_and_rotation() -> void:
	var g := UndergroundLogic.SEED_GLYPHS
	var right := g[UndergroundLogic.SEED_RIGHT]
	eq(UndergroundLogic.rotate_glyph(right, 1), UndergroundLogic.SEED_SKETCH, "the sketch is the seed turned a third")
	eq(UndergroundLogic.rotate_glyph(UndergroundLogic.SEED_SKETCH, -1), right, "turned back")
	var matches := 0
	for d in g:
		if d == UndergroundLogic.rotate_glyph(UndergroundLogic.SEED_SKETCH, -1):
			matches += 1
	eq(matches, 1, "exactly one drawer matches")
	var fwd := UndergroundLogic.rotate_glyph(UndergroundLogic.SEED_SKETCH, 1)
	check(not g.has(fwd), "turning the wrong way finds no drawer (no ambiguity)")
	check(g.has(UndergroundLogic.SEED_SKETCH), "the un-turned sketch is a distractor")
	check(UndergroundLogic.rotate_glyph(right, 1) != right, "the right glyph is not 3-fold symmetric")
	var uniq := {}
	for d in g:
		uniq[d] = true
	eq(uniq.size(), 12, "12 distinct glyphs")
	var one_notch := 0
	for d in g:
		var diff := 0
		for i in 6:
			if d[i] != right[i]:
				diff += 1
		if diff == 1:
			one_notch += 1
	check(one_notch >= 6, "at least six one-notch distractors")


func test_seed_library_take_and_return() -> void:
	var l := _new("leyla_key")
	check(not l.can_take("seed_drawer"), "no drawer open")
	l.open_seed_drawer(1)
	var ev := l.take("seed_drawer")
	check(ev.has("seed_taken:1") and l.has_item("seed_crystal"), "any seed can be taken")
	check(not ev.has("solved:seed"), "not the right one")
	check(not l.can_take("seed_drawer"), "its own drawer is empty now")
	l.open_seed_drawer(UndergroundLogic.SEED_RIGHT)
	ev = l.take("seed_drawer")
	check(ev.has("seed_returned:1") and ev.has("solved:seed"), "swap: the old seed goes home: %s" % str(ev))
	eq(int(l.state["seed_from"]), UndergroundLogic.SEED_RIGHT)
	ev = l.use_item_on("seed_crystal", "seed_library")
	check(ev.has("seed_returned:6") and int(l.state["seed_from"]) == -1, "returned")
	check(l.state["seed_found"], "stays solved")


func test_leave_path_echo_and_take_path_none() -> void:
	var leave := _new("leyla_key", false)
	var ev := leave.look("seed_library")
	check(ev.has("leyla_echo:%d" % UndergroundLogic.SEED_RIGHT), "Leyla touches the right drawer")
	check(leave.look("seed_library").is_empty(), "only once")
	var take := _new("leyla_key", true)
	check(take.has_item("crystal_lens"), "take path keeps the lens")
	check(take.look("seed_library").is_empty(), "no echo on the take path")
	var choir_first := _new("strand_key", false)
	check(choir_first.look("seed_library").is_empty(), "not before the Nursery is reachable")


func test_autoclave_cloudy_remelt_and_clear() -> void:
	var l := _new("leyla_key")
	check(l.pull_start_lever().has("autoclave_not_closed"), "door open")
	l.toggle_autoclave()
	check(l.pull_start_lever().has("autoclave_empty"), "empty")
	l.toggle_autoclave()
	l.open_seed_drawer(0)
	l.take("seed_drawer")
	l.use_item_on("seed_crystal", "autoclave")
	for i in 3:
		while int(l.state["pegs"][i]) != UndergroundLogic.PEGS_TARGET[i]:
			l.turn_peg(i)
	l.toggle_autoclave()
	var ev := l.pull_start_lever()
	check(ev.has("grew:cloudy"), "wrong seed: cloudy")
	check(l.take("autoclave").has("autoclave_shut"), "closed door")
	l.toggle_autoclave()
	l.take("autoclave")
	check(l.has_item("cloudy_crystal"), "cloudy crystal in hand")
	l.open_seed_drawer(UndergroundLogic.SEED_RIGHT)
	check(l.take("seed_drawer").has("seed_in_play"), "one seed at a time")
	l.use_item_on("cloudy_crystal", "autoclave")
	check(l.remelt().has("remelted") and l.state["chamber"] == "seed", "remelt returns the seed")
	l.take("autoclave")
	l.use_item_on("seed_crystal", "seed_library")
	l.take("seed_drawer")
	l.use_item_on("seed_crystal", "autoclave")
	l.turn_peg(1) # 2 -> 3: wrong programme
	l.toggle_autoclave()
	check(l.pull_start_lever().has("grew:cloudy"), "right seed, wrong pegs: cloudy")
	check(l.pull_start_lever().has("autoclave_full"), "a crystal is already there")
	ev = l.remelt()
	check(ev.has("autoclave_opened") and not l.state["ac_closed"], "a remelt opens the door by itself")
	for _i in 5:
		l.turn_peg(1) # 3 -> 2
	l.toggle_autoclave()
	ev = l.pull_start_lever()
	check(ev.has("grew:clear") and ev.has("solved:grow"), "seed 6, pegs 5-2-4: clear")
	l.toggle_autoclave()
	l.take("autoclave")
	check(l.has_item("nursery_crystal") and l.item_glows("nursery_crystal"), "Nursery crystal")
	check(l.remelt().has("nothing_happens"), "a clear crystal is not remelted")


func test_prism_solution_is_unique_by_brute_force() -> void:
	var l := _new()
	var sols: Array = []
	for p in range(UndergroundLogic.PRISM_MIN, UndergroundLogic.PRISM_MAX + 1):
		for q in range(UndergroundLogic.PRISM_MIN, UndergroundLogic.PRISM_MAX + 1):
			if l.seal_accepts(p, q):
				sols.append([p, q])
	eq(sols, [[0, -1]], "P = 0, Q = -1 is the only combination of 25")
	var start := UndergroundLogic.receptor_light(UndergroundLogic.PRISM_START, UndergroundLogic.PRISM_START)
	var lit := 0
	for r in start:
		if r != 0:
			lit += 1
	eq(lit, 1, "the start lights only one receptor")


func test_prism_turntables_open_the_camp() -> void:
	var l := _new("leyla_key")
	check(l.play_recorder().has("nothing_happens"), "camp closed")
	check(l.tap_crystal(0).has("nothing_happens"), "crystals behind the seal")
	l.turn_prism("p", 5)
	eq(int(l.state["prism_p"]), UndergroundLogic.PRISM_MAX, "turntables have end stops")
	l.turn_prism("p", -2)
	l.turn_prism("q", -2)
	check(not l.state["camp_open"], "Q at 0 is not enough")
	var ev := l.turn_prism("q", -1)
	check(ev.has("seal_open") and ev.has("recorder_clicks") and ev.has("solved:prisms"), "camp opens: %s" % str(ev))


func test_melody_and_shutter() -> void:
	var l := _new("leyla_key")
	l.state["camp_open"] = true
	check(l.play_recorder().has("recorder_play"), "rewind replays the tape")
	var pos_of := func(size: int) -> int: return UndergroundLogic.FRAME_SIZES.find(size)
	l.tap_crystal(pos_of.call(3))
	var ev := l.tap_crystal(pos_of.call(4))
	check(ev.has("crystals_damped") and (l.state["melody_input"] as Array).is_empty(), "wrong note damps")
	for size in UndergroundLogic.MELODY:
		ev = l.tap_crystal(pos_of.call(size))
	check(ev.has("shutter_open") and ev.has("solved:melody") and ev.has("gallery_awake"), "first wing wakes the Gallery")
	check(not l.state["door_west_open"], "the west door stays sealed for H1")
	eq(l.sealed_door(), "west")


func test_rings_open_the_other_wing() -> void:
	for key in ["strand_key", "leyla_key"]:
		var l := _new(key)
		check(l.pull_drum_handle().has("nothing_happens"), "Gallery asleep")
		l.state["gallery_awake"] = true
		check(l.pull_drum_handle().has("drum_wrong"), "wrong symbols")
		var other := "nursery" if key == "strand_key" else "choir"
		check(not l.zone_open(other), "other wing sealed")
		for i in 4:
			for _k in UndergroundLogic.DRUM_TARGET[i]:
				l.turn_drum(i)
		var ev := l.pull_drum_handle()
		check(ev.has("blast_door_open:" + l.sealed_door()) and ev.has("solved:rings"), "door opens (%s)" % key)
		check(l.zone_open(other), "other wing reachable (%s)" % key)
		check(l.turn_drum(0).has("nothing_happens"), "drums lock once open")


func test_resonance_needs_both_wings() -> void:
	var l := _new()
	l.state["gallery_awake"] = true
	l.state["hall_started"] = true
	for _i in 2:
		l.turn_freq("x", 1)
	l.turn_freq("y", 1)
	check(not l.state["array_awake"] and not l.scope_live(), "no crystal, no Nursery light")
	l.inventory.append("nursery_crystal")
	check(l.use_item_on("crystal_lens", "cradle").has("nothing_happens"), "no lens in this profile")
	l.inventory.append("cloudy_crystal")
	check(l.use_item_on("cloudy_crystal", "cradle").has("cradle_refused"), "cloudy crystal refused")
	l.use_item_on("nursery_crystal", "cradle")
	check(not l.state["array_awake"], "the shutter is still closed")
	l.state["shutter_open"] = true
	l.take_from_cradle()
	var ev := l.use_item_on("nursery_crystal", "cradle")
	check(ev.has("array_awake") and ev.has("echoes_appear") and ev.has("solved:resonance"), "3:2 with everything in")
	check(l.turn_freq("x", 1).has("knobs_locked"), "figure locked")
	check(l.take_from_cradle().has("item_added:nursery_crystal"), "the crystal can still be taken back")
	check(l.state["array_awake"], "the Array stays awake")


func test_lissajous_ratio_unique() -> void:
	var n := 0
	for x in range(UndergroundLogic.FREQ_MIN, UndergroundLogic.FREQ_MAX + 1):
		for y in range(UndergroundLogic.FREQ_MIN, UndergroundLogic.FREQ_MAX + 1):
			if x * 2 == y * 3:
				n += 1
	eq(n, 1, "3:2 is the only setting with that ratio")


func test_secret_socket() -> void:
	var plain := _new("strand_key", true, 5, 2)
	check(not plain.state["secret"], "two echoes are not enough")
	plain.state["gallery_awake"] = true
	plain.inventory.append("nursery_crystal")
	check(plain.use_item_on("nursery_crystal", "socket_42").has("socket_dark"), "dark socket")
	var l := _new("strand_key", true, 5, 3)
	check(l.state["secret"], "5 shards + 3 echoes")
	l.state["gallery_awake"] = true
	l.inventory.append("nursery_crystal")
	check(l.use_item_on("crystal_lens", "socket_42").has("socket_refused"), "only the Nursery crystal")
	var ev := l.use_item_on("nursery_crystal", "socket_42")
	check(ev.has("secret_echo") and l.state["true_ending"], "Leyla's 1998 echo")
	check(l.take_from_socket_42().has("item_added:nursery_crystal"), "taken back")
	check(not l.use_item_on("nursery_crystal", "socket_42").has("secret_echo"), "plays once")


func test_kept_echoes() -> void:
	var take := _new("strand_key", true)
	check(take.release_echo("welder").has("nothing_happens"), "invisible without a crystal in hand")
	take.select_item("crystal_lens")
	check(take.release_echo("welder").has("echo_released:welder"), "welder with the lens")
	check(take.release_echo("tech_a").has("nothing_happens"), "the Nursery is still sealed")
	take.state["door_east_open"] = true
	take.state["gallery_awake"] = true
	take.release_echo("tech_a")
	take.release_echo("tech_b")
	check(take.release_echo("strand_rail").has("all_echoes"), "all four")
	eq(take.collectibles(), [4, 4, "ui.echoes"], "collectibles")
	var leave := _new("strand_key", false)
	leave.inventory.append("cloudy_crystal")
	leave.select_item("cloudy_crystal")
	check(leave.release_echo("welder").has("nothing_happens"), "leave path: not by holding a crystal")
	check(leave.release_echo("welder", true).has("echo_released:welder"), "leave path: through a port")
	check(leave.release_echo("x", true).has("nothing_happens"), "unknown echo")


func test_full_solution_both_orders_both_endings() -> void:
	for key in ["strand_key", "leyla_key"]:
		for lens in [false, true]:
			var choice := "strand" if lens else "leyla"
			var l := _new(key, lens, 5, 3)
			check(l.choose_ending(choice).has("nothing_happens"), "no finale before the Array wakes")
			check(UndergroundSolver.solve(l, choice), "solver finishes (%s, lens=%s)" % [key, lens])
			eq(l.solved_count(), UndergroundLogic.PUZZLE_IDS.size(), "all 11 solved (%s)" % key)
			eq(l.hint_goal(), "done", "hints end at done")
			eq(str(l.profile_choices()["ch3_trust"]), choice, "trust recorded")
			check(bool(l.profile_choices()["ch3_true_ending"]), "the solver plays the secret")
			var epi := l.epilogue_keys()
			check(epi.has("epi3." + choice) and epi.has("epi3.secret"), "epilogue %s" % str(epi))
			check(l.choose_ending("strand").has("nothing_happens"), "only once")


func test_wing_order_follows_the_key() -> void:
	for key in ["strand_key", "leyla_key"]:
		var l := _new(key)
		var order: Array[String] = []
		for _i in 800:
			var g := l.hint_goal()
			if order.is_empty() or order[-1] != g:
				order.append(g)
			if g == "done":
				break
			UndergroundSolver.step(l, "leyla")
		var want := UndergroundLogic.goal_order("choir" if key == "strand_key" else "nursery")
		want.append("done")
		eq(order, want, "hint goals in solution order (%s)" % key)


func test_save_round_trip_mid_game() -> void:
	for key in ["strand_key", "leyla_key"]:
		var l := _new(key, true, 5, 3)
		for _i in 70:
			UndergroundSolver.step(l, "leyla")
		var json := JSON.stringify(l.to_dict())
		var r := UndergroundLogic.new()
		check(r.from_dict(JSON.parse_string(json)), "loads")
		eq(JSON.stringify(r.to_dict()), json, "identical after reload (%s)" % key)
		eq(r.inventory, l.inventory, "inventory")
		eq(typeof(r.state["tubes"][0]), TYPE_INT, "JSON floats coerced back to int")
		eq(typeof(r.state["iso"][0]), TYPE_BOOL, "bools stay bools")
		check(UndergroundSolver.solve(r, "strand"), "a loaded game can be finished (%s)" % key)


func test_every_hint_and_runtime_key_is_translated() -> void:
	var csv := FileAccess.open("res://localization/strings.csv", FileAccess.READ)
	check(csv != null, "strings.csv exists")
	if csv == null:
		return
	var keys := {}
	while not csv.eof_reached():
		var row := csv.get_csv_line()
		if row.size() >= 4:
			keys[row[0]] = row
	var must: Array[String] = ["ui.trust_strand", "ui.trust_leyla", "ui.choice_trust_prompt", "ui.echoes",
		"cap3.lift", "intro3.strand_key", "intro3.leyla_key", "intro3.2", "epi3.strand", "epi3.leyla",
		"epi3.echoes", "epi3.secret", "epi3.end", "item.strand_key.desc3", "item.leyla_key.desc3"]
	for g in UndergroundLogic.GOALS:
		for i in [1, 2, 3]:
			must.append("hint.%s.%d" % [g, i])
	for id in ["key_diamond", "key_triangle", "key_circle", "key_square", "resonance_meter", "ecg_strip",
			"strand_letters", "seed_crystal", "nursery_crystal", "cloudy_crystal"]:
		must.append("item.%s.name" % id)
		must.append("item.%s.desc" % id)
	for e in UndergroundLogic.ECHOES:
		must.append("echo3." + e)
	for k in must:
		check(keys.has(k), "missing key " + k)
		if keys.has(k):
			for col in [1, 2, 3]:
				check(str(keys[k][col]).strip_edges() != "", "empty translation %s col %d" % [k, col])


func test_game_state_starts_chapter_3() -> void:
	SaveSystem.save_path = "user://test_ch3.json"
	var saved: Dictionary = GameState.profile.duplicate(true)
	GameState.profile["choices"] = {"ch2_key": "strand_key", "ch1_lens": "take_lens"}
	check(GameState.start_new("ch3"), "start ch3")
	var l := GameState.logic as UndergroundLogic
	check(l != null and str(l.state["entry"]) == "choir", "logic from the registry, entry from the profile")
	check(l.has_item("crystal_lens"), "lens carried over")
	eq(GameState.next_hint()["goal"], "c3_interlock", "first hint")
	l.take("desk_hook")
	GameState.save_now()
	check(GameState.continue_saved(), "continue")
	check((GameState.logic as UndergroundLogic).has_item("key_diamond"), "state survives continue")
	SaveSystem.delete_game()
	SaveSystem.save_path = SaveSystem.SAVE_PATH
	GameState.profile = saved


# ------------------------------------------------------------------ per-game answers (docs/VARIANTS.md)
## 60 seeds x both wings: every variant is well formed, unique where it must be, solvable by the solver,
## saved with the game and identical after a load.
func test_variants_are_solvable_unique_and_saved() -> void:
	var seeds_ok := 0
	var differ := 0
	for n in 60:
		var game_seed := 1000 + n * 7919
		for key: String in ["strand_key", "leyla_key"]:
			var l := _new(key)
			l.apply_seed(game_seed)
			var s := l.state
			var ok := true
			# W3: a permutation; the start keeps the canonical shape (3 on the bench, exactly 2 hung wrong)
			var choir := l.choir_target().duplicate()
			choir.sort()
			ok = ok and choir == [1, 2, 3, 4, 5, 6, 7]
			var t: Array = s["tubes"]
			var all_tubes := t.filter(func(v: Variant) -> bool: return int(v) > 0)
			all_tubes.sort()
			ok = ok and all_tubes == [1, 2, 3, 4, 5, 6, 7]
			var wrong := 0
			var empty := 0
			for k in UndergroundLogic.SLOTS:
				if int(t[k]) == 0:
					empty += 1
				elif int(t[k]) != int(l.choir_target()[k]):
					wrong += 1
			ok = ok and empty == 3 and wrong == 2
			# W4: the ports still show every step exactly once
			var steps := 0
			for p: String in l.port_views():
				steps += (l.port_views()[p] as Dictionary).size()
			ok = ok and steps == 5
			# W2
			for v: Variant in l.case_code():
				ok = ok and int(v) >= 2 and int(v) <= 9
			# E1: twelve distinct glyphs; exactly one drawer equals the sketch turned back; the right one is not
			# three-fold symmetric; the sketch as drawn is in the library (a distractor)
			var g := l.seed_glyphs()
			var uniq := {}
			for d: Variant in g:
				uniq[str(d)] = true
			ok = ok and g.size() == 12 and uniq.size() == 12
			var back := UndergroundLogic.rotate_glyph(l.seed_sketch(), -1)
			ok = ok and g.count(back) == 1 and g.find(back) == l.seed_right()
			ok = ok and UndergroundLogic.rotate_glyph(back, 1) != back and g.has(l.seed_sketch())
			# E2
			var c := l.pegs_target()
			ok = ok and int(c[0]) != int(c[1]) and int(c[1]) != int(c[2])
			# E3: unique among the 25 positions, every receptor lit, and the start does not open the seal
			var sols := 0
			for p in range(UndergroundLogic.PRISM_MIN, UndergroundLogic.PRISM_MAX + 1):
				for q in range(UndergroundLogic.PRISM_MIN, UndergroundLogic.PRISM_MAX + 1):
					if l.seal_accepts(p, q):
						sols += 1
			ok = ok and sols == 1 and not l.rims().has(0)
			ok = ok and not l.seal_accepts(UndergroundLogic.PRISM_START, UndergroundLogic.PRISM_START)
			# E4 / H1 / H2
			ok = ok and l.melody() != [1, 2, 3, 4]
			var rings := {}
			for v: Variant in l.drum_target():
				rings[int(v)] = true
			ok = ok and rings.size() == 4
			ok = ok and UndergroundLogic.FREQ_TARGETS.has(l.freq_target())
			if not ok:
				check(false, "seed %d (%s): well-formed variant" % [game_seed, key])
				continue
			if l.choir_target() != [4, 6, 2, 7, 1, 5, 3] or l.startup() != [4, 2, 5, 1, 3]:
				differ += 1
			# hints name this game's answers
			ok = ok and str(l.hint_args("c3_choir", 3)[0]) == " ".join(l.choir_target().map(func(v: Variant) -> String: return str(v)))
			ok = ok and l.hint_args("c3_rings", 3).size() == 4 and l.hint_args("c3_seed", 2).is_empty()
			# save -> load keeps every answer
			var copy := UndergroundLogic.new()
			ok = ok and copy.from_dict(l.to_dict()) and JSON.stringify(copy.to_dict()) == JSON.stringify(l.to_dict())
			# the solver finishes the chapter with these answers
			var guard := 0
			while not l.state["complete"] and guard < 900:
				UndergroundSolver.step(l, "leyla" if n % 2 == 0 else "strand")
				guard += 1
			ok = ok and l.state["complete"]
			if ok:
				seeds_ok += 1
			else:
				check(false, "seed %d (%s): solvable, saved, hints follow" % [game_seed, key])
	eq(seeds_ok, 120, "120 variant games solved")
	check(differ > 100, "the answers really change between games (%d of 120)" % differ)


func test_remelt_opens_the_autoclave() -> void:
	var l := _new("leyla_key")
	l.state["chamber"] = "cloudy"
	l.state["ac_closed"] = true
	var ev := l.remelt()
	check(ev.has("remelted") and ev.has("autoclave_opened") and not l.state["ac_closed"], "the door swings open after a remelt")
