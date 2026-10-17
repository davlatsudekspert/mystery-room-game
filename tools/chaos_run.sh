#!/usr/bin/env bash
# One chaos-player run (game/qa/chaos.gd) with the log check, and the one summary line.
#
#   tools/chaos_run.sh --chapter=ch1|ch2|ch3|ch4 --seed=N [--steps=400] [--out=<dir>] [--log=<file>] [--warm=N] [--nudge=P] [--trace]
#
# The scene plays a chapter like a messy real player and prints its violations; this wrapper runs it through
# tools/qa_run.sh (Xvfb, software Vulkan, stall watchdog) and then reads the log for script errors: every
# "SCRIPT ERROR:" / "ERROR:" / "Parse Error:" block except the engine's own shutdown leak messages and the sound-card
# error of a container without audio. Last line (stdout):
#   chaos <chapter> seed <N>: steps S, taps T, item-in-hand taps H, violations V, script errors E
# Exit 0 only when V == 0 and E == 0.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG=""
ARGS=()
CHAPTER="?"
SEED="?"
for a in "$@"; do
	case "$a" in
		--log=*) LOG="${a#--log=}" ;;
		--chapter=*) CHAPTER="${a#--chapter=}"; ARGS+=("$a") ;;
		--seed=*) SEED="${a#--seed=}"; ARGS+=("$a") ;;
		*) ARGS+=("$a") ;;
	esac
done
[ "$CHAPTER" != "?" ] || { echo "usage: tools/chaos_run.sh --chapter=ch1|ch2|ch3|ch4 --seed=N [--steps=400] [--out=<dir>] [--log=<file>]" >&2; exit 2; }
LOG="${LOG:-$(mktemp /tmp/chaos.XXXXXX.log)}"

"$ROOT/tools/qa_run.sh" --stall="${CHAOS_STALL:-300}" --log="$LOG" -- res://qa/chaos.tscn -- "${ARGS[@]}" >&2
RC=$?

# error blocks of the log: a first line "SCRIPT ERROR: …" / "ERROR: …" with its indented "at:" / backtrace lines
ERRORS="$(awk '
	/^(SCRIPT ERROR|ERROR|USER ERROR|USER SCRIPT ERROR|Parse Error):/ { if (open) print blk; open = 1; blk = $0; next }
	open && /^[ \t]+(at:|GDScript backtrace|\[[0-9]+\])/ { blk = blk " | " $0; next }
	{ if (open) print blk; open = 0 }
	END { if (open) print blk }' "$LOG" |
	grep -vE 'ObjectDB instances were leaked|RID allocations|resources still in use at exit|Pages in use|Leaked instance|audio_driver_alsa|ERR_CANT_OPEN' || true)"
if [ -n "$ERRORS" ]; then E="$(printf '%s\n' "$ERRORS" | wc -l)"; else E=0; fi

grep -E '^VIOLATION ' "$LOG" >&2 || true
if [ "$E" -gt 0 ]; then
	echo "script errors in $LOG:" >&2
	printf '%s\n' "$ERRORS" | head -20 | cut -c1-400 >&2
fi

RES="$(grep -m1 '^CHAOS_RESULT ' "$LOG" || true)"
if [ -z "$RES" ]; then
	echo "chaos $CHAPTER seed $SEED: no result (the run ended before it finished, qa_run exit $RC), log $LOG" >&2
	echo "chaos $CHAPTER seed $SEED: steps 0, taps 0, item-in-hand taps 0, violations 1, script errors $E"
	exit 1
fi
field() { printf '%s\n' "$RES" | tr ' ' '\n' | sed -n "s/^$1=//p"; }
V="$(field violations)"
echo "chaos $(field chapter) seed $(field seed): steps $(field steps), taps $(field taps), item-in-hand taps $(field held), violations $V, script errors $E"
if [ "$RC" -eq 0 ] && [ "$V" -eq 0 ] && [ "$E" -eq 0 ]; then exit 0; fi
exit 1
