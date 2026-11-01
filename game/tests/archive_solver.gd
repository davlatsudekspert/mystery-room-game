class_name ArchiveSolver
extends RefCounted
## Scripted solver that finishes Chapter 2 from ANY reachable state (both Ch1 lens paths).
## Used by the no-softlock fuzz test: if it succeeds from every random state, the player can too.


static func solve(l: ArchiveLogic, choice: String = "leyla_key", max_steps: int = 600) -> bool:
	for _i in max_steps:
		if l.is_complete():
			return true
		step(l, choice)
	return l.is_complete()


static func step(l: ArchiveLogic, choice: String) -> void:
	var s := l.state
	var taken: Dictionary = s["taken"]
	# P1 catalogue
	if not taken.get("index_card", false):
		if not s["card_shown"]:
			if int(s["cat_drawer"]) != ArchiveLogic.CAT_DRAWER:
				l.open_cat_drawer(ArchiveLogic.CAT_DRAWER)
			l.pick_divider(ArchiveLogic.CAT_GROUP)
			l.pull_card(ArchiveLogic.CAT_CARD)
		l.take("index_card")
		return
	# P2 compressor (valves cycle 0..4)
	if not s["pressure_ok"]:
		var want := l.valve_solution()
		for i in 3:
			var guard := 0
			while int(s["valves"][i]) != want[i] and not s["pressure_ok"] and guard < 6:
				l.turn_valve(i)
				guard += 1
		return
	# P3 / P4 request card and dispatch
	if not s["file_delivered"]:
		if s["canister"] != "":
			if int(s["dest"]) != ArchiveLogic.DEST_STACKS:
				l.set_dest(ArchiveLogic.DEST_STACKS)
			l.send_canister()
			return
		if l.has_item("request_card"):
			if s["request_ok"]:
				l.use_item_on("request_card", "send_port")
			else:
				l.use_item_on("request_card", "card_tray")
			return
		if s["card_in_punch"]:
			for i in 8:
				if int(s["punch_keys"][i]) != int(l.punch_code()[i]):
					l.toggle_punch_key(i)
			l.pull_punch_lever()
			return
		if l.has_item("blank_card"):
			l.use_item_on("blank_card", "punch")
			return
		l.take("tray_card")
		return
	for spot in ["canister_file", "canister_key"]:
		if l.can_take(spot):
			l.take(spot)
			return
	# P5 locker
	if not s["locker_open"]:
		l.use_item_on("locker_key", "locker_9")
		return
	if l.can_take("locker_receiver"):
		l.take("locker_receiver")
		return
	# P6 hunt
	for pair in [["grille", "grille_reel"], ["ledger", "ledger_reel"], ["hatch", "hatch_reel"]]:
		if not taken.get(pair[1], false):
			l.open_hiding_place(pair[0])
			l.take(pair[1])
			return
	# P7 tapes
	if (s["clicks_heard"] as Array).size() < ArchiveLogic.TAPES.size():
		if int(s["deck_speed"]) != ArchiveLogic.SPEED_RIGHT:
			l.set_speed(ArchiveLogic.SPEED_RIGHT)
		var tape: String = s["deck_tape"]
		if tape == "" or (s["clicks_heard"] as Array).has(tape):
			for t: String in ArchiveLogic.TAPES:
				if not (s["clicks_heard"] as Array).has(t) and l.has_item(t):
					l.use_item_on(t, "deck")
					break
		l.play_tape()
		return
	# N1-N6 the lower floor (expansion games only)
	if l.exp_active() and _lower_floor(l):
		return
	# P8 booth
	if not s["booth_open"]:
		var guard := 0
		while str(s["dial_input"]) != "" and guard < 3: # finish a half-dialled number first
			l.dial_digit(0)
			guard += 1
		for ch in l.booth_code():
			l.dial_digit(int(ch))
		return
	# P9 splice
	if not s["reel_repaired"]:
		for slot in 4:
			if int(s["splice"][slot]) != int(l.splice_order()[slot]):
				l.splice_put(int(l.splice_order()[slot]), slot)
		return
	if l.can_take("splicer_reel"):
		l.take("splicer_reel")
		return
	# N7-N10 the upper floor and the projector lamp (Stage 2 games only)
	if l.exp_stage() >= 2 and not s["lamp_ok"] and _upper_floor(l):
		return
	# P10 projector
	if not s["film_seen"]:
		if l.has_item("film_reel"):
			l.use_item_on("film_reel", "projector")
		if not s["projector_on"]:
			l.toggle_projector()
		return
	for spot in ["case_crystal_1", "case_crystal_2"]:
		if l.can_take(spot):
			l.take(spot)
			return
	# P11 record the sign
	if not s["sign_recorded"]:
		if s["slide_on"]:
			l.toggle_slide_lamp()
		if not s["projector_on"]:
			l.toggle_projector()
		while int(s["frame"]) < ArchiveLogic.SIGN_FRAME:
			l.step_frame(1)
		while int(s["focus"]) != l.focus_sharp():
			l.turn_focus(1 if int(s["focus"]) < l.focus_sharp() else -1)
		if s["socket"] != "" and not str(s["socket"]).begins_with("crystal_blank"):
			l.take_from_socket()
		if s["socket"] == "":
			var blank := _blank(l)
			if blank != "":
				l.use_item_on(blank, "screen_socket")
		return
	if s["socket"] != "" and not str(s["socket"]).begins_with("crystal_blank"):
		l.take_from_socket()
		return
	# P11b record Strand's mark (leave path)
	if not s["has_lens"] and not s["mark_recorded"]:
		if s["projector_on"]:
			l.toggle_projector()
		if not s["slide_in"]:
			if l.has_item("emblem_slide"):
				l.use_item_on("emblem_slide", "slide_projector")
			else:
				if int(s["slide_drawer"]) != ArchiveLogic.SLIDE_MARK_DRAWER:
					l.open_slide_drawer(ArchiveLogic.SLIDE_MARK_DRAWER)
				l.take("slide_mark")
			return
		while int(s["slide_rot"]) % 2 != 0:
			l.rotate_slide()
		if not s["slide_on"]:
			l.toggle_slide_lamp()
		if s["socket"] == "":
			var blank2 := _blank(l)
			if blank2 != "":
				l.use_item_on(blank2, "screen_socket")
		return
	# P12 ports + alignment
	if not s["vault_unlocked"]:
		var mark := "crystal_lens" if s["has_lens"] else "crystal_mark"
		if l.crystal_image(s["port_left"]) != "mark":
			if s["port_left"] != "":
				l.take_from_port("left")
			_fetch(l, mark)
			l.use_item_on(mark, "port_left")
			return
		if l.crystal_image(s["port_right"]) != "sign":
			if s["port_right"] != "":
				l.take_from_port("right")
			_fetch(l, "crystal_sign")
			l.use_item_on("crystal_sign", "port_right")
			return
		while int(s["rot_left"]) % 4 != 0:
			l.turn_collar("rot_left")
		while int(s["rot_right"]) != l.vault_rot_target():
			l.turn_collar("rot_right")
		while int(s["zoom_right"]) != l.vault_zoom_target() and not s["vault_unlocked"]:
			l.turn_collar("zoom_right")
		return
	if not s["vault_open"]:
		l.turn_wheel()
		return
	l.choose_ending(choice)


