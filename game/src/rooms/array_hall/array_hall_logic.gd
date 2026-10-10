class_name ArrayHallLogic
extends RoomLogic
## Chapter 4 "The Experiment" — complete puzzle logic for the Array Hall: Panel 0, Strand's box, the Sun, the four
## rings, the Reliquary around the Core, the chronometer and the reversal of the Night of Silence. Puzzle data
## mirrors docs/CHAPTER4_DESIGN.md; the values the design left open are listed there under "Implementation data".
## Indices are 0-based: switches 0..4 = I..V, rings 0..3 = I..IV (outer -> inner), leaves 0..5, lines 0..3 =
## LOCK, LIGHT, ARRAY, VENT, chronometer minutes 0..7 = 03:10..03:17.

# ------------------------------------------------------------------ P1 Panel 0
const LINES := 4
const SWITCHES := 5
## Switch-major: PANEL[s * 4 + line] == 1 when switch s toggles that line. Rank 4 over GF(2): exactly two switch
## sets light every lamp ({I, II} and {IV, V}).
const PANEL: Array[int] = [1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1, 1, 0, 0]
## Chapter 1's Panel 7 matrix (LOCK, LIGHT, ARRAY, VENT), never drawn again here.
const CH1_PANEL: Array[int] = [1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1]
const ROMAN: Array[String] = ["I", "II", "III", "IV", "V"]
# ------------------------------------------------------------------ P2 Strand's box
const GEARS := 4
const GEAR_STEPS := 6
const BOX_START: Array[int] = [4, 1, 3, 5] # presses 2, 3, 0, 1
# ------------------------------------------------------------------ P3 / P4 the Sun
const GAP_MAX := 9
const GAP_START := 9
const GAP_TARGET := 4 # the needle sits in the green at 10 - gap
const ARC_COLD := 0
const ARC_SHORTED := 1
const ARC_LIT := 2
const ARC_OUT_GAP := 8 # gaps 8..9 snap the arc out
const LEAVES := 6
const IRIS_ORDER: Array[int] = [2, 5, 0, 4, 1, 3] # stack order, top -> bottom
# ------------------------------------------------------------------ P5 / P6 / P7 the Array
const RINGS := 4
const MARKS := 8 # floor marks 1..8 = positions 0..7; mark 1 (position 0) is under the catwalk hatches
const RINGS_START: Array[int] = [4, 2, 6, 1]
const ALIGN_TARGET: Array[int] = [2, 5, 7, 4] # the orrery: towers I-IV at marks 3 6 8 5
const TOWER_KEYS: Array[String] = ["tower_key_1", "tower_key_2", "tower_key_3", "tower_key_4"]
# ------------------------------------------------------------------ chronometer / P8 / P12
const MINUTES := 8 # 03:10 .. 03:17
const FLASH_MINUTE := 7 # the master lever, always 03:17
const NIGHT: Array[int] = [4, 5, 6] # minute of the Sun, the rings, the keeper (03:14, 03:15, 03:16)
const NIGHT_ACTS: Array[String] = ["sun", "rings", "keeper"]
const COLLAR_DIGITS := 10
# ------------------------------------------------------------------ P11 the held note
const KEEPER_MAX := 12
const NOTE_TARGET := 7
# ------------------------------------------------------------------ secret: the post station
const POST_DESTINATIONS := 6 # 0 director, 1 book, 2 flask (laboratories), 3 film, 4 letter, 5 lock (Chapter 2's dial)
const POST_LAB := 2
const POST_NUMBERS := 9
const POST_NUMBER := 7 # Laboratory 7
# ------------------------------------------------------------------ optional
const ECHOES: Array[String] = ["tech_panel", "tech_wheels", "clerk_post", "leyla_lift"]
const ECHO_ZONE := {"tech_panel": "panel", "tech_wheels": "bridge", "clerk_post": "watch", "leyla_lift": "lift"}
const CRYSTALS: Array[String] = ["crystal_lens"]
const CHOICES: Array[String] = ["take_lens", "leave_lens"]
const ENDINGS: Array[String] = ["dawn", "keeper", "true"]

## spot -> item for the one-off pick-ups
const SPOTS := {"box_log": "strand_log", "heart_watch": "pocket_watch", "heart_letter": "strand_last_letter",
	"heart_pawl": "reverse_pawl", "locker_note": "leyla_note_1998", "locker_parcel": "leyla_parcel"}

const PUZZLE_IDS: Array[String] = ["power", "box", "sun", "iris", "align", "keys", "cage", "collar", "lens",
	"pawl", "note", "reversal"]

## Hint goals (docs "Hint ladder"), prefixed "c4_". Text keys: hint.<goal>.1..3.
const GOALS: Array[String] = ["c4_power", "c4_box", "c4_sun", "c4_iris", "c4_align", "c4_keys", "c4_cage",
	"c4_collar", "c4_lens", "c4_pawl", "c4_note", "c4_reversal", "c4_finale"]


