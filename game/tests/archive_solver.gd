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
				if int(s["punch_keys"][i]) != ArchiveLogic.PUNCH_CODE[i]:
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
