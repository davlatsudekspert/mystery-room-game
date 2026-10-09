"""Chapter 2, Records Archive B: the fire shutter, the compressor and the
pneumatic post, the card catalogue and the card punch, steel lockers and
hiding places, Leyla's pocket receiver, the reel-to-reel tape deck, the
booth's rotary dial, the film and slide projectors, the crystals, the vault,
and the archive's room tone.

Mains is 50 Hz here too. The voice on Leyla's tapes is a *murmur*: a glottal
pulse train through three moving formants with random vowel targets, so it has
the rhythm and melody of speech but never says a word in any language (the
captions carry the text)."""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from synth import env, granular, modal, music, noise, osc, reverb
from synth.core import SR, n_of, add_at, add_circular, mix, pan, soft_clip, time_axis
from synth.filters import biquad, butter, fft_filter, one_pole_lp, smooth_band, tv_biquad
from synth.loops import periodic_freq, rotate_to_calm_point
from synth.music import hz

from . import kit, sound

ARCHIVE_LOOP = 60.0
STATIC_LOOP = 6.0


def _norm(x):
    return x / max(np.max(np.abs(x)), 1e-12)


@lru_cache(maxsize=None)
def _ir(kind: str, stereo: bool = False) -> np.ndarray:
    """Chapter 2 spaces (synthesised IRs, cached)."""
    s = 101 if stereo else 0
    if kind == "archive":  # big paper archive: plaster, concrete columns, shelves of paper
        return reverb.synth_ir(0.85, 7201 + s, stereo=stereo, predelay=0.011, lf_ratio=1.2, hf_ratio=0.35,
                               early=14, early_span=0.07, tone_hi=8000)
    if kind == "vault":  # steel and concrete vault opening onto the archive
        return reverb.synth_ir(1.6, 7202 + s, stereo=stereo, predelay=0.02, lf_ratio=1.35, hf_ratio=0.45,
                               early=16, early_span=0.09, tone_hi=8500)
    if kind == "booth":  # small panelled projection booth
        return reverb.synth_ir(0.4, 7203 + s, stereo=stereo, predelay=0.004, lf_ratio=1.1, hf_ratio=0.4,
                               early=10, early_span=0.025, tone_hi=9000)
    if kind == "amb":  # the archive as heard in the ambience bed
        return reverb.synth_ir(1.1, 7204 + s, stereo=stereo, predelay=0.012, hf_ratio=0.3, early=12,
                               early_span=0.06, tone_hi=7000)
    raise KeyError(kind)


def _room(x, wet=0.12, kind="archive"):
    return reverb.reverb(x, _ir(kind), wet)


def _events_from_rate(rate: np.ndarray, phase0: float = 0.0) -> np.ndarray:
    """Times (s) at which a phase running at ``rate`` (Hz, per sample) crosses
    a whole cycle: the strokes of a crank, claw or governor that speeds up or
    slows down."""
    ph = phase0 + np.cumsum(rate) / SR
    k = np.nonzero(np.diff(np.floor(ph)) > 0)[0] + 1
    return k / SR


def _wow(x, rng, depth=0.0010, rate=0.55, flutter=0.00005, f_rate=7.3):
    """Tape wow and flutter as a slowly varying delay (one-shots only)."""
    n = len(x)
    t = time_axis(n)
    d = (depth * (1.0 + np.sin(2 * np.pi * rate * t + rng.uniform(0, 6.3)))
         + flutter * np.sin(2 * np.pi * f_rate * t + rng.uniform(0, 6.3))
         + 0.25 * depth * (1.0 + noise.smooth_random(n, rng, 1.5, periodic=False)))
    idx = np.arange(n) - d * SR
    return np.interp(idx, np.arange(n), x, left=0.0, right=0.0)


def _deck_speaker(x, lo=300.0, hi=3000.0, drive=1.0):
    """The tape deck's small built-in speaker: band-limited, a cone
    resonance near 1.3 kHz and a little cone/amp saturation."""
    y = butter(x, "bandpass", (lo, hi), 2)
    y = biquad(y, "peak", 1300.0, 1.1, 4.0)
    return soft_clip(0.9 * _norm(y), drive)


def _tilt_pan(x, curve):
    """Mono -> stereo with a time-varying equal-power pan position."""
    ang = (np.clip(curve, -1, 1) + 1.0) * np.pi / 4.0
    return np.vstack([np.cos(ang) * x, np.sin(ang) * x])


# ------------------------------------------------------------------------------------------
# Voice murmur (tape diary)
# ------------------------------------------------------------------------------------------
_VOWELS = np.array([  # F1, F2, F3 (Hz), a woman's voice
    (820.0, 1500.0, 2800.0),
    (560.0, 2050.0, 2900.0),
    (360.0, 2550.0, 3150.0),
    (520.0, 960.0, 2650.0),
    (400.0, 900.0, 2550.0),
    (620.0, 1650.0, 2750.0),
    (690.0, 1800.0, 2700.0),
])


def _murmur(rng, dur: float, phrases, f0: float = 210.0) -> np.ndarray:
    """Speech-like murmur: syllables with phrase intonation and soft consonant
    noise, through three moving formants with *random* vowel targets.
    ``phrases`` is ``[(start_s, end_s), ...]``."""
    n = n_of(dur)
    t = time_axis(n)
    amp = np.zeros(n)
    cons = np.zeros(n)
    centres, vowels = [], []
    pitch_t, pitch_v = [0.0], [f0]
    accents = np.zeros(n)
    for p0, p1 in phrases:
        sylls = []
        s = p0
        while s < p1 - 0.1:
            d = min(rng.uniform(0.12, 0.25), p1 - s)
            sylls.append((s, d))
            s += d + (rng.uniform(0.04, 0.1) if rng.uniform() < 0.25 else 0.0)  # word gaps
        for i, (s0, d) in enumerate(sylls):
            if i == len(sylls) - 1:
                d *= 1.4  # phrase-final lengthening
            m = n_of(d)
            e = np.sin(np.pi * (np.arange(m) + 0.5) / m) * rng.uniform(0.45, 1.0)
            add_at(amp, e, s0)
            centres.append(s0 + 0.5 * d)
            vowels.append(int(rng.integers(0, len(_VOWELS))))
            c = rng.uniform()
            if c < 0.3:  # fricative
                ln = rng.uniform(0.04, 0.085)
                fn = n_of(ln)
                band = (2600.0, 6500.0) if rng.uniform() < 0.5 else (1700.0, 3900.0)
                f = butter(noise.white(fn, rng), "bandpass", band, 2) * np.sin(np.pi * (np.arange(fn) + 0.5) / fn)
                add_at(cons, f, max(0.0, s0 - 0.6 * ln), rng.uniform(0.25, 0.5))
            elif c < 0.55:  # plosive burst
                bn = n_of(0.02)
                b = butter(noise.white(bn, rng), "bandpass", (900.0, 4500.0), 2) * np.exp(-np.arange(bn) / (SR * 0.004))
                add_at(cons, b, s0, rng.uniform(0.4, 0.8))
            if rng.uniform() < 0.22:  # stressed syllable: a pitch accent
                add_at(accents, np.sin(np.pi * (np.arange(n_of(d * 1.6)) + 0.5) / n_of(d * 1.6)) ** 2,
                       s0 - 0.2 * d, rng.uniform(0.08, 0.16))
        # declination over the phrase, small reset at the next one
        pitch_t += [p0, p1]
        pitch_v += [f0 * rng.uniform(1.04, 1.12), f0 * rng.uniform(0.82, 0.9)]
    pitch_t.append(dur)
    pitch_v.append(pitch_v[-1])
    order = np.argsort(pitch_t, kind="stable")
    base = np.interp(t, np.array(pitch_t)[order], np.array(pitch_v)[order])
    f0_curve = base * (1.0 + accents) * (1.0 + 0.012 * noise.smooth_random(n, rng, 6.0, periodic=False))

    vt = _VOWELS[np.array(vowels)] * rng.uniform(0.93, 1.07, (len(vowels), 3))
    cs = np.array(centres)
    F = [np.interp(t, cs, vt[:, k]) for k in range(3)]
    glottal = one_pole_lp(osc.saw(f0_curve, n), 900.0)
    breath = butter(noise.white(n, rng), "highpass", 1200, 2) * 0.18
    exc = (_norm(glottal) + breath) * amp
    voiced = (tv_biquad(exc, "bandpass", F[0], F[0] / 90.0)
              + 1.6 * tv_biquad(exc, "bandpass", F[1], F[1] / 120.0)
              + 1.1 * tv_biquad(exc, "bandpass", F[2], F[2] / 170.0))
    return _norm(voiced) + 0.22 * cons


def _tape_hiss(n, rng):
    """Tape hiss with a faint flutter in its level (one-shots)."""
    h = noise.colored(n, rng, -1.0, 700, 10000)
    return h * (1.0 + 0.08 * np.sin(2 * np.pi * 7.3 * np.arange(n) / SR))


# ------------------------------------------------------------------------------------------
# Entrance and emergency power
# ------------------------------------------------------------------------------------------
@sound("shutter_slam", "sfx",
       "Corrugated steel fire shutter crashes down; slats rattle; emergency relays click on aisle by aisle")
