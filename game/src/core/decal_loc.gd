class_name DecalLoc
extends RefCounted
## Language variants of decals that show words (badge, index card, archive rules…), and per-game puzzle variants.
## The generator writes `<name>.png` (English) plus `<name>_ru.png` / `<name>_uz.png`. Materials keep pointing at
## the English file; this swaps the albedo texture of every decal material in a node tree to the current language.
## Decal materials are shared resources, so one swap covers every model, icon and inspect view that uses them.

const DECAL_MATERIAL_PREFIX := "res://assets/materials/M_Decal_"
const EN_META := "decal_en_path"

static var _touched: Array[StandardMaterial3D] = []
## Per-game puzzle variants (docs/VARIANTS.md): base file name -> suffix, e.g. "index_card" -> "_p3" picks
## index_card_p3.png (and index_card_p3_ru.png). Set by the room before it builds its models.
static var variant_suffix: Dictionary = {}


## Clear the variant table when a room is built (variants belong to one game).
static func set_variants(table: Dictionary) -> void:
	variant_suffix = table.duplicate()
	refresh()


## The language (and variant) version of an English texture path, or the path itself when there is none.
static func localized_path(en_path: String, lang: String = "") -> String:
	if en_path == "":
		return en_path
	var code := lang if lang != "" else Loc.current()
	var base := en_path.get_basename()
	var ext := en_path.get_extension()
	var suffix: String = variant_suffix.get(base.get_file(), "")
	if suffix != "" and ResourceLoader.exists("%s%s.%s" % [base, suffix, ext]):
		base += suffix
	var p := "%s.%s" % [base, ext]
	if code != "en":
		var lp := "%s_%s.%s" % [base, code, ext]
		if ResourceLoader.exists(lp):
			p = lp
	return p if ResourceLoader.exists(p) else en_path


## Swap every decal material under `root` to the current language.
static func apply(root: Node) -> void:
	for mi in ModelUtil.find_meshes(root):
		var mesh := mi.mesh
		if mesh == null:
			continue
		for i in mesh.get_surface_count():
			var m := mi.get_active_material(i) as StandardMaterial3D
			if m != null and m.resource_path.begins_with(DECAL_MATERIAL_PREFIX):
				_swap(m)


## Re-apply to every material already seen (after a language change).
static func refresh() -> void:
	for m in _touched:
		if is_instance_valid(m):
			_swap(m)


static func _swap(m: StandardMaterial3D) -> void:
	if not m.has_meta(EN_META):
		if m.albedo_texture == null:
			return
		m.set_meta(EN_META, m.albedo_texture.resource_path)
		_touched.append(m)
	var want := localized_path(str(m.get_meta(EN_META)))
	if m.albedo_texture == null or m.albedo_texture.resource_path != want:
		m.albedo_texture = load(want) as Texture2D
