#!/usr/bin/env python3
"""Builds the MYSTERY ROOM promo videos from the rendered game clips (promo/build_clips.sh), the narration lines
(promo/build_voice.sh), the game's own music / ambience / sfx and a synthesized sting.

  PROMO_WORK=/tmp/promo_work python3 promo/build_videos.py [v1] [v2] [v3]

Outputs (promo/): video1_teaser_9x16.mp4, video2_can_you_solve_it_9x16.mp4, video3_trailer_16x9.mp4 (English subs
burned in), video3_trailer_16x9_ru.mp4, video3_trailer_16x9_uz.mp4, plus the same for videos 1 and 2 (_ru, _uz),
and the .srt files for en / ru / uz. Every ffmpeg command is appended to promo/ffmpeg_log.txt.
"""
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORK = os.environ.get("PROMO_WORK", "/tmp/promo_work")
CLIPS = os.path.join(WORK, "clips")
VOICE = os.path.join(WORK, "voice")
TMP = os.path.join(WORK, "build")
OUT = os.path.join(ROOT, "promo")
AUDIO = os.path.join(ROOT, "game", "assets", "audio")
FONTS = os.path.join(ROOT, "game", "assets", "fonts")
os.makedirs(TMP, exist_ok=True)

LANGS = ["en", "ru", "uz"]

# Narration lines (English is spoken; ru / uz are subtitles only). Uzbek Latin uses the game's own apostrophes.
LINES = {
    "T1": ("Laboratory Seven has been silent for a very long time.",
           "Лаборатория 7 молчит уже очень давно.",
           "7-laboratoriya uzoq vaqtdan beri jimjit."),
    "T2": ("But something inside is still waiting.",
           "Но что-то внутри всё ещё ждёт.",
           "Ammo ichkarida nimadir hamon kutmoqda."),
    "T3": ("Can you find what the Institute forgot?",
           "Сможешь узнать, что забыл Институт?",
           "Institut nimani unutganini topa olasanmi?"),
    "S1": ("A locked drawer. Four silent wheels.",
           "Запертый ящик. Четыре молчаливых колеса.",
           "Qulflangan tortma. Toʻrtta jim gʻildirak."),
    "S2": ("Ink that only ultraviolet light can read.",
           "Чернила, которые читаются только в ультрафиолете.",
           "Faqat ultrabinafsha nur oʻqiy oladigan siyoh."),
    "S3": ("A panel that needs its power back.",
           "Щиток, которому нужно вернуть питание.",
           "Quvvati qaytishini kutayotgan panel."),
    "S4": ("Can you solve it? Two chapters, free to play.",
           "Сможешь решить? Две главы — бесплатно.",
           "Yecha olasanmi? Ikki bob — bepul."),
    "R1": ("The Institute was lost. Its secrets were not.",
           "Институт был потерян. Его тайны — нет.",
           "Institut yoʻqolgan edi. Sirlari esa yoʻq."),
    "R2": ("Search Leyla's laboratory. Every object has a story.",
           "Обыщи лабораторию Лейлы. У каждого предмета своя история.",
           "Leylaning laboratoriyasini tintuv qil. Har bir buyumning oʻz hikoyasi bor."),
    "R3": ("Read what only ultraviolet light can show.",
           "Прочти то, что показывает только ультрафиолет.",
           "Faqat ultrabinafsha nur koʻrsata oladigan narsani oʻqi."),
    "R4": ("Restore the power. Open the hidden darkroom.",
           "Верни питание. Открой тайную тёмную комнату.",
           "Quvvatni qaytar. Yashirin qorongʻi xonani och."),
    "R5": ("Follow the light, and bend the beam.",
           "Следуй за светом и направь луч.",
           "Nur izidan bor va nurni burib yoʻnalt."),
    "R6": ("Beneath the archive, a vault is waiting.",
           "Под архивом ждёт хранилище.",
           "Arxiv ostida seyfxona kutmoqda."),
    "R7": ("And something below is... listening.",
           "И что-то внизу... слушает.",
           "Va pastda nimadir... quloq solmoqda."),
    "R8": ("Mystery Room. Lost Institute. Two chapters, free to play.",
           "Mystery Room: Забытый институт. Две главы — бесплатно.",
           "Mystery Room: Sirli institut. Ikki bob — bepul."),
}