def shutter_slam(rng):
    out = np.zeros(n_of(2.7))
    # the last few slats clattering in the guide rails just before the hit
    for k, tt in enumerate((0.0, 0.012, 0.022, 0.03)):
        add_at(out, kit.tick(rng, 900, 6000, 10, t60=0.03, contact=0.0003, dur=0.05), tt, 0.15 + 0.1 * k)
    t = 0.035
    add_at(out, kit.clank(rng, 90, 4200, 30, t60=0.55, contact=0.0016, dur=1.0, noise_amt=0.5), t, 1.0)
    add_at(out, kit.thump(85, 36, 0.8, t60=0.5, glide=0.05, harm=0.45), t, 0.7)
    cn = n_of(0.6)
    burst = noise.white(cn, rng) * env.ar(cn, 0.001, 0.35)
    crash = modal.resonate(burst, modal.random_modes(rng, 400, 7000, 40, 0.08, 0.4, -1.5))
    add_at(out, _norm(butter(crash, "highpass", 300, 2)), t, 0.55)  # corrugated sheet crash
    # corrugated sheet: low, slowly beating panel modes
    md = modal.random_modes(rng, 110, 900, 14, 0.25, 0.7, -2.0)
    md = md + modal.Modes(md.freqs * 1.012, md.t60s, md.amps * 0.6)
    add_at(out, _norm(modal.strike(md, 1.2, 0.002, rng)), t, 0.4)
    # bounce, then the slats settle in the rails
    add_at(out, kit.clank(rng, 160, 3800, 20, t60=0.25, contact=0.0012, dur=0.4), t + 0.085, 0.5)
    add_at(out, kit.thump(110, 60, 0.25, t60=0.15, glide=0.03), t + 0.085, 0.4)
    tt = t + 0.13
    gap = 0.03
    for k in range(14):
        add_at(out, kit.tick(rng, 700, 5500, 10, t60=0.04, contact=0.0004, dur=0.07), tt,
               0.32 * np.exp(-k / 5.0) * rng.uniform(0.6, 1.0))
        tt += gap * rng.uniform(0.7, 1.4)
        gap *= 1.12
    # emergency relays wake up and the lamps strike, aisle by aisle
    for k in range(6):
        add_at(out, kit.relay(rng, 0.5), 0.3 + 0.12 * k + rng.uniform(-0.01, 0.01), 0.16 * (1.0 - 0.1 * k))
    return _big_room(out, 0.24)


def _big_room(x, wet):
    """Big events: the archive rings and the stacks and vault answer a little later."""
    return mix(reverb.reverb(x, _ir("archive"), wet), reverb.reverb(x, _ir("vault"), 0.35 * wet, dry=0.0))


@sound("relay_click", "sfx", "Old emergency relays pulling in: two quick clicks and a faint contactor buzz")
def relay_click(rng):
    out = np.zeros(n_of(0.4))
    add_at(out, kit.relay(rng, 0.9), 0.0, 1.0)
    add_at(out, kit.relay(rng, 0.6), 0.075, 0.6)
    d = 0.16
    bz = kit.buzz(d, 100.0, rng, bright=3000, rough=0.3) * env.swell(n_of(d), 0.01, 0.08)
    add_at(out, _norm(bz), 0.01, 0.06)
    return _room(out, 0.12)


# ------------------------------------------------------------------------------------------
# Compressor and pneumatic post
# ------------------------------------------------------------------------------------------
def _stroke(rng, weight=1.0):
    """One compressor piston stroke: a low knock, the valve plate tick and a
    short puff of air."""
    out = np.zeros(n_of(0.12))
    add_at(out, kit.knock(rng, 140, 1300, 8, t60=0.05, contact=0.0016, dur=0.1, noise_amt=0.2), 0.0, 0.8 * weight)
    add_at(out, kit.tick(rng, 1500, 6000, 8, t60=0.015, contact=0.0002, dur=0.03), 0.008, 0.25 * weight)
    pn = n_of(0.06)
    puff = butter(noise.white(pn, rng), "bandpass", (700, 3500), 2) * np.sin(np.pi * (np.arange(pn) + 0.5) / pn) ** 2
    add_at(out, _norm(puff), 0.02, 0.18)
    return out


@sound("compressor_start", "sfx",
       "Archive compressor starts: contactor clack, belt squeal, motor and piston chug spin up, air wheezes")
def compressor_start(rng):
    total = 3.6
    out = np.zeros(n_of(total))
    add_at(out, kit.relay(rng, 1.0), 0.0, 0.45)
    add_at(out, kit.clank(rng, 300, 3000, 14, t60=0.08, contact=0.0008, dur=0.15), 0.004, 0.25)
    d = total - 0.05
    n = n_of(d)
    tt = time_axis(n)
    spin = 1.0 - np.exp(-tt / 0.7)                       # motor speed 0..1
    level = env.curve([(0, 1), (2.6, 1), (d, 0)], n, "cos")
    # motor: 50 Hz hum and a rotor whine rising with speed
    h = kit.hum(d, 50.0, {2: 1.0, 4: 0.4, 6: 0.25}, rng) * np.clip(spin * 1.5, 0, 1)
    whine = osc.additive(60.0 + 520.0 * spin, n, [(1, 1.0), (2, 0.3), (3, 0.1)]) * spin ** 2
    add_at(out, (0.14 * h + 0.04 * whine) * level, 0.03)
    # belt squeal as the pulley catches
    sq = kit.creak(rng, 0.45, env.curve([(0, 1300), (0.2, 1900), (0.45, 2200)], n_of(0.45)),
                   env.curve([(0, 0), (0.05, 1), (0.3, 0.5), (0.45, 0)], n_of(0.45), "cos"),
                   modal.metal(rng, 1800, 6500, 10, 0.03), jitter=0.01, hiss=0.1)
    add_at(out, sq, 0.06, 0.14)
    # pistons: the crank runs up to 11 strokes per second
    rate = 11.0 * spin ** 1.3
    for k, st in enumerate(_events_from_rate(rate, 0.3)):
        g = (0.55 + 0.45 * min(1.0, k / 6.0)) * rng.uniform(0.8, 1.0) * np.interp(st, tt, level)
        add_at(out, _stroke(rng, 1.0), 0.03 + st, 0.55 * g)
    # air: intake/outlet hiss breathing with the strokes, plus a wheezing reed-like whistle
    ph = np.cumsum(rate) / SR
    breath = 0.5 + 0.5 * np.cos(2 * np.pi * ph)
    air = butter(noise.white(n, rng), "bandpass", (900, 5500), 2) * (0.3 + 0.7 * breath) * spin * level
    add_at(out, _norm(air), 0.03, 0.12)
    wz_f = 820.0 * (1.0 + 0.04 * np.cos(2 * np.pi * ph))
    wheeze = tv_biquad(noise.white(n, rng), "bandpass", wz_f, 18.0) * breath ** 2 * np.clip((tt - 0.6) / 0.8, 0, 1)
    add_at(out, _norm(wheeze) * level, 0.03, 0.08)
    return _room(out, 0.12)


@sound("compressor_loop", "sfx", "Compressor running steadily: piston chug, motor hum, breathing air (seamless loop)",
       loop=True)
def compressor_loop(rng):
    L = 4.0
    n = n_of(L)
    t = time_axis(n)
    out = np.zeros(n)
    fc = periodic_freq(11.0, L)
    for k in range(int(round(fc * L))):
        add_circular(out, _stroke(rng, rng.uniform(0.85, 1.0)), k / fc + rng.uniform(-0.002, 0.002), 0.55)
    f0 = periodic_freq(50.0, L)
    for kk, a in ((2, 1.0), (4, 0.4), (6, 0.25)):
        out += 0.14 * a / 1.65 * np.sin(2 * np.pi * kk * f0 * t + rng.uniform(0, 6.3))
    fw = periodic_freq(580.0, L)
    out += 0.03 * (np.sin(2 * np.pi * fw * t) + 0.3 * np.sin(2 * np.pi * 2 * fw * t))
    breath = 0.5 + 0.5 * np.cos(2 * np.pi * fc * t)
    air = fft_filter(noise.white(n, rng), lambda f: smooth_band(f, 900, 5500, 0.5))
    out += 0.12 * _norm(air) * (0.3 + 0.7 * breath)
    return reverb.reverb_circular(out, _ir("archive"), 0.1)


@sound("valve_squeak", "sfx", "Brass valve wheel turned a notch: short metal squeak and a breath of air")
def valve_squeak(rng):
    out = np.zeros(n_of(0.6))
    d = 0.34
    n = n_of(d)
    rate = env.curve([(0, 420), (0.12, 620), (0.25, 560), (d, 480)], n, "cos")
    amp = env.curve([(0, 0), (0.04, 0.9), (0.15, 1.0), (0.25, 0.5), (d, 0)], n, "cos")
    add_at(out, kit.creak(rng, d, rate, amp, modal.metal(rng, 1100, 5200, 12, 0.05), jitter=0.015, hiss=0.08), 0.0, 0.8)
    fr = kit.friction(rng, d, amp, 600, 4000, body=modal.metal(rng, 700, 3000, 8, 0.05), grit=0.3, grit_rate=900)
    add_at(out, _norm(fr), 0.0, 0.18)
    add_at(out, kit.tick(rng, 1500, 6500, 10, t60=0.03, contact=0.0002, dur=0.05), d - 0.02, 0.35)
    hn = n_of(0.25)
    hs = butter(noise.white(hn, rng), "bandpass", (1500, 6000), 2) * env.swell(hn, 0.05, 0.15)
    add_at(out, _norm(hs), d - 0.04, 0.08)
    return _room(out, 0.1)


@sound("tube_whoosh", "sfx",
       "Pneumatic post: the canister is sucked into the glass tube and rushes away through the ceiling run")
