"""Chapter 2 score, Records Archive B.

``music_archive``: A minor (Aeolian with Dorian and Lydian colours), calm and
mysterious, 'analog': slow detuned-saw pads, a tine electric piano, a
vibraphone with motor tremolo and a soft filtered-saw arpeggio with a tape
echo, all through gentle tape wow and a breath of hiss. 64 BPM, 10 sections of
4 bars (150 s).

``music_archive_finale``: the open vault. F major with a borrowed minor iv:
a tender celesta theme doubled by the electric piano over string pads, rising
to F6 and settling on C7sus4 so it falls back into the opening Fmaj9.

``AudioManager.music()`` loops every music stream, so both cues are seamless
loops: notes and reverb tails wrap around the loop point, continuous
oscillators use loop-periodic frequencies and the wow LFOs fit the loop."""
from __future__ import annotations

import numpy as np

from synth import env, modal, music, noise, osc, reverb
from synth.core import SR, n_of, time_axis
from synth.filters import biquad
from synth.loops import periodic_freq
from synth.music import Track, hz

from . import sound
from .music_tracks import _bass, _celesta_with_echo, _master

# ------------------------------------------------------------------------------------------
# music_archive: 64 BPM, 4 bars (15 s) per chord, 10 chords = 150 s
# ------------------------------------------------------------------------------------------
ARCH_SECTION = 15.0
ARCH_EIGHTH = 60.0 / 64.0 / 2.0
ARCH_CHORDS = [  # (bass, pad voicing)
    ("A1", ["E3", "G3", "B3", "C4"]),    # Am9
    ("F2", ["E3", "A3", "B3", "C4"]),    # Fmaj7(#11)
    ("D2", ["F3", "A3", "C4", "E4"]),    # Dm9
    ("E2", ["D3", "A3", "B3", "E4"]),    # E7sus4
    ("C2", ["E3", "G3", "B3", "D4"]),    # Cmaj9
    ("G2", ["D3", "G3", "B3", "E4"]),    # G6
    ("F2", ["E3", "G3", "A3", "C4"]),    # Fmaj9
    ("D2", ["F3", "A3", "B3", "D4"]),    # Dm6 (Dorian colour)
    ("Bb1", ["D3", "F3", "A3", "E4"]),   # Bbmaj7(#11)
    ("E2", ["D3", "G#3", "B3", "E4"]),   # E7 -> back to Am9
]
ARCH_EPIANO = [  # absolute times; every note is a chord tone of its section
    (2.8, "E5", .5), (3.75, "C5", .42), (4.7, "B4", .42), (6.6, "A4", .45),
    (17.8, "A4", .42), (18.75, "B4", .4), (19.7, "C5", .45), (21.6, "E5", .42),
    (32.8, "F5", .45), (33.75, "E5", .4), (34.7, "C5", .42), (36.6, "D5", .42), (40.6, "A4", .34),
    (41.5, "C5", .32),
    (47.8, "D5", .42), (48.75, "B4", .38), (50.6, "A4", .4),
    (62.8, "G5", .46), (63.75, "E5", .42), (64.7, "D5", .42), (66.6, "B4", .42), (71.4, "E5", .34),
    (81.0, "E5", .38), (82.0, "D5", .36),
    (92.8, "A5", .46), (93.75, "G5", .42), (94.7, "E5", .42), (96.6, "C5", .42), (101.6, "C5", .34),
    (102.5, "E5", .32),
    (107.8, "B4", .42), (108.75, "D5", .4), (109.7, "F5", .42), (111.6, "A4", .4),
    (125.0, "E5", .38), (126.0, "F5", .36), (127.5, "A4", .38),
    (137.8, "G#4", .4), (138.75, "B4", .38), (140.6, "D5", .4),
]
ARCH_VIBES = [(10.5, "E6", .35), (11.4, "B5", .3), (26.0, "B5", .3), (42.5, "E6", .3), (55.0, "B5", .3),
              (70.0, "D6", .32), (85.5, "B5", .3), (86.4, "E6", .28), (100.0, "E6", .3), (115.0, "B5", .3),
              (131.0, "A5", .3), (146.0, "E6", .26)]
ARCH_SWELLS = [(76.0, "D4", 11.0, 0.12), (120.5, "A3", 12.0, 0.11)]
ARCH_ARP_GAIN = [0.0, 0.55, 0.85, 1.0, 1.0, 0.9, 0.8, 0.55, 0.0, 0.0]
ARP_PATTERN = [0, 2, 1, 3, 2, 1, 3, 2]
ARP_ACCENT = [1.0, 0.6, 0.75, 0.6, 0.9, 0.6, 0.75, 0.6]

