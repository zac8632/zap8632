#!/usr/bin/env python3
"""Maintain a permanent archive of every listing ever scraped, including
ones that have since expired (delisted from mudah.my).

scrape_penang_owners.py's own output (penang_owners.xlsx) is a fresh
snapshot every run - only whatever's currently live on mudah. Once a
listing is taken down there's no trace of it left, and mudah doesn't
serve delisted pages, so there's no way to recover it after the fact.
This script runs right after that scrape and:

  1. Loads the persisted archive registry (penang_archive.json) and the
     folder of already-downloaded hero-image thumbnails
     (archive_images/<list_id>.jpg) - both restored from the data branch
     by the workflow before this runs, same pattern as the seen-listings
     registry.
  2. For every listing in today's scrape: adds it to the archive if new
     (status Active, First Seen = today), or refreshes it if already
     known (Last Seen = today, Status flipped back to Active if it had
     been marked Expired then reappeared, fields updated in case price
     etc. changed). Downloads the hero-image thumbnail to disk the first
     time a listing is seen - mudah's own CDN URL for it typically stops
     resolving once the ad is taken down, so this is a now-or-never copy.
  3. Anything in the archive that was NOT in today's scrape gets marked
     Expired (once - the Expired Date is only set the first time this
     happens, so it reflects when it actually disappeared, not today).
  4. Syncs the whole archive to a new "Archive" Google Sheet tab, with a
     Status column and an =IMAGE() formula pointing at the thumbnail's
     permanent raw.githubusercontent.com URL (this repo is public, so
     that URL is fetchable with no auth - see workers/telegram-webhook
     for the one other place this repo relies on that).

Deliberately does NOT try to re-fetch/backfill photos for listings that
had already expired before this script existed - mudah returns nothing
for a delisted ad's URL, so that history is genuinely gone. This only
prevents the same loss from happening again going forward, plus captures
whatever is still live today.
"""

import argparse
import datetime
import json
import os
import sys

import pandas as pd
import requests

from scrape_penang_owners import extract_list_id, sync_to_gsheet

RAW_BASE = "https://raw.githubusercontent.com/{owner}/{repo}/{branch}/scripts/listings-pipeline/archive_images/{list_id}.jpg"

# Columns carried from the daily scrape into each archive entry. Kept in
# sync with scrape_penang_owners.py's own row shape - Phone/Seller Name
# included because the existing "All Listings" tab already carries them
# (this doesn't introduce any new exposure of its own).
CARRY_FIELDS = [
    "Title", "Category", "Price", "Price (RM)", "Asset Type", "Property Type",
    "Location", "State", "Tenure", "Furnishing", "Bedrooms", "Bathrooms",
    "Size (sqft)", "Land Size", "Seller Name", "Agency", "Phone",
    "Has WhatsApp", "Listing URL",
]


def load_archive(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_archive(path, archive):
    with open(path, "w") as f:
        json.dump(archive, f, indent=2)


def download_hero_image(session, url, dest_path):
    if not url or os.path.exists(dest_path):
        return os.path.exists(dest_path)
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code == 200 and resp.content:
            with open(dest_path, "wb") as f:
                f.write(resp.content)
            return True
    except requests.RequestException as e:
        print(f"  [warn] hero image download failed for {url}: {e}", file=sys.stderr)
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scrape-output", default="penang_owners.xlsx",
                     help="Today's freshly-scraped file from scrape_penang_owners.py")
    ap.add_argument("--archive-file", default="penang_archive.json")
    ap.add_argument("--images-dir", default="archive_images")
    ap.add_argument("--gh-owner", default="zac8632")
    ap.add_argument("--gh-repo", default="zap8632")
    ap.add_argument("--gh-branch", default="data/penang-owners-scrape")
    ap.add_argument("--gsheet-id", default=None)
    ap.add_argument("--gsheet-key", default=None)
    args = ap.parse_args()

    today = datetime.date.today().strftime("%d/%m/%Y")
    os.makedirs(args.images_dir, exist_ok=True)

    # dtype=str on Phone: pd.read_excel re-infers dtype from the cell
    # contents on its own, regardless of how the sheet was written -
    # an all-digit text column like "0123456789" silently comes back as
    # the int 123456789, dropping the leading zero (confirmed with a
    # local round-trip test). Forcing it to stay text here avoids
    # re-introducing the exact phone-corruption bug this codebase has
    # already had to fix once before (see sync_to_gsheet's docstring).
    df = pd.read_excel(args.scrape_output, dtype={"Phone": str})
    archive = load_archive(args.archive_file)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0", "Referer": "https://www.mudah.my/"})

    seen_today = set()
    downloaded = 0
    for _, row in df.iterrows():
        url = row.get("Listing URL", "")
        list_id = extract_list_id(url)
        if not list_id:
            continue
        seen_today.add(list_id)

        entry = archive.get(list_id, {"First Seen": today})
        entry["Last Seen"] = today
        entry["Status"] = "Active"
        entry["Expired Date"] = ""
        for field in CARRY_FIELDS:
            val = row.get(field)
            entry[field] = "" if pd.isna(val) else val
        archive[list_id] = entry

        image_path = os.path.join(args.images_dir, f"{list_id}.jpg")
        hero_url = row.get("Hero Image URL")
        if not pd.isna(hero_url) and hero_url and not os.path.exists(image_path):
            if download_hero_image(session, hero_url, image_path):
                downloaded += 1

    expired_now = 0
    for list_id, entry in archive.items():
        if list_id not in seen_today and entry.get("Status") != "Expired":
            entry["Status"] = "Expired"
            entry["Expired Date"] = today
            expired_now += 1

    save_archive(args.archive_file, archive)

    active_count = sum(1 for e in archive.values() if e.get("Status") == "Active")
    print(f"Archive: {len(archive)} listings total ({active_count} active, "
          f"{len(archive) - active_count} expired) - {downloaded} new hero images "
          f"downloaded, {expired_now} listings newly marked expired this run.")

    if args.gsheet_id and args.gsheet_key:
        rows = []
        for list_id, entry in sorted(archive.items(), key=lambda kv: kv[1].get("First Seen", ""), reverse=True):
            image_url = RAW_BASE.format(owner=args.gh_owner, repo=args.gh_repo,
                                         branch=args.gh_branch, list_id=list_id)
            has_image = os.path.exists(os.path.join(args.images_dir, f"{list_id}.jpg"))
            row = {
                "Status": entry.get("Status", ""),
                "Hero Image": f'=IMAGE("{image_url}")' if has_image else "",
                "First Seen": entry.get("First Seen", ""),
                "Last Seen": entry.get("Last Seen", ""),
                "Expired Date": entry.get("Expired Date", ""),
            }
            for field in CARRY_FIELDS:
                val = entry.get(field, "")
                if field == "Phone" and val:
                    # USER_ENTERED (needed below for =IMAGE() to evaluate)
                    # would otherwise auto-parse this as a number and drop
                    # the leading 0 - a leading apostrophe forces text.
                    val = f"'{val}"
                row[field] = val
            rows.append(row)
        archive_df = pd.DataFrame(rows)
        sync_to_gsheet(archive_df, args.gsheet_id, args.gsheet_key, "Archive",
                        value_input_option="USER_ENTERED")


if __name__ == "__main__":
    main()
