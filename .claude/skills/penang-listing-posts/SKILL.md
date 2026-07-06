---
name: penang-listing-posts
description: >
  Turn the daily Penang owner-listing scrape into approval-ready social media
  carousel posts. Filters the scrape to high-value residential listings in the
  target areas, pulls the listing's real photos, builds branded cover creatives
  (price + key stats, multi-currency), writes per-platform captions with a CTA,
  and pushes everything to Airtable for human approval before Publer scheduling.
  Invoke when the user wants to generate today's (or a batch of) listing posts.
---

# Penang Listing Posts — content automation skill

This skill takes the output of the `scrape_penang_owners.py` pipeline and
produces **approval-ready social posts**. A human always reviews in Airtable
before anything is scheduled — this skill never posts to social media directly.

## Companion files (read these first, every run)

- **`rules-and-constraints.md`** — HARD rules. Read in full before generating
  anything. The no-hallucination and image-integrity rules are non-negotiable.
- **`context.md`** — brand, CTA details, target areas, price threshold,
  currency rates, and the fill-in-me TODO list. If TODOs are unfilled, stop and
  ask the user.
- **`style-guide.md`** — the visual system for the cover creatives (derived
  from the user's reference samples).
- **`caption-playbook.md`** — per-platform caption structure and CTA rules.
- **`platform-specs.md`** — exact sizes, slide caps, caption limits, safe zones.
- **`review-checklist.md`** — the approval checklist (used when reviewing in Airtable).

## Inputs

1. The latest scrape output. Prefer the committed copy on the data branch:
   `git show origin/data/penang-owners-scrape:scripts/mudah-penang-scraper/penang_owners.xlsx`
   (or a path the user gives you). Read with `dtype=str` so phone/price columns
   keep their exact form.
2. Optional: a date or "today only" filter — default to listings where
   `Is New Today == True` unless the user asks for the full qualifying set.

## Procedure

### 1. Filter to qualifying listings
Apply the criteria in `context.md` → "Qualifying criteria". A listing qualifies
only if ALL of:
- `Asset Type == residential`
- Category is a **For Sale** listing (not rent)
- `Price (RM)` ≥ the threshold in `context.md`
- Area matches (Location field OR an explicit area keyword in Title/Description)

Then drop any listId already in `posted_registry.json` (see context → "Already-
posted registry") so nothing is reposted. Default batch = listings where
`Is New Today == True` → these become **"Just Listed"** posts, one per qualifying
listing (no cap — if 10 qualify, produce 10). Log how many were dropped and why.
Never pad the set to hit a number.

### 2. Pull the listing's real photos
For each qualifying listing, fetch its detail page (same curl_cffi +
`__NEXT_DATA__` technique as the scraper) and extract the media/image URLs.
Download them. These real photos are the carousel body — see
`rules-and-constraints.md` before any enhancement.

### 3. Assess image quality; enhance only if needed
Per the image-integrity rule: low-res/blurry/dark photos may be
**enhanced** (denoise, sharpen, brighten, upscale) — never regenerated into new
content. Any AI-touched image is flagged `ai_enhanced = true` in Airtable so the
reviewer approves it explicitly. Keep the look bright and clean; do not overdo it.

### 4. Build the raw-native creatives (NOT posters)
Using `style-guide.md` (RAW NATIVE): the real photos are the content. Smart-crop
each photo to 4:5 and 9:16. On the first photo only, optionally composite ONE
minimal price/area tag (small, bottom-left) — no gradients, script fonts, stat
bands, badges, or logos. No separate designed cover slide, no CTA slide. All the
detail lives in the caption.

### 5. Write per-platform captions
Using `caption-playbook.md`: Instagram, TikTok, Threads, WhatsApp status. Every
factual claim must trace to scraped fields or the owner's own text (see rules).
CTA is a soft prompt only — never a number, link, or handle (privacy +
shadowban safety).

### 6. Assemble the carousel
Slide order: [cover creative] → [real listing photos] → [CTA slide]. Cap at the
platform max (10 for IG). Pick the best photos if there are more.

### 6b. Self-check gate (hard, automatic)
Before writing anything, scan every caption and every text layer of every
creative for: any digit-sequence that looks like a phone number, any URL/link,
any `@handle`, or any `wa.me`/`whatsapp`/`t.me` string. If found, strip or
regenerate — nothing with contact info or a link may reach the output folder.
Also re-verify each stat chip has a real source value and the price matches the
scrape exactly. Record the check result in the run report.

### 7. Create Airtable records for review
Commit the creatives + chosen photos to the data branch, then create one Airtable
row per listing (`Status = Pending Review`) with: the listing facts, the
per-platform captions, the creative + photo attachments (via public
raw.githubusercontent.com URLs), and the `ai_enhanced` flag. **Airtable is the
user's review/approval surface** — see `context.md` → "Review & approval —
Airtable". Also keep a local copy under `social-automation-output/<date>/<listId>/`
as backup. (Publer scheduling is the last stage and only reads approved rows.)

### 8. Stop. Report to the user.
Summarize: N qualifying, N posts drafted, any images enhanced (and which tier),
any listings skipped and why, and the Airtable link. Do NOT post anywhere.

## What this skill must never do
- Post to any social platform directly (a human reviews first).
- Invent specs, amenities, or areas not in the listing data.
- Generate a fake/idealized property image, or virtually stage an empty room.
- Put ANY phone number, link, or @handle on a creative or in a caption.
