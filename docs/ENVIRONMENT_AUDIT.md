# Environment Audit — 2026-10-08

Development runs in an **ephemeral cloud container** (Claude Code on the web). Anything not pushed to GitHub is lost when the container is recycled, so `tools/setup_env.sh` re-installs every tool reproducibly.

## Isolation
- This repository (`davlatsudekspert/mystery-room-game`, private) is cloned at `/home/user/mystery-room-game`.
- The unrelated production project NFCSTORE (`/home/user/nfcx`) is **never read, modified, built or deployed** by this project.
- Verified at session start: `git status --porcelain --ignored` in NFCSTORE is empty, and HEAD is unchanged at `684fb4f`.
- No secrets, env vars, workflows or configs were copied from NFCSTORE.

## System
| Item | Value |
|---|---|
| OS | Ubuntu 24.04.5 LTS, Linux 6.18 x86_64 |
| CPU / RAM | 4 vCPU / 15 GiB |
| GPU | none, uses Mesa **llvmpipe** (OpenGL) and **lavapipe** (Vulkan 1.4) software rasterizers |
| Display | Xvfb (virtual framebuffer) for runtime screenshots |

## Tools (all free)
| Tool | Version | Install method | Status |
|---|---|---|---|
| Godot | 4.7.2-stable (official) | GitHub release zip → `/opt/tools` | ✅ installed, `godot --version` OK |
| Godot export templates | 4.7.2 (Android, iOS, Web no-threads, Linux) | official `.tpz` | ✅ installed |
| Blender | 5.2.2 LTS | download.blender.org tarball → `/opt/tools` | ✅ installed, `blender --version` OK |
| Inkscape | 1.2.2 | apt | ✅ (SVG → PNG for logo/icons) |
| ImageMagick | 6.9.12 | preinstalled | ✅ |
| FFmpeg | 6.1.1 | preinstalled | ✅ (WAV → OGG Vorbis) |
| SoX | 14.4.2 | apt | ✅ |
| Python | 3.13 + numpy + Pillow | preinstalled | ✅ (texture and audio synthesis) |
| Java | OpenJDK 21 | preinstalled | ✅ (Android signing/Gradle) |
| Mesa Vulkan (lavapipe) | 25.2.8 | apt | ✅ |
| Krita / GIMP / Audacity | — | not installed | ⚠️ GUI-only tools with no automation value here; replaced by Python (Pillow/numpy), ImageMagick, Inkscape CLI and SoX/FFmpeg |
| Canva | Connector exposed in this session | — | ⏸ Not used yet. If it is used for store graphics (Phase 8), that will be recorded here. Logo/UI are produced with Inkscape (SVG) |
| Android SDK | — | to be installed in Phase 6 (dl.google.com reachable) | ⏳ |
| Xcode / macOS | — | **not available** (Linux container) | ❌ iOS builds cannot be compiled or verified here. Only the project and export preset are prepared |

## Network reachability (verified)
`github.com` releases ✅ · `download.blender.org` ✅ · `ambientcg.com` ✅ · `api.polyhaven.com` ✅ · `raw.githubusercontent.com` (Google Fonts) ✅ · `dl.google.com` ✅ · `services.gradle.org` ✅ · `repo.maven.apache.org` ✅ · `kenney.nl` ✅

## Limitations (stated honestly)
- **No GPU:** visual QA screenshots are rendered with software Vulkan, so they are visually accurate but slow. FPS numbers measured here are **not** representative of phones.
- **No physical Android device or emulator acceleration (KVM):** APKs can be built and inspected, but on-device testing needs the owner's phone.
- **No macOS:** iOS work is limited to configuration and docs.
