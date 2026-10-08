"""Original score. D minor throughout (Aeolian with Dorian and Lydian
colours). Loops are rendered circularly (notes and reverb tails wrap around
the loop point) and every continuous oscillator uses a loop-periodic
frequency, so the loops are seamless by construction."""
from __future__ import annotations

import numpy as np

from synth import env, music, reverb
from synth.core import SR
from synth.filters import biquad, butter, fft_filter, smooth_band
from synth.loops import periodic_freq
from synth.music import Track, hz

from . import kit, sound

# ------------------------------------------------------------------------------------------
# Menu theme: 8 chords x 18.75 s = 150 s
# ------------------------------------------------------------------------------------------
MENU_SECTION = 18.75
MENU_CHORDS = [  # (bass, pad voicing)
    ("D2", ["F3", "A3", "C4", "E4"]),    # Dm9
    ("Bb1", ["F3", "A3", "D4", "E4"]),   # Bbmaj7(#11)
    ("G2", ["F3", "Bb3", "D4", "A4"]),   # Gm9
    ("A2", ["F3", "A3", "D4", "E4"]),    # Dm(add9)/A
    ("Bb1", ["F3", "A3", "C4", "D4"]),   # Bbmaj9
    ("F2", ["A3", "C4", "E4", "G4"]),    # Fmaj9
    ("G2", ["Bb3", "D4", "E4", "G4"]),   # Gm6
    ("A2", ["G3", "D4", "E4", "A4"]),    # A7sus4 -> back to Dm9
]
# Celesta phrases per chord: (offset in section, note, velocity)
MENU_MELODY = [
    [(2.0, "A5", .72), (2.9, "F5", .55), (3.8, "E5", .55), (4.9, "D5", .62),
     (10.5, "D6", .5), (11.4, "C6", .45), (12.4, "A5", .5)],
    [(2.2, "F5", .55), (3.0, "A5", .58), (3.8, "D6", .62), (4.8, "E6", .5), (11.0, "D6", .42),
     (12.2, "A5", .4)],
    [(2.0, "Bb5", .68), (2.9, "A5", .55), (3.8, "G5", .55), (4.9, "D5", .6),
     (10.8, "F5", .45), (11.7, "A5", .48), (12.9, "G5", .45)],
    [(2.4, "E5", .55), (3.4, "D5", .5), (4.6, "A4", .5), (11.5, "E6", .38), (12.6, "D6", .36)],
    [(2.0, "D6", .68), (2.9, "C6", .55), (3.8, "A5", .55), (4.9, "F5", .6),
     (10.6, "C6", .45), (11.6, "D6", .5)],
    [(2.2, "C6", .62), (3.1, "A5", .5), (4.0, "G5", .5), (5.1, "E5", .58), (11.2, "G5", .42),
     (12.1, "A5", .45), (13.2, "C6", .45)],
    [(2.0, "Bb5", .64), (2.9, "G5", .5), (3.8, "E5", .58), (4.9, "D5", .55), (11.0, "D6", .4),
     (12.3, "Bb5", .38)],
    [(2.0, "A5", .6), (3.0, "G5", .5), (4.0, "E5", .5), (5.2, "D5", .55), (11.8, "E5", .38),
     (13.4, "A4", .36)],
]

# ------------------------------------------------------------------------------------------
# Gameplay underscore: D pedal, 8 sections x 20 s = 160 s
# ------------------------------------------------------------------------------------------
LAB_SECTION = 20.0
LAB_CHORDS = [
    ["D3", "F3", "A3", "E4"],     # Dm(add9)
    ["D3", "F3", "A3", "Bb3"],    # Bbmaj7/D (dark semitone rub)
    ["D3", "G3", "Bb3", "D4"],    # Gm/D
    ["C3", "F3", "A3", "D4"],     # Dm7
    ["D3", "F3", "Bb3", "E4"],    # Bb(#11)/D (Lydian colour)
    ["C3", "G3", "D4", "E4"],     # Csus/D (Dorian lift)
    ["D3", "G3", "Bb3", "E4"],    # Gm6/D
    ["D3", "G3", "A3", "E4"],     # A7sus4/D
]
LAB_MELODY = [  # absolute times, sparse, low register
    (6.0, "A4", .42), (7.4, "F4", .36), (8.9, "E4", .38),
    (31.0, "D5", .36),
    (46.0, "Bb4", .4), (47.5, "A4", .34), (49.2, "D4", .38),
    (71.0, "C5", .32),
    (86.0, "E5", .4), (87.6, "D5", .34), (89.4, "A4", .36),
    (113.0, "G4", .32), (114.8, "A4", .3),
    (126.0, "E4", .38), (127.5, "G4", .34), (129.3, "D4", .38),
    (151.0, "A4", .3),
]
LAB_SWELLS = [(24.0, "D4", 10.0, 0.16), (78.0, "A3", 11.0, 0.14), (133.0, "G3", 9.0, 0.12)]


