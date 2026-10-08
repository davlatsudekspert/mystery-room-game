"""Convolution reverb with synthesised impulse responses.

An IR is built from decorrelated noise split into frequency bands, each with
its own exponential decay (high bands die faster, like a real room with wood
panels and air absorption), plus a handful of discrete early reflections."""
from __future__ import annotations

from functools import lru_cache

import numpy as np
from scipy import signal as _sig

from .core import SR, n_of, raised_cos, to_stereo, length
from .env import LN1000

# Band edges (Hz) and centre points used to interpolate the per-band RT60.
_BAND_EDGES = [0, 180, 400, 900, 2000, 4500, 9000, 22050]


def synth_ir(rt60: float, seed: int, *, length_s: float | None = None, stereo: bool = True,
             predelay: float = 0.01, lf_ratio: float = 1.25, hf_ratio: float = 0.45,
             early: int = 10, early_span: float = 0.06, early_gain: float = 0.6,
             onset: float = 0.02, tone_hi: float = 12000.0) -> np.ndarray:
    """Return an energy-normalised IR, shape (2, n) if ``stereo`` else (n,).

    rt60      mid-band reverberation time (s)
    lf_ratio  RT60 multiplier at the lowest band, hf_ratio at the highest
    early     number of discrete early reflections in ``early_span`` seconds
    onset     raised-cosine build-up of the diffuse tail (s)
    tone_hi   gentle overall high cut of the tail (Hz)
    """
    rng = np.random.default_rng(seed)
    L = n_of(length_s if length_s is not None else rt60 * 1.15 + predelay + 0.05)
    t = np.arange(L) / SR
    f = np.fft.rfftfreq(L, 1.0 / SR)
    nb = len(_BAND_EDGES) - 1
    # Complementary band masks: M_b = C_b - C_{b+1} sums to exactly 1, so
    # the bands recombine to a flat spectrum before the decays are applied.
    lf = np.log2(np.maximum(f, 1e-3))
    cross = [np.ones_like(f)]
    for edge in _BAND_EDGES[1:-1]:
        u = np.clip((lf - np.log2(edge)) / 0.6 + 0.5, 0.0, 1.0)
        cross.append(0.5 - 0.5 * np.cos(np.pi * u))
    cross.append(np.zeros_like(f))
    masks = [cross[b] - cross[b + 1] for b in range(nb)]
    b_hc, a_hc = _sig.butter(2, min(tone_hi, SR * 0.45), fs=SR)
    b_er, a_er = _sig.butter(1, 6000, fs=SR)
    pd = n_of(predelay)
    on = min(n_of(onset), L - pd)
    chans = []
    for _ in range(2 if stereo else 1):
        noise_spec = np.fft.rfft(rng.standard_normal(L))
        tail = np.zeros(L)
        for b in range(nb):
            u = b / (nb - 1)  # log-interpolated RT60 per band
            band_rt = max(rt60 * np.exp(np.log(lf_ratio) * (1 - u) + np.log(hf_ratio) * u), 0.02)
            tail += np.fft.irfft(noise_spec * masks[b], n=L) * np.exp(-LN1000 * t / band_rt)
        tail = _sig.lfilter(b_hc, a_hc, tail)
        shaped = np.zeros(L)
        shaped[pd:] = tail[:L - pd]
        shaped[pd:pd + on] *= raised_cos(on)
        if early > 0:  # sparse, decaying early reflections with random sign
            er = np.zeros(L)
            taps = np.sort(rng.uniform(predelay * 0.5, predelay + early_span, early))
            for i, tt in enumerate(taps):
                k = n_of(tt)
                if k < L:
                    er[k] += rng.choice([-1.0, 1.0]) * (1.0 - 0.6 * i / early) * rng.uniform(0.6, 1.0)
            er = _sig.lfilter(b_er, a_er, er)
            ref = np.max(np.abs(shaped[:pd + on + n_of(early_span)]))
            shaped += er * (early_gain * ref / max(np.max(np.abs(er)), 1e-12))
        chans.append(shaped)
    ir = np.vstack(chans) if stereo else chans[0]
    ir /= np.sqrt(np.sum(ir ** 2) / (2 if stereo else 1))
    return ir


@lru_cache(maxsize=None)
def preset(name: str, stereo: bool = False) -> np.ndarray:
    """Named, cached IRs shared by the sound definitions."""
    s = 101 if stereo else 0
    if name == "lab":       # walnut-panelled lab: short, warm, quite damped
        return synth_ir(0.55, 7001 + s, stereo=stereo, predelay=0.006, hf_ratio=0.35,
                        early=12, early_span=0.04, tone_hi=9000)
    if name == "corridor":  # stone corridor behind the door: longer, brighter
        return synth_ir(1.4, 7002 + s, stereo=stereo, predelay=0.012, hf_ratio=0.5,
                        early=14, early_span=0.07, tone_hi=10000)
    if name == "plate":     # bright, dense, for glassy/magical one-shots
        return synth_ir(2.2, 7003 + s, stereo=stereo, predelay=0.015, lf_ratio=0.9,
                        hf_ratio=0.7, early=0, onset=0.005, tone_hi=14000)
    if name == "ui_plate":  # short, soft plate so UI feedback stays crisp
        return synth_ir(0.9, 7007 + s, stereo=stereo, predelay=0.008, lf_ratio=0.8,
                        hf_ratio=0.5, early=0, onset=0.004, tone_hi=11000)
    if name == "hall":      # deep music hall
        return synth_ir(4.8, 7004 + s, stereo=stereo, predelay=0.035, lf_ratio=1.3,
                        hf_ratio=0.4, early=16, early_span=0.09, onset=0.06, tone_hi=9000)
    if name == "hall_dark":  # darker, shorter hall for the gameplay music
        return synth_ir(3.6, 7005 + s, stereo=stereo, predelay=0.03, lf_ratio=1.3,
                        hf_ratio=0.3, early=16, early_span=0.08, onset=0.06, tone_hi=6500)
    if name == "room_amb":  # the lab as heard in the ambience bed
        return synth_ir(0.9, 7006 + s, stereo=stereo, predelay=0.008, hf_ratio=0.35,
                        early=12, early_span=0.05, tone_hi=8000)
    raise KeyError(name)


def convolve(x: np.ndarray, ir: np.ndarray) -> np.ndarray:
    """Full linear convolution. Mono x with stereo IR gives stereo output;
    stereo x with stereo IR convolves channel-wise."""
    if ir.ndim == 2 or x.ndim == 2:
        xs, irs = to_stereo(x), to_stereo(ir)
        return np.vstack([_sig.oaconvolve(xs[c], irs[c]) for c in range(2)])
    return _sig.oaconvolve(x, ir)


def reverb(x: np.ndarray, ir: np.ndarray, wet: float, dry: float = 1.0) -> np.ndarray:
    """Dry/wet mix; output is extended by the IR length so tails are kept."""
    w = convolve(x, ir)
    out = wet * w
    if x.ndim == 1 and out.ndim == 2:
        out[:, :length(x)] += dry * x
    else:
        out[..., :length(x)] += dry * x
    return out


def reverb_circular(x: np.ndarray, ir: np.ndarray, wet: float, dry: float = 1.0) -> np.ndarray:
    """Reverb for loops: the tail that rings past the end is wrapped onto the
    start (overlap-add), i.e. circular convolution, so the loop is seamless."""
    from .loops import wrap_tail
    n = length(x)
    full = reverb(x, ir, wet, dry)
    return wrap_tail(full, n)
