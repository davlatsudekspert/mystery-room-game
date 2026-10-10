extends Node
## QA: the first minute of a New Game, as a storyboard. Starts at the main menu, presses New Game (the real transition,
## the real SceneManager.goto, the real Lab 7 intro) and shoots the screen at the given seconds of real time after the
## press. Past the intro it plays like a player: taps the flip clock, then the notebook, so the contact sheet shows
## what the first touches feel like. Frames come as fast as the software renderer gives them: each shot is the first
## frame at or after its second of GAME time. Run it with a fixed frame rate, so that the slow software renderer does
## not stretch the timeline (every frame is exactly 1/N s of game time, however long it takes to draw):
##   tools/qa_run.sh -- --fixed-fps 10 res://qa/first_minute.tscn -- --out=<dir> [--times=0,3,6,10,15,20,30,45,60]
##        [--window=WxH] [--lang=en|ru|uz] [--skip-intro] [--reduce]
## The player-like part: the clock at 22 s and 25 s (the second tap is in its close-up: it rattles), back to the lab, the
## notebook at 32 s (the camera moves to the desk) and 36 s (it is taken: a ghost of it lifts off).

var out_dir := "/tmp"
var times: Array[float] = [0.0, 3.0, 6.0, 10.0, 13.0, 14.6, 15.1, 15.6, 16.4, 17.4, 20.0, 26.0, 30.0, 36.8, 45.0, 60.0] # the owner's nine (0 3 6 10 15 20 30 45 60: nearest frames) and the door beats
var win := Vector2i(1170, 540)
var lang := "en"
var skip_intro := false
var reduce := false
var _gt := 0.0 # game seconds since the New Game press
var shots: PackedStringArray = []
var _skip_sent := false


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--window="):
			var p := a.substr(9).split("x")
			win = Vector2i(int(p[0]), int(p[1]))
		elif a.begins_with("--lang="):
			lang = a.substr(7)
		elif a.begins_with("--times="):
			times.clear()
			for s in a.substr(8).split(",", false):
				times.append(float(s))
		elif a == "--skip-intro":
			skip_intro = true
		elif a == "--reduce":
			reduce = true
	DirAccess.make_dir_recursive_absolute(out_dir)
	get_window().size = win
	await _settle(0.3)
	Settings.set("emulate", {"size": Vector2i(2340, 1080), "dpi": 400.0, "safe": Rect2i(120, 0, 2220, 1080)})
	SaveSystem.save_path = "user://qa_first_minute.json"
	SaveSystem.delete_game()
	TranslationServer.set_locale(lang)
	Settings.values["reduce_motion"] = reduce
	var menu := (load("res://src/ui/main_menu.tscn") as PackedScene).instantiate() as Control
	get_tree().root.add_child(menu)
	# this scene must survive SceneManager's scene change (it frees the current scene): the menu becomes the current
	# scene and this node moves to the root
	reparent(get_tree().root)
	get_tree().current_scene = menu
	await _settle(2.0) # the menu's own entrance
	await _shot_now("menu")
	_gt = 0.0
	menu.call("_new_game")
	var i := 0
	while i < times.size():
		await get_tree().process_frame
		_gt += get_process_delta_time()
		var el := _gt
		_play_like_a_player(el)
		if el >= times[i]:
			var name := "fm_%02d" % int(times[i])
			await _save(name)
			shots.append("%s %.1f %s" % [name, el, _stage()])
			print("shot %s at %.1f s (%s)" % [name, el, _stage()])
			i += 1
	var f := FileAccess.open("%s/shots.txt" % out_dir, FileAccess.WRITE)
	f.store_string("\n".join(shots) + "\n")
	f.close()
	print("QA_DONE exit=0")
	get_tree().quit(0)


func _stage() -> String:
	return CrashGuard.stage()


func _settle(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += maxf(get_process_delta_time(), 0.001)


func _shot_now(name: String) -> void:
	await _save(name)


## (A headless run has no frames to wait for: it only checks that the flow runs without errors.)
func _save(name: String) -> void:
	if DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("%s/%s.png" % [out_dir, name])


## After the intro: the clock twice (the second tap, in its close-up, makes it rattle), then the notebook twice.
func _play_like_a_player(el: float) -> void:
	var room := get_tree().current_scene
	if room == null or not room.has_method("_on_tap") or room.get("cam") == null:
		return
	if skip_intro and not _skip_sent and el > 5.0:
		for c in room.get_children():
			if c is Lab7Intro:
				(c as Lab7Intro).skip()
				_skip_sent = true
	var cam: RoomCamera = room.get("cam")
	if cam.transitioning:
		return
	if el >= 22.0 and _step_n == 0:
		_step_n = 1
		_tap_model(room, "flip_clock") # from the lab: the camera moves to the clock
	elif el >= 25.0 and _step_n == 1:
		_step_n = 2
		_tap_model(room, "flip_clock") # in its close-up: it rattles
	elif el >= 28.0 and _step_n == 2:
		_step_n = 3
		cam.go("lab")
	elif el >= 32.0 and _step_n == 3:
		_step_n = 4
		_tap_model(room, "notebook") # the camera moves to the desk
	elif el >= 36.0 and _step_n == 4:
		_step_n = 5
		_tap_model(room, "notebook") # taken: a ghost lifts off


var _step_n := 0


func _tap_model(room: Node, id: String) -> void:
	var cam: RoomCamera = room.get("cam")
	var n: Node3D = (room.get("models") as Dictionary).get(id)
	if n == null:
		return
	var p := cam.unproject_position(n.global_position + Vector3(0, 0.03, 0))
	print("tap %s at %s (view %s)" % [id, p, cam.current()])
	room.call("_on_tap", p)
