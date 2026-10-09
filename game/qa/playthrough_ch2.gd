extends Node
## Runtime QA for Chapter 2: loads the real Archive scene and plays the chapter through simulated taps on the
## 3D parts (raycast → hotspot → logic), like a player. A step falls back to a direct logic call only when the
## tap did not work, and every fallback is reported with what the tap hit instead.
## Run: xvfb-run -a godot --path game res://qa/playthrough_ch2.tscn -- --out=<dir> [--lens=take|leave] [--lang=ru]
## A quick logic-flow run without screenshots: godot --headless --path game res://qa/playthrough_ch2.tscn -- …
## Exit code 0 = chapter completed with no failed step and no fallback.

var out_dir := "/tmp/ch2_playthrough"
var room: Node3D
var logic: ArchiveLogic
var report: Array[String] = []
var shot_n := 0
var taps_ok := 0
var taps_fallback := 0
var lens_path := "leave"


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		if a.begins_with("--lang="):
			TranslationServer.set_locale(a.substr(7))
		if a.begins_with("--lens="):
			lens_path = a.substr(7)
	DirAccess.make_dir_recursive_absolute(out_dir)
	SaveSystem.save_path = "user://qa_ch2_save.json"
	SaveSystem.profile_path = "user://qa_ch2_profile.json"
	GameState.profile = {"choices": {"ch1_lens": "take_lens" if lens_path == "take" else "leave_lens", "ch1_shards": 5}}
	GameState.start_new("ch2")
	logic = GameState.logic
	var t0 := Time.get_ticks_msec()
	room = (load("res://src/rooms/archive/archive.tscn") as PackedScene).instantiate()
	room.set("capture_mode", true)
	get_tree().root.add_child.call_deferred(room)
	await get_tree().process_frame
	await get_tree().process_frame
	_log("scene load+build: %d ms (software renderer; phones differ)" % (Time.get_ticks_msec() - t0))
	_log("path: Ch1 lens %s, shards 5" % lens_path)
	await _settle(1.2)
	await _perf("hall")
	await run()


# ====================================================================== helpers
## Report line, also printed at once so a long or stuck run shows how far it got.
func _log(line: String) -> void:
	report.append(line)
	print(line)


func _settle(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()


func _perf(label: String) -> void:
	await _settle(0.5)
	var rs := RenderingServer
	_log("perf[%s]: draw calls %d, primitives %d, objects %d" % [label,
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME)])


func shot(name: String) -> void:
	await _settle(0.3)
	if DisplayServer.get_name() == "headless": # logic-flow runs without a renderer: no pixels to save
		return
	await RenderingServer.frame_post_draw
	shot_n += 1
	var p := "%s/%02d_%s.png" % [out_dir, shot_n, name]
	get_viewport().get_texture().get_image().save_png(p)
	_log("shot %s" % p.get_file())


func cam() -> RoomCamera:
	return room.get("cam")


func view(id: String) -> void:
	cam().go(id)
	await _settle(0.9)


func busy() -> bool:
	return bool((room.get("hud") as Node).get("_busy")) or bool(room.get("_cinematic"))


func wait_idle(limit: float = 40.0) -> void:
	var t := 0.0
	while busy() and t < limit:
		await _settle(0.25)
		t += 0.25


func node_of(model: String, part: String) -> Node3D:
	var root: Node3D = (room.get("models") as Dictionary).get(model)
	if root == null:
		return null
	return root if part == "" else ModelUtil.find(root, part)


func _rect(n: Node3D, own_only: bool) -> Rect2:
	var meshes := ModelUtil.find_meshes(n)
	if own_only and n is MeshInstance3D:
		meshes = [n as MeshInstance3D]
	var r := Rect2()
	var first := true
	for mi in meshes:
		if not mi.is_visible_in_tree():
			continue
		var ab := mi.get_aabb()
		for k in 8:
			var wp := mi.global_transform * ab.get_endpoint(k)
			if cam().is_position_behind(wp):
				return Rect2()
			var sp := cam().unproject_position(wp)
			if first:
				r = Rect2(sp, Vector2.ZERO)
				first = false
			else:
				r = r.expand(sp)
	return r


