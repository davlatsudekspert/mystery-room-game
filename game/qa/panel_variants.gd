extends Node
## QA: the Panel 7 close-up of every wiring in Lab7Logic.PANEL_POOL, rendered from the real Lab 7 scene in one
## process (docs/VARIANTS.md). Each wiring is reached through a real game seed (the first seed that draws it; seed 0
## for the canonical one), the solver plays up to the breaker handle, and the camera goes to the "panel" view.
## Run: tools/qa_run.sh -- --resolution 1560x720 res://qa/panel_variants.tscn -- --out=<dir>
##   (1560x720 = a 19.5:9 phone; QA_XVFB_ARGS="-screen 0 1700x900x24" gives Xvfb the room)
## Writes <dir>/panel_<n>_seed<s>.png and prints one line per wiring: the seed, the shortest answer, the decal.

var out_dir := "/tmp"


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
	DirAccess.make_dir_recursive_absolute(out_dir)
	SaveSystem.save_path = "user://qa_probe_save.json"
	var failed := 0
	for n in Lab7Logic.PANEL_POOL.size():
		var game_seed := _seed_for(n)
		GameState.variant_seed = game_seed
		GameState.start_new("ch1")
		var logic := GameState.logic as Lab7Logic
		var guard := 0
		while not logic.state["handle_installed"] and guard < 300:
			guard += 1
			Lab7Solver.step(logic, "leave_lens")
		if logic.panel_variant() != n or not logic.state["handle_installed"]:
			failed += 1
		var answer := ", ".join(logic.panel_solution().map(func(v: Variant) -> String: return Lab7Logic.roman(int(v) + 1)))
		print("wiring %d: seed %d, shortest answer %s, matrix %s, plate panel_diagram_%d.jpg" % [n, game_seed, answer, str(logic.panel_matrix()), logic.panel_variant()])
		var room: Node3D = (load("res://src/rooms/lab7/lab7.tscn") as PackedScene).instantiate()
		room.set("capture_mode", true)
		get_tree().root.add_child(room)
		await _settle(1.5)
		var cam: RoomCamera = room.get("cam")
		cam.go("panel", true)
		await _settle(0.9)
		await _shot("panel_%d_seed%d" % [n, game_seed])
		room.queue_free()
		await _settle(0.5)
		SaveSystem.delete_game()
	print("wirings rendered: %d, failed: %d" % [Lab7Logic.PANEL_POOL.size(), failed])
	print("QA_DONE exit=%d" % (1 if failed > 0 else 0)) # tools/qa_run.sh: the run finished even if the process then hangs on exit
	get_tree().quit(1 if failed > 0 else 0)


## The first game seed that draws wiring n (seed 0 is the canonical wiring).
func _seed_for(n: int) -> int:
	if n == 0:
		return 0
	for s in range(1, 2000):
		var l := Lab7Logic.new()
		l.apply_seed(s)
		if l.panel_variant() == n:
			return s
	return 0


func _settle(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()


func _shot(shot_name: String) -> void:
	await RenderingServer.frame_post_draw
	var p := "%s/%s.png" % [out_dir, shot_name]
	get_viewport().get_texture().get_image().save_png(p)
	print("shot ", p)
