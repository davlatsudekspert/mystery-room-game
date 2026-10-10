shader_type canvas_item;
// The UV lamp's light on a sheet of paper (UIUVLight, drawn over the whole sheet, under the ink): the page sinks
// into a deep violet that covers the writing and feathers out toward the sheet's edges (a soft rounded falloff,
// no hard edge anywhere), with a brighter, uneven violet glow where the lamp points (the middle), and the paper
// fluorescing a little: a pale bluish mottling of its fibres. Blend mix: the paper's texture still shows through.

uniform vec2 center = vec2(0.5, 0.5); // where the lamp points, in UV of the sheet
uniform vec2 radius = vec2(0.36, 0.34); // the bright spot's radii, in UV of the sheet
uniform vec2 size_px = vec2(1600.0, 900.0); // the sheet's size
uniform float feather = 90.0; // px: the soft border toward the sheet's edges (and the rounding of its corners)
uniform float top_px = 0.0; // px: where the light begins (below the page's printed header, which stays readable)
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
	// the covered area: the sheet less a soft border, with rounded corners (a rounded-box distance in px)
	vec2 lo = vec2(0.0, top_px);
	vec2 p = UV * size_px - (lo + size_px) * 0.5;
	vec2 dq = abs(p) - ((size_px - lo) * 0.5 - vec2(feather));
	float sdf = length(max(dq, vec2(0.0))) + min(max(dq.x, dq.y), 0.0) - feather;
	// light has no straight edge: the border wanders a little, and the falloff is gentle
	sdf += (noise(UV * vec2(3.0, 2.2) + vec2(1.7, 0.4)) - 0.5) * feather * 0.9;
	float cover = smoothstep(0.0, feather * 1.4, -sdf);
	cover = cover * cover * (3.0 - 2.0 * cover);
	// the bright spot where the lamp points: never a perfect disc, it moves faintly and breathes
	float r = length((UV - center) / radius);
	float spot = 1.0 - smoothstep(0.0, 1.0, r);
	spot *= 0.85 + 0.15 * noise(UV * vec2(4.0, 3.0) + vec2(TIME * 0.02, 0.0));
	spot *= 0.97 + 0.03 * sin(TIME * 1.3);
	// the paper fluoresces a little: a pale bluish mottling of its fibres, and a rare brighter fleck
	float mottle = noise(UV * vec2(70.0, 48.0)) * 0.6 + noise(UV * vec2(190.0, 140.0)) * 0.4;
	float fleck = smoothstep(0.9, 1.0, noise(UV * vec2(420.0, 310.0))) * 0.35;
	vec3 col = mix(deep.rgb, glow.rgb, 0.18 + 0.36 * spot);
	col += fluor.rgb * cover * (0.04 + 0.06 * mottle + fleck * 0.4 + 0.05 * spot);
	float a = cover * (darken - 0.08 * spot) * strength;
	COLOR = vec4(col, clamp(a, 0.0, 1.0));
}
