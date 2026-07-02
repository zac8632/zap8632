---
name: signal-mine
description: Turn Malaysian property news and market chatter -- EdgeProp Malaysia, PenangPropertyTalk.com, The Edge, StarProperty, Bank Negara/OPR, MM2H policy, exchange rates, Penang state news -- into content angles for a Penang real estate personal brand. Triggers on "/signal-mine", "/signal", "mine this", "what's happening in the market", "content ideas from this news", "pull today's property news", "what should I post about this week". Two modes: LIVE (searches sources) and PASTE (creator supplies the dump). Geographic focus is northern Penang Island, with occasional KL/Selangor/national coverage only when macro in scope (OPR, MM2H, budget, foreign ownership rules, exchange rates). Every signal pairs with a personal-branding angle -- how it lets the creator show up as the on-the-ground expert, not just report it.
---

# Signal Mine — Malaysia Property Edition

## Before you start

Check `docs/voice-doc.md` and `docs/pillars.md`. If either file is missing or
still contains the `<!-- TEMPLATE: PENDING SETUP -->` marker, stop here — do
not generate output. Tell the creator this is a one-time setup step and hand
off to `/creator-os:onboarding`. Once onboarding is done, re-run this skill.

Finds the signal in Malaysian property news and turns it into content that builds the creator's personal brand as the go-to authority for foreign/expat/luxury buyers on northern Penang Island — not a news aggregator account.

## Scope

**Primary geography:** Penang Island, northern corridor — Tanjung Tokong, Tanjung Bungah, Gurney Drive, Georgetown, Bayan Lepas (Silicon Island spillover), Penang state-level policy (LRT, PSR reclamation, DOSM data).

**Secondary geography — occasional only:** Kuala Lumpur / Selangor / national-level stories. Include ONLY if at least one of these is true — this is a checklist, not a vibe call:
- It's a Bank Negara OPR/interest rate decision
- It's an MM2H policy change (any tier, deposit requirement, or approval-pace change)
- It's a federal Budget measure affecting property (RPGT, stamp duty, foreign ownership thresholds, HOC-style incentives)
- It's a USD/MYR or SGD/MYR exchange rate move of note
- It's DOSM/NAPIC national market data that includes a Penang-specific breakout
If a KL/Selangor story doesn't hit at least one of these, it's noise for this audience — route it to "The noise to ignore," don't include it as a signal regardless of how big the story is nationally.

**Sources to prioritize:**
- EdgeProp Malaysia (edgeprop.my) — most authoritative for market data, launches, policy analysis
- PenangPropertyTalk.com — Penang's dedicated property portal (developer updates, infrastructure news, MBPP/state announcements, ~150k monthly visits); also has a Telegram channel (@pptlk) worth checking for the freshest posts
- The Edge Malaysia property section
- StarProperty.my
- Malaysian property forums (e.g. Lowyat property subforum) — good for ground-truth buyer sentiment, not headline facts
- Bank Negara Malaysia announcements (OPR)
- MM2H official / Immigration Department updates
- Penang state government / Penang Island City Council (MBPP) announcements
- Developer press releases for northern Penang Island launches specifically

## Macro triggers to watch

Not just Penang-local news — these national/global stories ripple directly into this
audience (foreign/expat/MM2H/luxury buyers) and are worth checking on every LIVE run
even if nothing Penang-specific is happening that week:

