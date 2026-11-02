#!/usr/bin/env python3
"""Builds the YouTube package of the 1.1 promo: the "New floors" trailer (1920x1080) and the Short (1080x1920) in EN / RU / UZ
from the real-game clips (build_clips.sh), the game's own audio of every take, the game's music, the narration (build_voice.sh)
and the sting.

  PROMO_WORK=/tmp/promo_work python3 promo/v1_1/build_videos.py [trailer] [short]

Outputs (promo/v1_1/): trailer_new_floors_16x9[_ru|_uz].mp4, short_new_floors_9x16[_ru|_uz].mp4 and the .srt files.
Every ffmpeg command is appended to promo/v1_1/ffmpeg_log.txt; timeline facts go to promo/v1_1/timeline.json.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from translations import LINES  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
WORK = os.environ.get("PROMO_WORK", "/tmp/promo_work")
CLIPS = os.path.join(WORK, "clips")
VOICE = os.path.join(WORK, "voice11")
TMP = os.path.join(WORK, "build11")
OUT = HERE
AUDIO = os.path.join(ROOT, "game", "assets", "audio")
FONTS = os.path.join(ROOT, "game", "assets", "fonts")
os.makedirs(TMP, exist_ok=True)
LANGS = ["en", "ru", "uz"]
SEARCH = "Search: Mystery Room: Lost Institute"  # no store link exists yet; none is invented
SUB = {"en": "Version 1.1  -  New floors", "ru": "Версия 1.1  -  новые этажи", "uz": "1.1-versiya  -  yangi qavatlar"}
FREE = {"en": "Chapters 1 and 2 are free", "ru": "Главы 1 и 2 бесплатны", "uz": "1- va 2-bob bepul"}


def start_offset(clip):
    """Seconds of settling frames at the start of a clip (render_log.txt: start_frame)."""
    best = None
    for line in open(os.path.join(HERE, "render_log.txt"), encoding="utf-8"):
        m = re.search(r"clip=%s .*start_frame=(\d+)" % re.escape(clip), line)
        if m:
            best = int(m.group(1))
    return (best if best is not None else 37) / 30.0 + 0.05


# seg = (clip, offset after the settling, duration)
# voice = (line id, index of the seg it starts in, seconds into that seg)
SPECS = {
    "trailer": dict(
        name="trailer_new_floors_16x9", size=(1920, 1080), dark_title=(0.0, 4.6),
        segs=[("L_hall", 0.0, 7.8), ("L_plan", 0.0, 8.0), ("L_door", 0.0, 6.0), ("L_pump", 0.0, 12.8),
              ("L_cell", 0.0, 7.8), ("L_cold_walk", 0.0, 9.6), ("L_frost", 0.0, 9.0), ("L_lift", 0.0, 7.5),
              ("L_gallery", 0.0, 10.0), ("L_plate", 0.0, 7.0), ("L_office", 0.0, 7.5)],
        end_card=7.5,
        voice=[("V1", 0, 5.0), ("V2", 1, 1.2), ("V3", 1, 3.9), ("V4", 2, 1.3), ("V5", 3, 0.6), ("V6", 3, 7.5),
               ("V7", 4, 1.0), ("V8", 5, 1.0), ("V9", 6, 1.5), ("V10", 7, 1.0), ("V11", 8, 0.8), ("V12", 10, 0.8)],
        end_voice=("V14", 2.7), extra_voice=[("V13", 10, 4.2)],
        chapters=[("Intro", 0), ("The building and its floor plan", 1), ("Through the hidden door", 2), ("Pump Room", 3),
                  ("Night Cell", 4), ("Cold Store", 5), ("Frost window", 6), ("Book lift", 7), ("Reading Gallery", 8),
                  ("Plate Room", 9), ("Director's Office", 10)],
        music="music_archive",
    ),
    "short": dict(
        name="short_new_floors_9x16", size=(1080, 1920), dark_title=(0.0, 3.0),
        segs=[("P_hall", 0.0, 5.5), ("P_door", 0.0, 6.0), ("P_pump", 0.0, 5.8), ("P_cell", 0.0, 5.8),
              ("P_cold_walk", 0.0, 6.0), ("P_gallery", 0.0, 5.5), ("P_plate", 0.0, 4.3)],
        end_card=5.2,
        voice=[("S1", 0, 1.0), ("S2", 1, 0.2), ("S3", 2, 1.0), ("S4", 4, 0.8)],
        end_voice=("S5", 0.8), extra_voice=[],
        chapters=[], music="music_archive",
    ),
}


def run(cmd):
    with open(os.path.join(OUT, "ffmpeg_log.txt"), "a") as f:
        f.write(" ".join(repr(c) if re.search(r"[ ;\[\]()|]", c) else c for c in cmd) + "\n\n")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).decode().strip())


def ts(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return ("%02d:%02d:%06.3f" % (h, m, s)).replace(".", ",")


def timeline(spec):
    """Start time of each seg, the total length (segs + end card) and the absolute voice times."""
    starts, t = [], 0.0
    for _, _, d in spec["segs"]:
        starts.append(t)
        t += d
    total = t + spec["end_card"]
    voice = [(vid, starts[i] + off) for vid, i, off in spec["voice"]]
    for vid, i, off in spec.get("extra_voice", []):
        voice.append((vid, starts[i] + off))
    voice.append((spec["end_voice"][0], t + spec["end_voice"][1]))
    return starts, t, total, voice


def check_overlap(voice):
    c = sorted(cues(voice), key=lambda x: x[1])
    for (a, a0, a1), (b, b0, b1) in zip(c, c[1:]):
        if b0 < a1 + 0.1:
            raise SystemExit("voice lines overlap: %s (%.1f-%.1f) and %s (%.1f-%.1f)" % (a, a0, a1, b, b0, b1))


def cues(voice):
    out = []
    for vid, t0 in voice:
        d = dur(os.path.join(VOICE, vid + ".wav")) - 0.3
        out.append((vid, t0, t0 + d + 0.25))
    return out


def write_srt(spec, lang, voice):
    li = LANGS.index(lang)
    path = os.path.join(OUT, "%s_%s.srt" % (spec["name"], lang))
    with open(path, "w", encoding="utf-8") as f:
        for i, (vid, a, b) in enumerate(cues(voice), 1):
            f.write("%d\n%s --> %s\n%s\n\n" % (i, ts(a), ts(b), LINES[vid][li]))
    return path


def write_ass(spec, lang, voice):
    W, H = spec["size"]
    portrait = H > W
    size = 70 if portrait else 62
    marg_v = 330 if portrait else 70
    marg_lr = 70 if portrait else 220
    li = LANGS.index(lang)
    path = os.path.join(TMP, "%s_%s.ass" % (spec["name"], lang))
    hdr = ("[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
           "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,"
           "Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
           "Style: Sub,Noto Sans,%d,&H00FFFFFF,&H00FFFFFF,&H00101010,&H96000000,-1,0,0,0,100,100,0,0,3,14,0,2,%d,%d,%d,1\n\n"
           "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n") % (
        W, H, size, marg_lr, marg_lr, marg_v)
    end_card_t0 = timeline(spec)[1]
    with open(path, "w", encoding="utf-8") as f:
        f.write(hdr)
        for vid, a, b in cues(voice):
            if a >= end_card_t0 - 0.01:  # on the end card the text is part of the card layout (no subtitle box over the title)
                marg = 120 if portrait else 60
            else:
                marg = marg_v
            f.write("Dialogue: 0,%s,%s,Sub,,0,0,%d,,%s\n" % (ts(a)[1:-1].replace(",", "."), ts(b)[1:-1].replace(",", "."), marg, LINES[vid][li]))
    return path


def build_audio(key, spec, starts, t_end, total, voice, out):
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
    # the game's own audio of every take (ambience of the room, steps, doors, lift, moment cues)
    labels = []
    for i, (clip, off, d) in enumerate(spec["segs"]):
        k = add(os.path.join(CLIPS, clip + ".wav"), start_offset(clip) + off, d)
        fo = max(d - 0.3, 0)
        fl.append("[%d:a]%s,asetpts=PTS-STARTPTS,volume=2.0,afade=t=in:d=0.3,afade=t=out:st=%.3f:d=0.3[c%d]" % (k, fmt, fo, i))
        labels.append("[c%d]" % i)
    fl.append("%sconcat=n=%d:v=0:a=1,apad=whole_dur=%.2f,atrim=0:%.2f[clipaud]" % ("".join(labels), len(labels), total, total))
    m = add(os.path.join(AUDIO, "music", spec["music"] + ".ogg"), 0, total + 1)
    fl.append("[%d:a]%s,volume=0.5,afade=t=in:d=2.5,atrim=0:%.2f,afade=t=out:st=%.2f:d=3[mus]" % (m, fmt, total, total - 3.0))
    fl.append("[clipaud][mus]amix=inputs=2:normalize=0[bed]")
    vl = []
    for i, (vid, t0) in enumerate(voice):
        v = add(os.path.join(VOICE, vid + ".wav"))
        ms = int(t0 * 1000)
        fl.append("[%d:a]%s,adelay=%d|%d[v%d]" % (v, fmt, ms, ms, i))
        vl.append("[v%d]" % i)
    fl.append("%samix=inputs=%d:normalize=0,apad=whole_dur=%.2f,atrim=0:%.2f[voice]" % ("".join(vl), len(vl), total, total))
    fl.append("[voice]asplit=2[vo][vsc]")
    fl.append("[bed][vsc]sidechaincompress=threshold=0.015:ratio=9:attack=30:release=500:makeup=1[ducked]")
    k = add(os.path.join(WORK, "sting.wav"))
    ms = int((t_end + 0.1) * 1000)
    fl.append("[%d:a]%s,volume=-3dB,adelay=%d|%d[sting]" % (k, fmt, ms, ms))
    fl.append("[ducked][vo][sting]amix=inputs=3:normalize=0,atrim=0:%.2f,loudnorm=I=-16:TP=-1.5:LRA=9,aformat=sample_rates=48000:channel_layouts=stereo[aout]" % total)
    gs = out + ".graph.txt"
    open(gs, "w").write(";\n".join(fl))
    run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex_script", gs, "-map", "[aout]", "-t", "%.2f" % total, out])


def build_video(key, lang):
    spec = SPECS[key]
    W, H = spec["size"]
    portrait = H > W
    starts, t_end, total, voice = timeline(spec)
    check_overlap(voice)
    tmp = os.path.join(TMP, "%s_%s" % (spec["name"], lang))
    os.makedirs(tmp, exist_ok=True)
    inputs, chains, labels = [], [], []
    for i, (clip, off, d) in enumerate(spec["segs"]):
        inputs += ["-ss", "%.3f" % (start_offset(clip) + off), "-t", "%.3f" % d, "-i", os.path.join(CLIPS, clip + ".mp4")]
        chains.append("[%d:v]setpts=PTS-STARTPTS,scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,fps=30,"
                      "fade=t=in:st=0:d=0.3,fade=t=out:st=%.3f:d=0.3,format=yuv420p[v%d]" % (i, W, H, W, H, max(d - 0.3, 0), i))
        labels.append("[v%d]" % i)
    # the end card sits on the last frame of the last clip (held), dimmed
    chains.append("%sconcat=n=%d:v=1:a=0[cat]" % ("".join(labels), len(labels)))
    chains.append("[cat]tpad=stop_mode=clone:stop_duration=%.3f[pad]" % (spec["end_card"] + 0.5))
    last = "pad"
    cf = os.path.join(FONTS, "CormorantGaramond-Bold.ttf")
    nf = os.path.join(FONTS, "NotoSans-Variable.ttf")

    def alpha(t0, t1, fi=0.7, fo_=0.01):
        return "if(lt(t,%.2f),0,if(lt(t,%.2f),(t-%.2f)/%.2f,if(lt(t,%.2f),1,max(0,(%.2f-t)/%.2f))))" % (
            t0, t0 + fi, t0, fi, t1 - fo_, t1, fo_)

    n = 0

    def text(t, size, y, font, t0, t1, fi=0.7, fo_=0.01):
        nonlocal last, n
        chains.append("[%s]drawtext=fontfile='%s':text='%s':fontsize=%d:fontcolor=0xF4E9CC:borderw=4:bordercolor=0x101010:"
                      "x=(w-text_w)/2:y=h*%.3f:alpha='%s'[t%d]" % (last, font, t.replace(":", "\\:").replace("'", "’"), size, y, alpha(t0, t1, fi, fo_), n))
        last = "t%d" % n
        n += 1

    # opening title (dimmed picture) then end card
    a0, a1 = spec["dark_title"]
    chains.append("[%s]drawbox=x=0:y=0:w=iw:h=ih:color=black@0.5:t=fill:enable='between(t,%.2f,%.2f)'[d%d]" % (last, a0, a1, n))
    last = "d%d" % n
    n += 1
    big = 120 if portrait else 170
    mid = 84 if portrait else 96
    sm = 44 if portrait else 46
    text("MYSTERY ROOM", big, 0.30 if portrait else 0.30, cf, a0 + 0.3, a1, 0.6, 0.6)
    text("LOST INSTITUTE", mid, 0.38 if portrait else 0.47, cf, a0 + 0.3, a1, 0.6, 0.6)
    text(SUB[lang], sm, 0.45 if portrait else 0.64, nf, a0 + 0.8, a1, 0.6, 0.6)
    e0, e1 = t_end + 0.0, total
    chains.append("[%s]drawbox=x=0:y=0:w=iw:h=ih:color=black@0.62:t=fill:enable='between(t,%.2f,%.2f)'[d%d]" % (last, e0, e1 + 1, n))
    last = "d%d" % n
    n += 1
    text("MYSTERY ROOM", big, 0.22 if portrait else 0.22, cf, e0 + 0.2, e1 + 1, 0.8)
    text("LOST INSTITUTE", mid, 0.30 if portrait else 0.40, cf, e0 + 0.4, e1 + 1, 0.8)
    text(FREE[lang], sm + 8, 0.40 if portrait else 0.58, nf, e0 + 1.4, e1 + 1, 0.8)
    text(SEARCH, sm - 4 if portrait else sm, 0.46 if portrait else 0.66, nf, e0 + 1.8, e1 + 1, 0.8)
    ass = write_ass(spec, lang, voice)
    chains.append("[%s]ass='%s':fontsdir='%s'[vout]" % (last, ass, FONTS))
    gs = os.path.join(tmp, "graph.txt")
    open(gs, "w").write(";\n".join(chains))
    vid = os.path.join(tmp, "video.mp4")
    run(["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex_script", gs, "-map", "[vout]", "-t", "%.3f" % total,
        "-r", "30", "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-maxrate", "6M" if portrait else "9M", "-bufsize", "12M", "-pix_fmt", "yuv420p", vid])
    aud = os.path.join(TMP, spec["name"] + "_audio.wav")
    if not os.path.exists(aud):
        build_audio(key, spec, starts, t_end, total, voice, aud)
    final = os.path.join(OUT, spec["name"] + ("" if lang == "en" else "_" + lang) + ".mp4")
    run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", aud, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
         "-b:a", "192k", "-ar", "48000", "-ac", "2", "-shortest", "-movflags", "+faststart", final])
    return final


def main():
    which = sys.argv[1:] or list(SPECS)
    facts = {}
    for key in which:
        spec = SPECS[key]
        starts, t_end, total, voice = timeline(spec)
        facts[key] = dict(total=total, seg_starts=[round(s, 2) for s in starts], voice=[(v, round(t, 2)) for v, t in voice],
                          chapters=[(name, round(starts[i], 2)) for name, i in spec["chapters"]])
        for lang in LANGS:
            write_srt(spec, lang, voice)
            print(build_video(key, lang))
    old = {}
    p = os.path.join(OUT, "timeline.json")
    if os.path.exists(p):
        old = json.load(open(p))
    old.update(facts)
    json.dump(old, open(p, "w"), indent=1)


if __name__ == "__main__":
    main()
