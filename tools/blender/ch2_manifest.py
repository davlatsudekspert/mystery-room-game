#!/usr/bin/env python3
"""Chapter 2 asset manifest: what exists, what the code needs, what is missing.

For every model in docs/models/ch2.md it checks:
- the build script;
- the exported GLB;
- every node name the game code looks up (game/src/rooms/archive/*);
- the triangle count against the budget;
- the QA renders.
It then writes docs/models/CH2_MANIFEST.md. Integration and visual checks in Godot are recorded by hand in
the "Godot" column of that file's legend; this script only reports file facts.

    python3 tools/blender/ch2_manifest.py
"""
from __future__ import annotations

import glob
import json
import os
import struct

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# model -> (group, tri budget, required node names)
R = lambda *a: list(a)  # noqa: E731
MODELS: dict[str, tuple[str, int, list[str]]] = {
    "room_archive": ("A", 30000, R("fire_shutter", "shutter_lamp", "booth_bulb", "booth_glass", *[f"tube_p{i}" for i in range(5)],
                                  "tube_q0", *[f"elamp_glass_{k}" for k in range(10)])),
    "archive_pendant": ("A", 2500, R("bulb", "light_origin")),
    "vent_grille": ("A", 3000, R("IA_grille", "grille_reel_mount")),
    "floor_hatch": ("A", 3000, R("IA_hatch", "ring_pull", "hatch_reel_mount")),
    "projection_screen": ("A", 4000, R("screen_surface", "IA_screen_socket", "socket_mount", "socket_ring")),
    "library_ladder": ("A", 2500, R()),
    "card_catalogue": ("B1", 9000, R(*[f"IA_cat_drawer_{i}" for i in range(10)], *[f"cat_tray_mount_{i}" for i in range(10)])),
    "catalogue_tray": ("B1", 5000, R(*[f"IA_divider_{g}" for g in range(10)], *[f"IA_card_{n}" for n in range(10)])),
    "stacks_shelving": ("B1", 12000, R("terminal_top", "IA_ledger", "ledger_cover", "ledger_reel_mount")),
    "lockers": ("B1", 9000, R(*[f"IA_locker_{n}" for n in range(1, 13)], "receiver_mount")),
    "routing_chart": ("B1", 1500, R("chart_image")),
    "archivist_desk": ("B2", 6000, R()),
    "reading_table": ("B2", 5000, R("lamp_shade", "bulb", "light_origin")),
    "film_splicer": ("B2", 8000, R("light_box_glass", *[f"IA_frame_{k}" for k in range(4)], *[f"IA_slot_{s}" for s in range(4)],
                                  *[f"slot_mount_{s}" for s in range(4)], "splicer_reel_mount", "reel_can_lid")),
    "slide_cabinet": ("B2", 5000, R(*[f"IA_slide_drawer_{i}" for i in range(5)], "slide_mark_mount")),
    "lens_case": ("B2", 2500, R("IA_case_lid", "crystal_mount_1", "crystal_mount_2")),
    "tube_station": ("C1", 9000, R("IA_send_port", "port_flap", "canister_mount", "IA_receive_tray", "tray_door", "return_mount",
                                  "file_mount", "key_mount", "IA_dest_dial", "dest_ring", "IA_send_lever", "IA_card_tray",
                                  "tray_cards", "lamp_status")),
    "canister": ("C1", 1200, R("canister_cap")),
    "compressor_panel": ("C1", 9000, R("IA_valve_a", "IA_valve_b", "IA_valve_c", "needle_p", "needle_f", "motor_pulley",
                                      "compressor_tank")),
    "card_punch": ("C1", 6000, R(*[f"IA_punch_key_{i}" for i in range(8)], "IA_punch_slot", "card_in_punch", "IA_punch_lever")),
    "tape_deck": ("C1", 8000, R("IA_speed", "IA_play", "IA_eject", "spindle_l", "spindle_r", "deck_reel_mount", "takeup_reel",
                               "vu_needle", "vu_face")),
    "booth_door": ("C2", 6000, R("IA_booth_door", "IA_rotary_dial", *[f"IA_dial_hole_{d}" for d in range(10)], "booth_door_lamp")),
    "film_projector": ("C2", 9000, R("feed_reel_mount", "takeup_reel", "IA_run_lever", "IA_focus_ring", "IA_frame_prev",
                                    "IA_frame_next", "lamp_glow", "lens_origin")),
    "slide_projector": ("C2", 5000, R("IA_slide_gate", "slide_gate_mount", "IA_slide_rot", "IA_slide_lamp", "lamp_glow",
                                     "lens_origin")),
    "vault_door": ("D1", 14000, R("vault_frame", "IA_vault_door", "IA_vault_handle", *[f"bolt_{k}" for k in range(8)], "glass_disc",
                                 "IA_port_left", "IA_port_right", "port_left_mount", "port_right_mount", "light_pipe_left",
                                 "light_pipe_right", "IA_collar_left", "IA_collar_right", "IA_zoom_right")),
    "vault_interior": ("D1", 14000, R("vault_projector", "vault_lamp_glow", "vault_reel_screen", "key_strand_mount",
                                     "key_leyla_mount", "cradle_clamp_left", "cradle_clamp_right", "vault_bulb")),
    "leyla_badge": ("D2", 2500, R("badge_face")),
    "index_card": ("D2", 2500, R("card_face")),
    "request_card": ("D2", 2500, R("card_face", *[f"hole_{i}" for i in range(8)])),
    "file_folder": ("D2", 2500, R("folder_face")),
    "locker_key": ("D2", 2500, R()),
    "pocket_receiver": ("D2", 2500, R("needle", "tuning_knob")),
    "tape_reel": ("D2", 2500, R("label")),
    "film_reel": ("D2", 2500, R()),
    "lumen_crystal": ("D2", 2500, R("crystal_face")),
    "glass_slide": ("D2", 2500, R("slide_image")),
    "key_strand": ("D2", 2500, R()),
    "key_leyla": ("D2", 2500, R()),
    "echo_leyla_standing": ("E", 14000, R("echo_head")),
    "echo_archivist": ("E", 14000, R("echo_head")),
    "echo_scientists": ("E", 14000, R("echo_head_a", "echo_head_b")),
}


