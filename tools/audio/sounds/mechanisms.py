"""Mechanical props: brass wheels and rings, drawers, the gear box, the
keypad safe, the walnut desk's secret compartment, keys and lenses."""
from __future__ import annotations

import numpy as np

from synth import env, modal, noise, osc
from synth.core import n_of, add_at, time_axis
from synth.filters import biquad, butter

from . import kit, sound


def _norm(x):
    return x / max(np.max(np.abs(x)), 1e-12)


@sound("wheel_tick", "sfx", "Brass combination wheel moving one detent (crisp click)")
def wheel_tick(rng):
    out = np.zeros(n_of(0.2))
    n = n_of(0.02)
    zip_ = kit.friction(rng, 0.02, env.curve([(0, 0.2), (0.01, 1.0), (0.02, 0.0)], n), 2500, 8000,
                        grit=0.4, grit_rate=3000)
    add_at(out, _norm(zip_), 0.0, 0.12)
    add_at(out, kit.tick(rng, 2000, 9000, 16, t60=0.045, contact=0.00012, dur=0.12), 0.018)
    add_at(out, _norm(modal.strike(modal.metal(rng, 1500, 4200, 6, 0.12), 0.18, 0.0002, rng)), 0.018, 0.12)
    add_at(out, kit.thump(650, 420, 0.04, t60=0.025, glide=0.008), 0.018, 0.25)
    return kit.room(out, 0.08)


@sound("drawer_locked", "sfx", "Locked desk drawer tugged: wooden rattle against the bolt")
def drawer_locked(rng):
    out = np.zeros(n_of(0.6))
    for t, g in ((0.0, 1.0), (0.105, 0.8), (0.2, 0.62), (0.31, 0.35)):
        t = max(0.0, t + rng.uniform(-0.008, 0.008))
        add_at(out, kit.knock(rng, 150, 1600, 12, t60=0.07, contact=0.0013, dur=0.2), t, g)
        add_at(out, kit.tick(rng, 1200, 6500, 10, t60=0.03, contact=0.00025, dur=0.08),
               t + rng.uniform(0.003, 0.008), 0.6 * g)
        add_at(out, kit.thump(120, 80, 0.12, t60=0.07, glide=0.02), t, 0.35 * g)
    return kit.room(out, 0.14)


@sound("drawer_open", "sfx", "Wooden drawer slides open on dry runners and stops with a soft knock")
def drawer_open(rng):
    out = np.zeros(n_of(1.0))
    d = 0.78
    n = n_of(d)
    speed = env.curve([(0, 0), (0.06, 0.55), (0.18, 1.0), (0.5, 0.8), (0.7, 0.35), (d, 0)], n, "cos")
    slide = kit.friction(rng, d, speed, 180, 2200, body=modal.wood(rng, 120, 900, 12, 0.06),
                         grit=0.45, grit_rate=650, rough_rate=25)
    add_at(out, _norm(slide), 0.02, 0.8)
    rumble = butter(noise.white(n, rng), "bandpass", (90, 380), 2) * speed
    add_at(out, _norm(rumble), 0.02, 0.35)
    add_at(out, kit.knock(rng, 300, 2500, 8, t60=0.04, contact=0.001, dur=0.1), 0.0, 0.35)
    add_at(out, kit.knock(rng, 120, 1200, 12, t60=0.08, contact=0.0018, dur=0.25), 0.8, 0.9)
    add_at(out, kit.thump(110, 70, 0.15, t60=0.1, glide=0.02), 0.8, 0.4)
    for t, g in ((0.815, 0.25), (0.84, 0.15)):  # something small inside rolls and taps
        add_at(out, kit.tick(rng, 1800, 7000, 8, t60=0.04, contact=0.0003, dur=0.06), t, g)
    return kit.room(out, 0.12)


