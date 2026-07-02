#!/usr/bin/env python3
"""
Mudah.my Penang Island property listing scraper.

Scrapes the "properties for sale" search results for Penang Island
(the subarea codes in the URL you supplied already restrict results to
Penang Island districts) and saves the listings to an Excel file,
including a computed "listed date" and "days listed" so you can see how
long each listing has been up.

IMPORTANT: This was written without being able to load the live page
(the environment it was authored in has no network access to mudah.my),
so the extraction logic is deliberately heuristic/regex-based rather than
tied to exact CSS class names (mudah.my, like most sites, uses
webpack-hashed class names that change on every deploy, so hard-coded
classes would break quickly anyway). If some fields come out empty or
wrong on your first run, re-run with --debug-dump to save the raw text
blocks the scraper extracted per listing card, and adjust the regexes in
`FIELD PATTERNS` below (or send them to me and I'll patch it).

Usage:
    pip install -r requirements.txt
    playwright install chromium
    python scraper.py \
        --url "https://www.mudah.my/malaysia/properties-for-sale?adsby=false&subarea=117%2C116%2C102%2C99%2C88" \
        --max-pages 20 \
        --output penang_listings.xlsx
"""

import argparse
import re
import sys
from datetime import datetime, timedelta
from urllib.parse import urljoin

import pandas as pd
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# FIELD PATTERNS - tweak these if extraction is off for a field
# ---------------------------------------------------------------------------

PRICE_RE = re.compile(r"RM\s?[\d,]+(?:\.\d+)?", re.IGNORECASE)

BEDROOM_RE = re.compile(r"(\d+)\s*(?:Bedroom|Bed(?:room)?s?|BR)\b", re.IGNORECASE)
BATHROOM_RE = re.compile(r"(\d+)\s*(?:Bathroom|Bath(?:room)?s?)\b", re.IGNORECASE)
SIZE_RE = re.compile(r"([\d,]+)\s*(?:sq\.?\s?ft|sqft)", re.IGNORECASE)

RELATIVE_DATE_RE = re.compile(
    r"\b(\d+)\s*(minute|hour|day|week|month|year)s?\s*ago\b", re.IGNORECASE
)
TODAY_RE = re.compile(r"\btoday\b", re.IGNORECASE)
YESTERDAY_RE = re.compile(r"\byesterday\b", re.IGNORECASE)
# e.g. "17 Jun 2026" or "17 Jun"
ABS_DATE_RE = re.compile(
    r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*(\d{4})?\b",
    re.IGNORECASE,
)

# Penang Island districts/areas (used only to sanity-check / fill the
# "Location" column when a card doesn't clearly separate it).
PENANG_ISLAND_AREAS = [
    "George Town", "Georgetown", "Air Itam", "Ayer Itam", "Bayan Baru",
    "Bayan Lepas", "Batu Ferringhi", "Tanjung Bungah", "Tanjong Bungah",
    "Gelugor", "Jelutong", "Pulau Tikus", "Sungai Ara", "Sungai Nibong",
    "Relau", "Bukit Jambul", "Green Lane", "Farlim", "Paya Terubong",
    "Tanjung Tokong", "Batu Uban", "Sungai Dua", "Bukit Gambier",
    "Balik Pulau", "Teluk Bahang", "Bukit Jambul", "Island Glades",
]

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def parse_listed_date(text, scrape_time):
    """Best-effort parse of a relative/absolute date string found near a
    listing card into an absolute datetime. Returns None if nothing matched."""
    if not text:
        return None

    m = RELATIVE_DATE_RE.search(text)
    if m:
        amount = int(m.group(1))
        unit = m.group(2).lower()
        delta = {
            "minute": timedelta(minutes=amount),
            "hour": timedelta(hours=amount),
            "day": timedelta(days=amount),
            "week": timedelta(weeks=amount),
            "month": timedelta(days=amount * 30),
            "year": timedelta(days=amount * 365),
        }[unit]
        return scrape_time - delta

    if TODAY_RE.search(text):
        return scrape_time

    if YESTERDAY_RE.search(text):
        return scrape_time - timedelta(days=1)

    m = ABS_DATE_RE.search(text)
    if m:
        day = int(m.group(1))
        month = MONTHS[m.group(2).lower()[:3]]
        year = int(m.group(3)) if m.group(3) else scrape_time.year
        try:
            dt = datetime(year, month, day)
            # if the date would be in the future (no year given, month/day
            # already passed this year vs next), assume it's from last year
            if dt > scrape_time:
                dt = datetime(year - 1, month, day)
            return dt
        except ValueError:
            return None

    return None


def find_next_page_url(page, current_url):
    """Look for a 'next page' link via common patterns (rel=next, aria-label,
    or visible '>' / 'Next' text) rather than guessing the pagination
    query-param scheme."""
    candidates = page.locator(
        "a[rel='next'], a[aria-label*='Next' i], a:has-text('Next'), a:has-text('»')"
    )
    count = candidates.count()
    for i in range(count):
        href = candidates.nth(i).get_attribute("href")
        if href:
            next_url = urljoin(current_url, href)
            if next_url != current_url:
                return next_url
    return None


