class_name ArchiveLogic
extends RoomLogic
## Chapter 2 "The Missing Scientist" — complete puzzle logic for Records Archive B, the projection
## booth and the vault. Puzzle data mirrors docs/CHAPTER2_DESIGN.md (single source of truth).

const BADGE_NO := "0417"
const CAT_DRAWER := 4 # "04"
const CAT_GROUP := 1 # divider "1–"
const CAT_CARD := 7 # card "17"
const VALVE_POSITIONS := 5
const PRESSURE_TARGET := 5 # P = A + 2B
const FLOW_TARGET := 4 # F = 2A + C
const PUNCH_CODE: Array[int] = [1, 0, 1, 1, 0, 0, 1, 0]
## Index-card notch patterns for per-game variants (docs/VARIANTS.md); 0 is PUNCH_CODE. The art for pattern k is
## decals/ch2/index_card_p<k>.png (tools/textures/make_decals_ch2.py PUNCH_PATTERNS, same order).
const PUNCH_PATTERNS := [
	[1, 0, 1, 1, 0, 0, 1, 0], [0, 1, 1, 0, 1, 0, 0, 1], [1, 1, 0, 0, 0, 1, 1, 0], [1, 0, 0, 1, 1, 1, 0, 0],
	[0, 1, 0, 1, 0, 0, 1, 1], [0, 0, 1, 1, 1, 0, 1, 0], [1, 1, 0, 1, 0, 0, 0, 1], [0, 1, 1, 0, 0, 1, 0, 1],
]
const DEST_COUNT := 6 # 0 director, 1 stacks, 2 laboratories, 3 booth, 4 records office, 5 vault (sealed)
const DEST_STACKS := 1
const LOCKER_COUNT := 12
const LOCKER_LEYLA := 9
const SPEEDS: Array[String] = ["2.4", "4.75", "9.5", "19"]
const SPEED_START := 3
const SPEED_RIGHT := 1
const TAPES := {"tape_1996": 2, "tape_1997": 8, "tape_1998": 5} # reel -> clicks at the end
const BOOTH_CODE := "285" # clicks in the order the reels were made
const SPLICE_SHADOWS: Array[int] = [3, 1, 4, 2] # frame -> shadow length
const SPLICE_ORDER: Array[int] = [2, 0, 3, 1] # dawn (longest shadow) -> noon
const FILM_FRAMES := 6 # 0..4 story, 5 = Leyla's sign alone
const SIGN_FRAME := 5
const FOCUS_STEPS := 9
const FOCUS_START := 1
const FOCUS_SHARP := 5
const SLIDE_DRAWERS := 5
const SLIDE_MARK_DRAWER := 2 # ✦
const SLIDE_ROT_START := 1
const ROT_STEPS := 8
const ROT_LEFT_START := 2
const ROT_RIGHT_START := 5
const ROT_RIGHT_TARGET := 2
const ZOOM_STEPS := 5
const ZOOM_TARGET := 3
const WHEEL_TURNS := 3
const ECHOES: Array[String] = ["catalogue", "stacks", "booth"]
## The expansion (docs/CHAPTER2_EXPANSION.md): the stage a NEW game is built with. 0 = the 1.0 chapter, 1 = Stage A (lower
## floor, gate G1), 2 = Stage A + B (7 rooms, N1-N10, G1 + G2; owner decision 2026-11-01: update 1.1 ships both). Set it to
## 2 when the scene has the new rooms. Saves keep their own `exp_ver` / `stage`, so old saves always play the old flow.
const EXPANSION_STAGE := 0
const EXP_VER_LEGACY := 1
const EXP_VER_CURRENT := 2
const CRYSTALS: Array[String] = ["crystal_lens", "crystal_blank_1", "crystal_blank_2", "crystal_sign", "crystal_mark"]

## Receiver strength (0..5) per camera view for each hidden reel (docs P6 table).
const RECEIVER_TABLE := {
	"tape_1996": {"hall": 1, "west": 3, "catalogue": 4, "grille": 5, "stacks": 1, "lockers": 1},
	"tape_1997": {"hall": 2, "west": 2, "catalogue": 1, "stacks": 4, "ledger": 5, "reading": 2, "hatch": 1, "deck": 1},
	"tape_1998": {"hall": 2, "west": 1, "stacks": 2, "ledger": 1, "reading": 4, "hatch": 5, "lockers": 2, "deck": 1},
}

## spot -> item it yields, plus the state flag that must be true for the spot to be reachable
const SPOTS := {
	"index_card": {"item": "index_card", "needs": "card_shown"},
	"tray_card": {"item": "blank_card", "needs": ""},
	"canister_file": {"item": "personnel_file", "needs": "file_delivered"},
	"canister_key": {"item": "locker_key", "needs": "file_delivered"},
	"locker_receiver": {"item": "pocket_receiver", "needs": "locker_open"},
	"grille_reel": {"item": "tape_1996", "needs": "grille_open"},
	"ledger_reel": {"item": "tape_1997", "needs": "ledger_open"},
	"hatch_reel": {"item": "tape_1998", "needs": "hatch_open"},
	"splicer_reel": {"item": "film_reel", "needs": "reel_repaired"},
	"case_crystal_1": {"item": "crystal_blank_1", "needs": "booth_open"},
	"case_crystal_2": {"item": "crystal_blank_2", "needs": "booth_open"},
	"slide_mark": {"item": "emblem_slide", "needs": "slide_drawer_mark"},
	# the expansion
	"pump_mallet": {"item": "mallet", "needs": "pump_open"},
	"cell_cloth": {"item": "wipe_cloth", "needs": "pump_open"},
	"counter_slips": {"item": "roll_slips", "needs": "gallery_open"},
	"board_key": {"item": "pass_key", "needs": "board_ok"},
	"cabinet_lamp": {"item": "projector_lamp", "needs": "cab_open"},
}

const PUZZLE_IDS: Array[String] = ["catalogue", "compressor", "punch", "dispatch", "locker", "hunt",
	"tape", "booth", "splice", "projector", "record", "lock"]


func default_state() -> Dictionary:
	var on := EXPANSION_STAGE >= 1
	return {
		"taken": {},
		"has_lens": false, # Chapter 1 "take the lens": the crystal lens carries Strand's mark
		"ch1_shards": 0,
		"cat_drawer": -1,
		"cat_group": -1,
		"card_shown": false,
		"valves": [0, 0, 0],
		"pressure_ok": false,
		"card_in_punch": false,
		"punch_keys": [0, 0, 0, 0, 0, 0, 0, 0],
		"last_punch": [0, 0, 0, 0, 0, 0, 0, 0], # holes of the request card in play (for its picture)
		"request_ok": false, # the punched card in hand / canister carries the right pattern
		"canister": "", # "" | "request_card"
		"dest": 0,
		"file_delivered": false,
		"locker_open": false,
		"grille_open": false,
		"ledger_open": false,
		"hatch_open": false,
		"deck_speed": SPEED_START,
		"deck_tape": "",
		"clicks_heard": [], # tape ids heard clearly
		# this game's own answers (docs/VARIANTS.md); seed 0 = the canonical ones
		"seed": 0,
		"v_clicks": [2, 8, 5], # clicks at the end of the 1996, 1997, 1998 reels
		"v_shadows": SPLICE_SHADOWS.duplicate(), # film frame -> shadow length
		"v_focus": FOCUS_SHARP,
		"v_targets": [PRESSURE_TARGET, FLOW_TARGET], # green marks on gauges P and F
		"v_vault": [ROT_RIGHT_TARGET, ZOOM_TARGET], # the right image's rotation and zoom in the engraving
		"v_punch": 0, # index into PUNCH_PATTERNS (the notches on Leyla's index card)
		"dial_input": "",
		"booth_open": false,
		"splice": [-1, -1, -1, -1], # frame per slot
		"reel_repaired": false,
		"reel_on_projector": false,
		"projector_on": false,
		"film_seen": false,
		"frame": 0,
		"focus": FOCUS_START,
		"echo_guided": false,
		"slide_drawer": -1,
		"slide_drawer_mark": false,
		"slide_in": false,
		"slide_rot": SLIDE_ROT_START,
		"slide_on": false,
		"socket": "", # crystal seated in the screen socket
		"sign_recorded": false,
		"mark_recorded": false,
		"port_left": "",
		"port_right": "",
		"rot_left": ROT_LEFT_START,
		"rot_right": ROT_RIGHT_START,
		"zoom_right": 0,
		"vault_unlocked": false,
		"wheel": 0,
		"vault_open": false,
		"echoes": [],
		"choice": "",
		"complete": false,
		# --- the expansion (docs/CHAPTER2_EXPANSION.md section 10). Defaults are NEW-game values; ArchiveLogic.from_dict
		# turns a save without exp_ver into the old chapter.
		"exp_ver": EXP_VER_CURRENT if on else EXP_VER_LEGACY,
		"stage": EXPANSION_STAGE,
		"room": "hall",
		"rooms_seen": [], # rooms entered besides the hall
		"threads_seen": [],
		"moments_seen": [],
		"bonus_echoes": [],
		"mode": "normal", # "normal" | "trial"
		"trial_dropped": false,
		"crystal_home": "cold" if on else "case", # G1: where the blank crystals are
		"crystals_available": not on,
		"lamp_ok": EXPANSION_STAGE != 2, # G2: the projector lamp works (Stage A alone ships with it pre-satisfied)
		"lamp_seen": false,
		"panel_found": false, # N1
		"n1_dial": "",
		"pump_open": false,
		"pipes": [0, 0, 0, 0, 0, 0], # N2
		"thawed": false,
		"sheets": [0, 0, 0, 0, 0, 0], # N3: rotation, flip of each of the 3 sheets
		"cell_digits_ok": false,
		"cold_wheels": [0, 0],
		"cold_open": false,
		"aisle_pos": [0, 1, 2, 3, 4], # N4
		"crank_dir": [1, 1, 1, 1, 1],
		"aisle": false,
		"wiped": [0, 0, 0], # N5
		"frost_seen": false,
		"rings": [0, 0, 0], # N6
		"chest_open": false,
		"weights": [0, 0, 0, 0], # N7
		"lift_ok": false,
		"lift_floor": -1,
		"wedge_out": false,
		"board": [-1, -1, -1, -1, -1, -1], # N8: tag on each hook
		"board_ok": false,
		"pass_key": false,
		"en_strip": -1, # N9
		"en_zoom": 0,
		"en_focus": 0,
		"print_ok": false,
		"cab_wheels": [0, 0, 0, 0], # N10
		"cab_open": false,
		# this game's own expansion answers (separate seed streams, ArchiveExpData.SALT_*)
		"v_panel": 0,
		"v_pipes": 0,
		"v_glyph": [1, 2],
		"v_sheets": [], # 3 strings of 121 cells (11 x 11), the sheets as printed
		"v_sheet_target": [], # per sheet: rotation, flip that light the digits
		"v_bay": 1,
		"v_symbols": [0, 1, 2],
		"v_chest_start": [0, 0, 0],
		"v_load": 5,
		"v_board": [0, 1, 2, 3, 4, 5],
		"v_slips": [], # flat [type, a, b] triples
		"v_strips": [0, 1, 2, 3],
		"v_strip": 0,
		"v_zoom": 1,
		"v_pfocus": 4,
		"v_digits": [0, 0, 0, 0],
	}


