extends TestBase
## Random play (including nonsense actions) must never make Chapter 2 unfinishable or lose items.

const ITEMS: Array[String] = ["leyla_badge", "index_card", "blank_card", "request_card", "personnel_file",
	"locker_key", "pocket_receiver", "tape_1996", "tape_1997", "tape_1998", "film_reel", "crystal_lens",
	"crystal_blank_1", "crystal_blank_2", "crystal_sign", "crystal_mark", "emblem_slide"]
const TARGETS: Array[String] = ["punch", "send_port", "card_tray", "locker_9", "deck", "projector",
	"screen_socket", "slide_projector", "port_left", "port_right", "vault", "catalogue"]


func random_action(l: ArchiveLogic, rng: RandomNumberGenerator) -> void:
	match rng.randi_range(0, 27):
		0: l.take(ArchiveLogic.SPOTS.keys()[rng.randi_range(0, ArchiveLogic.SPOTS.size() - 1)])
		1: l.open_cat_drawer(rng.randi_range(-1, 10))
		2: l.pick_divider(rng.randi_range(0, 9))
		3: l.pull_card(rng.randi_range(0, 9))
		4: l.turn_valve(rng.randi_range(0, 2), [-1, 1][rng.randi_range(0, 1)])
		5: l.toggle_punch_key(rng.randi_range(0, 7))
		6: l.pull_punch_lever()
		7: l.step_dest([-1, 1][rng.randi_range(0, 1)])
		8: l.send_canister()
		9: l.use_item_on(ITEMS[rng.randi_range(0, ITEMS.size() - 1)], TARGETS[rng.randi_range(0, TARGETS.size() - 1)])
		10: l.try_locker(rng.randi_range(0, 13))
		11: l.open_hiding_place(["grille", "ledger", "hatch", "x"][rng.randi_range(0, 3)])
		12: l.step_speed([-1, 1][rng.randi_range(0, 1)])
		13: l.play_tape()
		14: l.eject_tape()
		15: l.dial_digit(rng.randi_range(0, 9))
		16: l.splice_put(rng.randi_range(0, 3), rng.randi_range(0, 3))
		17: l.splice_lift(rng.randi_range(0, 3))
		18: l.toggle_projector()
		19: l.step_frame([-1, 1][rng.randi_range(0, 1)])
		20: l.turn_focus([-1, 1][rng.randi_range(0, 1)])
		21: l.take_from_socket()
		22: l.open_slide_drawer(rng.randi_range(0, 4))
		23: [l.rotate_slide, l.toggle_slide_lamp, l.eject_slide][rng.randi_range(0, 2)].call()
		24: l.take_from_port(["left", "right"][rng.randi_range(0, 1)])
		25: l.turn_collar(["rot_left", "rot_right", "zoom_right"][rng.randi_range(0, 2)], [-1, 1][rng.randi_range(0, 1)])
		26: l.select_item(ITEMS[rng.randi_range(0, ITEMS.size() - 1)])
		27: ArchiveSolver.step(l, "leyla_key") # occasionally make real progress
	if rng.randi_range(0, 30) == 0:
		l.turn_wheel()
	if rng.randi_range(0, 40) == 0:
		l.release_echo(ArchiveLogic.ECHOES[rng.randi_range(0, 2)])