def _celesta_with_echo(track: Track, t: float, note: str, vel: float, rng, pos: float,
                       echo_s: float = 0.75, echoes=(0.32, 0.12), dur: float = 4.0, gain: float = 1.0,
                       inst=music.celesta) -> None:
    x = inst(hz(note), vel, rng, dur)
    track.add(t, x, gain, pos)
    y = x
    for k, g in enumerate(echoes, start=1):
        y = biquad(y, "lowpass", 3200 - 800 * k, 0.6)
        track.add(t + echo_s * k, y, gain * g, -pos * (0.9 if k % 2 else 0.5))


def _pads(track: Track, section: float, chords, rng, *, attack=5.0, release=5.5, overlap=2.5,
          gain=0.16, cutoff=1100.0, bright_cutoff=2300.0, voices=4, air=0.1):
    for i, voicing in enumerate(chords):
        start = i * section - overlap
        dur = section + 2 * overlap
        for j, note in enumerate(voicing):
            x = music.pad_note(hz(note), dur, rng, attack=attack, release=release, voices=voices,
                               cutoff=cutoff, bright_cutoff=bright_cutoff, air=air,
                               width=0.5 + 0.1 * j)
            track.add(start + rng.uniform(-0.15, 0.15), x, gain)


def _bass(track: Track, section: float, notes, rng, gain=0.2, overlap=2.5):
    for i, note in enumerate(notes):
        start = i * section - overlap
        dur = section + 2 * overlap
        x = music.pad_note(hz(note), dur, rng, attack=4.0, release=5.0, voices=3, detune_cents=5,
                           cutoff=380, bright_cutoff=650, width=0.2, air=0.0)
        n = x.shape[-1]
        sub = np.sin(2 * np.pi * hz(note) * np.arange(n) / SR) * env.swell(n, 4.0, 5.0)
        track.add(start, x + 0.3 * sub, gain)


def _master(buf: np.ndarray, hi_cut: float = 11000.0) -> np.ndarray:
    """Gentle, loop-safe tone shaping (zero-phase FFT): trims rumble below
    35 Hz and air above ``hi_cut`` (keeps the files small and soft)."""
    return fft_filter(buf, lambda f: smooth_band(f, 35.0, hi_cut, 0.8))


@sound("music_menu", "music",
       "Main menu theme: slow evolving D minor pads, sparse celesta melody with echoes, deep hall",
       loop=True, lufs=-20.0)
def music_menu(rng):
    L = MENU_SECTION * len(MENU_CHORDS)
    tr = Track(L, loop=True)
    _pads(tr, MENU_SECTION, [v for _, v in MENU_CHORDS], rng, gain=0.15, cutoff=1500, bright_cutoff=3200,
          air=0.15)
    _bass(tr, MENU_SECTION, [b for b, _ in MENU_CHORDS], rng, gain=0.075)
    # drone: D2 + A2, loop-periodic frequencies and a breath that fits the loop 4x
    n = tr.n
    dr = music.drone(periodic_freq(hz("D2"), L), n, rng, breath_rate=4.0 / L, depth=0.5)
    dr += 0.6 * music.drone(periodic_freq(hz("A2"), L), n, rng, breath_rate=3.0 / L, depth=0.6)
    tr.buf += 0.022 * biquad(dr, "lowpass", 500)
    for i, phrase in enumerate(MENU_MELODY):
        base = i * MENU_SECTION
        for t, note, vel in phrase:
            pos = rng.uniform(0.1, 0.35) * (1 if (i + len(note)) % 2 else -1)
            _celesta_with_echo(tr, base + t + rng.uniform(-0.04, 0.04), note, vel, rng, pos, gain=1.1)
    # a few music-box glints an octave above, very soft
    for t, note in ((26.0, "A6"), (64.5, "E6"), (99.0, "G6"), (139.0, "D6")):
        tr.add(t, music.music_box(hz(note), 0.5, rng, 4.0), 0.3, rng.uniform(-0.6, 0.6))
    out = reverb.reverb_circular(tr.buf, reverb.preset("hall", True), wet=0.55, dry=0.75)
    return _master(out, 10000.0)


@sound("music_lab", "music",
       "Gameplay underscore: low, sparse D-pedal pads, rare soft celesta, distant metallic swells",
       loop=True, lufs=-20.0)
