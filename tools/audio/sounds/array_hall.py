"""Chapter 4 ambience, the Array Hall (the unnumbered floor). Three seamless 60 s room tones:
``amb_array_hall`` (the bridge, the catwalk, the lift bay, Panel 0 and the apse: the big dark hall), ``amb_array_core``
(the island, the Core's own note) and ``amb_array_rooms`` (the booth and the watch room: small, warm, a clock).

The same rule as Chapter 3 (the owner's report of a steady hiss on the phone): **none of these beds is a broadband
noise floor.** The hall is a deep, tonal hum on A (the Core's note is A3, 220 Hz: only octaves and fifths of A, so it
agrees with the chapter's score and with ``ArrayHallTones``), narrow bands of air a few Hz wide, and sparse details
(the rings settling, a far relay, a technician's pencil tick, a glass-tube answer). Noise appears only band-limited
(below 450 Hz or a few Hz around a pitch) or in short envelopes.

Every layer is exactly periodic (loop-periodic frequencies, FFT-built noise, events and reverb tails mixed
circularly), so the loops are seamless by construction; ``synth_all`` verifies the encoded files."""
from __future__ import annotations

import numpy as np

from synth import noise, reverb
from synth.core import add_circular, n_of, pan
from synth.filters import biquad, butter
from synth.music import hz

from . import kit, sound
from .underground import LOOP, _band, _drift, _hum, _norm, _resonance, _settle
from functools import lru_cache


@lru_cache(maxsize=None)
def _ir(kind: str) -> np.ndarray:
    if kind == "hall":    # a huge round hall under the rock: very long, dark
        return reverb.synth_ir(7.5, 7411, stereo=True, predelay=0.04, lf_ratio=1.15, hf_ratio=0.28, early=12,
                               early_span=0.14, onset=0.09, tone_hi=5500)
    if kind == "core":    # the glass dome round the Core: bright, medium
        return reverb.synth_ir(4.2, 7412, stereo=True, predelay=0.02, lf_ratio=1.0, hf_ratio=0.5, early=14,
                               early_span=0.07, onset=0.04, tone_hi=8000)
    if kind == "rooms":   # a panelled office behind glass: small, warm
        return reverb.synth_ir(0.9, 7413, stereo=True, predelay=0.006, lf_ratio=1.0, hf_ratio=0.4, early=10,
                               early_span=0.03, tone_hi=7000)
    raise KeyError(kind)


def _wet(x: np.ndarray, kind: str, wet: float, dry: float = 1.0) -> np.ndarray:
    return reverb.reverb_circular(x, _ir(kind), wet, dry)


def _hall_parts(rng) -> dict:
    n = n_of(LOOP)
    parts: dict[str, np.ndarray] = {}
    # 1) the Array's mains: a low even hum on A (A1 ... : octaves and fifths only)
    parts["hum"] = 0.10 * _hum(n, rng, hz("A1"), {2: 0.8, 3: 0.55, 4: 1.0, 6: 0.7, 8: 0.5, 12: 0.32, 16: 0.2},
                               wander=0.15, rough=0.2)
    # 2) the weight of the hall: a very soft rumble, brown noise 35-140 Hz
    parts["rumble"] = 0.045 * np.vstack([noise.colored(n, rng, -6.0, 35, 140), noise.colored(n, rng, -6.0, 35, 140)]) \
        * (0.7 + 0.3 * noise.smooth_random(n, rng, 0.05))
    # 3) air moving over the rings: narrow bands at A-family pitches, slowly breathing
    air = np.zeros((2, n))
    for f, a, r in ((220.0, 1.0, 0.05), (330.0, 0.7, 0.07), (440.0, 0.6, 0.06), (660.0, 0.35, 0.08)):
        for c in range(2):
            air[c] += a * _band(n, rng, f) * _drift(n, rng, r) ** 2
    parts["air"] = 0.20 * air
    # 4) rare answers of the glass towers, long and soft
    res = np.zeros((2, n))
    for t0, nn, p, g in ((7.0, "E5", -0.4, 0.9), (22.0, "A4", 0.5, 0.8), (35.5, "C#5", -0.2, 0.7), (49.0, "E5", 0.45, 0.8)):
        add_circular(res, pan(_resonance(hz(nn), rng, dur=12.0, attack=2.0, t60=8.0, bright=0.3), p),
                     t0 + rng.uniform(0, 0.4), g)
    parts["towers"] = 0.20 * _wet(res, "hall", 0.65, 0.4)
    # 5) far off: a contactor, and a ring settling on its bearing (a low knock)
    ev = np.zeros((2, n))
    for t0, p in ((14.2, 0.6), (41.7, -0.5)):
        add_circular(ev, pan(_norm(butter(kit.relay(rng, 0.6), "lowpass", 3000, 2)), p), t0, 1.0)
    for t0, p in ((29.0, -0.3), (55.0, 0.35)):
        add_circular(ev, pan(_norm(butter(kit.thump(f_start=70.0, f_end=46.0, dur=0.6, t60=0.4), "lowpass", 420, 2)), p), t0, 0.8)
    parts["far"] = 0.11 * _wet(ev, "hall", 0.55, 0.9)
    return parts


