extends Node
## QA "tap map": renders camera views of a real chapter room and marks every tappable part in view.
## It taps a 5×5 grid over the part's own screen area through the room's raycast and colours the mark:
##   green  = at least 3 sample points reach the part;
##   orange = only 1–2 do (a small or mostly covered target);
##   red    = none do; the part most often hit instead is named.
## Run: xvfb-run -a godot --path game res://qa/tap_map.tscn -- --chapter=ch2 --views=cat_drawer,splicer --out=<dir>
##        [--steps=N] (solver steps first) [--do=open_cat_drawer:4,pick_divider:1] (logic calls; an argument that
##        is not an int is passed as a string, e.g. turn_freq:x:1) [--until=booth_open] (solver steps until that
##        state key is true) [--lens=take|leave] [--key=strand|leyla] (ch3: the Chapter 2 key path)
##        [--perf] (no tap marks: log draw calls / primitives / objects per view instead)
##        [--breakdown] (with --perf: the draw calls each model, effect node and light shadow adds to the view)
##        [--hud-breakdown] (with --perf: the HUD alone: the view's calls with the HUD shown / hidden, the HUD with the
##        3D room hidden, and the calls each HUD node adds; plus the nodes that break 2D batching)
##        [--screen=phone61|phone20|phone55|tablet10|WxH@dpi[:l,t,r,b]] (render as that phone: its aspect, dpi and
##        safe insets drive the HUD's size and the mm checks; the window takes the same aspect)
##        [--text-scale=1.15] (the player's Settings → Text size)
##        [--lang=ru|uz] (the game's language; the notebook and document shots follow it)
##        [--doc=poster] (also shoot that reader document, e.g. poster, chalkboard, evidence: <out>/doc_poster.png)
##        [--cam=name:x,y,z:tx,ty,tz:fov] (replace that view's camera, e.g. to shoot the old framing as "before")
##        [--notebook=4] (also shoot Leyla's notebook, page 4, as a player reads it: <out>/notebook_p4.png)
##        [--hud-check] (every control in the view — IA_*, Item_*, Shard_*, Echo_* — must have its tap point on
##        screen, clear of the HUD's input-blocking controls and at least EDGE_MM from the screen edge; a control
##        that only moves the camera to its own view when tapped here (RoomBase.in_reach) is not checked in this view;
##        a control under a banner that only covers it is a warning. The message and prompt banners are shown while it
##        measures, as they are while a player works a mechanism with an item in hand. Exit 1 on any failure)
## Writes <view>.png and tap_map.txt (one line per orange or red part, and one per HUD failure or warning).

const SCENES := {"ch1": "res://src/rooms/lab7/lab7.tscn", "ch2": "res://src/rooms/archive/archive.tscn",
	"ch3": "res://src/rooms/underground/underground.tscn"}

## Emulated screens (device px, dpi, safe insets l/t/r/b in device px): the phones the HUD check runs at.
const SCREENS := {
	"phone61": {"size": Vector2i(2340, 1080), "dpi": 400.0, "insets": [120, 0, 0, 0]}, # 19.5:9, camera cutout left
	"phone20": {"size": Vector2i(2400, 1080), "dpi": 400.0, "insets": [120, 0, 0, 0]}, # 20:9
	"phone55": {"size": Vector2i(1920, 1080), "dpi": 480.0, "insets": [0, 0, 0, 0]}, # 16:9
	"tablet10": {"size": Vector2i(2048, 1536), "dpi": 264.0, "insets": [0, 0, 0, 0]}, # 4:3
}
const SLIVER_SHOWN := 0.4 # less of a control than this on screen: it only peeks in at the edge (not a target in this view)
const EDGE_MM := 6.0 # a control's tap point keeps this far from the screen edge (thumbs and case bezels)
const ASSUMED_COLUMN := 0.13 # until HUD.blocked_rects() lands: the inventory column is ~13 % of the width

