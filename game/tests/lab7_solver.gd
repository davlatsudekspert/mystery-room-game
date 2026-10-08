class_name Lab7Solver
extends RefCounted
## Scripted solver that finishes Chapter 1 from ANY reachable state.
## Used by the no-softlock fuzz test: if it succeeds from every random state, the player can too.


static func solve(l: Lab7Logic, choice: String = "leave_lens", max_steps: int = 400) -> bool:
	for _i in max_steps:
		if l.is_complete():
			return true
		step(l, choice)
	return l.is_complete()


static func step(l: Lab7Logic, choice: String) -> void:
	var s := l.state
	if l.can_take("notebook"):
		l.take("notebook")
		return
	if not s["drawer_open"]:
		for i in 4:
			while int(s["drawer"][i]) != Lab7Logic.DRAWER_CODE[i] and not s["drawer_open"]:
				l.step_drawer_wheel(i, 1)
		return
	if l.can_take("drawer_lamp"):
		l.take("drawer_lamp")
		return
	if not s["box_open"]:
		var presses := gear_solution(s["gears"])
		for i in 3:
			for _k in presses[i]:
				l.press_gear(i)
		return
	if l.can_take("box_cell"):
		l.take("box_cell")
		return
	if l.has_item("uv_lamp_empty") and l.has_item("battery_cell"):
		l.combine("uv_lamp_empty", "battery_cell")
		return
	if not s["uv_page"]:
		l.uv_reveal("notebook_page")
		return
	if not s["safe_open"]:
		l.safe_press("C")
		for c in Lab7Logic.SAFE_CODE:
			l.safe_press(c)
		l.safe_press("E")
		return
	for spot in ["safe_key", "safe_lens", "safe_letter", "safe_valve"]:
		if l.can_take(spot):
			l.take(spot)
			return
	if not s["uv_desk"]:
		l.uv_reveal("desk_mark")
		return
	if not s["rosette"]:
		l.press_rosette()
		return
	if not s["compartment_open"]:
		l.use_item_on("brass_key", "desk_keyhole")
		return
	for spot in ["compartment_handle", "compartment_photo"]:
		if l.can_take(spot):
			l.take(spot)
			return
	if not s["handle_installed"]:
		l.use_item_on("breaker_handle", "panel_main")
		return
	if not s["power_on"]:
		if s["main_on"]:
			l.toggle_main()
		var want := [1, 1, 1, 0, 0]
		for i in 5:
			if int(s["switches"][i]) != want[i]:
				l.toggle_switch(i)
		l.toggle_main()
		return
	if not s["valve_installed"]:
		l.use_item_on("radio_valve", "radio")
		return
	if not s["signal_heard"]:
		l.set_dial(Lab7Logic.RADIO_TARGET)
		return
	if not s["shelf_open"]:
		for n in Lab7Logic.BEACON_PULSES:
			l.pull_book(n)
		return
	if not s["cabinet_open"] or not s["emblem_recorded"]:
		if s["lens_at"] == "projector":
			l.remove_lens()
			return
		if s["lens_at"] == "inventory" and l.has_item("crystal_lens") and not s["emblem_recorded"]:
			l.use_item_on("crystal_lens", "emblem_socket")
			return
		var guard := 0
		while not l.shadow_aligned() and guard < 40:
			l.turn_sculpture(0 if int(s["shadow"][0]) != 0 else 1)
			guard += 1
		return
	if l.can_take("cabinet_mirror"):
		l.take("cabinet_mirror")
		return
	if s["lens_at"] == "socket":
		l.remove_lens()
		return
	if s["lens_at"] != "projector":
		l.use_item_on("crystal_lens", "projector")
		return
	if not s["beam_on"]:
		for i in 3:
			while int(s["rings"][i]) != Lab7Logic.RING_TARGET[i]:
				l.turn_ring(i)
		l.pull_projector_lever()
		return
	if not s["mirror_b_mounted"]:
		l.use_item_on("mirror_item", "mirror_stand_b")
		return
	if not s["door_open"]:
		while int(s["mirrors"][0]) != 5:
			l.rotate_mirror(0, 1)
		while int(s["mirrors"][1]) != 1 and not s["door_open"]:
			l.rotate_mirror(1, 1)
		return
	l.choose_ending(choice)


## Brute force the 6^3 knob-press counts that bring all gears to 0 (shortest first).
static func gear_solution(g: Array) -> Array[int]:
	var best: Array[int] = [0, 0, 0]
	var best_n := 999
	for a in 6:
		for b in 6:
			for c in 6:
				var ga := (int(g[0]) + a + c) % 6
				var gb := (int(g[1]) + a + b) % 6
				var gc := (int(g[2]) + b + c) % 6
				if ga == 0 and gb == 0 and gc == 0 and a + b + c < best_n:
					best = [a, b, c]
					best_n = a + b + c
	return best