func default_state() -> Dictionary:
	return {
		"entry": "leyla", # "strand" (Strand's key) | "leyla" (Leyla's key, or no Chapter 2 save)
		# this game's answers (docs/VARIANTS.md); seed 0 = the canonical ones below
		"seed": 0,
		"v_panel": _plain(PANEL),
		"v_box": _plain(BOX_START),
		"v_gap": GAP_TARGET,
		"v_iris": _plain(IRIS_ORDER),
		"v_rings": _plain(RINGS_START),
		"v_align": _plain(ALIGN_TARGET),
		"v_night": _plain(NIGHT),
		"v_note": NOTE_TARGET,
		"has_lens": false, # Chapter 1 "take the lens"
		"trust_strand": false, # Chapter 3 "trust Strand"
		"secret": false, # Chapter 3 true-ending flag: Leyla's parcel waits in locker 17
		"all_earlier": false, # shards 5, Ch2 echoes 3, Ch3 echoes 4
		"taken": {},
		# gates opened by the carried key before power
		"booth_gate": false,
		"watch_gate": false,
		# P1
		"switches": [false, false, false, false, false],
		"power": false,
		# P2
		"box": _plain(BOX_START),
		"box_open": false,
		# P3 / P4
		"sun_lever": false,
		"gap": GAP_START,
		"arc": ARC_COLD,
		"sun_done": false,
		"iris_up": [false, false, false, false, false, false],
		"iris_open": false,
		# P5 / P6 / P7
		"rings": _plain(RINGS_START),
		"align_done": false, # the hall has replayed at least once
		"tower_keys": [true, true, true, true], # key still in its tower's bracket
		"gates": [false, false, false, false],
		"cage_open": false,
		# chronometer
		"wheel": FLASH_MINUTE,
		# P8
		"collar": [0, 0, 0, 0],
		"tower_open": false,
		# P9 / P10
		"lens_seated": false,
		"lens_by_leyla": false, # leave path: Leyla's echo seated it
		"heart_open": false,
		"pawl_fitted": false,
		# P11
		"keeper": 0,
		"note_done": false,
		# P12
		"master_up": false,
		"reversing": false,
		"night_undone": false,
		# secret
		"post_dial": 0,
		"post_number": 1,
		"canister": "",
		"parcel_sent": false,
		# optional and story beats
		"echoes": [],
		"looked_core": false,
		"choice": "",
		"complete": false,
	}


func is_complete() -> bool:
	return state["complete"]


## No earlier save: Leyla's key, the leave path, Leyla trusted, no secret (the same defaults Chapters 2 and 3 use).
func setup_from_profile(choices: Dictionary) -> void:
	state["entry"] = "strand" if str(choices.get("ch2_key", "")) == "strand_key" else "leyla"
	state["has_lens"] = str(choices.get("ch1_lens", "")) == "take_lens"
	state["trust_strand"] = str(choices.get("ch3_trust", "")) == "strand"
	state["secret"] = _truthy(choices.get("ch3_true_ending", false))
	state["all_earlier"] = _num(choices.get("ch1_shards", 0)) >= 5 and _num(choices.get("ch2_echoes", 0)) >= 3 \
		and _num(choices.get("ch3_echoes", 0)) >= 4
	inventory = ["strand_key" if state["entry"] == "strand" else "leyla_key"]
	if state["has_lens"]:
		inventory.append("crystal_lens")


## Profile values may come back from JSON as bools, numbers or strings.
static func _truthy(v: Variant) -> bool:
	match typeof(v):
		TYPE_BOOL:
			return v
		TYPE_INT, TYPE_FLOAT:
			return float(v) != 0.0
		TYPE_STRING:
			return str(v).to_lower() in ["true", "1"]
	return false


static func _num(v: Variant) -> int:
	return int(v) if typeof(v) in [TYPE_INT, TYPE_FLOAT] else (int(str(v)) if str(v).is_valid_int() else 0)


# ================================================================== zones
func zone_open(zone: String) -> bool:
	match zone:
		"bridge", "panel", "lift":
			return true
		"booth":
			return state["power"] or state["booth_gate"]
		"watch":
			return state["power"] or state["watch_gate"]
		"apse", "floor":
			return state["power"]
		"tower":
			return state["tower_open"]
	return false


# ================================================================== pick-ups
func can_take(spot: String) -> bool:
	if spot.begins_with("tower_"):
		var n := _tower_index(spot)
		return n >= 0 and zone_open("floor") and int(state["rings"][n]) == 0 and state["tower_keys"][n]
	match spot:
		"box_log":
			return state["box_open"] and not state["taken"].get(spot, false)
		"heart_watch", "heart_letter", "heart_pawl":
			return state["heart_open"] and not state["taken"].get(spot, false)
		"locker_note":
			return zone_open("watch") and not state["taken"].get(spot, false)
		"locker_parcel":
			return zone_open("watch") and state["secret"] and not state["taken"].get(spot, false)
		"post_canister":
			return zone_open("watch") and state["canister"] != ""
	return false


func take(spot: String) -> Array[String]:
	_begin()
	if not can_take(spot):
		_emit(_take_refusal(spot))
		return _end()
	if spot.begins_with("tower_"):
		var n := _tower_index(spot)
		state["tower_keys"][n] = false
		_add_item(TOWER_KEYS[n])
		_emit("key_taken:%d" % n)
		if keys_taken() == RINGS:
			_emit("solved:keys")
	elif spot == "post_canister":
		var item: String = state["canister"]
		state["canister"] = ""
		_add_item(item)
		_emit("canister_emptied")
	else:
		state["taken"][spot] = true
		_add_item(SPOTS[spot])
	return _end()


