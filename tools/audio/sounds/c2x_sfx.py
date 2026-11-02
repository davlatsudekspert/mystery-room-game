"""Chapter 2 expansion ("The Whole Building"): puzzle, door, lift, stair and object one-shots for N1-N10
(docs/CHAPTER2_EXPANSION.md section 8). Ids are prefixed ``c2x_`` so they never collide with the Chapter 1-4 set.
Every sound is built from the shared kit (modal strikes, stick-slip creaks, band-limited noise), mono, peak -1 dBFS
like the other one-shots. Noise layers are band-limited; nothing here is a steady hiss."""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from synth import env, modal, noise, osc, reverb
from synth.core import SR, add_at, n_of, time_axis
from synth.filters import biquad, butter

from . import kit, sound


def _nrm(x):
    return x / max(float(np.max(np.abs(x))), 1e-9)


def _sum(*xs):
    """Add signals of different lengths (padded to the longest)."""
    n = max(len(x) for x in xs)
    return sum(np.pad(x, (0, n - len(x))) for x in xs)


def _lp(x, f):
    return butter(x, "lowpass", f, 2)


def _bp(x, lo, hi):
    return butter(x, "bandpass", (lo, hi), 2)


def _mix(dur, items):
    """items: (signal, start_s, gain). Mono."""
    out = np.zeros(n_of(dur))
    for s, t, g in items:
        add_at(out, s, t, g)
    return out


def _room(x, kind="lab", wet=0.12):
    return kit.room(x, wet, kind)


def _band_noise(rng, dur, lo, hi, slope=-3.0):
    return noise.colored(n_of(dur), rng, slope, lo, hi)


def _shape(x, points, shape="cos"):
    return x * env.curve(points, len(x), shape)


def _iron(f0, t60, rng, count=7):
    """A struck iron pipe / plate: inharmonic modes, the lowest ringing longest."""
    ratios = np.array([1.0, 2.32, 4.1, 6.3, 8.9, 11.7, 14.2][:count]) * rng.uniform(0.98, 1.02, count)
    t60s = t60 * 0.7 ** np.arange(count)
    amps = 1.0 / (1.0 + 0.7 * np.arange(count))
    return modal.modes_from_ratios(f0, ratios, t60s, amps)


# ---- N1 warm wall and doors ------------------------------------------------------------------------

@sound("c2x_panel_open", "sfx", "Warm Wall: a painted panel on the east wall swings open (latch tick, dry hinge, soft thud)")
def c2x_panel_open(rng):
    latch = kit.tick(rng, 2200, 7000, 12, t60=0.03, contact=0.0002, dur=0.08)
    d = 0.9
    m = n_of(d)
    hinge = kit.creak(rng, d, env.curve([(0, 40), (d * 0.5, 70), (d, 35)], m), env.curve([(0, 0), (d * 0.3, 1), (d, 0)], m, "cos"),
                      modal.wood(rng, 200, 1800, 10, 0.12), jitter=0.12, hiss=0.05, hiss_band=(900, 3000))
    thud = kit.knock(rng, 120, 900, 8, t60=0.09, contact=0.003, dur=0.2, noise_amt=0.1)
    return _room(_mix(1.4, [(_nrm(latch), 0.0, 0.6), (_nrm(hinge), 0.05, 0.5), (_nrm(thud), 0.85, 0.9)]))


@sound("c2x_panel_cold", "sfx", "Warm Wall: a cold panel is rapped, a dull flat knock with no answer")
def c2x_panel_cold(rng):
    a = _lp(kit.knock(rng, 180, 1100, 8, t60=0.05, contact=0.002, dur=0.18, noise_amt=0.1), 1400)
    return _room(_mix(0.5, [(a, 0.0, 1.0), (0.6 * a, 0.22, 1.0)]), "lab", 0.08)


@sound("c2x_door_iron", "sfx", "Pump Room door found behind the panel: bolt clank, a long iron hinge groan, a heavy stop")
def c2x_door_iron(rng):
    bolt = kit.clank(rng, 250, 4200, 20, t60=0.4, contact=0.0006, dur=0.5)
    d = 1.5
    m = n_of(d)
    groan = kit.creak(rng, d, env.curve([(0, 14), (d * 0.5, 32), (d, 12)], m), env.curve([(0, 0), (d * 0.3, 1), (d * 0.8, 0.8), (d, 0)], m, "cos"),
                      modal.random_modes(rng, 90, 1100, 14, 0.1, 0.35, -2), jitter=0.15, hiss=0.03, hiss_band=(300, 1500))
    stop = _sum(kit.thump(80, 45, 0.5, 0.32), kit.clank(rng, 200, 2500, 12, t60=0.25, contact=0.001, dur=0.35, noise_amt=0.2))
    return _room(_mix(2.4, [(_nrm(bolt), 0.0, 0.8), (_nrm(groan), 0.25, 0.6), (_nrm(stop), 1.6, 0.9)]), "corridor", 0.2)


@sound("c2x_door_cold", "sfx", "Cold Store door opens: the rubber seal peels (soft sigh), the latch lets go, cold air moves out")
def c2x_door_cold(rng):
    seal = _shape(_band_noise(rng, 0.9, 250, 2200, -4.0), [(0, 0), (0.15, 1), (0.9, 0)])
    latch = kit.clank(rng, 300, 3500, 14, t60=0.2, contact=0.0008, dur=0.3, noise_amt=0.3)
    air = _shape(_band_noise(rng, 1.8, 120, 900, -3.0), [(0, 0), (0.5, 1), (1.8, 0)])
    thump = kit.thump(70, 42, 0.5, 0.3)
    return _room(_mix(2.2, [(_nrm(latch), 0.0, 0.7), (_nrm(seal), 0.08, 0.45), (_nrm(air), 0.3, 0.45), (_nrm(thump), 0.5, 0.35)]),
                 "corridor", 0.22)


@sound("c2x_cold_frozen", "sfx", "Frozen door: the wheel will not turn, an ice crunch and a dull thud against the seal")
def c2x_cold_frozen(rng):
    crunch = np.zeros(n_of(0.35))
    for k in range(9):
        add_at(crunch, kit.tick(rng, 1500 + 150 * k, 6500, 8, t60=0.015, contact=0.0002, dur=0.04), 0.01 * k * rng.uniform(0.5, 1.5), 0.6)
    thud = _sum(kit.thump(110, 60, 0.3, 0.12), 0.4 * kit.knock(rng, 150, 1200, 7, t60=0.05, contact=0.002, dur=0.15, noise_amt=0.2))
    return _room(_mix(0.8, [(_nrm(crunch), 0.0, 0.6), (_nrm(thud), 0.12, 0.9)]))