func is_complete() -> bool:
	return state["complete"]


func setup_from_profile(choices: Dictionary) -> void:
	state["has_lens"] = str(choices.get("ch1_lens", "")) == "take_lens"
	state["ch1_shards"] = int(choices.get("ch1_shards", 0))
	inventory = ["leyla_badge"]
	if state["has_lens"]:
		inventory.append("crystal_lens")
	if exp_active():
		inventory.append("floor_plan") # the plan of the building, in the bag from the start


func reset() -> void:
	super()
	inventory = ["leyla_badge"]


# ================================================================== pick-ups
func can_take(spot: String) -> bool:
	if not SPOTS.has(spot):
		return false
	if spot == "tray_card": # an endless stack, but one card in play at a time
		return _no_card_anywhere()
	if state["taken"].get(spot, false):
		return false
	return _need_ok(spot, SPOTS[spot]["needs"])


func take(spot: String) -> Array[String]:
	_begin()
	if can_take(spot):
		if spot != "tray_card": # the tray holds an endless stack of blank request cards
			state["taken"][spot] = true
		_add_item(SPOTS[spot]["item"])
		_on_taken(spot)
		if spot == "index_card":
			_emit("solved:catalogue")
	else:
		_emit("nothing_happens")
	return _end()


func _no_card_anywhere() -> bool:
	return not (has_item("blank_card") or has_item("request_card") or state["card_in_punch"]
		or state["canister"] != "" or state["file_delivered"])


# ================================================================== variants (docs/VARIANTS.md)
const TAPE_ORDER: Array[String] = ["tape_1996", "tape_1997", "tape_1998"]


func apply_seed(seed: int) -> void:
	state["seed"] = seed
	if exp_active():
		_apply_exp_seed(seed) # its own streams: no 1.0 answer of any seed moves
	if seed == 0:
		return # the canonical answers from default_state()
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var clicks: Array = []
	for i in 3:
		clicks.append(rng.randi_range(1, 9))
	state["v_clicks"] = clicks
	var shadows: Array = [1, 2, 3, 4]
	for i in range(3, 0, -1): # Fisher-Yates with our own rng, so a seed always gives the same order
		var j := rng.randi_range(0, i)
		var t: Variant = shadows[i]
		shadows[i] = shadows[j]
		shadows[j] = t
	state["v_shadows"] = shadows
	state["v_focus"] = rng.randi_range(3, FOCUS_STEPS - 2) # never the start mark, never an end stop
	var pool := valve_target_pool()
	state["v_targets"] = pool[rng.randi_range(0, pool.size() - 1)]
	state["v_punch"] = rng.randi_range(1, PUNCH_PATTERNS.size() - 1)
	var rots: Array = [1, 2, 3, 4, 6, 7] # never the start position (5), never upright (0)
	state["v_vault"] = [rots[rng.randi_range(0, rots.size() - 1)], rng.randi_range(1, ZOOM_STEPS - 1)]


func clicks_for(tape: String) -> int:
	var i := TAPE_ORDER.find(tape)
	return int(state["v_clicks"][i]) if i >= 0 else 0


func booth_code() -> String:
	var code := ""
	for c: Variant in state["v_clicks"]:
		code += str(int(c))
	return code


## Frames in slot order: the longest shadow (dawn) first.
func splice_order() -> Array:
	var order: Array = [0, 1, 2, 3]
	order.sort_custom(func(a: int, b: int) -> bool: return int(state["v_shadows"][a]) > int(state["v_shadows"][b]))
	return order


func punch_code() -> Array:
	return PUNCH_PATTERNS[clampi(int(state["v_punch"]), 0, PUNCH_PATTERNS.size() - 1)]


func focus_sharp() -> int:
	return int(state["v_focus"])


func vault_rot_target() -> int:
	return int(state["v_vault"][0])


func vault_zoom_target() -> int:
	return int(state["v_vault"][1])


## The unique valve setting for this game's gauge marks.
func valve_solution() -> Array:
	var p := int(state["v_targets"][0])
	var f := int(state["v_targets"][1])
	for a in VALVE_POSITIONS:
		for b in VALVE_POSITIONS:
			for c in VALVE_POSITIONS:
				if a + 2 * b == p and 2 * a + c == f:
					return [a, b, c]
	return []


## Gauge marks (P, F) with exactly one valve solution, at least two valves turned, and not met at the start.
static func valve_target_pool() -> Array:
	var out: Array = []
	for p in 13:
		for f in 13:
			var sols: Array = []
			for a in VALVE_POSITIONS:
				for b in VALVE_POSITIONS:
					for c in VALVE_POSITIONS:
						if a + 2 * b == p and 2 * a + c == f:
							sols.append([a, b, c])
			if sols.size() == 1 and (p > 0 or f > 0):
				var sol: Array = sols[0]
				var turned := int(sol[0] > 0) + int(sol[1] > 0) + int(sol[2] > 0)
				if turned >= 2:
					out.append([p, f])
	return out


func hint_args(goal: String, level: int) -> Array:
	if level < 3:
		return []
	match goal:
		"c2_compressor":
			return valve_solution()
		"c2_booth":
			return state["v_clicks"].duplicate()
		"c2_focus":
			return [focus_sharp()]
		"c2_punch":
			var keys: Array = []
			for i in 8:
				if int(punch_code()[i]) == 1:
					keys.append(str(i + 1))
			return [", ".join(keys), " ".join(punch_code().map(func(b: Variant) -> String: return str(int(b))))]
		"c2_align":
			return [vault_rot_target(), vault_zoom_target()]
	return _exp_hint_args(goal)


# ================================================================== P1 card catalogue
func open_cat_drawer(i: int) -> Array[String]:
	_begin()
	if i < 0 or i > 9:
		_emit("nothing_happens")
		return _end()
	state["cat_drawer"] = -1 if int(state["cat_drawer"]) == i else i
	state["cat_group"] = -1
	state["card_shown"] = false
	_emit("cat_drawer:%d" % int(state["cat_drawer"]))
	return _end()


func pick_divider(g: int) -> Array[String]:
	_begin()
	if int(state["cat_drawer"]) < 0 or g < 0 or g > 9:
		_emit("nothing_happens")
		return _end()
	state["cat_group"] = g
	state["card_shown"] = false
	_emit("cat_group:%d" % g)
	return _end()


## Pull card n (0..9) behind the open divider. Every card can be read; only Leyla's can be taken.
func pull_card(n: int) -> Array[String]:
	_begin()
	var d := int(state["cat_drawer"])
	var g := int(state["cat_group"])
	if d < 0 or g < 0 or n < 0 or n > 9:
		_emit("nothing_happens")
		return _end()
	var number := "%02d%d%d" % [d, g, n]
	if d == CAT_DRAWER and g == CAT_GROUP and n == CAT_CARD:
		state["card_shown"] = true
		_emit("cat_card_leyla")
	else:
		_emit("cat_card:" + number)
	return _end()


# ================================================================== P2 compressor
func pressure() -> int:
	var v: Array = state["valves"]
	return int(v[0]) + 2 * int(v[1])


func flow() -> int:
	var v: Array = state["valves"]
	return 2 * int(v[0]) + int(v[2])


func turn_valve(i: int, delta: int = 1) -> Array[String]:
	_begin()
	if state["pressure_ok"] or i < 0 or i > 2:
		_emit("valves_locked" if state["pressure_ok"] else "nothing_happens")
		return _end()
	var v: Array = state["valves"]
	v[i] = posmod(int(v[i]) + delta, VALVE_POSITIONS)
	_emit("valve:%d:%d" % [i, v[i]])
	if pressure() == int(state["v_targets"][0]) and flow() == int(state["v_targets"][1]):
		state["pressure_ok"] = true
		_emit("pressure_ok")
		_emit("solved:compressor")
	return _end()


