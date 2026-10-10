class_name CreditsData
extends RefCounted
## What the credits say (docs/CREDITS.md, the owner's decision): one source for Settings -> About and the slow
## end credits. Headings are localized; the names stay in Latin script in every language.

const CREATORS: Array[String] = ["Yuldashali Abdurakhmonov", "Aliyorbek Toshtemirov"]
const ENGINE := "Godot Engine"

enum Kind { TITLE, SUBTITLE, HEADING, NAME, LINE, THANKS, GAP }


## The blocks top to bottom: {"kind": Kind, "text": String}.
static func blocks() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	out.append({"kind": Kind.TITLE, "text": "MYSTERY ROOM"})
	out.append({"kind": Kind.SUBTITLE, "text": TranslationServer.translate("game.subtitle")})
	out.append({"kind": Kind.GAP, "text": ""})
	out.append({"kind": Kind.HEADING, "text": TranslationServer.translate("credits.created_by")})
	for n in CREATORS:
		out.append({"kind": Kind.NAME, "text": n})
	out.append({"kind": Kind.GAP, "text": ""})
	out.append({"kind": Kind.LINE, "text": TranslationServer.translate("credits.testers")})
	out.append({"kind": Kind.GAP, "text": ""})
	out.append({"kind": Kind.HEADING, "text": TranslationServer.translate("credits.made_with")})
	out.append({"kind": Kind.NAME, "text": ENGINE})
	out.append({"kind": Kind.GAP, "text": ""})
	out.append({"kind": Kind.LINE, "text": TranslationServer.translate("credits.cc0")})
	out.append({"kind": Kind.GAP, "text": ""})
	out.append({"kind": Kind.THANKS, "text": TranslationServer.translate("credits.thanks")})
	return out
