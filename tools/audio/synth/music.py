"""Musical building blocks: pitch helpers, struck instruments (music box,
celesta, bells, glass), evolving pads, drones and a loop-aware sequencer."""
from __future__ import annotations

import re

import numpy as np

from . import modal, osc
from .core import SR, n_of, add_at, add_circular, pan, raised_cos
from .env import swell, decay
from .filters import biquad, one_pole_lp

_NAMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(name: str) -> int:
    """'D4' -> 62, 'Bb3' -> 58, 'F#5' -> 78 (scientific pitch, C4 = 60)."""
    m = re.fullmatch(r"([A-G])([b#]?)(-?\d)", name)
    if not m:
        raise ValueError(name)
    acc = {"": 0, "b": -1, "#": 1}[m.group(2)]
    return 12 * (int(m.group(3)) + 1) + _NAMES[m.group(1)] + acc


def hz(note) -> float:
    m = midi(note) if isinstance(note, str) else note
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


# ---- struck instruments ---------------------------------------------------------

def music_box(f: float, vel: float, rng: np.random.Generator, dur: float = 4.0) -> np.ndarray:
    """Music-box tine with a faintly detuned twin (old comb, slight beating)."""
    md = modal.tine(f, t60=2.6 + 1.5 * (330.0 / max(f, 100.0)) ** 0.5, bright=0.18 + 0.2 * vel)
    md = md + modal.Modes(np.array([f * 1.0012, f * 2.0]), np.array([2.2, 0.9]), np.array([0.25, 0.08]))
    x = modal.strike(md, dur, contact=0.00035, rng=rng, noise=0.06, noise_decay=0.0015)
    return vel * x / max(np.max(np.abs(x)), 1e-9)


def celesta(f: float, vel: float, rng: np.random.Generator, dur: float = 4.0) -> np.ndarray:
    """Felt hammer on a steel plate over a wooden resonator: mostly
    fundamental, a little octave, brief inharmonic plate modes."""
    t60 = 2.2 * (523.0 / max(f, 100.0)) ** 0.35
    md = modal.Modes(
        f * np.array([1.0, 1.0007, 2.0, 3.0, 4.0, 2.756, 5.404]),
        t60 * np.array([1.0, 0.9, 0.35, 0.15, 0.08, 0.08, 0.03]),
        np.array([1.0, 0.3, 0.22 + 0.1 * vel, 0.07, 0.03, 0.12 * vel, 0.06 * vel]))
    x = modal.strike(md, dur, contact=0.0007 - 0.0003 * vel, rng=rng)
    return vel * x / max(np.max(np.abs(x)), 1e-9)


def bell(f: float, vel: float, rng: np.random.Generator, dur: float = 4.0, t60: float = 3.0,
         bright: float = 0.5) -> np.ndarray:
    md = modal.bell(f, t60=t60, bright=bright)
    x = modal.strike(md, dur, contact=0.0009, rng=rng)
    return vel * x / max(np.max(np.abs(x)), 1e-9)


def glass(f: float, vel: float, rng: np.random.Generator, dur: float = 3.0, t60: float = 2.0,
          attack: float = 0.0, bright: float = 0.4) -> np.ndarray:
    """Struck (attack=0) or softly swelled (attack>0) crystal glass."""
    md = modal.glass(f, t60=t60, bright=bright)
    x = modal.ring(md, dur, rng if attack > 0 else None)  # struck: zero phase, no onset click
    if attack > 0:
        x *= swell(len(x), attack, 0.0)
    else:
        x = np.convolve(x, modal.contact_pulse(0.0005))[:len(x)]
    return vel * x / max(np.max(np.abs(x)), 1e-9)


# ---- sustained voices -------------------------------------------------------------

