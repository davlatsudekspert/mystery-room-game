extends TestBase
## Chapter 4 puzzle logic: every puzzle, wrong inputs, both Chapter 2 keys, both Chapter 1 lens paths, both
## Chapter 3 trust values, the parcel secret, the three endings, a save round trip, per-game variants and the
## no-softlock fuzz.

const ITEMS: Array[String] = ["strand_key", "leyla_key", "crystal_lens", "tower_key_1", "tower_key_2", "tower_key_3",
	"tower_key_4", "strand_log", "pocket_watch", "strand_last_letter", "reverse_pawl", "leyla_note_1998", "leyla_parcel"]
const TARGETS: Array[String] = ["booth_gate", "watch_gate", "cradle", "chronometer", "post_canister", "gate_1", "gate_2",
	"gate_3", "gate_4", "gate_9", "gate_x", "nowhere"]
const SPOTS: Array[String] = ["box_log", "heart_watch", "heart_letter", "heart_pawl", "locker_note", "locker_parcel",
	"post_canister", "tower_1", "tower_2", "tower_3", "tower_4", "tower_7", "tower_x", "nowhere"]


func _new(key: String = "leyla_key", lens: bool = false, trust: String = "leyla", secret: bool = false) -> ArrayHallLogic:
	var l := ArrayHallLogic.new()
	l.setup_from_profile({"ch2_key": key, "ch1_lens": "take_lens" if lens else "leave_lens", "ch3_trust": trust,
		"ch3_true_ending": secret, "ch1_shards": 5 if secret else 2, "ch2_echoes": 3, "ch3_echoes": 4 if secret else 1})
	return l


## Play the solver until a state flag is true.
func _reach(l: ArrayHallLogic, flag: String, choice: String = "leave_lens") -> ArrayHallLogic:
	var guard := 0
	while not l.state[flag] and guard < 900:
		ArrayHallSolver.step(l, choice)
		guard += 1
	check(l.state[flag], "reached " + flag)
	return l


func _power(l: ArrayHallLogic) -> void:
	l.toggle_switch(0)
	l.toggle_switch(1)
	l.pull_main()


func test_profile_sets_entry_gates_lens_trust_and_secret() -> void:
	var a := _new("strand_key", true, "strand", true)
	eq(str(a.state["entry"]), "strand", "Strand's key")
	check(a.has_item("strand_key") and a.has_item("crystal_lens"), "key and lens carried")
	check(a.state["trust_strand"] and a.state["secret"] and a.state["all_earlier"], "trust, secret, all earlier")
	eq(a.intro_keys()[0], "intro4.strand_key")
	eq(a.item_desc_key("strand_key"), "item.strand_key.desc4")
	check(not a.zone_open("booth") and not a.zone_open("watch") and not a.zone_open("apse") and not a.zone_open("floor"), "dark hall")
	check(a.use_item_on("strand_key", "watch_gate").has("gate_wrong_key"), "Strand's key does not open the grille")
	check(a.use_item_on("strand_key", "booth_gate").has("gate_open:booth"), "Strand's key opens the booth gate early")
	check(a.zone_open("booth") and not a.zone_open("watch"), "booth open before power")
	check(a.use_item_on("strand_key", "booth_gate").has("nothing_happens"), "already open")
	var b := _new("leyla_key")
	eq(str(b.state["entry"]), "leyla")
	check(b.use_item_on("leyla_key", "watch_gate").has("gate_open:watch") and b.zone_open("watch"), "Leyla's key opens the grille")
	check(b.press_knob(0).has("nothing_happens"), "the booth is shut")
	var fresh := ArrayHallLogic.new()
	fresh.setup_from_profile({}) # no earlier save
	check(fresh.state["entry"] == "leyla" and fresh.has_item("leyla_key") and not fresh.has_item("crystal_lens"), "fresh default")
	check(not fresh.state["trust_strand"] and not fresh.state["secret"] and not fresh.state["all_earlier"], "no flags without saves")
	eq(fresh.ending_id(), "dawn", "the default ending is Dawn")
	var loose := ArrayHallLogic.new()
	loose.setup_from_profile({"ch3_true_ending": "true", "ch1_shards": "5", "ch2_echoes": 3.0, "ch3_echoes": 4})
	check(loose.state["secret"] and loose.state["all_earlier"], "profile values from JSON are read loosely")


func test_panel_zero_lights_every_lamp() -> void:
	var l := _new()
	check(l.pull_main().has("lines_dead"), "nothing live")
	check(l.turn_ring_wheel(0, 1).has("wheels_dead"), "wheels dead without power")
	check(l.turn_keeper(1).has("desk_dead") and l.lift_master().has("desk_dead"), "desk dead")
	check(l.toggle_switch(7).has("nothing_happens"), "no such switch")
	var ev := l.toggle_switch(0)
	check(ev.has("switch:0:1") and ev.has("lamps:1:0:1:0"), "switch I feeds LOCK and ARRAY: %s" % str(ev))
	l.toggle_switch(3)
	l.toggle_switch(4)
	check(l.pull_main().has("lines_dead"), "I, IV, V leave a lamp dark")
	eq(ArrayHallLogic.panel_solutions(ArrayHallLogic.PANEL), [[0, 1], [3, 4]], "exactly two switch sets")
	eq(l.panel_solution(), [0, 1], "the hint names I and II")
	eq(l.hint_args("c4_power", 3), ["I, II"], "hint text")
	l.toggle_switch(0)
	ev = l.pull_main()
	check(ev.has("power_on") and ev.has("gates_release") and ev.has("solved:power"), "IV and V also light every lamp: %s" % str(ev))
	check(l.zone_open("booth") and l.zone_open("watch") and l.zone_open("apse") and l.zone_open("floor"), "power releases every gate")
	check(l.toggle_switch(0).has("switches_locked"), "switches lock")
	check(l.pull_main().has("hall_powered"), "already running")
	check(ArrayHallLogic.panel_valid(ArrayHallLogic.PANEL), "canonical matrix is valid")
	check(not ArrayHallLogic.panel_valid(ArrayHallLogic.CH1_PANEL), "Chapter 1's matrix is never drawn")
	var single: Array = ArrayHallLogic.PANEL.duplicate()
	single[0] = 1
	single[1] = 1
	single[2] = 1
	single[3] = 1
	check(not ArrayHallLogic.panel_valid(single), "a switch that feeds all four is refused")


