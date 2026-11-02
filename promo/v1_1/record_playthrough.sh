#!/usr/bin/env bash
# Records the Chapter 2 playthrough (real taps, qa/playthrough_ch2_rec = playthrough_ch2 + step label/tap dots/markers)
# with Godot's movie writer under Xvfb.   usage: record_playthrough.sh <tag e.g. A> <seed> [WxH=1280x720]
# Output: $PROMO_WORK/rec_<tag>/{rec.avi,rec.log,markers.tsv,playthrough_ch2_report.txt}
set -u
TAG="$1"; SEED="$2"; RES="${3:-1280x720}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="${PROMO_WORK:-/tmp/promo_work}"
PG="$("$ROOT/promo/v1_1/make_scratch.sh" "rec_$TAG")"
OUT="$WORK/rec_$TAG"; rm -rf "$OUT"; mkdir -p "$OUT"
( cd "$PG" && godot --headless --path . --import > "$OUT/import.log" 2>&1 )
START=$(date +%s)
xvfb-run -a -s "-screen 0 ${RES}x24" godot --path "$PG" --write-movie "$OUT/rec.avi" --fixed-fps 30 --resolution "$RES" \
	res://qa/playthrough_ch2_rec.tscn -- --out="$OUT" --seed="$SEED" --no-continue > "$OUT/rec.log" 2>&1
echo "$(date -u +%FT%TZ) record_playthrough tag=$TAG seed=$SEED res=$RES rc=$? secs=$(( $(date +%s)-START ))" >> "$ROOT/promo/v1_1/render_log.txt"
