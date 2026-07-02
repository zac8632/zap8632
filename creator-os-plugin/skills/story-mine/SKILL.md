---
name: story-mine
description: Take a personal experience, client story, or moment the creator describes and surface the 3-5 content angles hiding inside it. Triggers on "/story-mine", "/story", "mine this story", "turn this into content", "what content is in this", "content from my experience", or any time the creator describes something that happened to them or a client and wants the postable angles pulled out. Outputs distinct angles (the lesson, the contrarian take, the framework, the proof, the relatable moment) each with a format and a draft hook. Turns lived experience into content.
---

# Story Mine

## Before you start

Check `docs/voice-doc.md` and `docs/pillars.md`. If either file is missing or
still contains the `<!-- TEMPLATE: PENDING SETUP -->` marker, stop here — do
not generate output. Tell the creator this is a one-time setup step and hand
off to `/creator-os:onboarding`. Once onboarding is done, re-run this skill.

Turns a story into content. The creator describes something that happened (to them, a client, their audience) and the skill pulls out the distinct content angles hiding inside it. The skill that makes your own life the most original content source you have.

## When to run this

- A client got a result and you want to post about it
- Something happened in your own journey worth sharing
- You have a great story but don't know how to turn it into content
- You're sitting on experience that isn't becoming content because you can't see the angle

## Why this matters

Lived experience is the one content source an AI can't generate and a competitor can't copy. Most creators waste their best stories because they only see one angle (usually "here's what happened"). A single story usually contains five different posts. This skill finds them.

## Not this skill — use instead

- The creator is reacting to external news, market data, or something they read/saw online (not their own or a client's lived experience) → use `signal-mine` instead.
- The creator has a post that already published and performed well → use `follow-up-engine` instead.

## Inputs

Required:
- The story or experience, described however the creator naturally tells it (messy is fine)

Reads if available:
- Voice doc, pillars, audience insight, the current goal

## The angles it pulls

From one story, it surfaces up to five distinct angle types:

1. **The lesson** — the takeaway, taught directly. The most obvious angle, so it's never the only one.
2. **The contrarian take** — the part of the story that argues against conventional wisdom in the niche.
3. **The framework** — the repeatable system or steps hidden inside what happened, extracted so others can use it.
4. **The proof / case study** — the story as evidence for a claim the creator already makes.
5. **The relatable moment** — the human, emotional, or vulnerable beat that builds connection more than information.

Not every story has all five. The skill only surfaces the ones genuinely present.

## Output structure

```
# Story Mine — [the story in a few words]

## What's in here
[One line: the raw story, and why it's worth mining]

## The angles

### 1. [Angle type] — [working title]
**The angle:** [The specific take, not just the topic]
**Why it works:** [What makes this angle land for the audience]
**Format:** [Reel / carousel / YouTube / newsletter / thread]
**Draft hook:** [Climax-led opener]

### 2. ...
[Continue for the angles genuinely present, up to 5]

## The strongest angle
[Which one to make first, and why it's the best use of this story]

## Don't waste this
[If the story has a rare or especially valuable element, flag it so the creator doesn't bury it in a throwaway post]
```

## Process

1. Read the story as told, however messy
2. Identify which of the five angle types are genuinely present (don't force all five)
3. For each: the specific angle, why it works, the format, a climax-led draft hook
4. Name the strongest angle and why
5. Flag anything rare in the story that deserves more than a throwaway post

## Critical rules

- Pull the angles ACTUALLY in the story. Never invent events or details that weren't described. If the creator says a client lost weight, don't fabricate a number they didn't give.
- The lesson angle is the obvious one, so never stop there. The value is the other four.
- Every angle gets a format and a draft hook, not just a topic.
- Don't force five. A simple story might only hold two real angles. Two strong beats five padded.
- The contrarian and framework angles are usually the highest-value, because they're the least obvious. Prioritise finding them.
- Match the voice doc. The hooks should sound like the creator, not generic.
- This is about REAL experience. If the creator describes something vague, ask for the specific detail (what actually happened, what changed, what was said) before mining, because specifics are what make a story postable.
