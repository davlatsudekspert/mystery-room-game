"""Chapter 3 score, the Underground Facility (Level -2 of the 1979 Meridian Institute).

Same family as Chapter 2 (analog pads, tine e-piano, tape wow, warm hall) with its own
colour: underground, crystalline and resonant. Glass-tube bells with a slightly detuned
twin (so every note shimmers), an overtone choir that breathes through the harmonic
series of E (the Choir's tubes), open fifths (3:2, the figure of the final puzzle) and a
low, rounded pulse at 48 beats a minute (Strand: "My heart keeps the count").

``music_underground``: E Dorian / Aeolian with Lydian colours, 8 sections of 20 s
(16 beats at 48 BPM) = 160 s.

``music_underground_finale``: the Array answers and the 1979 staff are heard. E major
with a borrowed minor iv: a tender bell theme doubled by the electric piano over warm
strings, a held E (the Array's single note) under everything, a slow cascade of lights
rising up the shaft, and a faint pulse that returns at the loop point. 8 sections of 10 s
= 80 s.

There is deliberately no hiss layer in either cue: the tape character comes from wow and
flutter only, so no noise floor can ever be heard under the music.

``AudioManager.music()`` loops every music stream, so both cues are seamless loops: notes
and reverb tails wrap around the loop point, continuous oscillators use loop-periodic
frequencies and the wow LFOs fit the loop."""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from synth import env, modal, music, osc, reverb
from synth.core import SR, n_of, time_axis
from synth.filters import biquad
from synth.loops import periodic_freq
from synth.music import Track, hz

from . import sound
from .music_archive import _epiano, _pad_chords, _tape_wow, _tremolo
from .music_tracks import _bass, _celesta_with_echo, _master

# ------------------------------------------------------------------------------------------
# music_underground: 48 BPM, 16 beats (20 s) per chord, 8 chords = 160 s
# ------------------------------------------------------------------------------------------
UG_BEAT = 60.0 / 48.0
UG_SECTION = 16 * UG_BEAT
UG_EIGHTH = UG_BEAT / 2.0
UG_CHORDS = [  # (bass, pad voicing)
    ("E2", ["B3", "E4", "F#4", "B4"]),    # Esus2 (open fifths)
    ("C2", ["E3", "G3", "B3", "F#4"]),    # Cmaj7(#11)
    ("D2", ["F#3", "A3", "C#4", "E4"]),   # Dmaj9
    ("B1", ["F#3", "A3", "D4", "E4"]),    # Bm11
    ("G2", ["B3", "D4", "F#4", "A4"]),    # Gmaj9
    ("A2", ["E3", "F#3", "B3", "C#4"]),   # A6/9
    ("F#2", ["E3", "A3", "B3", "C#4"]),   # F#m11
    ("B1", ["E3", "A3", "B3", "F#4"]),    # B7sus4 -> back to Esus2
]
UG_ARP_GAIN = [0.0, 0.55, 0.85, 1.0, 1.0, 0.9, 0.6, 0.0]
UG_PULSE_GAIN = [0.0, 0.55, 0.85, 1.0, 1.0, 0.9, 0.65, 0.0]
UG_ARP_PATTERN = [0, 2, 1, 3, 2, 1, 3, 2, 0, 3, 1, 2, 3, 1, 2, 0]
# (section, [(offset in section, note, velocity), ...], instrument); every note is a chord tone
UG_PHRASES = [
    (0, [(3.0, "B4", .50), (4.25, "E5", .45), (5.5, "F#5", .45), (8.0, "B4", .40)], "tube"),
    (1, [(3.0, "B4", .50), (4.25, "E5", .45), (5.5, "G5", .45), (7.0, "F#5", .40), (9.5, "E5", .40)], "tube"),
    (2, [(2.5, "A4", .50), (3.75, "C#5", .45), (5.0, "E5", .45), (6.25, "F#5", .45), (11.25, "A5", .35)], "tube"),
    (3, [(3.0, "D5", .42), (4.25, "B4", .40), (5.5, "A4", .40), (8.0, "F#4", .38)], "epiano"),
    (4, [(2.5, "D5", .50), (3.75, "F#5", .45), (5.0, "A5", .45), (6.25, "G5", .42), (10.0, "B4", .38)], "tube"),
    (5, [(3.0, "C#5", .45), (4.25, "E5", .45), (5.5, "F#5", .45), (6.75, "B5", .42), (11.0, "A4", .36)], "tube"),
    (6, [(2.5, "C#5", .45), (3.75, "A4", .40), (5.0, "B4", .42), (6.25, "E5", .42), (9.0, "C#5", .38)], "epiano"),
    (7, [(3.0, "F#5", .45), (4.25, "E5", .42), (5.5, "B4", .42), (8.0, "A4", .40), (12.0, "F#4", .34)], "tube"),
]
UG_GLINTS = [(14.0, "E6"), (33.5, "G6"), (55.0, "A6"), (94.0, "F#6"), (113.0, "C#6"), (152.0, "F#6")]
UG_SWELLS = [(66.0, "F#4", 11.0, 0.13), (123.0, "C#5", 12.0, 0.12)]  # bowed glass: (time, note, length, gain)

