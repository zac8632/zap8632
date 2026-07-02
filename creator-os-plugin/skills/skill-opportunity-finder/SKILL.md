---
name: skill-opportunity-finder
description: Scan the creator's recent Claude conversations and surface patterns worth turning into reusable skills. Triggers on "/skill-opportunity", "/find-skills", "what should I make a skill for", "skill opportunities", "what's repeatable", "audit my chats for skills", or any time the creator wants to know what to package next. Uses conversation_search and recent_chats to find repeated patterns and proposes them as skill candidates with rationale and ROI.
---

# Skill Opportunity Finder

The meta skill that tells you what to build next. Scans your chat history, finds what you keep repeating, proposes the skills.

## When to run this

- Quarterly workflow audit
- After heavy Claude usage when patterns have emerged
- Setting up a first skills pack — find the highest-leverage ones first
- When you catch yourself asking Claude the same thing repeatedly

## How it works

Uses conversation_search and recent_chats to scan recent conversations and identify patterns repeated 3+ times.

## Inputs

Optional:
- Time window (default 90 days)
- Domain filter (e.g. content only, not admin)
- Minimum frequency (default 3)

## Output structure

```
# Skill Opportunities — [date]

## Scanned
[Time window, conversations reviewed, patterns found]

## Top opportunities (ranked by leverage)

### 1. [Pattern name]
**What you keep doing:** [The repeated task]
**Frequency:** [X times in Y days]
**Example chats:** [Specific chats as evidence]
**Why it's a skill:** [Rationale]
**Proposed name + triggers:** [name + phrases]
**ROI:** [Time saved per use × frequency]

### 2. ...

## Should NOT be skills
[Patterns better left as one-off chats, and why]

## Build this first
[The single top pick]
```

## Process

1. recent_chats to pull the window
2. conversation_search for repeated patterns by keyword
3. Cluster similar tasks
4. Rank by frequency × leverage
5. For each: name, evidence, proposed skill, ROI
6. Flag 2-3 that should NOT be skills
7. Name the top pick → hand off to Skill Builder

## Critical rules

- 3+ occurrences to qualify. Two is coincidence.
- Cite SPECIFIC chats as evidence.
- Always include "should not be skills" — skill bloat is real.
- Rank by leverage, not raw frequency.
- End with the handoff to Skill Builder.
