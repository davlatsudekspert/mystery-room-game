# Chapter 3 group A: shell, lift, doors and shared art (measured results)

Contract: `docs/models/ch3.md` §0–§3, §11–§14. Models: `blast_door`, `array_below`, `shell_gallery`,
`freight_lift`, `shell_lift`, `shell_choir`, `shell_nursery`. Shared art: `tools/blender/lib_ch3_symbols.py`, the
new material slots, `tools/textures/make_decals_ch3.py` (decals, symbol images, texture sets) and the seed-0
shader-quad previews.

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [--shots=1,2,...]
python3 tools/textures/make_decals_ch3.py [--only symbols,interlock_plate,...] [--no-sheet]
python3 tools/materials/make_extra_materials.py
```

Scripts: `tools/blender/models/<name>.py`, helpers in `tools/blender/lib_ch3_a.py` (on top of `mrlib`,
`lib_mech`, `lib_arch`, `lib_props`, `lib_ch2_vault`, `lib_ch2_arch`; none of those were edited), build list
`tools/blender/build_lists/ch3_a.txt`. Every script builds its geometry directly in Godot axes (the
`lib_ch2_vault` "G-frame"), converts to Blender axes before parenting, exports `game/assets/models/<name>.glb`
and then **reads the GLB back**: required node names, parents, model-space positions (1 mm), identity rest
rotations, mount rotations, triangles, surfaces (mesh nodes × primitives) and material slots against §13, and
`check_glb_names.py` (passes on all seven GLBs).

QA renders: Cycles, 32 samples, 960 × 640, 2 threads, cameras from the §2 views (Godot position, target and
vertical FOV), neighbouring group-A GLBs imported. **Blender QA renders only, not Godot screenshots.** In the
renders the lamp glasses, jewels and Array rings get a QA-only emissive override (the code turns emission on in
the game); shader quads show the seed-0 preview images.

All coordinates are **Godot, metres**; models face +Z; angles follow §0 (positive = counter-clockwise looking
down the +axis).

MEASUREMENTS
