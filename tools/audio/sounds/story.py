"""Story moments: UV reveal, the Lumen Projector, the door of Lab 7,
Leyla's notebook pages and the 'puzzle solved' chime."""
from __future__ import annotations

import numpy as np

from synth import env, granular, modal, music, noise, osc, reverb, samples
from synth.core import n_of, add_at, mix, time_axis
from synth.filters import biquad, butter, tv_biquad
from synth.music import hz

from . import kit, sound


def _norm(x):
    return x / max(np.max(np.abs(x)), 1e-12)


def _plate(x, wet):
    return reverb.reverb(x, reverb.preset("plate"), wet)


@sound("reveal", "sfx", "Soft glassy shimmer as UV light reveals hidden ink")
def reveal(rng):
    out = np.zeros(n_of(1.3))
    for note, g, t0 in (("D6", 0.8, 0.0), ("A6", 0.6, 0.05), ("F6", 0.45, 0.11), ("E7", 0.25, 0.16)):
        for det in (1.0, 1.0025):
            x = music.glass(hz(note) * det, g, rng, dur=1.1, t60=1.0, attack=0.22, bright=0.25)
            add_at(out, x, t0)
    # scattered glints: tiny high pings, densest early
    def glint(r):
        return music.glass(r.uniform(2600, 5200), 1.0, r, dur=0.25, t60=0.18, bright=0.2)
    sparkle = granular.cloud(0.9, lambda t: 40.0 * np.exp(-t / 0.35), glint, rng, stereo=False,
                             gain_db=(-22, -6), circular=False)
    add_at(out, sparkle, 0.03, 0.6)
    air = kit.whoosh(rng, 1.0, 2500, 7000, q=0.8, attack=0.35, release=0.6)
    add_at(out, _norm(air), 0.0, 0.12)
    out *= env.curve([(0, 1), (0.8, 1), (1.3, 0)], len(out), "cos")
    return kit.limit(_plate(out, 0.3), 1.7, 0.45)


@sound("projector_charge", "sfx", "Lumen Projector charging: rising electrical whine over a growing hum")
def projector_charge(rng):
    d = 2.1
    n = n_of(d)
    t = time_axis(n)
    u = t / d
    f = 160.0 * (2300.0 / 160.0) ** (u ** 1.35)
    f *= 1.0 + 0.004 * np.sin(2 * np.pi * (5.0 + 3.0 * u) * t) * u
    whine = osc.additive(f, n, [(1, 1.0), (2, 0.35), (3, 0.18), (4, 0.06)])
    whine += 0.3 * osc.sine(f * 1.5, n)
    whine *= env.curve([(0, 0), (0.25, 0.25), (1.6, 0.8), (2.0, 1.0), (d, 0.9)], n, "cos")
    whine = biquad(whine, "lowpass", 6500, 0.7)
    h = kit.hum(d, 50.0, {2: 1.0, 4: 0.5, 6: 0.3, 8: 0.2}, rng) * env.curve([(0, 0), (d, 1.0)], n, "cos")
    cr = kit.spark(rng, d, env.curve([(0, 0), (1.3, 0.0), (1.7, 0.08), (d, 0.5)], n) ** 1.5, crackle=1.0, arc=0.0)
    sub = osc.sine(env.curve([(0, 40), (d, 70)], n, "exp"), n) * env.curve([(0, 0), (d, 1)], n, "cos")
    out = 0.55 * _norm(whine) + 0.3 * _norm(h) + 0.12 * _norm(cr) + 0.3 * sub
    # ends right at full charge so projector_fire / projector_fail can follow without a gap
    return kit.limit(kit.room(out, 0.12), 2.25, 0.12)


@sound("projector_fire", "sfx", "Projector fires through the crystal: bright resonant burst, long shimmering tail")
def projector_fire(rng):
    out = np.zeros(n_of(3.6))
    add_at(out, kit.thump(70, 34, 1.0, t60=0.9, glide=0.08), 0.0, 0.85)
    burst = butter(noise.white(n_of(0.25), rng), "highpass", 300, 2) * env.ar(n_of(0.25), 0.002, 0.18)
    add_at(out, _norm(burst), 0.0, 0.35)
    zn = n_of(0.18)
    zap = osc.sine(env.curve([(0, 3200), (0.18, 260)], zn, "exp"), zn) * env.ar(zn, 0.001, 0.16)
    add_at(out, zap, 0.0, 0.25)
    # crystal chord: D major add9 (wonder, not triumph)
    voices = (("D4", "bell", 0.55, 0.0), ("A4", "glass", 0.6, 0.012), ("D5", "bell", 0.7, 0.02),
              ("F#5", "glass", 0.55, 0.03), ("A5", "glass", 0.45, 0.04), ("E6", "glass", 0.35, 0.055))
    for note, kind, g, t0 in voices:
        if kind == "bell":
            x = music.bell(hz(note), g, rng, dur=3.4, t60=3.0, bright=0.55)
        else:
            x = music.glass(hz(note), g, rng, dur=3.4, t60=2.6, bright=0.4)
        add_at(out, x, t0)
    for note, g in (("A5", 0.3), ("D6", 0.25)):
        add_at(out, music.glass(hz(note) * 1.003, g, rng, dur=3.0, t60=2.4, attack=0.5, bright=0.3), 0.1)
    air = kit.whoosh(rng, 2.4, 6000, 1500, q=0.7, attack=0.05, release=0.85)
    add_at(out, _norm(air), 0.0, 0.18)
    out *= env.curve([(0, 1), (2.6, 1), (3.6, 0)], len(out), "cos")
    return kit.limit(_plate(out, 0.35), 3.4, 0.6)


