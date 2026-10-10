#!/usr/bin/env python3
"""Sets up the MYSTERY ROOM in-app purchase "full_game" in App Store Connect (workflow ios-iap.yml).

DRY RUN BY DEFAULT: without --apply every request is a GET and each change is only printed ("DRY RUN: would POST
..."). With --apply it creates or fixes, idempotently, on the app whose bundle id is exactly
com.mysteryroom.forgotteninstitute and nothing else:
  - the NON_CONSUMABLE in-app purchase productId "full_game", reference name "Full Game", with a review note;
  - localizations en-US "Full Game", ru «Полная игра», uz "To'liq o'yin" (App Store Connect has no Uzbek locale:
    the uz request is tried and its refusal reported), each with a one-line description (45 characters at most):
    "Unlocks Chapters 3 and 4. One-time purchase." (Chapters 1-2 are free); existing ones are PATCHed when different;
  - a price schedule with the United States as the base territory at the US$4.99 price point (its id is looked up
    through the API); Apple sets every other territory's price from it automatically;
  - availability in the territories where the app itself is available (with --territories all: every territory);
  - optionally (--review-screenshot PNG) the App Review screenshot. Review needs it; sandbox purchases do not. A
    different file replaces the current one (DELETE of that screenshot, the only DELETE this script can send).
It never submits anything for review (no *Submission endpoint is reachable from this script), never changes the
app's name, price or availability, and never touches another app. Writes go only to the in-app purchase endpoints
listed in WRITE_OK. At the end it prints the in-app purchase's state and what is still missing for
"Ready to Submit".

Environment (GitHub secrets): ASC_KEY_ID, ASC_ISSUER_ID, ASC_KEY_P8_BASE64. The JWT, key id and issuer id are never
printed. Exit 0 = done (or planned, in a dry run), 1 = a request failed or the record is not what we expect,
2 = missing or unreadable secrets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import asc_check  # noqa: E402  (the read-only client, key loading and output helpers)
from asc_check import API, Asc, err, load_key, check_key, out  # noqa: E402

BUNDLE_ID = "com.mysteryroom.forgotteninstitute"
PRODUCT_ID = "full_game"
REFERENCE_NAME = "Full Game"
IAP_TYPE = "NON_CONSUMABLE"
BASE_TERRITORY = "USA"
BASE_PRICE = "4.99"
REVIEW_NOTE = ("One-time purchase that unlocks Chapters 3 and 4 (Chapters 1 and 2 are free). To find it: main menu > "
	"Chapters > Chapter 3 > Unlock, or the Unlock button on the Chapter 2 complete screen. Restore purchases is on the "
	"same screen and in Settings. No account, no ads, no subscriptions.")
EXPECTED_IAP_ID = "6821386340" # full_game as created in App Store Connect (director, 2026-10-10)
# locale → (display name ≤ 30, description ≤ 45)
LOCALIZATIONS = {
	"en-US": ("Full Game", "Unlocks Chapters 3 and 4. One-time purchase."),
	"ru": ("Полная игра", "Открывает главы 3 и 4. Разовая покупка."),
	"uz": ("To'liq o'yin", "3 va 4-boblarni ochadi. Bir martalik xarid."),
}
# DELETE is allowed for one thing only: replacing the in-app purchase's App Review screenshot (an in-app purchase
# has one; a changed screenshot is deleted, then the new file is uploaded). Nothing else can be deleted.
DELETE_OK = re.compile(r"/v1/inAppPurchaseAppStoreReviewScreenshots/[A-Za-z0-9-]+")
WRITE_OK = re.compile(r"/v2/inAppPurchases(/[A-Za-z0-9-]+)?|/v1/inAppPurchaseLocalizations(/[A-Za-z0-9-]+)?|"
	r"/v1/inAppPurchasePriceSchedules|/v1/inAppPurchaseAvailabilities|/v1/inAppPurchaseAppStoreReviewScreenshots(/[A-Za-z0-9-]+)?")


class AscWriter(Asc):
	"""The read-only client plus POST/PATCH to the in-app purchase endpoints only, and only with --apply."""

	def __init__(self, key_id: str, issuer: str, key, apply: bool) -> None:
		super().__init__(key_id, issuer, key)
		self.apply = apply
		self.planned: list[str] = []
		self.failed: list[str] = []

	def send(self, method: str, path: str, body: dict | None, what: str) -> tuple[int, dict]:
		allowed = (method in ("POST", "PATCH") and WRITE_OK.fullmatch(path)) or (method == "DELETE" and DELETE_OK.fullmatch(path))
		if not allowed or "ubmission" in path:
			raise RuntimeError(f"refusing {method} {path}: not an in-app purchase setup endpoint")
		if not self.apply:
			out(f"  DRY RUN: would {method} {path}: {what}")
			self.planned.append(f"{method} {path}: {what}")
			return 0, {}
		for attempt in range(3):
			req = urllib.request.Request(API + path, data=json.dumps(body).encode() if body is not None else None, method=method,
				headers={"Authorization": "Bearer " + self._jwt(), "Content-Type": "application/json"})
			try:
				with urllib.request.urlopen(req, timeout=60) as r:
					status, resp = r.status, json.loads(r.read() or b"{}")
			except urllib.error.HTTPError as e:
				status, resp = e.code, {}
				try:
					resp = json.loads(e.read() or b"{}")
				except ValueError:
					pass
				if e.code == 429 and attempt < 2: # rate limited: nothing was done, safe to repeat
					time.sleep(5 * (attempt + 1))
					continue
			except urllib.error.URLError as e:
				status, resp = 0, {"errors": [{"title": "network error", "detail": str(e.reason)}]}
			break
		ok = 200 <= status < 300
		out(f"  {method} {path}: HTTP {status} ({what})" + ("" if ok else f": {err(resp)}"))
		if not ok:
			self.failed.append(f"{method} {path}: HTTP {status} {err(resp)}")
		return status, resp

	def upload(self, ops: list, data: bytes) -> bool:
		"""Uploads an asset with the upload operations App Store Connect returned (its own asset host, no JWT)."""
		for op in ops:
			url = str(op.get("url", ""))
			if not url.startswith("https://") or url.startswith(API):
				out(f"  refusing upload operation to {url[:40]}…")
				return False
			off, length = int(op.get("offset", 0)), int(op.get("length", len(data)))
			headers = {h["name"]: h["value"] for h in op.get("requestHeaders") or []}
			req = urllib.request.Request(url, data=data[off:off + length], method=op.get("method", "PUT"), headers=headers)
			try:
				with urllib.request.urlopen(req, timeout=120) as r:
					if not 200 <= r.status < 300:
						out(f"  upload part at {off}: HTTP {r.status}")
						return False
			except urllib.error.URLError as e:
				out(f"  upload part at {off} failed: {getattr(e, 'code', '')} {getattr(e, 'reason', '')}")
				return False
		return True


def first(body: dict) -> dict:
	d = body.get("data")
	return (d[0] if d else {}) if isinstance(d, list) else (d or {})


def find_app(asc: AscWriter) -> dict:
	st, apps = asc.get_all("/v1/apps", {"filter[bundleId]": BUNDLE_ID, "fields[apps]": "name,bundleId,sku"})
	apps = [a for a in apps if a["attributes"].get("bundleId") == BUNDLE_ID]
	out(f"- app with bundle id {BUNDLE_ID}: HTTP {st}, {len(apps)} exact match(es)")
	if len(apps) != 1:
		return {}
	a = apps[0]
	out(f"  app {a['id']}: {a['attributes'].get('name')!r}, SKU {a['attributes'].get('sku')}")
	return a


def ensure_iap(asc: AscWriter, app_id: str) -> dict:
	st, iaps = asc.get_all(f"/v1/apps/{app_id}/inAppPurchasesV2", {"filter[productId]": PRODUCT_ID, "limit": "200"})
	iaps = [i for i in iaps if i["attributes"].get("productId") == PRODUCT_ID]
	out(f"- in-app purchase {PRODUCT_ID}: HTTP {st}, {'found' if iaps else 'not found'}")
	if iaps:
		iap = iaps[0]
		a = iap["attributes"]
		out(f"  {iap['id']}: type {a.get('inAppPurchaseType')}, reference name {a.get('name')!r}, state {a.get('state')}"
			+ ("" if iap["id"] == EXPECTED_IAP_ID else f" (note: the director recorded id {EXPECTED_IAP_ID})"))
		if a.get("inAppPurchaseType") != IAP_TYPE:
			out(f"  ERROR: {PRODUCT_ID} exists as {a.get('inAppPurchaseType')}, not {IAP_TYPE}. A product id cannot be"
				" reused or retyped; the owner decides. Nothing else is changed.")
			asc.failed.append("wrong product type")
			return {}
		changes = {}
		if a.get("name") != REFERENCE_NAME:
			changes["name"] = REFERENCE_NAME
		if (a.get("reviewNote") or "") != REVIEW_NOTE:
			changes["reviewNote"] = REVIEW_NOTE
		if changes:
			asc.send("PATCH", f"/v2/inAppPurchases/{iap['id']}", {"data": {"type": "inAppPurchases", "id": iap["id"],
				"attributes": changes}}, f"set {', '.join(sorted(changes))}")
		else:
			out("  reference name and review note: as expected")
		return iap
	st, body = asc.send("POST", "/v2/inAppPurchases", {"data": {"type": "inAppPurchases",
		"attributes": {"name": REFERENCE_NAME, "productId": PRODUCT_ID, "inAppPurchaseType": IAP_TYPE,
			"reviewNote": REVIEW_NOTE, "familySharable": False},
		"relationships": {"app": {"data": {"type": "apps", "id": app_id}}}}},
		f"create {IAP_TYPE} {PRODUCT_ID} ({REFERENCE_NAME!r}) on app {app_id}")
	return first(body) if 200 <= st < 300 else {}


def ensure_localizations(asc: AscWriter, iap_id: str | None, try_uz: bool) -> list[str]:
	have: dict[str, dict] = {}
	if iap_id:
		st, locs = asc.get_all(f"/v2/inAppPurchases/{iap_id}/inAppPurchaseLocalizations")
		have = {l["attributes"].get("locale"): l for l in locs}
		out(f"- localizations: HTTP {st}, {sorted(have) or 'none'}")
	# Uzbek is tried at the first setup (or with --try-uz); once refused, re-runs do not send it again
	try_uz = try_uz or not have
	missing = []
	for locale, (name, desc) in LOCALIZATIONS.items():
		assert len(name) <= 30 and len(desc) <= 45, locale
		cur = have.get(locale)
		if locale == "uz" and not cur and not try_uz:
			out("  uz: not offered by App Store Connect (refused at the first setup; --try-uz asks again)")
			continue
		if cur:
			ca = cur["attributes"]
			if ca.get("name") == name and (ca.get("description") or "") == desc:
				out(f"  {locale}: {name!r} / {desc!r}: as expected")
				continue
			asc.send("PATCH", f"/v1/inAppPurchaseLocalizations/{cur['id']}", {"data": {"type": "inAppPurchaseLocalizations",
				"id": cur["id"], "attributes": {"name": name, "description": desc}}}, f"{locale}: {name!r} / {desc!r}")
			continue
		if not iap_id:
			out(f"  DRY RUN: would add {locale}: {name!r} / {desc!r}" + (" (App Store Connect is expected to refuse uz)" if locale == "uz" else ""))
			asc.planned.append(f"localization {locale}")
			continue
		n_failed = len(asc.failed)
		st, body = asc.send("POST", "/v1/inAppPurchaseLocalizations", {"data": {"type": "inAppPurchaseLocalizations",
			"attributes": {"locale": locale, "name": name, "description": desc},
			"relationships": {"inAppPurchaseV2": {"data": {"type": "inAppPurchases", "id": iap_id}}}}},
			f"add {locale}: {name!r} / {desc!r}")
		if asc.apply and not 200 <= st < 300:
			if locale == "uz":
				# Apple's App Store localization list has no Uzbek: not a failure of the setup
				del asc.failed[n_failed:]
				out("  uz: App Store Connect refused the Uzbek locale (not in its localization list); en-US and ru cover the store")
			else:
				missing.append(f"localization {locale}")
	return missing


def ensure_price(asc: AscWriter, iap_id: str | None) -> list[str]:
	if not iap_id:
		out(f"- price: DRY RUN: would look up the {BASE_TERRITORY} US${BASE_PRICE} price point of the new in-app purchase and"
			f" create a price schedule with base territory {BASE_TERRITORY}")
		asc.planned.append(f"price schedule {BASE_TERRITORY} US${BASE_PRICE}")
		return []
	st, pts = asc.get_all(f"/v2/inAppPurchases/{iap_id}/pricePoints", {"filter[territory]": BASE_TERRITORY, "limit": "200",
		"fields[inAppPurchasePricePoints]": "customerPrice,proceeds,territory"}, max_pages=60)
	match = [p for p in pts if str(p["attributes"].get("customerPrice")) in (BASE_PRICE, BASE_PRICE + "0")]
	out(f"- price points in {BASE_TERRITORY}: HTTP {st}, {len(pts)} listed; US${BASE_PRICE}: "
		+ (f"{match[0]['id']} (proceeds {match[0]['attributes'].get('proceeds')})" if match else "NOT FOUND"))
	if not match:
		asc.failed.append(f"no US${BASE_PRICE} price point")
		return [f"price US${BASE_PRICE}"]
	point_id = match[0]["id"]
	# the current schedule: base territory and the manual price there
	st, sched = asc.get(f"/v2/inAppPurchases/{iap_id}/iapPriceSchedule")
	if st == 200 and first(sched).get("id"):
		sid = first(sched)["id"]
		st2, base = asc.get(f"/v1/inAppPurchasePriceSchedules/{sid}/baseTerritory")
		st3, prices = asc.get_all(f"/v1/inAppPurchasePriceSchedules/{sid}/manualPrices",
			{"include": "inAppPurchasePricePoint,territory", "limit": "200"})
		base_id = first(base).get("id") if st2 == 200 else None
		points = {((p.get("relationships") or {}).get("inAppPurchasePricePoint") or {}).get("data", {}).get("id")
			for p in prices if not (p.get("attributes") or {}).get("endDate")}
		out(f"  price schedule: base territory {base_id}, manual price points {len(points)}")
		if base_id == BASE_TERRITORY and point_id in points:
			out(f"  US${BASE_PRICE} in {BASE_TERRITORY} is already the base price: as expected")
			return []
	else:
		out(f"  price schedule: none yet (HTTP {st})")
	st, _ = asc.send("POST", "/v1/inAppPurchasePriceSchedules", {"data": {"type": "inAppPurchasePriceSchedules",
		"relationships": {
			"inAppPurchase": {"data": {"type": "inAppPurchases", "id": iap_id}},
			"baseTerritory": {"data": {"type": "territories", "id": BASE_TERRITORY}},
			"manualPrices": {"data": [{"type": "inAppPurchasePrices", "id": "${price1}"}]}}},
		"included": [{"type": "inAppPurchasePrices", "id": "${price1}", "attributes": {"startDate": None},
			"relationships": {"inAppPurchaseV2": {"data": {"type": "inAppPurchases", "id": iap_id}},
				"inAppPurchasePricePoint": {"data": {"type": "inAppPurchasePricePoints", "id": point_id}}}}]},
		f"base territory {BASE_TERRITORY} at US${BASE_PRICE}; other territories follow Apple's equalized prices")
	return [] if (not asc.apply or 200 <= st < 300) else [f"price US${BASE_PRICE}"]


def app_territories(asc: AscWriter, app_id: str, mode: str) -> list[str] | None:
	if mode == "all":
		st, terr = asc.get_all("/v1/territories", {"limit": "200"})
		out(f"- territories: all {len(terr)} (HTTP {st})")
		return sorted(t["id"] for t in terr)
	st, avail = asc.get(f"/v1/apps/{app_id}/appAvailabilityV2")
	if st != 200 or not first(avail).get("id"):
		out(f"- app availability: HTTP {st}: not set up yet. The in-app purchase's availability follows the app's,"
			" so it is left unset; run again after the owner sets the app's availability (or use --territories all).")
		return None
	st2, terr = asc.get_all(f"/v2/appAvailabilities/{first(avail)['id']}/territoryAvailabilities",
		{"include": "territory", "limit": "200", "fields[territoryAvailabilities]": "available,territory"})
	ids = sorted(((t.get("relationships") or {}).get("territory") or {}).get("data", {}).get("id", "?")
		for t in terr if (t.get("attributes") or {}).get("available"))
	out(f"- app availability: {len(ids)} territories (HTTP {st2})")
	return ids


def ensure_availability(asc: AscWriter, iap_id: str | None, territories: list[str] | None) -> list[str]:
	if territories is None:
		return ["availability (the app's availability is not set up)"]
	if not territories:
		return ["availability (the app is available in no territory)"]
	if iap_id:
		st, av = asc.get(f"/v2/inAppPurchases/{iap_id}/inAppPurchaseAvailability")
		if st == 200 and first(av).get("id"):
			st2, cur = asc.get_all(f"/v1/inAppPurchaseAvailabilities/{first(av)['id']}/availableTerritories", {"limit": "200"})
			have = sorted(t["id"] for t in cur)
			out(f"  in-app purchase availability: {len(have)} territories (HTTP {st2})")
			if have == territories:
				out("  the same territories as the app: as expected")
				return []
		else:
			out(f"  in-app purchase availability: none yet (HTTP {st})")
	st, _ = asc.send("POST", "/v1/inAppPurchaseAvailabilities", {"data": {"type": "inAppPurchaseAvailabilities",
		"attributes": {"availableInNewTerritories": True},
		"relationships": {"inAppPurchase": {"data": {"type": "inAppPurchases", "id": iap_id or "(new)"}},
			"availableTerritories": {"data": [{"type": "territories", "id": t} for t in territories]}}}},
		f"available in {len(territories)} territories (the app's), and in new ones")
	return [] if (not asc.apply or 200 <= st < 300) else ["availability"]


def ensure_screenshot(asc: AscWriter, iap_id: str | None, path: str | None) -> list[str]:
	data = Path(path).read_bytes() if path else None
	if data is not None and not data.startswith(b"\x89PNG"):
		out(f"- review screenshot: {path} is not a PNG")
		return ["review screenshot"]
	name = Path(path).name if path else ""
	md5 = hashlib.md5(data).hexdigest() if data is not None else ""
	existing: dict = {}
	if iap_id:
		st, shot = asc.get(f"/v2/inAppPurchases/{iap_id}/appStoreReviewScreenshot")
		if st == 200 and first(shot).get("id"):
			existing = first(shot)
			a = existing.get("attributes") or {}
			out(f"- review screenshot: {a.get('fileName')} ({a.get('fileSize')} bytes), state "
				f"{(a.get('assetDeliveryState') or {}).get('state')}")
		else:
			out(f"- review screenshot: none (HTTP {st})")
	if existing:
		a = existing.get("attributes") or {}
		complete = (a.get("assetDeliveryState") or {}).get("state") == "COMPLETE"
		if data is None:
			return [] if complete else ["review screenshot (not complete; give --review-screenshot)"]
		same = (a.get("sourceFileChecksum") == md5) if a.get("sourceFileChecksum") else (
			a.get("fileSize") == len(data) and a.get("fileName") == name)
		if same and complete:
			out(f"  the same file as {path}: as expected")
			return []
		# one review screenshot per in-app purchase: remove the old one, then upload the new file
		st, _ = asc.send("DELETE", f"/v1/inAppPurchaseAppStoreReviewScreenshots/{existing['id']}", None,
			f"remove the old review screenshot ({a.get('fileName')}), replaced by {name}")
		if asc.apply and not 200 <= st < 300:
			return ["review screenshot (the old one could not be removed)"]
	elif data is None:
		return ["review screenshot (App Review needs it; sandbox testing does not)"]
	if not iap_id or not asc.apply:
		asc.send("POST", "/v1/inAppPurchaseAppStoreReviewScreenshots", {}, f"reserve {name} ({len(data)} bytes), upload it, commit")
		return []
	st, body = asc.send("POST", "/v1/inAppPurchaseAppStoreReviewScreenshots", {"data": {"type": "inAppPurchaseAppStoreReviewScreenshots",
		"attributes": {"fileName": name, "fileSize": len(data)},
		"relationships": {"inAppPurchaseV2": {"data": {"type": "inAppPurchases", "id": iap_id}}}}},
		f"reserve {name} ({len(data)} bytes)")
	res = first(body)
	if not 200 <= st < 300 or not res.get("id"):
		return ["review screenshot"]
	if not asc.upload((res.get("attributes") or {}).get("uploadOperations") or [], data):
		return ["review screenshot (upload failed)"]
	st, _ = asc.send("PATCH", f"/v1/inAppPurchaseAppStoreReviewScreenshots/{res['id']}", {"data": {
		"type": "inAppPurchaseAppStoreReviewScreenshots", "id": res["id"],
		"attributes": {"uploaded": True, "sourceFileChecksum": md5}}}, "commit the upload")
	return [] if 200 <= st < 300 else ["review screenshot"]


def main() -> int:
	ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	ap.add_argument("--apply", action="store_true", help="make the changes (default: dry run, GET requests only)")
	ap.add_argument("--territories", choices=["app", "all"], default="app",
		help="in-app purchase availability: the app's territories (default) or every territory")
	ap.add_argument("--review-screenshot", metavar="PNG", help="App Review screenshot of the purchase screen")
	ap.add_argument("--try-uz", action="store_true", help="send the Uzbek localization again (App Store Connect has refused it so far)")
	a = ap.parse_args()
	out(f"## App Store Connect in-app purchase setup: {PRODUCT_ID} ({'APPLY' if a.apply else 'DRY RUN, nothing is changed'})")
	key_id, issuer = os.environ.get("ASC_KEY_ID", "").strip(), os.environ.get("ASC_ISSUER_ID", "").strip()
	p8 = os.environ.get("ASC_KEY_P8_BASE64", "")
	missing = [n for n, v in (("ASC_KEY_ID", key_id), ("ASC_ISSUER_ID", issuer), ("ASC_KEY_P8_BASE64", p8)) if not v]
	if missing:
		out(f"Missing secrets: {', '.join(missing)}")
		return 2
	try:
		key, how = load_key(p8)
	except ValueError as e:
		out(f"- API key: ASC_KEY_P8_BASE64 is not a readable .p8 private key ({e})")
		return 2
	out(f"- API key: {check_key(key)}; decoded as {how}")
	asc = AscWriter(key_id, issuer, key, a.apply)
	app = find_app(asc)
	if not app:
		out("ERROR: exactly one app with this bundle id is required. Nothing was changed.")
		return 1
	iap = ensure_iap(asc, app["id"])
	if not iap and (a.apply or asc.failed):
		out("ERROR: the in-app purchase could not be created or is not as expected; stopping.")
		return 1
	iap_id = iap.get("id")
	todo: list[str] = []
	todo += ensure_localizations(asc, iap_id, a.try_uz)
	todo += ensure_price(asc, iap_id)
	todo += ensure_availability(asc, iap_id, app_territories(asc, app["id"], a.territories))
	todo += ensure_screenshot(asc, iap_id, a.review_screenshot)

	out()
	out("### Result")
	if iap_id:
		st, cur = asc.get(f"/v2/inAppPurchases/{iap_id}")
		ca = first(cur).get("attributes") or {}
		out(f"- {PRODUCT_ID} ({iap_id}): state {ca.get('state')} (HTTP {st}), type {ca.get('inAppPurchaseType')},"
			f" reference name {ca.get('name')!r}")
	else:
		out(f"- {PRODUCT_ID}: does not exist yet (dry run)")
	if not a.apply:
		out(f"- planned changes: {len(asc.planned)}" + ("" if asc.planned else " (none: everything is as expected)"))
	still = list(dict.fromkeys(todo))
	out("- still missing for Ready to Submit: " + ("; ".join(still) if still else "nothing this script can set"))
	out("- always the owner's: the Paid Apps agreement must be active (it is, per the owner, 2026-10-10); the first"
		" in-app purchase is submitted together with an app version (App Store Connect > the version > In-App"
		" Purchases); this script never submits anything.")
	out("- sandbox testing (TestFlight store_sandbox build) works once the product exists with a price; review"
		" approval is not needed for sandbox purchases.")
	if asc.failed:
		out(f"- FAILED requests: {len(asc.failed)}")
		for f in asc.failed:
			out(f"  - {f}")
	summary = os.environ.get("GITHUB_STEP_SUMMARY")
	if summary:
		with open(summary, "a", encoding="utf-8") as f:
			f.write("\n".join(asc_check.LINES) + "\n")
	return 1 if asc.failed else 0


if __name__ == "__main__":
	sys.exit(main())
