extends TestBase
## Tap assist (RoomBase.pick / TapAssist): a tap that misses a small 3D control by a few millimetres still means it.
## The test room is a camera 1 m from the origin and a few collider boxes. Positions are worked out in physical
## millimetres on a 400 dpi phone, the way the assist measures them.

const PHONE := {"size": Vector2i(2340, 1080), "dpi": 400.0, "safe": Rect2i(0, 0, 2340, 1080)}


func _mm(mm: float) -> float:
	return mm / UITheme.mm_per_px()


## World metres per screen px at the origin's depth (the camera looks straight at the plane z = 0).
func _m_per_px(r: TapTestRoom) -> float:
	var a := r.cam.unproject_position(Vector3.ZERO)
	var b := r.cam.unproject_position(Vector3(0.1, 0, 0))
	return 0.1 / a.distance_to(b)


## A flat part (thin in depth, so its outline scales exactly with distance) of `mm` on the screen, at the origin
## depth plus `shift` along x/y in mm.
func _part(r: TapTestRoom, name: String, mm: float, dx_mm: float = 0.0, dy_mm: float = 0.0, z: float = 0.0, hs: String = "t") -> StaticBody3D:
	var k := _m_per_px(r)
	var s := _mm(mm) * k
	return r.add_box(Vector3(_mm(dx_mm) * k, -_mm(dy_mm) * k, z), Vector3(s, s, 0.002), name, hs)


func _centre_px(r: TapTestRoom, body: StaticBody3D) -> Vector2:
	return r.cam.unproject_position((body.get_parent() as Node3D).global_position)


func _start() -> TapTestRoom:
	Settings.emulate = PHONE
	var r := TapTestRoom.create()
	await r.attach()
	return r


func _end(r: TapTestRoom) -> void:
	r.dispose()
	await (Engine.get_main_loop() as SceneTree).process_frame
	Settings.emulate = {}


func _part_of(hit: Dictionary) -> String:
	return "" if hit.is_empty() else str((hit["collider"] as Node).get_meta("part", ""))


func test_a_3mm_part_is_hit_by_a_tap_4mm_away_but_not_7mm_away() -> void:
	var r := await _start()
	var lever := _part(r, "IA_lever", 3.0)
	await r.settle()
	var c := _centre_px(r, lever)
	eq(_part_of(r.raycast(c)), "IA_lever", "the exact ray at the centre hits the part")
	eq(_part_of(r.raycast(c + Vector2(_mm(4.0), 0))), "", "the exact ray 4 mm away misses (no assist in raycast)")
	var near := r.pick(c + Vector2(_mm(4.0), 0))
	eq(_part_of(near), "IA_lever", "4 mm away: the assist picks the part")
	check(near.get("assisted", false), "and says it was assisted")
	eq(_part_of(r.pick(c + Vector2(-_mm(4.0), 0))), "IA_lever", "4 mm away on the other side")
	eq(_part_of(r.pick(c + Vector2(0, _mm(4.0)))), "IA_lever", "4 mm below")
	eq(_part_of(r.pick(c + Vector2(_mm(7.0), 0))), "", "7 mm away: out of the finger's reach")
	eq(_part_of(r.pick(c + Vector2(_mm(5.5), _mm(5.5)))), "", "diagonally 7.8 mm away: out of reach")
	# the whole tap path: _on_tap reaches interact() with the part
	r._on_tap(c + Vector2(_mm(4.0), 0))
	eq(r.taps.size(), 1, "a tap 4 mm away operates the part")
	eq(str(r.taps[0]["part"]) if r.taps.size() > 0 else "", "IA_lever", "it is the lever")
	eq(r.assisted_taps, 1, "counted as assisted")
	r._on_tap(c + Vector2(_mm(7.0), 0))
	eq(r.taps.size(), 1, "a tap 7 mm away does nothing")
	await _end(r)


func test_a_tap_at_the_exact_centre_behaves_as_before() -> void:
	var r := await _start()
	var lever := _part(r, "IA_lever", 3.0)
	_part(r, "IA_other", 3.0, 6.0)
	await r.settle()
	var c := _centre_px(r, lever)
	var exact := r.raycast(c)
	var picked := r.pick(c)
	check(picked == exact, "pick == raycast at the centre")
	check(not picked.has("assisted"), "a direct hit is not marked as assisted")
	r._on_tap(c)
	eq(r.assisted_taps, 0, "a direct tap is not counted as assisted")
	eq(str(r.taps[0]["part"]) if r.taps.size() > 0 else "", "IA_lever", "and operates the part it hit")
	await _end(r)