# ------------------------------------------------------------------------------------------
# music_underground_finale: 48 BPM, 8 beats (10 s) per chord, 8 chords = 80 s
# ------------------------------------------------------------------------------------------
UF_SECTION = 8 * UG_BEAT
UF_CHORDS = [  # (bass, pad voicing, pad gain)
    ("E2", ["B3", "E4", "F#4", "G#4"], 0.11),     # Eadd9
    ("C#2", ["G#3", "B3", "E4", "F#4"], 0.12),    # C#m11
    ("A2", ["E3", "G#3", "B3", "C#4"], 0.14),     # Amaj9
    ("F#2", ["E3", "A3", "B3", "C#4"], 0.16),     # F#m11
    ("A2", ["E3", "G#3", "B3", "D#4"], 0.18),     # Amaj7(#11), the light
    ("A2", ["E3", "A3", "C4", "F#4"], 0.17),      # Am6 (borrowed minor iv)
    ("G#2", ["E3", "B3", "E4", "G#4"], 0.14),     # E/G#
    ("B1", ["E3", "A3", "B3", "F#4"], 0.12),      # B7sus4 -> Eadd9
]
UF_THEME = [  # (time in section, note, velocity); the bell theme, doubled an octave down by the e-piano in the middle
    (0, [(1.0, "B5", .55), (2.5, "G#5", .50), (3.75, "F#5", .50), (5.0, "E5", .50), (7.5, "B4", .45)]),
    (1, [(1.0, "E5", .50), (2.5, "G#5", .50), (3.75, "F#5", .45), (5.0, "E5", .45), (7.5, "B4", .42)]),
    (2, [(1.0, "C#6", .55), (2.5, "B5", .50), (3.75, "G#5", .50), (5.0, "E5", .50), (7.5, "C#5", .45)]),
    (3, [(1.0, "A5", .50), (2.5, "C#6", .50), (3.75, "B5", .50), (5.0, "A5", .45), (7.5, "E5", .45)]),
    (4, [(1.0, "E6", .62), (2.5, "C#6", .58), (3.75, "B5", .55), (5.0, "D#6", .60), (7.0, "B5", .50), (8.5, "G#5", .45)]),
    (5, [(1.0, "C6", .55), (2.5, "A5", .50), (3.75, "F#5", .50), (5.0, "E5", .48), (7.5, "C5", .42)]),
    (6, [(1.0, "G#5", .50), (2.5, "B5", .50), (3.75, "G#5", .45), (5.0, "E5", .45), (7.5, "B4", .40)]),
    (7, [(1.0, "F#5", .48), (2.5, "E5", .45), (3.75, "B4", .45), (5.5, "A4", .40), (7.0, "B4", .38)]),
]
UF_CASCADE = ["E5", "G#5", "B5", "E6", "G#6", "B6", "E7"]  # the lights rising up the shaft, E major tones only