def tube_whoosh(rng):
    total = 2.0
    out = np.zeros(n_of(total))
    # intake pop and the canister knocking into the tube mouth
    pn = n_of(0.08)
    pop = butter(noise.white(pn, rng), "lowpass", 900, 2) * env.ar(pn, 0.002, 0.05)
    add_at(out, _norm(pop), 0.0, 0.5)
    add_at(out, kit.knock(rng, 200, 1800, 8, t60=0.05, contact=0.0012, dur=0.1), 0.01, 0.45)
    add_at(out, kit.thump(150, 80, 0.12, t60=0.08, glide=0.02), 0.01, 0.35)
    d = 1.85
    n = n_of(d)
    tt = time_axis(n)
    level = env.curve([(0, 0), (0.08, 1.0), (0.35, 0.85), (1.0, 0.35), (d, 0)], n, "cos")
    # air rush: band-pass sweeping down as it travels away (doppler) and closing (distance)
    rush = kit.whoosh(rng, d, 3600, 600, q=1.8, attack=0.04, release=0.5)
    add_at(out, _norm(rush) * level, 0.03, 0.6)
    # the tube's own resonances, gliding down a little
    src = noise.colored(n, rng, -2.0)
    tube = np.zeros(n)
    f_tube = 340.0 * (1.0 - 0.18 * (1 - np.exp(-tt / 0.6)))
    for k, a in ((1, 1.0), (2, 0.6), (3, 0.35), (4, 0.18)):
        tube += a * tv_biquad(src, "bandpass", f_tube * k, 14.0 + 4 * k, block=64)
    add_at(out, _norm(tube) * level ** 1.3, 0.03, 0.45)
    # the canister rattling along the glass, receding
    tr_t = 0.12
    while tr_t < 1.5:
        g = 0.22 * np.exp(-tr_t / 0.5) * rng.uniform(0.5, 1.0)
        add_at(out, kit.tick(rng, 1200, 5500, 8, t60=0.025, contact=0.0003, dur=0.04), tr_t, g)
        tr_t += rng.uniform(0.05, 0.13)
    out = out * env.curve([(0, 1), (1.5, 1), (total, 0)], len(out), "cos")
    return _room(out, 0.16)


@sound("canister_thump", "sfx", "Leather-banded brass canister drops into the receive tray: padded thump and rattle")
def canister_thump(rng):
    out = np.zeros(n_of(0.7))
    pn = n_of(0.05)
    puff = butter(noise.white(pn, rng), "bandpass", (200, 1500), 2) * env.ar(pn, 0.004, 0.03)
    add_at(out, _norm(puff), 0.0, 0.3)
    t = 0.03
    add_at(out, kit.knock(rng, 150, 1500, 12, t60=0.1, contact=0.002, dur=0.3, noise_amt=0.2), t, 1.0)
    add_at(out, kit.thump(140, 80, 0.3, t60=0.15, glide=0.03), t, 0.4)
    add_at(out, kit.clank(rng, 500, 5000, 14, t60=0.12, contact=0.0006, dur=0.2), t + 0.004, 0.45)
    add_at(out, _norm(modal.strike(modal.random_modes(rng, 300, 1600, 8, 0.05, 0.12, -1.0), 0.25, 0.0012, rng)),
           t, 0.45)  # hollow canister body
    for dt, g in ((0.06, 0.3), (0.1, 0.18), (0.15, 0.1)):  # settles and rocks in the tray
        add_at(out, kit.knock(rng, 300, 2500, 6, t60=0.03, contact=0.001, dur=0.06), t + dt, g)
        add_at(out, kit.tick(rng, 1500, 6000, 6, t60=0.025, contact=0.0003, dur=0.04), t + dt + 0.003, 0.5 * g)
    return _room(out, 0.12)


# ------------------------------------------------------------------------------------------
# Card catalogue and card punch
# ------------------------------------------------------------------------------------------
def _paper(rng, dur, move, rate=900.0):
    """Paper on paper: crinkle impulses through small paper resonances."""
    n = n_of(dur)
    d = noise.dust(n, rate * move, rng, heavy_tail=0.7)
    md = modal.random_modes(rng, 1600, 9000, 12, 0.002, 0.006, -1.0)
    x = butter(d, "highpass", 1400, 2) * 0.4 + modal.resonate(d, md) * 0.05
    air = butter(noise.white(n, rng), "bandpass", (1500, 7000), 2) * move
    return _norm(x) + 0.25 * _norm(air)


@sound("drawer_card_slide", "sfx",
       "Long oak catalogue drawer slides out on its runners, cards whisper inside, the stop catches")
def drawer_card_slide(rng):
    out = np.zeros(n_of(1.05))
    add_at(out, kit.tick(rng, 1400, 6000, 8, t60=0.03, contact=0.0003, dur=0.06), 0.0, 0.35)  # brass pull
    d = 0.72
    n = n_of(d)
    speed = env.curve([(0, 0), (0.05, 0.6), (0.15, 1.0), (0.45, 0.85), (0.62, 0.4), (d, 0)], n, "cos")
    slide = kit.friction(rng, d, speed, 200, 2600, body=modal.wood(rng, 140, 1100, 12, 0.07),
                         grit=0.35, grit_rate=500, rough_rate=20)
    add_at(out, _norm(slide), 0.02, 0.75)
    rumble = butter(noise.white(n, rng), "bandpass", (100, 420), 2) * speed
    add_at(out, _norm(rumble), 0.02, 0.3)
    add_at(out, _paper(rng, d, speed ** 1.5, 700.0), 0.04, 0.16)
    add_at(out, kit.knock(rng, 140, 1400, 12, t60=0.07, contact=0.0016, dur=0.2), 0.74, 0.8)
    add_at(out, kit.thump(120, 75, 0.12, t60=0.08, glide=0.02), 0.74, 0.35)
    add_at(out, kit.tick(rng, 1500, 6500, 8, t60=0.03, contact=0.0003, dur=0.05), 0.75, 0.3)
    add_at(out, _paper(rng, 0.12, env.curve([(0, 1), (0.12, 0)], n_of(0.12), "cos"), 1500.0), 0.75, 0.2)
    return _room(out, 0.11)


@sound("card_flick", "sfx", "Thumb flicks through a few index cards (quick papery riffle)")
def card_flick(rng):
    out = np.zeros(n_of(0.3))
    tt = 0.0
    for k in range(5):
        fn = n_of(0.03)
        flick = butter(noise.white(fn, rng), "bandpass", (1800, 8000), 2) * env.ar(fn, 0.001, 0.02)
        snap = modal.strike(modal.random_modes(rng, 1200, 5000, 6, 0.004, 0.012, -2.0), 0.03, 0.0003, rng)
        add_at(out, _norm(flick) + 0.5 * _norm(snap), tt, (1.0 - 0.13 * k) * rng.uniform(0.7, 1.0))
        tt += rng.uniform(0.026, 0.042)
    add_at(out, _paper(rng, 0.2, env.curve([(0, 1), (0.2, 0)], n_of(0.2), "cos"), 1200.0), 0.0, 0.25)
    pn = n_of(0.16)
    air = butter(noise.white(pn, rng), "bandpass", (400, 2000), 2) * env.swell(pn, 0.03, 0.12)
    add_at(out, _norm(air), 0.0, 0.12)
    return _room(out, 0.06)


@sound("punch_key", "sfx", "Card-punch key pressed down: hard key clack with a little spring")
def punch_key(rng):
    out = np.zeros(n_of(0.25))
    add_at(out, kit.knock(rng, 450, 3800, 12, t60=0.035, contact=0.0005, dur=0.08, noise_amt=0.5), 0.0, 1.0)
    add_at(out, kit.tick(rng, 2500, 9000, 10, t60=0.018, contact=0.0001, dur=0.04), 0.002, 0.35)
    add_at(out, kit.thump(230, 160, 0.06, t60=0.04, glide=0.01), 0.0, 0.45)
    n = n_of(0.12)
    tt = time_axis(n)
    spring = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt / td)
                 for f, a, td in ((1730.0, 1.0, 0.03), (3910.0, 0.5, 0.015)))
    add_at(out, spring, 0.006, 0.05)
    return _room(out, 0.07)


@sound("punch_lever", "sfx",
       "Card-punch lever pulled: ratchet, the dies chunk through the card, the lever springs back")
def punch_lever(rng):
    out = np.zeros(n_of(1.0))
    for k, tt in enumerate((0.0, 0.05, 0.095)):
        add_at(out, kit.tick(rng, 1500, 7000, 10, t60=0.03, contact=0.0002, dur=0.05), tt, 0.35 + 0.08 * k)
    t = 0.15
    add_at(out, kit.clank(rng, 160, 3600, 22, t60=0.2, contact=0.0012, dur=0.4), t, 1.0)
    add_at(out, kit.thump(120, 60, 0.3, t60=0.2, glide=0.03), t, 0.8)
    pn = n_of(0.04)
    crunch = butter(noise.dust(pn, 6000, rng, heavy_tail=0.5), "bandpass", (900, 6000), 2)
    add_at(out, _norm(crunch) * env.ar(pn, 0.001, 0.03), t + 0.004, 0.45)  # card stock pierced
    d = 0.18
    feed = kit.friction(rng, d, env.curve([(0, 0), (0.03, 1), (d, 0)], n_of(d), "cos"), 1200, 6000, grit=0.4,
                        grit_rate=1500)
    add_at(out, _norm(feed), t + 0.12, 0.12)  # card advances
    add_at(out, kit.clank(rng, 300, 4500, 14, t60=0.1, contact=0.0008, dur=0.2), t + 0.42, 0.45)  # spring return
    add_at(out, kit.thump(170, 110, 0.1, t60=0.06, glide=0.015), t + 0.42, 0.25)
    return _room(out, 0.12)


