---
name: onboarding
description: One-time setup for Creator OS — walks a new user through filling in docs/voice-doc.md and docs/pillars.md before any other skill in this plugin will run. Triggers on "/creator-os:onboarding", "/onboarding", "/setup", "set up creator os", "get started", or automatically whenever another Creator OS skill detects the docs are still template placeholders and hands off here. Also handles "update my voice doc" / "change my pillars" for editing after the first pass.
---

# Creator OS — Onboarding

Every other skill in this plugin reads `docs/voice-doc.md` and `docs/pillars.md`
to write in the creator's voice and stay on their pillars. Those files ship as
templates (marked `<!-- TEMPLATE: PENDING SETUP -->`) and must be filled in
once before anything else runs.

## When you're invoked directly by the user

Run the full interview below.

## When you're invoked as a hand-off from another skill

The other skill detected a template marker and stopped. Say briefly why you're
here ("Creator OS needs your voice doc and pillars filled in before I can do
that — takes a few minutes, one-time only"), then run the interview. Once done,
tell the user to re-run the command they originally wanted.

## The interview

Ask for this in one message, grouped, so the creator can answer in one pass —
don't drip it out question by question:

**Voice**
1. Three to five words that describe your tone
2. Point of view — "I", "we", or mixed, and when
3. Sentence rhythm — short and punchy, long and explanatory, or conversational
4. Any banned phrases, words, or clichés you never want to see
5. Emoji policy — never / sparingly / platform-dependent
6. Your exact sign-off phrasing (for newsletters/captions/videos)
7. Paste 3-5 real lines you've written that sound like you (optional but strongly
   recommended — this is the single highest-signal input)

**Pillars & audience**
8. One sentence: your niche/positioning
9. 3-5 content pillars, each with a one-line description
10. Who exactly you're making content for
11. Primary platforms, in priority order
12. Current goal — what winning looks like right now

If the creator skips optional items, proceed anyway — don't block on anything
except items 1-4, 6, 8-11, which the other skills depend on directly.

## On completion

1. Write the answers into `docs/voice-doc.md` and `docs/pillars.md`, matching
   each template's section headers.
2. Remove the `<!-- TEMPLATE: PENDING SETUP -->` marker and the instructional
   comment block from both files — their presence is what gates every other
   skill.
3. Confirm setup is complete and tell the creator every `/creator-os:*` skill
   is now live.

## Editing later

If the creator says something like "update my voice doc" or "change my
pillars" and the files are already filled in (no template marker), skip the
full interview — ask only what they want to change, then patch just that
section in place. Don't regenerate the whole file from scratch.