def pad_note(f: float, dur: float, rng: np.random.Generator, *, attack: float = 4.0,
             release: float = 5.0, voices: int = 4, detune_cents: float = 9.0,
             cutoff: float = 1100.0, bright_cutoff: float = 2400.0, bright_rate: float = 0.05,
             width: float = 0.7, air: float = 0.12) -> np.ndarray:
    """Warm, slowly evolving string-like pad note (stereo).

    Detuned band-limited saws are lowpassed twice (dark and bright versions)
    and morphed by a slow LFO, giving a gently breathing timbre; a soft sine
    'air' layer an octave up adds glassy sheen."""
    n = n_of(dur)
    left = np.zeros(n)
    right = np.zeros(n)
    for v in range(voices):
        cents = detune_cents * (2.0 * v / max(voices - 1, 1) - 1.0) + rng.uniform(-1.5, 1.5)
        drift = osc.vibrato(f * 2 ** (cents / 1200), n, rng.uniform(0.07, 0.17), rng.uniform(2.0, 4.0),
                            rng.uniform(0, 1))
        s = osc.saw(drift, n, rng.uniform(0, 1))
        p = width * (2.0 * v / max(voices - 1, 1) - 1.0)
        ang = (p + 1.0) * np.pi / 4.0
        left += np.cos(ang) * s
        right += np.sin(ang) * s
    out = np.vstack([left, right]) / voices
    dark = biquad(out, "lowpass", cutoff, 0.6)
    dark = biquad(dark, "lowpass", cutoff * 1.4, 0.55)
    bright = biquad(out, "lowpass", bright_cutoff, 0.6)
    morph = 0.5 - 0.5 * np.cos(2 * np.pi * (np.arange(n) / SR * bright_rate + rng.uniform(0, 1)))
    out = dark + (bright - dark) * (0.35 * morph)
    if air > 0:
        a = osc.sine(osc.vibrato(2 * f, n, 0.11, 3.0, rng.uniform(0, 1)), n, rng.uniform(0, 1))
        b = osc.sine(osc.vibrato(2 * f * 1.002, n, 0.13, 3.0, rng.uniform(0, 1)), n, rng.uniform(0, 1))
        out += air * np.vstack([a, b])
    out *= swell(n, attack, release)
    return out


def drone(f: float, n: int, rng: np.random.Generator, harmonics=(1.0, 0.5, 0.18, 0.08),
          breath_rate: float = 0.03, depth: float = 0.35) -> np.ndarray:
    """Continuous drone (stereo). Use a loop-periodic ``f`` and rates that fit
    the loop for seamless results."""
    parts = [(k + 1, a) for k, a in enumerate(harmonics)]
    l = osc.additive(f, n, parts, rng.uniform(0, 1, len(parts)))
    r = osc.additive(f * 1.0, n, parts, rng.uniform(0, 1, len(parts)))
    env = 1.0 - depth * (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(n) / SR * breath_rate))
    return np.vstack([l, r]) * env


def bowed_metal(f: float, dur: float, rng: np.random.Generator, attack: float = 2.5,
                release: float = 3.0) -> np.ndarray:
    """Slow swell of an inharmonic metal object (like a bowed cymbal or
    resonant instrument casing), tuned so its lowest mode is ``f``."""
    n = n_of(dur)
    ratios = [1.0, 1.506, 2.0, 2.33, 2.98, 4.07, 5.2]
    amps = [1.0, 0.45, 0.3, 0.35, 0.18, 0.1, 0.06]
    out = np.zeros((2, n))
    for r, a in zip(ratios, amps):
        for c in range(2):
            fr = osc.vibrato(f * r * (1 + rng.uniform(-0.0015, 0.0015)), n, rng.uniform(0.1, 0.3), 2.0,
                             rng.uniform(0, 1))
            am = 1.0 + 0.25 * np.sin(2 * np.pi * (np.arange(n) / SR * rng.uniform(0.15, 0.5) + rng.uniform(0, 1)))
            out[c] += a * am * osc.sine(fr, n, rng.uniform(0, 1))
    return out * swell(n, attack, release) / sum(amps)


# ---- sequencing ----------------------------------------------------------------------

class Track:
    """A stereo buffer that notes are mixed into. In ``loop`` mode every
    placement wraps around, so anything ringing past the end continues at the
    start - the whole track is then exactly periodic."""

    def __init__(self, seconds: float, loop: bool):
        self.n = n_of(seconds)
        self.loop = loop
        self.buf = np.zeros((2, self.n))

    def add(self, t: float, sig: np.ndarray, gain: float = 1.0, pos: float = 0.0) -> None:
        s = pan(sig, pos) if sig.ndim == 1 else sig
        (add_circular if self.loop else add_at)(self.buf, s, t, gain)


__all__ = ["midi", "hz", "music_box", "celesta", "bell", "glass", "pad_note", "drone",
           "bowed_metal", "Track", "raised_cos", "decay", "one_pole_lp"]
