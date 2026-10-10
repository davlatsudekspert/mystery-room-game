#!/usr/bin/env python3
"""Sets up the MYSTERY ROOM one-time product "full_game" in Google Play (workflow play-iap.yml).

DRY RUN BY DEFAULT: without --apply it only reads (GET), plus one read-only price calculation
(pricing:convertRegionPrices, which changes nothing), and prints what it would do. With --apply it creates or
fixes, idempotently, the managed product full_game of com.mysteryroom.forgotteninstitute only (the package of
game/export_presets.cfg): active, title "Full Game" / «Полная игра» (Play has no Uzbek listing language), a one-line
description, US$4.99 in the United States and Google's local prices for every other region
(convertRegionPrices, then autoConvertMissingPrices for anything left).

Before anything else it checks whether the service account may manage in-app products. It was given only "Release
apps to testing tracks", and Play also needs a payments (merchant) profile and an uploaded build that declares
com.android.vending.BILLING before a product can be created. Any of these missing ends the run with a clear
message naming it (exit 3). It never touches another app, a track, the store listing, the app's price or its
availability.

API: Google Play Developer API v3, inappproducts (get / insert / patch) and monetization pricing. Environment:
PLAY_SERVICE_ACCOUNT_JSON (GitHub secret; the key, the token and the account's e-mail are never printed).
Exit 0 = done (or planned), 1 = a request failed, 2 = missing or unreadable secret, 3 = a permission or Play
Console prerequisite is missing.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = os.environ.get("PLAY_API_BASE", "https://androidpublisher.googleapis.com/androidpublisher/v3").rstrip("/")
SCOPE = "https://www.googleapis.com/auth/androidpublisher"
PACKAGE = "com.mysteryroom.forgotteninstitute"
SKU = "full_game"
US_PRICE_MICROS = 4_990_000 # US$4.99
LISTINGS = {
	"en-US": {"title": "Full Game", "description": "Unlocks Chapters 3 and 4. One-time purchase."}, # Chapters 1-2 are free
	"ru-RU": {"title": "Полная игра", "description": "Открывает главы 3 и 4. Разовая покупка."},
}
HINT_PERMISSION = ("the service account may not manage in-app products. Play Console > Users and permissions > the "
	"MYSTERY ROOM service account > App permissions > MYSTERY ROOM only > tick \"Manage in-app products\" (Monetize > "
	"Products) > Apply. Do not give account-wide or other apps' permissions. docs/release/GOOGLE_PLAY_TESTING.md §11")
HINT_MERCHANT = ("Google Play has no payments (merchant) profile for this developer account. Play Console > Settings > "
	"Payments profile (or Monetize > Products > set up a merchant account). docs/release/GOOGLE_PLAY_TESTING.md §11")
HINT_BILLING = ("Play needs an uploaded build that declares com.android.vending.BILLING before it allows in-app products: "
	"run android.yml with build_type=release, include_billing=true (or store_sandbox=true), upload_to_play=true, "
	"play_track=internal, play_status=draft. docs/release/GOOGLE_PLAY_TESTING.md §11")

LINES: list[str] = []


def out(line: str = "") -> None:
	print(line, flush=True)
	LINES.append(line)


class Play:
	def __init__(self, info: dict, apply: bool) -> None:
		self._info = info
		self._token = ""
		self.apply = apply
		self.planned: list[str] = []
		self.failed: list[str] = []

	def _auth(self) -> str:
		if self._token:
			return self._token
		import jwt # PyJWT[crypto]
		now = int(time.time())
		assertion = jwt.encode({"iss": self._info["client_email"], "scope": SCOPE, "aud": self._info.get("token_uri",
			"https://oauth2.googleapis.com/token"), "iat": now, "exp": now + 1800}, self._info["private_key"], algorithm="RS256")
		data = urllib.parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion}).encode()
		req = urllib.request.Request(self._info.get("token_uri", "https://oauth2.googleapis.com/token"), data=data, method="POST")
		try:
			with urllib.request.urlopen(req, timeout=40) as r:
				self._token = json.loads(r.read())["access_token"]
		except urllib.error.HTTPError as e:
			raise RuntimeError(f"OAuth token request failed: HTTP {e.code} (wrong or revoked key?)") from None
		return self._token

	def call(self, method: str, path: str, query: dict | None = None, body: dict | None = None, write: bool = False,
			what: str = "") -> tuple[int, dict]:
		if not path.startswith(f"/applications/{PACKAGE}/"):
			raise RuntimeError(f"refusing a request outside {PACKAGE}: {path}")
		if write and not self.apply:
			out(f"  DRY RUN: would {method} {path}: {what}")
			self.planned.append(f"{method} {path}: {what}")
			return 0, {}
		url = API + path + ("?" + urllib.parse.urlencode(query) if query else "")
		for attempt in range(3):
			req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
				headers={"Authorization": "Bearer " + self._auth(), "Content-Type": "application/json"})
			try:
				with urllib.request.urlopen(req, timeout=60) as r:
					status, resp = r.status, json.loads(r.read() or b"{}")
			except urllib.error.HTTPError as e:
				status, resp = e.code, {}
				try:
					resp = json.loads(e.read() or b"{}")
				except ValueError:
					pass
				if e.code in (429, 500, 502, 503) and (method == "GET" or e.code == 429) and attempt < 2:
					time.sleep(4 * (attempt + 1))
					continue
			except urllib.error.URLError as e:
				status, resp = 0, {"error": {"message": f"network error: {e.reason}"}}
			break
		if write:
			ok = 200 <= status < 300
			out(f"  {method} {path}: HTTP {status} ({what})" + ("" if ok else f": {message(resp)}"))
			if not ok:
				self.failed.append(f"{method} {path}: HTTP {status} {message(resp)}")
		return status, resp


def message(resp: dict) -> str:
	e = resp.get("error") or {}
	return str(e.get("message") or e.get("status") or "no error body")[:400]


def diagnose(status: int, resp: dict) -> str | None:
	"""The Play Console prerequisite behind an error, or None."""
	text = message(resp).lower()
	if re.search(r"merchant|payments profile|payment profile", text):
		return HINT_MERCHANT
	if "billing" in text and re.search(r"permission|apk|bundle|upload", text):
		return HINT_BILLING
	if status == 403 or "does not have permission" in text or "permission" in text:
		return HINT_PERMISSION
	return None


def money_to_micros(m: dict) -> int:
	return int(m.get("units") or 0) * 1_000_000 + int(m.get("nanos") or 0) // 1000


def regional_prices(play: Play) -> dict:
	"""Google's local price for every region from US$4.99 (a calculation; nothing is stored)."""
	st, resp = play.call("POST", f"/applications/{PACKAGE}/pricing:convertRegionPrices",
		body={"price": {"currencyCode": "USD", "units": "4", "nanos": 990000000}})
	conv = resp.get("convertedRegionPrices") or {}
	if st != 200 or not conv:
		out(f"- regional prices: HTTP {st}: {message(resp)} (insert then relies on autoConvertMissingPrices)")
		return {}
	prices = {r: {"priceMicros": str(money_to_micros(v["price"])), "currency": v["price"]["currencyCode"]}
		for r, v in conv.items() if v.get("price")}
	sample = ", ".join(f"{r} {int(prices[r]['priceMicros']) / 1e6:g} {prices[r]['currency']}" for r in ("UZ", "RU", "KZ", "TR", "DE", "IN") if r in prices)
	out(f"- regional prices from US$4.99: {len(prices)} regions (HTTP 200), e.g. {sample}")
	return prices