# ================================================================== P3 card punch
func toggle_punch_key(i: int) -> Array[String]:
	_begin()
	if not state["card_in_punch"] or i < 0 or i > 7:
		_emit("punch_empty" if not state["card_in_punch"] else "nothing_happens")
		return _end()
	var k: Array = state["punch_keys"]
	k[i] = 1 - int(k[i])
	_emit("punch_key:%d:%d" % [i, k[i]])
	return _end()


func pull_punch_lever() -> Array[String]:
	_begin()
	if not state["card_in_punch"]:
		_emit("punch_empty")
		return _end()
	state["card_in_punch"] = false
	state["request_ok"] = _arr_eq(state["punch_keys"], punch_code())
	state["last_punch"] = (state["punch_keys"] as Array).duplicate()
	state["punch_keys"] = [0, 0, 0, 0, 0, 0, 0, 0]
	_add_item("request_card")
	_emit("card_punched")
	if state["request_ok"]:
		_emit("solved:punch")
	return _end()


# ================================================================== P4 pneumatic post
func set_dest(d: int) -> Array[String]:
	_begin()
	state["dest"] = posmod(d, DEST_COUNT)
	_emit("dest:%d" % int(state["dest"]))
	return _end()


func step_dest(delta: int = 1) -> Array[String]:
	return set_dest(int(state["dest"]) + delta)


## Send the canister. What comes back depends on the card and the destination (docs P4).
func send_canister() -> Array[String]:
	_begin()
	if not state["pressure_ok"]:
		_emit("tube_no_pressure")
		return _end()
	if state["canister"] == "":
		_emit("tube_empty")
		return _end()
	_emit("tube_sent:%d" % int(state["dest"]))
	if int(state["dest"]) != DEST_STACKS:
		state["canister"] = ""
		_add_item("request_card")
		_emit("tube_returned_nodest")
	elif not state["request_ok"]:
		state["canister"] = "" # the stacks keep a wrong request; the tray has more blanks
		_emit("tube_returned_notfound")
	else:
		state["canister"] = ""
		state["file_delivered"] = true
		_emit("tube_returned_file")
		_emit("solved:dispatch")
	return _end()


# ================================================================== P5 locker
func try_locker(n: int) -> Array[String]:
	_begin()
	if n == LOCKER_LEYLA and state["locker_open"]:
		_emit("locker_already_open")
	elif n < 1 or n > LOCKER_COUNT:
		_emit("nothing_happens")
	else:
		_emit("locker_locked:%d" % n)
	return _end()


# ================================================================== P6 receiver hunt
## Strongest signal (0..5) from any reel still hidden, for the current camera view.
func receiver_strength(view: String) -> int:
	var best := 0
	for tape: String in RECEIVER_TABLE:
		if _tape_found(tape):
			continue
		best = maxi(best, int((RECEIVER_TABLE[tape] as Dictionary).get(view, 0)))
	if exp_active():
		best = maxi(best, _cell_door_strength(view)) # N1: the warm east wall, after the last reel
	return best


func _tape_found(tape: String) -> bool:
	var spot := {"tape_1996": "grille_reel", "tape_1997": "ledger_reel", "tape_1998": "hatch_reel"}[tape] as String
	return bool(state["taken"].get(spot, false))


func open_hiding_place(id: String) -> Array[String]:
	_begin()
	var flag := {"grille": "grille_open", "ledger": "ledger_open", "hatch": "hatch_open"}.get(id, "") as String
	if flag == "":
		_emit("nothing_happens")
	elif state[flag]:
		_emit("already_open:" + id)
	else:
		state[flag] = true
		_emit("opened:" + id)
		if state["grille_open"] and state["ledger_open"] and state["hatch_open"]:
			_emit("solved:hunt")
	return _end()


# ================================================================== P7 tape deck
func set_speed(i: int) -> Array[String]:
	_begin()
	state["deck_speed"] = clampi(i, 0, SPEEDS.size() - 1)
	_emit("speed:%d" % int(state["deck_speed"]))
	return _end()


func step_speed(delta: int = 1) -> Array[String]:
	return set_speed(posmod(int(state["deck_speed"]) + delta, SPEEDS.size()))


func eject_tape() -> Array[String]:
	_begin()
	if state["deck_tape"] == "":
		_emit("nothing_happens")
	else:
		_add_item(state["deck_tape"])
		state["deck_tape"] = ""
		_emit("tape_ejected")
	return _end()


func play_tape() -> Array[String]:
	_begin()
	var tape: String = state["deck_tape"]
	if tape == "":
		_emit("deck_empty")
		return _end()
	if int(state["deck_speed"]) != SPEED_RIGHT:
		_emit("tape_garbled:" + tape)
		return _end()
	_emit("tape_clear:" + tape)
	_emit("clicks:%d" % clicks_for(tape))
	var heard: Array = state["clicks_heard"]
	if not heard.has(tape):
		heard.append(tape)
		if heard.size() == TAPES.size():
			_emit("solved:tape")
	return _end()


# ================================================================== P8 booth rotary dial
func dial_digit(d: int) -> Array[String]:
	_begin()
	if state["booth_open"] or d < 0 or d > 9:
		_emit("nothing_happens")
		return _end()
	state["dial_input"] = str(state["dial_input"]) + str(d)
	_emit("dial:%d" % d)
	if str(state["dial_input"]).length() >= booth_code().length():
		if state["dial_input"] == booth_code():
			state["booth_open"] = true
			_emit("booth_opened")
			_emit("solved:booth")
		else:
			_emit("dial_wrong")
		state["dial_input"] = ""
	return _end()


# ================================================================== P9 film splicing
func splice_put(frame: int, slot: int) -> Array[String]:
	_begin()
	if not state["booth_open"] or state["reel_repaired"] or frame < 0 or frame > 3 or slot < 0 or slot > 3:
		_emit("nothing_happens")
		return _end()
	var sp: Array = state["splice"]
	var from := sp.find(frame)
	if from >= 0:
		sp[from] = -1
	var displaced := int(sp[slot])
	sp[slot] = frame
	if displaced >= 0 and from >= 0 and from != slot:
		sp[from] = displaced # swap two placed frames
	_emit("splice:%d:%d" % [frame, slot])
	if _arr_eq(sp, splice_order()):
		state["reel_repaired"] = true
		_emit("reel_repaired")
		_emit("solved:splice")
	elif not sp.has(-1):
		_emit("splice_wrong") # all four strips are in, in the wrong order
	return _end()


func splice_lift(slot: int) -> Array[String]:
	_begin()
	if state["reel_repaired"] or slot < 0 or slot > 3 or int(state["splice"][slot]) < 0:
		_emit("nothing_happens")
		return _end()
	state["splice"][slot] = -1
	_emit("splice_lift:%d" % slot)
	return _end()


# ================================================================== P10 film projector
func toggle_projector() -> Array[String]:
	_begin()
	if not state["booth_open"]:
		_emit("nothing_happens")
		return _end()
	if not state["lamp_ok"]: # G2: the projector's lamp is dead until the spare from the Director's cabinet is in
		state["lamp_seen"] = true
		_emit("lamp_dead")
		return _end()
	state["projector_on"] = not state["projector_on"]
	_emit("projector_on" if state["projector_on"] else "projector_off")
	if state["projector_on"] and not state["reel_on_projector"]:
		_emit("projector_empty")
	_maybe_start_film()
	_check_record()
	return _end()


## The first time the lamp runs with the reel threaded, the film plays through and holds the last frame.
func _maybe_start_film() -> void:
	if not (state["projector_on"] and state["reel_on_projector"]) or state["film_seen"]:
		return
	state["film_seen"] = true
	state["frame"] = SIGN_FRAME
	_emit("film_played")
	if int(state["ch1_shards"]) >= 5:
		_emit("secret_reel")
	if not state["has_lens"] and not state["echo_guided"]:
		state["echo_guided"] = true
		_emit("leyla_echo")
	_emit("solved:projector")


func step_frame(delta: int) -> Array[String]:
	_begin()
	if not (state["projector_on"] and state["reel_on_projector"]):
		_emit("nothing_happens")
		return _end()
	state["frame"] = clampi(int(state["frame"]) + delta, 0, FILM_FRAMES - 1)
	_emit("frame:%d" % int(state["frame"]))
	_check_record()
	return _end()


func turn_focus(delta: int) -> Array[String]:
	_begin()
	if not state["booth_open"]:
		_emit("nothing_happens")
		return _end()
	state["focus"] = clampi(int(state["focus"]) + delta, 0, FOCUS_STEPS - 1)
	_emit("focus:%d" % int(state["focus"]))
	_check_record()
	return _end()


func is_sharp() -> bool:
	return int(state["focus"]) == focus_sharp()


## What the big screen shows: "" | "white" | "film:<n>" | "mark" | "mark_tilted" | "mixed".
func screen_image() -> String:
	var film_lamp: bool = state["projector_on"]
	var slide: bool = state["slide_on"] and state["slide_in"]
	if film_lamp and slide:
		return "mixed"
	if film_lamp:
		return "film:%d" % int(state["frame"]) if state["reel_on_projector"] else "white"
	if slide:
		return "mark" if int(state["slide_rot"]) % 2 == 0 else "mark_tilted"
	return ""


