"""Seamless ambience loops. Every layer is built to be exactly periodic:
FFT-synthesised noise, control curves whose spectra are periodic, grains and
events placed with wrap-around, IIR filters run in steady state and reverb
applied circularly. The loop point therefore has no seam by construction
(and ``synth_all`` verifies it on the encoded file)."""
from __future__ import annotations

import numpy as np

from synth import env, granular, modal, noise, reverb
from synth.core import n_of, time_axis, pan, add_circular
from synth.filters import fft_filter, smooth_band, tv_biquad
from synth.loops import periodic_freq, rotate_to_calm_point

from . import kit, sound

LAB_LOOP = 60.0
HUM_LOOP = 20.0


def _steady_tv_bandpass(x, f, q):
    """Time-varying band-pass in steady state for a periodic input: filter two
    periods and keep the second."""
    n = x.shape[-1]
    y = tv_biquad(np.concatenate([x, x], axis=-1), "bandpass", np.concatenate([f, f]), q, block=64)
    return y[..., n:]


def _glass_tap(rng):
    """A raindrop hitting the window pane, heard from inside: a tiny tick
    with a short glassy ring."""
    n = n_of(0.04)
    t = time_axis(n)
    f = rng.uniform(1800, 5600)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t / rng.uniform(0.003, 0.009))
    s += 0.5 * np.sin(2 * np.pi * f * rng.uniform(1.6, 2.4) * t) * np.exp(-t / 0.002)
    s += 0.7 * rng.standard_normal(n) * np.exp(-t / 0.0006)
    return s


def _sill_drop(rng):
    """A heavier drop on the outside sill: dull, short and woody."""
    md = modal.random_modes(rng, 350, 2200, 6, 0.01, 0.035, -2.0)
    return modal.strike(md, 0.06, 0.0007, rng, noise=0.3, noise_decay=0.001)


def _gutter_drip(rng):
    return kit.drop(rng, f0=rng.uniform(700, 1500), rise=rng.uniform(1.5, 4.0), dur=0.08, tick_amt=0.15)


@sound("amb_lab_dark", "ambience",
       "Lab 7 in the dark: rain on the window, distant wind, low room tone, rare drips and creaks",
       loop=True, lufs=-24.0)