## One step of N1-N6 (and the rooms they open). -> true if it did something.
static func _lower_floor(l: ArchiveLogic) -> bool:
	var s := l.state
	var taken: Dictionary = s["taken"]
	if not s["pump_open"]:
		if not s["panel_found"]:
			l.n1_open_panel(int(s["v_panel"]))
			return true
		var typed := str(s["n1_dial"])
		var next := ArchiveLogic.BADGE_NO.substr(typed.length(), 1) if ArchiveLogic.BADGE_NO.begins_with(typed) else "0"
		l.n1_dial(int(next))
		return true
	for room in ["pump", "cell"]:
		if l.room_open(room) and not l.room_seen(room):
			l.enter_room(room)
			return true
	if l.can_take("pump_mallet"):
		l.take("pump_mallet")
		return true
	if not s["thawed"]:
		var want := l.pipe_solution()
		for i in 6:
			if (int(s["pipes"][i]) == 1) != want.has(i):
				l.n2_toggle_valve(i)
				return true
		return false
	if not s["cell_digits_ok"] and not s["cold_open"]:
		var t: Array = s["v_sheet_target"]
		for i in 3:
			if int(s["sheets"][2 * i + 1]) != int(t[2 * i + 1]):
				l.n3_flip_sheet(i)
				return true
			if int(s["sheets"][2 * i]) != int(t[2 * i]):
				l.n3_turn_sheet(i)
				return true
		return false
	if not s["cold_open"]:
		for i in 2:
			if int(s["cold_wheels"][i]) != int(s["v_glyph"][i]):
				l.cold_wheel(i)
				return true
		return false
	if l.room_open("cold") and not l.room_seen("cold"):
		l.enter_room("cold")
		return true
	if not s["aisle"]:
		var route := l.aisle_route_from_here()
		if route.is_empty():
			return false
		l.n4_crank(int(route[0][0]), int(route[0][1]))
		return true
	if not s["frost_seen"]:
		if not taken.get("cell_cloth", false):
			l.take("cell_cloth")
			return true
		for b in 3:
			if int(s["wiped"][b]) == 0:
				l.n5_wipe(b)
				return true
	if not s["chest_open"]:
		var presses := ArchiveExpData.ring_route(s["rings"], l.chest_target())
		if presses.is_empty():
			return false
		l.n6_turn_ring(int(presses[0]))
		return true
	return false


