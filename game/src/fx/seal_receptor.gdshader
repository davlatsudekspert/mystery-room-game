shader_type spatial;
// One receptor of the spectral seal (docs/models/ch3.md §6 / §11, E3). Bits: 1 ▲ red, 2 ● green, 4 ■ blue.
// The rim ring (r 0.38–0.50 of the disc's bounding square) takes the additive colour of `rim` and shows one cream
// symbol per bit, so colour is never the only cue. The centre shows the light falling on it (`light`) in its additive
// colour with its symbols in a row. `accepted` = the whole seal accepts. UV 0..1 over the disc's bounding square.
render_mode cull_back;

uniform int rim = 3;
uniform int light = 0;
uniform bool accepted = false;
uniform sampler2D sym_triangle : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D sym_circle : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D sym_square : source_color, filter_linear_mipmap, repeat_disable;
uniform vec3 cream : source_color = vec3(0.95, 0.91, 0.80);

vec3 additive(int bits) {
	vec3 c = vec3(0.0);
	if ((bits & 1) != 0) c += vec3(1.0, 0.16, 0.10);
	if ((bits & 2) != 0) c += vec3(0.16, 0.95, 0.25);
	if ((bits & 4) != 0) c += vec3(0.18, 0.35, 1.0);
	return clamp(c, 0.0, 1.0);
}

float sym(int k, vec2 local) {
	// local: -0.5..0.5 inside the symbol's square, v up
	if (abs(local.x) > 0.5 || abs(local.y) > 0.5) {
		return 0.0;
	}
	vec2 t = vec2(local.x + 0.5, 0.5 - local.y);
	if (k == 0) return texture(sym_triangle, t).a;
	if (k == 1) return texture(sym_circle, t).a;
	return texture(sym_square, t).a;
}

void fragment() {
	vec2 p = vec2(UV.x, 1.0 - UV.y) - 0.5;
	float r = length(p) / 0.5;
	vec3 col = vec3(0.04, 0.045, 0.05);
	vec3 emit = vec3(0.0);
	float mark = 0.0;
	if (r >= 0.76) {
		vec3 rc = additive(rim);
		col = mix(vec3(0.08), rc * 0.85, 0.9);
		emit = rc * 0.25;
		for (int k = 0; k < 3; k++) {
			if (((rim >> k) & 1) != 0) {
				float a = radians(90.0 + 120.0 * float(k));
				vec2 c = vec2(cos(a), sin(a)) * 0.44;
				mark = max(mark, sym(k, (p - c) / 0.11));
			}
		}
	} else if (r < 0.72) {
		vec3 lc = additive(light);
		float glow = accepted ? 1.6 : 1.0;
		col = mix(col, lc, light != 0 ? 0.75 : 0.0);
		emit = lc * (light != 0 ? 1.4 * glow : 0.0) * (1.0 - 0.35 * r);
		int n = 0;
		for (int k = 0; k < 3; k++) {
			n += (light >> k) & 1;
		}
		int j = 0;
		for (int k = 0; k < 3; k++) {
			if (((light >> k) & 1) != 0) {
				vec2 c = vec2((float(j) - float(n - 1) * 0.5) * 0.17, 0.0);
				mark = max(mark, sym(k, (p - c) / 0.15));
				j += 1;
			}
		}
	} else {
		col = vec3(0.35, 0.28, 0.14); // the brass bezel line between rim and centre
	}
	ALBEDO = mix(col, cream, mark);
	EMISSION = mix(emit, cream * (r < 0.72 && light != 0 ? 1.2 : 0.35), mark);
	ROUGHNESS = 0.25;
}
