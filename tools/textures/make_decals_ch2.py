#!/usr/bin/env python3
"""Chapter 2 (Records Archive B) decals, glyphs, film frames and the linoleum texture set.

Original procedural artwork (PIL + numpy only, no third-party images). Outputs:
    game/assets/textures/decals/ch2/*.png|jpg     decals, glyphs, film frames (table: docs/models/ch2_decals.md)
    game/assets/textures/linoleum/{albedo.jpg, normal.png, orm.jpg}   M_Linoleum (seamless, 0.6 m repeat)
    qa/decals_ch2_contact_sheet.jpg               labelled QA sheet of everything above (EN)
    qa/decals_ch2_lang_sheet.jpg                  the localized decals as EN | RU | UZ

Puzzle data MUST match game/src/rooms/archive/archive_logic.gd and docs/CHAPTER2_DESIGN.md.

Decals with readable words are written in EN (<name>.<ext>), RU (<name>_ru.<ext>) and UZ (<name>_uz.<ext>);
see LOCALIZED and TXT. qa/decals_ch2_lang_sheet.jpg shows them side by side.

    python3 tools/textures/make_decals_ch2.py                       # everything + both QA sheets
    python3 tools/textures/make_decals_ch2.py --only badge,index_card --langs ru,uz --no-sheet
    python3 tools/textures/make_decals_ch2.py --sheet-only
"""
from __future__ import annotations

import argparse
import math
import os
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# make_decals only creates its (existing) output folders and seeds its own RNGs at import time.
from make_decals import aged_paper, noise  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "textures", "decals", "ch2")
TEX = os.path.join(ROOT, "game", "assets", "textures")
QA = os.path.join(ROOT, "qa")

# ---- puzzle data (mirrors archive_logic.gd) -------------------------------------------------
BADGE_NO = "0417"
PUNCH_CODE = [1, 0, 1, 1, 0, 0, 1, 0]          # notched / punched positions 1..8
SPLICE_SHADOWS = [3, 1, 4, 2]                  # film strip k -> shadow length (units)
TAPE_SPEED = "4.75"                            # SPEEDS[SPEED_RIGHT]
TAPE_YEARS = (1996, 1997, 1998)
DEST_SYMBOLS = ["star", "book", "flask", "film", "envelope", "padlock"]  # dial d = 0..5 at 12,2,4,6,8,10 o'clock
SIGN_IN_VAULT_SCALE = 0.55                     # 1 - 0.15 * ZOOM_TARGET
SIGN_IN_VAULT_ROT_CW = 90.0                    # 45 deg * ROT_RIGHT_TARGET, clockwise as seen
STAFF_COUNT = 41

# card geometry shared by index_card / request_card (1250 x 750 px = 0.125 x 0.075 m, 10 px per mm);
# mirrored in tools/blender/lib_ch2_items.py (HOLE_FROM_TOP, HOLE_D, NOTCH_W, NOTCH_D)
CARD_W, CARD_H = 1250, 750
HOLE_V_PX = 92            # punch-circle centre, px from the top edge (9.2 mm)  -> v = 1 - 92/750
HOLE_R_PX = 27            # printed punch circle radius (Ø 5.4 mm); hole discs are Ø 5.0 mm
NOTCH_W_PX = 84           # V-notch width at the top edge (8.4 mm)
NOTCH_D_PX = 100          # V-notch depth (10 mm): the tip passes the printed circle centre
NOTCH_FLAT_PX = 6         # flat at the notch tip (0.6 mm, as the model)
CARD_CORNER_PX = 15       # 1.5 mm corner radius
REQ_CLIP_PX = 45          # request card: clipped top-left corner (4.5 mm)


def card_pos_x(k: int) -> float:
    """Centre of edge position k (1..8) in px: u = (k - 0.5) / 8."""
    return (k - 0.5) * CARD_W / 8


# ---- languages ---------------------------------------------------------------------------------
# Every decal with readable words is written as <name>.<ext> (EN) plus <name>_ru.<ext> and <name>_uz.<ext>.
# Terminology follows game/localization/strings.csv (Archive «Б» / «B» arxivi, пневмопочта, Табельный №, Л.Р.).
# UZ is Latin with the modifier letter ʻ (U+02BB) in oʻ / gʻ. Puzzle data (0417, notches, 4.75, symbols, the
# B-3 shelf code that matches the 3D shelf label) is identical in every language.
LANGS = ("en", "ru", "uz")
TXT = {
    # shared
    "inst": ("MERIDIAN INSTITUTE", "ИНСТИТУТ «МЕРИДИАН»", "«MERIDIAN» INSTITUTI"),
    "inst_sp": ("MERIDIAN  INSTITUTE", "ИНСТИТУТ  «МЕРИДИАН»", "«MERIDIAN»  INSTITUTI"),
    "inst_line": ("Meridian Institute, 1977", "Институт «Меридиан», 1977", "«Meridian» instituti, 1977"),
    "archive_b": ("ARCHIVE B", "АРХИВ «Б»", "«B» ARXIVI"),
    "archive_b_sp": ("ARCHIVE  B", "АРХИВ  «Б»", "«B»  ARXIVI"),
    "stamp_inst": ("MERIDIAN · INSTITUTE ·", "ИНСТИТУТ «МЕРИДИАН» ·", "«MERIDIAN» INSTITUTI ·"),
    "staff_no": ("STAFF  No.", "ТАБЕЛЬНЫЙ  №", "XODIM  №"),
    "staff_no1": ("STAFF No.", "ТАБЕЛЬНЫЙ №", "XODIM №"),
    "surname": ("SURNAME", "ФАМИЛИЯ", "FAMILIYA"),
    # badge
    "badge_sub": ("STAFF PASS  ·  SECTION B", "ПРОПУСК  ·  СЕКТОР «Б»", "RUXSATNOMA  ·  «B» SEKTOR"),
    "badge_name": ("RAHIMOVA  L.", "РАХИМОВА  Л.", "RAHIMOVA  L."),
    "dept": ("Dept. of Light Physics", "Отдел физики света", "Yorugʻlik fizikasi boʻlimi"),
    "badge_role": ("Researcher  ·  Laboratory 7", "Научный сотрудник  ·  Лаборатория 7", "Ilmiy xodim  ·  7-laboratoriya"),
    "issued": ("ISSUED", "ВЫДАН", "BERILGAN"),
    "signature": ("SIGNATURE", "ПОДПИСЬ", "IMZO"),
    "sig_leyla": ("L. Rahimova", "Л. Рахимова", "L. Rahimova"),
    "stamp_personnel": ("· PERSONNEL ·", "· ОТДЕЛ КАДРОВ ·", "· KADRLAR BOʻLIMI ·"),
    # index card
    "ic_header": ("MERIDIAN INSTITUTE · ARCHIVE B · PERSONNEL INDEX", "ИНСТИТУТ «МЕРИДИАН» · АРХИВ «Б» · КАРТОТЕКА КАДРОВ",
                  "«MERIDIAN» INSTITUTI · «B» ARXIVI · KADRLAR KARTOTEKASI"),
    "ic_name": ("RAHIMOVA, Leyla", "Рахимова, Лейла", "Rahimova, Leyla"),
    "ic_role": ("researcher, Dept. of Light Physics", "науч. сотр., Отдел физики света",
                "ilmiy xodim, Yorugʻlik fizikasi boʻlimi"),
    "ic_lab": ("Laboratory 7 · since 1974", "Лаборатория 7 · с 1974 г.", "7-laboratoriya · 1974-yildan"),
    "ic_file": ("personnel file: Stacks B-3", "личное дело: стеллаж B-3", "shaxsiy ish: B-3 javoni"),
    "ic_note": ("req. via tube", "запрос пневмопочтой", "pnevmopochta orqali"),
    # request card
    "rc_header": ("REQUEST  —  ARCHIVE  B", "ЗАПРОС  —  АРХИВ  «Б»", "SOʻROV  —  «B»  ARXIVI"),
    "rc_item": ("ITEM / FILE", "ДЕЛО / ЕД. ХР.", "ISH / HUJJAT"),
    "rc_date": ("DATE", "ДАТА", "SANA"),
    "rc_sign": ("SIGN.", "ПОДП.", "IMZO"),
    "rc_instr": ("Punch the code positions. Send by pneumatic post.", "Пробейте позиции шифра. Отправьте пневмопочтой.",
                 "Shifr oʻrinlarini teshing. Pnevmatik pochta bilan yuboring."),
    "rc_form": ("Form A-12", "Форма А-12", "A-12 shakl"),
    # routing chart
    "chart_1": ("PNEUMATIC", "ПНЕВМО-", "PNEVMATIK"),
    "chart_2": ("POST", "ПОЧТА", "POCHTA"),
    # file cover
    "fc_sub": ("PERSONNEL RECORDS  ·  ARCHIVE B", "ЛИЧНЫЕ ДЕЛА  ·  АРХИВ «Б»", "SHAXSIY ISHLAR  ·  «B» ARXIVI"),
    "fc_title": ("PERSONNEL", "ЛИЧНОЕ ДЕЛО", "SHAXSIY ISH"),
    "fc_f_name": ("SURNAME, INITIAL", "ФАМИЛИЯ, ИНИЦИАЛ", "FAMILIYA, ISMI"),
    "fc_f_dept": ("DEPARTMENT", "ОТДЕЛ", "BOʻLIM"),
    "fc_f_file": ("FILE", "ШИФР", "SHIFR"),
    "fc_dept": ("Light Physics", "Физики света", "Yorugʻlik fizikasi"),
    "fc_stamp": ("RESTRICTED", "СЕКРЕТНО", "MAXFIY"),
    "fc_stamp2": ("ARCHIVE B · 1979", "АРХИВ «Б» · 1979", "«B» ARXIVI · 1979"),
    "fc_note": ("left XI.1979", "уволена XI.1979", "ketgan XI.1979"),
    # tape labels
    "tl_top": ("MAGNETIC  TAPE", "МАГНИТНАЯ  ЛЕНТА", "MAGNIT  LENTA"),
    "tl_date": ("DATE / NAME", "ДАТА / ИМЯ", "SANA / ISM"),
    "tl_speed": ("SPEED", "СКОРОСТЬ", "TEZLIK"),
    "tl_unit": ("cm/s", "см/с", "sm/s"),
    "tl_init": ("L.R.", "Л.Р.", "L.R."),
    # archive rules
    "ar_rules": ("RULES", "ПРАВИЛА", "QOIDALARI"),
    "ar_order": ("By order of the Director", "По приказу директора", "Direktor buyrugʻi bilan"),
    "ar_sig": ("E. Strand", "Э. Странд", "E. Strand"),
}
RULES_TXT = {
    "en": ["Admission by staff pass only.", "Files are requested by pneumatic post.", "No smoking. No open flame.",
           "Film and lantern slides: in the booth only.", "Return every file to its box.",
           "The vault is sealed by order of the Director.", "Leave the lamps as you found them."],
    "ru": ["Вход только по пропускам.", "Дела заказываются пневмопочтой.", "Не курить. Открытый огонь запрещён.",
           "Плёнки и диапозитивы — только в аппаратной.", "Возвращайте каждое дело в свою коробку.",
           "Хранилище опечатано по приказу директора.", "Оставляйте лампы так, как нашли."],
    "uz": ["Kirish faqat ruxsatnoma bilan.", "Hujjatlar pnevmatik pochta orqali soʻraladi.",
           "Chekish va ochiq olov taqiqlanadi.", "Plyonka va slaydlar — faqat apparatxonada.",
           "Har bir ishni oʻz qutisiga qaytaring.", "Seyfxona direktor buyrugʻi bilan muhrlangan.",
           "Chiroqlarni qanday boʻlsa, shunday qoldiring."],
}


def t(key: str, lang: str) -> str:
    return TXT[key][LANGS.index(lang)]


def lname(name: str, lang: str) -> str:
    """badge.png -> badge.png (en) / badge_ru.png / badge_uz.png"""
    if lang == "en":
        return name
    base, ext = name.rsplit(".", 1)
    return f"{base}_{lang}.{ext}"


# ---- fonts ------------------------------------------------------------------------------------
FONTS = os.path.join(ROOT, "game", "assets", "fonts")
SYS = "/usr/share/fonts"


def _first(*paths: str) -> str:
    for p in paths:
        if os.path.exists(p):
            return p
    return os.path.join(SYS, "truetype", "dejavu", "DejaVuSans.ttf")


URW = f"{SYS}/opentype/urw-base35"
F_TYPE = _first(f"{URW}/NimbusMonoPS-Regular.otf", f"{SYS}/truetype/freefont/FreeMono.ttf",
                f"{SYS}/truetype/dejavu/DejaVuSansMono.ttf")
F_TYPE_B = _first(f"{URW}/NimbusMonoPS-Bold.otf", f"{SYS}/truetype/freefont/FreeMonoBold.ttf",
                  f"{SYS}/truetype/dejavu/DejaVuSansMono-Bold.ttf")
F_HAND = _first(os.path.join(FONTS, "Caveat-Variable.ttf"))
F_SERIF_B = _first(os.path.join(FONTS, "CormorantGaramond-Bold.ttf"), f"{SYS}/truetype/dejavu/DejaVuSerif-Bold.ttf")
F_SERIF = _first(os.path.join(FONTS, "CormorantGaramond-SemiBold.ttf"), f"{SYS}/truetype/dejavu/DejaVuSerif.ttf")
F_ROMAN = _first(f"{URW}/NimbusRoman-Regular.otf", f"{SYS}/truetype/dejavu/DejaVuSerif.ttf")
F_ROMAN_B = _first(f"{URW}/NimbusRoman-Bold.otf", f"{SYS}/truetype/dejavu/DejaVuSerif-Bold.ttf")
F_SANS_N = _first(f"{URW}/NimbusSansNarrow-Bold.otf", f"{SYS}/truetype/dejavu/DejaVuSansCondensed-Bold.ttf")
F_SANS = _first(f"{URW}/NimbusSans-Regular.otf", f"{SYS}/truetype/dejavu/DejaVuSans.ttf")
F_SANS_B = _first(f"{URW}/NimbusSans-Bold.otf", f"{SYS}/truetype/dejavu/DejaVuSans-Bold.ttf")
F_GOTHIC = _first(f"{URW}/URWGothic-Demi.otf", F_SANS_B)
F_CHALK = _first(f"{SYS}/truetype/dejavu/DejaVuSerif.ttf", f"{SYS}/truetype/dejavu/DejaVuSans.ttf")   # has Greek

_font_cache: dict = {}


def font(path: str, size: float, weight: int | None = None) -> ImageFont.FreeTypeFont:
    key = (path, int(round(size)), weight)
    f = _font_cache.get(key)
    if f is None:
        f = ImageFont.truetype(path, max(1, int(round(size))))
        if weight is not None:
            try:
                f.set_variation_by_axes([weight])
            except Exception:  # static font
                pass
        _font_cache[key] = f
    return f


# ---- glyph coverage and per-glyph fallback (Cyrillic, Uzbek ʻ U+02BB) ----------------------------
# Every string goes through _runs(): a character the primary font lacks is drawn from a covering font of
# the same design family (GNU FreeFont is derived from the URW Nimbus fonts). A character no font covers
# raises, so no image can ship with a missing-glyph box. GLYPH_FALLBACKS records what was substituted.
_cmap_cache: dict = {}
GLYPH_FALLBACKS: set = set()
FF = f"{SYS}/truetype/freefont"
LIB = f"{SYS}/truetype/liberation"
DJ = f"{SYS}/truetype/dejavu"


def covers(path: str, ch: str) -> bool:
    if ch in " \n":
        return True
    cm = _cmap_cache.get(path, False)
    if cm is False:
        try:
            from fontTools.ttLib import TTFont
            cm = set(TTFont(path, fontNumber=0, lazy=True).getBestCmap().keys())
        except Exception:      # fontTools missing: trust the font
            cm = None
        _cmap_cache[path] = cm
    return cm is None or ord(ch) in cm


def fallback_for(path: str) -> str:
    n = os.path.basename(path)
    bold = "Bold" in n or "Demi" in n
    if "Mono" in n:
        # FreeMono draws ʻ as an acute-like tick; Liberation Mono has a proper turned comma
        chain = [f"{LIB}/LiberationMono-{'Bold' if bold else 'Regular'}.ttf", f"{DJ}/DejaVuSansMono{'-Bold' if bold else ''}.ttf",
                 f"{FF}/FreeMono{'Bold' if bold else ''}.ttf"]
    elif "Roman" in n or "Serif" in n or "Cormorant" in n:
        chain = [f"{FF}/FreeSerif{'Bold' if bold else ''}.ttf", f"{LIB}/LiberationSerif-{'Bold' if bold else 'Regular'}.ttf",
                 f"{DJ}/DejaVuSerif{'-Bold' if bold else ''}.ttf"]
    elif "Gothic" in n:
        chain = [f"{SYS}/opentype/inter/Inter-Bold.otf", f"{DJ}/DejaVuSans-Bold.ttf"]
    else:   # Nimbus Sans / Narrow and anything else
        chain = [f"{FF}/FreeSans{'Bold' if bold else ''}.ttf", f"{LIB}/LiberationSans-{'Bold' if bold else 'Regular'}.ttf",
                 f"{DJ}/DejaVuSans{'-Bold' if bold else ''}.ttf"]
    for c in chain:
        if os.path.exists(c):
            return c
    return f"{DJ}/DejaVuSans.ttf"


def _runs(txt: str, path: str):
    """Split txt into [substring, font path] runs, swapping in a fallback font for uncovered glyphs."""
    out = []
    fb = None
    for ch in txt:
        p = path
        if not covers(path, ch):
            fb = fb or fallback_for(path)
            if not covers(fb, ch):
                raise ValueError(f"no font covers {ch!r} (U+{ord(ch):04X}) for {os.path.basename(path)}")
            p = fb
            GLYPH_FALLBACKS.add((os.path.basename(path), f"U+{ord(ch):04X}", os.path.basename(fb)))
        if out and out[-1][1] == p:
            out[-1][0] += ch
        else:
            out.append([ch, p])
    return out


def text_width(txt: str, path: str, size: float, spacing: float = 0.0, weight=None) -> float:
    w = 0.0
    for sub, p in _runs(txt, path):
        f = font(p, size, weight if p == path else None)
        w += sum(f.getlength(c) for c in sub) + spacing * len(sub) if spacing else f.getlength(sub)
    return w - (spacing if spacing else 0.0)


def fit(txt: str, path: str, size: float, max_w: float, spacing: float = 0.0, weight=None, min_scale=0.5):
    """Largest size <= `size` (and the matching spacing) at which txt fits in max_w pixels."""
    sc = 1.0
    while sc > min_scale and text_width(txt, path, size * sc, spacing * sc, weight) > max_w:
        sc -= 0.02
    return size * sc, spacing * sc


def draw_text(d: ImageDraw.ImageDraw, x, y, txt, path, size, fill, anchor="la", weight=None, spacing=0.0):
    """ImageDraw text with per-glyph fallback, PIL-style anchor (h in l/m/r, v in a/t/m/s/b/d) and optional
    letter spacing (pixels)."""
    runs = _runs(txt, path)
    total = text_width(txt, path, size, spacing, weight)
    h, v = anchor[0], anchor[1]
    cx = x - (total / 2 if h == "m" else total if h == "r" else 0.0)
    f0 = font(path, size, weight)
    base = y if v == "s" else y + (f0.getbbox("H", anchor="l" + v)[1] - f0.getbbox("H", anchor="ls")[1])
    for sub, p in runs:
        f = font(p, size, weight if p == path else None)
        if spacing:
            for c in sub:
                d.text((cx, base), c, font=f, fill=fill, anchor="ls")
                cx += f.getlength(c) + spacing
        else:
            d.text((cx, base), sub, font=f, fill=fill, anchor="ls")
            cx += f.getlength(sub)


# ---- numeric helpers ---------------------------------------------------------------------------
def blur(a: np.ndarray, sigma: float, wrap: bool = False) -> np.ndarray:
    """Gaussian blur (FFT) for 2-D or HxWxC float arrays; reflect padding, or periodic with wrap."""
    if sigma <= 0.05:
        return a.astype(np.float32)
    pad = 0 if wrap else int(3 * sigma) + 2
    if pad:
        widths = ((pad, pad), (pad, pad)) + ((0, 0),) * (a.ndim - 2)
        p = np.pad(a.astype(np.float32), widths, mode="reflect")
    else:
        p = a.astype(np.float32)
    hh, ww = p.shape[:2]
    fy = np.fft.fftfreq(hh)[:, None]
    fx = np.fft.rfftfreq(ww)[None, :]
    g = np.exp(-2.0 * np.pi ** 2 * sigma ** 2 * (fx ** 2 + fy ** 2))
    if a.ndim == 3:
        g = g[..., None]
    out = np.fft.irfft2(np.fft.rfft2(p, axes=(0, 1)) * g, s=(hh, ww), axes=(0, 1))
    return out[pad:pad + a.shape[0], pad:pad + a.shape[1]].astype(np.float32)


def pnoise(h: int, w: int, scale: float, seed: int, stretch=(1.0, 1.0)) -> np.ndarray:
    """Periodic (tileable) smooth noise in 0..1; feature size ~scale px; stretch elongates (x, y)."""
    r = np.random.default_rng(seed)
    white = r.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None] * stretch[1]
    fx = np.fft.fftfreq(w)[None, :] * stretch[0]
    sig = scale * 0.5
    g = np.exp(-2.0 * np.pi ** 2 * sig ** 2 * (fx ** 2 + fy ** 2))
    n = np.real(np.fft.ifft2(np.fft.fft2(white) * g))
    lo, hi = np.percentile(n, 1), np.percentile(n, 99)
    return np.clip((n - lo) / (hi - lo + 1e-9), 0, 1).astype(np.float32)


def fbm(h: int, w: int, scale: float, seed: int, octaves: int = 4, stretch=(1.0, 1.0)) -> np.ndarray:
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        acc += amp * pnoise(h, w, scale / (2 ** o), seed + 17 * o, stretch)
        tot += amp
        amp *= 0.5
    return acc / tot


def smooth(e0: float, e1: float, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def hexf(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def paint(rgb: np.ndarray, mask: np.ndarray, color, opacity: float = 1.0) -> np.ndarray:
    """Lerp `color` (hex, rgb triple or HxWx3 array) onto a float sRGB image through mask (0..1)."""
    c = hexf(color) if isinstance(color, str) else np.asarray(color, np.float32)
    m = np.clip(mask * opacity, 0, 1)[..., None]
    return rgb * (1 - m) + c * m


def multiply(rgb: np.ndarray, mask: np.ndarray, color, opacity: float = 1.0) -> np.ndarray:
    c = (hexf(color) if isinstance(color, str) else np.asarray(color, np.float32)) / 255.0
    m = np.clip(mask * opacity, 0, 1)[..., None]
    return rgb * (1 - m + m * c)


def solid(h: int, w: int, color) -> np.ndarray:
    c = hexf(color) if isinstance(color, str) else np.asarray(color, np.float32)
    return np.broadcast_to(c, (h, w, 3)).astype(np.float32).copy()


def to_img(rgb: np.ndarray, alpha: np.ndarray | None = None) -> Image.Image:
    rgb8 = np.clip(rgb + 0.5, 0, 255).astype(np.uint8)
    if alpha is None:
        return Image.fromarray(rgb8, "RGB")
    a8 = np.clip(alpha * 255.0 + 0.5, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb8, a8]), "RGBA")


def grain(h: int, w: int, seed: int, sigma: float = 0.7) -> np.ndarray:
    r = np.random.default_rng(seed)
    g = blur(r.standard_normal((h, w)).astype(np.float32), sigma)
    return g / (g.std() + 1e-6)


