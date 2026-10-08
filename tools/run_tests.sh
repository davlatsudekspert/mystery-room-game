#!/usr/bin/env bash
# Headless automated tests. Usage: tools/run_tests.sh [filter]
set -uo pipefail
cd "$(dirname "$0")/../game"
godot --headless --import >/tmp/godot_import.log 2>&1 || { echo "import failed"; tail -30 /tmp/godot_import.log; exit 1; }
args=()
[[ $# -gt 0 ]] && args=(-- "--filter=$1")
godot --headless res://tests/run_all.tscn "${args[@]}" 2>&1 | grep -vE "^(Godot Engine|Vulkan|OpenGL)" 
exit ${PIPESTATUS[0]}
