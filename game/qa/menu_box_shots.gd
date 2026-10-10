extends Node
## QA: renders the main menu's gear box at exact moments (the backdrop is stepped by hand, so the frames do not
## depend on how fast the software renderer is).
##   tools/qa_run.sh -- res://qa/menu_box_shots.tscn -- --out=<dir> --mode=transition [--times=0,0.3,0.7]
## Modes: transition (New Game: frames at --times seconds after the tap), idle (the glint, the lid lift), play (taps the
## knobs through the real tap path until the box opens; frames at --times after the opening), reduce (reduce_motion).
## Options: --window=WxH (default 1170x540, a 6.1" phone's aspect), --lang=en|ru|uz.

var out_dir := "/tmp"
var mode := "transition"
var times: Array[float] = [0.0, 0.30, 0.66, 0.9, 1.1, 1.3, 1.5, 1.7, 1.9]
var open_times: Array[float] = [0.0, 0.25, 0.6, 1.1, 2.0]
var win := Vector2i(1170, 540)
var lang := "en"
var menu: Control
var bg: MenuBackground
var gotos := 0


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--mode="):
			mode = a.substr(7)
		elif a.begins_with("--window="):
			var p := a.substr(9).split("x")
			win = Vector2i(int(p[0]), int(p[1]))
		elif a.begins_with("--lang="):
			lang = a.substr(7)
		elif a.begins_with("--times="):
			times.clear()
			for s in a.substr(8).split(",", false):
				times.append(float(s))
	DirAccess.make_dir_recursive_absolute(out_dir)
	get_window().size = win
	await _settle(0.3)
	Settings.set("emulate", {"size": Vector2i(2340, 1080), "dpi": 400.0, "safe": Rect2i(120, 0, 2220, 1080)})
	SaveSystem.save_path = "user://qa_menu_box_save.json"
	GameState.start_new("ch1") # a save: the menu offers Continue
	TranslationServer.set_locale(lang)
	for m in mode.split(",", false):
		await _mode(m)
	print("QA_DONE exit=0")
	get_tree().quit(0)


func _mode(m: String) -> void:
	Settings.values["reduce_motion"] = m == "reduce"
	gotos = 0
	menu = (load("res://src/ui/main_menu.tscn") as PackedScene).instantiate()
	get_tree().root.add_child(menu)
	menu.set("goto_fn", func(path: String, fade: float) -> void:
		gotos += 1
		print("goto(%s, %.2f)" % [path, fade]))
	await _settle(1.6) # the entrance
	bg = menu.get("_bg")
	bg.manual = true
	match m:
		"transition", "reduce":
			await _transition()
		"idle":
			await _idle()
		"play":
			await _play()
	print("mode %s: gotos=%d" % [m, gotos])
	menu.queue_free()
	await _settle(0.2)


func _settle(seconds: float) -> void:
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < seconds * 1000.0:
		await get_tree().process_frame


func _step(seconds: float) -> void:
	var n := int(round(seconds * 60.0))
	for i in n:
		bg.advance(1.0 / 60.0)


func _shot(name: String) -> void:
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("%s/%s.png" % [out_dir, name])
	print("shot " + name)


func _transition() -> void:
	var now := 0.0
	await _shot("t_%04d" % 0)
	menu.call("_play", "ch1")
	for t in times:
		if t > now:
			_step(t - now)
			now = t
		await _shot("t_%04d" % int(round(t * 1000.0)))
	print("goto emitted: %d, black %.2f" % [bg.box.logic.goto_count, bg.fade()])


func _idle() -> void:
	_step(0.5)
	await _shot("idle_plain")
	bg.box.show_glint(0.42)
	bg.advance(0.0)
	await _shot("idle_glint")
	bg.box.show_glint(0.62)
	bg.advance(0.0)
	await _shot("idle_glint2")


## Taps the knobs on screen through MenuBackground.tap() (the real path) until the box opens.
func _play() -> void:
	var box := bg.box
	await _shot("play_0")
	var cam := bg.get_viewport().get_camera_3d()
	var plan: Array = []
	for i in 3:
		for n in int((MenuBoxLogic.SCRAMBLES[0] as Array)[i]):
			plan.append(i)
	for step in plan:
		var wp: Vector3 = box.get("_knobs")[step].global_position
		var p := cam.unproject_position(wp)
		print("tap knob %d at %s" % [step, p])
		print("hit=%s" % bg.tap(p))
		_step(0.12)
		await _shot("play_press_%d_%d" % [step, box.logic.presses])
		_step(0.3)
	print("phase after plan: %d wheels %s" % [box.logic.phase, box.logic.wheels])
	var prev := 0.0
	for t in open_times:
		_step(maxf(t - prev, 0.001))
		prev = t
		await _shot("play_open_%04d" % int(round(t * 1000.0)))
	_step(1.0)
	await _shot("play_hold")
	box.tap_anywhere()
	_step(0.4)
	await _shot("play_closing")
