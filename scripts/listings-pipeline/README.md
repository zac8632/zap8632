# Mudah.my Penang Island property scraper

Scrapes the mudah.my "properties for sale" search results filtered to
Penang Island (via the `subarea` codes already in your URL) and saves the
listings to an Excel file, including a computed listed date and how many
days each listing has been up.

## Setup

```bash
cd scripts/listings-pipeline
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Run

```bash
python scraper.py \
  --url "https://www.mudah.my/malaysia/properties-for-sale?adsby=false&subarea=117%2C116%2C102%2C99%2C88" \
  --max-pages 20 \
  --output penang_listings.xlsx
```

This produces `penang_listings.xlsx` with one row per listing:

| Column | Notes |
|---|---|
| Title | Listing title |
| Price | Raw `RM ...` text as shown |
| Location | Matched against a list of known Penang Island areas |
| Bedrooms / Bathrooms / Size (sqft) | Parsed from the card text when present |
| Listing URL | Direct link to the ad |
| Listed Date | Parsed from "X days ago" / "Yesterday" / absolute date text |
| Days Listed | `today - Listed Date`, so you can sort by how stale a listing is |
| Raw Card Text | Everything the scraper saw for that card, for troubleshooting |

## If fields come out wrong or empty

The site wasn't reachable from the environment this script was written
in, so the extraction is heuristic (regex over the visible text of each
listing card) rather than tied to exact CSS classes. If something looks
off:

1. Re-run with `--no-headless --debug-dump` — this opens a visible
   browser window and also writes `debug_page_N.json` files containing
   the raw text the scraper pulled from each card.
2. Check the `Raw Card Text` column in the output Excel — it shows
   exactly what text was available per listing, which usually makes it
   obvious why a regex didn't match (e.g. the date format differs from
   what's expected).
3. Adjust the regexes in the `FIELD PATTERNS` section at the top of
   `scraper.py` (e.g. `PRICE_RE`, `RELATIVE_DATE_RE`, `ABS_DATE_RE`), or
   share a sample of the raw card text and it can be patched precisely.

## Notes

- The scraper follows "next page" links found on the page rather than
  guessing mudah.my's pagination query-param scheme, so it should work
  regardless of whether that's `?page=`, `?o=`, etc.
- Be a reasonable citizen: `--delay-ms` (default 1500ms) waits between
  page loads. Don't crank `--max-pages` up unnecessarily or run this on
  a tight loop — respect mudah.my's terms of service and robots.txt.
- Re-running periodically (e.g. daily) and appending to a master sheet
  is the easiest way to track "how long has this listing been up" over
  time, since "Days Listed" here is only a point-in-time estimate parsed
  from the site's own relative-date text.
