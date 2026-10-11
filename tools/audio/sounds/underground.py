"""Chapter 3 ambience, the Underground Facility (Level -2). Four seamless 60 s room tones, one per zone of
``underground_room.gd`` (``amb_choir``, ``amb_gallery``, ``amb_nursery``, ``amb_lift``).

Design rule, learnt from the owner's report of a steady hiss on the phone: **none of these beds is a
broadband noise floor.** Each room tone is made of tonal material (a transformer or machine hum built from
E and its fifth, narrow resonating bands, glass tones) and sparse details (rare tube resonances, a distant
drip, soft steam puffs, cooling ticks, cable creaks). The only noise in them is
  * band-limited to a few Hz around a pitch (the 'air' of the gallery) or below 450 Hz (the shaft), or
  * confined to short envelopes (the autoclave's steam puffs, about a fifth of the loop).
Apart from the nursery's lamp buzz (a tonal comb of 100 Hz harmonics that stops near 2 kHz), nothing sits
above 1 kHz all the time.

The hums are built with the same frequency in both channels, so they stay steady when a phone speaker
sums the channels to mono (see ``_hum``).

Every layer is exactly periodic (frequencies with a whole number of cycles per loop, FFT-built noise,
events and reverb tails mixed circularly), so the loops are seamless by construction; ``synth_all``
verifies the encoded files."""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from synth import env, modal, music, noise, osc, reverb
from synth.core import SR, add_circular, n_of, pan, time_axis
from synth.filters import biquad, butter, fft_filter, smooth_band, tv_biquad
from synth.loops import periodic_freq, rotate_to_calm_point
from synth.music import hz

from . import kit, sound

LOOP = 60.0


# ---- rooms (synthesised IRs, cached; deterministic seeds) ------------------------------------------

@lru_cache(maxsize=None)
def _ir(kind: str) -> np.ndarray:
    if kind == "choir":    # the machine hall: big, concrete, brass tubes and steel cabinets
        return reverb.synth_ir(3.0, 7311, stereo=True, predelay=0.02, lf_ratio=1.2, hf_ratio=0.4, early=14,
                               early_span=0.08, onset=0.04, tone_hi=7000)
    if kind == "gallery":  # a round gallery over a deep hall: long, dark, a slow build-up
        return reverb.synth_ir(6.5, 7312, stereo=True, predelay=0.035, lf_ratio=1.1, hf_ratio=0.3, early=10,
                               early_span=0.12, onset=0.08, tone_hi=6000)
    if kind == "nursery":  # tiled, warm, small
        return reverb.synth_ir(1.1, 7313, stereo=True, predelay=0.008, lf_ratio=1.0, hf_ratio=0.45, early=12,
                               early_span=0.04, tone_hi=8000)
    if kind == "lift":     # a bare concrete shaft with a steel cage
        return reverb.synth_ir(2.6, 7314, stereo=True, predelay=0.015, lf_ratio=1.1, hf_ratio=0.5, early=8,
                               early_span=0.05, onset=0.02, tone_hi=6000)
    raise KeyError(kind)


def _wet(x: np.ndarray, kind: str, wet: float, dry: float = 1.0) -> np.ndarray:
    return reverb.reverb_circular(x, _ir(kind), wet, dry)


def _norm(x: np.ndarray) -> np.ndarray:
    return x / max(float(np.max(np.abs(x))), 1e-9)


# ---- building blocks -------------------------------------------------------------------------------

def _hum(n: int, rng, f0: float, partials: dict, wander: float = 0.15, spread: float = 0.0005,
         rough: float = 0.0) -> np.ndarray:
    """Stereo hum: the harmonic series of ``f0`` with every partial on a loop-periodic frequency, a slow
    loop-periodic level wander per channel and a different phase per channel (a soft stereo image).
    Both channels share each partial's frequency on purpose: a detune between the channels would beat
    at full depth when a phone speaker sums them to mono (the first renders swung 8-10 dB that way).
    ``spread`` is a small relative detune of the whole series from ``f0``; ``rough`` adds a little
    amplitude roughness to the upper partials (magnetostriction grain)."""
    t = time_axis(n)
    out = np.zeros((2, n))
    for k, a in partials.items():
        grain = 1.0 + rough * noise.smooth_random(n, rng, 12.0) if rough > 0 and k >= 6 else 1.0
        f = periodic_freq(f0 * k * (1.0 + rng.uniform(-spread, spread)), LOOP)
        base = rng.uniform(0, 2 * np.pi)
        for c in range(2):
            lvl = 1.0 + wander * np.sin(2 * np.pi * (rng.integers(1, 5) / LOOP) * t + rng.uniform(0, 2 * np.pi))
            out[c] += a * lvl * grain * np.sin(2 * np.pi * f * t + base + rng.uniform(-0.4, 0.4) * np.pi)
    return out