@sound("gear_turn", "sfx", "Strand's gear box knob: ratchet clicks and a gear settling into place")
def gear_turn(rng):
    out = np.zeros(n_of(0.45))
    d = 0.24
    n = n_of(d)
    whirr = kit.friction(rng, d, env.curve([(0, 0), (0.03, 1), (0.2, 0.8), (d, 0)], n, "cos"),
                         700, 4500, body=modal.metal(rng, 900, 4000, 8, 0.05), grit=0.3, grit_rate=1500)
    add_at(out, _norm(whirr), 0.0, 0.12)
    for i, t in enumerate((0.012, 0.062, 0.108, 0.152, 0.193)):
        add_at(out, kit.tick(rng, 1500, 8500, 12, t60=0.03, contact=0.0001, dur=0.06), t, 0.55 + 0.05 * i)
    add_at(out, kit.clank(rng, 400, 4200, 16, t60=0.12, contact=0.0005, dur=0.2), 0.235, 0.85)
    add_at(out, kit.thump(190, 130, 0.08, t60=0.05, glide=0.012), 0.235, 0.35)
    return kit.room(out, 0.1)


@sound("box_open", "sfx", "Small lid springs open: latch click, coil-spring twang, lid knock")
def box_open(rng):
    out = np.zeros(n_of(1.0))
    add_at(out, kit.tick(rng, 2000, 9000, 12, t60=0.03, contact=0.00012, dur=0.06), 0.0, 0.7)
    # coil spring: inharmonic modes with a slight downward droop and wobble
    n = n_of(0.45)
    t = time_axis(n)
    spring = np.zeros(n)
    for f, a, t60 in ((236, 1.0, 0.32), (531, 0.5, 0.22), (842, 0.3, 0.15), (1190, 0.18, 0.1)):
        fr = f * (1.0 - 0.06 * (1 - np.exp(-t / 0.05))) * (1 + 0.012 * np.sin(2 * np.pi * 17 * t))
        spring += a * osc.sine(fr, n, rng.uniform(0, 1)) * env.ar(n, 0.002, t60)
    add_at(out, _norm(spring), 0.012, 0.3)
    # tiny hinge creak as the lid swings
    d = 0.3
    n = n_of(d)
    cr = kit.creak(rng, d, env.curve([(0, 180), (0.15, 420), (d, 300)], n),
                   env.curve([(0, 0), (0.05, 1), (0.25, 0.6), (d, 0)], n, "cos"),
                   modal.metal(rng, 1500, 5000, 10, 0.05), hiss=0.1)
    add_at(out, cr, 0.05, 0.16)
    add_at(out, kit.knock(rng, 300, 2600, 9, t60=0.05, contact=0.0009, dur=0.15), 0.36, 0.9)
    add_at(out, kit.knock(rng, 300, 2600, 6, t60=0.03, contact=0.0009, dur=0.08), 0.405, 0.25)
    return kit.room(out, 0.12)


@sound("keypad_press", "sfx", "Electromechanical safe key: bakelite plunger click and contact")
def keypad_press(rng):
    out = np.zeros(n_of(0.16))
    add_at(out, kit.knock(rng, 1100, 5000, 10, t60=0.022, contact=0.00035, dur=0.06, noise_amt=0.4), 0.0)
    add_at(out, kit.thump(260, 200, 0.05, t60=0.035, glide=0.01), 0.0, 0.3)
    add_at(out, kit.tick(rng, 3000, 10000, 8, t60=0.012, contact=0.0001, dur=0.03), 0.011, 0.35)
    add_at(out, kit.relay(rng, 0.2, dur=0.1), 0.028, 0.18)
    return kit.room(out, 0.06)


@sound("safe_denied", "sfx", "Wrong code: two low electric buzzes from the safe")
def safe_denied(rng):
    out = np.zeros(n_of(0.62))
    add_at(out, kit.relay(rng, 0.4), 0.0, 0.35)
    for t, d in ((0.02, 0.2), (0.3, 0.24)):
        bz = kit.buzz(d, 98.0, rng, bright=2400, rough=0.25)
        bz += 0.35 * kit.buzz(d, 196.5, rng, bright=2600, rough=0.2)
        bz *= env.swell(len(bz), 0.006, 0.04)
        add_at(out, _norm(bz), t, 0.8)
    out = biquad(out, "peak", 550, 0.9, 5.0)
    return kit.room(out, 0.1)


