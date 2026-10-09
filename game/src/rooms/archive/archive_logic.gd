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
}

const PUZZLE_IDS: Array[String] = ["catalogue", "compressor", "punch", "dispatch", "locker", "hunt",
	"tape", "booth", "splice", "projector", "record", "lock"]


func default_state() -> Dictionary:
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
	}


func is_complete() -> bool:
	return state["complete"]


func setup_from_profile(choices: Dictionary) -> void:
	state["has_lens"] = str(choices.get("ch1_lens", "")) == "take_lens"
	state["ch1_shards"] = int(choices.get("ch1_shards", 0))
	inventory = ["leyla_badge"]
	if state["has_lens"]:
		inventory.append("crystal_lens")


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
	var need: String = SPOTS[spot]["needs"]
	return need == "" or bool(state[need])


func take(spot: String) -> Array[String]:
	_begin()
	if can_take(spot):
		if spot != "tray_card": # the tray holds an endless stack of blank request cards
			state["taken"][spot] = true
		_add_item(SPOTS[spot]["item"])
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
	return []


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
	return PUZZLE_IDS


func solved_count() -> int:
	var flags := [
		state["taken"].get("index_card", false), state["pressure_ok"],
		state["request_ok"] or state["file_delivered"], state["file_delivered"], state["locker_open"],
		state["grille_open"] and state["ledger_open"] and state["hatch_open"],
		(state["clicks_heard"] as Array).size() == TAPES.size(), state["booth_open"], state["reel_repaired"],
		state["film_seen"], state["sign_recorded"], state["vault_unlocked"],
	]
	var n := 0
	for f: bool in flags:
		if f:
			n += 1
	return n


func hint_goal() -> String:
	return ArchiveHints.current_goal(self)


func collectibles() -> Array:
	return [(state["echoes"] as Array).size(), ECHOES.size(), "ui.echoes"]


func epilogue_keys() -> Array[String]:
	var out: Array[String] = ["epi2.42nd", "epi2.strand_key" if state["choice"] == "strand_key" else "epi2.leyla_key"]
	if (state["echoes"] as Array).size() == ECHOES.size():
		out.append("epi2.echoes")
	out.append("epi2.recorder")
	return out


func profile_choices() -> Dictionary:
	return {"ch2_key": state["choice"], "ch2_echoes": (state["echoes"] as Array).size()}


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


# ================================================================== helpers
static func _arr_eq(a: Array, b: Array) -> bool:
	if a.size() != b.size():
		return false
	for i in a.size():
		if int(a[i]) != int(b[i]):
			return false
	return true