@sound("c2x_door_service", "sfx", "Service door (stairwell, lift hall): a light steel latch and a short hinge squeak, soft close")
def c2x_door_service(rng):
    latch = kit.tick(rng, 1500, 7500, 14, t60=0.05, contact=0.0003, dur=0.12)
    d = 0.7
    m = n_of(d)
    hinge = kit.creak(rng, d, env.curve([(0, 55), (d * 0.5, 95), (d, 50)], m), env.curve([(0, 0), (d * 0.4, 1), (d, 0)], m, "cos"),
                      modal.random_modes(rng, 400, 3200, 8, 0.06, 0.2, -2), jitter=0.1, hiss=0.04, hiss_band=(900, 3000))
    stop = kit.knock(rng, 100, 1100, 8, t60=0.07, contact=0.002, dur=0.2, noise_amt=0.15)
    return _room(_mix(1.3, [(_nrm(latch), 0.0, 0.7), (_nrm(hinge), 0.08, 0.45), (_nrm(stop), 0.75, 0.7)]), "corridor", 0.18)


@sound("c2x_door_pass", "sfx", "Pass door in the gallery: the pass key slides in, turns, the bolt draws back and the door unlatches")
def c2x_door_pass(rng):
    ins = kit.friction(rng, 0.18, np.linspace(0.8, 0.2, n_of(0.18)), 1500, 5000, grit=0.4) * 0.5
    turn = [kit.tick(rng, 2000, 6500, 12, t60=0.03, contact=0.0003, dur=0.08) for _ in range(3)]
    bolt = kit.clank(rng, 300, 3000, 12, t60=0.2, contact=0.0007, dur=0.3, noise_amt=0.3)
    wood = kit.knock(rng, 130, 1200, 8, t60=0.08, contact=0.0025, dur=0.2, noise_amt=0.1)
    return _room(_mix(1.5, [(_nrm(ins), 0.0, 0.5), (_nrm(turn[0]), 0.3, 0.5), (_nrm(turn[1]), 0.42, 0.6), (_nrm(turn[2]), 0.54, 0.6),
                            (_nrm(bolt), 0.75, 0.9), (_nrm(wood), 1.05, 0.5)]), "corridor", 0.15)


# ---- N2 pipes --------------------------------------------------------------------------------------

@sound("c2x_valve_wheel", "sfx", "Manifold valve wheel turned: a big iron wheel squeaks over a notch, a breath of pressure, a click")
def c2x_valve_wheel(rng):
    d = 0.75
    m = n_of(d)
    sq = kit.creak(rng, d, env.curve([(0, 80), (d * 0.5, 150), (d, 60)], m), env.curve([(0, 0), (d * 0.25, 1), (d * 0.8, 0.8), (d, 0)], m, "cos"),
                   modal.random_modes(rng, 700, 3600, 8, 0.06, 0.3, -2), jitter=0.1, hiss=0.05, hiss_band=(1200, 4000))
    air = _shape(_band_noise(rng, 0.5, 400, 2500, -3.0), [(0, 0), (0.1, 1), (0.5, 0)])
    click = _sum(kit.tick(rng, 1800, 6500, 10, t60=0.04, contact=0.0003, dur=0.1), 0.4 * kit.knock(rng, 150, 900, 6, t60=0.05, dur=0.15))
    return _room(_mix(1.0, [(_nrm(sq), 0.0, 0.7), (_nrm(air), 0.6, 0.25), (_nrm(click), 0.62, 0.8)]), "lab", 0.1)


@sound("c2x_pipe_flow", "sfx", "Pressure reaches the coil: a low thrum, rushing water in the pipe, gurgles, tapering off (1.9 s)")
def c2x_pipe_flow(rng):
    n = n_of(1.9)
    rush = noise.colored(n, rng, -3.0, 300, 2300) * (0.7 + 0.3 * noise.smooth_random(n, rng, 9.0, periodic=False))
    thrum = noise.colored(n, rng, -5.0, 60, 260)
    gur = np.zeros(n)
    for _ in range(14):
        add_at(gur, _lp(kit.drop(rng, f0=rng.uniform(250, 600), rise=2.0, dur=0.08, tick_amt=0.0), 1500), rng.uniform(0.1, 1.5), rng.uniform(0.3, 1))
    e = env.curve([(0, 0), (0.25, 1), (1.2, 0.8), (1.9, 0)], n, "cos")
    return _room((0.7 * _nrm(rush) + 0.5 * _nrm(thrum) + 0.25 * _nrm(gur)) * e, "lab", 0.15)


@sound("c2x_pipe_hazard", "sfx", "Wrong route: the vent to the hall hisses, the pipe rattles and a warning ping rings (calm, nothing is lost)")
def c2x_pipe_hazard(rng):
    n = n_of(1.7)
    hiss = _bp(noise.colored(n, rng, -2.0, 1200, 5200), 1200, 5200) * env.curve([(0, 0), (0.1, 1), (1.0, 0.7), (1.7, 0)], n, "cos")
    rattle = _mix(1.7, [(kit.clank(rng, 400, 3500, 14, t60=0.1, contact=0.0006, dur=0.2), 0.15 + 0.11 * k, 0.5 - 0.06 * k) for k in range(5)])
    ping = modal.strike(_iron(1560.0, 0.9, rng, 3), 1.2, 0.0004, rng)
    return _room(_mix(1.7, [(_nrm(hiss), 0.0, 0.6), (_nrm(rattle), 0.0, 0.45), (_nrm(ping), 0.1, 0.4)]), "corridor", 0.15)


@sound("c2x_thaw", "sfx", "The Cold Store door thaws: ice ticks and cracks, running drips, a long settling creak")
def c2x_thaw(rng):
    ticks = np.zeros(n_of(2.4))
    for _ in range(22):
        add_at(ticks, kit.tick(rng, 2000, 7500, 8, t60=0.03, contact=0.0002, dur=0.07), rng.uniform(0, 1.6), rng.uniform(0.3, 1.0))
    drips = np.zeros(n_of(2.4))
    for k in range(7):
        add_at(drips, _nrm(biquad(kit.drop(rng, dur=0.1), "lowpass", 4000, 0.7)), 0.5 + 0.28 * k + rng.uniform(0, 0.1), 0.5)
    d = 1.0
    m = n_of(d)
    cr = kit.creak(rng, d, env.curve([(0, 30), (d * 0.5, 55), (d, 28)], m), env.curve([(0, 0), (d * 0.4, 1), (d, 0)], m, "cos"),
                   modal.random_modes(rng, 150, 1400, 10, 0.1, 0.3, -2), jitter=0.12, hiss=0.03, hiss_band=(400, 1500))
    return _room(_mix(2.4, [(_nrm(ticks), 0.0, 0.5), (_nrm(drips), 0.0, 0.4), (_nrm(cr), 1.2, 0.5)]), "corridor", 0.2)


