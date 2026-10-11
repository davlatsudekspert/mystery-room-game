#!/usr/bin/env python3
"""Read-only Google Play check for MYSTERY ROOM (run by .github/workflows/play-check.yml).

It opens an API edit, reads the testing tracks (releases, version codes, status, release-note languages), the store
listing languages with their texts' lengths, and the number of uploaded graphics per language, then deletes the edit.
It never commits an edit, so nothing changes in Play Console. It prints no e-mail addresses, keys or tokens.

Env: PLAY_SERVICE_ACCOUNT_JSON (the service account's JSON key, the same secret android.yml uploads with).
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import jwt # PyJWT (with cryptography for RS256)

PACKAGE = "com.mysteryroom.forgotteninstitute"
API = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications/" + PACKAGE
SCOPE = "https://www.googleapis.com/auth/androidpublisher"
IMAGE_TYPES = ["icon", "featureGraphic", "phoneScreenshots", "sevenInchScreenshots", "tenInchScreenshots"]


def token(sa: dict) -> str:
    now = int(time.time())
    assertion = jwt.encode({"iss": sa["client_email"], "scope": SCOPE, "aud": sa["token_uri"], "iat": now,
        "exp": now + 600}, sa["private_key"], algorithm="RS256")
    body = urllib.parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": assertion}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(sa["token_uri"], data=body), timeout=30) as r:
            return json.load(r)["access_token"]
    except urllib.error.HTTPError as e:
        raise RuntimeError("token request -> HTTP %d" % e.code) from None


def call(tok: str, method: str, path: str) -> dict:
    req = urllib.request.Request(API + path, method=method, headers={"Authorization": "Bearer " + tok},
        data=b"{}" if method == "POST" else None)
    if method == "POST":
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        msg = ""
        try:
            msg = json.loads(e.read()).get("error", {}).get("message", "")
        except Exception:
            pass
        raise RuntimeError("%s %s -> HTTP %d %s" % (method, path or "/", e.code, msg)) from None


def main() -> int:
    raw = os.environ.get("PLAY_SERVICE_ACCOUNT_JSON", "")
    if not raw.strip():
        print("PLAY_SERVICE_ACCOUNT_JSON is empty")
        return 1
    sa = json.loads(raw)
    tok = token(sa)
    print("## Google Play read-only check (MYSTERY ROOM, %s)" % PACKAGE)
    edit = call(tok, "POST", "/edits")["id"]
    try:
        print("\n### Tracks")
        for t in call(tok, "GET", "/edits/%s/tracks" % edit).get("tracks", []):
            rels = t.get("releases", [])
            if not rels:
                print("- %s: no release" % t["track"])
                continue
            for rel in rels:
                notes = ", ".join(n.get("language", "?") for n in rel.get("releaseNotes", [])) or "none"
                print("- %s: release '%s', versionCodes %s, status %s%s, release notes: %s" % (t["track"],
                    rel.get("name", ""), ",".join(rel.get("versionCodes", [])) or "-", rel.get("status", "?"),
                    (", userFraction %s" % rel["userFraction"]) if "userFraction" in rel else "", notes))
        print("\n### Store listing (what the API sees)")
        for li in call(tok, "GET", "/edits/%s/listings" % edit).get("listings", []):
            lang = li.get("language", "?")
            print("- %s: title '%s', short %d chars, full %d chars" % (lang, li.get("title", ""),
                len(li.get("shortDescription", "")), len(li.get("fullDescription", ""))))
            counts = []
            hashes = []
            for it in IMAGE_TYPES:
                imgs = call(tok, "GET", "/edits/%s/listings/%s/%s" % (edit, lang, it)).get("images", [])
                counts.append("%s %d" % (it, len(imgs)))
                hashes += ["%s:%s" % (it, str(im.get("sha256", ""))[:16]) for im in imgs]
            print("    graphics: " + ", ".join(counts))
            if hashes: # sha256 prefixes: compare with the files in docs/store/google_play (sha256sum)
                print("    sha256: " + " ".join(hashes))
    finally:
        call(tok, "DELETE", "/edits/%s" % edit) # discard: nothing is ever committed
        print("\n(the API edit was deleted; nothing was changed)")
    print("\nNote: the API shows releases and their rollout status, not Google's review state. "
        "\"In review\" / \"approved\" is shown only in Play Console (Publishing overview) and by e-mail.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as e:
        print("error:", e)
        sys.exit(1)
