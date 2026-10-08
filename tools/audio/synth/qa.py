"""Quality checks: spectrogram PNGs (numpy + Pillow) and simple metrics."""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from .core import SR, to_mono, length

# A perceptual dark->bright colour ramp (approximation of 'magma').
_RAMP = np.array([
    [0, 0, 4], [28, 16, 68], [79, 18, 123], [129, 37, 129],
    [181, 54, 122], [229, 80, 100], [251, 135, 97], [254, 194, 135], [252, 253, 191],
], dtype=np.float64)


def _colour(v: np.ndarray) -> np.ndarray:
    v = np.clip(v, 0, 1) * (len(_RAMP) - 1)
    i = np.minimum(v.astype(int), len(_RAMP) - 2)
    f = (v - i)[..., None]
    return (_RAMP[i] * (1 - f) + _RAMP[i + 1] * f).astype(np.uint8)


def spectrogram_png(x: np.ndarray, path: str, title: str, width: int = 1200,
                    height: int = 360, floor_db: float = -110.0) -> None:
    """Waveform strip + log-frequency spectrogram (30 Hz .. 22 kHz, dBFS)."""
    m = to_mono(x)
    n = length(m)
    nfft = 1024 if n < SR else (2048 if n < 4 * SR else 4096)
    hop = max(64, int(np.ceil(max(n - nfft, 1) / width)))
    pad = np.pad(m, (nfft // 2, nfft // 2 + hop))
    frames = 1 + (len(pad) - nfft) // hop
    win = np.hanning(nfft)
    idx = np.arange(nfft)[None, :] + hop * np.arange(frames)[:, None]
    spec = np.abs(np.fft.rfft(pad[idx] * win, axis=1)) * (2.0 / win.sum())
    sdb = 20 * np.log10(spec + 1e-12)
    freqs = np.fft.rfftfreq(nfft, 1.0 / SR)
    rows = np.geomspace(30.0, SR / 2, height)[::-1]
    col = np.empty((height, frames))
    for c in range(frames):
        col[:, c] = np.interp(rows, freqs, sdb[c])
    img_spec = _colour((col - floor_db) / -floor_db)
    img_spec = np.array(Image.fromarray(img_spec).resize((width, height), Image.BILINEAR))

    wave_h = 90
    wave = np.full((wave_h, width, 3), 16, dtype=np.uint8)
    chunks = np.array_split(m, width)
    for xpix, ch in enumerate(chunks):
        if ch.size == 0:
            continue
        lo, hi = ch.min(), ch.max()
        y0 = int((1 - (hi + 1) / 2) * (wave_h - 1))
        y1 = int((1 - (lo + 1) / 2) * (wave_h - 1))
        clipped = max(abs(lo), abs(hi)) >= 0.999
        wave[y0:y1 + 1, xpix] = (255, 60, 60) if clipped else (120, 200, 255)
    wave[wave_h // 2, :] = (60, 60, 60)
    canvas = np.vstack([np.full((22, width, 3), 0, dtype=np.uint8), wave, img_spec])
    im = Image.fromarray(canvas)
    d = ImageDraw.Draw(im)
    pk = 20 * np.log10(np.max(np.abs(m)) + 1e-12)
    d.text((6, 4), f"{title}   {n / SR:.2f}s   peak {pk:.1f} dBFS", fill=(230, 230, 230))
    top = 22 + wave_h
    for f in (50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000):
        y = top + int(np.interp(np.log(f), np.log(rows[::-1]), np.arange(height)[::-1]))
        d.line([(0, y), (8, y)], fill=(200, 200, 200))
        d.text((10, y - 6), f"{f // 1000}k" if f >= 1000 else str(f), fill=(200, 200, 200))
    im.save(path)