func _take_refusal(spot: String) -> String:
	if spot.begins_with("tower_"):
		var n := _tower_index(spot)
		if n >= 0 and zone_open("floor") and state["tower_keys"][n]:
			return "tower_out_of_reach" # bring the tower under the hatch first
	elif spot == "locker_parcel" and zone_open("watch") and not state["secret"]:
		return "locker_bare"
	return "nothing_happens"


static func _tower_index(spot: String) -> int:
	var tail := spot.substr(6)
	if not tail.is_valid_int():
		return -1
	var n := int(tail) - 1
	return n if n >= 0 and n < RINGS else -1


func keys_taken() -> int:
	var n := 0
	for k in RINGS:
		if not state["tower_keys"][k]:
			n += 1
	return n


# ================================================================== P1 Panel 0
## Parity of each line under the switches that are up.
func lines() -> Array[int]:
	return panel_lines(state["v_panel"], state["switches"])


static func panel_lines(matrix: Array, switches: Array) -> Array[int]:
	var out: Array[int] = [0, 0, 0, 0]
	for s in SWITCHES:
		if switches[s]:
			for line in LINES:
				out[line] ^= int(matrix[s * LINES + line])
	return out


func all_lines_live() -> bool:
	return not lines().has(0)


func toggle_switch(i: int) -> Array[String]:
	_begin()
	if i < 0 or i >= SWITCHES:
		_emit("nothing_happens")
	elif state["power"]:
		_emit("switches_locked")
	else:
		state["switches"][i] = not state["switches"][i]
		_emit("switch:%d:%d" % [i, 1 if state["switches"][i] else 0])
		var l := lines()
		_emit("lamps:%d:%d:%d:%d" % [l[0], l[1], l[2], l[3]])
	return _end()


func pull_main() -> Array[String]:
	_begin()
	if state["power"]:
		_emit("hall_powered")
	elif not all_lines_live():
		_emit("lines_dead")
	else:
		state["power"] = true
		_emit("power_on")
		_emit("gates_release")
		_emit("solved:power")
	return _end()


## Every switch set that lights all four lamps (as arrays of switch indices). With rank 4 there are exactly two.
static func panel_solutions(matrix: Array) -> Array:
	var out: Array = []
	for mask in 1 << SWITCHES:
		var sw: Array = []
		for s in SWITCHES:
			sw.append((mask >> s) & 1 == 1)
		if not panel_lines(matrix, sw).has(0):
			var idx: Array = []
			for s in SWITCHES:
				if sw[s]:
					idx.append(s)
			out.append(idx)
	out.sort_custom(func(a: Array, b: Array) -> bool:
		return a.size() < b.size() if a.size() != b.size() else str(a) < str(b))
	return out


## The solution the hints name: fewest switches, then lexicographic.
func panel_solution() -> Array:
	var sols := panel_solutions(state["v_panel"])
	return sols[0] if not sols.is_empty() else []


## A matrix a game may draw: every switch feeds something, no switch feeds all four, every line is fed by at
## least two switches, rank 4 (so every lamp pattern is reachable and the all-live set is not unique by accident
## but always exactly two), and not Chapter 1's matrix.
static func panel_valid(matrix: Array) -> bool:
	if matrix.size() != SWITCHES * LINES or _ints_eq(matrix, CH1_PANEL):
		return false
	var rows: Array[int] = []
	for s in SWITCHES:
		var row := 0
		for line in LINES:
			row |= int(matrix[s * LINES + line]) << line
		if row == 0 or row == 15:
			return false
		rows.append(row)
	for line in LINES:
		var fed := 0
		for s in SWITCHES:
			fed += int(matrix[s * LINES + line])
		if fed < 2:
			return false
	return _rank_gf2(rows) == LINES


static func _rank_gf2(rows: Array[int]) -> int:
	var r: Array[int] = rows.duplicate()
	var rank := 0
	for bit in LINES:
		var pivot := -1
		for i in range(rank, r.size()):
			if (r[i] >> bit) & 1 == 1:
				pivot = i
				break
		if pivot < 0:
			continue
		var t: int = r[pivot]
		r[pivot] = r[rank]
		r[rank] = t
		for i in r.size():
			if i != rank and (r[i] >> bit) & 1 == 1:
				r[i] ^= r[rank]
		rank += 1
	return rank


# ================================================================== P2 Strand's box
## Knob i turns gear i and gear i + 1 one step of six; the last knob turns alone.
func press_knob(i: int) -> Array[String]:
	_begin()
	if not zone_open("booth") or i < 0 or i >= GEARS:
		_emit("nothing_happens")
	elif state["box_open"]:
		_emit("box_is_open")
	else:
		var g: Array = state["box"]
		g[i] = (int(g[i]) + 1) % GEAR_STEPS
		_emit("gear:%d:%d" % [i, int(g[i])])
		if i + 1 < GEARS:
			g[i + 1] = (int(g[i + 1]) + 1) % GEAR_STEPS
			_emit("gear:%d:%d" % [i + 1, int(g[i + 1])])
		if _all_zero(g):
			state["box_open"] = true
			_emit("box_open")
			_emit("solved:box")
	return _end()


## Presses per knob that bring every pointer to the mark from the current state (triangular, so unique).
func box_solution() -> Array:
	return coupled_solution(state["box"], [0, 0, 0, 0], GEAR_STEPS)