# ------------------------------------------------------------------------------------------
# music_archive_finale: 60 BPM, 2 bars (8 s) per chord, 8 chords = 64 s
# ------------------------------------------------------------------------------------------
FIN_SECTION = 8.0
FIN_CHORDS = [  # (bass, pad voicing, pad gain)
    ("F2", ["A3", "C4", "E4", "G4"], 0.11),    # Fmaj9
    ("E2", ["G3", "C4", "D4", "E4"], 0.12),    # Cadd9/E
    ("D2", ["F3", "A3", "C4", "E4"], 0.14),    # Dm9
    ("Bb1", ["F3", "A3", "D4", "E4"], 0.16),   # Bbmaj7(#11)
    ("A2", ["F3", "C4", "E4", "A4"], 0.18),    # Fmaj7/A
    ("G2", ["F3", "Bb3", "D4", "A4"], 0.17),   # Gm9
    ("Bb1", ["F3", "Bb3", "Db4", "G4"], 0.16),  # Bbm6 (borrowed minor iv)
    ("C2", ["G3", "Bb3", "C4", "F4"], 0.12),   # C7sus4 -> Fmaj9
]
FIN_THEME = [  # (time, note, velocity), celesta; doubled an octave down by the e-piano in the middle
    (1.0, "C6", .55), (2.0, "A5", .5), (3.0, "G5", .5), (4.5, "E5", .5), (6.0, "F5", .45),
    (9.0, "G5", .5), (10.0, "E5", .45), (11.0, "D5", .45), (13.0, "C5", .5),
    (17.0, "A5", .5), (18.0, "F5", .45), (19.0, "E5", .45), (20.0, "D5", .45), (22.0, "E5", .42),
    (25.0, "D6", .55), (26.0, "C6", .5), (27.0, "A5", .5), (28.5, "E5", .5),
    (33.0, "C6", .6), (34.0, "F6", .62), (35.0, "E6", .55), (36.0, "C6", .5), (38.0, "A5", .48),
    (41.0, "Bb5", .55), (42.0, "A5", .5), (43.0, "G5", .5), (44.0, "F5", .48), (45.5, "D5", .48),
    (49.0, "Db6", .52), (50.0, "C6", .45), (51.0, "Bb5", .48), (52.0, "F5", .45), (54.0, "G5", .42),
    (57.0, "F5", .45), (58.5, "G5", .42), (60.5, "C5", .4),
]


# ---- instruments -------------------------------------------------------------------------

def _epiano(f: float, vel: float, rng, dur: float = 4.0) -> np.ndarray:
    """Tine electric piano (two-operator FM, carrier = modulator): a bell-like
    attack that mellows into an almost pure tone, plus the tine's brief tink."""
    n = n_of(dur)
    t = time_axis(n)
    idx = (0.6 + 1.6 * vel) * np.exp(-t / 0.18) + 0.35
    x = osc.fm(f, f, idx, n)
    if f * 7.0 < 16000:
        x += 0.25 * vel * np.sin(2 * np.pi * 7.0 * f * t) * np.exp(-t / 0.012)
    x *= env.ar(n, 0.002, 2.8 * (440.0 / f) ** 0.35)
    return vel * x / max(np.max(np.abs(x)), 1e-9)


def _tremolo(x: np.ndarray, rng, rate: float = 4.6, depth: float = 0.3) -> np.ndarray:
    """Stereo auto-pan tremolo of the electric piano's amp (per note)."""
    lfo = np.sin(2 * np.pi * (rate * np.arange(len(x)) / SR + rng.uniform(0, 1)))
    return np.vstack([x * (1 + depth * lfo), x * (1 - depth * lfo)]) * 0.7


def _vibes(f: float, vel: float, rng, dur: float = 4.5) -> np.ndarray:
    """Vibraphone bar (1 : 4 : 10) with the motor's amplitude tremolo."""
    md = modal.Modes(f * np.array([1.0, 1.0009, 3.98, 9.9]),
                     np.array([3.2, 2.9, 0.9, 0.25]) * (523.0 / f) ** 0.3,
                     np.array([1.0, 0.25, 0.22 * vel, 0.05 * vel]))
    x = modal.strike(md, dur, contact=0.0014 - 0.0005 * vel, rng=rng)
    t = time_axis(len(x))
    x *= 1.0 - 0.28 * (0.5 - 0.5 * np.cos(2 * np.pi * 5.3 * t))
    return vel * x / max(np.max(np.abs(x)), 1e-9)