var out_dir := "/tmp/tap_map"
var room: Node3D
var lines: Array[String] = []
var hud_check := false
var notebook_page := 0
var doc_name := ""
var cam_overrides: Array[String] = []
var hud_controls := 0
var hud_failures := 0
var hud_warnings := 0
var hud_slivers := 0
var hud_focus_only := 0 # controls seen at a view's edge whose tap only moves the camera to their own view
var _screen_name := ""


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	var chapter := "ch2"
	var views: PackedStringArray = []
	var steps := 0
	var calls: PackedStringArray = []
	var lens := "leave"
	var key := "strand"
	var until := ""
	GameState.variant_seed = 0 # canonical answers unless --seed=N (players get a random seed per game)
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--chapter="):
			chapter = a.substr(10)
		elif a.begins_with("--views="):
			views = a.substr(8).split(",", false)
		elif a.begins_with("--steps="):
			steps = int(a.substr(8))
		elif a.begins_with("--do="):
			calls = a.substr(5).split(",", false)
		elif a.begins_with("--lens="):
			lens = a.substr(7)
		elif a.begins_with("--key="):
			key = a.substr(6)
		elif a.begins_with("--until="):
			until = a.substr(8)
		elif a.begins_with("--seed="):
			GameState.variant_seed = int(a.substr(7))
		elif a.begins_with("--brightness="):
			Settings.values["brightness"] = clampf(float(a.substr(13)), 0.7, 1.6) # the Settings slider's range, unsaved
		elif a.begins_with("--screen="):
			_screen_name = a.substr(9)
		elif a.begins_with("--text-scale="):
			Settings.values["text_scale"] = clampf(float(a.substr(13)), 0.9, 1.3)
		elif a == "--hud-check":
			hud_check = true
		elif a.begins_with("--lang="):
			TranslationServer.set_locale(a.substr(7))
		elif a.begins_with("--doc="):
			doc_name = a.substr(6)
		elif a.begins_with("--cam="):
			cam_overrides.append(a.substr(6))
		elif a.begins_with("--notebook="):
			notebook_page = int(a.substr(11))
	DirAccess.make_dir_recursive_absolute(out_dir)
	if _screen_name != "":
		await _apply_screen(_screen_name)
	SaveSystem.save_path = "user://qa_tapmap_save.json"
	SaveSystem.profile_path = "user://qa_tapmap_profile.json"
	GameState.profile = {"choices": {"ch1_lens": "take_lens" if lens == "take" else "leave_lens", "ch1_shards": 5,
		"ch2_key": key + "_key", "ch2_echoes": 3}}
	GameState.start_new(chapter)
	var logic := GameState.logic
	for _i in steps:
		_solve_step(chapter, logic)
	var guard := 0
	while until != "" and not bool(logic.state.get(until, false)) and guard < 600:
		guard += 1
		_solve_step(chapter, logic)
	for c in calls:
		var parts := c.split(":")
		var args: Array = []
		for k in range(1, parts.size()):
			args.append(int(parts[k]) if parts[k].is_valid_int() else parts[k])
		logic.callv(parts[0], args)
	logic.select_item("") # the solver may leave a tool (the UV lamp, the receiver) in hand: clean shots, no torch disc
	var scene: String = SCENES.get(chapter, SCENES["ch1"])
	room = (load(scene) as PackedScene).instantiate()
	room.set("capture_mode", true)
	get_tree().root.add_child(room)
	await _settle(1.5)
	var cam: RoomCamera = room.get("cam")
	var perf_only := OS.get_cmdline_user_args().has("--perf")
	for o in cam_overrides: # name:x,y,z:tx,ty,tz:fov
		var f := o.split(":")
		var p := f[1].split(",")
		var t := f[2].split(",")
		cam.add_view(f[0], Vector3(float(p[0]), float(p[1]), float(p[2])), Vector3(float(t[0]), float(t[1]), float(t[2])), float(f[3]))
	for v in views:
		if room.has_method("prepare_view"):
			room.call("prepare_view", v)
		cam.go(v, true)
		await _settle(0.9)
		if perf_only:
			# the room's reflection probe captures over several frames, and the software renderer runs at a few
			# frames per second: wait for it, or the shot shows the room darker than any phone would
			await _settle(2.5)
			await RenderingServer.frame_post_draw
			lines.append("perf[%s]: draw calls %d, primitives %d, objects %d" % [v,
				RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
				RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),
				RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME)])
			get_viewport().get_texture().get_image().save_png("%s/%s.png" % [out_dir, v]) # a clean shot, no marks
			if OS.get_cmdline_user_args().has("--breakdown"):
				await _breakdown(v)
			if OS.get_cmdline_user_args().has("--hud-breakdown"):
				await _hud_breakdown(v)
			continue
		print("tap_map: view %s" % v) # progress: tools/qa_run.sh kills a run whose log stops growing
		await _map(v)
	if notebook_page > 0 and room.get("hud") != null:
		GameState.logic.callv("take", ["notebook"]) if GameState.logic.can_take("notebook") else null
		(room.get("hud") as CanvasLayer).call("_show_notebook", notebook_page - 1)
		await _settle(0.8)
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("%s/notebook_p%d.png" % [out_dir, notebook_page])
	if doc_name != "" and room.get("hud") != null:
		(room.get("hud") as CanvasLayer).call("show_document", doc_name)
		await _settle(0.8)
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("%s/doc_%s.png" % [out_dir, doc_name])
	var qa_exit := 0
	if hud_check:
		lines.append("hud-check%s: %d controls in %d views, %d failures, %d banner warnings (%d focus-only controls and %d slivers not checked)" % [
			" (%s)" % _screen_name if _screen_name != "" else "", hud_controls, views.size(), hud_failures, hud_warnings,
			hud_focus_only, hud_slivers])
		qa_exit = 1 if hud_failures > 0 else 0
	var f := FileAccess.open(out_dir + "/tap_map.txt", FileAccess.WRITE)
	f.store_string("\n".join(lines) + "\n")
	print("\n".join(lines))
	SaveSystem.delete_game()
	print("QA_DONE exit=%d" % qa_exit) # tools/qa_run.sh: the run finished even if the process then hangs on exit
	get_tree().quit(qa_exit)


