#!/usr/bin/env python3
"""Mobile texture import policy: every 3D texture → VRAM compressed (ETC2/ASTC on phones) + mipmaps,
size-limited to 1024 px (2048 for the floor/wall albedo). Normal maps flagged as normal maps.
UI-only images stay lossless. Rewrites [params] in *.import files; run `godot --headless --import` after.
    python3 tools/build/texture_imports.py"""
import os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "game"))
UI_ONLY = ("assets/ui/", "decals/notebook_page", "decals/uv_desk_mark")  # stay lossless
BIG = ("textures/wood_floor/albedo", "textures/plaster_wall/albedo")
SMALL = ("round_spectacles", "magnifying_glass", "seadogs_compass", "retro_multimeter", "tea_set",
         "old_gas_mask", "vintage_electric_kettle", "marble_bust", "metal_stool")  # small props: 512 px
IMG = (".png", ".jpg", ".jpeg", ".webp")

changed = 0
for dirpath, _, files in os.walk(os.path.join(ROOT, "assets")):
    for f in files:
        if not f.endswith(".import") or not f[:-7].lower().endswith(IMG):
            continue
        p = os.path.join(dirpath, f)
        rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
        s = open(p, encoding="utf-8").read()
        if 'importer="texture"' not in s:
            continue
        ui = any(k in rel for k in UI_ONLY)
        name = f.lower()
        is_normal = ("normal" in name or "nor_gl" in name) and not ui
        want = {
            "compress/mode": "0" if ui else "2",
            "mipmaps/generate": "false" if ui else "true",
            "compress/normal_map": "1" if is_normal else "0",
            "process/size_limit": "0" if ui else ("2048" if any(k in rel for k in BIG) else ("512" if any(k in rel for k in SMALL) else "1024")),
            "detect_3d/compress_to": "0",
        }
        new = s
        for k, v in want.items():
            if re.search(rf"^{re.escape(k)}=.*$", new, flags=re.M):
                new = re.sub(rf"^{re.escape(k)}=.*$", f"{k}={v}", new, flags=re.M)
            else:
                new = new.rstrip("\n") + f"\n{k}={v}\n"
        if new != s:
            open(p, "w", encoding="utf-8").write(new)
            changed += 1
print(f"updated {changed} texture import files")
