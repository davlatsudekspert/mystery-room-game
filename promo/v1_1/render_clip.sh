#!/usr/bin/env bash
# Renders one clip of the 1.1 promo with qa/promo_ch2.tscn (movie writer, software Vulkan under Xvfb) and re-encodes it.
#   render_clip.sh <name> <WxH> <seed> <until|-> <room> "<steps>" [extra capture args]
# Output: $PROMO_WORK/clips/<name>.mp4 (H.264 crf 14, 30 fps, no audio) and <name>.wav (the game's audio of the take); the settling
# frames at the start are NOT trimmed here (start_frame in the log says how many).
# The command is appended to promo/v1_1/render_log.txt.
set -u
NAME="$1"; RES="$2"; SEED="$3"; UNTIL="$4"; ROOM="$5"; STEPS="$6"; shift 6
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="${PROMO_WORK:-/tmp/promo_work}"
W="${RES%x*}"; H="${RES#*x}"
PG="$WORK/pg_clip_${W}x${H}"
[ -d "$PG" ] || "$ROOT/promo/v1_1/make_scratch.sh" "clip_${W}x${H}" "$W" "$H" > /dev/null
mkdir -p "$WORK/clips" "$WORK/avi"
cp "$ROOT"/promo/v1_1/godot/promo_ch2.gd "$ROOT"/promo/v1_1/godot/promo_ch2.tscn "$PG/qa/"
[ -f "$PG/.imported" ] || { ( cd "$PG" && godot --headless --path . --import > "$WORK/avi/import_${W}x${H}.log" 2>&1 ); touch "$PG/.imported"; }
AVI="$WORK/avi/$NAME.avi"
U=""; [ "$UNTIL" = "-" ] || U="--until=$UNTIL"
START=$(date +%s)
xvfb-run -a -s "-screen 0 ${W}x${H}x24" godot --path "$PG" --write-movie "$AVI" --fixed-fps 30 --resolution "$RES" \
	res://qa/promo_ch2.tscn -- --seed="$SEED" $U --room="$ROOM" --steps="$STEPS" "$@" > "$WORK/avi/$NAME.log" 2>&1
RC=$?
S=$(grep -o "PROMO_START frame=[0-9]*" "$WORK/avi/$NAME.log" | head -1 | cut -d= -f2)
ffmpeg -v error -y -i "$AVI" -c:v libx264 -crf 14 -preset fast -pix_fmt yuv420p -r 30 "$WORK/clips/$NAME.mp4"
RC2=$?
# the game's own audio of the take (ambience, music, effects as the game played them), same timeline as the video
ffmpeg -v error -y -i "$AVI" -vn -c:a pcm_s16le "$WORK/clips/$NAME.wav"
rm -f "$AVI"
echo "$(date -u +%FT%TZ) clip=$NAME res=$RES seed=$SEED until=$UNTIL room=$ROOM extra=[$*] godot_rc=$RC enc_rc=$RC2 start_frame=$S secs=$(( $(date +%s)-START )) steps=[$STEPS]" >> "$ROOT/promo/v1_1/render_log.txt"
grep -c PROMO_DONE "$WORK/avi/$NAME.log"
echo "start_frame=$S"; ffprobe -v error -show_entries format=duration -of csv=p=0 "$WORK/clips/$NAME.mp4"
