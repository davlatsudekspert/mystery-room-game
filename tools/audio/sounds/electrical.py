"""Panel 7 and other electrics: toggles, the main breaker, relays, the UV
lamp and the door's magnetic lock. Mains here is 50 Hz."""
from __future__ import annotations

import numpy as np

from synth import env, modal, noise, osc
from synth.core import n_of, add_at, time_axis
from synth.filters import biquad, butter

from . import kit, sound


def _norm(x):
    return x / max(np.max(np.abs(x)), 1e-12)


@sound("switch_toggle", "sfx", "Heavy bakelite toggle switch snapping over (clack)")
def switch_toggle(rng):
    out = np.zeros(n_of(0.3))
    d = 0.03
    pre = kit.friction(rng, d, env.curve([(0, 0), (0.02, 1), (d, 0)], n_of(d), "cos"), 1500, 6000,
                       grit=0.3, grit_rate=2000)
    add_at(out, _norm(pre), 0.0, 0.08)
    add_at(out, kit.knock(rng, 800, 4500, 12, t60=0.03, contact=0.0004, dur=0.08, noise_amt=0.4), 0.025, 1.0)
    add_at(out, kit.tick(rng, 2500, 9000, 10, t60=0.015, contact=0.0001, dur=0.04), 0.028, 0.45)
    add_at(out, _norm(modal.strike(modal.random_modes(rng, 150, 700, 8, 0.04, 0.09, -1), 0.2, 0.002, rng)),
           0.025, 0.55)
    add_at(out, kit.thump(150, 95, 0.09, t60=0.06, glide=0.015), 0.025, 0.4)
    return kit.room(out, 0.1)


@sound("breaker_on", "sfx", "Main breaker lever thrown: big clunk, then transformer hum swells in")
def breaker_on(rng):
    out = np.zeros(n_of(2.5))
    d = 0.09
    lever = kit.friction(rng, d, env.curve([(0, 0), (0.05, 1), (d, 0.5)], n_of(d), "cos"), 400, 3500,
                         body=modal.metal(rng, 600, 3000, 8, 0.06), grit=0.4, grit_rate=900)
    add_at(out, _norm(lever), 0.0, 0.18)
    t_hit = 0.085
    add_at(out, kit.clank(rng, 150, 3000, 24, t60=0.28, contact=0.0015, dur=0.5), t_hit, 1.0)
    add_at(out, kit.thump(95, 45, 0.55, t60=0.4, glide=0.05), t_hit, 0.9)
    add_at(out, kit.tick(rng, 1800, 8000, 12, t60=0.03, contact=0.0001, dur=0.06), t_hit + 0.004, 0.5)
    sp = kit.spark(rng, 0.04, env.curve([(0, 1), (0.04, 0)], n_of(0.04)), crackle=1.0, arc=0.2)
    add_at(out, _norm(sp), t_hit + 0.002, 0.25)
    hd = 2.4
    n = n_of(hd)
    h = kit.hum(hd, 50.0, phases_rng=rng)
    h *= env.curve([(0, 0), (0.12, 0.15), (0.8, 0.85), (1.4, 0.75), (hd, 0)], n, "cos")
    h *= 1 + 0.08 * noise.smooth_random(n, rng, 3.0, periodic=False)
    add_at(out, h, t_hit, 0.5)
    return kit.room(out, 0.12)


@sound("breaker_trip", "sfx", "Breaker trips: spark crackle, hum dies, lever snaps back with a clunk")
def breaker_trip(rng):
    out = np.zeros(n_of(1.5))
    d = 0.32
    n = n_of(d)
    sp = kit.spark(rng, d, env.curve([(0, 0.4), (0.05, 1.0), (0.22, 0.8), (d, 0)], n), crackle=1.0, arc=0.55)
    add_at(out, _norm(sp), 0.0, 0.8)
    hd = 0.6
    hn = n_of(hd)
    t = time_axis(hn)
    f0 = 50.0 - 18.0 * np.clip((t - 0.2) / 0.4, 0, 1) ** 1.5
    harm = sum(a * osc.sine(f0 * k, hn) for k, a in ((1, 0.35), (2, 1.0), (3, 0.3), (4, 0.4), (6, 0.15)))
    harm *= env.curve([(0, 0.6), (0.2, 0.6), (hd, 0)], hn, "cos")
    add_at(out, _norm(harm), 0.0, 0.35)
    t_hit = 0.24
    add_at(out, kit.clank(rng, 200, 3500, 22, t60=0.22, contact=0.0012, dur=0.45), t_hit, 1.0)
    add_at(out, kit.thump(100, 50, 0.45, t60=0.3, glide=0.04), t_hit, 0.8)
    late = kit.spark(rng, 0.5, env.curve([(0, 0.25), (0.5, 0)], n_of(0.5)), crackle=1.0, arc=0.0)
    add_at(out, _norm(late), t_hit + 0.05, 0.22)
    return kit.room(out, 0.15)


