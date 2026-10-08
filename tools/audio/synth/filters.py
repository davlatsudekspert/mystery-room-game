"""Biquad (RBJ Audio-EQ-Cookbook) filters, time-varying filters and
zero-phase FFT filters for loop-safe (circular) processing."""
from __future__ import annotations

import numpy as np
from scipy import signal as _sig

from .core import SR, NYQ


def biquad_coeffs(kind: str, f0: float, q: float = 0.7071, gain_db: float = 0.0):
    """Return normalised (b, a) for an RBJ cookbook biquad."""
    f0 = float(np.clip(f0, 5.0, NYQ * 0.98))
    w0 = 2.0 * np.pi * f0 / SR
    cw, sw = np.cos(w0), np.sin(w0)
    alpha = sw / (2.0 * q)
    A = 10.0 ** (gain_db / 40.0)
    if kind == "lowpass":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "highpass":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "bandpass":  # constant 0 dB peak gain
        b = [alpha, 0.0, -alpha]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "notch":
        b = [1.0, -2 * cw, 1.0]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "allpass":
        b = [1 - alpha, -2 * cw, 1 + alpha]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "peak":
        b = [1 + alpha * A, -2 * cw, 1 - alpha * A]
        a = [1 + alpha / A, -2 * cw, 1 - alpha / A]
    elif kind in ("lowshelf", "highshelf"):
        sq = 2.0 * np.sqrt(A) * alpha
        if kind == "lowshelf":
            b = [A * ((A + 1) - (A - 1) * cw + sq), 2 * A * ((A - 1) - (A + 1) * cw),
                 A * ((A + 1) - (A - 1) * cw - sq)]
            a = [(A + 1) + (A - 1) * cw + sq, -2 * ((A - 1) + (A + 1) * cw),
                 (A + 1) + (A - 1) * cw - sq]
        else:
            b = [A * ((A + 1) + (A - 1) * cw + sq), -2 * A * ((A - 1) + (A + 1) * cw),
                 A * ((A + 1) + (A - 1) * cw - sq)]
            a = [(A + 1) - (A - 1) * cw + sq, 2 * ((A - 1) - (A + 1) * cw),
                 (A + 1) - (A - 1) * cw - sq]
    else:
        raise ValueError(f"unknown biquad kind {kind!r}")
    b = np.asarray(b) / a[0]
    a = np.asarray(a) / a[0]
    return b, a


def biquad(x: np.ndarray, kind: str, f0: float, q: float = 0.7071, gain_db: float = 0.0) -> np.ndarray:
    b, a = biquad_coeffs(kind, f0, q, gain_db)
    return _sig.lfilter(b, a, x, axis=-1)


def lowpass(x, f0, q=0.7071):
    return biquad(x, "lowpass", f0, q)


def highpass(x, f0, q=0.7071):
    return biquad(x, "highpass", f0, q)


def bandpass(x, f0, q=1.0):
    return biquad(x, "bandpass", f0, q)


def peak_eq(x, f0, gain_db, q=1.0):
    return biquad(x, "peak", f0, q, gain_db)


def shelf(x, kind, f0, gain_db, q=0.7071):
    return biquad(x, kind, f0, q, gain_db)


def butter(x: np.ndarray, kind: str, freq, order: int = 4) -> np.ndarray:
    """Butterworth via second-order sections. ``freq`` is a scalar, or a
    (lo, hi) pair for 'bandpass'/'bandstop'."""
    sos = _sig.butter(order, freq, btype=kind, fs=SR, output="sos")
    return _sig.sosfilt(sos, x, axis=-1)


def one_pole_lp(x: np.ndarray, fc: float) -> np.ndarray:
    a1 = np.exp(-2.0 * np.pi * fc / SR)
    return _sig.lfilter([1.0 - a1], [1.0, -a1], x, axis=-1)


def tv_biquad(x: np.ndarray, kind: str, f0, q=0.7071, gain_db: float = 0.0, block: int = 32) -> np.ndarray:
    """Time-varying biquad: ``f0`` (and optionally ``q``) are per-sample arrays.
    Coefficients are updated every ``block`` samples while the transposed
    direct-form state is carried across blocks, which is smooth for sweeps."""
    if x.ndim == 2:
        return np.vstack([tv_biquad(c, kind, f0, q, gain_db, block) for c in x])
    n = x.shape[0]
    f0 = np.broadcast_to(np.asarray(f0, dtype=np.float64), (n,))
    qa = np.broadcast_to(np.asarray(q, dtype=np.float64), (n,))
    y = np.empty(n)
    zi = np.zeros(2)
    for s in range(0, n, block):
        e = min(n, s + block)
        m = (s + e) // 2
        b, a = biquad_coeffs(kind, f0[m], qa[m], gain_db)
        y[s:e], zi = _sig.lfilter(b, a, x[s:e], zi=zi)
    return y


def fft_filter(x: np.ndarray, response) -> np.ndarray:
    """Zero-phase *circular* filter: multiplies the spectrum by
    ``response(freqs_hz) -> gain``. Ideal for loops: the result stays periodic."""
    n = x.shape[-1]
    X = np.fft.rfft(x, axis=-1)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    X *= response(f)
    return np.fft.irfft(X, n=n, axis=-1)


def smooth_band(f: np.ndarray, lo: float | None, hi: float | None, slope_oct: float = 0.5) -> np.ndarray:
    """Gain curve: 1 inside [lo, hi], raised-cosine skirts ``slope_oct`` octaves wide."""
    g = np.ones_like(f)
    lf = np.log2(np.maximum(f, 1e-3))
    if lo is not None:
        u = np.clip((lf - (np.log2(lo) - slope_oct)) / slope_oct, 0, 1)
        g *= 0.5 - 0.5 * np.cos(np.pi * u)
    if hi is not None:
        u = np.clip(((np.log2(hi) + slope_oct) - lf) / slope_oct, 0, 1)
        g *= 0.5 - 0.5 * np.cos(np.pi * u)
    return g


def circular_lfilter(b, a, x: np.ndarray, warm: int | None = None) -> np.ndarray:
    """Run an IIR filter as if the input repeated forever (steady state), by
    filtering a warm-up copy of the tail first. Keeps loops seamless."""
    n = x.shape[-1]
    w = n if warm is None else min(warm, n)
    ext = np.concatenate([x[..., n - w:], x], axis=-1)
    y = _sig.lfilter(b, a, ext, axis=-1)
    return y[..., w:]
