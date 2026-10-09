class_name UndergroundLogic
extends RoomLogic
## Chapter 3 "The Underground Facility" — complete puzzle logic for Level −2: the Choir Hall (Strand's wing),
## the Nursery (Leyla's wing) and the Resonance Gallery between them. Puzzle data mirrors
## docs/CHAPTER3_DESIGN.md; the values the design left open are listed there under "Implementation data".
## Indices are 0-based: cabinets 0..2 = I..III, rack slots 0..6, bench places 7..9, drawers 0..11 row-major.

# ------------------------------------------------------------------ W1 / W1b trapped-key interlock
const KEYS: Array[String] = ["key_diamond", "key_triangle", "key_circle", "key_square"]
const DESK_KEY := "key_diamond" # hangs on the control desk hook
const OFFICE_KEY := "key_square"
const CABINET_TAKES: Array[String] = ["key_triangle", "key_diamond", "key_circle"] # lock face of I, II, III
const CABINET_HOLDS: Array[String] = ["key_circle", "key_triangle", "key_square"] # key behind the glass of I, II, III
# ------------------------------------------------------------------ W2 heart strip
const CASE_CODE: Array[int] = [4, 2, 6] # peaks inside the sun, moon and star brackets
const CASE_DIGITS := 10
# ------------------------------------------------------------------ W3 the Choir
const SLOTS := 7
const BENCH := 3
const TUBES_START: Array[int] = [4, 0, 7, 2, 0, 5, 0, 6, 1, 3] # meter reading per place (0 = empty)
const CHOIR_TARGET: Array[int] = [4, 6, 2, 7, 1, 5, 3] # the chalk staircase
# ------------------------------------------------------------------ W4 witness startup
const LEVERS := 5
const STARTUP: Array[int] = [4, 2, 5, 1, 3] # lever per counter step 1..5
const KNOB_POSITIONS := 4 # 0 ○ (off), 1 ▲, 2 ●, 3 ■
const KNOB_TARGET := 2
## What each crystal port sees of the 1979 operator: counter step -> lever. Port C also sees the knob.
const PORT_VIEWS := {"A": {2: 2, 4: 1}, "B": {1: 4, 5: 3}, "C": {3: 5}}
const KNOB_PORT := "C"
# ------------------------------------------------------------------ E1 seed library
## Hexagonal lattice glyphs: 6 edges clockwise from the top, "1" = notched edge. Turning a glyph a third
## of a turn clockwise shifts it by two edges (see rotate_glyph).
const SEED_GLYPHS: Array[String] = ["110110", "001101", "100100", "111100", "010110", "110000",
	"110100", "100101", "010100", "101010", "110101", "111000"]
const SEED_RIGHT := 6 # row 2, column 3 (3 rows x 4 columns)
const SEED_COLUMNS := 4
const SEED_SKETCH := "001101" # Leyla's log: the right glyph turned a third of a turn clockwise
# ------------------------------------------------------------------ E2 autoclave
const PEG_MAX := 6
const PEGS_START: Array[int] = [1, 1, 1]
const PEGS_TARGET: Array[int] = [5, 2, 4]
# ------------------------------------------------------------------ E3 prism fans
const PRISM_MIN := -2
const PRISM_MAX := 2
const PRISM_START := 2
const PRISM_P := 0
const PRISM_Q := -1
const RED := 1 # ▲
const GREEN := 2 # ●
const BLUE := 4 # ■
const P_BANDS: Array[int] = [RED, GREEN, BLUE] # left to right
const Q_BANDS: Array[int] = [BLUE, GREEN, RED] # mirrored
const RIMS: Array[int] = [RED | GREEN, RED | GREEN, BLUE] # yellow ▲●, yellow ▲●, blue ■
# ------------------------------------------------------------------ E4 Leyla's crystals
const FRAME_SIZES: Array[int] = [3, 4, 2, 1] # shutter frame place (left to right) -> size, 1 = smallest
const MELODY: Array[int] = [3, 1, 4, 2] # by size
# ------------------------------------------------------------------ H1 / H2 Gallery
const DRUM_SYMBOLS := 6 # 0 ☼, 1 ☾, 2 ✦, 3 ▲, 4 ●, 5 ■
const DRUM_TARGET: Array[int] = [1, 3, 2, 4] # wheels outer -> inner: ☾ ▲ ✦ ●
const FREQ_MIN := 1
const FREQ_MAX := 5
const FREQ_START := 1
const FREQ_X := 3
const FREQ_Y := 2
# ------------------------------------------------------------------ optional
const ECHOES: Array[String] = ["welder", "tech_a", "tech_b", "strand_rail"]
const ECHO_ZONE := {"welder": "choir", "tech_a": "nursery", "tech_b": "nursery", "strand_rail": "gallery"}
const CRYSTALS: Array[String] = ["crystal_lens", "nursery_crystal", "cloudy_crystal"]
const CHOICES: Array[String] = ["strand", "leyla"]

