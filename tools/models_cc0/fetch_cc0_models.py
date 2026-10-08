#!/usr/bin/env python3
"""MYSTERY ROOM — fetch CC0 dressing props from Poly Haven and convert them to game-ready .glb.

Pipeline (reproducible, stdlib only + Blender for the conversion step):
  1. For each asset in ASSETS, read https://api.polyhaven.com/info/<id> (name, authors) and
     https://api.polyhaven.com/files/<id> (glTF -> 1k file list with md5 hashes).
  2. Download the 1k glTF + .bin + 1K JPG textures into a fresh, empty directory
     <dl-dir>/<id>/ and verify every md5. Downloads are treated as untrusted DATA: nothing
     from them is executed, and Blender only parses them with its glTF importer.
  3. Run Blender headless (tools/models_cc0/convert_gltf_to_glb.py) to optionally keep a
     subset of objects, decimate to the per-asset triangle target (never above 15k),
     normalise the pivot (base at y=0, or the hook point for hanging props), make glass
     alpha-blended (Godot ignores KHR transmission; source glass used opaque RGB JPGs),
     wire the ARM map's AO channel as occlusionTexture, and export a single binary .glb
     with the 1K JPG textures embedded:
         game/assets/models/cc0/<id>/<id>.glb
  4. Write tools/models_cc0/cc0_models_report.json (tris, bbox, sizes, authors, licence check).

Optional QA step (--qa): renders every exported .glb with Cycles (CPU, 32 spp, 512 px,
neutral grey studio) via tools/models_cc0/render_qa.py and composes
qa/cc0_props_contact_sheet.jpg with Pillow.

Licence: every Poly Haven asset is CC0 (https://polyhaven.com/license). The script also checks
that the licence page still states CC0 and that each asset page mentions CC0.

Usage:
    python3 tools/models_cc0/fetch_cc0_models.py                # fetch + convert all
    python3 tools/models_cc0/fetch_cc0_models.py --only marble_bust_01 --qa
    python3 tools/models_cc0/fetch_cc0_models.py --qa-only      # re-render the contact sheet
Environment: BLENDER (default /usr/local/bin/blender). Honours HTTPS_PROXY / SSL_CERT_FILE.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TOOLS = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "game", "assets", "models", "cc0")
QA_DIR = os.path.join(ROOT, "qa")
REPORT = os.path.join(TOOLS, "cc0_models_report.json")
BLENDER = os.environ.get("BLENDER", "/usr/local/bin/blender")
UA = {"User-Agent": "mystery-room-game-cc0-fetch/1.0 (CC0 asset pipeline)"}
RESOLUTION = "1k"
MAX_TRIS = 15000

# id, what it is used for, suggested placement in Lab 7 (Godot coordinates from docs/ROOM_LAYOUT.md),
# triangle target, keep-object filter.
# "target" is the triangle budget after decimation (None = keep the source mesh as is). Targets follow
# docs/ROOM_LAYOUT.md + docs/ART_DIRECTION.md mobile budgets (small items ~2.5k, larger props <= 6k,
# whole scene <= 150k) and never exceed MAX_TRIS (15k).
# "keep" lists object-name substrings to keep (None = keep every object in the file).
# "floor": True marks floor-scale props (only used to group the QA line-ups).
# Optional: "move" {object: (dx, dy, dz)}, "drop" [object] (rest on the surface below),
# "smooth_angle" (degrees, normals of decimated objects; default 40), "rotate" (rx, ry, rz degrees,
# Blender axes, baked into the root nodes), "pivot" ("bottom" default: base at y=0; "top": hang point).
ASSETS: list[dict] = [
    {"id": "vintage_microscope", "used_for": "Lab bench dressing (brass microscope)",
     "placement": "Lab bench top, free span between vial rack and radio, ~(-0.35, 0.92, 2.30); lab_bench.glb lists a microscope, so this can replace it", "target": 6000, "keep": None},
    {"id": "vintage_spacecraft_instrument", "used_for": "Storage-shelf dressing (Soviet-era enamel navigation instrument)",
     "placement": "Worn metal rack shelf or filing-cabinet top; keep it away from the radio so it is not read as a puzzle device", "target": 6000, "keep": None},
    {"id": "retro_multimeter", "used_for": "Panel-7 corner dressing (analogue multimeter)",
     "placement": "Floor/crate under Panel 7, ~(2.70, 0, -1.30), leads toward the panel; or a metal-rack shelf", "target": 4000, "keep": None},
    {"id": "book_encyclopedia_set_01", "used_for": "Shelf dressing (leather-bound book set)",
     "placement": "Metal-rack shelf or filing-cabinet top; NOT the bookshelf door (puzzle encyclopedia IA_book_1..9 lives there)", "target": 6000, "keep": None},
    {"id": "magnifying_glass_01", "used_for": "Desk dressing (magnifying glass)",
     "placement": "Desk top east of the notebook, ~(0.00, 0.78, -1.95)", "target": 2500, "keep": None,
     "rotate": (-90, 0, 0)},  # authored standing on its handle: laid flat, lens up, for desk placement
    {"id": "round_spectacles", "used_for": "Desk dressing (reading glasses)",
     "placement": "Desk top beside the notebook, ~(-0.05, 0.78, -2.10)", "target": 2500, "keep": None},
    {"id": "seadogs_compass", "used_for": "Desk/shelf dressing (brass compass)",
     "placement": "Bookshelf (not the shelf-3 clear spot) or the window sill", "target": 5000, "keep": None},
    # (3.5k made the bail ring visibly polygonal in close-up A/B renders; 5k keeps it round)
    # Subset of the 10-piece set: teapot + lid, one cup on its saucer, re-laid-out compactly
    # (the source lays every piece out in a grid). Pieces stay separate nodes in the .glb.
    {"id": "tea_set_01", "used_for": "Desk dressing (porcelain teapot, cup and saucer)",
     "placement": "Desk east end, ~(0.10, 0.78, -2.25): the 'cup of tea dried to a ring'; teapot is its own node", "target": 4000,
     "keep": ["tea_set_01_teapot_01", "tea_set_01_cup_small_01", "tea_set_01_saucer_circular_04"],
     # deltas in Blender coordinates (X right, Y back, Z up), metres
     "move": {"tea_set_01_teapot_01": (0.2366, 0.0613, 0.0), "tea_set_01_teapot_01_lid": (0.2366, 0.0613, 0.0),
              "tea_set_01_saucer_circular_04": (-0.0334, -0.2187, 0.0),
              "tea_set_01_cup_small_01": (-0.0334, 0.0313, 0.05)},
     "drop": ["tea_set_01_cup_small_01"], "smooth_angle": 60},
    {"id": "vintage_electric_kettle", "used_for": "Window-sill dressing (old electric kettle)",
     "placement": "Stone window sill (north wall, x 0.95-2.05, y ~1.45) or beside the radiator", "target": 4000, "keep": None, "smooth_angle": 50},
    {"id": "vintage_wooden_drawer_01", "floor": True, "used_for": "Floor/wall dressing (card-index drawer chest)",
     "placement": "North wall between filing cabinet and desk, ~(-1.85, 0, -2.27), facing +Z", "target": None, "keep": None},
    {"id": "metal_stool_02", "floor": True, "used_for": "Lab bench seating (metal lab stool)",
     "placement": "In front of the lab bench, ~(0.15, 0, 1.60); seat 0.46 m, stays under the Lumen beam (y 1.15)", "target": None, "keep": None},
    {"id": "worn_metal_rack", "floor": True, "used_for": "Storage corner (metal shelving)",
     "placement": "East wall south of the door, centre ~(2.70, 0, 1.95), facing -X; check clearance to the wall safe and mirror A", "target": None, "keep": None},
    {"id": "old_gas_mask", "floor": True, "used_for": "Story dressing (gas mask, 'ventilation accident')",
     "placement": "Free hook on the coat rack (2.6, 0, -2.15); origin = hook point (top), hose hangs 1.13 m", "target": 4000, "keep": None, "smooth_angle": 60,
     "pivot": "top"},  # authored hanging (hose 1 m below the mask): origin = top = hook point
    {"id": "marble_bust_01", "used_for": "Study dressing (marble bust)",
     "placement": "Top of the filing cabinet (-2.6, top, -2.2)", "target": 4000, "keep": None, "smooth_angle": 80},
]


def http_get(url: str, retries: int = 4) -> bytes:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception as e:  # network hiccup: retry with backoff
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET failed: {url}: {last}")


def get_json(url: str) -> dict:
    return json.loads(http_get(url).decode("utf-8"))


def check_site_license() -> bool:
    html = http_get("https://polyhaven.com/license").decode("utf-8", "ignore")
    return "CC0" in html and "licensed as" in html


def check_asset_page(aid: str) -> bool:
    html = http_get(f"https://polyhaven.com/a/{aid}").decode("utf-8", "ignore")
    return "CC0" in html


def safe_rel(path: str) -> str:
    """Reject absolute paths / traversal in file names coming from the API."""
    norm = os.path.normpath(path)
    if os.path.isabs(norm) or norm.startswith("..") or "\\" in path:
        raise ValueError(f"unsafe path from API: {path!r}")
    return norm


def download_asset(aid: str, dl_root: str) -> tuple[str, dict, int]:
    files = get_json(f"https://api.polyhaven.com/files/{aid}")
    entry = files["gltf"][RESOLUTION]["gltf"]
    dest = os.path.join(dl_root, aid)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    todo = [(os.path.basename(entry["url"]), entry)]
    todo += [(safe_rel(rel), meta) for rel, meta in entry.get("include", {}).items()]
    total = 0
    for rel, meta in todo:
        data = http_get(meta["url"])
        md5 = hashlib.md5(data).hexdigest()
        if md5 != meta["md5"]:
            raise RuntimeError(f"{aid}: md5 mismatch for {rel}")
        p = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(data)
        total += len(data)
    gltf_path = os.path.join(dest, os.path.basename(entry["url"]))
    return gltf_path, entry, total


def run_blender(script: str, args: list[str], cwd: str) -> str:
    cmd = [BLENDER, "-b", "--factory-startup", "-noaudio", "--python-exit-code", "1",
           "-P", script, "--"] + args
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.stderr.write(res.stdout[-4000:] + res.stderr[-4000:])
        raise RuntimeError(f"Blender failed: {' '.join(args[:4])}")
    return res.stdout


def convert(asset: dict, gltf_path: str, work: str) -> dict:
    aid = asset["id"]
    out_dir = os.path.join(OUT_DIR, aid)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{aid}.glb")
    stats = os.path.join(work, f"{aid}_stats.json")
    target = min(asset["target"] or MAX_TRIS, MAX_TRIS)
    args = ["--in", gltf_path, "--out", out, "--target-tris", str(target), "--stats", stats]
    if asset.get("keep"):
        args += ["--keep", ",".join(asset["keep"])]
    for name, delta in asset.get("move", {}).items():
        args += ["--move", f"{name}={delta[0]},{delta[1]},{delta[2]}"]
    for name in asset.get("drop", []):
        args += ["--drop", name]
    if asset.get("rotate"):
        args += ["--rotate=" + ",".join(str(v) for v in asset["rotate"])]  # '=' form: value may start with '-'

    args += ["--pivot", asset.get("pivot", "bottom")]
    if asset.get("smooth_angle"):
        args += ["--smooth-angle", str(asset["smooth_angle"])]
    run_blender(os.path.join(TOOLS, "convert_gltf_to_glb.py"), args, cwd=work)
    with open(stats) as f:
        return json.load(f)


def make_contact_sheet(ids: list[str], work: str) -> str:
    from PIL import Image, ImageDraw, ImageFont  # only needed for QA

    tiles = os.path.join(work, "qa_tiles")
    os.makedirs(tiles, exist_ok=True)
    glbs = [os.path.join(OUT_DIR, i, f"{i}.glb") for i in ids]
    run_blender(os.path.join(TOOLS, "render_qa.py"),
                ["--out-dir", tiles, "--size", "512", "--samples", "32",
                 "--floor", ",".join(x["id"] for x in ASSETS if x.get("floor"))] + glbs, cwd=work)
    report = json.load(open(REPORT)) if os.path.exists(REPORT) else {}
    cols = 4
    cell_w, cell_h, label_h = 512, 512, 46
    rows = (len(ids) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, (rows + 1) * (cell_h + label_h)), (34, 34, 36))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(size=18)
        small = ImageFont.load_default(size=15)
    except TypeError:
        font = small = ImageFont.load_default()
    for n, name in enumerate(ids):
        x, y = (n % cols) * cell_w, (n // cols) * (cell_h + label_h)
        info = report.get("assets", {}).get(name, {})
        d = info.get("dims_m", [0, 0, 0])
        sub = f"{d[0]:.2f} x {d[1]:.2f} x {d[2]:.2f} m (W x H x D)  |  {info.get('tris', '?')} tris"
        p = os.path.join(tiles, f"{name}.png")
        if os.path.exists(p):
            sheet.paste(Image.open(p).convert("RGB"), (x, y))
        draw.text((x + 8, y + cell_h + 3), name, fill=(235, 228, 210), font=font)
        draw.text((x + 8, y + cell_h + 24), sub, fill=(180, 175, 160), font=small)
    # last row: the two real-scale line-ups (each 2 cells wide)
    y = rows * (cell_h + label_h)
    for x, tag, title in ((0, "_lineup_desk", "Desk-scale props at real scale (checker = 0.1 m)"),
                          (2 * cell_w, "_lineup_floor", "Floor-scale props at real scale (checker = 0.5 m)")):
        p = os.path.join(tiles, f"{tag}.png")
        if os.path.exists(p):
            sheet.paste(Image.open(p).convert("RGB"), (x, y))
        draw.text((x + 8, y + cell_h + 3), title, fill=(235, 228, 210), font=font)
        draw.text((x + 8, y + cell_h + 24), "front orthographic, left to right in table order",
                  fill=(180, 175, 160), font=small)
    os.makedirs(QA_DIR, exist_ok=True)
    out = os.path.join(QA_DIR, "cc0_props_contact_sheet.jpg")
    sheet.save(out, quality=88)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="*", help="asset ids to process (default: all)")
    ap.add_argument("--dl-dir", help="download root (default: a fresh temp dir)")
    ap.add_argument("--qa", action="store_true", help="also render qa/cc0_props_contact_sheet.jpg")
    ap.add_argument("--qa-only", action="store_true", help="only render the contact sheet")
    a = ap.parse_args()

    assets = [x for x in ASSETS if not a.only or x["id"] in a.only]
    if a.only and len(assets) != len(a.only):
        print("unknown id in --only", file=sys.stderr)
        return 2
    work = tempfile.mkdtemp(prefix="cc0_work_")
    if not a.qa_only:
        dl_root = a.dl_dir or tempfile.mkdtemp(prefix="cc0_dl_")
        os.makedirs(dl_root, exist_ok=True)
        report = json.load(open(REPORT)) if os.path.exists(REPORT) else {"assets": {}}
        site_cc0 = check_site_license()
        print(f"polyhaven.com/license states CC0: {site_cc0}")
        if not site_cc0:
            print("Licence page no longer states CC0: stopping.", file=sys.stderr)
            return 1
        for asset in assets:
            aid = asset["id"]
            info = get_json(f"https://api.polyhaven.com/info/{aid}")
            page_cc0 = check_asset_page(aid)
            gltf_path, entry, nbytes = download_asset(aid, dl_root)
            st = convert(asset, gltf_path, work)
            glb = os.path.join(OUT_DIR, aid, f"{aid}.glb")
            st.update({
                "name": info.get("name"),
                "authors": sorted(info.get("authors", {}).keys()),
                "source_url": f"https://polyhaven.com/a/{aid}",
                "license": "CC0" if (site_cc0 and page_cc0) else "UNVERIFIED",
                "download_bytes": nbytes,
                "glb_bytes": os.path.getsize(glb),
                "used_for": asset["used_for"],
                "placement": asset["placement"],
                "source_polycount_api": info.get("polycount"),
            })
            report["assets"][aid] = st
            print(f"{aid:32s} tris {st['src_tris']:>6} -> {st['tris']:>6}  "
                  f"dims {st['dims_m']}  glb {st['glb_bytes']/1e6:.2f} MB  {st['license']}")
        report["generated"] = time.strftime("%Y-%m-%d")
        report["assets"] = {x["id"]: report["assets"][x["id"]] for x in ASSETS if x["id"] in report["assets"]}
        with open(REPORT, "w") as f:
            json.dump(report, f, indent=1, ensure_ascii=False)
        print(f"downloads kept in {dl_root}")
    if a.qa or a.qa_only:
        print("contact sheet:", make_contact_sheet([x["id"] for x in assets], work))
    shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
