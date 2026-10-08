#!/usr/bin/env python3
"""Fail if any exported GLB uses a node/mesh name that Godot's scene importer treats as an import hint.

Godot strips trailing digits/dots/underscores and then looks for suffixes such as `-col`, `_wheel`,
`-rigid`... A name like `IA_drawer_wheel_0` silently becomes a VehicleWheel3D named `IA_drawer_0`,
so gameplay code that looks the part up by name never finds it.

Usage: python3 tools/blender/check_glb_names.py [glb ...]   (default: every game/assets/models/**/*.glb)
"""
import glob
import json
import re
import struct
import sys
from pathlib import Path

HINTS = ("col", "convcol", "colonly", "convcolonly", "rigid", "rigidonly", "occ", "occonly",
         "navmesh", "vehicle", "wheel", "noimp")


def gltf_json(path: Path) -> dict:
    data = path.read_bytes()
    if data[:4] != b"glTF":
        raise ValueError(f"{path}: not a binary glTF")
    chunk_len = struct.unpack("<I", data[12:16])[0]
    return json.loads(data[20:20 + chunk_len])


def bad_names(doc: dict) -> list[str]:
    out = set()
    for kind in ("nodes", "meshes"):
        for item in doc.get(kind, []):
            name = item.get("name", "")
            stem = re.sub(r"[\d\s._-]+$", "", name).lower()
            for h in HINTS:
                if stem.endswith("-" + h) or stem.endswith("_" + h) or ("$" + h) in stem:
                    out.add(name)
    return sorted(out)


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parents[2]
    paths = [Path(p) for p in argv] or sorted(Path(p) for p in glob.glob(str(root / "game/assets/models/**/*.glb"), recursive=True))
    failed = 0
    for p in paths:
        names = bad_names(gltf_json(p))
        if names:
            failed += 1
            print(f"FAIL {p.relative_to(root) if p.is_absolute() else p}: Godot import-hint suffix in {names}")
    print(f"checked {len(paths)} GLB files, {failed} with reserved names")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