def _mallet(rng, f0, t60, count, bright, wood=0.8):
    body = modal.strike(_iron(f0, t60, rng, count), t60 * 1.5, 0.0012, rng, noise=0.3, noise_decay=0.001)
    hit = kit.knock(rng, 200, 2500 * bright, 8, t60=0.02, contact=0.0006, dur=0.08, noise_amt=0.3)
    return _mix(t60 * 1.5, [(_nrm(body), 0.0, 1.0), (_nrm(hit), 0.0, wood * 0.6)])


@sound("c2x_mallet_full", "sfx", "Mallet on a pipe that carries pressure: a full, low, long tone (about 130 Hz)")
def c2x_mallet_full(rng):
    return _room(_mallet(rng, 131.0, 1.1, 6, 0.8), "lab", 0.14)


@sound("c2x_mallet_dead", "sfx", "Mallet on a dead pipe: a short, high, empty tink (about 620 Hz)")
def c2x_mallet_dead(rng):
    return _room(_mallet(rng, 622.0, 0.22, 4, 1.4), "lab", 0.08)


@sound("c2x_mallet_cracked", "sfx", "Mallet on a cracked pipe next to the hazard: a rattling buzz that decays unevenly")
def c2x_mallet_cracked(rng):
    n = n_of(0.9)
    t = time_axis(n)
    base = _mallet(rng, 190.0, 0.5, 5, 1.0)
    base = np.pad(base, (0, max(0, n - len(base))))[:n]
    buzz = osc.saw(95.0 * (1 + 0.03 * np.sin(2 * np.pi * 7 * t)), n)
    buzz = _lp(buzz, 1800) * env.curve([(0, 0), (0.01, 1), (0.25, 0.5), (0.9, 0)], n, "lin") * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 38 * t)))
    return _room(_nrm(base) * 0.8 + 0.45 * _nrm(buzz), "lab", 0.1)


# ---- N3 light table --------------------------------------------------------------------------------

@sound("c2x_lightbox_on", "sfx", "Light table: a tube starter flickers three times and the box settles to a warm glow with a faint 100 Hz hum")
def c2x_lightbox_on(rng):
    n = n_of(1.4)
    t = time_axis(n)
    hum = (np.sin(2 * np.pi * 100 * t) + 0.5 * np.sin(2 * np.pi * 200 * t) + 0.2 * np.sin(2 * np.pi * 300 * t)) * env.curve(
        [(0, 0), (0.55, 0), (0.7, 1), (1.0, 0.6), (1.4, 0.25)], n, "cos")
    flick = np.zeros(n)
    for t0, g in ((0.0, 1.0), (0.18, 0.7), (0.34, 0.8)):
        add_at(flick, _nrm(kit.buzz(0.05, 120, rng, bright=3000, rough=0.5)) * np.hanning(n_of(0.05)), t0, g)
    click = kit.relay(rng, 0.5)
    return _room(_mix(1.4, [(_nrm(click), 0.0, 0.8), (_nrm(flick), 0.0, 0.45), (_nrm(hum), 0.0, 0.4)]), "lab", 0.08)


@sound("c2x_sheet_slide", "sfx", "An acetate sheet slides across the glass of the light table: smooth plastic friction and a tiny flex")
def c2x_sheet_slide(rng):
    d = 0.55
    sp = env.curve([(0, 0), (0.08, 1), (0.4, 0.7), (d, 0)], n_of(d), "cos")
    fr = kit.friction(rng, d, sp, 900, 4200, grit=0.1, rough_rate=22)
    flex = _lp(kit.knock(rng, 600, 3500, 6, t60=0.02, contact=0.0005, dur=0.06, noise_amt=0.3), 4000)
    return _room(_mix(0.8, [(_nrm(_lp(fr, 4500)), 0.0, 0.7), (_nrm(flex), 0.45, 0.35)]), "lab", 0.06)


@sound("c2x_sheet_turn", "sfx", "A sheet is turned a quarter: a short slide and a soft plastic tick as it seats")
def c2x_sheet_turn(rng):
    d = 0.28
    fr = kit.friction(rng, d, env.curve([(0, 0), (0.05, 1), (d, 0)], n_of(d), "cos"), 900, 4000, grit=0.1)
    tk = kit.knock(rng, 500, 4200, 7, t60=0.025, contact=0.0004, dur=0.07, noise_amt=0.3)
    return _room(_mix(0.5, [(_nrm(_lp(fr, 4500)), 0.0, 0.55), (_nrm(tk), 0.26, 0.8)]), "lab", 0.06)


@sound("c2x_sheet_flip", "sfx", "A sheet is flipped over by its tab: a soft flap of acetate, then two taps on the glass")
def c2x_sheet_flip(rng):
    flap = kit.whoosh(rng, 0.25, 500, 2200, q=1.0, attack=0.2, release=0.6)
    t1 = kit.knock(rng, 500, 4000, 7, t60=0.02, contact=0.0004, dur=0.06, noise_amt=0.3)
    return _room(_mix(0.6, [(_nrm(flap), 0.0, 0.5), (_nrm(t1), 0.24, 0.8), (_nrm(t1), 0.31, 0.45)]), "lab", 0.06)


@sound("c2x_light_digits", "sfx", "The two digits light up on the table: a soft, warm two-note glass chime over a gentle glow swell")
def c2x_light_digits(rng):
    a = modal.ring(modal.glass(880.0, 1.6, 0.35), 2.0)
    b = modal.ring(modal.glass(1318.5, 1.8, 0.35), 2.2)
    n = n_of(2.4)
    t = time_axis(n)
    glow = np.sin(2 * np.pi * 220 * t) * env.curve([(0, 0), (0.6, 0.6), (1.4, 0.3), (2.4, 0)], n, "cos")
    return _room(_mix(2.4, [(_nrm(a), 0.0, 0.6), (_nrm(b), 0.22, 0.55), (glow, 0.0, 0.18)]), "plate", 0.18)


# ---- N4 carriage aisle -----------------------------------------------------------------------------