def save(im: Image.Image, name: str, folder: str = OUT) -> str:
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name)
    if name.endswith(".jpg"):
        im.convert("RGB").save(path, quality=93, subsampling=0, optimize=True)
    else:
        im.save(path, optimize=True)
    print("  wrote", os.path.relpath(path, ROOT), im.size, im.mode)
    return path


def paper(w: int, h: int, base=(221, 208, 180), seed: int = 1, stains: int = 3, vignette: float = 0.25,
          fibres: float = 1.0) -> np.ndarray:
    """Aged paper (make_decals.aged_paper) plus fine fibres, as float sRGB."""
    rgb = np.asarray(aged_paper(w, h, base=base, seed=seed, stains=stains, vignette=vignette), np.float32)
    if fibres:
        f1 = noise(h, w, 1.6, 1, seed + 101)
        f2 = noise(h, w * 3, 2.0, 1, seed + 102)[:, ::3]
        rgb = rgb * (0.975 + 0.035 * fibres * (f1 - 0.5) + 0.03 * fibres * (f2 - 0.5))[..., None]
    return rgb


def edge_wear(w: int, h: int, seed: int, width: float = 30.0, amount: float = 0.18) -> np.ndarray:
    """0..1 mask that is 1 near the image border with a ragged inner edge (handling grime)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    n = noise(h, w, 30, 3, seed)
    return np.clip(1 - d / (width * (0.5 + n)), 0, 1) * amount


# ---- supersampled vector pen --------------------------------------------------------------------
class Pen:
    """Antialiased mask drawing: everything is drawn at `ss` x resolution in output-pixel
    coordinates and box-downsampled by .arr()."""

    def __init__(self, w: int, h: int, ss: int = 4):
        self.w, self.h, self.ss = w, h, ss
        self.im = Image.new("L", (w * ss, h * ss), 0)
        self.d = ImageDraw.Draw(self.im)

    def _p(self, pts):
        s = self.ss
        return [(x * s, y * s) for x, y in pts]

    def poly(self, pts, v: int = 255):
        self.d.polygon(self._p(pts), fill=v)

    def ellipse(self, cx, cy, rx, ry, v: int = 255):
        s = self.ss
        self.d.ellipse([(cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s], fill=v)

    def circle(self, cx, cy, r, v: int = 255):
        self.ellipse(cx, cy, r, r, v)

    def ring(self, cx, cy, r, width, v: int = 255):
        """Ring whose stroke is centred on radius r."""
        s = self.ss
        ro = r + width / 2
        self.d.ellipse([(cx - ro) * s, (cy - ro) * s, (cx + ro) * s, (cy + ro) * s], outline=v,
                       width=max(1, int(round(width * s))))

    def line(self, pts, width, v: int = 255, caps: bool = True):
        s = self.ss
        self.d.line(self._p(pts), fill=v, width=max(1, int(round(width * s))), joint="curve")
        if caps:
            for x, y in (pts[0], pts[-1]):
                self.circle(x, y, width / 2, v)

    def rect(self, x0, y0, x1, y1, v: int = 255, radius: float = 0, outline: float = 0):
        s = self.ss
        box = [x0 * s, y0 * s, x1 * s, y1 * s]
        if outline:
            self.d.rounded_rectangle(box, radius=radius * s, outline=v, width=max(1, int(round(outline * s))))
        else:
            self.d.rounded_rectangle(box, radius=radius * s, fill=v)

    def arc(self, cx, cy, r, a0, a1, width, v: int = 255):
        """Arc centred on radius r from angle a0 to a1 (degrees, PIL convention: 0 = +x, clockwise)."""
        s = self.ss
        ro = r + width / 2
        self.d.arc([(cx - ro) * s, (cy - ro) * s, (cx + ro) * s, (cy + ro) * s], a0, a1, fill=v,
                   width=max(1, int(round(width * s))))

    def text(self, x, y, txt, path, size, anchor="mm", v: int = 255, weight=None, spacing: float = 0,
             max_w: float = 0):
        """Text with glyph fallback; max_w > 0 shrinks size (and spacing) so the run fits that width."""
        if max_w:
            size, spacing = fit(txt, path, size, max_w, spacing, weight)
        draw_text(self.d, x * self.ss, y * self.ss, txt, path, size * self.ss, v, anchor, weight, spacing * self.ss)

    def paste_rotated(self, mask_img: Image.Image, cx, cy, angle_deg):
        """Max-composite an 'L' image (drawn at ss scale) rotated CCW by angle about its centre at (cx, cy)."""
        r = mask_img.rotate(angle_deg, resample=Image.BICUBIC, expand=True)
        x0 = int(cx * self.ss - r.width / 2)
        y0 = int(cy * self.ss - r.height / 2)
        base = self.im.crop((x0, y0, x0 + r.width, y0 + r.height))
        self.im.paste(ImageChops.lighter(base, r), (x0, y0))

    def arr(self) -> np.ndarray:
        im = self.im.resize((self.w, self.h), Image.BOX) if self.ss > 1 else self.im
        return np.asarray(im, np.float32) / 255.0


def text_mask(txt, path, size, ss=4, weight=None, pad=8, spacing: float = 0) -> Image.Image:
    """Tight 'L' image of a text run at ss scale (for rotated / jittered placement)."""
    px = size * ss
    wdt = text_width(txt, path, px, spacing * ss, weight)
    im = Image.new("L", (int(wdt + 2 * px) + 2 * pad * ss, int(2.2 * px) + 2 * pad * ss), 0)
    draw_text(ImageDraw.Draw(im), px + pad * ss, int(1.4 * px) + pad * ss, txt, path, px, 255, "ls", weight, spacing * ss)
    bb = im.getbbox()
    if bb is None:
        return Image.new("L", (2 * pad * ss, 2 * pad * ss), 0)
    p = pad * ss
    return im.crop((bb[0] - p, bb[1] - p, bb[2] + p, bb[3] + p))


def rot_text(pen: Pen, x, y, txt, path, size, angle=0.0, weight=None, spacing=0.0):
    pen.paste_rotated(text_mask(txt, path, size, pen.ss, weight, spacing=spacing), x, y, angle)


def arc_text(pen: Pen, cx, cy, r, txt, path, size, a_mid=-90.0, spacing=1.0, weight=None, inward=False,
             max_deg: float = 0.0):
    """Text set along a circle of radius r (baseline), centred at angle a_mid (deg, 0 = +x, +90 = down).
    Letters stand on the outside of the circle (top reading clockwise), or inside when inward.
    max_deg > 0 shrinks the font so the run spans at most that angle."""
    widths = [text_width(c, path, size, 0.0, weight) * spacing for c in txt]
    total = sum(widths)
    if max_deg and math.degrees(total / r) > max_deg:
        size *= math.radians(max_deg) * r / total
        widths = [text_width(c, path, size, 0.0, weight) * spacing for c in txt]
        total = sum(widths)
    a = math.radians(a_mid) - (total / r) / 2 * (-1 if inward else 1)
    for c, wdt in zip(txt, widths):
        step = wdt / r
        am = a + (step / 2) * (-1 if inward else 1)
        x, y = cx + r * math.cos(am), cy + r * math.sin(am)
        if c != " ":
            rot = -math.degrees(am) - 90 if not inward else -math.degrees(am) + 90
            rot_text(pen, x, y, c, path, size, rot, weight)
        a += step * (-1 if inward else 1)


def typed(pen: Pen, x, y, txt, size, rng, path=None, jitter=0.7, fade=(0.72, 1.0), anchor="ls", max_w: float = 0):
    """Typewriter text: per-character jitter and uneven ink. (x, y) = baseline start.
    max_w > 0 shrinks the type so the line fits that width."""
    path = path or F_TYPE
    if max_w:
        adv1 = font(path, 100).getlength("M") / 100.0
        size = min(size, max_w / max(1e-6, adv1 * len(txt)))
    f0 = font(path, size * pen.ss)
    s = pen.ss
    adv = f0.getlength("M")
    if anchor[0] == "m":
        x -= adv * len(txt) / s / 2
    elif anchor[0] == "r":
        x -= adv * len(txt) / s
    cx = x * s
    for c in txt:
        if c != " ":
            f = font(_runs(c, path)[0][1], size * pen.ss)
            v = int(255 * rng.uniform(*fade))
            dx, dy = rng.normal(0, jitter * 0.6) * s, rng.normal(0, jitter * 0.5) * s
            pen.d.text((cx + dx, y * s + dy), c, font=f, fill=v, anchor="ls")
            if rng.random() < 0.12:  # double strike / heavy key
                pen.d.text((cx + dx + 0.6 * s, y * s + dy), c, font=f, fill=int(v * 0.6), anchor="ls")
        cx += adv


def ink(mask: np.ndarray, seed: int, amount: float = 0.35, scale: float = 2.5) -> np.ndarray:
    """Uneven ink / worn print: modulate a mask with fine noise."""
    n = noise(mask.shape[0], mask.shape[1], scale, 2, seed)
    return mask * np.clip(1 - amount + amount * 1.5 * n, 0, 1)


def white_rgba(mask: np.ndarray) -> Image.Image:
    rgb = np.full(mask.shape + (3,), 255.0, np.float32)
    return to_img(rgb, mask)


def _bez(p0, p1, p2, n=24):
    t = np.linspace(0, 1, n)
    return [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
             (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]) for u in t]


def stamp_mask(w, h, seed, amount=0.45):
    """Rubber-stamp texture: blotchy coverage with speckle gaps."""
    n1 = noise(h, w, 9, 3, seed)
    n2 = noise(h, w, 2.2, 1, seed + 1)
    return np.clip(1 - amount + amount * 1.6 * n1, 0, 1) * (n2 > 0.22)


# =================================================================================================
# Glyphs (unit coordinates: the 512 box is [-0.5, 0.5]^2, +y down)
# =================================================================================================
MARK_RING_R = 0.384      # ring centreline radius (outer diameter = 2 * (0.384 + 0.016) = 0.80)
MARK_RING_W = 0.032
MARK_MERIDIAN_W = 0.030
MARK_MERIDIAN_HALF = 0.484
MARK_TICK = (0.432, 0.478, 0.022)   # r0, r1, width (Chapter 1 emblem's 12 ticks; 12 and 6 o'clock are the meridian)

SIGN_R = 0.40            # crescent outer radius -> sign height 0.80
SIGN_T = 0.112           # crescent thickness at its back
SIGN_PHI = 50.0          # horn angle from the opening axis (deg)
SIGN_DOT_R = 0.043
SIGN_DOT_DY = 0.165
SIGN_DOT_DX = 0.045      # dot column x relative to the outer circle centre


def _sign_geometry():
    """Return (outer centre x, inner centre x, inner radius, dot x, horn x) in unit coords, centred."""
    R, t, phi = SIGN_R, SIGN_T, math.radians(SIGN_PHI)
    d = (t * t - 2 * R * t) / (2 * t - 2 * R * (1 + math.cos(phi)))
    r2 = R + d - t
    horn = R * math.cos(phi)
    right = max(horn, SIGN_DOT_DX + SIGN_DOT_R)
    a = -(-R + right) / 2.0      # centre the bounding box
    return a, a + d, r2, a + SIGN_DOT_DX, a + horn


def draw_mark(pen: Pen, cx, cy, size, v=255, ticks=True, ring_w=None, line_w=None):
    s = size
    rw = (ring_w or MARK_RING_W) * s
    pen.ring(cx, cy, MARK_RING_R * s, rw, v)
    lw = (line_w or MARK_MERIDIAN_W) * s
    pen.rect(cx - lw / 2, cy - MARK_MERIDIAN_HALF * s, cx + lw / 2, cy + MARK_MERIDIAN_HALF * s, v)
    if ticks:
        r0, r1, tw = MARK_TICK
        for k in range(12):
            if k in (3, 9):
                continue
            a = 2 * math.pi * k / 12
            ca, sa = math.cos(a), math.sin(a)
            pen.line([(cx + r0 * s * ca, cy + r0 * s * sa), (cx + r1 * s * ca, cy + r1 * s * sa)], tw * s, v, caps=False)


def sign_end_point(progress: float):
    """Unit-coordinate position of the pen tip when the sign is drawn to `progress` (see sign_mask)."""
    oa, _, _, dx, _ = _sign_geometry()
    if progress < 0.8:
        total = 360.0 - 2 * SIGN_PHI
        ang = math.radians(-SIGN_PHI - total * progress / 0.8)
        r = SIGN_R - SIGN_T * 0.5 * (0.3 + 0.7 * abs(math.sin((ang - math.pi) / 2 + math.pi / 2)))
        return oa + r * math.cos(ang), r * math.sin(ang)
    k = min(2, int((progress - 0.8) / 0.2 * 3))
    return dx, (k - 1) * SIGN_DOT_DY


def sign_mask(size: int, progress: float = 1.0, ss: int = 4) -> np.ndarray:
    """Leyla's sign as a float mask (size x size), centred. progress < 1 draws it partially
    (crescent swept from the top horn anticlockwise, then the dots) for the film frame."""
    pen = Pen(size, size, ss)
    c = size / 2
    oa, ia, r2, dx, _ = _sign_geometry()
    R = SIGN_R * size
    pen.circle(c + oa * size, c, R)
    pen.circle(c + ia * size, c, r2 * size, 0)
    m = pen.arr()
    if progress < 1.0:
        yy, xx = np.mgrid[0:size, 0:size]
        ang = np.degrees(np.arctan2(yy - c, xx - (c + oa * size)))  # 0 = +x, +90 = down
        sweep = np.mod(-SIGN_PHI - ang, 360.0)        # 0 at the top horn, growing anticlockwise on screen
        total = 360.0 - 2 * SIGN_PHI
        keep = sweep <= total * min(1.0, progress / 0.8)
        m = m * blur(keep.astype(np.float32), size * 0.004)
    dots = Pen(size, size, ss)
    nd = 3 if progress >= 1.0 else max(0, int((progress - 0.8) / 0.2 * 3 + 1e-6))
    for k in range(nd):
        dots.circle(c + dx * size, c + (k - 1) * SIGN_DOT_DY * size, SIGN_DOT_R * size)
    return np.maximum(m, dots.arr())


def mark_mask(size: int, ss: int = 4, **kw) -> np.ndarray:
    pen = Pen(size, size, ss)
    draw_mark(pen, size / 2, size / 2, size, **kw)
    return pen.arr()


def glyph_mark():
    save(white_rgba(mark_mask(512)), "glyph_mark.png")


def glyph_sign():
    save(white_rgba(sign_mask(512)), "glyph_sign.png")


def vault_engraving():
    """Composed programmatically from the two glyph images: the mark upright at scale 1 plus the sign
    rotated 90 deg clockwise and scaled 0.55, both centred. Etched-glass look: thin cut contours
    (alpha ~0.6) over a faint frosted fill."""
    mpath, spath = os.path.join(OUT, "glyph_mark.png"), os.path.join(OUT, "glyph_sign.png")
    if not (os.path.exists(mpath) and os.path.exists(spath)):
        glyph_mark()
        glyph_sign()
    S = 512
    up = 4  # compose at 4x for clean contours
    mark = Image.open(mpath).getchannel("A").resize((S * up, S * up), Image.LANCZOS)
    sign = Image.open(spath).getchannel("A")
    n = int(round(S * up * SIGN_IN_VAULT_SCALE))
    sign_s = sign.resize((n, n), Image.LANCZOS).rotate(-SIGN_IN_VAULT_ROT_CW, resample=Image.BICUBIC)  # PIL: negative = clockwise
    comb = Image.new("L", (S * up, S * up), 0)
    comb.paste(sign_s, ((S * up - n) // 2, (S * up - n) // 2))
    m = np.maximum(np.asarray(mark, np.float32), np.asarray(comb, np.float32)) / 255.0
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((S, S), Image.BOX), np.float32) / 255.0
    # contour = band around the 0.5 iso-line of the shape (about 2.6 px wide)
    sm = blur(m, 0.8)
    edge = np.clip(1.0 - np.abs(sm - 0.5) / 0.32, 0, 1)
    inner = np.clip(m - blur(m, 3.0), 0, 1)          # a second, finer cut just inside the edge
    fill = m * 0.16
    frost = (0.85 + 0.3 * noise(S, S, 1.4, 1, 77)) * fill
    a = np.clip(frost + 0.60 * edge + 0.15 * inner, 0, 0.66)
    save(white_rgba(a), "vault_engraving.png")


# =================================================================================================
# Pictograms (shared by the routing chart and the destination ring). Unit box [-0.5, 0.5]^2, +y down.
# =================================================================================================
def picto(pen: Pen, kind: str, cx: float, cy: float, s: float, v: int = 255):
    """Single-colour pictogram (filled shapes with cut-outs) centred at (cx, cy), box size s px."""
    def P(x, y):
        return (cx + x * s, cy + y * s)

    def poly(pts, val=v):
        pen.poly([P(x, y) for x, y in pts], val)

    def circ(x, y, r, val=v):
        pen.circle(cx + x * s, cy + y * s, r * s, val)

    def line(pts, w, val=v, caps=True):
        pen.line([P(x, y) for x, y in pts], w * s, val, caps)

    def rect(x0, y0, x1, y1, val=v, rad=0.0):
        pen.rect(cx + x0 * s, cy + y0 * s, cx + x1 * s, cy + y1 * s, val, radius=rad * s)

    if kind == "star":       # four-pointed star with concave sides (Strand's ✦)
        pts = []
        for t in np.linspace(0, 2 * np.pi, 200, endpoint=False):
            c, sn = math.cos(t), math.sin(t)
            pts.append((0.49 * math.copysign(abs(c) ** 3.3, c), 0.49 * math.copysign(abs(sn) ** 3.3, sn)))
        poly(pts)
    elif kind == "book":     # open book
        for sg in (-1, 1):
            top = _bez((sg * 0.035, -0.20), (sg * 0.22, -0.36), (sg * 0.47, -0.27))
            bot = _bez((sg * 0.47, 0.22), (sg * 0.22, 0.13), (sg * 0.035, 0.28))
            poly(top + bot)
            cov_top = _bez((sg * 0.0, 0.28), (sg * 0.22, 0.14), (sg * 0.47, 0.22))
            cov_bot = _bez((sg * 0.50, 0.32), (sg * 0.22, 0.24), (sg * 0.0, 0.40))
            poly(cov_top + [(sg * 0.50, 0.22)] + cov_bot)
            line(_bez((sg * 0.03, 0.285), (sg * 0.22, 0.155), (sg * 0.48, 0.225)), 0.035, 0, caps=False)
            for f in (0.24, 0.44, 0.64):
                pts = []
                for t in np.linspace(0.16, 0.86, 18):
                    # point between the top and bottom curves at parameter t
                    tx = (1 - t) ** 2 * sg * 0.035 + 2 * (1 - t) * t * sg * 0.22 + t * t * sg * 0.47
                    ty = (1 - t) ** 2 * -0.20 + 2 * (1 - t) * t * -0.36 + t * t * -0.27
                    by = (1 - t) ** 2 * 0.28 + 2 * (1 - t) * t * 0.13 + t * t * 0.22
                    pts.append((tx, ty + (by - ty) * f))
                line(pts, 0.032, 0, caps=False)
        rect(-0.018, -0.24, 0.018, 0.40, 0)
    elif kind == "flask":    # Erlenmeyer flask with liquid and bubbles
        w = 0.075
        outline = [(-0.10, -0.40), (-0.10, -0.11), (-0.38, 0.35), (-0.34, 0.43), (0.34, 0.43), (0.38, 0.35),
                   (0.10, -0.11), (0.10, -0.40)]
        line(outline, w)
        rect(-0.17, -0.48, 0.17, -0.39, rad=0.025)
        top_y = 0.10
        hw = 0.10 + (top_y + 0.11) * (0.28 / 0.46)
        wave = [(x, top_y + 0.018 * math.sin(x * 22)) for x in np.linspace(-hw, hw, 16)]
        poly(wave + [(0.38, 0.35), (0.34, 0.43), (-0.34, 0.43), (-0.38, 0.35)])
        for bx, by, br in ((-0.08, 0.30, 0.042), (0.09, 0.34, 0.032), (0.03, 0.22, 0.026)):
            circ(bx, by, br, 0)
    elif kind == "film":     # film reel with a short film tail
        rx, ry, rad = -0.07, -0.07, 0.41
        rect(rx, ry + rad - 0.17, 0.49, ry + rad + 0.005, rad=0.015)
        circ(rx, ry, rad)
        for k in range(5):
            a = math.radians(-90 + 72 * k)
            circ(rx + 0.225 * math.cos(a), ry + 0.225 * math.sin(a), 0.098, 0)
        circ(rx, ry, 0.045, 0)
        ty = ry + rad - 0.0825
        for x in (0.24, 0.335, 0.43):
            rect(x - 0.026, ty - 0.026, x + 0.026, ty + 0.026, 0, rad=0.006)
    elif kind == "envelope":
        rect(-0.47, -0.31, 0.47, 0.31, rad=0.04)
        line([(-0.43, -0.27), (0.0, 0.07), (0.43, -0.27)], 0.065, 0, caps=False)
        line([(-0.43, 0.27), (-0.13, 0.0)], 0.045, 0, caps=False)
        line([(0.43, 0.27), (0.13, 0.0)], 0.045, 0, caps=False)
    elif kind == "padlock":
        pen.arc(cx, cy - 0.13 * s, 0.20 * s, 180, 360, 0.095 * s, v)
        rect(-0.2475, -0.14, -0.1525, 0.02)
        rect(0.1525, -0.14, 0.2475, 0.02)
        rect(-0.34, -0.03, 0.34, 0.45, rad=0.07)
        circ(0, 0.15, 0.075, 0)
        poly([(-0.035, 0.17), (0.035, 0.17), (0.06, 0.33), (-0.06, 0.33)], 0)
    elif kind == "memo":     # folded note
        poly([(-0.34, -0.45), (0.15, -0.45), (0.34, -0.26), (0.34, 0.45), (-0.34, 0.45)])
        line([(0.15, -0.45), (0.15, -0.26), (0.34, -0.26)], 0.04, 0, caps=False)
        for i, y in enumerate((-0.22, -0.08, 0.06, 0.20, 0.33)):
            line([(-0.24, y), (0.24 if i else 0.04, y)], 0.045, 0, caps=False)
    else:
        raise ValueError(kind)


def picto_mask(kind: str, size: int, fill: float = 0.86, ss: int = 4) -> np.ndarray:
    pen = Pen(size, size, ss)
    picto(pen, kind, size / 2, size / 2, size * fill)
    return pen.arr()


# ---- coloured enamel item icons (routing chart, left column) -------------------------------------
INK = "#22262B"


def item_icon(kind: str, S: int, seed: int = 0):
    """Small multi-colour enamel illustration of a dispatch item. Returns (rgb, alpha) S x S."""
    s = S
    rgb = np.zeros((S, S, 3), np.float32)
    alpha = np.zeros((S, S), np.float32)
    layers = []  # (mask, colour)

    def pen():
        return Pen(S, S, 4)

    def P(x, y):
        return (S / 2 + x * s, S / 2 + y * s)

    if kind == "memo":
        a = pen()
        pts = [(-0.30, -0.42), (0.14, -0.42), (0.32, -0.24), (0.32, 0.42), (-0.30, 0.42)]
        a.poly([P(*p) for p in pts])
        o = pen()
        o.line([P(*p) for p in pts + [pts[0]]], 0.045 * s)
        fold = pen()
        fold.poly([P(0.14, -0.42), P(0.14, -0.24), P(0.32, -0.24)])
        fo = pen()
        fo.line([P(0.14, -0.42), P(0.14, -0.24), P(0.32, -0.24)], 0.035 * s)
        t = pen()
        for i, y in enumerate((-0.20, -0.07, 0.06, 0.19, 0.31)):
            t.line([P(-0.21, y), P(0.22 if i else 0.02, y)], 0.035 * s)
        layers = [(a.arr(), "#F1EBDD"), (fold.arr(), "#D6CDB8"), (t.arr(), "#6E7680"), (o.arr(), INK), (fo.arr(), INK)]
    elif kind == "request_card":   # same look as request_card.png: buff, clipped corner, 8 circles, red band
        a = pen()
        clip = 0.07
        y0, y1 = -0.30, 0.30
        pts = [(-0.48 + clip, y0), (0.48, y0), (0.48, y1), (-0.48, y1), (-0.48, y0 + clip)]
        a.poly([P(*p) for p in pts])
        o = pen()
        o.line([P(*p) for p in pts + [pts[0]]], 0.035 * s)
        holes = pen()
        for k in range(8):
            hx = -0.48 + (k + 0.5) * 0.96 / 8
            holes.ring(*P(hx, -0.20), 0.032 * s, 0.016 * s)
        red = pen()
        red.rect(*P(-0.42, -0.10), *P(0.42, -0.01))
        lines = pen()
        for y in (0.08, 0.15, 0.22):
            for x in np.arange(-0.40, 0.40, 0.05):
                lines.rect(*P(x, y - 0.006), *P(x + 0.025, y + 0.006))
        layers = [(a.arr(), "#D8C192"), (lines.arr(), "#7A6448"), (red.arr(), "#9A3B2E"), (holes.arr(), "#4A3A28"),
                  (o.arr(), INK)]
    elif kind == "vial":       # tilted test tube with amber liquid and a cork
        ax0, ay0, ax1, ay1 = -0.13, -0.30, 0.13, 0.34

        def at(t):
            return P(ax0 + (ax1 - ax0) * t, ay0 + (ay1 - ay0) * t)
        g = pen()
        g.line([at(0.0), at(1.0)], 0.26 * s)
        gm = g.arr()
        liq = pen()
        liq.line([at(0.50), at(1.0)], 0.19 * s)
        lq = liq.arr()
        cork = pen()
        cork.line([at(-0.16), at(0.04)], 0.24 * s, caps=False)
        co = cork.arr()
        hl = pen()
        hl.line([P(ax0 - 0.07, ay0 + 0.06), P(ax1 - 0.08, ay1 - 0.10)], 0.03 * s)
        edge = np.clip(gm - np.clip(blur(gm, 2.0) * 2 - 1, 0, 1), 0, 1)
        cedge = np.clip(co - np.clip(blur(co, 2.0) * 2 - 1, 0, 1), 0, 1)
        layers = [(gm, "#D5E6E2"), (lq, "#C98A1E"), (hl.arr() * gm, "#FFFFFF"), (edge, INK), (co, "#8A5A34"),
                  (cedge, INK)]
    elif kind == "film_can":
        body = pen()
        body.rect(*P(-0.40, -0.08), *P(0.40, 0.20))
        body.ellipse(*P(0, 0.20), 0.40 * s, 0.16 * s)
        top = pen()
        top.ellipse(*P(0, -0.08), 0.40 * s, 0.16 * s)
        lid_ring = pen()
        lid_ring.ellipse(*P(0, -0.08), 0.31 * s, 0.115 * s)
        lid_in = pen()
        lid_in.ellipse(*P(0, -0.08), 0.27 * s, 0.095 * s)
        label = pen()
        label.rect(*P(-0.18, 0.04), *P(0.18, 0.20))
        o = pen()
        o.ellipse(*P(0, -0.08), 0.40 * s, 0.16 * s)
        oi = pen()
        oi.ellipse(*P(0, -0.08), 0.37 * s, 0.135 * s)
        bm = body.arr()
        tm = top.arr()
        edge = np.clip(np.maximum(bm, tm) - np.clip(blur(np.maximum(bm, tm), 2.2) * 2 - 1, 0, 1), 0, 1)
        layers = [(bm, "#6F7A74"), (tm, "#9AA59F"), (np.clip(lid_ring.arr() - lid_in.arr(), 0, 1), "#5E6862"),
                  (label.arr(), "#E3D7B8"), (edge, INK)]
    elif kind == "envelope_sealed":
        a = pen()
        a.rect(*P(-0.45, -0.29), *P(0.45, 0.29), radius=0.03 * s)
        fl = pen()
        fl.line([P(-0.42, -0.26), P(0, 0.06), P(0.42, -0.26)], 0.035 * s, caps=False)
        fl.line([P(-0.42, 0.26), P(-0.12, 0.0)], 0.03 * s, caps=False)
        fl.line([P(0.42, 0.26), P(0.12, 0.0)], 0.03 * s, caps=False)
        seal = pen()
        for k in range(9):
            ang = 2 * math.pi * k / 9
            seal.circle(*P(0.0 + 0.085 * math.cos(ang), 0.07 + 0.085 * math.sin(ang)), 0.045 * s)
        seal.circle(*P(0, 0.07), 0.10 * s)
        st = pen()
        picto(st, "star", *P(0, 0.07), 0.13 * s)
        am = a.arr()
        edge = np.clip(am - np.clip(blur(am, 2.2) * 2 - 1, 0, 1), 0, 1)
        layers = [(am, "#F1EBDD"), (fl.arr(), INK), (edge, INK), (seal.arr(), "#9E2A22"), (st.arr(), "#C8574A")]
    elif kind == "no_entry":
        a = pen()
        a.circle(S / 2, S / 2, 0.42 * s)
        b = pen()
        b.rect(*P(-0.28, -0.075), *P(0.28, 0.075), radius=0.02 * s)
        layers = [(a.arr(), "#B23A2E"), (b.arr(), "#F1EBDD")]
    else:
        raise ValueError(kind)
    for m, col in layers:
        rgb = paint(rgb, m, col)
        alpha = np.maximum(alpha, m)
    return rgb, alpha


def brass_disc_rgb(S: int, seed: int, base="#5B4A2E", r_frac=0.5) -> np.ndarray:
    """Dark aged brass, circularly brushed, lit from the top-left (float sRGB)."""
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    c = (S - 1) / 2
    ang = np.arctan2(yy - c, xx - c)
    rr = np.hypot(xx - c, yy - c) / (S * r_frac)
    # circular brushing: noise indexed by radius (streaks are rings)
    rings = noise(1, 2048, 3, 2, seed)[0]
    ri = np.clip((rr * 1400).astype(int), 0, 2047)
    brush = rings[ri]
    n = noise(S, S, 60, 3, seed + 1)
    b = hexf(base)
    shade = 0.85 + 0.25 * n + 0.10 * (brush - 0.5) + 0.12 * np.cos(ang + 2.35) * rr
    rgb = b[None, None, :] * shade[..., None]
    patina = smooth(0.62, 0.85, noise(S, S, 18, 3, seed + 2))
    rgb = paint(rgb, patina, "#3E4A3A", 0.35)
    return rgb


# =================================================================================================
# Routing chart (600 x 840, enamel sign)
# =================================================================================================
def routing_chart(lang: str = "en"):
    W, H = 600, 840
    r = np.random.default_rng(510)
    n = noise(H, W, 90, 4, 511)
    rgb = solid(H, W, "#E6DCC2") * (0.95 + 0.07 * n)[..., None]
    # enamel ripple + gloss gradient
    rgb = rgb * (0.985 + 0.02 * noise(H, W, 6, 2, 512))[..., None]
    # border: a dark blue enamel frame line inside the edge
    fr = Pen(W, H, 4)
    fr.rect(14, 14, W - 14, H - 14, radius=22, outline=7)
    rgb = paint(rgb, fr.arr(), "#1F3550")
    # header band
    hb = Pen(W, H, 4)
    hb.rect(28, 28, W - 28, 150, radius=12)
    hm = hb.arr()
    rgb = paint(rgb, hm, "#1F3550")
    ht = Pen(W, H, 4)
    ht.text(W / 2 + 34, 76, t("chart_1", lang), F_GOTHIC, 54, spacing=3, max_w=410)
    ht.text(W / 2 + 34, 124, t("chart_2", lang), F_GOTHIC, 54, spacing=14, max_w=410)
    # canister icon in the header
    cx, cy = 92, 89
    ht.rect(cx - 17, cy - 44, cx + 17, cy + 44, radius=15)
    ht.rect(cx - 20, cy - 30, cx + 20, cy - 22, 0)
    ht.rect(cx - 20, cy + 22, cx + 20, cy + 30, 0)
    ht.rect(cx - 6, cy - 54, cx + 6, cy - 44, radius=3)
    rgb = paint(rgb, ht.arr(), "#EDE4CC")
    # rows
    rows = [("memo", "star"), ("request_card", "book"), ("vial", "flask"), ("film_can", "film"),
            ("envelope_sealed", "envelope")]
    y0, dy = 214, 104
    lines = Pen(W, H, 4)
    for i in range(len(rows) + 1):
        y = y0 - dy / 2 + i * dy
        lines.rect(46, y - 1, W - 46, y + 1)
    rgb = paint(rgb, lines.arr(), "#1F3550", 0.35)
    TILE = 90
    for i, (item, dest) in enumerate(rows):
        y = y0 + i * dy
        # item tile (white enamel square)
        tile = Pen(W, H, 4)
        tile.rect(70, y - TILE / 2, 70 + TILE, y + TILE / 2, radius=12)
        tm = tile.arr()
        rgb = paint(rgb, blur(tm, 3) * 0.6, "#7E7460", 0.35)
        rgb = paint(rgb, tm, "#F4EEE0")
        irgb, ia = item_icon(item, 84, i)
        x0i, y0i = int(70 + (TILE - 84) / 2), int(y - 42)
        sub = rgb[y0i:y0i + 84, x0i:x0i + 84]
        rgb[y0i:y0i + 84, x0i:x0i + 84] = sub * (1 - ia[..., None]) + irgb * ia[..., None]
        # arrow (tube): dashed shaft + head
        ar = Pen(W, H, 4)
        for xd in range(190, 382, 30):
            ar.rect(xd, y - 6, xd + 18, y + 6, radius=3)
        ar.poly([(384, y - 24), (426, y), (384, y + 24)])
        rgb = paint(rgb, ar.arr(), "#1F3550")
        # destination roundel: cream symbol on dark brass (same look as the dial ring)
        rgb = roundel(rgb, 482, y, 46, dest, 520 + i)
    # bottom row: no entry -> padlock, crossed by a red "sealed" bar
    y = y0 + len(rows) * dy + 10
    irgb, ia = item_icon("no_entry", 90)
    x0i, y0i = 70, int(y - 45)
    sub = rgb[y0i:y0i + 90, x0i:x0i + 90]
    rgb[y0i:y0i + 90, x0i:x0i + 90] = sub * (1 - ia[..., None]) + irgb * ia[..., None]
    rgb = roundel(rgb, 482, y, 46, "padlock", 530)
    sb = Pen(W, H, 4)
    sb.rect(186, y - 15, 426, y + 15, radius=7)
    sbm = sb.arr()
    rgb = paint(rgb, blur(sbm, 3), "#4A3020", 0.35)
    rgb = paint(rgb, sbm, "#B23A2E")
    sbt = Pen(W, H, 4)
    for xd in range(196, 426, 34):
        sbt.poly([(xd, y + 15), (xd + 14, y - 15), (xd + 24, y - 15), (xd + 10, y + 15)])
    rgb = paint(rgb, sbt.arr() * sbm, "#F1EBDD", 0.85)
    # mounting rivets in the corners and a small plate number
    for rx, ry in ((36, 36), (W - 36, 36), (36, H - 36), (W - 36, H - 36)):
        rv = Pen(W, H, 4)
        rv.circle(rx, ry, 8)
        rgb = paint(rgb, rv.arr(), "#8F8A7E")
        hl = Pen(W, H, 4)
        hl.circle(rx - 2, ry - 2, 3)
        rgb = paint(rgb, hl.arr(), "#E8E2D4", 0.8)
    pn = Pen(W, H, 4)
    pn.text(W / 2, H - 40, t("archive_b_sp", lang), F_SANS_B, 18, spacing=3, max_w=300)
    rgb = paint(rgb, pn.arr(), "#1F3550", 0.75)
    # wear: enamel chips (dark iron showing) near the edges, grime, fine crazing
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dmin = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy))
    chip = (smooth(0.84, 0.90, noise(H, W, 7, 3, 540)) * (dmin < 20)).astype(np.float32)
    rgb = paint(rgb, blur(chip, 0.6), "#2A2622", 0.9)
    rgb = paint(rgb, np.clip(blur(chip, 2.0) - chip, 0, 1), "#6B4A2E", 0.5)
    grime = smooth(0.4, 1.0, noise(H, W, 80, 4, 541)) * 0.10 + edge_wear(W, H, 542, 40, 0.18)
    rgb = multiply(rgb, grime, "#6E5A3A")
    craze = Pen(W, H, 2)
    for _ in range(14):
        x, y = r.uniform(0, W), r.uniform(0, H)
        pts = [(x, y)]
        ang = r.uniform(0, 6.28)
        for _ in range(int(r.integers(3, 8))):
            ang += r.normal(0, 0.6)
            x += 9 * math.cos(ang)
            y += 9 * math.sin(ang)
            pts.append((x, y))
        craze.line(pts, 0.6, caps=False)
    rgb = multiply(rgb, craze.arr(), "#9A8E78", 0.35)
    save(to_img(rgb), lname("routing_chart.png", lang))


def roundel(rgb: np.ndarray, cx: float, cy: float, R: float, kind: str, seed: int) -> np.ndarray:
    """Composite a dark-brass roundel with a cream enamel pictogram onto rgb (in place style)."""
    H, W = rgb.shape[:2]
    S = int(2 * R + 8)
    x0, y0 = int(round(cx - S / 2)), int(round(cy - S / 2))
    disc = Pen(S, S, 4)
    disc.circle(S / 2, S / 2, R)
    dm = disc.arr()
    br = brass_disc_rgb(S, seed, r_frac=R / S)
    # bevel: bright upper-left rim, dark lower-right
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    rr = np.hypot(xx - S / 2, yy - S / 2) / R
    ang = np.arctan2(yy - S / 2, xx - S / 2)
    rim = smooth(0.84, 0.96, rr) * (1 - smooth(0.97, 1.0, rr))
    br = br * (1 + 0.45 * rim * np.cos(ang + 2.35))[..., None]
    inner_ring = smooth(0.80, 0.82, rr) * (1 - smooth(0.84, 0.86, rr))
    br = paint(br, inner_ring, "#2A2216", 0.7)
    pm = picto_mask(kind, S, fill=PICTO_SCALE.get(kind, 1.0) * (R * 1.12) / S)
    shadow = np.roll(np.roll(blur(pm, 1.2), 2, 0), 1, 1)
    br = paint(br, shadow * dm, "#15110A", 0.6)
    br = paint(br, pm * dm, "#E9DFC6")
    br = paint(br, np.clip(pm - np.roll(pm, 2, 0), 0, 1) * dm, "#FFF8E8", 0.35)
    # drop shadow of the roundel on the enamel
    sh = np.roll(np.roll(blur(dm, 3), 3, 0), 2, 1)
    sub = rgb[y0:y0 + S, x0:x0 + S]
    sub = multiply(sub, sh * 0.5, "#5A5040")
    sub = sub * (1 - dm[..., None]) + br * dm[..., None]
    rgb[y0:y0 + S, x0:x0 + S] = sub
    return rgb


# =================================================================================================
# Destination ring (512 x 512, RGBA: transparent centre and outside)
# =================================================================================================
DEST_R_IN, DEST_R_OUT, DEST_R_SYM = 0.29, 0.492, 0.393   # fractions of the image width
PICTO_SCALE = {"star": 0.88, "book": 1.06, "flask": 1.0, "film": 1.0, "envelope": 1.0, "padlock": 1.06}


def dest_symbols():
    S = 512
    c = (S - 1) / 2
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    rr = np.hypot(xx - c, yy - c) / S
    ang = np.arctan2(yy - c, xx - c)
    ring = Pen(S, S, 4)
    ring.circle(S / 2, S / 2, DEST_R_OUT * S)
    ring.circle(S / 2, S / 2, DEST_R_IN * S, 0)
    alpha = ring.arr()
    rgb = brass_disc_rgb(S, 600, base="#4E3F27")
    # bevels at both edges + an engraved groove on each side of the symbol track
    outer = smooth(DEST_R_OUT - 0.022, DEST_R_OUT - 0.004, rr)
    inner = 1 - smooth(DEST_R_IN + 0.004, DEST_R_IN + 0.020, rr)
    light = np.cos(ang + 2.35)
    rgb = rgb * (1 + 0.55 * outer * light - 0.45 * inner * light)[..., None]
    for rg in (DEST_R_OUT - 0.030, DEST_R_IN + 0.028):
        g = smooth(rg - 0.004, rg - 0.001, rr) * (1 - smooth(rg + 0.001, rg + 0.004, rr))
        rgb = paint(rgb, g, "#1E1810", 0.75)
        g2 = smooth(rg + 0.001, rg + 0.004, rr) * (1 - smooth(rg + 0.004, rg + 0.007, rr))
        rgb = paint(rgb, g2 * np.clip(light, 0, 1), "#C9A86A", 0.4)
    # six enamel symbols, d = 0..5 clockwise from 12 o'clock
    sym = Pen(S, S, 4)
    ticks = Pen(S, S, 4)
    for d, kind in enumerate(DEST_SYMBOLS):
        a = math.radians(-90 + 60 * d)
        px, py = S / 2 + DEST_R_SYM * S * math.cos(a), S / 2 + DEST_R_SYM * S * math.sin(a)
        picto(sym, kind, px, py, 0.135 * S * PICTO_SCALE.get(kind, 1.0))
        # index wedge on the inner groove, pointing at the knob
        ri = (DEST_R_IN + 0.012) * S
        tx, ty = S / 2 + ri * math.cos(a), S / 2 + ri * math.sin(a)
        nx, ny = math.cos(a), math.sin(a)
        ticks.poly([(tx - ny * 5 + nx * 8, ty + nx * 5 + ny * 8), (tx + ny * 5 + nx * 8, ty - nx * 5 + ny * 8),
                    (tx - nx * 1, ty - ny * 1)])
        # small engraved dots half-way between positions
        a2 = a + math.radians(30)
        ticks.circle(S / 2 + DEST_R_SYM * S * math.cos(a2), S / 2 + DEST_R_SYM * S * math.sin(a2), 3.0)
    sm = sym.arr()
    tm = ticks.arr()
    # cloisonne: dark cell outline, cream enamel, slight relief highlight
    cell = np.clip(blur(sm, 1.6) * 1.8, 0, 1)
    rgb = paint(rgb, cell, "#1A140C", 0.85)
    enamel = solid(S, S, "#E8DEC4") * (0.94 + 0.08 * noise(S, S, 20, 2, 601))[..., None]
    rgb = rgb * (1 - sm[..., None]) + enamel * sm[..., None]
    rgb = paint(rgb, np.clip(sm - np.roll(np.roll(sm, 2, 0), 2, 1), 0, 1), "#FFFBEF", 0.45)
    rgb = paint(rgb, np.clip(sm - np.roll(np.roll(sm, -2, 0), -2, 1), 0, 1), "#8C7A58", 0.4)
    rgb = paint(rgb, tm, "#E8DEC4", 0.95)
    # wear: enamel chips, grime in the grooves, polished rub on the top
    chips = smooth(0.87, 0.93, noise(S, S, 5, 2, 602)) * sm
    rgb = paint(rgb, chips, "#4A3B24", 0.6)
    rub = smooth(0.55, 0.9, noise(S, S, 50, 3, 603)) * (1 - sm)
    rgb = paint(rgb, rub, "#9C7F4C", 0.25)
    save(to_img(rgb, alpha), "dest_symbols.png")


# =================================================================================================
# Procedural portrait (badge photo) -- stylised 1970s ID photograph, original
# =================================================================================================
def _smooth_poly(pts, n=10):
    """Chaikin-smoothed closed polygon."""
    p = np.asarray(pts, np.float64)
    for _ in range(n // 3 + 1):
        q = np.roll(p, -1, 0)
        p = np.stack([0.75 * p + 0.25 * q, 0.25 * p + 0.75 * q], 1).reshape(-1, 2)
    return [tuple(v) for v in p]


def portrait(w: int, h: int, seed: int = 41, up: int = 2) -> np.ndarray:
    """Black-and-white studio ID portrait of a young woman with a dark bob (luminance 0..1).
    Stylised and original: shaded ellipsoid face, simple features, key light from camera left."""
    W, H = w * up, h * up
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, hy = 0.50 * W, 0.42 * H
    fw, fh = 0.19 * W, 0.20 * H
    X = (xx - cx) / fw
    Y = (yy - hy) / fh

    def P(x, y):
        return (cx + x * fw, hy + y * fh)

    def poly_mask(pts, smooth_n=9, soft=0.7):
        p = Pen(W, H, 2)
        p.poly([P(x, y) for x, y in _smooth_poly(pts, smooth_n)])
        return blur(p.arr(), soft * up)

    # backdrop: soft light behind the head, darker toward the corners and the bottom
    lum = 0.46 + 0.26 * np.exp(-(((xx / W - 0.40) / 0.50) ** 2 + ((yy / H - 0.30) / 0.60) ** 2)) - 0.08 * yy / H
    # jacket and blouse
    jacket = poly_mask([(-0.50, 1.02), (-1.3, 1.22), (-2.2, 1.50), (-2.9, 2.1), (-2.9, 3.4), (2.9, 3.4), (2.9, 2.1),
                        (2.2, 1.50), (1.3, 1.22), (0.50, 1.02)], 6)
    jl = 0.10 + 0.07 * np.clip(-X / 3, -0.3, 1) + 0.02 * noise(H, W, 30 * up, 2, seed + 5)
    lum = lum * (1 - jacket) + jacket * jl
    fold = poly_mask([(-0.60, 1.05), (-1.05, 1.25), (-0.70, 2.10), (-0.42, 3.4), (-0.20, 3.4), (-0.30, 2.0)], 3)
    lum = lum * (1 - 0.5 * fold) + 0.5 * fold * 0.19
    blouse = poly_mask([(-0.48, 0.98), (0.0, 1.62), (0.48, 0.98), (0.64, 1.16), (0.0, 2.05), (-0.64, 1.16)], 3)
    bl = 0.80 - 0.22 * np.clip(X, 0, 1) - 0.1 * np.clip((Y - 1.4), 0, 1)
    lum = lum * (1 - blouse) + blouse * bl
    # neck: a lit cylinder with a shadow under the jaw
    neck = poly_mask([(-0.40, 0.6), (0.40, 0.6), (0.46, 1.05), (0.0, 1.45), (-0.46, 1.05)], 3)
    nl = 0.50 - 0.22 * np.clip(X / 0.45, -1, 1) - 0.22 * np.exp(-((Y - 0.92) / 0.10) ** 2)
    lum = lum * (1 - neck) + neck * np.clip(nl, 0.12, 0.8)
    # hair, back mass (behind the face): a bob that ends at the jaw, curling in
    back = poly_mask([(1.02, 0.98), (1.30, 0.78), (1.40, 0.30), (1.38, -0.25), (1.24, -0.72), (0.95, -1.06),
                      (0.52, -1.27), (0.0, -1.34), (-0.52, -1.28), (-0.95, -1.08), (-1.24, -0.72), (-1.38, -0.25),
                      (-1.40, 0.30), (-1.32, 0.78), (-1.04, 0.98), (-0.8, 0.86), (0.0, 0.5), (0.8, 0.86)], 9)
    strands = noise(H, W * 5, 1.8 * up, 1, seed + 3)[:, ::5]
    sheen = np.exp(-(((X + 0.55) / 0.45) ** 2 + ((Y + 0.95) / 0.30) ** 2))
    sheen_side = np.exp(-(((X + 1.18) / 0.16) ** 2 + ((Y - 0.1) / 0.55) ** 2))
    hair_l = 0.06 + 0.05 * strands + (0.24 * sheen + 0.12 * sheen_side) * (0.55 + 0.45 * strands)
    lum = lum * (1 - back) + back * hair_l
    # face: ellipsoid shading
    taper = 1 - 0.30 * np.clip(Y, 0, 1) ** 1.6
    rr = np.sqrt((X / taper) ** 2 + Y ** 2)
    face = smooth(1.03, 0.97, rr)
    z = np.sqrt(np.clip(1 - (X / taper) ** 2 * 0.85 - Y ** 2 * 0.6, 0.02, 1))
    nxv, nyv, nzv = X * 0.9, Y * 0.6, z
    nn = np.sqrt(nxv ** 2 + nyv ** 2 + nzv ** 2)
    Lx, Ly, Lz = -0.55, -0.30, 0.78
    lam = np.clip((nxv * Lx + nyv * Ly + nzv * Lz) / nn, 0, 1)
    fl = 0.12 + 0.74 * lam
    for sx in (-1, 1):
        ex, ey = sx * 0.40, -0.10
        sock = np.exp(-(((X - ex) / 0.30) ** 2 + ((Y - ey) / 0.17) ** 2))
        fl = fl - 0.10 * sock
        lid = np.exp(-(((X - ex) / 0.17) ** 2 + ((Y - ey + 0.015 * 0) / 0.035) ** 2))
        fl = fl * (1 - 0.60 * lid)
        iris = np.exp(-(((X - ex - 0.02) / 0.065) ** 2 + ((Y - ey - 0.01) / 0.055) ** 2))
        fl = fl * (1 - 0.70 * iris)
        lash = np.exp(-(((X - ex) / 0.19) ** 2 + ((Y - ey + 0.045) / 0.02) ** 2))
        fl = fl * (1 - 0.45 * lash)
        by = ey - 0.20 - 0.05 * np.cos((X - ex) * 3.0)
        brow = np.exp(-((Y - by) / 0.028) ** 2) * np.exp(-((X - ex - sx * 0.04) / 0.22) ** 4)
        fl = fl * (1 - 0.55 * brow)
    nose_sh = np.exp(-(((X - 0.10) / 0.07) ** 2 + ((Y - 0.14) / 0.20) ** 2))
    fl = fl - 0.09 * nose_sh
    tip_sh = np.exp(-(((X - 0.02) / 0.16) ** 2 + ((Y - 0.36) / 0.035) ** 2))
    fl = fl - 0.10 * tip_sh
    bridge = np.exp(-(((X + 0.03) / 0.05) ** 2 + ((Y - 0.12) / 0.20) ** 2))
    fl = fl + 0.05 * bridge
    mouth = np.exp(-((X / 0.25) ** 4 + ((Y - 0.585) / 0.020) ** 2))
    fl = fl * (1 - 0.50 * mouth)
    upper = np.exp(-((X / 0.20) ** 2 + ((Y - 0.55) / 0.03) ** 2))
    fl = fl - 0.06 * upper
    lower = np.exp(-((X / 0.17) ** 2 + ((Y - 0.64) / 0.035) ** 2))
    fl = fl + 0.03 * lower
    cheek = np.exp(-(((X + 0.48) / 0.25) ** 2 + ((Y - 0.22) / 0.18) ** 2))
    fl = fl + 0.03 * cheek
    lum = lum * (1 - face) + face * np.clip(fl, 0.06, 0.95)
    # front hair: side-swept fringe from a left parting, and locks over the cheek edges
    fringe = poly_mask([(-0.40, -1.30), (0.6, -1.25), (1.18, -0.92), (1.16, -0.30), (0.78, -0.36), (0.30, -0.50),
                        (-0.20, -0.64), (-0.70, -0.74), (-1.06, -0.62), (-1.20, -0.80), (-0.95, -1.15)], 9)
    rlock = poly_mask([(0.80, -0.50), (1.15, -0.55), (1.36, 0.20), (1.26, 0.80), (1.00, 0.97), (0.86, 0.62),
                       (0.90, 0.10)], 6)
    llock = poly_mask([(-0.86, -0.45), (-1.20, -0.55), (-1.36, 0.20), (-1.28, 0.80), (-1.04, 0.97), (-0.93, 0.60),
                       (-0.96, 0.10)], 6)
    front = np.clip(fringe + rlock + llock, 0, 1)
    part = np.exp(-(((X + 0.40) / 0.05) ** 2) - ((Y + 1.10) / 0.25) ** 2)
    fsheen = np.exp(-(((X + 0.15) / 0.55) ** 2 + ((Y + 0.92) / 0.18) ** 2))
    hair_f = 0.06 + 0.05 * strands + 0.26 * fsheen * (0.5 + 0.5 * strands) + 0.10 * part
    shade = blur(np.roll(front, int(0.07 * fh), 0), 2.5 * up) * face
    lum = lum * (1 - 0.40 * shade)
    lum = lum * (1 - front) + front * hair_f
    lum = blur(lum, 0.5 * up)
    out = np.asarray(Image.fromarray(lum.astype(np.float32), "F").resize((w, h), Image.BOX), np.float32)
    out = out + r.normal(0, 0.018, out.shape).astype(np.float32)
    return np.clip(out, 0, 1)


# =================================================================================================
# Badge (860 x 540, RGBA: rounded corners)
# =================================================================================================
def badge(lang: str = "en"):
    W, H = 860, 540
    rgb = paper(W, H, base=(232, 224, 204), seed=701, stains=1, vignette=0.12, fibres=0.6)
    # guilloche security print (pale green rosette lines)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    gx, gy = 610, 330
    rr = np.hypot(xx - gx, yy - gy)
    th = np.arctan2(yy - gy, xx - gx)
    g1 = np.abs(np.sin(rr / 4.2 + 1.6 * np.sin(th * 12)))
    g2 = np.abs(np.sin(rr / 4.2 - 1.6 * np.sin(th * 12 + 0.5)))
    guil = (smooth(0.93, 0.99, g1) + smooth(0.93, 0.99, g2)) * (1 - smooth(200, 330, rr)) * smooth(30, 60, rr)
    rgb = paint(rgb, np.clip(guil, 0, 1), "#A9C2AE", 0.40)
    # top band
    band = Pen(W, H, 4)
    band.rect(0, 0, W, 112)
    bm = band.arr()
    rgb = paint(rgb, bm, "#23443A")
    stripe = Pen(W, H, 4)
    stripe.rect(0, 112, W, 120)
    rgb = paint(rgb, stripe.arr(), "#B08D57")
    hdr = Pen(W, H, 4)
    draw_mark(hdr, 70, 56, 92, ticks=True, ring_w=0.05, line_w=0.05)
    hdr.text(128, 50, t("inst_sp", lang), F_SERIF_B, 50, anchor="lm", spacing=2.5, max_w=W - 128 - 24)
    hdr.text(130, 92, t("badge_sub", lang), F_SANS_B, 21, anchor="lm", spacing=3, max_w=W - 130 - 24)
    rgb = paint(rgb, hdr.arr(), "#EDE3C8")
    # photo
    px0, py0, pw, ph = 40, 146, 230, 292
    por = portrait(pw, ph, 41)
    sep = np.stack([por * 1.0, por * 0.96, por * 0.86], -1) * 255 * 0.98 + 6
    rgb[py0:py0 + ph, px0:px0 + pw] = sep
    pf = Pen(W, H, 4)
    pf.rect(px0 - 1, py0 - 1, px0 + pw + 1, py0 + ph + 1, outline=2)
    rgb = paint(rgb, pf.arr(), "#3A3328", 0.8)
    # text block
    tx = Pen(W, H, 4)
    tx.text(304, 178, t("badge_name", lang), F_SANS_B, 52, anchor="ls", max_w=W - 304 - 24)
    tx.text(306, 220, t("dept", lang), F_SANS, 31, anchor="ls", max_w=W - 306 - 24)
    tx.text(306, 256, t("badge_role", lang), F_SANS, 24, anchor="ls", max_w=W - 306 - 24)
    rgb = paint(rgb, ink(tx.arr(), 702, 0.12), "#1C1E22")
    lab = Pen(W, H, 4)
    lab.text(306, 302, t("staff_no", lang), F_SANS_B, 20, anchor="ls", spacing=2, max_w=240)
    lab.text(306, 452, t("issued", lang), F_SANS_B, 18, anchor="ls", spacing=2, max_w=230)
    lab.text(560, 498, t("signature", lang), F_SANS_B, 16, anchor="ls", spacing=2, max_w=240)
    lab.rect(560, 472, 800, 473.5)
    rgb = paint(rgb, lab.arr(), "#4A5A50")
    num = Pen(W, H, 4)
    num.text(300, 410, "№", F_TYPE_B, 70, anchor="ls")
    num.text(372, 416, BADGE_NO, F_TYPE_B, 128, anchor="ls", spacing=2)
    rgb = paint(rgb, ink(num.arr(), 703, 0.10), "#14161A")
    yr = Pen(W, H, 4)
    yr.text(306, 492, "1976", F_TYPE_B, 34, anchor="ls")
    rgb = paint(rgb, yr.arr(), "#1C1E22")
    sig = Pen(W, H, 4)
    rot_text(sig, 676, 452, t("sig_leyla", lang), F_HAND, 48, angle=4, weight=520)
    rgb = paint(rgb, ink(sig.arr(), 704, 0.25), "#22306A", 0.9)
    # access-level diagonal stripe (red) in the lower right corner
    ds = Pen(W, H, 4)
    ds.poly([(W - 120, H), (W, H - 120), (W, H - 86), (W - 86, H)])
    rgb = paint(rgb, ds.arr(), "#A8322A", 0.9)
    # round violet stamp over the photo corner
    st = Pen(W, H, 4)
    sx, sy, sr = 248, 404, 62
    st.ring(sx, sy, sr, 4)
    st.ring(sx, sy, sr - 18, 2.5)
    arc_text(st, sx, sy, sr - 15, t("stamp_inst", lang), F_SANS_B, 13, a_mid=-90, spacing=1.05, max_deg=200)
    arc_text(st, sx, sy, sr - 15, t("stamp_personnel", lang), F_SANS_B, 13, a_mid=90, spacing=1.05, inward=True,
             max_deg=130)
    draw_mark(st, sx, sy, 58, ticks=False, ring_w=0.06, line_w=0.06)
    sm = st.arr() * stamp_mask(W, H, 705, 0.3)
    rgb = paint(rgb, sm, "#4B3C8C", 0.72)
    # lamination: gloss streak + slight edge yellowing
    gl = np.clip(1 - np.abs((xx * 0.55 - yy + 120) / 90.0), 0, 1) ** 2
    rgb = rgb + (gl * 18)[..., None]
    rgb = multiply(rgb, edge_wear(W, H, 706, 18, 0.12), "#8A7A50")
    cm = Pen(W, H, 4)
    cm.rect(0, 0, W - 0.5, H - 0.5, radius=32)
    save(to_img(rgb, cm.arr()), lname("badge.png", lang))


# =================================================================================================
# Index card / request card (1250 x 750)
# =================================================================================================
def card_outline_alpha(notched=(), clip_tl: float = 0.0) -> np.ndarray:
    """Card alpha: rounded corners, V-notches at the given positions (1..8), optional clipped corner."""
    pen = Pen(CARD_W, CARD_H, 4)
    pen.rect(0, 0, CARD_W, CARD_H, radius=CARD_CORNER_PX)
    for k in notched:
        x = card_pos_x(k)
        pen.poly([(x - NOTCH_W_PX / 2, -1), (x + NOTCH_W_PX / 2, -1), (x + NOTCH_FLAT_PX / 2, NOTCH_D_PX),
                  (x - NOTCH_FLAT_PX / 2, NOTCH_D_PX)], 0)
    if clip_tl:
        pen.poly([(-1, -1), (clip_tl + 1, -1), (-1, clip_tl + 1)], 0)
    return pen.arr()


def punch_positions(pen: Pen, numbers: bool = True, ring_w: float = 3.0):
    for k in range(1, 9):
        x = card_pos_x(k)
        pen.ring(x, HOLE_V_PX, HOLE_R_PX, ring_w)
        if numbers:
            pen.text(x, HOLE_V_PX + HOLE_R_PX + 26, str(k), F_SANS_B, 30)


def index_card(lang: str = "en"):
    W, H = CARD_W, CARD_H
    rng = np.random.default_rng(800)
    rgb = paper(W, H, base=(246, 240, 222), seed=801, stains=1, vignette=0.12, fibres=0.8)
    # printed form: red header rule, blue ruling
    pr = Pen(W, H, 4)
    for y in range(318, H - 60, 62):
        pr.rect(36, y, W - 36, y + 1.6)
    rgb = paint(rgb, pr.arr(), "#7C9BC0", 0.75)
    red = Pen(W, H, 4)
    red.rect(36, 196, W - 36, 199.5)
    red.rect(36, 204, W - 36, 205.5)
    red.rect(250, 262, 252, H - 40)
    rgb = paint(rgb, red.arr(), "#C0574B", 0.8)
    # edge positions 1..8 (printed circles + numbers)
    pp = Pen(W, H, 4)
    punch_positions(pp)
    rgb = paint(rgb, ink(pp.arr(), 802, 0.15), "#3A3F4A", 0.9)
    hd = Pen(W, H, 4)
    hd.text(40, 244, t("ic_header", lang), F_SANS_B, 22, anchor="ls", spacing=1.5, max_w=W - 80)
    rgb = paint(rgb, hd.arr(), "#8A3A30", 0.85)
    # typed entries
    tp = Pen(W, H, 4)
    typed(tp, 860, 300, "№ " + BADGE_NO, 56, rng, path=F_TYPE_B)
    typed(tp, 40, 312, "0417", 34, rng)
    typed(tp, 272, 372, t("ic_name", lang), 50, rng, path=F_TYPE_B, max_w=W - 272 - 40)
    typed(tp, 272, 434, t("ic_role", lang), 38, rng, max_w=W - 272 - 40)
    typed(tp, 272, 496, t("ic_lab", lang), 38, rng, max_w=W - 272 - 40)
    typed(tp, 272, 558, t("ic_file", lang), 38, rng, max_w=W - 272 - 40)
    typed(tp, 40, 434, "R-12", 34, rng)
    rgb = paint(rgb, ink(tp.arr(), 803, 0.3, 1.6), "#1E1F26", 0.92)
    # pencil note
    pc = Pen(W, H, 4)
    note = t("ic_note", lang)
    nsize, _ = fit(note, F_HAND, 58, 370, weight=560)
    rot_text(pc, 1022, 636, note, F_HAND, nsize, angle=6, weight=560)
    pc.line([(736, 664), (778, 656), (812, 660)], 3.0)
    pc.line([(792, 674), (812, 660), (794, 644)], 3.0)
    rgb = paint(rgb, ink(pc.arr(), 804, 0.5, 1.4), "#5A5A60", 0.85)
    # catalogue rod hole (bottom centre) -- dark so it reads as a hole even without alpha
    hole = Pen(W, H, 4)
    hole.circle(W / 2, H - 52, 30)
    hm = hole.arr()
    rgb = paint(rgb, np.clip(blur(hm, 3) - hm, 0, 1), "#8A7A5A", 0.6)
    # handling: thumb grime on the top edge, soft fold, foxing
    rgb = multiply(rgb, edge_wear(W, H, 805, 26, 0.16), "#8C7650")
    alpha = card_outline_alpha([k + 1 for k, b in enumerate(PUNCH_CODE) if b])
    cut = 1 - alpha
    rgb = paint(rgb, np.clip(blur(cut, 2.0) - cut, 0, 1), "#7A6848", 0.55)   # cut edges darken slightly
    alpha = np.clip(alpha - hm, 0, 1)
    rgb = paint(rgb, 1 - alpha, "#2A2620")
    save(to_img(rgb, alpha), lname("index_card.png", lang))


def request_card(lang: str = "en"):
    W, H = CARD_W, CARD_H
    rgb = paper(W, H, base=(220, 200, 156), seed=820, stains=1, vignette=0.12, fibres=0.9)
    pp = Pen(W, H, 4)
    punch_positions(pp, ring_w=3.5)
    rgb = paint(rgb, ink(pp.arr(), 821, 0.15), "#4A3A28", 0.9)
    hd = Pen(W, H, 4)
    hd.rect(36, 192, W - 36, 262, radius=4)
    hm = hd.arr()
    rgb = paint(rgb, hm, "#9A3B2E", 0.92)
    ht = Pen(W, H, 4)
    ht.text(W / 2, 228, t("rc_header", lang), F_GOTHIC, 46, spacing=4, max_w=W - 140)
    rgb = paint(rgb, ht.arr(), "#E9DAB8")
    f = Pen(W, H, 4)
    fields = [(t("staff_no", lang), 344), (t("surname", lang), 418), (t("rc_item", lang), 492),
              (t("rc_date", lang), 566)]
    for i, (label, y) in enumerate(fields):
        f.text(52, y, label, F_SANS_B, 26, anchor="ls", spacing=1.5, max_w=220)
        for x in range(290, W - 300 if i == 3 else W - 50, 14):
            f.rect(x, y + 2, x + 7, y + 4)
    f.text(W - 280, 566, t("rc_sign", lang), F_SANS_B, 26, anchor="ls", spacing=1.5, max_w=78)
    for x in range(W - 190, W - 50, 14):
        f.rect(x, 568, x + 7, 570)
    f.text(52, 660, t("rc_instr", lang), F_SANS, 22, anchor="ls", max_w=W - 52 - 230)
    f.text(W - 52, 700, t("rc_form", lang), F_SANS, 20, anchor="rs")
    rgb = paint(rgb, ink(f.arr(), 822, 0.15), "#4A3424", 0.85)
    # small canister pictogram in the corner
    cp = Pen(W, H, 4)
    cx, cy = W - 120, 640
    cp.rect(cx - 44, cy - 15, cx + 44, cy + 15, radius=14)
    cp.rect(cx - 29, cy - 16, cx - 26, cy + 16, 0)
    cp.rect(cx + 26, cy - 16, cx + 29, cy + 16, 0)
    cp.rect(cx + 44, cy - 5, cx + 54, cy + 5, radius=2)
    for xo in (-70, -88, -106):
        cp.rect(cx + xo, cy - 2, cx + xo + 10, cy + 2)
    rgb = paint(rgb, cp.arr(), "#9A3B2E", 0.8)
    rgb = multiply(rgb, edge_wear(W, H, 823, 22, 0.12), "#8C7650")
    alpha = card_outline_alpha(clip_tl=REQ_CLIP_PX)
    save(to_img(rgb, alpha), lname("request_card.png", lang))


# =================================================================================================
# File cover (1200 x 1600 manila folder)
# =================================================================================================
def file_cover(lang: str = "en"):
    W, H = 1200, 1600
    rng = np.random.default_rng(900)
    rgb = paper(W, H, base=(216, 192, 142), seed=901, stains=1, vignette=0.28, fibres=1.3)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # creases (vertical score lines near the spine edge) and a soft diagonal bend
    for x0 in (36, 58):
        cr = np.exp(-((xx - x0) / 2.0) ** 2)
        rgb = rgb * (1 - 0.10 * cr)[..., None] + (np.exp(-((xx - x0 - 3) / 2.0) ** 2) * 10)[..., None]
    bend = np.exp(-((xx * 0.4 + yy - 1450) / 60.0) ** 2) * 0.05
    rgb = rgb * (1 - bend)[..., None]
    # printed header
    pr = Pen(W, H, 4)
    draw_mark(pr, 170, 170, 150, ticks=True)
    pr.text(270, 150, t("inst", lang), F_SERIF_B, 72, anchor="ls", spacing=2, max_w=W - 270 - 90)
    pr.text(274, 205, t("fc_sub", lang), F_SANS_B, 30, anchor="ls", spacing=4, max_w=W - 274 - 90)
    pr.rect(90, 270, W - 90, 276)
    pr.rect(90, 284, W - 90, 286)
    rgb = paint(rgb, ink(pr.arr(), 902, 0.25), "#3A2E22", 0.88)
    # big title
    tt = Pen(W, H, 4)
    tt.text(W / 2, 400, t("fc_title", lang), F_GOTHIC, 118, spacing=12, max_w=W - 200)
    rgb = paint(rgb, ink(tt.arr(), 903, 0.3), "#2E241A", 0.9)
    # pasted label with typed entries
    lb = Pen(W, H, 4)
    lb.rect(150, 480, W - 150, 860, radius=10)
    lm = lb.arr()
    lab_rgb = paper(W, H, base=(238, 230, 210), seed=904, stains=0, vignette=0.0, fibres=0.6)
    rgb = paint(rgb, blur(lm, 6), "#5A4528", 0.25)
    rgb = rgb * (1 - lm[..., None]) + lab_rgb * lm[..., None]
    fr = Pen(W, H, 4)
    fr.rect(172, 502, W - 172, 838, radius=6, outline=3)
    for y in (612, 712):
        fr.rect(190, y, W - 190, y + 1.5)
    fr.text(194, 540, t("fc_f_name", lang), F_SANS_B, 20, anchor="ls", spacing=2, max_w=480)
    fr.text(194, 642, t("fc_f_dept", lang), F_SANS_B, 20, anchor="ls", spacing=2, max_w=480)
    fr.text(194, 742, t("staff_no1", lang), F_SANS_B, 20, anchor="ls", spacing=2, max_w=480)
    fr.text(700, 742, t("fc_f_file", lang), F_SANS_B, 20, anchor="ls", spacing=2, max_w=300)
    rgb = paint(rgb, fr.arr() * lm, "#5A4A3A", 0.8)
    tp = Pen(W, H, 4)
    typed(tp, 200, 600, t("badge_name", lang), 76, rng, path=F_TYPE_B, max_w=W - 200 - 200)
    typed(tp, 200, 696, t("fc_dept", lang), 56, rng, max_w=W - 200 - 200)
    typed(tp, 200, 812, "№ " + BADGE_NO, 76, rng, path=F_TYPE_B)
    typed(tp, 700, 812, "B-3", 64, rng, path=F_TYPE_B)
    rgb = paint(rgb, ink(tp.arr(), 905, 0.3, 1.6), "#1C1C22", 0.92)
    # red stamp, rotated
    st = Pen(W, H, 4)
    sm_img = Image.new("L", (760 * 4, 230 * 4), 0)
    sd = ImageDraw.Draw(sm_img)
    sd.rounded_rectangle([8, 8, 760 * 4 - 8, 230 * 4 - 8], radius=40, outline=255, width=36)
    sd.rounded_rectangle([60, 60, 760 * 4 - 60, 230 * 4 - 60], radius=24, outline=255, width=12)
    s1, sp1 = fit(t("fc_stamp", lang), F_GOTHIC, 96 * 4, 640 * 4)
    draw_text(sd, 380 * 4, 92 * 4, t("fc_stamp", lang), F_GOTHIC, s1, 255, "mm")
    s2, sp2 = fit(t("fc_stamp2", lang), F_SANS_B, 46 * 4, 640 * 4)
    draw_text(sd, 380 * 4, 172 * 4, t("fc_stamp2", lang), F_SANS_B, s2, 255, "mm")
    st.paste_rotated(sm_img, 640, 1080, 9)
    sm = st.arr() * stamp_mask(W, H, 906, 0.55)
    rgb = paint(rgb, sm, "#B0302A", 0.78)
    # handwritten pencil note + filing number
    hw = Pen(W, H, 4)
    rot_text(hw, 300, 1290, t("fc_note", lang), F_HAND, 64, angle=-3, weight=560)
    rot_text(hw, W - 200, 1520, "B-3 / 0417", F_HAND, 52, angle=2, weight=520)
    rgb = paint(rgb, ink(hw.arr(), 907, 0.45, 1.4), "#4A4A50", 0.8)
    # coffee ring
    cx, cy, cr = 880, 1340, 128
    d = np.hypot(xx - cx, (yy - cy) * 1.04)
    ringm = np.exp(-((d - cr) / 7.0) ** 2) * (0.5 + 0.5 * noise(H, W, 25, 2, 908))
    inside = (d < cr) * 0.10 * noise(H, W, 40, 2, 909)
    drip = np.exp(-(((xx - cx - 70) / 22.0) ** 2 + ((yy - cy - 150) / 16.0) ** 2))
    rgb = multiply(rgb, np.clip(ringm * 0.55 + inside + drip * 0.4, 0, 1), "#6A3E1A")
    # wear: edge darkening, corner rub
    rgb = multiply(rgb, edge_wear(W, H, 910, 70, 0.30), "#7A5A30")
    save(to_img(rgb), lname("file_cover.png", lang))


# =================================================================================================
# Tape hub labels (512 x 512, RGBA: round label with spindle hole)
# =================================================================================================
TAPE_INK = {1996: "#24357A", 1997: "#1E1E24", 1998: "#3A2E7A"}


def tape_label(year: int, lang: str = "en"):
    S = 512
    c = S / 2
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    rr = np.hypot(xx - c + 0.5, yy - c + 0.5)
    rgb = paper(S, S, base=(234, 226, 204), seed=year + 7, stains=1 if year != 1996 else 2, vignette=0.0,
                fibres=0.8)
    # printed band (manufacturer's orange ring) with arc text
    band = smooth(206, 208, rr) * (1 - smooth(246, 248, rr))
    rgb = paint(rgb, band, "#C2562E", 0.92)
    bt = Pen(S, S, 4)
    arc_text(bt, c, c, 219, t("tl_top", lang), F_SANS_B, 22, a_mid=-90, spacing=1.15, max_deg=110)
    arc_text(bt, c, c, 235, t("archive_b_sp", lang), F_SANS_B, 22, a_mid=90, spacing=1.2, inward=True, max_deg=90)
    for a in (-160, -20, 20, 160):
        ra = math.radians(a)
        bt.circle(c + 227 * math.cos(ra), c + 227 * math.sin(ra), 4)
    rgb = paint(rgb, bt.arr() * band, "#F3E6CF", 0.95)
    # printed fields
    pf = Pen(S, S, 4)
    pf.ring(c, c, 62, 2.5)
    pf.rect(118, 160, 394, 162)
    pf.text(150, 92, t("tl_date", lang), F_SANS_B, 15, anchor="ls", spacing=1.5, max_w=200)
    pf.rect(112, 396, 318, 398)
    pf.text(184, 270, t("tl_speed", lang), F_SANS_B, 15, anchor="rs", spacing=1.5, max_w=118)   # clear of the hub ring
    pf.text(326, 392, t("tl_unit", lang), F_SANS_B, 30, anchor="ls", max_w=70)
    rgb = paint(rgb, ink(pf.arr(), year + 1, 0.15), "#8A3A24", 0.85)
    # Leyla's handwriting
    hw = Pen(S, S, 4)
    tilt = {1996: -4, 1997: -2, 1998: -6}[year]
    rot_text(hw, 258, 134, f"{t('tl_init', lang)} {year}", F_HAND, 66, angle=tilt * 0.5, weight=640)
    rot_text(hw, 214, 352, TAPE_SPEED, F_HAND, 140, angle=tilt, weight=700)
    hw.line([(128, 412), (306, 405)], 4.0)   # underline the speed
    rgb = paint(rgb, ink(hw.arr(), year + 2, 0.25, 1.4), TAPE_INK[year], 0.95)
    # handling: grime, a little tape-oxide smudge
    smudge = smooth(0.70, 0.95, noise(S, S, 40, 3, year + 3)) * 0.25
    rgb = multiply(rgb, smudge, "#6A4A30")
    rgb = multiply(rgb, smooth(200, 256, rr) * 0.18, "#7A6040")
    # alpha: disc with spindle hole + 3 drive keyways
    al = Pen(S, S, 4)
    al.circle(c, c, 252)
    al.circle(c, c, 44, 0)
    for k in range(3):
        a = math.radians(-90 + 120 * k)
        kx, ky = c + 44 * math.cos(a), c + 44 * math.sin(a)
        al.circle(kx, ky, 11, 0)
    alpha = al.arr()
    edge = np.clip(blur(1 - alpha, 1.5) - (1 - alpha), 0, 1)
    rgb = paint(rgb, edge, "#7A6448", 0.6)
    save(to_img(rgb, alpha), lname(f"tape_label_{year}.png", lang))


# =================================================================================================
# Lantern slide (512 x 512, RGBA: clear glass)
# =================================================================================================
def slide_mark():
    S = 512
    c = S / 2
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    # clear glass with faint green edge tint and specks
    rgb = solid(S, S, "#DDE6E2")
    alpha = np.full((S, S), 0.10, np.float32)
    # cream paper mask with a round opening (under the tape), with a printed rule and the maker's notes
    mk = Pen(S, S, 4)
    mk.rect(0, 0, S, S)
    mk.circle(c, c, 214, 0)
    mm = mk.arr()
    mask_rgb = paper(S, S, base=(230, 220, 196), seed=955, stains=0, vignette=0.0, fibres=0.8)
    rgb = rgb * (1 - mm[..., None]) + mask_rgb * mm[..., None]
    rgb = paint(rgb, np.clip(blur(1 - mm, 1.5) - (1 - mm), 0, 1) * mm, "#6A5A40", 0.6)   # cut edge of the opening
    pr = Pen(S, S, 4)
    pr.ring(c, c, 222, 1.6)
    rgb = paint(rgb, pr.arr() * mm, "#5A4A36", 0.7)
    hw = Pen(S, S, 4)
    rot_text(hw, S - 108, S - 50, "E.S. 1971", F_HAND, 30, angle=0, weight=520)
    rgb = paint(rgb, ink(hw.arr(), 956, 0.3) * mm, "#2A2A40", 0.8)
    alpha = np.maximum(alpha, mm * 0.97)
    # the mark: black emulsion, slightly soft, with tiny emulsion pinholes
    m = mark_mask(400)
    mark = np.zeros((S, S), np.float32)
    mark[56:456, 56:456] = m
    pin = (noise(S, S, 1.2, 1, 951) > 0.93).astype(np.float32) * 0.4
    mark = mark * (1 - pin * mark)
    rgb = paint(rgb, mark, "#0E0F10")
    alpha = np.maximum(alpha, mark * 0.94)
    # tape binding border (black gummed paper), slightly ragged inner edge
    d = np.minimum(np.minimum(xx, S - 1 - xx), np.minimum(yy, S - 1 - yy))
    rag = 30 + 3 * noise(S, S, 10, 2, 952)
    tape = smooth(rag + 1.2, rag - 1.2, d)
    tape_rgb = solid(S, S, "#1E1C1A") * (0.9 + 0.25 * noise(S, S, 3, 2, 953))[..., None]
    scuff = smooth(0.72, 0.9, noise(S, S, 12, 3, 954)) * tape
    tape_rgb = paint(tape_rgb, scuff, "#6A645A", 0.6)
    rgb = rgb * (1 - tape[..., None]) + tape_rgb * tape[..., None]
    alpha = np.maximum(alpha, tape)
    # thumb-spot label (white paper dot) at the bottom-left, with Strand's star
    tl = Pen(S, S, 4)
    tl.circle(44, S - 44, 20)
    tm = tl.arr()
    rgb = paint(rgb, tm, "#ECE4D0")
    st = Pen(S, S, 4)
    picto(st, "star", 44, S - 44, 26)
    rgb = paint(rgb, st.arr(), "#8A2A22")
    alpha = np.maximum(alpha, tm)
    # glass sheen
    sh = np.clip(1 - np.abs((xx - yy * 0.6 - 120) / 60.0), 0, 1) * (1 - mm) * (1 - mark)
    rgb = paint(rgb, sh, "#FFFFFF", 0.4)
    alpha = np.maximum(alpha, sh * 0.25)
    save(to_img(rgb, alpha), "slide_mark.png")


# =================================================================================================
# Film look helpers
# =================================================================================================
def tone_curve(x: np.ndarray, contrast: float = 1.15, toe: float = 0.03) -> np.ndarray:
    """Filmic S-curve on 0..1 values."""
    x = np.clip(x, 0, None)
    y = 1.0 - np.exp(-x * 2.2)                                         # soft shoulder
    y = y / (1.0 - math.exp(-2.2 * 1.2))
    y = np.clip(y, 0, 1)
    y = 0.5 + (y - 0.5) * contrast
    return np.clip(y * (1 - toe) + toe, 0, 1)


def film_finish(lum: np.ndarray, seed: int, grain_amt=0.055, scratches=6, dust=60, vignette=0.55,
                weave=(2, 1), gate=True, tint=(1.0, 0.985, 0.95), hair=True, halation=0.0,
                contrast=1.15, flicker=0.0, dust_big=0.1) -> np.ndarray:
    """Turn a linear luminance scene (0..~2) into a 1979 black-and-white projected print (sRGB 0..255)."""
    h, w = lum.shape
    r = np.random.default_rng(seed)
    x = lum.astype(np.float32)
    if halation:
        x = x + halation * blur(np.clip(x - 0.8, 0, None), 0.008 * w) + halation * 0.5 * blur(np.clip(x - 0.6, 0, None), 0.035 * w)
    yy, xx = np.mgrid[0:h, 0:w]
    dn = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    x = x * (1.0 - vignette * smooth(0.35, 1.45, dn))                    # projector hotspot / lens falloff
    if flicker:
        x = x * (1 + flicker * (noise(h, w, w * 0.6, 2, seed + 9) - 0.5))
    y = tone_curve(x, contrast)
    g = grain(h, w, seed + 1, 0.6) * 0.7 + grain(h, w, seed + 2, 1.6) * 0.5
    mid = 0.35 + 0.65 * (1 - np.abs(y - 0.5) * 2) ** 0.6
    y = y + grain_amt * g * mid
    for _ in range(scratches):
        sx = r.uniform(0.04, 0.96) * w
        y0, y1 = sorted(r.uniform(0, h, 2))
        if r.random() < 0.5:
            y0, y1 = 0, h
        col = (np.arange(h) >= y0) & (np.arange(h) <= y1)
        wob = sx + 1.5 * np.sin(np.arange(h) / r.uniform(40, 120) + r.uniform(0, 6))
        width = r.uniform(0.5, 1.4)
        strength = r.uniform(0.06, 0.22) * (1 if r.random() < 0.6 else -1)
        brk = noise(h, 1, r.uniform(8, 30), 1, int(r.integers(1e6)))[:, 0] > 0.35
        for yi in np.nonzero(col & brk)[0]:
            xc = wob[yi]
            x0i = int(max(0, xc - 2))
            for xi in range(x0i, min(w, x0i + 5)):
                f = max(0.0, 1 - abs(xi - xc) / width)
                y[yi, xi] += strength * f
    dl = np.zeros((h, w), np.float32)
    dd = np.zeros((h, w), np.float32)
    for _ in range(dust):
        cx, cy = r.uniform(0, w), r.uniform(0, h)
        rad = r.uniform(0.6, 2.6) if r.random() > dust_big else r.uniform(3, 6)
        tgt = dd if r.random() < 0.7 else dl
        x0, x1 = int(max(0, cx - rad - 2)), int(min(w, cx + rad + 3))
        y0, y1 = int(max(0, cy - rad - 2)), int(min(h, cy + rad + 3))
        sub = np.sqrt((xx[y0:y1, x0:x1] - cx) ** 2 + ((yy[y0:y1, x0:x1] - cy) * r.uniform(0.6, 1.4)) ** 2)
        tgt[y0:y1, x0:x1] = np.maximum(tgt[y0:y1, x0:x1], np.clip(rad - sub + 0.5, 0, 1))
    if hair:
        hp = Pen(w, h, 2)
        hx, hy = r.uniform(0.05, 0.25) * w, r.uniform(0.6, 0.95) * h
        pts = []
        ang = r.uniform(0, 6.28)
        for _ in range(60):
            ang += r.normal(0, 0.12)
            hx += 2.2 * math.cos(ang)
            hy += 2.2 * math.sin(ang)
            pts.append((hx, hy))
        hp.line(pts, 1.2, caps=False)
        dd = np.maximum(dd, hp.arr() * 0.8)
    y = y - 0.55 * dd + 0.45 * dl
    if gate:
        ox, oy = weave
        y = np.roll(np.roll(y, oy, 0), ox, 1)
        gp = Pen(w, h, 2)
        m = 10
        gp.rect(m + ox, m + oy, w - m + ox, h - m + oy, radius=26)
        gm = blur(gp.arr(), 3.0)
        y = y * gm + 0.02 * (1 - gm)
    y = np.clip(y, 0, 1)
    rgb = np.stack([y * tint[0], y * tint[1], y * tint[2]], -1) * 255.0
    return rgb


# =================================================================================================
# Film strips (900 x 300, RGBA: sprocket holes are transparent)
# =================================================================================================
STRIP_W, STRIP_H = 900, 300
STRIP_MARGIN = 54          # sprocket band height (top and bottom)
STRIP_FRAME_W = 270
STRIP_PITCH = 292          # frame pitch; frames centred at 450 - 292, 450, 450 + 292
SUN_H_UNITS = 2.2          # obelisk height in shadow units: tan(elevation) = 2.2 / L


def obelisk_scene(fw: int, fh: int, L: int, seed: int, unit_frac: float = 0.12) -> np.ndarray:
    """Sundial obelisk film frame (linear luminance 0..~1.8). Shadow length L units, 1 unit = unit_frac * fw.
    The sun is on the left; its elevation follows tan(e) = H / L for an obelisk H = 2.2 units tall.
    Marker posts on the ground at 1..5 units from the obelisk make the length easy to read."""
    u = unit_frac * fw
    H = SUN_H_UNITS
    elev = math.degrees(math.atan2(H, L))
    k = float(np.clip((elev - 28.8) / (65.6 - 28.8), 0, 1))     # 0 = dawn (L = 4) .. 1 = high sun (L = 1)
    hor = 0.56 * fh
    yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
    # sky (yellow-filtered B&W: darker overhead), dawn darker and graded toward the sun
    top, low = 0.16 + 0.22 * k, 0.50 + 0.12 * k
    sky = top + (low - top) * np.clip(yy / hor, 0, 1) ** 1.2
    sx = (0.09 + 0.06 * k) * fw
    sun_h = float(np.clip((elev - 18.0) / (68.0 - 18.0), 0, 1)) ** 1.15     # 0 on the horizon .. 1 high
    sy = hor - 0.06 * fh - sun_h * (hor - 0.17 * fh)
    d = np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2)
    sky = sky + (0.55 - 0.2 * k) * np.exp(-d / (0.16 * fw)) + 0.6 * np.exp(-(d / (0.05 * fw)) ** 2)
    sky = np.where(d < 0.034 * fw, 1.9, sky)
    img = sky.copy()
    # far hills
    ridge = hor - (3 + 7 * noise(1, fw, 40, 3, seed)[0]) * fh / 180
    img = np.where(yy > ridge[None, :], 0.30 + 0.10 * k, img)
    # ground: light paving, brighter toward the camera
    g = 0.58 + 0.16 * ((yy - hor) / (fh - hor))
    img = np.where(yy >= hor, g, img)
    bx = 0.22 * fw
    by = hor + 0.24 * fh          # obelisk base line on the ground
    # marker posts at 1..5 units, standing just behind the shadow line (a ruler)
    posts = Pen(fw, fh, 4)
    for i in range(1, 6):
        mx = bx + i * u
        posts.rect(mx - 0.0075 * fw, by - 0.085 * fh, mx + 0.0075 * fw, by - 0.020 * fh)
        posts.ellipse(mx, by - 0.020 * fh, 0.012 * fw, 0.006 * fh)
    pm = posts.arr()
    # shadow on the ground: from the base to L units, tapering to the tip
    shp = Pen(fw, fh, 4)
    tip = bx + L * u
    shp.poly([(bx, by - 0.020 * fh), (tip - 0.01 * fw, by - 0.006 * fh), (tip, by + 0.002 * fh),
              (tip - 0.01 * fw, by + 0.010 * fh), (bx, by + 0.032 * fh)])
    sm = blur(shp.arr(), 0.35 + 0.5 * (1 - k))
    img = img * (1 - 0.86 * sm)
    img = img * (1 - pm) + pm * 0.16
    # obelisk: tapered shaft + pyramidion, lit face toward the sun (left), dark face right
    ow = 0.085 * fw
    top_y = by - H * u
    w0, w1 = ow / 2, ow * 0.28
    cap = top_y + 0.30 * u
    lit = Pen(fw, fh, 4)
    lit.poly([(bx - w0, by), (bx - w1, cap), (bx, cap), (bx, by)])
    lit.poly([(bx - w1, cap), (bx, top_y - 0.05 * u), (bx, cap)])
    dark = Pen(fw, fh, 4)
    dark.poly([(bx, by), (bx, cap), (bx + w1, cap), (bx + w0, by)])
    dark.poly([(bx, cap), (bx, top_y - 0.05 * u), (bx + w1, cap)])
    base = Pen(fw, fh, 4)
    base.rect(bx - w0 * 1.5, by - 0.045 * fh, bx + w0 * 1.5, by + 0.012 * fh)
    lm, dm, bm = lit.arr(), dark.arr(), base.arr()
    img = img * (1 - lm) + lm * (0.70 + 0.2 * k)
    img = img * (1 - dm) + dm * 0.10
    img = img * (1 - bm) + bm * (0.34 + 0.1 * k)
    return img


def film_strip(k: int):
    L = SPLICE_SHADOWS[k]
    w, h = STRIP_W, STRIP_H
    r = np.random.default_rng(300 + k)
    fh = h - 2 * STRIP_MARGIN - 12
    y0 = STRIP_MARGIN + 6
    lum = np.zeros((h, w), np.float32) + 0.06
    for j, cx in enumerate((w / 2 - STRIP_PITCH, w / 2, w / 2 + STRIP_PITCH)):
        x0 = int(round(cx - STRIP_FRAME_W / 2))
        sc = obelisk_scene(STRIP_FRAME_W, fh, L, 310 + 10 * k + j)
        sc = sc * (0.97 + 0.06 * r.random())          # exposure flicker per frame
        fr = Pen(STRIP_FRAME_W, fh, 4)
        fr.rect(0, 0, STRIP_FRAME_W, fh, radius=6)
        fm = fr.arr()
        lum[y0:y0 + fh, x0:x0 + STRIP_FRAME_W] = lum[y0:y0 + fh, x0:x0 + STRIP_FRAME_W] * (1 - fm) + sc * fm
    holes = Pen(w, h, 4)
    pitch = STRIP_PITCH / 4.0
    hw, hh = 22, 30
    for i in range(-2, 16):
        hx = w / 2 - STRIP_PITCH * 1.5 + pitch * (i + 0.5)
        for hy in (STRIP_MARGIN / 2, h - STRIP_MARGIN / 2):
            if -hw < hx < w + hw:
                holes.rect(hx - hw / 2, hy - hh / 2, hx + hw / 2, hy + hh / 2, radius=5)
    hm = holes.arr()
    ep = Pen(w, h, 4)                      # latent edge marks: key-code bars and a triangle (no words)
    bars = [6, 2, 2, 6, 2, 6, 6, 2, 2, 2, 6]
    for ex in (w / 2 - STRIP_PITCH, w / 2 + STRIP_PITCH):
        bx_ = ex - 52
        for bw in bars:
            ep.rect(bx_, h - 15, bx_ + bw, h - 7)
            bx_ += bw + 3
        ep.poly([(ex + 62, h - 16), (ex + 72, h - 11), (ex + 62, h - 6)])
        for k in range(3):
            ep.circle(ex + 82 + 7 * k, h - 11, 1.8)
    lum = lum + ep.arr() * 0.45
    rgb = film_finish(lum, 330 + k, grain_amt=0.04, scratches=3, dust=16, vignette=0.0, gate=False,
                      tint=(1.0, 0.94, 0.82), hair=False, contrast=1.25, dust_big=0.0)
    yy, xx = np.mgrid[0:h, 0:w]
    edge = smooth(0, 50, np.minimum(xx, w - 1 - xx)).astype(np.float32)
    rgb = rgb * (0.80 + 0.20 * edge)[..., None]
    # base colour in the margins (amber safety base)
    margin = ((yy < y0 - 2) | (yy > y0 + fh + 2)).astype(np.float32)
    rgb = paint(rgb, margin * 0.55, "#3A2414")
    rim = np.clip(blur(hm, 1.0) - hm, 0, 1) * 1.6
    rgb = paint(rgb, rim, "#C8B48A", 0.5)
    alpha = np.clip(1 - hm, 0, 1)
    save(to_img(rgb, alpha), f"film_strip_{k}.png")


# =================================================================================================
# Reel can lid (800 x 800, RGBA: transparent outside the disc)
# =================================================================================================
def reel_can_lid():
    S = 800
    c = S / 2
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    rr = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / c
    disc = Pen(S, S, 4)
    disc.circle(c, c, c - 2)
    alpha = disc.arr()
    n = noise(S, S, 120, 4, 401)
    fine = noise(S, S, 3, 2, 402)
    base = hexf("#5E6A60")
    rgb = base[None, None, :] * (0.86 + 0.18 * n + 0.06 * (fine - 0.5))[..., None]
    ang = np.arctan2(yy - c, xx - c)
    for r0, r1, s in ((0.965, 1.0, 0.55), (0.90, 0.93, 1.25), (0.86, 0.885, 0.78), (0.30, 0.32, 1.18)):
        m = smooth(r0 - 0.008, r0, rr) * (1 - smooth(r1, r1 + 0.008, rr))
        rgb = rgb * (1 + (s - 1) * m)[..., None]
    shade = 1 + 0.10 * np.cos(ang + 2.4) * smooth(0.84, 0.99, rr)
    rgb = rgb * shade[..., None]
    scuff = smooth(0.70, 0.86, noise(S, S, 25, 3, 404)) * smooth(0.6, 1.0, rr)
    rgb = paint(rgb, scuff, "#A9A9A0", 0.65)
    rust = smooth(0.80, 0.95, noise(S, S, 6, 2, 405)) * (0.4 + 0.6 * smooth(0.85, 1.0, rr))
    rgb = paint(rgb, rust, "#6B3A1E", 0.6)
    # painted pictogram band (cream enamel) across the middle
    bw, bh = 640, 270
    bx0, by0 = c - bw / 2, c - bh / 2 + 30
    band = Pen(S, S, 4)
    band.rect(bx0, by0, bx0 + bw, by0 + bh, radius=20)
    bm = band.arr()
    cream = hexf("#E3D7B8") * (0.92 + 0.1 * noise(S, S, 60, 3, 406))[..., None]
    rgb = rgb * (1 - bm[..., None]) + cream * bm[..., None]
    # three panels: sunrise (long shadow) -> morning -> high sun (short shadow); sun on the left
    ink_p = Pen(S, S, 4)
    sun_p = Pen(S, S, 4)
    pw = (bw - 40) / 3
    ground = by0 + 172
    U = 24                                   # shadow unit (px)
    # (shadow units, sun x offset from the obelisk, sun height above the ground; None = on the horizon)
    for i, (shadow, sdx, sh) in enumerate(((4.2, -54, None), (2.4, -52, 78), (0.9, -24, 128))):
        px0 = bx0 + 20 + i * pw
        if i:
            ink_p.rect(px0 - 1.5, by0 + 22, px0 + 1.5, by0 + 200)      # panel divider
        ox = px0 + 0.42 * pw                  # obelisk x
        ink_p.rect(px0 + 14, ground, px0 + pw - 14, ground + 3)        # ground line
        ink_p.poly([(ox - 9, ground), (ox - 5, ground - 76), (ox + 5, ground - 76), (ox + 9, ground)])
        ink_p.poly([(ox - 5, ground - 76), (ox, ground - 88), (ox + 5, ground - 76)])
        ink_p.poly([(ox + 8, ground + 2), (ox + 8 + shadow * U, ground + 6), (ox + 8 + shadow * U, ground + 10),
                    (ox + 8, ground + 16)])
        sx = ox + sdx
        if sh is None:         # sunrise: half sun on the horizon
            sun_p.circle(sx, ground, 19)
            sun_p.rect(sx - 30, ground, sx + 30, ground + 30, v=0)
            for a in range(195, 346, 30):
                ra = math.radians(a)
                sun_p.line([(sx + 26 * math.cos(ra), ground + 26 * math.sin(ra)),
                            (sx + 37 * math.cos(ra), ground + 37 * math.sin(ra))], 4.5)
        else:
            sy = ground - sh
            sun_p.circle(sx, sy, 16)
            for a in range(0, 360, 45):
                ra = math.radians(a)
                sun_p.line([(sx + 22 * math.cos(ra), sy + 22 * math.sin(ra)),
                            (sx + 31 * math.cos(ra), sy + 31 * math.sin(ra))], 4.5)
    ay = by0 + bh - 36
    ink_p.rect(bx0 + 70, ay - 4, bx0 + bw - 100, ay + 4)
    ink_p.poly([(bx0 + bw - 108, ay - 20), (bx0 + bw - 62, ay), (bx0 + bw - 108, ay + 20)])
    im_ink = ink(ink_p.arr(), 407, 0.22) * bm
    im_sun = ink(sun_p.arr(), 408, 0.18) * bm
    rgb = paint(rgb, im_sun, "#C77A22", 0.95)
    rgb = paint(rgb, im_ink, "#24282A", 0.95)
    chips = smooth(0.80, 0.9, noise(S, S, 9, 3, 409)) * (blur(bm, 6) < 0.92) * bm
    rgb = paint(rgb, chips.astype(np.float32), "#545C55", 0.85)
    # masking tape with Strand's initials (dressing, no clue)
    tape = Pen(S, S, 4)
    tape.poly([(268, 158), (532, 140), (536, 206), (272, 224)])
    tm = tape.arr()
    rgb = paint(rgb, tm, "#D9C79A", 0.92)
    rgb = multiply(rgb, np.clip(blur(tm, 2) - tm, 0, 1), "#3A3A30", 0.5)
    hw = Pen(S, S, 4)
    rot_text(hw, 402, 180, "E.S.  1979", F_HAND, 50, angle=4, weight=620)
    rgb = paint(rgb, ink(hw.arr(), 410, 0.2) * tm, "#1E2340", 0.92)
    rgb = rgb * (0.94 + 0.06 * fine)[..., None]
    save(to_img(rgb, alpha), "reel_can_lid.png")


# =================================================================================================
# Linoleum texture set (1024^2, seamless: one repeat = 2 x 2 tiles of 0.30 m -> 0.6 m, M_Linoleum)
# =================================================================================================
def _wrap_pen_lines(S: int, strokes, ss: int = 2) -> np.ndarray:
    """Draw polylines [(pts, width, value 0..1)] with wrap-around (seamless) and return a float mask."""
    pen = Pen(S, S, ss)
    for pts, wdt, val in strokes:
        for ox in (-S, 0, S):
            for oy in (-S, 0, S):
                q = [(x + ox, y + oy) for x, y in pts]
                xs = [p[0] for p in q]
                ys = [p[1] for p in q]
                if max(xs) < -10 or min(xs) > S + 10 or max(ys) < -10 or min(ys) > S + 10:
                    continue
                pen.line(q, wdt, int(255 * val), caps=True)
    return pen.arr()


def normal_from_height(hgt: np.ndarray, strength: float) -> np.ndarray:
    """OpenGL (Y+) tangent-space normal from a periodic height map (same convention as fetch_textures.py)."""
    dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * 0.5 * strength
    dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * 0.5 * strength
    v = np.stack([-dx, dy, np.ones_like(hgt)], axis=-1)
    v /= np.linalg.norm(v, axis=-1, keepdims=True)
    return (v * 0.5 + 0.5).astype(np.float32)


def linoleum():
    S, T = 1024, 512
    r = np.random.default_rng(1300)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    green = ((xx < T) == (yy < T))
    alb = np.zeros((S, S, 3), np.float32)
    rough = np.zeros((S, S), np.float32)
    # per-tile marbled chip pattern (each tile is a separate piece, so tile textures need not wrap)
    for ty in range(2):
        for tx in range(2):
            g = (tx == ty)
            seed = 1310 + 10 * (2 * ty + tx)
            horiz = g                       # tiles laid with the grain alternating (quarter-turned)
            st = (5.0, 1.0) if horiz else (1.0, 5.0)
            m1 = fbm(T, T, 60, seed, 4, st)
            m2 = fbm(T, T, 14, seed + 3, 3, st)
            chips = pnoise(T, T, 2.2, seed + 5, (2.5, 1.0) if horiz else (1.0, 2.5))
            if g:
                base, light, dark, speck = hexf("#33493C"), hexf("#435E4D"), hexf("#26382D"), hexf("#A9AE96")
                lot = 1.0 + (0.04 if (tx, ty) == (1, 1) else 0.0)     # dye-lot difference between tiles
            else:
                base, light, dark, speck = hexf("#D0C6A6"), hexf("#DCD3B7"), hexf("#BFB28F"), hexf("#7E8A70")
                lot = 1.0 - (0.025 if (tx, ty) == (0, 1) else 0.0)
            t = np.clip((m1 - 0.5) * 1.6 + (m2 - 0.5) * 1.1, -1, 1)
            col = base[None, None] + np.clip(t, 0, 1)[..., None] * (light - base) + np.clip(-t, 0, 1)[..., None] * (dark - base)
            sp = smooth(0.84, 0.90, chips)
            col = col * (1 - 0.32 * sp[..., None]) + speck * 0.32 * sp[..., None]
            col = col * lot
            alb[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T] = col
            rough[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T] = 0.34 if g else 0.40
    # seams (tile joints) centred on the tile borders, incl. the image edges (wraps)
    def seam_dist(c):
        return np.minimum(np.mod(c, T), T - np.mod(c, T))
    sd = np.minimum(seam_dist(xx + 0.5), seam_dist(yy + 0.5))
    seam = np.exp(-(sd / 1.3) ** 2)
    seam_dirt = np.exp(-(sd / 7.0) ** 2) * (0.6 + 0.4 * pnoise(S, S, 40, 1320))
    # global wear (periodic over the repeat)
    grime = fbm(S, S, 260, 1330, 4)
    traffic = smooth(0.45, 0.85, fbm(S, S, 380, 1331, 3))
    wax_haze = smooth(0.5, 0.9, fbm(S, S, 140, 1332, 3))
    # scuffs (black heel marks) and scratches, drawn with wrap-around
    scuffs = []
    for _ in range(14):                        # clusters of heel marks
        cx0, cy0 = r.uniform(0, S), r.uniform(0, S)
        base_ang = r.uniform(0, math.tau)
        for _ in range(int(r.integers(2, 7))):
            x, y = cx0 + r.normal(0, 40), cy0 + r.normal(0, 40)
            ang = base_ang + r.normal(0, 0.5)
            ln = r.uniform(6, 34)
            bend = r.normal(0, 0.03)
            pts = []
            for i in range(8):
                a = ang + bend * i
                pts.append((x + math.cos(a) * ln * i / 7, y + math.sin(a) * ln * i / 7))
            scuffs.append((pts, r.uniform(2.5, 7.0), r.uniform(0.25, 0.65)))
    scuff = blur(_wrap_pen_lines(S, scuffs), 1.6, wrap=True) * (0.6 + 0.6 * pnoise(S, S, 5, 1335))
    scr = []
    for _ in range(170):
        x, y = r.uniform(0, S), r.uniform(0, S)
        ang = r.normal(0.35, 0.5) if r.random() < 0.7 else r.uniform(0, math.tau)
        ln = r.uniform(25, 180)
        scr.append(([(x, y), (x + math.cos(ang) * ln, y + math.sin(ang) * ln)], r.uniform(0.6, 1.3), r.uniform(0.3, 0.9)))
    scratch = _wrap_pen_lines(S, scr)
    # chipped tile corners / edges (dark adhesive showing)
    chip_pen = Pen(S, S, 2)
    for cx, cy in ((T, T), (0, T), (T, 0), (0, 0)):
        for _ in range(int(r.integers(0, 3))):
            px, py = cx + r.normal(0, 30), cy + r.normal(0, 30)
            pts = []
            for k in range(9):
                a = 2 * math.pi * k / 9
                rad = r.uniform(3, 9)
                pts.append((px + rad * math.cos(a), py + rad * math.sin(a)))
            for ox in (-S, 0, S):
                for oy in (-S, 0, S):
                    chip_pen.poly([(x + ox, y + oy) for x, y in pts])
    chips = blur(chip_pen.arr() * smooth(16, 6, sd), 0.5, wrap=True)
    # compose albedo
    g3 = green[..., None]
    alb = alb * (1 - 0.16 * (grime[..., None] - 0.35) * (1.4 - 0.8 * g3))
    worn = traffic[..., None]
    grey = alb.mean(-1, keepdims=True)
    alb = alb * (1 - 0.25 * worn) + (grey * 0.9 + 18) * 0.25 * worn                 # dulled, faded walkway
    alb = alb * (1 - (0.10 * wax_haze)[..., None]) + np.array([150, 130, 80], np.float32) * (0.10 * wax_haze)[..., None] * (1 - g3 * 0.6)
    alb = alb * (1 - 0.30 * seam_dirt[..., None])
    alb = alb * (1 - 0.85 * seam[..., None]) + np.array([24, 22, 18], np.float32) * 0.85 * seam[..., None]
    alb = alb * (1 - 0.65 * scuff[..., None]) + np.array([30, 28, 26], np.float32) * 0.65 * scuff[..., None]
    sc_col = np.where(g3, np.array([110, 130, 112], np.float32), np.array([168, 156, 128], np.float32))
    alb = alb * (1 - 0.30 * scratch[..., None]) + sc_col * 0.30 * scratch[..., None]
    alb = alb * (1 - chips[..., None]) + np.array([34, 30, 24], np.float32) * chips[..., None]
    alb = alb * (0.985 + 0.03 * pnoise(S, S, 2.0, 1340))[..., None]
    # roughness: waxed, duller in the walkway, scuffs / scratches / seams rough
    rough = rough + 0.18 * traffic + 0.06 * (grime - 0.5) + 0.12 * scuff + 0.20 * scratch + 0.45 * seam + 0.3 * chips
    rough = rough - 0.06 * wax_haze
    rough = np.clip(rough + 0.03 * (pnoise(S, S, 6, 1341) - 0.5), 0.2, 0.95)
    # height -> normal
    hgt = -1.0 * seam - 0.25 * np.exp(-(sd / 4.0) ** 2) + 0.12 * smooth(30, 3, sd) * 0     # joint groove
    cup = 0.35 * np.exp(-(sd / 60.0) ** 2)                                              # slight edge curl
    hgt = hgt + cup - 0.12 * scratch + 0.05 * scuff - 0.7 * chips
    hgt = hgt + 0.04 * (pnoise(S, S, 3, 1342) - 0.5) + 0.25 * (fbm(S, S, 200, 1343, 3) - 0.5)
    normal = normal_from_height(hgt, 2.2)
    ao = np.clip(1 - 0.40 * seam - 0.10 * seam_dirt - 0.35 * chips, 0, 1)
    orm = np.stack([ao, rough, np.zeros_like(ao)], -1)
    folder = os.path.join(TEX, "linoleum")
    os.makedirs(folder, exist_ok=True)
    save(to_img(alb), "albedo.jpg", folder)
    save(to_img(normal * 255.0), "normal.png", folder)
    save(to_img(orm * 255.0), "orm.jpg", folder)


# =================================================================================================
# Film frames, secret reel, vault reel (1200 x 800, black-and-white 1979 prints)
# =================================================================================================
FW, FH = 1200, 800


def _limb(d: ImageDraw.ImageDraw, pts, widths):
    """Tapered limb through points with per-point widths (in canvas px), round joints."""
    for (x0, y0), (x1, y1), w0, w1 in zip(pts[:-1], pts[1:], widths[:-1], widths[1:]):
        dx, dy = x1 - x0, y1 - y0
        L = max(1e-6, math.hypot(dx, dy))
        nx, ny = -dy / L, dx / L
        d.polygon([(x0 + nx * w0 / 2, y0 + ny * w0 / 2), (x1 + nx * w1 / 2, y1 + ny * w1 / 2),
                   (x1 - nx * w1 / 2, y1 - ny * w1 / 2), (x0 - nx * w0 / 2, y0 - ny * w0 / 2)], fill=255)
    for (x, y), w in zip(pts, widths):
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=255)


def person_mask(h: float, sex: str = "m", outfit: str = "coat", hair: str = "short", arms: str = "down",
                reach=None, arm_angles=(20.0, 25.0), width: float = 1.0, ss: int = 3):
    """Organic human silhouette (front or back view, ~7.4 heads tall) as an 'L' image at ss x scale.
    Returns (image, feet_x, feet_y) in canvas pixels. reach = target (dx, dy) in px relative to the feet."""
    u = h / 7.4 * ss
    X0, X1, Y0, Y1 = -4.4, 4.4, -2.2, 7.8
    Wc, Hc = int((X1 - X0) * u) + 2, int((Y1 - Y0) * u) + 2
    im = Image.new("L", (Wc, Hc), 0)
    d = ImageDraw.Draw(im)

    def P(X, Y):
        return ((X - X0) * u, (Y - Y0) * u)

    def poly(pts):
        d.polygon([P(a, b) for a, b in _smooth_poly(pts, 6)], fill=255)

    f = sex == "f"
    S = (0.84 if f else 0.98) * width * (1.07 if outfit == "longcoat" else 1.0)
    # head (egg) and neck
    pts = []
    hs = 0.92
    for t in np.linspace(0, 2 * math.pi, 48, endpoint=False):
        sx = math.sin(t) * (0.37 if f else 0.39) * hs * (1 - 0.22 * max(0.0, -math.cos(t)) ** 1.5)
        pts.append(P(sx, 0.08 + 0.48 * hs - 0.52 * hs * math.cos(t)))
    d.polygon(pts, fill=255)
    poly([(-0.15, 0.85), (0.15, 0.85), (0.19, 1.22), (-0.19, 1.22)])
    # torso
    wa, hp = (0.66, 0.90) if f else (0.80, 0.84)
    poly([(-0.20, 1.02), (-0.55, 1.10), (-0.86 * S / 0.98, 1.20), (-S, 1.46), (-S * 0.96, 1.95), (-S * wa, 2.95),
          (-S * hp, 3.6), (-S * hp, 4.0), (S * hp, 4.0), (S * hp, 3.6), (S * wa, 2.95), (S * 0.96, 1.95), (S, 1.46),
          (0.86 * S / 0.98, 1.20), (0.55, 1.10), (0.20, 1.02)])
    # legs
    for sg in (-1, 1):
        if f:
            leg = [(sg * 0.30, 3.75), (sg * 0.24, 5.35), (sg * 0.23, 6.25), (sg * 0.21, 7.12)]
            lwid = [0.50, 0.34, 0.31, 0.17]
        elif outfit == "suit":
            leg = [(sg * 0.36, 3.8), (sg * 0.33, 5.3), (sg * 0.32, 7.12)]
            lwid = [0.52, 0.42, 0.36]
        else:
            leg = [(sg * 0.36, 3.8), (sg * 0.31, 5.3), (sg * 0.30, 6.3), (sg * 0.29, 7.12)]
            lwid = [0.52, 0.38, 0.34, 0.22]
        _limb(d, [P(*q) for q in leg], [w * u for w in lwid])
        sx_, sy_ = P(sg * (0.33 if not f else 0.24), 7.26)
        rx, ry = (0.25 if not f else 0.17) * u, 0.11 * u
        d.ellipse([sx_ - rx + sg * 0.05 * u, sy_ - ry, sx_ + rx + sg * 0.05 * u, sy_ + ry], fill=255)
    # clothes
    if outfit == "coat":
        wst = 0.80 if f else 0.95
        poly([(-S * 0.99, 1.44), (-S * 0.95, 2.2), (-S * wst, 2.95), (-S * 0.98, 4.0), (-S * 1.04, 5.12), (-0.05, 5.12),
              (0.0, 4.75), (0.05, 5.12), (S * 1.04, 5.12), (S * 0.98, 4.0), (S * wst, 2.95), (S * 0.95, 2.2),
              (S * 0.99, 1.44), (0.0, 1.2)])
    elif outfit == "longcoat":
        poly([(-S * 1.0, 1.42), (-S * 0.97, 2.6), (-S * 1.0, 4.2), (-S * 1.10, 6.05), (-0.04, 6.05), (0.0, 5.6),
              (0.04, 6.05), (S * 1.10, 6.05), (S * 1.0, 4.2), (S * 0.97, 2.6), (S * 1.0, 1.42), (0.0, 1.15)])
        poly([(-0.22, 0.98), (-0.66, 1.08), (-0.58, 1.70), (-0.14, 1.32)])
        poly([(0.22, 0.98), (0.66, 1.08), (0.58, 1.70), (0.14, 1.32)])
    elif outfit == "suit":
        poly([(-S * 1.0, 1.44), (-S * 0.94, 2.5), (-S * 0.88, 3.4), (-S * 0.90, 4.0), (S * 0.90, 4.0), (S * 0.88, 3.4),
              (S * 0.94, 2.5), (S * 1.0, 1.44), (0.0, 1.2)])
    elif outfit == "skirt":
        poly([(-S * 0.64, 2.95), (-S * 0.90, 4.0), (-S * 0.94, 5.35), (S * 0.94, 5.35), (S * 0.90, 4.0), (S * 0.64, 2.95)])
    # arms
    sleeve = 1.12 if outfit in ("coat", "longcoat") else 1.0
    upper, fore = 1.42, 1.30
    for sg in (-1, 1):
        mode = arms
        if arms == "reach":
            mode = "reach" if sg == -1 else "down"
        elif arms == "reach_r":
            mode = "reach" if sg == 1 else "down"
        elif arms == "up_r":
            mode = "up" if sg == 1 else "down"
        elif arms == "up_l":
            mode = "up" if sg == -1 else "down"
        sh = (sg * (S - 0.17), 1.47)
        if mode == "down":
            el = (sg * (S + 0.04), 2.72)
            wr = (sg * (S - 0.04), 3.92)
            hand = (sg * (S - 0.06), 4.16)
        elif mode == "pockets":
            el = (sg * (S + 0.06), 2.70)
            wr = (sg * (S - 0.22), 3.62)
            hand = None
        elif mode == "up":
            a1 = math.radians(arm_angles[0] if sg == -1 else arm_angles[1])
            a2 = a1 - math.radians(14)
            el = (sh[0] + sg * upper * math.sin(a1), sh[1] - upper * math.cos(a1))
            wr = (el[0] + sg * fore * math.sin(a2), el[1] - fore * math.cos(a2))
            hand = (wr[0] + sg * 0.20 * math.sin(a2), wr[1] - 0.20 * math.cos(a2))
        else:   # reach toward the target (relative to the feet, in px at 1x)
            tx, ty = reach[0] / (h / 7.4), 7.4 + reach[1] / (h / 7.4)
            dx, dy = tx - sh[0], ty - sh[1]
            dist = max(1e-3, math.hypot(dx, dy))
            d2 = min(dist, upper + fore + 0.1 - 1e-3)
            a = math.acos(float(np.clip((upper ** 2 + d2 ** 2 - (fore + 0.1) ** 2) / (2 * upper * d2), -1, 1)))
            base = math.atan2(dy, dx)
            ang = base - a if dx < 0 else base + a          # elbow below the shoulder-hand line
            el = (sh[0] + upper * math.cos(ang), sh[1] + upper * math.sin(ang))
            hand = (sh[0] + d2 * dx / dist, sh[1] + d2 * dy / dist)
            wr = (hand[0] - 0.16 * dx / dist, hand[1] - 0.16 * dy / dist)
            fx, fy = hand[0] + 0.24 * dx / dist, hand[1] + 0.24 * dy / dist
            _limb(d, [P(*hand), P(fx, fy)], [0.10 * u, 0.06 * u])
        _limb(d, [P(*sh), P(*el), P(*wr)], [0.42 * sleeve * u, 0.34 * sleeve * u, 0.27 * sleeve * u])
        if hand is not None:
            hx, hy = P(*hand)
            d.ellipse([hx - 0.14 * u, hy - 0.17 * u, hx + 0.14 * u, hy + 0.17 * u], fill=255)
    # hair
    if hair == "short":
        poly([(-0.42, 0.62), (-0.44, 0.30), (-0.30, 0.02), (0.0, -0.06), (0.30, 0.02), (0.44, 0.30), (0.42, 0.62),
              (0.36, 0.40), (-0.36, 0.40)])
    elif hair == "bob":
        poly([(-0.36, 0.96), (-0.47, 0.84), (-0.50, 0.52), (-0.47, 0.20), (-0.34, -0.01), (0.0, -0.07), (0.34, -0.01),
              (0.47, 0.20), (0.50, 0.52), (0.47, 0.84), (0.36, 0.96), (0.28, 0.80), (0.28, 0.46), (-0.28, 0.46),
              (-0.28, 0.80)])
    elif hair == "bun":
        poly([(-0.41, 0.55), (-0.43, 0.25), (-0.30, 0.0), (0.0, -0.06), (0.30, 0.0), (0.43, 0.25), (0.41, 0.55),
              (0.0, 0.35)])
        cx_, cy_ = P(0.0, -0.08)
        d.ellipse([cx_ - 0.22 * u, cy_ - 0.20 * u, cx_ + 0.22 * u, cy_ + 0.20 * u], fill=255)
    elif hair == "long":
        poly([(-0.46, 0.30), (-0.36, -0.02), (0.0, -0.09), (0.36, -0.02), (0.46, 0.30), (0.56, 1.10), (0.54, 1.70),
              (0.30, 1.66), (0.28, 1.0), (-0.28, 1.0), (-0.30, 1.66), (-0.54, 1.70), (-0.56, 1.10)])
    # organic merge: blur + threshold, then a whisper of softness for the downsample
    from PIL import ImageFilter
    r = max(1.0, 0.035 * u)
    im = im.filter(ImageFilter.GaussianBlur(r)).point(lambda v: 255 if v >= 128 else 0)
    im = im.filter(ImageFilter.GaussianBlur(max(0.6, ss * 0.35)))
    fx_, fy_ = P(0, 7.4)
    return im, fx_, fy_


def figure_row(lum: np.ndarray, figs: list, rim: float = 0.5, rim_w: float = 2.0, light=None, ss: int = 3,
               rim_dir=None):
    """Composite one row of figures (dicts: x, feet, h + person_mask kwargs + 'lb' luminance) onto lum.
    Rim light on the silhouette edges: all round (back light, favouring upward edges) or toward rim_dir."""
    H, W = lum.shape
    cov = Image.new("L", (W * ss, H * ss), 0)
    val = Image.new("L", (W * ss, H * ss), 0)
    for fg in figs:
        kw = {k: v for k, v in fg.items() if k not in ("lb", "lh", "x", "feet", "h")}
        if "reach" in kw and kw["reach"] is not None:
            kw["reach"] = (kw["reach"][0] - fg["x"], kw["reach"][1] - fg["feet"])
        im, fx, fy = person_mask(fg["h"], ss=ss, **kw)
        ox, oy = int(round(fg["x"] * ss - fx)), int(round(fg["feet"] * ss - fy))
        base = cov.crop((ox, oy, ox + im.width, oy + im.height))
        cov.paste(ImageChops.lighter(base, im), (ox, oy))
        val.paste(Image.new("L", im.size, int(255 * fg["lb"])), (ox, oy), im)
    c = np.asarray(cov.resize((W, H), Image.BOX), np.float32) / 255.0
    v = np.asarray(val.resize((W, H), Image.BOX), np.float32) / 255.0 / np.maximum(c, 1e-3)
    if light is not None:
        v = v * light
    b = blur(c, rim_w)
    edge = np.clip(c - b, 0, 1) * 2.0
    gx = np.roll(b, -1, 1) - np.roll(b, 1, 1)
    gy = np.roll(b, -1, 0) - np.roll(b, 1, 0)
    if rim_dir is None:
        wgt = 0.10 + 0.9 * np.clip(gy * 10, 0, 1)
    else:
        gl = np.hypot(gx, gy) + 1e-6
        # outward normal = -grad; light from rim_dir (unit vector pointing from the figure toward the light)
        wgt = np.clip((-gx * rim_dir[0] - gy * rim_dir[1]) / gl, 0, 1) ** 1.5
    fig = v + rim * edge * wgt
    return lum * (1 - c) + fig * c, c


def zoom_rays(src: np.ndarray, cx: float, cy: float, length: float = 0.4, steps: int = 32) -> np.ndarray:
    """Radial (god-ray) blur of an emission image toward the light centre (cx, cy)."""
    im = Image.fromarray(src.astype(np.float32), "F")
    acc = np.zeros_like(src, dtype=np.float32)
    wsum = 0.0
    for i in range(steps):
        sc = 1.0 - length * i / steps
        t = im.transform(im.size, Image.AFFINE, (sc, 0, cx * (1 - sc), 0, sc, cy * (1 - sc)), resample=Image.BILINEAR)
        wgt = 1.0 - i / steps
        acc += np.asarray(t, np.float32) * wgt
        wsum += wgt
    return acc / wsum


def ring_machine(W: int, H: int, cx: float, cy: float, R: float, tilt: float = 0.12, seed: int = 0,
                 power: float = 1.0, unstable: float = 0.0):
    """The Array: a vast ring of light. Returns (emission, structure mask, structure luminance)."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ry = R * (1 - tilt)
    q = np.sqrt(((xx - cx) / R) ** 2 + ((yy - cy) / ry) ** 2)
    ang = np.arctan2((yy - cy) / ry, (xx - cx) / R)
    e = 1.2 / R
    t_in = 0.82
    band = smooth(1.0 + e, 1.0 - e, q) * smooth(t_in - e, t_in + e, q)
    # torus shading: lit from inside (the inner edge glows), ribs every 15 deg, coils
    tq = np.clip((q - t_in) / (1 - t_in), 0, 1)
    ribs = np.abs(np.mod(np.degrees(ang) + 7.5, 15.0) - 7.5) < 0.9
    coils = (np.abs(np.sin(np.degrees(ang) * 2.0 * math.pi / 3.0)) > 0.55).astype(np.float32)
    s_lum = 0.06 + 0.30 * (1 - tq) ** 3 + 0.05 * coils * (1 - tq) - 0.04 * ribs + 0.08 * np.clip(-np.sin(ang), 0, 1) * tq
    s_lum = s_lum * (0.9 + 0.2 * noise(H, W, 30, 2, seed))
    # membrane of light inside the ring
    n1 = noise(H, W, 90, 3, seed + 1)
    swirl = np.sin(ang * 3 + q * 9 + n1 * 4) * 0.5 + 0.5
    inside = smooth(t_in + e, t_in - 3 * e, q)
    emit = inside * (0.16 + 0.42 * np.exp(-(q / 0.38) ** 2) + 0.16 * swirl * (0.5 + unstable)
                     + 0.25 * smooth(0.45, t_in, q))
    ripple = 0.5 + 0.5 * np.sin(q * 52.0 - n1 * 5.0)
    emit = emit + inside * 0.07 * ripple * smooth(0.05, 0.3, q)                  # standing light waves
    emit = emit + 1.1 * np.exp(-((q - t_in) / 0.016) ** 2)                      # inner rim
    emit = emit + 1.8 * np.exp(-(q / 0.08) ** 2)                                 # core
    lamps = np.zeros((H, W), np.float32)
    for k in range(24):
        a = math.radians(k * 15 + 7.5)
        lx, ly = cx + R * 0.91 * math.cos(a), cy + ry * 0.91 * math.sin(a)
        lamps += np.exp(-(((xx - lx) ** 2 + (yy - ly) ** 2) / (0.010 * R) ** 2))
    if unstable:
        emit = emit * (1 + unstable * (noise(H, W, 40, 2, seed + 7) - 0.5))
    ring_machine.inside = inside
    ring_machine.lamps = lamps * power
    return emit * power, band, s_lum