## spot -> item for the simple one-off pick-ups in Strand's office
const SPOTS := {"office_lamp": "ecg_strip", "office_letters": "strand_letters", "meter_case": "resonance_meter"}

const PUZZLE_IDS: Array[String] = ["interlock", "heart", "choir", "restore", "startup", "seed", "grow",
	"prisms", "melody", "rings", "resonance"]

## Hint goals (docs "Hint ladder"), prefixed "c3_" like Chapter 2. Text keys: hint.<goal>.1..3.
const GOALS: Array[String] = ["c3_interlock", "c3_heart", "c3_choir", "c3_restore", "c3_startup", "c3_seed",
	"c3_grow", "c3_prisms", "c3_melody", "c3_rings", "c3_resonance", "c3_finale"]
const CHOIR_GOALS: Array[String] = ["c3_interlock", "c3_heart", "c3_choir", "c3_restore", "c3_startup"]
const NURSERY_GOALS: Array[String] = ["c3_seed", "c3_grow", "c3_prisms", "c3_melody"]


func default_state() -> Dictionary:
	return {
		"entry": "nursery", # "choir" (Strand's key) | "nursery" (Leyla's key)
		"has_lens": false, # Chapter 1 "take the lens"
		"secret": false, # ch1_shards = 5 and ch2_echoes = 3: the 42nd socket glows
		"taken": {},
		"echo_guided": false, # leave path: Leyla's echo has shown the seed drawer
		# W1 / W1b
		"desk_hook": true,
		"iso": [true, true, true], # isolators I..III ON
		"cab_in": ["", "", ""], # key in each lock face
		"cab_held": [true, true, true], # each held key behind its glass
		"office_key": false, # the square key sits in the office door
		"office_open": false,
		"interlock_done": false,
		# W2
		"case_wheels": [0, 0, 0],
		"case_open": false,
		# W3
		"tubes": _plain(TUBES_START),
		"tube_hand": 0,
		"choir_tuned": false,
		# W4
		"desk_armed": false, # lockout cleared: every isolator back ON after the office was opened
		"levers": [0, 0, 0, 0, 0],
		"step": 0,
		"knob": 0,
		"hall_started": false,
		# E1 / E2
		"seed_drawer": -1, # open drawer
		"seed_from": -1, # drawer of the one seed in play (-1 = all seeds home)
		"seed_found": false,
		"chamber": "", # "" | "seed" | "clear" | "cloudy"
		"ac_closed": false,
		"pegs": _plain(PEGS_START),
		"crystal_grown": false,
		# E3 / E4
		"prism_p": PRISM_START,
		"prism_q": PRISM_START,
		"camp_open": false,
		"melody_input": [],
		"shutter_open": false,
		# Gallery
		"gallery_awake": false,
		"door_west_open": false,
		"door_east_open": false,
		"drums": [0, 0, 0, 0],
		"drum_open": false,
		"cradle": "",
		"freq_x": FREQ_START,
		"freq_y": FREQ_START,
		"array_awake": false,
		"socket_42": "",
		"true_ending": false,
		"echoes": [],
		"choice": "",
		"complete": false,
	}


func is_complete() -> bool:
	return state["complete"]


## No Chapter 2 save: Leyla's key (the Nursery), as the Chapter 2 epilogue points to her recorder.
func setup_from_profile(choices: Dictionary) -> void:
	state["entry"] = "choir" if str(choices.get("ch2_key", "")) == "strand_key" else "nursery"
	state["has_lens"] = str(choices.get("ch1_lens", "")) == "take_lens"
	state["secret"] = int(choices.get("ch1_shards", 0)) >= 5 and int(choices.get("ch2_echoes", 0)) >= 3
	inventory = ["strand_key" if state["entry"] == "choir" else "leyla_key"]
	if state["has_lens"]:
		inventory.append("crystal_lens")


# ================================================================== zones
func zone_open(zone: String) -> bool:
	match zone:
		"choir":
			return state["entry"] == "choir" or state["door_west_open"]
		"nursery":
			return state["entry"] == "nursery" or state["door_east_open"]
		"gallery":
			return state["gallery_awake"]
	return false


