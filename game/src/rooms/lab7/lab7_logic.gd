class_name Lab7Logic
extends RoomLogic
## Chapter 1 "The Locked Laboratory" — complete puzzle logic for Laboratory 7 and Leyla's darkroom.
## Puzzle data mirrors docs/PUZZLE_DESIGN.md and tools/textures/make_decals.py (single source of truth).

const DRAWER_CODE: Array[int] = [0, 3, 1, 7]
const GEAR_POSITIONS := 6
const GEAR_START: Array[int] = [1, 3, 2]
const SAFE_CODE := "7294"
## switch -> lamps toggled [LOCK, LIGHT, ARRAY, VENT]
const SWITCH_MATRIX: Array = [[1, 0, 0, 1], [0, 1, 0, 0], [0, 0, 1, 1], [1, 1, 0, 0], [0, 1, 1, 1]]
const LAMP_TARGET: Array[int] = [1, 1, 1, 0]
const RADIO_START := 80
const RADIO_TARGET := 36
const RADIO_TOLERANCE := 2
const RADIO_NEAR := 10
const BEACON_PULSES: Array[int] = [2, 6, 3]
const BOOK_COUNT := 9
const SHADOW_STEPS := 6 # 30° steps
const SHADOW_START: Array[int] = [2, 2] # ring yaw, rod tilt
const RING_COLORS: Array[String] = ["crimson", "amber", "green", "cobalt", "violet", "white"]
const RING_TARGET: Array[int] = [0, 3, 2] # crimson, cobalt, green (densities 1.84, 1.26, 0.79)
const RING_START := 5
const MIRROR_STEPS := 8 # 45° steps; normal angle = step * 45° in the XZ plane (x east, z south)
const MIRROR_A_START := 0
const MIRROR_B_START := 4
const SHARDS: Array[String] = ["under_desk", "bookshelf_top", "radiator", "coat_pocket", "darkroom"]

## Beam plan geometry (x, z) at height 1.15 m. See docs/PUZZLE_DESIGN.md P12.
const PROJECTOR_POS := Vector2(-2.3, 1.6)
const PROJECTOR_DIR := Vector2(1, 0)
const MIRROR_A_POS := Vector2(1.6, 1.6)
const MIRROR_B_POS := Vector2(1.6, 0.12)
const LOCK_POS := Vector2(2.97, 0.12)
const HIT_RADIUS := 0.12
const ROOM_MIN := Vector2(-3.0, -2.5)
const ROOM_MAX := Vector2(3.0, 2.5)

## spot -> item it yields, plus the state flag that must be true for the spot to be reachable
const SPOTS := {
	"notebook": {"item": "notebook", "needs": ""},
	"drawer_lamp": {"item": "uv_lamp_empty", "needs": "drawer_open"},
	"box_cell": {"item": "battery_cell", "needs": "box_open"},
	"safe_key": {"item": "brass_key", "needs": "safe_open"},
	"safe_lens": {"item": "crystal_lens", "needs": "safe_open"},
	"safe_letter": {"item": "strand_letter", "needs": "safe_open"},
	"safe_valve": {"item": "radio_valve", "needs": "safe_open"},
	"compartment_handle": {"item": "breaker_handle", "needs": "compartment_open"},
	"compartment_photo": {"item": "leyla_photo", "needs": "compartment_open"},
	"cabinet_mirror": {"item": "mirror_item", "needs": "cabinet_open"},
}


func default_state() -> Dictionary:
	return {
		"taken": {},
		"drawer": [0, 0, 0, 0],
		"drawer_open": false,
		"gears": GEAR_START.duplicate(),
		"box_open": false,
		"uv_page": false,
		"uv_desk": false,
		"safe_input": "",
		"safe_open": false,
		"rosette": false,
		"compartment_open": false,
		"handle_installed": false,
		"switches": [0, 0, 0, 0, 0],
		"main_on": false,
		"power_on": false,
		"trips": 0,
		"valve_installed": false,
		"dial": RADIO_START,
		"signal_heard": false,
		"books": [],
		"shelf_open": false,
		"shadow": SHADOW_START.duplicate(),
		"cabinet_open": false,
		"lens_at": "none", # none (not found yet) | inventory | projector | socket
		"emblem_recorded": false,
		"rings": [RING_START, RING_START, RING_START],
		"beam_on": false,
		"mirror_b_mounted": false,
		"mirrors": [MIRROR_A_START, MIRROR_B_START],
		"door_open": false,
		"shards": [],
		"choice": "",
		"complete": false,
	}


func recipes() -> Array:
	return [["uv_lamp_empty", "battery_cell", "uv_lamp"]]


