extends Node
## Zero-dependency headless test runner.
## Usage: godot --headless --path game res://tests/run_all.tscn  (exit code 0 = all passed)
## Optional filter: -- --filter=<substring of file or method>


## A test that awaits and then stops on a script error never completes: it fails after this long instead of
## hanging the whole run (and every agent waiting on it).
const TEST_TIMEOUT_S := 120


func _ready() -> void:
	var filter := ""
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--filter="):
			filter = a.substr(9)
	var files: Array[String] = []
	var dir := DirAccess.open("res://tests")
	for f in dir.get_files():
		if f.begins_with("test_") and f.ends_with(".gd") and f != "test_base.gd":
			files.append(f)
	files.sort()
	var total_checks := 0
	var total_tests := 0
	var failures: Array[String] = []
	var t0 := Time.get_ticks_msec()
	for f in files:
		var script := load("res://tests/" + f) as GDScript
		if script == null or not script.can_instantiate():
			# a parse error must fail the run, not hang it (the runner never reached quit() before)
			failures.append("%s: the script does not load (parse error?)" % f)
			print("[%s] ✗ does not load" % f)
			continue
		var suite: Object = script.new()
		var names: Array[String] = []
		for m in suite.get_method_list():
			var n: String = m["name"]
			if n.begins_with("test_") and (filter == "" or filter in f or filter in n):
				names.append(n)
		names.sort()
		for n in names:
			suite.set("current", f.get_basename() + "." + n)
			var before: int = (suite.get("failures") as Array).size()
			if suite.has_method("before_each"):
				suite.call("before_each")
			var result: Variant = suite.call(n)
			if result is Object and result.get_class() == "GDScriptFunctionState":
				if not await _finished(result as Object, TEST_TIMEOUT_S):
					(suite.get("failures") as Array).append("%s.%s: did not finish within %d s (a script error inside an await stops a test for good, or an await never resolved)" % [f.get_basename(), n, TEST_TIMEOUT_S])
			total_tests += 1
			var after: int = (suite.get("failures") as Array).size()
			print("  %s %s" % ["✓" if after == before else "✗", n])
		total_checks += int(suite.get("checks"))
		failures.append_array(suite.get("failures"))
		print("[%s] done" % f)
	var dt := Time.get_ticks_msec() - t0
	print("\n%d tests, %d checks, %d failures (%d ms)" % [total_tests, total_checks, failures.size(), dt])
	for msg in failures:
		printerr("FAIL " + msg)
	get_tree().quit(1 if failures.size() > 0 else 0)


## Waits for a test coroutine. -> false when it has not finished within `limit` seconds.
func _finished(state: Object, limit: float) -> bool:
	var done := {"v": false}
	state.connect("completed", func(_r: Variant = null) -> void: done["v"] = true)
	var t0 := Time.get_ticks_msec()
	while not done["v"]:
		if Time.get_ticks_msec() - t0 > int(limit * 1000.0):
			return false
		await get_tree().process_frame
	return true
