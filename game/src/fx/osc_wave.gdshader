shader_type spatial;
// Leyla's oscillograph (docs/models/ch3.md §7 / §11, E4): a phosphor sine whose density tells the note. cycles =
// 2 + 2 × (5 - size), so denser waves mean a higher, smaller crystal. amp 0 = a flat line (no note ringing).
// The CRT face is 0.10 × 0.08 m, UV 0..1.
render_mode unshaded, cull_back;

uniform float cycles = 6.0;
uniform float amp = 0.0;
uniform vec3 phosphor : source_color = vec3(0.45, 1.0, 0.55);

const float ASPECT = 1.25;

void fragment() {
	vec2 uv = vec2(UV.x, 1.0 - UV.y);
	float y = 0.5 + 0.32 * amp * sin(6.2831853 * cycles * uv.x - TIME * 3.0);
	float slope = 0.32 * amp * 6.2831853 * cycles * cos(6.2831853 * cycles * uv.x - TIME * 3.0) / ASPECT;
	float d = abs(uv.y - y) / sqrt(1.0 + slope * slope);
	float core = 1.0 - smoothstep(0.008, 0.016, d);
	float halo = exp(-d / 0.04) * 0.35;
	vec2 g = abs(fract(uv * vec2(10.0, 8.0)) - 0.5);
	float grat = (step(0.47, g.x) + step(0.47, g.y)) * 0.06;
	vec2 c = (uv - 0.5) * vec2(ASPECT, 1.0);
	float vignette = 1.0 - smoothstep(0.42, 0.62, length(c));
	ALBEDO = (vec3(0.02, 0.05, 0.03) + phosphor * (core + halo + grat)) * vignette;
}