func is_complete() -> bool:
	return state["complete"]


func has_uv() -> bool:
	return has_item("uv_lamp")


# ================================================================== pick-ups
func can_take(spot: String) -> bool:
	if not SPOTS.has(spot) or state["taken"].get(spot, false):
		return false
	var need: String = SPOTS[spot]["needs"]
	return need == "" or bool(state[need])


func take(spot: String) -> Array[String]:
	_begin()
	if can_take(spot):
		state["taken"][spot] = true
		var item: String = SPOTS[spot]["item"]
		_add_item(item)
		if item == "crystal_lens":
			state["lens_at"] = "inventory"
	else:
		_emit("nothing_happens")
	return _end()


## Optional collectibles; visible (and collectible) only under UV light.
func collect_shard(id: String) -> Array[String]:
	_begin()
	if SHARDS.has(id) and has_uv() and not (state["shards"] as Array).has(id):
		if id == "darkroom" and not state["shelf_open"]:
			_emit("nothing_happens")
			return _end()
		(state["shards"] as Array).append(id)
		_emit("shard_collected:" + id)
		if (state["shards"] as Array).size() == SHARDS.size():
			_emit("all_shards")
	else:
		_emit("nothing_happens")
	return _end()


# ================================================================== P1 drawer
func step_drawer_wheel(i: int, delta: int) -> Array[String]:
	_begin()
	if state["drawer_open"] or i < 0 or i > 3:
		_emit("drawer_static")
		return _end()
	var w: Array = state["drawer"]
	w[i] = posmod(int(w[i]) + delta, 10)
	_emit("drawer_wheel:%d:%d" % [i, w[i]])
	if _arr_eq(w, DRAWER_CODE):
		state["drawer_open"] = true
		_emit("drawer_opened")
		_emit("solved:drawer")
	return _end()


# ================================================================== P2 gear box
func press_gear(i: int) -> Array[String]:
	_begin()
	if state["box_open"] or i < 0 or i > 2:
		_emit("box_static")
		return _end()
	var g: Array = state["gears"]
	g[i] = (int(g[i]) + 1) % GEAR_POSITIONS
	var j := (i + 1) % 3
	g[j] = (int(g[j]) + 1) % GEAR_POSITIONS
	_emit("gears:%d:%d:%d" % [g[0], g[1], g[2]])
	if int(g[0]) == 0 and int(g[1]) == 0 and int(g[2]) == 0:
		state["box_open"] = true
		_emit("box_opened")
		_emit("solved:gearbox")
	return _end()


# ================================================================== P3 combine (RoomLogic.combine)
func _on_combined(result: String) -> void:
	if result == "uv_lamp":
		_emit("solved:lamp")


# ================================================================== UV reveals (P4 / P5)
func uv_reveal(target: String) -> Array[String]:
	_begin()
	if not has_uv():
		_emit("nothing_happens")
		return _end()
	match target:
		"notebook_page":
			if has_item("notebook") and not state["uv_page"]:
				state["uv_page"] = true
				_emit("uv_revealed:notebook_page")
		"desk_mark":
			if not state["uv_desk"]:
				state["uv_desk"] = true
				_emit("uv_revealed:desk_mark")
		_:
			_emit("nothing_happens")
	return _end()


# ================================================================== P4 safe
func safe_press(key: String) -> Array[String]:
	_begin()
	if state["safe_open"]:
		_emit("safe_static")
		return _end()
	var inp: String = state["safe_input"]
	match key:
		"C":
			state["safe_input"] = ""
			_emit("safe_cleared")
		"E":
			if inp == SAFE_CODE:
				state["safe_open"] = true
				state["safe_input"] = ""
				_emit("safe_opened")
				_emit("solved:safe")
			else:
				state["safe_input"] = ""
				_emit("safe_denied")
		_:
			if key.length() == 1 and key.is_valid_int():
				if inp.length() < 4:
					state["safe_input"] = inp + key
				_emit("safe_key:" + key)
			else:
				_emit("nothing_happens")
	return _end()


# ================================================================== P5 desk compartment
func press_rosette() -> Array[String]:
	_begin()
	if not state["rosette"]:
		state["rosette"] = true
		_emit("keyhole_revealed")
	else:
		_emit("rosette_click")
	return _end()


# ================================================================== P6 Panel 7
func lamps() -> Array[int]:
	var out: Array[int] = [0, 0, 0, 0]
	if not state["main_on"]:
		return out
	var sw: Array = state["switches"]
	for i in 5:
		if int(sw[i]) == 1:
			for j in 4:
				out[j] ^= int(SWITCH_MATRIX[i][j])
	return out


