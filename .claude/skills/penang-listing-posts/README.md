# Penang Listing Posts — social content automation

Stage 2 of the Penang property project. Stage 1 (`scripts/mudah-penang-scraper/`)
scrapes owner listings daily. This skill turns qualifying listings into
approval-ready social carousel posts, then routes them to Airtable for review.

## Flow
```
daily scrape  →  filter (≥RM1.2M, residential, target areas)
             →  pull real listing photos  →  light enhance if blurry
             →  branded cover creative (price + stats, MYR/USD/SGD)
             →  per-platform captions (no hashtags, soft CTA)
             →  Airtable (Pending Review)  →  [you approve here]
             →  Publer scheduling  →  IG feed / IG Story / Threads / TikTok / WhatsApp
```

## Files
- `SKILL.md` — the invokable skill (the procedure).
- `rules-and-constraints.md` — hard rules (no hallucination, 3-tier image policy,
  no contact info, approval gate).
- `context.md` — brand, CTA, areas, price threshold, currencies, cadence, dedup,
  rendering approach, Airtable review surface, Publer notes.
- `style-guide.md` — visual system for the creatives.
- `caption-playbook.md` — per-platform caption rules.
- `platform-specs.md` — exact sizes, slide caps, caption limits, safe zones.
- `review-checklist.md` — the approval checklist (used when reviewing in Airtable).
- `video-stage.md` — Stage 3 video spec (Ken Burns from the real photos; code later).

## Decisions (locked)
- **Brand**: Coastal Luxe palette + Montserrat/Playfair fonts; no logo/name/
  handle/contact on any output; soft CTA only (shadowban-safe).
- **No hashtags** anywhere.
- **REN/agent tag**: not needed.
- **Post volume**: no cap — every qualifying "Just Listed" listing gets a post.
- **Platforms**: Instagram feed + Instagram Story, TikTok, Threads, WhatsApp status.
- **Image policy**: three-tier (enhance real photos only; never fabricate/stage).
- **Image fetch**: runs in the GitHub Action (which can reach mudah).
- **Review surface**: Airtable (Pending Review → you approve). Publer is last.

## Build status / order
1. **Filter** — DONE, validated on real data (21/250 qualify, correct).
2. **Image fetch** — engine built (`build_listing_posts.py` + test workflow);
   pending a confirmation run to verify mudah photo extraction.
3. **Raw-native creatives** (crop 4:5 + 9:16, minimal price tag) + caption gen — DONE (captions validated; render runs in the Action).
4. **Enhancement (Tier 1/2)** + **registry write-back** + **video** (Stage 3, see `video-stage.md`) — all reuse the photos.
5. **Airtable** records for review (needs a token + base ID).
6. **Auto-daily** chaining after the scrape.
7. LAST: Publer scheduling of approved rows.
