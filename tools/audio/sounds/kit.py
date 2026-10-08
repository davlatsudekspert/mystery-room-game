"""Reusable sound-design building blocks for the one-shot effects:
clicks, knocks, thumps, friction, stick-slip creaks, hum, relays, sparks,
whooshes and water drops. All return mono float64 signals."""
from __future__ import annotations

import numpy as np

from synth import env, modal, noise, osc, reverb
from synth.core import SR, n_of, add_at, time_axis
from synth.filters import biquad, butter, tv_biquad


def room(x: np.ndarray, wet: float = 0.12, ir: str = "lab") -> np.ndarray:
    """Place a dry mono sound in the lab (adds the reverb tail)."""
    return reverb.reverb(x, reverb.preset(ir), wet)


def limit(x: np.ndarray, seconds: float, fade_s: float = 0.3) -> np.ndarray:
    """Cap a sound's length, fading the last ``fade_s`` seconds smoothly."""
    n = min(len(x), n_of(seconds))
    y = np.array(x[:n], copy=True)
    f = min(n, n_of(fade_s))
    y[n - f:] *= np.cos(0.5 * np.pi * (np.arange(f) + 0.5) / f) ** 2
    return y


def tick(rng, f_lo=2500.0, f_hi=9000.0, count=14, t60=0.04, contact=0.00015,
         dur=0.12, noise_amt=0.5) -> np.ndarray:
    """Small hard click: brass detent, relay contact, latch."""
    md = modal.metal(rng, f_lo, f_hi, count, t60)
    return modal.strike(md, dur, contact, rng, noise=noise_amt, noise_decay=0.0006)


def knock(rng, f_lo=180.0, f_hi=1800.0, count=10, t60=0.07, contact=0.0012,
          dur=0.25, noise_amt=0.3) -> np.ndarray:
    """Wooden knock (walnut panel, drawer front, lid)."""
    md = modal.wood(rng, f_lo, f_hi, count, t60)
    return modal.strike(md, dur, contact, rng, noise=noise_amt, noise_decay=0.0015)


def clank(rng, f_lo=300.0, f_hi=5000.0, count=24, t60=0.35, contact=0.0006, dur=0.6,
          noise_amt=0.4) -> np.ndarray:
    """Heavier metal impact (bolt, safe door, lever)."""
    md = modal.random_modes(rng, f_lo, f_hi, count, t60 * 0.15, t60, -2.5)
    return modal.strike(md, dur, contact, rng, noise=noise_amt, noise_decay=0.001)


def thump(f_start=95.0, f_end=48.0, dur=0.4, t60=0.28, glide=0.05, harm=0.3) -> np.ndarray:
    """Low body thump: a sine with a fast downward pitch glide. Short-lived 2nd
    and 3rd harmonics let small (phone) speakers convey the weight even
    though they cannot reproduce the fundamental."""
    n = n_of(dur)
    t = time_axis(n)
    f = f_end + (f_start - f_end) * np.exp(-t / glide)
    ph = 2.0 * np.pi * osc.phase_cycles(f, n)
    x = np.sin(ph) + harm * (0.8 * np.sin(2 * ph) * np.exp(-t / (0.35 * t60))
                             + 0.45 * np.sin(3 * ph) * np.exp(-t / (0.25 * t60)))
    return x * env.ar(n, 0.0015, t60)


def friction(rng, dur, speed, f_lo=300.0, f_hi=2500.0, body: modal.Modes | None = None,
             body_gain=0.5, grit=0.35, grit_rate=900.0, rough_rate=35.0) -> np.ndarray:
    """Sliding contact: band-limited noise whose level and roughness follow
    ``speed`` (0..1 array), plus tiny grit impacts at a speed-dependent rate,
    optionally coloured by a resonant body."""
    n = n_of(dur)
    sp = np.clip(np.broadcast_to(speed, (n,)), 0, None)
    base = butter(noise.white(n, rng), "bandpass", (f_lo, f_hi), 2)
    rough = np.clip(1.0 + 0.7 * noise.smooth_random(n, rng, rough_rate, periodic=False), 0.2, None)
    g = butter(noise.dust(n, grit_rate * sp, rng, heavy_tail=0.6), "highpass", f_lo, 2)
    exc = base * sp * rough + grit * g * 0.6
    if body is not None:
        exc = 0.55 * exc + body_gain * modal.resonate(exc, body) * 0.15
    return exc


def stick_slip(rng, dur, rate, amp=None, jitter=0.06, width=0.00035) -> np.ndarray:
    """Impulse train with instantaneous rate ``rate`` (Hz, array or scalar):
    the excitation of a creak. ``jitter`` randomises intervals."""
    n = n_of(dur)
    r = np.broadcast_to(np.asarray(rate, float), (n,))
    a = np.ones(n) if amp is None else np.broadcast_to(np.asarray(amp, float), (n,))
    exc = np.zeros(n)
    t = 0.0
    while True:
        i = int(t * SR)
        if i >= n:
            break
        exc[i] += a[i] * rng.uniform(0.55, 1.0)
        t += max(1.0 / SR, (1.0 / max(r[i], 1.0)) * (1.0 + jitter * rng.standard_normal()))
    return np.convolve(exc, modal.contact_pulse(width))[:n]


