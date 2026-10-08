"""Access to the few CC0 recordings kept in ``tools/audio/sources``
(see that folder's license files and docs/ASSET_LICENSES.md)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np

from .export import decode

SOURCES = Path(__file__).resolve().parent.parent / "sources"


@lru_cache(maxsize=None)
def _load(rel: str) -> np.ndarray:
    return decode(str(SOURCES / rel), channels=1)


def load(rel: str) -> np.ndarray:
    """Decode a source file to mono float64 at 44.1 kHz, DC-free and
    normalised to a 0 dBFS peak (a fresh copy each call)."""
    x = _load(rel)
    x = x - np.mean(x)
    return x / max(np.max(np.abs(x)), 1e-12)
