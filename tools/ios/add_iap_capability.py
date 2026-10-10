#!/usr/bin/env python3
"""Turns on the In-App Purchase capability in the Xcode project that Godot exports (ios.yml, store builds only).

Godot 4.7's iOS export has no In-App Purchase option: its project template leaves the target's
SystemCapabilities empty. In-App Purchase needs no entitlement key (the App ID com.mysteryroom.forgotteninstitute
already has the IN_APP_PURCHASE capability, so the App Store profile allows it); in Xcode the capability is the
target attribute com.apple.InAppPurchase plus StoreKit.framework, which the StoreKit plugin's .gdip links.

Usage: add_iap_capability.py <export dir> [--name MysteryRoom]. Idempotent. Exit 1 when the project does not look
as expected (nothing is written then).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CAP = "com.apple.InAppPurchase = {\n\t\t\t\t\t\t\t\tenabled = 1;\n\t\t\t\t\t\t\t};"


def main() -> int:
	ap = argparse.ArgumentParser()
	ap.add_argument("export_dir")
	ap.add_argument("--name", default="MysteryRoom")
	a = ap.parse_args()
	pbx = Path(a.export_dir) / f"{a.name}.xcodeproj/project.pbxproj"
	text = pbx.read_text(encoding="utf-8")
	if re.search(r"com\.apple\.InAppPurchase = \{\s*enabled = 1;", text):
		print("In-App Purchase capability: already on")
		return 0
	m = re.search(r"TargetAttributes = \{.*?SystemCapabilities = \{(\s*)\};", text, re.S)
	if not m:
		print("ERROR: no empty SystemCapabilities block under TargetAttributes in project.pbxproj")
		return 1
	start, end = m.span()
	block = text[start:end]
	block = re.sub(r"SystemCapabilities = \{\s*\};", "SystemCapabilities = {\n\t\t\t\t\t\t\t" + CAP + "\n\t\t\t\t\t\t};", block)
	pbx.write_text(text[:start] + block + text[end:], encoding="utf-8")
	print("In-App Purchase capability: com.apple.InAppPurchase enabled in the target's SystemCapabilities")
	if "StoreKit.framework" not in text:
		print("WARNING: StoreKit.framework is not linked (the StoreKit plugin's .gdip adds it)")
	return 0


if __name__ == "__main__":
	sys.exit(main())
