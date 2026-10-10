shader_type spatial;
// The vault reel on Leyla's pull-down screen (Chapter 2 finale): the 1979 frame with a projector's flicker, and the
// reveal of the 42nd silhouette at the right edge: the rest of the frame dims and a cold halo grows around her.
render_mode unshaded, cull_back;

uniform sampler2D reel : source_color, filter_linear_mipmap;
uniform float on = 1.0;         // 0 = dark screen
uniform float reveal = 0.0;     // 0..1
uniform vec2 focus = vec2(0.955, 0.665);  // the 42nd figure (UV)
uniform vec2 focus_size = vec2(0.038, 0.19);

void fragment() {
	vec3 c = texture(reel, UV).rgb * vec3(1.0, 0.97, 0.9);
	float t = TIME;
	float flick = 0.95 + 0.05 * sin(t * 37.0) * sin(t * 11.3);
	c *= mix(0.1, flick, on);
	vec2 d = (UV - focus) / focus_size;
	float r = length(d);
	// the rest of the frame sinks back; she keeps her own light
	float outside = smoothstep(1.0, 2.4, r);
	c *= mix(1.0, 0.45, reveal * outside);
	// a cold rim around her silhouette and a faint glow on her: light memory catching on the edge of the frame
	float rim = exp(-pow((r - 1.05) * 4.5, 2.0));
	float glow = exp(-r * r * 2.6);
	float pulse = 0.82 + 0.18 * sin(t * 2.4);
	c += vec3(0.6, 0.88, 1.0) * (rim * 0.2 + glow * 0.12) * reveal * pulse * on;
	ALBEDO = min(c, vec3(1.15));
}
