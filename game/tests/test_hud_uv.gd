extends TestBase
## The UV-revealed notebook page (owner feedback, item 5: "a hard pink/violet rectangle over the paper looks
## cheap"): the light is a UIUVLight drawn under the ink with a feathered pool (no flat ColorRect tint), the cipher
## glows (pale mint text with a soft halo, glyphs through the ink-glow shader), and the pool stays on the sheet.

const PHONE := {"size": Vector2i(1920, 1080), "dpi": 480.0, "safe": Rect2i(0, 0, 1920, 1080)}


func _open_uv_page(revealed: bool) -> HudTestRoom:
	SaveSystem.save_path = "user://test_hud_uv.json"
	Settings.emulate = PHONE
	TranslationServer.set_locale("en")
	GameState.start_new("ch1")
	var l := GameState.logic as Lab7Logic
	l._begin()
	l._add_item("notebook")
	l._add_item("uv_lamp")
	l._end()
	l.state["uv_page"] = revealed
	var r := HudTestRoom.create(l, true)
	await r.attach()
	r.hud.call("_show_notebook", 4)
	await r.wait(0.2)
	return r


func _finish(r: HudTestRoom) -> void:
	r.hud.call("_close_overlay")
	r.dispose()
	await (Engine.get_main_loop() as SceneTree).process_frame
	Settings.emulate = {}
	SaveSystem.delete_game()
	SaveSystem.save_path = SaveSystem.SAVE_PATH


func _lights(o: Node) -> Array[Node]:
	return o.find_children("*", "UIUVLight", true, false)


func test_revealed_page_has_a_soft_light_and_glowing_ink() -> void:
	var r := await _open_uv_page(true)
	var o := r.hud.get("_overlay") as Node
	if o == null:
		check(false, "the notebook opens")
		await _finish(r)
		return
	var lights := _lights(o)
	eq(lights.size(), 1, "one UV light on the page")
	for n in o.find_children("*", "ColorRect", true, false):
		var cr := n as ColorRect
		check(not (cr.color.b > cr.color.g + 0.3 and cr.color.a > 0.05 and cr.get_parent() is PanelContainer), "no flat violet tint over the paper")
	if lights.size() == 1:
		var light := lights[0] as UIUVLight
		eq(light.get_index(), 0, "the light is drawn before the text (the ink stays on top)")
		check(light.material is ShaderMaterial and (light.material as ShaderMaterial).shader == UIUVLight.LIGHT_SHADER, "the light is the feathered shader")
		check(is_equal_approx(light.strength, 1.0), "already lit")
		var m := light.material as ShaderMaterial
		var c: Vector2 = m.get_shader_parameter("center")
		var rad: Vector2 = m.get_shader_parameter("radius")
		# the pool and its halo (1.25 × the radius) stay inside the sheet: nothing is cut off by the sheet's edge
		check(c.x - rad.x * 1.25 >= -0.001 and c.x + rad.x * 1.25 <= 1.001, "the pool fits the sheet sideways (%s ± %s)" % [c, rad])
		check(c.y - rad.y * 1.25 >= -0.001 and c.y + rad.y * 1.25 <= 1.001, "the pool fits the sheet in height (%s ± %s)" % [c, rad])
	var glowing_text := 0
	for n in o.find_children("*", "Label", true, false):
		var l := n as Label
		if l.get_theme_color("font_color") == UIUVLight.INK:
			glowing_text += 1
			check(l.get_theme_constant("shadow_outline_size") > 0 and l.get_theme_color("font_shadow_color").a > 0.0, "the ink has a soft halo")
			check(l.get_theme_color("font_outline_color").a < 0.5, "and no dark rim")
	eq(glowing_text, 1, "the cipher line glows")
	var glyphs := 0
	for n in o.find_children("*", "TextureRect", true, false):
		var t := n as TextureRect
		if t.material is ShaderMaterial and (t.material as ShaderMaterial).shader == UIUVLight.INK_SHADER:
			glyphs += 1
	eq(glyphs, (GameState.logic as Lab7Logic).safe_glyphs().size(), "every glyph glows")
	await _finish(r)


func test_the_lamp_strikes_on_the_page() -> void:
	var r := await _open_uv_page(false)
	var o := r.hud.get("_overlay") as Node
	eq(_lights(o).size(), 0, "no light before the lamp is used")
	var uvb: IconButton = null
	for n in o.find_children("*", "IconButton", true, false):
		if (n as IconButton).icon_id == "uv":
			uvb = n
	check(uvb != null, "the page offers the UV lamp")
	if uvb != null:
		uvb.emit_signal("pressed")
		await r.wait(0.05)
		var lights := _lights(o)
		eq(lights.size(), 1, "the lamp lights the page")
		await r.wait(0.9)
		if lights.size() == 1:
			check(is_equal_approx((lights[0] as UIUVLight).strength, 1.0), "the light settles at full strength")
		check(bool((GameState.logic as Lab7Logic).state["uv_page"]), "the page is revealed in the logic")
	await _finish(r)