@sound("amb_array_hall", "ambience",
       "Array Hall: a deep mains hum on A, faint breathing air over the rings, rare glass-tower answers, a far "
       "contactor and a ring settling (no noise bed)",
       loop=True, lufs=-24.0)
def amb_array_hall(rng):
    out = sum(_hall_parts(rng).values())
    return _settle(_wet(out, "hall", 0.12, 1.0))


def _core_parts(rng) -> dict:
    n = n_of(LOOP)
    parts: dict[str, np.ndarray] = {}
    # the Core's own note A3 (220 Hz) held, with its octave and fifth, each breathing at its own slow rate
    parts["note"] = 0.085 * _hum(n, rng, hz("A2"), {2: 1.0, 3: 0.45, 4: 0.6, 6: 0.3, 8: 0.2}, wander=0.25)
    parts["sub"] = 0.04 * _hum(n, rng, hz("A1"), {1: 0.6, 2: 0.7, 3: 0.3}, wander=0.2)
    air = np.zeros((2, n))
    for f, a, r in ((440.0, 1.0, 0.06), (660.0, 0.6, 0.08), (880.0, 0.35, 0.09)):
        for c in range(2):
            air[c] += a * _band(n, rng, f, 0.008) * _drift(n, rng, r) ** 2
    parts["shimmer"] = 0.16 * air
    res = np.zeros((2, n))
    for t0, nn, p, g in ((9.0, "A5", 0.4, 0.8), (26.0, "E5", -0.5, 0.9), (38.0, "C#6", 0.2, 0.55), (51.5, "A4", -0.3, 0.9)):
        add_circular(res, pan(_resonance(hz(nn), rng, dur=11.0, attack=1.4, t60=7.0, bright=0.4), p),
                     t0 + rng.uniform(0, 0.4), g)
    parts["glass"] = 0.20 * _wet(res, "core", 0.6, 0.4)
    return parts


@sound("amb_array_core", "ambience",
       "The Core: its own note A held with octave and fifth, a narrow shimmer, slow glass answers (no noise bed)",
       loop=True, lufs=-24.0)
def amb_array_core(rng):
    out = sum(_core_parts(rng).values())
    return _settle(_wet(out, "core", 0.12, 1.0))


def _rooms_parts(rng) -> dict:
    n = n_of(LOOP)
    parts: dict[str, np.ndarray] = {}
    # a desk lamp's transformer: 100 Hz comb that stops near 1.2 kHz, and the building's A beneath it
    parts["lamp"] = 0.075 * _hum(n, rng, 100.0, {1: 0.7, 2: 0.6, 3: 0.4, 4: 0.3, 6: 0.15, 8: 0.08, 12: 0.04},
                                 wander=0.2, rough=0.3)
    parts["floor"] = 0.07 * _hum(n, rng, hz("A1"), {2: 0.8, 3: 0.5, 4: 0.8, 6: 0.4}, wander=0.15)
    ev = np.zeros((2, n))
    # a wall clock: one soft tick every 2 s, the louder every fourth
    for k in range(30):
        tk = _norm(biquad(kit.tick(rng, f_lo=1500.0, f_hi=3500.0, count=6, t60=0.02), "lowpass", 4200, 0.7))
        add_circular(ev, pan(tk, 0.3), 1.0 + 2.0 * k, 0.5 if k % 4 else 0.8)
    # a pencil on a pad, once, and the old pipe ticking as it cools
    add_circular(ev, pan(_norm(kit.knock(rng, f_lo=700.0, f_hi=1400.0, count=3)), -0.4), 33.4, 0.6)
    add_circular(ev, pan(_norm(kit.knock(rng, f_lo=250.0, f_hi=700.0, count=2)), 0.5), 47.8, 0.7)
    parts["ticks"] = 0.07 * _wet(ev, "rooms", 0.35, 1.0)
    return parts


@sound("amb_array_rooms", "ambience",
       "Booth and watch room: a lamp transformer's hum, the floor's A beneath it, a wall clock, a pencil, a pipe "
       "(no noise bed)",
       loop=True, lufs=-24.0)
def amb_array_rooms(rng):
    out = sum(_rooms_parts(rng).values())
    return _settle(_wet(out, "rooms", 0.10, 1.0))
