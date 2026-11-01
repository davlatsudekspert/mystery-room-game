extends TestBase
## The Pump Room's pipe board draws each variant graph without crossing pipes (docs/CHAPTER2_EXPANSION.md N2).


func test_every_pipe_graph_lays_out_without_crossings() -> void:
	for g in ArchiveExpData.PIPE_GRAPHS.size():
		var graph: Array = ArchiveExpData.PIPE_GRAPHS[g]
		var pos := ArchivePump.layout(graph)
		eq(pos.size(), 6, "graph %d: six nodes placed" % g)
		eq(ArchivePump.crossings(graph, pos), 0, "graph %d: no crossing pipes, none through a foreign node" % g)
		for i in pos.size():
			for j in range(i + 1, pos.size()):
				check(pos[i] != pos[j], "graph %d: nodes %d and %d do not share a spot" % [g, i, j])


func test_diagram_texture_is_drawn() -> void:
	var graph: Array = ArchiveExpData.PIPE_GRAPHS[0]
	var tex := ArchivePump.diagram_texture(graph, ArchivePump.layout(graph))
	check(tex != null and tex.get_width() == 460, "the diagram is a 460 px wide image")