# ---- instruments -------------------------------------------------------------------------

@lru_cache(maxsize=None)
def _cavern() -> np.ndarray:
    """A long, dark stone hall under the rock: slow build-up, bright early reflections, warm tail."""
    return reverb.synth_ir(5.4, 7301, stereo=True, predelay=0.04, lf_ratio=1.25, hf_ratio=0.38, early=18,
                           early_span=0.10, onset=0.07, tone_hi=7500)


def _tube(f: float, vel: float, rng, dur: float = 6.0) -> np.ndarray:
    """A struck crystal resonance tube: a near-harmonic stack (1, 2, 3, 4) with a faintly detuned twin of
    the fundamental, so each note shimmers slowly, a few glass partials (2.32, 4.25, 6.63) for the crystal
    ring, and a soft mallet. Higher notes die faster."""
    bright = 0.6 + 0.6 * vel
    t60 = 3.6 * (523.0 / max(f, 130.0)) ** 0.3
    md = modal.Modes(f * np.array([1.0, 1.0016, 2.0, 2.32, 3.0, 4.25, 6.63]),
                     t60 * np.array([1.0, 0.9, 0.6, 0.4, 0.3, 0.2, 0.1]),
                     np.array([1.0, 0.55, 0.30 * bright, 0.20 * bright, 0.14 * bright, 0.09 * bright, 0.05 * bright]))
    x = modal.strike(md, dur, contact=0.0010 - 0.0004 * vel, rng=rng)
    return vel * x / max(np.max(np.abs(x)), 1e-9)


def _pulse(f: float, dur: float = 1.8) -> np.ndarray:
    """A low, rounded pulse: a sine that settles from just above its pitch, with short-lived 2nd and 3rd
    harmonics so that phone speakers (nothing below ~150 Hz) still carry it."""
    n = n_of(dur)
    t = time_axis(n)
    fr = f * (1.0 + 0.05 * np.exp(-t / 0.05))
    ph = 2.0 * np.pi * osc.phase_cycles(fr, n)
    x = np.sin(ph) + 0.7 * np.sin(2.0 * ph) * np.exp(-t / 0.30) + 0.4 * np.sin(3.0 * ph) * np.exp(-t / 0.18)
    return x * env.ar(n, 0.014, 0.9)


def _bowed_glass(f: float, dur: float, rng, attack: float, release: float, bright: float = 0.35) -> np.ndarray:
    """A glass harmonica note: slowly bowed in, held with a faint wander, slowly let go (stereo)."""
    n = n_of(dur)
    out = np.zeros((2, n))
    for ratio, a in ((1.0, 1.0), (2.0, 0.40 * bright / 0.35), (3.0, 0.18 * bright / 0.35), (4.25, 0.09 * bright / 0.35)):
        for c in range(2):
            fr = osc.vibrato(f * ratio * (1.0 + rng.uniform(-0.0014, 0.0014)), n, rng.uniform(0.1, 0.25), 2.5,
                             rng.uniform(0, 1))
            am = 1.0 + 0.2 * np.sin(2 * np.pi * (np.arange(n) / SR * rng.uniform(0.12, 0.4) + rng.uniform(0, 1)))
            out[c] += a * am * osc.sine(fr, n, rng.uniform(0, 1))
    return out * env.swell(n, attack, release) / 1.4


def _overtone_choir(n: int, L: float, rng, root: str = "E2", partials=None) -> np.ndarray:
    """The Choir's tubes heard as one breathing organ: the even and 3rd partials of E (E, B, E, B ...) swell in
    and out at their own slow rates. Every frequency and rate fits the loop; only fifths and octaves of E are
    used, so it agrees with every chord of the cue."""
    if partials is None:
        partials = ((2, 1.0, 3), (3, 0.8, 5), (4, 0.7, 4), (6, 0.5, 7), (8, 0.4, 6), (12, 0.22, 9),
                    (16, 0.12, 8), (24, 0.06, 11))
    t = time_axis(n)
    f0 = hz(root)
    out = np.zeros((2, n))
    for k, a, rate in partials:
        for c in range(2):
            f = periodic_freq(f0 * k * (1.0 + rng.uniform(-0.0006, 0.0006)), L)
            slow = (0.5 - 0.5 * np.cos(2 * np.pi * (rate / L) * t + rng.uniform(0, 2 * np.pi))) ** 2
            out[c] += a * slow * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi))
    return out