## Renders as the named phone: the window takes its aspect (scaled to what the X server can fit, which keeps the
## canvas layout identical), and Settings.emulate gives UITheme its dpi and safe area, so the HUD is laid out and
## sized as on that phone and mm checks use its pixel pitch.
func _apply_screen(spec: String) -> void:
	var size := Vector2i.ZERO
	var dpi := 400.0
	var insets: Array = [0, 0, 0, 0]
	if SCREENS.has(spec):
		var d: Dictionary = SCREENS[spec]
		size = d["size"]
		dpi = float(d["dpi"])
		insets = d["insets"]
	else:
		var m := spec.split(":")
		var wh := m[0].split("@")
		var p := wh[0].split("x")
		size = Vector2i(int(p[0]), int(p[1]))
		if wh.size() > 1:
			dpi = float(wh[1])
		if m.size() > 1:
			var ins := m[1].split(",")
			for k in mini(4, ins.size()):
				insets[k] = int(ins[k])
	var win := get_window()
	win.size = size
	await _settle(0.3)
	if win.size != size:
		var k := minf(float(win.size.x) / size.x, float(win.size.y) / size.y)
		win.size = Vector2i(int(size.x * k), int(size.y * k))
		await _settle(0.3)
	var safe := Rect2i(int(insets[0]), int(insets[1]), size.x - int(insets[0]) - int(insets[2]),
		size.y - int(insets[1]) - int(insets[3]))
	Settings.set("emulate", {"size": size, "dpi": dpi, "safe": safe})
	lines.append("screen %s: %dx%d @ %.0f dpi, insets %s, window %s, canvas %s, %.4f mm per canvas px, text scale %.2f" % [
		spec, size.x, size.y, dpi, str(insets), str(win.size), str(get_viewport().get_visible_rect().size),
		UITheme.mm_per_px(), UITheme.scale()])


## One solver step of the chapter's scripted solver (the same ones the no-softlock tests use).
static func _solve_step(chapter: String, logic: RoomLogic) -> void:
	match chapter:
		"ch3":
			UndergroundSolver.step(logic as UndergroundLogic, "leyla")
		"ch2":
			ArchiveSolver.step(logic as ArchiveLogic, "leyla_key")
		_:
			Lab7Solver.step(logic as Lab7Logic, "leave_lens")


