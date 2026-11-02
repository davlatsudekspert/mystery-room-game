shader_type spatial;
// Depth pre-pass of Leyla's light echo: writes depth, no colour (see echo_leyla.gdshader).
render_mode blend_mix, unshaded, depth_draw_always, cull_back, shadows_disabled;

void fragment() {
	ALBEDO = vec3(0.0);
	ALPHA = 0.0;
}