def hall_columns(W: int, H: int, vpx: float, vpy: float, depths, f: float = 200.0, X: float = 5.6,
                 cam_h: float = 1.6, ceil: float = 9.0, width: float = 0.9):
    """Column masks of a one-point-perspective hall: list of (mask, depth)."""
    out = []
    for z in depths:
        for sg in (-1, 1):
            sx = vpx + sg * f * X / z
            wpx = f * width / z
            y0 = vpy - f * (ceil - cam_h) / z
            y1 = vpy + f * cam_h / z
            pen = Pen(W, H, 2)
            pen.rect(sx - wpx / 2, y0, sx + wpx / 2, y1)
            pen.rect(sx - wpx * 0.7, y1 - f * 0.5 / z, sx + wpx * 0.7, y1)          # plinth
            pen.rect(sx - wpx * 0.65, y0 + f * 0.6 / z, sx + wpx * 0.65, y0 + f * 1.0 / z)  # capital
            out.append((pen.arr(), z, sx, wpx))
    return out


def scratched_text(W, H, x, y, txt, size, angle=0.0):
    p = Pen(W, H, 4)
    rot_text(p, x, y, txt, F_HAND, size, angle=angle, weight=420)
    return p.arr()


def hall_floor(lum, vpx, vpy, f=200.0, cam_h=1.6, base=0.05, line=0.04, tile=2.0):
    H, W = lum.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    floor = yy > vpy + 1
    zf = np.where(floor, f * cam_h / np.maximum(yy - vpy, 1), 1e3)
    xw = (xx - vpx) * zf / f
    aa = np.clip(zf / 40.0, 0.002, 0.5)
    tiles = smooth(1 - aa * 2.5, 1.0, np.abs(np.mod(xw, tile) - tile / 2) * 2 / tile) + \
        smooth(1 - aa * 2.5, 1.0, np.abs(np.mod(zf, tile) - tile / 2) * 2 / tile)
    fade = np.clip(1.2 - zf / 30.0, 0, 1)
    return np.where(floor, base + line * np.clip(tiles, 0, 1) * fade, lum), floor