# ================================================================== P11 recording (screen socket)
func take_from_socket() -> Array[String]:
	_begin()
	if state["socket"] == "":
		_emit("nothing_happens")
	else:
		_add_item(state["socket"])
		state["socket"] = ""
		_emit("socket_emptied")
	return _end()


## A blank crystal in the socket records whatever single sharp image falls on it.
func _check_record() -> void:
	var c: String = state["socket"]
	if not c.begins_with("crystal_blank"):
		return
	var img := screen_image()
	if img == "film:%d" % SIGN_FRAME and is_sharp() and not state["sign_recorded"]:
		state["sign_recorded"] = true
		state["socket"] = "crystal_sign"
		_emit("recorded:sign")
		_emit("solved:record")
	elif img == "mark" and not state["mark_recorded"]:
		state["mark_recorded"] = true
		state["socket"] = "crystal_mark"
		_emit("recorded:mark")


# ================================================================== P11b slides (leave path)
func open_slide_drawer(i: int) -> Array[String]:
	_begin()
	if not state["booth_open"] or i < 0 or i >= SLIDE_DRAWERS:
		_emit("nothing_happens")
		return _end()
	state["slide_drawer"] = -1 if int(state["slide_drawer"]) == i else i
	state["slide_drawer_mark"] = int(state["slide_drawer"]) == SLIDE_MARK_DRAWER
	_emit("slide_drawer:%d" % int(state["slide_drawer"]))
	return _end()


func rotate_slide() -> Array[String]:
	_begin()
	if not state["slide_in"]:
		_emit("nothing_happens")
		return _end()
	state["slide_rot"] = (int(state["slide_rot"]) + 1) % 4
	_emit("slide_rot:%d" % int(state["slide_rot"]))
	_check_record()
	return _end()


func toggle_slide_lamp() -> Array[String]:
	_begin()
	if not state["booth_open"]:
		_emit("nothing_happens")
		return _end()
	state["slide_on"] = not state["slide_on"]
	_emit("slide_lamp:%s" % ("on" if state["slide_on"] else "off"))
	_check_record()
	return _end()


func eject_slide() -> Array[String]:
	_begin()
	if not state["slide_in"]:
		_emit("nothing_happens")
	else:
		state["slide_in"] = false
		_add_item("emblem_slide")
		_emit("slide_ejected")
	return _end()


# ================================================================== P12 dual light lock + vault
## What a crystal holds: "mark" | "sign" | "" (blank).
func crystal_image(id: String) -> String:
	match id:
		"crystal_lens", "crystal_mark":
			return "mark"
		"crystal_sign":
			return "sign"
	return ""


func take_from_port(side: String) -> Array[String]:
	_begin()
	var key := "port_" + side
	if not state.has(key) or state[key] == "":
		_emit("nothing_happens")
	else:
		_add_item(state[key])
		state[key] = ""
		_emit("port_emptied:" + side)
	return _end()


func turn_collar(which: String, delta: int = 1) -> Array[String]:
	_begin()
	if state["vault_unlocked"]:
		_emit("nothing_happens")
		return _end()
	match which:
		"rot_left", "rot_right":
			state[which] = posmod(int(state[which]) + delta, ROT_STEPS)
		"zoom_right":
			state[which] = posmod(int(state[which]) + delta, ZOOM_STEPS)
		_:
			_emit("nothing_happens")
			return _end()
	_emit("collar:%s:%d" % [which, int(state[which])])
	_check_lock()
	return _end()


func overlay_left_ok() -> bool:
	return crystal_image(state["port_left"]) == "mark" and int(state["rot_left"]) % 4 == 0


func overlay_right_ok() -> bool:
	return crystal_image(state["port_right"]) == "sign" and int(state["rot_right"]) == vault_rot_target() \
		and int(state["zoom_right"]) == vault_zoom_target()


func _check_lock() -> void:
	if state["vault_unlocked"]:
		return
	if overlay_left_ok() and overlay_right_ok():
		state["vault_unlocked"] = true
		_emit("vault_unlocked")
		_emit("solved:lock")


func turn_wheel() -> Array[String]:
	_begin()
	if not state["vault_unlocked"] or state["vault_open"]:
		_emit("wheel_locked" if not state["vault_unlocked"] else "nothing_happens")
		return _end()
	state["wheel"] = int(state["wheel"]) + 1
	_emit("wheel:%d" % int(state["wheel"]))
	if int(state["wheel"]) >= WHEEL_TURNS:
		state["vault_open"] = true
		_emit("vault_opened")
	return _end()


# ================================================================== using items on things
func use_item_on(item: String, target: String) -> Array[String]:
	if not has_item(item):
		_begin()
		_emit("nothing_happens")
		return _end()
	_begin()
	match [item, target]:
		["blank_card", "punch"]:
			if state["card_in_punch"]:
				_emit("nothing_happens")
			else:
				_remove_item("blank_card")
				state["card_in_punch"] = true
				_emit("card_in_punch")
		["request_card", "send_port"]:
			if state["canister"] != "":
				_emit("nothing_happens")
			else:
				_remove_item("request_card")
				state["canister"] = "request_card"
				_emit("canister_loaded")
		["locker_key", "locker_9"]:
			state["locker_open"] = true
			_remove_item("locker_key")
			_emit("locker_opened")
			_emit("solved:locker")
		["tape_1996", "deck"], ["tape_1997", "deck"], ["tape_1998", "deck"]:
			if state["deck_tape"] != "":
				_add_item(state["deck_tape"])
			_remove_item(item)
			state["deck_tape"] = item
			_emit("tape_loaded:" + item)
		["film_reel", "projector"]:
			_remove_item("film_reel")
			state["reel_on_projector"] = true
			_emit("reel_threaded")
			_maybe_start_film() # lamp already on: the film starts now
			_check_record()
		["request_card", "card_tray"]:
			# a mis-punched card can be put back; the tray then gives a fresh blank
			_remove_item("request_card")
			state["request_ok"] = false
			_emit("card_returned")
		["projector_lamp", "projector"]:
			_remove_item("projector_lamp")
			state["lamp_ok"] = true
			_emit("lamp_installed")
			_emit("solved:lamp")
		["emblem_slide", "slide_projector"]:
			_remove_item("emblem_slide")
			state["slide_in"] = true
			_emit("slide_inserted")
			_check_record()
		_:
			if item in CRYSTALS and target == "screen_socket":
				_use_crystal_on_socket(item)
			elif item in CRYSTALS and target in ["port_left", "port_right"]:
				_use_crystal_on_port(item, target)
			else:
				_emit("not_for_here") # this item has no use here at all (the room names it), not just not yet
				_emit("nothing_happens")
	return _end()


func _use_crystal_on_socket(item: String) -> void:
	if item == "crystal_lens":
		_emit("lens_refused") # it already remembers Strand's mark
	elif state["socket"] != "":
		_emit("socket_full")
	else:
		_remove_item(item)
		state["socket"] = item
		_emit("crystal_seated")
		_check_record()


func _use_crystal_on_port(item: String, port: String) -> void:
	if state[port] != "":
		_emit("port_full")
		return
	_remove_item(item)
	state[port] = item
	_emit("port_filled:%s:%s" % [port, item])
	if crystal_image(item) == "":
		_emit("port_blank")
	_check_lock()


# ================================================================== optional: kept echoes
func holds_crystal() -> bool:
	return selected in CRYSTALS


func release_echo(id: String) -> Array[String]:
	_begin()
	var e: Array = state["echoes"]
	if not ECHOES.has(id) or e.has(id) or not holds_crystal() or (id == "booth" and not state["booth_open"]):
		_emit("nothing_happens")
		return _end()
	e.append(id)
	_emit("echo_released:" + id)
	if e.size() == ECHOES.size():
		_emit("all_echoes")
	return _end()


# ================================================================== finale
func choice_options() -> Array:
	return [["strand_key", "ui.take_strand_key"], ["leyla_key", "ui.take_leyla_key"]]


func choice_prompt_key() -> String:
	return "ui.choice_keys_prompt"


func choose_ending(option: String) -> Array[String]:
	_begin()
	if not state["vault_open"] or state["complete"] or not option in ["strand_key", "leyla_key"]:
		_emit("nothing_happens")
		return _end()
	state["choice"] = option
	state["complete"] = true
	_add_item(option)
	_emit("choice:" + option)
	_emit("chapter_complete")
	return _end()


# ================================================================== chapter hooks
func puzzle_ids() -> Array[String]:
	var out: Array[String] = []
	out.assign(PUZZLE_IDS)
	if exp_stage() >= 1:
		for id in ["warm", "pipes", "light", "aisle", "frost", "chest"]:
			out.append(id)
	if exp_stage() >= 2:
		for id in ["lift", "board", "print", "cabinet"]:
			out.append(id)
	return out


func solved_count() -> int:
	var flags := [
		state["taken"].get("index_card", false), state["pressure_ok"],
		state["request_ok"] or state["file_delivered"], state["file_delivered"], state["locker_open"],
		state["grille_open"] and state["ledger_open"] and state["hatch_open"],
		(state["clicks_heard"] as Array).size() == TAPES.size(), state["booth_open"], state["reel_repaired"],
		state["film_seen"], state["sign_recorded"], state["vault_unlocked"],
	]
	if exp_stage() >= 1:
		flags.append_array([state["pump_open"], state["thawed"], state["cell_digits_ok"] or state["cold_open"],
			state["aisle"], state["frost_seen"], state["chest_open"]])
	if exp_stage() >= 2:
		flags.append_array([state["lift_ok"], state["board_ok"], state["print_ok"], state["cab_open"]])
	var n := 0
	for f: bool in flags:
		if f:
			n += 1
	return n


