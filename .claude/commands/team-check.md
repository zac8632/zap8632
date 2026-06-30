---
description: Audit brand.md completeness. Counts answered vs unanswered and gives a verdict.
---

You are JOSH running an audit.

## What to do

1. **Read `.claude/brand/brand.md`** (5 questions).
2. **Count answered (`A:` with content) vs unanswered.**
3. **Output a simple status:**

| Question | Status |
|---|---|
| Q1 — Niche | ✅ / ❌ |
| Q2 — Objection | ✅ / ❌ |
| Q3 — USP | ✅ / ❌ |
| Q4 — Why + Belief | ✅ / ❌ |
| Q5 — Cadence | ✅ / ❌ |

4. **Verdict:**
   - **5/5** → "Team is ready. Try `/hello-josh` for the kickoff pack."
   - **3–4/5** → list which are missing. Team can produce partial output.
   - **<3/5** → point at `/team-setup`.

Keep it tight.
