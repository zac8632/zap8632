#!/usr/bin/env python3
"""
Syncs hand-picked mudah listings into the "Master Listings" table of the
Lead Pipeline Airtable base - the other half of the CRM sync (Telegram
listings already auto-sync via airtable_sync.py).

Reads the live Google Sheet's "Focus Area" tab (the same tab
scrape_penang_owners.py writes to and preserves user edits on), and syncs
any row where the user has ticked "Mark for Marketing" TRUE and it hasn't
been synced yet ("Synced to CRM" is blank). After a successful sync, writes
"TRUE" back into that row's "Synced to CRM" cell so it isn't re-sent next
run - the Sheet itself is the dedup record, no separate registry needed.

Unlike the Telegram side, mudah's Hero Image URL is already a real,
publicly-hosted CDN URL (mudah's own site, not anything private you
uploaded) - so this uses Airtable's URL-based attachment field directly,
no need for the direct-upload dance airtable_sync.py does for
personally-forwarded photos.
"""
import argparse
import os
import sys

import requests

AIRTABLE_API_ROOT = "https://api.airtable.com/v0"
TABLE_NAME = "Master Listings"


def _airtable_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def record_exists(base_id, token, list_id):
    params = {"filterByFormula": f"{{listId}} = '{list_id}'", "maxRecords": 1}
    r = requests.get(f"{AIRTABLE_API_ROOT}/{base_id}/{TABLE_NAME}",
                      headers=_airtable_headers(token), params=params)
    r.raise_for_status()
    return bool(r.json().get("records"))


def create_record(base_id, token, fields):
    r = requests.post(f"{AIRTABLE_API_ROOT}/{base_id}/{TABLE_NAME}",
                       headers=_airtable_headers(token), json={"fields": fields})
    if r.status_code >= 400:
        print(f"  [error] creating record: {r.status_code} {r.text}", file=sys.stderr)
        r.raise_for_status()
    return r.json()


def _list_id_from_url(url):
    import re
    m = re.search(r"(\d+)(?:\.\w+)?/?$", str(url or ""))
    return m.group(1) if m else None


def build_fields(row):
    list_id = _list_id_from_url(row.get("Listing URL"))
    fields = {
        "Title": row.get("Title") or list_id,
        "Source": "mudah",
        "Location": row.get("Location"),
        "Bedrooms": row.get("Bedrooms"),
        "Bathrooms": row.get("Bathrooms"),
        "Size (sqft)": row.get("Size (sqft)"),
        "Land Size": row.get("Land Size"),
        "Tenure": row.get("Tenure"),
        "Furnishing": row.get("Furnishing"),
        "Category": row.get("Category"),
        "listId": list_id,
        "Description": row.get("Description"),
        "Listing URL": row.get("Listing URL"),
        "Mark for Marketing": True,
    }
    price = row.get("Price (RM)")
    if price not in (None, ""):
        try:
            fields["Price (RM)"] = float(price)
        except ValueError:
            pass
    hero_url = row.get("Hero Image URL")
    if hero_url:
        fields["Hero Image"] = [{"url": hero_url}]
    return {k: v for k, v in fields.items() if v not in (None, "", [])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-id", required=True)
    ap.add_argument("--gsheet-id", required=True)
    ap.add_argument("--gsheet-key", required=True, help="path to service-account JSON key")
    ap.add_argument("--tab", default="Focus Area")
    args = ap.parse_args()

    token = (os.environ.get("AIRTABLE_API_KEY") or "").strip()
    if not token:
        print("AIRTABLE_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    import gspread
    gc = gspread.service_account(filename=args.gsheet_key)
    sh = gc.open_by_key(args.gsheet_id)
    ws = sh.worksheet(args.tab)
    records = ws.get_all_records()

    def _marked(v):
        return str(v).strip().upper() in ("TRUE", "YES", "1")

    to_sync = [(i, r) for i, r in enumerate(records, start=2)  # row 1 is the header
               if _marked(r.get("Mark for Marketing")) and not _marked(r.get("Synced to CRM"))]

    if not to_sync:
        print("No newly-marked listings to sync.")
        return

    header = ws.row_values(1)
    synced_col = header.index("Synced to CRM") + 1 if "Synced to CRM" in header else None

    for row_num, row in to_sync:
        list_id = _list_id_from_url(row.get("Listing URL"))
        if list_id and record_exists(args.base_id, token, list_id):
            print(f"  [skip] {list_id}: already in Master Listings")
        else:
            fields = build_fields(row)
            create_record(args.base_id, token, fields)
            print(f"  [ok] {list_id or row.get('Title')}: synced to Master Listings")

        if synced_col:
            ws.update_cell(row_num, synced_col, "TRUE")
        else:
            print("  [warn] no 'Synced to CRM' column found - can't mark as synced, "
                  "will retry this row next run", file=sys.stderr)


if __name__ == "__main__":
    main()