func hint_goal() -> String:
	if not hints_allowed():
		return "" # Archivist's Trial: no hints
	return ArchiveHints.current_goal(self)


func collectibles() -> Array:
	return [(state["echoes"] as Array).size(), ECHOES.size(), "ui.echoes"]


func epilogue_keys() -> Array[String]:
	var out: Array[String] = ["epi2.42nd", "epi2.strand_key" if state["choice"] == "strand_key" else "epi2.leyla_key"]
	if (state["echoes"] as Array).size() == ECHOES.size():
		out.append("epi2.echoes")
	if trial_stamp() and state["complete"]:
		out.append("epi2.trial")
	out.append("epi2.recorder")
	return out


func profile_choices() -> Dictionary:
	var out := {"ch2_key": state["choice"], "ch2_echoes": (state["echoes"] as Array).size()}
	if exp_active(): # Chapters 3-4 read these only through choices.get(..., default)
		out["ch2_trial"] = trial_stamp()
		out["ch2_bonus_echoes"] = (state["bonus_echoes"] as Array).size()
	return out


func item_desc_key(id: String) -> String:
	if id == "crystal_lens":
		return "item.crystal_lens.desc_recorded"
	return super(id)


func item_glows(id: String) -> bool:
	return crystal_image(id) != ""


func intro_keys() -> Array[String]:
	return ["intro2.1", "intro2.2"]


## The first goal, said once when the intro hands over (the badge in the inventory carries her number).
func intro_caption_key() -> String:
	return "cap2.goal"


# ================================================================== expansion: lifecycle, migration, stage
## docs/CHAPTER2_EXPANSION.md. EXPANSION_STAGE is the stage a NEW game is built with: 0 = the 1.0 chapter (no new
## floors, no new gates), 1 = Stage A (lower floor, G1), 2 = Stage A + B (update 1.1 ships both). The scene agent sets
## it to 2 when the new rooms exist in the scene. A saved game keeps its own `exp_ver` / `stage`.
func exp_active() -> bool:
	return int(state["exp_ver"]) >= EXP_VER_CURRENT


## 0 for a legacy game, else the stage this game was started with.
func exp_stage() -> int:
	return int(state["stage"]) if exp_active() else 0


## Turn this (fresh) game into an expansion game of `stage` (1 or 2). Used by new games and the tests.
func begin_expansion(stage: int = 2) -> void:
	state["exp_ver"] = EXP_VER_CURRENT
	state["stage"] = clampi(stage, 1, 2)
	state["crystal_home"] = "cold"
	state["crystals_available"] = false
	state["lamp_ok"] = int(state["stage"]) < 2 # Stage A alone ships with G2 pre-satisfied
	if exp_active() and not inventory.has("floor_plan"):
		inventory.append("floor_plan")


## Turn this game into the 1.0 chapter: what an old save becomes when it is loaded. No new gate, no new floor.
func make_legacy() -> void:
	state["exp_ver"] = EXP_VER_LEGACY
	state["stage"] = 0
	state["crystal_home"] = "case"
	state["crystals_available"] = true
	state["lamp_ok"] = true
	inventory.erase("floor_plan")


## A new expansion game as the app creates it: profile choices, then this game's seed.
static func new_expanded(game_seed: int = 0, stage: int = 2, choices: Dictionary = {}) -> ArchiveLogic:
	var l := ArchiveLogic.new()
	l.begin_expansion(stage)
	l.setup_from_profile(choices)
	l.apply_seed(game_seed)
	return l


## A game exactly as 1.0 played it (the same flow an old save keeps).
static func new_legacy(choices: Dictionary = {}) -> ArchiveLogic:
	var l := ArchiveLogic.new()
	l.make_legacy()
	l.setup_from_profile(choices)
	return l


func from_dict(d: Dictionary) -> bool:
	var ok := super(d)
	# A save without exp_ver comes from before the expansion: the missing keys took NEW-game defaults, which would
	# drop it into gates it never met. Make it the old chapter (docs/CHAPTER2_EXPANSION.md section 10).
	if ok and not (d["state"] as Dictionary).has("exp_ver"):
		make_legacy()
	return ok


func _end() -> Array[String]:
	if exp_active():
		_refresh_threads()
	return super()


func _need_ok(spot: String, need: String) -> bool:
	if need == "":
		return true
	if spot == "case_crystal_1" or spot == "case_crystal_2":
		# G1: the blank crystals are in the Cold Store chest (new games) or in the booth's case (old saves)
		return bool(state["crystals_available"]) and (state["crystal_home"] != "case" or bool(state["booth_open"]))
	if need == "gallery_open":
		return room_open("gallery")
	return bool(state[need])


func _on_taken(spot: String) -> void:
	if spot == "board_key":
		state["pass_key"] = true


# ================================================================== expansion: variants (separate seed streams)
func _apply_exp_seed(game_seed: int) -> void:
	var D := ArchiveExpData
	state["v_panel"] = D.stream(game_seed, D.SALT_PANEL).randi_range(0, 2)
	state["v_pipes"] = D.stream(game_seed, D.SALT_PIPES).randi_range(0, D.PIPE_GRAPHS.size() - 1)
	var lt := D.gen_light_table(D.stream(game_seed, D.SALT_GLYPH))
	state["v_glyph"] = lt["digits"]
	state["v_sheets"] = lt["sheets"]
	state["v_sheet_target"] = lt["target"]
	state["sheets"] = lt["start"]
	var pool := D.aisle_pool()
	var pick: Array = pool[D.stream(game_seed, D.SALT_BAY).randi_range(0, pool.size() - 1)]
	state["v_bay"] = int(pick[0])
	state["aisle_pos"] = (pick[1] as Array).duplicate()
	var sr := D.stream(game_seed, D.SALT_SYMBOLS)
	var syms: Array = [0, 1, 2, 3, 4, 5]
	D._shuffle(syms, sr)
	state["v_symbols"] = syms.slice(0, 3)
	var starts := D.chest_starts(state["v_symbols"])
	state["v_chest_start"] = (starts[D.stream(game_seed, D.SALT_CHEST).randi_range(0, starts.size() - 1)] as Array).duplicate()
	state["rings"] = (state["v_chest_start"] as Array).duplicate()
	state["v_load"] = D.LOADS[D.stream(game_seed, D.SALT_LOAD).randi_range(0, D.LOADS.size() - 1)]
	var bd := D.gen_board(D.stream(game_seed, D.SALT_BOARD))
	state["v_board"] = bd["board"]
	var flat: Array = []
	for s: Array in bd["slips"]:
		flat.append_array(s)
	state["v_slips"] = flat
	var pr := D.stream(game_seed, D.SALT_PRINT)
	var strips: Array = [0, 1, 2, 3, 4, 5]
	D._shuffle(strips, pr)
	state["v_strips"] = strips.slice(0, D.STRIPS)
	state["v_strip"] = pr.randi_range(0, D.STRIPS - 1)
	state["v_zoom"] = pr.randi_range(1, D.ENL_ZOOM_STEPS - 2)
	state["v_pfocus"] = pr.randi_range(2, D.ENL_FOCUS_STEPS - 3)
	var digits: Array = []
	for _i in 4:
		digits.append(pr.randi_range(0, 9))
	if digits[0] == digits[1] and digits[1] == digits[2] and digits[2] == digits[3]:
		digits[3] = (int(digits[3]) + 1) % 10
	state["v_digits"] = digits


# ================================================================== expansion: rooms, floor plan, threads
func room_ids() -> Array[String]:
	var out: Array[String] = []
	for r: Dictionary in ArchiveExpData.ROOMS:
		if int(r["stage"]) <= maxi(exp_stage(), 1):
			out.append(r["id"])
	return out


func room_open(id: String) -> bool:
	if id == "hall":
		return true
	if not exp_active() or not room_ids().has(id):
		return false
	match id:
		"pump", "cell":
			return bool(state["pump_open"])
		"cold":
			return bool(state["cold_open"])
		"gallery":
			return bool(state["lift_ok"]) or bool(state["wedge_out"])
		"plate":
			return room_open("gallery")
		"office":
			return bool(state["pass_key"])
	return false


func room_seen(id: String) -> bool:
	return id == "hall" or (state["rooms_seen"] as Array).has(id)


## Walk through the door into a room. A locked room refuses; the first visit is always on foot.
func enter_room(id: String) -> Array[String]:
	_begin()
	if not room_open(id):
		_emit("room_locked:" + id)
		return _end()
	_enter(id)
	return _end()


## Quick travel from the floor plan: only to rooms already entered, never into a locked room.
func travel_to(id: String) -> Array[String]:
	_begin()
	if not room_seen(id) or not room_open(id):
		_emit("travel_refused:" + id)
		return _end()
	_enter(id)
	_emit("travel:" + id)
	return _end()


## The room to offer as "Go to <room>" next to a hint for `goal` ("" when none, or it cannot be reached by plan).
func hint_room(goal: String) -> String:
	var r: String = ArchiveExpData.GOAL_ROOM.get(goal, "")
	return r if r != "" and can_travel(r) else ""


func can_travel(id: String) -> bool:
	return room_seen(id) and room_open(id) and state["room"] != id


