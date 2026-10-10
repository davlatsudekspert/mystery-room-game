"""Echo GLB check (pure Python + numpy, run with python3 -I): every mesh of the given GLBs must be closed (each welded edge used exactly twice),
have a positive signed volume (outward faces) and use only the M_Echo material. Usage: python3 -I qa/blender/ch4/echo_check.py game/assets/models/echo_*.glb"""
import json
import struct
import sys

import numpy as np


def load(path):
    d = open(path, "rb").read()
    n = struct.unpack("<I", d[12:16])[0]
    j = json.loads(d[20:20 + n])
    off = 20 + n
    bl = struct.unpack("<I", d[off:off + 4])[0]
    binb = d[off + 8:off + 8 + bl]
    return j, binb


def acc(j, b, i):
    a = j["accessors"][i]
    v = j["bufferViews"][a["bufferView"]]
    ct = {5126: np.float32, 5123: np.uint16, 5125: np.uint32}[a["componentType"]]
    nc = {"SCALAR": 1, "VEC2": 2, "VEC3": 3}[a["type"]]
    arr = np.frombuffer(b, dtype=ct, count=a["count"] * nc, offset=v.get("byteOffset", 0) + a.get("byteOffset", 0))
    return arr.reshape(-1, nc) if nc > 1 else arr


bad = 0
for p in sys.argv[1:]:
    j, b = load(p)
    for nd in j["nodes"]:
        if "mesh" not in nd:
            continue
        m = j["meshes"][nd["mesh"]]
        for pr in m["primitives"]:
            pos = acc(j, b, pr["attributes"]["POSITION"]).astype(np.float64)
            idx = acc(j, b, pr["indices"]).astype(np.int64).reshape(-1, 3)
            v0, v1, v2 = pos[idx[:, 0]], pos[idx[:, 1]], pos[idx[:, 2]]
            vol = float(np.einsum("ij,ij->i", v0, np.cross(v1, v2)).sum() / 6.0)
            # closed: every undirected edge used exactly twice (weld by position first)
            key = {tuple(np.round(q, 6)): i for i, q in enumerate(pos)}
            rem = np.array([key[tuple(np.round(q, 6))] for q in pos])
            ii = rem[idx]
            e = np.concatenate([ii[:, [0, 1]], ii[:, [1, 2]], ii[:, [2, 0]]])
            e.sort(axis=1)
            _u, cnt = np.unique(e, axis=0, return_counts=True)
            open_edges = int((cnt != 2).sum())
            mat = j["materials"][pr["material"]]["name"] if "material" in pr else "-"
            flag = "" if (vol > 0 and open_edges == 0 and mat == "M_Echo") else "   <-- CHECK"
            bad += bool(flag)
            print(f"{p.split('/')[-1]:28s} {nd['name']:16s} tris {len(idx):5d} vol {vol:8.4f} m3 open edges {open_edges} mat {mat}{flag}")
print("problems:", bad)
