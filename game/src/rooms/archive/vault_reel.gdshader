shader_type spatial;
// The vault reel on Leyla's pull-down screen (Chapter 2 finale): the 1979 frame with a projector's flicker, and the
// reveal of the 42nd silhouette at the right edge: the rest of the frame dims and a cold halo grows around her.
render_mode unshaded, cull_back;

uniform sampler2D reel : source_color, filter_linear_mipmap;
uniform float on = 1.0;         // 0 = dark screen
uniform float reveal = 0.0;     // 0..1
uniform vec2 focus = vec2(0.955, 0.66);  // the 42nd figure (UV)
uniform vec2 focus_size = vec2(0.05, 0.2);

void fragment() {
	vec3 c = texture(reel, UV).rgb * vec3(1.0, 0.97, 0.9);
	float t = TIME;
	float flick = 0.95 + 0.05 * sin(t * 37.0) * sin(t * 11.3);
	c *= mix(0.1, flick, on);
	vec2 d = (UV - focus) / focus_size;
	float r = length(d);
	float outside = smoothstep(0.9, 2.2, r);
	c *= mix(1.0, 0.38, reveal * outside);
	float halo = exp(-r * r * 1.4);
	float rim = exp(-pow((r - 1.15) * 2.6, 2.0));
	float pulse = 0.85 + 0.15 * sin(t * 2.6);
	c += vec3(0.62, 0.9, 1.0) * (halo * 0.42 + rim * 0.22) * reveal * pulse * on;
	ALBEDO = min(c, vec3(1.15));
}