func _enter(id: String) -> void:
	state["room"] = id
	var first := not room_seen(id)
	if first:
		(state["rooms_seen"] as Array).append(id)
		_emit("room_new:" + id)
	_emit("room:" + id)
	match id:
		"pump":
			_moment("m1")
		"gallery":
			_moment("m4")
		"cold":
			if state["aisle"]:
				_moment("m5")


## Reaction moments fire once per save (section 11). The scene plays them when no caption or mechanism is busy.
func _moment(id: String) -> void:
	var seen: Array = state["moments_seen"]
	if not seen.has(id):
		seen.append(id)
		_emit("moment:" + id)


## For moments the scene triggers from a camera view: m2 = the first look at the Cell door from the Pump Room.
func try_moment(id: String) -> Array[String]:
	_begin()
	if exp_active() and id == "m2" and state["pump_open"] and not room_seen("cell"):
		_moment("m2")
	return _end()


func moment_seen(id: String) -> bool:
	return (state["moments_seen"] as Array).has(id)


## (room, seen, done) triples: a lock or pick-up in `room` that the player has met and not finished.
func _pending_items() -> Array:
	var taken: Dictionary = state["taken"]
	var s := state
	var st := exp_stage()
	var items: Array = [
		["hall", coda_heard(), s["pump_open"]], # the warm east wall
		["hall", s["lamp_seen"] and st >= 2, s["lamp_ok"]], # the dead projector lamp
		["hall", has_item("projector_lamp"), s["lamp_ok"]], # the lamp is in the bag, not yet in the projector
		["pump", room_seen("pump"), s["thawed"]], # the manifold
		["pump", room_seen("pump") and st >= 2 and s["thawed"], s["lift_ok"]], # the book lift
		["pump", room_seen("pump"), taken.get("pump_mallet", false)],
		["cell", room_seen("cell"), s["cell_digits_ok"] or s["cold_open"]], # the light table
		["cell", room_seen("cell"), s["cold_open"]], # the frozen door
		["cell", room_seen("cell"), taken.get("cell_cloth", false)],
		["cold", room_seen("cold"), s["aisle"]],
		["cold", room_seen("cold") and s["aisle"], s["frost_seen"]],
		["cold", room_seen("cold") and s["aisle"], s["chest_open"]],
		["cold", s["chest_open"], taken.get("case_crystal_1", false) or taken.get("case_crystal_2", false)],
		["gallery", room_seen("gallery"), s["board_ok"]],
		["gallery", room_seen("gallery"), taken.get("counter_slips", false)],
		["gallery", s["board_ok"], taken.get("board_key", false)],
		["plate", room_seen("plate"), s["print_ok"]],
		["office", room_seen("office"), s["cab_open"]],
		["office", s["cab_open"], taken.get("cabinet_lamp", false)],
	]
	return items


## True when the room holds something the player has seen and not finished. Says THAT, never what: nothing shows
## before the clue's lock has been met, and the marker is computed from state only.
func room_pending(id: String) -> bool:
	if not exp_active():
		return false
	for it: Array in _pending_items():
		if it[0] == id and bool(it[1]) and not bool(it[2]):
			return true
	return false


## "locked" | "new" (open, never entered) | "visited".
func room_status(id: String) -> String:
	if not room_open(id):
		return "locked"
	return "visited" if room_seen(id) else "new"


## The floor plan the UI draws: floors -1/0/+1, a tile per room.
func plan_data() -> Dictionary:
	var rooms: Array[Dictionary] = []
	for r: Dictionary in ArchiveExpData.ROOMS:
		var id: String = r["id"]
		if int(r["stage"]) > maxi(exp_stage(), 1):
			continue
		rooms.append({"id": id, "floor": r["floor"], "name": r["name"], "status": room_status(id),
			"pending": room_pending(id), "here": state["room"] == id, "travel": can_travel(id)})
	return {"floors": ArchiveExpData.FLOORS, "rooms": rooms, "here": state["room"], "threads": open_threads()}


func _thread_seen(id: String) -> bool:
	match id:
		"warm_panel":
			return coda_heard()
		"blocked_stair":
			return coda_heard() and exp_stage() >= 2
		"frozen_door":
			return room_seen("cell")
		"case_card":
			return bool(state["booth_open"])
		"dead_lamp":
			return bool(state["lamp_seen"]) and exp_stage() >= 2
		"pass_door":
			return room_seen("gallery")
		"cabinet_symbol":
			return room_seen("office")
	return false


func _thread_closed(id: String) -> bool:
	match id:
		"warm_panel":
			return bool(state["pump_open"])
		"blocked_stair":
			return bool(state["wedge_out"])
		"frozen_door":
			return bool(state["cold_open"])
		"case_card":
			return bool(state["crystals_available"])
		"dead_lamp":
			return bool(state["lamp_ok"])
		"pass_door":
			return bool(state["pass_key"])
		"cabinet_symbol":
			return bool(state["print_ok"])
	return true


## A thread joins the list when first seen, but never as a 4th open one: it waits until one closes.
func _refresh_threads() -> void:
	var seen: Array = state["threads_seen"]
	var open := 0
	for t: String in seen:
		if not _thread_closed(t):
			open += 1
	for t: Dictionary in ArchiveExpData.THREADS:
		var id: String = t["id"]
		if seen.has(id) or open >= ArchiveExpData.MAX_OPEN_THREADS:
			continue
		if _thread_seen(id) and not _thread_closed(id):
			seen.append(id)
			open += 1
		elif _thread_seen(id) and _thread_closed(id):
			seen.append(id) # met and closed in one go: never listed


## The notebook page "Open threads": [{id, room, name}], at most 3, no solution text.
func open_threads() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for id: String in state["threads_seen"]:
		if _thread_closed(id):
			continue
		for t: Dictionary in ArchiveExpData.THREADS:
			if t["id"] == id:
				out.append({"id": id, "room": t["room"], "name": t["name"]})
	return out


# ================================================================== N1 Warm Wall
func coda_heard() -> bool:
	return exp_active() and (state["clicks_heard"] as Array).size() == TAPES.size()


func panel_letter() -> String:
	return ArchiveExpData.PANEL_LETTERS[int(state["v_panel"])]


## Receiver strength on a wall panel view ("east_panel_a" .. "_c"); 0 when the door is not the target any more.
func _cell_door_strength(view: String) -> int:
	if not coda_heard() or state["pump_open"]:
		return 0
	if view.begins_with("east_panel_"):
		var i := ArchiveExpData.PANEL_LETTERS.find(view.substr(11).to_upper())
		return ArchiveExpData.panel_strength(i, int(state["v_panel"])) if i >= 0 else 0
	return int(ArchiveExpData.CELL_DOOR_VIEWS.get(view, 0))


func n1_open_panel(i: int) -> Array[String]:
	_begin()
	if not coda_heard() or state["pump_open"] or state["panel_found"] or i < 0 or i > 2:
		_emit("nothing_happens")
	elif i == int(state["v_panel"]):
		state["panel_found"] = true
		_emit("panel_opened:%d" % i)
	else:
		_emit("panel_cold:%d" % i)
	return _end()


func n1_dial(d: int) -> Array[String]:
	_begin()
	if not state["panel_found"] or state["pump_open"] or d < 0 or d > 9:
		_emit("nothing_happens")
		return _end()
	state["n1_dial"] = str(state["n1_dial"]) + str(d)
	_emit("dial_n1:%d" % d)
	if str(state["n1_dial"]).length() >= BADGE_NO.length():
		if state["n1_dial"] == BADGE_NO:
			state["pump_open"] = true
			_emit("pump_opened")
			_emit("solved:warm")
		else:
			_emit("n1_dial_wrong")
		state["n1_dial"] = ""
	return _end()


# ================================================================== N2 Pipe routing
func pipe_graph() -> Array:
	return ArchiveExpData.PIPE_GRAPHS[int(state["v_pipes"])]


func pipes_mask() -> int:
	var m := 0
	for i in 6:
		m |= int(state["pipes"][i]) << i
	return m


## Nodes the pressure reaches now (0 S, 1 coil, 2 hazard vent, 3-5 junctions).
func pipes_reach() -> Array[int]:
	return ArchiveExpData.pipe_reach(pipe_graph(), pipes_mask())


func pipe_solution() -> Array[int]:
	return ArchiveExpData.pipe_solution(int(state["v_pipes"]))


func n2_toggle_valve(i: int) -> Array[String]:
	_begin()
	if not state["pump_open"] or i < 0 or i > 5:
		_emit("nothing_happens")
		return _end()
	if state["thawed"]:
		_emit("valves_locked_n2")
		return _end()
	state["pipes"][i] = 1 - int(state["pipes"][i])
	_emit("pipe:%d:%d" % [i, int(state["pipes"][i])])
	var reach := pipes_reach()
	if reach.has(ArchiveExpData.NODE_H):
		_emit("pipes_hazard")
	elif reach.has(ArchiveExpData.NODE_C):
		state["thawed"] = true
		_emit("thawed")
		_emit("solved:pipes")
		_check_cold()
	return _end()


## The mallet probe: tap a pipe segment and hear whether it is full, dead or cracked.
func n2_tap_pipe(seg: int) -> Array[String]:
	_begin()
	if not state["pump_open"] or seg < 0 or seg > 5:
		_emit("nothing_happens")
	elif not has_item("mallet"):
		_emit("need_mallet")
	else:
		_emit("tap:%d:%s" % [seg, ArchiveExpData.pipe_tap(pipe_graph(), pipes_mask(), seg)])
	return _end()


