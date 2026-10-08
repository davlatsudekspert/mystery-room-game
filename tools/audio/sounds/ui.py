"""Interface feedback sounds: soft, tactile and tuned to D minor so they sit
with the music. UI files peak at -6 dBFS; item feedback at -3 dBFS."""
from __future__ import annotations

import numpy as np

from synth import env, modal, music, reverb
from synth.core import n_of, add_at
from synth.filters import biquad, butter
from synth.music import hz

from . import kit, sound


def _plate(x, wet, max_s=1.2):
    return kit.limit(reverb.reverb(x, reverb.preset("ui_plate"), wet), max_s, 0.35)


def _marimba(f, vel, rng, dur=0.9):
    """Rosewood bar tuned 1 : 3.93 : 9.2 with a soft yarn mallet."""
    md = modal.Modes(f * np.array([1.0, 3.93, 9.2, 1.0015]),
                     np.array([0.55, 0.12, 0.035, 0.45]) * (440.0 / f) ** 0.3,
                     np.array([1.0, 0.25 * vel, 0.06 * vel, 0.3]))
    x = modal.strike(md, dur, contact=0.0011, rng=rng)
    return vel * x / np.max(np.abs(x))


def _short(x, t60):
    """Tighten the ring-out of a note to ``t60`` seconds."""
    return x * env.decay(len(x), t60)


@sound("ui_tap", "ui", "Soft wooden tick for buttons and taps")
def ui_tap(rng):
    out = np.zeros(n_of(0.12))
    add_at(out, kit.knock(rng, 900, 3800, 9, t60=0.035, contact=0.0004, dur=0.1, noise_amt=0.15), 0.0)
    add_at(out, kit.thump(420, 300, 0.05, t60=0.03, glide=0.01), 0.0, 0.25)
    return biquad(out, "lowpass", 7000, 0.6)


@sound("ui_open", "ui", "Rising two-note celesta with a soft swish (panel/inventory opens)")
def ui_open(rng):
    out = np.zeros(n_of(0.8))
    add_at(out, kit.whoosh(rng, 0.28, 700, 3600, q=1.1, attack=0.5, release=0.5), 0.0, 0.18)
    add_at(out, _short(music.celesta(hz("D5"), 0.65, rng, 0.8), 0.45), 0.02)
    add_at(out, _short(music.celesta(hz("A5"), 0.8, rng, 0.8), 0.55), 0.085)
    return _plate(out, 0.12)


@sound("ui_close", "ui", "Falling two-note celesta with a soft swish (panel closes)")
def ui_close(rng):
    out = np.zeros(n_of(0.7))
    add_at(out, kit.whoosh(rng, 0.25, 3200, 800, q=1.1, attack=0.4, release=0.6), 0.0, 0.16)
    add_at(out, _short(music.celesta(hz("A5"), 0.7, rng, 0.7), 0.35), 0.0)
    add_at(out, _short(music.celesta(hz("D5"), 0.6, rng, 0.7), 0.4), 0.065)
    return _plate(out, 0.1)


@sound("ui_error", "ui", "Two muted, falling wood-block notes (gentle 'not quite')")
def ui_error(rng):
    out = np.zeros(n_of(0.5))
    for t, note, v in ((0.0, "A4", 1.0), (0.13, "Ab4", 0.85)):
        f = hz(note)
        md = modal.Modes(f * np.array([1.0, 2.76, 4.1]), np.array([0.16, 0.05, 0.02]),
                         np.array([1.0, 0.25, 0.08]))
        x = modal.strike(md, 0.35, contact=0.0018, rng=rng)
        add_at(out, v * x / np.max(np.abs(x)), t)
        add_at(out, kit.thump(330, 220, 0.1, t60=0.06, glide=0.02), t, 0.3 * v)
    out = butter(out, "lowpass", 3200, 2)
    return kit.room(out, 0.08)


@sound("ui_toast", "ui", "Warm marimba fourth for notifications/toasts")
def ui_toast(rng):
    out = np.zeros(n_of(1.0))
    add_at(out, _marimba(hz("A5"), 0.75, rng), 0.0)
    add_at(out, _marimba(hz("D6"), 0.9, rng), 0.09)
    return _plate(out, 0.14)


@sound("hint", "ui", "Soft glassy ping with a shimmering tail (hint available/shown)")
def hint(rng):
    out = np.zeros(n_of(1.6))
    a = music.glass(hz("A5"), 1.0, rng, dur=1.5, t60=1.3, bright=0.35)
    b = music.glass(hz("A5") * 1.0035, 0.6, rng, dur=1.5, t60=1.1, bright=0.3)  # slow beating
    c = music.glass(hz("E6"), 0.35, rng, dur=1.2, t60=0.8, bright=0.25)
    add_at(out, a + b, 0.0)
    add_at(out, c, 0.012)
    out *= env.swell(len(out), 0.004, 0.25)
    return _plate(out, 0.25, 1.6)


@sound("item_pickup", "sfx", "Quick leather/cloth rustle and a little music-box arpeggio (item taken)",
       peak_db=-3.0)
def item_pickup(rng):
    out = np.zeros(n_of(1.0))
    n = n_of(0.22)
    speed = env.curve([(0, 0), (0.03, 1.0), (0.12, 0.6), (0.22, 0)], n, "cos")
    rustle = kit.friction(rng, 0.22, speed, 700, 6000, grit=0.8, grit_rate=1800, rough_rate=60)
    add_at(out, rustle / np.max(np.abs(rustle)), 0.0, 0.45)
    for i, note in enumerate(("D5", "F5", "A5")):
        add_at(out, _short(music.music_box(hz(note), 0.55 + 0.15 * i, rng, 0.9), 0.6), 0.08 + 0.045 * i, 0.8)
    return _plate(out, 0.1)


@sound("item_combine", "sfx", "Two parts click together, then a bright celesta sparkle (items combined)",
       peak_db=-3.0)
def item_combine(rng):
    out = np.zeros(n_of(1.5))
    add_at(out, kit.tick(rng, 1800, 8000, 12, t60=0.05, contact=0.00025, dur=0.1), 0.0, 0.7)
    add_at(out, kit.knock(rng, 300, 2500, 8, t60=0.05, contact=0.0008, dur=0.12), 0.0, 0.5)
    add_at(out, kit.tick(rng, 2200, 9000, 12, t60=0.06, contact=0.0002, dur=0.1), 0.085, 0.9)
    for i, note in enumerate(("D5", "A5", "D6", "E6")):
        add_at(out, _short(music.celesta(hz(note), 0.5 + 0.12 * i, rng, 1.2), 0.9), 0.2 + 0.05 * i, 0.75)
    sw = music.glass(hz("A6"), 0.25, rng, dur=1.0, t60=0.9, attack=0.25, bright=0.2)
    add_at(out, sw, 0.22)
    return _plate(out, 0.18, 1.5)