func test_strands_box_coupled_gears() -> void:
	var l := _new("strand_key")
	l.use_item_on("strand_key", "booth_gate")
	check(not l.can_take("box_log"), "log inside the shut box")
	var ev := l.press_knob(2)
	check(ev.has("gear:2:4") and ev.has("gear:3:0"), "knob III drags gear IV: %s" % str(ev))
	eq(l.state["box"], [4, 1, 4, 0], "state after one press")
	for _i in 5:
		l.press_knob(2)
	eq(l.state["box"], [4, 1, 3, 5], "six presses are a full turn")
	eq(l.box_solution(), [2, 3, 0, 1], "canonical presses")
	eq(l.hint_args("c4_box", 3), [2, 3, 0, 1])
	for _i in 2:
		l.press_knob(0)
	for _i in 2:
		l.press_knob(1)
	check(not l.state["box_open"], "one press short")
	ev = l.press_knob(1)
	check(not ev.has("box_open"), "gear IV still off")
	ev = l.press_knob(3)
	check(ev.has("box_open") and ev.has("solved:box"), "all pointers on the mark: %s" % str(ev))
	check(l.press_knob(0).has("box_is_open"), "knobs refuse once open")
	check(l.take("box_log").has("item_added:strand_log"), "Strand's log")
	check(l.take("box_log").has("nothing_happens"), "only once")


func test_strike_the_arc() -> void:
	var l := _new()
	check(l.toggle_sun_lever().has("nothing_happens"), "apse dark")
	_power(l)
	var ev := l.toggle_sun_lever()
	check(ev.has("sun_lever:1") and ev.has("rods_apart") and ev.has("needle:0"), "lever on, rods apart: %s" % str(ev))
	for _i in 8:
		ev = l.turn_feed(-1)
	check(int(l.state["gap"]) == 1 and int(l.state["arc"]) == ArrayHallLogic.ARC_COLD, "no arc without the short")
	ev = l.turn_feed(-1)
	check(ev.has("arc_shorted") and ev.has("needle:10"), "rods touch: the needle slams over: %s" % str(ev))
	check(l.turn_feed(-1).has("gap:0"), "end stop")
	ev = l.turn_feed(1)
	check(ev.has("arc_struck") and ev.has("sun_flicker") and ev.has("needle:9"), "the arc strikes: %s" % str(ev))
	for _i in 2:
		ev = l.turn_feed(1)
	check(not l.sun_steady(), "gap 3 flickers")
	ev = l.turn_feed(1)
	check(ev.has("sun_steady") and ev.has("solved:sun") and ev.has("needle:6"), "gap 4 is the green band: %s" % str(ev))
	for _i in 3:
		l.turn_feed(1)
	check(int(l.state["arc"]) == ArrayHallLogic.ARC_LIT and not l.sun_steady(), "lit but weak at 7")
	ev = l.turn_feed(1)
	check(ev.has("arc_out") and int(l.state["arc"]) == ArrayHallLogic.ARC_COLD, "gap 8 snaps the arc out")
	check(l.turn_feed(-1).has("rods_apart"), "cold again: must short first")
	for _i in 7:
		l.turn_feed(-1)
	l.turn_feed(4)
	check(l.sun_steady() and not l.turn_feed(0).has("solved:sun"), "steady again, solved only once")
	ev = l.toggle_sun_lever()
	check(ev.has("sun_off") and int(l.state["arc"]) == ArrayHallLogic.ARC_COLD, "lever off kills the arc")
	l.turn_feed(-4)
	ev = l.toggle_sun_lever()
	check(ev.has("arc_shorted"), "lever on with the rods together shorts at once")
	eq(l.hint_args("c4_sun", 3), [4])


func test_iris_lifts_from_the_top() -> void:
	var l := _new()
	_power(l)
	var ev := l.lift_leaf(0)
	check(ev.has("leaf_pinned:0:2"), "leaf 1 is under leaf 3: %s" % str(ev))
	check(l.lift_leaf(3).has("leaf_pinned:3:2"), "the top leaf pins everything")
	check(l.lift_leaf(2).has("leaf_up:2"), "the top leaf lifts")
	check(l.lift_leaf(2).has("nothing_happens"), "lifted leaves latch")
	check(l.lift_leaf(0).has("leaf_pinned:0:5"), "then leaf 6 pins leaf 1")
	for leaf in [5, 0, 4, 1]:
		check(l.lift_leaf(leaf).has("leaf_up:%d" % leaf), "leaf %d in order" % leaf)
	check(not l.state["iris_open"], "one leaf left")
	ev = l.lift_leaf(3)
	check(ev.has("iris_open") and ev.has("solved:iris"), "iris open: %s" % str(ev))
	check(l.lift_leaf(6).has("nothing_happens"), "no seventh leaf")
	eq(l.hint_args("c4_iris", 3), ["3, 6, 1, 5, 2, 4"], "the hint counts leaves from 1")


func _light_sun(l: ArrayHallLogic) -> void:
	l.toggle_sun_lever()
	l.turn_feed(-9)
	l.turn_feed(ArrayHallLogic.GAP_TARGET)
	for leaf in ArrayHallLogic.IRIS_ORDER:
		l.lift_leaf(leaf)


