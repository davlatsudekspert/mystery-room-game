"""Chapter 2 expansion ("The Whole Building"), six seamless room ambiences, one per new room of
``docs/CHAPTER2_EXPANSION.md`` section 3b: ``amb_c2x_pump``, ``amb_c2x_cell``, ``amb_c2x_cold``,
``amb_c2x_gallery``, ``amb_c2x_plate``, ``amb_c2x_office``.

Rules kept from Chapter 3 (see ``underground.py``): no broadband noise floor. Every noise layer is band-limited
(nothing above about 3.5 kHz except the occasional ice tick or metal tick, which are short events), the hums
use one frequency in both channels (stable when a phone sums to mono), every layer is exactly periodic
(whole cycles per loop, FFT-built noise, events and reverb tails mixed circularly), so the loops are seamless.

The rooms differ in spectrum and rhythm as well as in content, so no two share a sound bed:
  pump     low roar (40-380 Hz) + 50 Hz mains + iron ticks + drips          dark, heavy, irregular
  cell     near silence + kettle simmer (0.5-3 kHz bubbles) + small clock   warm, small, 2 ticks per second
  cold     compressor hum + fan band + glassy ice creaks + far rumble       cold, tonal, still
  gallery  very low air + two narrow vent tones + far wood creaks           wide, slow, long reverb
  plate    100 Hz safelight buzz + drips into a tray + timer + trickle      wet, close, 2.5 ticks per second
  office   deep mantel clock (1.2 s) + wind gusts on the glass + lamp hum   dry, wooden, gusty
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from synth import env, modal, noise, osc, reverb
from synth.core import SR, add_circular, n_of, pan, time_axis
from synth.filters import biquad, butter, fft_filter, smooth_band
from synth.loops import periodic_freq

from . import kit, sound
from .underground import _band, _drift, _norm, _settle, _steady_bandpass

LOOP = 48.0


@lru_cache(maxsize=None)
def _ir(kind: str) -> np.ndarray:
    if kind == "pump":     # iron boiler room: hard, mid-long
        return reverb.synth_ir(2.0, 7411, stereo=True, predelay=0.012, lf_ratio=1.2, hf_ratio=0.35, early=12,
                               early_span=0.05, tone_hi=6500)
    if kind == "cell":     # tiny, wool and wood: almost dry
        return reverb.synth_ir(0.45, 7412, stereo=True, predelay=0.004, lf_ratio=1.0, hf_ratio=0.35, early=8,
                               early_span=0.02, tone_hi=7000)
    if kind == "cold":     # steel racks and frost: long and dark
        return reverb.synth_ir(3.8, 7413, stereo=True, predelay=0.02, lf_ratio=1.2, hf_ratio=0.3, early=14,
                               early_span=0.09, onset=0.03, tone_hi=6000)
    if kind == "gallery":  # a big quiet reading room: very long, soft
        return reverb.synth_ir(5.0, 7414, stereo=True, predelay=0.03, lf_ratio=1.1, hf_ratio=0.25, early=10,
                               early_span=0.12, onset=0.07, tone_hi=5000)
    if kind == "plate":    # tiled darkroom: short and bright-ish
        return reverb.synth_ir(0.8, 7415, stereo=True, predelay=0.006, lf_ratio=0.9, hf_ratio=0.5, early=12,
                               early_span=0.03, tone_hi=7000)
    if kind == "office":   # panelled study: short, warm
        return reverb.synth_ir(0.9, 7416, stereo=True, predelay=0.007, lf_ratio=1.0, hf_ratio=0.3, early=10,
                               early_span=0.04, tone_hi=6000)
    raise KeyError(kind)


def _wet(x, kind, wet, dry=1.0):
    return reverb.reverb_circular(x, _ir(kind), wet, dry)


def _st(n, rng, slope, lo, hi, skirt=0.5):
    """Two independent band-limited noises (a stereo bed)."""
    return np.vstack([noise.colored(n, rng, slope, lo, hi, skirt), noise.colored(n, rng, slope, lo, hi, skirt)])


def _hum(n, rng, f0, partials, wander=0.12):
    """Stereo hum with the same frequencies in both channels (mono-sum safe), loop-periodic."""
    t = time_axis(n)
    out = np.zeros((2, n))
    for k, a in partials.items():
        f = periodic_freq(f0 * k, LOOP)
        base = rng.uniform(0, 2 * np.pi)
        for c in range(2):
            lvl = 1.0 + wander * np.sin(2 * np.pi * (rng.integers(1, 4) / LOOP) * t + rng.uniform(0, 2 * np.pi))
            out[c] += a * lvl * np.sin(2 * np.pi * f * t + base + rng.uniform(-0.3, 0.3) * np.pi)
    return out


def _ev(x, lp=None):
    y = _norm(x)
    return butter(y, "lowpass", lp, 2) if lp else y


def _tick_train(n, rng, times, f_lo, f_hi, lp, p, g=1.0, vary=0.15):
    out = np.zeros((2, n))
    for i, t0 in enumerate(times):
        tk = kit.tick(rng, f_lo * (1 + vary * rng.uniform(-1, 1)), f_hi, 8, t60=0.03, contact=0.0003, dur=0.07)
        add_circular(out, pan(_ev(tk, lp), p), t0, g * (1.0 if i % 2 == 0 else 0.8))
    return out


def _flutter_env(n, rng, rate, depth):
    return np.clip(1.0 - depth + depth * (0.5 + 0.5 * noise.smooth_random(n, rng, rate)), 0.05, 1.3)


def _drop_fall(rng, f0):
    d = _ev(biquad(kit.drop(rng, f0=f0, rise=3.0, dur=0.12, tick_amt=0.15), "lowpass", 4200, 0.7))
    out = np.zeros(n_of(0.9))
    add_circular(out, d, 0.0, 1.0)
    add_circular(out, 0.3 * butter(d, "lowpass", 2500, 2), 0.11, 1.0)   # the ring after the plink
    return out


# ---- pump ------------------------------------------------------------------------------------------

@sound("amb_c2x_pump", "ambience",
       "Pump Room: boiler roar (40-380 Hz, flame flutter), 50 Hz mains hum, iron pipe expansion ticks, drips, a far "
       "pipe knock (no noise above 3.5 kHz)", loop=True, lufs=-24.0)
def amb_c2x_pump(rng):
    n = n_of(LOOP)
    roar = _st(n, rng, -6.0, 40, 380) * _flutter_env(n, rng, 0.35, 0.35)
    burner = _st(n, rng, -4.0, 180, 900) * _flutter_env(n, rng, 2.5, 0.6) * 0.60
    hum = 0.15 * _hum(n, rng, 50.0, {1: 0.35, 2: 1.0, 3: 0.4, 4: 0.3, 6: 0.14})
    ticks = np.zeros((2, n))
    for t0, k, p in ((5.0, 5, -0.5), (13.4, 3, 0.4), (22.0, 6, -0.3), (31.5, 4, 0.6), (39.0, 5, 0.0), (45.2, 3, -0.6)):
        times = t0 + np.cumsum(rng.uniform(0.15, 0.6, k))
        ticks += _tick_train(n, rng, times, 1800, 6500, 5000, p, 0.9)
    drips = np.zeros((2, n))
    for t0, f0, p in ((8.6, 1100.0, 0.5), (19.2, 820.0, -0.45), (27.3, 1400.0, 0.3), (41.7, 950.0, -0.2)):
        add_circular(drips, pan(_drop_fall(rng, f0), p), t0, 0.9)
    knock = np.zeros((2, n))
    for t0 in (16.0, 35.4):                                  # a far knock on a pipe, two raps
        k = _ev(kit.clank(rng, 150, 1600, 12, t60=0.5, contact=0.002, dur=0.6, noise_amt=0.1), 2200)
        add_circular(knock, pan(k, -0.7), t0, 1.0)
        add_circular(knock, pan(k, -0.7), t0 + 0.34, 0.6)
    mix = roar + burner + hum + 0.05 * _wet(ticks, "pump", 0.5, 1.0) + 0.13 * _wet(drips, "pump", 0.5, 0.8) \
        + 0.06 * _wet(knock, "pump", 0.6, 0.7)
    return _settle(_wet(mix, "pump", 0.10, 1.0))


# ---- cell ------------------------------------------------------------------------------------------

def _bubble(rng):
    return _ev(biquad(kit.drop(rng, f0=rng.uniform(500, 1700), rise=rng.uniform(2, 7), dur=0.05,
                               tick_amt=0.0), "lowpass", 3000, 0.7))


@sound("amb_c2x_cell", "ambience",
       "Night Cell: a quiet warm room, kettle simmer (soft bubbles, 0.5-3 kHz), a small clock ticking twice a second, "
       "a faint low pipe hum", loop=True, lufs=-24.0)
def amb_c2x_cell(rng):
    n = n_of(LOOP)
    pipe = 0.07 * _hum(n, rng, 55.0, {2: 1.0, 3: 0.45, 4: 0.3}, wander=0.25)
    # simmer: swells every 12 s (loop-periodic), made of many small resonant bubbles and a band of rushing water
    sw = np.clip(0.55 + 0.45 * np.sin(2 * np.pi * 4.0 * time_axis(n) / LOOP + 1.0) ** 2, 0, 1)
    bub = np.zeros((2, n))
    for _ in range(520):
        t0 = rng.uniform(0, LOOP)
        if rng.uniform() < sw[int(t0 * SR) % n] ** 2:
            add_circular(bub, pan(_bubble(rng), rng.uniform(0.15, 0.7)), t0, rng.uniform(0.2, 1.0))
    water = _st(n, rng, -4.0, 500, 2400, 0.4) * _flutter_env(n, rng, 3.0, 0.5) * sw ** 2
    kettle = 0.20 * bub + 0.12 * water
    ticks = np.zeros((2, n))                                 # a small clock: tick-tock, two per second
    for i in range(int(LOOP * 2)):
        hi = i % 2 == 0
        tk = kit.knock(rng, 900 if hi else 700, 4200, 8, t60=0.018, contact=0.0002, dur=0.05, noise_amt=0.4)
        add_circular(ticks, pan(_ev(tk, 5000), -0.35), i * 0.5 + 0.2, 1.0 if hi else 0.8)
    metal = np.zeros((2, n))                                 # the kettle lid ticking as it warms
    for t0 in (9.3, 21.7, 33.1, 44.6):
        add_circular(metal, pan(_ev(kit.tick(rng, 2200, 6500, 8, t60=0.05, contact=0.0003, dur=0.1), 5500), 0.55), t0, 1.0)
    mix = pipe + kettle + 0.09 * _wet(ticks, "cell", 0.25, 1.0) + 0.05 * _wet(metal, "cell", 0.25, 1.0)
    return _settle(_wet(mix, "cell", 0.08, 1.0))


# ---- cold ------------------------------------------------------------------------------------------

def _ice_creak(rng, d, r0, r1):
    m = n_of(d)
    body = modal.glass(rng.uniform(1100, 1700), 0.25, 0.55) + modal.random_modes(rng, 300, 1200, 8, 0.04, 0.12, -2)
    cr = kit.creak(rng, d, env.curve([(0, r0), (d * 0.5, r1), (d, r0)], m),
                   env.curve([(0, 0), (d * 0.3, 1.0), (d * 0.75, 0.5), (d, 0)], m, "cos"), body, jitter=0.1,
                   hiss=0.03, hiss_band=(900.0, 2800.0))
    return _ev(butter(cr, "lowpass", 4500, 2))


@sound("amb_c2x_cold", "ambience",
       "Cold Store: refrigeration compressor hum (50 Hz series), a slow fan band, glassy ice creaks, a far carriage rumble",
       loop=True, lufs=-24.0)
def amb_c2x_cold(rng):
    n = n_of(LOOP)
    comp = 0.13 * _hum(n, rng, 50.0, {1: 0.25, 2: 1.0, 3: 0.55, 4: 0.5, 5: 0.2, 6: 0.3, 8: 0.14, 12: 0.06}, wander=0.1)
    blade = 1.0 + 0.25 * np.sin(2 * np.pi * periodic_freq(17.0, LOOP) * time_axis(n))
    fan = 0.20 * _st(n, rng, -3.0, 110, 520) * blade * _drift(n, rng, 0.07, 0.3)
    ice = np.zeros((2, n))
    for t0, d, r0, r1, p, g in ((6.5, 1.3, 40, 90, -0.5, 1.0), (17.0, 0.9, 55, 110, 0.5, 0.7), (26.8, 1.6, 35, 80, -0.2, 0.9),
                                (36.0, 1.0, 50, 100, 0.6, 0.7), (43.5, 1.4, 38, 85, 0.1, 0.8)):
        add_circular(ice, pan(_ice_creak(rng, d, r0, r1), p), t0, g)
    ticks = np.zeros((2, n))
    for t0, p in ((11.2, 0.3), (23.4, -0.6), (31.0, 0.7), (40.3, -0.2)):   # frost cracking: single glassy ticks
        tk = kit.tick(rng, 2500, 7500, 10, t60=0.04, contact=0.0002, dur=0.1)
        add_circular(ticks, pan(_ev(tk, 5500), p), t0, 1.0)
    rumble = np.zeros((2, n))                                # a carriage rolling far away: two slow rumbles
    for t0, d in ((13.0, 5.5), (37.5, 6.5)):
        m = n_of(d)
        r = _st(m, rng, -6.0, 30, 130) * env.swell(m, 0.4 * d, 0.5 * d)
        add_circular(rumble, r, t0, 1.0)
    mix = comp + fan + 0.20 * _wet(ice, "cold", 0.5, 1.0) + 0.05 * _wet(ticks, "cold", 0.5, 1.0) + 0.12 * rumble
    return _settle(_wet(mix, "cold", 0.10, 1.0))


# ---- gallery ---------------------------------------------------------------------------------------

@sound("amb_c2x_gallery", "ambience",
       "Reading Gallery: a big quiet space, very low air, distant ventilation with two narrow drifting tones, far wood "
       "creaks and a few dust ticks, long reverb", loop=True, lufs=-24.0)
def amb_c2x_gallery(rng):
    n = n_of(LOOP)
    air = 0.13 * _st(n, rng, -6.0, 30, 190) * _flutter_env(n, rng, 0.08, 0.4)
    blade = 1.0 + 0.15 * np.sin(2 * np.pi * periodic_freq(11.0, LOOP) * time_axis(n))
    vent = 0.22 * _st(n, rng, -3.0, 90, 420) * blade * _flutter_env(n, rng, 0.05, 0.4)
    tones = np.zeros((2, n))
    for f, a, r in ((332.0, 1.0, 0.04), (498.0, 0.6, 0.05)):
        for c in range(2):
            tones[c] += a * _band(n, rng, f, 0.01) * _drift(n, rng, r, 0.6) ** 2
    creaks = np.zeros((2, n))
    for t0, d, p in ((10.5, 1.4, -0.5), (33.0, 1.8, 0.6)):
        m = n_of(d)
        cr = kit.creak(rng, d, env.curve([(0, 22), (d * 0.5, 38), (d, 20)], m),
                       env.curve([(0, 0), (d * 0.35, 1.0), (d, 0)], m, "cos"), modal.wood(rng, 120, 900, 10, 0.2),
                       jitter=0.15, hiss=0.02, hiss_band=(200, 900))
        add_circular(creaks, pan(_ev(butter(cr, "lowpass", 1400, 2)), p), t0, 1.0)
    dust = np.zeros((2, n))
    for t0, p in ((4.0, 0.4), (18.7, -0.5), (27.9, 0.2), (45.1, -0.3)):
        add_circular(dust, pan(_ev(kit.tick(rng, 1500, 4800, 8, t60=0.04, contact=0.0004, dur=0.1), 4000), p), t0, 1.0)
    mix = air + vent + 0.45 * tones + 0.17 * _wet(creaks, "gallery", 0.7, 0.6) + 0.04 * _wet(dust, "gallery", 0.7, 0.7)
    return _settle(_wet(mix, "gallery", 0.12, 1.0))


# ---- plate -----------------------------------------------------------------------------------------

@sound("amb_c2x_plate", "ambience",
       "Plate Room (darkroom): a 100 Hz safelight buzz, water dripping into a tray, an enlarger timer ticking 2.5 times "
       "a second, a faint tap trickle", loop=True, lufs=-24.0)
def amb_c2x_plate(rng):
    n = n_of(LOOP)
    f = periodic_freq(100.0, LOOP)
    w = osc.square(f, n, 0.15)
    w = fft_filter(w, lambda fr: smooth_band(fr, 110.0, 1500.0, 0.4))
    buzz_env = np.clip(0.85 + 0.15 * noise.smooth_random(n, rng, 0.4), 0.5, 1.0)
    for t0, d in ((14.2, 0.07), (38.8, 0.1)):                # the safelight flickers once or twice
        i0, m = int(t0 * SR), n_of(d)
        buzz_env[i0:i0 + m] *= 1.0 - 0.6 * np.sin(np.pi * np.arange(m) / m) ** 2
    buzz = 0.045 * np.vstack([w, w]) * buzz_env
    hum = 0.05 * _hum(n, rng, 50.0, {2: 1.0, 4: 0.4}, wander=0.2)
    drips = np.zeros((2, n))
    t0 = 1.3
    while t0 < LOOP - 1.0:
        f0 = rng.uniform(650, 1350)
        d = _drop_fall(rng, f0)
        add_circular(drips, pan(d, 0.4), t0, rng.uniform(0.6, 1.0))
        add_circular(drips, pan(0.35 * butter(d, "lowpass", 1800, 2), 0.4), t0 + 0.2, 0.7)   # a ripple in the tray
        t0 += rng.uniform(2.4, 4.4)
    timer = np.zeros((2, n))
    for i in range(int(LOOP * 2.5)):
        hi = i % 2 == 0
        tk = kit.tick(rng, 2400 if hi else 1900, 7000, 10, t60=0.022, contact=0.0002, dur=0.06, noise_amt=0.5)
        add_circular(timer, pan(_ev(tk, 5500), -0.5), i * 0.4 + 0.13, 1.0 if hi else 0.75)
    trickle = _st(n, rng, -3.0, 500, 2200, 0.4) * _flutter_env(n, rng, 7.0, 0.65) * 0.045
    mix = buzz + hum + 0.16 * _wet(drips, "plate", 0.4, 1.0) + 0.05 * _wet(timer, "plate", 0.3, 1.0) + trickle
    return _settle(_wet(mix, "plate", 0.08, 1.0))


# ---- office ----------------------------------------------------------------------------------------

@sound("amb_c2x_office", "ambience",
       "Director's Office: a deep mantel clock (tock every 0.6 s), wind gusting at the window glass, a green desk-lamp "
       "hum and a floorboard", loop=True, lufs=-24.0)
def amb_c2x_office(rng):
    n = n_of(LOOP)
    ticks = np.zeros((2, n))
    for i in range(int(LOOP / 0.6)):
        hi = i % 2 == 0
        tk = kit.knock(rng, 520 if hi else 400, 2600, 9, t60=0.05, contact=0.0006, dur=0.12, noise_amt=0.3)
        add_circular(ticks, pan(_ev(tk, 3500), 0.3), i * 0.6 + 0.15, 1.0 if hi else 0.85)
    gust = np.clip(0.5 + 0.5 * noise.smooth_random(n, rng, 0.12), 0, 1) ** 2.5
    src = _st(n, rng, -3.0, 80, 1400)
    fc = 420.0 * 2 ** (0.5 * noise.smooth_random(n, rng, 0.08))
    wind = 0.5 * _steady_bandpass(src, fc, 3.5) * gust + 0.12 * _st(n, rng, -5.0, 40, 160) * gust
    glass = np.zeros((2, n))                                 # the pane ticking in the frame in the strongest gust
    gi = int(np.argmax(gust))
    for k in range(3):
        add_circular(glass, pan(_ev(kit.tick(rng, 1200, 4500, 8, t60=0.05, contact=0.0004, dur=0.1), 3500), 0.7),
                     gi / SR + k * 0.45, 1.0)
    lamp = 0.045 * _hum(n, rng, 50.0, {2: 1.0, 4: 0.4, 6: 0.15}, wander=0.2)
    board = np.zeros((2, n))
    d = 1.1
    m = n_of(d)
    cr = kit.creak(rng, d, env.curve([(0, 26), (d * 0.5, 44), (d, 24)], m), env.curve([(0, 0), (d * 0.4, 1), (d, 0)], m, "cos"),
                   modal.wood(rng, 100, 700, 10, 0.18), jitter=0.15, hiss=0.02, hiss_band=(200, 800))
    add_circular(board, pan(_ev(butter(cr, "lowpass", 1200, 2)), -0.4), 29.4, 1.0)
    mix = 0.09 * _wet(ticks, "office", 0.25, 1.0) + 0.50 * wind + 0.09 * glass + lamp + 0.12 * _wet(board, "office", 0.3, 1.0)
    return _settle(_wet(mix, "office", 0.08, 1.0))
