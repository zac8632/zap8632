# Penang Listing Posts — social content automation

Stage 2 of the Penang property project. Stage 1 (`scripts/mudah-penang-scraper/`)
scrapes owner listings daily. This skill turns qualifying listings into
approval-ready social carousel posts.

## Flow
```
daily scrape  →  filter (≥RM1.2M, residential, target areas)
             →  pull real listing photos  →  light enhance if blurry
             →  branded cover creative (price + stats, MYR/USD/SGD)
             →  per-platform captions + CTA
             →  Airtable (Pending Review)  →  [human approves]
             →  Publer scheduling  →  IG / Threads / TikTok / WhatsApp
```

## Files
- `SKILL.md` — the invokable skill (the procedure).
- `rules-and-constraints.md` — hard rules (no hallucination, image integrity,
  owner privacy, approval gate).
- `context.md` — brand, CTA, areas, price threshold, currencies, Airtable
  schema, Publer notes. **Has TODOs to fill in.**
- `style-guide.md` — visual system for the creatives.
- `caption-playbook.md` — per-platform caption rules.

## Status: scaffolding done; executable build next
Decisions locked: Coastal Luxe palette + Montserrat/Playfair fonts; no
logo/name/handle/contact on any output (soft CTA only, shadowban-safe); branded
carousel (cover → real photos → CTA); three-tier image policy; MYR + USD/SGD
approx. Airtable + Publer are deferred to the LAST stage.

## Decisions
- **REN/agent tag**: NOT needed (confirmed) — creatives stay clean, no text/contact.
- **Post volume**: no cap — every qualifying "Just Listed" listing gets a post.
- **Platforms**: Instagram feed + Instagram Story, TikTok, Threads, WhatsApp status.
- **Open**: image-fetch location — recommended = the daily GitHub Action downloads
  qualifying listings' photos and commits them to the data branch (skill reads
  local files, runs anywhere); alternative = run the skill on the Mac. Confirm.

## Extra guidance files
- `platform-specs.md` — exact sizes, slide caps, caption limits, safe zones.
- `hashtag-bank.md` — vetted Penang/area/luxury hashtag sets + usage rules.
- `review-checklist.md` — the human approval checklist for the output folder.

Build order:
1. **Filter + image fetch** (no external deps — uses existing scrape data). Demo-able now.
2. **Creative render** (Coastal Luxe cover, 4:5 + 9:16) + caption gen → local
   review folder `social-automation-output/<date>/<listId>/`.
3. Run a demo on 1–2 real listings; user reviews.
4. LAST: Airtable base + Publer scheduling.