func _raw_lamps() -> Array[int]:
	var out: Array[int] = [0, 0, 0, 0]
	var sw: Array = state["switches"]
	for i in 5:
		if int(sw[i]) == 1:
			for j in 4:
				out[j] ^= int(SWITCH_MATRIX[i][j])
	return out


func toggle_switch(i: int) -> Array[String]:
	_begin()
	if i < 0 or i > 4:
		return _end()
	if state["power_on"]:
		_emit("switches_locked")
		return _end()
	var sw: Array = state["switches"]
	sw[i] = 1 - int(sw[i])
	_emit("switch:%d:%d" % [i, sw[i]])
	if state["main_on"]:
		_evaluate_power()
	return _end()


func toggle_main() -> Array[String]:
	_begin()
	if not state["handle_installed"]:
		_emit("main_no_handle")
		return _end()
	if state["power_on"]:
		_emit("main_locked")
		return _end()
	if state["main_on"]:
		state["main_on"] = false
		_emit("main_off")
		return _end()
	state["main_on"] = true
	_emit("main_on")
	_evaluate_power()
	return _end()


func _evaluate_power() -> void:
	var l := _raw_lamps()
	if l[3] == 1:
		state["main_on"] = false
		state["trips"] = int(state["trips"]) + 1
		_emit("breaker_tripped")
		return
	_emit("lamps:%d%d%d%d" % [l[0], l[1], l[2], l[3]])
	if _arr_eq(l, LAMP_TARGET):
		state["power_on"] = true
		_emit("power_restored")
		_emit("solved:circuits")


# ================================================================== P7/P8 radio
func radio_status() -> String:
	if not state["power_on"] or not state["valve_installed"]:
		return "dead"
	var d: int = absi(int(state["dial"]) - RADIO_TARGET)
	if d <= RADIO_TOLERANCE:
		return "signal"
	if d <= RADIO_NEAR:
		return "near"
	return "static"


## 0..1 clarity used by audio/visuals (1 = clean beacon).
func radio_clarity() -> float:
	if radio_status() == "dead":
		return 0.0
	var d: float = absf(float(state["dial"]) - RADIO_TARGET)
	return clampf(1.0 - maxf(0.0, d - RADIO_TOLERANCE) / float(RADIO_NEAR), 0.0, 1.0)


func set_dial(v: int) -> Array[String]:
	_begin()
	var nv := clampi(v, 0, 100)
	if nv == int(state["dial"]):
		return _end()
	state["dial"] = nv
	_emit("dial:%d" % nv)
	if radio_status() == "signal" and not state["signal_heard"]:
		state["signal_heard"] = true
		_emit("radio_signal")
		_emit("solved:radio")
	return _end()


func step_dial(delta: int) -> Array[String]:
	return set_dial(int(state["dial"]) + delta)


# ================================================================== P9 encyclopedia
func pull_book(n: int) -> Array[String]:
	_begin()
	if state["shelf_open"] or n < 1 or n > BOOK_COUNT:
		_emit("nothing_happens")
		return _end()
	var b: Array = state["books"]
	b.append(n)
	while b.size() > BEACON_PULSES.size():
		b.pop_front()
	_emit("book_pulled:%d" % n)
	if _arr_eq(b, BEACON_PULSES):
		state["shelf_open"] = true
		_emit("shelf_opened")
		_emit("solved:books")
	return _end()


# ================================================================== P10 shadow lock + Light Memory
## Ring faces the lamp and the rod stands upright. 6 steps of 30° span 180°, and both parts are
## symmetric under a half turn, so step 0 is the only aligned position for each.
func shadow_aligned() -> bool:
	var s: Array = state["shadow"]
	return int(s[0]) == 0 and int(s[1]) == 0


func turn_sculpture(part: int) -> Array[String]:
	_begin()
	if not state["shelf_open"] or part < 0 or part > 1:
		_emit("nothing_happens")
		return _end()
	var s: Array = state["shadow"]
	s[part] = (int(s[part]) + 1) % SHADOW_STEPS
	_emit("shadow:%d:%d" % [s[0], s[1]])
	_check_shadow()
	return _end()


func _check_shadow() -> void:
	if not state["power_on"] or not shadow_aligned():
		return
	if not state["cabinet_open"]:
		state["cabinet_open"] = true
		_emit("cabinet_opened")
		_emit("solved:shadow")
	if state["lens_at"] == "socket" and not state["emblem_recorded"]:
		state["emblem_recorded"] = true
		_emit("emblem_recorded")
		_emit("solved:record")


