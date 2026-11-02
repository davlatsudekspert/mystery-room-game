#!/usr/bin/env bash
# YouTube thumbnail (1280x720) and Shorts cover (1080x1920): a real game frame (from the rendered clips) + a large title.
#   PROMO_WORK=/tmp/promo_work promo/v1_1/build_covers.sh
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="${PROMO_WORK:-/tmp/promo_work}"
F="$ROOT/game/assets/fonts/CormorantGaramond-Bold.ttf"; N="$ROOT/game/assets/fonts/NotoSans-Variable.ttf"
OUT="$ROOT/promo/v1_1"
# frame: the frost window with the silhouette (L_frost, 6.5 s) / the Cold Store (P_cold_walk, 5.6 s)
ffmpeg -v error -y -ss 6.5 -i "$WORK/clips/L_frost.mp4" -frames:v 1 "$WORK/cover_l.png"
ffmpeg -v error -y -ss 5.6 -i "$WORK/clips/P_cold_walk.mp4" -frames:v 1 "$WORK/cover_p.png"
ffmpeg -v error -y -i "$WORK/cover_l.png" -vf "scale=1280:720,\
drawbox=x=0:y=0:w=iw:h=250:color=black@0.62:t=fill,drawbox=x=0:y=h-150:w=iw:h=150:color=black@0.62:t=fill,\
drawtext=fontfile='$F':text='NEW FLOORS':fontsize=170:fontcolor=0xF4E9CC:borderw=6:bordercolor=0x101010:x=(w-text_w)/2:y=34,\
drawtext=fontfile='$F':text='MYSTERY ROOM\: LOST INSTITUTE':fontsize=74:fontcolor=0xF4E9CC:borderw=5:bordercolor=0x101010:x=(w-text_w)/2:y=h-128,\
drawtext=fontfile='$N':text='Version 1.1  -  Chapter 2':fontsize=38:fontcolor=white:borderw=4:bordercolor=0x101010:x=w-text_w-30:y=h-190" \
	-frames:v 1 "$OUT/youtube_thumbnail_1280x720.png"
ffmpeg -v error -y -i "$WORK/cover_p.png" -vf "scale=1080:1920,\
drawbox=x=0:y=0:w=iw:h=560:color=black@0.62:t=fill,drawbox=x=0:y=h-330:w=iw:h=330:color=black@0.62:t=fill,\
drawtext=fontfile='$F':text='NEW FLOORS':fontsize=150:fontcolor=0xF4E9CC:borderw=7:bordercolor=0x101010:x=(w-text_w)/2:y=110,\
drawtext=fontfile='$F':text='Three floors. Seven rooms.':fontsize=64:fontcolor=white:borderw=5:bordercolor=0x101010:x=(w-text_w)/2:y=380,\
drawtext=fontfile='$F':text='MYSTERY ROOM':fontsize=130:fontcolor=0xF4E9CC:borderw=6:bordercolor=0x101010:x=(w-text_w)/2:y=h-290,\
drawtext=fontfile='$F':text='LOST INSTITUTE':fontsize=96:fontcolor=0xF4E9CC:borderw=5:bordercolor=0x101010:x=(w-text_w)/2:y=h-150" \
	-frames:v 1 "$OUT/shorts_cover_1080x1920.png"
