---
name: performance-pulse
description: Ingest real performance data for published content — pasted stats, screenshots of analytics dashboards, CSV exports from Instagram/YouTube/TikTok/LinkedIn/newsletter tools, or comment dumps — and turn it into a structured, persistent performance log. Classifies each post as winner/average/underperformer against the creator's own baseline, and automatically feeds winners to Follow-Up Engine, real audience questions to Audience Gaps, and progress to Goal Lock. Triggers on "/performance-pulse", "/pulse", "/log this", "log performance", "here's how this did", "update my stats", "this got X views/likes/saves", "import my analytics", "paste analytics", or any time the creator reports how a piece of content actually performed. This is the closed-loop layer — everything else in this system plans and makes content; this is the only skill that records what actually happened.
---

# Performance Pulse

The skill that closes the loop. Every other skill in this system helps you plan or make content. This one records what actually happened — and makes sure that reality feeds back into the next round of planning instead of evaporating.

## Why this exists

Without this skill, `follow-up-engine` and `audience-gaps` only work if the creator manually remembers to paste in what happened, every single time, from memory. That's a leaky loop — wins get forgotten, patterns never accumulate, and `goal-lock` ends up checking ideas against vibes instead of evidence. Performance Pulse is the ingestion + memory layer that makes the whole system self-correcting over time.

## Honest scope — read this before assuming it's automatic

**This is not a live API puller.** No analytics platform (Instagram Insights, YouTube Studio, TikTok Analytics, LinkedIn, ConvertKit/Beehiiv, etc.) is connected as a live data source in this setup. The creator supplies the numbers — by pasting stats, pasting a CSV export, uploading a screenshot of a dashboard (Claude can read the numbers off an image), or just typing "this got 40k views, 1200 saves." Performance Pulse's job is to take whatever form that arrives in, normalize it, log it permanently, and route it — not to reach out and fetch it itself.

If the creator later connects an analytics MCP/API for a platform, this skill should be the first one upgraded to call it directly instead of waiting for a paste. Until then, the loop closes at "creator reports it" rather than "system detects it" — still fully closed, just not fully autonomous.

## When to run this

- Right after checking stats on a published post/video/newsletter and wanting it logged
- Weekly, to batch-log everything published that week
- Whenever `goal-lock` needs real numbers to check progress against
- Whenever `follow-up-engine` or `audience-gaps` should pull from real data instead of the creator re-describing a win from memory
- Uploading a screenshot of an analytics dashboard and asking "how'd this do"

## Inputs

Required:
- The content this data belongs to (title/topic/platform — enough to identify it)
- The raw performance data, in whatever form it exists: pasted numbers, a CSV, a screenshot image, or a plain description ("got way more saves than usual")

Optional but valuable:
- Actual audience comments/DMs from the post (feeds `audience-gaps` with real questions instead of inferred ones)
- The post's publish date and format (Reel, Short, carousel, long-form, newsletter, etc.)

## The persistent log

**If running in Claude Code** (local filesystem persists across sessions): write to
`data/performance-log.json` — see the JSON shape below.

**If running in Claude.ai** (no persistent local filesystem between chats): use a
**Google Sheet**, not a Doc — a Sheet with real columns is far more reliable for the
Drive tool to read and append to than trying to store a JSON blob inside a Doc, which
risks corruption or misparsing on every write. Use a sheet named "Creator OS —
Performance Log" with this exact column structure, one row per entry:

| id | date_logged | title | platform | format | views | likes | saves | shares | comments | tier | why_flagged | needs_verification | comments_sample | actioned |
|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|

Leave any metric column blank rather than 0 if that number wasn't supplied — never
write 0 for a metric you don't actually have. `actioned` is `TRUE`/`FALSE`. Keep a
second small sheet or a fixed top section for the rolling baseline: one row per
platform+format combination with `views_median`, `saves_median` (or the relevant
primary metric for that platform), `sample_size`, `last_updated`.

Always read the full sheet before appending — never blind-append without checking
what's already logged, to avoid duplicate entries for the same post.

**Local JSON shape (Claude Code only)**, for reference — same fields as the sheet
columns above, structured as:

