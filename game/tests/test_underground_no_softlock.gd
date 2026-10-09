extends TestBase
## Random play (including nonsense actions) must never make Chapter 3 unfinishable or lose items,
## on both wing orders and both Chapter 1 lens paths.

const ITEMS: Array[String] = ["strand_key", "leyla_key", "crystal_lens", "key_diamond", "key_triangle",
	"key_circle", "key_square", "resonance_meter", "ecg_strip", "strand_letters", "seed_crystal",
	"nursery_crystal", "cloudy_crystal"]
const TARGETS: Array[String] = ["cabinet_0", "cabinet_1", "cabinet_2", "cabinet_9", "office_door", "desk_hook",
	"seed_library", "autoclave", "cradle", "socket_42", "lift_gate_west", "lift_gate_east", "choir"]
const SPOTS: Array[String] = ["desk_hook", "office_lamp", "office_letters", "meter_case", "seed_drawer",
	"autoclave", "nowhere"]


func random_action(l: UndergroundLogic, rng: RandomNumberGenerator) -> void:
	var dir: int = [-1, 1][rng.randi_range(0, 1)]
	match rng.randi_range(0, 30):
		0, 1: l.take(SPOTS[rng.randi_range(0, SPOTS.size() - 1)])
		2, 3: l.use_item_on(ITEMS[rng.randi_range(0, ITEMS.size() - 1)], TARGETS[rng.randi_range(0, TARGETS.size() - 1)])
		4, 5: l.turn_isolator(rng.randi_range(-1, 3))
		6, 7: l.take_cabinet_key(rng.randi_range(0, 2), ["in", "held", "x"][rng.randi_range(0, 2)])
		8: l.toggle_office()
		9: l.take_office_key()
		10: l.turn_case_wheel(rng.randi_range(0, 2), dir)
		11: l.try_case()
		12, 13: l.tap_tube(rng.randi_range(-1, 10))
		14:
			if rng.randi_range(0, 1) == 0:
				l.measure_tube(rng.randi_range(-1, 9))
			else:
				l.strike_hammer()
		15: l.pull_lever(rng.randi_range(0, 6))
		16: l.turn_knob(dir)
		17: l.open_seed_drawer(rng.randi_range(-1, 12))
		18: l.look(["seed_library", "port_a", "glass_floor"][rng.randi_range(0, 2)])
		19: [l.toggle_autoclave, l.pull_start_lever, l.remelt][rng.randi_range(0, 2)].call()
		20: l.turn_peg(rng.randi_range(0, 2), dir)
		21: l.turn_prism(["p", "q", "r"][rng.randi_range(0, 2)], dir)
		22:
			if rng.randi_range(0, 3) == 0:
				l.play_recorder()
			else:
				l.tap_crystal(rng.randi_range(-1, 4))
		23: l.turn_drum(rng.randi_range(0, 3), dir)
		24: l.pull_drum_handle()
		25: l.turn_freq(["x", "y"][rng.randi_range(0, 1)], dir)
		26: [l.take_from_cradle, l.take_from_socket_42][rng.randi_range(0, 1)].call()
		27: l.select_item(ITEMS[rng.randi_range(0, ITEMS.size() - 1)])
		28: l.release_echo(UndergroundLogic.ECHOES[rng.randi_range(0, 3)], rng.randi_range(0, 1) == 0)
		_: UndergroundSolver.step(l, "leyla") # make real progress now and then