## One step of N7-N10 plus taking and fitting the projector lamp. -> true if it did something.
static func _upper_floor(l: ArchiveLogic) -> bool:
	var s := l.state
	var taken: Dictionary = s["taken"]
	if not s["lift_ok"]:
		var want := ArchiveExpData.weights_for(l.lift_load())
		for i in 4:
			if int(s["weights"][i]) != int(want[i]):
				l.n7_toggle_weight(i)
				return true
		return false
	if not l.room_seen("gallery"):
		l.n7_call(1)
		l.enter_room("gallery")
		return true
	if not s["wedge_out"]:
		l.pull_wedge()
		return true
	if not taken.get("counter_slips", false):
		l.take("counter_slips")
		return true
	if not s["board_ok"]:
		for h in 6:
			if int(s["board"][h]) != int(s["v_board"][h]):
				l.n8_hang(int(s["v_board"][h]), h)
				return true
		return false
	if not taken.get("board_key", false):
		l.take("board_key")
		return true
	if not l.room_seen("plate"):
		l.enter_room("plate")
		return true
	if not s["print_ok"]:
		if int(s["en_strip"]) != int(s["v_strip"]):
			l.n9_load_strip(int(s["v_strip"]))
		elif int(s["en_zoom"]) != int(s["v_zoom"]):
			l.n9_zoom(1 if int(s["en_zoom"]) < int(s["v_zoom"]) else -1)
		elif int(s["en_focus"]) != int(s["v_pfocus"]):
			l.n9_focus(1 if int(s["en_focus"]) < int(s["v_pfocus"]) else -1)
		else:
			return false
		return true
	if not l.room_seen("office"):
		l.enter_room("office")
		return true
	if not s["cab_open"]:
		for i in 4:
			if int(s["cab_wheels"][i]) != int(s["v_digits"][i]):
				l.n10_turn_wheel(i)
				return true
		return false
	if not taken.get("cabinet_lamp", false):
		l.take("cabinet_lamp")
		return true
	l.use_item_on("projector_lamp", "projector")
	return true


## Bring a crystal back to the inventory from the screen socket or a port.
static func _fetch(l: ArchiveLogic, id: String) -> void:
	if l.has_item(id):
		return
	if l.state["socket"] == id:
		l.take_from_socket()
	elif l.state["port_left"] == id:
		l.take_from_port("left")
	elif l.state["port_right"] == id:
		l.take_from_port("right")


## A blank crystal from the inventory, taking one out of a port or the socket if needed.
static func _blank(l: ArchiveLogic) -> String:
	for id in ["crystal_blank_1", "crystal_blank_2"]:
		if l.has_item(id):
			return id
	for side in ["left", "right"]:
		if str(l.state["port_" + side]).begins_with("crystal_blank"):
			var id: String = l.state["port_" + side]
			l.take_from_port(side)
			return id
	return ""
