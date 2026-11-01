"""Chapter 2 expansion: hand-held item foley (docs/CHAPTER2_EXPANSION.md section 12). Gloved leather hand, four
tools, three gestures each: ``hand_pickup_<item>``, ``hand_equip_<item>``, ``hand_putaway_<item>`` for
``cloth`` (wipe_cloth), ``mallet``, ``uvlamp`` (uv_lamp) and ``keys`` (key ring). Short, quiet, dry, mono, peak -6 dBFS.
Nothing is above 6 kHz except the key jingle. Generic ``hand_leather_creak`` can be layered on any other item."""
from __future__ import annotations

import numpy as np

from synth import env, modal, noise, osc
from synth.core import add_at, n_of, time_axis
from synth.filters import butter

from . import kit, sound

PEAK = -6.0


def _nrm(x):
    return x / max(float(np.max(np.abs(x))), 1e-9)


def _lp(x, f):
    return butter(x, "lowpass", f, 2)


def _mix(dur, items):
    out = np.zeros(n_of(dur))
    for s, t, g in items:
        add_at(out, s, t, g)
    return out


def _leather(rng, dur=0.22, f=(40, 70)):
    """A glove closing round a handle: a short stick-slip creak through a soft leather body."""
    m = n_of(dur)
    cr = kit.creak(rng, dur, env.curve([(0, f[0]), (dur, f[1])], m), env.curve([(0, 0), (dur * 0.3, 1), (dur, 0)], m, "cos"),
                   modal.random_modes(rng, 180, 1300, 8, 0.05, 0.15, -2), jitter=0.12, hiss=0.06, hiss_band=(500, 2200))
    return _lp(_nrm(cr), 2600)


def _rustle(rng, dur, lo=600, hi=3200, slope=-3.0, peaks=0.5):
    n = n_of(dur)
    x = noise.colored(n, rng, slope, lo, hi) * env.curve([(0, 0), (dur * 0.2, 1), (dur * 0.6, 0.6), (dur, 0)], n, "cos")
    x = x * (1.0 - peaks + peaks * np.abs(noise.smooth_random(n, rng, 18, periodic=False)))
    return _lp(_nrm(x), 3600)


def _thud(rng, f=110, dur=0.18, soft=True):
    return _lp(_nrm(kit.thump(f, f * 0.6, dur, dur * 0.6)), 400 if soft else 900)


def _jingle(rng, count, dur, f_lo=2200):
    out = np.zeros(n_of(dur))
    for k in range(count):
        md = modal.metal(rng, f_lo, f_lo * 3.2, 8, 0.12)
        add_at(out, _nrm(modal.strike(md, 0.25, 0.0003, rng, noise=0.2)), rng.uniform(0, dur * 0.7), rng.uniform(0.4, 1.0))
    return out


# ---- cloth -----------------------------------------------------------------------------------------

@sound("hand_pickup_cloth", "sfx", "Hand: the wipe cloth is picked up, a soft cloth rustle and a light glove grip", peak_db=PEAK)
def hand_pickup_cloth(rng):
    return _mix(0.5, [(_rustle(rng, 0.4), 0.0, 0.8), (_leather(rng, 0.15), 0.03, 0.35)])


@sound("hand_equip_cloth", "sfx", "Hand: the cloth is shaken out and gripped, a short airy flick and a cloth pat", peak_db=PEAK)
def hand_equip_cloth(rng):
    fl = kit.whoosh(rng, 0.18, 700, 2200, q=0.9, attack=0.2, release=0.6)
    return _mix(0.45, [(_nrm(_lp(fl, 3200)), 0.0, 0.5), (_rustle(rng, 0.15, 500, 2500), 0.16, 0.4), (_thud(rng, 150, 0.08), 0.2, 0.3)])


@sound("hand_putaway_cloth", "sfx", "Hand: the cloth is folded away, a longer soft rustle and a muffled pat of the pocket", peak_db=PEAK)
def hand_putaway_cloth(rng):
    return _mix(0.65, [(_rustle(rng, 0.5, 500, 2800), 0.0, 0.7), (_thud(rng, 120, 0.15), 0.46, 0.5), (_leather(rng, 0.12), 0.05, 0.25)])


# ---- mallet ----------------------------------------------------------------------------------------

@sound("hand_pickup_mallet", "sfx", "Hand: the mallet is lifted, a wooden handle on a leather palm, a soft knock of the head", peak_db=PEAK)
def hand_pickup_mallet(rng):
    wd = _lp(_nrm(kit.knock(rng, 180, 1500, 8, t60=0.05, contact=0.002, dur=0.15, noise_amt=0.05)), 2000)
    return _mix(0.5, [(_leather(rng, 0.2), 0.0, 0.6), (wd, 0.16, 0.8)])


