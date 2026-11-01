"""Chapter 2 expansion: the six reaction-moment cues of docs/CHAPTER2_EXPANSION.md section 11, matching
``ArchiveExpData.MOMENTS`` (id -> cue): m1 ``lamp_dip``, m2 ``knocks``, m3 ``frost_steps``, m4 ``roll_call``,
m5 ``steps_above``, m6 ``echo_chime``.

Every cue exists twice. The plain id is the **Full** variant (Settings "Eerie moments: Full"); ``<id>_soft`` is the
**Soft** variant ("no sound sting"): lower, rounder, no transients, no crackle, shorter. Eerie, never shocking:
no sudden loud onset (every onset is at least 20 ms), nothing above 5 kHz except the single bulb tick of the Full
lamp cue, no voice at all (the roll call is pitched horn tones only: a count and then silence)."""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from synth import env, modal, music, noise, osc, reverb
from synth.core import SR, add_at, n_of, time_axis
from synth.filters import butter, tv_biquad

from . import kit, sound

PEAK_FULL = -6.0     # one-shot cues sit well under the usual -1 dBFS: scene volume stays below +6 dB over the ambience
PEAK_SOFT = -14.0


def _nrm(x):
    return x / max(float(np.max(np.abs(x))), 1e-9)


def _lp(x, f):
    return butter(x, "lowpass", f, 2)


def _mix(dur, items):
    out = np.zeros(n_of(dur))
    for s, t, g in items:
        add_at(out, s, t, g)
    return out


@lru_cache(maxsize=None)
def _ir(kind: str) -> np.ndarray:
    if kind == "behind_door":   # a small closed room heard through a door
        return reverb.synth_ir(0.5, 7421, stereo=False, predelay=0.006, lf_ratio=1.0, hf_ratio=0.3, early=8, early_span=0.02, tone_hi=3500)
    if kind == "hall":          # the big dark stacks
        return reverb.synth_ir(3.6, 7422, stereo=False, predelay=0.03, lf_ratio=1.1, hf_ratio=0.3, early=12, early_span=0.1, onset=0.05, tone_hi=6000)
    if kind == "horn":          # a PA horn in a tall hall: short slap and a long dark tail
        return reverb.synth_ir(1.6, 7423, stereo=False, predelay=0.04, lf_ratio=1.0, hf_ratio=0.3, early=6, early_span=0.12, tone_hi=4500)
    raise KeyError(kind)


def _wet(x, kind, wet, dry=1.0, cap=None):
    """Reverb; the tail is cut (smoothly) 0.8 s after the cue's own length so a file is never much longer than
    its moment (``cap`` = the dry length in seconds)."""
    y = reverb.reverb(x, _ir(kind), wet, dry)
    return kit.limit(y, cap + 0.8, 0.6) if cap is not None and len(y) > n_of(cap + 0.8) else y


def _pair(name, full_desc, soft_desc, fn):
    """Register ``name`` (Full) and ``name_soft`` (Soft) from ``fn(rng, soft) -> mono``."""
    sound(name, "sfx", full_desc, peak_db=PEAK_FULL)(lambda rng: fn(rng, False))
    sound(name + "_soft", "sfx", soft_desc, peak_db=PEAK_SOFT)(lambda rng: fn(rng, True))


# ---- M1 lamp_dip -----------------------------------------------------------------------------------

def _lamp_dip(rng, soft):
    d = 3.5
    n = n_of(d)
    t = time_axis(n)
    # the transformer hum sinks in pitch and level to an ember, holds, then recovers
    drop = 0.55 if soft else 1.0
    f = 100.0 * env.curve([(0, 1.0), (1.3, 1.0 - 0.38 * drop), (2.3, 1.0 - 0.38 * drop), (2.7, 1.0), (d, 1.0)], n, "cos")
    amp = env.curve([(0, 0.55), (0.2, 0.6), (1.3, 0.55 - 0.45 * drop), (2.3, 0.1), (2.55, 1.0), (2.8, 0.7), (d, 0.5)], n, "cos")
    ph = 2 * np.pi * np.cumsum(f) / SR
    hum = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph) + 0.12 * np.sin(5 * ph)
    hum = _lp(hum, 700 if soft else 1100) * amp
    out = _nrm(hum)
    if not soft:   # the bulb flaring back: one small, dry tick (the only highs in the cue)
        tick = _lp(kit.tick(rng, 2500, 6500, 10, t60=0.03, contact=0.0004, dur=0.08), 5000)
        add_at(out, _nrm(tick), 2.5, 0.35)
    return _wet(out, "behind_door", 0.1, cap=d)


