#!/usr/bin/env python3
"""
Pushes finalized Telegram listings (parsed, photo-curated, creative-rendered,
caption-written by telegram_listings.py) into the "Master Listings" table of
the Lead Pipeline Airtable base.

Airtable's attachment fields need a fetchable URL, not a local file - so this
script expects the curated photos/creatives it's about to link have ALREADY
been committed to a public data branch by the calling workflow (inbox-bot.yml,
step "Commit media to data branch"), and builds raw.githubusercontent.com
URLs from that commit. Run this AFTER that commit step, not standalone.

Safe to re-run: skips any batch whose listId/Batch ID already has a Master
Listings record (checked via the Airtable API), so a retried workflow run
doesn't create duplicate rows.
"""
import argparse
import glob
import json
import os
import sys

import requests

API_ROOT = "https://api.airtable.com/v0"
TABLE_NAME = "Master Listings"


def _headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _raw_url(repo, branch, path):
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"


def record_exists(base_id, token, batch_id):
    params = {"filterByFormula": f"{{listId}} = '{batch_id}'", "maxRecords": 1}
    r = requests.get(f"{API_ROOT}/{base_id}/{TABLE_NAME}", headers=_headers(token), params=params)
    r.raise_for_status()
    return bool(r.json().get("records"))


def create_record(base_id, token, fields):
    r = requests.post(f"{API_ROOT}/{base_id}/{TABLE_NAME}", headers=_headers(token),
                       json={"fields": fields})
    if r.status_code >= 400:
        print(f"  [error] creating record: {r.status_code} {r.text}", file=sys.stderr)
        r.raise_for_status()
    return r.json()


def build_fields(listing, media_repo, media_branch, media_prefix, curated_photo_names, creative_names, caption_text):
    photo_urls = [
        {"url": _raw_url(media_repo, media_branch, f"{media_prefix}/photos/{name}")}
        for name in curated_photo_names
    ]
    creative_urls = [
        {"url": _raw_url(media_repo, media_branch, f"{media_prefix}/creatives/{name}")}
        for name in creative_names
    ]
    fields = {
        "Title": listing.get("Title") or listing.get("_batch_id"),
        "Source": "telegram",
        "Location": listing.get("Location"),
        "Bedrooms": listing.get("Bedrooms"),
        "Bathrooms": listing.get("Bathrooms"),
        "Size (sqft)": listing.get("Size (sqft)"),
        "Land Size": listing.get("Land Size"),
        "Tenure": listing.get("Tenure"),
        "Furnishing": listing.get("Furnishing"),
        "Category": listing.get("Category"),
        "listId": listing.get("_batch_id"),
        "Description": listing.get("Description"),
        "Caption": caption_text,
        "Mark for Marketing": True,  # you personally chose to submit this one
    }
    if listing.get("Price (RM)"):
        fields["Price (RM)"] = listing["Price (RM)"]
    if creative_urls:
        fields["Hero Image"] = creative_urls[:1]
    if photo_urls:
        fields["Photos"] = photo_urls
    return {k: v for k, v in fields.items() if v not in (None, "", [])}


def _first_caption(captions_md_path, preferred="instagram"):
    """Pull one platform's caption out of captions.md (## header per platform)
    to use as the ready-to-post Description in Airtable."""
    if not os.path.exists(captions_md_path):
        return None
    sections, current, buf = {}, None, []
    with open(captions_md_path) as f:
        for line in f:
            if line.startswith("## "):
                if current:
                    sections[current] = "".join(buf).strip()
                current = line[3:].strip().lower()
                buf = []
            else:
                buf.append(line)
        if current:
            sections[current] = "".join(buf).strip()
    return sections.get(preferred) or next(iter(sections.values()), None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-id", required=True)
    ap.add_argument("--telegram-dir", required=True,
                     help="telegram_input dir with one subdirectory per finalized batch")
    ap.add_argument("--media-repo", required=True, help="owner/repo the media was committed to")
    ap.add_argument("--media-branch", required=True, help="data branch the media was committed to")
    args = ap.parse_args()

    token = os.environ.get("AIRTABLE_API_KEY")
    if not token:
        print("AIRTABLE_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    batch_dirs = sorted(
        d for d in glob.glob(os.path.join(args.telegram_dir, "*"))
        if os.path.isdir(d) and os.path.exists(os.path.join(d, "listing_raw.json"))
    )
    if not batch_dirs:
        print("No finalized batches found - nothing to sync.")
        return

    for batch_dir in batch_dirs:
        batch_id = os.path.basename(batch_dir)
        with open(os.path.join(batch_dir, "listing_raw.json")) as f:
            listing = json.load(f)
        listing["_batch_id"] = batch_id

        if record_exists(args.base_id, token, batch_id):
            print(f"  [skip] {batch_id}: already synced")
            continue

        photo_names = sorted(os.path.basename(p) for p in
                              glob.glob(os.path.join(batch_dir, "photos", "*")))
        creative_names = sorted(os.path.basename(p) for p in
                                 glob.glob(os.path.join(batch_dir, "creatives", "*"))
                                 if os.path.isfile(p))
        caption_text = _first_caption(os.path.join(batch_dir, "captions.md"))
        media_prefix = f"scripts/listings-pipeline/telegram_input/{batch_id}"

        fields = build_fields(listing, args.media_repo, args.media_branch, media_prefix,
                               photo_names, creative_names, caption_text)
        create_record(args.base_id, token, fields)
        print(f"  [ok] {batch_id}: synced to Master Listings")


if __name__ == "__main__":
    main()