func _tap_point(model: String, part: String, frac: Vector2) -> Vector2:
	var n := node_of(model, part)
	if n == null:
		return Vector2(-1, -1)
	var r := _rect(n, part != "" and not part.begins_with("Item_"))
	if r.size == Vector2.ZERO:
		return Vector2(-1, -1)
	var sp := r.get_center() + frac * r.size * 0.5
	var vs := get_viewport().get_visible_rect().size
	if sp.x < 0 or sp.y < 0 or sp.x > vs.x or sp.y > vs.y:
		return Vector2(-1, -1)
	if frac != Vector2.ZERO or not part.begins_with("IA_") or _resolves_to(sp, part):
		return sp
	# The middle of a part's bounds can be covered or empty (a deep drawer seen from above, a card behind a tab):
	# a player taps where the part is actually visible, so look for such a point, nearest the middle first.
	var best := sp
	var best_d := INF
	for gy in 7:
		for gx in 7:
			var p := r.position + r.size * Vector2(0.1 + 0.8 * gx / 6.0, 0.1 + 0.8 * gy / 6.0)
			if p.x < 0 or p.y < 0 or p.x > vs.x or p.y > vs.y:
				continue
			var d := p.distance_to(r.get_center())
			if d < best_d and _resolves_to(p, part):
				best = p
				best_d = d
	return best


func _resolves_to(sp: Vector2, part: String) -> bool:
	var h: Dictionary = room.call("raycast", sp)
	return not h.is_empty() and str(room.call("resolve", h)["part"]) == part


func tap(model: String, part: String, frac: Vector2 = Vector2.ZERO) -> void:
	var sp := _tap_point(model, part, frac)
	if sp.x < 0:
		return
	room.call("_on_tap", sp)
	await _settle(0.4)


func _hit(model: String, part: String, frac: Vector2) -> String:
	if node_of(model, part) == null:
		return "part missing"
	var sp := _tap_point(model, part, frac)
	if sp.x < 0:
		return "off-screen/behind camera"
	var h: Dictionary = room.call("raycast", sp)
	if h.is_empty():
		return "nothing"
	var r: Dictionary = room.call("resolve", h)
	return "%s/%s/%s" % [r["model"], r["hotspot"], r["part"]]


## Tap a part; succeed only if `cond` becomes true. Otherwise apply `fallback` (a logic call) and report it.
func act(model: String, part: String, cond: Callable, fallback: Callable, label: String = "", frac: Vector2 = Vector2.ZERO) -> void:
	if not cond.call():
		await tap(model, part, frac)
		await _settle(0.25)
	if cond.call():
		taps_ok += 1
	else:
		var why := _hit(model, part, frac)
		fallback.call()
		taps_fallback += 1
		_log("  fallback: %s (%s/%s, view %s, hit %s)" % [label if label != "" else part, model, part, cam().current(), why])


func step(label: String, ok: bool) -> void:
	_log(("✓ " if ok else "✗ ") + label)


func use(item: String) -> void:
	logic.select_item(item)
	await _settle(0.15)


