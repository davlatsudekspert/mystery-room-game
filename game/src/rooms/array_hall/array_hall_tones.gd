class_name ArrayHallTones
extends Node
## Pitched sounds of Chapter 4, synthesized once at runtime (original, no recorded assets): the Core's held hum, the beat
## between the keeper knob's note and the Core's own (two sines, so the ear hears what the oscillograph draws), the chime
## at each fold of the beam, the lights rising through the oculus and the chronometer's ratchet.
## Everything is a short AudioStreamWAV cached by its parameters; the hum and the beats loop.

const RATE := 22050
## The Core's own note and the beat loop: 4 s long, the keeper's note is 0.5 Hz × distance above the Core's, so every loop
## holds a whole number of beats and repeats without a click.
const CORE_HZ := 220.0
const LOOP_SECONDS := 4.0
## The fold chimes climb a pentatonic run, one per tower and the Core.
const CHIME_HZ: Array[float] = [440.0, 523.25, 659.25, 783.99, 987.77]
const RISE_HZ: Array[float] = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5, 1174.7]

static var _cache: Dictionary = {}
var _players: Array[AudioStreamPlayer] = []
var _hum: AudioStreamPlayer
var _beat: AudioStreamPlayer
var _beat_d := -1
var _hum_pitch := 1.0


func _ready() -> void:
	for i in 6:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_hum = AudioStreamPlayer.new()
	_hum.bus = "Ambience"
	_hum.volume_db = -80.0
	add_child(_hum)
	_beat = AudioStreamPlayer.new()
	_beat.bus = "SFX"
	_beat.volume_db = -80.0
	add_child(_beat)


# ---------------------------------------------------------------- the Core's hum and the beat
## The Core's held note, softly, while the hall is powered. `falling` is the Leyla path: the note sinks slowly.
func hum(on: bool, volume_db: float = -22.0, falling: bool = false) -> void:
	if not on:
		if _hum.playing:
			create_tween().tween_property(_hum, "volume_db", -80.0, 1.5).finished.connect(_hum.stop)
		return
	if not _hum.playing:
		_hum.stream = loop_stream(CORE_HZ * 0.5, "hum")
		_hum.pitch_scale = 1.0
		_hum.volume_db = -80.0
		_hum.play()
	create_tween().tween_property(_hum, "volume_db", volume_db, 2.0)
	if falling:
		create_tween().tween_property(_hum, "pitch_scale", 0.94, 40.0)


func hum_level(volume_db: float) -> void:
	if _hum.playing:
		create_tween().tween_property(_hum, "volume_db", volume_db, 1.2)


## The keeper knob against the Core: distance d (0 = locked) → a loop with d beats per 2 s. 0 = knob off.
func beat(keeper: int, target: int) -> void:
	if keeper <= 0:
		_beat_d = -1
		if _beat.playing:
			create_tween().tween_property(_beat, "volume_db", -80.0, 0.3).finished.connect(_beat.stop)
		return
	var d := absi(keeper - target)
	if d == _beat_d and _beat.playing:
		return
	_beat_d = d
	_beat.stream = beat_stream(d)
	_beat.volume_db = -17.0 if d > 0 else -13.0
	if not _beat.playing:
		_beat.play()


func beat_stream(d: int) -> AudioStreamWAV:
	var key := "beat:%d" % d
	if _cache.has(key):
		return _cache[key]
	var n := int(RATE * LOOP_SECONDS)
	var data := PackedByteArray()
	data.resize(n * 2)
	var f1 := CORE_HZ
	var f2 := CORE_HZ + 0.5 * d # whole beats per loop: 2 d
	for i in n:
		var t := float(i) / RATE
		var v := 0.5 * (sin(TAU * f1 * t) + sin(TAU * f2 * t)) * 0.34
		v += 0.05 * (sin(TAU * f1 * 2.0 * t) + sin(TAU * f2 * 2.0 * t))
		data.encode_s16(i * 2, int(clampf(v, -1.0, 1.0) * 32767.0))
	var w := _wav(data, true, n)
	_cache[key] = w
	return w


# ---------------------------------------------------------------- one-shots
func chime(index: int, volume_db: float = -9.0) -> void:
	var hz: float = CHIME_HZ[clampi(index, 0, CHIME_HZ.size() - 1)]
	_play(stream(hz, "glass"), volume_db)


## A light leaving the Core: a high bell from the pentatonic set, randomly chosen but never the same twice in a row.
func rise_note(i: int, volume_db: float = -16.0) -> void:
	_play(stream(RISE_HZ[(i * 3 + i / 7) % RISE_HZ.size()] * (2.0 if i % 5 == 4 else 1.0), "glass"), volume_db)


