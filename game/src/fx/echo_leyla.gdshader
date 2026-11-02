shader_type spatial;
// Leyla's light echo (Chapter 1 finale): soft white-blue light with a fresnel rim, a gentle inner glow and a faint
// shimmer. Used with a depth pre-pass material (next_pass): the first pass writes depth only, so only the front-most
// surface glows (no visible back faces, arm-over-torso seams or hollow-shell look).
render_mode blend_add, unshaded, depth_draw_never, cull_back, shadows_disabled;

uniform vec4 tint : source_color = vec4(0.78, 0.92, 1.0, 1.0);
uniform vec4 warm : source_color = vec4(1.0, 0.86, 0.66, 1.0); // the desk lamp's side
uniform vec3 lamp_pos = vec3(-0.2, 1.2, -2.2);
uniform float intensity = 1.0;
uniform float rim_power = 2.4;
uniform float rim_gain = 0.85;
uniform float body = 0.22;
uniform float animate = 1.0; // 0 with Settings "reduce_motion": no drift, no shimmer

varying vec3 wpos;
varying vec3 wnrm;

float hash(vec3 p) {
	p = fract(p * 0.3183099 + vec3(0.1, 0.2, 0.3));
	p *= 17.0;
	return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float vnoise(vec3 x) {
	vec3 i = floor(x);
	vec3 f = fract(x);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash(i), hash(i + vec3(1, 0, 0)), f.x), mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y),
		mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x), mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 n = normalize(NORMAL);
	float ndv = clamp(dot(n, normalize(VIEW)), 0.0, 1.0);
	float fres = pow(1.0 - ndv, rim_power);
	// soft form: wrapped light from the lamp side keeps the volume readable (face, folds of the coat, the bun)
	vec3 to_lamp = normalize(lamp_pos - wpos);
	float wrap = clamp(dot(normalize(wnrm), to_lamp) * 0.5 + 0.5, 0.0, 1.0);
	// inner glow: strongest where the surface faces the viewer, so the body is a lit volume, not an outline
	float core = pow(ndv, 1.6);
	// faint drifting shimmer (rising slowly), frozen with reduce-motion
	float t = TIME * animate;
	float sh = vnoise(wpos * vec3(9.0, 6.0, 9.0) + vec3(0.0, -t * 0.55, 0.0));
	float shimmer = 0.88 + 0.24 * sh;
	float rise = smoothstep(0.995, 1.0, vnoise(wpos * 38.0 + vec3(0.0, -t * 1.2, 0.0))); // tiny motes
	vec3 col = tint.rgb * (body * (0.45 + 0.55 * core) + fres * rim_gain);
	col += mix(tint.rgb, warm.rgb, 0.65) * wrap * wrap * 0.34 * core;
	// the figure dissolves into light toward the floor, and is brightest at the face and hands
	float fade = mix(0.35, 1.0, smoothstep(0.30, 0.95, wpos.y));
	col *= shimmer * fade;
	col += tint.rgb * rise * 0.5;
	ALBEDO = col * intensity;
}
