shader_type spatial;
// Soft additive light shaft for the Lumen beam (cylinder mesh along local -Z).
render_mode blend_add, unshaded, depth_draw_never, cull_disabled, shadows_disabled;

uniform vec4 color : source_color = vec4(0.78, 0.96, 1.0, 1.0);
uniform float energy = 1.6;
uniform float flow_speed = 1.4;

varying vec3 lpos;

void vertex() {
	lpos = VERTEX;
}

void fragment() {
	float edge = pow(clamp(abs(dot(NORMAL, VIEW)), 0.0, 1.0), 1.8);
	float motes = 0.85 + 0.15 * sin(lpos.z * 18.0 + TIME * flow_speed * 6.0) * sin(lpos.z * 7.0 - TIME * 2.0);
	ALBEDO = color.rgb * energy * edge * motes;
}
