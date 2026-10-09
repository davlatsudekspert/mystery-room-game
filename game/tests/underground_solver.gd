class_name UndergroundSolver
extends RefCounted
## Scripted solver that finishes Chapter 3 from ANY reachable state (both wing orders, both lens paths).
## Used by the no-softlock fuzz test: if it succeeds from every random state, the player can too.
## It also plays the 42nd-socket secret when the profile unlocks it.


static func solve(l: UndergroundLogic, choice: String = "leyla", max_steps: int = 800) -> bool:
	for _i in max_steps:
		if l.is_complete():
			return true
		step(l, choice)
	return l.is_complete()


static func step(l: UndergroundLogic, choice: String) -> void:
	var s := l.state
	var first: String = s["entry"]
	var second := "nursery" if first == "choir" else "choir"
	if not wing_done(l, first):
		_wing(l, first)
	elif not s["drum_open"]:
		_rings(l)
	elif not wing_done(l, second):
		_wing(l, second)
	elif not s["array_awake"]:
		_resonance(l)
	else:
		l.choose_ending(choice)


static func wing_done(l: UndergroundLogic, wing: String) -> bool:
	var s := l.state
	if wing == "choir":
		return s["hall_started"]
	return s["crystal_grown"] and s["chamber"] != "clear" and s["shutter_open"]


static func _wing(l: UndergroundLogic, wing: String) -> void:
	if wing == "choir":
		_choir(l)
	else:
		_nursery(l)


# ------------------------------------------------------------------ Choir Hall
static func _choir(l: UndergroundLogic) -> void:
	var s := l.state
	if not s["choir_tuned"]:
		if not l.has_item("resonance_meter"):
			if not s["office_open"]:
				forward(l)
			elif not s["case_open"]:
				for i in 3:
					while int(s["case_wheels"][i]) != UndergroundLogic.CASE_CODE[i] and not s["case_open"]:
						l.turn_case_wheel(i)
			else:
				for spot in ["office_lamp", "office_letters", "meter_case"]:
					if l.can_take(spot):
						l.take(spot)
			return
		tune(l)
		return
	if not s["interlock_done"]:
		forward(l)
		return
	if not l.desk_live():
		backward(l)
		return
	# W4: levers in the counter's order, then the knob to ●
	if int(s["step"]) < UndergroundLogic.LEVERS:
		l.pull_lever(UndergroundLogic.STARTUP[int(s["step"])])
	else:
		l.turn_knob(1)


## Run the interlock forward one action: towards the office door standing open.
static func forward(l: UndergroundLogic) -> void:
	var s := l.state
	var iso: Array = s["iso"]
	var cab_in: Array = s["cab_in"]
	if s["office_open"]:
		return
	if s["office_key"]:
		l.toggle_office()
	elif l.has_item("key_square"):
		l.use_item_on("key_square", "office_door")
	elif not iso[2]:
		l.take_cabinet_key(2, "held")
	elif cab_in[2] == "key_circle":
		l.turn_isolator(2)
	elif l.has_item("key_circle"):
		l.use_item_on("key_circle", "cabinet_2")
	elif not iso[0]:
		l.take_cabinet_key(0, "held")
	elif cab_in[0] == "key_triangle":
		l.turn_isolator(0)
	elif l.has_item("key_triangle"):
		l.use_item_on("key_triangle", "cabinet_0")
	elif not iso[1]:
		l.take_cabinet_key(1, "held")
	elif cab_in[1] == "key_diamond":
		l.turn_isolator(1)
	elif l.has_item("key_diamond"):
		l.use_item_on("key_diamond", "cabinet_1")
	else:
		l.take("desk_hook")


## Run the interlock backward one action: towards every isolator ON (office closed, keys home).
static func backward(l: UndergroundLogic) -> void:
	var s := l.state
	var iso: Array = s["iso"]
	var held: Array = s["cab_held"]
	var cab_in: Array = s["cab_in"]
	if s["office_open"]:
		l.toggle_office()
	elif s["office_key"]:
		l.take_office_key()
	elif not iso[2]:
		if not held[2]:
			l.use_item_on("key_square", "cabinet_2")
		else:
			l.turn_isolator(2)
	elif not iso[0]:
		if held[0]:
			l.turn_isolator(0)
		elif l.has_item("key_circle"):
			l.use_item_on("key_circle", "cabinet_0")
		elif cab_in[2] == "key_circle":
			l.take_cabinet_key(2, "in")
	elif not iso[1]:
		if held[1]:
			l.turn_isolator(1)
		elif l.has_item("key_triangle"):
			l.use_item_on("key_triangle", "cabinet_1")
		elif cab_in[0] == "key_triangle":
			l.take_cabinet_key(0, "in")
	else:
		l.turn_isolator(0) # all ON but the desk is not armed yet: cannot happen once the office was opened