def extract_listings_from_page(page, base_url):
    """Each mudah.my listing card is a single clickable <a href> whose
    innerText contains the whole card ("<Type> For Sale | listed X ago |
    RM ... | <Project>, <Area> | ... | Bed | ... | Bath | ... | by |
    <seller>"). So instead of guessing DOM card boundaries, just grab
    every anchor that looks like a listing (mentions "For Sale" and has a
    price) and parse its text as pipe-separated tokens."""

    anchors = page.evaluate(
        """
        () => {
            const results = [];
            const seen = new Set();
            const priceRe = /RM\\s?[\\d,]+/i;
            for (const a of document.querySelectorAll('a[href]')) {
                const text = a.innerText || '';
                if (!/for sale/i.test(text)) continue;
                if (!priceRe.test(text)) continue;
                const href = a.getAttribute('href');
                if (!href || seen.has(href)) continue;
                seen.add(href);
                results.push({ href: href, text: text });
            }
            return results;
        }
        """
    )

    scrape_time = datetime.now()
    listings = []
    for a in anchors:
        text = a["text"]
        tokens = [t.strip() for t in text.split("|")]
        tokens = [t for t in tokens if t]

        price_m = PRICE_RE.search(text)
        bed_m = BEDROOM_RE.search(text)
        bath_m = BATHROOM_RE.search(text)
        size_m = SIZE_RE.search(text)

        property_type = re.sub(r"\s*for sale\s*$", "", tokens[0], flags=re.IGNORECASE).strip() if tokens else ""

        location_token = ""
        for t in tokens:
            if "," in t:
                area_part = t.split(",")[-1].strip()
                if any(area.lower() == area_part.lower() for area in PENANG_ISLAND_AREAS):
                    location_token = t
                    break
        if not location_token:
            for area in PENANG_ISLAND_AREAS:
                if area.lower() in text.lower():
                    location_token = area
                    break

        by_idx = next((i for i, t in enumerate(tokens) if t.lower() == "by"), None)
        seller = tokens[by_idx + 1] if by_idx is not None and by_idx + 1 < len(tokens) else ""
        title = tokens[by_idx - 1] if by_idx is not None and by_idx > 0 else ""

        listed_dt = parse_listed_date(text, scrape_time)

        listings.append({
            "Title": title,
            "Property Type": property_type,
            "Price": price_m.group(0) if price_m else "",
            "Location": location_token,
            "Bedrooms": bed_m.group(1) if bed_m else "",
            "Bathrooms": bath_m.group(1) if bath_m else "",
            "Size (sqft)": size_m.group(1).replace(",", "") if size_m else "",
            "Seller": seller,
            "Listing URL": urljoin(base_url, a["href"]),
            "Listed Date": listed_dt.strftime("%Y-%m-%d") if listed_dt else "",
            "Days Listed": (scrape_time - listed_dt).days if listed_dt else "",
            "Raw Card Text": text.replace("\n", " | "),
            "Scraped At": scrape_time.strftime("%Y-%m-%d %H:%M"),
        })

    return listings


def scrape(url, max_pages, headless, delay_ms, debug_dump):
    all_listings = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
            )
        )

        current_url = url
        for page_num in range(1, max_pages + 1):
            print(f"[page {page_num}] loading {current_url}", file=sys.stderr)
            page.goto(current_url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(delay_ms)

            listings = extract_listings_from_page(page, current_url)
            print(f"[page {page_num}] found {len(listings)} listing candidates", file=sys.stderr)
            all_listings.extend(listings)

            if debug_dump:
                import json
                with open(f"debug_page_{page_num}.json", "w") as f:
                    json.dump(listings, f, indent=2)

            next_url = find_next_page_url(page, current_url)
            if not next_url or not listings:
                break
            current_url = next_url

        browser.close()

    return all_listings


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--url",
        default=(
            "https://www.mudah.my/malaysia/properties-for-sale"
            "?adsby=false&subarea=117%2C116%2C102%2C99%2C88"
        ),
        help="Search results URL (subarea codes here should already restrict to Penang Island).",
    )
    ap.add_argument("--max-pages", type=int, default=20)
    ap.add_argument("--output", default="penang_listings.xlsx")
    ap.add_argument("--headless", action="store_true", default=True)
    ap.add_argument("--no-headless", dest="headless", action="store_false")
    ap.add_argument("--delay-ms", type=int, default=1500, help="Wait after each page load, ms.")
    ap.add_argument(
        "--debug-dump",
        action="store_true",
        help="Save raw extracted card text per page to debug_page_N.json for troubleshooting.",
    )
    args = ap.parse_args()

    listings = scrape(args.url, args.max_pages, args.headless, args.delay_ms, args.debug_dump)

    if not listings:
        print("No listings extracted. Try --no-headless --debug-dump to inspect what's happening.",
              file=sys.stderr)
        sys.exit(1)

    df = pd.DataFrame(listings)
    df.drop_duplicates(subset=["Listing URL"], inplace=True)
    df.sort_values(by="Days Listed", ascending=False, inplace=True, na_position="last")

    with pd.ExcelWriter(args.output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Penang Listings")
        ws = writer.sheets["Penang Listings"]
        for col_cells in ws.columns:
            length = max(len(str(cell.value)) for cell in col_cells if cell.value is not None) if any(
                cell.value for cell in col_cells) else 10
            ws.column_dimensions[col_cells[0].column_letter].width = min(length + 2, 60)

    print(f"Saved {len(df)} unique listings to {args.output}")


if __name__ == "__main__":
    main()