## The blast door that H1 opens: the one to the second wing.
func sealed_door() -> String:
	return "east" if state["entry"] == "choir" else "west"


func _wake_gallery_or_power(wing: String) -> void:
	if state["gallery_awake"]:
		_emit("console_power:" + wing)
	else:
		state["gallery_awake"] = true
		_emit("gallery_awake")


# ================================================================== pick-ups
func can_take(spot: String) -> bool:
	match spot:
		"desk_hook":
			return zone_open("choir") and state["desk_hook"]
		"office_lamp", "office_letters":
			return state["office_open"] and not state["taken"].get(spot, false)
		"meter_case":
			return state["office_open"] and state["case_open"] and not state["taken"].get(spot, false)
		"seed_drawer":
			var d := int(state["seed_drawer"])
			if not zone_open("nursery") or d < 0 or d == int(state["seed_from"]):
				return false
			return int(state["seed_from"]) < 0 or has_item("seed_crystal")
		"autoclave":
			return zone_open("nursery") and not state["ac_closed"] and state["chamber"] != ""
	return false


func take(spot: String) -> Array[String]:
	_begin()
	if not can_take(spot):
		_emit(_take_refusal(spot))
		return _end()
	match spot:
		"desk_hook":
			state["desk_hook"] = false
			_add_item(DESK_KEY)
		"seed_drawer":
			if has_item("seed_crystal"): # swap: the seed in hand goes home first
				_remove_item("seed_crystal")
				_emit("seed_returned:%d" % int(state["seed_from"]))
			state["seed_from"] = int(state["seed_drawer"])
			_add_item("seed_crystal")
			_emit("seed_taken:%d" % int(state["seed_from"]))
			if int(state["seed_from"]) == SEED_RIGHT and not state["seed_found"]:
				state["seed_found"] = true
				_emit("solved:seed")
		"autoclave":
			var item: String = {"seed": "seed_crystal", "clear": "nursery_crystal", "cloudy": "cloudy_crystal"}[state["chamber"]]
			state["chamber"] = ""
			_add_item(item)
			_emit("autoclave_emptied")
		_:
			state["taken"][spot] = true
			_add_item(SPOTS[spot])
	return _end()


func _take_refusal(spot: String) -> String:
	if spot == "seed_drawer" and zone_open("nursery") and int(state["seed_drawer"]) >= 0 \
			and int(state["seed_from"]) >= 0 and int(state["seed_drawer"]) != int(state["seed_from"]):
		return "seed_in_play" # one seed out at a time; this one is in the autoclave or grown into a crystal
	if spot == "autoclave" and zone_open("nursery") and state["ac_closed"] and state["chamber"] != "":
		return "autoclave_shut"
	return "nothing_happens"


# ================================================================== W1 / W1b interlock
func all_on() -> bool:
	return state["iso"][0] and state["iso"][1] and state["iso"][2]


## ON -> OFF needs the cabinet's own key in its lock face; OFF -> ON needs its held key back behind the glass.
func turn_isolator(n: int) -> Array[String]:
	_begin()
	if not zone_open("choir") or n < 0 or n > 2:
		_emit("nothing_happens")
		return _end()
	var iso: Array = state["iso"]
	if iso[n]:
		if state["cab_in"][n] != CABINET_TAKES[n]:
			_emit("isolator_no_key")
			return _end()
		iso[n] = false
		_emit("isolator_off:%d" % n)
		if int(state["step"]) > 0 or int(state["knob"]) != 0: # the desk dies: half a startup is lost
			_reset_desk()
			_emit("levers_dropped")
	else:
		if not state["cab_held"][n]:
			_emit("isolator_held_missing")
			return _end()
		iso[n] = true
		_emit("isolator_on:%d" % n)
		_check_desk_armed()
	return _end()


## slot "in" = the key in the lock face (free while ON), "held" = the key behind the glass (free while OFF).
func take_cabinet_key(n: int, slot: String) -> Array[String]:
	_begin()
	if not zone_open("choir") or n < 0 or n > 2 or not slot in ["in", "held"]:
		_emit("nothing_happens")
	elif slot == "in":
		if state["cab_in"][n] == "":
			_emit("nothing_happens")
		elif not state["iso"][n]:
			_emit("key_trapped")
		else:
			var key: String = state["cab_in"][n]
			state["cab_in"][n] = ""
			_add_item(key)
	else:
		if not state["cab_held"][n]:
			_emit("nothing_happens")
		elif state["iso"][n]:
			_emit("key_trapped")
		else:
			state["cab_held"][n] = false
			_add_item(CABINET_HOLDS[n])
	return _end()