# ================================================================== P11 projector
func turn_ring(i: int) -> Array[String]:
	_begin()
	if i < 0 or i > 2:
		return _end()
	if state["beam_on"]:
		_emit("rings_locked")
		return _end()
	var r: Array = state["rings"]
	r[i] = (int(r[i]) + 1) % RING_COLORS.size()
	_emit("ring:%d:%d" % [i, r[i]])
	return _end()


func rings_tuned() -> bool:
	return _arr_eq(state["rings"], RING_TARGET)


func pull_projector_lever() -> Array[String]:
	_begin()
	if state["beam_on"]:
		_emit("beam_already_on")
		return _end()
	if not state["power_on"]:
		_emit("projector_no_power")
		return _end()
	if state["lens_at"] != "projector":
		_emit("projector_no_lens")
		return _end()
	if not rings_tuned():
		_emit("projector_scatter")
		return _end()
	state["beam_on"] = true
	_emit("beam_on")
	_emit("solved:projector")
	_check_beam()
	return _end()


# ================================================================== lens placement (M1)
func remove_lens() -> Array[String]:
	_begin()
	if state["lens_at"] in ["projector", "socket"]:
		if state["lens_at"] == "projector" and state["beam_on"]:
			state["beam_on"] = false
			_emit("beam_off")
		state["lens_at"] = "inventory"
		_add_item("crystal_lens")
		_emit("lens_removed")
	else:
		_emit("nothing_happens")
	return _end()


# ================================================================== P12 mirrors + light lock
func rotate_mirror(which: int, delta: int = 1) -> Array[String]:
	_begin()
	if which < 0 or which > 1 or (which == 1 and not state["mirror_b_mounted"]):
		_emit("nothing_happens")
		return _end()
	var m: Array = state["mirrors"]
	m[which] = posmod(int(m[which]) + delta, MIRROR_STEPS)
	_emit("mirror:%d:%d" % [which, m[which]])
	if state["beam_on"]:
		_check_beam()
	return _end()


static func mirror_normal(step: int) -> Vector2:
	var a := deg_to_rad(step * 45.0)
	return Vector2(cos(a), sin(a))


## Returns {"points": PackedVector2Array (x,z), "end": "lock"|"wall"|"mirror_back", "bounces": int}
func trace_beam() -> Dictionary:
	var pts := PackedVector2Array([PROJECTOR_POS])
	var p := PROJECTOR_POS
	var d := PROJECTOR_DIR
	var last := ""
	var mirrors := {"a": MIRROR_A_POS}
	if state["mirror_b_mounted"]:
		mirrors["b"] = MIRROR_B_POS
	for bounce in 8:
		var best_t := INF
		var best := ""
		for key: String in mirrors:
			if key == last:
				continue
			var t := _ray_hit(p, d, mirrors[key])
			if t < best_t:
				best_t = t
				best = key
		var tl := _ray_hit(p, d, LOCK_POS)
		if tl < best_t:
			best_t = tl
			best = "lock"
		if best == "":
			pts.append(_wall_hit(p, d))
			return {"points": pts, "end": "wall", "bounces": bounce}
		if best == "lock":
			pts.append(LOCK_POS)
			return {"points": pts, "end": "lock", "bounces": bounce}
		var pos: Vector2 = mirrors[best]
		pts.append(pos)
		var n := mirror_normal(int(state["mirrors"][0 if best == "a" else 1]))
		if d.dot(n) > -0.01:
			return {"points": pts, "end": "mirror_back", "bounces": bounce}
		d = (d - 2.0 * d.dot(n) * n).normalized()
		d = Vector2(snappedf(d.x, 1e-6), snappedf(d.y, 1e-6)).normalized()
		p = pos
		last = best
	return {"points": pts, "end": "wall", "bounces": 8}


func _ray_hit(p: Vector2, d: Vector2, target: Vector2) -> float:
	var to := target - p
	var t := to.dot(d)
	if t < 0.05:
		return INF
	if (to - d * t).length() > HIT_RADIUS:
		return INF
	return t


func _wall_hit(p: Vector2, d: Vector2) -> Vector2:
	var t := INF
	if d.x > 1e-6:
		t = minf(t, (ROOM_MAX.x - p.x) / d.x)
	elif d.x < -1e-6:
		t = minf(t, (ROOM_MIN.x - p.x) / d.x)
	if d.y > 1e-6:
		t = minf(t, (ROOM_MAX.y - p.y) / d.y)
	elif d.y < -1e-6:
		t = minf(t, (ROOM_MIN.y - p.y) / d.y)
	return p + d * t