def _held_note(n: int, L: float, rng, root: str = "E3") -> np.ndarray:
    """The Array's single held note: E and its octave and fifth, breathing a little, never stopping."""
    t = time_axis(n)
    f0 = hz(root)
    out = np.zeros((2, n))
    for ratio, a, rate in ((1.0, 1.0, 2), (2.0, 0.55, 3), (3.0, 0.3, 4), (4.0, 0.18, 5)):
        for c in range(2):
            f = periodic_freq(f0 * ratio * (1.0 + rng.uniform(-0.0005, 0.0005)), L)
            breath = 0.8 + 0.2 * np.sin(2 * np.pi * (rate / L) * t + rng.uniform(0, 2 * np.pi))
            out[c] += a * breath * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi))
    return out


def _pulse_layer(dry: Track, times_gain, roots, rng, gain: float) -> None:
    """Pulses on their own track (not through the hall, so each stays distinct)."""
    cache: dict[str, np.ndarray] = {}
    for t, g, root in zip(times_gain[0], times_gain[1], roots):
        if g <= 0:
            continue
        if root not in cache:
            cache[root] = _pulse(hz(root))
        dry.add(t + rng.uniform(-0.01, 0.01), cache[root], gain * g * rng.uniform(0.92, 1.0))


# ---- music_underground layers --------------------------------------------------------------

def _ug_pads(tr: Track, rng) -> None:
    _pad_chords(tr, UG_SECTION, [v for _, v in UG_CHORDS], rng, [0.14] * len(UG_CHORDS), attack=5.0, release=5.5,
                overlap=2.5, cutoff=930, bright_cutoff=2100, air=0.11)
    _bass(tr, UG_SECTION, [b for b, _ in UG_CHORDS], rng, gain=0.11)


def _ug_tube_arp(tr: Track, rng) -> None:
    """Slow tube-bell arpeggio on the off-beat (the pulse is on the beat), with a dotted tape echo."""
    cache: dict[int, np.ndarray] = {}
    for i, (_, voicing) in enumerate(UG_CHORDS):
        if UG_ARP_GAIN[i] <= 0:
            continue
        for k in range(16):
            if rng.uniform() < 0.18 and UG_ARP_GAIN[i] < 1.0:  # a few gaps, so the pattern breathes
                continue
            m = music.midi(voicing[UG_ARP_PATTERN[k]]) + 12
            if m not in cache:
                cache[m] = _tube(hz(m), 0.55, rng, 5.0)
            t = i * UG_SECTION + k * UG_BEAT + UG_EIGHTH + rng.uniform(-0.01, 0.01)
            g = 0.5 * UG_ARP_GAIN[i] * rng.uniform(0.8, 1.0) * (1.0 if k % 4 == 0 else 0.75)
            p = 0.4 * np.sin(2 * np.pi * k / 16.0)
            tr.add(t, cache[m], g, p)
            echo = cache[m]
            for e, eg in ((1, 0.30), (2, 0.11)):
                echo = biquad(echo, "lowpass", 2400 - 600 * e, 0.6)
                tr.add(t + 3 * UG_EIGHTH * e, echo, g * eg, -p * (1.4 if e % 2 else 0.8))


