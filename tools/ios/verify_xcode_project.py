#!/usr/bin/env python3
"""Static checks of the Xcode project that Godot exports for iOS (runs on Linux, no Xcode needed).

Usage: verify_xcode_project.py <export dir> --bundle-id ID --version 0.1.0 --build 12 [--team-env IOS_TEAM_ID]

Checks what App Store Connect validation rejects or what TestFlight asks about:
bundle id / version / build number / team / automatic signing in project.pbxproj, the shared scheme,
Info.plist keys (export compliance, full screen on iPad, landscape, launch storyboard, non-empty purpose
strings), localized InfoPlist.strings, the privacy manifest and its Resources entry, and icons without
alpha. The team id is compared with the env var, never printed. Exit 1 on any failure.
"""
from __future__ import annotations

import argparse
import json
import mmap
import os
import plistlib
import re
import struct
import sys
from pathlib import Path

FAIL: list[str] = []


def ok(cond: bool, what: str) -> None:
	print(("  ok    " if cond else "  FAIL  ") + what)
	if not cond:
		FAIL.append(what)


def png_info(path: Path) -> tuple[int, int, int, bool]:
	"""(width, height, color type, has tRNS) from the PNG header, without third-party modules."""
	data = path.read_bytes()
	if data[:8] != b"\x89PNG\r\n\x1a\n":
		raise ValueError("not a PNG")
	w, h, _depth, ctype = struct.unpack(">IIBB", data[16:26])
	return w, h, ctype, b"tRNS" in data[: data.find(b"IDAT")]


def build_settings(pbx: str, config: str) -> dict[str, str]:
	"""Build settings of the target's configuration (the block that sets PRODUCT_BUNDLE_IDENTIFIER)."""
	for m in re.finditer(r"/\* (\w+) \*/ = \{\s*isa = XCBuildConfiguration;\s*buildSettings = \{(.*?)\n\t\t\t\};", pbx, re.S):
		if m.group(1) == config and "PRODUCT_BUNDLE_IDENTIFIER" in m.group(2):
			return {k: v.strip().strip('"') for k, v in re.findall(r"^\s*([A-Za-z_\[\]=*]+) = (.*?);\s*$", m.group(2), re.M)}
	return {}


