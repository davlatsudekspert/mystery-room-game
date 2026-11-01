class_name ArchiveExpData
extends RefCounted
## Chapter 2 expansion "The Whole Building" (docs/CHAPTER2_EXPANSION.md): pure data, variant pools, generators and
## brute-force verifiers for N1-N10. No scene access, no state. ArchiveLogic keeps the state and the actions and
## calls these helpers; the tests call the verifiers over many seeds.

# ------------------------------------------------------------------ seed streams
## Every puzzle draws from its own stream (game seed xor a constant), so adding or changing one never moves another
## puzzle's variant, and no existing Chapter 2 answer of an existing seed moves (docs/VARIANTS.md).
const SALT_PANEL := 0x2A5F1
const SALT_PIPES := 0x2A5F2
const SALT_GLYPH := 0x2A5F3
const SALT_BAY := 0x2A5F4
const SALT_SYMBOLS := 0x2A5F5
const SALT_CHEST := 0x2A5F6
const SALT_LOAD := 0x2A5F7
const SALT_BOARD := 0x2A5F8
const SALT_PRINT := 0x2A5F9


static func stream(game_seed: int, salt: int) -> RandomNumberGenerator:
	var rng := RandomNumberGenerator.new()
	rng.seed = game_seed ^ salt
	return rng


# ------------------------------------------------------------------ rooms and floors
## id, floor, stage that introduces it, name key.
const ROOMS: Array[Dictionary] = [
	{"id": "hall", "floor": 0, "stage": 1, "name": "room2x.hall"},
	{"id": "pump", "floor": -1, "stage": 1, "name": "room2x.pump"},
	{"id": "cell", "floor": -1, "stage": 1, "name": "room2x.cell"},
	{"id": "cold", "floor": -1, "stage": 1, "name": "room2x.cold"},
	{"id": "gallery", "floor": 1, "stage": 2, "name": "room2x.gallery"},
	{"id": "plate", "floor": 1, "stage": 2, "name": "room2x.plate"},
	{"id": "office", "floor": 1, "stage": 2, "name": "room2x.office"},
]
const FLOORS: Array[int] = [-1, 0, 1]

## Open-thread pictograms (a thread is something seen that cannot be finished yet). id -> room it is seen in.
const THREADS: Array[Dictionary] = [
	{"id": "warm_panel", "room": "hall", "name": "thread2x.warm_panel"},
	{"id": "blocked_stair", "room": "hall", "name": "thread2x.blocked_stair"},
	{"id": "frozen_door", "room": "cell", "name": "thread2x.frozen_door"},
	{"id": "case_card", "room": "hall", "name": "thread2x.case_card"},
	{"id": "dead_lamp", "room": "hall", "name": "thread2x.dead_lamp"},
	{"id": "pass_door", "room": "gallery", "name": "thread2x.pass_door"},
	{"id": "cabinet_symbol", "room": "office", "name": "thread2x.cabinet_symbol"},
]
const MAX_OPEN_THREADS := 3

# ------------------------------------------------------------------ reaction moments (section 11)
## id -> {seconds, cue}. The scene plays them (Settings: Full / Soft = no sound sting / Off); the logic only says WHEN.
const MOMENTS := {
	"m1": {"seconds": 3.5, "cue": "lamp_dip", "caption": "cap2x.m1"},
	"m2": {"seconds": 4.0, "cue": "knocks", "caption": "cap2x.m2"},
	"m3": {"seconds": 4.0, "cue": "frost_steps", "caption": "cap2x.m3"},
	"m4": {"seconds": 9.0, "cue": "roll_call", "caption": "cap2x.m4"},
	"m5": {"seconds": 5.0, "cue": "steps_above", "caption": "cap2x.m5"},
	"m6": {"seconds": 5.0, "cue": "echo_chime", "caption": "cap2x.m6"},
}
## Events (the part before the first colon) that have a caption: cap2x.<event>. "tap" uses cap2x.tap_<kind>.
const CAPTION_EVENTS: Array[String] = ["panel_opened", "panel_cold", "n1_dial_wrong", "pump_opened", "pipes_hazard",
	"thawed", "need_mallet", "valves_locked_n2", "light_digits", "sheets_locked", "cold_frozen", "cold_opened", "clunk",
	"aisle_lore", "aisle_found", "cranks_locked", "need_aisle", "need_cloth", "band_clear", "frost_done", "chest_sealed",
	"chest_opened", "no_pressure", "weights_locked", "counter_heavy", "counter_light", "lift_balanced", "lift_stuck",
	"wedge_out", "board_wrong", "board_ok", "print_other", "print_ready", "cab_opened", "lamp_dead", "lamp_installed",
	"room_locked", "travel_refused", "trial_off", "bonus_echo"]
