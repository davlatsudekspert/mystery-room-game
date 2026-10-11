extends Node
## Audio buses, pooled SFX, crossfading music and layered ambience. Missing files are skipped silently.

const BUSES: Array[String] = ["Music", "Ambience", "SFX", "UI"]
const ROOT := "res://assets/audio/%s/%s.ogg"
const POOL_SIZE := 10

var _cache: Dictionary = {}
var _pool: Array[AudioStreamPlayer] = []
var _music: Array[AudioStreamPlayer] = []
var _music_idx := 0
var _music_name := ""
var _amb: Dictionary = {} # name -> AudioStreamPlayer
var _loops: Dictionary = {} # sfx_loop name -> AudioStreamPlayer
var sfx_count := 0 # one-shots played so far (QA: "did that tap make a sound?")
var last_sfx := ""


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for b in BUSES:
		if AudioServer.get_bus_index(b) == -1:
			AudioServer.add_bus()
			var i := AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, b)
			AudioServer.set_bus_send(i, "Master")
	for i in POOL_SIZE:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_pool.append(p)
	for i in 2:
		var m := AudioStreamPlayer.new()
		m.bus = "Music"
		m.volume_db = -80.0
		add_child(m)
		_music.append(m)
	Settings.changed.connect(func(_k: String) -> void: apply_volumes())
	apply_volumes()


func apply_volumes() -> void:
	_set_bus("Music", Settings.get_value("music_volume"))
	_set_bus("Ambience", Settings.get_value("ambience_volume"))
	_set_bus("SFX", Settings.get_value("sfx_volume"))
	_set_bus("UI", Settings.get_value("sfx_volume"))


func _set_bus(bus: String, linear: float) -> void:
	var i := AudioServer.get_bus_index(bus)
	if i >= 0:
		AudioServer.set_bus_volume_db(i, linear_to_db(maxf(linear, 0.0001)))
		AudioServer.set_bus_mute(i, linear <= 0.001)


func stream(category: String, name: String) -> AudioStream:
	var key := category + "/" + name
	if not _cache.has(key):
		var path := ROOT % [category, name]
		_cache[key] = load(path) if ResourceLoader.exists(path) else null
	return _cache[key]


func sfx(name: String, volume_db: float = 0.0, pitch: float = 1.0, bus: String = "SFX") -> void:
	var s := once_stream(name)
	if s == null:
		return
	sfx_count += 1
	last_sfx = name
	for p in _pool:
		if not p.playing:
			p.stream = s
			p.volume_db = volume_db
			p.pitch_scale = pitch
			p.bus = bus
			p.play()
			return


## The stream sfx() plays: a file imported as a loop (tape_hiss) is played once here. A pooled one-shot player
## never stops a loop, and the pool outlives every scene: on a phone the tape hiss of the Chapter 2 cliffhanger
## kept playing over the menu and every later chapter. Sounds that should loop go through sfx_loop().
func once_stream(name: String) -> AudioStream:
	var s := stream("sfx", name)
	if s == null or not loops(s):
		return s
	var key := "sfx/%s#once" % name
	if not _cache.has(key):
		push_warning("AudioManager.sfx(\"%s\"): the file loops; played once. Use sfx_loop() for a loop." % name)
		var once := s.duplicate() as AudioStream
		_set_loop(once, false)
		_cache[key] = once
	return _cache[key]


static func loops(s: AudioStream) -> bool:
	if s is AudioStreamOggVorbis:
		return (s as AudioStreamOggVorbis).loop
	if s is AudioStreamMP3:
		return (s as AudioStreamMP3).loop
	if s is AudioStreamWAV:
		return (s as AudioStreamWAV).loop_mode != AudioStreamWAV.LOOP_DISABLED
	return false


static func _set_loop(s: AudioStream, on: bool) -> void:
	if s is AudioStreamOggVorbis:
		(s as AudioStreamOggVorbis).loop = on
	elif s is AudioStreamMP3:
		(s as AudioStreamMP3).loop = on
	elif s is AudioStreamWAV:
		(s as AudioStreamWAV).loop_mode = AudioStreamWAV.LOOP_FORWARD if on else AudioStreamWAV.LOOP_DISABLED


