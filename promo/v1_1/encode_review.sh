#!/usr/bin/env bash
# Owner review video: the recorded Chapter 2 playthrough (seed A = 9137), 1280x720 30 fps H.264 + the game's audio (AAC).
# The step label (top left) and the tap captions (bottom left) are burned in from the recorder's markers (review_labels.py).
# The recording is cut at 450 s: the chapter-complete card at 443.9 s is the last thing shown; the cliffhanger / next-chapter card
# after it (443.9-511 s) is left out on purpose (Chapters 3-4 are not released).
#   PROMO_WORK=/tmp/promo_work promo/v1_1/encode_review.sh
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="${PROMO_WORK:-/tmp/promo_work}"
python3 "$ROOT/promo/v1_1/review_labels.py" "$WORK/rec_A/markers.tsv" "$WORK/review.ass" 450
ffmpeg -v error -y -i "$WORK/rec_A/rec.avi" -t 450 -vf "ass=$WORK/review.ass:fontsdir=$ROOT/game/assets/fonts" -c:v libx264 -preset slow -crf 24 -maxrate 3500k -bufsize 7M -pix_fmt yuv420p -r 30 \
	-af "loudnorm=I=-18:TP=-1.5:LRA=11" -c:a aac -b:a 128k -ar 48000 -movflags +faststart "$ROOT/promo/v1_1/OWNER_REVIEW_chapter2_full_seedA_1280x720.mp4"
cp "$WORK/rec_A/markers.tsv" "$ROOT/promo/v1_1/review_markers_seedA.tsv"
cp "$WORK/rec_A/playthrough_ch2_report.txt" "$ROOT/promo/v1_1/review_report_seedA.txt"
