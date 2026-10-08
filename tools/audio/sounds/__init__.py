"""Sound registry. Each sound is a function ``fn(rng) -> np.ndarray`` registered
with the ``@sound`` decorator together with its export settings."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

CATEGORY_DIRS = {"ui": "sfx", "sfx": "sfx", "ambience": "ambience", "music": "music"}


@dataclass
class SoundSpec:
    name: str
    category: str          # 'ui' | 'sfx' | 'ambience' | 'music'
    fn: Callable[[np.random.Generator], np.ndarray]
    desc: str
    loop: bool = False
    peak_db: float | None = None   # one-shots: peak normalisation target (dBFS)
    lufs: float | None = None      # music/ambience: integrated loudness target
    source: str = "synth"          # 'synth' or a note about CC0 source files
    fade_out: float = 0.03
    tags: list[str] = field(default_factory=list)

    @property
    def stereo(self) -> bool:
        return self.category in ("ambience", "music")

    @property
    def subdir(self) -> str:
        return CATEGORY_DIRS[self.category]


REGISTRY: dict[str, SoundSpec] = {}


def sound(name: str, category: str, desc: str, **kw):
    if category not in CATEGORY_DIRS:
        raise ValueError(category)
    if "peak_db" not in kw and category in ("ui", "sfx"):
        kw["peak_db"] = -6.0 if category == "ui" else -1.0

    def deco(fn):
        if name in REGISTRY:
            raise ValueError(f"duplicate sound {name}")
        REGISTRY[name] = SoundSpec(name, category, fn, desc, **kw)
        return fn
    return deco


MODULES = ("ui", "mechanisms", "electrical", "story", "ambience", "music_tracks")


def load_all() -> dict[str, SoundSpec]:
    """Import every sound module; importing registers its ``@sound`` functions."""
    import importlib
    for mod in MODULES:
        importlib.import_module(f"{__name__}.{mod}")
    return REGISTRY
