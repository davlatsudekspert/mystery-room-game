class_name UndergroundTones
extends Node
## Pitched sounds of Chapter 3, synthesized once at runtime (original, no recorded assets): the seven Choir tubes
## (a longer tube rings lower), Leyla's four tuning crystals (a smaller crystal rings higher) and the chord.
## Each tone is a short decaying sum of partials in an AudioStreamWAV, cached by pitch and kind.

const RATE := 22050
## Meter reading 1..7 (reading 1 = the longest tube): a pentatonic run, so the full Choir is a calm cluster.
const TUBE_HZ: Array[float] = [196.0, 220.0, 261.63, 293.66, 329.63, 392.0, 440.0]
## Crystal size 1..4 (1 = the smallest = the highest).
const CRYSTAL_HZ: Array[float] = [1318.5, 1046.5, 880.0, 783.99]

static var _cache: Dictionary = {}
var _players: Array[AudioStreamPlayer] = []


func _ready() -> void:
	for i in 8:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)


func tube(reading: int, volume_db: float = -6.0) -> void:
	if reading >= 1 and reading <= 7:
		_play(stream(TUBE_HZ[reading - 1], "tube"), volume_db)


func crystal(size: int, volume_db: float = -8.0) -> void:
	if size >= 1 and size <= 4:
		_play(stream(CRYSTAL_HZ[size - 1], "crystal"), volume_db)


## All seven tubes at once (the hall starts, the hammer rings the tuned Choir); `clean` false = a clash.
func chord(clean: bool, volume_db: float = -10.0) -> void:
	for r in range(1, 8):
		var hz: float = TUBE_HZ[r - 1] * (1.0 if clean else (1.0 + 0.045 * ((r * 37) % 5 - 2)))
		_play(stream(hz, "tube"), volume_db)


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


## A bell-like tone: a tube has the inharmonic partials of a chime, a crystal a glassy, nearly harmonic ring.
static func stream(hz: float, kind: String) -> AudioStreamWAV:
	var key := "%s:%.2f" % [kind, hz]
	if _cache.has(key):
		return _cache[key]
	var partials: Array = [[1.0, 1.0, 1.6], [2.76, 0.45, 0.9], [5.40, 0.22, 0.45], [8.93, 0.08, 0.25]] \
		if kind == "tube" else [[1.0, 1.0, 1.1], [2.0, 0.25, 0.6], [3.01, 0.12, 0.35], [4.2, 0.05, 0.2]]
	var seconds := 2.2 if kind == "tube" else 1.4
	var n := int(RATE * seconds)
	var data := PackedByteArray()
	data.resize(n * 2)
	var attack := int(RATE * 0.004)
	for i in n:
		var t := float(i) / RATE
		var v := 0.0
		for p: Array in partials:
			v += float(p[1]) * exp(-t / float(p[2])) * sin(TAU * hz * float(p[0]) * t)
		v *= 0.38 * minf(1.0, float(i) / attack)
		data.encode_s16(i * 2, int(clampf(v, -1.0, 1.0) * 32767.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = RATE
	w.stereo = false
	w.data = data
	_cache[key] = w
	return w
