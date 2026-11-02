#!/usr/bin/env python3
"""Builds the on-screen labels of the owner review video (ASS) from the recorder's markers.tsv (process frame = movie frame at 30 fps):
top-left "Now: <step>" (the puzzle step that is being played, named when it completes) and a short bottom-left "tap: <model/part>" after
every real tap. usage: review_labels.py <markers.tsv> <out.ass> [max seconds]"""
import sys

src, out = sys.argv[1], sys.argv[2]
limit = float(sys.argv[3]) if len(sys.argv) > 3 else 1e9
FPS = 30.0


def ts(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return "%d:%02d:%05.2f" % (h, m, s)


steps, taps = [], []
for line in open(src, encoding="utf-8"):
    f, kind, text = (line.rstrip("\n").split("\t") + ["", ""])[:3]
    if kind == "step":
        steps.append((int(f) / FPS, text.replace("OK ", "", 1)))
    elif kind == "tap":
        taps.append((int(f) / FPS, text))
hdr = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1280\nPlayResY: 720\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
       "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,"
       "Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
       "Style: Step,Noto Sans,20,&H00FFFFFF,&H00FFFFFF,&H00101010,&H99000000,-1,0,0,0,100,100,0,0,3,6,0,7,12,12,12,1\n"
       "Style: Tap,Noto Sans,17,&H0050E6FF,&H0050E6FF,&H00101010,&H99000000,0,0,0,0,100,100,0,0,3,5,0,1,12,12,40,1\n\n"
       "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
with open(out, "w", encoding="utf-8") as f:
    f.write(hdr)
    prev = 0.0
    for t, text in steps:
        if t <= prev + 0.05 or prev >= limit:
            continue
        f.write("Dialogue: 0,%s,%s,Step,,0,0,0,,Now: %s\n" % (ts(prev), ts(min(t, limit)), text.replace("{", "(")))
        prev = t
    for t, part in taps:
        if t < limit:
            f.write("Dialogue: 1,%s,%s,Tap,,0,0,0,,tap: %s\n" % (ts(t), ts(t + 0.7), part))