func test_rings_couple_and_fold_the_beam() -> void:
	var l := _new("strand_key", false, "strand")
	_power(l)
	var ev := l.turn_ring_wheel(0, 1)
	check(ev.has("ring:0:5") and ev.has("ring:1:3") and not ev.has("beam:0"), "wheel I drags ring II; no beam yet: %s" % str(ev))
	ev = l.turn_ring_wheel(3, -1)
	check(ev.has("ring:3:0") and ev.size() == 1, "wheel IV turns the inner ring alone")
	l.turn_ring_wheel(0, -1)
	eq(l.state["rings"], [4, 2, 6, 0], "back")
	_light_sun(l)
	check(l.beam_out() and not l.replay_live(), "beam out, not folded")
	eq(l.folded(), 0)
	eq(l.ring_solution(l.align_target()), [-2, -3, 4, 0], "shortest turns, outer first (%s)" % str(l.ring_solution(l.align_target())))
	ev = l.turn_ring_wheel(0, -1)
	check(ev.has("beam:0"), "still short of tower I")
	ev = l.turn_ring_wheel(0, -1)
	check(ev.has("beam:1"), "the beam reaches tower I: %s" % str(ev))
	eq(l.state["rings"], [2, 0, 6, 0])
	l.turn_ring_wheel(1, -1)
	check(l.state["rings"][1] == 7 and l.state["rings"][2] == 5, "wheel II drags ring III")
	l.turn_ring_wheel(1, -2)
	eq(l.folded(), 2)
	l.turn_ring_wheel(3, 2)
	l.turn_ring_wheel(2, 4)
	eq(l.state["rings"], [2, 5, 7, 6], "wheel III drags ring IV past its mark")
	eq(l.folded(), 3)
	check(l.scrub().has("chrono_locked"), "the wheel is clutched to the Array")
	l.turn_ring_wheel(3, -1)
	ev = l.turn_ring_wheel(3, -1)
	check(ev.has("beam:4") and ev.has("replay_on") and ev.has("solved:align") and ev.has("hall_replays"), "folded: %s" % str(ev))
	check(ev.has("guide_echo:strand"), "Strand's echo on the Strand path")
	check(l.replay_live() and l.aligned(), "replay live")
	ev = l.turn_ring_wheel(3, 1)
	check(ev.has("replay_off") and not ev.has("solved:align"), "breaking the beam ends the replay")
	ev = l.turn_ring_wheel(3, -1)
	check(ev.has("replay_on") and not ev.has("hall_replays"), "the story beat plays once")
	ev = l.toggle_sun_lever()
	check(ev.has("replay_off"), "the Sun off ends it too")
	l.toggle_sun_lever()
	l.turn_feed(-4)
	ev = l.turn_feed(4)
	check(ev.has("replay_on"), "steady again")
	for i in 4:
		l.turn_ring_wheel(i, -int(l.state["rings"][i]))
	check(l.home(), "home")
	ev = l.turn_ring_wheel(3, 1)
	ev = l.turn_ring_wheel(3, -1)
	check(ev.has("replay_weak"), "the straight path through the gaps flickers: %s" % str(ev))
	var leyla := _new("leyla_key", false, "leyla")
	_power(leyla)
	_light_sun(leyla)
	for i in 4:
		leyla.turn_ring_wheel(i, int(leyla.ring_solution(leyla.align_target())[i]))
	check(leyla.state["align_done"] and leyla.replay_live(), "aligned by the solution")
	eq(leyla.hint_args("c4_align", 3), ["3 6 8 5"], "marks in the hint")


func test_tower_keys_and_the_cage() -> void:
	var l := _new()
	check(l.take("tower_1").has("nothing_happens"), "no catwalk without power")
	_power(l)
	check(l.take("tower_1").has("tower_out_of_reach"), "tower I is not under the hatch")
	check(l.take("tower_7").has("nothing_happens") and l.take("tower_x").has("nothing_happens"), "no such tower")
	l.turn_ring_wheel(0, -4)
	eq(l.state["rings"], [0, 6, 6, 1], "ring I home, ring II dragged")
	var ev := l.take("tower_1")
	check(ev.has("key_taken:0") and l.has_item("tower_key_1"), "key I through the hatch")
	check(l.take("tower_1").has("nothing_happens"), "bracket empty")
	check(l.use_item_on("tower_key_1", "gate_2").has("key_wrong_gate"), "key I does not fit gate II")
	check(l.use_item_on("tower_key_1", "gate_9").has("nothing_happens"), "no gate 9")
	ev = l.use_item_on("tower_key_1", "gate_1")
	check(ev.has("gate_open:0") and not l.has_item("tower_key_1"), "key I stays in gate I")
	l.turn_ring_wheel(1, 2)
	eq(l.state["rings"], [0, 0, 0, 1], "wheel II brings ring II home and drags ring III home too")
	l.take("tower_2")
	check(l.take("tower_3").has("key_taken:2"), "key III: ring III was dragged home")
	check(l.take("tower_4").has("tower_out_of_reach"), "ring IV is one mark off")
	l.turn_ring_wheel(3, -1)
	ev = l.take("tower_4")
	check(ev.has("key_taken:3") and ev.has("solved:keys"), "all four keys: %s" % str(ev))
	check(l.home(), "fetching every key leaves the rings home")
	check(l.turn_collar(0).has("nothing_happens"), "collar behind the cage")
	for n in [2, 3]:
		l.use_item_on("tower_key_%d" % n, "gate_%d" % n)
	check(not l.state["cage_open"], "gate IV shut")
	ev = l.use_item_on("tower_key_4", "gate_4")
	check(ev.has("cage_open") and ev.has("solved:cage"), "cage open: %s" % str(ev))
	check(l.try_collar().has("collar_shut"), "latch feedback")


func _to_replay(l: ArrayHallLogic) -> void:
	_power(l)
	_light_sun(l)
	for i in 4:
		l.turn_ring_wheel(i, int(l.ring_solution(l.align_target())[i]))


func test_scrub_shows_the_night() -> void:
	var l := _new()
	_to_replay(l)
	check(l.replay_live(), "replaying")
	eq(int(l.state["wheel"]), 7, "the wheel stands at 03:17")
	var ev := l.scrub()
	check(ev.has("replay:0"), "forward only: round to 03:10")
	var seen := {}
	for _i in 7:
		ev = l.scrub()
		for e in ev:
			seen[e] = true
	check(seen.has("replay_sun_lit") and seen.has("replay_rings_set") and seen.has("replay_keeper_on") and seen.has("replay_flash"), "the Night's minutes: %s" % str(seen.keys()))
	eq(int(l.state["wheel"]), 7)
	eq(l.undo_at(4), "sun")
	eq(l.undo_at(5), "rings")
	eq(l.undo_at(6), "keeper")
	eq(l.undo_at(7), "master")
	eq(l.undo_at(2), "", "an idle minute")
	eq(l.first_minute(), 4)