# ------------------------------------------------------------------------------------------
# Lockers and hiding places
# ------------------------------------------------------------------------------------------
def _sheet(rng, f_lo=160.0, f_hi=2600.0, t60=0.35):
    """Thin painted steel sheet (locker door, grille): beating panel modes."""
    md = modal.random_modes(rng, f_lo, f_hi, 16, t60 * 0.25, t60, -2.0)
    return md + modal.Modes(md.freqs * 1.009, md.t60s * 0.8, md.amps * 0.5)


@sound("locker_rattle", "sfx", "Locked steel locker door tugged: thin metal clatter against the latch")
def locker_rattle(rng):
    out = np.zeros(n_of(0.65))
    for k, (tt, g) in enumerate(((0.0, 1.0), (0.1, 0.75), (0.19, 0.6), (0.29, 0.35))):
        tt += rng.uniform(-0.008, 0.008)
        add_at(out, _norm(modal.strike(_sheet(rng), 0.3, 0.0008, rng, noise=0.4, noise_decay=0.001)), max(0.0, tt), g)
        add_at(out, kit.tick(rng, 1500, 7000, 10, t60=0.03, contact=0.0002, dur=0.06), max(0.0, tt) + 0.004, 0.5 * g)
        add_at(out, kit.thump(150, 100, 0.08, t60=0.05, glide=0.015), max(0.0, tt), 0.25 * g)
    return _room(out, 0.12)


@sound("locker_open", "sfx", "Locker 9 unlocked: key clack, latch lifts, the thin steel door swings open and taps the next one")
def locker_open(rng):
    out = np.zeros(n_of(1.4))
    for tt, g in ((0.0, 0.35), (0.045, 0.4)):
        add_at(out, kit.tick(rng, 2500, 9000, 8, t60=0.015, contact=0.0001, dur=0.04), tt, g)
    add_at(out, kit.clank(rng, 400, 5000, 14, t60=0.08, contact=0.0005, dur=0.15), 0.1, 0.6)  # key turns
    add_at(out, kit.clank(rng, 300, 4000, 16, t60=0.12, contact=0.0007, dur=0.2), 0.27, 0.9)  # latch lifts
    add_at(out, _norm(modal.strike(_sheet(rng, t60=0.45), 0.5, 0.0015, rng)), 0.27, 0.45)
    d = 0.55
    n = n_of(d)
    cr = kit.creak(rng, d, env.curve([(0, 140), (0.25, 320), (d, 220)], n),
                   env.curve([(0, 0), (0.08, 0.8), (0.3, 1.0), (d, 0)], n, "cos"),
                   modal.metal(rng, 900, 4500, 12, 0.05), jitter=0.04, hiss=0.08)
    add_at(out, cr, 0.36, 0.3)
    wob = modal.ring(_sheet(rng, 120, 900, 0.6), 0.7, rng) * env.swell(n_of(0.7), 0.15, 0.3)
    add_at(out, _norm(wob), 0.38, 0.12)
    add_at(out, _norm(modal.strike(_sheet(rng, 200, 3000, 0.25), 0.35, 0.001, rng, noise=0.3)), 0.95, 0.5)
    add_at(out, kit.tick(rng, 1500, 6000, 8, t60=0.03, contact=0.0003, dur=0.05), 1.0, 0.2)
    return _room(out, 0.12)


@sound("grille_creak", "sfx", "Vent grille swings open on a rusty hinge: frame unsticks, creak, light metal rattle")
def grille_creak(rng):
    out = np.zeros(n_of(1.35))
    d = 0.1
    stick = kit.friction(rng, d, env.curve([(0, 0), (0.03, 1), (d, 0)], n_of(d), "cos"), 900, 6000, grit=0.7,
                         grit_rate=2500)
    add_at(out, _norm(stick), 0.0, 0.3)
    add_at(out, _norm(modal.strike(_sheet(rng, 300, 3500, 0.2), 0.3, 0.0008, rng, noise=0.3)), 0.08, 0.6)
    d = 0.9
    n = n_of(d)
    wob = 1.0 + 0.12 * noise.smooth_random(n, rng, 6.0, periodic=False)
    rate = env.curve([(0, 60), (0.25, 140), (0.5, 210), (0.75, 120), (d, 70)], n, "cos") * wob
    amp = env.curve([(0, 0), (0.08, 0.8), (0.4, 1.0), (0.6, 0.5), (0.75, 0.8), (d, 0)], n, "cos")
    add_at(out, kit.creak(rng, d, rate, amp, modal.metal(rng, 700, 4200, 14, 0.06), jitter=0.07, hiss=0.1), 0.12, 0.75)
    sq = kit.creak(rng, d, env.curve([(0, 520), (0.5, 760), (d, 600)], n, "cos"),
                   env.curve([(0, 0), (0.3, 0), (0.45, 0.8), (0.6, 0), (d, 0)], n, "cos"),
                   modal.metal(rng, 1500, 6000, 10, 0.04), jitter=0.012, hiss=0.04)
    add_at(out, sq, 0.12, 0.25)
    add_at(out, kit.tick(rng, 1200, 6000, 10, t60=0.04, contact=0.0003, dur=0.06), 1.07, 0.45)
    add_at(out, _norm(modal.strike(_sheet(rng, 400, 4000, 0.15), 0.25, 0.0006, rng)), 1.07, 0.3)
    return _room(out, 0.12)


@sound("hatch_open", "sfx", "Floor hatch: iron ring clinks, the heavy lid lifts with a creak and a breath of air, falls back with a thud")
def hatch_open(rng):
    out = np.zeros(n_of(1.9))
    add_at(out, kit.clank(rng, 500, 6000, 14, t60=0.18, contact=0.0004, dur=0.25), 0.0, 0.5)  # ring lifted
    add_at(out, kit.tick(rng, 1500, 7000, 8, t60=0.04, contact=0.0002, dur=0.06), 0.06, 0.3)
    d = 0.95
    n = n_of(d)
    rate = env.curve([(0, 25), (0.3, 55), (0.6, 80), (d, 45)], n, "cos")
    amp = env.curve([(0, 0), (0.1, 0.8), (0.45, 1.0), (0.8, 0.5), (d, 0)], n, "cos")
    body = modal.wood(rng, 90, 900, 14, 0.12) + modal.metal(rng, 600, 3000, 8, 0.06)
    add_at(out, kit.creak(rng, d, rate, amp, body, jitter=0.09, hiss=0.06), 0.25, 0.7)
    pn = n_of(0.35)
    suction = butter(noise.colored(pn, rng, -4.0), "lowpass", 700, 2) * env.ar(pn, 0.01, 0.25)
    add_at(out, _norm(suction), 0.22, 0.3)
    dust = kit.whoosh(rng, 0.6, 500, 2200, q=0.8, attack=0.3, release=0.6)
    add_at(out, _norm(dust), 0.3, 0.12)
    t = 1.28
    add_at(out, kit.knock(rng, 100, 1300, 16, t60=0.18, contact=0.0025, dur=0.5, noise_amt=0.25), t, 1.0)
    add_at(out, kit.thump(100, 50, 0.5, t60=0.3, glide=0.04), t, 0.5)
    add_at(out, kit.clank(rng, 600, 5000, 10, t60=0.1, contact=0.0005, dur=0.15), t + 0.01, 0.3)
    add_at(out, kit.tick(rng, 1500, 6000, 8, t60=0.04, contact=0.0003, dur=0.05), t + 0.08, 0.2)  # ring settles
    return _room(biquad(out, "highpass", 75, 0.7), 0.14)


@sound("ledger_thump", "sfx", "Heavy hollow ledger pulled out and opened: book thump, cover flap, hollow box with something inside")
def ledger_thump(rng):
    out = np.zeros(n_of(0.85))
    d = 0.2
    pull = kit.friction(rng, d, env.curve([(0, 0), (0.05, 1), (d, 0.3)], n_of(d), "cos"), 300, 3500, grit=0.4,
                        grit_rate=600)
    add_at(out, _norm(pull), 0.0, 0.25)
    t = 0.2
    add_at(out, kit.knock(rng, 130, 1500, 14, t60=0.08, contact=0.003, dur=0.3, noise_amt=0.25), t, 1.0)
    add_at(out, kit.thump(120, 70, 0.25, t60=0.12, glide=0.03), t, 0.4)
    add_at(out, _norm(modal.strike(modal.wood(rng, 250, 900, 8, 0.12), 0.25, 0.002, rng)), t, 0.35)  # hollow box
    fn = n_of(0.18)
    flap = tv_biquad(noise.colored(fn, rng, -3.0), "bandpass", env.curve([(0, 300), (0.18, 1100)], fn), 0.9)
    add_at(out, _norm(flap) * env.swell(fn, 0.06, 0.08), t + 0.13, 0.3)
    add_at(out, kit.knock(rng, 150, 1300, 10, t60=0.05, contact=0.003, dur=0.15), t + 0.3, 0.45)  # cover lands
    add_at(out, _paper(rng, 0.2, env.curve([(0, 1), (0.2, 0)], n_of(0.2), "cos"), 900.0), t + 0.3, 0.15)
    for dt, g in ((0.33, 0.25), (0.37, 0.15)):  # the reel shifts inside
        add_at(out, kit.tick(rng, 1500, 6000, 8, t60=0.03, contact=0.0003, dur=0.05), t + dt, g)
    return _room(out, 0.1)


# ------------------------------------------------------------------------------------------
# Pocket receiver
# ------------------------------------------------------------------------------------------
@sound("receiver_beep", "sfx", "Leyla's pocket receiver: short transistor beep from a tiny speaker")
def receiver_beep(rng):
    n = n_of(0.16)
    t = time_axis(n)
    f = 1240.0 * (1.0 + 0.01 * np.exp(-t / 0.01))
    x = osc.additive(f, n, [(1, 1.0), (2, 0.12), (3, 0.22), (5, 0.06)])
    x *= env.curve([(0, 0), (0.004, 1), (0.075, 0.85), (0.1, 0), (0.16, 0)], n, "cos")
    x = butter(x, "bandpass", (500, 6000), 2)
    x = biquad(x, "peak", 2500, 1.5, 3.0)
    return _room(x, 0.05)