def main() -> int:
	ap = argparse.ArgumentParser()
	ap.add_argument("export_dir")
	ap.add_argument("--name", default="MysteryRoom")
	ap.add_argument("--bundle-id", required=True)
	ap.add_argument("--version", required=True, help="CFBundleShortVersionString")
	ap.add_argument("--build", required=True, help="CFBundleVersion")
	ap.add_argument("--team-env", default="IOS_TEAM_ID", help="env var holding the expected team id")
	ap.add_argument("--custom-features", default="", help="comma list expected in the pck's project settings ('' = none)")
	a = ap.parse_args()
	root, n = Path(a.export_dir), a.name

	print("Xcode project files")
	pbx_path = root / f"{n}.xcodeproj/project.pbxproj"
	scheme = root / f"{n}.xcodeproj/xcshareddata/xcschemes/{n}.xcscheme"
	for p in (pbx_path, scheme, root / f"{n}.pck", root / f"{n}.xcframework", root / "PrivacyInfo.xcprivacy",
			root / n / f"{n}-Info.plist", root / n / "Launch Screen.storyboard", root / n / "Images.xcassets/AppIcon.appiconset/Contents.json"):
		ok(p.exists(), f"{p.relative_to(root)} exists")
	if FAIL:
		return 1
	pck_mb = (root / f"{n}.pck").stat().st_size / 1e6
	ok(pck_mb > 10, f"{n}.pck has the game data ({pck_mb:.0f} MB)")
	# Export-preset custom features are stored as "_custom_features" in the pck's project.binary.
	with open(root / f"{n}.pck", "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
		i = m.find(b"_custom_features")
		near = m[i: i + 200] if i >= 0 else b""
	want = [x for x in a.custom_features.split(",") if x]
	if want:
		ok(all(w.encode() in near for w in want), f"pck project settings carry custom features {want}")
	else:
		ok(i < 0, "pck carries no custom features (store build: no beta_unlock)")

	pbx = pbx_path.read_text(encoding="utf-8")
	team = os.environ.get(a.team_env, "")
	print("Build settings (Release and Debug)")
	for config in ("Release", "Debug"):
		bs = build_settings(pbx, config)
		ok(bool(bs), f"{config}: target build settings found")
		ok(bs.get("PRODUCT_BUNDLE_IDENTIFIER") == a.bundle_id, f"{config}: PRODUCT_BUNDLE_IDENTIFIER = {bs.get('PRODUCT_BUNDLE_IDENTIFIER')}")
		ok(bs.get("MARKETING_VERSION") == a.version, f"{config}: MARKETING_VERSION = {bs.get('MARKETING_VERSION')}")
		ok(bs.get("CURRENT_PROJECT_VERSION") == a.build, f"{config}: CURRENT_PROJECT_VERSION = {bs.get('CURRENT_PROJECT_VERSION')}")
		ok(bs.get("CODE_SIGN_STYLE") == "Automatic", f"{config}: CODE_SIGN_STYLE = {bs.get('CODE_SIGN_STYLE')}")
		dt = bs.get("DEVELOPMENT_TEAM", "")
		ok(bool(re.fullmatch(r"[A-Z0-9]{10}", dt)) and (not team or dt == team),
			f"{config}: DEVELOPMENT_TEAM is a 10-character team id" + (f" equal to ${a.team_env}" if team else ""))
		print(f"        {config}: IPHONEOS_DEPLOYMENT_TARGET={bs.get('IPHONEOS_DEPLOYMENT_TARGET')} "
			f"TARGETED_DEVICE_FAMILY={bs.get('TARGETED_DEVICE_FAMILY')} INFOPLIST_KEY_CFBundleDisplayName={bs.get('INFOPLIST_KEY_CFBundleDisplayName')}")
	ok("PrivacyInfo.xcprivacy in Resources" in pbx, "PrivacyInfo.xcprivacy is in the Resources build phase")
	ok(f"BlueprintName = {n};" in scheme.read_text(encoding="utf-8") or f'BlueprintName = "{n}"' in scheme.read_text(encoding="utf-8"),
		f"shared scheme {n} builds target {n}")

	print("Info.plist")
	info = plistlib.loads((root / n / f"{n}-Info.plist").read_bytes())
	ok(info.get("ITSAppUsesNonExemptEncryption") is False, "ITSAppUsesNonExemptEncryption = false (export compliance answered in the binary)")
	ok(info.get("UIRequiresFullScreen") is True, "UIRequiresFullScreen = true (no iPad multitasking orientation requirement)")
	ok(set(info.get("UISupportedInterfaceOrientations", [])) <= {"UIInterfaceOrientationLandscapeLeft", "UIInterfaceOrientationLandscapeRight"}
		and info.get("UISupportedInterfaceOrientations"), f"landscape only: {info.get('UISupportedInterfaceOrientations')}")
	ok(bool(info.get("UILaunchStoryboardName")), f"UILaunchStoryboardName = {info.get('UILaunchStoryboardName')!r}")
	ok(info.get("CFBundleShortVersionString") == "$(MARKETING_VERSION)" and info.get("CFBundleVersion") == "$(CURRENT_PROJECT_VERSION)",
		"CFBundleShortVersionString / CFBundleVersion come from the build settings")
	purpose = {k: v for k, v in info.items() if k.endswith("UsageDescription")}
	for k, v in sorted(purpose.items()):
		ok(bool(str(v).strip()), f"{k} is not empty ({v!r})")
	print(f"        UIRequiredDeviceCapabilities={info.get('UIRequiredDeviceCapabilities')} "
		f"UIFileSharingEnabled={info.get('UIFileSharingEnabled')}")

	print("Localized InfoPlist.strings")
	for lproj in sorted((root / n).glob("*.lproj")):
		text = (lproj / "InfoPlist.strings").read_text(encoding="utf-8") if (lproj / "InfoPlist.strings").exists() else ""
		empty = re.findall(r'^\s*(\w+UsageDescription)\s*=\s*""\s*;', text, re.M)
		keys = re.findall(r'^\s*(\w+)\s*=', text, re.M)
		ok(not empty, f"{lproj.name}: keys {keys}" + (f"; EMPTY {empty}" if empty else ""))

	print("Privacy manifest")
	priv = plistlib.loads((root / "PrivacyInfo.xcprivacy").read_bytes())
	ok(priv.get("NSPrivacyTracking") is False, "NSPrivacyTracking = false")
	ok(not priv.get("NSPrivacyTrackingDomains"), "no tracking domains")
	ok(not priv.get("NSPrivacyCollectedDataTypes"), "no collected data types (matches App Privacy 'Data Not Collected')")
	for t in priv.get("NSPrivacyAccessedAPITypes", []):
		print(f"        required-reason API {t.get('NSPrivacyAccessedAPIType')}: {t.get('NSPrivacyAccessedAPITypeReasons')}")

	print("Entitlements")
	ent_path = root / n / f"{n}.entitlements"
	ent = plistlib.loads(ent_path.read_bytes()) if ent_path.exists() else {}
	print(f"        {sorted(ent) or 'none (no capabilities that need a provisioning-profile entitlement)'}")

	print("App icons")
	icon_dir = root / n / "Images.xcassets/AppIcon.appiconset"
	images = json.loads((icon_dir / "Contents.json").read_text(encoding="utf-8")).get("images", [])
	has_1024 = False
	for img in images:
		f = img.get("filename")
		if not f:
			continue
		w, h, ctype, trns = png_info(icon_dir / f)
		size = float(img["size"].split("x")[0]) * float((img.get("scale") or "1x").rstrip("x"))
		has_1024 = has_1024 or w == 1024
		ok(w == h == round(size) and ctype in (0, 2) and not trns,
			f"{f}: {w}x{h} expected {round(size)}, color type {ctype} ({'no alpha' if ctype in (0, 2) and not trns else 'HAS ALPHA'})")
	ok(has_1024, "1024x1024 App Store icon present")

	print()
	print("RESULT: " + ("all checks passed" if not FAIL else f"{len(FAIL)} check(s) failed"))
	return 1 if FAIL else 0


if __name__ == "__main__":
	sys.exit(main())
