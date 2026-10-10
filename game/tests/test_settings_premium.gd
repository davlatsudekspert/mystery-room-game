extends TestBase
## Settings persistence/validation, save system atomicity, premium access rules.


func test_settings_persist_and_validate() -> void:
	var s: Node = load("res://src/autoload/settings.gd").new()
	s.path = "user://test_settings.cfg"
	s.load_settings()
	s.set_value("music_volume", 0.3)
	s.set_value("text_scale", 9.0)
	s.set_value("haptics", "not a bool")
	s.set_value("no_such_key", 1)
	var s2: Node = load("res://src/autoload/settings.gd").new()
	s2.path = "user://test_settings.cfg"
	s2.load_settings()
	eq(s2.get_value("music_volume"), 0.3, "persisted")
	eq(s2.get_value("text_scale"), 1.5, "clamped")
	eq(s2.get_value("haptics"), true, "wrong type rejected")
	DirAccess.remove_absolute("user://test_settings.cfg")
	s.free()
	s2.free()


func test_save_system_atomic_and_backup() -> void:
	var ss: Node = load("res://src/autoload/save_system.gd").new()
	ss.save_path = "user://test_save.json"
	ss.delete_game()
	check(ss.load_game().is_empty(), "no save initially")
	check(ss.save_game({"chapter": "ch1", "logic": {"a": 1}}), "save ok")
	check(ss.save_game({"chapter": "ch1", "logic": {"a": 2}}), "second save ok")
	eq(int(ss.load_game()["logic"]["a"]), 2, "latest wins")
	var f := FileAccess.open("user://test_save.json", FileAccess.WRITE)
	f.store_string("{corrupt")
	f.close()
	eq(int(ss.load_game().get("logic", {}).get("a", -1)), 1, "falls back to .bak when main file is corrupt")
	ss.delete_game()
	check(ss.load_game().is_empty(), "deleted")
	ss.free()


func test_game_state_save_continue_cycle() -> void:
	SaveSystem.save_path = "user://test_cycle.json"
	check(GameState.start_new("ch1"), "start ch1")
	var l := GameState.logic as Lab7Logic
	l.take("notebook")
	for _i in 30:
		Lab7Solver.step(l, "leave_lens")
	GameState.save_now()
	var snapshot := JSON.stringify(l.to_dict())
	check(GameState.continue_saved(), "continue")
	eq(JSON.stringify(GameState.logic.to_dict()), snapshot, "identical state after continue")
	SaveSystem.delete_game()
	SaveSystem.save_path = SaveSystem.SAVE_PATH


## Players get their own answers per game (docs/VARIANTS.md); Continue keeps them.
func test_new_games_draw_their_own_variant() -> void:
	SaveSystem.save_path = "user://test_variant.json"
	var keep: int = GameState.variant_seed
	GameState.variant_seed = -1
	var fresh: Node = load("res://src/autoload/game_state.gd").new()
	eq(fresh.get("variant_seed"), -1, "players' default is a random seed")
	fresh.free()
	for id: String in ["ch1", "ch2"]:
		var seeds := {}
		for _i in 6:
			check(GameState.start_new(id), "start " + id)
			seeds[int(GameState.logic.state["seed"])] = true
		check(seeds.size() >= 5 and not seeds.has(0), "%s: every new game draws a new seed (%d distinct of 6)" % [id,
			seeds.size()])
		var snapshot := JSON.stringify(GameState.logic.to_dict())
		check(GameState.continue_saved(), "continue " + id)
		eq(JSON.stringify(GameState.logic.to_dict()), snapshot, id + ": continue keeps the same answers")
	GameState.variant_seed = keep
	SaveSystem.delete_game()
	SaveSystem.save_path = SaveSystem.SAVE_PATH


func test_premium_rules() -> void:
	var p: Node = Premium
	p.path = "user://test_ent.cfg"
	p.revoke_all_for_tests()
	check(not p.REAL_PAYMENTS_ENABLED, "real payments must stay disabled")
	check(not p.tester_build(), "only exports with the beta_unlock feature open paid chapters for testers")
	check(p.can_play("ch1"), "chapter 1 is free")
	check(not p.can_play("ch2"), "chapter 2 is released but not owned")
	check(not p.can_play("ch3"), "chapter 3 is not released")
	check(not p.can_play("nope"), "unknown chapter")
	eq(p.provider.store_name(), "mock", "debug builds use the mock store")
	p.purchase("full_game")
	check(p.has_entitlement("full_game"), "mock purchase grants entitlement")
	check(p.can_play("ch2"), "the purchase opens chapter 2")
	check(not p.can_play("ch3"), "still unreleased even if owned")
	p.revoke_all_for_tests()
	p.restore_purchases()
	check(p.has_entitlement("full_game"), "restore re-grants from provider")
	p.revoke_all_for_tests()
	DirAccess.remove_absolute("user://test_ent.cfg")
	p.path = p.PATH


func test_hint_escalation() -> void:
	GameState.start_new("ch1")
	var h1 := GameState.next_hint()
	var h2 := GameState.next_hint()
	var h3 := GameState.next_hint()
	var h4 := GameState.next_hint()
	eq([h1["level"], h2["level"], h3["level"], h4["level"]], [1, 2, 3, 3], "escalates then stays at answer")
	eq(h1["goal"], "notebook")
	(GameState.logic as Lab7Logic).take("notebook")
	eq(GameState.next_hint()["level"], 1, "new goal restarts at nudge")
	SaveSystem.delete_game()