func toggle_office() -> Array[String]:
	_begin()
	if not zone_open("choir"):
		_emit("nothing_happens")
	elif state["office_open"]:
		state["office_open"] = false
		_emit("office_closed")
	elif not state["office_key"]:
		_emit("office_locked")
	else:
		_open_office()
	return _end()


func take_office_key() -> Array[String]:
	_begin()
	if not zone_open("choir") or not state["office_key"]:
		_emit("nothing_happens")
	elif state["office_open"]:
		_emit("key_trapped") # trapped while the door stands open
	else:
		state["office_key"] = false
		_add_item(OFFICE_KEY)
	return _end()


func _open_office() -> void:
	state["office_open"] = true
	_emit("office_opened")
	if not state["interlock_done"]:
		state["interlock_done"] = true
		_emit("solved:interlock")


func _use_key(key: String, target: String) -> void:
	if not zone_open("choir"):
		_emit("nothing_happens")
		return
	if target.begins_with("cabinet_"):
		var n := int(target.substr(8))
		if n < 0 or n > 2 or not target.substr(8).is_valid_int():
			_emit("nothing_happens")
		elif key == CABINET_TAKES[n] and state["cab_in"][n] == "":
			_remove_item(key)
			state["cab_in"][n] = key
			_emit("key_in:%d" % n)
		elif key == CABINET_HOLDS[n] and not state["cab_held"][n]:
			_remove_item(key)
			state["cab_held"][n] = true
			_emit("key_back:%d" % n)
		else:
			_emit("key_wrong_lock")
	elif target == "office_door":
		if key != OFFICE_KEY:
			_emit("key_wrong_lock")
		elif not state["office_key"]:
			_remove_item(key)
			state["office_key"] = true
			_open_office()
		else:
			_emit("nothing_happens")
	elif target == "desk_hook" and key == DESK_KEY:
		_remove_item(key)
		state["desk_hook"] = true
		_emit("key_hung")
	else:
		_emit("nothing_happens")


func _check_desk_armed() -> void:
	if all_on() and state["interlock_done"] and not state["desk_armed"]:
		state["desk_armed"] = true
		_emit("desk_live")
		_emit("solved:restore")


# ================================================================== W2 heart strip / meter case
func turn_case_wheel(i: int, delta: int = 1) -> Array[String]:
	_begin()
	if not state["office_open"] or state["case_open"] or i < 0 or i > 2:
		_emit("nothing_happens")
		return _end()
	var w: Array = state["case_wheels"]
	w[i] = posmod(int(w[i]) + delta, CASE_DIGITS)
	_emit("case_wheel:%d:%d" % [i, int(w[i])])
	if _ints_eq(w, CASE_CODE):
		state["case_open"] = true
		_emit("case_opened")
		_emit("solved:heart")
	return _end()


## Tapping the latch: feedback only (the case opens by itself on the right code).
func try_case() -> Array[String]:
	_begin()
	_emit("case_locked" if state["office_open"] and not state["case_open"] else "nothing_happens")
	return _end()


# ================================================================== W3 the Choir
## Tap a rack slot (0..6) or bench place (7..9): lift, hang or swap with the tube in hand.
func tap_tube(pos: int) -> Array[String]:
	_begin()
	if not zone_open("choir") or pos < 0 or pos >= SLOTS + BENCH:
		_emit("nothing_happens")
		return _end()
	if state["choir_tuned"]:
		_emit("rack_locked")
		return _end()
	var t: Array = state["tubes"]
	var hand := int(state["tube_hand"])
	var here := int(t[pos])
	if hand == 0 and here == 0:
		_emit("nothing_happens")
		return _end()
	t[pos] = hand
	state["tube_hand"] = here
	if hand == 0:
		_emit("tube_lifted:%d" % pos)
	elif here == 0:
		_emit("tube_placed:%d" % pos)
	else:
		_emit("tube_swapped:%d" % pos)
	return _end()


## Strand's meter on a tube (pos -1 = the tube in hand): the needle reads 1..7 while it rings.
func measure_tube(pos: int) -> Array[String]:
	_begin()
	if not has_item("resonance_meter") or not zone_open("choir") or pos < -1 or pos >= SLOTS + BENCH:
		_emit("nothing_happens")
		return _end()
	var r := int(state["tube_hand"]) if pos == -1 else int(state["tubes"][pos])
	_emit("meter:%d" % r if r > 0 else "nothing_happens")
	return _end()


