extends Node
## Player-style review of Chapter 2 (Records Archive B). It plays like a first-time player, not like the solver:
## - Chapter 1 finished with "take the lens", its chapter-complete screen and the main menu, then Chapter 2;
## - the real intro: the cards, the shutter slam, control handed back;
## - looking around the hall and tapping every main object;
## - wrong attempts, each of which must answer with a message or a caption;
## - the hint ladder, the documents, a language switch (RU, UZ, back to EN);
## - save → quit to the main menu → Continue;
## - the finale choice and the chapter-complete screen.
## Taps are real touch events pushed through the viewport, so the HUD blocks them where it would block a finger.
## Moving between views uses the player's own means: tapping an object, the Back button, free look at a root view.
## Every step leaves a screenshot and the exact HUD text the player saw (title, message, caption).
## Run: tools/qa_run.sh --stall=300 --log=<log> -- res://qa/player_review_ch2.tscn -- --out=<dir>
## Exit code 0 = no ✗ lines.

const LAB7_SCENE := "res://src/rooms/lab7/lab7.tscn"
const BOOTH_VIEWS := ["booth", "projector", "splicer", "slides", "slide_projector", "lens_case"]
const STALL_LIMIT_MS := 270000 # no report line for this long: the review itself is stuck (qa_run.sh kills at 300 s)

var out_dir := "/tmp/player_review_ch2"
var room: Node3D
var hud: Node
var logic: ArchiveLogic
var report: Array[String] = []
var shot_n := 0
var strings: Dictionary = {} # key -> {en, ru, uz} from localization/strings.csv
var feed: Array[Dictionary] = [] # every HUD title / message / caption that appeared, in order
var _was_vis: Dictionary = {"message": false, "caption": false}
var _last_txt: Dictionary = {"message": "", "caption": "", "title": ""}
var _taps_seen := 0
var taps_ok := 0
var taps_failed := 0
var t_start := 0
var _last_note_ms := 0
var _finished := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
	DirAccess.make_dir_recursive_absolute(out_dir)
	# QA-only files: the player's own save, profile and settings are never touched
	SaveSystem.save_path = "user://qa_review_ch2_save.json"
	SaveSystem.profile_path = "user://qa_review_ch2_profile.json"
	Settings.path = "user://qa_review_ch2_settings.cfg"
	Settings.values = Settings.DEFAULTS.duplicate()
	Settings.values["language"] = "en"
	SaveSystem.delete_game()
	_remove_user_file(SaveSystem.profile_path)
	_remove_user_file(Settings.path)
	GameState.profile = SaveSystem.load_profile()
	if "variant_seed" in GameState:
		GameState.set("variant_seed", 0) # the canonical answers; the script still reads them from the logic
	Loc.apply("en")
	_load_strings()
	t_start = Time.get_ticks_msec()
	_last_note_ms = t_start
	await get_tree().process_frame
	await run()


func run() -> void:
	await ch1_to_ch2() # 8. chapter transition (also how a player first arrives in Chapter 2)
	await intro() # 1
	await hints_start() # 4
	await read_doc("leyla_badge", "en") # 5
	await explore() # 2
	await early_mistakes() # 3
	await p1_catalogue()
	await p2_compressor()
	await p3_p4_tubes()
	await p5_locker()
	await language_switch() # 6
	await save_quit_continue() # 7
	await p6_hunt()
	await p7_deck()
	await p8_booth()
	await hint_after_booth() # 4 (later)
	await p9_splice()
	await p10_projector()
	await p11_record()
	await echoes()
	await p12_vault()
	await finale() # 9
	_finish()


# ====================================================================== report + watch
func note(line: String) -> void:
	report.append(line)
	print(line)
	_last_note_ms = Time.get_ticks_msec()


func check(label: String, ok: bool) -> void:
	note(("✓ " if ok else "✗ ") + label)


func _process(_delta: float) -> void:
	if not _finished and Time.get_ticks_msec() - _last_note_ms > STALL_LIMIT_MS:
		note("✗ the review stalled (no progress for %d s); last step above" % (STALL_LIMIT_MS / 1000))
		_finish()
		return
	if hud == null or not is_instance_valid(hud):
		return
	_poll("message", hud.get("_message") as Label)
	_poll("caption", hud.get("_caption_line") as Label)
	var top := hud.get("_top_caption") as Label
	if top and top.text != str(_last_txt["title"]):
		_last_txt["title"] = top.text
		if top.text != "":
			feed.append({"kind": "title", "text": tr(top.text)})


func _poll(kind: String, l: Label) -> void:
	if l == null:
		return
	var vis := l.modulate.a > 0.05 and l.text != ""
	if vis and (not bool(_was_vis[kind]) or l.text != str(_last_txt[kind])):
		feed.append({"kind": kind, "text": l.text})
	_was_vis[kind] = vis
	_last_txt[kind] = l.text


## Hide the current message and caption so the next action's answer is detected as new; returns the feed mark.
func mark() -> int:
	for k: String in ["_message", "_caption_line"]:
		var l := hud.get(k) as Label
		if l:
			l.modulate.a = 0.0
	_was_vis["message"] = false
	_was_vis["caption"] = false
	return feed.size()


func heard(since: int, kinds: Array = ["message", "caption"]) -> String:
	var parts: Array[String] = []
	for i in range(since, feed.size()):
		var e: Dictionary = feed[i]
		if kinds.has(str(e["kind"])):
			parts.append("%s «%s»" % [e["kind"], str(e["text"]).replace("\n", " ")])
	return "; ".join(parts)


func _kinds_since(since: int) -> String:
	var k: Array[String] = []
	for i in range(since, feed.size()):
		var kind := str((feed[i] as Dictionary)["kind"])
		if kind != "title" and not k.has(kind):
			k.append(kind)
	return " + ".join(k)


## Record what the game answered since `since`. With `expect`, the action is a wrong attempt that must answer.
func did(action: String, since: int, expect: bool) -> bool:
	await _settle(0.5)
	var got := heard(since)
	note("  • %s → view %s, title «%s»; %s" % [action, view_id(), title(), got if got != "" else "no message or caption"])
	if expect:
		if got != "":
			check("wrong attempt «%s» answers with a %s" % [action, _kinds_since(since)], true)
		else:
			check("wrong attempt «%s» gives no message or caption" % action, false)
	return got != ""


