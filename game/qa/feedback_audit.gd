extends Node
## QA: every tappable mechanism answers. Loads a chapter room and, for a list of player taps (a view and a part in
## a given puzzle state), taps the part's visible screen point through the room's own raycast like a finger, then
## checks that something answered: a HUD message or caption, a sound, a camera move, an opened document, or a
## change of the logic state. "Locked" and "not yet" states are the point: a silent tap is a ✗.
## Headless works (no pixels are needed):
##   godot --headless --path game res://qa/feedback_audit.tscn -- --chapter=ch1 [--out=<dir>] [--seed=N]
## Writes <out>/feedback_<chapter>.txt. Exit 0 = every tap answered.

const SCENES := {"ch1": "res://src/rooms/lab7/lab7.tscn", "ch2": "res://src/rooms/archive/archive.tscn"}

## [stage (state key the solver plays up to, "" = start), view, model, part, note]. Stages must come in play order.
const CASES := {
	"ch1": [
		["", "lab", "desk", "", "desk from the room → close-up"],
		["", "door", "door_lab7", "IA_door_leaf", "sealed door"],
		["", "lock", "light_sensor", "", "light lock before any light"],
		["", "clock", "flip_clock", "", "the stopped clock"],
		["", "desk", "cc_tea", "", "tea set on the desk"],
		["", "drawer", "desk", "IA_drawer_top", "locked drawer front"],
		["", "drawer", "desk", "IA_drawer_digit_0", "code wheel"],
		["", "desk_side", "desk", "IA_secret_panel", "desk side before the rosette"],
		["", "gearbox", "gear_box", "IA_box_lid", "shut gear box lid"],
		["", "gearbox", "gear_box", "IA_knob_0", "gear knob"],
		["", "filing", "filing_cabinet", "", "filing cabinet"],
		["", "chalkboard", "chalkboard", "", "chalkboard"],
		["", "poster", "poster_frame", "", "poster"],
		["", "bench", "lab_bench", "", "bench"],
		["", "radio", "radio", "IA_tuning_knob", "dead radio knob"],
		["", "radio", "radio", "IA_radio_hatch", "radio hatch"],
		["", "safe", "wall_safe", "IA_safe_door", "shut safe door"],
		["", "safe", "wall_safe", "IA_key_1", "safe key"],
		["", "panel", "panel7", "IA_main_lever", "main lever without its handle"],
		["", "panel", "panel7", "lamp_0", "panel lamp"],
		["", "panel", "panel7", "IA_switch_1", "breaker switch"],
		["", "coat", "coat_rack", "", "coat"],
		["", "window", "cc_kettle", "", "window sill"],
		["", "radiator", "radiator_tap", "IA_radiator", "radiator"],
		["", "mirror_b", "mirror_stand_b", "IA_mirror_mount", "empty mirror bracket"],
		["", "mirror_a", "mirror_stand", "IA_mirror_mount", "mirror A"],
		["", "projector", "lumen_projector", "IA_projector_lever", "projector lever, no power"],
		["", "projector", "lumen_projector", "IA_lens_socket", "empty lens socket, no power"],
		["", "books", "bookshelf", "IA_book_1", "book"],
		["drawer_open", "drawer", "desk", "IA_drawer_digit_1", "code wheel after the drawer opened"],
		["drawer_open", "drawer", "desk", "IA_drawer_top", "open drawer"],
		["box_open", "gearbox", "gear_box", "IA_knob_1", "gear knob after the box opened"],
		["box_open", "gearbox", "gear_box", "IA_box_lid", "open gear box"],
		["safe_open", "safe", "wall_safe", "IA_key_2", "safe key after it opened"],
		["safe_open", "safe", "wall_safe", "IA_safe_door", "open safe"],
		["compartment_open", "desk_side", "desk", "IA_compartment", "open compartment"],
		["power_on", "panel", "panel7", "IA_switch_1", "switch after the power is back"],
		["power_on", "panel", "panel7", "IA_main_lever", "main lever after the power is back"],
		["power_on", "radio", "radio", "IA_tuning_knob", "live radio knob"],
		["power_on", "projector", "lumen_projector", "IA_projector_lever", "projector lever, no lens"],
		["shelf_open", "books", "bookshelf", "IA_book_2", "book after the case swung open"],
		["shelf_open", "shadow", "shadow_lock", "sculpture_ring", "sculpture from the shadow view"],
		["shelf_open", "sculpture", "shadow_lock", "IA_ring_knob", "sculpture ring knob"],
		["shelf_open", "cabinet", "shadow_lock", "IA_cabinet_door", "locked cabinet"],
		["shelf_open", "emblem", "shadow_lock", "IA_emblem_socket", "empty emblem socket"],
		["shelf_open", "evidence", "evidence_board", "", "evidence wall (document)"],
		["emblem_recorded", "cabinet", "shadow_lock", "IA_cabinet_door", "open cabinet"],
		["beam_on", "projector_rings", "lumen_projector", "IA_ring_0", "ring while the beam is on"],
		["beam_on", "projector", "lumen_projector", "IA_projector_lever", "lever while the beam is on"],
		["beam_on", "lock", "light_sensor", "", "light lock with the beam on"],
	],
	"ch2": [
		["", "hall", "aisle_sign", "IA_aisle_sign", "aisle sign → west aisle"],
		["", "catalogue", "card_catalogue", "", "catalogue carcass"],
		["", "compressor", "compressor_panel", "gauge_p", "pressure gauge"],
		["", "compressor", "compressor_panel", "IA_valve_a", "valve A"],
		["", "station", "tube_station", "IA_send_lever", "send lever without pressure"],
		["", "station", "tube_station", "IA_send_port", "send port without pressure"],
		["", "station", "tube_station", "IA_receive_tray", "empty receive tray"],
		["", "chart", "routing_chart", "", "routing chart"],
		["", "desk", "archivist_desk", "", "desk → punch or deck"],
		["", "punch", "card_punch", "IA_punch_key_0", "punch key without a card"],
		["", "punch", "card_punch", "IA_punch_lever", "punch lever without a card"],
		["", "deck", "tape_deck", "IA_play", "play with no reel"],
		["", "deck", "tape_deck", "IA_eject", "eject with no reel"],
		["", "deck", "tape_deck", "IA_speed", "speed knob"],
		["", "lockers", "lockers", "IA_locker_9", "locker 9 without the key"],
		["", "lockers", "lockers", "IA_locker_3", "another locker"],
		["", "stacks", "stacks_shelving", "", "the stacks"],
		["", "reading", "reading_table", "", "reading table"],
		["", "booth_door", "booth_door", "IA_booth_door", "locked booth door"],
		["", "dial", "booth_door", "IA_rotary_dial", "dial centre"],
		["", "dial", "booth_door", "IA_dial_hole_5", "dial hole"],
		["", "screen", "projection_screen", "screen_surface", "dark screen"],
		["", "socket", "projection_screen", "IA_screen_socket", "empty screen socket"],
		["", "vault", "vault_door", "IA_vault_handle", "vault wheel, locked"],
		["", "vault", "vault_door", "bolt_0", "vault door body"],
		["", "vault_ports", "vault_door", "IA_port_left", "empty crystal port"],
		["", "vault_ports", "vault_door", "IA_collar_left", "collar"],
		["", "vault_ports", "vault_door", "glass_disc", "glass disc"],
		["locker_open", "locker9", "lockers", "IA_locker_9", "locker 9 after the receiver is taken"],
		["grille_open", "grille", "vent_grille", "IA_grille", "open grille (reel taken)"],
		["booth_open", "booth", "film_projector", "", "projector from the booth"],
		["booth_open", "projector", "film_projector", "IA_run_lever", "run lever with no reel"],
		["booth_open", "projector", "film_projector", "IA_focus_ring", "focus ring"],
		["booth_open", "splicer", "film_splicer", "light_box_glass", "splicer light box"],
		["booth_open", "splicer", "film_splicer", "IA_frame_0", "loose film strip"],
		["booth_open", "slides", "slide_cabinet", "IA_slide_drawer_0", "slide drawer"],
		["booth_open", "slide_projector", "slide_projector", "IA_slide_rot", "slide turn knob, no slide"],
		["booth_open", "slide_projector", "slide_projector", "IA_slide_lamp", "slide lamp"],
		["booth_open", "lens_case", "lens_case", "IA_case_lid", "lens case lid"],
		["vault_unlocked", "vault", "vault_door", "IA_vault_handle", "vault wheel, unlocked"],
	],
}

