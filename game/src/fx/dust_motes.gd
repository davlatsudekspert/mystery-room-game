class_name DustMotes
extends GPUParticles3D
## Slow floating dust lit by the room's light shafts (cheap: ~120 billboard particles).


static func create(extents: Vector3, amount: int = 120) -> DustMotes:
	var p := DustMotes.new()
	p.amount = amount
	p.lifetime = 14.0
	p.preprocess = 14.0
	p.visibility_aabb = AABB(-extents, extents * 2.0)
	var mat := ParticleProcessMaterial.new()
	mat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	mat.emission_box_extents = extents
	mat.gravity = Vector3(0, -0.004, 0)
	mat.initial_velocity_min = 0.0
	mat.initial_velocity_max = 0.02
	mat.direction = Vector3(0.3, 0.1, 0.2)
	mat.spread = 180.0
	mat.turbulence_enabled = true
	mat.turbulence_noise_strength = 0.6
	mat.turbulence_noise_speed_random = 0.2
	mat.turbulence_influence_min = 0.02
	mat.turbulence_influence_max = 0.05
	mat.scale_min = 0.5
	mat.scale_max = 1.2
	p.process_material = mat
	var quad := QuadMesh.new()
	quad.size = Vector2(0.006, 0.006)
	var sm := StandardMaterial3D.new()
	sm.shading_mode = BaseMaterial3D.SHADING_MODE_PER_PIXEL
	sm.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	sm.albedo_color = Color(1.0, 0.95, 0.85, 0.55)
	sm.vertex_color_use_as_albedo = false
	quad.material = sm
	p.draw_pass_1 = quad
	return p
