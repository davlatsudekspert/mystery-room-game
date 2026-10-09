extends Node
## Current chapter session: owns the RoomLogic, autosaves, tracks play time, hints and cross-chapter choices.

signal events(ev: Array[String])
signal chapter_started(chapter_id: String)
signal hint_shown(goal: String, level: int)

const AUTOSAVE_DELAY := 0.75
const COLLECT_ACHIEVEMENT := {"ch1": "light_remembers", "ch2": "echoes_of_the_archive", "ch3": "echoes_of_the_deep"}

var chapter_id := ""
var logic: RoomLogic
var profile: Dictionary = {}
var play_time := 0.0
var hints_used := 0
var in_game := false
var _hint_goal := ""
var _hint_level := 0
var _autosave_timer: Timer


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	profile = SaveSystem.load_profile()
	_autosave_timer = Timer.new()
	_autosave_timer.one_shot = true
	_autosave_timer.wait_time = AUTOSAVE_DELAY
	_autosave_timer.timeout.connect(save_now)
	add_child(_autosave_timer)


func _process(delta: float) -> void:
	if in_game and not get_tree().paused:
		play_time += delta


func _notification(what: int) -> void:
	if what in [NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_WM_CLOSE_REQUEST, NOTIFICATION_APPLICATION_FOCUS_OUT]:
		if in_game:
			save_now()


# ------------------------------------------------------------------ lifecycle
func start_new(id: String) -> bool:
	var l := Chapters.new_logic(id)
	if l == null:
		return false
	l.setup_from_profile(profile.get("choices", {}))
	_attach(id, l)
	play_time = 0.0
	hints_used = 0
	save_now()
	return true


func continue_saved() -> bool:
	var d := SaveSystem.load_game()
	if d.is_empty():
		return false
	var id := str(d.get("chapter", ""))
	var l := Chapters.new_logic(id)
	if l == null or not l.from_dict(d.get("logic", {})):
		return false
	_attach(id, l)
	var stats: Dictionary = d.get("stats", {})
	play_time = float(stats.get("play_time", 0.0))
	hints_used = int(stats.get("hints_used", 0))
	return true


func saved_chapter() -> String:
	return str(SaveSystem.load_game().get("chapter", ""))


func _attach(id: String, l: RoomLogic) -> void:
	if logic != null and logic.changed.is_connected(_on_logic_changed):
		logic.changed.disconnect(_on_logic_changed)
	chapter_id = id
	logic = l
	logic.changed.connect(_on_logic_changed)
	_hint_goal = ""
	_hint_level = 0
	chapter_started.emit(id)


func _on_logic_changed(ev: Array[String]) -> void:
	events.emit(ev)
	if ev.has("chapter_complete"):
		_on_chapter_complete()
	_autosave_timer.start()


func save_now() -> bool:
	if logic == null:
		return false
	return SaveSystem.save_game({
		"chapter": chapter_id,
		"logic": logic.to_dict(),
		"stats": {"play_time": play_time, "hints_used": hints_used},
	})


func _on_chapter_complete() -> void:
	var completed: Array = profile.get("completed", [])
	if not completed.has(chapter_id):
		completed.append(chapter_id)
	profile["completed"] = completed
	var choices: Dictionary = profile.get("choices", {})
	choices.merge(logic.profile_choices(), true)
	profile["choices"] = choices
	var c: Array = logic.collectibles()
	if int(c[1]) > 0 and int(c[0]) >= int(c[1]):
		unlock_achievement(COLLECT_ACHIEVEMENT.get(chapter_id, "collect_" + chapter_id))
	if hints_used == 0:
		unlock_achievement("no_hints_" + chapter_id)
	profile["hints_used"] = int(profile.get("hints_used", 0)) + hints_used
	SaveSystem.save_profile(profile)


func unlock_achievement(id: String) -> void:
	var a: Array = profile.get("achievements", [])
	if not a.has(id):
		a.append(id)
		profile["achievements"] = a
		SaveSystem.save_profile(profile)


func is_chapter_completed(id: String) -> bool:
	return (profile.get("completed", []) as Array).has(id)


# ------------------------------------------------------------------ hints
## Returns {"goal", "level" (1..3), "key"}; repeated requests for the same goal escalate the level.
func next_hint() -> Dictionary:
	if logic == null:
		return {}
	var goal := logic.hint_goal()
	if goal == "":
		return {}
	if goal != _hint_goal:
		_hint_goal = goal
		_hint_level = 0
	_hint_level = mini(_hint_level + 1, 3)
	hints_used += 1
	hint_shown.emit(goal, _hint_level)
	return {"goal": goal, "level": _hint_level, "key": "hint.%s.%d" % [goal, _hint_level]}


func current_hint_level() -> int:
	return _hint_level