@sound("power_on", "sfx", "Power restored: relays click in sequence, lights and the Array hum up")
def power_on(rng):
    total = 2.6
    out = np.zeros(n_of(total))
    for t, w, g in ((0.0, 1.0, 1.0), (0.17, 0.6, 0.7), (0.3, 0.8, 0.85), (0.335, 0.4, 0.45),
                    (0.52, 0.9, 0.8), (0.64, 0.5, 0.6), (0.83, 0.7, 0.7), (1.0, 0.5, 0.55), (1.04, 0.3, 0.35)):
        add_at(out, kit.relay(rng, w), t, g)
    # fluorescent tubes striking: starter tinks and a couple of flickers
    for t in (0.58, 0.7, 0.93):
        add_at(out, kit.tick(rng, 3000, 9000, 6, t60=0.02, contact=0.0001, dur=0.04), t, 0.18)
    hd = total - 0.4
    n = n_of(hd)
    ballast = kit.hum(hd, 50.0, {2: 1.0, 4: 0.5, 6: 0.35, 8: 0.25, 10: 0.18, 14: 0.1, 20: 0.05}, rng)
    flick = np.ones(n)
    for t0, dt in ((0.25, 0.06), (0.4, 0.05), (0.55, 0.035)):
        a, b = n_of(t0), n_of(t0 + dt)
        flick[a:b] = 0.15
    flick = butter(flick, "lowpass", 60, 2)
    ballast *= flick * env.curve([(0, 0), (0.25, 0.4), (0.9, 1.0), (1.7, 0.9), (hd, 0)], n, "cos")
    add_at(out, ballast, 0.4, 0.35)
    # the Array: a warm low swell under everything
    arr = kit.hum(hd, 50.0, {1: 0.6, 2: 1.0, 3: 0.5, 4: 0.2}, rng)
    arr *= env.curve([(0, 0), (1.0, 0.7), (1.5, 0.8), (hd, 0)], n, "cos")
    add_at(out, arr, 0.4, 0.4)
    whine = osc.sine(env.curve([(0, 300), (1.4, 520), (hd, 540)], n, "exp"), n)
    whine *= env.curve([(0, 0), (1.0, 0.6), (1.6, 0.5), (hd, 0)], n, "cos")
    add_at(out, whine, 0.4, 0.05)
    return kit.room(out, 0.12)


@sound("uv_on", "sfx", "UV lamp switched on: small click and a faint ballast buzz")
def uv_on(rng):
    out = np.zeros(n_of(1.1))
    add_at(out, kit.knock(rng, 1200, 5500, 10, t60=0.02, contact=0.00035, dur=0.06, noise_amt=0.3), 0.0, 1.0)
    add_at(out, kit.tick(rng, 2500, 9000, 8, t60=0.012, contact=0.0001, dur=0.03), 0.004, 0.4)
    d = 0.95
    n = n_of(d)
    bz = kit.buzz(d, 100.0, rng, bright=3500, rough=0.15)
    gate = np.ones(n)
    for t0, dt in ((0.035, 0.02), (0.07, 0.015)):
        gate[n_of(t0):n_of(t0 + dt)] = 0.2
    gate = butter(gate, "lowpass", 120, 2)
    sizzle = butter(noise.white(n, rng), "bandpass", (4500, 8500), 2)
    sig = (_norm(bz) + 0.12 * _norm(sizzle)) * gate * env.curve([(0, 0), (0.02, 1), (0.3, 0.6), (d, 0)], n, "cos")
    add_at(out, sig, 0.01, 0.16)
    return kit.room(out, 0.08)


@sound("maglock_release", "sfx", "Door maglock lets go: coil hum cuts out, armature clunk, door rattles")
def maglock_release(rng):
    out = np.zeros(n_of(0.8))
    hd = 0.16
    h = kit.hum(hd, 50.0, {2: 1.0, 4: 0.4, 6: 0.25, 8: 0.1}, rng)
    h *= env.swell(len(h), 0.04, 0.004)
    add_at(out, h, 0.0, 0.3)
    t_hit = 0.16
    add_at(out, kit.clank(rng, 300, 4000, 18, t60=0.15, contact=0.0008, dur=0.3), t_hit, 1.0)
    add_at(out, kit.thump(130, 60, 0.3, t60=0.22, glide=0.03), t_hit, 0.9)
    add_at(out, kit.relay(rng, 0.5), t_hit - 0.004, 0.4)
    add_at(out, kit.knock(rng, 100, 800, 12, t60=0.1, contact=0.002, dur=0.25), t_hit + 0.018, 0.4)
    add_at(out, kit.tick(rng, 1400, 6000, 8, t60=0.03, contact=0.0002, dur=0.05), t_hit + 0.045, 0.3)
    out = biquad(out, "lowshelf", 150, 0.7, 2.0)
    return kit.room(out, 0.15, "corridor")