## The draw calls each part of the room adds to this view: hide it (or switch its light's shadow off), measure,
## restore. Hiding removes both its colour pass and its shadow pass draws.
func _breakdown(view_id: String) -> void:
	# the HUD animates (captions fade, badges blink): hide it while measuring, or every delta carries its noise
	var hud := room.get("hud") as CanvasLayer
	if hud:
		hud.visible = false
	var base := await _draw_calls()
	lines.append("  %s scene only (HUD hidden): %d draw calls" % [view_id, base])
	var rows: Array = []
	var nodes: Array[Node3D] = []
	for n in room.get_children():
		if n is Node3D and not (n is Light3D or n is Camera3D or n is ReflectionProbe):
			nodes.append(n)
	for n in nodes:
		if not n.visible:
			continue
		n.visible = false
		var c := await _draw_calls()
		n.visible = true
		if base - c != 0:
			rows.append([base - c, str(n.name)])
		print("  breakdown %s: %s %d" % [view_id, n.name, base - c]) # progress for tools/qa_run.sh's stall watchdog
		if base - c >= 12: # a big one: which of its meshes
			for mi in n.find_children("*", "MeshInstance3D", true, false):
				var m := mi as MeshInstance3D
				if not m.is_visible_in_tree():
					continue
				m.visible = false
				var cm := await _draw_calls()
				m.visible = true
				print("    %s/%s %d" % [n.name, m.name, base - cm])
				if base - cm >= 2:
					rows.append([base - cm, "%s/%s (%d surfaces, shadow %s)" % [n.name, m.name,
						m.get_surface_override_material_count(),
						"off" if m.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF else "on"]])
	for l in room.find_children("*", "Light3D", true, false):
		var light := l as Light3D
		if not light.shadow_enabled or not light.is_visible_in_tree():
			continue
		light.shadow_enabled = false
		var c := await _draw_calls()
		light.shadow_enabled = true
		rows.append([base - c, "shadow of " + str(light.name)])
	if hud:
		hud.visible = true
	rows.sort_custom(func(a: Array, b: Array) -> bool: return int(a[0]) > int(b[0]))
	for r: Array in rows:
		lines.append("  %s %4d  %s" % [view_id, int(r[0]), str(r[1])])


## The HUD's own draw calls in this view. Measured three ways: the view with the HUD hidden, the HUD with the 3D room
## hidden (so only the 2D canvas draws), and the HUD with each of its nodes hidden in turn (a node is hidden, never
## faded, so its whole subtree drops out). Batching makes the deltas approximate: removing a node can merge the
## batches around it. Ends with the visible nodes that break batching (own material, clipping, outlines, shadows).
func _hud_breakdown(view_id: String) -> void:
	var hud := room.get("hud") as CanvasLayer
	if hud == null:
		return
	var root := hud.get("_root") as Control
	var total := await _draw_calls()
	hud.visible = false
	var scene := await _draw_calls()
	hud.visible = true
	room.visible = false
	var alone := await _draw_calls()
	hud.visible = false
	var empty := await _draw_calls()
	hud.visible = true
	lines.append("hud[%s]: view %d, HUD hidden %d, HUD alone (room hidden) %d, nothing shown %d -> HUD adds %d" % [
		view_id, total, scene, alone, empty, total - scene])
	var rows: Array = []
	for n in root.get_children():
		var ci := n as CanvasItem
		if ci == null or not ci.visible:
			continue
		ci.visible = false
		var c := await _draw_calls()
		ci.visible = true
		var delta := alone - c
		rows.append([delta, "%s (%s)" % [n.name, n.get_class()]])
		print("  hud-breakdown %s: %s %d" % [view_id, n.name, delta]) # progress for tools/qa_run.sh's stall watchdog
		if delta >= 3:
			for ch in n.get_children():
				var cc := ch as CanvasItem
				if cc == null or not cc.visible:
					continue
				cc.visible = false
				var c2 := await _draw_calls()
				cc.visible = true
				if alone - c2 != 0:
					rows.append([alone - c2, "  %s/%s (%s)" % [n.name, ch.name, ch.get_class()]])
	for r: Array in rows:
		lines.append("  %s %4d  %s" % [view_id, int(r[0]), str(r[1])])
	# what a visible label's outline and clipping cost (each switched off in turn, then restored)
	for l in root.find_children("*", "Label", true, false):
		var lab := l as Label
		if not lab.is_visible_in_tree() or lab.text == "":
			continue
		var base_c := await _draw_calls()
		var o := lab.get_theme_constant("outline_size")
		var clip := lab.clip_text
		var what := "'%s' (%s, %d px, outline %d, clip %s)" % [lab.atr(lab.text).left(24), lab.get_parent().name, lab.get_theme_font_size("font_size"), o, clip]
		if o > 0:
			lab.add_theme_constant_override("outline_size", 0)
			lines.append("  %s label %s without outline: %d -> %d" % [view_id, what, base_c, await _draw_calls()])
			lab.add_theme_constant_override("outline_size", o)
		if clip:
			lab.clip_text = false
			lines.append("  %s label %s without clip_text: %d -> %d" % [view_id, what, base_c, await _draw_calls()])
			lab.clip_text = true
		lab.visible = false
		lines.append("  %s label %s hidden: %d -> %d" % [view_id, what, base_c, await _draw_calls()])
		lab.visible = true
	var breakers: Array[String] = []
	_batch_breakers(root, "", breakers)
	for b in breakers:
		lines.append("  %s breaker: %s" % [view_id, b])
	room.visible = true


