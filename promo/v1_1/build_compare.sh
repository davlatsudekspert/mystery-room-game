#!/usr/bin/env bash
# Renders the source clips of the seed comparison (owner review): the same puzzle views of two games, seed A = 9137 and seed B = 3
# (chosen so that the panel letter, pipe graph, light-table digits, carriage order, chest rings and cabinet code all differ).
#   PROMO_WORK=/tmp/promo_work promo/v1_1/build_compare.sh [name ...]
# Job: name | WxH | seed | until | start room | steps | extra args.
set -u
cd "$(dirname "$0")"
JOBS=$(cat <<'JOBS_EOF'
CMP_hall_A|960x540|9137|-|hall|go:east_panel_b;wait:4|--hud=0 --music=0
CMP_hall_B|960x540|3|-|hall|go:east_panel_a;wait:4|--hud=0 --music=0
CMP_pump_A|960x540|9137|pump_open|pump|go:manifold;wait:4.5|--hud=0 --music=0
CMP_pump_B|960x540|3|pump_open|pump|go:manifold;wait:4.5|--hud=0 --music=0
CMP_cell_A|960x540|9137|pump_open|cell|go:light_table;wait:5|--hud=0 --music=0
CMP_cell_B|960x540|3|pump_open|cell|go:light_table;wait:5|--hud=0 --music=0
CMP_cold_A|960x540|9137|cold_open|cold|go:cranks;wait:4;go:cold_plate;wait:4;go:chest;wait:4|--hud=0 --music=0
CMP_cold_B|960x540|3|cold_open|cold|go:cranks;wait:4;go:cold_plate;wait:4;go:chest;wait:4|--hud=0 --music=0
CMP_office_A|960x540|9137|pass_key|office|go:cabinet;wait:5|--hud=0 --music=0
CMP_office_B|960x540|3|pass_key|office|go:cabinet;wait:5|--hud=0 --music=0
CMP_chest_A|960x540|9137|aisle|cold|go:chest;wait:4.5|--hud=0 --music=0
CMP_chest_B|960x540|3|aisle|cold|go:chest;wait:4.5|--hud=0 --music=0
JOBS_EOF
)
run() { IFS='|' read -r name res seed until room steps extra <<< "$1"; ./render_clip.sh "$name" "$res" "$seed" "$until" "$room" "$steps" $extra > /dev/null; }
export -f run
if [ $# -gt 0 ]; then
	for n in "$@"; do echo "$JOBS" | grep "^$n|"; done
else
	echo "$JOBS"
fi | xargs -P ${PAR:-1} -I{} bash -c 'run "$1"' _ {}
