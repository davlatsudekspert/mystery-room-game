"""Core constants and buffer helpers shared by every synthesis module.

Conventions used across the package:
  * sample rate is ``SR`` (44.1 kHz), all signals are float64 in [-1, 1];
  * a mono signal is a 1-D array of shape ``(n,)``;
  * a stereo signal is a 2-D array of shape ``(2, n)`` (channels first);
  * times are given in seconds, frequencies in Hz.
"""
from __future__ import annotations

import zlib

import numpy as np
from scipy import signal as _sig

SR = 44100
NYQ = SR / 2.0
# Global seed: the date of the Night of Silence. Every sound derives its own
# generator from this and its name, so outputs are reproducible bit for bit.
BASE_SEED = 19791114


def n_of(seconds: float) -> int:
    """Number of samples for a duration in seconds."""
    return max(0, int(round(seconds * SR)))


def time_axis(n: int) -> np.ndarray:
    return np.arange(n, dtype=np.float64) / SR


def make_rng(name: str, salt: int = 0) -> np.random.Generator:
    """Deterministic generator for a named sound (crc32 is stable across runs,
    unlike Python's salted ``hash``)."""
    return np.random.default_rng([BASE_SEED, zlib.crc32(name.encode("utf-8")), salt])


def db_to_amp(db: float) -> float:
    return float(10.0 ** (db / 20.0))


def amp_to_db(a: float) -> float:
    return float(20.0 * np.log10(max(a, 1e-12)))


def is_stereo(x: np.ndarray) -> bool:
    return x.ndim == 2


def length(x: np.ndarray) -> int:
    return x.shape[-1]


def zeros(seconds: float, stereo: bool = False) -> np.ndarray:
    n = n_of(seconds)
    return np.zeros((2, n)) if stereo else np.zeros(n)


def to_stereo(x: np.ndarray) -> np.ndarray:
    return x if x.ndim == 2 else np.vstack([x, x])


def to_mono(x: np.ndarray) -> np.ndarray:
    return x if x.ndim == 1 else 0.5 * (x[0] + x[1])


def pan(x: np.ndarray, pos: float) -> np.ndarray:
    """Equal-power pan of a mono signal. ``pos`` in [-1 (left), 1 (right)]."""
    ang = (np.clip(pos, -1.0, 1.0) + 1.0) * np.pi / 4.0
    return np.vstack([np.cos(ang) * x, np.sin(ang) * x])


def pad_to(x: np.ndarray, n: int) -> np.ndarray:
    cur = length(x)
    if cur >= n:
        return x[..., :n]
    widths = [(0, 0)] * (x.ndim - 1) + [(0, n - cur)]
    return np.pad(x, widths)


def add_at(dst: np.ndarray, src: np.ndarray, t: float, gain: float = 1.0) -> np.ndarray:
    """Mix ``src`` into ``dst`` starting at time ``t`` (in place, truncated at
    the end of ``dst``). Mono sources are duplicated into stereo targets."""
    start = n_of(t) if t >= 0 else -n_of(-t)
    if dst.ndim == 2 and src.ndim == 1:
        src = to_stereo(src)
    if dst.ndim == 1 and src.ndim == 2:
        src = to_mono(src)
    s0 = max(0, -start)
    d0 = max(0, start)
    count = min(length(src) - s0, length(dst) - d0)
    if count > 0:
        dst[..., d0:d0 + count] += gain * src[..., s0:s0 + count]
    return dst


def add_circular(dst: np.ndarray, src: np.ndarray, t: float, gain: float = 1.0) -> np.ndarray:
    """Mix ``src`` into ``dst`` at time ``t`` with wrap-around (for loops).
    ``t`` may be negative or beyond the buffer; indices are taken modulo the
    buffer length, so a note that rings past the loop end continues at its start."""
    n = length(dst)
    if dst.ndim == 2 and src.ndim == 1:
        src = to_stereo(src)
    if dst.ndim == 1 and src.ndim == 2:
        src = to_mono(src)
    start = int(round(t * SR)) % n
    pos = 0
    total = length(src)
    while pos < total:
        d0 = (start + pos) % n
        count = min(total - pos, n - d0)
        dst[..., d0:d0 + count] += gain * src[..., pos:pos + count]
        pos += count
    return dst


def mix(*signals: np.ndarray) -> np.ndarray:
    """Sum signals of different lengths (and mono/stereo) into one buffer."""
    stereo = any(s.ndim == 2 for s in signals)
    n = max(length(s) for s in signals)
    out = np.zeros((2, n)) if stereo else np.zeros(n)
    for s in signals:
        add_at(out, s, 0.0)
    return out


def raised_cos(n: int) -> np.ndarray:
    """Rising half-cosine ramp 0 -> 1 of n samples."""
    if n <= 0:
        return np.zeros(0)
    return 0.5 - 0.5 * np.cos(np.pi * (np.arange(n) + 0.5) / n)


def fade(x: np.ndarray, fade_in: float = 0.0, fade_out: float = 0.0) -> np.ndarray:
    """Raised-cosine fades at the edges (returns a copy)."""
    y = np.array(x, dtype=np.float64, copy=True)
    n = length(y)
    a = min(n_of(fade_in), n)
    b = min(n_of(fade_out), n)
    if a > 0:
        y[..., :a] *= raised_cos(a)
    if b > 0:
        y[..., n - b:] *= raised_cos(b)[::-1]
    return y


def remove_dc(x: np.ndarray, cutoff: float = 15.0) -> np.ndarray:
    """Remove DC and subsonic drift with a 2nd-order Butterworth high-pass."""
    sos = _sig.butter(2, cutoff, btype="highpass", fs=SR, output="sos")
    y = _sig.sosfilt(sos, x - np.mean(x, axis=-1, keepdims=True), axis=-1)
    return y


def peak(x: np.ndarray) -> float:
    return float(np.max(np.abs(x))) if x.size else 0.0


def normalize_peak(x: np.ndarray, dbfs: float) -> np.ndarray:
    p = peak(x)
    return x if p <= 0 else x * (db_to_amp(dbfs) / p)


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x)))) if x.size else 0.0


def soft_clip(x: np.ndarray, drive: float = 1.0) -> np.ndarray:
    """tanh saturation normalised so small signals keep unity gain."""
    if drive <= 0:
        return x
    return np.tanh(drive * x) / drive


def trim_tail(x: np.ndarray, threshold_db: float = -70.0, keep: float = 0.02) -> np.ndarray:
    """Cut trailing near-silence (keeps ``keep`` seconds after the last loud sample)."""
    env = np.abs(to_mono(x))
    above = np.nonzero(env > db_to_amp(threshold_db) * max(peak(x), 1e-12))[0]
    if above.size == 0:
        return x
    end = min(length(x), above[-1] + n_of(keep))
    return x[..., :end]
