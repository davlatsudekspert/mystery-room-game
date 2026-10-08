"""WAV/OGG export and loudness measurement through ffmpeg."""
from __future__ import annotations

import json
import re
import subprocess

import numpy as np
from scipy.io import wavfile

from .core import SR


def write_wav(path: str, x: np.ndarray) -> None:
    """32-bit float WAV (channels-last on disk)."""
    data = x.T if x.ndim == 2 else x
    wavfile.write(path, SR, np.ascontiguousarray(data, dtype=np.float32))


def encode_ogg(wav_path: str, ogg_path: str, channels: int, quality: float = 5.0) -> None:
    """libvorbis VBR. ``bitexact`` flags make the output byte-identical between
    runs (fixed stream serial, no encoder-version tag)."""
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", wav_path,
           "-map_metadata", "-1", "-ac", str(channels), "-ar", str(SR),
           "-c:a", "libvorbis", "-q:a", f"{quality:g}",
           "-fflags", "+bitexact", "-flags:a", "+bitexact", ogg_path]
    subprocess.run(cmd, check=True)


def decode(path: str, channels: int | None = None) -> np.ndarray:
    """Decode an audio file to float64 at ``SR`` (shape like core signals).

    Uses SoX (libvorbisfile), which honours Ogg granule positions and returns
    the exact sample count - ffmpeg's native Vorbis decoder can be off by
    some samples at the end, which would invalidate loop-seam checks."""
    if channels is None:
        probe = subprocess.run(["soxi", "-c", path], check=True, capture_output=True, text=True)
        channels = int(probe.stdout.strip())
    raw = subprocess.run(["sox", "-V1", path, "-t", "raw", "-e", "floating-point", "-b", "32",
                          "-c", str(channels), "-r", str(SR), "-"], check=True, capture_output=True).stdout
    data = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    if channels == 1:
        return data
    return data.reshape(-1, channels).T


def loudness(path: str) -> dict:
    """EBU R128 measurement via ffmpeg's loudnorm (first pass, JSON)."""
    res = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-i", path, "-af",
                          "loudnorm=print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True, check=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", res.stderr, re.S)
    if not m:
        raise RuntimeError("loudnorm output not found")
    d = json.loads(m.group(0))
    return {"integrated_lufs": float(d["input_i"]), "true_peak_dbtp": float(d["input_tp"]),
            "lra": float(d["input_lra"])}
