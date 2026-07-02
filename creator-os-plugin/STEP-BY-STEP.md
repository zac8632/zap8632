# Creator OS — Step-by-Step Usage (Cowork Desktop / Claude Code)

You've already installed the plugin. This is the "what do I actually type" guide —
day-to-day usage, not setup.

## How invocation works here vs claude.ai

Because this is installed as a **plugin** (not 18 separate claude.ai skill uploads),
every skill is namespaced under `creator-os:`. Two ways to trigger a skill:

- **Natural language** (works in both Cowork and Claude Code): just describe what you
  want — "pull today's Penang property news" — and the matching skill fires on its
  own based on its description, same as claude.ai.
- **Explicit slash command** (most reliable in Claude Code): `/creator-os:signal-mine`,
  `/creator-os:story-mine`, `/creator-os:reel-scripter`, etc. — one per skill folder
  name. Use this if natural language ever fires the wrong skill or nothing at all.

Both work. If you're ever unsure which skill will fire, just use the explicit
`/creator-os:<name>` form — it removes the ambiguity entirely.

## One-time setup, if not done yet

1. **Run onboarding first** — `/creator-os:onboarding`. This fills in
   `docs/voice-doc.md` and `docs/pillars.md` from a short interview. Every other
   skill checks for these before doing anything and will redirect you here if
   they're still template placeholders — so there's no way to skip this by
   accident. Takes a few minutes, one-time only. Want to change your voice or
   pillars later? Run `/creator-os:onboarding` again — it edits in place instead
   of re-running the full interview.
2. Two Google Sheets: **"Creator OS — Performance Log"** and **"Creator OS — Goal
   State"** — `performance-pulse` and `goal-lock` read/write these.
3. Confirm Google Drive is connected (needed for both Sheets above).

## Step-by-step: a real session, start to finish

### Step 1 — lock the goal (once a month, or when priorities change)
```
/creator-os:goal-lock
lock my goal: 8 new foreign-buyer consultations booked this month from content
```

### Step 2 — get a signal or story (as often as you want new material)

Pick one:
```
/creator-os:signal-mine
pull today's Penang property news
```
or, if you have a specific external article/link:
```
/creator-os:signal-mine
[paste link or headline]
```
or, if it's your own experience:
```
/creator-os:story-mine
[describe what happened, however messy]
```

### Step 3 — fix the opening
```
/creator-os:the-bridge
[paste the angle you picked from step 2]
```

### Step 4 — get the full script
```
/creator-os:reel-scripter
[use the-bridge's opener, or just say "write the reel"]
```
(For a YouTube long-form idea instead of a Reel: `/creator-os:long-form-outline` first,
then script it out. For turning one long video into a week of shorts:
`/creator-os:long-to-short`.)

### Step 5 — package it for the platform
```
/creator-os:caption-and-cta
platform: whatsapp (or linkedin/x/tiktok — NOT instagram, that's penang-ig-templates)
```
For YouTube specifically: `/creator-os:youtube-packaging` for the title/thumbnail pair.

### Step 6 — shoot it and post it yourself
Outside the system — this part's still you.

### Step 7 — log what actually happened (the step that closes the loop)
```
/creator-os:performance-pulse
this got 6.2k views, 340 saves, 12 DMs. comments included: "..."
```
First few posts per platform+format will come back "Provisional" — expected, needs
5 logged entries before a real baseline exists. Keep logging anyway.

### Step 8 — ride a win
```
/creator-os:follow-up-engine
what's next
```
Pulls straight from whatever performance-pulse just logged as a winner — no need to
re-describe it.

### Step 9 — check progress against the goal
```
/creator-os:goal-lock
am I on goal this month
```
Reads real numbers from the Performance Log sheet once there's data in it.

## Weekly cadence (suggested, not required)

- **Monday** — `signal-mine` live pull, pick the week's angle(s)
- **Through the week** — script + post using steps 3-6
- **After each post goes up** — `performance-pulse` log it, same day if possible
- **End of week** — `goal-lock` check-in
- **Monthly** — `skill-opportunity-finder` to see if a new repeatable pattern has
  emerged worth turning into its own skill via `skill-builder`

## If something doesn't fire right

Use the explicit `/creator-os:<skill-name>` form instead of natural language — it's
unambiguous. Full list of names: `onboarding`, `signal-mine`, `story-mine`,
`the-bridge`, `reel-scripter`, `long-form-outline`, `long-to-short`,
`series-planner`, `youtube-ideation`, `youtube-packaging`, `caption-and-cta`,
`newsletter-drafter`, `freebie-suggester`, `audience-gaps`, `follow-up-engine`,
`goal-lock`, `performance-pulse`, `skill-opportunity-finder`, `skill-builder`.

If a skill tells you to run `/creator-os:onboarding` before it'll produce
output, that's expected the first time — it means `docs/voice-doc.md` or
`docs/pillars.md` haven't been filled in yet.
