"""Granular texture engine: many short grains scheduled by a Poisson
process, each rendered by a callback, gain-scaled, panned and mixed (with
optional wrap-around so a textured loop has no seam)."""
from __future__ import annotations

from typing import Callable

import numpy as np

from .core import SR, n_of, add_at, add_circular, pan
from .noise import poisson_times

GrainFn = Callable[[np.random.Generator], np.ndarray]


def cloud(duration: float, rate, grain: GrainFn, rng: np.random.Generator, *,
          stereo: bool = True, gain_db: tuple[float, float] = (-18.0, 0.0),
          gain_skew: float = 2.0, pan_width: float = 0.9, circular: bool = True,
          gain_curve: Callable[[np.ndarray], np.ndarray] | None = None) -> np.ndarray:
    """Render a grain cloud.

    rate        grains per second (scalar or callable rate(t))
    grain       callback returning one mono grain
    gain_db     random grain gain range; ``gain_skew`` > 1 favours quiet grains
    gain_curve  optional callable giving an extra gain for each grain time
    circular    wrap grains that overrun the end back to the start
    """
    n = n_of(duration)
    out = np.zeros((2, n)) if stereo else np.zeros(n)
    times = poisson_times(duration, rate, rng)
    lo, hi = gain_db
    u = rng.uniform(0, 1, len(times)) ** gain_skew
    gains = 10 ** ((lo + (hi - lo) * u) / 20.0)
    if gain_curve is not None and len(times):
        gains = gains * gain_curve(times)
    pans = rng.uniform(-pan_width, pan_width, len(times))
    place = add_circular if circular else add_at
    for t, g, p in zip(times, gains, pans):
        g_sig = grain(rng)
        place(out, pan(g_sig, p) if stereo else g_sig, t, g)
    return out


def scatter(duration: float, events, render: Callable[[np.random.Generator, float], np.ndarray],
            rng: np.random.Generator, stereo: bool = True, circular: bool = True) -> np.ndarray:
    """Place explicitly timed events: ``events`` is ``[(t, gain, pan), ...]``
    and ``render(rng, t)`` returns the mono event signal."""
    n = n_of(duration)
    out = np.zeros((2, n)) if stereo else np.zeros(n)
    place = add_circular if circular else add_at
    for t, g, p in events:
        sig = render(rng, t)
        place(out, pan(sig, p) if stereo else sig, t, g)
    return out


__all__ = ["cloud", "scatter", "SR"]