## Appends one line per visible HUD node that breaks 2D batching: an own material, clipping, a font outline or shadow,
## a StyleBoxFlat with a shadow or anti-aliasing, a custom _draw (reports how many it has) or a different texture.
func _batch_breakers(n: Node, path: String, out: Array[String]) -> void:
	var ci := n as CanvasItem
	if ci != null and not ci.visible:
		return
	var here := path + "/" + str(n.name)
	if ci != null:
		var why: Array[String] = []
		if ci.material != null:
			why.append("material " + ci.material.get_class())
		if n is Control:
			var c := n as Control
			if c.clip_contents:
				why.append("clip_contents")
			if n is Label:
				var l := n as Label
				var o := l.get_theme_constant("outline_size")
				if o > 0:
					why.append("font outline %d" % o)
				if l.get_theme_color("font_shadow_color").a > 0.0:
					why.append("font shadow")
				why.append("font " + str(l.get_theme_font("font").resource_name if l.get_theme_font("font") else "?"))
			for sname in ["panel", "normal", "pressed", "hover"]:
				var sb := c.get_theme_stylebox(sname)
				if sb is StyleBoxFlat and c.has_theme_stylebox_override(sname):
					var f := sb as StyleBoxFlat
					if f.shadow_size > 0:
						why.append("StyleBoxFlat %s shadow" % sname)
					if f.anti_aliasing and (f.corner_radius_top_left > 0 or f.border_width_left > 0):
						why.append("StyleBoxFlat %s AA" % sname)
		if n is ScrollContainer:
			why.append("ScrollContainer clip")
		if n.get_script() != null and n.has_method("_draw"):
			why.append("custom _draw")
		if not why.is_empty():
			out.append("%s: %s" % [here, ", ".join(why)])
	for ch in n.get_children():
		_batch_breakers(ch, here, out)


func _draw_calls() -> int:
	for _i in 3:
		await RenderingServer.frame_post_draw
	return RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)


