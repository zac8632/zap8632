---
name: freebie-suggester
description: Turn a content topic or video idea into specific lead-magnet ideas tied to the creator's existing IP and graded on lead-gen power and effort. Triggers on "/freebie-suggester", "/freebie", "freebie ideas", "lead magnet ideas", "what freebie", "what could I give away", or any time the creator is working on content and wants freebie/opt-in ideas that fit. Outputs specific freebies (not generic types), each tied to the topic, with lead-gen and effort grades.
---

# Freebie Suggester

## Before you start

Check `docs/voice-doc.md` and `docs/pillars.md`. If either file is missing or
still contains the `<!-- TEMPLATE: PENDING SETUP -->` marker, stop here — do
not generate output. Tell the creator this is a one-time setup step and hand
off to `/creator-os:onboarding`. Once onboarding is done, re-run this skill.

Turns "I'm posting about X" into specific, buildable lead magnets that connect the content to the creator's offer. Not freebie types — actual freebie ideas.

## When to run this

- Planning a piece of content and want a matching opt-in
- Building a ManyChat keyword funnel and need the freebie
- Designing a lead-gen campaign around a topic
- Refreshing the freebie attached to an evergreen post

## The difference from generic freebie advice

Generic: "Make a PDF, a checklist, a template."
This skill: "20 climax-led hook openings from your top videos — swipe file PDF. Lead-gen: high. Effort: 30 min."

Specific. Tied to existing IP. Graded.

## Inputs

Required:
- The content topic or video idea

Reads if available:
- The creator's pillars, voice, existing offers
- Their existing content library (to tie freebies to existing IP)

## Output structure

```
# Freebie Ideas — [topic]

## The freebies (ranked by lead-gen power)

### 1. [Specific freebie name]
**Format:** [PDF / checklist / swipe file / template / mini-training / Notion doc / etc.]
**What's in it:** [Specific contents]
**Ties to your IP:** [Which existing video/post/framework this draws from]
**Lead-gen power:** [High / Medium / Low — and why]
**Effort to build:** [Time estimate]
**The hook to promote it:** [How you'd tease it in the content]

### 2. ...
[Continue for 3-5 freebies]

## The quick win
[The freebie with the best lead-gen-to-effort ratio — build this one first]

## The keyword
[Suggested ManyChat keyword for the top freebie]
```

## Process

1. Take the topic
2. Generate 3-5 SPECIFIC freebies — named, with contents, tied to existing IP where possible
3. Grade each on lead-gen power and effort
4. Surface the quick win (best ratio)
5. Suggest a ManyChat keyword for the top pick

## Critical rules

- SPECIFIC freebies, never generic types. "A checklist" is a fail. "The 12-point pre-publish checklist I run before every video" is a pass.
- Tie to existing IP wherever possible — repurposing existing content into a freebie is the lowest-effort highest-value move.
- Always grade lead-gen AND effort. The creator needs the ratio to prioritise.
- The quick win is the deliverable — the one freebie to build first.
- Connect the freebie to the funnel — suggest the keyword so it plugs into ManyChat.