## Forward turns per wheel for a chain where wheel i moves element i and i + 1 (the last moves alone).
static func coupled_solution(current: Array, target: Array, steps: int) -> Array:
	var p: Array = current.duplicate()
	var out: Array = []
	for i in p.size():
		var x := posmod(int(target[i]) - int(p[i]), steps)
		out.append(x)
		p[i] = (int(p[i]) + x) % steps
		if i + 1 < p.size():
			p[i + 1] = (int(p[i + 1]) + x) % steps
	return out


# ================================================================== P3 / P4 the Sun
func sun_steady() -> bool:
	return int(state["arc"]) == ARC_LIT and int(state["gap"]) == gap_target()


## The ammeter: 0 cold, 10 shorted, 10 - gap while the arc burns. The green band sits at 10 - gap_target().
func needle() -> int:
	match int(state["arc"]):
		ARC_SHORTED:
			return 10
		ARC_LIT:
			return 10 - int(state["gap"])
	return 0


func toggle_sun_lever() -> Array[String]:
	_begin()
	if not zone_open("apse"):
		_emit("nothing_happens")
		return _end()
	if state["reversing"] and int(state["wheel"]) != m_sun():
		_emit("held_fast")
		return _end()
	var was := replay_live()
	state["sun_lever"] = not state["sun_lever"]
	if state["sun_lever"]:
		_emit("sun_lever:1")
		if int(state["gap"]) == 0:
			state["arc"] = ARC_SHORTED
			_emit("arc_shorted")
		else:
			state["arc"] = ARC_COLD
			_emit("rods_apart")
	else:
		state["arc"] = ARC_COLD
		_emit("sun_lever:0")
		_emit("sun_off")
	_emit("needle:%d" % needle())
	_light_changed(was)
	return _end()


## The feed wheel: rods together (0) short the lamp; backing off strikes the arc; too far (8, 9) snaps it out.
func turn_feed(delta: int) -> Array[String]:
	_begin()
	if not zone_open("apse"):
		_emit("nothing_happens")
		return _end()
	if state["reversing"] and int(state["wheel"]) != m_sun():
		_emit("held_fast")
		return _end()
	var was := replay_live()
	var prev := int(state["arc"])
	state["gap"] = clampi(int(state["gap"]) + delta, 0, GAP_MAX)
	var gap := int(state["gap"])
	_emit("gap:%d" % gap)
	var arc := ARC_COLD
	if state["sun_lever"]:
		if gap == 0:
			arc = ARC_SHORTED
		elif gap >= ARC_OUT_GAP:
			arc = ARC_COLD
		elif prev == ARC_SHORTED or prev == ARC_LIT:
			arc = ARC_LIT
	state["arc"] = arc
	if arc != prev:
		if arc == ARC_SHORTED:
			_emit("arc_shorted")
		elif arc == ARC_LIT:
			_emit("arc_struck")
		elif prev == ARC_LIT:
			_emit("arc_out")
	elif arc == ARC_COLD and state["sun_lever"]:
		_emit("rods_apart")
	_emit("needle:%d" % needle())
	if arc == ARC_LIT:
		if sun_steady():
			_emit("sun_steady")
			if not state["sun_done"]:
				state["sun_done"] = true
				_emit("solved:sun")
		else:
			_emit("sun_flicker")
	_light_changed(was)
	return _end()


## A leaf lifts only when every leaf above it in the stack is already up. Lifted leaves latch.
func lift_leaf(i: int) -> Array[String]:
	_begin()
	if not zone_open("apse") or i < 0 or i >= LEAVES:
		_emit("nothing_happens")
		return _end()
	if state["iris_open"] or state["iris_up"][i]:
		_emit("nothing_happens")
		return _end()
	var order: Array = iris_order()
	for j: Variant in order:
		if int(j) == i:
			break
		if not state["iris_up"][int(j)]:
			_emit("leaf_pinned:%d:%d" % [i, int(j)])
			return _end()
	var was := replay_live()
	state["iris_up"][i] = true
	_emit("leaf_up:%d" % i)
	if not (state["iris_up"] as Array).has(false):
		state["iris_open"] = true
		_emit("iris_open")
		_emit("solved:iris")
	_light_changed(was)
	return _end()


func beam_out() -> bool:
	return state["power"] and sun_steady() and state["iris_open"]


# ================================================================== P5 / P6 / P7 the Array
## Leading rings that stand at the orrery's marks: the beam reaches that many towers.
func folded() -> int:
	var t := align_target()
	for k in RINGS:
		if int(state["rings"][k]) != int(t[k]):
			return k
	return RINGS


func aligned() -> bool:
	return folded() == RINGS


## Every tower at mark 1, under the catwalk: the Night started here, and the reversal ends here.
func home() -> bool:
	return _all_zero(state["rings"])


## The hall replays while the Sun's beam is folded through all four towers into the Core.
func replay_live() -> bool:
	return beam_out() and aligned()


