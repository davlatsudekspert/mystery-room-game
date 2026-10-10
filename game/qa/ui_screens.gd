extends Node
## QA: renders the menus and in-game overlays in EN, RU and UZ to check layout/fonts on a real frame, and measures
## every visible text and touch target (canvas px and mm on the emulated screen) into <out>/measure.json.
## Run (always through the watchdog, one Godot process at a time):
##   tools/qa_run.sh --stall=300 --log=<log> -- res://qa/ui_screens.tscn -- --out=<dir> [options]
## Options:
##   --langs=en,ru,uz       languages to render (the language picker is shown once, with the first language)
##   --menus-only           skip the in-game overlays
##   --device=<id>          phone61 (6.1" 2340x1080 ~400 dpi, left cutout), phone67 (6.7" 2796x1290 ~460 dpi,
##                          left/right sensor housing + home indicator), phone55 (5.5" 1920x1080 ~480 dpi, 16:9),
##                          tablet10 (10" 2048x1536 264 dpi), iphone (the owner's 19.5:9 iPhone, 2556x1179 460 dpi,
##                          notch + home indicator), android20 (20:9 Android, 2400x1080 405 dpi, punch hole + gesture
##                          bar), ipad (4:3, 2048x1536 264 dpi, home indicator)
##   --size=WxH --dpi=N     emulate any screen (overrides the preset); --safe=l,t,r,b insets in screen px
##   --text-scale=X         the player's Settings → Text size (0.9 / 1.0 / 1.15 / 1.3)
##   --saved                start with a saved game, so the main menu shows Continue
##   --mobile               menus as on a phone or tablet (no Quit item): Settings.emulate["mobile"]
##   --highlight=N          show main menu item N (0 = first) pressed/hovered in the main menu shots
##   --clean                do not draw the cutout zones on the screenshots (preview images; still measured)
##   --window=WxH           render window (default: the emulated screen). Same aspect = same canvas layout. Use one
##                          that fits the Xvfb screen (1280x1024) for builds that read DisplayServer's safe area
##                          directly: a window larger than the X screen makes it report bogus insets.
##   --shots=a,b            save and measure only the shots whose name contains one of these (e.g. settings,hud_item);
##                          the screens are still walked through, so a shot sees the same state as in a full run
##   --view=a,b             also shoot these close-ups of the room with an item in hand (<lang>_view_<id>), and with
##                          the bag open (<lang>_view_<id>_bag)
##   --probe=model/part     in each close-up, report whether that part (e.g. panel7/IA_main_lever) lies under a HUD
##                          control that stops taps (measure.json "_probe"); --show-blocked tints those controls
## HUD shots (names with "hud" or "view") also report HUD elements that overlap each other.
## Exit code 0 = no measured layout issue (clipped label, text wider than its button, element off-screen or under
## the emulated cutout). The window is resized to the emulated screen. If the X server cannot fit it, it renders at the same aspect ratio
## (identical canvas layout, lower pixel count) and says so. The emulated screen also drives the game's automatic
## text scale and safe area (Settings.emulate); the measurements use the same numbers.

const DEVICES := {
	"phone61": {"size": Vector2i(2340, 1080), "dpi": 400.0, "insets": [120, 0, 0, 0]},
	"phone67": {"size": Vector2i(2796, 1290), "dpi": 460.0, "insets": [177, 0, 177, 63]},
	"phone55": {"size": Vector2i(1920, 1080), "dpi": 480.0, "insets": [0, 0, 0, 0]},
	"tablet10": {"size": Vector2i(2048, 1536), "dpi": 264.0, "insets": [0, 0, 0, 0]},
	"iphone": {"size": Vector2i(2556, 1179), "dpi": 460.0, "insets": [177, 0, 177, 63]},
	"android20": {"size": Vector2i(2400, 1080), "dpi": 405.0, "insets": [100, 0, 0, 56]},
	"ipad": {"size": Vector2i(2048, 1536), "dpi": 264.0, "insets": [0, 0, 0, 40]},
}

