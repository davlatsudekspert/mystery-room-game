shader_type spatial;
// The master desk's strip chart (docs/models/ch4.md §4, §10): the pen marks of the Night of Silence, drawn from this
// game's own minutes. The paper is 0.40 x 0.46 m, UV 0..1: u across the eight minute columns 0..7 (0.05 m each, left
// to right), v up the slope. Each of the Sun, the rings and the keeper left one mark in the column of its minute; the
// master lever's heavy bar stands in column 7 (03:17). The column under the chronometer's hand glows a little.
// Pictograms only: a Sun with rays, two concentric rings, the keeper's wave, the lever's bar.

uniform int sun_min = 4;
uniform int rings_min = 5;
uniform int keeper_min = 6;
uniform float wheel = 7.0;
uniform vec3 paper : source_color = vec3(0.86, 0.8, 0.66);
uniform vec3 ink : source_color = vec3(0.07, 0.06, 0.05);

const float COL_W = 0.05;
const float PAPER_H = 0.46;
const float MARK_V = 0.60;

float line_d(vec2 p, vec2 a, vec2 b) {
	vec2 pa = p - a;
	vec2 ba = b - a;
	float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
	return length(pa - ba * h);
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	float col_f = UV.x * 8.0;
	int col = int(floor(col_f));
	// position inside the column in metres: x across, y up from the mark's height
	vec2 p = vec2((fract(col_f) - 0.5) * COL_W, (UV.y - MARK_V) * PAPER_H);
	float ink_a = 0.0;
	// the pen's baseline: a thin dotted vertical trace in every column
	float dots = step(0.5, fract(UV.y * PAPER_H * 120.0));
	ink_a = max(ink_a, (1.0 - smoothstep(0.0005, 0.0011, abs(p.x))) * dots * 0.55);
	// the Sun: a disc with eight rays
	if (col == sun_min) {
		float r = length(p);
		ink_a = max(ink_a, 1.0 - smoothstep(0.0125, 0.0145, r));
		float ang = atan(p.y, p.x);
		float ray = step(0.0152, r) * (1.0 - step(0.0235, r)) * step(0.55, abs(sin(ang * 4.0)));
		ink_a = max(ink_a, ray);
	}
	// the rings: two concentric outlines
	if (col == rings_min) {
		float r = length(p);
		ink_a = max(ink_a, (1.0 - smoothstep(0.0009, 0.0021, abs(r - 0.0215))));
		ink_a = max(ink_a, (1.0 - smoothstep(0.0009, 0.0021, abs(r - 0.0125))));
		ink_a = max(ink_a, 1.0 - smoothstep(0.0025, 0.0035, r));
	}
	// the keeper: the note's wave
	if (col == keeper_min) {
		float w = sin(p.y * 520.0) * 0.0095;
		float d = abs(p.x - w);
		float inside = step(abs(p.y), 0.0235);
		ink_a = max(ink_a, (1.0 - smoothstep(0.0011, 0.0022, d)) * inside);
	}
	// 03:17: the lever's heavy bar from the foot of the paper to the top, with a knob
	if (col == 7) {
		float bar = (1.0 - smoothstep(0.0036, 0.0046, abs(p.x))) * step(0.06, UV.y) * step(UV.y, 0.9);
		float knob = 1.0 - smoothstep(0.0095, 0.0112, length(p - vec2(0.0, (0.88 - MARK_V) * PAPER_H)));
		ink_a = max(ink_a, max(bar, knob));
	}
	// faint column rules
	float vline = 1.0 - smoothstep(0.0, 0.0012, min(fract(col_f), 1.0 - fract(col_f)) * COL_W);
	vec3 base = paper * (0.9 + 0.1 * hash(floor(UV * vec2(160.0, 190.0))));
	base *= 1.0 - 0.10 * vline;
	// the column under the hand
	float here = 1.0 - smoothstep(0.0, 0.6, abs(col_f - 0.5 - wheel));
	base += vec3(0.07, 0.05, 0.0) * here;
	// paper darkens toward the roll at the top and the edges
	float edge = smoothstep(0.0, 0.06, UV.x) * smoothstep(1.0, 0.94, UV.x);
	base *= 0.78 + 0.22 * edge;
	ALBEDO = mix(base, ink, clamp(ink_a, 0.0, 1.0) * 0.94);
	ROUGHNESS = 0.85;
}
