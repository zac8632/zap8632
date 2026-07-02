#!/usr/bin/env python3
"""
Visits each listing detail page from a scraped penang_listings.xlsx and
tries to reveal + extract the seller's contact info (mudah.my usually
hides the phone number behind a "Show Phone Number" / "Call" button).

Adds "Seller Name" and "Phone" columns to the sheet in place.

Usage:
    python fetch_contacts.py --input penang_listings.xlsx --output penang_listings.xlsx --limit 5
"""

import argparse
import json
import re
import sys

import pandas as pd
from playwright.sync_api import sync_playwright

PHONE_RE = re.compile(r"(?:\+?60|0)1[0-46-9][-\s]?\d{3,4}[-\s]?\d{4}")

REVEAL_BUTTON_SELECTOR = (
    "button:has-text('Show'), a:has-text('Show'), "
    "button:has-text('Call'), a:has-text('Call'), "
    "button:has-text('Phone'), a:has-text('Phone'), "
    "button:has-text('Contact'), a:has-text('Contact'), "
    "button:has-text('Number'), a:has-text('Number')"
)


def fetch_contact(page, url):
    result = {"Seller Name": "", "Phone": "", "Contact Fetch Status": ""}
    try:
        # "networkidle" can hang forever on pages with continuous
        # background traffic (ads, chat widgets) - use domcontentloaded
        # and just give the page a moment to render instead.
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(2000)
    except Exception as e:
        result["Contact Fetch Status"] = f"load failed: {e}"
        return result

    # Try clicking anything that looks like a "reveal number" control.
    try:
        buttons = page.locator(REVEAL_BUTTON_SELECTOR)
        count = min(buttons.count(), 5)
        for i in range(count):
            try:
                buttons.nth(i).click(timeout=3000)
                page.wait_for_timeout(1000)
            except Exception:
                continue
    except Exception:
        pass

    body_text = page.locator("body").inner_text()
    phone_m = PHONE_RE.search(body_text)
    if phone_m:
        result["Phone"] = phone_m.group(0)

    # Many listings reveal contact via a WhatsApp deep link instead of
    # printing the number as text - the number lives in the href.
    if not result["Phone"]:
        try:
            wa_links = page.locator("a[href*='wa.me'], a[href*='whatsapp']")
            for i in range(min(wa_links.count(), 3)):
                href = wa_links.nth(i).get_attribute("href") or ""
                m = re.search(r"(?:wa\.me/|phone=)(\d{8,15})", href)
                if m:
                    result["Phone"] = m.group(1)
                    break
        except Exception:
            pass

    # Heuristic seller name: "Joined since: ..." has proven to be a
    # reliable anchor across live tests (unlike "advertiser"/"seller"
    # labels, which sit near several unrelated UI widgets). In the
    # profile-card layout, the display name is the line immediately
    # above it.
    lines = [l.strip() for l in body_text.split("\n") if l.strip()]
    skip_pattern = re.compile(
        r"\b(advertiser|seller|posted by|listed by|joined since|view profile|chat now|show|call|contact|report)\b",
        re.IGNORECASE,
    )
    for i, line in enumerate(lines):
        if re.search(r"\bjoined since\b", line, re.IGNORECASE):
            if i > 0:
                candidate = lines[i - 1]
                if candidate and not skip_pattern.search(candidate) and not re.match(r"^\d", candidate):
                    result["Seller Name"] = candidate
            break

    result["Contact Fetch Status"] = "ok" if (result["Phone"] or result["Seller Name"]) else "no contact found"
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--limit", type=int, default=0, help="0 = all rows")
    ap.add_argument("--headless", action="store_true", default=True)
    ap.add_argument("--no-headless", dest="headless", action="store_false")
    ap.add_argument("--delay-ms", type=int, default=1500)
    args = ap.parse_args()

    df = pd.read_excel(args.input)
    if "Listing URL" not in df.columns:
        print("Input file has no 'Listing URL' column", file=sys.stderr)
        sys.exit(1)

    rows = df.to_dict("records")
    if args.limit:
        target = rows[: args.limit]
    else:
        target = rows

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
            )
        )
        for i, row in enumerate(target):
            url = row.get("Listing URL", "")
            if not url:
                continue
            print(f"[{i+1}/{len(target)}] {url}", file=sys.stderr)
            contact = fetch_contact(page, url)
            row.update(contact)
            # Printed to stdout (not written to any committed/uploaded
            # file) so a caller can pull results straight from CI logs
            # without this contact data ever being persisted to the repo.
            print("CONTACT_RESULT: " + json.dumps({
                "Listing URL": url,
                "Title": row.get("Title", ""),
                "Seller Name": contact["Seller Name"],
                "Phone": contact["Phone"],
                "Contact Fetch Status": contact["Contact Fetch Status"],
            }))
            page.wait_for_timeout(args.delay_ms)
        browser.close()

    out_df = pd.DataFrame(target + rows[len(target):] if args.limit else target)
    out_df.to_excel(args.output, index=False)
    print(f"Saved {len(out_df)} rows to {args.output} (local/ephemeral runner file only)", file=sys.stderr)


if __name__ == "__main__":
    main()