## Length of a tube in units 1..7 (the longest reads 1).
static func tube_length(reading: int) -> int:
	return 8 - reading


func rack() -> Array:
	return (state["tubes"] as Array).slice(0, SLOTS)


func strike_hammer() -> Array[String]:
	_begin()
	if not zone_open("choir"):
		_emit("nothing_happens")
	elif state["choir_tuned"]:
		_emit("choir_chord")
	elif _ints_eq(rack(), CHOIR_TARGET):
		state["choir_tuned"] = true
		_emit("choir_chord")
		_emit("solved:choir")
	else:
		_emit("choir_discord")
	return _end()


# ================================================================== W4 witness startup
func desk_live() -> bool:
	return state["desk_armed"] and all_on()


## Levers 1..5. The right lever for the counter's step goes down; any other trips the breaker.
func pull_lever(n: int) -> Array[String]:
	_begin()
	if not zone_open("choir") or n < 1 or n > LEVERS:
		_emit("nothing_happens")
	elif state["hall_started"]:
		_emit("hall_running")
	elif not desk_live():
		_emit("desk_dead")
	elif int(state["levers"][n - 1]) == 1:
		_emit("nothing_happens")
	elif int(state["step"]) >= LEVERS or STARTUP[int(state["step"])] != n:
		_trip()
	else:
		state["levers"][n - 1] = 1
		state["step"] = int(state["step"]) + 1
		_emit("lever:%d" % n)
		_emit("counter:%d" % int(state["step"]))
	return _end()


## The master knob. Reaching ● before all five levers (or with the Choir out of tune) trips the breaker.
func turn_knob(delta: int = 1) -> Array[String]:
	_begin()
	if not zone_open("choir"):
		_emit("nothing_happens")
		return _end()
	if state["hall_started"]:
		_emit("hall_running")
		return _end()
	if not desk_live():
		_emit("desk_dead")
		return _end()
	state["knob"] = posmod(int(state["knob"]) + delta, KNOB_POSITIONS)
	_emit("knob:%d" % int(state["knob"]))
	if int(state["knob"]) != KNOB_TARGET:
		return _end()
	if int(state["step"]) < LEVERS:
		_trip()
	elif not state["choir_tuned"]:
		_emit("choir_discord")
		_trip()
	else:
		_start_hall()
	return _end()


func _trip() -> void:
	_reset_desk()
	_emit("breaker_trip")


func _reset_desk() -> void:
	state["levers"] = [0, 0, 0, 0, 0]
	state["step"] = 0
	state["knob"] = 0


func _start_hall() -> void:
	state["hall_started"] = true
	_emit("hall_started")
	_emit("solved:startup")
	if not state["gallery_awake"]: # first wing: the west blast door opens onto the Gallery
		state["door_west_open"] = true
		_emit("blast_door_open:west")
	_wake_gallery_or_power("choir")
	_check_resonance()


# ================================================================== E1 seed library
func open_seed_drawer(i: int) -> Array[String]:
	_begin()
	if not zone_open("nursery") or i < 0 or i >= SEED_GLYPHS.size():
		_emit("nothing_happens")
		return _end()
	state["seed_drawer"] = -1 if int(state["seed_drawer"]) == i else i
	_emit("seed_drawer:%d" % int(state["seed_drawer"]))
	return _end()


## The camera arrived at a view. Leave path: Leyla's echo shows the right drawer once.
func look(view: String) -> Array[String]:
	_begin()
	if view == "seed_library" and zone_open("nursery") and not state["has_lens"] and not state["echo_guided"]:
		state["echo_guided"] = true
		_emit("leyla_echo:%d" % SEED_RIGHT)
	return _end()


## A glyph turned clockwise by `thirds` thirds of a turn.
static func rotate_glyph(glyph: String, thirds: int) -> String:
	var k := posmod(thirds * 2, 6)
	return glyph.substr(6 - k) + glyph.substr(0, 6 - k)


# ================================================================== E2 autoclave
func toggle_autoclave() -> Array[String]:
	_begin()
	if not zone_open("nursery"):
		_emit("nothing_happens")
	else:
		state["ac_closed"] = not state["ac_closed"]
		_emit("autoclave_closed" if state["ac_closed"] else "autoclave_opened")
	return _end()


func turn_peg(i: int, delta: int = 1) -> Array[String]:
	_begin()
	if not zone_open("nursery") or i < 0 or i > 2:
		_emit("nothing_happens")
		return _end()
	var p: Array = state["pegs"]
	p[i] = posmod(int(p[i]) - 1 + delta, PEG_MAX) + 1
	_emit("peg:%d:%d" % [i, int(p[i])])
	return _end()