@sound("projector_fail", "sfx", "Projector mistuned: the charge sputters, fizzles and dies with a pop")
def projector_fail(rng):
    out = np.zeros(n_of(1.4))
    d = 0.75
    n = n_of(d)
    f = env.curve([(0, 1500), (0.15, 1300), (0.6, 160), (d, 110)], n, "exp")
    w = osc.additive(f, n, [(1, 1.0), (2, 0.4), (3, 0.2)])
    gate = np.clip(0.6 + 0.9 * noise.smooth_random(n, rng, 18, periodic=False), 0, 1)
    w *= gate * env.curve([(0, 0.9), (0.4, 0.7), (d, 0)], n, "cos")
    add_at(out, biquad(w, "lowpass", 5000), 0.0, 0.45)
    sp = kit.spark(rng, 0.8, env.curve([(0, 0.6), (0.3, 1.0), (0.8, 0)], n_of(0.8)), crackle=1.0, arc=0.5)
    add_at(out, _norm(sp), 0.0, 0.55)
    add_at(out, kit.thump(190, 60, 0.4, t60=0.25, glide=0.03), 0.56, 0.8)
    pop = butter(noise.white(n_of(0.05), rng), "bandpass", (300, 3000), 2) * env.ar(n_of(0.05), 0.0005, 0.03)
    add_at(out, _norm(pop), 0.56, 0.5)
    hn = n_of(0.7)
    hf = env.curve([(0, 50), (0.7, 30)], hn)
    hm = sum(a * osc.sine(hf * k, hn) for k, a in ((2, 1.0), (4, 0.4), (6, 0.2)))
    add_at(out, hm * env.curve([(0, 0.5), (0.5, 0.3), (0.7, 0)], hn, "cos"), 0.0, 0.25)
    return kit.room(out, 0.15)


@sound("door_open", "sfx", "Heavy old wooden door unlatches and swings open on a long, groaning creak")
def door_open(rng):
    total = 2.6
    out = np.zeros(n_of(total))
    add_at(out, kit.clank(rng, 400, 5000, 14, t60=0.08, contact=0.0005, dur=0.15), 0.0, 0.5)
    add_at(out, kit.tick(rng, 1500, 7000, 10, t60=0.03, contact=0.00015, dur=0.06), 0.03, 0.35)
    d = 2.2
    n = n_of(d)
    wob = 1.0 + 0.15 * noise.smooth_random(n, rng, 5.0, periodic=False)
    rate = env.curve([(0, 28), (0.3, 62), (0.6, 115), (0.85, 88), (1.25, 165), (1.55, 120),
                      (1.9, 72), (d, 38)], n, "cos") * wob
    amp = env.curve([(0, 0), (0.12, 0.6), (0.45, 1.0), (0.68, 0.45), (0.9, 0.95), (1.4, 0.85),
                     (1.6, 0.35), (1.85, 0.7), (d, 0)], n, "cos")
    body = modal.metal(rng, 700, 4000, 12, 0.06) + modal.random_modes(rng, 70, 600, 14, 0.06, 0.16, -1.5)
    cr = kit.creak(rng, d, rate, amp, body, jitter=0.07, hiss=0.1, hiss_band=(900, 4000))
    add_at(out, cr, 0.12, 0.75)
    groan_rate = env.curve([(0, 14), (1.0, 22), (d, 12)], n) * wob
    groan = kit.creak(rng, d, groan_rate, amp ** 1.5, modal.random_modes(rng, 60, 300, 10, 0.1, 0.25, -1),
                      jitter=0.12, hiss=0.0)
    add_at(out, groan, 0.12, 0.35)
    air = butter(noise.colored(n, rng, -6.0), "lowpass", 600, 2) * env.curve([(0, 0), (0.6, 0.6), (1.6, 1.0),
                                                                                (d, 0)], n, "cos")
    add_at(out, _norm(air), 0.25, 0.12)
    # hinge squeal: near-periodic high-rate stick-slip (clean harmonic series),
    # breaking out in a few places along the swing
    sq_rate = env.curve([(0, 380), (0.4, 560), (0.75, 470), (1.1, 690), (1.5, 610), (d, 430)], n, "cos")
    sq_rate *= 1.0 + 0.03 * noise.smooth_random(n, rng, 3.0, periodic=False)
    sq_amp = env.curve([(0, 0), (0.25, 0), (0.42, 0.9), (0.62, 0.15), (0.95, 0.0), (1.12, 0.8), (1.3, 1.0),
                        (1.5, 0.2), (1.7, 0.0), (d, 0)], n, "cos")
    squeal = kit.creak(rng, d, sq_rate, sq_amp, modal.metal(rng, 900, 5500, 14, 0.05), jitter=0.012,
                       hiss=0.05, hiss_band=(2000, 6000))
    add_at(out, squeal, 0.12, 0.42)
    out *= env.curve([(0, 1), (2.2, 1), (total, 0)], len(out), "cos")
    return kit.limit(kit.room(out, 0.2, "corridor"), 2.9, 0.4)