## Wheel i turns ring i and ring i + 1 (the inner neighbour) one mark; wheel IV turns the inner ring alone.
func turn_ring_wheel(i: int, delta: int) -> Array[String]:
	_begin()
	if i < 0 or i >= RINGS:
		_emit("nothing_happens")
		return _end()
	if not state["power"]:
		_emit("wheels_dead")
		return _end()
	if state["reversing"] and int(state["wheel"]) != m_rings():
		_emit("held_fast")
		return _end()
	var was := replay_live()
	var r: Array = state["rings"]
	r[i] = posmod(int(r[i]) + delta, MARKS)
	_emit("ring:%d:%d" % [i, int(r[i])])
	if i + 1 < RINGS:
		r[i + 1] = posmod(int(r[i + 1]) + delta, MARKS)
		_emit("ring:%d:%d" % [i + 1, int(r[i + 1])])
	_light_changed(was)
	return _end()


## Shortest signed turns per wheel that bring the rings to `target` (outer wheel first).
func ring_solution(target: Array) -> Array:
	var out: Array = coupled_solution(state["rings"], target, MARKS)
	for i in out.size():
		if int(out[i]) > MARKS / 2:
			out[i] = int(out[i]) - MARKS
	return out


## Beam and replay events after anything that moves light: the beam's reach, the replay's transitions and the
## first replay's story beats. While time runs back the figures follow the wheel instead.
func _light_changed(was_live: bool) -> void:
	var live := replay_live()
	if beam_out():
		_emit("beam:%d" % folded())
	if state["reversing"]:
		return
	if live and not was_live:
		_emit("replay_on")
		if not state["align_done"]:
			state["align_done"] = true
			_emit("solved:align")
			_emit("hall_replays")
			if state["trust_strand"]:
				_emit("guide_echo:strand")
	elif was_live and not live:
		_emit("replay_off")
	elif not live and beam_out() and home():
		_emit("replay_weak")


# ================================================================== chronometer
## The time wheel runs forward only (and round again) while the hall replays.
func scrub() -> Array[String]:
	_begin()
	if state["reversing"] or not replay_live():
		_emit("chrono_locked")
		return _end()
	state["wheel"] = (int(state["wheel"]) + 1) % MINUTES
	var m := int(state["wheel"])
	_emit("replay:%d" % m)
	if m == m_sun():
		_emit("replay_sun_lit")
	elif m == m_rings():
		_emit("replay_rings_set")
	elif m == m_keeper():
		_emit("replay_keeper_on")
	elif m == FLASH_MINUTE:
		_emit("replay_flash")
	return _end()


# ================================================================== P8 the collar
func collar_target() -> Array:
	return [0, 3, 1, m_sun()]


func turn_collar(i: int, delta: int = 1) -> Array[String]:
	_begin()
	if not state["cage_open"] or state["tower_open"] or i < 0 or i > 3:
		_emit("nothing_happens")
		return _end()
	var c: Array = state["collar"]
	c[i] = posmod(int(c[i]) + delta, COLLAR_DIGITS)
	_emit("collar:%d:%d" % [i, int(c[i])])
	if _ints_eq(c, collar_target()):
		_open_tower()
	return _end()


## Tapping the collar's latch: feedback only.
func try_collar() -> Array[String]:
	_begin()
	_emit("collar_shut" if state["cage_open"] and not state["tower_open"] else "nothing_happens")
	return _end()


func _open_tower() -> void:
	state["tower_open"] = true
	_emit("tower_open")
	_emit("solved:collar")
	if not state["has_lens"] and not state["lens_seated"] and not has_item("crystal_lens"):
		# leave path: Leyla steps out of the light and seats the lens you left for her
		state["lens_seated"] = true
		state["lens_by_leyla"] = true
		_emit("leyla_echo_lens")
		_seat_effects()


## The camera arrived at a view. The Leyla path: the forty-second light turns toward you once.
func look(view: String) -> Array[String]:
	_begin()
	if view == "core" and zone_open("floor") and not state["looked_core"]:
		state["looked_core"] = true
		if not state["trust_strand"]:
			_emit("forty_second_turns")
	return _end()


# ================================================================== P9 / P10 the heart
func _use_on_cradle(item: String) -> void:
	if not zone_open("tower"):
		_emit("nothing_happens")
	elif state["lens_seated"]:
		_emit("cradle_full")
	elif item != "crystal_lens":
		_emit("cradle_refused")
	else:
		_remove_item(item)
		state["lens_seated"] = true
		_emit("lens_seated")
		_seat_effects()


## The Core's light through the lens casts the recorded mark on the heart drawer's face: it opens.
func _seat_effects() -> void:
	_emit("mark_projected")
	if not state["heart_open"]:
		state["heart_open"] = true
		_emit("heart_open")
		_emit("solved:lens")


func take_lens() -> Array[String]:
	_begin()
	if not zone_open("tower") or not state["lens_seated"]:
		_emit("nothing_happens")
	elif state["reversing"]:
		_emit("held_fast")
	else:
		state["lens_seated"] = false
		_add_item("crystal_lens")
		_emit("lens_taken")
	return _end()


func _use_on_chronometer(item: String) -> void:
	if item != "reverse_pawl":
		_emit("nothing_happens")
	elif state["pawl_fitted"]:
		_emit("nothing_happens")
	else:
		_remove_item(item)
		state["pawl_fitted"] = true
		_emit("pawl_fitted")
		_emit("solved:pawl")


# ================================================================== P11 the held note
func keeper_on() -> bool:
	return int(state["keeper"]) == note_target()


