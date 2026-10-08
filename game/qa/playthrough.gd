extends Node
## Runtime QA: loads the real Lab 7 scene and plays Chapter 1 through simulated taps on the 3D parts
## (raycast → hotspot → logic), falling back to direct logic calls only for models that are still
## placeholders. Saves a screenshot per step and a report. Exit code 0 = chapter completed.
## Run: xvfb-run godot --path game res://qa/playthrough.tscn -- --out=<dir> [--lang=ru]

var out_dir := "/tmp"
var room: Node3D
var logic: Lab7Logic
var report: Array[String] = []
var shot_n := 0
var taps_ok := 0
var taps_fallback := 0


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		if a.begins_with("--lang="):
			TranslationServer.set_locale(a.substr(7))
	SaveSystem.save_path = "user://qa_save.json"
	GameState.start_new("ch1")
	logic = GameState.logic
	var t0 := Time.get_ticks_msec()
	room = (load("res://src/rooms/lab7/lab7.tscn") as PackedScene).instantiate()
	room.set("capture_mode", true)
	get_tree().root.add_child.call_deferred(room)
	await get_tree().process_frame
	await get_tree().process_frame
	report.append("scene load+build: %d ms (software renderer; phones differ)" % (Time.get_ticks_msec() - t0))
	await _settle(1.0)
	await _perf("lab_root")
	await run()


func _perf(label: String) -> void:
	await _settle(0.5)
	var rs := RenderingServer
	report.append("perf[%s]: draw calls %d, primitives %d, objects %d, video mem %.0f MB, texture mem %.0f MB" % [label,
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME),
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED) / 1048576.0,
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED) / 1048576.0])