## A session that dies while loading a scene is remembered (CrashGuard); a clean pause or a crash later in play is not
## a loading crash, so only the first turns safe graphics on at the next launch.
func test_crash_guard_stages() -> void:
	CrashGuard.file_path = "user://test_session_stage_%d.txt" % OS.get_process_id()
	CrashGuard.mark("load:lab7")
	eq(CrashGuard.read_previous(), "load:lab7", "a session that died while loading is remembered")
	check(CrashGuard.crashed_while_loading(), "a loading crash")
	CrashGuard.mark("draw:lab7")
	eq(CrashGuard.read_previous(), "draw:lab7", "a session that died drawing a new scene's first frames is remembered")
	check(CrashGuard.crashed_while_loading(), "drawing the first frames counts as loading")
	CrashGuard.mark("play:lab7")
	CrashGuard.paused()
	eq(CrashGuard.read_previous(), "", "a clean pause is not a crash")
	CrashGuard.resumed()
	eq(CrashGuard.read_previous(), "play:lab7", "after resuming, the stage is back")
	check(not CrashGuard.crashed_while_loading(), "a crash during play keeps the graphics")
	CrashGuard.mark("menu")
	eq(CrashGuard.read_previous(), "", "the main menu is a clean stage")
	DirAccess.remove_absolute(CrashGuard.file_path)
	CrashGuard.file_path = CrashGuard.PATH
	CrashGuard.previous = ""


## Safe graphics keep every light but drop positional shadows, reflection probes and particles.
func test_safe_graphics_simplify_a_scene() -> void:
	var scene := Node3D.new()
	var omni := OmniLight3D.new()
	omni.shadow_enabled = true
	var spot := SpotLight3D.new()
	spot.shadow_enabled = true
	var sun := DirectionalLight3D.new()
	sun.shadow_enabled = true
	var probe := ReflectionProbe.new()
	var dust := GPUParticles3D.new()
	var we := WorldEnvironment.new()
	we.environment = Environment.new()
	we.environment.ambient_light_energy = 0.4
	for n: Node in [omni, spot, sun, probe, dust, we]:
		scene.add_child(n)
	var vp := SubViewport.new()
	vp.msaa_3d = Viewport.MSAA_4X
	scene.add_child(vp)
	var decal := Decal.new()
	scene.add_child(decal)
	we.environment.glow_enabled = true
	SceneManager.simplify_graphics(scene, 1)
	eq(vp.msaa_3d, Viewport.MSAA_DISABLED, "level 1: no MSAA in off-screen views")
	check(omni.shadow_enabled and probe.visible and dust.visible, "level 1 keeps shadows, probes and particles")
	SceneManager.simplify_graphics(scene, 2)
	SceneManager.simplify_graphics(scene, 2) # twice: the ambient boost is applied once
	check(not omni.shadow_enabled and not spot.shadow_enabled, "level 2: no positional shadows")
	check(sun.shadow_enabled and omni.visible and spot.visible, "every light stays; the sun keeps its shadow")
	check(not probe.visible and not dust.visible, "no reflection probe, no particles")
	eq(snappedf(we.environment.ambient_light_energy, 0.001), 0.6, "ambient raised once to make up for the probe")
	check(decal.visible and we.environment.glow_enabled, "level 2 keeps decals and glow")
	SceneManager.simplify_graphics(scene, 3)
	check(not decal.visible and not we.environment.glow_enabled and not sun.shadow_enabled, "level 3: no decals, glow or sun shadow")
	scene.free()


## Each crash while loading raises the safe level by one at the next launch, up to the maximum; a new epoch
## (a build that changes what the levels do) starts again from zero.
func test_safe_level_escalates() -> void:
	var keep := [Settings.get_value("safe_graphics"), Settings.get_value("safe_level"), Settings.get_value("safe_epoch")]
	Settings.set_value("safe_epoch", 0)
	Settings.set_value("safe_graphics", true)
	Settings.set_value("safe_level", 3)
	CrashGuard.previous = ""
	check(not CrashGuard.update_safe_level(), "no crash: no change")
	eq(CrashGuard.safe_level(), 0, "a new epoch resets the level and the old automatic switch")
	CrashGuard.previous = "load:lab7 wall_safe"
	for expect in [1, 2, 3]:
		check(CrashGuard.update_safe_level(), "a crash while loading raises the level")
		eq(CrashGuard.safe_level(), expect, "level after %d crashes" % expect)
	check(not CrashGuard.update_safe_level(), "never above the maximum")
	CrashGuard.previous = "play:lab7"
	check(not CrashGuard.update_safe_level(), "a crash during play does not change the graphics")
	CrashGuard.previous = ""
	Settings.set_value("safe_graphics", keep[0])
	Settings.set_value("safe_level", keep[1])
	Settings.set_value("safe_epoch", keep[2])


## iPhones start without MSAA (Metal crashed drawing the room's first frames with it); other platforms keep it.
func test_ios_starts_without_msaa() -> void:
	eq(CrashGuard.min_level_for("iOS"), 1, "iOS starts at safe level 1 (no MSAA)")
	eq(CrashGuard.min_level_for("Android"), 0, "Android keeps MSAA")
	eq(CrashGuard.min_level_for("Linux"), 0, "desktop and QA keep MSAA")