def music_lab(rng):
    L = LAB_SECTION * len(LAB_CHORDS)
    tr = Track(L, loop=True)
    _pads(tr, LAB_SECTION, LAB_CHORDS, rng, attack=6.0, release=6.5, overlap=3.0, gain=0.15,
          cutoff=850, bright_cutoff=1800, voices=4, air=0.08)
    n = tr.n
    dr = music.drone(periodic_freq(hz("D2"), L), n, rng, harmonics=(1.0, 0.6, 0.3, 0.15, 0.06),
                     breath_rate=5.0 / L, depth=0.45)
    dr += 0.5 * music.drone(periodic_freq(hz("A1"), L), n, rng, breath_rate=3.0 / L, depth=0.5)
    tr.buf += 0.035 * biquad(dr, "lowpass", 420)
    for t, note, vel in LAB_MELODY:
        _celesta_with_echo(tr, t, note, vel, rng, rng.uniform(-0.3, 0.3), echo_s=1.1, echoes=(0.25, 0.1),
                           gain=1.0)
    for t, note, d, g in LAB_SWELLS:
        tr.add(t, music.bowed_metal(hz(note), d, rng, attack=d * 0.4, release=d * 0.45), 1.6 * g)
    # distant air moving through the building, twice per loop
    for t in (52.0, 118.0):
        air = butter(kit.whoosh(rng, 12.0, 180, 520, q=0.9, attack=0.45, release=0.45), "lowpass", 900, 4)
        tr.add(t, air / np.max(np.abs(air)), 0.05, rng.uniform(-0.5, 0.5))
    out = reverb.reverb_circular(tr.buf, reverb.preset("hall_dark", True), wet=0.5, dry=0.75)
    return _master(out, 8000.0)


@sound("stinger_chapter_complete", "music",
       "Chapter complete: Bbmaj7 lifts to a warm D major add9 bloom; a last high 9th and a faint b6 linger",
       lufs=-20.0, fade_out=1.2)
def stinger_chapter_complete(rng):
    total = 8.6
    tr = Track(total, loop=False)
    sw = sum(music.glass(hz(nn), 0.3, rng, dur=2.2, t60=2.0, attack=1.2, bright=0.3) for nn in ("A5", "D6"))
    tr.add(0.0, sw, 0.5, 0.0)
    wh = kit.whoosh(rng, 2.0, 400, 3000, q=0.8, attack=0.7, release=0.3)
    tr.add(0.0, wh / np.max(np.abs(wh)), 0.08)
    for note in ("F3", "A3", "D4"):
        tr.add(0.0, music.pad_note(hz(note), 3.0, rng, attack=0.8, release=1.3, voices=4, cutoff=1300, air=0.08),
               0.16)
    tr.add(0.0, music.pad_note(hz("Bb1"), 3.0, rng, attack=0.8, release=1.3, voices=3, cutoff=400, air=0.0), 0.1)
    for t, note, v in ((0.3, "F5", 0.5), (0.62, "A5", 0.55), (0.94, "D6", 0.6)):
        _celesta_with_echo(tr, t, note, v, rng, 0.2, gain=0.6)
    # resolution: D major add9
    t0 = 2.0
    for note in ("D3", "A3", "F#4", "E5"):
        tr.add(t0 - 0.2, music.pad_note(hz(note), 6.4, rng, attack=0.6, release=3.8, voices=4, cutoff=1500,
                                        air=0.1), 0.16)
    bass = music.pad_note(hz("D2"), 6.4, rng, attack=0.5, release=3.8, voices=3, cutoff=420, air=0.0)
    tr.add(t0 - 0.2, bass, 0.11)
    for note, kind, g, dt, p in (("D4", "bell", 0.5, 0.0, -0.2), ("A4", "celesta", 0.55, 0.05, 0.25),
                                 ("D5", "bell", 0.6, 0.1, -0.1), ("F#5", "celesta", 0.5, 0.16, 0.3)):
        f = hz(note)
        x = music.bell(f, g, rng, dur=5.0, t60=4.0, bright=0.4) if kind == "bell" else music.celesta(f, g, rng, 5.0)
        tr.add(t0 + dt, x, 0.7, p)
    for t, note, v in ((3.3, "A5", 0.45), (4.05, "F#5", 0.4), (4.9, "E6", 0.48)):
        _celesta_with_echo(tr, t, note, v, rng, -0.25, gain=0.55, inst=music.music_box)
    tr.add(5.7, music.glass(hz("Bb5"), 0.3, rng, dur=2.6, t60=2.2, attack=0.9, bright=0.2), 0.3, 0.4)
    out = reverb.reverb(tr.buf, reverb.preset("hall", True), wet=0.5, dry=0.75)[:, :tr.n]
    out *= env.curve([(0, 1), (total - 1.6, 1), (total, 0)], tr.n, "cos")
    return _master(out, 12000.0)
