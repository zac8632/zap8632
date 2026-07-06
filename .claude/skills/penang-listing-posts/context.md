# Context & configuration

This file holds the knobs. Anything marked **TODO** must be filled in by the
user before a real (non-demo) run — if a TODO is blank, stop and ask.

## Brand & creative identity (decided)
No logo, business name, website, or social handles on the creatives — posts stay
clean: property + price + stats + a soft CTA. The posting account itself is the
identity.

Palette — **"Coastal Luxe"** (bright + premium, fits Penang seafront):
- Background: White `#FFFFFF` / Soft Mist `#F2F6FA`
- Primary: Azure → Ocean gradient `#1CA9E0` → `#0E6BA8`
- Deep contrast (headline text / photo scrim): Midnight Navy `#0A2540`
- Luxury accent (dividers, script word, icons): Champagne Gold `#D4AF37`
- Text on dark areas: White `#FFFFFF`
- Alt warm option available on request ("Sunset Luxe": coral→amber) if you ever
  prefer warm over coastal.

Fonts (both free Google Fonts — no licensing issues for automation):
- Headline / stats / labels: **Montserrat** (bold / extra-bold, uppercase)
- Elegant accent word: **Playfair Display** (italic) — Great Vibes as a scriptier
  alternative.

## Public CTA (soft, no contact details)
- To avoid shadowbans and protect privacy, NO phone/WhatsApp number, link, or
  handle appears on any creative OR caption.
- CTA is a soft prompt only: "DM to arrange a viewing", "Comment INFO",
  "Save & share". Inbound DMs are handled by the posting account.

## Qualifying criteria
A listing qualifies for a post only if ALL are true:
- `Asset Type == residential`
- Category contains "For Sale" (exclude rentals)
- `Price (RM)` ≥ **1,200,000**
- Area match — either:
  - `Location` is one of: `Tanjung Bungah`, `Tanjong Tokong`, OR
  - Title or Description contains any of these keywords (case-insensitive):
    `Gurney`, `Seri Tanjung Pinang`, `STP`, `Andaman`, `Tanjung Bungah`,
    `Tanjung Tokong`, `Tanjong Tokong`
- Default batch = listings where `Is New Today == True` (override on request).

Notes:
- Gurney, Seri Tanjung Pinang, and Andaman are precinct/development names that
  usually appear in the owner's text, not the Location field — hence the keyword
  match. This keeps every match "based on what the owner wrote".
- Tune this list here; the skill reads it from this file.

## Currencies
- Source of truth: **MYR** (from scraped Price).
- Also display (labelled approximate): **USD**, **SGD**.
- Approx rates (update periodically; last set 2026-07-05):
  - 1 MYR ≈ 0.213 USD
  - 1 MYR ≈ 0.287 SGD
- Always render conversions with "≈" and "approx." Never as exact.

## Posting volume ("Just Listed" — no cap)
- Produce a post for EVERY qualifying new listing that day. If 10 qualify, make
  10. These are framed as **"Just Listed"** posts. No artificial cap.
- The already-posted registry still prevents reposting the same listing on later
  days.
- (Optional, later: if a single day's volume ever gets very high, light spacing
  can be applied at the Publer scheduling stage — this is a scheduling choice,
  never a content-generation cap.)

## Already-posted registry (dedup across days)
- A listing that qualified and was already turned into a post must NOT be
  reposted on a later day. Track produced listIds in
  `social-automation-output/posted_registry.json` ({listId: first_posted_date}),
  same pattern as the scraper's seen-file. Skip any listId already in it.

## Rendering approach — clean overlay (reference: @propertyluxemalaysia)
- Direction: full-bleed real photo + a light, elegant text overlay (NOT a heavy
  designed poster). See `style-guide.md`. Layout: vertical project name down the
  left edge, bottom-left stack of price + location + a rounded spec pill
  (`3 Beds | 3 Baths | 2827 sqft`, omitting any unknown part), subtle bottom
  gradient scrim for legibility. No logo/handle/link/phone number anywhere.
- Rendering is Pillow (crop to 4:5 / 9:16 + composite the overlay on the hero
  photo only — see `photo_curate.py` for how the hero is chosen).

