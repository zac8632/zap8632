# Creator OS — plugin

18 bundled skills for a Penang property personal brand: signal mining, story mining,
scripting, packaging, and performance tracking. Packaged as a proper plugin (one
`.claude-plugin/plugin.json` manifest + `skills/` directory) so it installs as one
unit instead of 18 separate uploads.

## Honest note on Cowork Desktop specifically

I can't confirm from here exactly what Cowork Desktop's local-plugin install UI looks
like today — I don't have live access to test it myself, and it's the kind of detail
that changes. Two paths, try in this order:

**Path A — Cowork Desktop, if it supports local plugin folders:**
1. Unzip this download somewhere on your machine
2. Open Cowork Desktop → Customize → Personal plugins → the "+" button
3. Look for an option like "Install from folder" / "Add local plugin" and point it
   at the unzipped `creator-os-plugin` folder
4. If you only see "Browse plugins" (a directory of published plugins, not a local
   upload option), Path A isn't available in your version — fall back to Path B

**Path B — Claude Code (confirmed to work this way):**
1. Unzip this download
2. From a terminal: `claude --plugin-dir /path/to/creator-os-plugin`
3. Inside that session, run `/reload-plugins` if needed
4. All 18 skills are now available as `creator-os:<skill-name>` — e.g.
   `/creator-os:signal-mine`

**Path C — if neither local-plugin route works on your setup:**
Fall back to the claude.ai web method from before — 18 individual skill ZIPs
uploaded one at a time via Customize → Skills. Slower, but guaranteed to work since
it doesn't depend on a plugin-loading feature I can't verify live from here.

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
