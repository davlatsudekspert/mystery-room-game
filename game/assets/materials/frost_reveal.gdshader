shader_type spatial;
// Frost pane of the Cold Store window (N5): hoar frost over the glass, wiped away where `wipe_mask` is white.
// Used by the slot M_Decal_FrostPane on the `frost_glass` quad of frost_window.glb; the quad's UV 0..1 covers the pane
// (U left to right, V 0 = top of the pane = row 0 of the mask image). Mobile-safe: no screen-texture read, one blended pass.
//
// wipe_mask  R channel, 0 = frost stays, 1 = wiped clear. The scene paints it (finger or band-tap) into a small ImageTexture
//            (suggested 64 x 96, FORMAT_R8 / FORMAT_L8, filter linear) and updates it with Texture.update(image).
// reveal     global 0..1 multiplier: 1 = frost fully there (default), 0 = pane clear (e.g. after all bands are seen).
// The mask edge is made ragged by the frost texture so a wiped stroke looks like melted ice, not a soft brush.
render_mode blend_mix, depth_draw_never, cull_back, specular_schlick_ggx;

uniform sampler2D wipe_mask : filter_linear, hint_default_black;
uniform sampler2D frost_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 frost_tint : source_color = vec4(0.894, 0.941, 0.965, 1.0);
uniform float reveal : hint_range(0.0, 1.0) = 1.0;
uniform vec2 tiling = vec2(2.2, 3.3);
uniform float edge_softness : hint_range(0.02, 0.4) = 0.14;

void fragment() {
	vec4 f = texture(frost_tex, UV * tiling);
	float w = texture(wipe_mask, UV).r;
	// ragged melt edge: the frost crystals decide where the wipe stops
	float keep = 1.0 - smoothstep(0.5 - edge_softness, 0.5 + edge_softness, w + (f.a - 0.5) * 0.45);
	float a = clamp(f.a * 0.95 + 0.12, 0.0, 1.0) * keep * reveal;
	ALBEDO = mix(frost_tint.rgb, f.rgb, 0.65);
	ALPHA = a;
	ROUGHNESS = 0.75;
	SPECULAR = 0.4;
	RIM = 0.25;
	RIM_TINT = 0.5;
}
