shader_type spatial;
// The vault's frosted glass disc: the faint engraving, plus the images of the two port crystals
// rear-projected onto it. Left port: rotation only. Right port: rotation and zoom.
render_mode unshaded, cull_back, shadows_disabled, blend_mix;

uniform sampler2D engraving : source_color, filter_linear, repeat_disable;
uniform sampler2D left_img : source_color, filter_linear, repeat_disable;
uniform sampler2D right_img : source_color, filter_linear, repeat_disable;
uniform float left_on = 0.0;
uniform float right_on = 0.0;
uniform float rot_left = 0.0; // radians, clockwise as seen
uniform float rot_right = 0.0;
uniform float scale_right = 1.0;
uniform float unlocked = 0.0;
uniform vec3 glow : source_color = vec3(0.62, 0.95, 1.0);

float sample_img(sampler2D tex, vec2 uv, float rot, float scale) {
	vec2 p = uv - 0.5;
	float c = cos(rot);
	float s = sin(rot);
	// inverse rotation of the lookup turns the shown image clockwise (UV y points down)
	p = vec2(c * p.x + s * p.y, -s * p.x + c * p.y) / scale + 0.5;
	if (p.x < 0.0 || p.y < 0.0 || p.x > 1.0 || p.y > 1.0) {
		return 0.0;
	}
	return texture(tex, p).a;
}

void fragment() {
	float r = length(UV - 0.5);
	if (r > 0.5) {
		discard;
	}
	vec3 col = vec3(0.16, 0.19, 0.19) + vec3(0.06) * (1.0 - r * 2.0);
	float eng = texture(engraving, UV).a;
	col += vec3(0.85, 0.82, 0.72) * eng * 0.32;
	float l = sample_img(left_img, UV, rot_left, 1.0) * left_on;
	float rr = sample_img(right_img, UV, rot_right, scale_right) * right_on;
	float pulse = 0.85 + 0.15 * sin(TIME * 2.4);
	col += glow * (l + rr) * (1.1 + unlocked * 1.6) * pulse;
	col += glow * unlocked * 0.25 * (1.0 - r * 2.0);
	ALBEDO = col;
	ALPHA = 0.94;
}