_pair("lamp_dip", "M1 lamp that dies (3.5 s): the work lamp's transformer hum sinks in pitch and level to an ember, then flares back with a small bulb tick",
      "M1 lamp that dies, Soft: the same hum dip, shallower and rounder, no tick", _lamp_dip)


# ---- M2 knocks -------------------------------------------------------------------------------------

def _knocks(rng, soft):
    d = 4.0
    f_lp = 650 if soft else 1000
    out = np.zeros(n_of(d))
    for t0, g in ((0.35, 0.8), (1.05, 1.0), (1.75, 0.9)):    # three soft knocks from inside the Cell
        k = kit.knock(rng, 140, 1300, 9, t60=0.09, contact=0.003 if soft else 0.0018, dur=0.3, noise_amt=0.08)
        add_at(out, _lp(_nrm(k), f_lp), t0 + rng.uniform(-0.02, 0.02), g * (0.6 if soft else 1.0))
    out = _wet(out, "behind_door", 0.35)
    out = np.pad(out, (0, max(0, n_of(d) - len(out))))[:n_of(d)] if len(out) < n_of(d) else out
    kt = np.zeros(n_of(d))
    for t0, g in ((2.75, 0.7), (3.2, 0.9), (3.55, 0.5)):      # then the kettle ticking as it cools
        tk = _lp(kit.tick(rng, 1800, 5200, 10, t60=0.06, contact=0.0004, dur=0.12), 4500)
        add_at(kt, _nrm(tk), t0, g * (0.5 if soft else 1.0))
    return _wet(_mix(d, [(out[:n_of(d)], 0.0, 1.0), (kt, 0.0, 0.45)]), "behind_door", 0.12, cap=d)


_pair("knocks", "M2 knocks behind the door (4 s): three soft muffled wooden knocks from inside the Cell, then a kettle ticking as it cools",
      "M2 knocks, Soft: the same, quieter and more muffled, kettle ticks fainter", _knocks)


# ---- M3 frost_steps --------------------------------------------------------------------------------

def _frost_steps(rng, soft):
    d = 4.0
    n = n_of(d)
    src = noise.colored(n, rng, -3.0, 80, 1800)
    fc = np.exp(np.interp(np.arange(n) / SR, [0, 1.4, 2.6, d], np.log([240, 650, 520, 260])))
    who = tv_biquad(src, "bandpass", fc, 1.1, block=64)
    who = _lp(who, 1100) * env.curve([(0, 0), (1.5, 1), (2.3, 0.8), (d, 0)], n, "cos")
    out = _nrm(who) * (0.9 if soft else 1.0)
    if not soft:
        for t0, g in ((1.0, 0.4), (2.0, 0.3)):             # muffled steps on the far side of the pane
            st = _lp(kit.thump(110, 65, 0.2, 0.09), 350)
            add_at(out, _nrm(st), t0, g)
        m = n_of(0.16)
        sq = kit.creak(rng, 0.16, env.curve([(0, 260), (0.16, 380)], m), np.hanning(m), modal.glass(rng.uniform(1500, 2200), 0.1, 0.3), jitter=0.05, hiss=0.0)
        add_at(out, _lp(_nrm(sq), 3000), 3.3, 0.15)         # a faint cloth squeak, the "mark" being written
    return _wet(out, "hall", 0.18, cap=d)


_pair("frost_steps", "M3 shadow on the frost (4 s): a soft muffled whoosh as something passes behind the pane, two far footsteps, a faint squeak",
      "M3 shadow on the frost, Soft: only the soft whoosh, lower", _frost_steps)


# ---- M4 roll_call ----------------------------------------------------------------------------------

def _horn_note(f0, f1, dur, rng, soft):
    n = n_of(dur)
    t = time_axis(n)
    f = np.geomspace(f0, f1, n) * (1.0 + 0.012 * np.sin(2 * np.pi * 5.2 * t))
    x = osc.saw(f, n)
    x = x - 0.4 * osc.saw(f * 2.005, n)
    x = _lp(x, 1500 if soft else 2300)
    x = butter(x, "highpass", 300, 2)
    return x * env.curve([(0, 0), (0.05, 1), (dur * 0.7, 0.8), (dur, 0)], n, "cos")