@sound("c2x_crank", "sfx", "Compactus crank: a handle turned with a ratchet clicking faster, a gear grind (1.4 s)")
def c2x_crank(rng):
    d = 1.4
    out = np.zeros(n_of(d))
    t = 0.0
    while t < d - 0.1:
        add_at(out, _sum(_nrm(kit.tick(rng, 1200, 6000, 12, t60=0.03, contact=0.0003, dur=0.07)), 0.4 * _nrm(kit.knock(rng, 150, 1000, 6, t60=0.04, dur=0.1))),
               t, 0.7 + 0.3 * rng.uniform())
        t += 0.16 - 0.08 * (t / d)
    grind = kit.friction(rng, d, env.curve([(0, 0.3), (0.6, 1), (d, 0.5)], n_of(d), "lin"), 120, 900, grit=0.2)
    return _room(_mix(d + 0.2, [(out, 0.0, 0.8), (_nrm(grind), 0.0, 0.35)]), "corridor", 0.12)


@sound("c2x_carriage_roll", "sfx", "A heavy shelf carriage rolls one slot along its rails: a low rumble with rail-joint beats, a stop")
def c2x_carriage_roll(rng):
    d = 2.6
    n = n_of(d)
    t = time_axis(n)
    sp = env.curve([(0, 0), (0.5, 1), (2.0, 0.9), (2.5, 0.0)], n, "cos")
    rumble = noise.colored(n, rng, -6.0, 30, 180) * sp
    # the wheels' flats: a beat that follows the speed; its low harmonics carry on a phone speaker
    beat = np.sin(2 * np.pi * np.cumsum(7.5 * sp) / SR) ** 2
    mid = _bp(noise.colored(n, rng, -3.0, 140, 700), 140, 700) * (0.4 + 0.6 * beat) * sp
    joints = np.zeros(n)
    for k in range(7):
        add_at(joints, _lp(kit.thump(140, 90, 0.12, 0.05), 400), 0.45 + 0.28 * k, 0.5)
    stop = _sum(kit.thump(75, 42, 0.45, 0.25), 0.3 * kit.clank(rng, 150, 2000, 10, t60=0.2, contact=0.002, dur=0.3, noise_amt=0.1))
    out = 0.8 * _nrm(rumble) + 0.5 * _nrm(mid) + 0.3 * _nrm(joints)
    return _room(_mix(d + 0.6, [(out, 0.0, 1.0), (_nrm(stop), 2.45, 0.8)]), "corridor", 0.2)


@sound("c2x_carriage_clunk", "sfx", "The carriage will not move (no gap beside it): a dull steel clunk and a short rattle of the rails")
def c2x_carriage_clunk(rng):
    hit = _sum(kit.thump(95, 52, 0.4, 0.2), 0.5 * kit.clank(rng, 150, 2200, 14, t60=0.25, contact=0.0012, dur=0.4, noise_amt=0.15))
    rat = _mix(0.5, [(kit.tick(rng, 800, 4000, 8, t60=0.03, dur=0.06), 0.02 * k + 0.05, 0.3 / (k + 1)) for k in range(5)])
    return _room(_mix(0.9, [(_nrm(hit), 0.0, 1.0), (_nrm(rat), 0.04, 0.3)]), "corridor", 0.2)


@sound("c2x_aisle_found", "sfx", "The right aisle opens: the shelves part and a long breath of still, cold air with a faint low chime")
def c2x_aisle_found(rng):
    air = _shape(_band_noise(rng, 2.2, 90, 700, -4.0), [(0, 0), (0.6, 1), (2.2, 0)])
    ch = modal.ring(modal.glass(392.0, 2.5, 0.2), 2.8)
    return _room(_mix(2.8, [(_nrm(air), 0.0, 0.7), (_nrm(ch), 0.3, 0.3)]), "corridor", 0.25)


# ---- N5 frost window -------------------------------------------------------------------------------

def _wipe(rng, d, f_lo, f_hi, grit, squeak):
    n = n_of(d)
    sp = env.curve([(0, 0), (0.1 * d, 1), (0.7 * d, 0.85), (d, 0)], n, "cos") * (1.0 + 0.2 * noise.smooth_random(n, rng, 6, periodic=False))
    fr = kit.friction(rng, d, np.clip(sp, 0, None), f_lo, f_hi, grit=grit, grit_rate=1500, rough_rate=30)
    out = _lp(fr, 5200)
    if squeak:   # a glassy squeak where the cloth turns on the pane
        m = n_of(0.18)
        sq = kit.creak(rng, 0.18, env.curve([(0, 220), (0.18, 340)], m), np.hanning(m), modal.glass(rng.uniform(2000, 3200), 0.1, 0.4),
                       jitter=0.05, hiss=0.0)
        add_at(out, 0.45 * _nrm(sq) * np.max(np.abs(out)), 0.55 * d)
    return out


@sound("c2x_frost_wipe_1", "sfx", "Frost window, wipe variant 1: a cloth drags across fine ice crystals (crisp, medium)")
def c2x_frost_wipe_1(rng):
    return _room(_wipe(rng, 0.62, 700, 4300, 0.5, False), "lab", 0.05)


@sound("c2x_frost_wipe_2", "sfx", "Frost window, wipe variant 2: a longer, softer stroke with a glass squeak at the turn")
def c2x_frost_wipe_2(rng):
    return _room(_wipe(rng, 0.85, 500, 3600, 0.3, True), "lab", 0.05)


@sound("c2x_frost_wipe_3", "sfx", "Frost window, wipe variant 3: a short quick wipe, grittier")
def c2x_frost_wipe_3(rng):
    return _room(_wipe(rng, 0.42, 900, 4800, 0.8, False), "lab", 0.05)


@sound("c2x_frost_wipe_4", "sfx", "Frost window, wipe variant 4: a slow low-pitched stroke, damp and heavy, with a squeak")
def c2x_frost_wipe_4(rng):
    return _room(_wipe(rng, 1.0, 350, 2800, 0.25, True), "lab", 0.05)


@sound("c2x_frost_done", "sfx", "The last band is clear: loose ice flakes fall and tinkle on the sill")
def c2x_frost_done(rng):
    out = np.zeros(n_of(1.4))
    for k in range(16):
        add_at(out, _lp(kit.tick(rng, 2500, 8000, 10, t60=0.05, contact=0.0002, dur=0.1), 6000), 0.06 * k + rng.uniform(0, 0.05) + 0.003 * k * k, rng.uniform(0.3, 1.0) * (1 - k / 22))
    ch = modal.ring(modal.glass(1760.0, 0.7, 0.4), 1.0)
    return _room(_mix(1.4, [(_nrm(out), 0.0, 0.8), (_nrm(ch), 0.05, 0.12)]), "plate", 0.15)


# ---- N6 chest rings --------------------------------------------------------------------------------