def _band(n: int, rng, f: float, rel_bw: float = 0.012) -> np.ndarray:
    """Noise confined to a few Hz around ``f`` (exactly periodic): a breathy, tonal shimmer, not hiss."""
    return noise.colored(n, rng, 0.0, f * (1.0 - rel_bw), f * (1.0 + rel_bw), skirt_oct=0.03)


def _drift(n: int, rng, rate: float, depth: float = 0.45) -> np.ndarray:
    """A slow, positive level curve (loop-periodic)."""
    return np.clip((1.0 - depth) + depth * noise.smooth_random(n, rng, rate), 0.03, 1.3)


def _resonance(f: float, rng, dur: float = 11.0, attack: float = 1.6, t60: float = 7.0, bright: float = 0.3) -> np.ndarray:
    """A crystal tube or glass rod singing in sympathy: slowly swelled, long ringing, with a faintly
    detuned twin so it shimmers (mono)."""
    x = music.glass(f, 0.5, rng, dur=dur, t60=t60, attack=attack, bright=bright)
    x += 0.7 * music.glass(f * 1.0014, 0.5, rng, dur=dur, t60=t60, attack=attack, bright=bright)
    return x / 1.7


def _settle(x: np.ndarray, reach_s: float = 0.25) -> np.ndarray:
    """Start the loop at its calmest moment (``rotate_to_calm_point``), then slide the start by up to
    ``reach_s`` to the sample where the signal's own slope is smallest, so the wrap point is an ordinary,
    gentle step of the hum rather than one of its steepest ones (a steady hum has no 'calm' moment, and its
    seam step would otherwise be a matter of luck)."""
    y = rotate_to_calm_point(x)
    n = y.shape[-1]
    d = np.abs(np.diff(y, axis=-1, prepend=y[:, -1:]))      # d[:, s] = |y[s] - y[s-1]|
    score = (d / (np.percentile(d, 99.9, axis=-1, keepdims=True) + 1e-12)).max(axis=0)
    cand = np.arange(-n_of(reach_s), n_of(reach_s)) % n
    shift = int(cand[np.argmin(score[cand])])
    return np.roll(y, -shift, axis=-1)


def _steady_bandpass(x: np.ndarray, f: np.ndarray, q: float) -> np.ndarray:
    """Time-varying band-pass in steady state for a periodic input: filter two periods, keep the second."""
    n = x.shape[-1]
    y = tv_biquad(np.concatenate([x, x], axis=-1), "bandpass", np.concatenate([f, f]), q, block=64)
    return y[..., n:]


# ---- amb_choir -------------------------------------------------------------------------------------