def film_frame_0():
    """The Array Hall: a vast hall with the ring machine of light, tiny figures for scale."""
    W, H = FW, FH
    vpx, vpy = 600, 410
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy, R = 600, 300, 255
    lum = np.full((H, W), 0.03, np.float32)
    lum, floor = hall_floor(lum, vpx, vpy)
    glow = np.exp(-np.hypot(xx - cx, (yy - cy) * 1.2) / 380.0)
    lum = lum + 0.10 * glow
    # ceiling beams converging to the vanishing point, and rows of hanging lamps
    cb = Pen(W, H, 2)
    for xb in np.linspace(-14, 14, 9):
        cb.line([(vpx + xb * 200 / 1.0, vpy - 200 * 7.4 / 1.0), (vpx + xb * 200 / 60, vpy - 200 * 7.4 / 60)], 3)
    for z in (1.4, 2.0, 2.8, 3.9, 5.4, 7.5):
        cb.rect(0, vpy - 200 * 7.4 / z - 300 / z, W, vpy - 200 * 7.4 / z)
    lum = lum * (1 - cb.arr() * (yy < vpy)) + cb.arr() * (yy < vpy) * 0.015
    lamps = np.zeros((H, W), np.float32)
    for z in (1.6, 2.2, 3.0, 4.1, 5.6, 7.7, 10.5):
        for xl in (-3.2, 3.2):
            lx, ly = vpx + 200 * xl / z, vpy - 200 * 5.2 / z
            lamps += np.exp(-((xx - lx) ** 2 + (yy - ly) ** 2) / (2 + 14 / z) ** 2)
    # gantry: dais with steps under the ring, pylons and a catwalk
    st = Pen(W, H, 4)
    st.poly([(cx - 280, 520), (cx + 280, 520), (cx + 330, 548), (cx - 330, 548)])
    for i in range(6):
        y0 = 548 + i * 7
        st.rect(cx - 330 - i * 14, y0, cx + 330 + i * 14, y0 + 4.5)
    for sg in (-1, 1):
        st.poly([(cx + sg * 170, 522), (cx + sg * 228, 372), (cx + sg * 246, 372), (cx + sg * 204, 522)])
        st.poly([(cx + sg * 286, 522), (cx + sg * 244, 400), (cx + sg * 256, 398), (cx + sg * 308, 522)])
    st.rect(cx - 400, 476, cx + 400, 480)
    for xr in range(cx - 400, cx + 401, 25):
        st.rect(xr, 476, xr + 2, 506)
    st.rect(cx - 400, 504, cx + 400, 507)
    sm = st.arr()
    gantry_l = 0.03 + 0.12 * np.exp(-np.abs(xx - cx) / 260) * (yy < 530) + \
        (yy > 547) * 0.10 * np.exp(-np.abs(xx - cx) / 300)
    cols = hall_columns(W, H, vpx, vpy, [1.15, 1.55, 2.1, 2.85, 3.85, 5.2, 7.0], f=200, X=6.2, ceil=8.6)
    z_ring = 2.9
    occl = sm.copy()

    def draw_cols(lum, occl, far):
        for m, z, sx, wpx in sorted(cols, key=lambda t: -t[1]):
            if (z > z_ring) != far:
                continue
            edge_x = sx - np.sign(sx - cx) * wpx / 2
            lit = np.clip(1 - np.abs(xx - edge_x) / (wpx * 0.45), 0, 1) ** 1.5
            cl = 0.02 + 0.03 / z + 0.30 * np.exp(-np.abs(sx - cx) / 420) * lit * (1 - 0.5 * smooth(vpy - 40, vpy - 400, yy))
            lum = lum * (1 - m) + m * cl
            occl = np.maximum(occl, m)
        return lum, occl
    lum, occl = draw_cols(lum, occl, True)
    emit, band, s_lum = ring_machine(W, H, cx, cy, R, tilt=0.10, seed=1500)
    inside = ring_machine.inside
    lum = lum * (1 - 0.85 * inside)
    lum = lum * (1 - band) + band * s_lum
    lum = lum + (emit + ring_machine.lamps) * (1 - band)
    occl = np.maximum(occl, band)
    lum = lum * (1 - sm) + sm * gantry_l
    lum, occl = draw_cols(lum, occl, False)
    lum = lum + 0.9 * lamps * (1 - np.maximum(occl, inside))
    # tiny figures at the foot of the dais (scale)
    figs = []
    for x0, hh, sx_, hr in ((474, 60, "m", "short"), (506, 56, "f", "bun"), (686, 62, "m", "short"),
                            (722, 58, "m", "short"), (748, 55, "f", "bob")):
        figs.append(dict(x=x0, feet=572, h=hh, sex=sx_, outfit="coat", hair=hr, lb=0.025, lh=0.03))
    lum, fc = figure_row(lum, figs, rim=0.18, rim_w=0.8)
    occl = np.maximum(occl, fc)
    # polished floor: reflection streak of the ring, figures' shadows toward the camera
    yr = np.clip(yy - 548, 0, None)
    streak = np.exp(-((xx - cx) / 120.0) ** 2) * np.exp(-yr / 240.0) * (yy > 548)
    lum = lum + 0.28 * streak * (0.75 + 0.25 * noise(H, W, 6, 2, 1501))
    src = (emit * (1 - occl)) * smooth(0.2, 1.2, emit)
    rays = zoom_rays(src, cx, cy, length=0.6, steps=40)
    lum = lum + 0.40 * rays
    lum = lum + 0.05 * np.exp(-np.hypot(xx - cx, yy - cy) / 450.0)
    rgb = film_finish(lum * 0.92, 1510, grain_amt=0.035, scratches=6, dust=60, vignette=0.55, halation=0.25,
                      contrast=1.22, flicker=0.05)
    save(to_img(rgb), "film_frame_0.jpg")


