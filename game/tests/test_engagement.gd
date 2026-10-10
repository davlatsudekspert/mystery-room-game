extends TestBase
## The engagement pass on Chapters 1–2 (docs/ENGAGEMENT.md): the texts its beats speak exist in every language, the
## Chapter 1 epilogue agrees with Chapter 2 (the corridor, not a train home), and the Chapter 3 card picks a hand-off
## that matches what the build can do. The scene-level flows (resume at the ending, the cliffhanger, Continue across
## the Chapter 1 → 2 hand-off) are checked by qa/transition_check.tscn and qa/teaser_shots.tscn.

const KEYS := ["cap1.draught", "cap1.corridor", "cap1.beam_b", "epi1.postmark",
	"cap2.reel_41", "cap2.reel_42", "cap2.vault_answers", "cap2.whisper", "achv.forty_two", "cap2.rumble",
	"cap2.shaft_lamps", "cap2.shaft_hum", "tease2.voice_1", "tease2.voice_2", "tease2.voice_3", "tease2.voice_who",
	"tease2.second_cap", "tease2.second_voice", "tease2.tag_strand_key", "tease2.tag_leyla_key", "tease2.coming_soon",
	"tease2.unlock_line", "tease2.continue_story", "tease2.not_now", "msg.c2_crystal_dark", "msg.c2_crystal_blur",
	"msg.c2_crystal_mixed", "msg.c2_crystal_waits", "msg.c2_mixed", "epi2.recorder", "chapter.ch3.title"]


func test_engagement_texts_exist_in_every_language() -> void:
	for loc in ["en", "ru", "uz"]:
		TranslationServer.set_locale(loc)
		for k: String in KEYS:
			check(tr(k) != k and tr(k).strip_edges() != "", "%s untranslated in %s" % [k, loc])
	TranslationServer.set_locale("en")


func test_ch1_epilogue_ends_in_the_corridor() -> void:
	var l := Lab7Logic.new()
	l.reset()
	l.state["choice"] = "leave_lens"
	var keys := l.epilogue_keys()
	eq(keys[-1], "epi1.postmark", "the postmark line is read under the corridor lamp")
	check(not keys.has("epi.postmark"), "the train-home line is gone from the epilogue")
	TranslationServer.set_locale("en")
	check(not tr("epi1.postmark").to_lower().contains("train"), "no train home: Chapter 2 continues beyond the door")
	check(tr("epi1.postmark").contains("1979"), "the 1979 postmark (story twist 1) is still told")


func test_ch3_card_hand_off_matches_the_build() -> void:
	var st := ArchiveTeaser.card_state()
	check(st in ["soon", "unlock", "play"], "card state %s" % st)
	if Premium.can_play("ch3"):
		eq(st, "play", "a playable Chapter 3 is never sold again")
	elif not bool(Chapters.get_chapter("ch3").get("released", false)) or not Premium.store_open():
		eq(st, "soon", "unreleased, or no store (real payments off): coming soon, no buy button")
	else:
		eq(st, "unlock", "released and sellable: the card offers the purchase screen")
