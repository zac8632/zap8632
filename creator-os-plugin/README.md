# Creator OS — plugin

18 bundled skills for a Penang property personal brand: signal mining, story mining,
scripting, packaging, and performance tracking. Packaged as a proper plugin (one
`.claude-plugin/plugin.json` manifest + `skills/` directory) so it installs as one
unit instead of 18 separate uploads.

## Install (share this with other users)

This repo doubles as a plugin marketplace via `.claude-plugin/marketplace.json` at
the repo root. Anyone with access to `zac8632/zap8632` can install from inside
Claude Code:

```
/plugin marketplace add zac8632/zap8632
/plugin install creator-os
```

That's it — all 18 skills load as `creator-os:<skill-name>`, e.g.
`/creator-os:signal-mine`. To pick up updates later:

```
/plugin marketplace update zap8632-marketplace
/plugin update creator-os
```

**Local dev / no marketplace access:**
1. Clone or unzip this folder somewhere
2. `claude --plugin-dir /path/to/creator-os-plugin`
3. Run `/reload-plugins` inside that session if the skills don't show up right away

## What's inside

```
creator-os-plugin/
├── .claude-plugin/
│   └── plugin.json          ← the manifest that makes this one installable unit
├── skills/
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

Voice doc, pillars doc, and the Google Sheets setup for performance-pulse/goal-lock
are unchanged from before — see the earlier `creator-os-claude-ai.zip` download for
`docs/voice-doc.md` and `docs/pillars.md` if you don't still have them.
