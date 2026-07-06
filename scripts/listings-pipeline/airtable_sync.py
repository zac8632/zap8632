#!/usr/bin/env python3
"""
Pushes finalized Telegram listings (parsed, photo-curated, creative-rendered,
caption-written by telegram_listings.py) into the "Master Listings" table of
the Lead Pipeline Airtable base.

Uploads photos/creatives via Airtable's direct attachment-upload endpoint
(base64 file content, no public URL needed) - earlier versions of this script
required committing media to a public git branch first so Airtable could
fetch it via raw.githubusercontent.com, which meant every forwarded photo
became publicly reachable. Direct upload avoids that entirely.

Safe to re-run: skips any batch whose listId/Batch ID already has a Master
Listings record (checked via the Airtable API), so a retried workflow run
doesn't create duplicate rows.
"""
import argparse
import base64
import glob
import json
import mimetypes
import os
import sys

import requests

API_ROOT = "https://api.airtable.com/v0"
CONTENT_ROOT = "https://content.airtable.com/v0"
TABLE_NAME = "Master Listings"


def _headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


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


def upload_attachment(base_id, token, record_id, field_name, file_path):
    """Uploads one local file straight to an attachment field via Airtable's
    content API - no public URL, no git commit needed."""
    content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    with open(file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    url = f"{CONTENT_ROOT}/{base_id}/{record_id}/{field_name}/uploadAttachment"
    r = requests.post(url, headers=_headers(token), json={
        "contentType": content_type,
        "file": b64,
        "filename": os.path.basename(file_path),
    })
    if r.status_code >= 400:
        print(f"  [error] uploading {file_path}: {r.status_code} {r.text}", file=sys.stderr)
        return False
    return True


def build_fields(listing, caption_text):
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
    args = ap.parse_args()

    token = (os.environ.get("AIRTABLE_API_KEY") or "").strip()
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

        photo_paths = sorted(glob.glob(os.path.join(batch_dir, "photos", "*")))
        creative_paths = sorted(p for p in glob.glob(os.path.join(batch_dir, "creatives", "*"))
                                 if os.path.isfile(p))
        caption_text = _first_caption(os.path.join(batch_dir, "captions.md"))

        fields = build_fields(listing, caption_text)
        record = create_record(args.base_id, token, fields)
        record_id = record["id"]

        for p in creative_paths[:1]:
            upload_attachment(args.base_id, token, record_id, "Hero Image", p)
        for p in photo_paths:
            upload_attachment(args.base_id, token, record_id, "Photos", p)

        print(f"  [ok] {batch_id}: synced to Master Listings "
              f"({len(creative_paths[:1])} hero image, {len(photo_paths)} photos uploaded)")


if __name__ == "__main__":
    main()
