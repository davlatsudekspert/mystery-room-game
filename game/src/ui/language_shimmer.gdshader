shader_type canvas_item;
// A soft gold shimmer that sweeps across the title now and then (it only brightens the lettering: it is added
// where the logo is opaque). main/language_select.gd feeds `t` (seconds) so reduce_motion can simply stop feeding it.

uniform float t = -1.0; // seconds since the screen appeared; negative = off
uniform float period = 7.0; // one sweep per period
uniform float first = 1.4; // the first sweep starts this long after the logo is up
uniform float sweep_share = 0.42; // share of the period the sweep takes (the rest is stillness)
uniform float band = 0.13; // band half-width (in logo widths)
uniform float strength = 0.5;
uniform vec3 gold : source_color = vec3(1.0, 0.84, 0.5);

void fragment() {
	vec4 c = texture(TEXTURE, UV);
	float tt = t - first;
	if (t >= 0.0 && tt >= 0.0) {
		float ph = mod(tt, period) / period / sweep_share;
		if (ph <= 1.0) {
			float k = ph * ph * (3.0 - 2.0 * ph);
			float pos = mix(-0.35, 1.35, k);
			float x = UV.x + (UV.y - 0.5) * 0.35; // slanted band
			float d = (x - pos) / band;
			float fade = sin(3.14159265 * ph); // soft in and out
			c.rgb += gold * exp(-d * d) * fade * strength * c.a;
		}
	}
	COLOR = c;
}