func test_collar_opens_the_tower_and_leyla_seats_the_lens() -> void:
	var l := _new("leyla_key", false, "leyla")
	_power(l)
	l.state["cage_open"] = true
	check(l.look("core").has("forty_second_turns"), "the forty-second light turns (Leyla path)")
	check(l.look("core").is_empty(), "once")
	eq(l.collar_target(), [0, 3, 1, 4], "the minute the Sun was lit")
	eq(l.hint_args("c4_collar", 3), [0, 3, 1, 4])
	for _i in 3:
		l.turn_collar(1)
	l.turn_collar(2)
	for _i in 3:
		l.turn_collar(3)
	check(not l.state["tower_open"], "0-3-1-3 is not it")
	var ev := l.turn_collar(3)
	check(ev.has("tower_open") and ev.has("solved:collar"), "0-3-1-4 opens the tower: %s" % str(ev))
	check(ev.has("leyla_echo_lens") and ev.has("mark_projected") and ev.has("heart_open") and ev.has("solved:lens"), "Leyla seats the lens: %s" % str(ev))
	check(l.state["lens_seated"] and l.state["lens_by_leyla"], "seated by Leyla")
	check(l.turn_collar(0).has("nothing_happens"), "collar locks")
	check(l.take_lens().has("item_added:crystal_lens") and not l.state["lens_seated"], "the lens is yours to take")
	check(l.state["heart_open"], "the drawer stays open")
	check(l.use_item_on("crystal_lens", "cradle").has("lens_seated"), "and to seat again")
	check(l.take("heart_pawl").has("item_added:reverse_pawl"), "the pawl")
	check(l.take("heart_watch").has("item_added:pocket_watch") and l.take("heart_letter").has("item_added:strand_last_letter"), "watch and letter")
	var strand := _new("strand_key", true, "strand")
	_power(strand)
	strand.state["cage_open"] = true
	check(strand.look("core").is_empty(), "no forty-second turn on the Strand path")
	for _i in 3:
		strand.turn_collar(1)
	strand.turn_collar(2)
	ev = strand.turn_collar(3, 4)
	check(ev.has("tower_open") and not ev.has("leyla_echo_lens") and not strand.state["lens_seated"], "take path: the socket waits")
	check(strand.use_item_on("strand_key", "cradle").has("cradle_refused"), "only the lens fits")
	ev = strand.use_item_on("crystal_lens", "cradle")
	check(ev.has("lens_seated") and ev.has("mark_projected") and ev.has("heart_open") and ev.has("solved:lens"), "seated: %s" % str(ev))
	check(strand.use_item_on("pocket_watch", "cradle").has("nothing_happens"), "no watch in hand")
	strand.take("heart_watch")
	check(strand.use_item_on("pocket_watch", "cradle").has("cradle_full"), "cradle full")


func test_pawl_and_the_held_note() -> void:
	var l := _new()
	_power(l)
	l.inventory.append("reverse_pawl")
	check(l.use_item_on("strand_key", "chronometer").has("nothing_happens"), "a key is not a pawl")
	var ev := l.use_item_on("reverse_pawl", "chronometer")
	check(ev.has("pawl_fitted") and ev.has("solved:pawl") and not l.has_item("reverse_pawl"), "fitted")
	ev = l.turn_keeper(1)
	check(ev.has("keeper:1") and ev.has("beat:6"), "far off: fast beat: %s" % str(ev))
	l.turn_keeper(-5)
	check(l.turn_keeper(0).has("keeper_off"), "end stop at 0")
	ev = l.turn_keeper(5)
	check(ev.has("beat:2"), "nearer: slower")
	l.turn_keeper(1)
	ev = l.turn_keeper(1)
	check(ev.has("beat:0") and ev.has("keeper_on") and ev.has("solved:note"), "matched at 7: %s" % str(ev))
	check(l.keeper_on(), "keeper on")
	ev = l.turn_keeper(10)
	check(int(l.state["keeper"]) == 12 and ev.has("beat:5") and not l.keeper_on(), "end stop at 12")
	eq(l.hint_args("c4_note", 3), [7])


## After _to_replay: open the Reliquary by hand, seat the lens, fit the pawl, tune the keeper.
func _ready_for_reversal(l: ArrayHallLogic) -> void:
	l.state["cage_open"] = true
	l.state["tower_open"] = true
	if not l.has_item("crystal_lens"):
		l.inventory.append("crystal_lens")
	l.use_item_on("crystal_lens", "cradle")
	l.take("heart_pawl")
	l.use_item_on("reverse_pawl", "chronometer")
	l.turn_keeper(ArrayHallLogic.NOTE_TARGET)


func test_reversal_order_snap_back_and_release() -> void:
	var l := _new("leyla_key", true, "strand")
	_to_replay(l)
	check(l.lift_master().has("master_held"), "nothing to run back with")
	check(l.wind_back().has("chrono_locked"), "the clock only runs forward")
	_ready_for_reversal(l)
	check(l.reversal_ready(), "ready")
	l.scrub()
	check(l.lift_master().has("master_held"), "the wheel must stand at 03:17")
	for _i in 7:
		l.scrub()
	var ev := l.lift_master()
	check(ev.has("reversal_begins") and ev.has("figures_unfreeze") and l.state["reversing"], "03:17: the lever lifts: %s" % str(ev))
	check(l.lift_master().has("nothing_happens"), "already up")
	check(l.turn_keeper(-1).has("held_fast") and l.turn_ring_wheel(0, 1).has("held_fast"), "not at 03:17")
	check(l.toggle_sun_lever().has("held_fast") and l.turn_feed(1).has("held_fast"), "the Sun too")
	check(l.take_lens().has("held_fast") and l.scrub().has("chrono_locked"), "lens held, no scrubbing")
	ev = l.wind_back()
	check(ev.has("wound:6") and int(l.state["wheel"]) == 6, "03:16")
	check(l.turn_ring_wheel(0, 1).has("held_fast"), "the rings' minute is 03:15")
	ev = l.wind_back()
	check(ev.has("snap_back") and int(l.state["wheel"]) == 7 and not l.state["master_up"] and not l.state["reversing"], "rushing past the keeper snaps back: %s" % str(ev))
	check(l.keeper_on() and l.aligned() and l.sun_steady() and l.replay_live(), "the Night's configuration is restored")
	check(l.has_item("pocket_watch") == false and l.state["pawl_fitted"] and l.state["lens_seated"], "nothing else changes")
	# the right way
	l.lift_master()
	l.wind_back()
	ev = l.turn_keeper(-ArrayHallLogic.NOTE_TARGET)
	check(ev.has("keeper_off"), "keeper off at 03:16")
	check(l.wind_back().has("wound:5"), "03:15")
	check(l.turn_keeper(1).has("held_fast"), "the keeper's minute has passed")
	for i in 4:
		var turns: Array = l.ring_solution([0, 0, 0, 0])
		l.turn_ring_wheel(i, int(turns[i]))
	check(l.home() and not l.replay_live(), "rings home; the Core is the light now")
	check(l.wind_back().has("wound:4"), "03:14")
	ev = l.toggle_sun_lever()
	check(ev.has("sun_off") and not ev.has("replay_off"), "the Sun goes out; no replay events while winding")
	ev = l.wind_back()
	check(ev.has("wound:3") and ev.has("night_undone") and ev.has("lights_rise") and ev.has("solved:reversal"), "03:13: the Night undone: %s" % str(ev))
	check(ev.has("strand_stays") and not ev.has("forty_second_rises"), "Strand stays on the Strand path; no parcel")
	check(not l.state["reversing"] and l.state["night_undone"], "done")
	check(l.wind_back().has("chrono_locked") and l.lift_master().has("nothing_happens"), "the hall is still")
	eq(l.hint_goal(), "c4_finale")
	check(l.take_lens().has("item_added:crystal_lens"), "the lens is free again")
	l.use_item_on("crystal_lens", "cradle")
	ev = l.choose_ending("take_lens")
	check(ev.has("choice:take_lens") and ev.has("chapter_complete") and l.has_item("crystal_lens"), "taken")
	eq(l.ending_id(), "keeper")
	eq(l.epilogue_keys(), ["epi4.keeper", "epi4.lens_taken", "epi4.end"] as Array[String])
	eq(l.profile_choices(), {"ch4_ending": "keeper", "ch4_lens": "take_lens", "ch4_echoes": 0, "ch4_parcel": false})
	check(l.choose_ending("leave_lens").has("nothing_happens"), "only once")


