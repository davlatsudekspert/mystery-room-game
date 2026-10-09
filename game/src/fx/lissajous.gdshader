shader_type spatial;
// The Lissajous figure x = sin(a t + π/2), y = sin(b t), t ∈ [0, 2π] (docs/models/ch3.md §8 / §11, H2).
// mode 0: Strand's brass plate, the figure engraved as a dark groove with a bright edge;
// mode 1: the console's oscilloscope, a green phosphor trace (a dot in the centre while not live).
// The distance to the curve comes from the points sharing the fragment's x or y (2a + 2b candidates) and the
// tangent there, so the cost does not grow with the figure's length.
render_mode cull_back;

uniform int fa = 3;
uniform int fb = 2;
uniform int mode = 0;
uniform bool live = true;
uniform float aspect = 1.0; // the quad's width / height
uniform float extent = 0.40; // half the figure's size, as a share of the quad's height
uniform vec3 brass : source_color = vec3(0.66, 0.50, 0.26);
uniform vec3 groove : source_color = vec3(0.10, 0.075, 0.05);
uniform vec3 phosphor : source_color = vec3(0.40, 1.0, 0.55);

const float TAU = 6.2831853;

vec2 curve_at(float t, float a, float b) {
	return vec2(cos(a * t), sin(b * t));
}

float dist_to_curve(vec2 q) {
	float a = float(fa);
	float b = float(fb);
	float best = 1e5;
	vec2 qc = clamp(q, vec2(-1.0), vec2(1.0));
	float ax = acos(qc.x);
	for (int k = 0; k < 5; k++) {
		if (k >= fa) break;
		for (int s = -1; s <= 1; s += 2) {
			float t = (float(s) * ax + TAU * float(k)) / a;
			vec2 c = curve_at(t, a, b);
			vec2 tg = vec2(-a * sin(a * t), b * cos(b * t));
			float perp = abs((q.y - c.y) * tg.x) / max(length(tg), 1e-4);
			best = min(best, min(length(q - c), abs(q.x) <= 1.0 ? perp : 1e5));
		}
	}
	float ay = asin(qc.y);
	for (int k = 0; k < 5; k++) {
		if (k >= fb) break;
		for (int s = 0; s < 2; s++) {
			float t = ((s == 0 ? ay : 3.14159265 - ay) + TAU * float(k)) / b;
			vec2 c = curve_at(t, a, b);
			vec2 tg = vec2(-a * sin(a * t), b * cos(b * t));
			float perp = abs((q.x - c.x) * tg.y) / max(length(tg), 1e-4);
			best = min(best, min(length(q - c), abs(q.y) <= 1.0 ? perp : 1e5));
		}
	}
	return best;
}

void fragment() {
	vec2 uv = vec2(UV.x, 1.0 - UV.y) - 0.5;
	vec2 q = vec2(uv.x * aspect, uv.y) / extent; // figure units: -1..1
	float d = (live || mode == 0) ? dist_to_curve(q) : length(q);
	float px = max(fwidth(q.x), 1e-4);
	if (mode == 0) {
		float w = 0.035;
		float g = 1.0 - smoothstep(w, w + px, d);
		float edge = (1.0 - smoothstep(w + px, w + 0.03 + px, d)) * (1.0 - g);
		ALBEDO = mix(brass * (1.0 + 0.25 * edge), groove, g);
		METALLIC = mix(0.9, 0.2, g);
		ROUGHNESS = mix(0.32, 0.8, g);
	} else {
		float core = 1.0 - smoothstep(0.02, 0.02 + 2.0 * px, d);
		float halo = exp(-d / 0.09) * 0.45;
		float r = length(uv) * 2.0;
		vec2 gl = abs(fract(uv * 8.0) - 0.5);
		float grat = (step(0.48, gl.x) + step(0.48, gl.y)) * 0.05 * (1.0 - step(1.0, r));
		ALBEDO = vec3(0.01, 0.025, 0.015);
		ROUGHNESS = 0.15;
		EMISSION = phosphor * (core * 2.4 + halo + grat) * (1.0 - smoothstep(0.92, 1.0, r));
	}
}