func pull_start_lever() -> Array[String]:
	_begin()
	if not zone_open("nursery"):
		_emit("nothing_happens")
	elif not state["ac_closed"]:
		_emit("autoclave_not_closed")
	elif state["chamber"] == "":
		_emit("autoclave_empty")
	elif state["chamber"] != "seed":
		_emit("autoclave_full")
	elif int(state["seed_from"]) == SEED_RIGHT and _ints_eq(state["pegs"], PEGS_TARGET):
		state["chamber"] = "clear"
		_emit("grew:clear")
		if not state["crystal_grown"]:
			state["crystal_grown"] = true
			_emit("solved:grow")
	else:
		state["chamber"] = "cloudy"
		_emit("grew:cloudy")
	return _end()


## A cloudy crystal in the chamber melts back into its seed.
func remelt() -> Array[String]:
	_begin()
	if not zone_open("nursery") or state["chamber"] != "cloudy":
		_emit("nothing_happens")
	else:
		state["chamber"] = "seed"
		_emit("remelted")
	return _end()


# ================================================================== E3 prism fans
## Bands (RED | GREEN | BLUE) falling on receptors 0..2 for prism positions p, q.
static func receptor_light(p: int, q: int) -> Array[int]:
	var r: Array[int] = [0, 0, 0]
	for k in 3:
		if p + k >= 0 and p + k < 3:
			r[p + k] |= P_BANDS[k]
		if q + k >= 0 and q + k < 3:
			r[q + k] |= Q_BANDS[k]
	return r


static func seal_accepts(p: int, q: int) -> bool:
	var r := receptor_light(p, q)
	return r[0] == RIMS[0] and r[1] == RIMS[1] and r[2] == RIMS[2]


func turn_prism(which: String, delta: int) -> Array[String]:
	_begin()
	var key := "prism_" + which
	if not zone_open("nursery") or not which in ["p", "q"]:
		_emit("nothing_happens")
		return _end()
	state[key] = clampi(int(state[key]) + delta, PRISM_MIN, PRISM_MAX)
	_emit("prism:%s:%d" % [which, int(state[key])])
	var r := receptor_light(int(state["prism_p"]), int(state["prism_q"]))
	_emit("receptors:%d:%d:%d" % [r[0], r[1], r[2]])
	if not state["camp_open"] and seal_accepts(int(state["prism_p"]), int(state["prism_q"])):
		state["camp_open"] = true
		_emit("seal_open")
		_emit("recorder_clicks")
		_emit("solved:prisms")
	return _end()


# ================================================================== E4 Leyla's crystals
func play_recorder() -> Array[String]:
	_begin()
	_emit("recorder_play" if state["camp_open"] and zone_open("nursery") else "nothing_happens")
	return _end()


## Tap the crystal at frame place 0..3. A wrong note damps all four and resets the input.
func tap_crystal(pos: int) -> Array[String]:
	_begin()
	if not state["camp_open"] or not zone_open("nursery") or pos < 0 or pos >= FRAME_SIZES.size():
		_emit("nothing_happens")
		return _end()
	var size := FRAME_SIZES[pos]
	_emit("crystal_note:%d" % size)
	if state["shutter_open"]:
		return _end()
	var input: Array = state["melody_input"]
	if input.size() >= MELODY.size() or MELODY[input.size()] != size:
		state["melody_input"] = []
		_emit("crystals_damped")
		return _end()
	input.append(size)
	if input.size() == MELODY.size():
		state["melody_input"] = []
		state["shutter_open"] = true
		_emit("shutter_open")
		_emit("solved:melody")
		_wake_gallery_or_power("nursery")
		_check_resonance()
	return _end()


# ================================================================== H1 the Array's rings
func turn_drum(i: int, delta: int = 1) -> Array[String]:
	_begin()
	if not zone_open("gallery") or state["drum_open"] or i < 0 or i > 3:
		_emit("nothing_happens")
		return _end()
	var d: Array = state["drums"]
	d[i] = posmod(int(d[i]) + delta, DRUM_SYMBOLS)
	_emit("drum:%d:%d" % [i, int(d[i])])
	return _end()


