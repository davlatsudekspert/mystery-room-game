shader_type spatial;
// The archive's cinema screen: a film frame (blurred by the projector's focus) and/or a lantern slide.
// The slide is a dark ink image on clear glass, so it projects as a bright field with a dark mark.
render_mode unshaded, cull_back, shadows_disabled;

uniform sampler2D image : source_color, filter_linear, repeat_disable;
uniform sampler2D slide : source_color, filter_linear, repeat_disable;
uniform float image_on = 0.0;
uniform float slide_on = 0.0;
uniform float slide_rot = 0.0; // radians, clockwise as seen
uniform float white = 0.0; // lamp on with no film threaded
uniform float blur = 0.0; // 0 sharp .. 1 very soft
uniform float brightness = 1.0;
uniform vec3 base_color : source_color = vec3(0.10, 0.10, 0.095);
const float ASPECT = 1.5; // 2.4 m × 1.6 m

vec3 soft(vec2 uv, float r) {
	if (r < 0.0005) {
		return texture(image, uv).rgb;
	}
	vec3 acc = vec3(0.0);
	float w = 0.0;
	for (int i = 0; i < 16; i++) {
		float a = float(i) * 2.39996;
		float d = sqrt((float(i) + 0.5) / 16.0);
		vec2 o = vec2(cos(a), sin(a)) * d * r * vec2(1.0, ASPECT);
		acc += texture(image, uv + o).rgb;
		w += 1.0;
	}
	return acc / w;
}

void fragment() {
	vec2 uv = UV;
	float t = TIME;
	float fl = 1.0 - 0.05 * (0.5 + 0.5 * sin(t * 48.0)) - 0.03 * (0.5 + 0.5 * sin(t * 13.0 + 1.7));
	vec3 col = base_color;
	vec3 lamp = vec3(1.0, 0.97, 0.9);
	float lit = max(max(image_on, slide_on), white);
	if (lit > 0.0) {
		col = mix(col, lamp * 1.25, lit);
	}
	if (image_on > 0.0) {
		vec3 img = soft(uv, blur * 0.018);
		float grain = fract(sin(dot(uv * 900.0 + t, vec2(12.9898, 78.233))) * 43758.5453);
		img = img * (0.92 + 0.08 * grain);
		col = mix(col, img * 1.45, image_on * (1.0 - 0.45 * slide_on));
	}
	if (slide_on > 0.0) {
		vec2 p = (uv - 0.5) * vec2(ASPECT, 1.0);
		float c = cos(slide_rot);
		float s = sin(slide_rot);
		p = vec2(c * p.x - s * p.y, s * p.x + c * p.y);
		vec2 g = p / 0.85 + 0.5;
		float ink = 0.0;
		if (g.x > 0.0 && g.y > 0.0 && g.x < 1.0 && g.y < 1.0) {
			ink = texture(slide, g).a;
		}
		col = mix(col, col * (1.0 - 0.85 * ink), slide_on);
	}
	float v = 1.0 - 0.32 * length((uv - 0.5) * vec2(1.0, 1.3));
	ALBEDO = col * v * fl * brightness;
}