@sound("hand_equip_mallet", "sfx", "Hand: the mallet is set in the grip, a glove squeeze and a small hollow wooden tock", peak_db=PEAK)
def hand_equip_mallet(rng):
    wd = _lp(_nrm(kit.knock(rng, 200, 1800, 8, t60=0.06, contact=0.0015, dur=0.2, noise_amt=0.05)), 2400)
    return _mix(0.45, [(_leather(rng, 0.16, (50, 85)), 0.0, 0.55), (wd, 0.14, 0.7)])


@sound("hand_putaway_mallet", "sfx", "Hand: the mallet goes away, a dull wood-on-leather thud and a short slide", peak_db=PEAK)
def hand_putaway_mallet(rng):
    return _mix(0.5, [(_rustle(rng, 0.18, 300, 1800, -4.0, 0.3), 0.0, 0.4), (_thud(rng, 130, 0.2), 0.14, 0.9),
                      (_lp(_nrm(kit.knock(rng, 150, 1000, 7, t60=0.05, contact=0.003, dur=0.12, noise_amt=0.0)), 1500), 0.14, 0.35)])


# ---- UV lamp ---------------------------------------------------------------------------------------

def _uv_hum(dur, rise):
    n = n_of(dur)
    t = time_axis(n)
    f = 120.0 * (1.0 + (0.3 if rise else -0.0) * (1 - np.exp(-t * 9))) if rise else 150.0 * np.exp(-t * 6)
    ph = 2 * np.pi * np.cumsum(f) / 44100
    x = np.sin(ph) + 0.4 * np.sin(2 * ph)
    return _lp(x, 900) * (env.curve([(0, 0), (0.02, 1), (dur * 0.7, 0.6), (dur, 0)], n, "lin") if rise else env.curve([(0, 1), (dur, 0)], n, "lin"))


@sound("hand_pickup_uvlamp", "sfx", "Hand: the UV lamp is picked up, a small clink of the casing against the glove and a rubber grip", peak_db=PEAK)
def hand_pickup_uvlamp(rng):
    cl = _nrm(modal.strike(modal.metal(rng, 1100, 5000, 10, 0.1), 0.25, 0.0004, rng, noise=0.2))
    return _mix(0.5, [(_leather(rng, 0.18), 0.0, 0.5), (cl, 0.12, 0.6), (_thud(rng, 160, 0.08), 0.15, 0.3)])


@sound("hand_equip_uvlamp", "sfx", "Hand: the UV lamp is switched on, a switch click and a faint rising electronic hum", peak_db=PEAK)
def hand_equip_uvlamp(rng):
    sw = _nrm(kit.tick(rng, 1800, 6000, 12, t60=0.03, contact=0.0003, dur=0.08))
    return _mix(0.6, [(sw, 0.0, 0.9), (_nrm(_uv_hum(0.5, True)), 0.03, 0.3)])


@sound("hand_putaway_uvlamp", "sfx", "Hand: the UV lamp is switched off and put away, a falling hum, a click and a soft case thud", peak_db=PEAK)
def hand_putaway_uvlamp(rng):
    sw = _nrm(kit.tick(rng, 1600, 5500, 12, t60=0.03, contact=0.0003, dur=0.08))
    return _mix(0.7, [(_nrm(_uv_hum(0.3, False)), 0.0, 0.25), (sw, 0.02, 0.8), (_thud(rng, 120, 0.15), 0.38, 0.6), (_rustle(rng, 0.15, 400, 2000), 0.3, 0.3)])


# ---- keys ------------------------------------------------------------------------------------------

@sound("hand_pickup_keys", "sfx", "Hand: the key ring is lifted, a bright short jingle of several keys", peak_db=PEAK)
def hand_pickup_keys(rng):
    return _mix(0.55, [(_jingle(rng, 7, 0.4), 0.0, 0.7), (_leather(rng, 0.14), 0.0, 0.2)])


@sound("hand_equip_keys", "sfx", "Hand: a key is taken from the ring and held, a short two-key clink and a clasp tick", peak_db=PEAK)
def hand_equip_keys(rng):
    return _mix(0.4, [(_jingle(rng, 3, 0.25), 0.0, 0.6), (_nrm(kit.tick(rng, 1600, 5500, 10, t60=0.03, dur=0.07)), 0.2, 0.5)])


@sound("hand_putaway_keys", "sfx", "Hand: the keys slide into a pocket, a muffled jingle and a cloth pat", peak_db=PEAK)
def hand_putaway_keys(rng):
    return _mix(0.55, [(_lp(_jingle(rng, 5, 0.3, 1800), 3500), 0.0, 0.5), (_rustle(rng, 0.25, 400, 2200), 0.05, 0.5), (_thud(rng, 120, 0.12), 0.32, 0.4)])


@sound("hand_leather_creak", "sfx", "Hand: a generic glove-on-leather creak to layer under any other held item (e.g. lift a book or a lens)", peak_db=PEAK)
def hand_leather_creak(rng):
    return _leather(rng, 0.28, (35, 65))
