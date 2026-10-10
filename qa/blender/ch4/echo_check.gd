extends SceneTree

const MODELS := ["echo_crowd", "echo_named", "echo_strand_desk", "echo_leyla_1998_lift", "echo_leyla_1998_lens",
	"echo_tech_panel", "echo_tech_wheels", "echo_clerk_post"]


func _init() -> void:
	var bad := 0
	for m in MODELS:
		var ps := load("res://assets/models/%s.glb" % m) as PackedScene
		if ps == null:
			print("MISSING ", m)
			bad += 1
			continue
		var root := ps.instantiate()
		var meshes := 0
		var tris := 0
		var names: PackedStringArray = []
		var surf_bad := 0
		var stack: Array = [root]
		while stack.size() > 0:
			var n: Node = stack.pop_back()
			names.append(str(n.name))
			if n is MeshInstance3D:
				var mi := n as MeshInstance3D
				meshes += 1
				if mi.mesh.get_surface_count() != 1:
					surf_bad += 1
				var arr := mi.mesh.surface_get_arrays(0)
				tris += (arr[Mesh.ARRAY_INDEX] as PackedInt32Array).size() / 3
				var mat := mi.mesh.surface_get_material(0)
				if mat == null or str(mat.resource_name) != "M_Echo" and not str(mat.resource_name).begins_with("M_Echo"):
					print("  material of ", n.name, ": ", mat.resource_name if mat else "null")
				var t := mi.transform.origin
				if t.length() > 1e-4:
					print("  NOT AT ORIGIN ", n.name, t)
			for c in n.get_children():
				stack.append(c)
		print(m, ": ", meshes, " meshes, ", tris, " tris, surfaces!=1: ", surf_bad, ", nodes: ", ", ".join(names))
		root.free()
	print("echo_check done, problems ", bad)
	quit()
