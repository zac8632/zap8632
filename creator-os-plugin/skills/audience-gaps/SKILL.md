---
name: audience-gaps
description: Surface the questions a creator's audience is silently asking while consuming a piece of content, and what to do with each. Triggers on "/audience-gaps", "/gaps", "/questions", "what will they ask", "audience questions", "what's missing", or any time the creator pastes content (Reel, carousel, script, idea) and wants to know what their audience will wonder. Outputs 3 audience questions with a recommended action for each (patch the gap, make it the next post, or pre-write the reply). Can also pull real questions logged by Performance Pulse from actual comments on published posts.
---

# Audience Gaps

## Before you start

Check `docs/voice-doc.md` and `docs/pillars.md`. If either file is missing or
still contains the `<!-- TEMPLATE: PENDING SETUP -->` marker, stop here — do
not generate output. Tell the creator this is a one-time setup step and hand
off to `/creator-os:onboarding`. Once onboarding is done, re-run this skill.

Surfaces the 3 questions your audience is silently asking while they watch/read your content — and turns each into an action.

## When to run this

- Before publishing — catch gaps that weaken the content
- After publishing — mine the questions for follow-up content
- Planning — see what an idea leaves unanswered before you make it
- Performance Pulse logs recurring unanswered questions in real comments

## Three uses

1. **Gap-finding:** questions reveal what's missing from the content
2. **Follow-up fuel:** each question becomes a follow-up post
3. **Engagement prep:** pre-write replies before publishing for first-hour velocity

## Inputs

Required:
- The content (Reel script, carousel, video idea, post — any format, any stage)

Reads if available:
- Audience insight (the exact pains/language the audience uses)
- The creator's pillars
- `data/performance-log.json` — if the creator pastes real comments logged against a published post, prioritise those actual questions over inferred ones

## Output structure

```
# Audience Gaps — [content title]

## Q1: [The question, in the audience's voice]
**Why they're asking:** [The gap or curiosity that triggers it]
**Source:** [Inferred, or "actual comment logged in performance-log.json"]
**What to do:**
- Patch it: [specific addition to the original]
- OR make it the next post: [drafted hook]
- OR pre-write the reply: [drafted comment/DM response]

## Q2: ...
## Q3: ...

## The biggest gap
[Which of the 3 most weakens the content if unanswered — and the move]
```

## Process

1. Read the content as the audience would
2. If real comments are available (pasted, or logged in `performance-log.json`), prioritise the actual questions over inferred ones — mark them as such
3. Identify the 3 strongest questions a viewer would silently ask
4. For each: why they're asking + the three possible actions
5. Name the biggest gap — the one that most weakens the content if ignored

## Critical rules

- Questions in the AUDIENCE'S voice, not the creator's. What the viewer actually wonders.
- Tie each question to a real gap or curiosity in the content — not generic "tell me more."
- Every question gets all three action options (patch / next post / pre-write reply).
- The biggest-gap call is the deliverable — it's the one to act on first.
- Ground in audience insight where available — real pains beat guessed ones. Real logged comments beat inferred questions every time — always label which kind you're using.
