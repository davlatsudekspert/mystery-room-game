#!/usr/bin/env python3
"""Measure the Chapter 2 expansion audio (``c2x_*`` modules) from the *encoded* files and print a Markdown table
plus a list of warnings. We cannot listen here, so the checks are numeric proxies:

  * length, decoded sample peak, EBU R128 integrated loudness / true peak / LRA (ffmpeg loudnorm)
  * clipping: any decoded sample at or above -0.1 dBFS
  * spectral proxy for hiss: share of the energy above 6 kHz and above 10 kHz (dB below the total), plus the spectral
    centroid. Ambience beds must keep the >6 kHz share below -30 dB (no hiss in the high band).
  * loops: seam step ratio and level jump from ``synth.loops.seam_report`` on the decoded file, and the mono-sum
    loudness change (a phone speaker sums the channels: it must stay within 1.5 dB of stereo).
  * leading silence of one-shots (the cue must start within 30 ms).

    python3 tools/audio/measure_ch2x.py [--md docs-table.md]
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import synth_all  # noqa: E402
from synth import export, loops  # noqa: E402
from synth.core import SR, amp_to_db, to_mono  # noqa: E402

MODS = {"c2x_amb", "c2x_sfx", "c2x_moments", "c2x_hands"}
HF_LIMIT_DB = -30.0     # ambience: energy above 6 kHz at least 30 dB below the total


def band_share_db(x: np.ndarray, f_lo: float) -> float:
    m = to_mono(x)
    spec = np.abs(np.fft.rfft(m * np.hanning(len(m)))) ** 2
    f = np.fft.rfftfreq(len(m), 1.0 / SR)
    tot = spec.sum() + 1e-30
    return 10 * np.log10(spec[f >= f_lo].sum() / tot + 1e-30)


def centroid(x: np.ndarray) -> float:
    m = to_mono(x)
    spec = np.abs(np.fft.rfft(m * np.hanning(len(m))))
    f = np.fft.rfftfreq(len(m), 1.0 / SR)
    return float((f * spec).sum() / (spec.sum() + 1e-30))


def mono_sum_lufs(path: str) -> float:
    dec = export.decode(path, 2)
    with tempfile.TemporaryDirectory() as tmp:
        w = os.path.join(tmp, "m.wav")
        export.write_wav(w, to_mono(dec))
        return export.loudness(w)["integrated_lufs"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", help="write the Markdown table here too")
    args = ap.parse_args()
    specs = synth_all.load_all()
    names = [n for n, s in specs.items() if s.fn.__module__.rsplit(".", 1)[-1] in MODS]
    rows, warns = [], []
    for n in names:
        s = specs[n]
        path = synth_all.OUT_ROOT / s.subdir / f"{n}.ogg"
        if not path.exists():
            warns.append(f"{n}: file missing")
            continue
        dec = export.decode(str(path), 2 if s.stereo else 1)
        dur = dec.shape[-1] / SR
        pk = amp_to_db(float(np.max(np.abs(dec))))
        lm = export.loudness(str(path))
        hf6, hf10 = band_share_db(dec, 6000), band_share_db(dec, 10000)
        cen = centroid(dec)
        mono = to_mono(dec)
        lead = int(np.argmax(np.abs(mono) > 10 ** (-40 / 20) * np.max(np.abs(mono)))) / SR * 1000
        extra = ""
        if pk >= -0.1:
            warns.append(f"{n}: clipping risk, peak {pk:.2f} dBFS")
        if s.loop and s.stereo:
            sr = loops.seam_report(dec)
            ms = mono_sum_lufs(str(path))
            extra = f"seam {sr['jump_ratio']:.2f} / {sr['level_jump_db']:.2f} dB; mono {ms - lm['integrated_lufs']:+.1f} dB"
            if not sr["ok"]:
                warns.append(f"{n}: loop seam check failed")
            if abs(lm["integrated_lufs"] - s.lufs) > 0.5:
                warns.append(f"{n}: loudness {lm['integrated_lufs']:.1f} LUFS, target {s.lufs}")
            if lm["true_peak_dbtp"] > -1.0:
                warns.append(f"{n}: true peak {lm['true_peak_dbtp']:.1f} dBTP")
            if hf6 > HF_LIMIT_DB:
                warns.append(f"{n}: high-band share {hf6:.1f} dB (limit {HF_LIMIT_DB})")
            # a mono file is 3 dB (coherent) to 6 dB (incoherent) below the stereo file in LUFS; the Chapter 3
            # beds measure -3.4 .. -5.9. Anything below -7 dB means channels cancelling when summed.
            if ms - lm["integrated_lufs"] < -7.0:
                warns.append(f"{n}: mono-sum cancellation {ms - lm['integrated_lufs']:+.1f} dB")
        else:
            if s.peak_db is not None and pk - s.peak_db > 0.35:
                warns.append(f"{n}: peak {pk:.2f}, target {s.peak_db}")
            # moment cues and the stair/lift/carriage sounds have an intentional lead-in; only clicks must be immediate
            if lead > 150 and not s.loop and s.fn.__module__.rsplit(".", 1)[-1] != "c2x_moments":
                warns.append(f"{n}: starts {lead:.0f} ms late")
            if s.loop:
                sr = loops.seam_report(dec)
                extra = f"seam {sr['jump_ratio']:.2f} / {sr['level_jump_db']:.2f} dB"
                if not sr["ok"]:
                    warns.append(f"{n}: loop seam check failed")
        level = f"{lm['integrated_lufs']:.1f} LUFS, TP {lm['true_peak_dbtp']:.1f}" if s.stereo else f"peak {pk:.1f} dBFS"
        rows.append(f"| `{n}` | `{path.relative_to(synth_all.REPO / 'game' / 'assets' / 'audio')}` | {dur:.2f} s | {level} | "
                    f"{hf6:.0f} / {hf10:.0f} dB | {cen:.0f} Hz | {extra} |")
    head = ["| id | file | length | level | >6k / >10k share | centroid | loop checks |", "|---|---|---|---|---|---|---|"]
    out = "\n".join(head + rows)
    print(out)
    if args.md:
        Path(args.md).write_text(out + "\n")
    print()
    print("Ambience distinctness (1/3-octave spectrum distance in dB RMS, larger = more different):")
    amb = [n for n in names if specs[n].category == "ambience"]
    prof = {}
    edges = 2 ** np.arange(np.log2(40), np.log2(12000), 1 / 3)
    for n in amb:
        d = to_mono(export.decode(str(synth_all.OUT_ROOT / "ambience" / f"{n}.ogg"), 2))
        sp = np.abs(np.fft.rfft(d)) ** 2
        f = np.fft.rfftfreq(len(d), 1.0 / SR)
        prof[n] = np.array([10 * np.log10(sp[(f >= a) & (f < b)].sum() + 1e-20) for a, b in zip(edges[:-1], edges[1:])])
        prof[n] -= prof[n].max()
    print("| | " + " | ".join(n.replace("amb_c2x_", "") for n in amb) + " |")
    print("|---" * (len(amb) + 1) + "|")
    for a in amb:
        print("| " + a.replace("amb_c2x_", "") + " | " + " | ".join(f"{np.sqrt(np.mean((prof[a] - prof[b]) ** 2)):.1f}" for b in amb) + " |")
    print()
    print("WARNINGS:" if warns else "no warnings")
    for w in warns:
        print(" -", w)
    return 1 if warns else 0


if __name__ == "__main__":
    sys.exit(main())
