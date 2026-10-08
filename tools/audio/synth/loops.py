"""Seamless-loop helpers and loop-seam verification.

Two complementary techniques are used:
  * ``wrap_tail``: render events/reverb past the loop end and overlap-add the
    overrun onto the start (circular rendering) - exact for anything driven
    by periodic sources;
  * ``crossfade_loop``: for free-running material, render ``L + xfade``
    samples and equal-power crossfade the extra tail over the first
    ``xfade`` samples, so the sample after the last one *is* the continuation.
"""
from __future__ import annotations

import numpy as np

from .core import n_of, length


def wrap_tail(buf: np.ndarray, n: int) -> np.ndarray:
    """Fold everything beyond ``n`` samples back onto the start."""
    out = np.array(buf[..., :n], copy=True)
    pos = n
    total = length(buf)
    while pos < total:
        count = min(n, total - pos)
        out[..., :count] += buf[..., pos:pos + count]
        pos += count
    return out


def crossfade_loop(buf: np.ndarray, n: int, xfade_s: float, power: bool = True) -> np.ndarray:
    """Make ``buf`` loop at ``n`` samples using its extra tail (needs
    ``len(buf) >= n + xfade``). Equal-power for uncorrelated material."""
    x = n_of(xfade_s)
    if length(buf) < n + x:
        raise ValueError("buffer too short for the requested crossfade")
    out = np.array(buf[..., :n], copy=True)
    u = (np.arange(x) + 0.5) / x
    if power:
        fin, fout = np.sin(0.5 * np.pi * u), np.cos(0.5 * np.pi * u)
    else:
        fin, fout = u, 1.0 - u
    out[..., :x] = buf[..., :x] * fin + buf[..., n:n + x] * fout
    return out


def rotate_to_calm_point(x: np.ndarray, window_s: float = 0.05) -> np.ndarray:
    """Rotate a *periodic* loop so the file starts at its calmest moment
    (smallest short-term level change, no transient nearby). Rotation keeps
    the loop seamless; it only moves where playback begins, so the Vorbis
    encoder (which codes the first and last frames independently) meets
    steady material at the wrap point."""
    mono = x.mean(axis=0) if x.ndim == 2 else x
    n = mono.shape[0]
    w = n_of(window_s)
    hop = max(1, w // 2)
    frames = n // hop
    e = np.square(mono[:frames * hop]).reshape(frames, hop).mean(axis=1)
    win = np.convolve(np.concatenate([e[-2:], e, e[:2]]), np.ones(2) / 2.0, mode="same")[2:-2]
    lvl = 10 * np.log10(win + 1e-12)
    jump = np.abs(lvl - np.roll(lvl, -2))
    peaks = np.abs(mono[:frames * hop]).reshape(frames, hop).max(axis=1)
    crest = 20 * np.log10((np.maximum(peaks, np.roll(peaks, -1)) + 1e-12) / (np.sqrt(win) + 1e-12))
    loud = np.abs(lvl - np.median(lvl))
    score = jump + 0.5 * crest + 0.5 * loud
    k = int(np.argmin(score))
    shift = ((k + 1) * hop) % n
    return np.roll(x, -shift, axis=-1)


def periodic_freq(f: float, loop_s: float) -> float:
    """Nearest frequency with a whole number of cycles in the loop."""
    cycles = max(1, round(f * loop_s))
    return cycles / loop_s


def seam_report(x: np.ndarray, window_s: float = 0.05, probes: int = 400) -> dict:
    """Check a loop's wrap point (last sample -> first sample).

    * sample continuity: the jump across the seam is compared with the
      signal's own 99.9th-percentile sample-to-sample step (ratio < 1 is
      indistinguishable from normal motion);
    * level continuity: the RMS change between the windows just before and
      just after the seam is ranked against the same measurement taken at
      ``probes`` evenly spaced points inside the file (sparse textures have
      natural level jumps, so the seam only has to look like any other point).
    """
    chans = x if x.ndim == 2 else x[None, :]
    n = chans.shape[-1]
    worst_ratio, jumps, typ = 0.0, [], []
    for c in chans:
        d = np.abs(np.diff(c))
        p999 = float(np.percentile(d, 99.9)) + 1e-12
        jump = float(abs(c[0] - c[-1]))
        worst_ratio = max(worst_ratio, jump / p999)
        jumps.append(jump)
        typ.append(p999)
    w = n_of(window_s)
    mono = chans.mean(axis=0)

    def level_jump(pos: int) -> float:
        a = mono[np.arange(pos - w, pos) % n]
        b = mono[np.arange(pos, pos + w) % n]
        ra = np.sqrt(np.mean(a * a)) + 1e-9
        rb = np.sqrt(np.mean(b * b)) + 1e-9
        return float(abs(20 * np.log10(ra / rb)))

    seam_db = level_jump(0)
    inside = np.array([level_jump(int(p)) for p in np.linspace(w, n - w, probes)])
    pct = float(np.mean(inside < seam_db) * 100.0)
    return {
        "seam_jump": max(jumps),
        "p99_9_step": max(typ),
        "jump_ratio": worst_ratio,
        "level_jump_db": seam_db,
        "level_jump_percentile": pct,
        "ok": worst_ratio < 1.0 and (seam_db < 1.5 or pct < 99.0),
    }
