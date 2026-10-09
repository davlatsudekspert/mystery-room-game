shader_type spatial;
// Lattice glyphs of the seed library (docs/models/ch3.md §6 / §11, E1). A flat-topped regular hexagon of
// circumradius 0.42 of its cell; edge e (0..5) runs clockwise from the top, its outward normal at 90° - 60° e
// (counter-clockwise from +u). Bit e set = a V-notch at the edge midpoint, 0.30 of the edge wide and 0.22 of the
// apothem deep. A clockwise third of a turn shifts edge e to e + 2 (UndergroundLogic.rotate_glyph).
// grid 4 × 3: the glyph panel (cell i = 4 r + c covers u ∈ [c/4, (c+1)/4], v ∈ [(2-r)/3, (3-r)/3]); 1 × 1: one glyph.
// style 0 = an engraved enamel plate, 1 = a pencil sketch (outline only). Alpha is 0 outside the hexagon.
render_mode cull_back, depth_draw_opaque;

uniform int bits[12];
uniform ivec2 grid = ivec2(4, 3);
uniform int hidden = -1;
uniform int style = 0;
uniform vec3 enamel : source_color = vec3(0.86, 0.83, 0.74);
uniform vec3 engraving : source_color = vec3(0.13, 0.10, 0.08);
uniform vec3 graphite : source_color = vec3(0.24, 0.24, 0.27);

const float R = 0.42;

float sd_triangle(vec2 p, vec2 p0, vec2 p1, vec2 p2) {
	vec2 e0 = p1 - p0, e1 = p2 - p1, e2 = p0 - p2;
	vec2 v0 = p - p0, v1 = p - p1, v2 = p - p2;
	vec2 pq0 = v0 - e0 * clamp(dot(v0, e0) / dot(e0, e0), 0.0, 1.0);
	vec2 pq1 = v1 - e1 * clamp(dot(v1, e1) / dot(e1, e1), 0.0, 1.0);
	vec2 pq2 = v2 - e2 * clamp(dot(v2, e2) / dot(e2, e2), 0.0, 1.0);
	float s = sign(e0.x * e2.y - e0.y * e2.x);
	vec2 d = min(min(vec2(dot(pq0, pq0), s * (v0.x * e0.y - v0.y * e0.x)),
		vec2(dot(pq1, pq1), s * (v1.x * e1.y - v1.y * e1.x))),
		vec2(dot(pq2, pq2), s * (v2.x * e2.y - v2.y * e2.x)));
	return -sqrt(d.x) * sign(d.y);
}

float glyph_sdf(vec2 p, int mask) {
	float a = R * 0.8660254;
	float d = -1.0;
	for (int e = 0; e < 6; e++) {
		float ang = radians(90.0 - 60.0 * float(e));
		d = max(d, dot(p, vec2(cos(ang), sin(ang))) - a);
	}
	float hw = 0.15 * R;
	float depth = 0.22 * a;
	for (int e = 0; e < 6; e++) {
		if (((mask >> e) & 1) == 0) {
			continue;
		}
		float ang = radians(90.0 - 60.0 * float(e));
		vec2 n = vec2(cos(ang), sin(ang));
		vec2 t = vec2(-n.y, n.x);
		vec2 m = n * a;
		float over = 0.02; // the cut opens a little beyond the edge, so no sliver of the edge is left
		vec2 b0 = m + n * over + t * hw * (1.0 + over / depth);
		vec2 b1 = m + n * over - t * hw * (1.0 + over / depth);
		d = max(d, -sd_triangle(p, b0, b1, m - n * depth));
	}
	return d;
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(41.3, 289.1))) * 17853.531);
}

void fragment() {
	vec2 uv = vec2(UV.x, 1.0 - UV.y);
	vec2 cell = uv * vec2(grid);
	int c = clamp(int(floor(cell.x)), 0, grid.x - 1);
	int r = (grid.y - 1) - clamp(int(floor(cell.y)), 0, grid.y - 1);
	int i = r * grid.x + c;
	vec2 p = fract(cell) - 0.5;
	float d = glyph_sdf(p, bits[clamp(i, 0, 11)]);
	float aa = max(fwidth(p.x), 0.002);
	float inside = 1.0 - smoothstep(-aa, aa, d);
	if (style == 0) {
		float groove = 1.0 - smoothstep(0.018, 0.018 + aa, abs(d + 0.035));
		ALBEDO = mix(enamel, engraving, groove);
		ALPHA = inside;
		ROUGHNESS = 0.3;
	} else {
		float line = 1.0 - smoothstep(0.010, 0.010 + aa, abs(d));
		line *= 0.75 + 0.25 * hash(floor(uv * 512.0));
		ALBEDO = graphite;
		ALPHA = line * 0.9;
		ROUGHNESS = 0.9;
	}
	if (i == hidden) {
		ALPHA = 0.0;
	}
}
