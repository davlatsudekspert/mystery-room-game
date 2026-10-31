#!/usr/bin/env bash
# Shorts cover (1080x1920) and YouTube thumbnail (1280x720) from real game frames (clips rendered by build_clips.sh).
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${PROMO_WORK:-/tmp/promo_work}"
CF="$ROOT/game/assets/fonts/CormorantGaramond-Bold.ttf"
NF="$ROOT/game/assets/fonts/NotoSans-Variable.ttf"
ffmpeg -v error -y -ss 6.0 -i "$WORK/clips/l_darkroom_P.mp4" -frames:v 1 "$WORK/cover_p.png"
ffmpeg -v error -y -ss 4.0 -i "$WORK/clips/l_darkroom_L.mp4" -frames:v 1 "$WORK/cover_l.png"
ffmpeg -v error -y -i "$WORK/cover_p.png" -vf "scale=1080:1920,eq=brightness=-0.12,drawbox=x=0:y=ih*0.55:w=iw:h=ih*0.45:color=black@0.55:t=fill,\
drawtext=fontfile=$CF:text='MYSTERY ROOM':fontsize=118:fontcolor=0xF4E9CC:borderw=5:bordercolor=0x101010:x=(w-text_w)/2:y=h*0.62,\
drawtext=fontfile=$CF:text='LOST INSTITUTE':fontsize=84:fontcolor=0xF4E9CC:borderw=4:bordercolor=0x101010:x=(w-text_w)/2:y=h*0.70,\
drawtext=fontfile=$NF:text='Chapters 1 and 2 are free':fontsize=44:fontcolor=white:borderw=4:bordercolor=0x101010:x=(w-text_w)/2:y=h*0.78" \
	-frames:v 1 "$ROOT/promo/shorts_cover_1080x1920.png"
ffmpeg -v error -y -i "$WORK/cover_l.png" -vf "scale=1280:720,eq=brightness=-0.1,drawbox=x=0:y=ih*0.58:w=iw:h=ih*0.42:color=black@0.55:t=fill,\
drawtext=fontfile=$CF:text='MYSTERY ROOM':fontsize=110:fontcolor=0xF4E9CC:borderw=5:bordercolor=0x101010:x=(w-text_w)/2:y=h*0.60,\
drawtext=fontfile=$CF:text='LOST INSTITUTE':fontsize=70:fontcolor=0xF4E9CC:borderw=4:bordercolor=0x101010:x=(w-text_w)/2:y=h*0.78" \
	-frames:v 1 "$ROOT/promo/youtube_thumbnail_1280x720.png"