func test_reversal_hint_names_the_schedule() -> void:
	var l := _new()
	var args := l.hint_args("c4_reversal", 3)
	eq(args.size(), 6, "three minutes with their steps")
	eq([args[0], args[2], args[4]], [6, 5, 4], "latest minute first")
	check(str(args[1]).length() > 0 and str(args[3]) != str(args[5]), "step names")
	eq(l.hint_args("c4_reversal", 2), [], "no answer below level 3")


func test_parcel_secret_and_true_ending() -> void:
	var plain := _new("leyla_key", false, "leyla", false)
	plain.use_item_on("leyla_key", "watch_gate")
	check(plain.take("locker_note").has("item_added:leyla_note_1998"), "Leyla's note for everyone")
	check(plain.take("locker_parcel").has("locker_bare"), "no parcel without the Chapter 3 secret")
	var l := _new("leyla_key", false, "leyla", true)
	check(l.take("locker_parcel").has("nothing_happens"), "watch room shut")
	l.use_item_on("leyla_key", "watch_gate")
	check(l.take("locker_parcel").has("item_added:leyla_parcel"), "the parcel")
	check(l.send_post().has("station_dead"), "no power")
	_power(l)
	check(l.send_post().has("canister_empty"), "empty canister")
	check(l.use_item_on("leyla_note_1998", "post_canister").has("nothing_happens") or not l.has_item("leyla_note_1998"), "only the parcel goes in")
	check(l.use_item_on("leyla_parcel", "post_canister").has("canister_loaded"), "loaded")
	check(l.use_item_on("leyla_key", "post_canister").has("canister_full"), "full")
	l.turn_post_dial(2)
	l.turn_post_number(6)
	eq([int(l.state["post_dial"]), int(l.state["post_number"])], [2, 7], "Laboratory 7")
	var ev := l.send_post()
	check(ev.has("post_no_receiver") and l.state["canister"] == "leyla_parcel", "no receiver in the present; the parcel comes back")
	check(l.take("post_canister").has("item_added:leyla_parcel"), "and can be taken out")
	l.use_item_on("leyla_parcel", "post_canister")
	_light_sun(l)
	for i in 4:
		l.turn_ring_wheel(i, int(l.ring_solution(l.align_target())[i]))
	l.state["cage_open"] = true
	l.state["tower_open"] = true
	l.inventory.append("crystal_lens")
	l.use_item_on("crystal_lens", "cradle")
	l.take("heart_pawl")
	l.use_item_on("reverse_pawl", "chronometer")
	l.turn_keeper(ArrayHallLogic.NOTE_TARGET)
	l.lift_master()
	l.turn_post_number(1) # 8
	check(l.send_post().has("post_returned"), "wrong laboratory, even while time runs back")
	l.turn_post_number(-1)
	l.wind_back()
	ev = l.send_post()
	check(ev.has("parcel_sent") and l.state["parcel_sent"] and l.state["canister"] == "", "sent into 1979: %s" % str(ev))
	eq(l.ending_id(), "true")
	check(ArrayHallSolver.solve(l, "leave_lens"), "the solver finishes from mid-reversal")
	var epi := l.epilogue_keys()
	check(epi.has("epi4.true") and epi.has("epi4.parcel") and epi.has("epi4.lens_left") and not epi.has("epi4.strand_stays"), "true epilogue: %s" % str(epi))
	check(bool(l.profile_choices()["ch4_parcel"]), "recorded")


func test_kept_echoes_visibility() -> void:
	var take := _new("strand_key", true)
	check(take.release_echo("tech_panel").has("nothing_happens"), "invisible without a crystal or the replay")
	take.select_item("crystal_lens")
	check(take.release_echo("tech_panel").has("echo_released:tech_panel"), "panel technician with the lens")
	check(take.release_echo("clerk_post").has("nothing_happens"), "the watch room is shut")
	check(take.release_echo("leyla_lift").has("echo_released:leyla_lift"), "Leyla at the lift")
	_power(take)
	take.release_echo("clerk_post")
	check(take.release_echo("tech_wheels").has("all_echoes"), "all four")
	eq(take.collectibles(), [4, 4, "ui.echoes"])
	var leave := _new("leyla_key", false)
	check(leave.release_echo("tech_panel").has("nothing_happens"), "leave path: no crystal yet")
	_to_replay(leave)
	check(leave.release_echo("tech_panel").has("echo_released:tech_panel"), "leave path: through the replay")
	check(leave.release_echo("x").has("nothing_happens"), "unknown echo")


func test_full_solution_every_profile_and_ending() -> void:
	var endings := {}
	for key in ["strand_key", "leyla_key"]:
		for lens in [false, true]:
			for trust in ["leyla", "strand"]:
				for secret in [false, true]:
					var choice := "take_lens" if lens else "leave_lens"
					var l := _new(key, lens, trust, secret)
					check(l.choose_ending(choice).has("nothing_happens"), "no finale before the Night is undone")
					check(ArrayHallSolver.solve(l, choice), "solver finishes (%s, lens=%s, %s, secret=%s)" % [key, lens, trust, secret])
					eq(l.solved_count(), ArrayHallLogic.PUZZLE_IDS.size(), "all 12 solved (%s %s %s %s)" % [key, lens, trust, secret])
					eq(l.hint_goal(), "done")
					var want := "true" if secret else ("keeper" if trust == "strand" else "dawn")
					eq(l.ending_id(), want, "ending")
					endings[want] = true
					var epi := l.epilogue_keys()
					check(epi[0] == "epi4." + want and epi[-1] == "epi4.end", "epilogue %s" % str(epi))
					eq(epi.has("epi4.strand_stays"), secret and trust == "strand", "Strand's extra line only on the true Strand path")
					eq(str(l.profile_choices()["ch4_lens"]), choice)
					eq(bool(l.state["lens_by_leyla"]), not lens, "Leyla seats the lens on the leave path")
	eq(endings.size(), 3, "Dawn, the Keeper and the true ending are all reachable")


