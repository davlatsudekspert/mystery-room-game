extends TestBase
## Hint goals follow the solution path and every goal has three translated levels.


func test_goals_progress_monotonically_to_done() -> void:
	var l := Lab7Logic.new()
	var seen: Array[String] = []
	for _i in 400:
		var g := Lab7Hints.current_goal(l)
		if seen.is_empty() or seen[-1] != g:
			seen.append(g)
		if g == "done":
			break
		Lab7Solver.step(l, "leave_lens")
	eq(seen[-1], "done", "reaches done")
	for g in seen:
		check(g == "done" or Lab7Hints.GOALS.has(g), "goal listed: " + g)
	var idx := -1
	for g in seen:
		if g == "done":
			continue
		var gi := Lab7Hints.GOALS.find(g)
		check(gi > idx or g == "retrieve_lens", "goal order %s after index %d" % [g, idx])
		idx = maxi(idx, gi)


func test_every_goal_has_three_translated_levels() -> void:
	var csv := FileAccess.open("res://localization/strings.csv", FileAccess.READ)
	check(csv != null, "strings.csv exists")
	if csv == null:
		return
	var keys := {}
	while not csv.eof_reached():
		var row := csv.get_csv_line()
		if row.size() >= 4:
			keys[row[0]] = row
	for g in Lab7Hints.GOALS:
		for k in Lab7Hints.keys_for(g):
			check(keys.has(k), "missing hint key " + k)
			if keys.has(k):
				for col in [1, 2, 3]:
					check(str(keys[k][col]).strip_edges() != "", "empty translation %s col %d" % [k, col])
