"""Main-menu gear box: the soft wheel click, the muffled knock from inside, the latch, the lid swinging open on a
warm glow, and the lid closing. All original synthesis; they are quieter and rounder than the in-game props so
the menu stays calm."""
from __future__ import annotations

import numpy as np

from synth import env, modal, osc
from synth.core import n_of, add_at, time_axis
from synth.filters import butter

from . import kit, sound


def _norm(x):
    return x / max(np.max(np.abs(x)), 1e-12)


@sound("menu_click", "sfx", "Menu gear box: a knob pushed in and its brass wheel dropping one notch (soft click)")
def menu_click(rng):
    out = np.zeros(n_of(0.3))
    add_at(out, kit.knock(rng, 420, 2400, 8, t60=0.03, contact=0.0006, dur=0.08), 0.0, 0.35)       # knob bottoms out
    add_at(out, kit.tick(rng, 1500, 5600, 10, t60=0.045, contact=0.0003, dur=0.12), 0.026, 0.8)     # pawl drops in the notch
    add_at(out, _norm(modal.strike(modal.metal(rng, 1100, 3300, 5, 0.14), 0.18, 0.0003, rng)), 0.028, 0.1)
    add_at(out, kit.thump(520, 340, 0.05, t60=0.03, glide=0.01), 0.026, 0.2)
    return kit.room(out, 0.1)


@sound("menu_knock", "sfx", "Menu gear box: a muffled knock from inside as the lid settles, as if something wants out")
def menu_knock(rng):
    out = np.zeros(n_of(0.7))
    k1 = butter(kit.knock(rng, 90, 760, 9, t60=0.09, contact=0.003, dur=0.3), "lowpass", 1100, 2)
    add_at(out, _norm(k1), 0.0, 0.8)
    add_at(out, kit.thump(120, 68, 0.2, t60=0.12, glide=0.025), 0.0, 0.45)
    k2 = butter(kit.knock(rng, 90, 700, 8, t60=0.06, contact=0.003, dur=0.2), "lowpass", 900, 2)
    add_at(out, _norm(k2), 0.105, 0.3)
    return kit.room(out, 0.16)


@sound("menu_latch", "sfx", "Menu gear box: the latch releases (clack, small spring, low clunk)")
def menu_latch(rng):
    out = np.zeros(n_of(0.6))
    add_at(out, kit.tick(rng, 1800, 7600, 13, t60=0.03, contact=0.0002, dur=0.08), 0.0, 0.8)
    add_at(out, kit.clank(rng, 500, 3800, 14, t60=0.14, contact=0.0006, dur=0.25), 0.012, 0.55)
    n = n_of(0.3)
    t = time_axis(n)
    spring = np.zeros(n)
    for f, a, t60 in ((310, 1.0, 0.2), (702, 0.45, 0.13), (1090, 0.25, 0.08)):
        spring += a * osc.sine(f * (1.0 - 0.04 * (1 - np.exp(-t / 0.04))), n, rng.uniform(0, 1)) * env.ar(n, 0.002, t60)
    add_at(out, _norm(spring), 0.02, 0.16)
    add_at(out, kit.thump(190, 100, 0.14, t60=0.08, glide=0.02), 0.012, 0.5)
    return kit.room(out, 0.12)


@sound("menu_lid_open", "sfx", "Menu gear box: the lid swings up on its hinge and stops with a soft knock, a warm light swells")
def menu_lid_open(rng):
    out = np.zeros(n_of(2.2))
    d = 0.7
    n = n_of(d)
    cr = kit.creak(rng, d, env.curve([(0, 150), (0.35, 330), (d, 210)], n),
                   env.curve([(0, 0), (0.12, 1), (0.5, 0.7), (d, 0)], n, "cos"),
                   modal.metal(rng, 1300, 4600, 9, 0.05), hiss=0.08)
    add_at(out, cr, 0.0, 0.2)
    add_at(out, butter(kit.knock(rng, 140, 1300, 9, t60=0.07, contact=0.0018, dur=0.25), "lowpass", 2400, 2), 0.64, 0.8)
    add_at(out, kit.thump(150, 80, 0.2, t60=0.12, glide=0.02), 0.64, 0.35)
    add_at(out, kit.knock(rng, 140, 1300, 6, t60=0.04, contact=0.002, dur=0.12), 0.71, 0.2)
    # the warm light: a soft chord (A, E, A) that swells and fades slowly, a little brass shimmer on top
    n = n_of(1.7)
    t = time_axis(n)
    pad = np.zeros(n)
    for f, a in ((220.0, 1.0), (329.63, 0.7), (440.0, 0.55), (659.25, 0.18)):
        pad += a * (osc.sine(f * (1 + 0.0015 * np.sin(2 * np.pi * 4.1 * t)), n, rng.uniform(0, 1))
                    + 0.25 * osc.sine(2 * f, n, rng.uniform(0, 1)))
    pad = butter(pad, "lowpass", 1800, 2) * env.swell(n, 0.55, 1.0)
    add_at(out, _norm(pad), 0.42, 0.11)
    return kit.room(out, 0.14)


@sound("menu_lid_close", "sfx", "Menu gear box: the lid comes down and settles with a soft wooden thud and a small latch click")
def menu_lid_close(rng):
    out = np.zeros(n_of(0.8))
    add_at(out, kit.whoosh(rng, 0.3, 500, 260, q=1.0, attack=0.4, release=0.5), 0.0, 0.05)
    add_at(out, butter(kit.knock(rng, 120, 1000, 9, t60=0.07, contact=0.0022, dur=0.25), "lowpass", 2000, 2), 0.3, 0.8)
    add_at(out, kit.thump(130, 70, 0.18, t60=0.1, glide=0.02), 0.3, 0.4)
    add_at(out, kit.tick(rng, 1800, 7000, 10, t60=0.03, contact=0.0002, dur=0.06), 0.33, 0.45)
    return kit.room(out, 0.12)
