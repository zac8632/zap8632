# Creator OS — plugin

19 bundled skills for a content creator's personal brand: onboarding, signal
mining, story mining, scripting, packaging, and performance tracking. Packaged
as a proper plugin (one `.claude-plugin/plugin.json` manifest + `skills/`
directory) so it installs as one unit instead of separate uploads.

## Install (share this with other users)

This repo doubles as a plugin marketplace via `.claude-plugin/marketplace.json` at
the repo root. Anyone with access to this repo can install from inside Claude Code:

```
/plugin marketplace add <owner>/<repo>
/plugin install creator-os
```

That's it — all skills load as `creator-os:<skill-name>`, e.g.
`/creator-os:signal-mine`. To pick up updates later:

```
/plugin marketplace update creator-os-marketplace
/plugin update creator-os
```

**Local dev / no marketplace access:**
1. Clone or unzip this folder somewhere
2. `claude --plugin-dir /path/to/creator-os-plugin`
3. Run `/reload-plugins` inside that session if the skills don't show up right away

## First run: onboarding (required, one-time)

Right after installing, run:

```
/creator-os:onboarding
```

This is a short interview that fills in `docs/voice-doc.md` and
`docs/pillars.md` — the creator's tone, banned phrases, sign-off, pillars, and
audience. Every other skill in this plugin reads those two files and refuses
to produce output until they're filled in (they check for a template marker
and hand off to onboarding automatically if it's still there), so there's no
way for a new user to skip this by accident. It only runs once — to change
your voice or pillars later, just run `/creator-os:onboarding` again and it
edits in place instead of re-running the full interview.

## What's inside

```
creator-os-plugin/
├── .claude-plugin/
│   └── plugin.json          ← the manifest that makes this one installable unit
├── docs/
│   ├── voice-doc.md          ← template, filled in by /creator-os:onboarding
│   └── pillars.md            ← template, filled in by /creator-os:onboarding
├── skills/
│   ├── onboarding/SKILL.md
│   ├── signal-mine/SKILL.md
│   ├── story-mine/SKILL.md
│   ├── follow-up-engine/SKILL.md
│   ├── youtube-ideation/SKILL.md
│   ├── long-form-outline/SKILL.md
│   ├── the-bridge/SKILL.md
│   ├── reel-scripter/SKILL.md
│   ├── long-to-short/SKILL.md
│   ├── series-planner/SKILL.md
│   ├── youtube-packaging/SKILL.md
│   ├── caption-and-cta/SKILL.md
│   ├── newsletter-drafter/SKILL.md
│   ├── freebie-suggester/SKILL.md
│   ├── audience-gaps/SKILL.md
│   ├── goal-lock/SKILL.md
│   ├── performance-pulse/SKILL.md
│   ├── skill-opportunity-finder/SKILL.md
│   └── skill-builder/SKILL.md
└── README.md                 ← this file
```

The Google Sheets setup for performance-pulse/goal-lock (two sheets: "Creator
OS — Performance Log" and "Creator OS — Goal State", with Google Drive
connected) is separate from onboarding — see STEP-BY-STEP.md.
