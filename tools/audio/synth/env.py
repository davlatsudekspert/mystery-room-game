"""Envelope generators (ADSR, exponential decays, breakpoint curves)."""
from __future__ import annotations

import numpy as np

from .core import SR, n_of, raised_cos

LN1000 = 6.907755278982137  # ln(1000): a T60 decay falls by 60 dB


def decay(n: int, t60: float) -> np.ndarray:
    """Exponential decay reaching -60 dB after ``t60`` seconds."""
    return np.exp(-LN1000 * np.arange(n) / (SR * max(t60, 1e-5)))


def ar(n: int, attack: float, t60: float) -> np.ndarray:
    """Raised-cosine attack followed by an exponential decay."""
    a = min(n_of(attack), n)
    env = np.empty(n)
    env[:a] = raised_cos(a)
    env[a:] = decay(n - a, t60)
    return env


def adsr(n: int, attack: float, decay_s: float, sustain: float, release: float,
         gate: float | None = None) -> np.ndarray:
    """Classic ADSR. The gate (note-on time) defaults to ``n - release``.
    Attack is a raised cosine, decay and release are exponential-like."""
    gate_n = n - n_of(release) if gate is None else min(n, n_of(gate))
    env = np.zeros(n)
    a = min(n_of(attack), gate_n)
    env[:a] = raised_cos(a)
    d = min(n_of(decay_s), max(gate_n - a, 0))
    if d > 0:
        k = np.arange(d) / d
        env[a:a + d] = sustain + (1.0 - sustain) * np.exp(-5.0 * k) * (1 - k)
    if gate_n > a + d:
        env[a + d:gate_n] = sustain
    level = env[gate_n - 1] if gate_n > 0 else 0.0
    r = n - gate_n
    if r > 0:
        k = np.arange(r) / r
        env[gate_n:] = level * np.exp(-5.0 * k) * (1.0 - k)
    return env


def curve(points, n: int, shape: str = "lin") -> np.ndarray:
    """Breakpoint envelope. ``points`` is ``[(time_s, value), ...]``.
    shape: 'lin' (linear), 'cos' (smooth S-curves), 'exp' (linear in dB,
    values must be > 0)."""
    pts = sorted(points)
    ts = np.array([p[0] for p in pts]) * SR
    vs = np.array([p[1] for p in pts], dtype=np.float64)
    idx = np.arange(n, dtype=np.float64)
    if shape == "exp":
        return np.exp(np.interp(idx, ts, np.log(np.maximum(vs, 1e-9))))
    if shape == "cos":
        out = np.empty(n)
        seg = np.clip(np.searchsorted(ts, idx, side="right") - 1, 0, len(ts) - 2)
        t0, t1 = ts[seg], ts[seg + 1]
        u = np.clip((idx - t0) / np.maximum(t1 - t0, 1e-9), 0.0, 1.0)
        u = 0.5 - 0.5 * np.cos(np.pi * u)
        out[:] = vs[seg] + (vs[seg + 1] - vs[seg]) * u
        out[idx < ts[0]] = vs[0]
        out[idx > ts[-1]] = vs[-1]
        return out
    return np.interp(idx, ts, vs)


def swell(n: int, attack: float, release: float) -> np.ndarray:
    """Smooth rise and fall (raised cosine both ends), flat in the middle."""
    env = np.ones(n)
    a = min(n_of(attack), n)
    r = min(n_of(release), n - a)
    env[:a] = raised_cos(a)
    if r > 0:
        env[n - r:] = raised_cos(r)[::-1]
    return env