func _check_beam() -> void:
	if not state["beam_on"] or state["door_open"]:
		return
	var tr := trace_beam()
	_emit("beam_path:" + str(tr["end"]))
	if tr["end"] == "lock":
		if state["emblem_recorded"]:
			state["door_open"] = true
			_emit("door_unlocked")
			_emit("solved:mirrors")
		else:
			_emit("lock_waits_for_sign")


# ================================================================== using items on things
func use_item_on(item: String, target: String) -> Array[String]:
	if not has_item(item):
		_begin()
		_emit("nothing_happens")
		return _end()
	if item == "uv_lamp":
		return uv_reveal(target)
	_begin()
	match [item, target]:
		["brass_key", "desk_keyhole"]:
			if state["rosette"] and not state["compartment_open"]:
				state["compartment_open"] = true
				_remove_item("brass_key")
				_emit("compartment_opened")
				_emit("solved:compartment")
			else:
				_emit("nothing_happens")
		["breaker_handle", "panel_main"]:
			state["handle_installed"] = true
			_remove_item("breaker_handle")
			_emit("handle_installed")
		["radio_valve", "radio"]:
			state["valve_installed"] = true
			_remove_item("radio_valve")
			_emit("valve_installed")
			if radio_status() == "signal" and not state["signal_heard"]:
				state["signal_heard"] = true
				_emit("radio_signal")
				_emit("solved:radio")
		["crystal_lens", "projector"]:
			state["lens_at"] = "projector"
			_remove_item("crystal_lens")
			_emit("lens_in_projector")
		["crystal_lens", "emblem_socket"]:
			if state["shelf_open"]:
				state["lens_at"] = "socket"
				_remove_item("crystal_lens")
				_emit("lens_in_socket")
				_check_shadow()
			else:
				_emit("nothing_happens")
		["mirror_item", "mirror_stand_b"]:
			state["mirror_b_mounted"] = true
			_remove_item("mirror_item")
			_emit("mirror_mounted")
			if state["beam_on"]:
				_check_beam()
		_:
			_emit("nothing_happens")
	return _end()


# ================================================================== finale
func choose_ending(option: String) -> Array[String]:
	_begin()
	if not state["door_open"] or state["complete"] or not option in ["take_lens", "leave_lens"]:
		_emit("nothing_happens")
		return _end()
	state["choice"] = option
	state["complete"] = true
	if option == "take_lens":
		state["lens_at"] = "inventory"
		_add_item("crystal_lens")
	_emit("choice:" + option)
	_emit("chapter_complete")
	return _end()


# ================================================================== helpers
static func _arr_eq(a: Array, b: Array) -> bool:
	if a.size() != b.size():
		return false
	for i in a.size():
		if int(a[i]) != int(b[i]):
			return false
	return true


## Ordered list of puzzle ids for progress display.
const PUZZLE_IDS: Array[String] = ["drawer", "gearbox", "lamp", "safe", "compartment", "circuits",
	"radio", "books", "shadow", "record", "projector", "mirrors"]


func puzzle_ids() -> Array[String]:
	return PUZZLE_IDS


func hint_goal() -> String:
	return Lab7Hints.current_goal(self)


func choice_options() -> Array:
	return [["take_lens", "ui.take_lens"], ["leave_lens", "ui.leave_lens"]]


func collectibles() -> Array:
	return [(state["shards"] as Array).size(), SHARDS.size(), "ui.shards"]


func epilogue_keys() -> Array[String]:
	var out: Array[String] = ["outro.listening", "epi.take" if state["choice"] == "take_lens" else "epi.leave"]
	if (state["shards"] as Array).size() == SHARDS.size():
		out.append("epi.shards")
	out.append("epi.postmark")
	return out


func profile_choices() -> Dictionary:
	return {"ch1_lens": state["choice"], "ch1_shards": (state["shards"] as Array).size()}


func item_desc_key(id: String) -> String:
	if id == "crystal_lens" and state["emblem_recorded"]:
		return "item.crystal_lens.desc_recorded"
	return super(id)


func item_glows(id: String) -> bool:
	return id == "crystal_lens" and state["emblem_recorded"]


func solved_count() -> int:
	var n := 0
	var flags := {
		"drawer": state["drawer_open"], "gearbox": state["box_open"], "lamp": has_item("uv_lamp") or state["uv_page"] or state["uv_desk"],
		"safe": state["safe_open"], "compartment": state["compartment_open"], "circuits": state["power_on"],
		"radio": state["signal_heard"], "books": state["shelf_open"], "shadow": state["cabinet_open"],
		"record": state["emblem_recorded"], "projector": state["beam_on"] or state["door_open"], "mirrors": state["door_open"],
	}
	for k: String in flags:
		if flags[k]:
			n += 1
	return n
