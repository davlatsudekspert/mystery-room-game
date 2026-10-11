extends TestBase
## ModelUtil.merge_static: many small static meshes draw as one mesh per material. Code-built props use primitive
## meshes (BoxMesh, PrismMesh, CylinderMesh), which do not expose surface_get_format to scripts; the Ch2 aisle
## sign stopped on that with a script error and was never merged.


func _box(parent: Node3D, n: String, mat: Material, pos: Vector3) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.name = n
	mi.mesh = BoxMesh.new()
	mi.material_override = mat
	mi.position = pos
	parent.add_child(mi)
	return mi


func test_merges_primitive_meshes() -> void:
	var root := Node3D.new()
	var green := StandardMaterial3D.new()
	var brass := StandardMaterial3D.new()
	var a := _box(root, "a", green, Vector3(0, 0, 0))
	var b := _box(root, "b", green, Vector3(1, 0, 0))
	var c := MeshInstance3D.new()
	c.name = "c"
	c.mesh = PrismMesh.new()
	c.material_override = brass
	root.add_child(c)
	var d := MeshInstance3D.new()
	d.name = "d"
	d.mesh = CylinderMesh.new()
	d.material_override = brass
	root.add_child(d)
	var merged := ModelUtil.merge_static(root, "")
	check(merged != null, "primitive meshes merge")
	if merged != null:
		eq(merged.mesh.get_surface_count(), 2, "one surface per material")
		check(merged.mesh.get_aabb().size.x >= 1.9, "the merged mesh keeps each part's position")
	check(not a.visible and not b.visible and not c.visible and not d.visible, "the originals hide")
	root.free()


func test_merges_array_meshes_by_prefix() -> void:
	var root := Node3D.new()
	var mat := StandardMaterial3D.new()
	var parts: Array[MeshInstance3D] = []
	for i in 3:
		var am := ArrayMesh.new()
		am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, BoxMesh.new().surface_get_arrays(0))
		var mi := MeshInstance3D.new()
		mi.name = "book_%d" % i
		mi.mesh = am
		mi.material_override = mat
		root.add_child(mi)
		parts.append(mi)
	var other := _box(root, "frame", mat, Vector3.ZERO)
	var merged := ModelUtil.merge_static(root, "book_")
	check(merged != null, "array meshes merge")
	if merged != null:
		eq(merged.mesh.get_surface_count(), 1, "one material, one surface")
	for mi in parts:
		check(not mi.visible, "%s hides" % mi.name)
	check(other.visible, "a part without the prefix stays")
	root.free()
