extends Node
## Runtime QA: loads the real Lab 7 scene and plays Chapter 1 through simulated taps on the 3D parts
## (raycast → hotspot → logic), falling back to direct logic calls only for models that are still
## placeholders. Saves a screenshot per step and a report. Exit code 0 = chapter completed.
## Run: xvfb-run godot --path game res://qa/playthrough.tscn -- --out=<dir> [--lang=ru] [--from=p7] [--to=p9] [--seed=N]

var out_dir := "/tmp"
var room: Node3D
var logic: Lab7Logic
var report: Array[String] = []
var shot_n := 0
var taps_ok := 0
var taps_fallback := 0
var taps_under_hud := 0 # taps whose point lies under a HUD control (a finger would hit the HUD, not the room)
var _from := 1 # --from=pN: the solver plays everything before puzzle N, the 3D run starts there
var _to := 99 # --to=pN: stop after puzzle N

## State that must hold before section N starts (the solver advances until it does).
const FROM_READY := {
	2: "drawer_open", 3: "box_open", 4: "uv_desk", 5: "safe_taken", 6: "compartment_taken", 7: "power_on",
	9: "signal_heard", 10: "shelf_open", 11: "mirror_taken", 12: "beam_on",
}



## Report line, also printed at once (tools/qa_run.sh treats a silent log as a stalled run).
func _log(line: String) -> void:
	report.append(line)
	print(line)

func _ready() -> void:
	GameState.variant_seed = 0 # canonical answers unless --seed=N (players get a random seed per game)
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		if a.begins_with("--lang="):
			TranslationServer.set_locale(a.substr(7))
		if a.begins_with("--seed="):
			GameState.variant_seed = int(a.substr(7)) # this game's own answers (docs/VARIANTS.md)
		if a.begins_with("--from=p"):
			_from = int(a.substr(8))
		if a.begins_with("--to=p"):
			_to = int(a.substr(6))
	DirAccess.make_dir_recursive_absolute(out_dir)
	SaveSystem.save_path = "user://qa_save.json"
	GameState.start_new("ch1")
	logic = GameState.logic
	_advance_to(_from)
	var t0 := Time.get_ticks_msec()
	room = (load("res://src/rooms/lab7/lab7.tscn") as PackedScene).instantiate()
	room.set("capture_mode", true)
	get_tree().root.add_child.call_deferred(room)
	await get_tree().process_frame
	await get_tree().process_frame
	_log("scene load+build: %d ms (software renderer; phones differ)" % (Time.get_ticks_msec() - t0))
	await _settle(1.0)
	await _perf("lab_root")
	await run()


func _ready_for(k: int) -> bool:
	var s := logic.state
	match str(FROM_READY.get(k, "")):
		"drawer_open": return s["drawer_open"] and logic.has_item("uv_lamp_empty")
		"box_open": return s["box_open"] and logic.has_item("battery_cell")
		"uv_desk": return logic.has_item("uv_lamp") and s["uv_page"]
		"safe_taken": return s["safe_open"] and logic.has_item("radio_valve") and logic.has_item("brass_key")
		"compartment_taken": return logic.has_item("breaker_handle")
		"power_on": return s["power_on"]
		"signal_heard": return s["signal_heard"]
		"shelf_open": return s["shelf_open"]
		"mirror_taken": return logic.has_item("mirror_item") and s["emblem_recorded"] and s["lens_at"] == "inventory"
		"beam_on": return s["beam_on"]
	return true


func _advance_to(k: int) -> void:
	if k <= 1:
		return
	var guard := 0
	while not _ready_for(k) and guard < 200:
		guard += 1
		Lab7Solver.step(logic, "leave_lens")
	logic.select_item("")
	_log("start: puzzle %d (solver played the earlier ones in %d steps)" % [k, guard])