var out_dir := "/tmp"
var screen_size := Vector2i.ZERO # emulated screen in device px (ZERO = the real window)
var dpi := 0.0
var insets: Array = [0, 0, 0, 0] # l, t, r, b in device px
var text_scale := 1.0
var window_size := Vector2i.ZERO
var report: Dictionary = {}
var clean := false # --clean: no cutout zones drawn on the screenshots
var shots_filter: PackedStringArray = [] # --shots=: only these are saved and measured
var views: PackedStringArray = [] # --view=: close-ups to shoot
var probe := "" # --probe=model/part
var show_blocked := false # --show-blocked
var _cutout_layer: CanvasLayer


func _ready() -> void:
	_run.call_deferred() # the root is still busy adding children during _ready


func _run() -> void:
	var langs: PackedStringArray = ["en", "ru", "uz"]
	var menus_only := false
	var saved := false
	var mobile := false
	var highlight := -1
	var device := ""
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--langs="):
			langs = a.substr(8).split(",", false)
		elif a == "--menus-only":
			menus_only = true
		elif a == "--saved":
			saved = true
		elif a == "--mobile":
			mobile = true
		elif a.begins_with("--highlight="):
			highlight = int(a.substr(12))
		elif a == "--clean":
			clean = true
		elif a.begins_with("--shots="):
			shots_filter = a.substr(8).split(",", false)
		elif a.begins_with("--device="):
			device = a.substr(9)
		elif a.begins_with("--view="):
			views = a.substr(7).split(",", false)
		elif a.begins_with("--probe="):
			probe = a.substr(8)
		elif a == "--show-blocked":
			show_blocked = true
	if device != "":
		var d: Dictionary = DEVICES[device]
		screen_size = d["size"]
		dpi = d["dpi"]
		insets = (d["insets"] as Array).duplicate()
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--size="):
			var p := a.substr(7).split("x")
			screen_size = Vector2i(int(p[0]), int(p[1]))
		elif a.begins_with("--dpi="):
			dpi = float(a.substr(6))
		elif a.begins_with("--safe="):
			var p := a.substr(7).split(",")
			insets = [int(p[0]), int(p[1]), int(p[2]), int(p[3])]
		elif a.begins_with("--text-scale="):
			text_scale = float(a.substr(13))
		elif a.begins_with("--window="):
			var p := a.substr(9).split("x")
			window_size = Vector2i(int(p[0]), int(p[1]))
	DirAccess.make_dir_recursive_absolute(out_dir)
	await _apply_screen()
	if mobile:
		Settings.emulate["mobile"] = true
	SaveSystem.save_path = "user://qa_ui_save.json"
	Premium.path = "user://qa_ui_entitlements.cfg" # nothing owned: the chapter list offers Unlock
	Premium.revoke_all_for_tests()
	if saved:
		GameState.start_new("ch1") # saves: the menu offers Continue
	for li in langs.size():
		var lang := langs[li]
		TranslationServer.set_locale(lang)
		Settings.values["text_scale"] = text_scale
		# --- first-launch language picker, main menu, settings, chapters
		if li == 0: # the picker shows all three languages at once
			var picker: Control = (load("res://src/ui/language_select.tscn") as PackedScene).instantiate()
			get_tree().root.add_child(picker)
			await _settle(1.0)
			await _shot("language_select", picker)
			picker.queue_free()
			await _settle(0.2)
		var menu: Control = (load("res://src/ui/main_menu.tscn") as PackedScene).instantiate()
		get_tree().root.add_child(menu)
		await _settle(1.5)
		var items: Node = menu.get("_menu")
		if highlight >= 0 and items != null and highlight < items.get_child_count():
			items.get_child(highlight).call("_set_hl", 1.0) # MenuItem's hover/press accent, fully in
			await _settle(0.1)
		await _shot("%s_main_menu" % lang, menu)
		var host: Node = menu.get("_panel_host")
		menu.call("_show_settings")
		await _settle(0.6)
		await _shot("%s_settings" % lang, host)
		menu.call("_show_chapters")
		await _settle(0.6)
		await _shot("%s_chapters" % lang, host)
		# the purchase screen (debug build: the mock store's price); also the App Review screenshot of full_game
		menu.call("_show_purchase")
		await _settle(0.6)
		await _shot("%s_purchase" % lang, host)
		menu.call("_confirm", "ui.new_game_confirm", func() -> void: pass)
		await _settle(0.4)
		await _shot("%s_confirm" % lang, host)
		menu.queue_free()
		await _settle(0.3)
		if menus_only:
			continue
		# --- in-game HUD and overlays
		GameState.start_new("ch1")
		var l := GameState.logic as Lab7Logic
		for i in 30:
			Lab7Solver.step(l, "leave_lens")
		var room: Node3D = (load("res://src/rooms/lab7/lab7.tscn") as PackedScene).instantiate()
		room.set("capture_mode", true)
		get_tree().root.add_child(room)
		await _settle(2.0)
		var hud: Node = room.get("hud")
		# intro card: text over black, then skip its lines with taps like a player
		hud.call("play_intro")
		await _settle(1.6)
		var intro: Control = (hud.get("_root") as Control).get_child(-1)
		await _shot("%s_intro" % lang, intro)
		for i in 80:
			if not bool(hud.get("_busy")):
				break
			if is_instance_valid(intro):
				var ev := InputEventMouseButton.new()
				ev.button_index = MOUSE_BUTTON_LEFT
				ev.pressed = true
				intro.gui_input.emit(ev)
			await _settle(0.25)
		await _settle(2.0) # the intro's own captions start 1.2 s after it ends
		hud.call("caption", "", 0.01)
		hud.call("set_caption", "")
		l.select_item("")
		hud.call("_refresh_inventory")
		await _settle(1.0)
		await _shot("%s_hud_bare" % lang, hud) # the 3D frame behind captions (contrast is measured on it)
		for v in views:
			await _closeup_shots(room, hud, l, lang, v)
		# "item found": the same call the rooms make when an item is picked up (room_base _feedback)
		var found_id := "notebook" if l.has_item("notebook") else str(l.inventory[0])
		hud.call("message", tr("ui.item_added") % tr(ItemDB.name_key(found_id)), 30.0)
		await _settle(0.8)
		await _shot("%s_hud_item_found" % lang, hud)
		hud.call("message", "", 0.01)
		await _settle(0.6)
		l.select_item("uv_lamp" if l.has_item("uv_lamp") else str(l.inventory[0]))
		hud.call("_refresh_inventory")
		hud.call("set_meter", 3) # Chapter 2 receiver meter (top right)
		hud.call("message", tr("msg.c2_vault_unlocked") if lang != "uz" else tr("msg.c2_locker_open"), 30.0)
		hud.call("caption", tr("cap2.vault_reel"), 30.0)
		hud.call("set_caption", "obj.drawing") # a long view title
		await _settle(0.8)
		await _shot("%s_hud_captions" % lang, hud)
		hud.call("set_caption", "")
		hud.call("set_meter", -1)
		hud.call("message", "", 0.01)
		hud.call("caption", "", 0.01)
		await _settle(0.8)
		await _overlay_shot(hud, "show_hint", [], "%s_hint" % lang)
		await _hint_ladder_shots(hud, lang)
		await _overlay_shot(hud, "show_pause", [], "%s_pause" % lang)
		# the settings panel as the pause menu opens it (over the 3D room, not the main menu)
		var settings_btn := _find_button(hud.get("_overlay"), "ui.settings")
		if settings_btn != null:
			settings_btn.emit_signal("pressed")
			await _settle(0.8)
			await _shot("%s_pause_settings" % lang, hud.get("_overlay"))
		await _overlay_shot(hud, "show_inspect", ["crystal_lens"], "%s_inspect" % lang, 1.0)
		await _overlay_shot(hud, "_show_notebook", [7], "%s_notebook" % lang) # the longest page
		l.state["uv_page"] = true # the page Leyla wrote in UV ink, as the lamp shows it
		await _overlay_shot(hud, "_show_notebook", [4], "%s_notebook_uv" % lang, 1.6)
		await _overlay_shot(hud, "show_document", ["letter"], "%s_letter" % lang)
		await _overlay_shot(hud, "show_document", ["personnel_file"], "%s_document" % lang)
		await _overlay_shot(hud, "show_document", ["photo"], "%s_photo" % lang)
		await _overlay_shot(hud, "show_document", ["evidence"], "%s_evidence" % lang)
		await _overlay_shot(hud, "show_document", ["badge"], "%s_picture" % lang)
		await _overlay_shot(hud, "show_choice", [], "%s_choice" % lang, 0.8)
		await _overlay_shot(hud, "show_chapter_complete", [], "%s_chapter_complete" % lang, 1.4)
		hud.call("_close_overlay")
		room.queue_free()
		await _settle(0.5)
		_save_report()
	SaveSystem.delete_game()
	_save_report()
	var n_issues := 0
	for k: String in report:
		if not k.begins_with("_"):
			n_issues += (report[k]["issues"] as Array).size()
	print("ui_screens: %d layout issues (clipped / off-screen / under the cutout), details in measure.json" % n_issues)
	# tools/qa_run.sh: the run finished even if the process then hangs on exit. exit 1 = some layout issue.
	print("QA_DONE exit=%d" % (1 if n_issues > 0 else 0))
	get_tree().quit(1 if n_issues > 0 else 0)


