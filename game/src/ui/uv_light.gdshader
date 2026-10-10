shader_type canvas_item;
// The UV lamp's light on a sheet of paper (UIUVLight, drawn over the whole sheet, under the ink): a soft violet
// pool over the written part of the page, deepest in the middle, fading out smoothly well before the sheet's
// edges (no hard edge anywhere), a faint scattered halo around it, and the paper fluorescing a little: a pale
// bluish mottling of its fibres where the light falls. Blend mix: the paper's texture still shows through.

uniform vec2 center = vec2(0.5, 0.45); // pool centre, in UV of the sheet
uniform vec2 radius = vec2(0.36, 0.3); // pool radii, in UV of the sheet
uniform float strength : hint_range(0.0, 1.0) = 1.0; // the lamp coming on
uniform float darken : hint_range(0.0, 1.0) = 0.78; // how far the paper sinks toward violet in the middle
uniform vec4 deep : source_color = vec4(0.07, 0.035, 0.17, 1.0); // the dark of the room the lamp shines into
uniform vec4 glow : source_color = vec4(0.49, 0.31, 1.0, 1.0); // the lamp's violet
uniform vec4 fluor : source_color = vec4(0.72, 0.8, 1.0, 1.0); // paper brighteners under UV

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
}

void fragment() {
	vec2 d = (UV - center) / radius;
	float r = length(d);
	// the pool: full in the middle, gone by r = 1 (radius keeps r = 1.25 inside the sheet)
	float pool = 1.0 - smoothstep(0.3, 1.0, r);
	pool = pool * pool * (3.0 - 2.0 * pool);
	// a lamp's beam is never a perfect disc: a slow, faint unevenness, and a slight breathing
	pool *= 0.92 + 0.08 * noise(UV * vec2(4.0, 3.0) + vec2(TIME * 0.02, 0.0));
	pool *= 0.98 + 0.02 * sin(TIME * 1.3);
	// the light scattered around the pool: a wide, weak violet tint
	float halo = (1.0 - smoothstep(0.55, 1.25, r)) * 0.2;
	// the paper fluoresces a little: a pale bluish mottling of its fibres, and a rare brighter fleck
	float mottle = noise(UV * vec2(70.0, 48.0)) * 0.6 + noise(UV * vec2(190.0, 140.0)) * 0.4;
	float fleck = smoothstep(0.9, 1.0, noise(UV * vec2(420.0, 310.0))) * 0.35;
	vec3 col = mix(deep.rgb, glow.rgb, 0.3 + 0.16 * (1.0 - min(r, 1.0)));
	col += fluor.rgb * pool * (0.05 + 0.07 * mottle + fleck * 0.5);
	float a = max(pool * darken, halo) * strength;
	COLOR = vec4(col, clamp(a, 0.0, 1.0));
}
