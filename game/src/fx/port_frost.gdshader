shader_type canvas_item;
// The edge of a crystal inspection port's memory (docs/models/ch3.md §11): a cold, frosted vignette over the
// screen while the player looks through a port at a kept 1979 moment. No gameplay role.

uniform float strength : hint_range(0.0, 1.0) = 1.0;
uniform vec3 frost : source_color = vec3(0.78, 0.92, 1.0);

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(269.5, 183.3))) * 43758.5453);
}

void fragment() {
	vec2 p = UV - 0.5;
	p.x *= SCREEN_PIXEL_SIZE.y / SCREEN_PIXEL_SIZE.x;
	float r = length(p) / 0.62;
	float crystals = hash(floor(UV * 180.0)) * 0.35;
	float a = smoothstep(0.62, 1.0, r + crystals * 0.25) * 0.85;
	a += 0.04 * sin(TIME * 1.7 + r * 9.0);
	COLOR = vec4(frost, clamp(a, 0.0, 0.9) * strength);
}
