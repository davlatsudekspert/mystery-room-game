shader_type spatial;
// Strand's ECG strip (docs/models/ch3.md §11, W2): the printed grid paper with this game's heart trace in pen.
// Exactly peaks[b] full QRS complexes evenly spaced inside pen bracket b (☼ ☾ ✦), plus one complex in each gap and
// at each end, so counting the whole strip never gives a bracket's number. Low P and T waves around every beat.
// UV 0..1 over the strip (u left -> right along the trace, v from the bottom edge up), 0.32 m × 0.05 m.
render_mode cull_disabled;

uniform sampler2D paper : source_color, filter_linear_mipmap, repeat_disable;
uniform ivec3 peaks = ivec3(4, 2, 6);
uniform vec3 ink : source_color = vec3(0.10, 0.11, 0.22);
uniform float baseline = 0.30;
uniform float height = 0.27;

const vec2 SIZE = vec2(0.32, 0.05);
const float W = 0.0042; // QRS width in u

float beat(float x, float s) {
	// x = u - centre, s = the spacing to the next beat (P and T waves scale with it)
	float r = exp(-(x * x) / (W * W));
	float q = -0.16 * exp(-pow((x + 1.7 * W) / (0.8 * W), 2.0));
	float sw = -0.30 * exp(-pow((x - 1.7 * W) / (0.9 * W), 2.0));
	float pw = 0.09 * exp(-pow((x + 0.30 * s) / (0.07 * s), 2.0));
	float tw = 0.15 * exp(-pow((x - 0.36 * s) / (0.10 * s), 2.0));
	return r + q + sw + pw + tw;
}

float bracket(float u, float lo, float hi, int n) {
	if (n <= 0 || u < lo - 0.06 || u > hi + 0.06) {
		return 0.0;
	}
	float s = (hi - lo) / float(n);
	int i0 = int(floor((u - lo) / s));
	float y = 0.0;
	for (int k = i0 - 1; k <= i0 + 1; k++) {
		if (k >= 0 && k < n) {
			y += beat(u - (lo + (float(k) + 0.5) * s), s);
		}
	}
	return y;
}

float trace(float u) {
	float y = bracket(u, 0.06, 0.32, peaks.x) + bracket(u, 0.38, 0.62, peaks.y) + bracket(u, 0.68, 0.94, peaks.z);
	y += beat(u - 0.03, 0.06) + beat(u - 0.35, 0.06) + beat(u - 0.65, 0.06) + beat(u - 0.97, 0.06);
	return baseline + height * y;
}

void fragment() {
	vec2 uv = vec2(UV.x, 1.0 - UV.y);
	vec3 base = texture(paper, UV).rgb;
	float e = 0.0006;
	float y = trace(uv.x);
	float slope = (trace(uv.x + e) - trace(uv.x - e)) / (2.0 * e) * (SIZE.y / SIZE.x);
	float d = abs(uv.y - y) * SIZE.y / sqrt(1.0 + slope * slope); // metres from the pen line
	float aa = max(fwidth(uv.y) * SIZE.y, 0.00005);
	float line = 1.0 - smoothstep(0.00028, 0.00028 + aa, d);
	ALBEDO = mix(base, ink, line * 0.92);
	ROUGHNESS = 0.85;
}