func test_hint_goals_follow_the_solution() -> void:
	for lens in [false, true]:
		var l := _new("strand_key", lens, "strand", true)
		var order: Array[String] = []
		for _i in 1200:
			var g := l.hint_goal()
			if order.is_empty() or order[-1] != g:
				order.append(g)
			if g == "done":
				break
			ArrayHallSolver.step(l, "leave_lens")
		var want := ArrayHallLogic.goal_order(lens)
		want.append("done")
		eq(order, want, "hint goals in solution order (lens=%s)" % lens)


func test_save_round_trip_mid_game() -> void:
	for n in 4:
		var l := _new("strand_key" if n % 2 == 0 else "leyla_key", n < 2, "strand" if n % 2 == 1 else "leyla", true)
		l.apply_seed(31 + n)
		for _i in 60 + n * 40:
			ArrayHallSolver.step(l, "leave_lens")
		var json := JSON.stringify(l.to_dict())
		var r := ArrayHallLogic.new()
		check(r.from_dict(JSON.parse_string(json)), "loads")
		eq(JSON.stringify(r.to_dict()), json, "identical after reload (%d)" % n)
		eq(r.inventory, l.inventory, "inventory")
		eq(typeof(r.state["rings"][0]), TYPE_INT, "JSON floats coerced back to int")
		eq(typeof(r.state["v_panel"][0]), TYPE_INT, "the matrix stays ints")
		eq(typeof(r.state["switches"][0]), TYPE_BOOL, "bools stay bools")
		check(ArrayHallSolver.solve(r, "take_lens"), "a loaded game can be finished (%d)" % n)


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
	var must: Array[String] = ["ui.lens4_take", "ui.lens4_leave", "ui.choice_lens4_prompt", "ui.echoes", "cap4.lift",
		"intro4.strand_key", "intro4.leyla_key", "intro4.2", "epi4.dawn", "epi4.keeper", "epi4.true", "epi4.strand_stays",
		"epi4.parcel", "epi4.lens_taken", "epi4.lens_left", "epi4.echoes", "epi4.all_light", "epi4.end",
		"item.strand_key.desc4", "item.leyla_key.desc4", "item.crystal_lens.desc_recorded", "achv.collect_ch4"]
	for g in ArrayHallLogic.GOALS:
		for i in [1, 2, 3]:
			must.append("hint.%s.%d" % [g, i])
	for a in ArrayHallLogic.NIGHT_ACTS:
		must.append("hint.c4_act." + a)
	for id in ITEMS.slice(3):
		must.append("item.%s.name" % id)
		must.append("item.%s.desc" % id)
	for e in ArrayHallLogic.ECHOES:
		must.append("echo4." + e)
	for k in must:
		check(keys.has(k), "missing key " + k)
		if keys.has(k):
			for col in [1, 2, 3]:
				check(str(keys[k][col]).strip_edges() != "", "empty translation %s col %d" % [k, col])


## The registry entry is safe before the scene exists: a chapter without a scene is never released, so neither
## the chapter select (`Premium.can_play`) nor the chapter-complete card (same check) can send the player to an
## empty scene path. Its title and subtitle are translated, so the locked row is not broken either.
func test_registration_is_safe_without_a_scene() -> void:
	var ch := Chapters.get_chapter("ch4")
	check(not ch.is_empty(), "ch4 is registered")
	eq(Chapters.next_of("ch3"), "ch4", "after Chapter 3")
	eq(Chapters.next_of("ch4"), "", "the last chapter")
	check(ResourceLoader.exists(str(ch["logic"])), "the logic script exists")
	check(Chapters.new_logic("ch4") is ArrayHallLogic, "the registry builds the Array Hall logic")
	for c: Dictionary in Chapters.LIST:
		var scene := str(c["scene"])
		if bool(c["released"]):
			check(scene != "" and ResourceLoader.exists(scene), "%s is released and its scene loads" % c["id"])
		if scene == "":
			check(not bool(c["released"]), "%s has no scene, so it stays unreleased" % c["id"])
			check(not Premium.can_play(str(c["id"])), "%s cannot be played" % c["id"])
	for loc in ["en", "ru", "uz"]:
		TranslationServer.set_locale(loc)
		for k: String in [str(ch["title"]), str(ch["subtitle"]), "ui.coming_soon", "ui.to_be_continued"]:
			check(tr(k) != k, "%s translated in %s" % [k, loc])
	TranslationServer.set_locale("en")
	# every Chapter 4 item resolves: name and description keys, and a document key where the item is a document
	for id in ITEMS.slice(3):
		check(ItemDB.exists(id), "ItemDB knows " + id)
		var doc := ItemDB.document(id)
		if doc != "":
			check(doc.ends_with("4"), "%s: the document id %s is a Chapter 4 reader case" % [id, doc])
			check(tr("doc4." + _doc_text_key(doc)) != "doc4." + _doc_text_key(doc), "doc text for " + doc)


func _doc_text_key(doc: String) -> String:
	return {"log4": "log", "letter4": "letter", "watch4": "watch", "note4": "note", "parcel4": "parcel"}.get(doc, "?")