def _choir_parts(rng) -> dict:
    n = n_of(LOOP)
    parts: dict[str, np.ndarray] = {}
    # 1) the transformers: a low, even hum on E (E2 B2 E3 B3 E4 B4 E5 ...: only octaves and fifths, so it agrees
    #    with every chord of the score); the 165-660 Hz partials carry it on a phone speaker
    parts["hum"] = 0.10 * _hum(n, rng, hz("E1"), {2: 0.8, 3: 0.6, 4: 1.0, 6: 0.75, 8: 0.6, 12: 0.4, 16: 0.28, 24: 0.12},
                               wander=0.15, rough=0.25)
    # 2) the weight of the hall below hearing on a phone: a very soft rumble (brown noise, 35-140 Hz)
    parts["rumble"] = 0.048 * np.vstack([noise.colored(n, rng, -6.0, 35, 140), noise.colored(n, rng, -6.0, 35, 140)]) \
        * (0.7 + 0.3 * noise.smooth_random(n, rng, 0.05))
    # 3) the Choir's brass and crystal tubes singing in sympathy with the hum: rare and faint
    res = np.zeros((2, n))
    for t0, notes, p, g in ((6.0, ("B4",), -0.35, 1.0), (19.5, ("E4", "B4"), 0.4, 0.85), (31.5, ("D5",), -0.1, 0.7),
                            (43.0, ("A4", "E5"), 0.55, 0.8), (53.5, ("G4",), -0.55, 0.6)):
        for nn in notes:
            add_circular(res, pan(_resonance(hz(nn), rng, dur=11.0, attack=1.6, t60=7.0), p), t0 + rng.uniform(0, 0.4),
                         g / len(notes) ** 0.5)
    parts["tubes"] = 0.21 * _wet(res, "choir", 0.6, 0.5)
    # 4) switch cabinets far off: two contactors pulling in
    ev = np.zeros((2, n))
    for t0, p in ((27.3, 0.7), (50.1, -0.6)):
        add_circular(ev, pan(_norm(butter(kit.relay(rng, 0.6), "lowpass", 3500, 2)), p), t0, 1.0)  # far off: no highs
    parts["cabinets"] = 0.085 * _wet(ev, "choir", 0.5, 1.0)
    return parts


@sound("amb_choir", "ambience",
       "Choir Hall: a low transformer hum on E, faint crystal-tube resonances singing in sympathy, two far "
       "contactors (no noise bed)",
       loop=True, lufs=-24.0)
def amb_choir(rng):
    out = sum(_choir_parts(rng).values())
    return _settle(_wet(out, "choir", 0.12, 1.0))


# ---- amb_gallery -----------------------------------------------------------------------------------

def _drip(rng, f0: float) -> np.ndarray:
    """A drop falling a long way, heard from the glass floor: the plink, then the echo from the Array's
    floor 30 m down (about 0.17 s there and back) and a weaker second bounce."""
    d = _norm(biquad(kit.drop(rng, f0=f0, rise=3.0, dur=0.12, tick_amt=0.15), "lowpass", 4500, 0.7))
    out = np.zeros(n_of(1.0))
    add_circular(out, d, 0.0, 1.0)
    e1 = biquad(d, "lowpass", 2600, 0.6)
    add_circular(out, e1, 0.175, 0.38)
    add_circular(out, biquad(e1, "lowpass", 1800, 0.6), 0.35, 0.14)
    return out


def _gallery_parts(rng) -> dict:
    n = n_of(LOOP)
    parts: dict[str, np.ndarray] = {}
    # 1) air moving up the shaft, singing across the glass: narrow bands (a few Hz wide) at E-family pitches
    air = np.zeros((2, n))
    for f, a, r in ((165.0, 1.0, 0.05), (247.0, 0.8, 0.07), (330.0, 0.7, 0.06), (494.0, 0.5, 0.08),
                    (659.0, 0.3, 0.09)):
        for c in range(2):
            air[c] += a * _band(n, rng, f) * _drift(n, rng, r) ** 2
    parts["air"] = 0.34 * air
    # 2) the Array a long way down: only its faintest hum
    parts["array"] = 0.045 * _hum(n, rng, hz("E1"), {2: 0.5, 3: 0.3, 4: 0.25}, wander=0.2)
    # 3) the memorial wall: 41 crystals answering the air now and then (E Dorian pitches, long and soft)
    res = np.zeros((2, n))
    for t0, nn, p, g in ((4.5, "B5", 0.5, 0.9), (13.0, "E6", -0.45, 0.55), (22.5, "F#5", -0.2, 0.8), (31.0, "A5", 0.6, 0.7),
                         (38.5, "C#6", -0.6, 0.6), (46.0, "E5", 0.2, 0.9), (54.5, "B5", -0.3, 0.7)):
        add_circular(res, pan(_resonance(hz(nn), rng, dur=12.0, attack=2.0, t60=8.0, bright=0.35), p),
                     t0 + rng.uniform(0, 0.4), g)
    parts["crystals"] = 0.24 * _wet(res, "gallery", 0.7, 0.4)
    # 4) a distant drip, twice a minute, into the deep hall
    drips = np.zeros((2, n))
    for t0, f0, p, g in ((17.4, 1250.0, -0.4, 1.0), (43.9, 980.0, 0.45, 0.8)):
        add_circular(drips, pan(_drip(rng, f0), p), t0, g)
    parts["drips"] = 0.18 * _wet(drips, "gallery", 0.55, 0.8)
    return parts


