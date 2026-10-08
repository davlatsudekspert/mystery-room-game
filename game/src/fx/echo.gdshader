shader_type spatial;
// "Light echo" of a person kept by the Lumen Array: fresnel rim glow with drifting scanlines.
render_mode blend_add, unshaded, depth_draw_never, cull_back, shadows_disabled;

uniform vec4 tint : source_color = vec4(0.72, 0.93, 1.0, 1.0);
uniform float intensity = 1.0;
uniform float rim_power = 2.2;
uniform float body = 0.10;

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), rim_power);
	float lines = 0.8 + 0.2 * sin(wpos.y * 140.0 - TIME * 6.0);
	float shimmer = 0.9 + 0.1 * sin(TIME * 3.1 + wpos.x * 5.0);
	ALBEDO = tint.rgb * (body + fres) * lines * shimmer * intensity;
}
