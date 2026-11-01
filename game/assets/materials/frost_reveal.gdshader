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
uniform vec4 frost_tint : source_color = vec4(0.894, 0.941, 0.965, 1.0);
uniform float reveal : hint_range(0.0, 1.0) = 1.0;
uniform vec2 pane_size = vec2(0.8, 1.2); // metres: the noise is laid out in metres, so it never tiles and never stretches
uniform float edge_softness : hint_range(0.02, 0.4) = 0.14;
uniform float seed = 0.0;

// Procedural frost (no texture, so no repeat): value noise in layers. Large haze + patches, fine crystals bent by the haze, vertical
// streaks where water ran, and thicker frost toward the frame, where real window frost grows first.
float hash(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
}

float fbm(vec2 p, int oct) {
	float v = 0.0;
	float amp = 0.5;
	for (int k = 0; k < oct; k++) {
		v += amp * vnoise(p);
		p = p * 2.03 + vec2(17.1, 9.7);
		amp *= 0.5;
	}
	return v;
}

void fragment() {
	vec2 p = UV * pane_size + vec2(seed * 7.3, seed * 3.1);
	float haze = fbm(p * 4.0, 4); // patches of a hand's size
	float fine = fbm(p * 34.0 + haze * 4.0, 3); // crystals
	float ridge = 1.0 - abs(2.0 * vnoise(p * 70.0 + haze * 6.0) - 1.0); // feathery crystal ridges
	float streak = vnoise(vec2(p.x * 26.0, p.y * 2.2 + haze * 2.0));
	vec2 e = min(UV, vec2(1.0) - UV) * pane_size;
	float edge = min(e.x, e.y);
	float grow = smoothstep(0.30, 0.0, edge);
	float n = clamp(0.55 * haze + 0.45 * fine, 0.0, 1.0);
	float w = texture(wipe_mask, UV).r;
	// ragged melt edge: the crystals decide where the wipe stops
	float keep = 1.0 - smoothstep(0.5 - edge_softness, 0.5 + edge_softness, w + (n - 0.5) * 0.45);
	float a = clamp(0.10 + 0.85 * haze + 0.30 * grow + 0.45 * (fine - 0.5) + 0.30 * (ridge - 0.5) + 0.12 * (streak - 0.5), 0.12, 0.97) * keep * reveal;
	vec3 col = mix(frost_tint.rgb * 0.82, vec3(0.97, 0.99, 1.0), clamp(fine * 1.0 + ridge * 0.35 + grow * 0.25 - 0.1, 0.0, 1.0));
	col = mix(col, vec3(0.66, 0.78, 0.86), clamp((0.52 - haze) * 2.4, 0.0, 0.7)); // thin patches show a little of the cold blue behind
	ALBEDO = col;
	ALPHA = a;
	ROUGHNESS = 0.75;
	SPECULAR = 0.4;
	RIM = 0.25;
	RIM_TINT = 0.5;
}