func invariants(l: UndergroundLogic) -> String:
	var s := l.state
	var seen := {}
	for id in l.inventory:
		if seen.has(id):
			return "duplicate item " + id
		seen[id] = true
	if not l.has_item("strand_key" if s["entry"] == "choir" else "leyla_key"):
		return "the Chapter 2 key is gone"
	if l.has_item("crystal_lens") != bool(s["has_lens"]):
		return "lens lost or appeared"
	# interlock keys: each in exactly one place
	for k in UndergroundLogic.KEYS:
		var n := int(l.has_item(k))
		for c in 3:
			n += int(s["cab_in"][c] == k)
			n += int(s["cab_held"][c] and UndergroundLogic.CABINET_HOLDS[c] == k)
		n += int(k == UndergroundLogic.DESK_KEY and s["desk_hook"])
		n += int(k == UndergroundLogic.OFFICE_KEY and s["office_key"])
		if n != 1:
			return "%s in %d places" % [k, n]
	for c in 3:
		if not s["iso"][c] and s["cab_in"][c] != UndergroundLogic.CABINET_TAKES[c]:
			return "isolator %d OFF without its key" % c
		if s["iso"][c] and not s["cab_held"][c]:
			return "isolator %d ON without its held key" % c
	if s["office_open"] and not s["office_key"]:
		return "office open without the key"
	# tubes: all seven, once each
	var tubes: Array = (s["tubes"] as Array).filter(func(t: Variant) -> bool: return int(t) != 0)
	if int(s["tube_hand"]) != 0:
		tubes.append(int(s["tube_hand"]))
	tubes.sort()
	if str(tubes) != str([1, 2, 3, 4, 5, 6, 7]):
		return "tubes %s" % str(tubes)
	# the one seed in play (or the crystal grown from it) is in exactly one place
	var seed_objs := int(l.has_item("seed_crystal")) + int(l.has_item("cloudy_crystal")) \
		+ int(l.has_item("nursery_crystal")) + int(s["chamber"] != "") + int(s["cradle"] != "") + int(s["socket_42"] != "")
	if seed_objs != (1 if int(s["seed_from"]) >= 0 else 0):
		return "seed objects %d for seed_from %d" % [seed_objs, int(s["seed_from"])]
	if s["crystal_grown"] and not (l.has_item("nursery_crystal") or s["chamber"] == "clear"
			or s["cradle"] == "nursery_crystal" or s["socket_42"] == "nursery_crystal"):
		return "Nursery crystal lost"
	if s["array_awake"] and not (s["hall_started"] and s["shutter_open"] and s["crystal_grown"]):
		return "Array awake too early"
	if s["drum_open"] and not s["gallery_awake"]:
		return "door open before the Gallery"
	if s["true_ending"] and not s["secret"]:
		return "secret without the profile"
	return ""


func test_random_play_never_softlocks() -> void:
	var rng := RandomNumberGenerator.new()
	var runs := 240
	var completed := 0
	var deep := 0 # runs whose random play itself got past the Gallery's drum lock
	for seed in runs:
		rng.seed = 9000 + seed
		var l := UndergroundLogic.new()
		l.setup_from_profile({"ch2_key": "strand_key" if seed % 2 == 0 else "leyla_key",
			"ch1_lens": "take_lens" if seed % 4 < 2 else "leave_lens",
			"ch1_shards": 5 if seed % 3 == 0 else 2, "ch2_echoes": 3})
		var steps := rng.randi_range(50, 1500)
		var bad := ""
		for _i in steps:
			random_action(l, rng)
			bad = invariants(l)
			if bad != "":
				break
		check(bad == "", "seed %d invariant: %s" % [seed, bad])
		deep += int(l.state["drum_open"])
		var copy := UndergroundLogic.new()
		copy.from_dict(JSON.parse_string(JSON.stringify(l.to_dict())))
		eq(JSON.stringify(copy.to_dict()), JSON.stringify(l.to_dict()), "seed %d save round trip" % seed)
		if UndergroundSolver.solve(copy, "strand" if seed % 5 == 0 else "leyla"):
			completed += 1
		else:
			check(false, "seed %d: unsolvable after random play; goal=%s state=%s inv=%s" % [seed, copy.hint_goal(), str(copy.state), str(copy.inventory)])
	eq(completed, runs, "every random state remains completable")
	check(deep >= runs / 10, "random play reaches the second wing often enough (%d of %d)" % [deep, runs])


func test_hint_goal_always_listed() -> void:
	var rng := RandomNumberGenerator.new()
	for seed in 40:
		rng.seed = 400 + seed
		var l := UndergroundLogic.new()
		l.setup_from_profile({"ch2_key": "strand_key" if seed % 2 == 0 else "leyla_key"})
		for _i in 600:
			random_action(l, rng)
			var g := l.hint_goal()
			if g != "done" and not UndergroundLogic.GOALS.has(g):
				check(false, "seed %d: unknown goal %s" % [seed, g])
				break