- **Bank Negara OPR decisions** (6x/year) — directly affects financing cost conversations with buyers
- **Budget announcements** (RPGT changes, stamp duty exemptions, foreign ownership thresholds, HOC-style incentives)
- **MM2H policy revisions** — tier changes, deposit requirements, approval pace (this audience's single biggest anxiety trigger)
- **USD/MYR and SGD/MYR exchange rate moves** — directly affects purchasing power for Singaporean, Taiwanese, expat buyers; a big MYR move is always worth a post
- **Fed rate decisions (US)** — indirectly moves MYR and regional capital flows
- **Singapore property cooling measures / ABSD changes** — Singaporean buyers often compare directly against Penang as an alternative
- **China/Taiwan economic and travel-policy news** — affects sentiment and capital flow from Chinese and Taiwanese buyer segments
- **DOSM property market data releases** (National Property Information Centre / NAPIC quarterly reports) — hard data for authority-building content
- **Penang Silicon Island / PSR reclamation progress, LRT construction milestones** — Penang-specific but macro-scale, always high interest

When one of these fires, it usually outranks a routine local launch story — flag it as the fastest win unless something hyper-local is more time-sensitive that week.

## Two modes

**LIVE mode** — the creator says something like "pull today's Penang property news" or "/signal-mine live". Claude actively searches the sources above (web search + fetch) for current news, reads the actual articles, and mines them for angles. Follow the copyright rules below strictly — paraphrase, never reproduce article text.

**PASTE mode** — the creator pastes a link, a headline, a forum thread, or a screenshot/quote of something they saw. Claude mines the pasted material directly. Use this when a source is paywalled, forum-gated, or the creator wants to react to something specific they personally spotted (which is often the higher-signal path — see input cues below).

## Not this skill — use instead

- The creator is describing something that happened to THEM or a client (a personal or client story, not external news) → use `story-mine` instead.
- The creator has a post/Reel/video that already published and performed well and wants to ride the win → use `follow-up-engine` instead, which reads from the performance log rather than external news.
- The creator wants Instagram-specific content (captions + Canva visuals via the funnel/hook framework) → that's `penang-ig-templates`, a separate skill; `signal-mine` only produces the angle, not the finished IG asset.

## How to input an idea (cues for the creator)

The sharper the input, the sharper the angles. Use whichever of these fits what you've got — don't overthink it, a rough paste is still useful:

**1. Just a link or headline (fastest):**
```
edgeprop.my/content/[whatever]/OPR-cut-january-2027
```
Claude will fetch it, read it, mine it.

**2. A screenshot** of a forum post, article, or WhatsApp forward — just upload it. Claude reads the text off the image directly.

**3. A quick personal take** — this is the highest-signal input because it's already got your angle in it:
```
saw on PropertyTalk today — bunch of people saying MM2H approvals have slowed down again.
haven't confirmed with my own clients yet but worth checking.
```
That one line is enough — Claude will mine it AND flag that it needs verification before you post it as fact.

**4. A batch dump** — paste 3-5 headlines/links at once if you've been saving tabs all week:
```
1. [EdgeProp] Penang new launches Q2 2026 report
2. [The Edge] Bank Negara holds OPR at 3.00%
3. [PropertyTalk thread] "anyone else notice Tanjung Bungah units sitting longer than usual"
4. [Star] Penang LRT alignment finalised
```
Claude ranks across the whole batch, not just per-item.

**5. "Live mode" trigger** — if you don't have anything saved and just want Claude to go find what's current:
```
/signal-mine live — what's worth posting about in Penang property this week
```

## Inputs

Required (one of):
- A live-mode request (Claude searches the sources above)
- A pasted dump — link(s), headline(s), forum thread text, screenshot, or a personal take

Reads if available:
- `docs/pillars.md` — the creator's pillars and audience (foreign/expat/MM2H/luxury buyers, northern Penang Island)
- `docs/voice-doc.md` — tone
- Recent entries in `data/performance-log.json` — avoid re-mining an angle that already underperformed recently

## Output structure

```
# Signal Mine — [date]

## Sources checked
[LIVE mode: which sources were searched and what came back. PASTE mode: what was supplied.]

## What's in here
[2-line summary]

## The signals worth posting about (ranked)

### 1. [The angle]
**The signal:** [What in the source triggered this — paraphrased, never quoted at length]
**Source:** [EdgeProp / PropertyTalk / Bank Negara / etc. — named, with link if fetched live]
**Geography:** [Penang / KL-Selangor-national]
**Why it's worth posting:** [Relevance to the foreign/expat/luxury buyer audience specifically]
**The take:** [The creator's specific opinion/frame — not just "here's the news"]
**Personal branding angle:** [How this lets the creator show up as the on-the-ground expert — e.g. "confirm/deny this with a real client anecdote," "correct a misconception clients keep raising," "go on record before other agents catch up"]
**Format:** [Reel, carousel, video, WhatsApp broadcast, newsletter]
**Draft hook:** [Climax-led opener]
**Needs verification?** [Flag if this is forum chatter/rumor rather than confirmed fact — never let the creator post unverified claims as fact]

### 2. ...
[Continue for 5-8 signals]

## The noise to ignore
[What's not worth posting, and why — e.g. generic KL launch news outside the audience, unverifiable forum rumors not worth the risk]

## The fastest win
[The one to post about TODAY while it's current]
```

## Process

1. Determine mode: LIVE (search) or PASTE (creator supplied it)
2. LIVE: search EdgeProp, The Edge, StarProperty, Bank Negara, MM2H/Immigration sources, Penang state announcements, and Penang-relevant forum chatter for current stories. Fetch and read the actual articles, don't work off search snippets alone.
3. PASTE: read whatever was supplied — link, headline, thread, screenshot, personal take
4. Filter for genuine relevance to the foreign/expat/MM2H/luxury buyer segment on northern Penang Island; apply the KL/Selangor rule (only if genuinely national in scope)
5. For each strong signal: the angle, source, geography, why it matters, the take, the personal-branding angle, format, draft hook, and a verification flag if it's not confirmed fact
6. Call out the noise to ignore
7. Name the fastest win

## Critical rules

- **Copyright:** never reproduce article text. Paraphrase everything. If a specific figure or exact wording matters (e.g. an exact OPR percentage, an exact policy threshold), state the fact plainly rather than quoting the article's sentence. One short quote under 15 words maximum per source, and only if the exact phrasing is legally/materially significant.
- **Verification flag is mandatory** for anything meeting any of these conditions — this is a checklist, not a judgment call: (a) sourced from a forum, Facebook group, Telegram channel comment, or WhatsApp forward rather than a named news outlet or official announcement; (b) states a specific number (price, threshold, deadline, percentage) that isn't corroborated by a second source; (c) describes a policy or rule change without a named official source (Bank Negara, Immigration Department, MBPP, a developer's own press release). If any of (a)-(c) applies, the flag is mandatory — the creator is a licensed negotiator, not an anonymous content account, and posting unverified claims as fact carries real professional risk.
- Every signal needs BOTH a content angle and a personal-branding angle — this isn't a news recap account, it's building one person's authority. "Here's what happened" is not enough; "here's what happened and here's how you personally comment on it as the expert" is the deliverable.
- Apply the geography rule strictly. Don't let KL/Selangor stories crowd out Penang unless they're genuinely national in scope and material to Penang buyers.
- Rank by relevance to the foreign/expat/luxury buyer audience and the RM800k+ threshold, not by how big the story is nationally.
- Always include the noise-to-ignore section.
- Flag time-sensitivity — some signals are post-today, some are evergreen background for later.
- In LIVE mode, name the actual sources checked in the output, even the ones that turned up nothing useful — the creator should know the search was thorough, not just see the hits.
