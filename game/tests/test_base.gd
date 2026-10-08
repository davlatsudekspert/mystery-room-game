class_name TestBase
extends RefCounted
## Minimal assertion helper for the zero-dependency test runner (tests/run_all.gd).

var failures: Array[String] = []
var checks := 0
var current := ""


func check(cond: bool, msg: String) -> void:
	checks += 1
	if not cond:
		failures.append("%s: %s" % [current, msg])


func eq(actual: Variant, expected: Variant, msg: String = "") -> void:
	checks += 1
	if typeof(actual) != typeof(expected) or actual != expected:
		failures.append("%s: %s expected <%s> got <%s>" % [current, msg, str(expected), str(actual)])


func has(events: Array, e: String, msg: String = "") -> void:
	check(events.has(e), "%s missing event '%s' in %s" % [msg, e, str(events)])


func lacks(events: Array, e: String, msg: String = "") -> void:
	check(not events.has(e), "%s unexpected event '%s' in %s" % [msg, e, str(events)])