@sound("amb_gallery", "ambience",
       "Resonance Gallery: air singing across the glass floor in narrow bands, faint crystal answers from the "
       "memorial wall, a distant drip into the deep hall (no noise bed)",
       loop=True, lufs=-24.0)
def amb_gallery(rng):
    out = sum(_gallery_parts(rng).values())
    return _settle(_wet(out, "gallery", 0.10, 1.0))


# ---- amb_nursery -----------------------------------------------------------------------------------

def _steam_puff(rng, dur: float) -> np.ndarray:
    """The working autoclave sighing: a soft 'sssh' that swells in, breathes and thins out (mono)."""
    n = n_of(dur)
    x = noise.colored(n, rng, -4.5, 1100, 5200)
    x *= env.curve([(0, 0), (0.30 * dur, 1.0), (0.5 * dur, 0.75), (dur, 0)], n, "cos") \
        * (0.8 + 0.2 * noise.smooth_random(n, rng, 2.5, periodic=False))
    return x


def _nursery_parts(rng) -> dict:
    n = n_of(LOOP)
    t = time_axis(n)
    parts: dict[str, np.ndarray] = {}
    # 1) warm room tone: a soft, low hum (E, B, E, B), the chamber heaters breathing
    hum = _hum(n, rng, hz("E1"), {2: 0.7, 3: 0.4, 4: 0.5, 6: 0.22, 8: 0.1}, wander=0.2)
    parts["warmth"] = 0.10 * fft_filter(hum, lambda f: smooth_band(f, None, 1300.0, 0.5))
    # 2) growth lamps: three ballast buzzes around 100 Hz that beat slowly against each other, flickering a
    #    little, each in its own place (a thin pulse wave through a 120-1700 Hz band)
    lamps = np.zeros((2, n))
    for off, p in ((-0.0012, -0.6), (0.0, 0.0), (0.0015, 0.6)):
        f = periodic_freq(100.0 * (1.0 + off), LOOP)
        w = osc.square(f, n, 0.18)
        w = fft_filter(w, lambda fr: smooth_band(fr, 120.0, 1700.0, 0.4))
        flick = np.clip(0.82 + 0.22 * noise.smooth_random(n, rng, 0.35), 0.3, 1.0)
        lamps += pan(w * flick, p)
    for t0, d in ((21.6, 0.09), (47.3, 0.12)):  # a ballast stutter: the lamps dip for a moment
        dip = np.ones(n)
        i0, m = int(t0 * SR), n_of(d)
        dip[i0:i0 + m] = 1.0 - 0.7 * np.sin(np.pi * np.arange(m) / m) ** 2
        lamps *= dip
    parts["lamps"] = 0.036 * lamps
    # 3) the working autoclave (right of centre): steam puffs, about a fifth of the loop
    puffs = np.zeros((2, n))
    for t0, d in ((8.0, 3.4), (24.5, 2.8), (38.0, 4.0), (51.5, 3.1)):
        add_circular(puffs, pan(_steam_puff(rng, d), 0.35 + rng.uniform(-0.08, 0.08)), t0, rng.uniform(0.8, 1.0))
        add_circular(puffs, pan(_norm(butter(kit.tick(rng, 1500, 6000, 10, t60=0.05, contact=0.0003, dur=0.08), "lowpass", 5000, 2)), 0.35),
                     t0 - 0.02, 0.35)
    parts["steam"] = 0.075 * _wet(puffs, "nursery", 0.3, 1.0)
    # 4) metal cooling and ticking: little clusters of soft ticks, one per autoclave
    ticks = np.zeros((2, n))
    for t0, p in ((4.7, -0.7), (15.9, -0.25), (29.1, 0.25), (42.6, 0.7), (56.0, 0.1)):
        tt = t0
        for _ in range(int(rng.integers(3, 7))):
            add_circular(ticks, pan(_norm(butter(kit.tick(rng, 1800, 6500, 8, t60=0.05, contact=0.0002, dur=0.08), "lowpass", 6000, 2)), p), tt,
                         rng.uniform(0.35, 1.0))
            tt += rng.uniform(0.2, 0.75)
    ev = np.zeros((2, n))
    add_circular(ev, pan(_norm(butter(kit.relay(rng, 0.6), "lowpass", 4500, 2)), -0.4), 35.2, 1.0)  # the thermostat
    parts["ticks"] = 0.064 * _wet(ticks, "nursery", 0.3, 1.0) + 0.04 * _wet(ev, "nursery", 0.3, 1.0)
    return parts