## The keeper knob (0 off, 1..12). The beat against the Core's note slows as the knob nears it.
func turn_keeper(delta: int) -> Array[String]:
	_begin()
	if not state["power"]:
		_emit("desk_dead")
		return _end()
	if state["reversing"] and int(state["wheel"]) != m_keeper():
		_emit("held_fast")
		return _end()
	state["keeper"] = clampi(int(state["keeper"]) + delta, 0, KEEPER_MAX)
	var p := int(state["keeper"])
	_emit("keeper:%d" % p)
	if p == 0:
		_emit("keeper_off")
	else:
		_emit("beat:%d" % absi(p - note_target()))
		if p == note_target():
			_emit("keeper_on")
			if not state["note_done"]:
				state["note_done"] = true
				_emit("solved:note")
	return _end()


# ================================================================== P12 the reversal
func reversal_ready() -> bool:
	return state["pawl_fitted"] and state["lens_seated"] and keeper_on() and replay_live() \
		and int(state["wheel"]) == FLASH_MINUTE


## 03:17: lift the master lever. Only with the Night's configuration in place and the pawl fitted.
func lift_master() -> Array[String]:
	_begin()
	if not state["power"]:
		_emit("desk_dead")
	elif state["master_up"] or state["night_undone"]:
		_emit("nothing_happens")
	elif not reversal_ready():
		_emit("master_held")
	else:
		state["master_up"] = true
		state["reversing"] = true
		_emit("reversal_begins")
		_emit("figures_unfreeze")
	return _end()


## What must be undone at a minute before the wheel may leave it ("" = nothing).
func undo_at(minute: int) -> String:
	if minute == FLASH_MINUTE:
		return "master"
	var n := night()
	for a in NIGHT_ACTS.size():
		if int(n[a]) == minute:
			return NIGHT_ACTS[a]
	return ""


func undo_done(minute: int) -> bool:
	match undo_at(minute):
		"master":
			return state["master_up"]
		"keeper":
			return int(state["keeper"]) == 0
		"rings":
			return home()
		"sun":
			return not state["sun_lever"]
	return true


## Wind the chronometer back one minute. Leaving a minute whose step is still done snaps the Array to 03:17.
func wind_back() -> Array[String]:
	_begin()
	if not state["reversing"] or state["night_undone"]:
		_emit("chrono_locked")
		return _end()
	if not undo_done(int(state["wheel"])):
		_snap_back()
		return _end()
	state["wheel"] = int(state["wheel"]) - 1
	_emit("wound:%d" % int(state["wheel"]))
	if int(state["wheel"]) < first_minute():
		state["night_undone"] = true
		state["reversing"] = false
		_emit("night_undone")
		_emit("lights_rise")
		_emit("solved:reversal")
		if state["trust_strand"]:
			_emit("strand_stays")
		if state["parcel_sent"]:
			_emit("forty_second_rises")
	return _end()


## The Array holds: back to 03:17 with the Night's configuration. Nothing else changes and no item is lost.
func _snap_back() -> void:
	var was := replay_live()
	state["wheel"] = FLASH_MINUTE
	state["master_up"] = false
	state["reversing"] = false
	state["keeper"] = note_target()
	state["rings"] = align_target().duplicate()
	state["sun_lever"] = true
	state["gap"] = gap_target()
	state["arc"] = ARC_LIT
	_emit("snap_back")
	_light_changed(was)


# ================================================================== secret: the post station
func turn_post_dial(delta: int) -> Array[String]:
	_begin()
	if not zone_open("watch"):
		_emit("nothing_happens")
	else:
		state["post_dial"] = posmod(int(state["post_dial"]) + delta, POST_DESTINATIONS)
		_emit("post_dial:%d" % int(state["post_dial"]))
	return _end()


func turn_post_number(delta: int) -> Array[String]:
	_begin()
	if not zone_open("watch"):
		_emit("nothing_happens")
	else:
		state["post_number"] = posmod(int(state["post_number"]) - 1 + delta, POST_NUMBERS) + 1
		_emit("post_number:%d" % int(state["post_number"]))
	return _end()


func _use_on_canister(item: String) -> void:
	if not zone_open("watch"):
		_emit("nothing_happens")
	elif state["canister"] != "":
		_emit("canister_full")
	elif item != "leyla_parcel":
		_emit("nothing_happens")
	else:
		_remove_item(item)
		state["canister"] = item
		_emit("canister_loaded")


## While time runs back, the Institute's post runs too: Laboratory 7 is the flask and the 7.
func send_post() -> Array[String]:
	_begin()
	if not zone_open("watch"):
		_emit("nothing_happens")
	elif not state["power"]:
		_emit("station_dead")
	elif state["canister"] == "":
		_emit("canister_empty")
	elif not state["reversing"]:
		_emit("post_no_receiver")
	elif int(state["post_dial"]) != POST_LAB or int(state["post_number"]) != POST_NUMBER:
		_emit("post_returned")
	else:
		state["canister"] = ""
		state["parcel_sent"] = true
		_emit("parcel_sent")
	return _end()


# ================================================================== using items on things
func use_item_on(item: String, target: String) -> Array[String]:
	_begin()
	if not has_item(item):
		_emit("nothing_happens")
		return _end()
	match target:
		"booth_gate", "watch_gate":
			_use_gate_key(item, target)
		"cradle":
			_use_on_cradle(item)
		"chronometer":
			_use_on_chronometer(item)
		"post_canister":
			_use_on_canister(item)
		_:
			if target.begins_with("gate_"):
				_use_tower_key(item, target)
			else:
				_emit("nothing_happens")
	return _end()