var out_dir := "/tmp/feedback_audit"
var chapter := "ch1"
var room: Node3D
var hud: Node
var logic: RoomLogic
var lines: Array[String] = []
var bad := 0


func _ready() -> void:
	GameState.variant_seed = 0
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--chapter="):
			chapter = a.substr(10)
		elif a.begins_with("--seed="):
			GameState.variant_seed = int(a.substr(7))
	DirAccess.make_dir_recursive_absolute(out_dir)
	SaveSystem.save_path = "user://qa_feedback_save.json"
	SaveSystem.profile_path = "user://qa_feedback_profile.json"
	GameState.profile = {"choices": {"ch1_lens": "leave_lens", "ch1_shards": 5}}
	GameState.start_new(chapter)
	logic = GameState.logic
	room = (load(SCENES[chapter]) as PackedScene).instantiate()
	room.set("capture_mode", true)
	get_tree().root.add_child.call_deferred(room)
	await get_tree().process_frame
	await get_tree().process_frame
	hud = room.get("hud")
	await _settle(1.0)
	await run()


func _log(l: String) -> void:
	lines.append(l)
	print(l)


func _settle(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()


func cam() -> RoomCamera:
	return room.get("cam")


func busy() -> bool:
	return bool(hud.get("_busy")) or bool(room.get("_cinematic")) or bool(room.get("_ending"))


func _solve_until(key: String) -> void:
	var guard := 0
	while key != "" and not bool(logic.state.get(key, false)) and guard < 600:
		guard += 1
		if chapter == "ch2":
			ArchiveSolver.step(logic as ArchiveLogic, "leyla_key")
		else:
			Lab7Solver.step(logic as Lab7Logic, "leave_lens")
	logic.select_item("")


func _node(model: String, part: String) -> Node3D:
	var root: Node3D = (room.get("models") as Dictionary).get(model)
	if root == null:
		return null
	return root if part == "" else ModelUtil.find(root, part)


func _rect(n: Node3D, own_only: bool) -> Rect2:
	var meshes := ModelUtil.find_meshes(n)
	if own_only and n is MeshInstance3D:
		meshes = [n as MeshInstance3D]
	var r := Rect2()
	var first := true
	for mi in meshes:
		if not mi.is_visible_in_tree():
			continue
		var ab := mi.get_aabb()
		for k in 8:
			var wp := mi.global_transform * ab.get_endpoint(k)
			if cam().is_position_behind(wp):
				continue
			var sp := cam().unproject_position(wp)
			r = Rect2(sp, Vector2.ZERO) if first else r.expand(sp)
			first = false
	if first and n.get_child_count() > 0 and not cam().is_position_behind(n.global_position):
		# a tap area with no mesh of its own (a static part of the shell): its collider box
		for c in n.get_children():
			for cs in c.get_children():
				if cs is CollisionShape3D and (cs as CollisionShape3D).shape is BoxShape3D:
					var sz := ((cs as CollisionShape3D).shape as BoxShape3D).size
					var aabb := AABB(-sz * 0.5, sz)
					for k in 8:
						var wp := (cs as Node3D).global_transform * aabb.get_endpoint(k)
						if cam().is_position_behind(wp):
							continue
						var sp := cam().unproject_position(wp)
						r = Rect2(sp, Vector2.ZERO) if first else r.expand(sp)
						first = false
	return r


func _hit(sp: Vector2) -> String:
	var h: Dictionary = room.call("raycast", sp)
	if h.is_empty():
		return ""
	return str(room.call("resolve", h)["part"])


## The screen point to tap: the part's projected centre, or the nearest sample that really resolves to the part.
func _tap_point(model: String, part: String) -> Array:
	var n := _node(model, part)
	if n == null:
		return [Vector2(-1, -1), "part missing"]
	var r := _rect(n, part != "")
	if r.size == Vector2.ZERO:
		return [Vector2(-1, -1), "off-screen"]
	var vs := get_viewport().get_visible_rect().size
	var mid := r.get_center()
	if part == "" or _hit(mid) == part:
		return [mid, _hit(mid)]
	var best := mid
	var best_d := INF
	for gy in 7:
		for gx in 7:
			var p := r.position + r.size * Vector2(0.1 + 0.8 * gx / 6.0, 0.1 + 0.8 * gy / 6.0)
			if p.x < 0 or p.y < 0 or p.x > vs.x or p.y > vs.y:
				continue
			var d := p.distance_to(mid)
			if d < best_d and _hit(p) == part:
				best = p
				best_d = d
	return [best, _hit(best)]


func _label_text(name: String) -> String:
	var l := hud.get(name) as Label
	if l == null or l.modulate.a < 0.05 or not l.is_visible_in_tree():
		return ""
	return l.text


func _clear_text(name: String) -> void:
	var l := hud.get(name) as Label
	if l:
		l.text = ""
		l.modulate.a = 0.0


func run() -> void:
	var stage := ""
	for c: Array in CASES[chapter]:
		if str(c[0]) != stage:
			stage = str(c[0])
			_solve_until(stage)
			await _settle(1.5)
			var t := 0.0
			while busy() and t < 90.0:
				await _settle(0.5)
				t += 0.5
			_log("-- stage: %s" % (stage if stage != "" else "start"))
		var view: String = c[1]
		if room.has_method("prepare_view"):
			room.call("prepare_view", view)
		cam().go(view, true)
		await _settle(0.6)
		var tp := _tap_point(c[2], c[3])
		var sp: Vector2 = tp[0]
		if sp.x < 0:
			_log("✗ %s [%s %s/%s]: %s" % [c[4], view, c[2], c[3], tp[1]])
			bad += 1
			continue
		_clear_text("_message")
		_clear_text("_caption_line")
		var sfx0: int = AudioManager.sfx_count
		var state0 := JSON.stringify(logic.state)
		var view0 := cam().current()
		var sel0: String = logic.selected
		room.call("_on_tap", sp)
		await _settle(0.5)
		var answers: Array[String] = []
		var msg := _label_text("_message")
		var cap := _label_text("_caption_line")
		if msg != "":
			answers.append("message «%s»" % msg)
		if cap != "":
			answers.append("caption «%s»" % cap)
		if AudioManager.sfx_count != sfx0:
			answers.append("sound %s" % AudioManager.last_sfx)
		if cam().current() != view0:
			answers.append("camera → %s" % cam().current())
		if JSON.stringify(logic.state) != state0 or logic.selected != sel0:
			answers.append("state changed")
		if hud.get("_overlay") != null:
			answers.append("document opened")
			hud.call("_close_overlay")
		var hit: String = tp[1]
		var where := "%s %s/%s" % [view, c[2], c[3]] + ("" if hit == c[3] or c[3] == "" else " (hit %s)" % hit)
		if answers.is_empty():
			bad += 1
			_log("✗ %s [%s]: no answer" % [c[4], where])
		else:
			_log("✓ %s [%s]: %s" % [c[4], where, "; ".join(answers)])
		var t2 := 0.0
		while busy() and t2 < 60.0:
			await _settle(0.5)
			t2 += 0.5
	_log("feedback audit %s: %d taps, %d silent" % [chapter, (CASES[chapter] as Array).size(), bad])
	var f := FileAccess.open("%s/feedback_%s.txt" % [out_dir, chapter], FileAccess.WRITE)
	f.store_string("\n".join(lines) + "\n")
	SaveSystem.delete_game()
	print("QA_DONE exit=%d" % (0 if bad == 0 else 1))
	get_tree().quit(0 if bad == 0 else 1)