func pull_drum_handle() -> Array[String]:
	_begin()
	if not zone_open("gallery") or state["drum_open"]:
		_emit("nothing_happens")
	elif not _ints_eq(state["drums"], DRUM_TARGET):
		_emit("drum_wrong")
	else:
		state["drum_open"] = true
		state["door_%s_open" % sealed_door()] = true
		_emit("blast_door_open:" + sealed_door())
		_emit("solved:rings")
	return _end()


# ================================================================== H2 half resonance
func turn_freq(axis: String, delta: int) -> Array[String]:
	_begin()
	var key := "freq_" + axis
	if not zone_open("gallery") or not axis in ["x", "y"]:
		_emit("nothing_happens")
		return _end()
	if state["array_awake"]:
		_emit("knobs_locked")
		return _end()
	state[key] = clampi(int(state[key]) + delta, FREQ_MIN, FREQ_MAX)
	_emit("freq:%s:%d" % [axis, int(state[key])])
	_check_resonance()
	return _end()


## The oscilloscope draws a figure only with the Choir running, the Nursery's light in and the crystal cradled.
func scope_live() -> bool:
	return state["hall_started"] and state["shutter_open"] and state["cradle"] == "nursery_crystal"


func _check_resonance() -> void:
	if state["array_awake"] or not scope_live():
		return
	if int(state["freq_x"]) == FREQ_X and int(state["freq_y"]) == FREQ_Y:
		state["array_awake"] = true
		_emit("array_awake")
		_emit("echoes_appear")
		_emit("solved:resonance")


func take_from_cradle() -> Array[String]:
	_begin()
	if not zone_open("gallery") or state["cradle"] == "":
		_emit("nothing_happens")
	else:
		_add_item(state["cradle"])
		state["cradle"] = ""
		_emit("cradle_emptied")
	return _end()


func take_from_socket_42() -> Array[String]:
	_begin()
	if not zone_open("gallery") or state["socket_42"] == "":
		_emit("nothing_happens")
	else:
		_add_item(state["socket_42"])
		state["socket_42"] = ""
		_emit("socket_emptied")
	return _end()


# ================================================================== using items on things
func use_item_on(item: String, target: String) -> Array[String]:
	_begin()
	if not has_item(item):
		_emit("nothing_happens")
		return _end()
	if item in KEYS:
		_use_key(item, target)
		return _end()
	match target:
		"cradle":
			_use_on_cradle(item)
		"socket_42":
			_use_on_socket(item)
		"seed_library":
			if item == "seed_crystal" and zone_open("nursery"):
				_remove_item(item)
				_emit("seed_returned:%d" % int(state["seed_from"]))
				state["seed_from"] = -1
			else:
				_emit("nothing_happens")
		"autoclave":
			if not item in ["seed_crystal", "cloudy_crystal"] or not zone_open("nursery"):
				_emit("nothing_happens")
			elif state["ac_closed"]:
				_emit("autoclave_shut")
			elif state["chamber"] != "":
				_emit("autoclave_full")
			else:
				_remove_item(item)
				state["chamber"] = "seed" if item == "seed_crystal" else "cloudy"
				_emit("autoclave_loaded")
		"lift_gate_west", "lift_gate_east":
			if not item in ["strand_key", "leyla_key"]:
				_emit("nothing_happens")
			elif (item == "strand_key") == (target == "lift_gate_west"):
				_emit("gate_open")
			else:
				_emit("gate_wrong_key")
		_:
			_emit("nothing_happens")
	return _end()


func _use_on_cradle(item: String) -> void:
	if not zone_open("gallery"):
		_emit("nothing_happens")
	elif state["cradle"] != "":
		_emit("cradle_full")
	elif item != "nursery_crystal":
		_emit("cradle_refused" if item in CRYSTALS or item == "seed_crystal" else "nothing_happens")
	else:
		_remove_item(item)
		state["cradle"] = item
		_emit("crystal_cradled")
		_check_resonance()


func _use_on_socket(item: String) -> void:
	if not zone_open("gallery"):
		_emit("nothing_happens")
	elif not state["secret"]:
		_emit("socket_dark")
	elif state["socket_42"] != "":
		_emit("nothing_happens")
	elif item != "nursery_crystal":
		_emit("socket_refused" if item in CRYSTALS or item == "seed_crystal" else "nothing_happens")
	else:
		_remove_item(item)
		state["socket_42"] = item
		_emit("crystal_socketed")
		if not state["true_ending"]:
			state["true_ending"] = true
			_emit("secret_echo")


# ================================================================== optional: kept echoes
func holds_crystal() -> bool:
	return selected in CRYSTALS


