shader_type spatial;
// The pool of light an echo stands in (Chapter 4): a thin ring and a soft glow on the floor under the figure's feet, so a
// figure of light reads as standing on the deck and not hovering above it. `intensity` is faded with the figure.
render_mode blend_add, unshaded, depth_draw_never, cull_disabled, shadows_disabled;

uniform vec4 tint : source_color = vec4(0.62, 0.9, 1.0, 1.0);
uniform float intensity = 1.0;

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float r = length(p);
	float ring = smoothstep(1.0, 0.9, r) * smoothstep(0.7, 0.88, r);
	float glow = smoothstep(1.0, 0.1, r) * 0.1;
	float pulse = 0.92 + 0.08 * sin(TIME * 2.4);
	float a = clamp((ring * 0.5 + glow) * intensity * pulse, 0.0, 1.0);
	ALBEDO = tint.rgb;
	ALPHA = a;
}
