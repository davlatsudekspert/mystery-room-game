#!/usr/bin/env bash
# Renders every source clip of the promo videos from the real game (see promo/README.md for the list).
#   PROMO_WORK=/tmp/promo_work promo/build_clips.sh [name ...]   (no names = all; 2 renders run in parallel)
# Each job: name | WxH | room | prep | steps | extra args. The first second of each clip is the scene settling: trim it.
set -u
cd "$(dirname "$0")"
L=1920x1080; P=1080x1920
JOBS=$(cat <<'JOBS_EOF'
a_finale_L|1920x1080|archive|archive:vault_unlocked|go:vault;wait:2;turnwheel:0;waitview:vault_reel:15;wait:6;waitoverlay:25;choose;waitview:shaft:12;wait:11|--hud=0
a_finale_P|1080x1920|archive|archive:vault_unlocked|go:vault;wait:2;turnwheel:0;waitview:vault_reel:15;wait:6;waitoverlay:25;choose;waitview:shaft:12;wait:11|--hud=0
l_dark_L|1920x1080|lab|lab:1|wait:0.5;yaw:-40:6;wait:6.5|--hud=0
l_drawer_L|1920x1080|lab|lab:1|go:drawer;wait:1.5;logic:step_drawer_wheel:1:1;wait:0.7;logic:step_drawer_wheel:2:1;wait:0.7;logic:step_drawer_wheel:2:1;wait:1.5|--hud=0
l_gearbox_L|1920x1080|lab|lab:1|go:gearbox;wait:1.5;logic:press_gear:0;wait:0.8;logic:press_gear:1;wait:0.8;logic:press_gear:0;wait:1.5|--hud=0
l_uv_L|1920x1080|lab|lab:40|hud:on;notebook:4;wait:1.5;uvbtn;wait:4.5|--hud=0
l_panel_L|1920x1080|lab|lab:6|go:panel;wait:1.5;logic:toggle_switch:0;wait:0.8;logic:toggle_switch:2;wait:0.8;logic:toggle_switch:3;wait:2|--hud=0
l_powered_L|1920x1080|lab|lab:7|wait:0.5;yaw:35:5;wait:5.5;go:radio;wait:3|--hud=0
l_darkroom_L|1920x1080|lab|lab:10|go:darkroom;wait:0.5;yaw:25:5;wait:5.5;go:evidence;wait:3|--hud=0
l_beam_L|1920x1080|lab|lab:12|wait:0.5;yaw:30:4;wait:5|--hud=0
a_hall_L|1920x1080|archive|archive:none|wait:0.5;yaw:-40:6;wait:6.5|--hud=0
a_catalogue_L|1920x1080|archive|archive:none|go:catalogue;wait:2;go:cat_drawer;wait:2.5|--hud=0
a_compressor_L|1920x1080|archive|archive:none|go:compressor;wait:2.5;go:station;wait:2|--hud=0
a_deck_L|1920x1080|archive|archive:none|go:desk;wait:1.5;go:deck;wait:3|--hud=0
l_dark_P|1080x1920|lab|lab:1|keep:width;wait:0.5;yaw:-45:7;wait:7.5|--hud=0
l_drawer_P|1080x1920|lab|lab:1|go:drawer;wait:1.5;logic:step_drawer_wheel:1:1;wait:0.7;logic:step_drawer_wheel:2:1;wait:0.7;logic:step_drawer_wheel:2:1;wait:1.5|--hud=0
l_uv_P|1080x1920|lab|lab:40|hud:on;notebook:4;wait:1.5;uvbtn;wait:4.5|--hud=0
l_panel_P|1080x1920|lab|lab:6|go:panel;wait:1.5;logic:toggle_switch:0;wait:0.8;logic:toggle_switch:2;wait:0.8;logic:toggle_switch:3;wait:2|--hud=0
l_darkroom_P|1080x1920|lab|lab:10|keep:width;go:darkroom;wait:0.5;yaw:25:5;wait:5.5;keep:height;go:evidence;wait:3|--hud=0
l_beam_P|1080x1920|lab|lab:12|keep:width;wait:0.5;yaw:30:4;wait:5|--hud=0
a_hall_P|1080x1920|archive|archive:none|keep:width;wait:0.5;yaw:-40:7;wait:7.5|--hud=0
a_deck_P|1080x1920|archive|archive:none|go:station;wait:1.5;go:deck;wait:3.5|--hud=0
JOBS_EOF
)
run() { IFS='|' read -r name res room prep steps extra <<< "$1"; ./render_clip.sh "$name" "$res" "$room" "$prep" "$steps" $extra > /dev/null; }
export -f run
if [ $# -gt 0 ]; then
	for n in "$@"; do echo "$JOBS" | grep "^$n|"; done
else
	echo "$JOBS"
fi | xargs -P ${PAR:-1} -I{} bash -c 'run "$1"' _ {}