def amb_lab_dark(rng):
    L = LAB_LOOP
    n = n_of(L)
    t = time_axis(n)
    out = np.zeros((2, n))

    # Shared slow 'weather' curves (loop-periodic): rain intensity and gusts.
    weather = noise.smooth_random(n, rng, 0.05)
    gust = np.clip(noise.smooth_random(n, rng, 0.08), -0.2, 1.0)

    def w_at(tt):
        return np.interp(tt, t, weather)

    # 1) rain hiss through the glass (muffled), partly correlated L/R
    common = noise.colored(n, rng, -1.5, 400, 8000)
    wash = np.vstack([0.7 * common + 0.5 * noise.colored(n, rng, -1.5, 400, 8000),
                      0.7 * common + 0.5 * noise.colored(n, rng, -1.5, 400, 8000)])
    wash = fft_filter(wash, lambda f: 1.0 / (1.0 + (f / 4500.0) ** 2))
    out += 0.3 * wash * (0.75 + 0.25 * weather)

    # 2) individual drops on the pane (granular, wrap-around): the main texture
    taps = granular.cloud(L, lambda tt: 140.0 * (1.0 + 0.45 * w_at(tt)), _glass_tap, rng,
                          gain_db=(-36, -6), gain_skew=2.2, pan_width=0.75)
    out += 0.55 * fft_filter(taps, lambda f: smooth_band(f, 700, 4500, 0.8))

    # 3) heavier drops on the sill and gutter drips outside
    sill = granular.cloud(L, lambda tt: 7.0 * (1.0 + 0.5 * w_at(tt)), _sill_drop, rng,
                          gain_db=(-30, -8), gain_skew=1.8, pan_width=0.6)
    out += 0.5 * fft_filter(sill, lambda f: smooth_band(f, 250, 5000, 0.6))
    drips = granular.cloud(L, 0.7, _gutter_drip, rng, gain_db=(-30, -14), pan_width=0.5)
    out += 0.6 * fft_filter(drips, lambda f: smooth_band(f, None, 3500, 0.8))

    # 4) distant wind: a soft band of air plus a faint whistle at the window frame
    rumble = np.vstack([noise.colored(n, rng, -4.5, 90, 700), noise.colored(n, rng, -4.5, 90, 700)])
    out += 0.16 * rumble * (0.45 + 0.55 * gust)
    whistle_f = 520.0 * 2 ** (0.5 * noise.smooth_random(n, rng, 0.06))
    src = np.vstack([noise.colored(n, rng, -3.0), noise.colored(n, rng, -3.0)])
    whistle = _steady_tv_bandpass(src, whistle_f, 9.0)
    out += 0.1 * whistle * np.clip(gust, 0, 1) ** 2

    # 5) low room tone (kept small: phones cannot play it and it would only eat loudness)
    tone = np.vstack([noise.colored(n, rng, -6.0, 40, 160), noise.colored(n, rng, -6.0, 40, 160)])
    out += 0.07 * tone

    # 6) rare in-room events: a leak dripping onto the floor, building creaks
    room = np.zeros((2, n))
    for tt, g, p in ((7.3, 0.5, 0.55), (21.8, 0.35, 0.6), (38.4, 0.45, 0.5), (52.9, 0.3, 0.62)):
        add_circular(room, pan(kit.drop(rng, f0=rng.uniform(1100, 1500), rise=3.0, dur=0.12), p), tt, g)
    for tt, d, r0, r1, g, p in ((13.2, 0.7, 35, 70, 0.22, -0.5), (33.6, 0.9, 25, 55, 0.18, 0.3),
                                 (47.5, 0.5, 45, 90, 0.15, -0.2)):
        m = n_of(d)
        cr = kit.creak(rng, d, env.curve([(0, r0), (d * 0.6, r1), (d, r0)], m),
                       env.curve([(0, 0), (d * 0.3, 1.0), (d * 0.7, 0.6), (d, 0)], m, "cos"),
                       modal.random_modes(rng, 90, 900, 14, 0.04, 0.14, -2), jitter=0.1, hiss=0.05)
        cr = np.convolve(cr, np.ones(4) / 4, mode="same")
        add_circular(room, pan(cr, p), tt, g)
    out += reverb.reverb_circular(room, reverb.preset("room_amb", True), 0.45)

    # glue: the window sounds reflect around the room too
    out = reverb.reverb_circular(out, reverb.preset("room_amb", True), 0.12)
    return rotate_to_calm_point(out)


@sound("amb_power_hum", "ambience",
       "Restored power: subtle 50 Hz transformer hum with harmonics and faint electrical hiss",
       loop=True, lufs=-24.0)
def amb_power_hum(rng):
    L = HUM_LOOP
    n = n_of(L)
    t = time_axis(n)
    f0 = periodic_freq(50.0, L)
    # 100 Hz dominates (magnetostriction), but the 200-1000 Hz harmonics are kept
    # strong enough that the hum still reads on phone speakers.
    harmonics = {1: 0.18, 2: 1.0, 3: 0.4, 4: 0.7, 5: 0.18, 6: 0.5, 8: 0.32, 10: 0.2, 12: 0.13,
                 14: 0.08, 16: 0.06, 20: 0.03}
    out = np.zeros((2, n))
    for c in range(2):
        for k, a in harmonics.items():
            # slow, loop-periodic level wander per harmonic (rates are multiples of 1/L)
            rate = rng.integers(1, 6) / L
            wander = 1.0 + 0.12 * np.sin(2 * np.pi * rate * t + rng.uniform(0, 2 * np.pi))
            out[c] += (a * (1 + rng.uniform(-0.1, 0.1)) * wander
                       * np.sin(2 * np.pi * k * f0 * t + rng.uniform(0, 2 * np.pi)))
    # magnetostriction 'grain': a little roughness on the upper harmonics
    rough = 1.0 + 0.25 * noise.smooth_random(n, rng, 15.0)
    buzz = sum(0.04 * np.sin(2 * np.pi * k * f0 * t + rng.uniform(0, 6.3)) for k in (24, 28, 32, 36, 40))
    out += buzz * rough
    hiss = np.vstack([noise.colored(n, rng, -1.0, 2000, 9000), noise.colored(n, rng, -1.0, 2000, 9000)])
    out += 0.06 * hiss
    out += 0.08 * np.vstack([noise.colored(n, rng, -6.0, 30, 200), noise.colored(n, rng, -6.0, 30, 200)])
    return reverb.reverb_circular(out, reverb.preset("room_amb", True), 0.15)
