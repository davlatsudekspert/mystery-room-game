class_name ArrayHallSolver
extends RefCounted
## Scripted solver that finishes Chapter 4 from ANY reachable state (both keys, both lens paths, both trust values,
## with or without the secret). Used by the no-softlock fuzz test: if it succeeds from every random state, the
## player can too. It also posts Leyla's parcel when the profile makes the secret live.


static func solve(l: ArrayHallLogic, choice: String = "leave_lens", max_steps: int = 1200) -> bool:
	for _i in max_steps:
		if l.is_complete():
			return true
		step(l, choice)
	return l.is_complete()


static func step(l: ArrayHallLogic, choice: String) -> void:
	var s := l.state
	if s["night_undone"]:
		l.choose_ending(choice)
	elif s["reversing"]:
		_reverse(l)
	elif not s["power"]:
		_panel(l)
	elif not s["box_open"]:
		_box(l)
	elif not l.sun_steady():
		_sun(l)
	elif not s["iris_open"]:
		_iris(l)
	elif not s["align_done"]:
		_align(l, l.align_target())
	elif l.keys_taken() < ArrayHallLogic.RINGS:
		_keys(l)
	elif not s["cage_open"]:
		_cage(l)
	elif not s["tower_open"]:
		_collar(l)
	elif not s["lens_seated"]:
		l.use_item_on("crystal_lens", "cradle")
	elif not s["pawl_fitted"]:
		_pawl(l)
	elif not l.keeper_on():
		_note(l)
	elif s["secret"] and not s["parcel_sent"] and not _post_ready(l):
		_prepare_post(l)
	elif not l.replay_live():
		_align(l, l.align_target())
	elif int(s["wheel"]) != ArrayHallLogic.FLASH_MINUTE:
		l.scrub()
	else:
		l.lift_master()


# ------------------------------------------------------------------ Act I
static func _panel(l: ArrayHallLogic) -> void:
	var s := l.state
	var want: Array = l.panel_solution()
	for i in ArrayHallLogic.SWITCHES:
		if bool(s["switches"][i]) != want.has(i):
			l.toggle_switch(i)
			return
	l.pull_main()


static func _box(l: ArrayHallLogic) -> void:
	var presses: Array = l.box_solution()
	for i in presses.size():
		if int(presses[i]) > 0:
			l.press_knob(i)
			return


## Lever on, rods together, then back off to the green.
static func _sun(l: ArrayHallLogic) -> void:
	var s := l.state
	if not s["sun_lever"]:
		l.toggle_sun_lever()
		return
	var gap := int(s["gap"])
	match int(s["arc"]):
		ArrayHallLogic.ARC_COLD:
			l.turn_feed(-1 if gap > 0 else 1)
		ArrayHallLogic.ARC_SHORTED:
			l.turn_feed(1)
		_:
			l.turn_feed(signi(l.gap_target() - gap))


static func _iris(l: ArrayHallLogic) -> void:
	for leaf: Variant in l.iris_order():
		if not l.state["iris_up"][int(leaf)]:
			l.lift_leaf(int(leaf))
			return


# ------------------------------------------------------------------ Act II
## One click of the first wheel (outer first) whose ring is off the target; the inner neighbour follows.
static func _align(l: ArrayHallLogic, target: Array) -> void:
	var s := l.state
	if not l.sun_steady():
		_sun(l)
		return
	if not s["iris_open"]:
		_iris(l)
		return
	var turns: Array = l.ring_solution(target)
	for i in turns.size():
		if int(turns[i]) != 0:
			l.turn_ring_wheel(i, signi(int(turns[i])))
			return


static func _keys(l: ArrayHallLogic) -> void:
	var s := l.state
	for i in ArrayHallLogic.RINGS:
		if s["tower_keys"][i]:
			var d := posmod(-int(s["rings"][i]), ArrayHallLogic.MARKS) # only wheel i is turned, so ring i alone counts
			if d != 0:
				l.turn_ring_wheel(i, 1 if d <= ArrayHallLogic.MARKS / 2 else -1)
			else:
				l.take("tower_%d" % (i + 1))
			return


static func _cage(l: ArrayHallLogic) -> void:
	for i in ArrayHallLogic.RINGS:
		if not l.state["gates"][i]:
			l.use_item_on(ArrayHallLogic.TOWER_KEYS[i], "gate_%d" % (i + 1))
			return


static func _collar(l: ArrayHallLogic) -> void:
	var s := l.state
	var want: Array = l.collar_target()
	for i in 4:
		while int(s["collar"][i]) != int(want[i]) and not s["tower_open"]:
			l.turn_collar(i)


# ------------------------------------------------------------------ Act III
static func _pawl(l: ArrayHallLogic) -> void:
	if l.has_item("reverse_pawl"):
		l.use_item_on("reverse_pawl", "chronometer")
	else:
		for spot in ["heart_pawl", "heart_watch", "heart_letter"]:
			if l.can_take(spot):
				l.take(spot)


static func _note(l: ArrayHallLogic) -> void:
	l.turn_keeper(l.note_target() - int(l.state["keeper"]))


# ------------------------------------------------------------------ secret
static func _post_ready(l: ArrayHallLogic) -> bool:
	var s := l.state
	return s["canister"] == "leyla_parcel" and int(s["post_dial"]) == ArrayHallLogic.POST_LAB \
		and int(s["post_number"]) == ArrayHallLogic.POST_NUMBER


static func _prepare_post(l: ArrayHallLogic) -> void:
	var s := l.state
	if s["canister"] != "leyla_parcel":
		if l.has_item("leyla_parcel"):
			l.use_item_on("leyla_parcel", "post_canister")
		else:
			l.take("locker_parcel")
		return
	if int(s["post_dial"]) != ArrayHallLogic.POST_LAB:
		l.turn_post_dial(ArrayHallLogic.POST_LAB - int(s["post_dial"]))
		return
	var n := int(s["post_number"])
	if n != ArrayHallLogic.POST_NUMBER:
		l.turn_post_number(ArrayHallLogic.POST_NUMBER - n)


# ------------------------------------------------------------------ Act IV
## At each minute undo that minute's step, then wind back; post the parcel on the way.
static func _reverse(l: ArrayHallLogic) -> void:
	var s := l.state
	if s["secret"] and not s["parcel_sent"]:
		if _post_ready(l):
			l.send_post()
		else:
			_prepare_post(l)
		return
	match l.undo_at(int(s["wheel"])):
		"keeper":
			if int(s["keeper"]) != 0:
				l.turn_keeper(-int(s["keeper"]))
				return
		"rings":
			if not l.home():
				var turns: Array = l.ring_solution([0, 0, 0, 0])
				for i in turns.size():
					if int(turns[i]) != 0:
						l.turn_ring_wheel(i, signi(int(turns[i])))
						return
		"sun":
			if s["sun_lever"]:
				l.toggle_sun_lever()
				return
	l.wind_back()
