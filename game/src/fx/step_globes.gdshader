shader_type spatial;
// The control desk's step counter (docs/models/ch3.md §5 / §11, W4): five opal globes on a mast, globe k
// (1 = bottom) lit while k <= lit. The globe is found from its world height (y = base_y + spacing × (k - 1)), which
// is the same as the model's vertex colour R = 0.2 k but does not depend on how the colours were imported.
render_mode cull_back;

uniform int lit = 0;
uniform float base_y = 1.30;
uniform float spacing = 0.17;
uniform vec3 opal : source_color = vec3(0.86, 0.84, 0.78);
uniform vec3 glow : source_color = vec3(1.0, 0.78, 0.45);
uniform float energy = 2.6;

varying float wy;

void vertex() {
	wy = (MODEL_MATRIX * vec4(VERTEX, 1.0)).y;
}

void fragment() {
	int k = int(round((wy - base_y) / spacing)) + 1;
	bool on = k >= 1 && k <= lit;
	ALBEDO = on ? mix(opal, glow, 0.35) : opal * 0.82;
	ROUGHNESS = 0.35;
	EMISSION = on ? glow * energy : vec3(0.0);
}
