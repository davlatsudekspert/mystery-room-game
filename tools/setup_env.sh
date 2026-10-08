#!/usr/bin/env bash
# Reproducibly installs the free toolchain into a fresh (ephemeral) Linux container.
# Idempotent: re-running skips what is already present.
set -euo pipefail
GODOT_VER="4.7.2"
BLENDER_VER="5.2.2"
TOOLS=/opt/tools
mkdir -p "$TOOLS"

if ! command -v godot >/dev/null || [[ "$(godot --headless --version 2>/dev/null)" != ${GODOT_VER}* ]]; then
  echo ">> Godot $GODOT_VER"
  curl -sSL -o /tmp/godot.zip "https://github.com/godotengine/godot/releases/download/${GODOT_VER}-stable/Godot_v${GODOT_VER}-stable_linux.x86_64.zip"
  unzip -oq /tmp/godot.zip -d "$TOOLS" && rm /tmp/godot.zip
  ln -sf "$TOOLS/Godot_v${GODOT_VER}-stable_linux.x86_64" /usr/local/bin/godot
fi

TPL="$HOME/.local/share/godot/export_templates/${GODOT_VER}.stable"
if [[ ! -f "$TPL/version.txt" ]]; then
  echo ">> Godot export templates (Android, iOS, Web, Linux)"
  mkdir -p "$TPL"
  curl -sSL -o /tmp/tpl.tpz "https://github.com/godotengine/godot/releases/download/${GODOT_VER}-stable/Godot_v${GODOT_VER}-stable_export_templates.tpz"
  unzip -oq -j /tmp/tpl.tpz templates/android_debug.apk templates/android_release.apk templates/android_source.zip \
    templates/ios.zip templates/version.txt templates/icudt_godot.dat templates/web_nothreads_release.zip \
    templates/web_nothreads_debug.zip templates/linux_release.x86_64 templates/linux_debug.x86_64 -d "$TPL"
  rm /tmp/tpl.tpz
fi

if [[ ! -x "$TOOLS/blender-${BLENDER_VER}-linux-x64/blender" ]]; then
  echo ">> Blender $BLENDER_VER"
  curl -sSL "https://download.blender.org/release/Blender${BLENDER_VER%.*}/blender-${BLENDER_VER}-linux-x64.tar.xz" | tar -xJ -C "$TOOLS"
fi
ln -sf "$TOOLS/blender-${BLENDER_VER}-linux-x64/blender" /usr/local/bin/blender

if ! command -v inkscape >/dev/null || ! command -v sox >/dev/null || [[ ! -f /usr/share/vulkan/icd.d/lvp_icd.json ]]; then
  echo ">> apt: lavapipe Vulkan, Inkscape, SoX, fonttools"
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq mesa-vulkan-drivers mesa-utils vulkan-tools inkscape sox >/dev/null
fi
python3 -c "import fontTools" 2>/dev/null || pip3 install -q fonttools

echo "Toolchain ready:"
godot --headless --version
blender --version | head -1
