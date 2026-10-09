class_name ItemDress
extends RefCounted
## Per-item variations of shared item models: tape labels per year, recorded images on Lumen crystals,
## punched holes on request cards. Used by the room, the inspect view and the inventory icons, so an item
## always looks the same everywhere.

const GLYPHS := {
	"mark": "res://assets/textures/decals/ch2/glyph_mark.png",
	"sign": "res://assets/textures/decals/ch2/glyph_sign.png",
}
const PUNCH_CODE: Array[int] = [1, 0, 1, 1, 0, 0, 1, 0]


static func apply(id: String, node: Node3D, logic: RoomLogic = null) -> void:
	if node == null:
		return
	if id.begins_with("tape_"):
		var label := ModelUtil.find(node, "label") as MeshInstance3D
		var m := ModelUtil.load_material("M_Decal_TapeLabel_" + id.substr(5))
		if label and m:
			label.material_override = m
	elif id in ["crystal_sign", "crystal_mark"]:
		glyph(node, "sign" if id == "crystal_sign" else "mark")
	elif id == "request_card" or id == "blank_card":
		var pattern: Array = []
		if id == "request_card" and logic != null and logic.state.has("last_punch"):
			pattern = logic.state["last_punch"]
		for i in 8:
			var h := ModelUtil.find(node, "hole_%d" % i)
			if h:
				h.visible = i < pattern.size() and int(pattern[i]) == 1
	DecalLoc.apply(node) # badge, cards and labels show their words in the current language


## Show a recorded image glowing on a crystal's front face (`crystal_face`, UV 0..1).
static func glyph(node: Node3D, image: String) -> void:
	var face := ModelUtil.find(node, "crystal_face") as MeshInstance3D
	if face == null or not GLYPHS.has(image) or not ResourceLoader.exists(GLYPHS[image]):
		return
	var m := StandardMaterial3D.new()
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.albedo_color = Color(0.8, 0.96, 1.0, 0.55)
	m.albedo_texture = load(GLYPHS[image])
	m.emission_enabled = true
	m.emission = Color("cff6ff")
	m.emission_energy_multiplier = 2.2
	m.emission_texture = m.albedo_texture
	m.roughness = 0.1
	face.material_override = m
