class_name MenuBoxLogic
extends RefCounted
## Rules and timeline of the main-menu gear box (no scene access; MenuBox renders it).
##
## The rule is small and not Chapter 1's: pressing a knob turns its own wheel one notch forward and its meshing
## neighbours one notch back. Six notches per wheel; 0 = the pointer faces the front mark (the numeral side),
## the player's side. When all three face the front the latch releases and the lid opens; a few seconds later (or on
## a tap) it closes and the wheels are scrambled again, a few presses from solved, so it can be played again.
## The coupling matrix has determinant -1, so every state is solvable (distance() <= 15 presses).
##
## Phases: CLOSED (idle, knobs accept presses) -> OPENING -> OPEN -> CLOSING -> CLOSED, and STARTING, the New Game /
## Continue transition: the wheels spin into alignment, the latch releases, the lid opens, the camera pushes in and
## the screen goes to black while the loading flow (SceneManager.goto) starts, exactly once.

signal event(name: StringName, arg: int) # press, turn (arg = wheel; dir(arg) = +1/-1), aligned, open, close, closed, ...

enum Phase { CLOSED, OPENING, OPEN, CLOSING, STARTING }

const NOTCHES := 6
const COUPLING: Array[Array] = [[1, -1, 0], [-1, 1, -1], [0, -1, 1]] # [knob][wheel]: notches turned by one press
## Scrambles: how many presses of each knob solve the box (2-4 taps, a different feel each time).
const SCRAMBLES: Array[Array] = [[1, 0, 1], [0, 2, 1], [2, 1, 0], [1, 1, 1], [0, 1, 2], [2, 0, 0], [1, 2, 0], [0, 0, 2]]

const OPEN_S := 1.1 # the lid swings up (the first part is the latch popping)
const HOLD_S := 4.5 # open, light spilling out, before it closes by itself
const CLOSE_S := 0.8
## The start transition. Landings: the wheels click into place one after another, then the latch, the lid, the push.
const START_SPIN_S := 0.34 # each wheel spins this long before it lands
const START_LATCH_T := 0.95
const START_LID_S := 0.7
const START_GOTO_T := 1.35 # the loading flow starts here (its own 0.45 s fade ends at START_END_T)
const START_END_T := 1.8
## When the six start events happen: three landings (click, click, click), the latch, the goto, the end.
const START_TIMES: Array[float] = [0.34, 0.54, 0.74, START_LATCH_T, START_GOTO_T, START_END_T]
const SKIP_S := 0.25 # a tap during the transition: black in this long, the loading flow starts at once

var wheels: Array[int] = [0, 0, 0] # notches from the front mark
var phase: Phase = Phase.CLOSED
var phase_t := 0.0
var presses := 0 # since the last scramble
var opens := 0 # how often it opened (touch)
var start_t := 0.0
var goto_count := 0
var skipped := false
var skip_t := 0.0
var reduced := false # Settings "reduce_motion": the start is a short fade only

var _scramble_i := 0
var _start_i := 0 # next entry of START_TIMES


func _init() -> void:
	scramble()


## Wheels a few presses from solved (the next entry of SCRAMBLES; `which` < 0 continues the cycle).
func scramble(which: int = -1) -> void:
	if which < 0:
		which = _scramble_i
		_scramble_i = (_scramble_i + 1) % SCRAMBLES.size()
	var p: Array = SCRAMBLES[which % SCRAMBLES.size()]
	for w in 3:
		var v := 0
		for k in 3:
			v -= int(p[k]) * int(COUPLING[k][w])
		wheels[w] = posmod(v, NOTCHES)
	presses = 0


func is_aligned() -> bool:
	return wheels[0] == 0 and wheels[1] == 0 and wheels[2] == 0


## The direction wheel w turns when knob k is pressed: +1 forward, -1 back, 0 not at all.
static func dir(knob: int, wheel: int) -> int:
	return int(COUPLING[knob][wheel])


## The fewest presses that align the wheels from `w` (unique mod 6, so the minimum is the solution itself).
static func distance_of(w: Array) -> int:
	var best := 99
	for a in NOTCHES:
		for b in NOTCHES:
			for c in NOTCHES:
				if best <= a + b + c:
					continue
				var ok := true
				for i in 3:
					var v := int(w[i]) + a * int(COUPLING[0][i]) + b * int(COUPLING[1][i]) + c * int(COUPLING[2][i])
					if posmod(v, NOTCHES) != 0:
						ok = false
						break
				if ok:
					best = a + b + c
	return best


