class_name ArchiveCell
extends RefCounted
## Chapter 2 expansion, room R3: the Night Cell (docs/CHAPTER2_EXPANSION.md N3; docs/models/ch2_exp.md "R3 Night Cell").
## SKELETON: the real zone arrives in the next commit (views, light table, cold door, kettle, diary).

const VIEWS: Array[String] = ["cell"]

var room: Node3D
var zones: ArchiveZones
var root: Node3D
var logic: ArchiveLogic


func _init(r: Node3D, z: ArchiveZones, zone_root: Node3D) -> void:
	room = r
	zones = z
	root = zone_root
	logic = r.get("logic")


func build() -> void:
	pass
