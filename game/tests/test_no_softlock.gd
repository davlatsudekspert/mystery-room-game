extends TestBase
## Random play (including nonsense actions) must never make Chapter 1 unfinishable or lose items.

const ITEMS: Array[String] = ["notebook", "uv_lamp_empty", "battery_cell", "uv_lamp", "brass_key",
	"crystal_lens", "strand_letter", "radio_valve", "breaker_handle", "leyla_photo", "mirror_item"]
const TARGETS: Array[String] = ["desk_keyhole", "panel_main", "radio", "projector", "emblem_socket",
	"mirror_stand_b", "notebook_page", "desk_mark", "door", "safe", "chalkboard"]


func random_action(l: Lab7Logic, rng: RandomNumberGenerator) -> void:
	match rng.randi_range(0, 19):
		0: l.take(Lab7Logic.SPOTS.keys()[rng.randi_range(0, Lab7Logic.SPOTS.size() - 1)])
		1: l.step_drawer_wheel(rng.randi_range(0, 3), [-1, 1][rng.randi_range(0, 1)])
		2: l.press_gear(rng.randi_range(0, 2))
		3: l.combine(ITEMS[rng.randi_range(0, ITEMS.size() - 1)], ITEMS[rng.randi_range(0, ITEMS.size() - 1)])
		4: l.uv_reveal(TARGETS[rng.randi_range(0, TARGETS.size() - 1)])
		5: l.safe_press("0123456789CE"[rng.randi_range(0, 11)])
		6: l.press_rosette()
		7: l.use_item_on(ITEMS[rng.randi_range(0, ITEMS.size() - 1)], TARGETS[rng.randi_range(0, TARGETS.size() - 1)])
		8: l.toggle_switch(rng.randi_range(0, 4))
		9: l.toggle_main()
		10: l.step_dial(rng.randi_range(-15, 15))
		11: l.pull_book(rng.randi_range(1, 9))
		12: l.turn_sculpture(rng.randi_range(0, 1))
		13: l.turn_ring(rng.randi_range(0, 2))
		14: l.pull_projector_lever()
		15: l.remove_lens()
		16: l.rotate_mirror(rng.randi_range(0, 1), [-1, 1][rng.randi_range(0, 1)])
		17: l.collect_shard(Lab7Logic.SHARDS[rng.randi_range(0, 4)])
		18: l.select_item(ITEMS[rng.randi_range(0, ITEMS.size() - 1)])
		19: Lab7Solver.step(l, "leave_lens") # occasionally make real progress


func invariants(l: Lab7Logic) -> String:
	var seen := {}
	for id in l.inventory:
		if seen.has(id):
			return "duplicate item " + id
		seen[id] = true
	var lens_places := int(l.has_item("crystal_lens")) + int(l.state["lens_at"] in ["projector", "socket"])
	if l.state["taken"].get("safe_lens", false) and lens_places != 1:
		return "crystal lens in %d places (lens_at=%s)" % [lens_places, l.state["lens_at"]]
	if not l.state["taken"].get("safe_lens", false) and lens_places != 0:
		return "lens exists before the safe"
	if l.state["taken"].get("safe_key", false) and not l.state["compartment_open"] and not l.has_item("brass_key"):
		return "brass key lost"
	if l.state["taken"].get("compartment_handle", false) and not l.state["handle_installed"] and not l.has_item("breaker_handle"):
		return "breaker handle lost"
	if l.state["taken"].get("safe_valve", false) and not l.state["valve_installed"] and not l.has_item("radio_valve"):
		return "valve lost"
	if l.state["taken"].get("cabinet_mirror", false) and not l.state["mirror_b_mounted"] and not l.has_item("mirror_item"):
		return "mirror lost"
	if l.state["power_on"] and not l.state["handle_installed"]:
		return "power without handle"
	if l.state["door_open"] and not l.state["emblem_recorded"]:
		return "door open without emblem"
	return ""


func test_random_play_never_softlocks() -> void:
	var rng := RandomNumberGenerator.new()
	var runs := 300
	var completed := 0
	for seed in runs:
		rng.seed = 1000 + seed
		var l := Lab7Logic.new()
		if seed % 3 != 0:
			l.apply_seed(7 + seed * 13) # most runs play a drawn game (docs/VARIANTS.md): Panel 7's wiring varies too
		var steps := rng.randi_range(50, 1500)
		var bad := ""
		for _i in steps:
			random_action(l, rng)
			bad = invariants(l)
			if bad != "":
				break
		check(bad == "", "seed %d invariant: %s" % [seed, bad])
		# save -> load round trip mid-game, then the solver must finish
		var copy := Lab7Logic.new()
		copy.from_dict(JSON.parse_string(JSON.stringify(l.to_dict())))
		eq(JSON.stringify(copy.to_dict()), JSON.stringify(l.to_dict()), "seed %d save round trip" % seed)
		if Lab7Solver.solve(copy, "take_lens" if seed % 2 == 0 else "leave_lens"):
			completed += 1
		else:
			check(false, "seed %d: unsolvable after random play; goal=%s state=%s" % [seed, Lab7Hints.current_goal(copy), str(copy.state)])
	eq(completed, runs, "every random state remains completable")
