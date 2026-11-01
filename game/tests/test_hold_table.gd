extends TestBase
## The hands layer's data table (docs/CHAPTER2_EXPANSION.md section 12): every item is decided once, rows are well formed.


func test_every_item_has_a_row_or_is_listed_as_none() -> void:
	for id: String in ItemDB.ITEMS:
		check(HoldTable.ROWS.has(id) != HoldTable.NONE.has(id), "item %s has exactly one of a hold row or an explicit none" % id)
	for id: String in HoldTable.ROWS:
		check(ItemDB.exists(id), "hold row %s names a real item" % id)
	for id in HoldTable.NONE:
		check(ItemDB.exists(id), "none entry %s names a real item" % id)


func test_rows_are_complete() -> void:
	for id: String in HoldTable.ROWS:
		var r: Dictionary = HoldTable.ROWS[id]
		for k in ["pos", "rot", "scale", "audio"]:
			check(r.has(k), "row %s has %s" % [id, k])
		check(ResourceLoader.exists(str(r.get("model", ItemDB.model_path(id)))), "row %s: the model exists" % id)
		check((r["pos"] as Vector3).z < 0.0, "row %s lies in front of the camera" % id)


func test_audio_tools_map_keys() -> void:
	eq(HoldTable.audio_tool("mallet"), "mallet", "mallet")
	eq(HoldTable.audio_tool("wipe_cloth"), "cloth", "cloth")
	eq(HoldTable.audio_tool("uv_lamp"), "uvlamp", "uv lamp")
	eq(HoldTable.audio_tool("pass_key"), "keys", "any key maps to the keys foley")
	eq(HoldTable.audio_tool("notebook"), "", "documents have none")