HOOK = {"en": "CAN YOU SOLVE IT?", "ru": "СМОЖЕШЬ РЕШИТЬ?", "uz": "YECHA OLASANMI?"}
SEARCH = "Search: Mystery Room: Lost Institute"  # placeholder, the store links do not exist yet

# Finale clip timings (seconds inside a_finale_*.mp4, see promo/README.md): set after inspecting the frames.
FIN = {"vault_open_ss": 0.0, "shaft_ss": 0.0}
if os.path.exists(os.path.join(os.path.dirname(__file__), "finale_timing.py")):
    exec(open(os.path.join(os.path.dirname(__file__), "finale_timing.py")).read())

# Video specs. seg = (clip, start in clip, duration). Times of voice / sfx / titles are in video seconds.
# sfx = (game sfx name, time, gain dB, optional (start, dur) trim of the sample)
SPECS = {
    "v1": dict(
        name="video1_teaser_9x16", size=(1080, 1920), srt="video1_teaser",
        segs=[("l_dark_P", 1.0, 6.0), ("l_uv_P", 1.0, 4.5), ("l_darkroom_P", 1.0, 4.5), ("FIN_SHAFT_P", 0, 2.5)],
        total=20.0,
        voice=[("T1", 0.6), ("T2", 6.4), ("T3", 11.2)],
        music=("music_lab", 0.0), ambience="amb_lab_dark",
        sfx=[("intro_thunder", 0.2, -8), ("uv_on", 7.5, -4), ("page_turn", 10.7, -8)],
        sting=17.3,
        titles=[dict(kind="title", t0=17.3, t1=20.0)],
    ),
    "v2": dict(
        name="video2_can_you_solve_it_9x16", size=(1080, 1920), srt="video2_can_you_solve_it",
        segs=[("l_drawer_P", 1.0, 4.4), ("l_uv_P", 1.0, 6.0), ("l_panel_P", 1.0, 5.1), ("l_beam_P", 1.0, 5.5),
              ("a_hall_P", 1.0, 3.5)],
        total=30.0,
        voice=[("S1", 0.4), ("S2", 4.6), ("S3", 10.8), ("S4", 25.0)],
        music=("music_lab", 20.0), ambience="amb_lab_dark",
        sfx=[("wheel_tick", 1.5, -6), ("wheel_tick", 2.2, -6), ("wheel_tick", 2.9, -6), ("uv_on", 5.9, -4),
             ("switch_toggle", 11.9, -4), ("switch_toggle", 12.7, -4), ("switch_toggle", 13.5, -4)],
        sting=24.6,
        titles=[dict(kind="hook", t0=0.2, t1=3.6), dict(kind="end", t0=24.6, t1=30.0)],
    ),
    "v3": dict(
        name="video3_trailer_16x9", size=(1920, 1080), srt="video3_trailer",
        segs=[("l_dark_L", 1.0, 6.5), ("l_drawer_L", 1.0, 4.4), ("l_gearbox_L", 1.0, 4.6), ("l_uv_L", 1.0, 6.0),
              ("l_panel_L", 1.0, 5.1), ("l_darkroom_L", 1.0, 8.0), ("l_beam_L", 1.0, 5.0), ("a_hall_L", 1.0, 4.5),
              ("FIN_OPEN_L", 0, 5.0), ("FIN_SHAFT_L", 0, 6.0)],
        total=60.0,
        voice=[("R1", 0.8), ("R2", 7.0), ("R3", 16.0), ("R4", 22.0), ("R5", 35.0), ("R6", 40.0), ("R7", 50.0),
               ("R8", 53.6)],
        music=("music_lab", 0.0), music2=("music_archive", 36.0, 30.0), ambience="amb_lab_dark",
        sfx=[("intro_thunder", 0.2, -8), ("wheel_tick", 8.0, -6), ("wheel_tick", 8.7, -6), ("wheel_tick", 9.4, -6),
             ("gear_turn", 12.4, -8), ("gear_turn", 13.2, -8), ("gear_turn", 14.0, -8), ("uv_on", 17.0, -4),
             ("switch_toggle", 23.0, -4), ("switch_toggle", 23.8, -4), ("switch_toggle", 24.6, -4),
             ("vault_wheel", 45.0, -6), ("vault_bolts", 46.0, -4), ("vault_door_open", 47.2, -4),
             ("receiver_static", 50.5, -16)],
        sting=55.0,
        titles=[dict(kind="title", t0=53.0, t1=60.0)],
    ),
}