@sound("receiver_static", "sfx",
       "Pocket receiver static: soft hiss with a drifting band, crackles and a faint heterodyne whistle (seamless loop)",
       loop=True)
def receiver_static(rng):
    L = STATIC_LOOP
    n = n_of(L)
    t = time_axis(n)
    hiss = noise.colored(n, rng, -1.0, 300, 6000)
    hiss *= 1.0 + 0.25 * noise.smooth_random(n, rng, 1.5)
    # a slowly drifting, resonant band: the receiver 'searching'
    centre = 1300.0 * 2.0 ** (0.7 * noise.smooth_random(n, rng, 0.7))
    src = noise.colored(n, rng, 0.0)
    band = tv_biquad(np.concatenate([src, src]), "bandpass", np.concatenate([centre, centre]), 4.0, block=64)[n:]
    band *= 0.6 + 0.4 * noise.smooth_random(n, rng, 0.9)
    # crackles (wrap-around)

    def crack(r):
        m = n_of(0.006)
        return r.standard_normal(m) * np.exp(-np.arange(m) / (SR * r.uniform(0.0004, 0.0015)))
    cr = granular.cloud(L, 9.0, crack, rng, stereo=False, gain_db=(-24, 0), gain_skew=2.5)
    # faint heterodyne whistle with a wandering pitch (all rates fit the loop)
    fw = periodic_freq(1760.0, L)
    wh = np.sin(2 * np.pi * fw * t + 1.2 * np.sin(2 * np.pi * (2.0 / L) * t) + 0.4 * np.sin(2 * np.pi * (5.0 / L) * t))
    wh *= np.clip(noise.smooth_random(n, rng, 0.5), 0, 1) ** 2
    out = 0.5 * _norm(hiss) + 0.3 * _norm(band) + 0.35 * _norm(cr) + 0.04 * wh
    out = fft_filter(out, lambda f: smooth_band(f, 350, 5000, 0.6))  # the receiver's tiny speaker
    return out


# ------------------------------------------------------------------------------------------
# Tape deck
# ------------------------------------------------------------------------------------------
@sound("deck_play", "sfx", "Reel-to-reel Play key: heavy key clunk, pinch roller engages, motor spins up")
def deck_play(rng):
    out = np.zeros(n_of(0.6))
    add_at(out, kit.knock(rng, 300, 3500, 12, t60=0.05, contact=0.0009, dur=0.12, noise_amt=0.4), 0.0, 0.9)
    add_at(out, kit.clank(rng, 250, 4000, 16, t60=0.1, contact=0.001, dur=0.2), 0.035, 0.85)  # pinch roller
    add_at(out, kit.thump(150, 85, 0.15, t60=0.1, glide=0.02), 0.035, 0.5)
    add_at(out, kit.relay(rng, 0.3, dur=0.1), 0.05, 0.25)  # solenoid
    d = 0.45
    n = n_of(d)
    tt = time_axis(n)
    spin = 1.0 - np.exp(-tt / 0.08)
    motor = kit.hum(d, 50.0, {2: 1.0, 4: 0.5, 6: 0.2}, rng) + 0.3 * osc.sine(300 * spin + 80, n)
    add_at(out, motor * spin * env.curve([(0, 1), (0.2, 1), (d, 0)], n, "cos"), 0.04, 0.18)
    return _room(out, 0.08)


@sound("deck_eject", "sfx", "Tape reel lifted off / dropped onto the deck spindle: latch pop, hub clatter, slide")
def deck_eject(rng):
    out = np.zeros(n_of(0.7))
    add_at(out, kit.clank(rng, 400, 5000, 12, t60=0.06, contact=0.0006, dur=0.12), 0.0, 0.7)
    add_at(out, kit.thump(200, 140, 0.06, t60=0.04, glide=0.01), 0.0, 0.3)
    d = 0.16
    sl = kit.friction(rng, d, env.curve([(0, 0), (0.04, 1), (d, 0)], n_of(d), "cos"), 900, 5000, grit=0.5,
                      grit_rate=1200)
    add_at(out, _norm(sl), 0.05, 0.25)
    for dt, g in ((0.2, 0.6), (0.24, 0.35), (0.3, 0.2)):  # plastic hub clatter
        add_at(out, kit.knock(rng, 600, 5000, 8, t60=0.02, contact=0.0004, dur=0.05, noise_amt=0.4), dt, g)
    return _room(out, 0.08)


@sound("tape_voice", "sfx",
       "Leyla's tape diary: a muffled, speech-like murmur (no real words) with hiss, wow and hum through the deck speaker",
       fade_out=0.25)
def tape_voice(rng):
    dur = 9.0
    n = n_of(dur)
    phrases = [(0.3, 2.25), (2.6, 4.45), (4.85, 6.75), (7.1, 8.55)]
    v = _murmur(rng, dur, phrases, f0=212.0)
    gate = np.ones(n)  # a couple of oxide dropouts
    for t0 in (3.4, 6.1):
        gate[n_of(t0):n_of(t0 + rng.uniform(0.05, 0.1))] = 0.35
    v = _wow(v * butter(gate, "lowpass", 60, 2), rng, depth=0.0009)
    v = soft_clip(0.8 * _norm(butter(v, "bandpass", (240, 2900), 2)), 0.8)  # old tape, saturated a little
    hiss = _tape_hiss(n, rng)
    hum = kit.hum(dur, 50.0, {1: 0.5, 2: 1.0, 3: 0.3}, rng)
    x = 0.8 * v + 0.16 * _norm(hiss) + 0.025 * hum
    x *= env.curve([(0, 0), (0.06, 1), (dur - 0.3, 1), (dur, 0)], n, "cos")
    return _room(_deck_speaker(x), 0.07)


@sound("tape_garble", "sfx", "Tape at the wrong speed: chipmunk-fast, warbling, slurring murmur with hiss")
def tape_garble(rng):
    dur = 2.5
    v = _murmur(rng, 7.0, [(0.1, 2.3), (2.6, 4.5), (4.8, 6.9)], f0=200.0)
    v = butter(v, "lowpass", 6000, 4)
    n = n_of(dur)
    t = time_axis(n)
    r = env.curve([(0, 2.7), (0.5, 2.3), (0.9, 3.0), (1.3, 1.3), (1.55, 0.7), (1.85, 1.6), (2.2, 2.6),
                   (dur, 2.4)], n, "cos")
    r *= 1.0 + 0.16 * np.sin(2 * np.pi * 2.3 * t) + 0.07 * noise.smooth_random(n, rng, 6.0, periodic=False)
    pos = np.cumsum(r)
    y = np.interp(pos, np.arange(len(v)), v, right=0.0)
    y = soft_clip(0.9 * _norm(butter(y, "bandpass", (300, 4200), 2)), 0.9)
    squeal = osc.sine(1250.0 * r, n) * 0.5 * (r / 3.0) ** 2  # capstan and guides singing at speed
    hiss = _tape_hiss(n, rng)
    x = 0.8 * y + 0.03 * squeal + 0.18 * _norm(hiss)
    x *= env.curve([(0, 0), (0.03, 1), (dur - 0.15, 1), (dur, 0)], n, "cos")
    return _room(_deck_speaker(x, 300, 3800), 0.07)


@sound("tape_clicks", "sfx", "One click recorded at the end of a reel (a sharp tap with a little mic thump), through the deck speaker")
def tape_clicks(rng):
    out = np.zeros(n_of(0.3))
    add_at(out, kit.knock(rng, 600, 3800, 10, t60=0.02, contact=0.0003, dur=0.06, noise_amt=0.6), 0.0, 1.0)
    add_at(out, kit.tick(rng, 1500, 5000, 8, t60=0.012, contact=0.0002, dur=0.03), 0.001, 0.5)
    add_at(out, kit.thump(240, 140, 0.08, t60=0.05, glide=0.01), 0.0, 0.45)
    pn = n_of(0.04)
    hs = butter(noise.white(pn, rng), "bandpass", (500, 3000), 2) * env.ar(pn, 0.001, 0.025)
    add_at(out, _norm(hs), 0.0, 0.2)
    return _room(_deck_speaker(out, 260, 3200, 0.8), 0.06)


@sound("tape_hiss", "sfx", "Tape deck running with no signal: hiss, capstan flutter and a faint hum (seamless loop)",
       loop=True)
def tape_hiss(rng):
    L = 6.0
    n = n_of(L)
    t = time_axis(n)
    h = noise.colored(n, rng, -1.0, 700, 10000)
    h *= 1.0 + 0.08 * np.sin(2 * np.pi * periodic_freq(7.3, L) * t)
    f0 = periodic_freq(50.0, L)
    hum = sum(a * np.sin(2 * np.pi * k * f0 * t + rng.uniform(0, 6.3)) for k, a in ((1, 0.5), (2, 1.0), (3, 0.3)))
    x = 0.85 * _norm(h) + 0.06 * hum / 1.8
    return fft_filter(x, lambda f: smooth_band(f, 300, 3000, 0.5) * (1 + 0.5 * np.exp(-((np.log2(np.maximum(f, 1) / 1300)) ** 2) / 0.3)))


