extends SceneTree
## Prints the answers of the Chapter 2 expansion for some seeds (language-neutral). godot --headless --path <pg> -s res://qa/seed_probe.gd -- 9137 2468 ...
func _init() -> void:
	var seeds: Array = []
	for a in OS.get_cmdline_user_args():
		seeds.append(int(a))
	for sd: int in seeds:
		var al := ArchiveLogic.new()
		al.begin_expansion(2)
		al.apply_seed(sd)
		var s := al.state
		print("seed %d: panel=%s pipes#%d sol=%s glyph=%s bay=%d aisle_pos=%s sym=%s chest_start=%s presses=%s cabinet=%s load=%d strip=%d zoom=%d pfocus=%d punch=%s valves=%s booth=%s" % [sd,
			al.panel_letter(), int(s["v_pipes"]), str(al.pipe_solution()), str(al.light_digits()), int(s["v_bay"]), str(s["aisle_pos"]),
			str(s["v_symbols"]), str(s["v_chest_start"]), str(al.chest_presses()), str(al.cabinet_digits()), int(s["v_load"]),
			int(s["v_strip"]), int(s["v_zoom"]), int(s["v_pfocus"]), str(al.punch_code()), str(al.valve_solution()), al.booth_code()])
	quit()