## Every Chapter 4 string is complete in the three languages and uses the same placeholders in each.
func test_chapter_4_strings_are_complete_and_consistent() -> void:
	var csv := FileAccess.open("res://localization/strings.csv", FileAccess.READ)
	check(csv != null, "strings.csv exists")
	if csv == null:
		return
	var rx := RegEx.new()
	rx.compile("%[sd]")
	var seen := 0
	var prefixes: Array[String] = ["msg.c4_", "cap4.", "obj4.", "doc4.", "echo4.", "intro4.", "epi4.", "hint.c4_", "ui.lens4_",
		"ui.choice_lens4_", "achv.collect_ch4"]
	while not csv.eof_reached():
		var row := csv.get_csv_line()
		if row.size() < 4:
			continue
		var is4 := false
		for p in prefixes:
			is4 = is4 or row[0].begins_with(p)
		if not is4 and not (row[0].begins_with("item.") and row[0].ends_with("4")):
			continue
		seen += 1
		var counts: Array[int] = []
		for col in [1, 2, 3]:
			check(str(row[col]).strip_edges() != "", "%s: empty column %d" % [row[0], col])
			counts.append(rx.search_all(str(row[col])).size())
		check(counts[0] == counts[1] and counts[1] == counts[2], "%s: placeholders differ across languages %s" % [row[0], counts])
	check(seen > 150, "expected the full Chapter 4 table, saw %d" % seen)


func test_game_state_starts_chapter_4() -> void:
	SaveSystem.save_path = "user://test_ch4.json"
	var saved: Dictionary = GameState.profile.duplicate(true)
	GameState.profile["choices"] = {"ch2_key": "strand_key", "ch1_lens": "take_lens", "ch3_trust": "strand",
		"ch3_true_ending": true}
	check(GameState.start_new("ch4"), "start ch4")
	var l := GameState.logic as ArrayHallLogic
	check(l != null and str(l.state["entry"]) == "strand" and l.state["trust_strand"] and l.state["secret"], "logic from the registry, flags from the profile")
	check(l.has_item("crystal_lens"), "lens carried over")
	eq(GameState.next_hint()["goal"], "c4_power", "first hint")
	l.use_item_on("strand_key", "booth_gate")
	GameState.save_now()
	check(GameState.continue_saved(), "continue")
	check((GameState.logic as ArrayHallLogic).state["booth_gate"], "state survives continue")
	SaveSystem.delete_game()
	SaveSystem.save_path = SaveSystem.SAVE_PATH
	GameState.profile = saved


# ------------------------------------------------------------------ per-game answers (docs/VARIANTS.md)
## 60 seeds x two profiles: every variant is well formed, unique where it must be, solvable by the solver,
## saved with the game and identical after a load.
func test_variants_are_solvable_unique_and_saved() -> void:
	var seeds_ok := 0
	var differ := 0
	for n in 60:
		var game_seed := 1000 + n * 7919
		for p in 2:
			var l := _new("strand_key" if p == 0 else "leyla_key", p == 0, "strand" if p == 1 else "leyla", n % 3 == 0)
			l.apply_seed(game_seed)
			var s := l.state
			var ok := true
			# P1: a valid matrix with exactly two switch sets
			ok = ok and ArrayHallLogic.panel_valid(s["v_panel"]) and ArrayHallLogic.panel_solutions(s["v_panel"]).size() == 2
			ok = ok and l.panel_solution().size() >= 1 and l.panel_solution().size() <= 5
			# P2: at least two pointers off the mark; the box state is the variant start
			var off := 0
			for v: Variant in s["v_box"]:
				ok = ok and int(v) >= 0 and int(v) <= 5
				if int(v) != 0:
					off += 1
			ok = ok and off >= 2 and str(s["box"]) == str(s["v_box"])
			# P3 / P4
			ok = ok and l.gap_target() >= 2 and l.gap_target() <= 6
			var leaves: Array = l.iris_order().duplicate()
			leaves.sort()
			ok = ok and leaves == [0, 1, 2, 3, 4, 5]
			# P5: no tower at mark 1 in the orrery; the start differs in at least two rings and is the ring state
			var diffs := 0
			for i in 4:
				ok = ok and int(l.align_target()[i]) >= 1 and int(l.align_target()[i]) <= 7
				ok = ok and int(s["v_rings"][i]) >= 1 and int(s["v_rings"][i]) <= 7
				if int(s["v_rings"][i]) != int(l.align_target()[i]):
					diffs += 1
			ok = ok and diffs >= 2 and str(s["rings"]) == str(s["v_rings"]) and l.folded() < 4
			# P12 / P8: three distinct minutes in 03:11..03:16; the collar follows the Sun's minute
			var mins := {}
			for v: Variant in l.night():
				ok = ok and int(v) >= 1 and int(v) <= 6
				mins[int(v)] = true
			ok = ok and mins.size() == 3 and int(l.collar_target()[3]) == l.m_sun() and l.first_minute() >= 1
			# P11
			ok = ok and l.note_target() >= 1 and l.note_target() <= 12
			if not ok:
				check(false, "seed %d (%d): well-formed variant" % [game_seed, p])
				continue
			if l.align_target() != [2, 5, 7, 4] or l.night() != [4, 5, 6] or l.note_target() != 7:
				differ += 1
			# hints name this game's answers
			ok = ok and l.hint_args("c4_align", 3)[0] == " ".join(l.align_target().map(func(v: Variant) -> String: return str(int(v) + 1)))
			ok = ok and l.hint_args("c4_collar", 3) == l.collar_target() and l.hint_args("c4_sun", 2).is_empty()
			ok = ok and l.hint_args("c4_reversal", 3).size() == 6
			# save -> load keeps every answer
			var copy := ArrayHallLogic.new()
			ok = ok and copy.from_dict(l.to_dict()) and JSON.stringify(copy.to_dict()) == JSON.stringify(l.to_dict())
			# the solver finishes the chapter with these answers
			var guard := 0
			while not l.state["complete"] and guard < 1200:
				ArrayHallSolver.step(l, "take_lens" if n % 2 == 0 else "leave_lens")
				guard += 1
			ok = ok and l.state["complete"] and l.solved_count() == 12
			ok = ok and (not l.state["secret"] or l.state["parcel_sent"])
			if ok:
				seeds_ok += 1
			else:
				check(false, "seed %d (%d): solvable, saved, hints follow (goal %s)" % [game_seed, p, l.hint_goal()])
	eq(seeds_ok, 120, "120 variant games solved")
	check(differ > 100, "the answers really change between games (%d of 120)" % differ)