# ------------------------------------------------------------------------------------------
# Booth: rotary dial, door, splicer, projectors
# ------------------------------------------------------------------------------------------
@sound("dial_wind", "sfx", "Rotary dial wound round by a finger: ratchety friction and the finger-stop clink")
def dial_wind(rng):
    out = np.zeros(n_of(0.5))
    d = 0.34
    n = n_of(d)
    sp = env.curve([(0, 0), (0.04, 1), (0.25, 0.9), (d, 0.3)], n, "cos")
    fr = kit.friction(rng, d, sp, 800, 6000, body=modal.metal(rng, 900, 4500, 10, 0.04), grit=0.5, grit_rate=1200)
    add_at(out, _norm(fr), 0.0, 0.3)
    for st in _events_from_rate(28.0 * sp):
        add_at(out, kit.tick(rng, 2500, 8000, 6, t60=0.012, contact=0.0001, dur=0.025), st, 0.12 * rng.uniform(0.6, 1))
    add_at(out, kit.tick(rng, 1500, 7000, 12, t60=0.05, contact=0.00015, dur=0.1), d, 0.8)  # finger stop
    add_at(out, kit.thump(380, 260, 0.05, t60=0.03, glide=0.01), d, 0.2)
    return _room(out, 0.06, "booth")


@sound("dial_return", "sfx", "Rotary dial spins back: buzzing governor, pulse-contact ticks, soft stop")
def dial_return(rng):
    out = np.zeros(n_of(0.75))
    d = 0.6
    n = n_of(d)
    lvl = env.curve([(0, 0), (0.03, 1), (0.5, 0.9), (d, 0)], n, "cos")
    gov = kit.buzz(d, 92.0, rng, bright=2600, rough=0.25)
    whirr = kit.friction(rng, d, lvl, 1200, 6000, grit=0.3, grit_rate=800)
    add_at(out, (0.6 * _norm(gov) + 0.3 * _norm(whirr)) * lvl, 0.0, 0.35)
    for k in range(6):  # ten pulses a second
        add_at(out, kit.tick(rng, 1800, 7500, 8, t60=0.02, contact=0.00012, dur=0.04), 0.02 + 0.1 * k, 0.45)
    add_at(out, kit.knock(rng, 500, 3500, 8, t60=0.03, contact=0.0006, dur=0.08), d, 0.6)
    add_at(out, kit.tick(rng, 2000, 7000, 8, t60=0.03, contact=0.0002, dur=0.05), d + 0.003, 0.35)
    return _room(out, 0.06, "booth")


@sound("booth_unlatch", "sfx", "Booth door lock releases: solenoid clunk, bolt slides back, the door creaks ajar and bumps its stop")
def booth_unlatch(rng):
    out = np.zeros(n_of(1.6))
    add_at(out, kit.relay(rng, 1.0), 0.0, 0.7)
    add_at(out, kit.clank(rng, 250, 4500, 18, t60=0.15, contact=0.0009, dur=0.3), 0.02, 1.0)
    add_at(out, kit.thump(130, 70, 0.25, t60=0.15, glide=0.03), 0.02, 0.6)
    d = 0.14
    bolt = kit.friction(rng, d, env.curve([(0, 0), (0.03, 1), (d, 0)], n_of(d), "cos"), 700, 5000,
                        body=modal.metal(rng, 800, 4000, 10, 0.05), grit=0.4, grit_rate=1500)
    add_at(out, _norm(bolt), 0.06, 0.3)
    add_at(out, kit.tick(rng, 1500, 7000, 10, t60=0.035, contact=0.0002, dur=0.06), 0.2, 0.5)
    d = 0.8
    n = n_of(d)
    rate = env.curve([(0, 35), (0.35, 70), (d, 45)], n, "cos")
    amp = env.curve([(0, 0), (0.1, 0.8), (0.4, 1.0), (d, 0)], n, "cos")
    body = modal.wood(rng, 120, 1200, 12, 0.08) + modal.metal(rng, 900, 4000, 8, 0.05)
    add_at(out, kit.creak(rng, d, rate, amp, body, jitter=0.07, hiss=0.08), 0.55, 0.45)
    add_at(out, kit.knock(rng, 150, 1500, 12, t60=0.07, contact=0.0015, dur=0.2), 1.35, 0.55)
    return _room(out, 0.12)


@sound("splicer_click", "sfx", "Film splicer: blade snaps down through the film and the clamp clicks")
def splicer_click(rng):
    out = np.zeros(n_of(0.3))
    add_at(out, kit.clank(rng, 900, 8000, 16, t60=0.06, contact=0.00025, dur=0.1, noise_amt=0.6), 0.0, 1.0)
    pn = n_of(0.012)
    snip = butter(noise.white(pn, rng), "highpass", 2500, 2) * env.ar(pn, 0.0005, 0.008)
    add_at(out, _norm(snip), 0.001, 0.4)  # film cut
    add_at(out, kit.thump(300, 210, 0.05, t60=0.03, glide=0.01), 0.0, 0.25)
    add_at(out, kit.tick(rng, 2000, 8000, 10, t60=0.025, contact=0.00012, dur=0.05), 0.045, 0.55)  # clamp
    return _room(out, 0.06, "booth")


def _claw(rng):
    """One frame of the film projector's intermittent: claw pulldown tick,
    film slap in the gate, shutter blade flick."""
    out = np.zeros(n_of(0.04))
    add_at(out, kit.tick(rng, 1500, 6500, 8, t60=0.012, contact=0.00025, dur=0.03, noise_amt=0.3), 0.0, 1.0)
    add_at(out, kit.knock(rng, 250, 1800, 6, t60=0.015, contact=0.001, dur=0.03, noise_amt=0.2), 0.002, 0.6)
    fn = n_of(0.012)
    flap = butter(noise.white(fn, rng), "bandpass", (2000, 7000), 2) * env.ar(fn, 0.001, 0.008)
    add_at(out, _norm(flap), 0.019, 0.15)
    return out


def _projector_bed(rng, d, spin, claw_bank, claw_gain=0.5):
    """Running film projector at speed ``spin`` (0..1 array): motor whine,
    fan, 24 fps intermittent and the shutter's 48 Hz flutter on the fan air."""
    n = n_of(d)
    out = np.zeros(n)
    fps = 24.0 * spin
    ph = np.cumsum(fps) / SR
    motor = osc.additive(440.0 * spin + 1e-3, n, [(1, 1.0), (2, 0.35), (3, 0.12)]) * spin ** 1.5
    h = kit.hum(d, 50.0, {2: 1.0, 4: 0.4, 6: 0.2}, rng)
    fan = butter(noise.colored(n, rng, -2.0), "bandpass", (250, 3500), 2)
    flutter = 1.0 + 0.3 * np.sin(2 * np.pi * 2.0 * ph)  # two-blade shutter at 2x the frame rate
    out += 0.05 * motor + 0.06 * h * np.clip(spin * 2, 0, 1) + 0.35 * _norm(fan) * spin * flutter
    for st in _events_from_rate(fps, 0.5):
        i = min(n - 1, int(st * SR))
        add_at(out, claw_bank[int(rng.integers(len(claw_bank)))], st, claw_gain * rng.uniform(0.85, 1.0)
               * (0.4 + 0.6 * spin[i]))
    return out


@sound("film_projector_start", "sfx",
       "16 mm projector run lever: clack, motor and fan spin up, the claw clatter speeds up to 24 frames a second")
def film_projector_start(rng):
    total = 2.5
    out = np.zeros(n_of(total))
    add_at(out, kit.knock(rng, 600, 4500, 12, t60=0.04, contact=0.0005, dur=0.1, noise_amt=0.4), 0.0, 0.9)
    add_at(out, kit.clank(rng, 300, 4000, 14, t60=0.08, contact=0.0008, dur=0.15), 0.01, 0.5)
    add_at(out, kit.relay(rng, 0.4, dur=0.1), 0.06, 0.25)  # lamp relay
    bank = [_claw(rng) for _ in range(8)]
    d = total - 0.05
    n = n_of(d)
    tt = time_axis(n)
    spin = 1.0 - np.exp(-tt / 0.45)
    bed = _projector_bed(rng, d, spin, bank)
    bed *= env.curve([(0, 1), (1.6, 1), (d, 0.0)], n, "cos")  # hands over to film_projector_loop
    add_at(out, bed, 0.04, 0.8)
    return _room(out, 0.08, "booth")


@sound("film_projector_loop", "sfx",
       "Film projector running at 24 fps under the film: claw clatter, motor, fan and shutter flutter (~22 s bed)",
       fade_out=2.5)
def film_projector_loop(rng):
    d = 22.0
    n = n_of(d)
    bank = [_claw(rng) for _ in range(10)]
    spin = np.ones(n) * (1.0 + 0.006 * noise.smooth_random(n, rng, 0.5, periodic=False))
    bed = _projector_bed(rng, d, spin, bank)
    # film flutter through the gate, slow sway as the reels change weight
    gate = butter(noise.white(n, rng), "bandpass", (3000, 9000), 2) * (0.6 + 0.4 * noise.smooth_random(n, rng, 0.3, False))
    bed += 0.05 * _norm(gate)
    bed *= env.curve([(0, 0), (1.2, 1.0), (d, 1.0)], n, "cos")
    return _room(bed, 0.08, "booth")


