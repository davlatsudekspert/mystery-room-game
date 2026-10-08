"""Modal synthesis: objects are modelled as banks of exponentially decaying
sinusoidal modes (frequency, T60, amplitude). Struck sounds are the mode sum
shaped by a contact pulse; scraped/creaking sounds drive the same modes as
resonant filters with an arbitrary excitation signal."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import signal as _sig

from .core import SR, NYQ, n_of
from .env import LN1000


@dataclass
class Modes:
    freqs: np.ndarray
    t60s: np.ndarray
    amps: np.ndarray

    def scaled(self, freq_mul: float = 1.0, t60_mul: float = 1.0, amp_mul: float = 1.0) -> "Modes":
        return Modes(self.freqs * freq_mul, self.t60s * t60_mul, self.amps * amp_mul)

    def __add__(self, other: "Modes") -> "Modes":
        return Modes(np.concatenate([self.freqs, other.freqs]),
                     np.concatenate([self.t60s, other.t60s]),
                     np.concatenate([self.amps, other.amps]))


def modes_from_ratios(f0: float, ratios, t60s, amps) -> Modes:
    r = np.asarray(ratios, dtype=np.float64)
    return Modes(f0 * r, np.broadcast_to(np.asarray(t60s, float), r.shape).copy(),
                 np.broadcast_to(np.asarray(amps, float), r.shape).copy())


# ---- mode recipes ---------------------------------------------------------------

def bar(f0: float, t60: float = 1.0, count: int = 5, bright: float = 0.5) -> Modes:
    """Free-free bar (xylophone/celesta plate). Higher modes decay faster."""
    ratios = np.array([1.0, 2.756, 5.404, 8.933, 13.344, 18.638])[:count]
    t60s = t60 / ratios ** 0.9
    amps = bright ** np.arange(count)
    return Modes(f0 * ratios, t60s, amps)


def tine(f0: float, t60: float = 2.0, bright: float = 0.35) -> Modes:
    """Cantilever tine (music box comb): 1 : 6.27 : 17.55 : 34.39."""
    ratios = np.array([1.0, 6.267, 17.547, 34.386])
    t60s = t60 * np.array([1.0, 0.18, 0.05, 0.02])
    amps = np.array([1.0, bright, bright * 0.45, bright * 0.2])
    return Modes(f0 * ratios, t60s, amps)


def bell(f0: float, t60: float = 3.0, bright: float = 0.6) -> Modes:
    """Tuned bell partials (hum, prime, tierce, quint, nominal ...).
    ``f0`` is the prime (heard as the strike note); hum = f0/2, nominal = 2*f0."""
    ratios = np.array([0.5, 1.0, 1.2, 1.5, 2.0, 2.5, 2.66, 3.0, 4.0, 5.33, 6.0])
    amps = np.array([0.35, 0.8, 0.45, 0.25, 1.0, 0.25, 0.3, 0.25, 0.18, 0.12, 0.08])
    amps[4:] *= bright / 0.6
    t60s = t60 * np.array([1.6, 1.2, 0.9, 0.7, 0.8, 0.45, 0.4, 0.35, 0.25, 0.18, 0.12])
    return Modes(f0 * ratios, t60s, amps)


def glass(f0: float, t60: float = 1.5, bright: float = 0.5) -> Modes:
    """Glass bowl / crystal: few, widely spaced, long-ringing modes."""
    ratios = np.array([1.0, 2.32, 4.25, 6.63, 9.38])
    amps = np.array([1.0, 0.6, 0.35, 0.2, 0.1])
    amps[1:] *= 2.0 * bright
    t60s = t60 * np.array([1.0, 0.7, 0.45, 0.3, 0.2])
    return Modes(f0 * ratios, t60s, amps)


def random_modes(rng: np.random.Generator, f_lo: float, f_hi: float, count: int,
                 t60_lo: float, t60_hi: float, tilt_db_oct: float = -3.0) -> Modes:
    """Inharmonic object: log-uniform frequencies. T60 shrinks with frequency,
    from about ``t60_hi`` at ``f_lo`` to ``t60_lo`` at ``f_hi``; amplitudes
    follow a spectral tilt in dB/octave."""
    lf = rng.uniform(np.log(f_lo), np.log(f_hi), count)
    freqs = np.exp(lf)
    u = (lf - np.log(f_lo)) / max(np.log(f_hi) - np.log(f_lo), 1e-9)
    t60s = np.exp(np.log(t60_hi) * (1 - u) + np.log(t60_lo) * u) * rng.uniform(0.7, 1.3, count)
    octs = np.log2(freqs / f_lo)
    amps = 10 ** (tilt_db_oct * octs / 20.0) * rng.uniform(0.4, 1.0, count)
    return Modes(freqs, t60s, amps)


def wood(rng, f_lo=150.0, f_hi=2500.0, count=10, t60=0.08) -> Modes:
    """Wooden body: low-Q, short-lived modes."""
    return random_modes(rng, f_lo, f_hi, count, t60 * 0.35, t60, -2.0)


def metal(rng, f_lo=800.0, f_hi=9000.0, count=16, t60=0.3) -> Modes:
    """Small brass/steel part: dense, brighter, longer-ringing modes."""
    return random_modes(rng, f_lo, f_hi, count, t60 * 0.25, t60, -1.0)


# ---- rendering --------------------------------------------------------------------

def ring(modes: Modes, dur: float, rng: np.random.Generator | None = None) -> np.ndarray:
    """Impulse response of the mode bank (sum of decaying sines). Modes start
    at sine phase 0 like a physically struck object (no onset step/click);
    pass ``rng`` to randomise phases for sustained, swelled uses."""
    n = n_of(dur)
    t = np.arange(n) / SR
    out = np.zeros(n)
    phases = rng.uniform(0, 2 * np.pi, len(modes.freqs)) if rng is not None else np.zeros(len(modes.freqs))
    for f, t60, a, ph in zip(modes.freqs, modes.t60s, modes.amps, phases):
        if f >= NYQ * 0.95 or f <= 0 or a == 0:
            continue
        m = min(n, n_of(t60 * 1.3) + 1)  # stop after ~-78 dB
        out[:m] += a * np.exp(-LN1000 * t[:m] / t60) * np.sin(2 * np.pi * f * t[:m] + ph)
    return out


def contact_pulse(width: float) -> np.ndarray:
    """Half-sine force pulse; shorter contact -> brighter strike."""
    k = max(1, n_of(width))
    p = np.sin(np.pi * (np.arange(k) + 0.5) / k)
    return p / p.sum()


def strike(modes: Modes, dur: float, contact: float = 0.0004, rng=None,
           noise: float = 0.0, noise_decay: float = 0.004) -> np.ndarray:
    """Struck object: mode bank excited by a contact pulse, plus an optional
    short noise transient (the 'tick' of the contact itself)."""
    out = _sig.oaconvolve(ring(modes, dur), contact_pulse(contact))[:n_of(dur)]
    if noise > 0 and rng is not None:
        k = n_of(noise_decay * 6)
        tick = rng.standard_normal(k) * np.exp(-np.arange(k) / (SR * noise_decay))
        out[:k] += noise * tick * np.max(np.abs(out[:n_of(0.01)]) + 1e-9)
    return out


def resonate(x: np.ndarray, modes: Modes) -> np.ndarray:
    """Filter an excitation through the modes (2-pole resonators in parallel).
    Each resonator's impulse response is a unit-amplitude decaying sine."""
    out = np.zeros_like(x)
    for f, t60, a in zip(modes.freqs, modes.t60s, modes.amps):
        if f >= NYQ * 0.95 or f <= 0 or a == 0:
            continue
        w = 2 * np.pi * f / SR
        r = np.exp(-LN1000 / (SR * max(t60, 1e-4)))
        out += a * _sig.lfilter([0.0, np.sin(w)], [1.0, -2 * r * np.cos(w), r * r], x)
    return out