## Nonsense and real moves of the expansion's puzzles (only for games with exp_ver >= 2).
func random_exp_action(l: ArchiveLogic, rng: RandomNumberGenerator) -> void:
	match rng.randi_range(0, 27):
		0: l.enter_room(ArchiveExpData.ROOMS[rng.randi_range(0, 6)]["id"])
		1: l.travel_to(ArchiveExpData.ROOMS[rng.randi_range(0, 6)]["id"])
		2: l.n1_open_panel(rng.randi_range(-1, 3))
		3: l.n1_dial(rng.randi_range(0, 9))
		4: l.n2_toggle_valve(rng.randi_range(-1, 6))
		5: l.n2_tap_pipe(rng.randi_range(-1, 6))
		6: l.n3_turn_sheet(rng.randi_range(0, 2))
		7: l.n3_flip_sheet(rng.randi_range(0, 2))
		8: l.cold_wheel(rng.randi_range(0, 1), [-1, 1][rng.randi_range(0, 1)])
		9: l.n4_crank(rng.randi_range(0, 4), rng.randi_range(-1, 1))
		10: l.n5_wipe(rng.randi_range(0, 2))
		11: l.n6_turn_ring(rng.randi_range(0, 2))
		12: l.n7_toggle_weight(rng.randi_range(0, 3))
		13: l.n7_call(rng.randi_range(-1, 1))
		14: l.pull_wedge()
		15: l.n8_hang(rng.randi_range(0, 5), rng.randi_range(0, 5))
		16: l.n8_lift_tag(rng.randi_range(0, 5))
		17: l.n9_load_strip(rng.randi_range(0, 3))
		18: l.n9_zoom([-1, 1][rng.randi_range(0, 1)])
		19: l.n9_focus([-1, 1][rng.randi_range(0, 1)])
		20: l.n10_turn_wheel(rng.randi_range(0, 3), [-1, 1][rng.randi_range(0, 1)])
		21: l.take(["pump_mallet", "cell_cloth", "counter_slips", "board_key", "cabinet_lamp"][rng.randi_range(0, 4)])
		22: l.use_item_on(["projector_lamp", "mallet", "wipe_cloth", "floor_plan"][rng.randi_range(0, 3)],
			["projector", "deck", "punch", "frost"][rng.randi_range(0, 3)])
		23: l.try_moment("m2")
		24: l.select_item(["mallet", "wipe_cloth", "projector_lamp", "floor_plan"][rng.randi_range(0, 3)])
		25: l.trial_off()
		26: l.toggle_projector()
		27: ArchiveSolver.step(l, "leyla_key")


func invariants(l: ArchiveLogic) -> String:
	var s := l.state
	var seen := {}
	for id in l.inventory:
		if seen.has(id):
			return "duplicate item " + id
		seen[id] = true
	# crystals: every crystal that exists is in exactly one place
	var placed := 0
	for id in ArchiveLogic.CRYSTALS:
		placed += int(l.has_item(id)) + int(s["socket"] == id) + int(s["port_left"] == id) + int(s["port_right"] == id)
	var expected := int(s["has_lens"]) + int(s["taken"].get("case_crystal_1", false)) + int(s["taken"].get("case_crystal_2", false))
	if placed != expected:
		return "crystals in %d places, expected %d" % [placed, expected]
	# reels
	for pair in [["tape_1996", "grille_reel"], ["tape_1997", "ledger_reel"], ["tape_1998", "hatch_reel"]]:
		if s["taken"].get(pair[1], false):
			var n := int(l.has_item(pair[0])) + int(s["deck_tape"] == pair[0])
			if n != 1:
				return "%s in %d places" % [pair[0], n]
	if s["taken"].get("slide_mark", false) and int(l.has_item("emblem_slide")) + int(s["slide_in"]) != 1:
		return "emblem slide lost or doubled"
	if s["taken"].get("splicer_reel", false) and int(l.has_item("film_reel")) + int(s["reel_on_projector"]) != 1:
		return "film reel lost or doubled"
	if s["taken"].get("canister_key", false) and not s["locker_open"] and not l.has_item("locker_key"):
		return "locker key lost"
	var cards := int(l.has_item("blank_card")) + int(l.has_item("request_card")) + int(s["card_in_punch"]) + int(s["canister"] != "")
	if cards > 1:
		return "%d request cards in play" % cards
	if l.exp_active():
		var lamps := int(l.has_item("projector_lamp")) + int(s["lamp_ok"] and l.exp_stage() >= 2)
		if s["taken"].get("cabinet_lamp", false) and lamps != 1:
			return "projector lamp lost or doubled (%d)" % lamps
		if s["film_seen"] and not s["lamp_ok"]:
			return "the film ran with a dead lamp"
		if s["taken"].get("case_crystal_1", false) and not s["crystals_available"]:
			return "a crystal was taken before the chest opened"
		var pos: Array = s["aisle_pos"]
		for j in 4:
			if int(pos[j]) >= int(pos[j + 1]):
				return "carriages overlap"
		if (s["rooms_seen"] as Array).has("cold") and not s["cold_open"]:
			return "entered the cold store while it was closed"
		if (s["rooms_seen"] as Array).has("office") and not s["pass_key"]:
			return "entered the office without the pass key"
		if s["pass_key"] and not s["board_ok"]:
			return "pass key without a solved board"
	if s["vault_unlocked"] and not (s["sign_recorded"] and (s["has_lens"] or s["mark_recorded"])):
		return "vault unlocked without both images"
	if s["sign_recorded"] and s["socket"] != "crystal_sign" and not l.has_item("crystal_sign") \
			and s["port_left"] != "crystal_sign" and s["port_right"] != "crystal_sign":
		return "sign crystal lost"
	return ""


