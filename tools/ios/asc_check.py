#!/usr/bin/env python3
"""Read-only App Store Connect check for MYSTERY ROOM.

Every request this script makes is an HTTP GET (enforced in Asc.get): it never creates, edits or
deletes anything in App Store Connect or the Apple Developer portal.

It prints only MYSTERY ROOM records: apps whose name contains "Mystery Room" or whose bundle id
contains "mysteryroom", and bundle ids that contain "mysteryroom". Other apps, bundle ids,
certificates and users of the account are read only to be filtered out (or counted) and are never
printed. The JWT, the key id, the issuer id and the team id are never printed.

Environment (GitHub secrets): ASC_KEY_ID, ASC_ISSUER_ID, ASC_KEY_P8_BASE64 (base64 of the .p8; a raw
PEM is accepted too), optional IOS_TEAM_ID (only compared with the App ID prefix, never printed).

Modes:
  (default)  report: the facts for docs/release/IOS_TESTFLIGHT.md, exit 0 when the key works.
  --gate     preflight for ios.yml: exit 3 unless the bundle id is registered AND an app record uses
             it (otherwise Xcode's automatic signing could register a new App ID). Writes
             app_found/next_build to $GITHUB_OUTPUT.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = os.environ.get("ASC_API_BASE", "https://api.appstoreconnect.apple.com").rstrip("/")
LINES: list[str] = []


def out(line: str = "") -> None:
	print(line, flush=True)
	LINES.append(line)


def norm(s: str | None) -> str:
	return re.sub(r"[^a-z]", "", (s or "").lower())


def is_ours_app(attrs: dict, bundle_id: str) -> bool:
	return attrs.get("bundleId") == bundle_id or "mysteryroom" in norm(attrs.get("name")) \
		or "mysteryroom" in norm(attrs.get("bundleId"))


def is_ours_bundle(identifier: str | None, bundle_id: str) -> bool:
	return identifier == bundle_id or "mysteryroom" in norm(identifier)


class Asc:
	def __init__(self, key_id: str, issuer: str, pem: bytes) -> None:
		self._key_id, self._issuer, self._pem = key_id, issuer, pem
		self._token, self._token_at = "", 0.0

	def _jwt(self) -> str:
		import jwt  # PyJWT[crypto]
		now = time.time()
		if not self._token or now - self._token_at > 600:
			payload = {"iss": self._issuer, "iat": int(now), "exp": int(now) + 900, "aud": "appstoreconnect-v1"}
			self._token = jwt.encode(payload, self._pem, algorithm="ES256", headers={"kid": self._key_id, "typ": "JWT"})
			self._token_at = now
		return self._token

	def get(self, path: str, params: dict | None = None) -> tuple[int, dict]:
		url = path if path.startswith("http") else API + path
		if params:
			url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params, safe="[],")
		if not url.startswith(API + "/"):
			raise RuntimeError("refusing a request outside the App Store Connect API")
		for attempt in range(3):
			req = urllib.request.Request(url, method="GET", headers={"Authorization": "Bearer " + self._jwt()})
			try:
				with urllib.request.urlopen(req, timeout=40) as r:
					return r.status, json.loads(r.read() or b"{}")
			except urllib.error.HTTPError as e:
				body: dict = {}
				try:
					body = json.loads(e.read() or b"{}")
				except ValueError:
					pass
				if e.code in (429, 500, 502, 503, 504) and attempt < 2:
					time.sleep(3 * (attempt + 1))
					continue
				return e.code, body
			except urllib.error.URLError as e:
				if attempt < 2:
					time.sleep(3 * (attempt + 1))
					continue
				return 0, {"errors": [{"title": "network error", "detail": str(e.reason)}]}
		return 0, {}

	def get_all(self, path: str, params: dict | None = None, max_pages: int = 50) -> tuple[int, list]:
		status, body = self.get(path, params)
		items = list(body.get("data") or []) if status == 200 else []
		pages = 1
		while status == 200 and (body.get("links") or {}).get("next") and pages < max_pages:
			status, body = self.get(body["links"]["next"])
			items += list(body.get("data") or []) if status == 200 else []
			pages += 1
		return status, items


def err(body: dict) -> str:
	e = (body.get("errors") or [{}])[0]
	return " / ".join(str(e.get(k)) for k in ("code", "title", "detail") if e.get(k)) or "no error body"


def load_pem(raw: str) -> bytes:
	raw = raw.strip()
	if raw.startswith("-----BEGIN"):
		return raw.encode()
	return base64.b64decode("".join(raw.split()), validate=False)


def check_key(pem: bytes) -> str:
	from cryptography.hazmat.primitives import serialization
	from cryptography.hazmat.primitives.asymmetric import ec
	key = serialization.load_pem_private_key(pem, password=None)
	if not isinstance(key, ec.EllipticCurvePrivateKey) or key.curve.name != "secp256r1":
		return "not an EC P-256 key (an App Store Connect .p8 must be)"
	return "EC P-256 private key (format OK)"


def short(s: str | None, n: int = 90) -> str:
	s = (s or "").replace("\n", " ").strip()
	return s if len(s) <= n else s[: n - 1] + "…"


def report_app(asc: Asc, app: dict, bundle_id: str) -> int:
	"""Prints one MYSTERY ROOM app record; returns the highest build number found (0 if none)."""
	a, app_id = app["attributes"], app["id"]
	out(f"### App record {app_id}")
	out(f"- name: {a.get('name')!r}  bundleId: {a.get('bundleId')}  sku: {a.get('sku')}  primaryLocale: {a.get('primaryLocale')}")
	out(f"- bundle id matches the repo ({bundle_id}): {'YES' if a.get('bundleId') == bundle_id else 'NO'}")
	st, full = asc.get(f"/v1/apps/{app_id}")
	if st == 200:
		fa = full["data"]["attributes"]
		keep = {k: fa.get(k) for k in ("contentRightsDeclaration", "isOrEverWasMadeForKids", "subscriptionStatusUrl",
			"streamlinedPurchasingEnabled", "accessibilityUrl") if k in fa}
		out(f"- app attributes: {json.dumps(keep, ensure_ascii=False)}")

	st, infos = asc.get_all(f"/v1/apps/{app_id}/appInfos", {"include": "primaryCategory,primarySubcategoryOne,secondaryCategory"})
	out(f"- appInfos: HTTP {st}, {len(infos)} found")
	for info in infos:
		ia = info.get("attributes") or {}
		rel = info.get("relationships") or {}
		cats = {k: ((rel.get(k) or {}).get("data") or {}).get("id") for k in ("primaryCategory", "primarySubcategoryOne", "secondaryCategory")}
		out(f"  - appInfo {info['id']}: state={ia.get('state') or ia.get('appStoreState')} ageRating={ia.get('appStoreAgeRating')} "
			f"categories={json.dumps(cats)}")
		st2, locs = asc.get_all(f"/v1/appInfos/{info['id']}/appInfoLocalizations")
		out(f"    appInfoLocalizations: HTTP {st2}, locales={[l['attributes'].get('locale') for l in locs]}")
		for loc in locs:
			la = loc["attributes"]
			out(f"    - {la.get('locale')}: name={la.get('name')!r} subtitle={la.get('subtitle')!r} "
				f"privacyPolicyUrl={la.get('privacyPolicyUrl')!r} privacyChoicesUrl={la.get('privacyChoicesUrl')!r}")
		st3, ard = asc.get(f"/v1/appInfos/{info['id']}/ageRatingDeclaration")
		if st3 == 200 and ard.get("data"):
			set_vals = {k: v for k, v in (ard["data"].get("attributes") or {}).items() if v not in (None, False, "NONE")}
			out(f"    ageRatingDeclaration (non-default answers): {json.dumps(set_vals, ensure_ascii=False) if set_vals else 'none answered yet'}")
		else:
			out(f"    ageRatingDeclaration: HTTP {st3}")

	st, vers = asc.get_all(f"/v1/apps/{app_id}/appStoreVersions")
	out(f"- appStoreVersions: HTTP {st}, {len(vers)} found")
	for v in vers:
		va = v["attributes"]
		out(f"  - {va.get('platform')} {va.get('versionString')}: appStoreState={va.get('appStoreState')} "
			f"appVersionState={va.get('appVersionState')} releaseType={va.get('releaseType')} copyright={va.get('copyright')!r}")
		st2, locs = asc.get_all(f"/v1/appStoreVersions/{v['id']}/appStoreVersionLocalizations")
		out(f"    localizations: HTTP {st2}, locales={[l['attributes'].get('locale') for l in locs]}")
		for loc in locs:
			la = loc["attributes"]
			out(f"    - {la.get('locale')}: description={len(la.get('description') or '')} chars {short(la.get('description'), 60)!r}; "
				f"keywords={la.get('keywords')!r}; promotionalText={short(la.get('promotionalText'))!r}; "
				f"supportUrl={la.get('supportUrl')!r}; marketingUrl={la.get('marketingUrl')!r}")

	st, builds = asc.get_all("/v1/builds", {"filter[app]": app_id, "sort": "-uploadedDate", "limit": "200",
		"fields[builds]": "version,uploadedDate,processingState,expired,minOsVersion"}, max_pages=5)
	nums = [int(b["attributes"]["version"]) for b in builds if re.fullmatch(r"\d+", str(b["attributes"].get("version") or ""))]
	out(f"- builds: HTTP {st}, {len(builds)} found, highest build number: {max(nums) if nums else 'none'}")
	for b in builds[:5]:
		ba = b["attributes"]
		out(f"  - build {ba.get('version')} uploaded {ba.get('uploadedDate')} {ba.get('processingState')} expired={ba.get('expired')}")
	st, prv = asc.get_all("/v1/preReleaseVersions", {"filter[app]": app_id, "fields[preReleaseVersions]": "version,platform"}, max_pages=2)
	out(f"- TestFlight versions: HTTP {st}, {[p['attributes'].get('version') for p in prv]}")
	st, groups = asc.get_all(f"/v1/apps/{app_id}/betaGroups", {"fields[betaGroups]": "name,isInternalGroup,publicLinkEnabled"})
	out(f"- TestFlight groups: HTTP {st}, " + (", ".join(
		f"{g['attributes'].get('name')!r} ({'internal' if g['attributes'].get('isInternalGroup') else 'external'})" for g in groups) or "none"))
	st, iaps = asc.get_all(f"/v1/apps/{app_id}/inAppPurchasesV2", {"fields[inAppPurchases]": "productId,name,inAppPurchaseType,state"})
	out(f"- in-app purchases: HTTP {st}, " + (", ".join(
		f"{i['attributes'].get('productId')} [{i['attributes'].get('inAppPurchaseType')}, {i['attributes'].get('state')}]" for i in iaps) or "none"))
	st, avail = asc.get(f"/v1/apps/{app_id}/appAvailabilityV2")
	if st == 200 and avail.get("data"):
		av_id = avail["data"]["id"]
		out(f"- availability: availableInNewTerritories={avail['data'].get('attributes', {}).get('availableInNewTerritories')}")
		st2, terr = asc.get_all(f"/v2/appAvailabilities/{av_id}/territoryAvailabilities",
			{"include": "territory", "limit": "200", "fields[territoryAvailabilities]": "available,territory"})
		avail_ids = sorted(((t.get("relationships") or {}).get("territory") or {}).get("data", {}).get("id", "?")
			for t in terr if (t.get("attributes") or {}).get("available"))
		focus = {c: (c in avail_ids) for c in ("UZB", "RUS", "KAZ", "USA")}
		out(f"  territories: HTTP {st2}, {len(avail_ids)} available of {len(terr)}; {json.dumps(focus)}")
	else:
		out(f"- availability: HTTP {st} (not set up yet or not readable)")
	return max(nums) if nums else 0


def main() -> int:
	ap = argparse.ArgumentParser()
	ap.add_argument("--bundle-id", default="com.mysteryroom.forgotteninstitute")
	ap.add_argument("--gate", action="store_true", help="preflight mode for ios.yml (exit 3 unless record + bundle id exist)")
	ap.add_argument("--min-build", type=int, default=1, help="gate mode: next_build is at least this")
	args = ap.parse_args()
	bundle_id = args.bundle_id

	key_id, issuer = os.environ.get("ASC_KEY_ID", "").strip(), os.environ.get("ASC_ISSUER_ID", "").strip()
	p8, team = os.environ.get("ASC_KEY_P8_BASE64", ""), os.environ.get("IOS_TEAM_ID", "").strip()
	missing = [n for n, v in (("ASC_KEY_ID", key_id), ("ASC_ISSUER_ID", issuer), ("ASC_KEY_P8_BASE64", p8)) if not v]
	out("## App Store Connect read-only check (MYSTERY ROOM)")
	if missing:
		out(f"Missing secrets: {', '.join(missing)}")
		return 2
	out(f"- IOS_TEAM_ID secret present: {'yes' if team else 'no'}")
	try:
		pem = load_pem(p8)
		out(f"- API key: {check_key(pem)}")
	except Exception as e:  # noqa: BLE001 - report the class only, never the key material
		out(f"- API key: cannot be read as a PEM private key ({type(e).__name__}); re-check ASC_KEY_P8_BASE64")
		return 2
	asc = Asc(key_id, issuer, pem)

	st, body = asc.get("/v1/apps", {"limit": "1", "fields[apps]": "bundleId"})
	if st != 200:
		out(f"- Key works: NO (GET /v1/apps -> HTTP {st}: {err(body)})")
		if st == 401:
			out("  401 = the JWT was rejected: wrong key id / issuer id, a revoked key, or a .p8 of another key.")
		return 1
	out("- Key works: yes (GET /v1/apps -> HTTP 200)")

	# Apps: exact bundle-id filter, then a local scan for "Mystery Room" names (others are never printed).
	st, exact = asc.get_all("/v1/apps", {"filter[bundleId]": bundle_id, "fields[apps]": "name,bundleId,sku,primaryLocale"})
	exact = [a for a in exact if a["attributes"].get("bundleId") == bundle_id]
	out(f"- GET /v1/apps?filter[bundleId]={bundle_id}: HTTP {st}, {len(exact)} exact match(es)")
	st, all_apps = asc.get_all("/v1/apps", {"limit": "200", "fields[apps]": "name,bundleId,sku,primaryLocale"})
	ours = {a["id"]: a for a in exact}
	for a in all_apps:
		if is_ours_app(a["attributes"], bundle_id):
			ours[a["id"]] = a
	out(f"- Apps named like \"Mystery Room\" or with a mysteryroom bundle id (scan HTTP {st}): {len(ours)}")

	# Bundle ids (App IDs): exact filter, then a local scan for *mysteryroom* identifiers.
	bfields = {"fields[bundleIds]": "name,identifier,platform,seedId", "limit": "200"}
	st, bexact = asc.get_all("/v1/bundleIds", {"filter[identifier]": bundle_id, **bfields})
	st_all, ball = asc.get_all("/v1/bundleIds", bfields)
	bours = {b["id"]: b for b in bexact + ball if is_ours_bundle(b["attributes"].get("identifier"), bundle_id)}
	registered = [b for b in bours.values() if b["attributes"].get("identifier") == bundle_id]
	out(f"- GET /v1/bundleIds?filter[identifier]={bundle_id}: HTTP {st}; registered: {'YES' if registered else 'NO'}")
	out(f"### Bundle ids containing \"mysteryroom\" (scan HTTP {st_all}): {len(bours)}")
	for b in bours.values():
		ba = b["attributes"]
		prefix = ("matches IOS_TEAM_ID" if ba.get("seedId") == team else "differs from IOS_TEAM_ID") if team else "team id not given"
		out(f"- {ba.get('identifier')}  name={ba.get('name')!r}  platform={ba.get('platform')}  App ID prefix {prefix}")
		st2, caps = asc.get_all(f"/v1/bundleIds/{b['id']}/bundleIdCapabilities")
		out(f"  capabilities: HTTP {st2}, {sorted(c['attributes'].get('capabilityType') for c in caps) or 'none'}")
		st3, profs = asc.get_all(f"/v1/bundleIds/{b['id']}/profiles", {"fields[profiles]": "name,profileType,profileState,expirationDate"})
		out(f"  profiles: HTTP {st3}, " + ("; ".join(
			f"{p['attributes'].get('name')!r} {p['attributes'].get('profileType')} {p['attributes'].get('profileState')} "
			f"expires {str(p['attributes'].get('expirationDate'))[:10]}" for p in profs) or "none"))

	highest = 0
	app_found = False
	for a in ours.values():
		out()
		highest = max(highest, report_app(asc, a, bundle_id))
		app_found = app_found or a["attributes"].get("bundleId") == bundle_id

	# Role probes. The API has no endpoint that returns the calling key's own role.
	out()
	out("### API key role probes (the API cannot report a key's own role)")
	st, certs = asc.get_all("/v1/certificates", {"fields[certificates]": "certificateType", "limit": "200"}, max_pages=3)
	if st == 200:
		counts: dict[str, int] = {}
		for c in certs:
			t = c["attributes"].get("certificateType") or "?"
			counts[t] = counts.get(t, 0) + 1
		out(f"- GET /v1/certificates: HTTP 200 (signing assets readable); team certificate counts by type: {json.dumps(counts)}")
	else:
		out(f"- GET /v1/certificates: HTTP {st} ({err(certs if isinstance(certs, dict) else {})})")
	st, _ = asc.get("/v1/users", {"limit": "1", "fields[users]": "roles"})
	out(f"- GET /v1/users (body discarded): HTTP {st} -> "
		+ ("user management readable: Admin or App Manager key (not Developer/Marketing/Sales)" if st == 200
			else "not readable: the key is NOT Admin (cloud distribution signing needs Admin)" if st == 403 else "inconclusive"))
	out("- Admin vs App Manager cannot be told apart through the API. Cloud-managed distribution signing needs Admin;")
	out("  the macOS export step proves it, or the owner reads the key's Access column in Users and Access.")

	out()
	out(f"### Verdict: bundle id registered={'YES' if registered else 'NO'}; app record with this bundle id={'YES' if app_found else 'NO'}")
	next_build = max(args.min_build, highest + 1)
	out(f"- next build number (CFBundleVersion): {next_build}")
	summary = os.environ.get("GITHUB_STEP_SUMMARY")
	if summary:
		with open(summary, "a", encoding="utf-8") as f:
			f.write("\n".join(LINES) + "\n")
	gh_out = os.environ.get("GITHUB_OUTPUT")
	if gh_out:
		with open(gh_out, "a", encoding="utf-8") as f:
			f.write(f"app_found={'true' if (registered and app_found) else 'false'}\nnext_build={next_build}\n")
	if args.gate and not (registered and app_found):
		out("GATE FAILED: the bundle id must be registered and used by an existing app record before a signed build;")
		out("otherwise Xcode's automatic signing would register a new App ID. Nothing was changed.")
		return 3
	return 0


if __name__ == "__main__":
	sys.exit(main())