# ====================================================================== small helpers
func _settle(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()


func shot(name: String) -> void:
	await _settle(0.25)
	await RenderingServer.frame_post_draw
	shot_n += 1
	var p := "%s/%03d_%s.png" % [out_dir, shot_n, name]
	get_viewport().get_texture().get_image().save_png(p)
	report.append("    [shot %s]" % p.get_file())


func cam() -> RoomCamera:
	return room.get("cam") as RoomCamera


func view_id() -> String:
	if room == null or not is_instance_valid(room) or room.get("cam") == null:
		return "-"
	return cam().current()


func title() -> String:
	var top := hud.get("_top_caption") as Label
	return tr(top.text) if top and top.text != "" else ""


func model(id: String) -> Node3D:
	return (room.get("models") as Dictionary).get(id) as Node3D


func node_of(model_id: String, part_name: String) -> Node3D:
	var root := model(model_id)
	if root == null:
		return null
	return root if part_name == "" else ModelUtil.find(root, part_name)


func busy() -> bool:
	return bool(hud.get("_busy")) or bool(room.get("_cinematic"))


func wait_idle(limit: float = 60.0) -> void:
	var t := 0.0
	while busy() and t < limit:
		await _settle(0.25)
		t += 0.25


## Puzzle answers come from the logic (a game may carry its own variant), constants only as a fallback.
func _k(name: String, fallback: Variant) -> Variant:
	return (logic.get_script() as Script).get_script_constant_map().get(name, fallback)


func _ask(method: String, fallback: Variant) -> Variant:
	return logic.call(method) if logic.has_method(method) else fallback


func _remove_user_file(p: String) -> void:
	for f in [p, p + ".bak", p + ".tmp"]:
		if FileAccess.file_exists(f):
			DirAccess.remove_absolute(f)


func _load_strings() -> void:
	var f := FileAccess.open("res://localization/strings.csv", FileAccess.READ)
	if f == null:
		return
	var head := f.get_csv_line()
	var col := {"en": head.find("en"), "ru": head.find("ru"), "uz": head.find("uz")}
	while not f.eof_reached():
		var row := f.get_csv_line()
		if row.size() < head.size():
			continue
		strings[row[0]] = {"en": row[int(col["en"])], "ru": row[int(col["ru"])], "uz": row[int(col["uz"])]}


func _csv(key: String, code: String) -> String:
	return str((strings.get(key, {}) as Dictionary).get(code, "?"))


func _find_button(root: Node, text_key: String) -> Button:
	if root == null or not is_instance_valid(root):
		return null
	if root is Button and not root.is_queued_for_deletion() and ((root as Button).text == text_key or (root as Button).text == tr(text_key)):
		return root
	for c in root.get_children():
		var b := _find_button(c, text_key)
		if b:
			return b
	return null


## Press a HUD/menu button like a finger would: only if it is there, visible and enabled.
func press(b: Button, what: String) -> bool:
	if b == null or not is_instance_valid(b):
		check("button «%s» is there" % what, false)
		return false
	if not b.is_visible_in_tree() or b.disabled:
		check("button «%s» can be pressed (visible %s, disabled %s)" % [what, b.is_visible_in_tree(), b.disabled], false)
		return false
	b.emit_signal("pressed")
	return true


func _collect_texts(n: Node, out: Array[String]) -> void:
	if n == null or not is_instance_valid(n):
		return
	if n is CanvasItem and not (n as CanvasItem).is_visible_in_tree():
		return
	if n is Label and (n as Label).text != "":
		out.append(tr((n as Label).text).replace("\n", " "))
	if n is Button and (n as Button).text != "":
		out.append("[%s]" % tr((n as Button).text))
	for c in n.get_children():
		_collect_texts(c, out)


func _overlay_texts(o: Node) -> String:
	var t: Array[String] = []
	_collect_texts(o, t)
	return " | ".join(t)


func _first_texture(n: Node) -> Texture2D:
	if n == null:
		return null
	for t in n.find_children("*", "TextureRect", true, false):
		if (t as TextureRect).texture != null:
			return (t as TextureRect).texture
	return null


func _overlay() -> Node:
	return hud.get("_overlay") as Node


func press_escape() -> void:
	# Android back / Escape: SceneManager hands it to the current scene's handle_back()
	for pressed in [true, false]:
		var k := InputEventKey.new()
		k.keycode = KEY_ESCAPE
		k.physical_keycode = KEY_ESCAPE
		k.pressed = pressed
		get_viewport().push_input(k)
	await _settle(0.5)


func _wait_scene(pred: Callable, limit: float = 30.0) -> Node:
	var t := 0.0
	while t < limit:
		var cs := get_tree().current_scene
		if cs != null and is_instance_valid(cs) and cs.is_node_ready() and bool(pred.call(cs)):
			return cs
		await get_tree().process_frame
		t += get_process_delta_time()
	return null


func _is_main_menu(n: Node) -> bool:
	var s := n.get_script() as Script
	return s != null and s.resource_path.ends_with("main_menu.gd")


func _is_archive(n: Node) -> bool:
	return n is ArchiveRoom


func _bind(n: Node) -> void:
	room = n as Node3D
	hud = room.get("hud")
	logic = GameState.logic as ArchiveLogic
	var touch := room.get("touch") as TouchInput
	if touch and not touch.tapped.is_connected(_on_room_tapped):
		touch.tapped.connect(_on_room_tapped)
	_last_txt["title"] = ""


func _on_room_tapped(_p: Vector2) -> void:
	_taps_seen += 1


# ====================================================================== aiming and tapping
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
				if own_only:
					return Rect2()
				continue
			var sp := cam().unproject_position(wp)
			if first:
				r = Rect2(sp, Vector2.ZERO)
				first = false
			else:
				r = r.expand(sp)
	return r


func _centre_of(n: Node3D) -> Vector3:
	var ab := AABB()
	var first := true
	for mi in ModelUtil.find_meshes(n):
		var b := mi.global_transform * mi.get_aabb()
		ab = b if first else ab.merge(b)
		first = false
	return ab.get_center()


## Screen rectangles of HUD controls that stop a finger (buttons, open panels).
func _hud_blockers() -> Array[Rect2]:
	var out: Array[Rect2] = []
	if hud != null:
		_collect_blockers(hud.get("_root") as Control, out)
	return out


func _collect_blockers(n: Node, out: Array[Rect2]) -> void:
	if n == null:
		return
	if n is Control:
		var c := n as Control
		if not c.is_visible_in_tree():
			return
		if c.mouse_filter == Control.MOUSE_FILTER_STOP and c != hud.get("_root"):
			out.append(c.get_global_rect())
	for ch in n.get_children():
		_collect_blockers(ch, out)


func _blocked(p: Vector2, rects: Array[Rect2]) -> bool:
	for r in rects:
		if r.has_point(p):
			return true
	return false


func _resolves(sp: Vector2, model_id: String, part_name: String, accept: Array = []) -> bool:
	var h: Dictionary = room.call("raycast", sp)
	if h.is_empty():
		return false
	var r: Dictionary = room.call("resolve", h)
	if not accept.is_empty():
		return accept.has(str(r["part"]))
	return str(r["part"]) == part_name if part_name != "" else str(r["model"]) == model_id


## Where a player would tap to hit this part (or, with part "", any part of the model): the point nearest the
## middle where it is actually visible and not under a HUD button.
func _aim(model_id: String, part_name: String, frac: Vector2 = Vector2.ZERO, accept: Array = []) -> Vector2:
	var n := node_of(model_id, part_name)
	if n == null:
		return Vector2(-1, -1)
	var own := part_name != "" and not part_name.begins_with("Item_")
	var r := _rect(n, own)
	if r.size == Vector2.ZERO:
		r = _rect(n, false)
	if r.size == Vector2.ZERO:
		return Vector2(-1, -1)
	var screen := get_viewport().get_visible_rect()
	var blockers := _hud_blockers()
	var c := r.get_center() + frac * r.size * 0.5
	if frac != Vector2.ZERO:
		return c if screen.has_point(c) and not _blocked(c, blockers) else Vector2(-1, -1)
	if screen.has_point(c) and not _blocked(c, blockers) and _resolves(c, model_id, part_name, accept):
		return c
	var best := Vector2(-1, -1)
	var best_d := INF
	for gy in 11:
		for gx in 11:
			var p := r.position + r.size * Vector2(0.04 + 0.92 * gx / 10.0, 0.04 + 0.92 * gy / 10.0)
			if not screen.has_point(p) or _blocked(p, blockers):
				continue
			var d := p.distance_to(r.get_center())
			if d < best_d and _resolves(p, model_id, part_name, accept):
				best = p
				best_d = d
	return best


func _hit_at(sp: Vector2) -> String:
	var h: Dictionary = room.call("raycast", sp)
	if h.is_empty():
		return "nothing"
	var r: Dictionary = room.call("resolve", h)
	return "%s/%s/%s" % [r["model"], r["hotspot"], r["part"]]


func _hit(model_id: String, part_name: String, frac: Vector2 = Vector2.ZERO, accept: Array = []) -> String:
	if node_of(model_id, part_name) == null:
		return "part missing"
	var sp := _aim(model_id, part_name, frac, accept)
	if sp.x < 0:
		return "not visible from here (or only under the HUD)"
	return _hit_at(sp)


## A real touch: press and release pushed through the viewport (GUI first, then the room's TouchInput).
func tap_screen(sp: Vector2) -> bool:
	var t := 0.0
	while cam().transitioning and t < 2.0:
		await _settle(0.1)
		t += 0.1
	var before := _taps_seen
	for pressed in [true, false]:
		var ev := InputEventScreenTouch.new()
		ev.index = 0
		ev.position = sp
		ev.pressed = pressed
		get_viewport().push_input(ev, true)
	await _settle(0.45)
	return _taps_seen > before


func tap(model_id: String, part_name: String, frac: Vector2 = Vector2.ZERO, accept: Array = []) -> bool:
	var sp := _aim(model_id, part_name, frac, accept)
	if sp.x < 0:
		note("    (cannot see %s%s from view %s)" % [model_id, "/" + part_name if part_name != "" else "", view_id()])
		return false
	var ok := await tap_screen(sp)
	if not ok:
		note("    (the touch at %d,%d did not reach the room: HUD or input lock in the way)" % [int(sp.x), int(sp.y)])
	return ok


## Tap a part; it must make `cond` true. Otherwise the step is applied by a logic call (so the review goes on)
## and reported as ✗: a player tapping there would be stuck.
func act(label: String, model_id: String, part_name: String, cond: Callable, fallback: Callable, frac: Vector2 = Vector2.ZERO,
		accept: Array = []) -> bool:
	if not cond.call():
		await tap(model_id, part_name, frac, accept)
		await _settle(0.3)
	if cond.call():
		taps_ok += 1
		return true
	var why := _hit(model_id, part_name, frac, accept)
	fallback.call()
	taps_failed += 1
	note("✗ tapping does not do it: %s (%s/%s in view %s; the tap hits %s) — applied by a logic call to go on" % [label,
		model_id, part_name, view_id(), why])
	await _settle(0.9)
	return false


## Tap a part that should open another view.
func nav(label: String, model_id: String, part_name: String, expect: String) -> bool:
	return await act(label, model_id, part_name, func() -> bool: return cam().current() == expect,
		func() -> void: cam().go(expect))


## A wrong attempt: tap, wait for the answer, record it (must be a message or a caption).
func attempt(action: String, model_id: String, part_name: String, wait: float = 0.0) -> bool:
	var aim := _hit(model_id, part_name)
	var since := mark()
	var reached := await tap(model_id, part_name)
	if wait > 0.0:
		await _settle(wait)
	await wait_idle()
	if not reached or not aim.ends_with("/" + part_name) and part_name != "":
		note("    (aimed at %s/%s, the tap hits %s)" % [model_id, part_name, aim])
	return await did(action, since, true)


func pick(id: String) -> void:
	if logic.selected == id:
		return
	var b := _slot_button(id)
	if b != null and b.is_visible_in_tree():
		b.emit_signal("pressed")
		await _settle(0.3)
	if logic.selected != id:
		note("✗ tapping the inventory slot of %s does not select it" % id)
		logic.select_item(id)
		await _settle(0.2)


func unpick() -> void:
	if logic.selected != "":
		room.call("handle_back")
		await _settle(0.3)


func _slot_button(id: String) -> Button:
	var box := hud.get("_inv_box") as HBoxContainer
	var idx := logic.inventory.find(id)
	if box == null or idx < 0:
		return null
	var slots: Array[Button] = []
	for c in box.get_children():
		if c is Button and not c.is_queued_for_deletion():
			slots.append(c as Button)
	return slots[idx] if idx < slots.size() else null


# ====================================================================== moving around like a player
func press_back_button() -> void:
	var b := hud.get("_back_btn") as Button
	if b != null and b.is_visible_in_tree():
		b.emit_signal("pressed")
	else:
		room.call("go_back")
	await _settle(0.85)


func to_hall() -> void:
	for i in 12:
		if cam().current() == "hall":
			return
		if _overlay() != null:
			room.call("handle_back")
			await _settle(0.4)
			continue
		if busy():
			await wait_idle()
			continue
		await press_back_button()
	if cam().current() != "hall":
		note("✗ Back does not lead back to the hall from «%s»" % cam().current())
		cam().go("hall")
		await _settle(0.9)


## The booth root: Back from a booth close-up, or (from the hall) the booth door, then the open door again.
func to_booth() -> void:
	for i in 3:
		if cam().current() == "booth" or not BOOTH_VIEWS.has(cam().current()):
			break
		await press_back_button()
	if cam().current() == "booth":
		return
	await unpick()
	await open_from("hall", "booth_door", "booth_door")
	await nav("walk through the open booth door", "booth_door", "", "booth")


func to_root(root_view: String) -> void:
	if root_view == "hall":
		await to_hall()
	else:
		await to_booth()


## Free-look the root camera toward a world point, like a player dragging to look around.
func look_toward(p: Vector3) -> void:
	var c := cam()
	var dir := (p - c.global_position).normalized()
	var base: Dictionary = c.views[c.current()]
	var t := Transform3D(Basis.IDENTITY, base["pos"]).looking_at(base["target"], Vector3.UP)
	var fwd0 := -t.basis.z
	var yaw := rad_to_deg(atan2(fwd0.x, fwd0.z) - atan2(dir.x, dir.z))
	var pitch := rad_to_deg(asin(clampf(dir.y, -1.0, 1.0)) - asin(clampf(fwd0.y, -1.0, 1.0)))
	c.yaw = wrapf(-yaw, -180.0, 180.0)
	c.pitch = clampf(pitch, RoomCamera.PITCH_MIN, RoomCamera.PITCH_MAX)
	c.call("_apply_free_look")
	if not _on_screen(p):
		var best_yaw := c.yaw
		var best_d := INF
		for step in 36:
			c.yaw = wrapf(step * 10.0 - 180.0, -180.0, 180.0)
			c.call("_apply_free_look")
			if c.is_position_behind(p):
				continue
			var d := c.unproject_position(p).distance_to(get_viewport().get_visible_rect().get_center())
			if d < best_d:
				best_d = d
				best_yaw = c.yaw
		c.yaw = best_yaw
		c.call("_apply_free_look")
	await _settle(0.35)


func _on_screen(p: Vector3) -> bool:
	return not cam().is_position_behind(p) and get_viewport().get_visible_rect().grow(-40.0).has_point(cam().unproject_position(p))


## From a root view: look at the object and tap it; it must open `expect`. If its middle does not, tap the other
## parts of it a player can see. Returns false (and reports ✗) when no visible part of it opens the view.
func open_from(root_view: String, model_id: String, expect: String, report_fail: bool = true) -> bool:
	await to_root(root_view)
	var n := model(model_id)
	if n == null:
		note("✗ model missing: " + model_id)
		return false
	await look_toward(_centre_of(n))
	var start := cam().current()
	await tap(model_id, "")
	await _settle(0.5)
	var went := cam().current()
	if went != expect:
		for body in n.find_children("*", "StaticBody3D", true, false):
			if cam().current() == expect:
				break
			if cam().current() != start:
				await to_root(root_view)
				await look_toward(_centre_of(n))
			var cs := body.get_child(0) as Node3D
			var p := cs.global_position if cs else (body as Node3D).global_position
			if cam().is_position_behind(p):
				continue
			var sp := cam().unproject_position(p)
			if not get_viewport().get_visible_rect().has_point(sp) or _blocked(sp, _hud_blockers()):
				continue
			var h: Dictionary = room.call("raycast", sp)
			if h.is_empty() or str((room.call("resolve", h) as Dictionary)["model"]) != model_id:
				continue
			await tap_screen(sp)
			await _settle(0.5)
		if cam().current() == expect:
			note("    (the first tap on %s went to «%s»; another visible part of it opens «%s»)" % [model_id, went, expect])
	if cam().current() != expect:
		if report_fail:
			note("✗ tapping %s from the %s does not open its view «%s» (camera at «%s»)" % [model_id, root_view, expect, cam().current()])
		else:
			note("    (no visible part of %s opens «%s»; the camera is at «%s»)" % [model_id, expect, cam().current()])
		cam().go(expect)
		await _settle(0.9)
		return false
	return true


func _target_area(id: String) -> Dictionary:
	var r := _rect(model(id), false).intersection(get_viewport().get_visible_rect())
	if r.size == Vector2.ZERO:
		return {"w": 0.0, "h": 0.0, "area": 0.0}
	var hits := 0
	var blockers := _hud_blockers()
	var n := 15
	for gy in n:
		for gx in n:
			var p := r.position + r.size * Vector2((gx + 0.5) / n, (gy + 0.5) / n)
			if not _blocked(p, blockers) and _resolves(p, id, ""):
				hits += 1
	return {"w": r.size.x, "h": r.size.y, "area": r.get_area() * hits / float(n * n)}


func _meter() -> int:
	var m := hud.get("_meter") as Control
	if m == null or not m.visible:
		return -1
	var lit := 0
	for b: Variant in (hud.get("_meter_bars") as Array):
		if (b as ColorRect).color.is_equal_approx(Color("7dff9a")):
			lit += 1
	return lit


# ====================================================================== layout (overflow, clipping, glyphs)
func layout_check(root: Node, where: String) -> void:
	if root == null or not is_instance_valid(root):
		note("  (layout %s: nothing open)" % where)
		return
	await _settle(0.15)
	var issues: Array[String] = []
	_layout_walk(root, get_viewport().get_visible_rect(), issues)
	if issues.is_empty():
		check("layout %s: no text off screen, clipped, spilling out of its panel or missing glyphs" % where, true)
	for i in issues:
		check("layout %s: %s" % [where, i], false)


## The in-room HUD: the generic checks plus the lines that share the screen with each other.
func hud_layout_check(where: String) -> void:
	await layout_check(hud.get("_root"), where)
	var msg := hud.get("_message") as Label
	var inv := hud.get("_inv_panel") as Control
	var top := hud.get("_top_caption") as Label
	var cap := hud.get("_caption_line") as Label
	if msg and msg.modulate.a > 0.05 and inv and inv.is_visible_in_tree() and msg.get_global_rect().intersects(inv.get_global_rect()):
		check("layout %s: the message «%s» overlaps the inventory bar" % [where, msg.text.substr(0, 40)], false)
	if top and top.text != "" and top.get_line_count() > 1:
		note("  ! layout %s: the title «%s» wraps to %d lines" % [where, tr(top.text), top.get_line_count()])
		if cap and cap.modulate.a > 0.05 and top.get_global_rect().intersects(cap.get_global_rect()):
			check("layout %s: the wrapped title overlaps the caption line" % where, false)


func _layout_walk(n: Node, vr: Rect2, issues: Array[String]) -> void:
	if n is CanvasItem and not (n as CanvasItem).is_visible_in_tree():
		return
	if (n is Label or n is Button) and (n as Control).modulate.a > 0.05:
		var c := n as Control
		var text := c.atr(str(c.get("text")))
		if text.strip_edges() != "":
			var r := c.get_global_rect()
			var short := text.substr(0, 48).replace("\n", " ")
			if not vr.grow(1.0).encloses(r):
				issues.append("«%s» runs off the screen (box %d,%d %d×%d)" % [short, int(r.position.x), int(r.position.y), int(r.size.x), int(r.size.y)])
			var font := c.get_theme_font("font")
			var fs := c.get_theme_font_size("font_size")
			if n is Label:
				var l := n as Label
				if l.autowrap_mode == TextServer.AUTOWRAP_OFF:
					var w := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
					if w > r.size.x + 2.0:
						issues.append("«%s» is wider than its label (%d > %d px)" % [short, int(w), int(r.size.x)])
				elif l.get_visible_line_count() < l.get_line_count():
					issues.append("«%s» has %d lines but shows %d" % [short, l.get_line_count(), l.get_visible_line_count()])
				elif l.get_line_count() >= 4 and r.size.x < 160.0:
					issues.append("«%s» is squeezed into a %d px column (%d lines)" % [short, int(r.size.x), l.get_line_count()])
			else:
				var b := n as Button
				var sb := b.get_theme_stylebox("normal")
				var pad := (sb.get_content_margin(SIDE_LEFT) + sb.get_content_margin(SIDE_RIGHT)) if sb else 0.0
				var w := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x + pad
				if w > r.size.x + 2.0 and b.autowrap_mode == TextServer.AUTOWRAP_OFF:
					issues.append("button «%s»: the text is wider than the button (%d > %d px)" % [short, int(w), int(r.size.x)])
			var panel := _panel_of(c)
			if panel != null and not panel.get_global_rect().grow(1.0).encloses(r):
				issues.append("«%s» spills out of its panel" % short)
			var missing := ""
			for i in text.length():
				var code := text.unicode_at(i)
				if code > 32 and not font.has_char(code) and not missing.contains(char(code)):
					missing += char(code)
			if missing != "":
				issues.append("«%s» uses characters missing from its font: %s" % [short, missing])
	for ch in n.get_children():
		_layout_walk(ch, vr, issues)


func _panel_of(c: Control) -> Control:
	var p := c.get_parent()
	while p != null and p is Control:
		if p is ScrollContainer:
			return null # scrolled content may extend beyond its window by design
		if p is PanelContainer:
			return p as Control
		p = p.get_parent()
	return null


# ====================================================================== 8. Chapter 1 → Chapter 2
func ch1_to_ch2() -> void:
	note("== Chapter transition: finish Chapter 1 with «take the lens», then go on to Chapter 2")
	GameState.start_new("ch1")
	var l1 := GameState.logic as Lab7Logic
	var lab := (load(LAB7_SCENE) as PackedScene).instantiate() as Node3D
	lab.set("capture_mode", true) # the Chapter 1 review covers its intro
	get_tree().root.add_child.call_deferred(lab)
	await get_tree().process_frame
	await get_tree().process_frame
	get_tree().current_scene = lab # the review node itself must survive scene changes
	room = lab
	hud = lab.get("hud")
	await _settle(1.0)
	var steps := 0
	while not l1.state["door_open"] and steps < 400:
		steps += 1
		Lab7Solver.step(l1, "take_lens")
		if steps % 15 == 0:
			await get_tree().process_frame
	note("  Chapter 1 played to the open door by its solver (%d steps; the Chapter 1 review covers its taps); shards %d" % [
		steps, (l1.state["shards"] as Array).size()])
	var w := 0.0
	while _overlay() == null and w < 60.0:
		await _settle(0.25)
		w += 0.25
	await shot("ch1_finale_choice")
	var take := _find_button(_overlay(), "ui.take_lens")
	check("Chapter 1 finale offers «take the lens»", take != null)
	if not press(take, "take the lens"):
		l1.choose_ending("take_lens")
	await _settle(3.0)
	await shot("ch1_chapter_complete")
	check("Chapter 1 complete", l1.state["complete"])
	var o := _overlay()
	note("  Chapter 1 complete screen: " + _overlay_texts(o))
	var mem: Dictionary = GameState.profile.get("choices", {})
	var disk: Dictionary = SaveSystem.load_profile().get("choices", {})
	check("profile choices.ch1_lens = take_lens (memory %s, disk %s)" % [mem.get("ch1_lens", "-"), disk.get("ch1_lens", "-")],
		str(mem.get("ch1_lens", "")) == "take_lens" and str(disk.get("ch1_lens", "")) == "take_lens")
	var play := _find_button(o, "ui.play")
	if play != null and play.is_visible_in_tree():
		check("the Chapter 1 complete screen offers «Play» for Chapter 2", true)
		play.emit_signal("pressed")
	else:
		note("! the Chapter 1 complete screen has no «Play» for Chapter 2; it says «%s» (Premium.can_play(\"ch2\") = %s, Chapters ch2 released = %s)" % [
			tr("ui.to_be_continued"), Premium.can_play("ch2"), Chapters.get_chapter("ch2").get("released", false)])
		press(_find_button(o, "ui.main_menu"), "Main menu")
		var mm := await _wait_scene(_is_main_menu)
		hud = null
		if mm == null:
			check("«Main menu» opens the main menu", false)
		else:
			await _settle(1.0)
			await shot("main_menu_after_ch1")
			note("  main menu: " + _overlay_texts(mm))
			if press(_find_button(mm, "ui.chapters"), "Chapters"):
				await _settle(0.8)
				await shot("chapters_menu")
				for id in ["ch1", "ch2"]:
					var b := _chapter_button(mm, "chapter.%s.title" % id)
					note("  chapters menu, %s: button «%s», %s" % [id, tr(b.text) if b else "-", "disabled" if b and b.disabled else "enabled"])
				var b2 := _chapter_button(mm, "chapter.ch2.title")
				if b2 != null and not b2.disabled:
					b2.emit_signal("pressed")
				else:
					press(_find_button(mm, "ui.close"), "Close")
		if not (get_tree().current_scene is ArchiveRoom):
			note("  → no button leads to Chapter 2 yet; starting it with the same two calls the «Play» button makes (hud.gd show_chapter_complete): GameState.start_new(\"ch2\") + SceneManager.goto(scene)")
			if GameState.start_new("ch2"):
				SceneManager.goto(str(Chapters.get_chapter("ch2")["scene"]))
	var ar := await _wait_scene(_is_archive, 40.0)
	if ar == null:
		check("Chapter 2 scene loads", false)
		_finish()
		return
	_bind(ar)
	var s := logic.state
	note("== Chapter 2 starts with the Chapter 1 choices")
	check("state.has_lens = true (Chapter 1 took the lens)", s["has_lens"])
	check("inventory: Leyla's badge + the crystal lens (%s)" % ", ".join(logic.inventory), logic.has_item("leyla_badge") and logic.has_item("crystal_lens"))
	check("state.ch1_shards = profile ch1_shards (%d)" % int(s["ch1_shards"]), int(s["ch1_shards"]) == int((GameState.profile.get("choices", {}) as Dictionary).get("ch1_shards", -1)))


func _chapter_button(root: Node, title_key: String) -> Button:
	for l in root.find_children("*", "Label", true, false):
		if (l as Label).text == title_key:
			for c in l.get_parent().get_children():
				if c is Button:
					return c as Button
	return null


# ====================================================================== 1. intro
func _intro_overlay() -> ColorRect:
	var r := hud.get("_root") as Control
	if r == null:
		return null
	for c in r.get_children():
		if c is ColorRect and c != _overlay() and (c as ColorRect).mouse_filter == Control.MOUSE_FILTER_STOP and not c.is_queued_for_deletion():
			return c as ColorRect
	return null


func _intro_text(o: Node) -> String:
	if o == null or not is_instance_valid(o):
		return ""
	for c in o.get_children():
		if c is Label and (c as Label).modulate.a > 0.05 and (c as Label).text != "" and (c as Label).text != "ui.tap_to_continue":
			return (c as Label).text
	return ""


func intro() -> void:
	note("== Intro on the first entry")
	var since := feed.size()
	var o := _intro_overlay()
	check("the intro starts on the first entry (input locked: %s)" % bool(hud.get("_busy")), o != null and bool(hud.get("_busy")))
	await _settle(1.4)
	await shot("intro_card1")
	note("  card 1 on screen: «%s»" % _intro_text(o))
	check("card 1 is intro2.1", _intro_text(o) == tr("intro2.1"))
	var t := 0.0
	while t < 12.0 and _intro_text(o) != tr("intro2.2"):
		await _settle(0.2)
		t += 0.2
	await _settle(1.0)
	await shot("intro_card2")
	note("  card 2 on screen: «%s» (card 1 stayed %.1f s)" % [_intro_text(o), 1.4 + t])
	# a first-time player taps to move on
	var tap_ms := Time.get_ticks_msec()
	for pressed in [true, false]:
		var ev := InputEventScreenTouch.new()
		ev.position = get_viewport().get_visible_rect().get_center()
		ev.pressed = pressed
		get_viewport().push_input(ev, true)
	var slam_alpha := -1.0
	var slam_view := ""
	t = 0.0
	while t < 12.0:
		var m := hud.get("_message") as Label
		if m.modulate.a > 0.05 and m.text == tr("msg.c2_shutter"):
			slam_alpha = o.color.a if is_instance_valid(o) else 0.0
			slam_view = view_id()
			break
		await get_tree().process_frame
		t += get_process_delta_time()
	var dt := (Time.get_ticks_msec() - tap_ms) / 1000.0
	await shot("intro_shutter_slam")
	check("tap to continue ends card 2 early (the slam comes %.1f s after the tap)" % dt, slam_alpha >= 0.0 and dt < 4.0)
	note("  the shutter slams: message «%s», view «%s», title «%s»; the black intro screen is still %d%% opaque" % [
		tr("msg.c2_shutter"), slam_view, title(), int(maxf(slam_alpha, 0.0) * 100.0)])
	await _settle(0.6)
	await shot("intro_after_slam")
	t = 0.0
	while busy() and t < 20.0:
		await _settle(0.25)
		t += 0.25
	var touch := room.get("touch") as TouchInput
	check("the intro hands control back (view «%s», input %s)" % [view_id(), "on" if touch.enabled else "off"],
		not busy() and touch.enabled and view_id() == "hall" and _intro_overlay() == null)
	await shot("intro_control_back")
	await _settle(1.8)
	await shot("first_screen")
	var all := heard(since, ["title", "message", "caption"])
	note("  everything the opening showed: %s" % all)
	var tut := heard(since, ["caption"]).contains(tr("tut.look"))
	check("the first screen shows the controls («%s»)" % tr("tut.look"), tut)
	note("  ! the first screen names no goal: the title «%s», the slam message and the controls line; the badge (0417) is only in the inventory" % title())


# ====================================================================== 4. hints
func hints_start() -> void:
	var goal := logic.hint_goal()
	note("== Hint ladder at the start (goal %s)" % goal)
	var hb := hud.get("_hint_btn") as Button
	if not press(hb, "hint"):
		return
	await _settle(0.6)
	var o := _overlay()
	await shot("hint_level1")
	var texts: Array[String] = [_overlay_texts(o)]
	note("  level 1: " + texts[0])
	var more := _find_button(o, "ui.hint_more")
	for lvl in [2, 3]:
		if more != null and not more.disabled:
			more.emit_signal("pressed")
			await _settle(0.5)
			await shot("hint_level%d" % lvl)
			texts.append(_overlay_texts(o))
			note("  level %d: %s" % [lvl, texts[-1]])
	check("each level shows new text (3 levels)", texts.size() == 3 and texts[0] != texts[1] and texts[1] != texts[2])
	check("«%s» is disabled at level 3" % tr("ui.hint_more"), more != null and more.disabled)
	await layout_check(o, "hint panel EN")
	await press_escape()
	check("Back (Android back / Escape) closes the hint panel", _overlay() == null)


func hint_after_booth() -> void:
	var goal := logic.hint_goal()
	note("== One hint later in the chapter (after the booth opened; goal %s)" % goal)
	await to_booth()
	if not press(hud.get("_hint_btn") as Button, "hint"):
		return
	await _settle(0.6)
	var o := _overlay()
	await shot("hint_after_booth")
	var txt := _overlay_texts(o)
	note("  level 1: " + txt)
	check("the hint is about the splicer (goal %s, text hint.%s.1)" % [goal, goal], goal == "c2_splice" and txt.contains(tr("hint.c2_splice.1")))
	press(_find_button(o, "ui.close"), "Close")
	await _settle(0.4)
	check("«Close» closes the hint panel", _overlay() == null)


# ====================================================================== 5. documents
func read_doc(id: String, tag: String, expect_tex: String = "") -> void:
	note("== Document: %s (%s)" % [id, tag])
	if not logic.has_item(id):
		check("%s is in the inventory" % id, false)
		return
	await pick(id)
	var slot := _slot_button(id)
	if slot != null:
		slot.emit_signal("pressed") # tapping the selected item again inspects it
	else:
		hud.call("show_inspect", id)
	await _settle(1.4)
	var o := _overlay()
	check("tapping the selected %s opens the inspect view" % id, o != null)
	await shot("inspect_%s_%s" % [id, tag])
	note("  inspect: " + _overlay_texts(o))
	if not press(_find_button(o, "ui.read"), "Read"):
		await unpick()
		return
	await _settle(0.8)
	o = _overlay()
	await shot("doc_%s_%s" % [id, tag])
	var tex := _first_texture(o)
	var txt := _overlay_texts(o)
	note("  document: %s%s" % [txt if txt != "" else "(picture only)", " · picture " + tex.resource_path.get_file() if tex else ""])
	if id in ["leyla_badge", "index_card"]:
		check("the %s picture is shown" % id, tex != null)
		if expect_tex != "":
			check("the picture is the %s variant (%s)" % [tag, expect_tex], tex != null and tex.resource_path.get_file() == expect_tex)
	else:
		check("the %s document has text" % id, txt.length() > 20)
	await layout_check(o, "document %s %s" % [id, tag])
	room.call("handle_back")
	await _settle(0.4)
	check("Back closes the document", _overlay() == null)
	await unpick()


# ====================================================================== 2. explore from the hall
const EXPLORE := [["catalogue", "card_catalogue"], ["compressor", "compressor_panel"], ["tube station", "tube_station"],
	["routing chart", "routing_chart"], ["archivist's desk", "archivist_desk"], ["lockers", "lockers"],
	["stacks", "stacks_shelving"], ["reading table", "reading_table"], ["floor hatch", "floor_hatch"],
	["vent grille", "vent_grille"], ["booth door", "booth_door"], ["vault", "vault_door"], ["projection screen", "projection_screen"]]


func explore() -> void:
	note("== Explore from the hall: look at each main object and tap it")
	for e: Array in EXPLORE:
		var label: String = e[0]
		var id: String = e[1]
		var n := model(id)
		if n == null:
			check("model %s exists" % id, false)
			continue
		await to_hall()
		var expect := str(room.call("hotspot_view", str(n.get_meta("hotspot", ""))))
		await look_toward(_centre_of(n))
		var area := _target_area(id)
		await shot("look_" + expect)
		var since := mark()
		var ok := await open_from("hall", id, expect, false)
		await _settle(0.3)
		await shot("view_" + expect)
		var side := sqrt(float(area["area"]))
		note("  • %s: on screen ≈ %d×%d px, tappable ≈ %d px² (≈ %d px square) → view «%s», title «%s»%s" % [label,
			int(area["w"]), int(area["h"]), int(area["area"]), int(side), view_id(), title(),
			"; " + heard(since) if heard(since) != "" else ""])
		if side < 70.0:
			note("  ! small target from the hall: the %s is about %d px square (screen 1920×1080)" % [label, int(side)])
		check("tapping the %s from the hall opens its own view «%s» with a title" % [label, expect], ok and title() != "")
	await to_hall()


# ====================================================================== 3. wrong attempts before any progress
func early_mistakes() -> void:
	note("== Wrong attempts before any progress")
	var s := logic.state
	# the vault wheel while the bolts are in
	await open_from("hall", "vault_door", "vault")
	await attempt("turn the vault wheel while it is locked", "vault_door", "IA_vault_handle")
	await shot("wrong_vault_wheel")
	# the booth dial with a guessed code
	await open_from("hall", "booth_door", "booth_door")
	await nav("the dial", "booth_door", "IA_dial_hole_1", "dial")
	var since := mark()
	for d in [1, 2, 3]:
		var n0 := str(s["dial_input"]).length()
		await act("dial %d" % d, "booth_door", "IA_dial_hole_%d" % d, func() -> bool: return str(s["dial_input"]).length() != n0 or s["booth_open"],
			func() -> void: logic.dial_digit(d))
		await _settle(0.9)
	await did("dial a guessed code 1-2-3 on the booth door", since, true)
	await shot("wrong_dial_code")
	check("a wrong code clears the dial and keeps the booth shut", str(s["dial_input"]) == "" and not s["booth_open"])
	# an item on an unrelated object: Leyla's badge on the compressor
	await to_hall()
	await pick("leyla_badge")
	await open_from("hall", "compressor_panel", "compressor")
	await attempt("use Leyla's badge on the compressor (unrelated object)", "compressor_panel", "")
	check("the badge stays in the inventory", logic.has_item("leyla_badge"))
	await unpick()
	# valves that give no pressure
	since = mark()
	for v in ["c", "a"]:
		var i := "abc".find(v)
		var v0 := int(s["valves"][i])
		await act("valve " + v.to_upper(), "compressor_panel", "IA_valve_" + v, func() -> bool: return int(s["valves"][i]) != v0,
			func() -> void: logic.turn_valve(i, 1))
	await _settle(1.0)
	await did("turn valves A and C once (A 1, B 0, C 1: no pressure)", since, true)
	var marks: Array = s.get("v_targets", [5, 4])
	note("    the gauges now read P %d and F %d (green marks %d and %d): the needles move and the valves squeak, nothing on screen says the pressure is still too low" % [
		logic.pressure(), logic.flow(), int(marks[0]), int(marks[1])])
	await shot("wrong_valves")
	# the tube station without pressure
	await open_from("hall", "tube_station", "station")
	await attempt("pull the tube station's send lever without pressure", "tube_station", "IA_send_lever")
	await shot("station_no_pressure")


# ====================================================================== the chapter, with its wrong turns
func p1_catalogue() -> void:
	note("== P1 card catalogue (badge 0417 → drawer 04, divider 1–, card 17)")
	var s := logic.state
	var dr := int(_k("CAT_DRAWER", 4))
	var gr := int(_k("CAT_GROUP", 1))
	var cd := int(_k("CAT_CARD", 7))
	await open_from("hall", "card_catalogue", "catalogue")
	await shot("catalogue")
	await act("drawer 0%d" % dr, "card_catalogue", "IA_cat_drawer_%d" % dr, func() -> bool: return int(s["cat_drawer"]) == dr,
		func() -> void: logic.open_cat_drawer(dr))
	await _settle(0.8)
	note("  drawer open → view «%s», title «%s»" % [view_id(), title()])
	await act("divider %d–" % gr, "card_catalogue", "IA_divider_%d" % gr, func() -> bool: return int(s["cat_group"]) == gr,
		func() -> void: logic.pick_divider(gr))
	await _settle(0.8)
	await shot("catalogue_section")
	var wrong := (cd + 6) % 10
	await attempt("pull a wrong card (0%d%d%d)" % [dr, gr, wrong], "card_catalogue", "IA_card_%d" % wrong)
	await shot("wrong_card")
	var since := mark()
	await act("pull card 0%d%d%d" % [dr, gr, cd], "card_catalogue", "IA_card_%d" % cd, func() -> bool: return s["card_shown"],
		func() -> void: logic.pull_card(cd))
	await did("pull Leyla's card", since, false)
	await shot("card_leyla")
	await act("take the index card", "card_catalogue", "IA_card_%d" % cd, func() -> bool: return logic.has_item("index_card"),
		func() -> void: logic.take("index_card"))
	check("P1 → Leyla's index card", logic.has_item("index_card"))
	await read_doc("index_card", "en")


func p2_compressor() -> void:
	var s := logic.state
	var want: Array = _ask("valve_solution", [1, 2, 2])
	note("== P2 compressor (valves %s)" % str(want))
	await open_from("hall", "compressor_panel", "compressor")
	var since := mark()
	for i in 3:
		for _k2 in posmod(int(want[i]) - int(s["valves"][i]), 5):
			var v0 := int(s["valves"][i])
			await act("valve " + "ABC"[i], "compressor_panel", "IA_valve_" + "abc"[i],
				func() -> bool: return int(s["valves"][i]) != v0 or s["pressure_ok"], func() -> void: logic.turn_valve(i, 1))
	await _settle(1.2)
	await did("set the valves right", since, false)
	await shot("compressor_pressure")
	check("P2 → pressure", s["pressure_ok"])


func _punch(code: Array, label: String) -> void:
	var s := logic.state
	await open_from("hall", "archivist_desk", "desk")
	await nav("the card punch", "card_punch", "", "punch")
	await pick("blank_card")
	await act("blank card into the punch", "card_punch", "IA_punch_slot", func() -> bool: return s["card_in_punch"],
		func() -> void: logic.use_item_on("blank_card", "punch"))
	for i in 8:
		if int(code[i]) == 1:
			await act("key %d" % (i + 1), "card_punch", "IA_punch_key_%d" % i, func() -> bool: return int(s["punch_keys"][i]) == 1,
				func() -> void: logic.toggle_punch_key(i))
	await shot("punch_" + label)
	await act("punch lever", "card_punch", "IA_punch_lever", func() -> bool: return logic.has_item("request_card"),
		func() -> void: logic.pull_punch_lever())


func _send(label: String, wrong: bool) -> void:
	var s := logic.state
	var since := mark()
	await act("send lever", "tube_station", "IA_send_lever", func() -> bool: return s["canister"] == "" or busy(),
		func() -> void: logic.send_canister())
	await _settle(2.0)
	await shot("tube_" + label.replace(" ", "_"))
	await wait_idle()
	await _settle(0.5)
	await did(label, since, wrong)


func _load_canister() -> void:
	var s := logic.state
	await pick("request_card")
	await act("card into the canister", "tube_station", "IA_send_port", func() -> bool: return s["canister"] != "",
		func() -> void: logic.use_item_on("request_card", "send_port"))


func p3_p4_tubes() -> void:
	note("== P3/P4 request card and the pneumatic post")
	var s := logic.state
	var stacks := int(_k("DEST_STACKS", 1))
	await open_from("hall", "tube_station", "station")
	await act("take a blank card from the tray", "tube_station", "IA_card_tray", func() -> bool: return logic.has_item("blank_card"),
		func() -> void: logic.take("tray_card"))
	await open_from("hall", "archivist_desk", "desk")
	await nav("the card punch", "card_punch", "", "punch")
	await attempt("press a punch key with no card in the punch", "card_punch", "IA_punch_key_0")
	# a careless first card: only hole 1
	await _punch([1, 0, 0, 0, 0, 0, 0, 0], "wrong")
	note("  first card punched with hole 1 only (request_ok %s)" % s["request_ok"])
	# the dial starts on ✦ Director: a wrong destination
	await open_from("hall", "tube_station", "station")
	await _load_canister()
	await _send("send the canister with the dial on destination %d (not the stacks)" % int(s["dest"]), true)
	check("the canister brings the card back", logic.has_item("request_card"))
	# the stacks, with the wrongly punched card
	await _load_canister()
	for _g in 8:
		if int(s["dest"]) == stacks:
			break
		var d0 := int(s["dest"])
		await act("destination dial", "tube_station", "IA_dest_dial", func() -> bool: return int(s["dest"]) != d0,
			func() -> void: logic.step_dest(1))
	await _send("send the wrongly punched card to the stacks", true)
	check("the stacks keep the wrong card and the tray gives a fresh blank", not logic.has_item("request_card") and logic.can_take("tray_card"))
	# the right card
	await act("take a fresh blank card", "tube_station", "IA_card_tray", func() -> bool: return logic.has_item("blank_card"),
		func() -> void: logic.take("tray_card"))
	await _punch(_k("PUNCH_CODE", [1, 0, 1, 1, 0, 0, 1, 0]), "right")
	check("P3 → a correctly punched request card", logic.has_item("request_card") and s["request_ok"])
	await open_from("hall", "tube_station", "station")
	await _load_canister()
	await _send("send the right card to the stacks", false)
	check("P4 → the file is delivered", s["file_delivered"])
	var vis: Node = room.get("visuals")
	await act("open the receive tray", "tube_station", "IA_receive_tray", func() -> bool: return bool(vis.get("tray_open")),
		func() -> void: vis.set("tray_open", true))
	await _settle(0.6)
	await shot("station_file")
	await act("take the file", "tube_station", "Item_canister_file", func() -> bool: return logic.has_item("personnel_file"),
		func() -> void: logic.take("canister_file"))
	await act("take the key", "tube_station", "Item_canister_key", func() -> bool: return logic.has_item("locker_key"),
		func() -> void: logic.take("canister_key"))
	check("P4 → personnel file + locker key", logic.has_item("personnel_file") and logic.has_item("locker_key"))
	await read_doc("personnel_file", "en")


func p5_locker() -> void:
	note("== P5 locker 9")
	var s := logic.state
	await open_from("hall", "lockers", "lockers")
	await attempt("open locker 3 by hand", "lockers", "IA_locker_3")
	await pick("locker_key")
	await attempt("use the locker key on locker 4", "lockers", "IA_locker_4")
	check("the key stays in the inventory", logic.has_item("locker_key"))
	await pick("locker_key")
	await act("key on locker 9", "lockers", "IA_locker_9", func() -> bool: return s["locker_open"],
		func() -> void: logic.use_item_on("locker_key", "locker_9"))
	await _settle(1.2)
	await shot("locker9_open")
	await act("take the receiver", "lockers", "Item_locker_receiver", func() -> bool: return logic.has_item("pocket_receiver"),
		func() -> void: logic.take("locker_receiver"))
	check("P5 → pocket receiver", logic.has_item("pocket_receiver"))


# ====================================================================== 6. language
func _choose_language(code: String) -> void:
	await to_hall()
	if not press(hud.get("_pause_btn") as Button, "pause"):
		return
	await _settle(0.5)
	if not press(_find_button(_overlay(), "ui.settings"), "Settings"):
		return
	await _settle(0.7)
	var o := _overlay()
	press(_find_button(o, str(Loc.NATIVE_NAMES[code])), str(Loc.NATIVE_NAMES[code]))
	await _settle(0.7)
	await shot("settings_" + code)
	await layout_check(o, "settings panel " + code)
	press(_find_button(o, "ui.close"), "Close")
	await _settle(0.7)
	o = _overlay()
	await shot("pause_" + code)
	note("  pause menu: " + _overlay_texts(o))
	check("the pause menu is in %s" % code, _overlay_texts(o).contains(_csv("ui.resume", code)))
	await layout_check(o, "pause menu " + code)
	press(_find_button(o, "ui.resume"), "Resume")
	await _settle(0.4)


func _title_ok(code: String, where: String) -> void:
	var top := hud.get("_top_caption") as Label
	var key := top.text if top else ""
	check("%s title in %s: «%s»" % [where, code, title()], key != "" and title() == _csv(key, code) and (code == "en" or title() != _csv(key, "en")))


func language_switch() -> void:
	note("== Language: switch to RU, then UZ, then back to EN (pause → Settings → language)")
	for code: String in ["ru", "uz", "en"]:
		await _choose_language(code)
		check("the game language is now %s" % code, Loc.current() == code)
		await to_hall()
		_title_ok(code, "hall")
		if code == "en":
			continue
		# a view title and a message
		await open_from("hall", "compressor_panel", "compressor")
		_title_ok(code, "compressor")
		var since := mark()
		await tap("compressor_panel", "IA_valve_a")
		await _settle(0.6)
		var got := heard(since, ["message"])
		note("  valve after the pressure is set → %s" % got)
		check("message in %s («%s»)" % [code, _csv("msg.c2_valves_locked", code)], got.contains(_csv("msg.c2_valves_locked", code)))
		await shot("lang_%s_compressor_message" % code)
		await hud_layout_check("HUD %s, compressor with a message" % code)
		await open_from("hall", "vault_door", "vault")
		_title_ok(code, "vault")
		await shot("lang_%s_vault" % code)
		await hud_layout_check("HUD %s, vault (longest title)" % code)
		await open_from("hall", "lockers", "lockers")
		since = mark()
		await tap("lockers", "IA_locker_3")
		await _settle(0.6)
		got = heard(since, ["message"])
		check("«locked» message in %s (%s)" % [code, got], got.contains(_csv("msg.c2_locker_locked", code)))
		# the badge picture
		await to_hall()
		await read_doc("leyla_badge", code, "badge_%s.png" % code)
		# the hint panel
		if press(hud.get("_hint_btn") as Button, "hint"):
			await _settle(0.6)
			var o := _overlay()
			await shot("lang_%s_hint" % code)
			var txt := _overlay_texts(o)
			note("  hint panel: " + txt)
			check("the hint panel is in %s" % code, txt.contains(_csv("ui.hint", code)) and txt.contains(_csv("ui.close", code)))
			await layout_check(o, "hint panel " + code)
			press(_find_button(o, "ui.close"), "Close")
			await _settle(0.4)
	await shot("lang_back_en")


# ====================================================================== 7. save → quit → continue
func save_quit_continue() -> void:
	note("== Save → quit to the main menu → Continue (after the locker)")
	await to_hall()
	await unpick()
	var before := JSON.stringify(logic.to_dict())
	var play_before := GameState.play_time
	var hints_before := GameState.hints_used
	if not press(hud.get("_pause_btn") as Button, "pause"):
		return
	await _settle(0.5)
	await shot("pause_before_quit")
	var menu := _find_button(_overlay(), "ui.main_menu")
	if not press(menu, "Main menu"):
		return
	var mm := await _wait_scene(_is_main_menu)
	hud = null
	check("«Main menu» saves and opens the main menu", mm != null and SaveSystem.has_save() and GameState.saved_chapter() == "ch2")
	if mm == null:
		return
	await _settle(1.0)
	await shot("main_menu_after_quit")
	note("  main menu: " + _overlay_texts(mm))
	if not press(_find_button(mm, "ui.continue"), "Continue"):
		return
	var ar := await _wait_scene(_is_archive, 40.0)
	if ar == null:
		check("Continue opens Chapter 2", false)
		return
	_bind(ar)
	await _settle(2.5)
	var after := JSON.stringify(logic.to_dict())
	check("Continue restores exactly the saved state", after == before)
	if after != before:
		note("    before: " + before.substr(0, 400))
		note("    after:  " + after.substr(0, 400))
	check("the intro does not replay", _intro_overlay() == null and not bool(hud.get("_busy")))
	check("the camera starts at the hall (view «%s»)" % view_id(), view_id() == "hall")
	check("play time and hints used carry over (%.0f s → %.0f s, hints %d → %d)" % [play_before, GameState.play_time, hints_before, GameState.hints_used],
		GameState.play_time >= play_before - 1.0 and GameState.hints_used == hints_before)
	await shot("continued_hall")
	await open_from("hall", "lockers", "lockers")
	await nav("open locker 9", "lockers", "IA_locker_9", "locker9")
	await shot("continued_locker9")
	check("locker 9 is drawn open and empty after Continue", logic.state["locker_open"] and not logic.can_take("locker_receiver"))


# ====================================================================== the rest of the chapter
func p6_hunt() -> void:
	note("== P6 receiver hunt")
	var s := logic.state
	await to_hall()
	var since := mark()
	await pick("pocket_receiver")
	await _settle(0.6)
	note("  receiver selected at the hall: meter %d/5; %s" % [_meter(), heard(since)])
	await shot("receiver_hall")
	await open_from("hall", "vent_grille", "grille")
	note("  meter at the grille: %d/5" % _meter())
	await act("open the grille", "vent_grille", "IA_grille", func() -> bool: return s["grille_open"],
		func() -> void: logic.open_hiding_place("grille"))
	await _settle(0.9)
	await shot("grille_open")
	await act("take reel 1996", "vent_grille", "Item_grille_reel", func() -> bool: return logic.has_item("tape_1996"),
		func() -> void: logic.take("grille_reel"))
	note("  meter after taking it: %d/5" % _meter())
	await open_from("hall", "stacks_shelving", "stacks")
	note("  meter at the stacks: %d/5" % _meter())
	await nav("the hollow ledger", "stacks_shelving", "IA_ledger", "ledger")
	note("  meter at the ledger: %d/5" % _meter())
	await act("open the ledger", "stacks_shelving", "IA_ledger", func() -> bool: return s["ledger_open"],
		func() -> void: logic.open_hiding_place("ledger"))
	await _settle(0.9)
	await act("take reel 1997", "stacks_shelving", "Item_ledger_reel", func() -> bool: return logic.has_item("tape_1997"),
		func() -> void: logic.take("ledger_reel"))
	await open_from("hall", "floor_hatch", "hatch")
	note("  meter at the hatch: %d/5" % _meter())
	await act("open the hatch", "floor_hatch", "IA_hatch", func() -> bool: return s["hatch_open"],
		func() -> void: logic.open_hiding_place("hatch"))
	await _settle(1.2)
	await shot("hatch_open")
	await act("take reel 1998", "floor_hatch", "Item_hatch_reel", func() -> bool: return logic.has_item("tape_1998"),
		func() -> void: logic.take("hatch_reel"))
	await unpick()
	check("P6 → three reels", logic.has_item("tape_1996") and logic.has_item("tape_1997") and logic.has_item("tape_1998"))


func _wait_tape() -> void:
	var vis: Node = room.get("visuals")
	var t := 0.0
	while t < 30.0 and bool(vis.get("_tape_playing")):
		await _settle(0.5)
		t += 0.5


func p7_deck() -> void:
	note("== P7 tape deck")
	var s := logic.state
	var speeds: Array = _k("SPEEDS", ["2.4", "4.75", "9.5", "19"])
	var right := int(_k("SPEED_RIGHT", 1))
	await open_from("hall", "archivist_desk", "desk")
	await nav("the tape deck", "tape_deck", "", "deck")
	await attempt("press Play with no reel on the deck", "tape_deck", "IA_play")
	await pick("tape_1996")
	await act("reel 1996 onto the deck", "tape_deck", "", func() -> bool: return s["deck_tape"] == "tape_1996",
		func() -> void: logic.use_item_on("tape_1996", "deck"))
	await attempt("play reel 1996 at %s cm/s (wrong speed)" % speeds[int(s["deck_speed"])], "tape_deck", "IA_play", 1.0)
	await shot("deck_wrong_speed")
	await _wait_tape()
	for _g in 8:
		if int(s["deck_speed"]) == right:
			break
		var sp0 := int(s["deck_speed"])
		await act("speed knob", "tape_deck", "IA_speed", func() -> bool: return int(s["deck_speed"]) != sp0,
			func() -> void: logic.step_speed(1))
	for tape: String in ["tape_1996", "tape_1997", "tape_1998"]:
		if s["deck_tape"] != tape:
			await pick(tape)
			await act("load " + tape, "tape_deck", "", func() -> bool: return s["deck_tape"] == tape,
				func() -> void: logic.use_item_on(tape, "deck"))
		var since := mark()
		await act("play " + tape, "tape_deck", "IA_play", func() -> bool: return (s["clicks_heard"] as Array).has(tape),
			func() -> void: logic.play_tape())
		await _settle(2.5)
		await shot("deck_" + tape)
		await _wait_tape()
		note("  %s at %s: %s" % [tape, speeds[int(s["deck_speed"])], heard(since, ["caption", "message"])])
	check("P7 → all three reels heard", (s["clicks_heard"] as Array).size() == 3)
	await read_doc("tape_1997", "heard")


func p8_booth() -> void:
	var s := logic.state
	var code := str(_ask("booth_code", "285"))
	note("== P8 booth dial %s" % code)
	await open_from("hall", "booth_door", "booth_door")
	await nav("the dial", "booth_door", "IA_dial_hole_%s" % code[0], "dial")
	var since := mark()
	for ch in code:
		var d := int(ch)
		var n0 := str(s["dial_input"]).length()
		await act("dial %d" % d, "booth_door", "IA_dial_hole_%d" % d, func() -> bool: return str(s["dial_input"]).length() != n0 or s["booth_open"],
			func() -> void: logic.dial_digit(d))
		await _settle(0.9)
	await wait_idle()
	await _settle(0.8)
	await did("dial %s" % code, since, false)
	await shot("booth_open")
	check("P8 → the booth opens and the camera steps inside (view «%s»)" % view_id(), s["booth_open"] and view_id() == "booth")


func p9_splice() -> void:
	note("== P9 film splicer")
	var s := logic.state
	await to_booth()
	await open_from("booth", "film_splicer", "splicer")
	await shot("splicer_loose")
	var since := mark()
	for k in 4:
		await act("pick strip %d" % k, "film_splicer", "IA_frame_%d" % k, func() -> bool: return int(room.get("_held_frame")) == k,
			func() -> void: room.set("_held_frame", k))
		await act("strip %d into slot %d" % [k, k + 1], "film_splicer", "IA_slot_%d" % k, func() -> bool: return int(s["splice"][k]) == k,
			func() -> void: logic.splice_put(k, k))
	await _settle(0.8)
	await did("splice the strips in the order they lie (f0 f1 f2 f3, not by shadow)", since, true)
	await shot("splice_wrong")
	check("a wrong order leaves the reel torn", not s["reel_repaired"])
	var order: Array = _ask("splice_order", [2, 0, 3, 1])
	since = mark()
	for slot in 4:
		var f := int(order[slot])
		if int(s["splice"][slot]) == f:
			continue
		await act("pick strip %d" % f, "film_splicer", "IA_frame_%d" % f, func() -> bool: return int(room.get("_held_frame")) == f,
			func() -> void:
				var at := (s["splice"] as Array).find(f)
				if at >= 0:
					logic.splice_lift(at)
				room.set("_held_frame", f))
		await act("strip %d into slot %d" % [f, slot + 1], "film_splicer", "IA_slot_%d" % slot, func() -> bool: return int(s["splice"][slot]) == f,
			func() -> void: logic.splice_put(f, slot))
	await _settle(0.8)
	await did("splice by shadow length %s" % str(order), since, false)
	await shot("splice_right")
	check("P9 → the reel is repaired", s["reel_repaired"])
	await act("take the film reel", "film_splicer", "Item_splicer_reel", func() -> bool: return logic.has_item("film_reel"),
		func() -> void: logic.take("splicer_reel"))


func p10_projector() -> void:
	note("== P10 film projector")
	var s := logic.state
	await to_booth()
	await open_from("booth", "film_projector", "projector")
	await attempt("pull the projector's run lever with no reel threaded", "film_projector", "IA_run_lever")
	note("    the lamp is %s and the big screen shows «%s» (the screen is not in this view)" % ["on" if s["projector_on"] else "off", logic.screen_image()])
	await shot("projector_no_reel")
	var since := mark()
	await act("run lever off again", "film_projector", "IA_run_lever", func() -> bool: return not s["projector_on"],
		func() -> void: logic.toggle_projector())
	await did("switch the empty projector off", since, false)
	await pick("film_reel")
	await act("thread the reel (reel selected, tap the projector)", "film_projector", "IA_run_lever", func() -> bool: return s["reel_on_projector"],
		func() -> void: logic.use_item_on("film_reel", "projector"))
	since = mark()
	await act("run lever", "film_projector", "IA_run_lever", func() -> bool: return s["projector_on"], func() -> void: logic.toggle_projector())
	await _settle(4.0)
	await shot("film_frame")
	await _settle(9.0)
	await shot("film_later")
	await wait_idle(90.0)
	note("  the film: " + heard(since))
	check("P10 → the film is seen", s["film_seen"])
	if view_id() != "projector":
		await open_from("booth", "film_projector", "projector")
	var sharp := int(_ask("focus_sharp", 5))
	for _g in 12:
		if int(s["focus"]) == sharp:
			break
		var f0 := int(s["focus"])
		await act("focus ring", "film_projector", "IA_focus_ring", func() -> bool: return int(s["focus"]) != f0,
			func() -> void: logic.turn_focus(1))
	check("the picture is sharp (focus %d)" % int(s["focus"]), int(s["focus"]) == sharp)


func p11_record() -> void:
	note("== Crystals and P11 recording the sign")
	var s := logic.state
	var vis: Node = room.get("visuals")
	await to_booth()
	await open_from("booth", "lens_case", "lens_case")
	await act("open the lens case", "lens_case", "IA_case_lid", func() -> bool: return bool(vis.get("case_open")),
		func() -> void: vis.set("case_open", true))
	await _settle(0.8)
	await shot("lens_case_open")
	for k in [1, 2]:
		await act("take crystal %d" % k, "lens_case", "Item_case_crystal_%d" % k, func() -> bool: return logic.has_item("crystal_blank_%d" % k),
			func() -> void: logic.take("case_crystal_%d" % k))
	await to_hall()
	await open_from("hall", "projection_screen", "screen")
	await shot("screen_sign")
	await nav("the crystal socket", "projection_screen", "IA_screen_socket", "socket")
	await pick("crystal_lens")
	await attempt("seat the crystal lens in the screen socket", "projection_screen", "IA_screen_socket")
	await pick("crystal_blank_1")
	var since := mark()
	await act("seat a blank crystal", "projection_screen", "IA_screen_socket", func() -> bool: return s["sign_recorded"],
		func() -> void: logic.use_item_on("crystal_blank_1", "screen_socket"))
	await _settle(1.0)
	await did("record the sign", since, false)
	await shot("socket_recorded")
	await act("take the sign crystal", "projection_screen", "IA_screen_socket", func() -> bool: return logic.has_item("crystal_sign"),
		func() -> void: logic.take_from_socket(), Vector2.ZERO, ["IA_screen_socket", "Item_socket", "socket_ring"])
	check("P11 → crystal with Leyla's sign", logic.has_item("crystal_sign"))


func echoes() -> void:
	note("== Optional: kept echoes (seen while a crystal is held)")
	var s := logic.state
	await to_hall()
	var since := mark()
	await pick("crystal_lens")
	await _settle(1.0)
	note("  holding the crystal lens: %s" % heard(since))
	for id: String in ["catalogue", "stacks"]:
		var n := model("echo_" + id)
		if n == null or not n.visible:
			note("  ! the %s echo is not shown at the hall" % id)
			continue
		await look_toward(_centre_of(n))
		await shot("echo_" + id)
		since = mark()
		var aim := _hit("echo_" + id, "")
		await tap("echo_" + id, "")
		await _settle(1.2)
		var got := (s["echoes"] as Array).has(id)
		note("  • tap the %s echo from the hall (aim hits %s) → %s; %s" % [id, aim, "released" if got else "not released", heard(since)])
		if not got:
			note("  ! the %s echo cannot be released by tapping it from the hall" % id)
	# into the booth with the crystal held: the open door answers like an unrelated object
	await open_from("hall", "booth_door", "booth_door")
	since = mark()
	await tap("booth_door", "")
	await _settle(0.6)
	note("  • tap the open booth door while holding the crystal → view «%s»; %s" % [view_id(), heard(since)])
	if view_id() != "booth":
		note("  ! holding a crystal (needed to see the echoes) blocks walking into the booth: the open door answers «%s»; the player must put the crystal away first" % heard(since))
	await unpick()
	await to_booth()
	await pick("crystal_lens")
	await _settle(0.6)
	var nb := model("echo_booth")
	if nb != null and nb.visible:
		await look_toward(_centre_of(nb))
		await shot("echo_booth")
		since = mark()
		await tap("echo_booth", "")
		await _settle(1.2)
		note("  • tap Strand's echo in the booth → %s; %s" % ["released" if (s["echoes"] as Array).has("booth") else "not released", heard(since)])
	else:
		note("  ! Strand's echo is not shown in the booth")
	await unpick()
	note("  kept echoes released: %d / 3" % (s["echoes"] as Array).size())


func p12_vault() -> void:
	note("== P12 dual light lock")
	var s := logic.state
	await to_hall()
	await open_from("hall", "vault_door", "vault")
	await shot("vault_closed")
	await nav("the ports", "vault_door", "IA_port_left", "vault_ports")
	await pick("crystal_blank_2")
	await attempt("seat a blank crystal in the left port", "vault_door", "IA_port_left")
	await shot("vault_blank_port")
	await act("take the blank crystal back out", "vault_door", "IA_port_left", func() -> bool: return s["port_left"] == "",
		func() -> void: logic.take_from_port("left"), Vector2.ZERO, ["IA_port_left", "Item_port_left"])
	check("the blank crystal is back in the inventory", logic.has_item("crystal_blank_2"))
	var mark_crystal := "crystal_lens" if s["has_lens"] else "crystal_mark"
	await pick(mark_crystal)
	await act("mark crystal, left port", "vault_door", "IA_port_left", func() -> bool: return s["port_left"] == mark_crystal,
		func() -> void: logic.use_item_on(mark_crystal, "port_left"))
	await pick("crystal_sign")
	await act("sign crystal, right port", "vault_door", "IA_port_right", func() -> bool: return s["port_right"] == "crystal_sign",
		func() -> void: logic.use_item_on("crystal_sign", "port_right"))
	await shot("vault_ports_filled")
	var since := mark()
	var rt := int(_k("ROT_RIGHT_TARGET", 2))
	var zt := int(_k("ZOOM_TARGET", 3))
	for _g in 10:
		if int(s["rot_left"]) % 4 == 0 or s["vault_unlocked"]:
			break
		var a0 := int(s["rot_left"])
		await act("left collar", "vault_door", "IA_collar_left", func() -> bool: return int(s["rot_left"]) != a0, func() -> void: logic.turn_collar("rot_left"))
	for _g in 10:
		if int(s["rot_right"]) == rt or s["vault_unlocked"]:
			break
		var b0 := int(s["rot_right"])
		await act("right collar", "vault_door", "IA_collar_right", func() -> bool: return int(s["rot_right"]) != b0, func() -> void: logic.turn_collar("rot_right"))
	for _g in 10:
		if int(s["zoom_right"]) == zt or s["vault_unlocked"]:
			break
		var z0 := int(s["zoom_right"])
		await act("zoom collar", "vault_door", "IA_zoom_right", func() -> bool: return int(s["zoom_right"]) != z0, func() -> void: logic.turn_collar("zoom_right"))
	await _settle(1.5)
	await did("align the overlay", since, false)
	await shot("vault_unlocked")
	check("P12 → the vault unlocks", s["vault_unlocked"])
	await press_back_button()
	if view_id() != "vault":
		await open_from("hall", "vault_door", "vault")
	for _i in int(_k("WHEEL_TURNS", 3)):
		var w0 := int(s["wheel"])
		await act("vault wheel", "vault_door", "IA_vault_handle", func() -> bool: return int(s["wheel"]) != w0 or s["vault_open"],
			func() -> void: logic.turn_wheel())
		await _settle(0.7)
	check("the vault opens", s["vault_open"])


# ====================================================================== 9. finale
func finale() -> void:
	note("== Finale: the vault reel, two keys, the chapter-complete screen")
	var s := logic.state
	var since := feed.size()
	var w := 0
	while _overlay() == null and w < 240:
		w += 1
		await _settle(0.25)
		if w == 14:
			await shot("finale_vault_open")
		if w == 30:
			await shot("finale_vault_reel")
	note("  before the choice: " + heard(since))
	await shot("finale_choice")
	var o := _overlay()
	note("  choice: " + _overlay_texts(o))
	var strand := _find_button(o, "ui.take_strand_key")
	var leyla := _find_button(o, "ui.take_leyla_key")
	check("both keys are offered (Strand's and Leyla's)", strand != null and leyla != null)
	await layout_check(o, "finale choice EN")
	await press_escape()
	check("Back does not dismiss the finale choice", _overlay() != null)
	if not press(strand, "Strand's key"):
		logic.choose_ending("strand_key")
	await _settle(3.0)
	await shot("chapter_complete")
	check("the choice sets state.choice = strand_key and completes the chapter", s["choice"] == "strand_key" and s["complete"])
	var mem: Dictionary = GameState.profile.get("choices", {})
	var disk: Dictionary = SaveSystem.load_profile().get("choices", {})
	check("profile choices.ch2_key = strand_key (memory %s, disk %s)" % [mem.get("ch2_key", "-"), disk.get("ch2_key", "-")],
		str(mem.get("ch2_key", "")) == "strand_key" and str(disk.get("ch2_key", "")) == "strand_key")
	check("profile keeps choices.ch1_lens = take_lens", str(disk.get("ch1_lens", "")) == "take_lens")
	o = _overlay()
	note("  chapter screen: " + _overlay_texts(o))
	for key in ["ui.chapter_complete", "chapter.ch2.title", "ui.time", "ui.puzzles", "ui.hints_used", "ui.echoes"]:
		var v := _stat_value(o, key)
		check("chapter screen shows «%s»%s" % [tr(key), " = " + v if v != "" else ""], _has_label(o, key))
	await layout_check(o, "chapter-complete screen EN")
	await press_escape()
	check("Back does not dismiss the chapter-complete screen", _overlay() != null)


func _has_label(root: Node, key: String) -> bool:
	for l in root.find_children("*", "Label", true, false):
		if (l as Label).text == key and (l as Label).is_visible_in_tree():
			return true
	return false


func _stat_value(root: Node, key: String) -> String:
	if root == null:
		return ""
	for l in root.find_children("*", "Label", true, false):
		if (l as Label).text == key:
			var p := l.get_parent()
			var i := l.get_index()
			if p is VBoxContainer and i + 1 < p.get_child_count() and p.get_child(i + 1) is Label:
				return (p.get_child(i + 1) as Label).text
	return ""


func _finish() -> void:
	if _finished:
		return
	_finished = true
	note("taps pushed through the viewport that did their job: %d; steps that needed a logic call: %d" % [taps_ok, taps_failed])
	note("review runtime (in-game clock): %.1f min" % ((Time.get_ticks_msec() - t_start) / 60000.0))
	var f := FileAccess.open(out_dir + "/player_review_ch2.txt", FileAccess.WRITE)
	f.store_string("\n".join(report) + "\n")
	f.close()
	SaveSystem.delete_game()
	_remove_user_file(SaveSystem.profile_path)
	_remove_user_file(Settings.path)
	var bad := report.filter(func(l: String) -> bool: return l.begins_with("✗")).size()
	print("player review ch2: %d problems" % bad)
	var qa_exit: int = 0 if bad == 0 else 1
	print("QA_DONE exit=%d" % qa_exit) # tools/qa_run.sh: the run finished even if the process then hangs on exit
	get_tree().quit(qa_exit)