@sound("film_projector_stop", "sfx", "Projector switched off: lever clack, the clatter slows and stops, motor and fan wind down")
def film_projector_stop(rng):
    total = 2.4
    out = np.zeros(n_of(total))
    add_at(out, kit.knock(rng, 600, 4500, 12, t60=0.04, contact=0.0005, dur=0.1, noise_amt=0.4), 0.0, 0.9)
    add_at(out, kit.clank(rng, 300, 4000, 14, t60=0.08, contact=0.0008, dur=0.15), 0.01, 0.4)
    bank = [_claw(rng) for _ in range(8)]
    d = 2.0
    n = n_of(d)
    tt = time_axis(n)
    spin = np.clip(np.exp(-tt / 0.55) - 0.04, 0, 1) / 0.96
    bed = _projector_bed(rng, d, spin, bank)
    add_at(out, bed, 0.0, 0.8)
    st = float(tt[np.argmax(spin <= 0.0)]) if np.any(spin <= 0.0) else d
    add_at(out, kit.knock(rng, 300, 2500, 8, t60=0.04, contact=0.001, dur=0.1), min(st, d - 0.1), 0.35)  # claw parks
    return _room(out, 0.08, "booth")


@sound("slide_clunk", "sfx", "Glass slide pushed into (or out of) the slide projector gate: plastic-and-metal clunk with a spring")
def slide_clunk(rng):
    out = np.zeros(n_of(0.5))
    d = 0.08
    sl = kit.friction(rng, d, env.curve([(0, 0), (0.02, 1), (d, 0.4)], n_of(d), "cos"), 1000, 6000, grit=0.4,
                      grit_rate=1500)
    add_at(out, _norm(sl), 0.0, 0.25)
    add_at(out, kit.knock(rng, 300, 3000, 12, t60=0.05, contact=0.0008, dur=0.12, noise_amt=0.4), 0.075, 1.0)
    add_at(out, kit.clank(rng, 600, 5500, 12, t60=0.06, contact=0.0005, dur=0.1), 0.078, 0.45)
    add_at(out, kit.thump(170, 110, 0.1, t60=0.06, glide=0.015), 0.075, 0.4)
    add_at(out, _norm(modal.strike(modal.glass(3100.0, t60=0.12, bright=0.3), 0.15, 0.0003, rng)), 0.079, 0.08)
    add_at(out, kit.tick(rng, 2000, 8000, 8, t60=0.02, contact=0.00012, dur=0.04), 0.13, 0.35)
    return _room(out, 0.08, "booth")


@sound("slide_fan_loop", "sfx", "Slide projector running: cooling fan, blade hum and lamp transformer (seamless loop)",
       loop=True)
def slide_fan_loop(rng):
    L = 5.0
    n = n_of(L)
    t = time_axis(n)
    rot = periodic_freq(47.6, L)  # fan rotor, 5 blades
    bpf = 5.0 * rot
    tone = sum(a * np.sin(2 * np.pi * k * bpf * t + rng.uniform(0, 6.3)) for k, a in ((1, 1.0), (2, 0.4), (3, 0.15)))
    tone += 0.3 * np.sin(2 * np.pi * rot * t)
    f0 = periodic_freq(50.0, L)
    hum = sum(a * np.sin(2 * np.pi * k * f0 * t + rng.uniform(0, 6.3)) for k, a in ((2, 1.0), (4, 0.4), (6, 0.2)))
    air = noise.colored(n, rng, -2.0, 200, 7000) * (1.0 + 0.15 * np.sin(2 * np.pi * bpf * t))
    x = 0.08 * tone + 0.05 * hum + 0.6 * _norm(air)
    return reverb.reverb_circular(x, _ir("booth"), 0.1)


# ------------------------------------------------------------------------------------------
# Crystals and the vault
# ------------------------------------------------------------------------------------------
@sound("crystal_record", "sfx", "A crystal records the image: rising glassy shimmer that locks into a bright A chime and glows out")
def crystal_record(rng):
    out = np.zeros(n_of(3.0))
    # charge: glass partials gliding up as the light pours in
    d = 0.75
    n = n_of(d)
    tt = time_axis(n)
    rise = np.zeros(n)
    for f0, g in ((hz("A5"), 1.0), (hz("E6"), 0.6), (hz("B6"), 0.35)):
        f = f0 * 2.0 ** (-1.0 + tt / d)
        rise += g * osc.additive(f, n, [(1, 1.0), (2.32, 0.25)], rng.uniform(0, 1, 2))
    rise *= env.curve([(0, 0), (0.6, 0.6), (d, 1.0)], n, "cos")
    add_at(out, _norm(rise), 0.0, 0.4)
    wh = kit.whoosh(rng, d, 1200, 7000, q=0.9, attack=0.85, release=0.05)
    add_at(out, _norm(wh), 0.0, 0.12)
    # lock: struck crystal chord with a soft low bloom
    t = d
    for note, kind, g, dt in (("A4", "bell", 0.45, 0.0), ("E5", "glass", 0.6, 0.006), ("A5", "glass", 0.7, 0.012),
                              ("B5", "glass", 0.45, 0.02), ("E6", "glass", 0.4, 0.03)):
        x = (music.bell(hz(note), g, rng, dur=2.2, t60=1.8, bright=0.45) if kind == "bell"
             else music.glass(hz(note), g, rng, dur=2.2, t60=1.6, bright=0.4))
        add_at(out, x, t + dt)
    add_at(out, music.glass(hz("A6"), 0.25, rng, dur=1.8, t60=1.4, attack=0.3, bright=0.2), t + 0.05)
    add_at(out, kit.thump(110, 70, 0.6, t60=0.5, glide=0.06, harm=0.2), t, 0.35)
    out *= env.curve([(0, 1), (2.3, 1), (3.0, 0)], len(out), "cos")
    return kit.limit(reverb.reverb(out, reverb.preset("plate"), 0.3), 3.2, 0.5)


@sound("collar_click", "sfx", "Brass collar or selector turned one detent: firm click with a small ring")
def collar_click(rng):
    out = np.zeros(n_of(0.35))
    d = 0.06
    fr = kit.friction(rng, d, env.curve([(0, 0), (0.02, 1), (d, 0.3)], n_of(d), "cos"), 900, 5000, grit=0.3,
                      grit_rate=1200)
    add_at(out, _norm(fr), 0.0, 0.15)
    add_at(out, kit.tick(rng, 1000, 6000, 14, t60=0.06, contact=0.0002, dur=0.12), 0.05, 1.0)
    ring_ = modal.strike(modal.Modes(np.array([640.0, 1720.0, 3240.0, 5100.0]), np.array([0.22, 0.14, 0.08, 0.05]),
                                     np.array([1.0, 0.55, 0.3, 0.15])), 0.3, 0.0003, rng)
    add_at(out, _norm(ring_), 0.05, 0.22)
    add_at(out, kit.thump(260, 180, 0.05, t60=0.03, glide=0.01), 0.05, 0.25)
    return _room(out, 0.08)


@sound("vault_bolts", "sfx", "Vault light lock accepted: eight heavy bolts retract around the door in a rolling cascade")
def vault_bolts(rng):
    out = np.zeros(n_of(2.6))
    add_at(out, kit.relay(rng, 1.0), 0.0, 0.6)
    for k in range(8):  # in step with the 0.12 s bolt animation
        t = 0.02 + 0.12 * k + rng.uniform(-0.006, 0.006)
        g = 0.75 + 0.25 * np.sin(np.pi * k / 7.0)
        d = 0.09
        sl = kit.friction(rng, d, env.curve([(0, 0), (0.02, 1), (d, 0.2)], n_of(d), "cos"), 400, 4000,
                          body=modal.metal(rng, 500, 3000, 8, 0.05), grit=0.4, grit_rate=900)
        add_at(out, _norm(sl), t, 0.15 * g)
        add_at(out, kit.clank(rng, 150, 3200, 20, t60=0.22, contact=0.0012, dur=0.35), t + 0.07, 0.75 * g)
        add_at(out, kit.thump(100, 55, 0.25, t60=0.18, glide=0.03), t + 0.07, 0.4 * g)
    t = 1.06
    add_at(out, kit.clank(rng, 80, 2500, 28, t60=0.6, contact=0.002, dur=1.0), t, 1.0)
    add_at(out, kit.thump(70, 35, 0.8, t60=0.6, glide=0.06, harm=0.4), t, 0.7)
    door = modal.random_modes(rng, 70, 600, 12, 0.5, 1.4, -2.0)  # the whole door rings
    add_at(out, _norm(modal.strike(door, 1.5, 0.003, rng)), t, 0.3)
    return reverb.reverb(out, _ir("vault"), 0.22)


@sound("vault_wheel", "sfx", "Spoked vault wheel heaved round: heavy gear grind, ratchet clunks, a final clunk")
def vault_wheel(rng):
    out = np.zeros(n_of(1.2))
    d = 0.7
    n = n_of(d)
    sp = env.curve([(0, 0), (0.1, 1.0), (0.5, 0.85), (d, 0.0)], n, "cos")
    grind = kit.friction(rng, d, sp, 150, 2500, body=modal.metal(rng, 200, 1800, 14, 0.12), grit=0.5,
                         grit_rate=400, rough_rate=15)
    add_at(out, _norm(grind), 0.0, 0.45)
    for k, tt in enumerate((0.12, 0.29, 0.46)):
        add_at(out, kit.clank(rng, 200, 3000, 14, t60=0.12, contact=0.0012, dur=0.2), tt, 0.45 + 0.05 * k)
        add_at(out, kit.thump(130, 80, 0.12, t60=0.08, glide=0.02), tt, 0.3)
    add_at(out, kit.clank(rng, 120, 2600, 22, t60=0.3, contact=0.0015, dur=0.4), d, 1.0)
    add_at(out, kit.thump(90, 45, 0.4, t60=0.3, glide=0.04), d, 0.8)
    return reverb.reverb(out, _ir("vault"), 0.15)


@sound("vault_door_open", "sfx",
       "The round vault door swings open: seal breaks with a sigh of air, massive hinge groans, deep rumble, it settles")
