#!/usr/bin/env python3
"""Convert the QA PNG renders of the Night Cell and the hall additions into small JPG previews under docs/previews/ch2_expansion/
with the prefixes `cell_` (R3) and `hall_` (hall additions).

    python3 tools/blender/ch2x_cell_pack_previews.py <png dir>      # e.g. $MR_QA_DIR/ch2x
"""
import os
import sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "docs", "previews", "ch2_expansion")
os.makedirs(OUT, exist_ok=True)
src = sys.argv[1]
MAP = {  # png stem -> output stem
    "prev_cell_cell": "cell_room_overview", "prev_cell_cell2": "cell_room_overview2", "prev_cell_desk_light": "cell_room_desk_light",
    "prev_cell_cot": "cell_room_cot", "prev_cell_shelf": "cell_room_shelf", "prev_cell_door": "cell_room_door", "prev_cell_west": "cell_room_west",
    "cot": "cell_cot", "cot_head": "cell_cot_head", "light_table": "cell_light_table", "light_table_top": "cell_light_table_top",
    "acetate_sheet": "cell_acetate_sheet", "kettle_hotplate": "cell_kettle_hotplate", "kettle_hotplate_front": "cell_kettle_front",
    "cold_door": "cell_cold_door", "cold_door_lock": "cell_cold_door_lock", "cold_door_coil": "cell_cold_door_coil",
    "cell_diary": "cell_diary", "wipe_cloth": "cell_wipe_cloth",
    "service_door_closed": "hall_service_door_closed", "service_door": "hall_service_door_open", "service_door_dial": "hall_service_door_dial",
    "stair_stump": "hall_stair_stump", "stair_stump_top": "hall_stair_stump_top", "floor_plan_frame": "hall_floor_plan_frame",
}
for stem, out in MAP.items():
    f = os.path.join(src, stem + ".png")
    if not os.path.exists(f):
        print("missing", stem)
        continue
    im = Image.open(f).convert("RGB")
    if im.width > 900:
        im = im.resize((900, round(im.height * 900 / im.width)), Image.LANCZOS)
    path = os.path.join(OUT, out + ".jpg")
    im.save(path, quality=82, optimize=True)
    print("wrote", os.path.relpath(path, ROOT), os.path.getsize(path) // 1024, "KB")