func test_never_through_a_wall() -> void:
	var r := await _start()
	var lever := _part(r, "IA_lever", 3.0)
	# a wall 0.5 m in front of the lever, covering the whole view
	var wall := r.add_box(Vector3(0, 0, 0.5), Vector3(2, 2, 0.05), "", "room")
	await r.settle()
	var c := _centre_px(r, lever)
	for off_mm in [0.0, 2.0, 4.0]:
		var h := r.pick(c + Vector2(_mm(off_mm), 0))
		check(h.get("collider") == wall, "%.0f mm away: the wall is what the finger touched, not the lever behind it" % off_mm)
		check(not h.has("assisted"), "%.0f mm away: not assisted" % off_mm)
	r._on_tap(c + Vector2(_mm(4.0), 0))
	eq(r.assisted_taps, 0, "nothing assisted through the wall")
	for t in r.taps:
		check(str(t["part"]) != "IA_lever", "the lever behind the wall is never operated")
	# the same lever with the wall gone is reachable again
	wall.collision_layer = 0
	await r.settle()
	eq(_part_of(r.pick(c + Vector2(_mm(4.0), 0))), "IA_lever", "without the wall the assist picks the lever")
	await _end(r)


func test_a_part_just_behind_the_surface_it_sits_on_is_still_picked() -> void:
	var r := await _start()
	var lever := _part(r, "IA_lever", 3.0)
	# the panel the lever is mounted on: 3 cm behind the lever's centre, a plain surface of the same object
	var panel := r.add_box(Vector3(0, 0, -0.03), Vector3(2, 2, 0.01), "", "t")
	await r.settle()
	var c := _centre_px(r, lever)
	var tap := c + Vector2(_mm(4.0), 0)
	check(r.raycast(tap)["collider"] == panel, "the exact ray at 4 mm hits the panel")
	eq(_part_of(r.pick(tap)), "IA_lever", "furniture the lever sits on does not hide it")
	# a panel of no object at all (a wall, the floor): the same
	panel.set_meta("hotspot", "")
	eq(_part_of(r.pick(tap)), "IA_lever", "a surface without a hotspot does not protect itself")
	await _end(r)


func test_a_finger_on_another_object_keeps_what_it_touched() -> void:
	var r := await _start()
	var lever := _part(r, "IA_lever", 3.0, 0.0, 0.0, 0.0, "desk")
	# the notebook lying right in front of the drawer: its own surface is what the finger is on
	var notebook := r.add_box(Vector3(0, 0, -0.03), Vector3(2, 2, 0.01), "", "notebook")
	await r.settle()
	var c := _centre_px(r, lever)
	var tap := c + Vector2(_mm(4.0), 0)
	var h := r.pick(tap)
	check(h.get("collider") == notebook and not h.has("assisted"), "a touch on another object's surface stays there")
	r._on_tap(tap)
	eq(r.assisted_taps, 0, "not assisted")
	eq(str(r.taps[0]["hotspot"]) if r.taps.size() > 0 else "", "notebook", "the notebook answers")
	await _end(r)


func test_never_instead_of_a_directly_hit_part() -> void:
	var r := await _start()
	var big := _part(r, "IA_big", 40.0)
	# a small part right beside the big one: 20 mm + 0.5 mm gap from the big part's centre to its near edge
	var small := _part(r, "IA_small", 3.0, 20.0 + 0.5 + 1.5)
	await r.settle()
	var c := _centre_px(r, big)
	# 1 mm inside the big part's right edge: the small part is 1.5 mm away on the screen, the big part is under the finger
	var inside := c + Vector2(_mm(19.0), 0)
	eq(_part_of(r.pick(inside)), "IA_big", "a tap on the big part stays on the big part")
	check(not r.pick(inside).has("assisted"), "and is not assisted")
	# 4.5 mm past the big part's edge: 1 mm from the small part's outline, so the small part is the closest
	var gap := c + Vector2(_mm(24.5), 0)
	eq(_part_of(r.raycast(gap)), "", "the exact ray misses both")
	eq(_part_of(r.pick(gap)), "IA_small", "the nearest on the screen wins: the small part")
	# between them but nearer the big one (no direct hit): the big part is closer
	var between := c + Vector2(_mm(20.2), 0)
	eq(_part_of(r.raycast(between)), "", "in the gap the exact ray hits neither")
	eq(_part_of(r.pick(between)), "IA_big", "in the gap the closer part wins")
	check(small != null, "small part exists")
	await _end(r)


func test_equal_screen_distance_goes_to_the_nearer_part() -> void:
	var r := await _start()
	# two flat parts on one line of sight, the farther one added first; the same size on the screen
	var k := _m_per_px(r)
	var s := _mm(3.0) * k
	var x := _mm(6.0) * k
	var far := r.add_box(Vector3(x * 1.015, 0, 1.0 - 1.015), Vector3(s * 1.015, s * 1.015, 0.002), "IA_far", "t")
	var near := r.add_box(Vector3(x * 0.985, 0, 1.0 - 0.985), Vector3(s * 0.985, s * 0.985, 0.002), "IA_near", "t")
	await r.settle()
	var c := r.cam.unproject_position(Vector3(x, 0, 0))
	var tap := c + Vector2(0, _mm(3.5))
	eq(_part_of(r.raycast(tap)), "", "the exact ray misses both")
	eq(_part_of(r.pick(tap)), "IA_near", "same distance on the screen: the nearer part wins")
	check(far != null and near != null, "both exist")
	await _end(r)