## The carried Chapter 2 key opens its own gate before power: Strand's the booth, Leyla's the watch room.
func _use_gate_key(item: String, target: String) -> void:
	if not item in ["strand_key", "leyla_key"]:
		_emit("nothing_happens")
		return
	var own := "booth_gate" if item == "strand_key" else "watch_gate"
	if own != target:
		_emit("gate_wrong_key")
	elif state[target] or state["power"]:
		_emit("nothing_happens")
	else:
		state[target] = true
		_emit("gate_open:" + target.substr(0, target.length() - 5))


func _use_tower_key(item: String, target: String) -> void:
	var tail := target.substr(5)
	if not zone_open("floor") or not tail.is_valid_int() or not item in TOWER_KEYS:
		_emit("nothing_happens")
		return
	var n := int(tail) - 1
	if n < 0 or n >= RINGS:
		_emit("nothing_happens")
	elif state["gates"][n]:
		_emit("nothing_happens")
	elif TOWER_KEYS.find(item) != n:
		_emit("key_wrong_gate")
	else:
		_remove_item(item)
		state["gates"][n] = true
		_emit("gate_open:%d" % n)
		if not (state["gates"] as Array).has(false):
			state["cage_open"] = true
			_emit("cage_open")
			_emit("solved:cage")


# ================================================================== optional: kept echoes
func holds_crystal() -> bool:
	return selected in CRYSTALS


## Visible in its zone while a crystal is held, or while the hall replays (both paths).
func echo_visible(id: String) -> bool:
	if not ECHO_ZONE.has(id) or not zone_open(ECHO_ZONE[id]):
		return false
	return holds_crystal() or replay_live()


func release_echo(id: String) -> Array[String]:
	_begin()
	var e: Array = state["echoes"]
	if e.has(id) or not echo_visible(id):
		_emit("nothing_happens")
		return _end()
	e.append(id)
	_emit("echo_released:" + id)
	if e.size() == ECHOES.size():
		_emit("all_echoes")
	return _end()


# ================================================================== finale
func choice_options() -> Array:
	return [["take_lens", "ui.lens4_take"], ["leave_lens", "ui.lens4_leave"]]


func choice_prompt_key() -> String:
	return "ui.choice_lens4_prompt"


func choose_ending(option: String) -> Array[String]:
	_begin()
	if not state["night_undone"] or state["complete"] or not option in CHOICES:
		_emit("nothing_happens")
		return _end()
	if option == "take_lens" and state["lens_seated"]:
		state["lens_seated"] = false
		_add_item("crystal_lens")
	state["choice"] = option
	state["complete"] = true
	_emit("choice:" + option)
	_emit("chapter_complete")
	return _end()


## true: the parcel went to Laboratory 7; keeper: Strand (trusted in Chapter 3) stays; dawn otherwise.
func ending_id() -> String:
	if state["parcel_sent"]:
		return "true"
	if state["trust_strand"]:
		return "keeper"
	return "dawn"


# ================================================================== chapter hooks
func puzzle_ids() -> Array[String]:
	return PUZZLE_IDS


func solved_count() -> int:
	var n := 0
	for f: String in ["power", "box_open", "sun_done", "iris_open", "align_done", "cage_open", "tower_open",
			"heart_open", "pawl_fitted", "note_done", "night_undone"]:
		if state[f]:
			n += 1
	if keys_taken() == RINGS:
		n += 1
	return n


func hint_goal() -> String:
	if state["complete"]:
		return "done"
	if state["night_undone"]:
		return "c4_finale"
	if state["reversing"]:
		return "c4_reversal"
	if not state["power"]:
		return "c4_power"
	if not state["box_open"]:
		return "c4_box"
	if not state["sun_done"]:
		return "c4_sun"
	if not state["iris_open"]:
		return "c4_iris"
	if not state["align_done"]:
		return "c4_align"
	if keys_taken() < RINGS:
		return "c4_keys"
	if not state["cage_open"]:
		return "c4_cage"
	if not state["tower_open"]:
		return "c4_collar"
	if not state["lens_seated"]:
		return "c4_lens"
	if not state["pawl_fitted"]:
		return "c4_pawl"
	if not state["note_done"]:
		return "c4_note"
	return "c4_reversal"


## The order hint goals appear in; the leave path never shows c4_lens (Leyla seats it).
static func goal_order(has_lens: bool) -> Array[String]:
	var out: Array[String] = []
	for g in GOALS:
		if g != "c4_lens" or has_lens:
			out.append(g)
	return out


func collectibles() -> Array:
	return [(state["echoes"] as Array).size(), ECHOES.size(), "ui.echoes"]


func epilogue_keys() -> Array[String]:
	var ending := ending_id()
	var out: Array[String] = ["epi4." + ending]
	if ending == "true":
		if state["trust_strand"]:
			out.append("epi4.strand_stays")
		out.append("epi4.parcel")
	out.append("epi4.lens_taken" if state["choice"] == "take_lens" else "epi4.lens_left")
	if (state["echoes"] as Array).size() == ECHOES.size():
		out.append("epi4.echoes")
		if state["all_earlier"]:
			out.append("epi4.all_light")
	out.append("epi4.end")
	return out


