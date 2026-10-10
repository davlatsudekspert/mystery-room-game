extends UndergroundLogic
## QA helper for qa/playthrough_ch3.gd: the Chapter 3 logic that also records every player action the solver makes
## ([method, args]), so one solver step on a copy of the game says what the player should do next.

var calls: Array = []


func _rec(m: String, args: Array) -> void:
	calls.append([m, args])


func take(spot: String) -> Array[String]:
	_rec("take", [spot])
	return super(spot)


func turn_isolator(n: int) -> Array[String]:
	_rec("turn_isolator", [n])
	return super(n)


func take_cabinet_key(n: int, slot: String) -> Array[String]:
	_rec("take_cabinet_key", [n, slot])
	return super(n, slot)


func toggle_office() -> Array[String]:
	_rec("toggle_office", [])
	return super()


func take_office_key() -> Array[String]:
	_rec("take_office_key", [])
	return super()


func turn_case_wheel(i: int, delta: int = 1) -> Array[String]:
	_rec("turn_case_wheel", [i, delta])
	return super(i, delta)


func tap_tube(pos: int) -> Array[String]:
	_rec("tap_tube", [pos])
	return super(pos)


func strike_hammer() -> Array[String]:
	_rec("strike_hammer", [])
	return super()


func pull_lever(n: int) -> Array[String]:
	_rec("pull_lever", [n])
	return super(n)


func turn_knob(delta: int = 1) -> Array[String]:
	_rec("turn_knob", [delta])
	return super(delta)


func open_seed_drawer(i: int) -> Array[String]:
	_rec("open_seed_drawer", [i])
	return super(i)


func toggle_autoclave() -> Array[String]:
	_rec("toggle_autoclave", [])
	return super()


func turn_peg(i: int, delta: int = 1) -> Array[String]:
	_rec("turn_peg", [i, delta])
	return super(i, delta)


func pull_start_lever() -> Array[String]:
	_rec("pull_start_lever", [])
	return super()


func remelt() -> Array[String]:
	_rec("remelt", [])
	return super()


func turn_prism(which: String, delta: int) -> Array[String]:
	_rec("turn_prism", [which, delta])
	return super(which, delta)


func tap_crystal(pos: int) -> Array[String]:
	_rec("tap_crystal", [pos])
	return super(pos)


func turn_drum(i: int, delta: int = 1) -> Array[String]:
	_rec("turn_drum", [i, delta])
	return super(i, delta)


func pull_drum_handle() -> Array[String]:
	_rec("pull_drum_handle", [])
	return super()


func turn_freq(axis: String, delta: int) -> Array[String]:
	_rec("turn_freq", [axis, delta])
	return super(axis, delta)


func take_from_cradle() -> Array[String]:
	_rec("take_from_cradle", [])
	return super()


func take_from_socket_42() -> Array[String]:
	_rec("take_from_socket_42", [])
	return super()


func use_item_on(item: String, target: String) -> Array[String]:
	_rec("use_item_on", [item, target])
	return super(item, target)


func choose_ending(option: String) -> Array[String]:
	_rec("choose_ending", [option])
	return super(option)
