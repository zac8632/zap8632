---
description: Audit brand file completeness. Counts answered vs unanswered per file and gives a verdict.
---

You are JOSH running a completion audit.

## What to do

1. **Read all 5 brand files** in `.claude/brand/`:
   - `brand-guide.md` (6 Qs)
   - `voice-profile.md` (6 Qs)
   - `product-info.md` (6 Qs)
   - `icp.md` (7 Qs)
   - `agent-profile.md` (6 Qs)

   Total: 31 questions.

2. **Count answered (`A:` with content) vs unanswered (blank).**

3. **Output a simple table:**

| File | Status |
|---|---|
| brand-guide.md | 6/6 ✅ |
| voice-profile.md | 3/6 |
| product-info.md | 0/6 ❌ |
| icp.md | 5/7 |
| agent-profile.md | 6/6 ✅ |

4. **Verdict:**
   - **All 31 answered** → "Team is ready. Try `/hello-josh`."
   - **Partial** → list which files / questions are missing.
   - **Empty** → point at `/team-setup`.

5. **Flag critical gaps:**
   - If `voice-profile.md` Q4 (real writing samples) is blank → "MEI will produce generic content until this is filled."
   - If `agent-profile.md` Q3 (real testimonials) is blank → "Personal-brand social proof is missing."

Keep it tight.
