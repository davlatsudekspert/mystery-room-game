#!/usr/bin/env python3
"""Download the game's SIL OFL fonts from the google/fonts repository.

Writes into game/assets/fonts/:
    CormorantGaramond-SemiBold.ttf   static wght=600 instance of CormorantGaramond[wght].ttf
    CormorantGaramond-Bold.ttf       static wght=700 instance
    CormorantGaramond-OFL.txt
    NotoSans-Variable.ttf            NotoSans[wdth,wght].ttf, unchanged (UI / body)
    NotoSans-OFL.txt
    Caveat-Variable.ttf              Caveat[wght].ttf, unchanged (handwriting)
    Caveat-OFL.txt

The static Cormorant instances are made with fontTools.varLib.instancer. That is
a "Modified Version" under the OFL, which is allowed: none of these families
declares a Reserved Font Name, and the result stays under the OFL (licence
text shipped alongside).

Usage (from the repository root):  python3 tools/fonts/fetch_fonts.py
Requires: fontTools. Network: raw.githubusercontent.com
"""
from __future__ import annotations

import io
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "game" / "assets" / "fonts"
BASE = "https://raw.githubusercontent.com/google/fonts/main/ofl"

FAMILIES = {
    # family dir: (source file, license file name, outputs)
    "cormorantgaramond": ("CormorantGaramond[wght].ttf", "CormorantGaramond-OFL.txt",
                          [("CormorantGaramond-SemiBold.ttf", {"wght": 600}),
                           ("CormorantGaramond-Bold.ttf", {"wght": 700})]),
    "notosans": ("NotoSans[wdth,wght].ttf", "NotoSans-OFL.txt",
                 [("NotoSans-Variable.ttf", None)]),
    "caveat": ("Caveat[wght].ttf", "Caveat-OFL.txt",
               [("Caveat-Variable.ttf", None)]),
}


def get(url: str) -> bytes:
    last = None
    for i in range(5):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"download failed: {url}: {last}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for fam, (src, lic_name, outputs) in FAMILIES.items():
        meta = get(f"{BASE}/{fam}/METADATA.pb").decode("utf-8")
        if not re.search(r'^license:\s*"OFL"', meta, re.M):
            raise SystemExit(f"{fam}: METADATA.pb does not declare license OFL")
        lic = get(f"{BASE}/{fam}/OFL.txt").decode("utf-8")
        if "SIL Open Font License, Version 1.1" not in lic:
            raise SystemExit(f"{fam}: OFL.txt is not SIL OFL 1.1")
        (OUT / lic_name).write_text(lic)
        data = get(f"{BASE}/{fam}/{urllib.parse.quote(src)}")
        for out_name, location in outputs:
            if location:
                font = TTFont(io.BytesIO(data))
                font = instancer.instantiateVariableFont(font, location, updateFontNames=True)
                font.save(OUT / out_name)
            else:
                (OUT / out_name).write_bytes(data)  # ship upstream bytes unchanged
            print(f"  {fam}: {out_name} ({(OUT / out_name).stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