def run(cmd, log=True):
    if log:
        with open(os.path.join(OUT, "ffmpeg_log.txt"), "a") as f:
            f.write(" ".join(repr(c) if " " in c or ";" in c else c for c in cmd) + "\n\n")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def dur(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path])
    return float(out.decode().strip())


def ts(t, comma=True):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return "%02d:%02d:%06.3f" % (h, m, s) if not comma else ("%02d:%02d:%06.3f" % (h, m, s)).replace(".", ",")


def cues(spec):
    out = []
    for vid, t0 in spec["voice"]:
        d = dur(os.path.join(VOICE, vid + ".wav")) - 0.3
        out.append((vid, t0, t0 + d + 0.25))
    return out


def write_srt(spec, lang):
    li = LANGS.index(lang)
    path = os.path.join(OUT, "%s_%s.srt" % (spec["srt"], lang))
    with open(path, "w", encoding="utf-8") as f:
        for i, (vid, a, b) in enumerate(cues(spec), 1):
            f.write("%d\n%s --> %s\n%s\n\n" % (i, ts(a), ts(b), LINES[vid][li]))
    return path


def write_ass(spec, lang):
    W, H = spec["size"]
    portrait = H > W
    size = 74 if portrait else 68
    marg_v = 560 if portrait else 96
    marg_lr = 90 if portrait else 200
    li = LANGS.index(lang)
    path = os.path.join(TMP, "%s_%s.ass" % (spec["name"], lang))
    hdr = ("[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
           "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,"
           "Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
           "Style: Sub,Noto Sans,%d,&H00FFFFFF,&H00FFFFFF,&H00101010,&H96000000,-1,0,0,0,100,100,0,0,3,14,0,2,%d,%d,%d,1\n\n"
           "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n") % (
        W, H, size, marg_lr, marg_lr, marg_v)
    with open(path, "w", encoding="utf-8") as f:
        f.write(hdr)
        for vid, a, b in cues(spec):
            f.write("Dialogue: 0,%s,%s,Sub,,0,0,0,,%s\n" % (ts(a, False)[1:-1], ts(b, False)[1:-1], LINES[vid][li]))
    return path


def fin_clip(tag):
    # (clip file, ss) for the finale excerpts
    if tag.startswith("FIN_OPEN"):
        return "a_finale_" + tag[-1], FIN["vault_open_ss"]
    return "a_finale_" + tag[-1], FIN["shaft_ss"]