def _rand_staff(rng, n, x0, dx, feet, h, jitter=6.0):
    figs = []
    for i in range(n):
        f = rng.random() < 0.34
        outfit = "coat" if rng.random() < 0.62 else ("skirt" if f else "suit")
        hair = rng.choice(["bob", "bun", "long"], p=[0.45, 0.4, 0.15]) if f else "short"
        figs.append(dict(x=x0 + i * dx + rng.normal(0, jitter), feet=feet + rng.normal(0, 2),
                         h=h * rng.uniform(0.93, 1.05) * (0.95 if f else 1.0), sex="f" if f else "m", outfit=outfit,
                         hair=hair, width=rng.uniform(0.94, 1.08), lb=rng.uniform(0.012, 0.03), lh=0.05))
    return figs


def staff_photo_lum(extra: bool, seed: int = 1700):
    """The 1979 staff photograph in the Array Hall: 41 silhouettes in rows before the ring of light.
    With extra=True a 42nd figure stands alone at the far right edge (Leyla, 1998, long coat)."""
    W, H = FW, FH
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = 600, 290
    lum = np.full((H, W), 0.03, np.float32)
    lum, floor = hall_floor(lum, 600, 470, base=0.05, line=0.03)
    emit, band, s_lum = ring_machine(W, H, cx, cy, 470, tilt=0.08, seed=seed + 1)
    inside = ring_machine.inside
    lum = lum * (1 - 0.85 * inside)
    lum = lum * (1 - band) + band * s_lum
    lum = lum + (emit + ring_machine.lamps) * (1 - band) * 0.9
    lum = lum + 0.08 * np.exp(-np.hypot(xx - cx, yy - cy) / 500.0)
    # the dais edge they stand on
    da = Pen(W, H, 4)
    da.rect(0, 540, W, 556)
    dm = da.arr()
    lum = lum * (1 - dm) + dm * (0.10 + 0.10 * np.exp(-np.abs(xx - cx) / 300))
    occl = band.copy()
    mid = 578          # the group stands a little left of centre; the right edge stays open
    rows = [_rand_staff(rng, 14, mid - 6.5 * 66, 66, 552, 232),
            _rand_staff(rng, 14, mid - 6.5 * 71 + 8, 71, 604, 260),
            _rand_staff(rng, 13, mid - 6.0 * 81, 81, 672, 294)]
    assert sum(len(r) for r in rows) == STAFF_COUNT
    for i, row in enumerate(rows):
        lum, c = figure_row(lum, row, rim=0.55 - 0.08 * i, rim_w=1.6 + 0.3 * i)
        occl = np.maximum(occl, c)
    # shadows of the front row thrown toward the camera on the polished floor
    sh = Pen(W, H, 2)
    for fg in rows[2]:
        x, ft = fg["x"], fg["feet"]
        sh.poly([(x - 18, ft), (x + 18, ft), (x + 30 + (x - 600) * 0.12, H), (x - 30 + (x - 600) * 0.12, H)])
    shm = blur(sh.arr(), 4) * (yy > 672)
    lum = lum * (1 - 0.6 * shm)
    if extra:
        leyla = [dict(x=1146, feet=702, h=314, sex="f", outfit="longcoat", hair="long", arms="pockets",
                      lb=0.05, lh=0.06)]
        _, hm = figure_row(np.zeros_like(lum), leyla, rim=0.0)
        lum = lum + 0.22 * np.clip(blur(hm, 14) - hm, 0, 1)        # she stands in the light
        lum, c = figure_row(lum, leyla, rim=0.75, rim_w=1.8)
        occl = np.maximum(occl, c)
        sh2 = Pen(W, H, 2)
        sh2.poly([(1128, 702), (1164, 702), (1228, H), (1158, H)])
        lum = lum * (1 - 0.55 * blur(sh2.arr(), 4) * (yy > 700))
    src = emit * (1 - occl) * smooth(0.25, 1.0, emit)
    lum = lum + 0.45 * zoom_rays(src, cx, cy, length=0.5, steps=36)
    return lum


