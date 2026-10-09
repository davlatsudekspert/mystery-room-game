shader_type spatial;
// The chalk "staircase" over the Choir rack (docs/models/ch3.md §4 / §11, W3): the printed chalk grid plus this
// game's seven dots, dot k on column k at line heights[k]. The quad spans x ∈ [-1.30, 1.30], y ∈ [2.55, 3.45];
// UV 0..1 with u -> +X and v -> +Y.
render_mode cull_back, depth_draw_opaque;

uniform sampler2D grid : source_color, filter_linear_mipmap, repeat_disable;
uniform int heights[7];
uniform vec3 chalk : source_color = vec3(0.93, 0.92, 0.86);

const vec2 SIZE = vec2(2.60, 0.90);

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	vec2 uv = vec2(UV.x, 1.0 - UV.y);
	vec4 g = texture(grid, UV);
	float dots = 0.0;
	for (int k = 0; k < 7; k++) {
		float x = float(k - 3) * 0.34;
		vec2 c = vec2((x + 1.30) / 2.60, (0.10 + 0.12 * float(heights[k] - 1)) / 0.90);
		vec2 dm = (uv - c) * SIZE;
		// a pressed chalk dot: a slightly ragged disc, denser in the middle
		float ang = atan(dm.y, dm.x);
		float r = 0.034 + 0.003 * sin(ang * 5.0 + float(k)) + 0.002 * sin(ang * 11.0);
		dots = max(dots, 1.0 - smoothstep(r - 0.006, r, length(dm)));
	}
	float grain = 0.72 + 0.28 * hash(floor(uv * vec2(900.0, 310.0)));
	float a_dot = dots * grain;
	ALBEDO = mix(g.rgb, chalk, a_dot);
	ALPHA = clamp(max(g.a, a_dot), 0.0, 1.0);
	ROUGHNESS = 0.95;
}
