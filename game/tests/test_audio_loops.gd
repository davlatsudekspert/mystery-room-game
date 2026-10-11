extends TestBase
## Looping sounds must stop. A file imported as a loop (sfx/tape_hiss) played through the pooled one-shot
## AudioManager.sfx() never ended: on the owner's iPhone the Chapter 2 cliffhanger's tape hiss kept playing over the
## menu and Chapter 3 (a steady 0.5-4 kHz hiss in the owner's screen recording). Loops now go through sfx_loop(), which
## the scene change stops, and sfx() plays a looping file once.

const SFX_DIR := "res://assets/audio/sfx"


func _tree() -> SceneTree:
	return Engine.get_main_loop() as SceneTree


func _wait(seconds: float) -> void:
	await _tree().create_timer(seconds).timeout


func test_sfx_plays_a_looping_file_once() -> void:
	var looping: Variant = AudioManager.stream("sfx", "tape_hiss")
	check(looping is AudioStream and AudioManager.loops(looping as AudioStream), "tape_hiss is imported as a loop")
	var once := AudioManager.once_stream("tape_hiss")
	check(once != null and not AudioManager.loops(once), "sfx() gets a copy of tape_hiss that plays once")
	check(AudioManager.loops(looping as AudioStream), "the loop itself is left alone for sfx_loop()")
	AudioManager.sfx("tape_hiss", -60.0)
	var pool: Array = AudioManager.get("_pool")
	var looping_players := 0
	for p: AudioStreamPlayer in pool:
		if p.playing and p.stream != null and AudioManager.loops(p.stream):
			looping_players += 1
		p.stop()
	eq(looping_players, 0, "no pooled one-shot player holds a looping stream")


func test_sfx_loop_starts_and_stops() -> void:
	AudioManager.sfx_loop("tape_hiss", true, -60.0, 1.0, 0.05)
	check(AudioManager.sfx_loop_playing("tape_hiss"), "the loop runs")
	AudioManager.sfx_loop("tape_hiss", true, -50.0, 1.0, 0.05) # again (a rewind): the same loop, not a second one
	var loops: Dictionary = AudioManager.get("_loops")
	eq(loops.size(), 1, "starting a running loop again does not stack a second one")
	var p: AudioStreamPlayer = loops["tape_hiss"]
	AudioManager.sfx_loop("tape_hiss", false, 0.0, 1.0, 0.05)
	check(not AudioManager.sfx_loop_playing("tape_hiss"), "turned off")
	await _wait(0.3)
	check(not is_instance_valid(p), "its player is freed once faded out")


func test_scene_change_stops_every_loop() -> void:
	AudioManager.sfx_loop("tape_hiss", true, -60.0, 1.0, 0.05)
	AudioManager.sfx_loop("compressor_loop", true, -60.0, 1.0, 0.05)
	AudioManager.stop_sfx_loops(0.05)
	check(not AudioManager.sfx_loop_playing("tape_hiss") and not AudioManager.sfx_loop_playing("compressor_loop"),
		"stop_sfx_loops() ends every loop")
	await _wait(0.3)
	var src := FileAccess.get_file_as_string("res://src/autoload/scene_manager.gd")
	check(src.contains("AudioManager.stop_sfx_loops("), "SceneManager.goto stops the loops of the scene it leaves")


## Every AudioManager.sfx("name") in the game plays a file that ends: a loop belongs in sfx_loop().
func test_no_one_shot_call_plays_a_loop() -> void:
	var re := RegEx.create_from_string("AudioManager\\.sfx\\(\"([a-z0-9_]+)\"")
	var bad: Array[String] = []
	var calls := 0
	for path in _scripts("res://src"):
		var src := FileAccess.get_file_as_string(path)
		for m in re.search_all(src):
			calls += 1
			var s := AudioManager.stream("sfx", m.get_string(1))
			if s != null and AudioManager.loops(s):
				bad.append("%s: %s" % [path.get_file(), m.get_string(1)])
	check(calls > 50, "the scan finds the game's sfx() calls (%d)" % calls)
	eq(bad.size(), 0, "sfx() calls that play a looping file %s" % str(bad))


func _scripts(dir: String) -> Array[String]:
	var out: Array[String] = []
	var d := DirAccess.open(dir)
	if d == null:
		return out
	for f in d.get_files():
		if f.ends_with(".gd"):
			out.append(dir.path_join(f))
	for sub in d.get_directories():
		out.append_array(_scripts(dir.path_join(sub)))
	return out