def film_frame_2():
    rgb = film_finish(staff_photo_lum(False) * 0.95, 1720, grain_amt=0.035, scratches=5, dust=55, vignette=0.55,
                      halation=0.25, contrast=1.2, flicker=0.04)
    save(to_img(rgb), "film_frame_2.jpg")


def vault_reel():
    rgb = film_finish(staff_photo_lum(True) * 0.95, 1790, grain_amt=0.04, scratches=9, dust=85, vignette=0.6,
                      halation=0.25, contrast=1.2, flicker=0.07, tint=(1.0, 0.97, 0.90), weave=(-1, 2))
    save(to_img(rgb), "vault_reel.jpg")


def film_frame_1():
    """Professor Strand demonstrates light memory: a figure before a glowing crystal disc."""
    W, H = FW, FH
    rng = np.random.default_rng(1600)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    lum = np.full((H, W), 0.03, np.float32)
    dx, dy = 420, 360            # disc centre
    # blackboard with chalk diagrams behind
    bb = Pen(W, H, 4)
    bb.rect(90, 70, 1110, 450, radius=4)
    bm = bb.arr()
    lum = lum * (1 - bm) + bm * 0.055
    fr = Pen(W, H, 4)
    fr.rect(84, 64, 1116, 456, outline=8)
    fr.rect(80, 450, 1120, 466)
    lum = lum * (1 - fr.arr()) + fr.arr() * 0.09
    ch = Pen(W, H, 4)
    ch.text(170, 140, "E = hν", F_CHALK, 50, anchor="lm")
    ch.text(830, 130, "λ → ψ(t)", F_CHALK, 44, anchor="lm")
    ch.text(820, 220, "LUX MEMINIT", F_HAND, 44, anchor="lm", weight=450)
    for k in range(3):
        ch.ring(250, 300, 40 + 26 * k, 2.5)
    ch.line([(140, 300), (380, 300)], 2.5)
    ch.line([(880, 330), (960, 270), (1040, 330), (1080, 300)], 3)
    for a in range(0, 360, 30):
        ra = math.radians(a)
        ch.line([(960 + 30 * math.cos(ra), 390 + 30 * math.sin(ra)), (960 + 52 * math.cos(ra), 390 + 52 * math.sin(ra))], 2)
    chalk = blur(ch.arr(), 0.8) * (0.6 + 0.4 * noise(H, W, 3, 2, 1601))
    lum = lum + 0.14 * chalk * bm
    # floor
    lum = np.where(yy > 690, 0.045 + 0.03 * (yy - 690) / 110, lum)
    # pedestal and the disc in its brass ring
    pd = Pen(W, H, 4)
    pd.rect(dx - 9, dy + 80, dx + 9, 700)
    pd.poly([(dx - 70, 705), (dx + 70, 705), (dx + 30, 690), (dx - 30, 690)])
    pd.rect(dx - 50, dy + 78, dx + 50, dy + 92, radius=4)
    pm = pd.arr()
    lum = lum * (1 - pm) + pm * (0.05 + 0.18 * np.clip(1 - np.abs(xx - dx - 5) / 12, 0, 1))
    d = np.hypot(xx - dx, yy - dy)
    ringm = smooth(86, 84, d) * smooth(66, 68, d)
    core = smooth(67, 64, d)
    lum = lum * (1 - ringm) + ringm * (0.05 + 0.12 * np.clip(1 - np.abs(d - 69) / 3, 0, 1)
                                       + 0.06 * np.clip(-(yy - dy) / 80, 0, 1))
    facets = 0.5 + 0.5 * np.cos(np.arctan2(yy - dy, xx - dx) * 6)
    disc = core * (0.42 + 0.95 * np.exp(-(d / 26) ** 2) + 0.10 * facets * (d / 66) + 0.08 * np.sin(d / 5.0)
                   + 0.08 * noise(H, W, 14, 2, 1602))
    lum = lum * (1 - core) + disc
    # light falling on the board and the room
    spill = np.exp(-d / 260.0)
    lum = lum + 0.16 * spill
    # Strand, reaching toward the disc, lit from the disc side
    sx, sfeet, sh = 770, 770, 610
    light = 1.0 + 3.0 * np.clip((sx - xx) / 140.0, 0, 1) ** 1.5
    fig = [dict(x=sx, feet=sfeet, h=sh, sex="m", outfit="coat", hair="short", arms="reach", reach=(dx + 92, dy + 6),
                width=1.04, lb=0.05, lh=0.06)]
    lum, sc = figure_row(lum, fig, rim=0.9, rim_w=2.6, light=light, rim_dir=(-0.95, -0.3))
    # audience heads in the foreground, out of focus
    aud = [dict(x=x, feet=1420 + rng.normal(0, 30), h=900 * rng.uniform(0.92, 1.05), sex=sx_, outfit="suit",
                hair=hr, lb=0.015, lh=0.02) for x, sx_, hr in ((150, "m", "short"), (420, "f", "bun"),
                                                               (700, "m", "short"), (1010, "f", "bob"))]
    al = np.zeros((H, W), np.float32)
    al, ac = figure_row(al, aud, rim=0.0)
    ac = blur(ac, 7)
    lum = lum * (1 - ac) + ac * 0.015
    src = disc * (1 - np.maximum(sc, ac))
    lum = lum + 0.30 * zoom_rays(src, dx, dy, length=0.6, steps=36)
    rgb = film_finish(lum, 1610, grain_amt=0.035, scratches=6, dust=55, vignette=0.55, halation=0.22, contrast=1.2,
                      flicker=0.05, weave=(1, -1))
    save(to_img(rgb), "film_frame_1.jpg")


