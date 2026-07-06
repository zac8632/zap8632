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
  `scripts/listings-pipeline/penang_owners.xlsx` (committed daily by the
  GitHub Action).
- Read with `dtype=str` to preserve phone/price formatting.
- Google Sheet (live mirror):
  https://docs.google.com/spreadsheets/d/1MVjmW28PuJruSwbt-JUrY9f51dPMC-O6lDDLfOwOpRI/edit

## Second source — Telegram bot (personal listings, non-mudah)
`telegram_listings.py` + `.github/workflows/inbox-bot.yml`. The
user personally forwards a WhatsApp listing (free-text description + photos,
often from other agents) into a Telegram chat with our bot. Personal-use
only, one whitelisted chat_id - not a shared/multi-colleague tool. The
workflow polls Telegram's `getUpdates` API (cheap, no persistent process
needed - GitHub Actions can't run a long-lived listener anyway), buffers
messages per chat, and finalizes a "batch" as one listing once that chat has
been idle for `BATCH_IDLE_SECONDS` (10 min default) - covers sending photos
and caption as separate messages in either order.

**Why this source exists**: photos come from Telegram's own file API at full
original quality - no mudah watermark, no CDN downscaling. This is the answer
to the watermark problem, not a heuristic fix on the mudah side (see "Image
policy" above - both automated mudah watermark-removal attempts were
abandoned).

**Field extraction** is regex/keyword-based (mirrors the scraper's own
extraction style) and handles both common listing-text styles seen in real
samples:
- Inline: "3+1 bedrooms", "RM2.4mil", "freehold", "1,920sf".
- Reversed label style (from template-based agent listings): "Bedroom：5",
  "Built-Up (sqft) : 2899", "Land Area (sqft) : 1650" - including the
  full-width "：" colon some templates use. "RM 998 K" (thousand suffix) is
  also handled alongside the "mil"/"million" shorthand.
- Also extracted: tenure, furnishing, facing, asset/property type (keyword-
  classified: terrace/semi-d/bungalow → landed; condo/apartment/studio →
  condominium; shop/office/retail → commercial), for-sale vs for-rent.

Every field traces to text actually typed - unclear fields are left blank,
same no-hallucination rule as everywhere else. Title = the first substantive
line: generic banner lines ("FOR SALE") and label-only lines with no value
yet ("Property Address :") are both skipped in favour of the next real line.

**The agent's own name/phone line is stripped out entirely** before it ever
reaches Description, Title, or any field a caption/creative could draw from -
see `extract_agent_and_strip()`. It's kept ONLY in a private
`_agent_contact_internal` field, which itself never gets written to
`listing_raw.json` (that file ends up in a public workflow artifact - see
below) or to git. It's fed only to `sync_agent_log_to_gsheet()`.

**Private agent-contact log — must NOT go through git.** This repo is
PUBLIC: a "data branch" is just a public git branch, and workflow artifacts
on a public repo are publicly downloadable with no login. So the log
(listing facts + agent name/phone, kept for the user's own reference) is
synced straight to a **private Google Sheet** via `sync_agent_log_to_gsheet()`
- reusing the same `GSHEET_SERVICE_ACCOUNT_JSON` secret already set up for the
mudah pipeline, pointed at a repo variable `TELEGRAM_LOG_GSHEET_ID` (a
separate Sheet from the public-facing property one, shared with the same
service account's client_email). `append_to_excel_log()` still exists in the
file as a local/manual-testing helper only - never wire its output path into
anything committed or uploaded.

**Setup required before this does anything** (one-time):
1. Create a bot via **@BotFather** on Telegram → get a token.
2. Add it as a GitHub repo secret named `TELEGRAM_BOT_TOKEN`.
3. Message the bot once from your own Telegram account - the run log prints
   `unauthorised chat_id=<N>` for any sender not yet whitelisted.
4. Add that chat_id to `ALLOWED_CHAT_IDS` in `telegram_listings.py` (empty set
   = reject everyone, the safe default until configured).
5. (Optional) Create/reuse a private Google Sheet for the agent-contact log,
   share it with the service account's client_email, set repo variable
   `TELEGRAM_LOG_GSHEET_ID` to its ID.
6. Test manually via `workflow_dispatch` (`dry_run: true` first, to check
   extraction without downloading/rendering anything) before enabling the
   commented-out `schedule` trigger in the workflow.

Once a listing batch is finalized with photos, it runs through the exact same
`photo_curate.select_representative_photos()` + `post_content.render_creatives()`
+ `post_content.build_captions()` calls as the mudah pipeline - same curation,
same clean-overlay style, same caption rules. Output lands in
`telegram_input/<chat_id>_<timestamp>/` (photos, curated creatives, captions,
raw parsed listing JSON with the agent field already stripped) - same shape
as the mudah pipeline's `posts_input/`.

State (the `getUpdates` offset + any still-buffering batches) persists on a
`data/telegram-bot-state` branch, same pattern as the scraper's data branch.

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
