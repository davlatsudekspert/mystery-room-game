"""Chapter 4 score, the Array Hall (the unnumbered floor, the Experiment of 1998).

Same family as Chapters 2 and 3 (analog pads, glass-tube bells, tape wow, a warm hall) with its own centre: the Core's
note A (220 Hz), and the idea of the beat: two nearly equal pitches that slowly drift apart and together. Bells come in
pairs a few cents apart, a low pulse counts at 48 beats a minute, an overtone organ on A breathes underneath.

``music_array_hall``: A Dorian with Lydian colours, 8 sections of 20 s (16 beats at 48 BPM) = 160 s.

``music_array_hall_reversal``: the hall runs time back; the pulse doubles to 96 a minute, the bells fall in descending
runs, bowed glass swells climb, and the last two sections open out into a held A. 8 sections of 10 s = 80 s.

No hiss layer in either cue (the tape character is wow only). ``AudioManager.music()`` loops every music stream, so both
are seamless loops: notes and tails wrap around the loop point, continuous oscillators use loop-periodic frequencies."""
from __future__ import annotations

import numpy as np

from synth import music, reverb
from synth.filters import biquad
from synth.loops import periodic_freq
from synth.music import Track, hz

from . import sound
from .music_archive import _pad_chords, _tape_wow
from .music_tracks import _bass, _celesta_with_echo, _master
from .music_underground import (UG_BEAT, UG_EIGHTH, _bowed_glass, _cavern, _held_note, _overtone_choir, _pulse_layer,
                                _tube)

SECTION = 16 * UG_BEAT
CHORDS = [  # (bass, pad voicing)
    ("A1", ["E3", "A3", "B3", "E4"]),    # Asus2
    ("F2", ["A3", "C4", "E4", "G4"]),    # Fmaj7#... F6/9-ish open (A C E G = Am7 over F)
    ("G2", ["B3", "D4", "F#4", "A4"]),   # Gmaj9
    ("D2", ["A3", "D4", "E4", "F#4"]),   # Dsus2/6
    ("E2", ["B3", "E4", "F#4", "A4"]),   # E11
    ("C2", ["G3", "C4", "E4", "B4"]),    # Cmaj7
    ("D2", ["A3", "D4", "F#4", "B4"]),   # D6/9
    ("E2", ["B3", "D4", "E4", "A4"]),    # E7sus4 -> Asus2
]
ARP_GAIN = [0.0, 0.55, 0.85, 1.0, 1.0, 0.9, 0.6, 0.0]
PULSE_GAIN = [0.0, 0.55, 0.85, 1.0, 1.0, 0.9, 0.65, 0.0]
ARP_PATTERN = [0, 2, 1, 3, 2, 1, 3, 2, 0, 3, 1, 2, 3, 1, 2, 0]
# (section, [(offset in section, note, velocity)]); every note is a chord tone. Each bell is doubled a few cents sharp (the beat)
PHRASES = [
    (0, [(3.0, "E5", .50), (4.25, "A5", .45), (5.5, "B5", .45), (8.0, "E5", .40)]),
    (1, [(3.0, "E5", .50), (4.25, "G5", .45), (5.5, "A5", .45), (7.0, "G5", .40), (9.5, "E5", .40)]),
    (2, [(2.5, "D5", .50), (3.75, "F#5", .45), (5.0, "A5", .45), (6.25, "B5", .45), (11.25, "F#5", .35)]),
    (3, [(3.0, "A5", .42), (4.25, "F#5", .40), (5.5, "E5", .40), (8.0, "D5", .38)]),
    (4, [(2.5, "F#5", .50), (3.75, "A5", .45), (5.0, "B5", .45), (6.25, "A5", .42), (10.0, "E5", .38)]),
    (5, [(3.0, "G5", .45), (4.25, "E5", .45), (5.5, "B5", .45), (6.75, "G5", .42), (11.0, "C5", .36)]),
    (6, [(2.5, "F#5", .45), (3.75, "D5", .40), (5.0, "B4", .42), (6.25, "F#5", .42), (9.0, "A5", .38)]),
    (7, [(3.0, "A5", .45), (4.25, "G5", .42), (5.5, "E5", .42), (8.0, "D5", .40), (12.0, "A4", .34)]),
]
GLINTS = [(14.0, "A6"), (33.5, "E6"), (55.0, "B6"), (94.0, "F#6"), (113.0, "E6"), (152.0, "A6")]
SWELLS = [(66.0, "E4", 11.0, 0.12), (123.0, "A4", 12.0, 0.12)]


def _pads(tr: Track, rng) -> None:
    _pad_chords(tr, SECTION, [v for _, v in CHORDS], rng, [0.14] * len(CHORDS), attack=5.0, release=5.5,
                overlap=2.5, cutoff=930, bright_cutoff=2100, air=0.11)
    _bass(tr, SECTION, [b for b, _ in CHORDS], rng, gain=0.11)


