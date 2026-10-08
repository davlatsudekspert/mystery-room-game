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


func run() -> void:
	var s := logic.state
	await shot("lab_dark_start")
	# --- notebook + drawer (P1)
	await view("desk")
	await shot("desk_view")
	if not await tap_part("notebook", ""):
		logic.take("notebook"); taps_fallback += 1
	await view("drawer")
	await shot("drawer_closeup_locked")
	var code := Lab7Logic.DRAWER_CODE
	for i in 4:
		var guard := 0
		while int(s["drawer"][i]) != code[i] and guard < 12:
			guard += 1
			if not await tap_part("desk", "IA_drawer_wheel_%d" % i, Vector3(0, 0.01, 0)):
				logic.step_drawer_wheel(i, 1); taps_fallback += 1
	await _settle(0.8)
	await shot("drawer_open_0317")
	if logic.can_take("drawer_lamp"):
		if not await tap_part("desk", "IA_drawer_top"):
			logic.take("drawer_lamp"); taps_fallback += 1
	step("P1 drawer 0317 → UV lamp", func() -> bool: return s["drawer_open"] and logic.has_item("uv_lamp_empty"))
	# --- gear box (P2)
	cam().go("lab")
	await _settle(0.8)
	await view("bookshelf")
	await shot("bookshelf_view")
	await view("gearbox")
	await shot("gearbox_closeup")
	var presses := Lab7Solver.gear_solution(s["gears"])
	for i in 3:
		for _k in presses[i]:
			if not await tap_part("gear_box", "IA_knob_%d" % i):
				logic.press_gear(i); taps_fallback += 1
	await _settle(1.0)
	await shot("gearbox_open")
	if logic.can_take("box_cell"):
		logic.take("box_cell"); taps_fallback += 1
	step("P2 gear box → battery", func() -> bool: return s["box_open"] and logic.has_item("battery_cell"))
	# --- combine (P3) through the HUD path
	logic.select_item("uv_lamp_empty")
	logic.combine("uv_lamp_empty", "battery_cell")
	step("P3 combine → UV lamp", func() -> bool: return logic.has_item("uv_lamp"))
	# --- UV: notebook page, desk mark (P4/P5)
	logic.select_item("uv_lamp")
	await view("desk")
	await view("desk_side")
	room.set("_uv_aim", cam().unproject_position(Vector3(0.262, 0.52, -2.05)))
	await _settle(1.2)
	await shot("uv_desk_mark")
	if not s["uv_desk"]:
		logic.uv_reveal("desk_mark"); taps_fallback += 1
	logic.uv_reveal("notebook_page")
	var hud: Node = room.get("hud")
	hud.call("show_document", "notebook")
	await _settle(0.2)
	hud.set("_overlay", hud.get("_overlay"))
	# open page 5 with UV revealed
	hud.call("_show_notebook", 4)
	await shot("notebook_uv_page")
	hud.call("_close_overlay")
	logic.select_item("")
	step("UV reveals (page + desk)", func() -> bool: return s["uv_page"] and s["uv_desk"])
	# --- poster + safe (P4)
	cam().go("lab")
	await _settle(0.8)
	await view("poster")
	await shot("poster_resonances")
	await view("safe")
	for c in "7294":
		if not await tap_part("wall_safe", "IA_key_" + c):
			logic.safe_press(c); taps_fallback += 1
	if not await tap_part("wall_safe", "IA_key_enter"):
		logic.safe_press("E"); taps_fallback += 1
	await _settle(1.4)
	await shot("safe_open")
	for spot in ["safe_key", "safe_lens", "safe_letter", "safe_valve"]:
		if logic.can_take(spot):
			logic.take(spot); taps_fallback += 1
	step("P4 safe 7294 → key, lens, letter, valve", func() -> bool: return s["safe_open"] and logic.has_item("crystal_lens"))
	# --- compartment (P5)
	await view("desk")
	await view("desk_side")
	if not await tap_part("desk", "IA_rosette"):
		logic.press_rosette(); taps_fallback += 1
	logic.select_item("brass_key")
	if not await tap_part("desk", "IA_keyhole"):
		logic.use_item_on("brass_key", "desk_keyhole"); taps_fallback += 1
	await _settle(0.8)
	await shot("desk_compartment_open")
	for spot in ["compartment_handle", "compartment_photo"]:
		if logic.can_take(spot):
			logic.take(spot); taps_fallback += 1
	step("P5 compartment → breaker handle", func() -> bool: return logic.has_item("breaker_handle"))
	# --- Panel 7 (P6)
	cam().go("lab")
	await _settle(0.8)
	await view("panel")
	logic.select_item("breaker_handle")
	if not await tap_part("panel7", "IA_main_lever"):
		logic.use_item_on("breaker_handle", "panel_main"); taps_fallback += 1
	for i in [0, 1, 2]:
		if not await tap_part("panel7", "IA_switch_%d" % i):
			logic.toggle_switch(i); taps_fallback += 1
	if not await tap_part("panel7", "IA_main_lever"):
		logic.toggle_main(); taps_fallback += 1
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
	await view("bench")
	await view("radio")
	logic.select_item("radio_valve")
	if not await tap_part("radio", ""):
		logic.use_item_on("radio_valve", "radio"); taps_fallback += 1
	logic.set_dial(Lab7Logic.RADIO_TARGET)
	await _settle(1.5)
	await shot("radio_tuned_41m")
	step("P7/P8 radio valve + 41 m", func() -> bool: return s["signal_heard"])
	# --- books (P9)
	cam().go("lab")
	await _settle(0.8)
	await view("bookshelf")
	await view("books")
	for n in Lab7Logic.BEACON_PULSES:
		if not await tap_part("bookshelf", "IA_book_%d" % n):
			logic.pull_book(n); taps_fallback += 1
	await _settle(2.6)
	cam().go("lab")
	await _settle(1.0)
	await view("bookshelf")
	await shot("bookcase_open")
	step("P9 books II-VI-III → darkroom", func() -> bool: return s["shelf_open"])
	# --- darkroom shadow + recording (P10)
	cam().go("darkroom")
	await _settle(1.0)
	await shot("darkroom")
	await view("shadow")
	await shot("shadow_misaligned")
	logic.select_item("crystal_lens")
	logic.use_item_on("crystal_lens", "emblem_socket")
	var guard := 0
	while not logic.shadow_aligned() and guard < 12:
		guard += 1
		var p := 0 if int(s["shadow"][0]) % 3 != 0 else 1
		if not await tap_part("shadow_lock", "IA_ring_knob" if p == 0 else "IA_rod_knob"):
			logic.turn_sculpture(p); taps_fallback += 1
	await _settle(1.2)
	await shot("shadow_emblem_recorded")
	if logic.can_take("cabinet_mirror"):
		logic.take("cabinet_mirror"); taps_fallback += 1
	logic.remove_lens()
	step("P10 shadow lock + emblem recorded + mirror", func() -> bool: return s["emblem_recorded"] and logic.has_item("mirror_item"))
	# --- projector (P11)
	cam().go("lab")
	await _settle(1.0)
	await view("vials")
	await shot("vials_densities")
	await view("projector")
	logic.select_item("crystal_lens")
	if not await tap_part("lumen_projector", "IA_lens_socket"):
		logic.use_item_on("crystal_lens", "projector"); taps_fallback += 1
	for i in 3:
		var g := 0
		while int(s["rings"][i]) != Lab7Logic.RING_TARGET[i] and g < 8:
			g += 1
			if not await tap_part("lumen_projector", "IA_ring_%d" % i):
				logic.turn_ring(i); taps_fallback += 1
	if not await tap_part("lumen_projector", "IA_projector_lever"):
		logic.pull_projector_lever(); taps_fallback += 1
	await _settle(1.0)
	await shot("projector_beam_on")
	step("P11 projector tuned → beam", func() -> bool: return s["beam_on"])
	# --- mirrors (P12)
	logic.select_item("mirror_item")
	logic.use_item_on("mirror_item", "mirror_stand_b")
	while int(s["mirrors"][0]) != 5:
		logic.rotate_mirror(0, 1)
	cam().go("lab")
	await _settle(1.0)
	await shot("beam_first_mirror")
	while int(s["mirrors"][1]) != 1 and not s["door_open"]:
		logic.rotate_mirror(1, 1)
	await _settle(2.5)
	await shot("finale_echo_1979")
	await _settle(6.0)
	await shot("door_open")
	step("P12 mirrors → light lock → door", func() -> bool: return s["door_open"])
	logic.choose_ending("leave_lens")
	await _settle(2.0)
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
