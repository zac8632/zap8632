---
name: newsletter-drafter
description: Write a full newsletter draft in the creator's voice and structure, including subject lines, preview text, body, and CTA. Triggers on "/newsletter-drafter", "/newsletter", "write a newsletter", "draft a newsletter", "newsletter issue", "repurpose this into a newsletter", or any time the creator wants a newsletter written. Reads the voice doc and newsletter style guide. Can write from a topic or repurpose a video/post.
---

# Newsletter Drafter

## Before you start

Check `docs/voice-doc.md` and `docs/pillars.md`. If either file is missing or
still contains the `<!-- TEMPLATE: PENDING SETUP -->` marker, stop here — do
not generate output. Tell the creator this is a one-time setup step and hand
off to `/creator-os:onboarding`. Once onboarding is done, re-run this skill.

Writes complete newsletter drafts in the creator's voice and structure. From a topic, or repurposed from existing content.

## When to run this

- Weekly newsletter
- Repurposing a video/post into an issue
- Promoting an offer via newsletter

## Inputs

Required: one of —
- Topic + 2-3 bullet points
- A video/post to repurpose
- A previous issue to write the next of

Reads if available:
- Voice doc, newsletter style guide, recent issues

## Output structure

```
## Subject lines (3)
1. [Curiosity-led]
2. [Benefit-led]
3. [Identity/contrarian-led]

## Preview text
[Matching the recommended subject line]

## Body
[Full draft in the creator's structure]

## CTA
[Single specific ask]

## Notes
[Read time, pillar, A/B suggestions]
```

## Default structure (override if style guide differs)

1. Climax-led open (never "Hope you're well")
2. Setup
3. The body — the lesson
4. Take-away
5. Sign-off — read the exact phrasing from `voice-doc.md`; never invent or reuse a generic one
6. PS / CTA

## Process

1. Read voice doc and style guide
2. If repurposing, extract the insight — don't transcribe
3. 3 subject lines across angles
4. Match preview text
5. Body in the creator's structure
6. Single CTA

## Critical rules

- Never open with pleasantries. Climax-led always.
- Subject + preview work together, never duplicate.
- Body skim-readable — short paragraphs, line breaks.
- ONE CTA. Multiple asks = no asks.
- Sign-off uses the exact phrasing from `voice-doc.md` — never a generic or invented one.
- 3-5 min read unless content earns more.
