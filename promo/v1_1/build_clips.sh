#!/usr/bin/env bash
# Renders the source clips of the 1.1 trailer / Short / comparison from the real game (see README.md for the list).
#   PROMO_WORK=/tmp/promo_work promo/v1_1/build_clips.sh [name ...]      (no names = all, one render at a time)
# Job: name | WxH | seed | until (solver state key, "-" = new game) | start room | steps | extra args.  Steps: godot/promo_ch2.gd.
# The first ~1.2 s of a clip is the scene settling (the log's start_frame says how long); build_videos.py trims it.
set -u
cd "$(dirname "$0")"
JOBS=$(cat <<'JOBS_EOF'
L_hall|1920x1080|9137|-|hall|wait:0.4;yaw:-40:7;wait:7.4|--hud=0 --music=0
L_plan|1920x1080|9137|pump_open|hall|wait:0.4;yaw:25:3;wait:3;seen;hud:on;plan;wait:5|--hud=0 --music=0
L_door|1920x1080|9137|pump_open|hall|go:east_south;wait:1.6;tap:service_door:IA_service_door;waitroom:pump:10;wait:3|--hud=0 --music=0
L_pump|1920x1080|9137|pump_open|pump|wait:0.6;go:pipes;wait:3;go:manifold;wait:3.2;go:cell_door;wait:6|--hud=0 --music=0
L_cell|1920x1080|9137|pump_open|cell|wait:0.8;yaw:-30:4;go:light_table;wait:4.5;go:cold_door;wait:2.5|--hud=0 --music=0
L_cold_walk|1920x1080|9137|cold_open|cell|go:cold_door;wait:1.6;tapat:cell:2.15,1.0,0.0;waitroom:cold:10;wait:3;go:cranks;wait:3.5|--hud=0 --music=0
L_frost|1920x1080|9137|aisle|cold|logic:take:cell_cloth;go:frost;wait:2.5;wipe;wait:5.5|--hud=0 --music=0
L_lift|1920x1080|9137|thawed|pump|go:lift_door;wait:2.5;go:lift_weights;wait:3.5;go:lift_panel;wait:2.5|--hud=0 --music=0
L_gallery|1920x1080|9137|lift_ok|gallery|wait:1;go:gallery;wait:3;go:board;wait:3.5;go:balcony;wait:3|--hud=0 --music=0
L_door2|1920x1080|9137|lift_ok|gallery|go:gallery;wait:1.5;tap:gallery_room_gallery:IA_door_plate;waitroom:plate:8;wait:2.5|--hud=0 --music=0
L_plate|1920x1080|9137|lift_ok|plate|wait:1;go:enlarger;wait:3.5;go:trays;wait:3|--hud=0 --music=0
L_office|1920x1080|9137|pass_key|office|wait:1;yaw:25:4;go:cabinet;wait:3.5;go:office_desk;wait:3|--hud=0 --music=0
P_hall|1080x1920|9137|-|hall|keep:width;wait:0.4;yaw:-40:5;wait:5.6|--hud=0 --music=0
P_door|1080x1920|9137|pump_open|hall|keep:width;go:east_south;wait:1.6;tap:service_door:IA_service_door;waitroom:pump:10;wait:3|--hud=0 --music=0
P_pump|1080x1920|9137|pump_open|pump|keep:width;wait:0.8;go:pump;wait:1.5;keep:height;go:manifold;wait:3.5|--hud=0 --music=0
P_cell|1080x1920|9137|pump_open|cell|keep:width;wait:0.8;yaw:-30:3;wait:1;keep:height;go:light_table;wait:4|--hud=0 --music=0
P_cold_walk|1080x1920|9137|cold_open|cell|keep:width;go:cold_door;wait:1.6;tapat:cell:2.15,1.0,0.0;waitroom:cold:10;wait:3.5|--hud=0 --music=0
P_gallery|1080x1920|9137|lift_ok|gallery|keep:width;wait:1;go:board;wait:3;go:balcony;wait:2.5|--hud=0 --music=0
P_plate|1080x1920|9137|lift_ok|plate|keep:width;wait:1;keep:height;go:enlarger;wait:3.5|--hud=0 --music=0
JOBS_EOF
)
run() { IFS='|' read -r name res seed until room steps extra <<< "$1"; ./render_clip.sh "$name" "$res" "$seed" "$until" "$room" "$steps" $extra > /dev/null; }
export -f run
if [ $# -gt 0 ]; then
	for n in "$@"; do echo "$JOBS" | grep "^$n|"; done
else
	echo "$JOBS"
fi | xargs -P ${PAR:-1} -I{} bash -c 'run "$1"' _ {}