def _pluck(f: float, dur: float = 0.9) -> np.ndarray:
    """Soft analog pluck: two slightly detuned saws whose low-pass closes fast."""
    n = n_of(dur)
    t = time_axis(n)
    x = osc.saw(f * 1.002, n) + 0.7 * osc.saw(f * 0.998, n, 0.37)
    bright = biquad(biquad(x, "lowpass", 2300, 0.8), "lowpass", 2800, 0.7)
    dark = biquad(biquad(x, "lowpass", 420, 0.8), "lowpass", 520, 0.7)
    y = (dark + (bright - dark) * np.exp(-t / 0.09)) * env.ar(n, 0.003, 0.7)
    return y / max(np.max(np.abs(y)), 1e-9)


def _tape_wow(buf: np.ndarray, L: float, rng, depth: float = 0.0012, rate: float = 0.31,
              flutter: float = 0.00005, f_rate: float = 5.7) -> np.ndarray:
    """Circular tape wow and flutter (a slowly varying delay whose LFO rates fit
    the loop, read with wrap-around), so the loop stays seamless."""
    n = buf.shape[-1]
    t = time_axis(n)
    d = (depth * (1.0 + np.sin(2 * np.pi * periodic_freq(rate, L) * t + rng.uniform(0, 6.3)))
         + flutter * np.sin(2 * np.pi * periodic_freq(f_rate, L) * t + rng.uniform(0, 6.3)))
    pos = np.arange(n) - d * SR
    i0 = np.floor(pos).astype(np.int64)
    fr = pos - i0
    i0 %= n
    i1 = (i0 + 1) % n
    return buf[..., i0] * (1.0 - fr) + buf[..., i1] * fr


def _hiss(buf: np.ndarray, rng, below_db: float = 38.0) -> np.ndarray:
    """A breath of (loop-periodic) tape hiss, ``below_db`` under the mix RMS."""
    n = buf.shape[-1]
    h = np.vstack([noise.colored(n, rng, -1.0, 1500, 12000), noise.colored(n, rng, -1.0, 1500, 12000)])
    r = np.sqrt(np.mean(buf * buf))
    return h * (r * 10 ** (-below_db / 20.0) / 0.25)


def _pad_chords(track: Track, section: float, chords, rng, gains, *, attack, release, overlap, cutoff,
                bright_cutoff, voices=4, air=0.08):
    for i, voicing in enumerate(chords):
        start = i * section - overlap
        dur = section + 2 * overlap
        for j, note in enumerate(voicing):
            x = music.pad_note(hz(note), dur, rng, attack=attack, release=release, voices=voices,
                               cutoff=cutoff, bright_cutoff=bright_cutoff, air=air, width=0.5 + 0.1 * j)
            track.add(start + rng.uniform(-0.15, 0.15), x, gains[i])


# ---- cues --------------------------------------------------------------------------------

@sound("music_archive", "music",
       "Archive underscore: A minor analog pads, tine e-piano, vibraphone, soft pluck arpeggio with tape echo and wow",
       loop=True, lufs=-20.0)
