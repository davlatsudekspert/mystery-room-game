shader_type spatial;
// The cold shaft of daylight down the oculus once the vent opens: a faint cone, brightest at the top and along its
// middle, with slow dust-like banding. Additive and unshaded; `strength` fades it in.
render_mode blend_add, unshaded, depth_draw_never, cull_disabled, shadows_disabled;

uniform vec3 tint : source_color = vec3(0.62, 0.78, 1.0);
uniform float strength = 0.0;

varying vec3 lpos;

void vertex() {
	lpos = VERTEX;
}

void fragment() {
	float edge = pow(clamp(abs(dot(NORMAL, VIEW)), 0.0, 1.0), 1.6);
	float h = clamp(lpos.y * 0.5 + 0.5, 0.0, 1.0); // cylinder mesh spans -1..1 in y after scaling by the node
	float bands = 0.8 + 0.2 * sin(lpos.y * 14.0 + TIME * 0.6) * sin(lpos.x * 9.0 - TIME * 0.35);
	ALBEDO = tint * edge * (0.25 + 0.75 * h) * bands * strength;
}
