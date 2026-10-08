"""Noise sources: white, coloured (FFT-shaped and therefore loop-periodic),
sparse impulses (dust / crackle) and smooth random control curves."""
from __future__ import annotations

import numpy as np

from .core import SR


def white(n: int, rng: np.random.Generator) -> np.ndarray:
    return rng.standard_normal(n) * 0.3


def colored(n: int, rng: np.random.Generator, slope_db_oct: float = -3.0,
            lo: float | None = None, hi: float | None = None, skirt_oct: float = 0.5) -> np.ndarray:
    """Gaussian noise with a spectral slope (dB/octave), optionally band-limited.
    Built in the frequency domain, so it is exactly periodic with period ``n``
    (perfect for seamless loops). Normalised to RMS 0.25."""
    from .filters import smooth_band
    spec = rng.standard_normal(n // 2 + 1) + 1j * rng.standard_normal(n // 2 + 1)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    g = np.power(np.maximum(f, 10.0) / 1000.0, slope_db_oct / 6.0206)
    g *= smooth_band(f, lo, hi, skirt_oct)
    g[0] = 0.0
    y = np.fft.irfft(spec * g, n=n)
    r = np.sqrt(np.mean(y * y))
    return y * (0.25 / r) if r > 0 else y


def pink(n, rng, lo=None, hi=None):
    return colored(n, rng, -3.0, lo, hi)


def brown(n, rng, lo=None, hi=None):
    return colored(n, rng, -6.0, lo, hi)


def smooth_random(n: int, rng: np.random.Generator, rate_hz: float, periodic: bool = True) -> np.ndarray:
    """Slowly wandering control signal with roughly ``rate_hz`` bandwidth,
    scaled to about [-1, 1]. Periodic by construction when ``periodic``."""
    m = n if periodic else 2 * n
    spec = rng.standard_normal(m // 2 + 1) + 1j * rng.standard_normal(m // 2 + 1)
    f = np.fft.rfftfreq(m, 1.0 / SR)
    spec *= np.exp(-0.5 * (f / max(rate_hz, 1e-4)) ** 2)
    spec[0] = 0.0
    y = np.fft.irfft(spec, n=m)[:n]
    p = np.max(np.abs(y))
    return y / p if p > 0 else y


def poisson_times(duration: float, rate, rng: np.random.Generator, t0: float = 0.0) -> np.ndarray:
    """Event times of a (possibly inhomogeneous) Poisson process on
    [t0, t0+duration). ``rate`` is events/s or a callable rate(t_array)."""
    if callable(rate):
        probe = np.linspace(t0, t0 + duration, 512)
        rmax = float(np.max(rate(probe))) * 1.05 + 1e-9
        count = rng.poisson(rmax * duration)
        ts = np.sort(rng.uniform(t0, t0 + duration, count))
        keep = rng.uniform(0, rmax, count) < rate(ts)
        return ts[keep]
    count = rng.poisson(max(rate, 0.0) * duration)
    return np.sort(rng.uniform(t0, t0 + duration, count))


def dust(n: int, rate_hz, rng: np.random.Generator, heavy_tail: float = 0.0) -> np.ndarray:
    """Sparse random impulses with random sign. ``rate_hz`` may be a per-sample
    array. ``heavy_tail`` > 0 makes a few impulses much louder (crackle)."""
    rate = np.broadcast_to(np.asarray(rate_hz, dtype=np.float64), (n,))
    hits = rng.uniform(0, 1, n) < rate / SR
    out = np.zeros(n)
    k = int(np.count_nonzero(hits))
    amps = rng.uniform(0.2, 1.0, k)
    if heavy_tail > 0:
        amps = amps * (rng.pareto(1.0 / heavy_tail, k) + 1.0) ** 0.5
        amps /= max(np.max(amps), 1e-9)
    out[hits] = amps * rng.choice([-1.0, 1.0], k)
    return out
