#!/usr/bin/env bash
# Render one real-game clip with Godot's movie writer (software Vulkan under Xvfb) and re-encode it losslessly-ish.
#   promo/render_clip.sh <name> <WxH> <room lab|archive> <prep> "<steps>" [extra capture args...]
# Output: $PROMO_WORK/clips/<name>.mp4 (H.264 crf 12, 30 fps, no audio). The command line is appended to promo/render_log.txt.
set -u
NAME="$1"; RES="$2"; ROOM="$3"; PREP="$4"; STEPS="$5"; shift 5
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${PROMO_WORK:-/tmp/promo_work}"
mkdir -p "$WORK/clips" "$WORK/avi"
# Scratch copy of the project dir: symlinks to game/, but project.godot without the 1280x720 window override
# and with the viewport size set to the clip size (the movie writer records the project viewport size). No game file is changed.
W="${RES%x*}"; H="${RES#*x}"
PG="$WORK/pg_${W}x${H}"
if [ ! -d "$PG" ]; then
	mkdir -p "$PG"
	for f in $(ls -A "$ROOT/game"); do [ "$f" = project.godot ] || ln -sfn "$ROOT/game/$f" "$PG/$f"; done
	sed -e '/window_width_override/d' -e '/window_height_override/d' -e "s/^window\/size\/viewport_width=.*/window\/size\/viewport_width=$W/" -e "s/^window\/size\/viewport_height=.*/window\/size\/viewport_height=$H/" "$ROOT/game/project.godot" > "$PG/project.godot"
	# smaller MJPEG intermediate (the disk of the build container is small)
	printf '\n[editor]\n\nmovie_writer/mjpeg_quality=0.6\n' >> "$PG/project.godot"
fi
AVI="$WORK/avi/$NAME.avi"
START=$(date +%s)
xvfb-run -a -s "-screen 0 ${W}x${H}x24" godot --path "$PG" --write-movie "$AVI" --fixed-fps 30 --resolution "$RES" \
	res://qa/promo_capture.tscn -- --room="$ROOM" --prep="$PREP" --steps="$STEPS" "$@" > "$WORK/avi/$NAME.log" 2>&1
RC=$?
ffmpeg -v error -y -i "$AVI" -c:v libx264 -crf 12 -preset fast -pix_fmt yuv420p -r 30 "$WORK/clips/$NAME.mp4"
RC2=$?
rm -f "$AVI"
echo "$(date -u +%FT%TZ) clip=$NAME res=$RES room=$ROOM prep=$PREP extra=[$*] godot_rc=$RC enc_rc=$RC2 secs=$(( $(date +%s)-START )) steps=[$STEPS]" >> "$ROOT/promo/render_log.txt"
grep -c PROMO_DONE "$WORK/avi/$NAME.log"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$WORK/clips/$NAME.mp4"