## A sound effect that loops until it is turned off (the tape hiss under a recording): `on` starts it or changes its
## volume, `on` false fades it out. Every loop also stops when the scene changes (SceneManager.goto).
func sfx_loop(name: String, on: bool, volume_db: float = 0.0, pitch: float = 1.0, fade: float = 0.3) -> void:
	if on and not _loops.has(name):
		var s := stream("sfx", name)
		if s == null:
			return
		_set_loop(s, true)
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		p.stream = s
		p.pitch_scale = pitch
		p.volume_db = -60.0
		add_child(p)
		p.play()
		_loops[name] = p
		create_tween().tween_property(p, "volume_db", volume_db, maxf(fade, 0.01))
	elif not on and _loops.has(name):
		var p: AudioStreamPlayer = _loops[name]
		_loops.erase(name)
		var tw := create_tween()
		tw.tween_property(p, "volume_db", -60.0, maxf(fade, 0.01))
		tw.tween_callback(p.queue_free)
	elif on and _loops.has(name):
		create_tween().tween_property(_loops[name], "volume_db", volume_db, maxf(fade, 0.01))


func sfx_loop_playing(name: String) -> bool:
	return _loops.has(name)


## QA: the sound effects still looping (sfx_loop names, and any pooled player holding a loop, which must not happen).
func looping_sfx() -> Array[String]:
	var out: Array[String] = []
	for n: String in _loops:
		out.append(n)
	for p in _pool:
		if p.playing and p.stream != null and loops(p.stream):
			out.append("pool:" + p.stream.resource_path.get_file())
	return out


func stop_sfx_loops(fade: float = 0.3) -> void:
	for n: String in _loops.keys():
		sfx_loop(n, false, 0.0, 1.0, fade)


func ui(name: String = "ui_tap") -> void:
	sfx(name, -4.0, 1.0, "UI")


func sfx_at(name: String, pos: Vector3, parent: Node, volume_db: float = 0.0, pitch: float = 1.0) -> void:
	var s := stream("sfx", name)
	if s == null or parent == null:
		return
	var p := AudioStreamPlayer3D.new()
	p.stream = s
	p.bus = "SFX"
	p.volume_db = volume_db
	p.pitch_scale = pitch
	p.unit_size = 4.0
	parent.add_child(p)
	p.global_position = pos
	p.finished.connect(p.queue_free)
	p.play()


func music(name: String, fade: float = 2.0) -> void:
	if name == _music_name:
		return
	_music_name = name
	var s := stream("music", name)
	var old := _music[_music_idx]
	_music_idx = 1 - _music_idx
	var nw := _music[_music_idx]
	var tw := create_tween().set_parallel(true)
	tw.tween_property(old, "volume_db", -80.0, fade)
	if s != null:
		if s is AudioStreamOggVorbis:
			(s as AudioStreamOggVorbis).loop = true
		nw.stream = s
		nw.volume_db = -40.0
		nw.play()
		tw.tween_property(nw, "volume_db", 0.0, fade)


func stop_music(fade: float = 2.0) -> void:
	_music_name = ""
	for m in _music:
		create_tween().tween_property(m, "volume_db", -80.0, fade)


func ambience(name: String, on: bool, volume_db: float = 0.0, fade: float = 2.0) -> void:
	if on and not _amb.has(name):
		var s := stream("ambience", name)
		if s == null:
			return
		if s is AudioStreamOggVorbis:
			(s as AudioStreamOggVorbis).loop = true
		var p := AudioStreamPlayer.new()
		p.bus = "Ambience"
		p.stream = s
		p.volume_db = -60.0
		add_child(p)
		p.play()
		_amb[name] = p
		create_tween().tween_property(p, "volume_db", volume_db, fade)
	elif not on and _amb.has(name):
		var p: AudioStreamPlayer = _amb[name]
		_amb.erase(name)
		var tw := create_tween()
		tw.tween_property(p, "volume_db", -60.0, fade)
		tw.tween_callback(p.queue_free)
	elif on and _amb.has(name):
		create_tween().tween_property(_amb[name], "volume_db", volume_db, fade)


func stop_all_ambience(fade: float = 1.5) -> void:
	for n: String in _amb.keys():
		ambience(n, false, 0.0, fade)


func haptic(ms: int = 20) -> void:
	if Settings.get_value("haptics") and OS.has_feature("mobile"):
		Input.vibrate_handheld(ms)