def gltf(path: str) -> dict:
    data = open(path, "rb").read()
    n = struct.unpack("<I", data[12:16])[0]
    return json.loads(data[20:20 + n])


def tris(doc: dict) -> int:
    t = 0
    acc = doc.get("accessors", [])
    for m in doc.get("meshes", []):
        for p in m.get("primitives", []):
            if "indices" in p:
                t += acc[p["indices"]]["count"] // 3
            elif "POSITION" in p.get("attributes", {}):
                t += acc[p["attributes"]["POSITION"]]["count"] // 3
    return t


def main() -> None:
    rows = []
    totals = {"ready": 0, "partial": 0, "missing": 0}
    for name, (group, budget, need) in MODELS.items():
        script = os.path.exists(os.path.join(ROOT, "tools/blender/models", name + ".py"))
        glb_path = os.path.join(ROOT, "game/assets/models", name + ".glb")
        renders = len(glob.glob(os.path.join(ROOT, "qa/blender/ch2", name + "*.png"))) + \
            len(glob.glob(os.path.join(ROOT, "qa/blender/ch2", "item_" + name + "*.png")))
        if not os.path.exists(glb_path):
            rows.append((name, group, "✓" if script else "—", "—", "—", "—", f"{renders}", "missing"))
            totals["missing"] += 1
            continue
        doc = gltf(glb_path)
        names = {n.get("name", "") for n in doc.get("nodes", [])}
        missing = [x for x in need if x not in names]
        t = tris(doc)
        status = "ready" if not missing and t <= budget * 1.05 else "partial"
        totals[status] += 1
        miss = ", ".join(missing[:6]) + (f" (+{len(missing) - 6})" if len(missing) > 6 else "") if missing else "all present"
        rows.append((name, group, "✓" if script else "—", "✓", f"{t:,} / {budget:,}", miss, f"{renders}", status))
    out = ["# Chapter 2 asset manifest", "",
           "Generated by `tools/blender/ch2_manifest.py` from the files on disk. Do not edit it by hand: rerun the script.", "",
           "- **ready**: the GLB exists, every node name the game code needs is present, and the tris are within budget (5 % slack).",
           "- **partial**: the GLB exists but names are missing or it is over budget.",
           "- **missing**: no GLB yet.", "",
           "Integration and visual checks in the real Godot scene are tracked in `docs/GAMEPLAY_QA.md`.", "",
           f"**Totals:** {totals['ready']} ready, {totals['partial']} partial, {totals['missing']} missing of {len(MODELS)}.", "",
           "| Model | Group | Script | GLB | Tris / budget | Required names | QA renders | Status |",
           "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append("| `%s` | %s | %s | %s | %s | %s | %s | **%s** |" % r)
    path = os.path.join(ROOT, "docs/models/CH2_MANIFEST.md")
    open(path, "w").write("\n".join(out) + "\n")
    print(f"{totals} -> {path}")


if __name__ == "__main__":
    main()
