shader_type spatial;
// The Sun's beam, folded tower to tower (docs/models/ch4.md §5): the ribbons of beam_segment.glb as one MultiMesh. The
// instance colour carries r = brightness, g = length / 40 m, b = 1 for a stub that fades out (the beam stops at the
// ring that is not in line), a = flicker amount. Unshaded and additive, soft at the edges, with slow motes in it.
render_mode blend_add, unshaded, depth_draw_never, cull_disabled, shadows_disabled;

uniform vec3 tint : source_color = vec3(0.80, 0.96, 1.0);
uniform float energy = 0.9;

varying vec4 inst;

void vertex() {
	inst = COLOR;
}

void fragment() {
	float across = 1.0 - abs(UV.x * 2.0 - 1.0);
	float core = pow(across, 2.4);
	float halo = pow(across, 0.9) * 0.30;
	float along = UV.y * inst.g * 40.0;
	float motes = 0.86 + 0.14 * sin(along * 2.7 - TIME * 6.0) * sin(along * 1.1 + TIME * 1.7);
	float tail = mix(1.0, 1.0 - smoothstep(0.25, 1.0, UV.y), inst.b);
	float head = smoothstep(0.0, 0.015, UV.y);
	float flick = 1.0 - inst.a * (0.35 + 0.35 * sin(TIME * 41.0 + along * 0.7) + 0.3 * sin(TIME * 23.0));
	ALBEDO = tint * (core + halo) * motes * tail * head * inst.r * flick * energy;
}
