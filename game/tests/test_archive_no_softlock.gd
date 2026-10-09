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
		var l := ArchiveLogic.new()
		l.setup_from_profile({"ch1_lens": "take_lens" if seed % 2 == 0 else "leave_lens", "ch1_shards": seed % 6})
		var steps := rng.randi_range(50, 1500)
		var bad := ""
		for _i in steps:
			random_action(l, rng)
			bad = invariants(l)
			if bad != "":
				break
		check(bad == "", "seed %d invariant: %s" % [seed, bad])
		var copy := ArchiveLogic.new()
		copy.from_dict(JSON.parse_string(JSON.stringify(l.to_dict())))
		eq(JSON.stringify(copy.to_dict()), JSON.stringify(l.to_dict()), "seed %d save round trip" % seed)
		if ArchiveSolver.solve(copy, "strand_key" if seed % 3 == 0 else "leyla_key"):
			completed += 1
		else:
			check(false, "seed %d: unsolvable after random play; goal=%s state=%s inv=%s" % [seed, copy.hint_goal(), str(copy.state), str(copy.inventory)])
	eq(completed, runs, "every random state remains completable")


func test_hint_goals_follow_the_solution() -> void:
	for lens in [false, true]:
		var l := ArchiveLogic.new()
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
