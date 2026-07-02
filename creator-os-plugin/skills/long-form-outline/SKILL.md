---
name: long-form-outline
description: Turn a YouTube topic into a full long-form video outline — cold open, setup, body sections with payoffs, synthesis, and CTA. Triggers on "/long-form-outline", "/outline", "/yt-outline", "outline this video", "video outline", "structure this video", "youtube structure", or any time the creator has a YouTube topic and needs the structural skeleton before scripting. Outputs the retention-aware structure that a script gets written into.
---

# Long-form Outline

## Before you start

Check `docs/voice-doc.md` and `docs/pillars.md`. If either file is missing or
still contains the `<!-- TEMPLATE: PENDING SETUP -->` marker, stop here — do
not generate output. Tell the creator this is a one-time setup step and hand
off to `/creator-os:onboarding`. Once onboarding is done, re-run this skill.

The structural skeleton for a YouTube long-form video. Built for retention — every section has a payoff, nothing sags.

## When to run this

- Topic locked, need the structure before scripting
- A video idea that's strong but you don't know how to build it
- Restructuring a video that's running long or losing focus

## Not this skill — use instead

- The topic is too big for ONE video and needs to become several connected pieces across platforms → use `series-planner` instead. This skill structures a single video; `series-planner` structures a multi-part arc.

## Inputs

Required:
- The topic or concept

Reads if available:
- Pillars, voice doc, the concept (if briefed elsewhere)
- Target length

## Output structure

```
# Outline — [working title]

**Target length:** [estimate]
**Core promise:** [what the viewer gets — one line]

## Cold open (0:00-0:30)
[The climax-led hook. What's shown/said first. The promise made.]

## Setup (0:30-1:30)
[Why this matters, what's at stake, the stakes that earn the watch time]

## Body
### Section 1: [Title] — [payoff]
[What this covers, the point it makes, the payoff that keeps them watching]

### Section 2: [Title] — [payoff]
[...]

### Section 3: [Title] — [payoff]
[...]

[3-5 sections depending on length]

## Synthesis
[Where it all lands — the through-line tied together]

## CTA
[The single ask, tied to the goal]

## Retention notes
[Where viewers are likely to drop, and the move to hold them at each point]
```

## Process

1. Define the core promise in one line
2. Write the cold open — climax-led
3. Setup — establish the stakes
4. 3-5 body sections, each with its own payoff
5. Synthesis — tie the through-line
6. CTA tied to the goal
7. Flag retention risk points and the holds

## Critical rules

- Every body section needs a payoff. No section ends on setup.
- The cold open is climax-led (pairs with The Bridge).
- Length drives section count — don't pad a 6-minute concept into 12.
- The core promise is the spine — every section must serve it or get cut.
- Retention notes are the differentiator — name where it sags and how to hold.
- This outputs structure, not script. Scripting is the next step.