# ------------------------------------------------------------------ no softlock
func random_action(l: ArrayHallLogic, rng: RandomNumberGenerator) -> void:
	var dir: int = [-1, 1][rng.randi_range(0, 1)]
	match rng.randi_range(0, 44):
		0, 1: l.take(SPOTS[rng.randi_range(0, SPOTS.size() - 1)])
		2, 3: l.use_item_on(ITEMS[rng.randi_range(0, ITEMS.size() - 1)], TARGETS[rng.randi_range(0, TARGETS.size() - 1)])
		4: l.toggle_switch(rng.randi_range(-1, 5))
		5: l.pull_main()
		6: l.press_knob(rng.randi_range(-1, 4))
		7: l.toggle_sun_lever()
		8, 9: l.turn_feed([-1, 1, -3, 3, 9][rng.randi_range(0, 4)])
		10: l.lift_leaf(rng.randi_range(-1, 6))
		11, 12, 13: l.turn_ring_wheel(rng.randi_range(-1, 4), dir)
		14: l.scrub()
		15: l.turn_collar(rng.randi_range(-1, 4), dir)
		16: l.try_collar()
		17: l.take_lens()
		18, 19: l.turn_keeper([-1, 1, -5, 5, 12][rng.randi_range(0, 4)])
		20: l.lift_master()
		21, 22: l.wind_back()
		23: l.turn_post_dial(dir)
		24: l.turn_post_number(dir)
		25: l.send_post()
		26: l.select_item(ITEMS[rng.randi_range(0, ITEMS.size() - 1)])
		27: l.release_echo(ArrayHallLogic.ECHOES[rng.randi_range(0, 3)])
		28: l.look(["core", "bridge", "x"][rng.randi_range(0, 2)])
		29: l.choose_ending(["take_lens", "leave_lens", "x"][rng.randi_range(0, 2)])
		_: ArrayHallSolver.step(l, "leave_lens") # make real progress now and then


func invariants(l: ArrayHallLogic) -> String:
	var s := l.state
	var seen := {}
	for id in l.inventory:
		if seen.has(id):
			return "duplicate item " + id
		seen[id] = true
	if not l.has_item("strand_key" if s["entry"] == "strand" else "leyla_key"):
		return "the Chapter 2 key is gone"
	var lens_places := int(l.has_item("crystal_lens")) + int(s["lens_seated"])
	if lens_places != int(bool(s["has_lens"]) or bool(s["lens_by_leyla"])):
		return "lens in %d places" % lens_places
	for i in 4:
		var n := int(s["tower_keys"][i]) + int(l.has_item(ArrayHallLogic.TOWER_KEYS[i])) + int(s["gates"][i])
		if n != 1:
			return "tower key %d in %d places" % [i, n]
	var pawl := int(not s["taken"].get("heart_pawl", false)) + int(l.has_item("reverse_pawl")) + int(s["pawl_fitted"])
	if pawl != 1:
		return "pawl in %d places" % pawl
	var parcel := int(l.has_item("leyla_parcel")) + int(s["canister"] == "leyla_parcel") + int(s["parcel_sent"])
	if s["secret"]:
		if parcel + int(not s["taken"].get("locker_parcel", false)) != 1:
			return "parcel in %d places" % parcel
	elif parcel != 0:
		return "a parcel without the secret"
	if s["box_open"] and str(s["box"]) != str([0, 0, 0, 0]):
		return "box open with a pointer off"
	if s["iris_open"] != not (s["iris_up"] as Array).has(false):
		return "iris flag disagrees with the leaves"
	match int(s["arc"]):
		ArrayHallLogic.ARC_LIT:
			if not s["sun_lever"] or int(s["gap"]) < 1 or int(s["gap"]) > 7:
				return "arc lit at gap %d lever %s" % [int(s["gap"]), str(s["sun_lever"])]
		ArrayHallLogic.ARC_SHORTED:
			if not s["sun_lever"] or int(s["gap"]) != 0:
				return "shorted at gap %d" % int(s["gap"])
	if (s["cage_open"] and (s["gates"] as Array).has(false)) or (s["cage_open"] and not s["power"]):
		return "cage open too early"
	if s["tower_open"] and not s["cage_open"]:
		return "tower open before the cage"
	if s["heart_open"] and not s["tower_open"]:
		return "heart open before the tower"
	if s["pawl_fitted"] and not s["heart_open"]:
		return "pawl fitted before the drawer"
	if s["reversing"] and not (s["master_up"] and s["pawl_fitted"] and s["lens_seated"] and s["power"]):
		return "reversing without the Night's configuration"
	if s["reversing"] and s["night_undone"]:
		return "reversing after the release"
	if s["night_undone"] and not (s["pawl_fitted"] and s["master_up"]):
		return "released without the pawl"
	if s["parcel_sent"] and not s["secret"]:
		return "parcel sent without the secret"
	if s["complete"] and not s["night_undone"]:
		return "complete before the release"
	return ""


func test_random_play_never_softlocks() -> void:
	var rng := RandomNumberGenerator.new()
	var runs := 200
	var completed := 0
	var deep := 0 # runs whose random play itself opened the glass tower
	for seed in runs:
		rng.seed = 7000 + seed
		var l := _new("strand_key" if seed % 2 == 0 else "leyla_key", seed % 4 < 2, "strand" if seed % 3 == 0 else "leyla",
			seed % 5 != 0)
		if seed % 7 == 0:
			l.apply_seed(500 + seed)
		var steps := rng.randi_range(100, 1500)
		var bad := ""
		for _i in steps:
			random_action(l, rng)
			bad = invariants(l)
			if bad != "":
				break
		check(bad == "", "seed %d invariant: %s" % [seed, bad])
		deep += int(l.state["tower_open"])
		var copy := ArrayHallLogic.new()
		copy.from_dict(JSON.parse_string(JSON.stringify(l.to_dict())))
		eq(JSON.stringify(copy.to_dict()), JSON.stringify(l.to_dict()), "seed %d save round trip" % seed)
		if ArrayHallSolver.solve(copy, "take_lens" if seed % 2 == 0 else "leave_lens"):
			completed += 1
			check(not copy.state["secret"] or copy.state["parcel_sent"], "seed %d: the secret stays reachable" % seed)
		else:
			check(false, "seed %d: unsolvable after random play; goal=%s state=%s inv=%s" % [seed, copy.hint_goal(), str(copy.state), str(copy.inventory)])
	eq(completed, runs, "every random state remains completable")
	check(deep >= runs / 10, "random play reaches the Core often enough (%d of %d)" % [deep, runs])


func test_hint_goal_always_listed() -> void:
	var rng := RandomNumberGenerator.new()
	for seed in 40:
		rng.seed = 400 + seed
		var l := _new("strand_key" if seed % 2 == 0 else "leyla_key", seed % 3 == 0)
		for _i in 600:
			random_action(l, rng)
			var g := l.hint_goal()
			if g != "done" and not ArrayHallLogic.GOALS.has(g):
				check(false, "seed %d: unknown goal %s" % [seed, g])
				break
