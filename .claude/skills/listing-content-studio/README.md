# Penang Listing Posts — social content automation

Stage 2 of the Penang property project, with **two ingestion sources** feeding
the same downstream pipeline:

1. **mudah scrape** (`scripts/listings-pipeline/build_listing_posts.py`) —
   daily-scraped owner listings, filtered to qualifying ones.
2. **Telegram bot** (`scripts/listings-pipeline/telegram_listings.py`) — a
   colleague forwards a WhatsApp listing (text + photos) into Telegram; the
   bot extracts what it can from the free text and downloads the photos at
   full original quality. No mudah watermark on this source.

Both sources converge on the same `photo_curate.py` (quality scoring + room
classification) + `post_content.py` (creative render + captions) pipeline.

## Flow
```
mudah scrape ──▶ filter (≥RM1.2M, residential, target areas) ──┐
                                                                 ├──▶ curate photos (blur/quality
Telegram bot ──▶ parse free text (price/beds/baths/area/...)  ──┘     score + room classification:
                 + download full-res photos                            exterior/living/kitchen/
                                                                        bedroom/bathroom/scenic view
                                                                        + landed-home extras)
                                                                 │
                                                                 ▼
                                                    clean overlay creative (propertyluxemalaysia
                                                    style: vertical project name, price + location
                                                    + spec pill, 4:5 + 9:16) + per-platform captions
                                                                 │
                                                                 ▼
                                                    Airtable (Pending Review) → [you approve]
                                                                 │
                                                                 ▼
                                                    Publer scheduling → IG feed / IG Story /
                                                    Threads / TikTok / WhatsApp
```

## Files
- `SKILL.md` — the invokable skill (the procedure).
- `rules-and-constraints.md` — hard rules (no hallucination, 3-tier image policy,
  no contact info, approval gate).
- `context.md` — brand, CTA, areas, price threshold, currencies, cadence, dedup,
  rendering approach, Airtable review surface, Publer notes.
- `style-guide.md` — visual system for the creatives (propertyluxemalaysia-style
  clean overlay, not a designed poster).
- `caption-playbook.md` — per-platform caption rules.
- `platform-specs.md` — exact sizes, slide caps, caption limits, safe zones.
- `review-checklist.md` — the approval checklist (used when reviewing in Airtable).
- `video-stage.md` — Stage 3 video spec (Ken Burns from the real photos; code later).

## Decisions (locked)
- **Brand**: Coastal Luxe palette + Montserrat/Playfair fonts; no logo/name/
  handle/contact on any output; soft CTA only (shadowban-safe).
- **Creative style**: clean overlay on the real photo (vertical project name,
  price + location + spec pill), NOT a designed poster.
- **No hashtags** anywhere.
- **REN/agent tag**: not needed.
- **Post volume**: no cap — every qualifying "Just Listed" listing gets a post.
- **Platforms**: Instagram feed + Instagram Story, TikTok, Threads, WhatsApp status.
- **Image policy**: Tier 1 auto-enhancement (blur/quality scoring, dark-photo
  brightening) always on; Tier 2 (e.g. watermark removal) attempted twice on
  mudah photos and abandoned both times (see below) - photos ship as-is.
- **Photo curation**: up to 5 photos per listing, picked by quality + room
  category (exterior/living/kitchen/bedroom/bathroom + scenic view + landed-
  home extras), never padded with low-quality photos.
- **Watermark (mudah source)**: two automated removal attempts failed - a
  single-box de-blend didn't cover the actual repeating tiled pattern, and a
  whole-image heuristic + LaMa inpaint destroyed real content (sky/mirror/
  walls). Both removed. mudah photos ship with the visible watermark.
  The Telegram source has no watermark at all (original photos), which is
  part of why it exists.
- **Review surface**: Airtable (Pending Review → you approve). Publer is last.

## Build status / order
1. **mudah filter + image fetch + curation + creatives + captions** — DONE,
   validated against real data and a real Action run.
2. **Telegram bot ingestion** — built (`telegram_listings.py` + workflow);
   needs a bot token + colleague chat_id whitelist to actually test end-to-end
   (see setup notes in `telegram-listing-bot.yml`).
3. **Registry write-back** (dedup across days for mudah source) — not yet wired.
4. **Video** (Stage 3, see `video-stage.md`) — spec only, code not started.
5. **Airtable** records for review (needs a token + base ID) — not started.
6. **Auto-daily** chaining after the scrape — not started.
7. LAST: Publer scheduling of approved rows.
