"""Oscillators. Frequencies may be scalars or per-sample arrays (for glides,
vibrato and FM). Band-limited shapes use polyBLEP to keep aliasing low."""
from __future__ import annotations

import numpy as np

from .core import SR, NYQ


def _freq_array(freq, n: int) -> np.ndarray:
    f = np.asarray(freq, dtype=np.float64)
    return np.full(n, float(f)) if f.ndim == 0 else f[:n]


def phase_cycles(freq, n: int, phase0: float = 0.0) -> np.ndarray:
    """Running phase in cycles (not wrapped) for a (possibly varying) frequency.
    Sample k holds the phase *before* advancing, so sample 0 equals ``phase0``."""
    f = _freq_array(freq, n)
    ph = np.empty(n)
    ph[0] = 0.0
    np.cumsum(f[:-1] / SR, out=ph[1:])
    return ph + phase0


def sine(freq, n: int, phase0: float = 0.0) -> np.ndarray:
    return np.sin(2.0 * np.pi * phase_cycles(freq, n, phase0))


def _polyblep(t: np.ndarray, dt: np.ndarray) -> np.ndarray:
    out = np.zeros_like(t)
    m = t < dt
    x = t[m] / dt[m]
    out[m] = x + x - x * x - 1.0
    m = t > 1.0 - dt
    x = (t[m] - 1.0) / dt[m]
    out[m] = x * x + x + x + 1.0
    return out


def saw(freq, n: int, phase0: float = 0.0) -> np.ndarray:
    """Band-limited (polyBLEP) sawtooth in [-1, 1]."""
    f = _freq_array(freq, n)
    t = np.mod(phase_cycles(f, n, phase0), 1.0)
    dt = np.clip(np.abs(f) / SR, 1e-9, 0.5)
    return 2.0 * t - 1.0 - _polyblep(t, dt)


def square(freq, n: int, duty: float = 0.5, phase0: float = 0.0) -> np.ndarray:
    """Band-limited, zero-mean pulse wave built from two polyBLEP saws
    (spans [-1, 1] at 50 % duty)."""
    return saw(freq, n, phase0) - saw(freq, n, phase0 + duty)


def triangle(freq, n: int, phase0: float = 0.0) -> np.ndarray:
    """Triangle from the folded phase; its harmonics fall at 12 dB/oct, so
    aliasing is negligible for the low/mid frequencies used here."""
    t = np.mod(phase_cycles(freq, n, phase0 + 0.25), 1.0)
    return 4.0 * np.abs(t - 0.5) - 1.0


def additive(freq, n: int, partials, phases=None) -> np.ndarray:
    """Sum of sine partials ``[(ratio, amp), ...]`` on a common fundamental.
    Partials above Nyquist are skipped (per sample, so glides stay clean)."""
    f = _freq_array(freq, n)
    base = phase_cycles(f, n)
    out = np.zeros(n)
    for i, (ratio, amp) in enumerate(partials):
        if amp == 0.0:
            continue
        ph0 = 0.0 if phases is None else phases[i]
        fk = f * ratio
        if np.min(fk) >= NYQ * 0.95:
            continue
        part = amp * np.sin(2.0 * np.pi * (base * ratio + ph0))
        part[fk >= NYQ * 0.95] = 0.0
        out += part
    return out


def fm(carrier, modulator, index, n: int) -> np.ndarray:
    """Two-operator phase-modulation (classic FM). ``index`` may vary per sample."""
    mod = sine(modulator, n)
    idx = np.asarray(index, dtype=np.float64)
    return np.sin(2.0 * np.pi * phase_cycles(carrier, n) + idx * mod)


def vibrato(freq: float, n: int, rate: float, cents: float, phase0: float = 0.0) -> np.ndarray:
    """Frequency curve with sinusoidal vibrato of +-``cents``."""
    lfo = np.sin(2.0 * np.pi * (np.arange(n) * rate / SR + phase0))
    return freq * 2.0 ** (cents * lfo / 1200.0)
