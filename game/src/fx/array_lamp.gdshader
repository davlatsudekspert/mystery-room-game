shader_type spatial;
// The roll board's forty-two lamps as one MultiMesh: dark glass, and the instance colour (rgb = the lamp's colour,
// a = how lit it is) drives the emission, so the finale can put them out one by one.
varying vec4 inst;

void vertex() {
	inst = COLOR;
}

void fragment() {
	ALBEDO = mix(vec3(0.05, 0.045, 0.04), inst.rgb * 0.5, inst.a);
	ROUGHNESS = 0.18;
	EMISSION = inst.rgb * inst.a * 2.2;
}