func _perf(label: String) -> void:
	await _settle(0.5)
	var rs := RenderingServer
	_log("perf[%s]: draw calls %d, primitives %d, objects %d, video mem %.0f MB, texture mem %.0f MB" % [label,
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
	_log("shot %s" % p.get_file())


func cam() -> RoomCamera:
	return room.get("cam")


func view(id: String) -> void:
	cam().go(id)
	await _settle(0.9)


func part_node(model: String, part: String) -> Node3D:
	return ModelUtil.find((room.get("models") as Dictionary).get(model), part)


## Screen rectangle covered by a part's meshes (projected AABB corners). Empty if behind the camera.
func _part_rect(model: String, part: String) -> Rect2:
	var n: Node3D = part_node(model, part) if part != "" else ((room.get("models") as Dictionary).get(model) as Node3D)
	if n == null:
		return Rect2()
	# a named part: its own mesh only (children such as drawer digits are separate targets);
	# a whole model: every visible mesh
	var meshes := ModelUtil.find_meshes(n)
	if part != "" and n is MeshInstance3D:
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


## Screen point to tap: the part's projected centre, shifted by `frac` of its half-size
## (x: -1 left … +1 right, y: -1 top … +1 bottom). Returns (-1, -1) when the part is missing/off-screen.
func _tap_point(model: String, part: String, frac: Vector2) -> Vector2:
	var r := _part_rect(model, part)
	if r.size == Vector2.ZERO and r.position == Vector2.ZERO:
		return Vector2(-1, -1)
	var sp := r.get_center() + frac * r.size * 0.5
	var vs := get_viewport().get_visible_rect().size
	if sp.x < 0 or sp.y < 0 or sp.x > vs.x or sp.y > vs.y:
		return Vector2(-1, -1)
	return sp


## Tap a 3D part on screen (true player path: raycast → hotspot → logic).
func tap_part(model: String, part: String, frac: Vector2 = Vector2.ZERO) -> void:
	var sp := _tap_point(model, part, frac)
	if sp.x < 0:
		return
	_note_hud(sp, "%s/%s" % [model, part])
	room.call("_on_tap", sp)
	await _settle(0.35)


## The solver's taps go straight to the room, so a control under the HUD would still "work" here. Count the taps a
## finger could not make: the point lies inside one of HUD.blocked_rects().
func _note_hud(sp: Vector2, what: String) -> void:
	var hud: Node = room.get("hud")
	if hud == null or not hud.has_method("blocked_rects"):
		return
	for r: Rect2 in hud.call("blocked_rects"):
		if r.has_point(sp):
			taps_under_hud += 1
			_log("  ! tap under the HUD: %s at %d,%d (view %s)" % [what, int(sp.x), int(sp.y), cam().current()])
			return


func _what_was_hit(model: String, part: String, frac: Vector2) -> String:
	if (part_node(model, part) if part != "" else (room.get("models") as Dictionary).get(model)) == null:
		return "part missing"
	var sp := _tap_point(model, part, frac)
	if sp.x < 0:
		return "off-screen/behind camera"
	var hit: Dictionary = room.call("_raycast", sp)
	if hit.is_empty():
		return "nothing"
	var r: Dictionary = room.call("_resolve", hit)
	return "%s/%s/%s" % [r["model"], r["hotspot"], r["part"]]


## Optional Lumen shard: go to its view with the UV torch on, aim at it, tap it.
func shard(id: String, view_id: String) -> void:
	var s := logic.state
	await view(view_id)
	logic.select_item("uv_lamp")
	var n: Node3D = (room.get("_shard_nodes") as Dictionary).get(id)
	var ok := false
	if n != null and not cam().is_position_behind(n.global_position):
		var sp := cam().unproject_position(n.global_position)
		room.set("_uv_aim", sp)
		await _settle(0.6)
		await shot("shard_" + id)
		room.call("_on_tap", sp)
		await _settle(0.4)
		ok = (s["shards"] as Array).has(id)
	if ok:
		taps_ok += 1
		await check_hidden(id)
	else:
		logic.collect_shard(id)
		taps_fallback += 1
		_log("  fallback: shard %s (view %s)" % [id, cam().current()])
	logic.select_item("")


func check_hidden(id: String) -> void:
	await get_tree().process_frame
	var n: Node3D = (room.get("_shard_nodes") as Dictionary).get(id)
	if n != null and n.visible:
		_log("✗ shard %s still visible after it was collected" % id)


func step(label: String, cond: Callable) -> void:
	var ok: bool = cond.call()
	_log(("✓ " if ok else "✗ ") + label)


## Tap a 3D part; succeed only if `cond` becomes true. Otherwise apply `fallback` (logic call).
func act(model: String, part: String, cond: Callable, fallback: Callable, label: String = "", frac: Vector2 = Vector2.ZERO) -> void:
	if not cond.call():
		await tap_part(model, part, frac)
		await _settle(0.25)
	if cond.call():
		taps_ok += 1
	else:
		var why := _what_was_hit(model, part, frac)
		fallback.call()
		taps_fallback += 1
		_log("  fallback: %s %s (view %s, hit %s)" % [label if label != "" else part, model, cam().current(), why])


func run() -> void:
	var s := logic.state
	var L := logic
	var hud: Node = room.get("hud")
	await shot("lab_dark_start")
	# Android back button (room.handle_back is what SceneManager calls): pause at the room view and resume,
	# then step out of a close-up instead of quitting the game
	room.call("handle_back")
	await _settle(0.3)
	var pause_opened: bool = hud.get("_overlay") != null
	room.call("handle_back")
	await _settle(0.3)
	var pause_closed: bool = hud.get("_overlay") == null
	await view("desk")
	room.call("handle_back")
	await _settle(0.9)
	step("Back button: pause → resume, close-up → room", func() -> bool: return pause_opened and pause_closed and cam().current() == "lab")
	# --- notebook + drawer (P1)
	if _from <= 1 and 1 <= _to:
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
				await act("desk", "IA_drawer_digit_%d" % i, func() -> bool: return int(s["drawer"][i]) == (before + 1) % 10,
					func() -> void: L.step_drawer_wheel(i, 1), "wheel %d" % i, Vector2(0, -0.5))
		await _settle(0.8)
		await shot("drawer_open_0317")
		await act("desk", "Item_drawer_lamp", func() -> bool: return L.has_item("uv_lamp_empty"), func() -> void: L.take("drawer_lamp"), "lamp in drawer")
		step("P1 drawer 0317 → UV lamp", func() -> bool: return s["drawer_open"] and L.has_item("uv_lamp_empty"))
	# --- gear box (P2)
	if _from <= 2 and 2 <= _to:
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
	if _from <= 3 and 3 <= _to:
		L.select_item("uv_lamp_empty")
		L.combine("uv_lamp_empty", "battery_cell")
		step("P3 combine → UV lamp", func() -> bool: return L.has_item("uv_lamp"))
	# --- UV: desk mark (dwell) + notebook page (HUD button)
	if _from <= 3 and 3 <= _to:
		L.select_item("uv_lamp")
		await view("desk")
		await view("desk_side")
		room.set("_uv_aim", cam().unproject_position(Vector3(0.262, 0.52, -2.05)))
		await _settle(1.4)
		await shot("uv_desk_mark")
		if s["uv_desk"]:
			taps_ok += 1
		else:
			L.uv_reveal("desk_mark"); taps_fallback += 1; _log("  fallback: uv desk dwell")
		hud.call("_show_notebook", 4)
		await _settle(0.3)
		L.uv_reveal("notebook_page")
		hud.call("_show_notebook", 4)
		await shot("notebook_uv_page")
		hud.call("_close_overlay")
		L.select_item("")
		step("UV reveals (page + desk)", func() -> bool: return s["uv_page"] and s["uv_desk"])
		await shard("under_desk", "under_desk")
		cam().go("lab")
		await _settle(0.8)
		await shard("radiator", "radiator")
		cam().go("lab")
		await _settle(0.8)
		await shard("coat_pocket", "coat")
		cam().go("lab")
		await _settle(0.8)
	# --- poster + safe (P4)
	if _from <= 4 and 4 <= _to:
		cam().go("lab")
		await _settle(0.8)
		await view("poster")
		await shot("poster_resonances")
		await view("safe")
		await shot("safe_keypad")
		for c in L.safe_code():
			var n0 := str(s["safe_input"]).length()
			await act("wall_safe", "IA_key_" + c, func() -> bool: return str(s["safe_input"]).length() > n0, func() -> void: L.safe_press(c), "key " + c)
		await act("wall_safe", "IA_key_enter", func() -> bool: return s["safe_open"], func() -> void: L.safe_press("E"), "enter")
		await _settle(1.4)
		await shot("safe_open")
		for spot in ["safe_key", "safe_lens", "safe_letter", "safe_valve"]:
			var item: String = Lab7Logic.SPOTS[spot]["item"]
			await act("wall_safe", "Item_" + spot, func() -> bool: return L.has_item(item), func() -> void: L.take(spot), spot)
		step("P4 safe %s → key, lens, letter, valve" % L.safe_code(), func() -> bool: return s["safe_open"] and L.has_item("crystal_lens"))
	# --- compartment (P5)
	if _from <= 5 and 5 <= _to:
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
	if _from <= 6 and 6 <= _to:
		cam().go("lab")
		await _settle(0.8)
		await view("panel")
		L.select_item("breaker_handle")
		await act("panel7", "IA_main_lever", func() -> bool: return s["handle_installed"], func() -> void: L.use_item_on("breaker_handle", "panel_main"), "install handle")
		for i: int in L.panel_solution(): # this game's wiring: the answer comes from the state
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
	if _from <= 7 and 7 <= _to:
		await view("chalkboard")
		await shot("chalkboard")
		await view("radio")
		L.select_item("radio_valve")
		await act("radio", "", func() -> bool: return s["valve_installed"], func() -> void: L.use_item_on("radio_valve", "radio"), "valve")
		var g := 0
		while not s["signal_heard"] and g < 30:
			g += 1
			var d0 := int(s["dial"])
			await act("radio", "IA_tuning_knob", func() -> bool: return int(s["dial"]) < d0, func() -> void: L.step_dial(-2), "tuning knob",
				Vector2(-0.6, 0))
		await _settle(1.5)
		await shot("radio_tuned_41m")
		step("P7/P8 radio valve + 41 m", func() -> bool: return s["signal_heard"])
	# --- books (P9)
	if _from <= 9 and 9 <= _to:
		cam().go("lab")
		await _settle(0.8)
		await view("books")
		await shot("encyclopedia")
		for n in L.beacon():
			var b0 := str(s["books"])
			await act("bookshelf", "IA_book_%d" % n, func() -> bool: return str(s["books"]) != b0 or s["shelf_open"], func() -> void: L.pull_book(n), "book %d" % n)
			await _settle(0.6)
		await _settle(2.6)
		cam().go("lab")
		await _settle(1.0)
		await view("bookshelf")
		await shot("bookcase_open")
		step("P9 books %s → darkroom" % "-".join(L.beacon().map(func(n: Variant) -> String: return Lab7Logic.roman(int(n)))), func() -> bool: return s["shelf_open"])
		await shard("bookshelf_top", "bookshelf_top") # rides on the swung bookcase
	# --- darkroom shadow + recording (P10)
	if _from <= 10 and 10 <= _to:
		cam().go("darkroom")
		await _settle(1.2)
		await shot("darkroom")
		await shard("darkroom", "darkroom_floor")
		cam().go("darkroom")
		await _settle(0.8)
		await view("shadow")
		await shot("shadow_misaligned")
		L.select_item("crystal_lens")
		await act("shadow_lock", "IA_emblem_socket", func() -> bool: return s["lens_at"] == "socket", func() -> void: L.use_item_on("crystal_lens", "emblem_socket"), "emblem socket")
		await view("sculpture")
		var guard := 0
		while not L.shadow_aligned() and guard < 14:
			guard += 1
			var p := 0 if int(s["shadow"][0]) != 0 else 1
			var sh0 := str(s["shadow"])
			await act("shadow_lock", "IA_ring_knob" if p == 0 else "IA_rod_knob", func() -> bool: return str(s["shadow"]) != sh0,
				func() -> void: L.turn_sculpture(p), "sculpture %d" % p)
		await view("shadow")
		await _settle(1.2)
		await shot("shadow_emblem_recorded")
		await view("cabinet")
		await act("shadow_lock", "Item_cabinet_mirror", func() -> bool: return L.has_item("mirror_item"), func() -> void: L.take("cabinet_mirror"), "mirror")
		L.remove_lens()
		step("P10 shadow lock + emblem recorded + mirror", func() -> bool: return s["emblem_recorded"] and L.has_item("mirror_item"))
	# --- projector (P11)
	if _from <= 11 and 11 <= _to:
		cam().go("lab")
		await _settle(1.0)
		await view("vials")
		await shot("vials_densities")
		await view("projector")
		L.select_item("crystal_lens")
		await act("lumen_projector", "IA_lens_socket", func() -> bool: return s["lens_at"] == "projector", func() -> void: L.use_item_on("crystal_lens", "projector"), "lens socket")
		await view("projector_rings")
		await shot("projector_rings_closeup")
		for i in 3:
			var gg := 0
			while int(s["rings"][i]) != Lab7Logic.RING_TARGET[i] and gg < 8:
				gg += 1
				var r0 := int(s["rings"][i])
				await act("lumen_projector", "IA_ring_%d" % i, func() -> bool: return int(s["rings"][i]) != r0, func() -> void: L.turn_ring(i), "ring %d" % i)
		await shot("projector_tuned")
		await view("projector")
		await act("lumen_projector", "IA_projector_lever", func() -> bool: return s["beam_on"], func() -> void: L.pull_projector_lever(), "lever")
		await _settle(1.0)
		await shot("projector_beam_on")
		step("P11 projector tuned → beam", func() -> bool: return s["beam_on"])
	# --- mirrors (P12)
	if _from <= 12 and 12 <= _to:
		await view("mirror_b")
		L.select_item("mirror_item")
		await act("mirror_stand_b", "IA_mirror_mount", func() -> bool: return s["mirror_b_mounted"], func() -> void: L.use_item_on("mirror_item", "mirror_stand_b"), "mount mirror")
		await view("mirror_a")
		var m := 0
		while int(s["mirrors"][0]) != 5 and m < 10:
			m += 1
			var a0 := int(s["mirrors"][0])
			await act("mirror_stand", "IA_mirror_mount", func() -> bool: return int(s["mirrors"][0]) == (a0 + 1) % 8, func() -> void: L.rotate_mirror(0, 1), "mirror A")
		cam().go("lab")
		await _settle(1.0)
		await shot("beam_first_mirror")
		await view("mirror_b")
		m = 0
		while int(s["mirrors"][1]) != 1 and not s["door_open"] and m < 10:
			m += 1
			var b1 := int(s["mirrors"][1])
			await act("mirror_stand_b", "IA_mirror_mount", func() -> bool: return int(s["mirrors"][1]) == (b1 + 1) % 8 or s["door_open"], func() -> void: L.rotate_mirror(1, 1), "mirror B")
		_log("  P12 state: mirrors %s, B mounted %s, beam %s, trace %s, emblem %s" % [str(s["mirrors"]),
			s["mirror_b_mounted"], s["beam_on"], L.trace_beam()["end"], s["emblem_recorded"]])
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
		step("Lumen shards 5/5", func() -> bool: return (s["shards"] as Array).size() == 5 or _from > 3)
	_finish()


func _finish() -> void:
	_log("taps through 3D scene: %d, logic fallbacks (missing models/placeholders): %d" % [taps_ok, taps_fallback])
	_log("taps under a HUD control: %d (window %dx%d)" % [taps_under_hud, get_viewport().get_visible_rect().size.x, get_viewport().get_visible_rect().size.y])
	var f := FileAccess.open(out_dir + "/playthrough_report.txt", FileAccess.WRITE)
	f.store_string("\n".join(report) + "\n")
	SaveSystem.delete_game()
	var ok: bool = logic.state["complete"] if _to >= 12 else not report.any(func(l: String) -> bool: return l.begins_with("✗"))
	var qa_exit: int = 0 if ok and taps_fallback == 0 else 1
	print("QA_DONE exit=%d" % qa_exit) # tools/qa_run.sh: the run finished even if the process then hangs on exit
	get_tree().quit(qa_exit)