## Take path: visible while a crystal is held, in the echo's own zone. Both paths: visible through an
## inspection port (the ports are in the Choir Hall and show every kept moment on the floor).
func echo_visible(id: String, via_port: bool = false) -> bool:
	if not ECHO_ZONE.has(id):
		return false
	if via_port:
		return zone_open("choir")
	return state["has_lens"] and holds_crystal() and zone_open(ECHO_ZONE[id])


func release_echo(id: String, via_port: bool = false) -> Array[String]:
	_begin()
	var e: Array = state["echoes"]
	if e.has(id) or not echo_visible(id, via_port):
		_emit("nothing_happens")
		return _end()
	e.append(id)
	_emit("echo_released:" + id)
	if e.size() == ECHOES.size():
		_emit("all_echoes")
	return _end()


# ================================================================== finale
func choice_options() -> Array:
	return [["strand", "ui.trust_strand"], ["leyla", "ui.trust_leyla"]]


func choice_prompt_key() -> String:
	return "ui.choice_trust_prompt"


func choose_ending(option: String) -> Array[String]:
	_begin()
	if not state["array_awake"] or state["complete"] or not option in CHOICES:
		_emit("nothing_happens")
		return _end()
	state["choice"] = option
	state["complete"] = true
	_emit("choice:" + option)
	_emit("chapter_complete")
	return _end()


# ================================================================== chapter hooks
func puzzle_ids() -> Array[String]:
	return PUZZLE_IDS


func solved_count() -> int:
	var n := 0
	for f: String in ["interlock_done", "case_open", "choir_tuned", "desk_armed", "hall_started", "seed_found",
			"crystal_grown", "camp_open", "shutter_open", "drum_open", "array_awake"]:
		if state[f]:
			n += 1
	return n


func hint_goal() -> String:
	var first: String = state["entry"]
	var g := _wing_goal(first)
	if g != "":
		return g
	if not state["drum_open"]:
		return "c3_rings"
	g = _wing_goal("nursery" if first == "choir" else "choir")
	if g != "":
		return g
	if not state["array_awake"]:
		return "c3_resonance"
	if not state["complete"]:
		return "c3_finale"
	return "done"


func _wing_goal(wing: String) -> String:
	if wing == "choir":
		if state["hall_started"]:
			return ""
		if not state["choir_tuned"]:
			if not has_item("resonance_meter"):
				return "c3_heart" if state["office_open"] else "c3_interlock"
			return "c3_choir"
		if not state["interlock_done"]: # tuned by eye before ever opening the office
			return "c3_interlock"
		return "c3_startup" if desk_live() else "c3_restore"
	if not state["crystal_grown"]:
		return "c3_grow" if int(state["seed_from"]) == SEED_RIGHT else "c3_seed"
	if not state["camp_open"]:
		return "c3_prisms"
	if not state["shutter_open"]:
		return "c3_melody"
	return ""


## The order hint goals appear in for an entry wing ("choir" | "nursery").
static func goal_order(entry: String) -> Array[String]:
	var out: Array[String] = []
	out.append_array(CHOIR_GOALS if entry == "choir" else NURSERY_GOALS)
	out.append("c3_rings")
	out.append_array(NURSERY_GOALS if entry == "choir" else CHOIR_GOALS)
	out.append_array(["c3_resonance", "c3_finale"] as Array[String])
	return out


func collectibles() -> Array:
	return [(state["echoes"] as Array).size(), ECHOES.size(), "ui.echoes"]


func epilogue_keys() -> Array[String]:
	var out: Array[String] = ["epi3.strand" if state["choice"] == "strand" else "epi3.leyla"]
	if (state["echoes"] as Array).size() == ECHOES.size():
		out.append("epi3.echoes")
	if state["true_ending"]:
		out.append("epi3.secret")
	out.append("epi3.end")
	return out


func profile_choices() -> Dictionary:
	return {"ch3_trust": state["choice"], "ch3_echoes": (state["echoes"] as Array).size(),
		"ch3_true_ending": state["true_ending"]}


func item_desc_key(id: String) -> String:
	match id:
		"crystal_lens":
			return "item.crystal_lens.desc_recorded"
		"strand_key", "leyla_key":
			return "item.%s.desc3" % id
	return super(id)


func item_glows(id: String) -> bool:
	return id in ["crystal_lens", "nursery_crystal"]


func intro_keys() -> Array[String]:
	return ["intro3.strand_key" if state["entry"] == "choir" else "intro3.leyla_key", "intro3.2"]


func intro_caption_key() -> String:
	return "cap3.lift"


# ================================================================== helpers
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
