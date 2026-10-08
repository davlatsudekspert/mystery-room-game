class_name Lab7Hints
extends RefCounted
## Picks the first unmet goal whose prerequisites are met (docs/PUZZLE_DESIGN.md "Hint ladder").
## Text keys: hint.<goal>.1 (nudge), .2 (where), .3 (answer).


static func current_goal(l: Lab7Logic) -> String:
	var s := l.state
	var taken: Dictionary = s["taken"]
	if not l.has_item("notebook") and not taken.get("notebook", false):
		return "notebook"
	# Act A: both early branches are available; prefer whichever is not done.
	if not s["drawer_open"]:
		return "drawer"
	if not taken.get("drawer_lamp", false):
		return "take_lamp"
	if not s["box_open"]:
		return "gearbox"
	if not taken.get("box_cell", false):
		return "take_cell"
	if not l.has_uv():
		return "lamp"
	# Act B
	if not s["uv_page"]:
		return "cipher"
	if not s["safe_open"]:
		return "safe"
	for spot in ["safe_key", "safe_lens", "safe_letter", "safe_valve"]:
		if not taken.get(spot, false):
			return "take_safe"
	if not s["compartment_open"]:
		return "compartment" if not s["rosette"] else "key"
	if not taken.get("compartment_handle", false):
		return "take_handle"
	# Act C
	if not s["handle_installed"]:
		return "handle"
	if not s["power_on"]:
		return "circuits"
	if not s["valve_installed"]:
		return "valve"
	if not s["signal_heard"]:
		return "tune"
	# Act D
	if not s["shelf_open"]:
		return "books"
	if not s["cabinet_open"]:
		return "shadow"
	if not taken.get("cabinet_mirror", false):
		return "take_mirror"
	if not s["emblem_recorded"]:
		return "record"
	# Act E
	if s["lens_at"] == "socket":
		return "retrieve_lens"
	if s["lens_at"] != "projector":
		return "lens"
	if not s["beam_on"]:
		return "projector"
	if not s["mirror_b_mounted"]:
		return "mount_mirror"
	if not s["door_open"]:
		return "mirrors"
	if not s["complete"]:
		return "finale"
	return "done"


static func keys_for(goal: String) -> Array[String]:
	return ["hint.%s.1" % goal, "hint.%s.2" % goal, "hint.%s.3" % goal]


const GOALS: Array[String] = ["notebook", "drawer", "take_lamp", "gearbox", "take_cell", "lamp", "cipher",
	"safe", "take_safe", "compartment", "key", "take_handle", "handle", "circuits", "valve", "tune", "books",
	"shadow", "take_mirror", "record", "retrieve_lens", "lens", "projector", "mount_mirror", "mirrors", "finale"]