## Hang every tube in its slot, then strike the master hammer.
static func tune(l: UndergroundLogic) -> void:
	var s := l.state
	var t: Array = s["tubes"]
	var hand := int(s["tube_hand"])
	if hand != 0:
		l.tap_tube(UndergroundLogic.CHOIR_TARGET.find(hand))
		return
	for k in UndergroundLogic.SLOTS:
		if int(t[k]) != UndergroundLogic.CHOIR_TARGET[k]:
			if int(t[k]) != 0:
				l.tap_tube(k)
			else:
				l.tap_tube(t.find(UndergroundLogic.CHOIR_TARGET[k]))
			return
	l.strike_hammer()


# ------------------------------------------------------------------ Nursery
static func _nursery(l: UndergroundLogic) -> void:
	var s := l.state
	var right := UndergroundLogic.SEED_RIGHT
	if not s["crystal_grown"]:
		var from := int(s["seed_from"])
		if from >= 0 and from != right:
			_bring_seed_home(l)
		elif from < 0:
			if int(s["seed_drawer"]) != right:
				l.open_seed_drawer(right)
			l.take("seed_drawer")
		else:
			_grow(l)
		return
	if s["chamber"] == "clear":
		if s["ac_closed"]:
			l.toggle_autoclave()
		l.take("autoclave")
		return
	if not s["camp_open"]:
		var p := int(s["prism_p"])
		var q := int(s["prism_q"])
		if p != UndergroundLogic.PRISM_P:
			l.turn_prism("p", signi(UndergroundLogic.PRISM_P - p))
		else:
			l.turn_prism("q", signi(UndergroundLogic.PRISM_Q - q))
		return
	if not s["shutter_open"]:
		var want: int = UndergroundLogic.MELODY[(s["melody_input"] as Array).size()]
		l.tap_crystal(UndergroundLogic.FRAME_SIZES.find(want))


## A wrong seed is in play: remelt it if needed and put it back in its drawer.
static func _bring_seed_home(l: UndergroundLogic) -> void:
	var s := l.state
	if l.has_item("seed_crystal"):
		l.use_item_on("seed_crystal", "seed_library")
	elif s["chamber"] == "cloudy":
		l.remelt()
	elif s["chamber"] == "seed":
		if s["ac_closed"]:
			l.toggle_autoclave()
		l.take("autoclave")
	elif l.has_item("cloudy_crystal"):
		if s["ac_closed"]:
			l.toggle_autoclave()
		l.use_item_on("cloudy_crystal", "autoclave")


## The right seed is in play: get it into the chamber, programme 5-2-4, close, start.
static func _grow(l: UndergroundLogic) -> void:
	var s := l.state
	match str(s["chamber"]):
		"cloudy":
			l.remelt()
		"seed":
			for i in 3:
				while int(s["pegs"][i]) != UndergroundLogic.PEGS_TARGET[i]:
					l.turn_peg(i)
			if not s["ac_closed"]:
				l.toggle_autoclave()
			l.pull_start_lever()
		"":
			var item := "seed_crystal" if l.has_item("seed_crystal") else "cloudy_crystal"
			if s["ac_closed"]:
				l.toggle_autoclave()
			l.use_item_on(item, "autoclave")


# ------------------------------------------------------------------ Gallery
static func _rings(l: UndergroundLogic) -> void:
	var s := l.state
	for i in 4:
		while int(s["drums"][i]) != UndergroundLogic.DRUM_TARGET[i]:
			l.turn_drum(i)
	l.pull_drum_handle()


static func _resonance(l: UndergroundLogic) -> void:
	var s := l.state
	if s["socket_42"] != "":
		l.take_from_socket_42()
		return
	if s["secret"] and not s["true_ending"] and l.has_item("nursery_crystal"):
		l.use_item_on("nursery_crystal", "socket_42")
		return
	if s["cradle"] != "nursery_crystal":
		l.use_item_on("nursery_crystal", "cradle")
		return
	var x := int(s["freq_x"])
	if x != UndergroundLogic.FREQ_X:
		l.turn_freq("x", signi(UndergroundLogic.FREQ_X - x))
		return
	var y := int(s["freq_y"])
	l.turn_freq("y", signi(UndergroundLogic.FREQ_Y - y))
