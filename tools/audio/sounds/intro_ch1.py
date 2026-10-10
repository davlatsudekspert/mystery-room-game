"""Chapter 1's opening: the heavy brass key turning in the heavy lock, and a distant roll of thunder over the rain."""
from __future__ import annotations

import numpy as np

from synth import env, modal, noise, osc
from synth.core import n_of, add_at, time_axis
from synth.filters import butter

from . import kit, sound


def _norm(x):
    return x / max(np.max(np.abs(x)), 1e-12)


@sound("intro_key", "sfx", "Chapter 1 opening: a heavy brass key slides into a heavy old lock, grinds round and the bolt drops")
def intro_key(rng):
    out = np.zeros(n_of(2.4))
    # the key slides in: a low metallic scrape with a few catches on the pins
    d = 0.42
    n = n_of(d)
    slide = kit.friction(rng, d, env.curve([(0, 0), (0.06, 0.8), (0.3, 0.55), (d, 0)], n, "cos"), 300, 2600,
                         body=modal.metal(rng, 500, 3000, 9, 0.1), grit=0.5, grit_rate=700)
    add_at(out, _norm(slide), 0.0, 0.3)
    for t, g in ((0.1, 0.5), (0.19, 0.4), (0.28, 0.35)):
        add_at(out, kit.tick(rng, 1400, 6500, 9, t60=0.03, contact=0.00025, dur=0.06), t, g)
    add_at(out, kit.clank(rng, 250, 2800, 12, t60=0.12, contact=0.0008, dur=0.2), 0.43, 0.5)   # key seats
    # the turn: a slow grinding rotation with a groaning wheel of tumblers
    d = 0.9
    n = n_of(d)
    turn = kit.friction(rng, d, env.curve([(0, 0), (0.1, 0.7), (0.5, 1.0), (0.8, 0.6), (d, 0)], n, "cos"), 180, 2200,
                        body=modal.metal(rng, 300, 2400, 10, 0.12), grit=0.6, grit_rate=520, rough_rate=18)
    add_at(out, _norm(turn), 0.7, 0.45)
    for t in (0.85, 1.0, 1.16, 1.3, 1.44):
        add_at(out, kit.tick(rng, 1000, 5200, 9, t60=0.035, contact=0.0003, dur=0.07), t + rng.uniform(-0.01, 0.01), 0.45)
    # the bolt drops: a deep clunk with a ring and a low thump that phone speakers can still hear
    add_at(out, kit.clank(rng, 140, 3200, 22, t60=0.4, contact=0.0012, dur=0.8), 1.62, 1.0)
    add_at(out, kit.thump(130, 60, 0.45, t60=0.3, glide=0.04), 1.62, 0.8)
    add_at(out, kit.thump(210, 120, 0.15, t60=0.08, glide=0.02), 1.66, 0.3)
    add_at(out, kit.tick(rng, 1800, 7600, 12, t60=0.03, contact=0.0002, dur=0.07), 1.64, 0.5)
    return kit.room(out, 0.2, "corridor")


@sound("intro_thunder", "sfx", "Chapter 1 opening: a long, distant roll of thunder behind the rain")
def intro_thunder(rng):
    dur = 5.0
    n = n_of(dur)
    t = time_axis(n)
    x = noise.brown(n, rng)
    x = butter(x, "lowpass", 220, 2)
    # a few swells of rolling energy, one main crack far away
    g = np.zeros(n)
    for t0, a, w in ((0.15, 1.0, 0.6), (0.9, 0.7, 0.9), (1.9, 0.5, 1.2), (3.0, 0.25, 1.4)):
        g += a * np.exp(-0.5 * ((t - t0) / (w * 0.5)) ** 2) * (0.6 + 0.4 * np.sin(2 * np.pi * (3.0 + t0) * t))
    y = x * np.clip(g, 0, None)
    y += 0.12 * butter(noise.white(n, rng), "bandpass", (80, 600), 2) * np.exp(-t / 0.5) * (t > 0.1)
    y *= env.swell(n, 0.25, 1.6)
    return _norm(y)