@sound("c2x_ring_click", "sfx", "Chest ring turned one symbol: a firm brass detent click with a small ring (the next ring follows)")
def c2x_ring_click(rng):
    a = _sum(kit.tick(rng, 1800, 7000, 14, t60=0.05, contact=0.0003, dur=0.12), 0.3 * kit.knock(rng, 300, 1800, 6, t60=0.05, dur=0.1))
    b = kit.tick(rng, 1400, 6000, 12, t60=0.04, contact=0.0003, dur=0.1)
    return _room(_mix(0.35, [(_nrm(a), 0.0, 1.0), (_nrm(b), 0.09, 0.55)]), "lab", 0.06)


@sound("c2x_chest_sealed", "sfx", "The chest is still sealed: the lid is tried, a short rattle against the lock")
def c2x_chest_sealed(rng):
    r = _mix(0.5, [(kit.clank(rng, 400, 4500, 14, t60=0.12, contact=0.0006, dur=0.2), 0.0, 1.0), (kit.clank(rng, 400, 4500, 14, t60=0.1, contact=0.0006, dur=0.2), 0.13, 0.6)])
    return _room(r, "lab", 0.08)


@sound("c2x_chest_unlock", "sfx", "The rings line up: three tumbler clicks, a deep latch release, the lid creaks open with a faint glass rustle")
def c2x_chest_unlock(rng):
    cl = [kit.tick(rng, 2000 + 300 * k, 7500, 12, t60=0.04, contact=0.0003, dur=0.09) for k in range(3)]
    latch = _sum(kit.clank(rng, 150, 2500, 16, t60=0.3, contact=0.0009, dur=0.4, noise_amt=0.2), 0.6 * kit.thump(90, 55, 0.3, 0.15))
    d = 0.9
    m = n_of(d)
    lid = kit.creak(rng, d, env.curve([(0, 45), (d, 80)], m), env.curve([(0, 0), (d * 0.3, 1), (d, 0)], m, "cos"),
                    modal.wood(rng, 150, 1600, 10, 0.12), jitter=0.12, hiss=0.04, hiss_band=(900, 3000))
    rustle = _mix(0.6, [(_lp(kit.tick(rng, 3000, 8000, 8, t60=0.03, dur=0.06), 6500), 0.1 * k + rng.uniform(0, 0.05), 0.5) for k in range(5)])
    return _room(_mix(2.3, [(_nrm(cl[0]), 0.0, 0.7), (_nrm(cl[1]), 0.25, 0.75), (_nrm(cl[2]), 0.5, 0.8), (_nrm(latch), 0.85, 1.0),
                            (_nrm(lid), 1.15, 0.45), (_nrm(rustle), 1.6, 0.25)]), "corridor", 0.18)


# ---- N7 lift ---------------------------------------------------------------------------------------

@sound("c2x_weight_hang", "sfx", "A cast-iron counterweight is hung on the hook: a metal clank and the hook swinging")
def c2x_weight_hang(rng):
    k = modal.strike(_iron(210.0, 0.5, rng, 6), 0.8, 0.0008, rng, noise=0.4)
    sw = kit.knock(rng, 120, 900, 6, t60=0.04, contact=0.002, dur=0.1, noise_amt=0.1)
    return _room(_mix(1.0, [(_nrm(k), 0.0, 1.0), (_nrm(sw), 0.18, 0.35), (_nrm(sw), 0.42, 0.2)]), "corridor", 0.15)


@sound("c2x_weight_off", "sfx", "A counterweight is lifted off the hook: a quick scrape and a light clink")
def c2x_weight_off(rng):
    sc = kit.friction(rng, 0.15, env.curve([(0, 1), (0.15, 0)], n_of(0.15), "lin"), 800, 4500, grit=0.3) * 0.7
    k = modal.strike(_iron(330.0, 0.25, rng, 4), 0.4, 0.0005, rng, noise=0.3)
    return _room(_mix(0.6, [(_nrm(sc), 0.0, 0.6), (_nrm(k), 0.12, 0.8)]), "corridor", 0.1)


@sound("c2x_lift_balanced", "sfx", "Load and counterweight are equal: the weights swing level, the cable settles with a low relief creak")
def c2x_lift_balanced(rng):
    k = modal.strike(_iron(150.0, 0.8, rng, 6), 1.2, 0.001, rng, noise=0.3)
    d = 1.0
    m = n_of(d)
    cr = kit.creak(rng, d, env.curve([(0, 20), (d, 12)], m), env.curve([(0, 0), (d * 0.2, 1), (d, 0)], m, "cos"),
                   modal.random_modes(rng, 100, 900, 10, 0.1, 0.3, -2), jitter=0.15, hiss=0.03, hiss_band=(300, 1000))
    return _room(_mix(1.8, [(_nrm(k), 0.0, 0.8), (_nrm(cr), 0.3, 0.5)]), "corridor", 0.2)


@sound("c2x_counter_heavy", "sfx", "The counterweight is too heavy: the cable groans taut and the weights knock the frame")
def c2x_counter_heavy(rng):
    d = 0.9
    m = n_of(d)
    cr = kit.creak(rng, d, env.curve([(0, 14), (d, 26)], m), env.curve([(0, 0), (d * 0.3, 1), (d, 0)], m, "cos"),
                   modal.random_modes(rng, 80, 700, 10, 0.1, 0.3, -2), jitter=0.15, hiss=0.03, hiss_band=(300, 900))
    k = _sum(kit.thump(90, 50, 0.4, 0.2), 0.5 * kit.clank(rng, 150, 2000, 12, t60=0.25, contact=0.001, dur=0.3, noise_amt=0.1))
    return _room(_mix(1.4, [(_nrm(cr), 0.0, 0.5), (_nrm(k), 0.55, 0.9)]), "corridor", 0.18)


@sound("c2x_counter_light", "sfx", "The counterweight is too light: a slack cable clink and a small hollow tap")
def c2x_counter_light(rng):
    ch = _mix(0.6, [(modal.strike(_iron(900.0 + 120 * k, 0.15, rng, 3), 0.25, 0.0004, rng, noise=0.3), 0.07 * k, 0.8 - 0.15 * k) for k in range(4)])
    k = kit.knock(rng, 200, 1500, 7, t60=0.05, contact=0.002, dur=0.15, noise_amt=0.1)
    return _room(_mix(0.8, [(_nrm(ch), 0.0, 0.6), (_nrm(k), 0.34, 0.5)]), "corridor", 0.12)