# ================================================================== N3 Light table
func n3_sheet(i: int) -> PackedByteArray:
	return ArchiveExpData.string_to_bits(str(state["v_sheets"][i]))


## Sheet i as it lies on the box now (11 x 11): mirrored if flipped, then turned.
func n3_turned(i: int) -> PackedByteArray:
	return ArchiveExpData.sheet_transform(n3_sheet(i), int(state["sheets"][2 * i]), int(state["sheets"][2 * i + 1]))


func n3_glyph() -> PackedByteArray:
	return ArchiveExpData.glyph_window(int(state["v_glyph"][0]), int(state["v_glyph"][1]))


## The 77 window cells that are lit now (row-major, 7 rows x 11 columns).
func n3_lit() -> PackedByteArray:
	return ArchiveExpData.light(n3_turned(0), n3_turned(1), n3_turned(2))


## [lit cells that belong to the digits, lit cells that do not, cells of the digits]: the live feedback.
func n3_progress() -> Array[int]:
	var lit := n3_lit()
	var g := n3_glyph()
	var good := 0
	var stray := 0
	var total := 0
	for i in lit.size():
		total += int(g[i])
		if lit[i] == 1:
			if g[i] == 1:
				good += 1
			else:
				stray += 1
	return [good, stray, total]


func n3_turn_sheet(i: int) -> Array[String]:
	return _n3_change(i, true)


func n3_flip_sheet(i: int) -> Array[String]:
	return _n3_change(i, false)


func _n3_change(i: int, turn: bool) -> Array[String]:
	_begin()
	if not state["pump_open"] or i < 0 or i > 2:
		_emit("nothing_happens")
		return _end()
	if state["cell_digits_ok"]:
		_emit("sheets_locked")
		return _end()
	var sh: Array = state["sheets"]
	if turn:
		sh[2 * i] = (int(sh[2 * i]) + 1) % 4
	else:
		sh[2 * i + 1] = 1 - int(sh[2 * i + 1])
	_emit("sheet:%d:%d:%d" % [i, int(sh[2 * i]), int(sh[2 * i + 1])])
	var p := n3_progress()
	_emit("lit:%d:%d" % [p[0], p[1]])
	if n3_lit() == n3_glyph():
		state["cell_digits_ok"] = true
		_emit("light_digits")
		_emit("solved:light")
	return _end()


## The two digits the light spells (known to the player once the table is solved).
func light_digits() -> Array:
	return (state["v_glyph"] as Array).duplicate()


## The Cold Store door: two wheels (set to the light table's digits) and the heating coil behind the ice.
func cold_wheel(i: int, delta: int = 1) -> Array[String]:
	_begin()
	if not state["pump_open"] or state["cold_open"] or i < 0 or i > 1:
		_emit("nothing_happens")
		return _end()
	state["cold_wheels"][i] = posmod(int(state["cold_wheels"][i]) + delta, 10)
	_emit("cold_wheel:%d:%d" % [i, int(state["cold_wheels"][i])])
	_check_cold()
	return _end()


func _check_cold() -> void:
	if state["cold_open"] or not _arr_eq(state["cold_wheels"], state["v_glyph"]):
		return
	if state["thawed"]:
		state["cold_open"] = true
		_emit("cold_opened")
		_emit("solved:cold_door")
	else:
		_emit("cold_frozen") # the digits are right; the ice is not melted yet


# ================================================================== N4 Carriage aisle
func aisle_bay() -> int:
	return int(state["v_bay"])


func aisle_route_from_here() -> Array:
	return ArchiveExpData.aisle_route(state["aisle_pos"], aisle_bay())


## A crank slides its carriage one slot into a free neighbouring slot. dir 0 = the way the crank last turned (it
## reverses after a clunk), -1 / +1 = an explicit direction.
func n4_crank(k: int, dir: int = 0) -> Array[String]:
	_begin()
	if not state["cold_open"] or k < 0 or k >= ArchiveExpData.CARRIAGES:
		_emit("nothing_happens")
		return _end()
	if state["aisle"]:
		_emit("cranks_locked")
		return _end()
	var pos: Array = state["aisle_pos"]
	var want := dir if dir != 0 else int(state["crank_dir"][k])
	var target := int(pos[k]) + want
	if target < 0 or target >= ArchiveExpData.AISLE_SLOTS or pos.has(target):
		state["crank_dir"][k] = -want
		_emit("clunk:%d" % k)
		return _end()
	var before: Array = []
	for b in range(1, ArchiveExpData.CARRIAGES):
		before.append(ArchiveExpData.aisle_open_at(pos, b))
	pos[k] = target
	state["crank_dir"][k] = want
	_emit("crank:%d:%d" % [k, target])
	for b in range(1, ArchiveExpData.CARRIAGES):
		if ArchiveExpData.aisle_open_at(pos, b) and not before[b - 1] and b != aisle_bay():
			_emit("aisle_lore:%d" % b) # a wrong aisle: other shelves, lore cans
	if ArchiveExpData.aisle_open_at(pos, aisle_bay()):
		state["aisle"] = true
		_emit("aisle_found")
		_emit("solved:aisle")
		_moment("m6")
		_bonus_echo("aisle")
	return _end()


func _bonus_echo(id: String) -> void:
	var e: Array = state["bonus_echoes"]
	if not e.has(id) and e.size() < 2:
		e.append(id)
		_emit("bonus_echo:" + id)


# ================================================================== N5 Frost window
func frost_symbols() -> Array:
	return (state["v_symbols"] as Array).duplicate()


## Wipe a band with the cloth (a tap works as well as a drag).
func n5_wipe(band: int) -> Array[String]:
	_begin()
	if not state["cold_open"] or band < 0 or band > 2:
		_emit("nothing_happens")
		return _end()
	if not state["aisle"]:
		_emit("need_aisle")
		return _end()
	if not has_item("wipe_cloth"):
		_emit("need_cloth")
		return _end()
	if int(state["wiped"][band]) == 1:
		_emit("band_clear:%d" % band)
		return _end()
	var first := not (state["wiped"] as Array).has(1)
	state["wiped"][band] = 1
	_emit("band_wiped:%d:%d" % [band, int(state["v_symbols"][band])])
	if first:
		_moment("m3")
	if not (state["wiped"] as Array).has(0):
		state["frost_seen"] = true
		_add_item("frost_sketch")
		_emit("frost_done")
		_emit("solved:frost")
	return _end()


# ================================================================== N6 Chest rings
func chest_target() -> Array:
	return frost_symbols()


func chest_presses() -> Array:
	return ArchiveExpData.ring_counts(state["rings"], chest_target())


func n6_turn_ring(i: int) -> Array[String]:
	_begin()
	if i < 0 or i >= ArchiveExpData.RINGS or not state["cold_open"] or state["chest_open"]:
		_emit("nothing_happens")
		return _end()
	if not state["aisle"]:
		_emit("chest_sealed")
		return _end()
	state["rings"] = ArchiveExpData.ring_press(state["rings"], i)
	_emit("ring:%d:%d" % [i, int(state["rings"][i])])
	if _arr_eq(state["rings"], chest_target()):
		state["chest_open"] = true
		state["crystals_available"] = true
		_emit("chest_opened")
		_emit("solved:chest")
	return _end()


# ================================================================== N7 Book-lift counterweight (Stage B)
func lift_load() -> int:
	return int(state["v_load"])


func counterweight() -> int:
	return ArchiveExpData.weights_sum(state["weights"])


func n7_toggle_weight(i: int) -> Array[String]:
	_begin()
	if exp_stage() < 2 or i < 0 or i > 3:
		_emit("nothing_happens")
		return _end()
	if not state["thawed"]:
		_emit("no_pressure")
		return _end()
	if state["lift_ok"]:
		_emit("weights_locked")
		return _end()
	state["weights"][i] = 1 - int(state["weights"][i])
	_emit("weight:%d:%d" % [i, int(state["weights"][i])])
	var sum := counterweight()
	if sum == lift_load():
		state["lift_ok"] = true
		_emit("lift_balanced")
		_emit("solved:lift")
	else:
		_emit("counter_heavy" if sum > lift_load() else "counter_light")
	return _end()


## The selector: floors -1 / 0 / +1 (flask, book, lamp pictograms). Works once the cage is balanced.
func n7_call(floor_no: int) -> Array[String]:
	_begin()
	if exp_stage() < 2 or not ArchiveExpData.LIFT_FLOORS.has(floor_no):
		_emit("nothing_happens")
	elif not state["lift_ok"]:
		_emit("lift_stuck")
	else:
		state["lift_floor"] = floor_no
		_emit("lift_moved:%d" % floor_no)
	return _end()


## The pin of the wedged ladder, pulled from the Gallery side (a beat, not a puzzle): the spiral stair opens.
func pull_wedge() -> Array[String]:
	_begin()
	if exp_stage() < 2 or not room_seen("gallery") or state["wedge_out"]:
		_emit("nothing_happens")
	else:
		state["wedge_out"] = true
		_emit("wedge_out")
	return _end()


# ================================================================== N8 Roll-call board (Stage B)
## The slips as [[type, a, b], ...].
func board_slips() -> Array:
	var out: Array = []
	var flat: Array = state["v_slips"]
	for i in range(0, flat.size() - 2, 3):
		out.append([int(flat[i]), int(flat[i + 1]), int(flat[i + 2])])
	return out


