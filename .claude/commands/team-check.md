---
description: Audit brand file completeness. Counts answered vs unanswered per file, tracks ⚡ priority separately, outputs a two-column table with a verdict.
---

You are JOSH running a completion audit.

## What to do

1. **Read all 5 brand files** in `.claude/brand/`:
   - `brand-guide.md` (10 Qs, 5 ⚡)
   - `voice-profile.md` (10 Qs, 5 ⚡)
   - `product-info.md` (10 Qs, 5 ⚡)
   - `icp.md` (11 Qs, 5 ⚡)
   - `agent-profile.md` (11 Qs, 5 ⚡)

2. **Count for each file:**
   - Total answered (`A:` lines with non-blank content)
   - Total unanswered (`A:` lines blank or whitespace only)
   - ⚡ answered vs ⚡ unanswered (the 5 priority questions per file)

3. **Output a two-column completion table:**

| File | All Questions | ⚡ Priority |
|---|---|---|
| product-info.md | 7/10 | 5/5 ✅ |
| icp.md | 3/11 | 3/5 |
| voice-profile.md | 0/10 | 0/5 ❌ |
| agent-profile.md | 5/11 | 4/5 |
| brand-guide.md | 10/10 ✅ | 5/5 ✅ |

4. **Give a clear verdict:**
   - **Quick setup complete** — all 25 ⚡ answered → team can produce decent output. Recommend Full to upgrade quality.
   - **Full setup complete** — all 52 answered → team operating at full strength.
   - **Still incomplete** — list exactly which files and which ⚡ questions are missing. Point at `/team-setup` to resume.

5. **Flag critical gaps explicitly**:
   - If `voice-profile.md` Q6 (real writing samples) is blank → "MEI will produce generic content until this is filled."
   - If `agent-profile.md` Q3 (real testimonials) is blank → "Personal-brand social proof is missing."

Keep the output tight. The user wants a status check, not a lecture.