func test_random_play_never_softlocks() -> void:
	var rng := RandomNumberGenerator.new()
	var runs := 300
	var completed := 0
	for seed in runs:
		rng.seed = 7000 + seed
		var l := ArchiveLogic.new_legacy()
		l.setup_from_profile({"ch1_lens": "take_lens" if seed % 2 == 0 else "leave_lens", "ch1_shards": seed % 6})
		var steps := rng.randi_range(50, 1500)
		var bad := ""
		for _i in steps:
			random_action(l, rng)
			bad = invariants(l)
			if bad != "":
				break
		check(bad == "", "seed %d invariant: %s" % [seed, bad])
		var copy := ArchiveLogic.new_legacy()
		copy.from_dict(JSON.parse_string(JSON.stringify(l.to_dict())))
		eq(JSON.stringify(copy.to_dict()), JSON.stringify(l.to_dict()), "seed %d save round trip" % seed)
		if ArchiveSolver.solve(copy, "strand_key" if seed % 3 == 0 else "leyla_key"):
			completed += 1
		else:
			check(false, "seed %d: unsolvable after random play; goal=%s state=%s inv=%s" % [seed, copy.hint_goal(), str(copy.state), str(copy.inventory)])
	eq(completed, runs, "every random state remains completable")


func test_random_play_never_softlocks_the_expansion() -> void:
	var rng := RandomNumberGenerator.new()
	var runs := 200
	var completed := 0
	for seed in runs:
		rng.seed = 9000 + seed
		var l := ArchiveLogic.new_expanded(seed, 1 + seed % 2, {"ch1_lens": "take_lens" if seed % 2 == 0 else "leave_lens", "ch1_shards": seed % 6})
		if seed % 5 == 0:
			l.set_mode("trial")
		var steps := rng.randi_range(80, 1800)
		var bad := ""
		for _i in steps:
			if rng.randi_range(0, 2) == 0:
				random_exp_action(l, rng)
			else:
				random_action(l, rng)
			bad = invariants(l)
			if bad != "":
				break
		check(bad == "", "expansion seed %d invariant: %s" % [seed, bad])
		var copy := ArchiveLogic.new_legacy()
		copy.from_dict(JSON.parse_string(JSON.stringify(l.to_dict())))
		eq(JSON.stringify(copy.to_dict()), JSON.stringify(l.to_dict()), "expansion seed %d save round trip" % seed)
		if ArchiveSolver.solve(copy, "strand_key" if seed % 3 == 0 else "leyla_key", 1200):
			completed += 1
		else:
			check(false, "expansion seed %d: unsolvable after random play; goal=%s state=%s" % [seed, copy.hint_goal(), str(copy.state)])
	eq(completed, runs, "every random expansion state remains completable")


func test_hint_goals_follow_the_solution() -> void:
	for lens in [false, true]:
		var l := ArchiveLogic.new_legacy()
		l.setup_from_profile({"ch1_lens": "take_lens" if lens else "leave_lens"})
		var seen: Array[String] = []
		for _i in 600:
			var g := l.hint_goal()
			if seen.is_empty() or seen[-1] != g:
				seen.append(g)
			if g == "done":
				break
			ArchiveSolver.step(l, "leyla_key")
		eq(seen[-1], "done", "reaches done (lens=%s)" % lens)
		var idx := -1
		for g in seen:
			if g == "done":
				continue
			var gi := ArchiveHints.GOALS.find(g)
			check(gi >= 0, "goal listed: " + g)
			check(gi >= idx, "goal order %s after index %d (lens=%s)" % [g, idx, lens])
			idx = maxi(idx, gi)