def music_archive(rng):
    L = ARCH_SECTION * len(ARCH_CHORDS)
    tr = Track(L, loop=True)
    _pad_chords(tr, ARCH_SECTION, [v for _, v in ARCH_CHORDS], rng, [0.14] * len(ARCH_CHORDS), attack=5.0,
                release=5.5, overlap=2.5, cutoff=950, bright_cutoff=2100)
    _bass(tr, ARCH_SECTION, [b for b, _ in ARCH_CHORDS], rng, gain=0.17)
    # soft arpeggio: eighth notes on the chord tones an octave up, with a dotted-eighth tape echo
    cache: dict[str, np.ndarray] = {}
    for i, (_, voicing) in enumerate(ARCH_CHORDS):
        g_sec = ARCH_ARP_GAIN[i]
        if g_sec <= 0:
            continue
        for k in range(int(round(ARCH_SECTION / ARCH_EIGHTH))):
            note = voicing[ARP_PATTERN[k % 8]]
            m = music.midi(note) + 12
            key = str(m)
            if key not in cache:
                cache[key] = _pluck(hz(m))
            t = i * ARCH_SECTION + k * ARCH_EIGHTH + rng.uniform(-0.006, 0.006)
            g = 0.06 * g_sec * ARP_ACCENT[k % 8] * rng.uniform(0.85, 1.0)
            p = 0.35 * np.sin(2 * np.pi * k / 16.0)
            tr.add(t, cache[key], g, p)
            echo = cache[key]
            for e, eg in ((1, 0.32), (2, 0.12)):
                echo = biquad(echo, "lowpass", 2200 - 600 * e, 0.6)
                tr.add(t + 3 * ARCH_EIGHTH * e, echo, g * eg, -p * (1.5 if e % 2 else 0.8))
    for t, note, vel in ARCH_EPIANO:
        x = _tremolo(_epiano(hz(note), vel, rng, 4.0), rng)
        tr.add(t + rng.uniform(-0.03, 0.03), x, 0.55)
        echo = biquad(x, "lowpass", 2000, 0.6)
        tr.add(t + 3 * ARCH_EIGHTH, echo, 0.12)
    for t, note, vel in ARCH_VIBES:
        tr.add(t, _vibes(hz(note), vel, rng), 0.5, rng.uniform(-0.45, 0.45))
    for t, note, d, g in ARCH_SWELLS:
        tr.add(t, music.bowed_metal(hz(note), d, rng, attack=d * 0.4, release=d * 0.45), 1.5 * g)
    # a low, loop-periodic drone under everything (A1 + E2)
    n = tr.n
    dr = music.drone(periodic_freq(hz("A1"), L), n, rng, harmonics=(1.0, 0.5, 0.2, 0.08), breath_rate=5.0 / L,
                     depth=0.5)
    dr += 0.5 * music.drone(periodic_freq(hz("E2"), L), n, rng, breath_rate=3.0 / L, depth=0.5)
    tr.buf += 0.025 * biquad(dr, "lowpass", 400)
    out = reverb.reverb_circular(tr.buf, reverb.preset("hall_dark", True), wet=0.45, dry=0.8)
    out = _tape_wow(out, L, rng)
    out += _hiss(out, rng)
    return _master(out, 9000.0)


@sound("music_archive_finale", "music",
       "Vault finale: tender celesta theme with e-piano over warm F major strings, a borrowed minor iv, glass light",
       loop=True, lufs=-20.0)
def music_archive_finale(rng):
    L = FIN_SECTION * len(FIN_CHORDS)
    tr = Track(L, loop=True)
    _pad_chords(tr, FIN_SECTION, [v for _, v, _ in FIN_CHORDS], rng, [g for _, _, g in FIN_CHORDS], attack=3.0,
                release=3.5, overlap=2.0, cutoff=1300, bright_cutoff=2800, voices=5, air=0.12)
    _bass(tr, FIN_SECTION, [b for b, _, _ in FIN_CHORDS], rng, gain=0.15, overlap=2.0)
    for t, note, vel in FIN_THEME:
        pos = 0.2 * np.sin(t * 0.7)
        _celesta_with_echo(tr, t + rng.uniform(-0.02, 0.02), note, vel, rng, pos, echo_s=0.75, gain=1.0)
        if 16.0 <= t < 56.0:  # the e-piano joins an octave down through the heart of the theme
            x = _tremolo(_epiano(hz(note) / 2.0, vel * 0.9, rng, 4.0), rng, rate=3.8, depth=0.2)
            tr.add(t + 0.01, x, 0.35)
    # light pouring out of the vault: soft glass swells at the peak and at the minor iv
    for t, notes, g in ((32.2, ("A5", "C6"), 0.3), (48.2, ("F5", "Db6"), 0.26)):
        for nn in notes:
            tr.add(t, music.glass(hz(nn), 0.5, rng, dur=6.0, t60=4.0, attack=1.6, bright=0.25), g,
                   rng.uniform(-0.4, 0.4))
    for t, note in ((30.0, "E6"), (62.0, "G6")):
        tr.add(t, music.music_box(hz(note), 0.5, rng, 4.0), 0.28, rng.uniform(-0.5, 0.5))
    tr.add(40.5, music.bowed_metal(hz("D4"), 9.0, rng, attack=3.5, release=4.0), 0.12)
    n = tr.n
    dr = music.drone(periodic_freq(hz("F2"), L), n, rng, harmonics=(1.0, 0.5, 0.2, 0.08), breath_rate=2.0 / L,
                     depth=0.5)
    tr.buf += 0.018 * biquad(dr, "lowpass", 400)
    out = reverb.reverb_circular(tr.buf, reverb.preset("hall", True), wet=0.5, dry=0.75)
    out = _tape_wow(out, L, rng, depth=0.0008)
    out += _hiss(out, rng, 42.0)
    return _master(out, 11000.0)