def _ug_melody(tr: Track, rng) -> None:
    for sec, notes, inst in UG_PHRASES:
        for off, note, vel in notes:
            t = sec * UG_SECTION + off + rng.uniform(-0.03, 0.03)
            pos = rng.uniform(0.1, 0.4) * (1 if (sec + len(note)) % 2 else -1)
            if inst == "tube":
                _celesta_with_echo(tr, t, note, vel, rng, pos, echo_s=3 * UG_EIGHTH, gain=1.05, inst=_tube)
            else:
                x = _tremolo(_epiano(hz(note), vel, rng, 4.0), rng)
                tr.add(t, x, 0.5)
                tr.add(t + 3 * UG_EIGHTH, biquad(x, "lowpass", 2000, 0.6), 0.11)
    for t, note in UG_GLINTS:
        tr.add(t, music.music_box(hz(note), 0.5, rng, 4.0), 0.26, rng.uniform(-0.55, 0.55))
    for t, note, d, g in UG_SWELLS:
        tr.add(t, _bowed_glass(hz(note), d, rng, attack=d * 0.4, release=d * 0.45), g)


def _ug_choir(tr: Track, rng) -> None:
    tr.buf += 0.020 * _overtone_choir(tr.n, UG_SECTION * 8, rng)
    # a low, loop-periodic drone under everything (E2 + B2: the 3:2 fifth)
    L = UG_SECTION * 8
    dr = music.drone(periodic_freq(hz("E2"), L), tr.n, rng, harmonics=(1.0, 0.5, 0.2, 0.08), breath_rate=5.0 / L,
                     depth=0.5)
    dr += 0.5 * music.drone(periodic_freq(hz("B2"), L), tr.n, rng, breath_rate=3.0 / L, depth=0.5)
    tr.buf += 0.014 * biquad(dr, "lowpass", 500)


def _ug_pulse(dry: Track, rng) -> None:
    times, gains, roots = [], [], []
    for i, (bass, _) in enumerate(UG_CHORDS):
        for k in range(8):
            times.append(i * UG_SECTION + k * 2 * UG_BEAT)
            gains.append(UG_PULSE_GAIN[i] * (1.0 if k % 2 == 0 else 0.7))
            roots.append(bass)
    _pulse_layer(dry, (times, gains), roots, rng, 0.33)


UG_WET_LAYERS = (_ug_pads, _ug_tube_arp, _ug_melody, _ug_choir)


@sound("music_underground", "music",
       "Underground underscore: slow E Dorian pads, glass-tube bells with a shimmering twin, a low pulse at 48 BPM, "
       "an overtone choir and tape wow",
       loop=True, lufs=-20.0)
def music_underground(rng):
    L = UG_SECTION * len(UG_CHORDS)
    tr = Track(L, loop=True)
    for layer in UG_WET_LAYERS:
        layer(tr, rng)
    dry = Track(L, loop=True)
    _ug_pulse(dry, rng)
    out = reverb.reverb_circular(tr.buf, _cavern(), wet=0.5, dry=0.78)
    out += reverb.reverb_circular(dry.buf, reverb.preset("room_amb", True), wet=0.3, dry=1.0)
    out = _tape_wow(out, L, rng, depth=0.0010)
    return _master(out, 10000.0)


# ---- music_underground_finale layers -----------------------------------------------------------

def _uf_pads(tr: Track, rng) -> None:
    _pad_chords(tr, UF_SECTION, [v for _, v, _ in UF_CHORDS], rng, [g for _, _, g in UF_CHORDS], attack=3.2,
                release=3.8, overlap=2.0, cutoff=1300, bright_cutoff=2800, voices=5, air=0.12)
    _bass(tr, UF_SECTION, [b for b, _, _ in UF_CHORDS], rng, gain=0.15, overlap=2.0)