def _arp(tr: Track, rng) -> None:
    """Slow tube-bell arpeggio on the off-beat; each note answered a moment later by a twin a few cents sharp."""
    cache: dict[int, np.ndarray] = {}
    for i, (_, voicing) in enumerate(CHORDS):
        if ARP_GAIN[i] <= 0:
            continue
        for k in range(16):
            if rng.uniform() < 0.18 and ARP_GAIN[i] < 1.0:
                continue
            m = music.midi(voicing[ARP_PATTERN[k]]) + 12
            if m not in cache:
                cache[m] = _tube(hz(m), 0.55, rng, 5.0)
            t = i * SECTION + k * UG_BEAT + UG_EIGHTH + rng.uniform(-0.01, 0.01)
            g = 0.5 * ARP_GAIN[i] * rng.uniform(0.8, 1.0) * (1.0 if k % 4 == 0 else 0.75)
            p = 0.4 * np.sin(2 * np.pi * k / 16.0)
            tr.add(t, cache[m], g, p)
            echo = cache[m]
            for e, eg in ((1, 0.30), (2, 0.11)):
                echo = biquad(echo, "lowpass", 2400 - 600 * e, 0.6)
                tr.add(t + 3 * UG_EIGHTH * e, echo, g * eg, -p * (1.4 if e % 2 else 0.8))


def _melody(tr: Track, rng) -> None:
    for sec, notes in PHRASES:
        for off, note, vel in notes:
            t = sec * SECTION + off + rng.uniform(-0.03, 0.03)
            pos = rng.uniform(0.1, 0.4) * (1 if (sec + len(note)) % 2 else -1)
            _celesta_with_echo(tr, t, note, vel, rng, pos, echo_s=3 * UG_EIGHTH, gain=1.0, inst=_tube)
            # the twin: a few cents sharp, a little later and softer, on the other side: the slow beat
            tr.add(t + 0.02, _tube(hz(note) * 1.0029, vel * 0.7, rng, 5.0), 0.32, -pos)
    for t, note in GLINTS:
        tr.add(t, music.music_box(hz(note), 0.5, rng, 4.0), 0.26, rng.uniform(-0.55, 0.55))
    for t, note, d, g in SWELLS:
        tr.add(t, _bowed_glass(hz(note), d, rng, attack=d * 0.4, release=d * 0.45), g)


def _organ(tr: Track, rng) -> None:
    L = SECTION * len(CHORDS)
    tr.buf += 0.020 * _overtone_choir(tr.n, L, rng, root="A1")
    dr = music.drone(periodic_freq(hz("A1"), L), tr.n, rng, harmonics=(1.0, 0.5, 0.2, 0.08), breath_rate=5.0 / L, depth=0.5)
    dr += 0.5 * music.drone(periodic_freq(hz("E2"), L), tr.n, rng, breath_rate=3.0 / L, depth=0.5)
    tr.buf += 0.014 * biquad(dr, "lowpass", 500)


def _pulse(dry: Track, rng) -> None:
    times, gains, roots = [], [], []
    for i, (bass, _) in enumerate(CHORDS):
        for k in range(8):
            times.append(i * SECTION + k * 2 * UG_BEAT)
            gains.append(PULSE_GAIN[i] * (1.0 if k % 2 == 0 else 0.7))
            roots.append(bass)
    _pulse_layer(dry, (times, gains), roots, rng, 0.33)


@sound("music_array_hall", "music",
       "Array Hall underscore: slow A Dorian pads, tube bells in pairs a few cents apart (the beat), a low pulse at "
       "48 BPM, an overtone organ on A and tape wow",
       loop=True, lufs=-20.0)
def music_array_hall(rng):
    L = SECTION * len(CHORDS)
    tr = Track(L, loop=True)
    for layer in (_pads, _arp, _melody, _organ):
        layer(tr, rng)
    dry = Track(L, loop=True)
    _pulse(dry, rng)
    out = reverb.reverb_circular(tr.buf, _cavern(), wet=0.5, dry=0.78)
    out += reverb.reverb_circular(dry.buf, reverb.preset("room_amb", True), wet=0.3, dry=1.0)
    out = _tape_wow(out, L, rng, depth=0.0010)
    return _master(out, 10000.0)


# ---- the reversal -----------------------------------------------------------------------------------