@sound("safe_open", "sfx", "Heavy safe bolts retract with a clunk, then the steel door creaks open")
def safe_open(rng):
    out = np.zeros(n_of(2.3))
    d = 0.16
    n = n_of(d)
    turn = kit.friction(rng, d, env.curve([(0, 0), (0.04, 1), (d, 0)], n, "cos"), 600, 5000,
                        body=modal.metal(rng, 800, 4000, 10, 0.08), grit=0.4, grit_rate=1200)
    add_at(out, _norm(turn), 0.0, 0.2)
    add_at(out, kit.clank(rng, 140, 3500, 26, t60=0.32, contact=0.0012, dur=0.6), 0.16, 1.0)
    add_at(out, kit.thump(110, 52, 0.45, t60=0.3, glide=0.04), 0.16, 0.8)
    add_at(out, kit.clank(rng, 180, 3800, 18, t60=0.22, contact=0.001, dur=0.4), 0.215, 0.5)
    add_at(out, kit.tick(rng, 1500, 7000, 10, t60=0.04, contact=0.00015, dur=0.06), 0.165, 0.4)
    # hinge creak under the weight of the door
    d = 1.45
    n = n_of(d)
    jitter = 1.0 + 0.12 * noise.smooth_random(n, rng, 4.0, periodic=False)
    rate = env.curve([(0, 35), (0.3, 75), (0.7, 120), (1.0, 95), (1.3, 60), (d, 40)], n) * jitter
    amp = env.curve([(0, 0), (0.15, 0.7), (0.5, 1.0), (0.75, 0.55), (1.05, 0.85), (d, 0)], n, "cos")
    body = modal.metal(rng, 500, 3400, 14, 0.09) + modal.random_modes(rng, 90, 420, 8, 0.12, 0.3, -1)
    add_at(out, kit.creak(rng, d, rate, amp, body, jitter=0.08, hiss=0.08), 0.5, 0.8)
    sq_rate = env.curve([(0, 520), (0.5, 700), (0.9, 640), (d, 560)], n, "cos")
    sq_amp = env.curve([(0, 0), (0.35, 0), (0.55, 0.9), (0.8, 0.3), (1.0, 0.7), (1.2, 0), (d, 0)], n, "cos")
    add_at(out, kit.creak(rng, d, sq_rate, sq_amp, modal.metal(rng, 1200, 6000, 12, 0.05), jitter=0.01,
                          hiss=0.04), 0.5, 0.3)
    add_at(out, kit.thump(80, 55, 0.3, t60=0.2, glide=0.05), 1.95, 0.25)
    return kit.room(out, 0.15)


@sound("rosette_press", "sfx", "Carved wooden rosette pressed in: hollow wood click and a hidden latch")
def rosette_press(rng):
    out = np.zeros(n_of(0.4))
    add_at(out, kit.knock(rng, 400, 3000, 10, t60=0.04, contact=0.0008, dur=0.12), 0.0, 0.85)
    add_at(out, _norm(modal.strike(modal.wood(rng, 150, 520, 6, 0.13), 0.3, 0.0015, rng)), 0.0, 0.5)
    add_at(out, kit.tick(rng, 1500, 7000, 10, t60=0.03, contact=0.00015, dur=0.06), 0.034, 0.55)
    return kit.room(out, 0.12)


@sound("secret_panel", "sfx", "Hidden walnut panel: latch release, smooth wooden slide, click into place")
def secret_panel(rng):
    out = np.zeros(n_of(1.3))
    add_at(out, kit.tick(rng, 1400, 6500, 10, t60=0.035, contact=0.0002, dur=0.07), 0.0, 0.55)
    d = 0.85
    n = n_of(d)
    speed = env.curve([(0, 0), (0.12, 0.9), (0.45, 1.0), (0.7, 0.6), (d, 0)], n, "cos")
    slide = kit.friction(rng, d, speed, 280, 3000, body=modal.wood(rng, 200, 1500, 12, 0.05),
                         grit=0.25, grit_rate=420, rough_rate=18)
    add_at(out, _norm(slide), 0.06, 0.6)
    add_at(out, kit.knock(rng, 250, 2400, 10, t60=0.06, contact=0.001, dur=0.15), 0.93, 0.85)
    add_at(out, kit.tick(rng, 1600, 7500, 10, t60=0.03, contact=0.00015, dur=0.06), 0.945, 0.6)
    return kit.room(out, 0.12)


