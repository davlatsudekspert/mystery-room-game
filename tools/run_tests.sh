#!/usr/bin/env bash
# Headless automated tests. Usage: tools/run_tests.sh [filter]
set -uo pipefail
cd "$(dirname "$0")/.."
python3 tools/blender/check_glb_names.py || exit 1
cd game
godot --headless --import >/tmp/godot_import.log 2>&1 || { echo "import failed"; tail -30 /tmp/godot_import.log; exit 1; }
args=()
[[ $# -gt 0 ]] && args=(-- "--filter=$1")
# a hung test (an await that never resolves) must fail the run, not block every agent that runs the suite
timeout "${MR_TEST_TIMEOUT:-600}" godot --headless res://tests/run_all.tscn "${args[@]}" 2>&1 | grep -vE "^(Godot Engine|Vulkan|OpenGL)"
status=${PIPESTATUS[0]}
[[ $status -eq 124 ]] && echo "TIMEOUT: the test run did not finish within ${MR_TEST_TIMEOUT:-600} s (a test is hung; see its last lines above)"
exit $status