func profile_choices() -> Dictionary:
	return {"ch4_ending": ending_id(), "ch4_lens": state["choice"], "ch4_echoes": (state["echoes"] as Array).size(),
		"ch4_parcel": state["parcel_sent"]}


func item_desc_key(id: String) -> String:
	match id:
		"crystal_lens":
			return "item.crystal_lens.desc_recorded"
		"strand_key", "leyla_key":
			return "item.%s.desc4" % id
	return super(id)


func item_glows(id: String) -> bool:
	return id == "crystal_lens"


func intro_keys() -> Array[String]:
	return ["intro4.strand_key" if state["entry"] == "strand" else "intro4.leyla_key", "intro4.2"]


func intro_caption_key() -> String:
	return "cap4.lift"


# ================================================================== per-game answers (docs/VARIANTS.md)
func gap_target() -> int:
	return int(state["v_gap"])


func iris_order() -> Array:
	return state["v_iris"]


func align_target() -> Array:
	return state["v_align"]


func night() -> Array:
	return state["v_night"]


func m_sun() -> int:
	return int(night()[0])


func m_rings() -> int:
	return int(night()[1])


func m_keeper() -> int:
	return int(night()[2])


## The minute before the earliest step of the Night: reaching it releases the light.
func first_minute() -> int:
	return mini(mini(m_sun(), m_rings()), m_keeper())


func note_target() -> int:
	return int(state["v_note"])


func apply_seed(game_seed: int) -> void:
	state["seed"] = game_seed
	if game_seed == 0:
		return
	var rng := RandomNumberGenerator.new()
	rng.seed = game_seed
	# P1: a rank-4 matrix (exactly two switch sets light every lamp)
	var matrix: Array = []
	while not panel_valid(matrix):
		matrix = []
		for _i in SWITCHES * LINES:
			matrix.append(rng.randi_range(0, 1))
	state["v_panel"] = matrix
	# P2: at least two pointers off the mark
	var box: Array = [0, 0, 0, 0]
	while box.count(0) > GEARS - 2:
		box = [rng.randi_range(0, 5), rng.randi_range(0, 5), rng.randi_range(0, 5), rng.randi_range(0, 5)]
	state["v_box"] = box
	state["box"] = box.duplicate()
	# P3 / P4
	state["v_gap"] = rng.randi_range(2, 6)
	state["v_iris"] = _shuffled(rng, [0, 1, 2, 3, 4, 5])
	# P5: towers never at mark 1 (so a key is never free while the beam is folded); the start is off by two or more
	var target: Array = [rng.randi_range(1, 7), rng.randi_range(1, 7), rng.randi_range(1, 7), rng.randi_range(1, 7)]
	var start: Array = target.duplicate()
	while _diff_count(start, target) < 2:
		start = [rng.randi_range(1, 7), rng.randi_range(1, 7), rng.randi_range(1, 7), rng.randi_range(1, 7)]
	state["v_align"] = target
	state["v_rings"] = start
	state["rings"] = start.duplicate()
	# P12: three distinct minutes 03:11..03:16 for the Sun, the rings and the keeper (the collar follows the Sun)
	state["v_night"] = _shuffled(rng, [1, 2, 3, 4, 5, 6]).slice(0, 3)
	# P11
	state["v_note"] = rng.randi_range(1, KEEPER_MAX)


static func _diff_count(a: Array, b: Array) -> int:
	var n := 0
	for i in a.size():
		if int(a[i]) != int(b[i]):
			n += 1
	return n


static func _shuffled(rng: RandomNumberGenerator, a: Array) -> Array:
	var out: Array = a.duplicate()
	for i in range(out.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var t: Variant = out[i]
		out[i] = out[j]
		out[j] = t
	return out


## Level-3 hints name this game's own answers.
func hint_args(goal: String, level: int) -> Array:
	if level < 3:
		return []
	match goal:
		"c4_power":
			return [", ".join(panel_solution().map(func(v: Variant) -> String: return ROMAN[int(v)]))]
		"c4_box":
			return box_solution().duplicate()
		"c4_sun":
			return [gap_target()]
		"c4_iris":
			return [", ".join(iris_order().map(func(v: Variant) -> String: return str(int(v) + 1)))]
		"c4_align":
			return [" ".join(align_target().map(func(v: Variant) -> String: return str(int(v) + 1)))]
		"c4_collar":
			return collar_target()
		"c4_note":
			return [note_target()]
		"c4_reversal":
			var order: Array = []
			for a in NIGHT_ACTS.size():
				order.append([int(night()[a]), NIGHT_ACTS[a]])
			order.sort_custom(func(x: Array, y: Array) -> bool: return int(x[0]) > int(y[0]))
			var out: Array = []
			for step: Array in order:
				out.append(int(step[0]))
				out.append(tr("hint.c4_act.%s" % str(step[1])))
			return out
	return []


static func _all_zero(a: Array) -> bool:
	for v: Variant in a:
		if int(v) != 0:
			return false
	return true


static func _ints_eq(a: Array, b: Array) -> bool:
	if a.size() != b.size():
		return false
	for i in a.size():
		if int(a[i]) != int(b[i]):
			return false
	return true


static func _plain(a: Array) -> Array:
	var out: Array = []
	out.append_array(a)
	return out