## The keeper's held chord when the notes lock: the Core's note and its fifth, long.
func chord(volume_db: float = -10.0) -> void:
	_play(stream(CORE_HZ, "glass"), volume_db)
	_play(stream(CORE_HZ * 1.5, "glass"), volume_db - 3.0)
	_play(stream(CORE_HZ * 2.0, "glass"), volume_db - 5.0)


## The chronometer's ratchet: a run of dry ticks, `count` of them, down in pitch for winding back.
func ratchet(count: int, down: bool = false, volume_db: float = -10.0) -> void:
	_play(stream(2400.0 if not down else 1700.0, "tick%d" % clampi(count, 1, 8)), volume_db)


## A low swell under the reversal and the rise (a held fifth that grows and fades).
func swell(seconds: float = 6.0, hz: float = 110.0, volume_db: float = -12.0) -> void:
	var s := stream(hz, "swell%d" % int(seconds))
	_play(s, volume_db)


func _play(s: AudioStream, volume_db: float) -> void:
	for p in _players:
		if not p.playing:
			p.stream = s
			p.volume_db = volume_db
			p.play()
			return
	_players[0].stream = s
	_players[0].volume_db = volume_db
	_players[0].play()


static func _wav(data: PackedByteArray, loop: bool, frames: int) -> AudioStreamWAV:
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = RATE
	w.stereo = false
	w.data = data
	if loop:
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_begin = 0
		w.loop_end = frames
	return w


## A looping soft tone (the hum): a few harmonics at hz, 4 s long.
static func loop_stream(hz: float, kind: String) -> AudioStreamWAV:
	var key := "loop:%s:%.2f" % [kind, hz]
	if _cache.has(key):
		return _cache[key]
	var n := int(RATE * LOOP_SECONDS)
	var data := PackedByteArray()
	data.resize(n * 2)
	for i in n:
		var t := float(i) / RATE
		var v := 0.50 * sin(TAU * hz * t) + 0.28 * sin(TAU * hz * 2.0 * t + 0.4) + 0.14 * sin(TAU * hz * 3.0 * t + 1.1) \
			+ 0.07 * sin(TAU * hz * 4.0 * t)
		v *= 0.55 * (0.92 + 0.08 * sin(TAU * t / LOOP_SECONDS * 2.0))
		data.encode_s16(i * 2, int(clampf(v, -1.0, 1.0) * 32767.0))
	var w := _wav(data, true, n)
	_cache[key] = w
	return w


## A decaying bell/glass tone, a ratchet tick run or a swell, by `kind`.
static func stream(hz: float, kind: String) -> AudioStreamWAV:
	var key := "%s:%.2f" % [kind, hz]
	if _cache.has(key):
		return _cache[key]
	var seconds := 2.4
	var n: int
	var data := PackedByteArray()
	if kind.begins_with("tick"):
		var count := int(kind.substr(4))
		seconds = 0.12 * count + 0.1
		n = int(RATE * seconds)
		data.resize(n * 2)
		for i in n:
			var t := float(i) / RATE
			var local := fmod(t, 0.12)
			var v := exp(-local / 0.008) * sin(TAU * hz * local) * 0.55
			data.encode_s16(i * 2, int(clampf(v, -1.0, 1.0) * 32767.0))
	elif kind.begins_with("swell"):
		seconds = float(kind.substr(5))
		n = int(RATE * seconds)
		data.resize(n * 2)
		for i in n:
			var t := float(i) / RATE
			var env := pow(sin(PI * t / seconds), 1.6)
			var v := env * 0.4 * (sin(TAU * hz * t) + 0.6 * sin(TAU * hz * 1.5 * t) + 0.3 * sin(TAU * hz * 2.0 * t))
			data.encode_s16(i * 2, int(clampf(v, -1.0, 1.0) * 32767.0))
	else:
		n = int(RATE * seconds)
		data.resize(n * 2)
		var partials: Array = [[1.0, 1.0, 1.4], [2.0, 0.35, 0.9], [3.01, 0.15, 0.5], [4.2, 0.06, 0.25]]
		var attack := int(RATE * 0.004)
		for i in n:
			var t := float(i) / RATE
			var v := 0.0
			for p: Array in partials:
				v += float(p[1]) * exp(-t / float(p[2])) * sin(TAU * hz * float(p[0]) * t)
			v *= 0.34 * minf(1.0, float(i) / attack)
			data.encode_s16(i * 2, int(clampf(v, -1.0, 1.0) * 32767.0))
	var w := _wav(data, false, n)
	_cache[key] = w
	return w
