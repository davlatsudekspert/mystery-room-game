shader_type spatial;
// The keeper's oscillograph (docs/models/ch4.md §4, §10): the Core's own note and the keeper's note drawn together. The
// two sines beat; the envelope of the picture slows as the knob nears the Core's note (beat = the distance in marks) and
// stands still when they match. Keeper off: the Core's note alone. The CRT face is a disc, UV 0..1 over its square.
render_mode unshaded, cull_back;

uniform float beat = 6.0; // distance in marks (0 = locked)
uniform float probe = 1.0; // 0 = the keeper is off
uniform float live = 1.0; // 0 = the desk is dead
uniform vec3 phosphor : source_color = vec3(0.45, 1.0, 0.55);

void fragment() {
	vec2 uv = vec2(UV.x, 1.0 - UV.y);
	vec2 c = (uv - 0.5) * 2.0;
	float rr = length(c);
	float f = 9.0;
	// the beat: d beats across the face, drifting at a speed that follows d
	float delta = beat * 0.42;
	float t = TIME * (1.6 + 0.5 * beat);
	float a = 6.2831853 * f * uv.x - TIME * 3.2;
	float b = 6.2831853 * (f + delta) * uv.x - TIME * 3.2 - t * 0.0;
	float carrier = sin(a);
	float s = mix(carrier * 0.62, 0.5 * (sin(a) + sin(b)), probe);
	float env = mix(0.62, abs(cos(3.1415927 * delta * uv.x + t * 0.0)), probe);
	float amp = 0.34;
	float y = 0.5 + amp * s;
	float dy = abs(uv.y - y);
	float core = 1.0 - smoothstep(0.012, 0.024, dy);
	float halo = exp(-dy / 0.05) * 0.30;
	// envelope guides: faint lines where the beat's swing peaks
	float de = min(abs(uv.y - (0.5 + amp * env)), abs(uv.y - (0.5 - amp * env)));
	float guide = (1.0 - smoothstep(0.006, 0.013, de)) * 0.40 * probe;
	vec2 g = abs(fract(uv * vec2(10.0, 8.0)) - 0.5);
	float grat = (step(0.47, g.x) + step(0.47, g.y)) * 0.05;
	float vig = 1.0 - smoothstep(0.80, 1.0, rr);
	vec3 col = vec3(0.012, 0.04, 0.025) + phosphor * ((core + halo) * (0.35 + 0.65 * live) + guide + grat);
	ALBEDO = col * vig * (0.15 + 0.85 * live);
}