def film_frame_3():
    """Leyla draws her sign on the light glass: a woman's silhouette, the sign half-drawn."""
    W, H = FW, FH
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    lum = np.full((H, W), 0.025, np.float32)
    lum = np.where(yy > 700, 0.04, lum)
    # the light glass: a frosted pane in a frame, glowing from within
    gx0, gy0, gx1, gy1 = 350, 70, 1090, 640
    gcx, gcy = (gx0 + gx1) / 2, 330
    gp = Pen(W, H, 4)
    gp.rect(gx0, gy0, gx1, gy1, radius=6)
    gm = gp.arr()
    glow = 0.40 + 0.20 * np.exp(-(((xx - gcx - 40) / 380) ** 2 + ((yy - gcy) / 300) ** 2)) + \
        0.05 * noise(H, W, 60, 3, 1801)
    lum = lum * (1 - gm) + gm * glow
    fr = Pen(W, H, 4)
    fr.rect(gx0 - 14, gy0 - 14, gx1 + 14, gy1 + 14, radius=8, outline=14)
    fr.rect(gx0 + 140, gy1 + 14, gx0 + 158, 712)
    fr.rect(gx1 - 158, gy1 + 14, gx1 - 140, 712)
    fr.rect(gx0 + 90, 705, gx0 + 210, 715)
    fr.rect(gx1 - 210, 705, gx1 - 90, 715)
    for xs_ in np.linspace(gx0 + 20, gx1 - 20, 12):                 # rivets on the frame
        fr.circle(xs_, gy0 - 7, 2.2, 0)
        fr.circle(xs_, gy1 + 7, 2.2, 0)
    fm = fr.arr()
    lum = lum * (1 - fm) + fm * 0.06
    # the half-drawn sign: luminous strokes on the glass
    size, scx, scy, prog = 340, 755, 318, 0.47
    sm = sign_mask(size, progress=prog)
    sg = np.zeros((H, W), np.float32)
    x0, y0 = scx - size // 2, scy - size // 2
    sg[y0:y0 + size, x0:x0 + size] = sm
    tipx, tipy = sign_end_point(prog)
    tx, ty = scx + tipx * size, scy + tipy * size
    tip = np.exp(-((xx - tx) ** 2 + (yy - ty) ** 2) / 14.0 ** 2)
    lum = lum + 1.4 * sg + 0.35 * blur(sg, 6) + 1.2 * tip
    # light spilling onto the floor under the pane
    lum = lum + 0.10 * np.exp(-((xx - gcx) / 320) ** 2) * np.exp(-np.clip(yy - 715, 0, None) / 50) * (yy > 715)
    # Leyla, in front of the glass, reaching across to the end of the stroke
    fig = [dict(x=436, feet=792, h=700, sex="f", outfit="coat", hair="bob", arms="reach_r", reach=(tx - 6, ty + 4),
                lb=0.03, lh=0.035, width=0.96)]
    lum, c = figure_row(lum, fig, rim=0.45, rim_w=2.4)
    src = (sg * 1.4 + tip) * (1 - c)
    lum = lum + 0.30 * zoom_rays(src, tx, ty, length=0.35, steps=28)
    rgb = film_finish(lum, 1810, grain_amt=0.035, scratches=5, dust=50, vignette=0.55, halation=0.3, contrast=1.2,
                      flicker=0.05, weave=(2, 0))
    save(to_img(rgb), "film_frame_3.jpg")