## Photo pipeline (full-res fetch → curate → render)
1. **Full-res fetch**: mudah's Apollo/CDN URLs carry a size token (`;s=WxH`).
   `build_listing_posts.py` probes multiple rewrites (as-scraped / upsized /
   size-param removed) rather than guessing one, and keeps the best. This gets
   the best AVAILABLE version — it cannot invent detail beyond what the owner
   uploaded.
2. **Curate** (`photo_curate.py`): score every downloaded photo for blur
   (Laplacian variance) and resolution, and classify it into a room category
   (zero-shot CLIP: exterior/facade, living room, kitchen, bedroom, bathroom —
   plus landed-home extras: dining room, garden/compound, car porch/garage,
   balcony/patio, staircase/hallway, used as fallbacks). Pick the sharpest photo
   per category, capped at 5, exterior first. This is classification of real
   photos, not generation — stays within the no-hallucination rule.
3. **Render**: the overlay goes on the curated hero photo only; the rest ride
   as plain carousel slides.

## Image source & where the skill runs
- IMPORTANT: mudah.my is network-blocked from the Claude web/cloud environment,
  so the skill cannot fetch listing pages/images from a web session. Two options
  (see the open question in README) — recommended: the **GitHub Action** (which
  can reach mudah) downloads each qualifying listing's photos and commits them to
  the `data/penang-owners-scrape` branch, so the skill just reads local files and
  can run anywhere. Alternative: run the skill on the user's Mac.

## Data source
- Primary: `origin/data/penang-owners-scrape` →
  `scripts/mudah-penang-scraper/penang_owners.xlsx` (committed daily by the
  GitHub Action).
- Read with `dtype=str` to preserve phone/price formatting.
- Google Sheet (live mirror):
  https://docs.google.com/spreadsheets/d/1MVjmW28PuJruSwbt-JUrY9f51dPMC-O6lDDLfOwOpRI/edit

## Review & approval — Airtable (the review surface)
After filtering and building creatives + captions, the skill creates one Airtable
record per listing with `Status = Pending Review`. **Airtable is the single place
the user reviews and approves** — approve/reject there; Publer (last stage) reads
approved rows. A local copy under `social-automation-output/` is kept as backup.

Attachments: the repo is public, so creatives + photos are committed to the data
branch and attached to Airtable via their **raw.githubusercontent.com** URLs
(Airtable ingests attachments from public URLs). No file uploads needed.

Needed from the user (one-time):
- An Airtable **Personal Access Token** (scopes: `data.records:read/write`,
  `schema.bases:read`) + the **base ID**. Then the skill creates/fills the
  "Posts" table per the schema below. (I can create the base structure via the
  API once a token is shared, or the user creates it from the schema.)

Base: **"Penang Listing Posts"**, table **"Posts"**.
Suggested fields:
- `Listing ID` (single line) — mudah listId
- `Title` (single line)
- `Area` (single line)
- `Price MYR` (currency/number)
- `Price USD approx` (single line)
- `Price SGD approx` (single line)
- `Beds` / `Baths` / `Size (sqft)` / `Tenure` (single line; blank if unknown)
- `Source URL` (URL) — the mudah listing
- `Cover 4:5` (attachment) / `Cover 9:16` (attachment)
- `Carousel Photos` (attachment, multiple)
- `Caption — Instagram` / `Caption — TikTok` / `Caption — Threads`
  / `Caption — WhatsApp` (long text)
- `AI Enhanced?` (checkbox) — true if any image was AI-touched
- `Owner Contact (internal)` (single line, PRIVATE — never posted)
- `Status` (single select: Pending Review / Approved / Rejected / Scheduled / Posted)
- `Reviewer Notes` (long text)
- `Publer Status` (single line — filled by the scheduling step)
- To create: user provides an Airtable **Personal Access Token** (scopes:
  data.records:read/write, schema.bases:read) and the **base ID**.

## Scheduler — Publer  — LAST STAGE (deferred)
Wire only after Airtable. Near-term the skill stops at the local review folder.
- User has a Publer account (AppSumo lifetime).
- ACTION NEEDED: confirm API access. In Publer → Settings/Account, look for
  "API" or generate an access token. If the AppSumo tier has no API, the
  fallback is Airtable → Make.com → Publer, or Publer's bulk CSV/scheduled
  import from approved Airtable rows.
- Auto-posting reality: IG & Threads schedule cleanly; TikTok auto-post is
  limited; WhatsApp status typically needs a manual tap. Plan = auto for IG/
  Threads, semi-auto/manual for TikTok + WhatsApp.
