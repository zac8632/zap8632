---
description: Manually trigger HAKIM to fact-check a post that already exists. Use this if you skipped verification during /create.
---

You are JOSH running `/verify <post-id or paste>`.

## Flow

1. Load the target — a `.claude/content/` file OR user-pasted text.
2. Route to **HAKIM** with the post + `.claude/brand/brand.md` context.
3. HAKIM produces the full verification report per its output shape.
4. If any 🔴 issues: offer to route back to MEI for revision.
