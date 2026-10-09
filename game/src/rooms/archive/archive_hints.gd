class_name ArchiveHints
extends RefCounted
## Picks the first unmet goal whose prerequisites are met (docs/CHAPTER2_DESIGN.md "Hint ladder").
## Text keys: hint.<goal>.1 (nudge), .2 (where), .3 (answer). Goals are prefixed "c2_".

const GOALS: Array[String] = ["c2_catalogue", "c2_compressor", "c2_punch", "c2_dispatch", "c2_take_file",
	"c2_locker", "c2_take_receiver", "c2_hunt", "c2_tape", "c2_booth", "c2_splice", "c2_take_reel",
	"c2_project", "c2_take_crystal", "c2_focus", "c2_record_sign", "c2_mark", "c2_ports", "c2_align",
	"c2_wheel", "c2_finale"]


static func current_goal(l: ArchiveLogic) -> String:
	var s := l.state
	var taken: Dictionary = s["taken"]
	if not taken.get("index_card", false):
		return "c2_catalogue"
	if not s["pressure_ok"]:
		return "c2_compressor"
	if not s["file_delivered"]:
		var ready: bool = (l.has_item("request_card") and s["request_ok"]) or s["canister"] != ""
		return "c2_dispatch" if ready else "c2_punch"
	if not taken.get("canister_file", false) or not taken.get("canister_key", false):
		return "c2_take_file"
	if not s["locker_open"]:
		return "c2_locker"
	if not taken.get("locker_receiver", false):
		return "c2_take_receiver"
	for spot in ["grille_reel", "ledger_reel", "hatch_reel"]:
		if not taken.get(spot, false):
			return "c2_hunt"
	if (s["clicks_heard"] as Array).size() < ArchiveLogic.TAPES.size():
		return "c2_tape"
	if not s["booth_open"]:
		return "c2_booth"
	if not s["reel_repaired"]:
		return "c2_splice"
	if not taken.get("splicer_reel", false):
		return "c2_take_reel"
	if not s["film_seen"]:
		return "c2_project"
	if not (taken.get("case_crystal_1", false) or taken.get("case_crystal_2", false)):
		return "c2_take_crystal"
	if not s["sign_recorded"]:
		return "c2_focus" if not l.is_sharp() else "c2_record_sign"
	if not s["has_lens"] and not s["mark_recorded"]:
		return "c2_mark"
	if not s["vault_unlocked"]:
		var ports_right: bool = l.crystal_image(s["port_left"]) == "mark" and l.crystal_image(s["port_right"]) == "sign"
		return "c2_align" if ports_right else "c2_ports"
	if not s["vault_open"]:
		return "c2_wheel"
	if not s["complete"]:
		return "c2_finale"
	return "done"


static func keys_for(goal: String) -> Array[String]:
	return ["hint.%s.1" % goal, "hint.%s.2" % goal, "hint.%s.3" % goal]