@sound("c2x_lift_stuck", "sfx", "The book lift is not balanced: the cage jolts against its stops with a short motor strain")
def c2x_lift_stuck(rng):
    n = n_of(0.9)
    t = time_axis(n)
    mot = _lp(osc.saw(70 + 20 * t, n), 700) * env.curve([(0, 0), (0.1, 1), (0.45, 0.8), (0.55, 0)], n, "cos")
    k = _sum(kit.thump(85, 48, 0.4, 0.2), 0.5 * kit.clank(rng, 200, 2500, 12, t60=0.2, contact=0.001, dur=0.3, noise_amt=0.1))
    return _room(_mix(0.9, [(_nrm(mot), 0.0, 0.4), (_nrm(k), 0.5, 0.9)]), "corridor", 0.18)


@sound("c2x_lift_bell", "sfx", "Lift bell: a small brass arrival bell, one clear ding with a short ring")
def c2x_lift_bell(rng):
    b = modal.ring(modal.bell(1046.5, 1.6, 0.55), 2.0)
    tk = kit.tick(rng, 3000, 8000, 8, t60=0.01, contact=0.0001, dur=0.03)
    return _room(_mix(2.0, [(_nrm(b), 0.0, 1.0), (_nrm(tk), 0.0, 0.2)]), "corridor", 0.12)


@sound("c2x_lift_move", "sfx", "The book lift travels one floor: a motor hum rising, cable and weight clanks passing, a settling clunk (3.6 s)")
def c2x_lift_move(rng):
    d = 3.6
    n = n_of(d)
    t = time_axis(n)
    sp = env.curve([(0, 0), (0.6, 1), (2.8, 1), (3.3, 0)], n, "cos")
    f = 62 + 30 * sp
    ph = 2 * np.pi * np.cumsum(f) / SR
    motor = _lp(np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.3 * np.sin(3 * ph), 900) * sp
    rope = _bp(noise.colored(n, rng, -3.0, 150, 900), 150, 900) * sp * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(9 * sp) / SR) ** 2)
    cl = np.zeros(n)
    for tt in (0.9, 1.6, 2.2, 2.7):
        add_at(cl, modal.strike(_iron(rng.uniform(260, 420), 0.3, rng, 4), 0.5, 0.0007, rng, noise=0.3), tt + rng.uniform(-0.05, 0.05), 0.5)
    stop = _sum(kit.thump(80, 45, 0.5, 0.3), 0.5 * kit.clank(rng, 150, 2000, 12, t60=0.25, contact=0.001, dur=0.3, noise_amt=0.1))
    out = 0.6 * _nrm(motor) + 0.4 * _nrm(rope) + 0.5 * _nrm(cl)
    return _room(_mix(d + 0.6, [(out, 0.0, 1.0), (_nrm(stop), 3.3, 0.8)]), "corridor", 0.2)


@sound("c2x_wedge_pull", "sfx", "The wedge pin is pulled from the blocked spiral stair: wood squeals out of a tight fit, a knock, a clatter down the steps")
def c2x_wedge_pull(rng):
    d = 0.9
    m = n_of(d)
    sq = kit.creak(rng, d, env.curve([(0, 28), (d * 0.7, 75), (d, 120)], m), env.curve([(0, 0), (d * 0.3, 1), (d * 0.9, 0.9), (d, 0)], m, "cos"),
                   modal.wood(rng, 250, 2200, 10, 0.1), jitter=0.12, hiss=0.04, hiss_band=(800, 2800))
    pop = kit.knock(rng, 150, 1600, 8, t60=0.06, contact=0.0008, dur=0.15, noise_amt=0.2)
    cl = _mix(0.9, [(kit.knock(rng, 200 + 40 * k, 2000, 7, t60=0.05, contact=0.0008, dur=0.1), 0.0 + 0.1 * k * (1 + 0.1 * k), 0.8 / (1 + 0.3 * k)) for k in range(6)])
    stair = _mix(0.9, [(modal.strike(_iron(rng.uniform(400, 700), 0.2, rng, 3), 0.3, 0.0005, rng), 0.12 * k + 0.02, 0.35 / (1 + 0.4 * k)) for k in range(5)])
    return _room(_mix(2.4, [(_nrm(sq), 0.0, 0.6), (_nrm(pop), 0.9, 1.0), (_nrm(cl), 1.0, 0.45), (_nrm(stair), 1.05, 0.3)]), "corridor", 0.2)


@sound("c2x_stair_steps", "sfx", "Climbing the iron spiral stair: six slow footsteps on steel treads, each with a soft ring")
def c2x_stair_steps(rng):
    out = np.zeros(n_of(3.2))
    for k in range(6):
        thud = _lp(kit.thump(130, 80, 0.15, 0.07), 500)
        ring = modal.strike(_iron(rng.uniform(300, 480), 0.35, rng, 4), 0.5, 0.001, rng, noise=0.3)
        t0 = 0.1 + 0.46 * k + rng.uniform(-0.02, 0.02)
        add_at(out, _nrm(thud), t0, 0.8)
        add_at(out, _nrm(ring), t0, 0.25)
    return _room(out, "corridor", 0.25)


# ---- walking (version 1.1: camera travel) ------------------------------------------------------------

def _footstep(rng, body, scuff_hi):
    """One soft shoe step on old floor: a dull low thud and a short, quiet scuff of the sole."""
    thud = _lp(kit.thump(body, body * 0.55, 0.16, 0.07, glide=0.02, harm=0.15), 700)
    scuff = _bp(_band_noise(rng, 0.09, 500, scuff_hi), 500, scuff_hi) * env.curve([(0, 0), (0.008, 1), (0.09, 0)], n_of(0.09), "lin")
    return _mix(0.2, [(_nrm(thud), 0.0, 0.85), (_nrm(scuff), 0.004, 0.22)])


@sound("c2x_step_soft_a", "sfx", "One soft footstep on the old floor (camera travel, left foot): a dull low thud and a quiet scuff of the sole")
def c2x_step_soft_a(rng):
    return _room(_footstep(rng, 120, 2600), "corridor", 0.1)


@sound("c2x_step_soft_b", "sfx", "One soft footstep on the old floor (camera travel, right foot): slightly lighter and a little higher than the left")
def c2x_step_soft_b(rng):
    return _room(_footstep(rng, 142, 3200), "corridor", 0.1)


@sound("c2x_stair_climb", "sfx", "A short climb on the iron stair (camera travel): five quick steps on steel treads, each with a faint ring")
def c2x_stair_climb(rng):
    out = np.zeros(n_of(1.4))
    for k in range(5):
        thud = _lp(kit.thump(150, 90, 0.12, 0.05), 600)
        ring = modal.strike(_iron(rng.uniform(320, 520), 0.25, rng, 4), 0.35, 0.001, rng, noise=0.3)
        t0 = 0.05 + 0.2 * k + rng.uniform(-0.01, 0.01)
        add_at(out, _nrm(thud), t0, 0.8)
        add_at(out, _nrm(ring), t0, 0.2)
    return _room(out, "corridor", 0.2)