def product_body(prices: dict, home: str) -> dict:
	prices = dict(prices)
	prices["US"] = {"priceMicros": str(US_PRICE_MICROS), "currency": "USD"}
	default = prices["US"]
	if home != "USD":
		default = next((p for p in prices.values() if p["currency"] == home), None)
		if default is None:
			raise RuntimeError(f"no converted price in the home currency {home}")
	return {"packageName": PACKAGE, "sku": SKU, "status": "active", "purchaseType": "managedUser",
		"defaultPrice": default, "prices": prices, "defaultLanguage": "en-US", "listings": LISTINGS}


def package_from_presets(path: Path) -> str:
	m = re.findall(r'^package/unique_name="([^"]+)"', path.read_text(encoding="utf-8"), re.M) if path.exists() else []
	return m[0] if m and len(set(m)) == 1 else ""


def main() -> int:
	ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	ap.add_argument("--apply", action="store_true", help="create or fix the product (default: dry run)")
	ap.add_argument("--home-currency", default="USD", help="the payments profile's currency (Play's default price must be in it)")
	ap.add_argument("--presets", default="game/export_presets.cfg")
	a = ap.parse_args()
	out(f"## Google Play one-time product setup: {SKU} ({'APPLY' if a.apply else 'DRY RUN, nothing is changed'})")
	pkg = package_from_presets(Path(a.presets))
	if pkg != PACKAGE:
		out(f"ERROR: the Android presets' package is {pkg!r}, expected {PACKAGE}. Nothing was done.")
		return 1
	raw = os.environ.get("PLAY_SERVICE_ACCOUNT_JSON", "")
	if not raw.strip():
		out("Missing secret: PLAY_SERVICE_ACCOUNT_JSON")
		return 2
	try:
		info = json.loads(raw)
		assert info.get("type") == "service_account" and info.get("private_key") and info.get("client_email")
	except (ValueError, AssertionError):
		out("- PLAY_SERVICE_ACCOUNT_JSON is not a service-account JSON key (its content is not printed)")
		return 2
	play = Play(info, a.apply)
	try:
		play._auth()
	except RuntimeError as e:
		out(f"- {e}")
		return 2
	out(f"- service account token: OK (package {PACKAGE})")

	# 1. May this account read and manage in-app products of this app?
	st, resp = play.call("GET", f"/applications/{PACKAGE}/inappproducts", {"maxResults": "100"})
	if st != 200:
		hint = diagnose(st, resp) or HINT_PERMISSION
		out(f"- in-app products list: HTTP {st}: {message(resp)}")
		out(f"MISSING: {hint}")
		return 3
	products = {p.get("sku"): p for p in resp.get("inappproduct") or []}
	out(f"- in-app products list: HTTP 200, {len(products)} product(s): {sorted(products) or 'none'}")

	# 2. The product
	cur = products.get(SKU)
	if cur is None:
		st, got = play.call("GET", f"/applications/{PACKAGE}/inappproducts/{SKU}")
		cur = got if st == 200 else None
	prices = regional_prices(play)
	body = product_body(prices, a.home_currency.upper())
	q = {"autoConvertMissingPrices": "true"}
	if cur is None:
		out(f"- {SKU}: not found")
		st, resp = play.call("POST", f"/applications/{PACKAGE}/inappproducts", q, body, write=True,
			what=f"insert managed product {SKU}, active, US$4.99 + {len(body['prices']) - 1} regional prices, listings {sorted(LISTINGS)}")
	else:
		out(f"- {SKU}: found, status {cur.get('status')}, type {cur.get('purchaseType')}, default price "
			f"{int((cur.get('defaultPrice') or {}).get('priceMicros', 0)) / 1e6:g} {(cur.get('defaultPrice') or {}).get('currency')}, "
			f"{len(cur.get('prices') or {})} regional prices, listings {sorted(cur.get('listings') or {})}")
		if cur.get("purchaseType") not in (None, "managedUser"):
			out(f"ERROR: {SKU} exists as {cur.get('purchaseType')}; a product id cannot be retyped. The owner decides.")
			return 1
		us = (cur.get("prices") or {}).get("US") or {}
		have = {k: {f: (v or {}).get(f) for f in ("title", "description")} for k, v in (cur.get("listings") or {}).items()}
		same = (cur.get("status") == "active" and have == LISTINGS and us.get("currency") == "USD"
			and int(us.get("priceMicros", 0)) == US_PRICE_MICROS)
		if same:
			out("  active, US$4.99 in the US, listings as expected: nothing to change")
			st, resp = 200, cur
		else:
			st, resp = play.call("PUT", f"/applications/{PACKAGE}/inappproducts/{SKU}", q, body, write=True,
				what="update to active, US$4.99 + regional prices, listings")
	if a.apply and not 200 <= st < 300:
		hint = diagnose(st, resp)
		if hint:
			out(f"MISSING: {hint}")
			return 3
		return 1

	out()
	out("### Result")
	if a.apply:
		st, got = play.call("GET", f"/applications/{PACKAGE}/inappproducts/{SKU}")
		if st == 200:
			pr = got.get("prices") or {}
			out(f"- {SKU}: status {got.get('status')}, {len(pr)} regional prices; US "
				f"{int((pr.get('US') or {}).get('priceMicros', 0)) / 1e6:g} {(pr.get('US') or {}).get('currency')}, UZ "
				f"{int((pr.get('UZ') or {}).get('priceMicros', 0)) / 1e6:g} {(pr.get('UZ') or {}).get('currency')}")
		else:
			out(f"- {SKU}: HTTP {st}: {message(got)}")
	else:
		out(f"- planned changes: {len(play.planned)}" + ("" if play.planned else " (none: everything is as expected)"))
	out("- testing: only accounts in Play Console > Settings > License testing buy with test cards; anyone else on the"
		" internal track pays real money (docs/release/GOOGLE_PLAY_TESTING.md §11)")
	summary = os.environ.get("GITHUB_STEP_SUMMARY")
	if summary:
		with open(summary, "a", encoding="utf-8") as f:
			f.write("\n".join(LINES) + "\n")
	return 1 if play.failed else 0


if __name__ == "__main__":
	sys.exit(main())
