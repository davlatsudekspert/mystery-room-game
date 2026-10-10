#!/usr/bin/env python3
"""Adds the store (billing) plugins to a build copy of the Godot project. Used by android.yml and ios.yml on the
runner only; the repository never contains the plugins, so a build without them cannot ask for BILLING or link
StoreKit by accident (docs/MONETIZATION.md).

  --android  GodotGooglePlayBilling 3.3.0 (godot-sdk-integrations, MIT): unzips to game/addons/GodotGooglePlayBilling
             and enables its editor plugin in project.godot. Its export plugin then adds the plugin's AAR and
             com.android.billingclient:billing-ktx:9.1.0 to the Gradle build, whose manifest merge adds
             com.android.vending.BILLING. Gradle builds only (the "Android AAB" preset).
  --ios      "Godot iOS plugin for In-App purchase" 0.4.0 (hrk4649/godot_ios_plugin_iap, MIT; StoreKit 2; .gdip +
             static xcframework built for Godot 4.7): unzips to game/ios/plugins/ios-in-app-purchase and turns on
             plugins/IOSInAppPurchase in the "iOS" preset.

Each release zip is pinned by its SHA-256; a different file stops the build. --zip uses a local copy instead of
downloading (it is checked the same way). Prints only what it changed. Exit 1 on any mismatch.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

PLUGINS = {
	"android": {
		"name": "GodotGooglePlayBilling 3.3.0",
		"url": "https://github.com/godot-sdk-integrations/godot-google-play-billing/releases/download/3.3.0/godot-google-play-billing.zip",
		"sha256": "20d75623d6f337f08d8283c83098b73678d5f575e39247af5a8eb80588b18568",
		"prefix": "GodotGooglePlayBilling/",
		"dest": "addons",
		"must": ["GodotGooglePlayBilling/plugin.cfg", "GodotGooglePlayBilling/export_plugin.gd",
			"GodotGooglePlayBilling/bin/release/GodotGooglePlayBilling-release.aar",
			"GodotGooglePlayBilling/bin/debug/GodotGooglePlayBilling-debug.aar", "GodotGooglePlayBilling/LICENSE"],
	},
	"ios": {
		"name": "Godot iOS plugin for In-App purchase 0.4.0",
		"url": "https://github.com/hrk4649/godot_ios_plugin_iap/releases/download/0.4.0/ios-in-app-purchase-v0.4.0.zip",
		"sha256": "578800e79f2bcd8719eb00e4f80d036960518ec1b113c7b47626f95a8aeda87a",
		"prefix": "ios/plugins/ios-in-app-purchase/",
		"dest": "",
		"must": ["ios/plugins/ios-in-app-purchase/ios-in-app-purchase.gdip", "ios/plugins/ios-in-app-purchase/LICENSE",
			"ios/plugins/ios-in-app-purchase/ios-in-app-purchase.release.xcframework/ios-arm64/ios-in-app-purchase.a",
			"ios/plugins/ios-in-app-purchase/ios-in-app-purchase.debug.xcframework/ios-arm64/ios-in-app-purchase.a"],
	},
}
ANDROID_PLUGIN_CFG = "res://addons/GodotGooglePlayBilling/plugin.cfg"
IOS_PLUGIN_KEY = "plugins/IOSInAppPurchase"


def fetch(spec: dict, local: str | None) -> bytes:
	if local:
		data = Path(local).read_bytes()
	else:
		with urllib.request.urlopen(spec["url"], timeout=120) as r:
			data = r.read()
	got = hashlib.sha256(data).hexdigest()
	if got != spec["sha256"]:
		sys.exit(f"ERROR: {spec['name']}: SHA-256 {got} does not match the pinned {spec['sha256']}")
	print(f"{spec['name']}: {len(data)} bytes, SHA-256 {got} (pinned) OK")
	return data


def unpack(spec: dict, data: bytes, game: Path) -> None:
	dest = game / spec["dest"] if spec["dest"] else game
	with zipfile.ZipFile(io.BytesIO(data)) as z:
		names = z.namelist()
		missing = [m for m in spec["must"] if m not in names]
		if missing:
			sys.exit(f"ERROR: {spec['name']}: the zip lacks {missing}")
		for n in names:
			# only the plugin's own folder, never a path that climbs out of it
			if ".." in Path(n).parts or n.startswith("/"):
				sys.exit(f"ERROR: {spec['name']}: unsafe path in the zip: {n}")
			if not n.startswith(spec["prefix"]):
				if not spec["prefix"].startswith(n): # its parent folders are fine
					print(f"  skipped {n}")
				continue
			out = dest / n
			if n.endswith("/"):
				out.mkdir(parents=True, exist_ok=True)
				continue
			out.parent.mkdir(parents=True, exist_ok=True)
			out.write_bytes(z.read(n))
	print(f"  unpacked to {(dest / spec['prefix']).relative_to(game.parent)}")


def enable_android(game: Path) -> None:
	p = game / "project.godot"
	text = p.read_text(encoding="utf-8")
	if ANDROID_PLUGIN_CFG in text:
		print("  project.godot: the billing editor plugin is already enabled")
		return
	m = re.search(r"^\[editor_plugins\]\s*\n(.*?)(?=^\[|\Z)", text, re.S | re.M)
	if m and "enabled=PackedStringArray(" in m.group(1):
		text = re.sub(r'(enabled=PackedStringArray\()', rf'\1"{ANDROID_PLUGIN_CFG}", ', text, count=1)
		text = text.replace(f'"{ANDROID_PLUGIN_CFG}", )', f'"{ANDROID_PLUGIN_CFG}")')
	else:
		text = text.rstrip("\n") + f'\n\n[editor_plugins]\n\nenabled=PackedStringArray("{ANDROID_PLUGIN_CFG}")\n'
	p.write_text(text, encoding="utf-8")
	print(f"  project.godot: editor plugin {ANDROID_PLUGIN_CFG} enabled")


def enable_ios(game: Path) -> None:
	p = game / "export_presets.cfg"
	lines = p.read_text(encoding="utf-8").split("\n")
	# find the [preset.N] whose name is "iOS", then its [preset.N.options] block
	ios_index = None
	current = None
	for line in lines:
		m = re.fullmatch(r"\[preset\.(\d+)\]", line)
		if m:
			current = m.group(1)
		elif current is not None and line == 'name="iOS"':
			ios_index = current
	if ios_index is None:
		sys.exit("ERROR: export_presets.cfg has no preset named iOS")
	start = lines.index(f"[preset.{ios_index}.options]")
	end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("[")), len(lines))
	block = lines[start + 1:end]
	for i, line in enumerate(block):
		if line.startswith(IOS_PLUGIN_KEY + "="):
			block[i] = IOS_PLUGIN_KEY + "=true"
			break
	else:
		while block and block[-1] == "":
			block.pop()
		block.append(IOS_PLUGIN_KEY + "=true")
		block.append("")
	lines[start + 1:end] = block
	p.write_text("\n".join(lines), encoding="utf-8")
	print(f"  export_presets.cfg: [preset.{ios_index}.options] {IOS_PLUGIN_KEY}=true")


def main() -> int:
	ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	ap.add_argument("--game", default="game", help="the Godot project folder (a build copy)")
	ap.add_argument("--android", action="store_true")
	ap.add_argument("--ios", action="store_true")
	ap.add_argument("--zip", help="a local copy of the release zip (only with one of --android / --ios)")
	a = ap.parse_args()
	game = Path(a.game).resolve()
	if not (game / "project.godot").exists():
		sys.exit(f"ERROR: {game} is not a Godot project")
	if a.android == a.ios:
		sys.exit("ERROR: give exactly one of --android or --ios")
	which = "android" if a.android else "ios"
	spec = PLUGINS[which]
	unpack(spec, fetch(spec, a.zip), game)
	enable_android(game) if which == "android" else enable_ios(game)
	return 0


if __name__ == "__main__":
	sys.exit(main())
