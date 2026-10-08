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
	quad.size = Vector2(0.008, 0.008)
	var sm := StandardMaterial3D.new()
	sm.shading_mode = BaseMaterial3D.SHADING_MODE_PER_PIXEL
	sm.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	sm.albedo_color = Color(1.0, 0.95, 0.85, 0.5)
	sm.albedo_texture = _soft_dot()
	sm.vertex_color_use_as_albedo = false
	# motes right in front of the lens would be huge, out-of-focus blobs: fade them out up close
	sm.distance_fade_mode = BaseMaterial3D.DISTANCE_FADE_PIXEL_ALPHA
	sm.distance_fade_min_distance = 0.25
	sm.distance_fade_max_distance = 0.9
	quad.material = sm
	p.draw_pass_1 = quad
	return p


## Round mote with a soft edge (a bare quad reads as a white square in close-ups).
static func _soft_dot() -> GradientTexture2D:
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	g.add_point(0.45, Color(1, 1, 1, 0.55))
	var t := GradientTexture2D.new()
	t.gradient = g
	t.width = 32
	t.height = 32
	t.fill = GradientTexture2D.FILL_RADIAL
	t.fill_from = Vector2(0.5, 0.5)
	t.fill_to = Vector2(1.0, 0.5)
	return t
