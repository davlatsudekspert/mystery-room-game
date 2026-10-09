shader_type spatial;
// A Jacob's-ladder arc climbing between two diverging rods (docs/models/ch3.md §4 transformer): a jagged
// blue-white line that rises from the narrow gap at the bottom to the wide top, breaks and starts again.
// The quad spans the rods' gap: width 0.40, height 1.10, UV 0..1 (v up).
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled;

uniform float on = 1.0;
uniform float phase = 0.0;
uniform vec3 arc : source_color = vec3(0.70, 0.85, 1.0);

float hash(float x) {
	return fract(sin(x * 91.345) * 47453.21);
}

void fragment() {
	vec2 uv = vec2(UV.x, 1.0 - UV.y);
	float t = fract(TIME * 0.42 + phase);
	float h = t * 0.96 + 0.02;
	float half_w = (0.015 + 0.165 * h) / 0.40; // the gap grows from 0.03 to 0.36 m
	float x = (uv.x - 0.5) / max(half_w, 0.001);
	float seed = floor(TIME * 24.0);
	float jag = (hash(floor(uv.x * 40.0) + seed) - 0.5) * 0.018 + 0.03 * sin(x * 1.5708 + 1.5708) * h;
	float d = abs(uv.y - h - jag);
	float core = (1.0 - smoothstep(0.002, 0.008, d)) * step(abs(x), 1.0);
	float glow = exp(-d * 60.0) * 0.5 * step(abs(x), 1.0);
	float flick = 0.75 + 0.25 * hash(seed + 3.0);
	ALBEDO = arc * (core * 3.0 + glow) * flick * on;
}