# ====================================================================== the chapter
func run() -> void:
	var s := logic.state
	var L := logic
	await shot("hall_start")
	await view("west")
	await shot("west_root")
	# P1 catalogue: drawer 04, divider 1–, card 17
	await view("catalogue")
	await shot("catalogue")
	await act("card_catalogue", "IA_cat_drawer_4", func() -> bool: return int(s["cat_drawer"]) == 4, func() -> void: L.open_cat_drawer(4), "drawer 04")
	await _settle(0.8)
	await act("card_catalogue", "IA_divider_1", func() -> bool: return int(s["cat_group"]) == 1, func() -> void: L.pick_divider(1), "divider 1–")
	await _settle(0.5)
	await shot("catalogue_drawer_open")
	await act("card_catalogue", "IA_card_7", func() -> bool: return s["card_shown"], func() -> void: L.pull_card(7), "card 17")
	await act("card_catalogue", "IA_card_7", func() -> bool: return L.has_item("index_card"), func() -> void: L.take("index_card"), "take index card")
	step("P1 catalogue 04 / 1– / 17 → index card", L.has_item("index_card"))
	# P2 compressor: A 1, B 2, C 2
	await view("hall")
	await view("compressor")
	await shot("compressor_rest")
	for pair in [[0, 1], [1, 2], [2, 2]]:
		var i: int = pair[0]
		for _k in int(pair[1]):
			var v0 := int(s["valves"][i])
			await act("compressor_panel", "IA_valve_" + "abc"[i], func() -> bool: return int(s["valves"][i]) != v0 or s["pressure_ok"],
				func() -> void: L.turn_valve(i, 1), "valve " + "ABC"[i])
	await _settle(1.0)
	await shot("compressor_pressure_ok")
	step("P2 valves 1-2-2 → pressure", s["pressure_ok"])
	# P3 punch the request card
	await view("hall")
	await view("station")
	await act("tube_station", "IA_card_tray", func() -> bool: return L.has_item("blank_card"), func() -> void: L.take("tray_card"), "blank card")
	await view("desk")
	await view("punch")
	await use("blank_card")
	await act("card_punch", "IA_punch_slot", func() -> bool: return s["card_in_punch"], func() -> void: L.use_item_on("blank_card", "punch"), "card into punch")
	for i in 8:
		if ArchiveLogic.PUNCH_CODE[i] == 1:
			await act("card_punch", "IA_punch_key_%d" % i, func() -> bool: return int(s["punch_keys"][i]) == 1, func() -> void: L.toggle_punch_key(i), "key %d" % (i + 1))
	await shot("punch_keys")
	await act("card_punch", "IA_punch_lever", func() -> bool: return L.has_item("request_card"), func() -> void: L.pull_punch_lever(), "punch lever")
	step("P3 punch 10110010 → request card", L.has_item("request_card") and s["request_ok"])
	# P4 dispatch to the stacks
	await view("hall")
	await view("station")
	await use("request_card")
	await act("tube_station", "IA_send_port", func() -> bool: return s["canister"] != "", func() -> void: L.use_item_on("request_card", "send_port"), "card into canister")
	for _guard in 12:
		if not (int(s["dest"]) != ArchiveLogic.DEST_STACKS):
			break
		var d0 := int(s["dest"])
		await act("tube_station", "IA_dest_dial", func() -> bool: return int(s["dest"]) != d0, func() -> void: L.step_dest(1), "destination dial")
	await shot("station_ready")
	await act("tube_station", "IA_send_lever", func() -> bool: return s["file_delivered"], func() -> void: L.send_canister(), "send lever")
	await _settle(2.0)
	await shot("canister_flight")
	await wait_idle()
	await view("station")
	await act("tube_station", "IA_receive_tray", func() -> bool: return bool(room.get("visuals").get("tray_open")), func() -> void: room.get("visuals").set("tray_open", true), "open receive tray")
	await _settle(0.5)
	await shot("station_file")
	await act("tube_station", "Item_canister_file", func() -> bool: return L.has_item("personnel_file"), func() -> void: L.take("canister_file"), "take file")
	await act("tube_station", "Item_canister_key", func() -> bool: return L.has_item("locker_key"), func() -> void: L.take("canister_key"), "take key")
	step("P4 dispatch → file + locker key", L.has_item("personnel_file") and L.has_item("locker_key"))
	# P5 locker 9
	await view("hall")
	await view("lockers")
	await use("locker_key")
	await act("lockers", "IA_locker_9", func() -> bool: return s["locker_open"], func() -> void: L.use_item_on("locker_key", "locker_9"), "key on locker 9")
	await _settle(1.0)
	await view("locker9")
	await shot("locker9_open")
	await act("lockers", "Item_locker_receiver", func() -> bool: return L.has_item("pocket_receiver"), func() -> void: L.take("locker_receiver"), "take receiver")
	step("P5 locker 9 → receiver", L.has_item("pocket_receiver"))
	# P6 hunt with the receiver
	await use("pocket_receiver")
	await view("hall")
	await shot("receiver_hall")
	await view("west")
	await view("grille")
	await shot("receiver_grille")
	await act("vent_grille", "IA_grille", func() -> bool: return s["grille_open"], func() -> void: L.open_hiding_place("grille"), "grille")
	await _settle(0.8)
	await act("vent_grille", "Item_grille_reel", func() -> bool: return L.has_item("tape_1996"), func() -> void: L.take("grille_reel"), "reel 1996")
	await view("hall")
	await view("stacks")
	await view("ledger")
	await act("stacks_shelving", "IA_ledger", func() -> bool: return s["ledger_open"], func() -> void: L.open_hiding_place("ledger"), "ledger")
	await _settle(0.9)
	await shot("ledger_open")
	await act("stacks_shelving", "Item_ledger_reel", func() -> bool: return L.has_item("tape_1997"), func() -> void: L.take("ledger_reel"), "reel 1997")
	await view("hall")
	await view("hatch")
	await act("floor_hatch", "IA_hatch", func() -> bool: return s["hatch_open"], func() -> void: L.open_hiding_place("hatch"), "hatch")
	await _settle(1.2)
	await shot("hatch_open")
	await act("floor_hatch", "Item_hatch_reel", func() -> bool: return L.has_item("tape_1998"), func() -> void: L.take("hatch_reel"), "reel 1998")
	L.select_item("")
	step("P6 receiver hunt → 3 reels", L.has_item("tape_1996") and L.has_item("tape_1997") and L.has_item("tape_1998"))
	# P7 tape deck at 4.75
	await view("hall")
	await view("desk")
	await view("deck")
	for _guard in 12:
		if not (int(s["deck_speed"]) != ArchiveLogic.SPEED_RIGHT):
			break
		var sp0 := int(s["deck_speed"])
		await act("tape_deck", "IA_speed", func() -> bool: return int(s["deck_speed"]) != sp0, func() -> void: L.step_speed(1), "speed knob")
	for tape: String in ["tape_1996", "tape_1997", "tape_1998"]:
		await use(tape)
		await act("tape_deck", "", func() -> bool: return s["deck_tape"] == tape, func() -> void: L.use_item_on(tape, "deck"), "load " + tape)
		await act("tape_deck", "IA_play", func() -> bool: return (s["clicks_heard"] as Array).has(tape), func() -> void: L.play_tape(), "play " + tape)
		await _settle(3.0)
		await shot("deck_" + tape)
		await _settle(9.0)
	step("P7 three reels at 4.75 → clicks 2, 8, 5", (s["clicks_heard"] as Array).size() == 3)
	# P8 booth dial 2-8-5
	await view("hall")
	await view("booth_door")
	await view("dial")
	await shot("dial")
	for ch in ArchiveLogic.BOOTH_CODE:
		var d := int(ch)
		var n0 := str(s["dial_input"]).length()
		await act("booth_door", "IA_dial_hole_%d" % d, func() -> bool: return str(s["dial_input"]).length() != n0 or s["booth_open"],
			func() -> void: L.dial_digit(d), "dial %d" % d)
		await _settle(0.9)
	await wait_idle()
	await shot("booth_open")
	step("P8 dial 285 → booth open", s["booth_open"])
	# P9 splice by shadow length
	await view("booth")
	await shot("booth_root")
	await view("splicer")
	await shot("splicer_loose")
	for slot in 4:
		var f: int = ArchiveLogic.SPLICE_ORDER[slot]
		await act("film_splicer", "IA_frame_%d" % f, func() -> bool: return int(room.get("_held_frame")) == f or int(s["splice"][slot]) == f,
			func() -> void: room.set("_held_frame", f), "pick strip %d" % f)
		await act("film_splicer", "IA_slot_%d" % slot, func() -> bool: return int(s["splice"][slot]) == f, func() -> void: L.splice_put(f, slot), "slot %d" % slot)
	await _settle(0.8)
	await shot("splicer_done")
	await act("film_splicer", "Item_splicer_reel", func() -> bool: return L.has_item("film_reel"), func() -> void: L.take("splicer_reel"), "take film reel")
	step("P9 splice f2 f0 f3 f1 → reel", L.has_item("film_reel"))
	# P10 project, focus
	await view("projector")
	await use("film_reel")
	await act("film_projector", "", func() -> bool: return s["reel_on_projector"], func() -> void: L.use_item_on("film_reel", "projector"), "thread reel")
	await act("film_projector", "IA_run_lever", func() -> bool: return s["projector_on"], func() -> void: L.toggle_projector(), "run lever")
	await _settle(4.0)
	await shot("film_frame")
	await _settle(14.0)
	await shot("film_sign_blurred")
	await wait_idle(60.0)
	await view("projector")
	for _guard in 12:
		if not (int(s["focus"]) != ArchiveLogic.FOCUS_SHARP):
			break
		var f0 := int(s["focus"])
		await act("film_projector", "IA_focus_ring", func() -> bool: return int(s["focus"]) != f0, func() -> void: L.turn_focus(1), "focus ring")
	step("P10 film seen, focus 5", s["film_seen"] and L.is_sharp())
	# crystals from the lens case
	await view("booth")
	await view("lens_case")
	await act("lens_case", "IA_case_lid", func() -> bool: return bool(room.get("visuals").get("case_open")), func() -> void: room.get("visuals").set("case_open", true), "open lens case")
	await _settle(0.8)
	await shot("lens_case_open")
	await act("lens_case", "Item_case_crystal_1", func() -> bool: return L.has_item("crystal_blank_1"), func() -> void: L.take("case_crystal_1"), "crystal 1")
	await act("lens_case", "Item_case_crystal_2", func() -> bool: return L.has_item("crystal_blank_2"), func() -> void: L.take("case_crystal_2"), "crystal 2")
	# P11 record the sign at the screen socket
	await view("hall")
	await view("west")
	await view("screen")
	await shot("screen_sign_sharp")
	await view("socket")
	await use("crystal_blank_1")
	await act("projection_screen", "IA_screen_socket", func() -> bool: return s["sign_recorded"], func() -> void: L.use_item_on("crystal_blank_1", "screen_socket"), "blank crystal in socket")
	await _settle(1.0)
	await shot("socket_recorded")
	await act("projection_screen", "Item_socket", func() -> bool: return L.has_item("crystal_sign"), func() -> void: L.take_from_socket(), "take sign crystal")
	step("P11 sign recorded", s["sign_recorded"] and L.has_item("crystal_sign"))
	# P11b (leave path): record Strand's mark with the slide projector
	if not s["has_lens"]:
		await view("hall")
		await view("booth_door")
		await view("booth")
		await view("projector")
		await act("film_projector", "IA_run_lever", func() -> bool: return not s["projector_on"], func() -> void: L.toggle_projector(), "projector off")
		await view("slides")
		await act("slide_cabinet", "IA_slide_drawer_2", func() -> bool: return int(s["slide_drawer"]) == 2, func() -> void: L.open_slide_drawer(2), "drawer ✦")
		await _settle(0.6)
		await shot("slides_drawer_open")
		await act("slide_cabinet", "Item_slide_mark", func() -> bool: return L.has_item("emblem_slide"), func() -> void: L.take("slide_mark"), "take slide")
		await view("slide_projector")
		await use("emblem_slide")
		await act("slide_projector", "IA_slide_gate", func() -> bool: return s["slide_in"], func() -> void: L.use_item_on("emblem_slide", "slide_projector"), "slide into gate")
		for _guard in 12:
			if not (int(s["slide_rot"]) % 2 != 0):
				break
			var r0 := int(s["slide_rot"])
			await act("slide_projector", "IA_slide_rot", func() -> bool: return int(s["slide_rot"]) != r0, func() -> void: L.rotate_slide(), "rotate slide")
		await act("slide_projector", "IA_slide_lamp", func() -> bool: return s["slide_on"], func() -> void: L.toggle_slide_lamp(), "slide lamp")
		await view("hall")
		await view("west")
		await view("screen")
		await shot("screen_mark")
		await view("socket")
		await use("crystal_blank_2")
		await act("projection_screen", "IA_screen_socket", func() -> bool: return s["mark_recorded"], func() -> void: L.use_item_on("crystal_blank_2", "screen_socket"), "second blank in socket")
		await act("projection_screen", "Item_socket", func() -> bool: return L.has_item("crystal_mark"), func() -> void: L.take_from_socket(), "take mark crystal")
		step("P11b mark recorded", s["mark_recorded"])
	# optional echoes: hold a crystal and tap each one
	await view("hall")
	await use("crystal_sign")
	for id: String in ["stacks", "catalogue"]:
		var echo := node_of("echo_" + id, "")
		if echo:
			await view("west")
			await shot("echo_" + id)
			await act("echo_" + id, "", func() -> bool: return (s["echoes"] as Array).has(id), func() -> void: L.release_echo(id), "echo " + id)
	# P12 dual light lock
	var mark := "crystal_lens" if s["has_lens"] else "crystal_mark"
	await view("hall")
	await view("vault")
	await shot("vault_closed")
	await view("vault_ports")
	await use(mark)
	await act("vault_door", "IA_port_left", func() -> bool: return s["port_left"] == mark, func() -> void: L.use_item_on(mark, "port_left"), "mark crystal left")
	await use("crystal_sign")
	await act("vault_door", "IA_port_right", func() -> bool: return s["port_right"] == "crystal_sign", func() -> void: L.use_item_on("crystal_sign", "port_right"), "sign crystal right")
	await shot("vault_ports_filled")
	for _guard in 12:
		if not (int(s["rot_left"]) % 4 != 0):
			break
		var a0 := int(s["rot_left"])
		await act("vault_door", "IA_collar_left", func() -> bool: return int(s["rot_left"]) != a0, func() -> void: L.turn_collar("rot_left"), "left collar")
	for _guard in 12:
		if not (int(s["rot_right"]) != ArchiveLogic.ROT_RIGHT_TARGET):
			break
		var b0 := int(s["rot_right"])
		await act("vault_door", "IA_collar_right", func() -> bool: return int(s["rot_right"]) != b0, func() -> void: L.turn_collar("rot_right"), "right collar")
	for _guard in 12:
		if not (int(s["zoom_right"]) != ArchiveLogic.ZOOM_TARGET and not s["vault_unlocked"]):
			break
		var z0 := int(s["zoom_right"])
		await act("vault_door", "IA_zoom_right", func() -> bool: return int(s["zoom_right"]) != z0, func() -> void: L.turn_collar("zoom_right"), "zoom collar")
	await _settle(1.4)
	await shot("vault_overlay_locked_in")
	step("P12 overlay → vault unlocked", s["vault_unlocked"])
	await view("vault")
	for _i in ArchiveLogic.WHEEL_TURNS:
		var w0 := int(s["wheel"])
		await act("vault_door", "IA_vault_handle", func() -> bool: return int(s["wheel"]) != w0 or s["vault_open"], func() -> void: L.turn_wheel(), "vault wheel")
		await _settle(0.6)
	await _settle(3.5)
	await shot("vault_opening")
	var hud: Node = room.get("hud")
	var w := 0
	while w < 120 and hud.get("_overlay") == null:
		w += 1
		await _settle(0.25)
		if w == 20:
			await shot("vault_reel")
	await shot("finale_choice")
	hud.call("_close_overlay")
	L.choose_ending("leyla_key")
	await _settle(2.5)
	await shot("chapter_complete")
	step("Finale → chapter complete", s["complete"])
	_finish()


func _finish() -> void:
	_log("taps through the 3D scene: %d, logic fallbacks: %d" % [taps_ok, taps_fallback])
	var f := FileAccess.open(out_dir + "/playthrough_ch2_report.txt", FileAccess.WRITE)
	f.store_string("\n".join(report) + "\n")
	SaveSystem.delete_game()
	var ok: bool = logic.state["complete"] and not report.any(func(l: String) -> bool: return l.begins_with("✗"))
	var qa_exit: int = 0 if ok and taps_fallback == 0 else 1
	print("QA_DONE exit=%d" % qa_exit) # tools/qa_run.sh: the run finished even if the process then hangs on exit
	get_tree().quit(qa_exit)