@sound("door_slam", "sfx", "Heavy wooden door slams shut; latch catches; the room rings briefly")
def door_slam(rng):
    out = np.zeros(n_of(1.9))
    add_at(out, _norm(kit.whoosh(rng, 0.2, 200, 900, q=0.8, attack=0.8, release=0.1)), 0.0, 0.18)
    t = 0.18
    add_at(out, kit.knock(rng, 70, 700, 16, t60=0.22, contact=0.003, dur=0.6, noise_amt=0.2), t, 0.9)
    add_at(out, kit.thump(85, 38, 0.7, t60=0.45, glide=0.05), t, 0.8)
    add_at(out, kit.knock(rng, 250, 2200, 14, t60=0.07, contact=0.0009, dur=0.25), t + 0.001, 0.85)
    add_at(out, kit.knock(rng, 900, 4000, 10, t60=0.03, contact=0.0004, dur=0.1), t + 0.002, 0.35)
    add_at(out, kit.clank(rng, 1200, 6000, 14, t60=0.08, contact=0.0003, dur=0.15), t + 0.012, 0.45)
    for dt, g in ((0.06, 0.18), (0.11, 0.12), (0.19, 0.08), (0.25, 0.05)):
        add_at(out, kit.tick(rng, 1500, 7000, 8, t60=0.03, contact=0.0002, dur=0.05), t + dt, g)
    # Heard from inside the lab: the room rings, and the corridor behind answers.
    return mix(reverb.reverb(out, reverb.preset("corridor"), 0.25),
               reverb.reverb(out, reverb.preset("lab"), 0.15, dry=0.0))


@sound("page_turn", "sfx", "A page of Leyla's notebook is turned (paper crinkle and air flap)",
       source="synth + Kenney CC0 `bookFlip2.ogg` (RPG Audio)")
def page_turn(rng):
    out = np.zeros(n_of(0.7))
    # recorded paper (CC0) for the fine crinkle detail; rumble trimmed off
    rec = butter(samples.load("kenney/rpg-audio/bookFlip2.ogg"), "highpass", 150, 2)
    add_at(out, rec / np.max(np.abs(rec)), 0.0, 0.8)
    # synthesised layer: sparse crinkles through small 'paper' resonances + an air flap
    d = 0.5
    n = n_of(d)
    move = env.curve([(0, 0), (0.04, 0.5), (0.1, 0.25), (0.2, 1.0), (0.33, 0.7), (0.42, 0.25), (d, 0)], n, "cos")
    crk = noise.dust(n, 900 * move, rng, heavy_tail=0.8)
    paper = modal.random_modes(rng, 1800, 9000, 12, 0.002, 0.006, -1.0)
    crk = butter(crk, "highpass", 1500, 2) * 0.4 + modal.resonate(crk, paper) * 0.05
    add_at(out, _norm(crk), 0.0, 0.3)
    flap = tv_biquad(noise.colored(n, rng, -3.0), "bandpass", env.curve([(0, 350), (0.2, 1200), (d, 450)], n),
                     0.8) * move ** 2
    add_at(out, _norm(flap), 0.0, 0.3)
    return butter(kit.room(out, 0.06), "highpass", 180, 2)


@sound("puzzle_solved", "sfx", "Resonant bell-like D major add9 chord, gently arpeggiated (puzzle solved)")
def puzzle_solved(rng):
    out = np.zeros(n_of(2.6))
    voices = (("D4", "bell", 0.55, 0.0), ("A4", "celesta", 0.7, 0.04), ("D5", "bell", 0.75, 0.08),
              ("F#5", "celesta", 0.65, 0.12), ("A5", "glass", 0.45, 0.16), ("E6", "box", 0.4, 0.22))
    for note, kind, g, t0 in voices:
        f = hz(note)
        if kind == "bell":
            x = music.bell(f, g, rng, dur=2.4, t60=2.2, bright=0.45)
        elif kind == "celesta":
            x = music.celesta(f, g, rng, dur=2.4)
        elif kind == "glass":
            x = music.glass(f, g, rng, dur=2.4, t60=1.8, bright=0.35)
        else:
            x = music.music_box(f, g, rng, dur=2.4)
        add_at(out, x, t0)
    pad = sum(music.pad_note(hz(nn), 2.4, rng, attack=0.15, release=1.9, voices=3, cutoff=900, air=0.0)
              for nn in ("D3", "A3"))
    add_at(out, pad[0] + pad[1], 0.0, 0.12)
    out *= env.curve([(0, 1), (1.9, 1), (2.6, 0)], len(out), "cos")
    return kit.limit(_plate(out, 0.28), 2.6, 0.5)