def vault_door_open(rng):
    total = 5.0
    out = np.zeros(n_of(total))
    add_at(out, kit.clank(rng, 100, 3000, 24, t60=0.35, contact=0.0018, dur=0.6), 0.0, 0.8)
    add_at(out, kit.thump(80, 40, 0.5, t60=0.35, glide=0.05), 0.0, 0.8)
    # the seal lets go: pressure sigh
    sn = n_of(1.2)
    sigh = noise.colored(sn, rng, -2.0, 300, 7000) * env.curve([(0, 0), (0.04, 1.0), (0.4, 0.4), (1.2, 0)], sn, "cos")
    add_at(out, _norm(sigh), 0.05, 0.3)
    d = 3.4
    n = n_of(d)
    wob = 1.0 + 0.15 * noise.smooth_random(n, rng, 3.0, periodic=False)
    rate = env.curve([(0, 9), (0.6, 18), (1.4, 26), (2.2, 20), (2.8, 13), (d, 8)], n, "cos") * wob
    amp = env.curve([(0, 0), (0.3, 0.7), (1.0, 1.0), (1.8, 0.8), (2.5, 0.9), (3.0, 0.4), (d, 0)], n, "cos")
    body = modal.random_modes(rng, 45, 380, 16, 0.15, 0.5, -1.0) + modal.metal(rng, 400, 2200, 10, 0.1)
    add_at(out, kit.creak(rng, d, rate, amp, body, jitter=0.1, hiss=0.05, hiss_band=(600, 2500)), 0.35, 1.0)
    groan_rate = env.curve([(0, 90), (1.0, 140), (2.0, 120), (d, 85)], n, "cos") * wob
    groan_amp = env.curve([(0, 0), (0.6, 0.0), (1.0, 0.7), (1.5, 0.3), (2.1, 0.8), (2.6, 0.0), (d, 0)], n, "cos")
    add_at(out, kit.creak(rng, d, groan_rate, groan_amp, modal.metal(rng, 250, 2000, 12, 0.08), jitter=0.03, hiss=0.0),
           0.35, 0.35)
    rumble = butter(noise.colored(n, rng, -6.0), "lowpass", 220, 2) * amp
    add_at(out, _norm(rumble), 0.35, 0.35)
    t = 3.75
    add_at(out, kit.clank(rng, 90, 2500, 24, t60=0.5, contact=0.002, dur=0.8), t, 0.75)
    add_at(out, kit.thump(75, 38, 0.6, t60=0.45, glide=0.05), t, 0.9)
    out *= env.curve([(0, 1), (4.4, 1), (total, 0)], len(out), "cos")
    return kit.limit(reverb.reverb(out, _ir("vault"), 0.28), 5.6, 0.8)


@sound("key_lift", "sfx", "A heavy key lifted out of its cradle: catch releases, metal slides free, a faint ring")
def key_lift(rng):
    out = np.zeros(n_of(1.0))
    add_at(out, kit.tick(rng, 1500, 7000, 12, t60=0.04, contact=0.0002, dur=0.08), 0.0, 0.6)
    add_at(out, kit.clank(rng, 400, 5000, 12, t60=0.08, contact=0.0006, dur=0.15), 0.01, 0.5)
    d = 0.2
    sl = kit.friction(rng, d, env.curve([(0, 0), (0.04, 1), (d, 0)], n_of(d), "cos"), 1500, 7000,
                      body=modal.metal(rng, 1800, 7000, 10, 0.05), grit=0.5, grit_rate=1500)
    add_at(out, _norm(sl), 0.05, 0.3)
    md = modal.Modes(np.array([1870.0, 4410.0, 7020.0]), np.array([0.5, 0.3, 0.15]), np.array([1.0, 0.5, 0.25]))
    add_at(out, _norm(modal.strike(md, 0.7, 0.0003, rng)), 0.24, 0.3)
    return _room(out, 0.12, "vault")


# ------------------------------------------------------------------------------------------
# Ambience
# ------------------------------------------------------------------------------------------
def _distant_tube(rng, d=2.6):
    """Somewhere in the building a canister runs through the ceiling tubes:
    a muffled rush that moves across, and a far-off thunk."""
    n = n_of(d)
    x = kit.whoosh(rng, d, 900, 300, q=1.1, attack=0.35, release=0.5)
    tt = time_axis(n)
    src = noise.colored(n, rng, -3.0)
    tube = sum(a * tv_biquad(src, "bandpass", 300.0 * k * (1.0 - 0.1 * tt / d), 12.0, block=64)
               for k, a in ((1, 1.0), (2, 0.5), (3, 0.2)))
    x = _norm(x) + 0.5 * _norm(tube) * env.swell(n, 0.35 * d, 0.5 * d)
    x = butter(x, "lowpass", 1400, 2)
    k = kit.knock(rng, 90, 600, 8, t60=0.08, contact=0.003, dur=0.2) * 0.6
    out = np.zeros(n + n_of(0.3))
    add_at(out, x, 0.0, 1.0)
    add_at(out, butter(k, "lowpass", 900, 2), d - 0.15, 0.9)
    return out


@sound("amb_archive", "ambience",
       "Records Archive B: deep room tone, the Array humming far below, a slow clock, ticking pipes, distant canisters in the tubes",
       loop=True, lufs=-24.0)
def amb_archive(rng):
    L = ARCHIVE_LOOP
    n = n_of(L)
    t = time_axis(n)
    out = np.zeros((2, n))
    # 1) room tone: ventilation and the big still air of the stacks
    vent = np.vstack([noise.colored(n, rng, -5.0, 40, 500), noise.colored(n, rng, -5.0, 40, 500)])
    out += 0.12 * vent * (1.0 + 0.15 * noise.smooth_random(n, rng, 0.05))
    air = np.vstack([noise.colored(n, rng, -2.5, 200, 5000), noise.colored(n, rng, -2.5, 200, 5000)])
    out += 0.035 * air
    # 2) the Array, far beneath the floor: a breathing 100 Hz-led hum (all rates fit the loop)
    f0 = periodic_freq(50.0, L)
    hum = np.zeros((2, n))
    for c in range(2):
        for k, a in ((1, 0.3), (2, 1.0), (3, 0.35), (4, 0.4), (6, 0.15), (8, 0.06)):
            wander = 1.0 + 0.2 * np.sin(2 * np.pi * rng.integers(1, 4) / L * t + rng.uniform(0, 6.3))
            hum[c] += a * wander * np.sin(2 * np.pi * k * f0 * t + rng.uniform(0, 6.3))
    breath = 0.6 + 0.4 * np.sin(2 * np.pi * (2.0 / L) * t + 1.0)
    out += 0.012 * hum * breath
    # 3) a wall clock, tick-tock, left of centre, quiet
    clock = np.zeros((2, n))
    tick_a = kit.tick(rng, 1800, 6000, 10, t60=0.03, contact=0.0003, dur=0.06)
    tick_b = kit.tick(rng, 1400, 5000, 10, t60=0.035, contact=0.0003, dur=0.06)
    for k in range(int(L)):
        add_circular(clock, pan((tick_a if k % 2 == 0 else tick_b) * rng.uniform(0.85, 1.0), -0.45), k + 0.31)
    out += 0.04 * butter(clock, "bandpass", (700, 5000), 2)
    # 4) pipes ticking as they cool: little clusters of metallic ticks
    pipes = np.zeros((2, n))
    for t0, p in ((4.2, 0.6), (17.9, -0.3), (29.5, 0.7), (41.0, 0.2), (55.3, -0.65)):
        tt = t0
        for k in range(int(rng.integers(3, 7))):
            add_circular(pipes, pan(kit.tick(rng, 2000, 7000, 8, t60=0.05, contact=0.0002, dur=0.08), p), tt,
                         rng.uniform(0.3, 1.0))
            tt += rng.uniform(0.15, 0.7)
    out += 0.05 * pipes
    # 5) canisters in the ceiling tubes, far off, crossing the room
    tubes = np.zeros((2, n))
    for t0, p0, p1, g in ((9.0, -0.8, 0.6, 1.0), (33.5, 0.7, -0.5, 0.8), (48.8, -0.4, 0.8, 0.7)):
        x = _distant_tube(rng)
        add_circular(tubes, _tilt_pan(x, np.linspace(p0, p1, len(x))), t0, g)
    out += 0.11 * tubes
    # 6) rare events: a stack of paper settling, a shelf creak, an old relay
    ev = np.zeros((2, n))
    for t0, p in ((14.6, 0.4), (44.2, -0.5)):
        d = 0.5
        rs = _paper(rng, d, env.curve([(0, 0), (0.1, 1), (0.3, 0.5), (d, 0)], n_of(d), "cos"), 500.0)
        add_circular(ev, pan(butter(rs, "lowpass", 5000, 2), p), t0, 0.25)
    for t0, d, r0, r1, p in ((23.4, 0.8, 30, 60, -0.3), (51.1, 0.6, 40, 80, 0.5)):
        m = n_of(d)
        cr = kit.creak(rng, d, env.curve([(0, r0), (d * 0.6, r1), (d, r0)], m),
                       env.curve([(0, 0), (d * 0.3, 1.0), (d * 0.7, 0.6), (d, 0)], m, "cos"),
                       modal.random_modes(rng, 90, 900, 14, 0.04, 0.14, -2), jitter=0.1, hiss=0.05)
        add_circular(ev, pan(np.convolve(cr, np.ones(4) / 4, mode="same"), p), t0, 0.16)
    add_circular(ev, pan(kit.relay(rng, 0.6), 0.8), 37.2, 0.12)
    out += reverb.reverb_circular(ev, _ir("amb", True), 0.45)
    out = reverb.reverb_circular(out, _ir("amb", True), 0.15)
    return rotate_to_calm_point(out)