const BONUS_ECHOES: Array[String] = ["aisle", "office"]

# ------------------------------------------------------------------ N1 Warm Wall
const PANEL_LETTERS: Array[String] = ["A", "B", "C"]
## Receiver strength of the cell door per view (the rest comes from the panel the needle points at).
const CELL_DOOR_VIEWS := {"hall": 1, "east_south": 4, "stair": 1}


## Receiver strength on the three painted panels: 5 on the door's panel, 3 next to it, 2 on the far one.
static func panel_strength(panel: int, door_panel: int) -> int:
	return [5, 3, 2][clampi(absi(panel - door_panel), 0, 2)]


# ------------------------------------------------------------------ N2 Pipe routing
## Six verified graphs. Nodes: 0 source S (compressor stub), 1 coil C (Cold Store), 2 hazard H (vent to the hall),
## 3-5 junctions. Valve i opens edge i. Solved when S reaches C and not H. Each graph has exactly ONE solution with the
## fewest open valves (PIPE_MIN), brute force over 2^6 (ArchiveExpData.pipe_analyse, tested for every graph).
const PIPE_GRAPHS := [
	[[1, 2], [0, 2], [3, 5], [3, 4], [1, 3], [0, 5]],
	[[0, 3], [4, 5], [1, 4], [0, 2], [0, 5], [1, 2]],
	[[1, 5], [4, 5], [0, 2], [2, 3], [0, 4], [1, 3]],
	[[0, 3], [3, 4], [1, 4], [2, 5], [1, 2], [0, 5]],
	[[0, 4], [0, 2], [3, 4], [1, 5], [3, 5], [1, 2]],
	[[0, 2], [4, 5], [0, 5], [1, 2], [3, 4], [1, 3]],
]
const NODE_S := 0
const NODE_C := 1
const NODE_H := 2


## Nodes the pressure reaches from S with the valves in `mask` (bit i = valve i open).
static func pipe_reach(graph: Array, mask: int) -> Array[int]:
	var seen: Array[int] = [NODE_S]
	var changed := true
	while changed:
		changed = false
		for i in graph.size():
			if (mask >> i) & 1 == 1:
				var u := int(graph[i][0])
				var v := int(graph[i][1])
				if seen.has(u) != seen.has(v):
					seen.append(v if seen.has(u) else u)
					changed = true
	return seen


static func pipe_solves(graph: Array, mask: int) -> bool:
	var r := pipe_reach(graph, mask)
	return r.has(NODE_C) and not r.has(NODE_H)


## {"min": fewest valves of a solution, "masks": all fewest-valve solutions, "solutions": count of all solving masks,
## "hazard": masks that reach H}.
static func pipe_analyse(graph: Array) -> Dictionary:
	var best := 99
	var masks: Array[int] = []
	var n_sol := 0
	var haz := 0
	for m in 1 << graph.size():
		if pipe_reach(graph, m).has(NODE_H):
			haz += 1
		if pipe_solves(graph, m):
			n_sol += 1
			var k := _popcount(m)
			if k < best:
				best = k
				masks = [m]
			elif k == best:
				masks.append(m)
	return {"min": best, "masks": masks, "solutions": n_sol, "hazard": haz}


## The valves of the (unique) shortest solution, ascending.
static func pipe_solution(graph_index: int) -> Array[int]:
	var a := pipe_analyse(PIPE_GRAPHS[graph_index])
	var out: Array[int] = []
	var m := int((a["masks"] as Array)[0])
	for i in 6:
		if (m >> i) & 1 == 1:
			out.append(i)
	return out