def film_frame_4():
    """The crowd raises their hands toward the light (seen from behind)."""
    W, H = FW, FH
    rng = np.random.default_rng(1900)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = 600, 250
    lum = np.full((H, W), 0.03, np.float32)
    emit, band, s_lum = ring_machine(W, H, cx, cy, 300, tilt=0.12, seed=1901, power=0.7)
    inside = ring_machine.inside
    lum = lum * (1 - 0.85 * inside)
    lum = lum * (1 - band) + band * s_lum
    lum = lum + (emit + ring_machine.lamps) * (1 - band)
    lum = lum + 0.10 * np.exp(-np.hypot(xx - cx, yy - cy) / 380.0)
    occl = band.copy()
    specs = [(22, 520, 140, 0.0), (15, 610, 240, 0.0), (10, 780, 400, 0.0), (6, 1030, 640, 0.0)]
    for n, feet, hgt, _ in specs:
        row = []
        dxs = W / (n - 1)
        for i in range(n):
            mode = rng.choice(["up", "up", "up_r", "up_l", "down"], p=[0.45, 0.2, 0.15, 0.1, 0.1])
            f = rng.random() < 0.35
            row.append(dict(x=-40 + i * (W + 80) / (n - 1) + rng.normal(0, dxs * 0.15), feet=feet + rng.normal(0, 6),
                            h=hgt * rng.uniform(0.92, 1.06), sex="f" if f else "m",
                            outfit="coat" if rng.random() < 0.7 else ("skirt" if f else "suit"),
                            hair=rng.choice(["bob", "bun", "long"]) if f else "short", arms=mode,
                            arm_angles=(rng.uniform(5, 40), rng.uniform(5, 40)), lb=0.02, lh=0.025))
        lum, c = figure_row(lum, row, rim=0.55 - 0.25 * min(1.0, hgt / 640), rim_w=1.2 + hgt / 300)
        occl = np.maximum(occl, c)
    src = (emit + 0.3 * np.exp(-np.hypot(xx - cx, yy - cy) / 200)) * (1 - occl)
    lum = lum + 0.65 * zoom_rays(src, cx, cy, length=0.7, steps=44)
    rgb = film_finish(lum * 0.9, 1910, grain_amt=0.035, scratches=6, dust=55, vignette=0.55, halation=0.35,
                      contrast=1.22, flicker=0.05, weave=(0, 1))
    save(to_img(rgb), "film_frame_4.jpg")


def film_frame_5():
    """Leyla's sign alone, white on dark, centred, 60 % of the frame height, sharp (recordable)."""
    W, H = FW, FH
    size = 600                                  # sign height = 0.80 * size = 480 px = 60 % of 800
    sm = sign_mask(size, ss=4)
    sg = np.zeros((H, W), np.float32)
    x0, y0 = (W - size) // 2, (H - size) // 2
    sg[y0:y0 + size, x0:x0 + size] = sm
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    lum = 0.03 + 0.03 * np.exp(-np.hypot(xx - W / 2, yy - H / 2) / 400.0)
    lum = lum + 1.25 * sg + 0.10 * blur(sg, 10)
    rgb = film_finish(lum, 1950, grain_amt=0.022, scratches=2, dust=14, vignette=0.4, halation=0.08, contrast=1.1,
                      weave=(1, 0), hair=False, dust_big=0.0)
    save(to_img(rgb), "film_frame_5.jpg")


def film_secret():
    """13 November 1979: Strand alone at the ring machine, the hall empty."""
    W, H = FW, FH
    vpx, vpy = 600, 440
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy, R = 600, 310, 300
    lum = np.full((H, W), 0.02, np.float32)
    lum, floor = hall_floor(lum, vpx, vpy, base=0.04, line=0.03)
    cols = hall_columns(W, H, vpx, vpy, [1.3, 1.9, 2.7, 3.8], f=200, X=6.8, ceil=8.6)
    for m, z, sxc, wpx in sorted(cols, key=lambda t: -t[1]):
        edge_x = sxc - np.sign(sxc - cx) * wpx / 2
        lit = np.clip(1 - np.abs(xx - edge_x) / (wpx * 0.45), 0, 1) ** 1.5
        lum = lum * (1 - m) + m * (0.015 + 0.22 * np.exp(-np.abs(sxc - cx) / 420) * lit)
    emit, band, s_lum = ring_machine(W, H, cx, cy, R, tilt=0.10, seed=2001, power=1.1, unstable=0.8)
    inside = ring_machine.inside
    lum = lum * (1 - 0.9 * inside)
    lum = lum * (1 - band) + band * s_lum * 0.8
    lum = lum + (emit + ring_machine.lamps * 0.5) * (1 - band)
    st = Pen(W, H, 4)
    st.poly([(cx - 300, 592), (cx + 300, 592), (cx + 350, 616), (cx - 350, 616)])
    for i in range(5):
        st.rect(cx - 350 - i * 16, 616 + i * 7, cx + 350 + i * 16, 620 + i * 7)
    for sg in (-1, 1):
        st.poly([(cx + sg * 200, 594), (cx + sg * 268, 420), (cx + sg * 288, 420), (cx + sg * 240, 594)])
    sm = st.arr()
    lum = lum * (1 - sm) + sm * (0.02 + 0.10 * np.exp(-np.abs(xx - cx) / 240) * (yy < 600))
    occl = np.maximum(band, sm)
    fig = [dict(x=cx + 8, feet=596, h=96, sex="m", outfit="coat", hair="short", arms="down", lb=0.02, lh=0.025)]
    lum, c = figure_row(lum, fig, rim=0.6, rim_w=0.9)
    occl = np.maximum(occl, c)
    shp = Pen(W, H, 2)
    shp.poly([(cx + 2, 596), (cx + 14, 596), (cx + 40, H), (cx - 22, H)])
    lum = lum * (1 - 0.7 * blur(shp.arr(), 3) * (yy > 596))
    yr = np.clip(yy - 616, 0, None)
    lum = lum + 0.22 * np.exp(-((xx - cx) / 130.0) ** 2) * np.exp(-yr / 200.0) * (yy > 616)
    src = emit * (1 - occl) * smooth(0.2, 1.2, emit)
    lum = lum + 0.45 * zoom_rays(src, cx, cy, length=0.6, steps=40)
    lum = lum + 0.30 * scratched_text(W, H, 150, 742, "13.XI.1979", 34, angle=3)
    rgb = film_finish(lum * 0.9, 2010, grain_amt=0.045, scratches=11, dust=95, vignette=0.65, halation=0.3,
                      contrast=1.22, flicker=0.10, tint=(0.97, 0.98, 1.0), weave=(-2, 1))
    save(to_img(rgb), "film_secret.jpg")


# =================================================================================================
# Archive rules notice (700 x 1000) and archive-box label atlas (1024 x 1024, 4 x 8 strips)
# =================================================================================================
def _wrap(txt: str, path: str, size: float, width: float):
    words, lines, cur = txt.split(), [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if text_width(cand, path, size) <= width or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def archive_rules(lang: str = "en"):
    W, H = 700, 1000
    rgb = paper(W, H, base=(226, 214, 186), seed=1100, stains=2, vignette=0.30, fibres=1.0)
    pr = Pen(W, H, 4)
    pr.rect(34, 34, W - 34, H - 34, outline=3)
    pr.rect(44, 44, W - 44, H - 44, outline=1.2)
    draw_mark(pr, W / 2, 104, 84)
    pr.text(W / 2, 176, t("inst_sp", lang), F_SANS_B, 19, spacing=4, max_w=W - 160)
    pr.text(W / 2, 236, t("archive_b", lang), F_SERIF_B, 64, spacing=3, max_w=W - 160)
    pr.text(W / 2, 290, t("ar_rules", lang), F_SERIF_B, 40, spacing=14, max_w=W - 200)
    pr.rect(120, 322, W - 120, 324.5)
    pr.rect(120, 330, W - 120, 331)
    # the rules: shrink type until the last baseline clears the stamp and signature block (y < 760)
    rules = RULES_TXT[lang]
    for size in np.arange(26, 18.9, -0.5):
        lh, gap = size * 1.31, size * 0.85
        wrapped = [_wrap(r, F_ROMAN, size, W - 240) for r in rules]
        bottom = 392 + sum(lh * len(w) + gap for w in wrapped) - gap - lh
        if bottom < 760:
            break
    y = 392
    for i, lines in enumerate(wrapped, 1):
        pr.text(92, y, f"{i}.", F_ROMAN_B, size + 1, anchor="ls")
        for j, line in enumerate(lines):
            pr.text(132, y + j * lh, line, F_ROMAN, size, anchor="ls")
        y += lh * len(lines) + gap
    pr.text(W - 90, H - 150, t("ar_order", lang), F_ROMAN, 22, anchor="rs", max_w=W - 330)
    pr.text(W - 90, H - 120, t("inst_line", lang), F_ROMAN, 22, anchor="rs", max_w=W - 330)
    rgb = paint(rgb, ink(pr.arr(), 1101, 0.22), "#2A2118", 0.9)
    st = Pen(W, H, 4)
    sx, sy = 170, H - 150
    st.ring(sx, sy, 62, 4)
    st.ring(sx, sy, 46, 2)
    arc_text(st, sx, sy, 49, t("stamp_inst", lang), F_SANS_B, 13, a_mid=-90, spacing=1.05, max_deg=200)
    arc_text(st, sx, sy, 49, "· " + t("archive_b", lang) + " ·", F_SANS_B, 13, a_mid=90, spacing=1.1, inward=True,
             max_deg=130)
    draw_mark(st, sx, sy, 56, ticks=False, ring_w=0.06, line_w=0.06)
    rgb = paint(rgb, st.arr() * stamp_mask(W, H, 1102, 0.4), "#4B3C8C", 0.6)
    sig = Pen(W, H, 4)
    rot_text(sig, W - 200, H - 88, t("ar_sig", lang), F_HAND, 44, angle=3, weight=520)
    rgb = paint(rgb, ink(sig.arr(), 1103, 0.3), "#1E2340", 0.85)
    # water stain creeping up from the bottom edge, foxing
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    tide = H - 120 - 60 * noise(1, W, 120, 3, 1104)[0][None, :]
    stain = smooth(tide - 4, tide + 30, yy) * 0.10 + np.exp(-((yy - tide) / 3.0) ** 2) * 0.22
    rgb = multiply(rgb, stain, "#7A5A30")
    fox = smooth(0.82, 0.92, noise(H, W, 8, 2, 1105)) * 0.3
    rgb = multiply(rgb, fox, "#9A6A3A")
    save(to_img(rgb), lname("archive_rules.jpg", lang))


def box_labels():
    S, CW, CHh = 1024, 256, 128
    rng = np.random.default_rng(1200)
    rgb = np.zeros((S, S, 3), np.float32)
    bases = [(232, 222, 196), (222, 204, 160), (238, 232, 214), (214, 200, 168)]
    stripes = [None, None, "#A8322A", "#2F4F7A", None, "#3E6B48", None]
    for r in range(8):
        for c in range(4):
            k = r * 4 + c
            x0, y0 = c * CW, r * CHh
            base = bases[int(rng.integers(len(bases)))]
            cell = paper(CW, CHh, base=base, seed=1210 + k, stains=0, vignette=0.18, fibres=0.8)
            pen = Pen(CW, CHh, 4)
            pen.rect(8, 8, CW - 8, CHh - 8, outline=2)
            stc = stripes[int(rng.integers(len(stripes)))]
            sp = Pen(CW, CHh, 4)
            if stc:
                sp.rect(10, 10, 26, CHh - 10)
            year = int(rng.integers(1962, 1980))
            box = int(rng.integers(1, 240))
            rng_code = rng.choice(["B-3", "B-3", "B-3", "B-2", "B-4", "B-1"])
            lo = int(rng.integers(0, 98)) * 10 + 1000 * int(rng.integers(0, 2))
            span = f"№ {lo:04d}–{lo + int(rng.integers(2, 6)) * 10 - 1:04d}"   # file-number range, no words
            tp = Pen(CW, CHh, 4)
            xt = 38 if stc else 22
            typed(tp, xt, 58, f"{rng_code} / {year} / {box:03d}", 20 if stc else 21, rng, path=F_TYPE_B, jitter=0.4)
            typed(tp, xt, 94, span, 19, rng, jitter=0.4)
            cell = paint(cell, ink(pen.arr(), 1220 + k, 0.2), "#5A4A3A", 0.7)
            if stc:
                cell = paint(cell, ink(sp.arr(), 1230 + k, 0.2), stc, 0.85)
            cell = paint(cell, ink(tp.arr(), 1240 + k, 0.3, 1.6), "#1E1F26", 0.9)
            if rng.random() < 0.3:          # handwritten addition
                hw = Pen(CW, CHh, 4)
                rot_text(hw, CW - 52, 92, rng.choice(["II", "1979", "?", "L.R.", "x"]), F_HAND, 26,
                         angle=float(rng.uniform(-8, 8)), weight=520)
                cell = paint(cell, ink(hw.arr(), 1250 + k, 0.3), "#3A3A60", 0.8)
            age = rng.uniform(0.0, 0.25)
            cell = multiply(cell, np.full((CHh, CW), age, np.float32), "#8A6A40")
            cell = multiply(cell, edge_wear(CW, CHh, 1260 + k, 14, 0.25), "#6A5030")
            rgb[y0:y0 + CHh, x0:x0 + CW] = cell
    save(to_img(rgb), "box_labels.jpg")


# =================================================================================================
# QA contact sheet
# =================================================================================================
SHEET_ITEMS = ["glyph_mark.png", "glyph_sign.png", "vault_engraving.png", "dest_symbols.png", "routing_chart.png",
               "badge.png", "index_card.png", "request_card.png", "film_strip_0.png", "film_strip_1.png",
               "film_strip_2.png", "film_strip_3.png", "reel_can_lid.png", "tape_label_1996.png",
               "tape_label_1997.png", "tape_label_1998.png", "slide_mark.png", "file_cover.png", "archive_rules.jpg",
               "box_labels.jpg", "film_frame_0.jpg", "film_frame_1.jpg", "film_frame_2.jpg", "film_frame_3.jpg",
               "film_frame_4.jpg", "film_frame_5.jpg", "film_secret.jpg", "vault_reel.jpg",
               "../../linoleum/albedo.jpg", "../../linoleum/normal.png", "../../linoleum/orm.jpg"]


def contact_sheet():
    SW, TH, PAD, LAB = 2400, 300, 18, 50
    tiles = []
    for name in SHEET_ITEMS:
        path = os.path.normpath(os.path.join(OUT, name))
        if not os.path.exists(path):
            continue
        im = Image.open(path).convert("RGBA")
        th = TH if im.width / im.height < 2.5 else TH * 0.75
        tw = int(im.width * th / im.height)
        if tw > SW - 2 * PAD:
            tw = SW - 2 * PAD
            th = im.height * tw / im.width
        im = im.resize((tw, int(th)), Image.LANCZOS)
        bg = Image.new("RGBA", im.size, (46, 52, 54, 255))
        chk = Pen(im.width, im.height, 1)
        for yy in range(0, im.height, 16):
            for xx in range(0, im.width, 16):
                if (xx // 16 + yy // 16) % 2:
                    chk.d.rectangle([xx, yy, xx + 15, yy + 15], fill=255)
        bg = Image.composite(Image.new("RGBA", im.size, (58, 64, 66, 255)), bg, chk.im)
        bg.alpha_composite(im)
        label = name.replace("../../", "").replace("linoleum/", "linoleum ")
        src = Image.open(path)
        tiles.append((bg.convert("RGB"), f"{label}\n{src.width}x{src.height} {src.mode}"))
    rows, cur, wsum = [], [], PAD
    for t in tiles:
        if wsum + t[0].width + PAD > SW and cur:
            rows.append(cur)
            cur, wsum = [], PAD
        cur.append(t)
        wsum += t[0].width + PAD
    rows.append(cur)
    height = PAD + sum(max(t[0].height for t in r) + LAB + PAD for r in rows) + 60
    sheet = Image.new("RGB", (SW, height), (28, 30, 32))
    d = ImageDraw.Draw(sheet)
    f = font(F_SANS, 18)
    d.text((PAD, 14), "MYSTERY ROOM - Chapter 2 decals, glyphs, film frames, linoleum (tools/textures/make_decals_ch2.py)",
           font=font(F_SANS_B, 24), fill=(230, 222, 200))
    y = 60
    for r in rows:
        x = PAD
        rh = max(t[0].height for t in r)
        for im, lab in r:
            sheet.paste(im, (x, y))
            d.multiline_text((x, y + im.height + 4), lab, font=f, fill=(200, 196, 186), spacing=6)
            x += im.width + PAD
        y += rh + LAB + PAD
    os.makedirs(QA, exist_ok=True)
    path = os.path.join(QA, "decals_ch2_contact_sheet.jpg")
    sheet.save(path, quality=88)
    print("  wrote", os.path.relpath(path, ROOT), sheet.size)


# ---- language sheet ----------------------------------------------------------------------------------
LOCALIZED = {   # generator name -> EN output file (RU / UZ variants: lname(file, lang))
    "routing_chart": "routing_chart.png", "badge": "badge.png", "index_card": "index_card.png",
    "request_card": "request_card.png", "file_cover": "file_cover.png", "archive_rules": "archive_rules.jpg",
    "tape_label_1996": "tape_label_1996.png", "tape_label_1997": "tape_label_1997.png",
    "tape_label_1998": "tape_label_1998.png",
}


def lang_sheet():
    """qa/decals_ch2_lang_sheet.jpg: every localized decal as EN | RU | UZ."""
    CW, CH, PAD, LAB = 780, 430, 16, 30
    rows = [n for n in LOCALIZED.values() if os.path.exists(os.path.join(OUT, n))]
    sheet = Image.new("RGB", (3 * CW + 4 * PAD, 70 + len(rows) * (CH + LAB + PAD)), (28, 30, 32))
    d = ImageDraw.Draw(sheet)
    d.text((PAD, 18), "Chapter 2 localized decals: EN | RU | UZ (tools/textures/make_decals_ch2.py)",
           font=font(F_SANS_B, 26), fill=(230, 222, 200))
    y = 70
    for name in rows:
        for i, lang in enumerate(LANGS):
            path = os.path.join(OUT, lname(name, lang))
            x = PAD + i * (CW + PAD)
            if not os.path.exists(path):
                continue
            im = Image.open(path).convert("RGBA")
            sc = min(CW / im.width, CH / im.height)
            im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
            bg = Image.new("RGBA", im.size, (52, 58, 60, 255))
            bg.alpha_composite(im)
            sheet.paste(bg.convert("RGB"), (x + (CW - im.width) // 2, y))
            d.text((x, y + CH + 4), lname(name, lang), font=font(F_SANS, 20), fill=(200, 196, 186))
        y += CH + LAB + PAD
    path = os.path.join(QA, "decals_ch2_lang_sheet.jpg")
    sheet.save(path, quality=88)
    print("  wrote", os.path.relpath(path, ROOT), sheet.size)


GENERATORS: dict = {}


def register(name, fn, localized=False):
    """fn(langs) for localized decals (one file per language), fn() otherwise."""
    GENERATORS[name] = (fn, localized)


def _per_lang(fn, *a):
    return lambda langs: [fn(*a, lang) for lang in langs]


register("glyph_mark", glyph_mark)
register("glyph_sign", glyph_sign)
register("vault_engraving", vault_engraving)
for _k in range(4):
    register(f"film_strip_{_k}", (lambda k: (lambda: film_strip(k)))(_k))
register("reel_can_lid", reel_can_lid)
register("index_card", _per_lang(index_card), True)
register("request_card", _per_lang(request_card), True)
register("badge", _per_lang(badge), True)
register("routing_chart", _per_lang(routing_chart), True)
register("dest_symbols", dest_symbols)
for _y in TAPE_YEARS:
    register(f"tape_label_{_y}", _per_lang(tape_label, _y), True)
register("slide_mark", slide_mark)
register("file_cover", _per_lang(file_cover), True)
register("linoleum", linoleum)
register("film_frame_0", film_frame_0)
register("film_frame_1", film_frame_1)
register("film_frame_2", film_frame_2)
register("film_frame_3", film_frame_3)
register("film_frame_4", film_frame_4)
register("film_frame_5", film_frame_5)
register("film_secret", film_secret)
register("vault_reel", vault_reel)
register("archive_rules", _per_lang(archive_rules), True)
register("box_labels", box_labels)


# ================================================================================================= main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma-separated generator names")
    ap.add_argument("--langs", default=",".join(LANGS), help="languages for decals with words (default en,ru,uz)")
    ap.add_argument("--sheet-only", action="store_true", help="only rebuild the QA sheets")
    ap.add_argument("--no-sheet", action="store_true", help="skip the QA sheets")
    args = ap.parse_args()
    langs = [x for x in args.langs.split(",") if x]
    bad = [x for x in langs if x not in LANGS]
    if bad:
        ap.error(f"unknown language(s) {bad}; known: {LANGS}")
    names = [] if args.sheet_only else list(GENERATORS)
    if args.only:
        names = [n for n in args.only.split(",") if n]
        bad = [n for n in names if n not in GENERATORS]
        if bad:
            ap.error(f"unknown: {bad}; known: {list(GENERATORS)}")
    for n in names:
        fn, localized = GENERATORS[n]
        print(f"[{n}]" + (f" {','.join(langs)}" if localized else ""))
        fn(langs) if localized else fn()
    if GLYPH_FALLBACKS:
        print("glyph fallbacks:", ", ".join(f"{a} {c} -> {b}" for a, c, b in sorted(GLYPH_FALLBACKS)))
    if not args.no_sheet and (args.sheet_only or not args.only):
        print("[contact_sheet]")
        contact_sheet()
        lang_sheet()
    return 0


if __name__ == "__main__":
    sys.exit(main())
