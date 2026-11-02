#!/usr/bin/env python3
"""Owner review: side-by-side clip of the same puzzles in two games (seed A = 9137 left, seed B = 3 right), made from the real
game footage of build_compare.sh. The answers under each picture come from promo/v1_1/godot/seed_probe.gd (the logic's own
solution values for those seeds; `seed_probe_output.txt`). PRIVATE: it shows answers, it is not for YouTube.

  PROMO_WORK=/tmp/promo_work python3 promo/v1_1/build_compare.py
Output: promo/v1_1/OWNER_REVIEW_seed_comparison_A_vs_B.mp4 (1920x720, 30 fps, H.264 + the game's ambience of seed A's takes)
"""
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
WORK = os.environ.get("PROMO_WORK", "/tmp/promo_work")
CLIPS = os.path.join(WORK, "clips")
TMP = os.path.join(WORK, "build11", "cmp")
FONT = os.path.join(ROOT, "game", "assets", "fonts", "NotoSans-Variable.ttf")
os.makedirs(TMP, exist_ok=True)


def start_offset(clip):
    best = 37
    for line in open(os.path.join(HERE, "render_log.txt"), encoding="utf-8"):
        m = re.search(r"clip=%s .*start_frame=(\d+)" % re.escape(clip), line)
        if m:
            best = int(m.group(1))
    return best / 30.0 + 0.05


def esc(t):
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


# (clip base, offset after settling, duration, title, left line(s), right line(s)); values from seed_probe_output.txt
PUZ = [
    ("CMP_hall", 0.3, 4.0, "N1 Warm wall: the hidden panel", ["Panel letter: B"], ["Panel letter: A"]),
    ("CMP_pump", 0.5, 4.0, "N2 Pump Room: pipe graph on the manifold card", ["Open valves: 1 3 4 5"], ["Open valves: 1 2 3"]),
    ("CMP_cell", 0.8, 4.5, "N3 Night Cell: light table", ["Light digits: 1 1  (cold door)"], ["Light digits: 3 1  (cold door)"]),
    ("CMP_cold", 0.3, 3.2, "N4 Cold Store: carriages and cranks", ["Carriage start slots: 1 3 4 5 6"], ["Carriage start slots: 0 1 2 3 4"]),
    ("CMP_cold", 5.4, 3.2, "N4 Cold Store: plan plate (which carriage hides the chest)", ["Chest bay: 4"], ["Chest bay: 2"]),
    ("CMP_chest", 1.5, 3.2, "N6 Cold Store: chest rings", ["Signs 3 2 1, presses 1 1 4"], ["Signs 5 3 4, presses 2 0 5"]),
    ("CMP_office", 0.6, 4.5, "N10 Director's Office: cabinet", ["Cabinet code: 4 0 7 6"], ["Cabinet code: 6 5 3 7"]),
]
CODES = [("Chapter 1-2 codes (from the logic)", "Seed A 9137", "Seed B 3"),
         ("Booth dial (P8)", "743", "414"),
         ("Compressor valves (P2)", "1 0 2", "4 2 2"),
         ("Request card punch (P3)", "1 0 0 1 1 1 0 0", "0 1 0 1 0 0 1 1")]


def run(cmd):
    with open(os.path.join(HERE, "ffmpeg_log.txt"), "a") as f:
        f.write(" ".join(repr(c) if re.search(r"[ ;\[\]()|]", c) else c for c in cmd) + "\n\n")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def dt(text, x, y, size, color="white"):
    return "drawtext=fontfile='%s':text='%s':fontsize=%d:fontcolor=%s:x=%s:y=%s" % (FONT, esc(text), size, color, x, y)


def seg(i, base, off, d, title, left, right):
    out = os.path.join(TMP, "seg%d.mp4" % i)
    a, b = base + "_A", base + "_B"
    ins = ["-ss", "%.2f" % (start_offset(a) + off), "-t", "%.2f" % d, "-i", os.path.join(CLIPS, a + ".mp4"),
           "-ss", "%.2f" % (start_offset(b) + off), "-t", "%.2f" % d, "-i", os.path.join(CLIPS, b + ".mp4"),
           "-ss", "%.2f" % (start_offset(a) + off), "-t", "%.2f" % d, "-i", os.path.join(CLIPS, a + ".wav")]
    fg = ("[0:v]setpts=PTS-STARTPTS,scale=960:540,fps=30[l];[1:v]setpts=PTS-STARTPTS,scale=960:540,fps=30[r];[l][r]hstack=inputs=2[h];"
          "[h]pad=1920:720:0:64:color=0x141414,"
          + dt("SEED A (9137)", "20", "14", 30, "0xF4D58A") + ","
          + dt("SEED B (3)", "w-text_w-20", "14", 30, "0xF4D58A") + ","
          + dt(title, "(w-text_w)/2", "16", 28) + ","
          + dt(left[0], "20", "612", 44) + ","
          + dt(right[0], "980", "612", 44) + ","
          + "drawbox=x=958:y=64:w=4:h=656:color=0x141414:t=fill,format=yuv420p[v];"
          "[2:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=2.0,afade=t=in:d=0.2,afade=t=out:st=%.2f:d=0.2[a]" % (d - 0.2))
    run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", fg, "-map", "[v]", "-map", "[a]", "-r", "30", "-c:v", "libx264",
         "-crf", "20", "-preset", "medium", "-c:a", "aac", "-ar", "48000", "-ac", "2", "-t", "%.2f" % d, out])
    return out


def card(name, d, lines):
    out = os.path.join(TMP, name + ".mp4")
    chain = "color=c=0x141414:s=1920x720:r=30:d=%.1f,format=yuv420p" % d
    y = 120
    for i, (t, size, col) in enumerate(lines):
        chain += "," + dt(t, "(w-text_w)/2", str(y), size, col)
        y += size + 34
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", chain, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "%.1f" % d,
         "-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-shortest", out])
    return out


def main():
    parts = [card("intro", 3.5, [("Same chapter, different answers", 64, "white"), ("Seed A (9137) on the left, seed B (3) on the right", 40, "0xF4D58A"),
                                 ("Real game footage. Owner review only: answers are shown, not for YouTube.", 32, "0xBBBBBB")])]
    for i, p in enumerate(PUZ):
        parts.append(seg(i, *p))
    lines = [(CODES[0][0], 52, "white")] + [("%s:   %s    |    %s" % c, 44, "0xF4D58A") for c in CODES[1:]]
    parts.append(card("codes", 4.5, lines))
    lst = os.path.join(TMP, "list.txt")
    open(lst, "w").write("".join("file '%s'\n" % p for p in parts))
    final = os.path.join(HERE, "OWNER_REVIEW_seed_comparison_A_vs_B.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-crf", "21", "-preset", "slow", "-pix_fmt", "yuv420p",
         "-r", "30", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-movflags", "+faststart", final])
    print(final)


if __name__ == "__main__":
    main()