```json
{
  "entries": [
    {
      "id": "2026-07-02-lumina-cma-reel",
      "date_logged": "2026-07-02",
      "title": "Lumina Residence CMA breakdown Reel",
      "platform": "instagram",
      "format": "reel",
      "metrics": { "views": 42000, "likes": 1800, "saves": 640, "shares": 210, "comments": 95 },
      "tier": "winner",
      "why_flagged": "saves 3.4x the account's 90-day median for Reels",
      "needs_verification": false,
      "comments_sample": ["how do I get this kind of report for my own unit?", "is this only for Lumina or can you do other projects?"],
      "actioned": false
    }
  ],
  "baseline": {
    "instagram_reel": { "views_median": 12000, "saves_median": 190, "sample_size": 24, "last_updated": "2026-07-02" }
  }
}
```

Either way — Sheet or local JSON — this is the system's memory. It accumulates over
time; every log call appends, never overwrites prior entries. `follow-up-engine`,
`audience-gaps`, and `goal-lock` all read from it.

## Tiering logic

A post is tiered against the creator's OWN rolling baseline for that platform+format combination, not generic external benchmarks:

- **Winner:** the primary engagement signal for that format (saves/shares for IG, watch-time-adjacent proxies for YouTube, opens/clicks for newsletter) beats the rolling median by 2x or more.
- **Average:** within roughly 0.5x–2x of the rolling median.
- **Underperformer:** below 0.5x of the rolling median.

**Startup period (fewer than 5 entries for a platform+format):** never assign winner/average/underperformer — tier as **Provisional** every time, and say explicitly how many entries exist so far (e.g. "2 of 5 needed for a real baseline"). Still log the entry and still flag it to `follow-up-engine` if it's an obvious standout by a wide margin (e.g. 5x+ any prior entry) — don't withhold a follow-up opportunity just because the baseline is thin, just label the confidence honestly as "early signal, not yet a validated baseline" rather than a confirmed win.

## Output structure

```
# Performance Pulse — [content logged]

## Logged
[What was recorded, in plain terms — platform, format, the key numbers]

## Tier: [Winner / Average / Underperformer / Provisional — not enough baseline data yet]
[The specific comparison that earned this tier]

## Routed to
- [ ] Follow-Up Engine — [only if tier: winner; note it's ready to run]
- [ ] Audience Gaps — [only if real comments were supplied; note the questions are now logged as real, not inferred]
- [ ] Goal Lock — [always; note the entry now counts toward the locked goal's metric]

## Baseline update
[How this entry shifted the rolling median for this platform+format, if at all]

## Worth knowing
[Any pattern this entry adds to or breaks — e.g. "third Reel in a row where a client-result angle outperformed a tips angle"]
```

## Process

1. Parse whatever the creator supplies — pasted numbers, CSV, screenshot (read the numbers directly off the image), or plain description — into the structured metrics shape
2. Read the existing log — `data/performance-log.json` if running in Claude Code, or the Google Sheet/Doc in Drive if running in Claude.ai; if it doesn't exist yet, create it fresh and tell the creator where it lives
3. Compute the tier against the rolling baseline for that platform+format
4. Append the new entry — never overwrite prior entries
5. Update the rolling baseline for that platform+format
6. If tier is winner, flag it as ready for `follow-up-engine`
7. If real comments were supplied, flag them as ready for `audience-gaps`
8. Note the entry now counts toward whatever `goal-lock` has locked
9. Call out any pattern across entries worth flagging to the creator directly, unprompted — this is the highest-value part of the skill over time

## Critical rules

- Never fabricate metrics. If a number wasn't supplied, leave it out of the entry rather than estimating it.
- Always tier against the creator's OWN rolling baseline, never a generic "good engagement rate" benchmark pulled from general knowledge — those don't reflect this specific audience.
- State plainly when there isn't enough baseline data yet (fewer than 5 prior entries for that platform+format) rather than tiering with false confidence.
- Log accumulates — every entry is additive to `data/performance-log.json`. Never truncate or drop prior entries when writing.
- Be honest that this is creator-reported data, not a live API pull, if asked how the numbers got there.
- Winners get explicitly routed to `follow-up-engine` in the output — don't just log and stop, name the handoff.
- Real comments always beat inferred audience questions — when comments are supplied, say so explicitly so `audience-gaps` knows to prioritize them.
- Surface cross-entry patterns proactively once there's enough data (5+ entries) — this is what makes the loop actually strategic instead of just bookkeeping.