def _roll_call(rng, soft):
    d = 9.0
    n = n_of(d)
    t = time_axis(n)
    on = env.curve([(0, 0), (0.3, 0), (0.45, 1), (5.4, 1), (5.7, 0.35), (d, 0.0)], n, "lin")
    hum = (np.sin(2 * np.pi * 100 * t) + 0.5 * np.sin(2 * np.pi * 200 * t)) * on * 0.05
    out = hum
    # the count: "forty" is two pitched horn syllables, "forty-one" three, the last one falling away; then nothing
    def say(t0, notes):
        tt = t0
        for f0, f1, dd in notes:
            add_at(out, _horn_note(f0, f1, dd, rng, soft), tt, 1.0)
            tt += dd + 0.07
    say(1.3, [(392.0, 370.0, 0.30), (330.0, 300.0, 0.36)])
    say(3.2, [(392.0, 372.0, 0.30), (349.0, 330.0, 0.24), (294.0, 247.0, 0.75)])
    if not soft:   # old horn crackle in the open channel
        cr = butter(noise.dust(n, 55 * on, rng, heavy_tail=0.6), "bandpass", (900, 3200), 2)
        out = out + 0.08 * _nrm(cr) * on
    # after 41 the line stays open for a long hiss (band-limited and soft), then the horn clicks off
    h0, h1 = (5.8, 7.6) if soft else (5.8, 8.6)
    hn = noise.colored(n, rng, -2.0, 600, 3200)
    hiss = hn * env.curve([(0, 0), (h0, 0), (h0 + 0.7, 1), (h1 - 0.9, 0.8), (h1, 0), (d, 0)], n, "cos")
    out = out + (0.10 if soft else 0.16) * _nrm(hiss) / max(1e-9, 1.0) * 1.0
    if not soft:
        click = _lp(kit.relay(rng, 0.4), 4000)
        add_at(out, _nrm(click), 8.7, 0.12)
    return _wet(out, "horn", 0.3, cap=d)


_pair("roll_call", "M4 roll call (9 s): an old PA horn sounds two spoken-rhythm tone phrases (a count: two notes, then three) with crackle, then stops; a long soft hiss and a click. No voice, tones only",
      "M4 roll call, Soft: the same count in a rounder horn, no crackle, a shorter fainter hiss, no click", _roll_call)


# ---- M5 steps_above --------------------------------------------------------------------------------

def _steps_above(rng, soft):
    d = 5.0
    out = np.zeros(n_of(d))
    for i, (t0, g, lp) in enumerate(((0.5, 0.7, 260), (1.7, 0.9, 300), (2.9, 1.0, 300), (4.1, 0.7, 240))):
        th = _lp(kit.thump(100, 62, 0.28, 0.14), lp * (0.8 if soft else 1.0))
        plank = _lp(kit.knock(rng, 120, 900, 8, t60=0.1, contact=0.003, dur=0.25, noise_amt=0.05), 700)
        m = n_of(0.5)
        cr = kit.creak(rng, 0.5, env.curve([(0, 30), (0.5, 55)], m), env.curve([(0, 0), (0.2, 1), (0.5, 0)], m, "cos"),
                       modal.wood(rng, 100, 700, 8, 0.15), jitter=0.12, hiss=0.0)
        add_at(out, _nrm(th), t0, g * 0.9)
        add_at(out, _nrm(plank), t0 + 0.02, g * 0.35)
        add_at(out, _lp(_nrm(cr), 900), t0 + 0.15, g * (0.12 if soft else 0.2))
        if not soft:   # fine dust shaken loose
            for _ in range(16):
                add_at(out, _lp(kit.tick(rng, 1800, 4800, 6, t60=0.02, contact=0.0004, dur=0.05), 4200), t0 + 0.2 + rng.uniform(0, 0.8) ** 1.5, 0.05 * g * rng.uniform(0.3, 1))
    return _wet(out, "hall", 0.28, cap=d)


_pair("steps_above", "M5 steps above (5 s): four slow footfalls cross the ceiling, each with a plank creak and a little dust",
      "M5 steps above, Soft: lower, rounder footfalls, no dust", _steps_above)


# ---- M6 echo_chime ---------------------------------------------------------------------------------

def _echo_chime(rng, soft):
    d = 5.0
    out = np.zeros(n_of(d))
    notes = (("E5", 0.0, 1.0), ("B5", 0.95, 0.8)) if soft else (("E5", 0.0, 1.0), ("B5", 0.95, 0.85), ("F#5", 1.9, 0.6))
    for nn, t0, g in notes:
        f = music.hz(nn)
        a = music.glass(f, 1.0, rng, dur=4.0, t60=2.8, attack=0.35, bright=0.25)
        b = music.glass(f * 1.0016, 1.0, rng, dur=4.0, t60=2.8, attack=0.35, bright=0.25)
        add_at(out, 0.6 * (a + 0.7 * b), t0, g)
    out = _lp(out, 4500 if soft else 6500)
    return _wet(out, "hall", 0.55, 0.8, cap=d)


_pair("echo_chime", "M6 echo at the rail end (5 s): three soft swelled glass notes (E, B, F sharp) answering in a long dark hall",
      "M6 echo at the rail end, Soft: two notes, rounder", _echo_chime)