def _uf_theme(tr: Track, rng) -> None:
    for sec, notes in UF_THEME:
        for off, note, vel in notes:
            t = sec * UF_SECTION + off + rng.uniform(-0.02, 0.02)
            pos = 0.2 * np.sin(t * 0.7)
            _celesta_with_echo(tr, t, note, vel, rng, pos, echo_s=3 * UG_EIGHTH, gain=1.0)
            if 2 <= sec < 7:  # the e-piano joins an octave down through the heart of the theme
                x = _tremolo(_epiano(hz(note) / 2.0, vel * 0.9, rng, 4.0), rng, rate=3.8, depth=0.2)
                tr.add(t + 0.01, x, 0.35)
    # a tube bell joins at the peak, so the crystal colour of the chapter is heard in the light
    for t, note, vel in ((41.0, "E6", .45), (45.0, "D#6", .42)):
        tr.add(t + 0.03, _tube(hz(note), vel, rng, 6.0), 0.5, rng.uniform(-0.3, 0.3))


def _uf_light(tr: Track, rng) -> None:
    """The light pouring out of the shaft: soft glass swells at the peak and at the minor iv, music-box glints,
    and the lights rising: a slow cascade of glass notes, left to right."""
    for t, notes, g in ((42.2, ("B5", "E6"), 0.30), (52.2, ("A5", "C6"), 0.24)):
        for nn in notes:
            tr.add(t, music.glass(hz(nn), 0.5, rng, dur=6.0, t60=4.0, attack=1.6, bright=0.25), g,
                   rng.uniform(-0.4, 0.4))
    for t, note in ((30.0, "E6"), (78.0, "G#6")):
        tr.add(t, music.music_box(hz(note), 0.5, rng, 4.0), 0.26, rng.uniform(-0.5, 0.5))
    tr.add(40.5, _bowed_glass(hz("E4"), 9.0, rng, attack=3.5, release=4.0), 0.12)
    for k, nn in enumerate(UF_CASCADE):
        t = 62.5 + 0.85 * k
        pos = -0.6 + 1.2 * k / (len(UF_CASCADE) - 1)
        g = music.glass(hz(nn), 0.5, rng, dur=5.0, t60=3.5, bright=0.35)
        tr.add(t, g, 0.18, pos)
        tr.add(t + 3 * UG_EIGHTH, biquad(g, "lowpass", 2600, 0.6), 0.05, -pos)


def _uf_held(tr: Track, rng) -> None:
    L = UF_SECTION * len(UF_CHORDS)
    tr.buf += 0.013 * _held_note(tr.n, L, rng)
    dr = music.drone(periodic_freq(hz("E2"), L), tr.n, rng, harmonics=(1.0, 0.5, 0.2, 0.08), breath_rate=2.0 / L,
                     depth=0.5)
    tr.buf += 0.016 * biquad(dr, "lowpass", 400)


def _uf_pulse(dry: Track, rng) -> None:
    """The pulse is only a memory here: faint at the start and end of the loop, gone through the light."""
    sec_gain = [0.7, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5]
    times, gains, roots = [], [], []
    for i, (bass, _, _) in enumerate(UF_CHORDS):
        for k in range(4):
            times.append(i * UF_SECTION + (k * 2 + 1) * UG_BEAT)  # off the loop point: no onset at the seam
            gains.append(sec_gain[i] * (1.0 if k % 2 == 0 else 0.7))
            roots.append(bass)
    _pulse_layer(dry, (times, gains), roots, rng, 0.40)


UF_WET_LAYERS = (_uf_pads, _uf_theme, _uf_light, _uf_held)


@sound("music_underground_finale", "music",
       "Underground finale: the Array answers; a tender bell theme with e-piano over warm E major strings, a held E, "
       "lights rising, a borrowed minor iv",
       loop=True, lufs=-20.0)
def music_underground_finale(rng):
    L = UF_SECTION * len(UF_CHORDS)
    tr = Track(L, loop=True)
    for layer in UF_WET_LAYERS:
        layer(tr, rng)
    dry = Track(L, loop=True)
    _uf_pulse(dry, rng)
    out = reverb.reverb_circular(tr.buf, reverb.preset("hall", True), wet=0.5, dry=0.75)
    out += reverb.reverb_circular(dry.buf, reverb.preset("room_amb", True), wet=0.3, dry=1.0)
    out = _tape_wow(out, L, rng, depth=0.0008)
    return _master(out, 11000.0)