def creak(rng, dur, rate, amp, body: modal.Modes, jitter=0.06, hiss=0.15,
          hiss_band=(1200.0, 5000.0)) -> np.ndarray:
    """Stick-slip creak through a resonant body (hinge, floorboard, door)."""
    n = n_of(dur)
    exc = stick_slip(rng, dur, rate, amp, jitter)
    out = modal.resonate(exc, body)
    out /= max(np.max(np.abs(out)), 1e-9)
    a = np.broadcast_to(np.asarray(amp, float), (n,))
    h = butter(noise.white(n, rng), "bandpass", hiss_band, 2) * a
    return out + hiss * h / max(np.max(np.abs(h)), 1e-9)


def hum(dur, f0=50.0, harmonics=None, phases_rng=None) -> np.ndarray:
    """Mains/transformer hum: 50 Hz series, the 100 Hz magnetostriction
    component dominant."""
    if harmonics is None:
        harmonics = {1: 0.35, 2: 1.0, 3: 0.32, 4: 0.42, 5: 0.1, 6: 0.18, 8: 0.08, 10: 0.05, 12: 0.03}
    n = n_of(dur)
    t = time_axis(n)
    out = np.zeros(n)
    for k, a in harmonics.items():
        ph = phases_rng.uniform(0, 2 * np.pi) if phases_rng is not None else 0.0
        out += a * np.sin(2 * np.pi * k * f0 * t + ph)
    return out / sum(harmonics.values())


def relay(rng, weight=1.0, dur=0.15) -> np.ndarray:
    """Relay pull-in: armature impact, contact bounces, small body thunk."""
    out = np.zeros(n_of(dur))
    add_at(out, tick(rng, 1800, 9500, 14, t60=0.025, contact=0.0001, dur=0.08), 0.0)
    for k, (dt, g) in enumerate([(0.0021, 0.45), (0.0043, 0.25), (0.0068, 0.12)]):
        add_at(out, tick(rng, 2500, 9000, 8, t60=0.012, contact=0.0001, dur=0.03), dt + rng.uniform(0, 0.0008), g)
    add_at(out, knock(rng, 140, 900, 7, t60=0.05, contact=0.0015, dur=0.12, noise_amt=0.1), 0.0, 0.6 * weight)
    return out


def buzz(dur, f0, rng, bright=2500.0, rough=0.3) -> np.ndarray:
    """Electrical buzz: a jittery pulse wave, band-limited."""
    n = n_of(dur)
    f = f0 * (1.0 + 0.004 * noise.smooth_random(n, rng, 30, periodic=False))
    x = osc.square(f, n, 0.3)
    x *= 1.0 + rough * noise.smooth_random(n, rng, 120, periodic=False)
    x = butter(x, "lowpass", bright, 2)
    return butter(x, "highpass", f0 * 0.8, 2)


def spark(rng, dur, rate_env, crackle=1.0, arc=0.4, arc_f=100.0) -> np.ndarray:
    """Electric spark/arc: heavy-tailed crackle impulses through small
    resonances, plus an intermittent arc buzz. ``rate_env`` (array, 0..1)
    shapes density over time."""
    n = n_of(dur)
    e = np.broadcast_to(rate_env, (n,))
    d = noise.dust(n, 2600.0 * e, rng, heavy_tail=0.8)
    md = modal.random_modes(rng, 1500, 11000, 10, 0.002, 0.008, -1.0)
    cr = 0.5 * butter(d, "highpass", 900, 2) + modal.resonate(d, md) * 0.08
    gate = np.clip(noise.smooth_random(n, rng, 25, periodic=False) * 2.0, 0, 1) * e
    ab = buzz(dur, arc_f, rng, bright=6000, rough=0.8) * gate
    out = crackle * cr / max(np.max(np.abs(cr)), 1e-9) + arc * ab / max(np.max(np.abs(ab)), 1e-9)
    return out


def whoosh(rng, dur, f_start, f_end, q=1.4, attack=0.3, release=0.5, color=-3.0) -> np.ndarray:
    """Air movement: coloured noise through a sweeping band-pass."""
    n = n_of(dur)
    x = noise.colored(n, rng, color)
    f = np.geomspace(f_start, f_end, n)
    y = tv_biquad(x, "bandpass", f, q, block=64)
    return y * env.swell(n, attack * dur, release * dur)


def drop(rng, f0=None, rise=None, dur=0.09, tick_amt=0.25) -> np.ndarray:
    """Water drop 'plink': a decaying sine with an upward chirp (bubble
    resonance) and a tiny impact tick."""
    n = n_of(dur)
    t = time_axis(n)
    f0 = rng.uniform(900, 2400) if f0 is None else f0
    rise = rng.uniform(2.0, 6.0) if rise is None else rise
    f = f0 * (1.0 + rise * t)
    s = osc.sine(f, n) * env.ar(n, 0.0004, rng.uniform(0.03, 0.07))
    tk = noise.white(n, rng) * np.exp(-t / 0.0006)
    return s + tick_amt * biquad(tk, "highpass", 2500)
