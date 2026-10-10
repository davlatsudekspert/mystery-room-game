#!/usr/bin/env python3
"""Validate all strings and write game/localization/strings.csv (keys,en,ru,uz).
Run after editing any strings_*.py:  python3 tools/localization/build_csv.py"""
import csv, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from strings_core import S as CORE
from strings_ch1 import S as CH1
from strings_hints import H
from strings_ch2 import S as CH2, H as H2
from strings_ch3 import S as CH3, H as H3
from strings_ch4 import S as CH4, H as H4
from strings_menu import S as MENU

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "game", "localization", "strings.csv")
LANGS = ["en", "ru", "uz"]  # fixed order: EN (default) → RU → UZ (Latin)

rows = list(CORE) + list(CH1) + list(CH2) + list(CH3) + list(CH4) + list(MENU)
for goal, levels in list(H.items()) + list(H2.items()) + list(H3.items()) + list(H4.items()):
    assert len(levels) == 3, goal
    for i, (en, ru, uz) in enumerate(levels, 1):
        rows.append((f"hint.{goal}.{i}", en, ru, uz))

errors = []
seen = set()
CYR = re.compile(r"[А-Яа-яЁё]")
BAD_UZ_APOS = re.compile(r"[oOgG]['‘’`]")
for key, *vals in rows:
    if key in seen:
        errors.append(f"duplicate key {key}")
    seen.add(key)
    ph = [sorted(re.findall(r"%[sd]", v)) for v in vals]
    if any(p != ph[0] for p in ph):
        errors.append(f"{key}: placeholder mismatch {ph}")
    en, ru, uz = vals
    allow_empty = key == "doc.notebook.p5"
    if not allow_empty and not all(v.strip() for v in vals):
        errors.append(f"{key}: empty translation")
    if CYR.search(uz):
        errors.append(f"{key}: Cyrillic in Uzbek (must be Latin): {uz}")
    if BAD_UZ_APOS.search(uz):
        errors.append(f"{key}: use ʻ (U+02BB) for oʻ/gʻ in Uzbek: {uz}")
    if CYR.search(en):
        errors.append(f"{key}: Cyrillic in English")
    if ru.strip() and not CYR.search(ru) and not key.startswith(("game.title", "obj.poster")) and re.search(r"[A-Za-z]{4,}", ru) and key not in ("game.title",):
        errors.append(f"{key}: Russian text has no Cyrillic: {ru}")
if errors:
    print("\n".join(errors))
    sys.exit(1)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    w.writerow(["keys"] + LANGS)
    for key, en, ru, uz in rows:
        w.writerow([key] + [v.replace("\n", "\\n") for v in (en, ru, uz)])
print(f"wrote {len(rows)} keys → {OUT}")