# ---- N8 roll-call board ----------------------------------------------------------------------------

@sound("c2x_tag_hook", "sfx", "A staff tag is hung on a board hook: a brass hook tick and the tag swinging against wood")
def c2x_tag_hook(rng):
    hk = kit.tick(rng, 2500, 8000, 14, t60=0.05, contact=0.0002, dur=0.1)
    wd = kit.knock(rng, 250, 2800, 8, t60=0.05, contact=0.0008, dur=0.12, noise_amt=0.2)
    return _room(_mix(0.45, [(_nrm(hk), 0.0, 0.9), (_nrm(wd), 0.06, 0.55), (_nrm(wd), 0.17, 0.25)]), "lab", 0.1)


@sound("c2x_tag_lift", "sfx", "A staff tag is lifted off its hook: a light tick and a small slide")
def c2x_tag_lift(rng):
    sl = kit.friction(rng, 0.12, env.curve([(0, 1), (0.12, 0)], n_of(0.12), "lin"), 1500, 5000, grit=0.3) * 0.6
    hk = kit.tick(rng, 2500, 8000, 10, t60=0.04, contact=0.0002, dur=0.08)
    return _room(_mix(0.3, [(_nrm(sl), 0.0, 0.4), (_nrm(hk), 0.1, 0.8)]), "lab", 0.08)


@sound("c2x_board_ok", "sfx", "The tags hang in the right order: a soft rattle of all six, a wood clack and a tiny key dropping into the tray")
def c2x_board_ok(rng):
    rt = _mix(0.7, [(kit.tick(rng, 2000, 7500, 10, t60=0.04, contact=0.0003, dur=0.08), 0.07 * k + rng.uniform(0, 0.03), 0.5) for k in range(6)])
    cl = kit.knock(rng, 200, 2500, 9, t60=0.07, contact=0.001, dur=0.2, noise_amt=0.2)
    key = modal.strike(_iron(1900.0, 0.5, rng, 4), 0.7, 0.0003, rng, noise=0.2)
    return _room(_mix(1.7, [(_nrm(rt), 0.0, 0.5), (_nrm(cl), 0.75, 0.9), (_nrm(key), 1.0, 0.5)]), "corridor", 0.14)


@sound("c2x_board_wrong", "sfx", "The tags do not agree with the slips: a dull wooden rattle, nothing happens")
def c2x_board_wrong(rng):
    rt = _mix(0.6, [(_lp(kit.knock(rng, 200, 2000, 7, t60=0.03, contact=0.0008, dur=0.08), 2500), 0.08 * k, 0.6 - 0.08 * k) for k in range(5)])
    return _room(rt, "lab", 0.08)


# ---- N9 enlarger -----------------------------------------------------------------------------------

@sound("c2x_enlarger_lamp", "sfx", "Enlarger lamp: a switch click, a thump of the transformer and a warm lamp glow that holds a moment, then a click off")
def c2x_enlarger_lamp(rng):
    n = n_of(1.5)
    t = time_axis(n)
    hum = (np.sin(2 * np.pi * 100 * t) + 0.4 * np.sin(2 * np.pi * 200 * t)) * env.curve([(0, 0), (0.02, 1), (0.4, 0.7), (1.0, 0.7), (1.05, 0.0)], n, "lin")
    on = kit.relay(rng, 0.9)
    off = kit.relay(rng, 0.6)
    return _room(_mix(1.5, [(_nrm(on), 0.0, 0.9), (_nrm(hum), 0.0, 0.25), (_nrm(off), 1.05, 0.7)]), "lab", 0.1)


@sound("c2x_enlarger_knob", "sfx", "Enlarger zoom or head knob turned a step: a small geared detent click and a brief ring")
def c2x_enlarger_knob(rng):
    a = _sum(kit.tick(rng, 1500, 6000, 12, t60=0.04, contact=0.0003, dur=0.1), 0.5 * kit.knock(rng, 250, 1800, 6, t60=0.03, dur=0.08))
    b = kit.tick(rng, 1200, 5000, 10, t60=0.03, contact=0.0003, dur=0.08)
    return _room(_mix(0.3, [(_nrm(a), 0.0, 1.0), (_nrm(b), 0.07, 0.4)]), "lab", 0.06)


@sound("c2x_enlarger_focus", "sfx", "Enlarger focus ring: a smooth knurled ring turning, fine ticks, a soft end stop")
def c2x_enlarger_focus(rng):
    d = 0.5
    fr = kit.friction(rng, d, env.curve([(0, 0), (0.06, 1), (0.4, 0.8), (d, 0)], n_of(d), "cos"), 1200, 5000, grit=0.5, grit_rate=1800)
    stop = kit.tick(rng, 1500, 5500, 10, t60=0.03, contact=0.0004, dur=0.08)
    return _room(_mix(0.7, [(_nrm(_lp(fr, 5000)), 0.0, 0.5), (_nrm(stop), 0.48, 0.7)]), "lab", 0.06)


@sound("c2x_enlarger_fan", "sfx", "Enlarger lamp-house fan (seamless 4 s loop for sfx_loop): a small fan with a 20 Hz blade beat over a soft 100 Hz hum",
       loop=True)
def c2x_enlarger_fan(rng):
    d = 4.0
    n = n_of(d)
    t = time_axis(n)
    blade = 1.0 + 0.3 * np.sin(2 * np.pi * 20.0 * t)
    hum = np.sin(2 * np.pi * 100 * t) + 0.4 * np.sin(2 * np.pi * 200 * t) + 0.2 * np.sin(2 * np.pi * 300 * t)
    air = noise.colored(n, rng, -3.0, 120, 900)          # FFT-built, so exactly periodic
    return 0.4 * _nrm(hum) + 0.6 * _nrm(air) * blade


@sound("c2x_strip_load", "sfx", "A negative strip is slid into the carrier: a smooth film slide and a small click as the carrier closes")
def c2x_strip_load(rng):
    sl = kit.friction(rng, 0.3, env.curve([(0, 0), (0.05, 1), (0.3, 0)], n_of(0.3), "cos"), 1200, 4500, grit=0.15)
    cl = _sum(kit.tick(rng, 1500, 6000, 12, t60=0.04, contact=0.0003, dur=0.1), 0.5 * kit.knock(rng, 300, 2000, 6, t60=0.03, dur=0.08))
    return _room(_mix(0.6, [(_nrm(_lp(sl, 4500)), 0.0, 0.5), (_nrm(cl), 0.3, 0.9)]), "lab", 0.08)