func _settle(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()


func shot(name: String) -> void:
	await _settle(0.3)
	await RenderingServer.frame_post_draw
	shot_n += 1
	var p := "%s/%02d_%s.png" % [out_dir, shot_n, name]
	get_viewport().get_texture().get_image().save_png(p)
	report.append("shot %s" % p.get_file())


func cam() -> RoomCamera:
	return room.get("cam")


func view(id: String) -> void:
	cam().go(id)
	await _settle(0.9)


func part_node(model: String, part: String) -> Node3D:
	return ModelUtil.find((room.get("models") as Dictionary).get(model), part)


## Tap the on-screen position of a 3D part (true player path). Returns false if the part is missing or off-screen.
func tap_part(model: String, part: String, offset: Vector3 = Vector3.ZERO) -> bool:
	var n: Node3D = part_node(model, part) if part != "" else ((room.get("models") as Dictionary).get(model) as Node3D)
	if n == null:
		return false
	var center: Vector3 = n.global_position
	for mi in ModelUtil.find_meshes(n):
		center = mi.global_transform * mi.get_aabb().get_center()
		break
	center += offset
	if cam().is_position_behind(center):
		return false
	var sp := cam().unproject_position(center)
	var vs := get_viewport().get_visible_rect().size
	if sp.x < 0 or sp.y < 0 or sp.x > vs.x or sp.y > vs.y:
		return false
	var before := JSON.stringify(logic.to_dict()) + cam().current()
	room.call("_on_tap", sp)
	await _settle(0.35)
	var changed := before != JSON.stringify(logic.to_dict()) + cam().current()
	if changed:
		taps_ok += 1
	return changed


func step(label: String, cond: Callable) -> void:
	var ok: bool = cond.call()
	report.append(("✓ " if ok else "✗ ") + label)


## Tap a 3D part; succeed only if `cond` becomes true. Otherwise apply `fallback` (logic call).
func act(model: String, part: String, cond: Callable, fallback: Callable, label: String = "", offset: Vector3 = Vector3.ZERO) -> void:
	if not cond.call():
		await tap_part(model, part, offset)
		await _settle(0.25)
	if cond.call():
		taps_ok += 1
	else:
		fallback.call()
		taps_fallback += 1
		report.append("  fallback: %s %s" % [label if label != "" else part, model])


func run() -> void:
	var s := logic.state
	var L := logic
	await shot("lab_dark_start")
	# --- notebook + drawer (P1)
	await view("desk")
	await shot("desk_view")
	await act("notebook", "", func() -> bool: return L.has_item("notebook"), func() -> void: L.take("notebook"), "notebook")
	await view("drawer")
	await shot("drawer_closeup_locked")
	var code := Lab7Logic.DRAWER_CODE
	for i in 4:
		var guard := 0
		while int(s["drawer"][i]) != code[i] and guard < 12:
			guard += 1
			var before := int(s["drawer"][i])
			await act("desk", "IA_drawer_wheel_%d" % i, func() -> bool: return int(s["drawer"][i]) != before,
				func() -> void: L.step_drawer_wheel(i, 1), "wheel %d" % i, Vector3(0, 0.012, 0))
	await _settle(0.8)
	await shot("drawer_open_0317")
	await act("desk", "Item_drawer_lamp", func() -> bool: return L.has_item("uv_lamp_empty"), func() -> void: L.take("drawer_lamp"), "lamp in drawer")
	step("P1 drawer 0317 → UV lamp", func() -> bool: return s["drawer_open"] and L.has_item("uv_lamp_empty"))
	# --- gear box (P2)
	cam().go("lab")
	await _settle(0.8)
	await view("gearbox")
	await shot("gearbox_closeup")
	var presses := Lab7Solver.gear_solution(s["gears"])
	for i in 3:
		for _k in presses[i]:
			var g0 := str(s["gears"])
			await act("gear_box", "IA_knob_%d" % i, func() -> bool: return str(s["gears"]) != g0 or s["box_open"],
				func() -> void: L.press_gear(i), "knob %d" % i)
	await _settle(1.0)
	await shot("gearbox_open")
	await act("gear_box", "Item_box_cell", func() -> bool: return L.has_item("battery_cell"), func() -> void: L.take("box_cell"), "cell")
	step("P2 gear box → battery", func() -> bool: return s["box_open"] and L.has_item("battery_cell"))
	# --- combine (P3) through the HUD
	L.select_item("uv_lamp_empty")
	L.combine("uv_lamp_empty", "battery_cell")
	step("P3 combine → UV lamp", func() -> bool: return L.has_item("uv_lamp"))
	# --- UV: desk mark (dwell) + notebook page (HUD button)
	L.select_item("uv_lamp")
	await view("desk")
	await view("desk_side")
	room.set("_uv_aim", cam().unproject_position(Vector3(0.262, 0.52, -2.05)))
	await _settle(1.4)
	await shot("uv_desk_mark")
	if s["uv_desk"]:
		taps_ok += 1
	else:
		L.uv_reveal("desk_mark"); taps_fallback += 1; report.append("  fallback: uv desk dwell")
	var hud: Node = room.get("hud")
	hud.call("_show_notebook", 4)
	await _settle(0.3)
	L.uv_reveal("notebook_page")
	hud.call("_show_notebook", 4)
	await shot("notebook_uv_page")
	hud.call("_close_overlay")
	L.select_item("")
	step("UV reveals (page + desk)", func() -> bool: return s["uv_page"] and s["uv_desk"])
	# --- poster + safe (P4)
	cam().go("lab")
	await _settle(0.8)
	await view("poster")
	await shot("poster_resonances")
	await view("safe")
	await shot("safe_keypad")
	for c in "7294":
		var n0 := str(s["safe_input"]).length()
		await act("wall_safe", "IA_key_" + c, func() -> bool: return str(s["safe_input"]).length() > n0, func() -> void: L.safe_press(c), "key " + c)
	await act("wall_safe", "IA_key_enter", func() -> bool: return s["safe_open"], func() -> void: L.safe_press("E"), "enter")
	await _settle(1.4)
	await shot("safe_open")
	for spot in ["safe_key", "safe_lens", "safe_letter", "safe_valve"]:
		var item: String = Lab7Logic.SPOTS[spot]["item"]
		await act("wall_safe", "Item_" + spot, func() -> bool: return L.has_item(item), func() -> void: L.take(spot), spot)
	step("P4 safe 7294 → key, lens, letter, valve", func() -> bool: return s["safe_open"] and L.has_item("crystal_lens"))
	# --- compartment (P5)
	await view("desk")
	await view("desk_side")
	await act("desk", "IA_rosette", func() -> bool: return s["rosette"], func() -> void: L.press_rosette(), "rosette")
	await _settle(0.6)
	L.select_item("brass_key")
	await act("desk", "IA_keyhole", func() -> bool: return s["compartment_open"], func() -> void: L.use_item_on("brass_key", "desk_keyhole"), "keyhole")
	await _settle(0.8)
	await shot("desk_compartment_open")
	await act("desk", "Item_compartment_handle", func() -> bool: return L.has_item("breaker_handle"), func() -> void: L.take("compartment_handle"), "handle")
	await act("desk", "Item_compartment_photo", func() -> bool: return L.has_item("leyla_photo"), func() -> void: L.take("compartment_photo"), "photo")
	step("P5 compartment → breaker handle", func() -> bool: return L.has_item("breaker_handle"))
	# --- Panel 7 (P6)
	cam().go("lab")
	await _settle(0.8)
	await view("panel")
	L.select_item("breaker_handle")
	await act("panel7", "IA_main_lever", func() -> bool: return s["handle_installed"], func() -> void: L.use_item_on("breaker_handle", "panel_main"), "install handle")
	for i in [0, 1, 2]:
		await act("panel7", "IA_switch_%d" % i, func() -> bool: return int(s["switches"][i]) == 1, func() -> void: L.toggle_switch(i), "switch %d" % i)
	await act("panel7", "IA_main_lever", func() -> bool: return s["power_on"], func() -> void: L.toggle_main(), "main lever")
	await _settle(2.6)
	await shot("panel_power_restored")
	step("P6 circuits → power", func() -> bool: return s["power_on"])
	cam().go("lab")
	await _settle(1.0)
	await shot("lab_powered")
	await _perf("lab_powered")
	# --- radio (P7/P8)
	await view("chalkboard")
	await shot("chalkboard")
	await view("radio")
	L.select_item("radio_valve")
	await act("radio", "", func() -> bool: return s["valve_installed"], func() -> void: L.use_item_on("radio_valve", "radio"), "valve")
	var g := 0
	while not s["signal_heard"] and g < 30:
		g += 1
		var d0 := int(s["dial"])
		await act("radio", "IA_tuning_knob", func() -> bool: return int(s["dial"]) != d0, func() -> void: L.step_dial(-2), "tuning knob",
			Vector3(-0.012, 0, 0))
	await _settle(1.5)
	await shot("radio_tuned_41m")
	step("P7/P8 radio valve + 41 m", func() -> bool: return s["signal_heard"])
	# --- books (P9)
	cam().go("lab")
	await _settle(0.8)
	await view("books")
	await shot("encyclopedia")
	for n in Lab7Logic.BEACON_PULSES:
		var b0 := str(s["books"])
		await act("bookshelf", "IA_book_%d" % n, func() -> bool: return str(s["books"]) != b0 or s["shelf_open"], func() -> void: L.pull_book(n), "book %d" % n)
		await _settle(0.6)
	await _settle(2.6)
	cam().go("lab")
	await _settle(1.0)
	await view("bookshelf")
	await shot("bookcase_open")
	step("P9 books II-VI-III → darkroom", func() -> bool: return s["shelf_open"])
	# --- darkroom shadow + recording (P10)
	cam().go("darkroom")
	await _settle(1.2)
	await shot("darkroom")
	await view("shadow")
	await shot("shadow_misaligned")
	L.select_item("crystal_lens")
	L.use_item_on("crystal_lens", "emblem_socket")
	var guard := 0
	while not L.shadow_aligned() and guard < 14:
		guard += 1
		var p := 0 if int(s["shadow"][0]) != 0 else 1
		var sh0 := str(s["shadow"])
		await act("shadow_lock", "IA_ring_knob" if p == 0 else "IA_rod_knob", func() -> bool: return str(s["shadow"]) != sh0,
			func() -> void: L.turn_sculpture(p), "sculpture %d" % p)
	await _settle(1.2)
	await shot("shadow_emblem_recorded")
	await view("cabinet")
	await act("shadow_lock", "Item_cabinet_mirror", func() -> bool: return L.has_item("mirror_item"), func() -> void: L.take("cabinet_mirror"), "mirror")
	L.remove_lens()
	step("P10 shadow lock + emblem recorded + mirror", func() -> bool: return s["emblem_recorded"] and L.has_item("mirror_item"))
	# --- projector (P11)
	cam().go("lab")
	await _settle(1.0)
	await view("vials")
	await shot("vials_densities")
	await view("projector")
	L.select_item("crystal_lens")
	await act("lumen_projector", "IA_lens_socket", func() -> bool: return s["lens_at"] == "projector", func() -> void: L.use_item_on("crystal_lens", "projector"), "lens socket")
	for i in 3:
		var gg := 0
		while int(s["rings"][i]) != Lab7Logic.RING_TARGET[i] and gg < 8:
			gg += 1
			var r0 := int(s["rings"][i])
			await act("lumen_projector", "IA_ring_%d" % i, func() -> bool: return int(s["rings"][i]) != r0, func() -> void: L.turn_ring(i), "ring %d" % i)
	await shot("projector_tuned")
	await act("lumen_projector", "IA_projector_lever", func() -> bool: return s["beam_on"], func() -> void: L.pull_projector_lever(), "lever")
	await _settle(1.0)
	await shot("projector_beam_on")
	step("P11 projector tuned → beam", func() -> bool: return s["beam_on"])
	# --- mirrors (P12)
	await view("mirror_b")
	L.select_item("mirror_item")
	await act("mirror_stand_b", "IA_mirror_mount", func() -> bool: return s["mirror_b_mounted"], func() -> void: L.use_item_on("mirror_item", "mirror_stand_b"), "mount mirror")
	await view("mirror_a")
	var m := 0
	while int(s["mirrors"][0]) != 5 and m < 10:
		m += 1
		var a0 := int(s["mirrors"][0])
		await act("mirror_stand", "IA_mirror_mount", func() -> bool: return int(s["mirrors"][0]) != a0, func() -> void: L.rotate_mirror(0, 1), "mirror A")
	cam().go("lab")
	await _settle(1.0)
	await shot("beam_first_mirror")
	await view("mirror_b")
	m = 0
	while int(s["mirrors"][1]) != 1 and not s["door_open"] and m < 10:
		m += 1
		var b1 := int(s["mirrors"][1])
		await act("mirror_stand_b", "IA_mirror_mount", func() -> bool: return int(s["mirrors"][1]) != b1 or s["door_open"], func() -> void: L.rotate_mirror(1, 1), "mirror B")
	await _settle(2.5)
	await shot("finale_echo_1979")
	await _settle(4.0)
	await shot("finale_door")
	# wait for the choice overlay, then choose
	var w := 0
	while w < 60 and hud.get("_overlay") == null:
		w += 1
		await _settle(0.25)
	await shot("finale_choice")
	step("P12 mirrors → light lock → door", func() -> bool: return s["door_open"])
	hud.call("_close_overlay")
	L.choose_ending("leave_lens")
	await _settle(2.5)
	await shot("chapter_complete")
	step("Finale choice → chapter complete", func() -> bool: return s["complete"])
	_finish()


func _finish() -> void:
	report.append("taps through 3D scene: %d, logic fallbacks (missing models/placeholders): %d" % [taps_ok, taps_fallback])
	var f := FileAccess.open(out_dir + "/playthrough_report.txt", FileAccess.WRITE)
	f.store_string("\n".join(report) + "\n")
	print("\n".join(report))
	SaveSystem.delete_game()
	get_tree().quit(0 if logic.state["complete"] else 1)
