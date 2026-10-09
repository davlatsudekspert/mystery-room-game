class_name ModelUtil
extends RefCounted
## Loads GLB models, swaps Blender preview materials for the game's material library by slot name,
## and builds tap colliders: a box per interactive part (IA_*) and trimesh blockers for big static meshes.

const MAT_DIR := "res://assets/materials/%s.tres"
const LARGE_PART_M := 0.15
static var _mat_cache: Dictionary = {}


static func load_material(slot_name: String) -> Material:
	var base := slot_name.get_slice(".", 0) # strip Blender ".001" suffixes
	if _mat_cache.has(base):
		return _mat_cache[base]
	var path := MAT_DIR % base
	var m: Material = load(path) if ResourceLoader.exists(path) else null
	_mat_cache[base] = m
	return m


## Instantiate a model under `parent`. Returns null (with a warning) if the file is missing.
static func spawn(model: String, parent: Node3D, xform: Transform3D = Transform3D.IDENTITY,
		colliders: String = "parts") -> Node3D:
	var path := model if model.begins_with("res://") else "res://assets/models/%s.glb" % model
	if not ResourceLoader.exists(path):
		push_warning("Model missing: " + path)
		return null
	var scene: PackedScene = load(path)
	var inst: Node3D = scene.instantiate()
	inst.name = model.get_file().get_basename()
	parent.add_child(inst)
	inst.transform = xform
	apply_materials(inst)
	if colliders != "none":
		build_colliders(inst, colliders)
	return inst


static func apply_materials(root: Node) -> void:
	for mi: MeshInstance3D in find_meshes(root):
		var mesh := mi.mesh
		if mesh == null:
			continue
		for i in mesh.get_surface_count():
			var src := mesh.surface_get_material(i)
			if src == null:
				continue
			var m := load_material(src.resource_name)
			if m != null:
				mi.set_surface_override_material(i, m)


static func find_meshes(root: Node) -> Array[MeshInstance3D]:
	var out: Array[MeshInstance3D] = []
	if root is MeshInstance3D:
		out.append(root)
	for c in root.get_children():
		out.append_array(find_meshes(c))
	return out


## Small interactive parts (IA_*) get a snug box (a generous, stable tap target). Everything else gets
## an exact trimesh so furniture never swallows taps meant for objects sitting on or inside it.
## mode "static": the same, used for the room shell.
static func build_colliders(root: Node3D, mode: String) -> void:
	for mi: MeshInstance3D in find_meshes(root):
		if mi.mesh == null:
			continue
		var body := StaticBody3D.new()
		body.name = "Col"
		body.collision_layer = 1
		body.collision_mask = 0
		var shape := CollisionShape3D.new()
		var is_ia := mi.name.begins_with("IA_")
		# Large interactive parts (drawers, doors, panels) get an exact trimesh too, so their bounding box
		# never covers the small controls mounted on them (drawer digits, knobs, keyholes).
		if is_ia and mi.mesh.get_aabb().get_longest_axis_size() <= LARGE_PART_M:
			var aabb := mi.mesh.get_aabb()
			var box := BoxShape3D.new()
			box.size = (aabb.size + Vector3.ONE * 0.004).max(Vector3.ONE * 0.012)
			shape.shape = box
			shape.position = aabb.get_center()
		else:
			shape.shape = mi.mesh.create_trimesh_shape()
		body.add_child(shape)
		mi.add_child(body)
		body.set_meta("part", str(mi.name) if is_ia else "")


## Give one interactive part its exact shape instead of the padded box. For tabbed cards and divider guides
## standing in a row: a box would cover the empty space beside each tab and steal taps meant for the card behind.
## (Not for rings or holes, such as a rotary dial: there the padded box is what makes the hole tappable.)
static func use_exact_collider(mi: MeshInstance3D) -> void:
	if mi == null or mi.mesh == null:
		return
	for body in mi.get_children():
		if body is StaticBody3D:
			for cs in body.get_children():
				if cs is CollisionShape3D:
					var tri := mi.mesh.create_trimesh_shape()
					tri.backface_collision = true # a card can be tapped from either side
					(cs as CollisionShape3D).shape = tri
					(cs as CollisionShape3D).position = Vector3.ZERO


## Find a node by exact name anywhere below root (GLB hierarchies can nest).
static func find(root: Node, node_name: String) -> Node3D:
	if root == null:
		return null
	var n := root.find_child(node_name, true, false)
	return n as Node3D


static func set_emission(mi: MeshInstance3D, on: bool, color: Color = Color.WHITE, energy: float = -1.0) -> void:
	if mi == null:
		return
	for i in mi.get_surface_override_material_count():
		var m := mi.get_active_material(i)
		if m is BaseMaterial3D:
			var u := (m as BaseMaterial3D).duplicate() as BaseMaterial3D
			u.emission_enabled = on
			if color != Color.WHITE:
				u.emission = color
			if energy >= 0.0:
				u.emission_energy_multiplier = energy
			mi.set_surface_override_material(i, u)
