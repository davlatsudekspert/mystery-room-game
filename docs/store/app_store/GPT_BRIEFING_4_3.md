# Briefing for a helper AI: App Review 4.3 / 4.2.6 rejections (state on 2026-10-20)

Paste this whole file into the helper AI first. It explains the situation, the verified facts and the rules. The owner talks to it in Uzbek; replies to Apple are written in English.

## 1. Situation
- The owner (developer account holder, signs replies with their own name: [OWNER NAME]) has five iOS apps rejected by App Review under **Guideline 4.3 (Spam)** and **4.2.6 (App Generation Services)**:
  MYSTERY ROOM: Lost Institute (game, v1.0 build 18), FORENSIC EXPERT (v0.3.0), LabGuide Uz, Dental Expert UZ, NFCSTORE. Other apps on the account, not rejected here: Hasharchilar (volunteering), NurseGuide (nursing reference, in development), BugunBor (local deals marketplace).
- Apple's instruction: if the app already meets the guidelines, do NOT resubmit; reply in the Resolution Center and answer nine questions (what it does, users, market gap, beta testing with feedback applied, standalone or suite, could it be an IAP elsewhere, shared code with own apps, shared code with third parties, client/third-party content).
- **Done on 2026-10-20:** a full nine-question reply for every app (05:37–06:13), then one short clarification per app (06:34–06:38). **Nothing was resubmitted.** The status of every app is still "Rejected 4.3.0 Design: Spam" until Apple answers in the same thread (usually 1–3 days).
- Claude Code (the main assistant) is out of usage until about Saturday 2026-10-24, so this helper AI covers replies until then.

## 2. Verified facts (use only these; never invent)
All apps: code written with AI-assisted development tools under the owner's direction and review; owner is the designer and product director and the provider of the concept; no client, no template, no app-generation service. For FORENSIC, LabGuide and Dental, part of the educational content was drafted with AI and then verified item by item by the owner as a subject-matter expert (the owner is a certified state forensic medical expert and biochemist). Each app has its own repository, content, backend and data. The class-test feature (students join by QR/code, take a test, teacher sees results) was first built in LabGuide and adapted for Dental and FORENSIC. NFCSTORE: its code was written by an AI chat, shares no code with the others.

**MYSTERY ROOM facts (verified from its repository):**
- Godot Engine 4.7 (MIT), about 29,000 lines of own GDScript in 72 files, 187 3D models built by own Blender scripts, 100 synthesized audio files, 990+ localized text entries (EN/RU/UZ). Third-party: CC0 textures/props (ambientCG, Poly Haven) and OFL fonts; all listed in docs/ASSET_LICENSES.md.
- Chapters 1–2 free and complete; Chapters 3–4 exist in the code but are hidden in the store build ("Coming soon"); the paid update (Ch3–4, $4.99) is planned later.
- Puzzle answers are generated per new game (anti-walkthrough), consistent across all clues; three hint levels that name where the next step is; offline, no ads, no accounts, no data collected; rated 9+.
- Beta testing started 2026-10-09: TestFlight builds 10–18, Google Play internal builds 13–20; plus automated full playthroughs on random seeds, a random-tapping stress test, layout checks on several screens. Real device-testing findings fixed: text vanished before it could be read; settings did not fit a 20:9 phone and text too big; Chapter 1 control panel too small (pinch-zoom and larger parts added); a selected inventory item blocked taps; a hint showed 3 digits while the safe needed 4 (hint now names the place); Chapter 3 tape recorder kept hissing.
- App icon and logo were made with an AI image tool and disclosed in the submission.

## 3. Rules for the helper AI
1. Never invent facts, numbers, tester counts or dates. If a fact is missing, ask the owner.
2. Every statement must stay consistent with section 2 and with what was already sent (see the separate full-texts file the browser helper saved; ask the owner to paste it if needed). Replies in Resolution Center cannot be edited after sending, so check every sentence.
3. Write each app's reply for that app only. Do not copy text between apps: Apple compares replies from the same account.
4. Never press "Submit for Review" / "Отправить на проверку", never upload a new build, never change metadata, prices or in-app purchases. Only reply in the existing thread.
5. Be honest about AI use; it is allowed. What Apple dislikes is spam, copies, templates and false statements.
6. Do not send the owner's email, phone or password anywhere. Never ask for passwords or 2-step codes.
7. Before sending anything, show the owner the final text and wait for "ha".

## 4. What to do when Apple answers
- **Approved:** tell the owner to press "Выпустить эту версию" (manual release) in App Store Connect.
- **Rejected again for 4.3:** do NOT just argue again. Ask the owner what substantial new value could be shown (Mystery Room: open Chapter 3 or add a clearly new feature; the other apps: new content or features) and wait for Claude Code (Saturday). Meanwhile you may draft a short reply listing what makes the app different, using only section 2 facts.
- **Apple asks a follow-up question:** answer only that question, briefly, with section 2 facts; ask the owner for anything you do not know.
- **A different guideline** (e.g. metadata, screenshots, privacy): read the message, explain it to the owner in Uzbek, propose the smallest fix, and wait for approval before changing anything.

## 5. Mystery Room texts already sent (for reference)
Full reply (06:13) answered all nine questions with the facts above, and a clarification (06:38): "besides the apps I listed, my developer account also has a volunteering app, a nursing reference app (in development) and a local deals marketplace. None of them is a game, and none shares content, code or assets with Mystery Room." The first reply states the game was designed and directed by the owner and built with AI-assisted development tools, and is not made for a client.

The complete texts of all five apps' replies and clarifications are in the full-texts file saved by the browser helper on 2026-10-20 (sections 1–6). Paste that file after this briefing.