RSEC = 8 * UG_BEAT
RCHORDS = [  # (bass, pad voicing, pad gain): the night's chords fall, then open into A
    ("A1", ["E3", "A3", "C4", "E4"], 0.12),     # Am
    ("G2", ["D3", "G3", "B3", "D4"], 0.13),     # G
    ("F2", ["C3", "F3", "A3", "C4"], 0.14),     # F
    ("E2", ["B2", "E3", "G3", "B3"], 0.15),     # Em
    ("D2", ["A2", "D3", "F#3", "A3"], 0.16),    # D
    ("E2", ["B2", "E3", "A3", "B3"], 0.16),     # Esus4 (the flash)
    ("A1", ["E3", "A3", "B3", "E4"], 0.14),     # Asus2
    ("A1", ["E3", "A3", "C#4", "E4"], 0.13),    # A (the rise, open)
]
FALLS = [  # descending glass runs, one per section until the flash: (section, [notes])
    (0, ["E6", "C6", "A5", "E5"]), (1, ["D6", "B5", "G5", "D5"]), (2, ["C6", "A5", "F5", "C5"]),
    (3, ["B5", "G5", "E5", "B4"]), (4, ["A5", "F#5", "D5", "A4"]),
]
RISE = ["A4", "C#5", "E5", "A5", "C#6", "E6", "A6"]


def _r_pads(tr: Track, rng) -> None:
    _pad_chords(tr, RSEC, [v for _, v, _ in RCHORDS], rng, [g for _, _, g in RCHORDS], attack=3.0, release=3.5,
                overlap=2.0, cutoff=1200, bright_cutoff=2600, voices=5, air=0.12)
    _bass(tr, RSEC, [b for b, _, _ in RCHORDS], rng, gain=0.15, overlap=2.0)


def _r_falls(tr: Track, rng) -> None:
    for sec, notes in FALLS:
        for k, nn in enumerate(notes):
            t = sec * RSEC + 1.0 + 1.3 * k + rng.uniform(-0.02, 0.02)
            pos = 0.5 - 0.3 * k
            _celesta_with_echo(tr, t, nn, 0.5 + 0.03 * sec, rng, pos, echo_s=3 * UG_EIGHTH, gain=1.0, inst=_tube)
            tr.add(t + 0.02, _tube(hz(nn) * 1.0029, 0.4, rng, 4.0), 0.28, -pos)
    # bowed glass climbing before the flash, then letting go
    for k, (nn, d) in enumerate((("E4", 9.0), ("A4", 8.0), ("E5", 7.0))):
        tr.add(RSEC * 2 + 6.0 * k + 2.0, _bowed_glass(hz(nn), d, rng, attack=d * 0.5, release=d * 0.4), 0.10 + 0.03 * k)
    # the rise: the lights going up, after the flash
    for k, nn in enumerate(RISE):
        t = RSEC * 5 + 3.5 + 0.8 * k
        pos = -0.6 + 1.2 * k / (len(RISE) - 1)
        g = music.glass(hz(nn), 0.5, rng, dur=5.0, t60=3.5, bright=0.35)
        tr.add(t, g, 0.18, pos)
        tr.add(t + 3 * UG_EIGHTH, biquad(g, "lowpass", 2600, 0.6), 0.05, -pos)
    tr.add(RSEC * 5 + 0.4, _bowed_glass(hz("A4"), 9.0, rng, attack=3.0, release=4.5), 0.13)


def _r_held(tr: Track, rng) -> None:
    L = RSEC * len(RCHORDS)
    tr.buf += 0.014 * _held_note(tr.n, L, rng, root="A3")
    dr = music.drone(periodic_freq(hz("A1"), L), tr.n, rng, harmonics=(1.0, 0.5, 0.2, 0.08), breath_rate=2.0 / L, depth=0.5)
    tr.buf += 0.016 * biquad(dr, "lowpass", 400)


def _r_pulse(dry: Track, rng) -> None:
    """The count doubles to 96 a minute through the fall and goes quiet at the flash; a faint 48 returns at the end."""
    sec_gain = [0.6, 0.75, 0.9, 1.0, 1.0, 0.0, 0.0, 0.0]
    times, gains, roots = [], [], []
    for i, (bass, _, _) in enumerate(RCHORDS):
        for k in range(8):
            times.append(i * RSEC + (k + 0.5) * UG_BEAT)  # off the loop point
            gains.append(sec_gain[i] * (1.0 if k % 2 == 0 else 0.7))
            roots.append(bass)
    _pulse_layer(dry, (times, gains), roots, rng, 0.36)


@sound("music_array_hall_reversal", "music",
       "Array Hall reversal: the night's chords fall as the pulse doubles, descending bell runs and climbing bowed glass, "
       "a flash on Esus4, then the lights rising into a held A",
       loop=True, lufs=-20.0)
def music_array_hall_reversal(rng):
    L = RSEC * len(RCHORDS)
    tr = Track(L, loop=True)
    for layer in (_r_pads, _r_falls, _r_held):
        layer(tr, rng)
    dry = Track(L, loop=True)
    _r_pulse(dry, rng)
    out = reverb.reverb_circular(tr.buf, reverb.preset("hall", True), wet=0.5, dry=0.75)
    out += reverb.reverb_circular(dry.buf, reverb.preset("room_amb", True), wet=0.3, dry=1.0)
    out = _tape_wow(out, L, rng, depth=0.0008)
    return _master(out, 11000.0)
