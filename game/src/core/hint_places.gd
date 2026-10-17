class_name HintPlaces
extends RefCounted
## Where each hint goal's next step is: a short place name (a localisation key) per goal of Chapters 1-4.
## Pure data, no scene access. The hint dialog shows "Next step: <place>" so the player does not take the
## answer for the close-up they happen to stand in front of (owner, 2026-10-11).

const PLACES: Dictionary = {
	# Chapter 1
	"notebook": "obj.desk", "drawer": "hintplace.drawer", "take_lamp": "hintplace.drawer",
	"gearbox": "obj.gearbox", "take_cell": "obj.gearbox", "lamp": "hintplace.bag", "cipher": "hintplace.notebook",
	"safe": "obj.safe", "take_safe": "obj.safe", "compartment": "obj.desk", "key": "obj.desk",
	"take_handle": "obj.desk", "handle": "obj.panel", "circuits": "obj.panel", "valve": "obj.radio",
	"tune": "obj.radio", "books": "hintplace.bookcase", "shadow": "hintplace.shadow",
	"take_mirror": "hintplace.cabinet", "record": "hintplace.emblem", "retrieve_lens": "hintplace.emblem",
	"lens": "obj.projector", "projector": "obj.projector", "mount_mirror": "obj.mirror_a",
	"mirrors": "hintplace.mirrors", "finale": "hintplace.door",
	# Chapter 2
	"c2_catalogue": "hintplace.catalogue", "c2_compressor": "obj2.compressor", "c2_punch": "obj2.punch",
	"c2_dispatch": "obj2.station", "c2_take_file": "obj2.station", "c2_locker": "obj2.lockers",
	"c2_take_receiver": "obj2.lockers", "c2_hunt": "hintplace.hunt", "c2_tape": "obj2.deck",
	"c2_booth": "obj2.booth", "c2_splice": "obj2.splicer", "c2_take_reel": "obj2.splicer",
	"c2_project": "obj2.projector", "c2_take_crystal": "obj2.booth", "c2_focus": "obj2.projector",
	"c2_record_sign": "obj2.screen", "c2_mark": "obj2.slides", "c2_ports": "obj2.vault_open",
	"c2_align": "obj2.vault_open", "c2_wheel": "obj2.vault_open", "c2_finale": "obj2.vault_open",
	# Chapter 3
	"c3_interlock": "obj3.switch_room", "c3_heart": "obj3.office", "c3_choir": "obj3.choir",
	"c3_restore": "obj3.switch_room", "c3_startup": "obj3.desk", "c3_seed": "obj3.library",
	"c3_grow": "obj3.autoclave", "c3_prisms": "obj3.prisms", "c3_melody": "obj3.camp",
	"c3_rings": "obj3.glass_floor", "c3_resonance": "obj3.console", "c3_finale": "obj3.gallery",
	# Chapter 4
	"c4_power": "obj4.bridge", "c4_box": "obj4.gear_box", "c4_sun": "obj4.apse", "c4_iris": "obj4.iris",
	"c4_align": "obj4.handwheels", "c4_keys": "obj4.catwalk", "c4_cage": "obj4.island",
	"c4_collar": "obj4.collar", "c4_lens": "obj4.core", "c4_pawl": "hintplace.chronometer",
	"c4_note": "obj4.core", "c4_reversal": "obj4.desk", "c4_finale": "obj4.core",
}


## The localisation key naming the place of the goal's next step; "" when the goal has none.
static func place_key(goal: String) -> String:
	return str(PLACES.get(goal, ""))
