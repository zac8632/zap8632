---
name: long-to-short
description: Turn a YouTube long-form video into short-form scripts (Reels, Shorts, TikTok) ready to shoot or clip. Triggers on "/long-to-short", "/repurpose", "/clips", "turn this into shorts", "reels from this video", "short form from long form", "clip this video", or any time the creator has a long-form video (transcript or topic) and wants short-form versions. Identifies the most clippable moments and writes them as standalone short scripts.
---

# Long-to-Short

One long-form video becomes a week of short-form. Finds the most clippable moments and writes them as standalone shorts.

## When to run this

- Published a YouTube video, want Reels/Shorts/TikToks from it
- Maximising one piece of long-form into a content week
- Finding the standalone moments inside a longer narrative

## Inputs

Required:
- The long-form video (transcript ideal, topic + key points acceptable)

Reads if available:
- Voice doc
- Which platforms to cut for (Reels, Shorts, TikTok)

## Output structure

```
# Short-form from [video title]

## The clippable moments (ranked)

### Short 1: [The moment]
**Why it stands alone:** [What makes this work without the full video context]
**The script:**
- Opener (climax-led): [line]
- Beat 1: [line]
- Beat 2: [line]
- Beat 3: [line]
- CTA: [line]
**Source timestamp:** [where in the long-form this came from, if known]

### Short 2: ...
[Continue for 5-7 shorts]

## Post this first
[The strongest standalone short]

## Sequencing
[Suggested order to post these across the week to build on each other]
```

## Process

1. Read the long-form
2. Identify 5-7 moments that work as standalone shorts
3. For each: why it stands alone + the full short script (climax-led)
4. Rank them, name the first to post
5. Suggest posting sequence across the week

## Critical rules

- Each short must STAND ALONE — work without the viewer having seen the long-form.
- Climax-led openers (pairs with The Bridge).
- The moment must be genuinely clippable — not every section of a video is short-form material. Cut weak ones.
- 5-7 shorts max from one video — quality over volume.
- Sequence them — these should build a content week, not just exist as fragments.
- Match the voice doc.
