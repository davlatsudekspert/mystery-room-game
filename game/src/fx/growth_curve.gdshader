shader_type spatial;
// Leyla's growth chart (docs/models/ch3.md §6 / §11, E2): the printed 6-line graph paper plus this game's curve in
// pencil. The curve rises from the axis to levels[0], holds through stage 0, steps to levels[1], holds, steps to
// levels[2], holds, then falls. Line l sits at v = 0.12 + 0.13 (l - 1); stage s spans u ∈ [0.12 + 0.27 s,
// 0.39 + 0.27 s]. The quad is 0.60 × 0.80 m, UV 0..1 (u -> right, v -> up).
render_mode cull_back;

uniform sampler2D grid : source_color, filter_linear_mipmap, repeat_disable;
uniform ivec3 levels = ivec3(5, 2, 4);
uniform vec3 pencil : source_color = vec3(0.20, 0.20, 0.26);

const vec2 SIZE = vec2(0.60, 0.80);
const float AXIS = 0.085;

float level_v(int l) {
	return 0.12 + 0.13 * float(l - 1);
}

float curve(float u) {
	float y = AXIS;
	y = mix(y, level_v(levels.x), smoothstep(0.10, 0.16, u));
	y = mix(y, level_v(levels.y), smoothstep(0.365, 0.415, u));
	y = mix(y, level_v(levels.z), smoothstep(0.635, 0.685, u));
	y = mix(y, AXIS, smoothstep(0.91, 0.975, u));
	// a hand-drawn line wobbles a little
	return y + 0.0025 * sin(u * 83.0) + 0.0015 * sin(u * 211.0 + 1.3);
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

void fragment() {
	vec2 uv = vec2(UV.x, 1.0 - UV.y);
	vec3 base = texture(grid, UV).rgb;
	float on_paper = step(0.10, uv.x) * step(uv.x, 0.975);
	float e = 0.001;
	float y = curve(uv.x);
	float slope = (curve(uv.x + e) - curve(uv.x - e)) / (2.0 * e) * (SIZE.y / SIZE.x);
	float d = abs(uv.y - y) * SIZE.y / sqrt(1.0 + slope * slope);
	float aa = max(fwidth(uv.y) * SIZE.y, 0.0001);
	float line = (1.0 - smoothstep(0.0013, 0.0013 + aa, d)) * on_paper;
	line *= 0.7 + 0.3 * hash(floor(uv * vec2(768.0, 1024.0)));
	ALBEDO = mix(base, pencil, line * 0.9);
	ROUGHNESS = 0.9;
}