func distance() -> int:
	return distance_of(wheels)


## A knob for the idle fidget: one whose press does not solve the box and keeps it within a few presses of solved
## (so a player who starts right after a fidget is not lost). `r` is a random number in [0, 1); -1 when none fits.
func pick_idle_knob(r: float) -> int:
	var ok: Array[int] = []
	for k in 3:
		var after: Array = []
		for w in 3:
			after.append(posmod(wheels[w] + dir(k, w), NOTCHES))
		var d := distance_of(after)
		if d > 0 and d <= 6:
			ok.append(k)
	if ok.is_empty():
		return -1
	return ok[mini(int(r * ok.size()), ok.size() - 1)]


func can_press() -> bool:
	return phase == Phase.CLOSED


## Press knob k. Returns false when the box is busy. Emits press, turn (per wheel), then aligned/open when solved.
func press(k: int) -> bool:
	if phase != Phase.CLOSED or k < 0 or k > 2:
		return false
	presses += 1
	event.emit(&"press", k)
	for w in 3:
		var d := dir(k, w)
		if d != 0:
			wheels[w] = posmod(wheels[w] + d, NOTCHES)
			event.emit(&"turn", w)
	if is_aligned():
		event.emit(&"aligned", presses)
		phase = Phase.OPENING
		phase_t = 0.0
		opens += 1
		event.emit(&"latch", 0)
	return true


## A tap that is not on a knob: closes an open lid early. Returns true if it did something.
func tap_anywhere() -> bool:
	if phase == Phase.OPEN:
		_begin_close()
		return true
	if phase == Phase.STARTING:
		skip()
		return true
	return false


func is_starting() -> bool:
	return phase == Phase.STARTING


## New Game / Continue: starts the transition (a short fade only with reduce_motion).
func begin_start(reduce_motion: bool) -> void:
	if phase == Phase.STARTING:
		return
	phase = Phase.STARTING
	reduced = reduce_motion
	start_t = 0.0
	_start_i = 0
	skipped = false
	skip_t = 0.0
	event.emit(&"start", 1 if reduce_motion else 0)
	if reduce_motion:
		_send_goto()


## A tap during the transition: the loading flow starts now (once) and the screen is black in SKIP_S.
func skip() -> void:
	if phase != Phase.STARTING or skipped:
		return
	skipped = true
	skip_t = 0.0
	event.emit(&"skip", 0)
	_send_goto()


func _send_goto() -> void:
	if goto_count == 0:
		goto_count = 1
		event.emit(&"goto", 0)


## 0..1: how black the screen is because of the transition (the start's own fade, or the skip's).
func fade() -> float:
	if phase != Phase.STARTING:
		return 0.0
	var f := 0.0
	if reduced:
		f = 0.0 # the loading flow's own fade does the work
	else:
		f = smoothstep(START_GOTO_T + 0.1, START_END_T, start_t)
	if skipped:
		f = maxf(f, smoothstep(0.0, SKIP_S, skip_t))
	return f


func _begin_close() -> void:
	phase = Phase.CLOSING
	phase_t = 0.0
	scramble() # behind the lid, which hides the wheels' top side while it is up
	event.emit(&"close", 0)


func tick(delta: float) -> void:
	match phase:
		Phase.OPENING:
			phase_t += delta
			if phase_t >= OPEN_S:
				phase = Phase.OPEN
				phase_t = 0.0
				event.emit(&"open", 0)
		Phase.OPEN:
			phase_t += delta
			if phase_t >= HOLD_S:
				_begin_close()
		Phase.CLOSING:
			phase_t += delta
			if phase_t >= CLOSE_S:
				phase = Phase.CLOSED
				phase_t = 0.0
				event.emit(&"closed", 0)
		Phase.STARTING:
			start_t += delta
			if skipped:
				skip_t += delta
			if reduced:
				return
			while _start_i < 6:
				if start_t < START_TIMES[_start_i]:
					break
				if skipped and _start_i != 5:
					_start_i += 1 # no clicks behind the fade
					continue
				_start_event(_start_i)
				_start_i += 1


func _start_event(i: int) -> void:
	if i < 3:
		wheels[i] = 0
		event.emit(&"land", i)
	elif i == 3:
		event.emit(&"latch", 1)
	elif i == 4:
		_send_goto()
	else:
		event.emit(&"start_done", 0)