def build_video(key, lang):
    spec = SPECS[key]
    W, H = spec["size"]
    tmp = os.path.join(TMP, "%s_%s" % (spec["name"], lang))
    os.makedirs(tmp, exist_ok=True)
    # ---- video graph
    inputs, chains, labels = [], [], []
    for i, (clip, ss, d) in enumerate(spec["segs"]):
        if clip.startswith("FIN_"):
            clip, base = fin_clip(clip)
            ss = base + ss
        inputs += ["-ss", "%.3f" % ss, "-t", "%.3f" % d, "-i", os.path.join(CLIPS, clip + ".mp4")]
        fo = max(d - 0.25, 0)
        chains.append("[%d:v]setpts=PTS-STARTPTS,scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,fps=30,"
                      "fade=t=in:st=0:d=0.25,fade=t=out:st=%.3f:d=0.25,format=yuv420p[v%d]" % (i, W, H, W, H, fo, i))
        labels.append("[v%d]" % i)
    chains.append("%sconcat=n=%d:v=1:a=0[cat]" % ("".join(labels), len(labels)))
    last = "cat"
    # tail: hold black if segments are shorter than the total (title card sits on black / last frame)
    seg_total = sum(s[2] for s in spec["segs"])
    if seg_total < spec["total"]:
        chains.append("[%s]tpad=stop_mode=add:stop_duration=%.3f:color=black[pad]" % (last, spec["total"] - seg_total + 0.5))
        last = "pad"
    cf = os.path.join(FONTS, "CormorantGaramond-Bold.ttf")
    nf = os.path.join(FONTS, "NotoSans-Variable.ttf")

    def alpha(t0, t1, fi=0.7, fo_=0.6):
        return "if(lt(t,%.2f),0,if(lt(t,%.2f),(t-%.2f)/%.2f,if(lt(t,%.2f),1,max(0,(%.2f-t)/%.2f))))" % (
            t0, t0 + fi, t0, fi, t1 - fo_, t1, fo_)

    n = 0
    for tt in spec["titles"]:
        a = alpha(tt["t0"], tt["t1"] + 0.0001, fo_=0.01 if tt["kind"] in ("title", "end") else 0.6)
        fs_big = 150 if W < H else 150
        if tt["kind"] == "hook":
            fs = 92 if W < H else 100
            chains.append("[%s]drawtext=fontfile='%s':text='%s':fontsize=%d:fontcolor=0xF4E9CC:borderw=5:bordercolor=0x101010:"
                          "x=(w-text_w)/2:y=h*0.16:alpha='%s'[t%d]" % (last, cf, HOOK[lang], fs, a, n))
            last = "t%d" % n
            n += 1
        elif tt["kind"] in ("title", "end"):
            # darken the picture under the card, then the name, the sub title and the search line
            chains.append("[%s]drawbox=x=0:y=0:w=iw:h=ih:color=black@0.55:t=fill:enable='between(t,%.2f,%.2f)'[d%d]" % (
                last, tt["t0"], tt["t1"], n))
            last = "d%d" % n
            parts = []
            if tt["kind"] == "end":
                parts.append((HOOK[lang], 84 if W < H else 90, 0.14 if W < H else 0.22, cf))
            parts.append(("MYSTERY ROOM", 112 if W < H else 170, 0.27 if W < H else 0.33, cf))
            parts.append(("LOST INSTITUTE", 80 if W < H else 92, 0.36 if W < H else 0.50, cf))
            parts.append((SEARCH, 40 if W < H else 44, 0.45 if W < H else 0.68, nf))
            for text, fs, y, font in parts:
                chains.append("[%s]drawtext=fontfile='%s':text='%s':fontsize=%d:fontcolor=0xF4E9CC:borderw=4:"
                              "bordercolor=0x101010:x=(w-text_w)/2:y=h*%.2f:alpha='%s'[t%d]" % (
                                  last, font, text.replace(":", "\\:"), fs, y, alpha(tt["t0"], tt["t1"], 0.8, 0.01), n))
                last = "t%d" % n
                n += 1
    ass = write_ass(spec, lang)
    chains.append("[%s]ass='%s':fontsdir='%s'[vout]" % (last, ass, FONTS))
    gs = os.path.join(tmp, "graph.txt")
    open(gs, "w").write(";\n".join(chains))
    vid = os.path.join(tmp, "video.mp4")
    run(["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex_script", gs, "-map", "[vout]", "-t", "%.3f" % spec["total"],
        "-r", "30", "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-maxrate", "6M" if W < H else "9M", "-bufsize", "12M", "-pix_fmt", "yuv420p", vid])
    # ---- audio (the same for every language; built once per video)
    aud = os.path.join(TMP, spec["name"] + "_audio.wav")
    if not os.path.exists(aud):
        build_audio(spec, aud)
    final = os.path.join(OUT, spec["name"] + ("" if lang == "en" else "_" + lang) + ".mp4")
    run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", aud, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
         "-b:a", "192k", "-ar", "48000", "-ac", "2", "-shortest", "-movflags", "+faststart", final])
    return final