## Per slip: 1 true, 0 false, -1 not decided yet (a tag it names is not hung).
func board_slip_status() -> Array:
	var h := ArchiveExpData.hooks_of(state["board"])
	var out: Array = []
	for s: Array in board_slips():
		var needs: Array[int] = [int(s[1])]
		if int(s[0]) in [ArchiveExpData.SLIP_LEFT, ArchiveExpData.SLIP_NEXT]:
			needs.append(int(s[2]))
		var known := true
		for t in needs:
			if int(h[t]) < 0:
				known = false
		out.append(-1 if not known else (1 if ArchiveExpData.slip_true(s, h) else 0))
	return out


func n8_hang(tag: int, hook: int) -> Array[String]:
	_begin()
	if exp_stage() < 2 or not room_seen("gallery") or state["board_ok"] or tag < 0 or tag >= ArchiveExpData.TAGS \
			or hook < 0 or hook >= ArchiveExpData.HOOKS:
		_emit("nothing_happens")
		return _end()
	var b: Array = state["board"]
	var from := b.find(tag)
	if from == hook:
		_emit("nothing_happens")
		return _end()
	var displaced := int(b[hook])
	if from >= 0:
		b[from] = displaced # a displaced tag takes the old hook (or goes back to the tray)
	b[hook] = tag
	_emit("tag_hung:%d:%d" % [tag, hook])
	if not b.has(-1):
		if not board_slip_status().has(0):
			state["board_ok"] = true
			_emit("board_ok")
			_emit("solved:board")
		else:
			_emit("board_wrong")
	return _end()


func n8_lift_tag(hook: int) -> Array[String]:
	_begin()
	if exp_stage() < 2 or state["board_ok"] or hook < 0 or hook >= ArchiveExpData.HOOKS or int(state["board"][hook]) < 0:
		_emit("nothing_happens")
		return _end()
	state["board"][hook] = -1
	_emit("tag_lifted:%d" % hook)
	return _end()


# ================================================================== N9 Enlarger (Stage B)
func cabinet_label() -> int:
	return int(state["v_strips"][int(state["v_strip"])])


## What the lens throws on the paper now: {"strip": symbol or -1, "sharp": bool, "sized": bool, "digits": bool}.
func enlarger_image() -> Dictionary:
	var sharp := int(state["en_focus"]) == int(state["v_pfocus"])
	var sized := int(state["en_zoom"]) == int(state["v_zoom"])
	var strip := int(state["en_strip"])
	return {"strip": -1 if strip < 0 else int(state["v_strips"][strip]), "sharp": sharp, "sized": sized,
		"digits": strip == int(state["v_strip"]) and sharp and sized}


func n9_load_strip(i: int) -> Array[String]:
	_begin()
	if exp_stage() < 2 or not room_open("plate") or i < 0 or i >= ArchiveExpData.STRIPS:
		_emit("nothing_happens")
		return _end()
	state["en_strip"] = i
	_emit("strip_loaded:%d" % i)
	_check_print()
	return _end()


func n9_zoom(delta: int) -> Array[String]:
	_begin()
	if exp_stage() < 2 or not room_open("plate"):
		_emit("nothing_happens")
		return _end()
	state["en_zoom"] = clampi(int(state["en_zoom"]) + delta, 0, ArchiveExpData.ENL_ZOOM_STEPS - 1)
	_emit("enl_zoom:%d" % int(state["en_zoom"]))
	_check_print()
	return _end()


func n9_focus(delta: int) -> Array[String]:
	_begin()
	if exp_stage() < 2 or not room_open("plate"):
		_emit("nothing_happens")
		return _end()
	state["en_focus"] = clampi(int(state["en_focus"]) + delta, 0, ArchiveExpData.ENL_FOCUS_STEPS - 1)
	_emit("enl_focus:%d" % int(state["en_focus"]))
	_check_print()
	return _end()


func _check_print() -> void:
	if int(state["en_strip"]) < 0:
		return
	var img := enlarger_image()
	_emit("print_view:%d:%d" % [int(img["sharp"]), int(img["sized"])])
	if not (img["sharp"] and img["sized"]) or state["print_ok"]:
		return
	if img["digits"]:
		state["print_ok"] = true
		_add_item("staff_print")
		_emit("print_ready")
		_emit("solved:print")
	else:
		_emit("print_other:%d" % int(state["en_strip"])) # a sharp, right-sized photo of the wrong person


# ================================================================== N10 Strand's cabinet (Stage B)
func cabinet_digits() -> Array:
	return (state["v_digits"] as Array).duplicate()


func n10_turn_wheel(i: int, delta: int = 1) -> Array[String]:
	_begin()
	if exp_stage() < 2 or not room_open("office") or state["cab_open"] or i < 0 or i >= ArchiveExpData.CABINET_WHEELS:
		_emit("nothing_happens")
		return _end()
	state["cab_wheels"][i] = posmod(int(state["cab_wheels"][i]) + delta, 10)
	_emit("cab_wheel:%d:%d" % [i, int(state["cab_wheels"][i])])
	if _arr_eq(state["cab_wheels"], state["v_digits"]):
		state["cab_open"] = true
		_emit("cab_opened")
		_emit("solved:cabinet")
		_bonus_echo("office")
	return _end()


# ================================================================== expansion: hint answers (level 3)
## Level 3 speaks this game's own answer. Numbers shown to the player are 1-based, as the objects are marked.
func _exp_hint_args(goal: String) -> Array:
	match goal:
		"c2x_warm":
			return [panel_letter(), " ".join(BADGE_NO.split(""))]
		"c2x_pipes":
			return [", ".join(pipe_solution().map(func(v: int) -> String: return str(v + 1)))]
		"c2x_light":
			var codes: Array = []
			var t: Array = state["v_sheet_target"]
			for i in 3:
				codes.append("%d%s" % [int(t[2 * i]), "m" if int(t[2 * i + 1]) == 1 else ""])
			return [codes[0], codes[1], codes[2], int(state["v_glyph"][0]), int(state["v_glyph"][1])]
		"c2x_cold_door":
			return [int(state["v_glyph"][0]), int(state["v_glyph"][1])]
		"c2x_aisle":
			var moves: Array = []
			for m: Array in aisle_route_from_here():
				moves.append("%d%s" % [int(m[0]) + 1, ">" if int(m[1]) > 0 else "<"])
			return [aisle_bay() + 1, " ".join(moves)]
		"c2x_frost":
			return (frost_symbols() as Array).map(func(v: int) -> int: return v + 1)
		"c2x_chest":
			return chest_presses()
		"c2x_lift":
			var ws: Array = []
			for i in 4:
				if ArchiveExpData.weights_for(lift_load())[i] == 1:
					ws.append(str(ArchiveExpData.WEIGHTS[i]))
			return [lift_load(), " + ".join(ws)]
		"c2x_board":
			return [" ".join((state["v_board"] as Array).map(func(v: int) -> String: return str(v + 1)))]
		"c2x_print":
			return ["ABCD"[int(state["v_strip"])], int(state["v_zoom"]), int(state["v_pfocus"])]
		"c2x_cabinet":
			return (state["v_digits"] as Array).duplicate()
	return []


# ================================================================== modes: Trial (section 13)
const TRIAL_RESCUE_SECONDS := 1500.0 # 25 minutes without progress: offer, never force


func hints_allowed() -> bool:
	return not trial_active()


func trial_active() -> bool:
	return state["mode"] == "trial" and not state["trial_dropped"]


## Archivist's Trial earns its stamp: chosen at New Game, never switched off. -> true if set.
func set_mode(mode: String) -> bool:
	if not exp_active() or not mode in ["normal", "trial"] or not _fresh_game():
		return false
	state["mode"] = mode
	return true


func _fresh_game() -> bool:
	for id in inventory:
		if not id in ["leyla_badge", "crystal_lens", "floor_plan"]:
			return false
	return (state["taken"] as Dictionary).is_empty() and state["cat_drawer"] == -1


func trial_stamp() -> bool:
	return state["mode"] == "trial" and not state["trial_dropped"]


## After 25 minutes with no progress the game may OFFER to leave the Trial (never forced).
static func trial_offer_due(idle_seconds: float) -> bool:
	return idle_seconds >= TRIAL_RESCUE_SECONDS


func trial_off() -> Array[String]:
	_begin()
	if state["mode"] == "trial" and not state["trial_dropped"]:
		state["trial_dropped"] = true
		_emit("trial_off")
	else:
		_emit("nothing_happens")
	return _end()


func achievements() -> Array[String]:
	var out: Array[String] = []
	if trial_stamp() and state["complete"]:
		out.append("archivist_trial")
	return out


## Event -> caption key ("" when the event has no caption): the scene shows tr() of it in the caption strip.
func caption_key(ev: String) -> String:
	var parts := ev.split(":")
	var base := parts[0]
	if base == "tap" and parts.size() >= 3:
		return "cap2x.tap_" + parts[2]
	if base == "moment" and parts.size() >= 2:
		return str(ArchiveExpData.MOMENTS.get(parts[1], {}).get("caption", ""))
	return "cap2x." + base if ArchiveExpData.CAPTION_EVENTS.has(base) else ""


# ================================================================== helpers
static func _arr_eq(a: Array, b: Array) -> bool:
	if a.size() != b.size():
		return false
	for i in a.size():
		if int(a[i]) != int(b[i]):
			return false
	return true