func _save_report() -> void:
	var f := FileAccess.open(out_dir + "/measure.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(report, "\t"))
	f.close()


func _find_button(root: Node, text_key: String) -> Button:
	if root == null or not is_instance_valid(root):
		return null
	if root is Button and ((root as Button).text == text_key or (root as Button).text == tr(text_key)):
		return root
	for c in root.get_children():
		var b := _find_button(c, text_key)
		if b:
			return b
	return null


func _overlay_shot(hud: Node, method: String, args: Array, name: String, wait: float = 0.5) -> void:
	hud.call("_close_overlay")
	hud.callv(method, args)
	await _settle(wait)
	var o: Variant = hud.get("_overlay")
	await _shot(name, o if o != null else hud)


# ====================================================================== screen emulation
func _apply_screen() -> void:
	var win := get_window()
	if screen_size != Vector2i.ZERO:
		var want := window_size if window_size != Vector2i.ZERO else screen_size
		win.size = want
		await _settle(0.3)
		var got := win.size
		if got != want:
			# the X server could not fit it: keep the aspect ratio so the canvas layout stays identical
			var k := minf(float(got.x) / screen_size.x, float(got.y) / screen_size.y)
			win.size = Vector2i(int(screen_size.x * k), int(screen_size.y * k))
			await _settle(0.3)
			print("ui_screens: window %s instead of %s (same aspect, same canvas layout)" % [win.size, screen_size])
	else:
		screen_size = win.size
	if dpi <= 0.0:
		dpi = float(DisplayServer.screen_get_dpi())
	var safe := Rect2i(int(insets[0]), int(insets[1]), screen_size.x - int(insets[0]) - int(insets[2]), screen_size.y - int(insets[1]) - int(insets[3]))
	Settings.set("emulate", {"size": screen_size, "dpi": dpi, "safe": safe}) # read by UITheme (no-op on older builds)
	var vis := get_viewport().get_visible_rect().size
	report["_device"] = {"screen": [screen_size.x, screen_size.y], "dpi": dpi, "insets": insets, "text_scale": text_scale,
		"canvas": [vis.x, vis.y], "window": [win.size.x, win.size.y], "mm_per_canvas_px": _mm_per_px()}
	print("ui_screens: screen %s @ %.0f dpi, canvas %s, %.4f mm per canvas px, text scale %.2f" % [screen_size, dpi, vis, _mm_per_px(), text_scale])
	# mark the emulated cutout / home-indicator zones on the screenshots
	_cutout_layer = CanvasLayer.new()
	_cutout_layer.layer = 127
	_cutout_layer.visible = not clean
	add_child(_cutout_layer)
	var k2 := vis.x / float(screen_size.x)
	var zones := [Rect2(0, 0, insets[0] * k2, vis.y), Rect2(0, 0, vis.x, insets[1] * k2),
		Rect2(vis.x - insets[2] * k2, 0, insets[2] * k2, vis.y), Rect2(0, vis.y - insets[3] * k2, vis.x, insets[3] * k2)]
	for z: Rect2 in zones:
		if z.size.x <= 0.0 or z.size.y <= 0.0:
			continue
		var r := ColorRect.new()
		r.color = Color(1, 0, 0.2, 0.22)
		r.position = z.position
		r.size = z.size
		r.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_cutout_layer.add_child(r)


func _mm_per_px() -> float:
	var vis := get_viewport().get_visible_rect().size
	return float(screen_size.x) / vis.x * 25.4 / dpi


func _unsafe_rects() -> Array[Rect2]:
	var vis := get_viewport().get_visible_rect().size
	var k := vis.x / float(screen_size.x)
	var out: Array[Rect2] = []
	if int(insets[0]) > 0:
		out.append(Rect2(0, 0, insets[0] * k, vis.y))
	if int(insets[1]) > 0:
		out.append(Rect2(0, 0, vis.x, insets[1] * k))
	if int(insets[2]) > 0:
		out.append(Rect2(vis.x - insets[2] * k, 0, insets[2] * k, vis.y))
	if int(insets[3]) > 0:
		out.append(Rect2(0, vis.y - insets[3] * k, vis.x, insets[3] * k))
	return out


# ====================================================================== measurement
func _measure(scope: Node) -> Dictionary:
	var texts: Array = []
	var targets: Array = []
	var issues: Array = []
	_walk(scope, texts, targets, issues)
	return {"texts": texts, "targets": targets, "issues": issues}


func _alpha(c: CanvasItem) -> float:
	var a := 1.0
	var n: Node = c
	while n != null:
		if n is CanvasItem:
			a *= (n as CanvasItem).modulate.a
			if n == c:
				a *= c.self_modulate.a
		n = n.get_parent()
	return a


func _scroll_clip(c: Control) -> Rect2:
	var n := c.get_parent()
	while n != null:
		if n is ScrollContainer:
			return (n as Control).get_global_rect()
		n = n.get_parent()
	return Rect2()


func _walk(n: Node, texts: Array, targets: Array, issues: Array) -> void:
	if n is CanvasItem and not (n as CanvasItem).visible:
		return
	if n is Control:
		var c := n as Control
		if c.is_visible_in_tree() and _alpha(c) > 0.05:
			_inspect_control(c, texts, targets, issues)
	for ch in n.get_children():
		_walk(ch, texts, targets, issues)


func _inspect_control(c: Control, texts: Array, targets: Array, issues: Array) -> void:
	var vis := get_viewport().get_visible_rect()
	var r := c.get_global_rect()
	var clip := _scroll_clip(c)
	var mm := _mm_per_px()
	var shown := r if clip.size == Vector2.ZERO else r.intersection(clip)
	if clip.size != Vector2.ZERO and shown.size.y < 2.0:
		return # scrolled out of view inside a ScrollContainer (reachable by scrolling)
	var label_text := ""
	var fs := 0
	if c is Label and (c as Label).text.strip_edges() != "":
		var l := c as Label
		label_text = tr(l.text) if l.auto_translate_mode != Node.AUTO_TRANSLATE_MODE_DISABLED else l.text
		fs = l.get_theme_font_size("font_size")
		if l.get_visible_line_count() < l.get_line_count() and l.max_lines_visible < 0:
			issues.append("clipped label (%d/%d lines): %s" % [l.get_visible_line_count(), l.get_line_count(), label_text.left(40)])
		if l.autowrap_mode == TextServer.AUTOWRAP_OFF:
			var w := l.get_theme_font("font").get_string_size(label_text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
			if w > r.size.x + 2.0:
				issues.append("label wider than its box (%.0f > %.0f): %s" % [w, r.size.x, label_text.left(40)])
	elif c is Button:
		var b := c as Button
		if b.text != "":
			label_text = tr(b.text) if b.auto_translate_mode != Node.AUTO_TRANSLATE_MODE_DISABLED else b.text
			fs = b.get_theme_font_size("font_size")
			var sb := b.get_theme_stylebox("normal")
			var room := r.size.x - (sb.get_margin(SIDE_LEFT) + sb.get_margin(SIDE_RIGHT) if sb else 0.0)
			var w := b.get_theme_font("font").get_string_size(label_text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
			if b.autowrap_mode == TextServer.AUTOWRAP_OFF and w > room + 2.0:
				issues.append("button text wider than the button (%.0f > %.0f): %s" % [w, room, label_text.left(40)])
	if label_text != "":
		var col: Color = c.get_theme_color("font_color")
		texts.append({"text": label_text.left(48).replace("\n", " "), "px": fs, "mm": snappedf(fs * mm, 0.01),
			"color": col.to_html(false), "rect": [int(r.position.x), int(r.position.y), int(r.size.x), int(r.size.y)],
			"kind": c.get_class() if not (c is IconButton) else "IconButton"})
	var interactive := (c is BaseButton or c is Range) and c.mouse_filter != Control.MOUSE_FILTER_IGNORE
	if interactive and not (c is ScrollBar):
		var side := minf(r.size.x, r.size.y)
		var what := label_text if label_text != "" else (str(c.get("icon_id")) if c is IconButton else c.get_class())
		targets.append({"what": what.left(32), "w_mm": snappedf(r.size.x * mm, 0.1), "h_mm": snappedf(r.size.y * mm, 0.1),
			"min_mm": snappedf(side * mm, 0.1), "rect": [int(r.position.x), int(r.position.y), int(r.size.x), int(r.size.y)]})
	# off-screen / under the cutout (only for things the player reads or taps)
	if label_text != "" or interactive:
		var what2 := label_text.left(32) if label_text != "" else c.get_class()
		if not vis.grow(2.0).encloses(shown):
			issues.append("off-screen: %s %s" % [what2, shown])
		for z in _unsafe_rects():
			if z.intersects(shown) and z.intersection(shown).get_area() > 4.0:
				issues.append("under the cutout/home indicator: %s" % what2)
				break


func _settle(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()


func _shot(name: String, scope: Node = null) -> void:
	if not shots_filter.is_empty():
		var wanted := false
		for f in shots_filter:
			if name.contains(f):
				wanted = true
		if not wanted:
			print("skip " + name) # the log keeps growing for tools/qa_run.sh's stall watchdog
			return
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("%s/%s.png" % [out_dir, name])
	if scope != null:
		report[name] = _measure(scope)
		var issues: Array = report[name]["issues"]
		if (name.contains("hud") or name.contains("view")) and scope.get("_root") is Control:
			issues.append_array(_hud_overlaps(scope))
		print("shot %s (%d texts, %d targets, %d issues)" % [name, (report[name]["texts"] as Array).size(), (report[name]["targets"] as Array).size(), issues.size()])
	else:
		print("shot " + name) # tools/qa_run.sh restarts a run whose log stops growing


# ====================================================================== close-ups, hints, HUD overlaps
## A close-up of the room as the player sees it with an item in hand (the owner could not reach Panel 7's main
## lever under the old inventory bar), then with the bag open. With --probe, says whether the part lies under a
## HUD control that stops taps.
func _closeup_shots(room: Node3D, hud: Node, l: RoomLogic, lang: String, view: String) -> void:
	var cam := room.get("cam") as RoomCamera
	if cam == null or not cam.views.has(view):
		print("ui_screens: no view %s" % view)
		return
	var home := cam.current()
	cam.go(view, true)
	await _settle(1.2)
	if not l.inventory.is_empty():
		l.select_item(str(l.inventory[0]))
		hud.call("_refresh_inventory")
	await _settle(0.8)
	await _blocked_tint(hud)
	await _shot("%s_view_%s" % [lang, view], hud)
	_probe_report(room, hud, "%s_view_%s" % [lang, view])
	if hud.has_method("set_bag_open"):
		hud.call("set_bag_open", true)
		await _settle(0.8)
		await _blocked_tint(hud)
		await _shot("%s_view_%s_bag" % [lang, view], hud)
		_probe_report(room, hud, "%s_view_%s_bag" % [lang, view])
		hud.call("set_bag_open", false)
	_clear_tint()
	l.select_item("")
	hud.call("_refresh_inventory")
	cam.go(home, true)
	await _settle(0.8)


## The rects of every HUD control that stops a tap (the HUD's blocked_rects() when it has one).
func _hud_blocked(hud: Node) -> Array[Rect2]:
	if hud.has_method("blocked_rects"):
		return hud.call("blocked_rects")
	var out: Array[Rect2] = []
	for n in (hud.get("_root") as Node).find_children("*", "Control", true, false):
		var c := n as Control
		if c.is_visible_in_tree() and c.mouse_filter == Control.MOUSE_FILTER_STOP and _alpha(c) > 0.05:
			out.append(c.get_global_rect())
	return out


func _probe_report(room: Node3D, hud: Node, shot_name: String) -> void:
	if probe == "" or not probe.contains("/"):
		return
	var models: Dictionary = room.get("models")
	var n := ModelUtil.find(models.get(probe.get_slice("/", 0)), probe.get_slice("/", 1))
	var cam := room.get("cam") as RoomCamera
	if n == null or cam == null:
		print("ui_screens: probe %s not found" % probe)
		return
	var mi := n as MeshInstance3D
	var c := (mi.global_transform * mi.get_aabb()).get_center() if mi else n.global_position
	var p := cam.unproject_position(c)
	var hit := ""
	for r in _hud_blocked(hud):
		if r.has_point(p):
			hit = str(r)
	var res := {"part": probe, "screen": [snappedf(p.x, 1), snappedf(p.y, 1)], "covered_by": hit}
	var probes: Dictionary = report.get("_probe", {})
	probes[shot_name] = res
	report["_probe"] = probes
	print("probe %s %s at %s: %s" % [shot_name, probe, p, ("UNDER a HUD control " + hit) if hit != "" else "free to tap"])


var _tint_layer: CanvasLayer


## --show-blocked: a red tint over every HUD control that stops a tap (where the world cannot be tapped).
func _blocked_tint(hud: Node) -> void:
	_clear_tint()
	if not show_blocked:
		return
	_tint_layer = CanvasLayer.new()
	_tint_layer.layer = 120
	add_child(_tint_layer)
	for r in _hud_blocked(hud):
		var cr := ColorRect.new()
		cr.color = Color(1.0, 0.1, 0.1, 0.28)
		cr.position = r.position
		cr.size = r.size
		cr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_tint_layer.add_child(cr)
	await _settle(0.1)


func _clear_tint() -> void:
	if _tint_layer != null:
		_tint_layer.queue_free()
		_tint_layer = null


## The hint ladder: Stronger hint to level 2, Show the answer to level 3, then the same goal asked again.
func _hint_ladder_shots(hud: Node, lang: String) -> void:
	var more := _find_button(hud.get("_overlay"), "ui.hint_more")
	for lvl in [2, 3]:
		if more == null or not is_instance_valid(more) or more.disabled or not more.is_visible_in_tree():
			break
		more.emit_signal("pressed")
		await _settle(0.5)
		await _shot("%s_hint_%d" % [lang, lvl], hud.get("_overlay"))
	await _overlay_shot(hud, "show_hint", [], "%s_hint_reopen" % lang)


## HUD elements that overlap each other: the corner buttons, the bag, the banners, the meter and each visible
## inventory slot and item action (the open overlay and anything faded out are left out).
func _hud_overlaps(hud: Node) -> Array:
	var items: Array = []
	var root := hud.get("_root") as Control
	var inv := hud.get("_inv_panel") as Control
	for c in root.get_children():
		if not (c is Control) or c == hud.get("_overlay") or c == inv:
			continue
		var cc := c as Control
		if cc.is_visible_in_tree() and _alpha(cc) > 0.05 and cc.size.x > 1.0 and cc.size.y > 1.0:
			items.append([_hud_name(hud, cc), cc.get_global_rect()])
	if inv != null and inv.is_visible_in_tree() and _alpha(inv) > 0.05:
		var box := hud.get("_inv_box") as Control
		for s in box.get_children():
			var sc := s as Control
			if sc.is_visible_in_tree():
				var clip := _scroll_clip(sc)
				var r := sc.get_global_rect()
				r = r if clip.size == Vector2.ZERO else r.intersection(clip)
				if r.size.y > 2.0:
					items.append(["slot", r])
		var act := hud.get("_actions") as Control
		if act != null:
			for b in act.get_children():
				if (b as Control).is_visible_in_tree():
					items.append(["item action", (b as Control).get_global_rect()])
	var out: Array = []
	for i in items.size():
		for j in range(i + 1, items.size()):
			var a: Rect2 = items[i][1]
			var b: Rect2 = items[j][1]
			if a.intersects(b) and a.intersection(b).get_area() > 4.0:
				out.append("overlap: %s %s × %s %s" % [items[i][0], a, items[j][0], b])
	return out


func _hud_name(hud: Node, c: Control) -> String:
	for prop in ["_top_plate", "_cap_plate", "_msg_plate", "_prompt_plate", "_back_btn", "_hint_btn", "_pause_btn", "_bag_btn", "_meter"]:
		if hud.get(prop) == c:
			return prop.substr(1)
	return c.get_class()