## What a tap with the mallet on pipe segment `edge` sounds like: "full" (pressure in it), "cracked" (pressure in a
## pipe that touches the hazard vent) or "dead" (no pressure).
static func pipe_tap(graph: Array, mask: int, edge: int) -> String:
	if edge < 0 or edge >= graph.size() or (mask >> edge) & 1 == 0:
		return "dead"
	var r := pipe_reach(graph, mask)
	var u := int(graph[edge][0])
	var v := int(graph[edge][1])
	if not (r.has(u) and r.has(v)):
		return "dead"
	return "cracked" if u == NODE_H or v == NODE_H else "full"


static func _popcount(m: int) -> int:
	var n := 0
	while m > 0:
		n += m & 1
		m >>= 1
	return n


# ------------------------------------------------------------------ N3 Light table (M14)
const GRID := 11
const WIN_ROW0 := 2
const WIN_ROWS := 7
const GLYPH_DIGITS: Array[int] = [1, 2, 3, 4, 5, 7] # no 0, 6, 8, 9: rotation makes them ambiguous
## 5 x 7 digit font: 7 rows of 5 cells per digit ('#' = lit).
const DIGIT_ROWS := {
	0: [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
	1: ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
	2: [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
	3: [".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."],
	4: ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
	5: ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
	6: ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
	7: ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
	8: [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
	9: [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
}


## Lit cells of two digits in the 7 x 11 window (row-major, 77 cells): digit 1 in columns 0-4, a gap, digit 2 in 6-10.
static func glyph_window(d1: int, d2: int) -> PackedByteArray:
	var out := PackedByteArray()
	out.resize(WIN_ROWS * GRID)
	for r in WIN_ROWS:
		for c in 5:
			out[r * GRID + c] = 1 if (DIGIT_ROWS[d1][r] as String)[c] == "#" else 0
			out[r * GRID + 6 + c] = 1 if (DIGIT_ROWS[d2][r] as String)[c] == "#" else 0
	return out


## Turn an 11 x 11 sheet: mirror left-right if `flip` is 1, then rotate `rot` quarter turns clockwise.
static func sheet_transform(m: PackedByteArray, rot: int, flip: int) -> PackedByteArray:
	var cur := m.duplicate()
	if flip == 1:
		var f := PackedByteArray()
		f.resize(GRID * GRID)
		for r in GRID:
			for c in GRID:
				f[r * GRID + c] = cur[r * GRID + (GRID - 1 - c)]
		cur = f
	for _i in posmod(rot, 4):
		var t := PackedByteArray()
		t.resize(GRID * GRID)
		for r in GRID:
			for c in GRID:
				t[r * GRID + c] = cur[(GRID - 1 - c) * GRID + r]
		cur = t
	return cur


## The 77 window cells (rows WIN_ROW0 ..) of an 11 x 11 sheet.
static func window_of(m: PackedByteArray) -> PackedByteArray:
	return m.slice(WIN_ROW0 * GRID, (WIN_ROW0 + WIN_ROWS) * GRID)


## Light through the three sheets (each already turned): transparent on all three, window cells only.
static func light(a: PackedByteArray, b: PackedByteArray, c: PackedByteArray) -> PackedByteArray:
	var out := PackedByteArray()
	out.resize(WIN_ROWS * GRID)
	for i in WIN_ROWS * GRID:
		var k := WIN_ROW0 * GRID + i
		out[i] = 1 if (a[k] == 1 and b[k] == 1 and c[k] == 1) else 0
	return out


static func bits_to_string(m: PackedByteArray) -> String:
	var s := ""
	for v in m:
		s += "1" if v == 1 else "0"
	return s


static func string_to_bits(s: String) -> PackedByteArray:
	var out := PackedByteArray()
	out.resize(s.length())
	for i in s.length():
		out[i] = 1 if s[i] == "1" else 0
	return out


## All 100 two-digit light patterns (as strings), pair index d1 * 10 + d2: what counts as "legible".
static func legible_patterns() -> Dictionary:
	var out := {}
	for d1 in 10:
		for d2 in 10:
			out[bits_to_string(glyph_window(d1, d2))] = d1 * 10 + d2
	return out


## Scan the 8^3 orientations of three physical sheets. -> {"pairs": distinct legible pairs (d1*10+d2) lit by any
## orientation, "combos": number of orientation triples that light one}. A fair set has exactly the target pair.
static func scan_orientations(sheets: Array) -> Dictionary:
	var variants: Array = [] # [sheet][orientation] -> turned sheet
	for s: PackedByteArray in sheets:
		var v: Array = []
		for o in 8:
			v.append(sheet_transform(s, o & 3, o >> 2))
		variants.append(v)
	var legible := legible_patterns()
	var pairs := {}
	var combos := 0
	for o0 in 8:
		for o1 in 8:
			for o2 in 8:
				var key := bits_to_string(light(variants[0][o0], variants[1][o1], variants[2][o2]))
				if legible.has(key):
					pairs[int(legible[key])] = true
					combos += 1
	return {"pairs": pairs.keys(), "combos": combos}


## Orientation index o = rot + 4 * flip.
static func orient_index(rot: int, flip: int) -> int:
	return posmod(rot, 4) + 4 * clampi(flip, 0, 1)


## Generate this game's light table. -> {"digits": [d1, d2], "sheets": [3 strings of 121 cells], "target": [r0, f0, r1,
## f1, r2, f2] (the orientation that lights the digits), "start": [same layout, never solved]}. Deterministic in rng.
static func gen_light_table(rng: RandomNumberGenerator) -> Dictionary:
	for _attempt in 200:
		var d1: int = GLYPH_DIGITS[rng.randi_range(0, GLYPH_DIGITS.size() - 1)]
		var d2: int = GLYPH_DIGITS[rng.randi_range(0, GLYPH_DIGITS.size() - 1)]
		var glyph := glyph_window(d1, d2)
		# designed sheets: the glyph cells are clear on all three; every other window cell is blocked on 1 or 2 of them
		var designed: Array[PackedByteArray] = []
		for _i in 3:
			var p := PackedByteArray()
			p.resize(GRID * GRID)
			designed.append(p)
		var patterns: Array[int] = [1, 2, 4, 3, 5, 6]
		for r in GRID:
			for c in GRID:
				var k := r * GRID + c
				var in_win := r >= WIN_ROW0 and r < WIN_ROW0 + WIN_ROWS
				if in_win and glyph[(r - WIN_ROW0) * GRID + c] == 1:
					for i in 3:
						designed[i][k] = 1
				elif in_win:
					var mask: int = patterns[rng.randi_range(0, patterns.size() - 1)]
					for i in 3:
						designed[i][k] = 0 if (mask >> i) & 1 == 1 else 1
				else:
					for i in 3:
						designed[i][k] = rng.randi_range(0, 1)
		var target: Array[int] = []
		var start: Array[int] = []
		var physical: Array[PackedByteArray] = []
		for i in 3:
			var tr_rot := rng.randi_range(0, 3)
			var tr_flip := rng.randi_range(0, 1)
			var st_o := rng.randi_range(0, 7)
			if st_o == orient_index(tr_rot, tr_flip):
				st_o = (st_o + 1 + rng.randi_range(0, 6)) % 8
			# physical sheet B such that turning it by the target orientation gives the designed sheet
			var b := designed[i]
			for o in 8:
				var cand := sheet_transform(designed[i], o & 3, o >> 2)
				if sheet_transform(cand, tr_rot, tr_flip) == designed[i]:
					b = cand
					break
			physical.append(b)
			target.append_array([tr_rot, tr_flip])
			start.append_array([st_o & 3, st_o >> 2])
		var scan := scan_orientations(physical)
		if scan["pairs"] != [d1 * 10 + d2]:
			continue
		var lit0 := light(sheet_transform(physical[0], start[0], start[1]), sheet_transform(physical[1], start[2], start[3]),
			sheet_transform(physical[2], start[4], start[5]))
		if lit0 == glyph:
			continue
		return {"digits": [d1, d2], "sheets": [bits_to_string(physical[0]), bits_to_string(physical[1]),
			bits_to_string(physical[2])], "target": target, "start": start}
	return {}


# ------------------------------------------------------------------ N4 Carriage aisle
const CARRIAGES := 5
const AISLE_SLOTS := 7
const AISLE_MIN_ROUTE := 3


## All 21 arrangements: sorted slot of each of the five carriages (carriages never pass each other).
static func aisle_states() -> Array:
	var out: Array = []
	for a in AISLE_SLOTS:
		for b in range(a + 1, AISLE_SLOTS):
			for c in range(b + 1, AISLE_SLOTS):
				for d in range(c + 1, AISLE_SLOTS):
					for e in range(d + 1, AISLE_SLOTS):
						out.append([a, b, c, d, e])
	return out


## The arrangements one crank away: a carriage slides one slot into an adjacent free slot.
static func aisle_neighbours(pos: Array) -> Array:
	var out: Array = []
	for k in CARRIAGES:
		for d in [-1, 1]:
			var p: int = int(pos[k]) + d
			if p >= 0 and p < AISLE_SLOTS and not pos.has(p):
				var t := pos.duplicate()
				t[k] = p
				out.append(t)
	return out


## Solved when carriage `bay` (1-4) has a free slot directly in front of it, i.e. a gap between it and the carriage
## before it: an aisle opens left of the bay's carriage.
static func aisle_open_at(pos: Array, bay: int) -> bool:
	return bay >= 1 and bay < CARRIAGES and int(pos[bay]) - int(pos[bay - 1]) >= 2


## Fewest cranks from `pos` to an arrangement that opens the aisle of `bay`; -1 if unreachable.
static func aisle_distance(pos: Array, bay: int) -> int:
	var dist := {str(pos): 0}
	var queue: Array = [pos]
	var head := 0
	while head < queue.size():
		var u: Array = queue[head]
		head += 1
		if aisle_open_at(u, bay):
			return int(dist[str(u)])
		for v: Array in aisle_neighbours(u):
			if not dist.has(str(v)):
				dist[str(v)] = int(dist[str(u)]) + 1
				queue.append(v)
	return -1


## Every (bay, start) with a shortest route of at least AISLE_MIN_ROUTE cranks.
static func aisle_pool() -> Array:
	var out: Array = []
	for bay in range(1, CARRIAGES):
		for s: Array in aisle_states():
			if aisle_distance(s, bay) >= AISLE_MIN_ROUTE:
				out.append([bay, s])
	return out


## The cranks of a shortest route as [carriage, direction] pairs.
static func aisle_route(pos: Array, bay: int) -> Array:
	var prev := {}
	var move := {}
	var seen := {str(pos): true}
	var queue: Array = [pos]
	var head := 0
	while head < queue.size():
		var u: Array = queue[head]
		head += 1
		if aisle_open_at(u, bay):
			var path: Array = []
			var cur := u
			while str(cur) != str(pos):
				path.push_front(move[str(cur)])
				cur = prev[str(cur)]
			return path
		for k in CARRIAGES:
			for d in [-1, 1]:
				var p: int = int(u[k]) + d
				if p >= 0 and p < AISLE_SLOTS and not u.has(p):
					var t := u.duplicate()
					t[k] = p
					if not seen.has(str(t)):
						seen[str(t)] = true
						prev[str(t)] = u
						move[str(t)] = [k, d]
						queue.append(t)
	return []


# ------------------------------------------------------------------ N5/N6 symbols and chest rings
const SYMBOLS := 6 # the Chapter 3 drum set, drawn as art
const RINGS := 3
const CHEST_MIN := 4
const CHEST_MAX := 9


static func ring_press(rings: Array, i: int) -> Array:
	var r := rings.duplicate()
	r[i] = (int(r[i]) + 1) % SYMBOLS
	r[(i + 1) % RINGS] = (int(r[(i + 1) % RINGS]) + 1) % SYMBOLS
	return r


## Fewest presses (BFS) from `rings` to `target`; -1 if the target cannot be reached.
static func ring_distance(rings: Array, target: Array) -> int:
	var r := _ring_bfs(rings, target)
	return int(r["dist"])


## Shortest press sequence (ring indices); [] when already there or unreachable (see ring_distance).
static func ring_route(rings: Array, target: Array) -> Array:
	return _ring_bfs(rings, target)["path"]


static func _ring_bfs(rings: Array, target: Array) -> Dictionary:
	if rings == target:
		return {"dist": 0, "path": []}
	var prev := {}
	var move := {}
	var seen := {str(rings): true}
	var queue: Array = [rings]
	var head := 0
	while head < queue.size():
		var u: Array = queue[head]
		head += 1
		for i in RINGS:
			var v := ring_press(u, i)
			if seen.has(str(v)):
				continue
			seen[str(v)] = true
			prev[str(v)] = u
			move[str(v)] = i
			if v == target:
				var path: Array = []
				var cur := v
				while str(cur) != str(rings):
					path.push_front(move[str(cur)])
					cur = prev[str(cur)]
				return {"dist": path.size(), "path": path}
			queue.append(v)
	return {"dist": -1, "path": []}


## All starts that reach `target` in CHEST_MIN..CHEST_MAX presses, in a fixed order.
static func chest_starts(target: Array) -> Array:
	var out: Array = []
	for a in SYMBOLS:
		for b in SYMBOLS:
			for c in SYMBOLS:
				var s := [a, b, c]
				var d := ring_distance(s, target)
				if d >= CHEST_MIN and d <= CHEST_MAX:
					out.append(s)
	return out


## Press counts per ring of a shortest route: [n0, n1, n2].
static func ring_counts(rings: Array, target: Array) -> Array:
	var counts := [0, 0, 0]
	for i: int in ring_route(rings, target):
		counts[i] += 1
	return counts


# ------------------------------------------------------------------ N7 book-lift counterweight
const WEIGHTS: Array[int] = [1, 2, 4, 8]
## Loads 5-14 that are not a single weight.
const LOADS: Array[int] = [5, 6, 7, 9, 10, 11, 12, 13, 14]
const LIFT_FLOORS: Array[int] = [-1, 0, 1]


static func weights_sum(hung: Array) -> int:
	var s := 0
	for i in WEIGHTS.size():
		if int(hung[i]) == 1:
			s += WEIGHTS[i]
	return s


## The weights (as 0/1 per weight) that balance `load`.
static func weights_for(load: int) -> Array:
	var out: Array = []
	for i in WEIGHTS.size():
		out.append((load >> i) & 1)
	return out


# ------------------------------------------------------------------ N8 roll-call board
const TAGS := 6
const HOOKS := 6
const SLIP_END_L := 0 # tag a hangs on the first hook
const SLIP_END_R := 1 # tag a hangs on the last hook
const SLIP_LEFT := 2 # tag a hangs somewhere left of tag b
const SLIP_NEXT := 3 # tag a hangs next to tag b
const SLIP_NOT_END := 4 # tag a does not hang at either end
const MIN_SLIPS := 4
const MAX_SLIPS := 6


## Is slip [type, a, b] true when `hook_of[tag]` says where each tag hangs?
static func slip_true(slip: Array, hook_of: Array) -> bool:
	var a := int(slip[1])
	var b := int(slip[2])
	match int(slip[0]):
		SLIP_END_L:
			return int(hook_of[a]) == 0
		SLIP_END_R:
			return int(hook_of[a]) == HOOKS - 1
		SLIP_LEFT:
			return int(hook_of[a]) < int(hook_of[b])
		SLIP_NEXT:
			return absi(int(hook_of[a]) - int(hook_of[b])) == 1
		SLIP_NOT_END:
			return int(hook_of[a]) != 0 and int(hook_of[a]) != HOOKS - 1
	return false


static func all_permutations() -> Array:
	var out: Array = []
	_perm_rec([], [0, 1, 2, 3, 4, 5], out)
	return out


static func _perm_rec(prefix: Array, rest: Array, out: Array) -> void:
	if rest.is_empty():
		out.append(prefix)
		return
	for i in rest.size():
		var r := rest.duplicate()
		r.remove_at(i)
		_perm_rec(prefix + [rest[i]], r, out)


## hook_of[tag] for a board (board[hook] = tag).
static func hooks_of(board: Array) -> Array:
	var h: Array = [-1, -1, -1, -1, -1, -1]
	for hook in board.size():
		if int(board[hook]) >= 0:
			h[int(board[hook])] = hook
	return h


## How many full boards (of the 720) make every slip true.
static func count_solutions(slips: Array) -> int:
	var n := 0
	for board: Array in all_permutations():
		var h := hooks_of(board)
		var ok := true
		for s: Array in slips:
			if not slip_true(s, h):
				ok = false
				break
		if ok:
			n += 1
	return n


## The unique board for `slips`, or [] when there is none or more than one.
static func solve_slips(slips: Array) -> Array:
	var found: Array = []
	for board: Array in all_permutations():
		var h := hooks_of(board)
		var ok := true
		for s: Array in slips:
			if not slip_true(s, h):
				ok = false
				break
		if ok:
			found.append(board)
	return found[0] if found.size() == 1 else []


## Generate this game's board: -> {"board": [tag per hook], "slips": [[type, a, b], ...]} with exactly one board that
## satisfies all slips, MIN_SLIPS..MAX_SLIPS slips, at least one that fixes an end. Deterministic in rng.
static func gen_board(rng: RandomNumberGenerator) -> Dictionary:
	var perms := all_permutations()
	for _attempt in 300:
		var board: Array = [0, 1, 2, 3, 4, 5]
		for i in range(5, 0, -1):
			var j := rng.randi_range(0, i)
			var t: Variant = board[i]
			board[i] = board[j]
			board[j] = t
		var hook_of := hooks_of(board)
		# every slip that is true for this board
		var ends: Array = []
		var others: Array = []
		for a in TAGS:
			if int(hook_of[a]) == 0:
				ends.append([SLIP_END_L, a, 0])
			elif int(hook_of[a]) == HOOKS - 1:
				ends.append([SLIP_END_R, a, 0])
			else:
				others.append([SLIP_NOT_END, a, 0])
			for b in TAGS:
				if a == b:
					continue
				if int(hook_of[a]) < int(hook_of[b]):
					others.append([SLIP_LEFT, a, b])
				if a < b and absi(int(hook_of[a]) - int(hook_of[b])) == 1:
					others.append([SLIP_NEXT, a, b])
		_shuffle(others, rng)
		var slips: Array = [ends[rng.randi_range(0, ends.size() - 1)]]
		var alive := _alive(perms, slips)
		for s: Array in others:
			if alive.size() <= 1 or slips.size() >= MAX_SLIPS:
				break
			var next := _filter(alive, s)
			if next.size() < alive.size():
				slips.append(s)
				alive = next
		if alive.size() != 1:
			continue
		# pad to the minimum with further true slips, then drop any slip that is not needed (keeping the minimum)
		for s: Array in others:
			if slips.size() >= MIN_SLIPS:
				break
			if not slips.has(s):
				slips.append(s)
		var idx := slips.size() - 1
		while idx >= 1 and slips.size() > MIN_SLIPS:
			var trial := slips.duplicate()
			trial.remove_at(idx)
			if _alive(perms, trial).size() == 1:
				slips = trial
			idx -= 1
		return {"board": board, "slips": slips}
	return {}


static func _alive(perms: Array, slips: Array) -> Array:
	var out: Array = []
	for board: Array in perms:
		var h := hooks_of(board)
		var ok := true
		for s: Array in slips:
			if not slip_true(s, h):
				ok = false
				break
		if ok:
			out.append(board)
	return out


static func _filter(boards: Array, slip: Array) -> Array:
	var out: Array = []
	for board: Array in boards:
		if slip_true(slip, hooks_of(board)):
			out.append(board)
	return out


static func _shuffle(a: Array, rng: RandomNumberGenerator) -> void:
	for i in range(a.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var t: Variant = a[i]
		a[i] = a[j]
		a[j] = t


# ------------------------------------------------------------------ N9 enlarger and N10 cabinet
const STRIPS := 4
const ENL_ZOOM_STEPS := 5 # like the vault overlay's zoom (P12)
const ENL_FOCUS_STEPS := 9 # like the projector focus (P10)
const ENL_ZOOM_START := 0
const ENL_FOCUS_START := 0
const CABINET_WHEELS := 4