func test_respects_hud_blocked_rects() -> void:
	var r := await _start()
	var lever := _part(r, "IA_lever", 3.0)
	await r.settle()
	var c := _centre_px(r, lever)
	var tap := c + Vector2(_mm(4.0), 0)
	var hud := r.hud as TapTestRoom.FakeHud
	# a HUD button over the lever's centre: the lever is not picked for a touch beside the button
	hud.rects = [Rect2(c - Vector2(_mm(2.0), _mm(2.0)), Vector2(_mm(4.0), _mm(4.0)))]
	eq(_part_of(r.pick(tap)), "", "a part under a HUD control is not picked")
	# a touch inside a HUD control is never assisted
	hud.rects = [Rect2(tap - Vector2(_mm(1.0), _mm(1.0)), Vector2(_mm(2.0), _mm(2.0)))]
	eq(_part_of(r.pick(tap)), "", "a touch under a HUD control is not assisted")
	# a HUD control elsewhere changes nothing
	hud.rects = [Rect2(c + Vector2(_mm(30.0), 0), Vector2(_mm(9.0), _mm(9.0)))]
	eq(_part_of(r.pick(tap)), "IA_lever", "a HUD control elsewhere does not matter")
	await _end(r)


func test_hidden_parts_and_parts_out_of_reach_are_not_picked() -> void:
	var r := await _start()
	var lever := _part(r, "IA_lever", 3.0)
	var c0 := _centre_px(r, lever)
	var far := _part(r, "IA_far_knob", 3.0, 12.0, 0.0, 0.0, "farobj")
	await r.settle()
	var tap := c0 + Vector2(_mm(4.0), 0)
	eq(_part_of(r.pick(tap)), "IA_lever", "baseline: the lever")
	# put away (set_present(false): invisible, no collider): ignored
	r.set_present(lever.get_parent() as Node3D, false)
	await r.settle()
	eq(_part_of(r.pick(tap)), "", "a part that is not present is not picked")
	r.set_present(lever.get_parent() as Node3D, true)
	await r.settle()
	eq(_part_of(r.pick(tap)), "IA_lever", "present again: picked")
	# a part of an object whose own view is another one: a tap near it must not move the camera
	var tap2 := _centre_px(r, far) + Vector2(_mm(4.0), _mm(4.0))
	eq(_part_of(r.pick(tap2)), "IA_far_knob", "in reach: picked")
	r.far_hotspots = ["farobj"]
	eq(_part_of(r.pick(tap2)), "", "out of reach (needs its own view): not picked")
	await _end(r)


func test_picks_are_deterministic() -> void:
	var r := await _start()
	var a := _part(r, "IA_a", 3.0, -3.0, 0.0)
	_part(r, "IA_b", 3.0, 3.0, 0.0)
	_part(r, "IA_c", 3.0, 0.0, 3.0)
	await r.settle()
	var tap := _centre_px(r, a) + Vector2(_mm(2.0), _mm(5.0))
	var first := r.pick(tap)
	check(not first.is_empty(), "something is picked")
	for i in 5:
		var again := r.pick(tap)
		check(again["collider"] == first["collider"] and again["position"] == first["position"], "the same tap, the same pick (%d)" % i)
	await _end(r)


func test_no_parts_no_pick() -> void:
	var r := await _start()
	await r.settle()
	check(r.pick(Vector2(300, 300)).is_empty(), "an empty room picks nothing")
	r.add_box(Vector3(0, 0, -1), Vector3(4, 4, 0.1), "", "room")
	await r.settle()
	var h := r.pick(Vector2(300, 300))
	check(not h.is_empty() and not h.has("assisted"), "a plain wall stays what the ray found")
	await _end(r)


func test_the_reach_follows_the_screen_dpi() -> void:
	var r := await _start()
	var lever := _part(r, "IA_lever", 3.0)
	await r.settle()
	var c := _centre_px(r, lever)
	var tap := c + Vector2(_mm(5.5), 0) # 4 mm from the lever's edge on a 400 dpi phone
	eq(_part_of(r.pick(tap)), "IA_lever", "inside the reach at 400 dpi")
	# the same pixels on a 200 dpi screen are twice as many millimetres: out of reach
	Settings.emulate = {"size": Vector2i(2340, 1080), "dpi": 200.0, "safe": Rect2i(0, 0, 2340, 1080)}
	eq(_part_of(r.pick(tap)), "", "the same pixels at 200 dpi are 2x the millimetres: out of reach")
	await _end(r)
