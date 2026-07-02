---
name: goal-lock
description: Lock the creator's current primary goal and filter every piece of work through it. Triggers on "/goal-lock", "/goal", "goal check", "monetization focus", "is this on goal", "keep me focused", or any time the creator wants to make sure what they're working on actually serves their current objective. Reads the locked goal and tells the creator whether the current idea/draft/plan moves them toward it — and if not, what would. Grounds the check in real performance data from Performance Pulse when available, not just judgment calls. The skill that stops creators making content for content's sake.
---

# Goal Lock

The strategic filter. Lock one primary goal, then run any idea, draft, or plan through it before committing time.

## When to run this

- Start of a batching session — set the lens for everything you make
- Mid-work gut check — "is this thread/Reel/video actually serving the goal?"
- Whenever a shiny new idea appears and you need to know if it's a distraction
- Quarterly reset — change the locked goal as priorities shift
- Weekly, to check actual logged performance against the goal metric (pulls from `data/performance-log.json`)

## How it works

The skill holds ONE primary goal at a time. Everything gets measured against it. The goal can be any of:
- Revenue (hit £X this quarter from content)
- Audience growth (get to X followers/subs)
- Audience quality (attract the RIGHT audience, not just more)
- Lead capture (X emails/month into the funnel)
- Authority (become known for a specific thing)

## Inputs

First run: the creator states the goal. Skill confirms and locks it — write to
`data/goal-state.json` if running in Claude Code, or to a single row in a Google Sheet
named "Creator OS — Goal State" if running in Claude.ai (columns: `goal`, `metric`,
`timeframe`, `date_locked`). A Sheet row is more reliable to read/update reproducibly
than free text in a Doc. Overwrite that one row when the goal changes — this state
isn't cumulative like the performance log, only the current lock matters.
Every run after: the creator pastes an idea, draft, content plan, or decision. Skill filters it.

Reads if available:
- The performance log (`data/performance-log.json` in Claude Code, or the "Creator OS
  — Performance Log" Sheet in Claude.ai) — actual logged results, to ground the check
  in real numbers instead of a guess

## Output structure

```
# Goal Check — [the locked goal]

## The goal
[Restated, with the metric and timeframe]

## Where you actually stand
[If performance-log.json has entries: real progress toward the metric — e.g. "14 of 40 target leads captured this month, from 6 logged posts." If no log data yet: "No performance data logged yet — this check is judgment-only. Run Performance Pulse after posting to make this check evidence-based."]

## What you brought
[One-line summary of the idea/draft/plan]

## On goal? 
[YES / PARTIALLY / NO]

## The reasoning
[2-3 sentences. Does this move the needle on the goal? How directly? Reference real performance data if available — e.g. "your last 3 lead-capture CTAs converted at 2x your educational posts, so this format is on-goal."]

## If it's not fully on-goal — the fix
[Specific change that would make it serve the goal. Or: "park this, here's what to do instead."]

## The sharper version
[How to take the same idea and make it pull harder toward the goal]
```

## Process

1. If no goal is locked, ask for it. Confirm the metric and timeframe. Lock it (local file in Claude Code, or Drive doc/sheet in Claude.ai).
2. Check the performance log for real progress against the metric, if it exists
3. Take the idea/draft/plan the creator brings
4. Assess honestly — on goal, partially, or off — grounded in real data where possible
5. If off or partial, give the specific fix
6. Always offer the sharper version — the same idea pulling harder toward the goal

## Critical rules

- ONE goal at a time. If the creator names three goals, force a priority — which ONE comes first.
- Be honest. If something is off-goal, say so. The skill is useless if it rubber-stamps everything.
- The goal is about social media outcomes — followers, leads, revenue, authority, audience quality. Not vanity.
- Never just judge — always give the fix or the sharper version. The creator should leave with an action.
- If the creator keeps bringing off-goal ideas, name the pattern. "This is the third off-goal idea today — what's pulling you away from the goal?"
- Prefer real performance-log data over assumption whenever it exists. If it doesn't exist yet, say so plainly rather than inventing numbers.
