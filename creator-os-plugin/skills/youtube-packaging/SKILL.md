---
name: youtube-packaging
description: Generate YouTube title and thumbnail-word pairs that follow the pairing principle — title and thumb do different jobs and never echo each other. Triggers on "/youtube-packaging", "/yt-package", "/title", "/thumb", "title for this video", "thumbnail word", "title and thumb", "package this video", or any time the creator needs YouTube packaging. Returns 3 title + thumb pairs with rationale, plus a critique mode for draft titles.
---

# YouTube Packaging

## Before you start

Check `docs/voice-doc.md` and `docs/pillars.md`. If either file is missing or
still contains the `<!-- TEMPLATE: PENDING SETUP -->` marker, stop here — do
not generate output. Tell the creator this is a one-time setup step and hand
off to `/creator-os:onboarding`. Once onboarding is done, re-run this skill.

Titles and thumbnail words as paired packages. The pairing principle: title sets context, thumbnail creates curiosity — they never say the same thing.

## The pairing principle

- **Title:** the context, the keywords, the "what." The algorithm reads it.
- **Thumbnail words:** the curiosity, the contrast, the "wait, what?" The human reacts to it.
- Overlap = wasted real estate. They must do different jobs.

## When to run this

- New video, packaging unwritten
- Underperforming title, need alternatives
- Critiquing a draft title/thumb

## Modes

**Generate:** topic/concept in → 3 title + thumb pairs.
**Critique:** draft title/thumb in → verdict + fixes.

## Inputs

Generate: video topic or concept, target pillar, length.
Critique: the draft title and/or thumb words.

## Output — Generate mode

```
# YouTube Packaging — [topic]

## Pair 1
**Title:** [text]
**Thumb words:** [1-3 words]
**The pairing:** [How they do different jobs and combine]

## Pair 2 / Pair 3
[Same]

## Recommendation
[Which to lead with and why]
```

## Output — Critique mode

```
# Packaging Critique — [draft]

## Verdict: [Pass / Fix / Fail]
## Working: [...]
## Not working: [...]
## Pairing check: [Is the thumb doing a different job than the title?]
## 3 fixes: [Revised pairs]
```

## Process

Generate: 3 pairs across different angles (curiosity, benefit, identity), each with pairing rationale, then recommend.
Critique: check the pairing principle, name what works and what doesn't, give 3 fixes.

## Critical rules

- Title and thumb NEVER echo. Reject any pair where a thumb word appears in the title.
- Titles under 60 characters where possible.
- Thumb words: 1-3 max.
- Never sacrifice clarity for curiosity — the pair must tell the viewer what they get.
- 3 pairs minimum in Generate mode.
- Critique always ends with constructive fixes.
