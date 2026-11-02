#!/usr/bin/env bash
# Builds the scratch Godot project used for the 1.1 recordings (no file of game/ is changed):
#   $PROMO_WORK/pg_<tag>: symlinks to everything in game/, except
#     project.godot  -> copy with the viewport set to the clip size (tag "WxH") or kept as is (tag "native")
#     qa/            -> real directory: symlinks to all game/qa files + the recorder scripts of promo/v1_1/godot/
# usage: make_scratch.sh <tag> [W H]
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="${PROMO_WORK:-/tmp/promo_work}"
TAG="$1"; PG="$WORK/pg_$TAG"
rm -rf "$PG"; mkdir -p "$PG/qa"
for f in $(ls -A "$ROOT/game"); do case "$f" in project.godot|qa) ;; *) ln -sfn "$ROOT/game/$f" "$PG/$f";; esac; done
for f in $(ls -A "$ROOT/game/qa"); do ln -sfn "$ROOT/game/qa/$f" "$PG/qa/$f"; done
if [ $# -ge 3 ]; then
	sed -e '/window_width_override/d' -e '/window_height_override/d' -e "s/^window\/size\/viewport_width=.*/window\/size\/viewport_width=$2/" -e "s/^window\/size\/viewport_height=.*/window\/size\/viewport_height=$3/" "$ROOT/game/project.godot" > "$PG/project.godot"
else
	cp "$ROOT/game/project.godot" "$PG/project.godot"
fi
printf '\n[editor]\n\nmovie_writer/mjpeg_quality=%s\n' "${MJPEG_Q:-0.5}" >> "$PG/project.godot"
# recorder scripts (real files, replacing a same-named symlink)
for f in "$ROOT"/promo/v1_1/godot/*; do rm -f "$PG/qa/$(basename "$f")"; cp "$f" "$PG/qa/"; done
echo "$PG"
# the recording copy of the Chapter 2 playthrough (label, tap dots, markers) and its scene
python3 "$ROOT/promo/v1_1/godot/make_rec.py" "$ROOT/game/qa/playthrough_ch2.gd" "$PG/qa/playthrough_ch2_rec.gd"
cat > "$PG/qa/playthrough_ch2_rec.tscn" <<'TSCN'
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://qa/playthrough_ch2_rec.gd" id="1"]

[node name="PlaythroughCh2Rec" type="Node"]
script = ExtResource("1")
TSCN
