#!/usr/bin/env python3
"""Regenerate every audio asset of MYSTERY ROOM deterministically.

    python3 tools/audio/synth_all.py                 # everything
    python3 tools/audio/synth_all.py --only ui_tap,reveal --qa-dir /tmp/qa

Pipeline per sound: render (fixed seed) -> clean-up (DC removal, fades for
one-shots) -> level (peak target for SFX, EBU R128 loudness target for music
and ambience) -> 44.1 kHz OGG Vorbis (q5, bit-exact) -> verification of the
encoded file (decoded peak, loudness, loop-seam continuity).

Requires: python3, numpy, scipy, Pillow (QA images only) and ffmpeg with
libvorbis on PATH.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import numpy as np  # noqa: E402

from synth import export, loops, qa  # noqa: E402
from synth.core import (SR, db_to_amp, amp_to_db, fade, make_rng, normalize_peak, peak,  # noqa: E402
                        remove_dc, to_mono, to_stereo, trim_tail)
from synth.filters import fft_filter, smooth_band  # noqa: E402
from sounds import load_all  # noqa: E402

REPO = HERE.parent.parent
OUT_ROOT = REPO / "game" / "assets" / "audio"
README = HERE / "README.md"
TRUE_PEAK_CEILING = -1.0


def _clean_loop(x: np.ndarray) -> np.ndarray:
    """Circular (zero-phase FFT) DC/subsonic removal keeps the loop periodic."""
    return fft_filter(x - x.mean(axis=-1, keepdims=True), lambda f: smooth_band(f, 22.0, None, 0.6))


def _encode(x: np.ndarray, out_path: Path, tmpdir: str) -> None:
    wav = os.path.join(tmpdir, out_path.stem + ".wav")
    export.write_wav(wav, x)
    export.encode_ogg(wav, str(out_path), channels=2 if x.ndim == 2 else 1)


def render(name: str, qa_dir: str | None) -> dict:
    specs = load_all()
    spec = specs[name]
    t0 = time.time()
    x = np.asarray(spec.fn(make_rng(name)), dtype=np.float64)
    x = to_stereo(x) if spec.stereo else to_mono(x)
    if not np.all(np.isfinite(x)):
        raise RuntimeError(f"{name}: non-finite samples")
    out_dir = OUT_ROOT / spec.subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{name}.ogg"
    info: dict = {"name": name, "category": spec.category, "loop": spec.loop, "source": spec.source,
                  "desc": spec.desc, "path": str(out_path.relative_to(REPO))}

    with tempfile.TemporaryDirectory() as tmp:
        if spec.loop:
            x = _clean_loop(x)
        else:
            x = remove_dc(x)
            x = trim_tail(x, -70.0, keep=0.03)
            x = fade(x, 0.0015, spec.fade_out)

        if spec.lufs is not None:
            # Loudness: measure the clean render, apply the gain, verify true peak.
            x = normalize_peak(x, -6.0)
            wav = os.path.join(tmp, "measure.wav")
            export.write_wav(wav, x)
            lm = export.loudness(wav)
            x = x * db_to_amp(spec.lufs - lm["integrated_lufs"])
        else:
            x = normalize_peak(x, spec.peak_db)

        # Encode and verify the *decoded* file. Vorbis moves peaks by a fraction
        # of a dB (not linearly with gain), so a few trims are tried and the
        # best result is kept, never exceeding the target by more than 0.3 dB.
        best = None
        g_db = 0.0
        for _ in range(6):
            y = x * db_to_amp(g_db)
            _encode(y, out_path, tmp)
            dec = export.decode(str(out_path), 2 if spec.stereo else 1)
            if spec.lufs is not None:
                lm = export.loudness(str(out_path))
                info["loudness"] = lm
                over = lm["true_peak_dbtp"] - TRUE_PEAK_CEILING
                if over > 0:  # only ever reduce gain (no limiter); reported below
                    g_db -= over + 0.1
                    continue
                x = y
                break
            p = amp_to_db(peak(dec))
            err = p - spec.peak_db
            score = abs(err) + (10.0 if err > 0.3 else 0.0)
            if best is None or score < best[0]:
                best = (score, out_path.read_bytes(), p, dec, y)
            if abs(err) <= 0.2:
                break
            g_db -= err
        if best is not None:
            _, data, p, dec, x = best
            out_path.write_bytes(data)
            info["decoded_peak_dbfs"] = round(p, 2)

        info["duration_s"] = round(dec.shape[-1] / SR, 3)
        # loudest 100 ms RMS: a quick, comparable 'how loud does it feel' figure for mixing
        mono = to_mono(dec)
        w = int(0.1 * SR)
        if len(mono) >= w:
            c = np.concatenate([[0.0], np.cumsum(mono * mono)])
            info["rms100_max_dbfs"] = round(amp_to_db(float(np.sqrt(np.max(c[w:] - c[:-w]) / w))), 1)
        info["size_kb"] = round(out_path.stat().st_size / 1024, 1)
        info["channels"] = 2 if spec.stereo else 1
        if spec.loop:
            info["seam_render"] = loops.seam_report(x)
            info["seam_encoded"] = loops.seam_report(dec)
        if qa_dir:
            qa.spectrogram_png(dec, os.path.join(qa_dir, f"{name}.png"), name)
    info["seconds"] = round(time.time() - t0, 1)
    return info


def _fmt_dur(s: float) -> str:
    return f"{int(s // 60)}:{s % 60:04.1f}" if s >= 60 else f"{s:.2f} s"


def update_readme(results: list[dict]) -> None:
    if not README.exists():
        return
    order = {"ui": 0, "sfx": 1, "ambience": 2, "music": 3}
    rows = ["| File | Duration | Loop | Level | Size | Source | Description |", "|---|---|:-:|---|---|---|---|"]
    for r in sorted(results, key=lambda r: (order[r["category"]], r["name"])):
        if "loudness" in r:
            level = f"{r['loudness']['integrated_lufs']:.1f} LUFS"
        else:
            level = f"peak {r['decoded_peak_dbfs']:.1f} dBFS"
        rows.append(f"| `{r['path'].replace('game/assets/audio/', '')}` | {_fmt_dur(r['duration_s'])} | "
                    f"{'yes' if r['loop'] else 'no'} | {level} | {r['size_kb']:.0f} KB | {r['source']} | "
                    f"{r['desc']} |")
    text = README.read_text()
    a, b = "<!-- ASSET-TABLE:START -->", "<!-- ASSET-TABLE:END -->"
    if a in text and b in text:
        head, rest = text.split(a, 1)
        _, tail = rest.split(b, 1)
        README.write_text(head + a + "\n" + "\n".join(rows) + "\n" + b + tail)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma-separated sound names")
    ap.add_argument("--qa-dir", help="write spectrogram PNGs and report.json here")
    ap.add_argument("--jobs", type=int, default=min(4, os.cpu_count() or 1))
    ap.add_argument("--list", action="store_true", help="list registered sounds and exit")
    args = ap.parse_args()

    specs = load_all()
    if args.list:
        for s in specs.values():
            print(f"{s.category:9s} {s.name:28s} {s.desc}")
        return 0
    names = list(specs) if not args.only else [n.strip() for n in args.only.split(",") if n.strip()]
    unknown = [n for n in names if n not in specs]
    if unknown:
        print("unknown sounds:", ", ".join(unknown), file=sys.stderr)
        return 2
    if args.qa_dir:
        os.makedirs(args.qa_dir, exist_ok=True)

    # Longest jobs first for better parallel packing.
    names.sort(key=lambda n: (specs[n].category not in ("music", "ambience"), n))
    results = []
    if args.jobs > 1 and len(names) > 1:
        with ProcessPoolExecutor(max_workers=args.jobs) as ex:
            futs = {n: ex.submit(render, n, args.qa_dir) for n in names}
            for n, f in futs.items():
                results.append(f.result())
    else:
        results = [render(n, args.qa_dir) for n in names]

    ok = True
    for r in sorted(results, key=lambda r: (r["category"], r["name"])):
        extra = ""
        if "loudness" in r:
            lm = r["loudness"]
            extra += f" I={lm['integrated_lufs']:.1f} LUFS TP={lm['true_peak_dbtp']:.1f} dBTP LRA={lm['lra']:.1f}"
        if "decoded_peak_dbfs" in r:
            extra += f" peak={r['decoded_peak_dbfs']:.1f} dBFS"
        if r.get("loop"):
            s = r["seam_encoded"]
            extra += (f" seam ratio={s['jump_ratio']:.2f} level_jump={s['level_jump_db']:.2f} dB"
                      f" (p{s['level_jump_percentile']:.0f})")
            ok &= bool(r["seam_render"]["ok"] and s["ok"])
        print(f"{r['category']:9s} {r['name']:26s} {r['duration_s']:7.2f}s {r['size_kb']:7.1f} KB"
              f" [{r['seconds']}s]{extra}")
    if args.qa_dir:
        with open(os.path.join(args.qa_dir, "report.json"), "w") as fh:
            json.dump(results, fh, indent=1, default=float)
    if not args.only:
        update_readme(results)
    if not ok:
        print("LOOP SEAM CHECK FAILED", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
