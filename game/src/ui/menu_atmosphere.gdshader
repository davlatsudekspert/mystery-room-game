shader_type canvas_item;
// Main menu atmosphere over the 3D backdrop (a 2D canvas shader: no 3D shader, cheap on phone GPUs):
//   - a heavy vignette centred on the hero object (and toward the screen edges), so the scene falls off into
//     darkness;
//   - a dark gradient behind the menu column on the left, so the menu text reads over any frame;
//   - a soft warm glow behind the logo.
// main_menu.gd sets the uniforms from its layout (UV units: 0..1 across the screen).

uniform vec2 canvas = vec2(1920.0, 1080.0); // canvas size in px (the vignette is round in screen space)
uniform vec2 focus = vec2(0.7, 0.55); // the hero object's centre
uniform float column_end = 0.45; // the legibility gradient has faded out here (x)
uniform float column_dark = 0.8;
uniform float vignette = 0.96;
uniform float vignette_inner = 0.16; // radius (in screen heights) that stays clear around the hero
uniform float vignette_outer = 0.9;
uniform float edges = 0.55; // plus a classic darkening toward the screen edges and corners
uniform vec3 shade : source_color = vec3(0.012, 0.014, 0.016);
uniform vec2 glow_center = vec2(0.2, 0.3);
uniform vec2 glow_radius = vec2(0.2, 0.25);
uniform float glow = 0.0; // 0..1 (the menu fades it in with the logo)
uniform vec3 glow_color : source_color = vec3(1.0, 0.66, 0.3);


float hash(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}


void fragment() {
	vec2 uv = UV;
	float l = 1.0 - smoothstep(0.0, column_end, uv.x);
	l = column_dark * l;
	vec2 d = (uv - focus) * canvas / canvas.y;
	float v = vignette * smoothstep(vignette_inner, vignette_outer, length(d));
	v = 1.0 - (1.0 - v) * (1.0 - edges * smoothstep(0.3, 0.75, length(uv - vec2(0.5))));
	float dark = 1.0 - (1.0 - l) * (1.0 - v);
	vec2 g = (uv - glow_center) / glow_radius;
	float gl = glow * 0.2 * exp(-dot(g, g) * 1.6);
	// result = scene * (1 - dark) * (1 - gl) + shade * dark * (1 - gl) + glow_color * gl
	float a = 1.0 - (1.0 - dark) * (1.0 - gl);
	vec3 rgb = (shade * dark * (1.0 - gl) + glow_color * gl) / max(a, 0.0001);
	a = clamp(a + (hash(FRAGCOORD.xy) - 0.5) / 160.0, 0.0, 1.0); // dither: no banding in the dark gradients
	COLOR = vec4(rgb, a);
}
