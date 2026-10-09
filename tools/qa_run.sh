#!/usr/bin/env bash
# Run a Godot QA scene under Xvfb with a watchdog.
#
# The container renders with software Vulkan (lavapipe) under Xvfb. Under heavy CPU load (several Blender builds at
# once) a run can deadlock inside the swapchain, or hang on exit after it has finished. Headless runs of the same
# scenes do not hang, so this is an environment issue, not a game bug. This wrapper:
#   - treats a "QA_DONE exit=N" line in the log as the result, even if the process then hangs on exit;
#   - kills a run whose log has not grown for STALL seconds and retries it (up to 3 attempts);
#   - runs at most QA_SLOTS (default 2) rendered runs at once across all callers (memory).
#
#   tools/qa_run.sh [--stall=180] [--log=<file>] -- res://qa/playthrough_ch2.tscn -- --out=<dir> --lens=take
set -u
STALL=180
LOG=""
while [ $# -gt 0 ]; do
	case "$1" in
		--stall=*) STALL="${1#--stall=}"; shift ;;
		--log=*) LOG="${1#--log=}"; shift ;;
		--) shift; break ;;
		*) echo "unknown option $1" >&2; exit 2 ;;
	esac
done
[ $# -gt 0 ] || { echo "usage: tools/qa_run.sh [--stall=S] [--log=F] -- <scene> [-- args]" >&2; exit 2; }
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="${LOG:-$(mktemp /tmp/qa_run.XXXXXX.log)}"

# A rendered Godot run takes 3–5 GB of RAM with the software renderer. Three or four at once got runs killed by
# the out-of-memory killer, so at most QA_SLOTS (default 2) run together; the others wait for a free slot.
# Waiting runs are served first come, first served: each takes a ticket, and only the oldest ticket may
# grab a free slot (otherwise a caller that runs back to back could take every freed slot).
SLOTS="${QA_SLOTS:-2}"
QDIR=/tmp/qa_render_queue
mkdir -p "$QDIR"
TICKET="$QDIR/$(date +%s%N).$$"
: > "$TICKET"
trap 'rm -f "$TICKET"' EXIT
exec 9>/dev/null
while true; do
	for t in "$QDIR"/*; do
		[ -e "$t" ] || continue
		kill -0 "${t##*.}" 2>/dev/null || rm -f "$t" # the caller died while waiting
	done
	if [ "$(ls "$QDIR" | sort | head -1)" = "$(basename "$TICKET")" ]; then
		for i in $(seq 0 $((SLOTS - 1))); do
			exec 9>"/tmp/qa_render_slot_$i.lock"
			if flock -n 9; then
				rm -f "$TICKET"
				break 2
			fi
		done
	fi
	sleep 3
done

for attempt in 1 2 3; do
	: > "$LOG"
	# 9>&-: only this script holds the slot lock; an Xvfb or Godot left behind by a killed run must not keep it
	xvfb-run -a godot --path "$ROOT/game" "$@" > "$LOG" 2>&1 9>&- &
	pid=$!
	last_size=-1
	still=0
	result=""
	while kill -0 "$pid" 2>/dev/null; do
		sleep 5
		if grep -q '^QA_DONE exit=' "$LOG"; then
			result=$(grep -m1 -o 'QA_DONE exit=[0-9]*' "$LOG" | cut -d= -f2)
			sleep 10 # give it a moment to exit by itself
			pkill -P "$pid" 2>/dev/null; kill "$pid" 2>/dev/null
			break
		fi
		size=$(stat -c %s "$LOG")
		if [ "$size" = "$last_size" ]; then
			still=$((still + 5))
		else
			still=0
			last_size=$size
		fi
		if [ "$still" -ge "$STALL" ]; then
			echo "qa_run: no output for ${STALL}s (attempt $attempt), restarting" >&2
			pkill -P "$pid" 2>/dev/null; kill "$pid" 2>/dev/null
			pkill -f "godot --path $ROOT/game $1" 2>/dev/null
			break
		fi
	done
	wait "$pid" 2>/dev/null
	rc=$?
	if [ -z "$result" ] && grep -q '^QA_DONE exit=' "$LOG"; then
		result=$(grep -m1 -o 'QA_DONE exit=[0-9]*' "$LOG" | cut -d= -f2)
	fi
	if [ -n "$result" ]; then
		echo "qa_run: finished (exit $result), log $LOG"
		exit "$result"
	fi
	if [ "$still" -lt "$STALL" ]; then
		echo "qa_run: godot exited with $rc before QA_DONE (crash or script error), log $LOG"
		exit 3
	fi
done
echo "qa_run: gave up after 3 stalled attempts, log $LOG"
exit 4
