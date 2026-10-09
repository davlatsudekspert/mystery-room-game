# Chapter 2 group C1: archive hall devices (measured results)

Models: `tube_station`, `canister`, `compressor_panel`, `card_punch`, `tape_deck`.
Scripts: `tools/blender/models/<name>.py`, shared helpers in `tools/blender/lib_ch2_devices1.py`,
build list `tools/blender/build_lists/ch2_devices1.txt`. Contract: `docs/models/ch2.md` §0–§2, §5.

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render] [-- --only-views]
```

Every script exports `game/assets/models/<name>.glb`, then reads the GLB back (`verify_glb`): required
node names, parents, pivot positions (1 mm), identity rest rotation, triangle budget and Godot
import-hint suffixes. `check_glb_names.py` passes on all five GLBs. QA renders go to `qa/blender/ch2/`
(Cycles, 32 samples, 960 × 640 hero / 960 × 480 in-game views, 2 threads). In-room renders import
`room_archive.glb` and the neighbouring device GLBs; items that do not exist yet are proxies of the
contract size.

All coordinates are **Godot, model-local, metres** (front = +Z). Angles follow `docs/models/devices.md`.

PLACEHOLDER