@sound("c2x_print_ready", "sfx", "The print develops in the tray: paper slips into the liquid, a gentle slosh, a few drops (1.8 s)")
def c2x_print_ready(rng):
    n = n_of(1.8)
    sl = kit.friction(rng, 0.25, env.curve([(0, 0), (0.05, 1), (0.25, 0)], n_of(0.25), "cos"), 1000, 4500, grit=0.1)
    sg = _bp(noise.colored(n, rng, -4.0, 180, 1100), 180, 1100) * (0.5 + 0.5 * np.sin(2 * np.pi * 1.6 * time_axis(n)) ** 2) * env.curve([(0, 0), (0.3, 1), (1.8, 0)], n, "cos")
    dr = _mix(1.8, [(_nrm(biquad(kit.drop(rng, dur=0.1), "lowpass", 3500, 0.7)), 0.6 + 0.35 * k, 0.5) for k in range(3)])
    return _room(_mix(1.8, [(_nrm(_lp(sl, 4500)), 0.0, 0.4), (_nrm(sg), 0.1, 0.6), (_nrm(dr), 0.0, 0.5)]), "lab", 0.12)


# ---- N10 cabinet -----------------------------------------------------------------------------------

@sound("c2x_cab_wheel", "sfx", "Cabinet digit wheel advances one number: a crisp brass tick with a tiny barrel click")
def c2x_cab_wheel(rng):
    a = kit.tick(rng, 1800, 7000, 12, t60=0.035, contact=0.0003, dur=0.09)
    b = kit.knock(rng, 400, 2500, 6, t60=0.02, contact=0.0004, dur=0.05, noise_amt=0.3)
    return _room(_mix(0.2, [(_nrm(a), 0.0, 1.0), (_nrm(b), 0.025, 0.4)]), "lab", 0.05)


@sound("c2x_cab_open", "sfx", "Strand's cabinet opens: the last wheel seats, a latch drops, a wooden drawer slides out and a lamp glass rolls and clinks")
def c2x_cab_open(rng):
    seat = kit.tick(rng, 1800, 7000, 12, t60=0.04, contact=0.0003, dur=0.1)
    latch = kit.clank(rng, 300, 3500, 14, t60=0.15, contact=0.0006, dur=0.25, noise_amt=0.2)
    dr = kit.friction(rng, 0.7, env.curve([(0, 0), (0.08, 1), (0.6, 0.6), (0.7, 0)], n_of(0.7), "cos"), 120, 1800, body=modal.wood(rng, 150, 1400, 8, 0.15), body_gain=0.8, grit=0.3)
    stop = kit.knock(rng, 120, 1000, 7, t60=0.08, contact=0.002, dur=0.2, noise_amt=0.1)
    glass = modal.strike(modal.glass(2600.0, 0.4, 0.4), 0.6, 0.0003, rng, noise=0.1)
    return _room(_mix(2.0, [(_nrm(seat), 0.0, 0.6), (_nrm(latch), 0.2, 0.9), (_nrm(_lp(dr, 3000)), 0.55, 0.5), (_nrm(stop), 1.2, 0.8),
                            (_nrm(glass), 1.35, 0.3), (_nrm(glass), 1.5, 0.15)]), "lab", 0.12)


# ---- projector lamp, plan, refusals ----------------------------------------------------------------

@sound("c2x_lamp_fail", "sfx", "The booth projector lamp is dead: a dull filament tink, a weak electrical sigh dropping in pitch")
def c2x_lamp_fail(rng):
    n = n_of(1.0)
    t = time_axis(n)
    f = 380 * np.exp(-3.0 * t)
    sg = _lp(osc.saw(f, n), 1200) * env.curve([(0, 0), (0.03, 1), (0.6, 0.0)], n, "cos")
    tink = modal.strike(modal.glass(1900.0, 0.2, 0.4), 0.3, 0.0003, rng, noise=0.2)
    return _room(_mix(1.0, [(_nrm(tink), 0.0, 0.8), (_nrm(sg), 0.04, 0.35)]), "lab", 0.1)


@sound("c2x_lamp_fit", "sfx", "The new projector lamp is fitted: a glass bulb turned into the socket, a clink, the filament warming up in pitch and a soft tick")
def c2x_lamp_fit(rng):
    d = 0.5
    m = n_of(d)
    tw = kit.creak(rng, d, env.curve([(0, 60), (d, 110)], m), np.hanning(m), modal.glass(rng.uniform(2200, 3000), 0.1, 0.4), jitter=0.08, hiss=0.05, hiss_band=(1500, 4000))
    cl = modal.strike(modal.glass(2100.0, 0.5, 0.45), 0.6, 0.0003, rng, noise=0.2)
    n = n_of(1.3)
    t = time_axis(n)
    fil = np.sin(2 * np.pi * np.cumsum(180 + 380 * (1 - np.exp(-2.2 * t))) / SR) * env.curve([(0, 0), (0.15, 0.6), (0.9, 1), (1.3, 0)], n, "cos")
    tick = kit.relay(rng, 0.5)
    return _room(_mix(2.0, [(_nrm(tw), 0.0, 0.4), (_nrm(cl), 0.55, 0.7), (_nrm(fil), 0.6, 0.3), (_nrm(tick), 1.2, 0.5)]), "lab", 0.12)


@sound("c2x_refused", "sfx", "A closed room or lift floor is tried: two dull wooden taps, calm, no alarm")
def c2x_refused(rng):
    a = _lp(kit.knock(rng, 150, 1200, 8, t60=0.05, contact=0.002, dur=0.15, noise_amt=0.1), 1600)
    return _room(_mix(0.5, [(_nrm(a), 0.0, 1.0), (_nrm(a), 0.2, 0.65)]), "lab", 0.08)


@sound("c2x_plan_unfold", "sfx", "The floor plan is unfolded: crisp paper creases and a soft rustle")
def c2x_plan_unfold(rng):
    n = n_of(0.9)
    pap = _bp(noise.colored(n, rng, -2.0, 700, 4200), 700, 4200) * env.curve([(0, 0), (0.05, 1), (0.9, 0)], n, "cos") * (
        0.5 + 0.5 * np.abs(noise.smooth_random(n, rng, 14, periodic=False)))
    cr = _mix(0.9, [(kit.tick(rng, 1500, 5500, 6, t60=0.02, dur=0.04), 0.07 * k + rng.uniform(0, 0.04), 0.5) for k in range(8)])
    return _room(_mix(0.9, [(_nrm(pap), 0.0, 0.6), (_nrm(cr), 0.0, 0.5)]), "lab", 0.05)
