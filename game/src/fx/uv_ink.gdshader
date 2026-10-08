shader_type spatial;
// Fluorescent "invisible ink": glows only inside the UV lamp's cone (global uniforms set by UVTorch).
render_mode blend_add, unshaded, depth_draw_never, cull_disabled, shadows_disabled;

uniform sampler2D ink : source_color, filter_linear_mipmap, hint_default_white;
uniform bool use_texture = true;
uniform vec4 ink_color : source_color = vec4(0.62, 1.0, 0.86, 1.0);
uniform float strength = 1.6;
uniform float cone_cos = 0.975;
uniform float always = 0.0; // 1 = show regardless of light (debug/screenshots)

global uniform vec3 uv_light_pos;
global uniform vec3 uv_light_dir;
global uniform float uv_light_on;

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 to = normalize(wpos - uv_light_pos);
	float c = dot(to, normalize(uv_light_dir));
	float lit = smoothstep(cone_cos - 0.015, cone_cos + 0.01, c) * uv_light_on;
	lit = max(lit, always);
	float a = use_texture ? texture(ink, UV).a : 1.0;
	float flicker = 0.92 + 0.08 * sin(TIME * 23.0 + wpos.x * 40.0);
	ALBEDO = ink_color.rgb * a * lit * strength * flicker;
}
