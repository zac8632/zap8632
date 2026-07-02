---
name: follow-up-engine
description: When a piece of content performs well, generate the follow-up content that compounds the win. Triggers on "/follow-up-engine", "/follow-up", "/whats-next", "this performed well", "follow up to this", "what's the next post", "ride this", or any time the creator has a post/Reel/carousel/video that worked and wants the next move. Outputs 5 follow-up angles that capitalise on the validated audience response — not generic repurposing. Reads winners logged by Performance Pulse automatically when no content is pasted directly.
---

# Follow-Up Engine

A post worked. Now what. This skill generates the follow-up content that rides a validated win instead of starting from zero.

## When to run this

- A Reel/post/carousel/video outperformed — capitalise while the audience is warm
- A topic clearly resonated and you want to go deeper
- Building a content streak off a single hit
- Performance Pulse flags a new winner in the performance log

## The principle

When something performs, the audience has TOLD you what they want. The fastest content win is responding to that signal — not chasing the next new idea. This skill turns one hit into a sequence.

## Not this skill — use instead

- The creator wants a fresh idea with no prior published win to build from → use `signal-mine` (external news) or `story-mine` (personal/client story) instead.
- The creator wants to know what questions their audience has about a piece BEFORE or shortly after publishing (not specifically riding a proven win) → use `audience-gaps` instead.

## Inputs

Required:
- The content that performed (the topic/format/angle) — OR pull the latest unactioned winner from `data/performance-log.json` if Performance Pulse is installed and the creator doesn't paste one directly
- Why you think it worked (or the skill infers it) — saves, shares, comments, watch time

Reads if available:
- The actual comments on the winning post (paste them for sharper follow-ups)
- Pillars and goal
- `data/performance-log.json` (winner tier entries, their metrics, and why they were flagged)

## Output structure

```
# Follow-Up Engine — [the winning content]

## Why it worked
[The likely reason this resonated — the signal the audience sent, cited from performance data if available]

## The follow-up angles (5)

### 1. The deeper cut
[Go one level deeper on the exact thing that resonated]
**Format:** [Best format] **Draft hook:** [Climax-led]

### 2. The next question
[Answer the obvious "but what about..." the winning content raised]
**Format / hook**

### 3. The other side
[The contrarian or complementary angle]
**Format / hook**

### 4. The how-to
[If the win was a "what", make the "how". If it was a "how", make the "what".]
**Format / hook**

### 5. The proof
[A case study, example, or result that backs up the winning claim]
**Format / hook**

## Post this next
[The single strongest follow-up to make while the win is hot]
```

## Process

1. Identify why the content worked — the signal the audience sent (from pasted data, or from `performance-log.json` if the creator references a logged winner)
2. Generate 5 follow-up angles that ride that specific signal
3. Each with format and draft hook
4. Name the one to post next
5. If sourced from `performance-log.json`, mark that entry as `actioned: true` after generating the follow-ups

## Critical rules

- Follow-ups must ride the SPECIFIC thing that worked, not the general topic. If a hook framework Reel hit, the follow-up is about hooks — not "more content tips."
- Use the actual comments if supplied — the audience literally tells you the follow-up in the comments.
- Every angle gets a format and a draft hook.
- Name the single next post — the creator needs one clear move, not five maybes.
- Speed matters — frame the fastest-to-ship option when the win is time-sensitive.
- When pulling from the performance log, only pull entries tagged `tier: winner` that are not yet `actioned`.
