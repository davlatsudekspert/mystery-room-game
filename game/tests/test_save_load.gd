extends TestBase
## Save format robustness: round trips, JSON number coercion, corrupted and future data.


func test_round_trip_through_json() -> void:
	var l := Lab7Logic.new()
	for _i in 60:
		Lab7Solver.step(l, "leave_lens")
	var json := JSON.stringify(l.to_dict())
	var r := Lab7Logic.new()
	check(r.from_dict(JSON.parse_string(json)), "loads")
	eq(r.inventory, l.inventory, "inventory")
	eq(JSON.stringify(r.to_dict()), json, "identical after reload")
	eq(typeof(r.state["dial"]), TYPE_INT, "JSON floats coerced back to int")
	eq(typeof(r.state["gears"][0]), TYPE_INT, "array ints coerced")


func test_corrupted_data_falls_back_to_defaults() -> void:
	var r := Lab7Logic.new()
	check(not r.from_dict({"state": "garbage"}), "rejects non-dict state")
	eq(r.state, Lab7Logic.new().state, "defaults kept")
	r.from_dict({"state": {"drawer_open": "yes", "dial": [1, 2], "gears": [1, 2], "unknown_key": 5}, "inventory": [3, "notebook", "notebook"], "selected": "brass_key"})
	eq(r.state["drawer_open"], false, "wrong type ignored")
	eq(r.state["dial"], Lab7Logic.RADIO_START, "wrong type ignored")
	eq(r.state["gears"], [1, 3, 2], "wrong array length ignored")
	check(not r.state.has("unknown_key"), "unknown keys dropped")
	eq(r.inventory, ["notebook"] as Array[String], "non-strings and duplicates dropped")
	eq(r.selected, "", "selection must be an owned item")


func test_save_is_language_independent() -> void:
	var l := Lab7Logic.new()
	Lab7Solver.solve(l)
	var text := JSON.stringify(l.to_dict())
	for word in ["Leyla's", "Лейла", "daftar", "notebook page"]:
		check(not text.contains(word), "no translated text in save: " + word)