def build_audio(spec, out):
    T = spec["total"]
    ins, fl = [], []
    idx = 0

    def add(path, ss=None, d=None):
        nonlocal idx
        if ss is not None:
            ins.extend(["-ss", "%.3f" % ss])
        if d is not None:
            ins.extend(["-t", "%.3f" % d])
        ins.extend(["-i", path])
        idx += 1
        return idx - 1

    fmt = "aformat=sample_rates=48000:channel_layouts=stereo"
    # music bed (+ optional second cue crossfaded in)
    m1 = add(os.path.join(AUDIO, "music", spec["music"][0] + ".ogg"), spec["music"][1], T + 1)
    fl.append("[%d:a]%s,volume=0.55,afade=t=in:d=2.5,atrim=0:%.2f,afade=t=out:st=%.2f:d=2.5[m1]" % (
        m1, fmt, T, T - 2.5 if "music2" not in spec else 40.0))
    bed = "m1"
    if "music2" in spec:
        name, ss, st = spec["music2"]
        m2 = add(os.path.join(AUDIO, "music", name + ".ogg"), ss, T - st + 1)
        fl.append("[%d:a]%s,volume=0.55,afade=t=in:d=4,atrim=0:%.2f,adelay=%d|%d,afade=t=out:st=%.2f:d=2.5[m2]" % (
            m2, fmt, T - st + 1, int(st * 1000), int(st * 1000), T - 2.5))
        fl.append("[m1][m2]amix=inputs=2:normalize=0[mm]")
        bed = "mm"
    a1 = add(os.path.join(AUDIO, "ambience", spec["ambience"] + ".ogg"), 0, T)
    fl.append("[%d:a]%s,volume=0.30,afade=t=in:d=2,afade=t=out:st=%.2f:d=1.5[amb]" % (a1, fmt, T - 1.5))
    fl.append("[%s][amb]amix=inputs=2:normalize=0[bedmix]" % bed)
    # voice
    vlabels = []
    for i, (vid, t0) in enumerate(spec["voice"]):
        v = add(os.path.join(VOICE, vid + ".wav"))
        ms = int(t0 * 1000)
        fl.append("[%d:a]%s,volume=1.0,adelay=%d|%d[v%d]" % (v, fmt, ms, ms, i))
        vlabels.append("[v%d]" % i)
    fl.append("%samix=inputs=%d:normalize=0,apad=whole_dur=%.2f,atrim=0:%.2f[voice]" % ("".join(vlabels), len(vlabels), T, T))
    fl.append("[voice]asplit=2[vo][vsc]")
    fl.append("[bedmix][vsc]sidechaincompress=threshold=0.015:ratio=9:attack=30:release=500:makeup=1[ducked]")
    # sfx + sting
    sl = []
    for i, s in enumerate(spec["sfx"]):
        name, t0, g = s[0], s[1], s[2]
        k = add(os.path.join(AUDIO, "sfx", name + ".ogg"))
        ms = int(t0 * 1000)
        fl.append("[%d:a]%s,volume=%ddB,adelay=%d|%d[s%d]" % (k, fmt, g, ms, ms, i))
        sl.append("[s%d]" % i)
    k = add(os.path.join(WORK, "sting.wav"))
    ms = int(spec["sting"] * 1000)
    fl.append("[%d:a]%s,volume=-3dB,adelay=%d|%d[sting]" % (k, fmt, ms, ms))
    sl.append("[sting]")
    fl.append("[ducked][vo]%samix=inputs=%d:normalize=0,atrim=0:%.2f,loudnorm=I=-16:TP=-1.5:LRA=9,aformat=sample_rates=48000:channel_layouts=stereo[aout]" % (
        "".join(sl), 2 + len(sl), T))
    gs = out + ".graph.txt"
    open(gs, "w").write(";\n".join(fl))
    run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex_script", gs, "-map", "[aout]", "-t", "%.2f" % T, out])


def main():
    which = sys.argv[1:] or list(SPECS)
    for key in which:
        spec = SPECS[key]
        for lang in LANGS:
            write_srt(spec, lang)
            print(build_video(key, lang))


if __name__ == "__main__":
    main()
