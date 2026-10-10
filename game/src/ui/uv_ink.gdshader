shader_type canvas_item;
// Fluorescent ink glowing under the UV lamp, for a picture (a glyph drawn in white on transparent): the strokes in
// pale mint with a whiter core, and a soft halo around them that fades out inside the rect (the picture is drawn
// inset by `inset` on every side to leave room for it).

uniform vec4 ink : source_color = vec4(0.58, 1.0, 0.84, 1.0);
uniform float inset = 0.14; // fraction of the rect kept free on each side for the halo
uniform float spread = 0.06; // halo reach, in UV of the picture
uniform float halo = 0.85; // halo strength
uniform float strength : hint_range(0.0, 1.0) = 1.0;

float stroke(sampler2D tex, vec2 uv) {
	if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) {
		return 0.0;
	}
	return texture(tex, uv).a;
}

void fragment() {
	vec2 uv = (UV - vec2(inset)) / (1.0 - 2.0 * inset);
	float core = stroke(TEXTURE, uv);
	float g = 0.0;
	float wsum = 0.0;
	for (int i = 0; i < 12; i++) {
		float ang = float(i) * 0.5235988 + 0.26;
		vec2 dir = vec2(cos(ang), sin(ang));
		for (int k = 1; k <= 3; k++) {
			float w = 1.0 / float(k);
			g += stroke(TEXTURE, uv + dir * spread * float(k)) * w;
			wsum += w;
		}
	}
	g = g / wsum;
	vec3 col = mix(ink.rgb, vec3(1.0), core * 0.15);
	float a = max(core, smoothstep(0.0, 0.45, g) * halo * 0.7);
	COLOR = vec4(col, a * strength);
}