@sound("amb_nursery", "ambience",
       "Nursery: a warm low hum, three growth-lamp buzzes beating slowly, soft steam puffs and cooling ticks from "
       "the autoclaves (no noise bed)",
       loop=True, lufs=-24.0)
def amb_nursery(rng):
    out = sum(_nursery_parts(rng).values())
    return _settle(_wet(out, "nursery", 0.10, 1.0))


# ---- amb_lift --------------------------------------------------------------------------------------

def _cable_creak(rng, d: float, r0: float, r1: float) -> np.ndarray:
    m = n_of(d)
    cr = kit.creak(rng, d, env.curve([(0, r0), (d * 0.6, r1), (d, r0)], m),
                   env.curve([(0, 0), (d * 0.3, 1.0), (d * 0.7, 0.6), (d, 0)], m, "cos"),
                   modal.random_modes(rng, 90, 900, 14, 0.06, 0.2, -2), jitter=0.12, hiss=0.04,
                   hiss_band=(300.0, 1200.0))
    return _norm(np.convolve(cr, np.ones(5) / 5, mode="same"))


def _lift_parts(rng) -> dict:
    n = n_of(LOOP)
    parts: dict[str, np.ndarray] = {}
    # 1) the power hum of the hoist and its transformer (E again; the 2nd partial leads)
    parts["power"] = 0.10 * _hum(n, rng, hz("E1"), {2: 1.0, 3: 0.55, 4: 0.7, 6: 0.35, 8: 0.25, 12: 0.1},
                                 wander=0.12, rough=0.3)
    # 2) shaft air: a slow breath of low rumble (45-260 Hz) and a faint, low whistle that drifts
    breath = 0.55 + 0.45 * noise.smooth_random(n, rng, 0.06)
    parts["shaft"] = 0.07 * np.vstack([noise.colored(n, rng, -5.0, 45, 260), noise.colored(n, rng, -5.0, 45, 260)]) \
        * np.clip(breath, 0.1, 1.2)
    whistle_f = 205.0 * 2 ** (0.18 * noise.smooth_random(n, rng, 0.05))
    src = np.vstack([noise.colored(n, rng, -3.0, 60, 450), noise.colored(n, rng, -3.0, 60, 450)])  # nothing above the whistle
    parts["whistle"] = 0.25 * _steady_bandpass(src, whistle_f, 10.0) * np.clip(0.4 + 0.6 * noise.smooth_random(n, rng, 0.07), 0, 1) ** 2
    # 3) the hoist cables taking up the strain: three slow creaks
    ev = np.zeros((2, n))
    for t0, d, r0, r1, p, g in ((13.5, 1.5, 18, 36, -0.25, 1.0), (31.0, 1.2, 24, 44, 0.3, 0.8), (48.5, 1.8, 16, 32, -0.1, 0.9)):
        add_circular(ev, pan(_cable_creak(rng, d, r0, r1), p), t0, g)
    parts["creaks"] = 0.13 * _wet(ev, "lift", 0.5, 1.0)
    return parts


@sound("amb_lift", "ambience",
       "Freight lift shaft: the hoist's power hum on E, slow shaft air with a faint low whistle, rare cable creaks "
       "(no noise bed)",
       loop=True, lufs=-24.0)
def amb_lift(rng):
    out = sum(_lift_parts(rng).values())
    return _settle(_wet(out, "lift", 0.12, 1.0))