@sound("key_turn", "sfx", "Brass key slides into the lock past the pins and turns with a clack")
def key_turn(rng):
    out = np.zeros(n_of(1.0))
    d = 0.3
    n = n_of(d)
    scrape = kit.friction(rng, d, env.curve([(0, 0), (0.03, 1), (0.25, 0.8), (d, 0)], n, "cos"), 1500, 8000,
                          body=modal.metal(rng, 2000, 8000, 10, 0.04), grit=0.6, grit_rate=1500)
    add_at(out, _norm(scrape), 0.0, 0.22)
    for t, g in ((0.06, 0.4), (0.12, 0.45), (0.172, 0.4), (0.228, 0.5)):
        add_at(out, kit.tick(rng, 3000, 10000, 8, t60=0.015, contact=0.0001, dur=0.04), t, g)
    add_at(out, kit.tick(rng, 1500, 6000, 10, t60=0.03, contact=0.0003, dur=0.06), 0.31, 0.5)
    d2 = 0.25
    n2 = n_of(d2)
    twist = kit.friction(rng, d2, env.curve([(0, 0), (0.05, 1), (0.2, 0.9), (d2, 0)], n2, "cos"), 800, 4500,
                         grit=0.3, grit_rate=900)
    add_at(out, _norm(twist), 0.44, 0.2)
    add_at(out, kit.clank(rng, 500, 6000, 16, t60=0.12, contact=0.0004, dur=0.25), 0.68, 1.0)
    add_at(out, kit.thump(220, 120, 0.1, t60=0.07, glide=0.015), 0.68, 0.4)
    add_at(out, kit.tick(rng, 1500, 7000, 10, t60=0.03, contact=0.00015, dur=0.06), 0.705, 0.55)
    return kit.room(out, 0.1)


@sound("lens_insert", "sfx", "Crystal lens seats into its brass mount: soft scrape, click, glass ring")
def lens_insert(rng):
    out = np.zeros(n_of(1.0))
    d = 0.13
    n = n_of(d)
    scr = kit.friction(rng, d, env.curve([(0, 0), (0.03, 1), (d, 0.3)], n, "cos"), 2000, 8000, grit=0.4,
                       grit_rate=900)
    add_at(out, _norm(scr), 0.0, 0.18)
    add_at(out, kit.tick(rng, 1500, 7000, 14, t60=0.06, contact=0.00015, dur=0.1), 0.125, 0.9)
    add_at(out, _norm(modal.strike(modal.glass(2350.0, t60=0.55, bright=0.4), 0.7, 0.0003, rng)), 0.127, 0.4)
    add_at(out, kit.tick(rng, 2500, 8000, 8, t60=0.025, contact=0.0001, dur=0.05), 0.168, 0.45)
    return kit.room(out, 0.1)


@sound("ring_turn", "sfx", "Projector's brass colour ring turns one stop (click with a slight ring)")
def ring_turn(rng):
    out = np.zeros(n_of(0.5))
    d = 0.12
    n = n_of(d)
    fr = kit.friction(rng, d, env.curve([(0, 0), (0.02, 1), (d, 0.4)], n, "cos"), 1000, 6000, grit=0.3,
                      grit_rate=1200)
    add_at(out, _norm(fr), 0.0, 0.18)
    add_at(out, kit.tick(rng, 1200, 7000, 16, t60=0.07, contact=0.00015, dur=0.12), 0.1, 1.0)
    ring_ = modal.strike(modal.Modes(np.array([930.0, 2480.0, 4650.0, 6900.0]), np.array([0.3, 0.2, 0.12, 0.06]),
                                     np.array([1.0, 0.6, 0.35, 0.2])), 0.4, 0.0002, rng)
    add_at(out, _norm(ring_), 0.1, 0.28)
    return kit.room(out, 0.1)
