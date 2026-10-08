#!/usr/bin/env bash
# Rebuild every procedural model listed in tools/blender/build_lists/*.txt (one script name per line).
set -euo pipefail
cd "$(dirname "$0")/../.."
fail=0
for list in tools/blender/build_lists/*.txt; do
  while read -r script; do
    [[ -z "$script" || "$script" == \#* ]] && continue
    echo ">> $script"
    if ! blender -b --factory-startup -P "tools/blender/models/$script" -- --no-render > /tmp/blender_build.log 2>&1; then
      echo "FAILED: $script"; tail -20 /tmp/blender_build.log; fail=1
    fi
  done < "$list"
done
python3 tools/blender/check_glb_names.py || fail=1
exit $fail
