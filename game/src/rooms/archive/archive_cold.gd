class_name ArchiveCold
extends RefCounted
## Chapter 2 expansion, room R4: the Cold Store (docs/CHAPTER2_EXPANSION.md N4-N6).
## SKELETON: the real zone arrives in the next commit.

const VIEWS: Array[String] = ["cold"]

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