func _settle(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()


func _map(view_id: String) -> void:
	var cam: Camera3D = room.get("cam")
	var rect := get_viewport().get_visible_rect()
	var marks: Array[Dictionary] = []
	for body in room.find_children("*", "StaticBody3D", true, false):
		var b := body as StaticBody3D
		if b.collision_layer == 0 or not b.is_visible_in_tree():
			continue
		var part := str(b.get_meta("part", ""))
		if part == "":
			continue
		var mi := b.get_parent() as MeshInstance3D
		var r := _screen_rect(cam, mi) if mi != null and mi.mesh != null else Rect2()
		if r.size == Vector2.ZERO or not rect.intersects(r):
			continue
		# sample the part's own screen area like a player tapping what they see
		var hits := 0
		var total := 0
		var centroid := Vector2.ZERO
		var others: Dictionary = {}
		var inner := r.grow_individual(-r.size.x * 0.1, -r.size.y * 0.1, -r.size.x * 0.1, -r.size.y * 0.1)
		for gy in 5:
			for gx in 5:
				var sp := inner.position + inner.size * Vector2((gx + 0.5) / 5.0, (gy + 0.5) / 5.0)
				if not rect.has_point(sp):
					continue
				total += 1
				var hit: Dictionary = room.call("raycast", sp)
				var got := "" if hit.is_empty() else str(room.call("resolve", hit)["part"])
				if got == part:
					hits += 1
					centroid += sp
				else:
					others[got] = int(others.get(got, 0)) + 1
		if total == 0:
			continue
		# a far part hidden behind walls or furniture is simply not in view: skip it, so the report lists only
		# parts a player could aim at (a near part blocked by scenery is still reported)
		if hits == 0 and others.keys() == [""] and cam.global_position.distance_to(mi.global_position) > 1.2:
			continue
		var pos := centroid / hits if hits > 0 else r.get_center()
		var top := ""
		var best := 0
		for k: String in others:
			if int(others[k]) > best:
				best = int(others[k])
				top = k
		# parts that carry a 3D label (card tabs, divider tabs): the label is where a player taps
		for lbl in mi.find_children("*", "Label3D", false, false):
			var lp := (lbl as Node3D).global_position
			if cam.is_position_behind(lp) or not rect.has_point(cam.unproject_position(lp)):
				continue
			var lh: Dictionary = room.call("raycast", cam.unproject_position(lp))
			var lgot := "" if lh.is_empty() else str(room.call("resolve", lh)["part"])
			if lgot != part:
				lines.append("%s: tapping the label «%s» of %s hits %s" % [view_id, (lbl as Label3D).text, part,
					lgot if lgot != "" else "(nothing)"])
			elif hits < 3:
				hits = 3 # its label is a sure target, even if most of its body is covered
		var hs := str(room.call("resolve", {"collider": b, "position": b.global_position}).get("hotspot", ""))
		marks.append({"pos": pos, "part": part, "hits": hits, "got": top, "rect": r, "hotspot": hs})
		if hits < 3:
			lines.append("%s: %s reachable at %d/%d sample points (mostly hits %s)" % [view_id, part, hits, total,
				top if top != "" else "(nothing)"])
	var zones: Array[Dictionary] = []
	if hud_check:
		zones = await _hud_check(view_id, marks)
	var layer := CanvasLayer.new()
	layer.layer = 100
	var canvas := _Marks.new()
	canvas.marks = marks
	canvas.zones = zones
	canvas.edge_px = EDGE_MM / UITheme.mm_per_px() if hud_check else 0.0
	canvas.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(canvas)
	add_child(layer)
	await _settle(0.3)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("%s/%s.png" % [out_dir, view_id])
	layer.queue_free()
	if hud_check:
		_hud_restore()


## Is this part a control a player must be able to tap (not scenery that merely answers a tap)?
static func _is_control(part: String) -> bool:
	return part.begins_with("IA_") or part.begins_with("Item_") or part.begins_with("Shard_") \
		or part.begins_with("Echo_") or part == "main_handle"


## The HUD check for one view. Shows the message and prompt banners (an item in hand, a line of feedback: the
## state a player is in while working a mechanism), then tests every control's tap point against the screen edge,
## the HUD's input-blocking controls and the banners. Returns the zones to draw on the shot.
func _hud_check(view_id: String, marks: Array[Dictionary]) -> Array[Dictionary]:
	var vp := get_viewport().get_visible_rect()
	var hud := room.get("hud") as CanvasLayer
	var logic: RoomLogic = GameState.logic
	# the worst case a player sees here: an item selected (prompt banner, inspect / combine flyout) and a message
	if hud != null:
		for id: String in logic.inventory:
			if id != "uv_lamp":
				logic.select_item(id)
				break
		hud.call("message", tr("msg.nothing"), 30.0)
		await _settle(0.5)
	var blocked := _blocked_rects(hud)
	var covers := _banner_rects(hud)
	var edge_px := EDGE_MM / UITheme.mm_per_px()
	var named: PackedStringArray = []
	for b in blocked:
		named.append("%s %s" % [b["name"], _fmt_rect(b["rect"])])
	for c in covers:
		named.append("%s %s" % [c["name"], _fmt_rect(c["rect"])])
	lines.append("HUD zones[%s]: %s" % [view_id, "; ".join(named)])
	var zones: Array[Dictionary] = []
	for b in blocked:
		zones.append({"rect": b["rect"], "kind": "blocked", "name": b["name"]})
	for c in covers:
		zones.append({"rect": c["rect"], "kind": "cover", "name": c["name"]})
	for m in marks:
		var part: String = m["part"]
		if not _is_control(part) or int(m["hits"]) == 0:
			continue # scenery, or a part already reported as covered by the scene itself
		var p: Vector2 = m["pos"]
		if not _operable_here(str(m.get("hotspot", ""))):
			hud_focus_only += 1 # seen from afar: a tap moves the camera to the object's own view, where it is checked
			m["focus_only"] = true
			continue
		hud_controls += 1
		var why := ""
		if not vp.has_point(p):
			why = "tap point off screen"
		else:
			var d := minf(minf(p.x - vp.position.x, vp.end.x - p.x), minf(p.y - vp.position.y, vp.end.y - p.y))
			var pr: Rect2 = m["rect"]
			var shown := pr.intersection(vp).get_area() / maxf(pr.get_area(), 1.0)
			if d < edge_px and shown < SLIVER_SHOWN:
				# a neighbour's door or drawer peeking in at the screen edge: scenery here, a target in its own view
				hud_slivers += 1
				m["hud_warn"] = "sliver, %d %% shown" % int(shown * 100.0)
				lines.append("HUD[%s]: %s — only %d %% of it is on screen, %.1f mm from the edge: scenery here, not checked" % [
					view_id, part, int(shown * 100.0), d * UITheme.mm_per_px()])
				continue
			if d < edge_px:
				why = "%.1f mm from the screen edge (min %.0f)" % [d * UITheme.mm_per_px(), EDGE_MM]
			else:
				for b in blocked:
					if (b["rect"] as Rect2).has_point(p):
						why = "under the HUD: %s" % b["name"]
						break
		if why != "":
			hud_failures += 1
			m["hud"] = why
			lines.append("HUD[%s]: %s — %s" % [view_id, part, why])
			continue
		var r: Rect2 = m["rect"]
		if not vp.encloses(r):
			hud_warnings += 1
			m["hud_warn"] = "partly off screen"
			lines.append("HUD[%s]: %s — part partly off screen (tap point %.0f,%.0f is on)" % [view_id, part, p.x, p.y])
			continue
		for c in covers:
			if (c["rect"] as Rect2).has_point(p):
				hud_warnings += 1
				m["hud_warn"] = "under a banner"
				lines.append("HUD[%s]: %s — covered by a banner (%s)" % [view_id, part, c["name"]])
				break
	return zones


## Can the control at this screen point be worked from the current view, or does a tap on it only move the camera
## to the object's own view (RoomBase.in_reach: a hotspot is operable from its own view and deeper ones)?
func _operable_here(hs: String) -> bool:
	if hs == "":
		return true
	for fn in ["in_reach", "_in_reach"]:
		if room.has_method(fn):
			return bool(room.call(fn, hs))
	return true


static func _fmt_rect(r: Rect2) -> String:
	return "[%d,%d %dx%d]" % [int(r.position.x), int(r.position.y), int(r.size.x), int(r.size.y)]


func _hud_restore() -> void:
	var logic: RoomLogic = GameState.logic
	logic.select_item("")
	var hud := room.get("hud") as CanvasLayer
	if hud != null:
		hud.call("message", "", 0.1)


## Where a tap never reaches the room: HUD.blocked_rects() when the HUD provides it, otherwise every visible HUD
## control that stops input (buttons, slots, scroll areas) plus the inventory column as assumed until then
## (ASSUMED_COLUMN of the width, from under the Back button to the bottom). -> [{rect, name}]
func _blocked_rects(hud: CanvasLayer) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	if hud == null:
		return out
	if hud.has_method("blocked_rects"):
		for r: Rect2 in hud.call("blocked_rects"):
			out.append({"rect": r, "name": "HUD control"})
		return out
	var rects: Array[Dictionary] = []
	for c in hud.find_children("*", "Control", true, false):
		var ctl := c as Control
		if not ctl.is_visible_in_tree() or ctl.mouse_filter != Control.MOUSE_FILTER_STOP:
			continue
		if ctl is UIBanner or ctl is Label:
			continue
		var r := ctl.get_global_rect()
		if r.size.x < 2.0 or r.size.y < 2.0:
			continue
		var nm := str(ctl.name)
		if ctl is IconButton:
			nm = "%s button" % (ctl as IconButton).icon_id
		elif ctl is Button and ctl.tooltip_text != "":
			nm = "slot «%s»" % ctl.tooltip_text
		rects.append({"rect": r, "name": nm})
	# keep the outermost rects only
	for a in rects:
		var inside := false
		for b in rects:
			if a != b and (b["rect"] as Rect2).encloses(a["rect"]) and (b["rect"] as Rect2) != (a["rect"] as Rect2):
				inside = true
				break
		if not inside:
			out.append(a)
	var vp := get_viewport().get_visible_rect()
	var safe := UITheme.safe_margins()
	var top := safe.y + UITheme.HUD_PAD + UITheme.target(UITheme.HUD_BACK_PX) + 16.0
	out.append({"rect": Rect2(0.0, top, vp.size.x * ASSUMED_COLUMN, vp.size.y - top), "name": "inventory column (assumed %d %%)" % int(ASSUMED_COLUMN * 100)})
	return out


## Banners that cover the scene without taking input (title, caption, message, prompt). -> [{rect, name}]
func _banner_rects(hud: CanvasLayer) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	if hud == null:
		return out
	for c in hud.find_children("*", "Control", true, false):
		if c is UIBanner and (c as Control).is_visible_in_tree() and (c as Control).modulate.a > 0.05:
			var b := c as UIBanner
			var txt := b.title_label.text if b.title_label.text != "" else b.subtitle_label.text
			out.append({"rect": b.get_global_rect(), "name": "banner «%s»" % tr(txt).left(40)})
	return out


func _screen_rect(cam: Camera3D, mi: MeshInstance3D) -> Rect2:
	var ab := mi.mesh.get_aabb()
	var r := Rect2()
	for k in 8:
		var wp := mi.global_transform * ab.get_endpoint(k)
		if cam.is_position_behind(wp):
			return Rect2()
		var sp := cam.unproject_position(wp)
		r = Rect2(sp, Vector2.ZERO) if k == 0 else r.expand(sp)
	return r


class _Marks extends Control:
	var marks: Array[Dictionary] = []
	var zones: Array[Dictionary] = [] # HUD check: blocked (red) and cover (yellow) rects
	var edge_px := 0.0 # HUD check: the screen-edge margin (cyan line)

	func _draw() -> void:
		var font := ThemeDB.fallback_font
		for z: Dictionary in zones:
			var blocked: bool = z["kind"] == "blocked"
			var zc := Color(1.0, 0.2, 0.2) if blocked else Color(1.0, 0.85, 0.2)
			draw_rect(z["rect"], Color(zc, 0.12), true)
			draw_rect(z["rect"], zc, false, 1.5)
		if edge_px > 0.0:
			draw_rect(Rect2(Vector2.ONE * edge_px, size - Vector2.ONE * 2.0 * edge_px), Color(0.3, 0.9, 1.0, 0.8), false, 1.0)
		for m: Dictionary in marks:
			var h: int = m["hits"]
			var c := Color(0.2, 1.0, 0.35) if h >= 3 else (Color(1.0, 0.7, 0.1) if h > 0 else Color(1.0, 0.25, 0.2))
			draw_circle(m["pos"], 5.0, c)
			var label: String = str(m["part"]).replace("IA_", "")
			if h < 3:
				label += " %d→%s" % [h, str(m["got"]).replace("IA_", "")]
			if m.has("hud"):
				draw_arc(m["pos"], 11.0, 0.0, TAU, 24, Color(1.0, 0.2, 0.2), 2.5)
				label += " ✗ " + str(m["hud"])
			elif m.has("hud_warn"):
				draw_arc(m["pos"], 11.0, 0.0, TAU, 24, Color(1.0, 0.85, 0.2), 2.0)
				label += " ! " + str(m["hud_warn"])
			draw_string(font, m["pos"] + Vector2(7, 4), label, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, c)
