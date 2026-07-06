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

## Rendering approach (how creatives are built)
- Creatives are rendered as **HTML/CSS → headless-Chromium screenshot**
  (Playwright, already installed). This is the only way to hit the reference
  quality (gradients, script fonts, stat chips, scrims) reliably — PIL/Pillow
  can't match the samples. One HTML template per size (4:5, 9:16), fonts + icons
  embedded, filled per listing, screenshotted at 1080-wide.

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

## Airtable  — LAST STAGE (deferred)
Do not build this until the creative + caption output has been demoed and
approved. Near-term, the skill writes drafts to a local review folder
(`social-automation-output/<date>/<listId>/`) with the creatives, chosen photos,
and a `captions.md` per listing, so you can eyeball results before we wire any
external service.

When we do build it — proposed base: **"Penang Listing Posts"**, table **"Posts"**.
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
