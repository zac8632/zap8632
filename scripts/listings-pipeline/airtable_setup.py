#!/usr/bin/env python3
"""
One-time schema setup for the "Lead Pipeline" Airtable base (run via
setup-crm-schema.yml, not locally - this sandbox has no network access
to Airtable's API).

Creates two tables:
  - Master Listings: Telegram-submitted listings + mudah listings you've
    explicitly marked for marketing (NOT the full daily mudah scrape - that
    stays in the Google Sheet, this base would blow past the Free plan's
    1,000-record cap otherwise).
  - My Pipeline: your personal follow-up tracker, one row per listing you're
    actively working, linked back to Master Listings.

Airtable's public API can create tables/fields, but NOT automations (the
"button copies this record into My Pipeline" behaviour) - that last wiring
step is a 2-minute manual job in the Airtable UI, described in the printed
instructions at the end of this script.

Safe to re-run: skips creating a table if one with the same name already
exists in the base.
"""
import argparse
import os
import sys

import requests

API_ROOT = "https://api.airtable.com/v0"
META_ROOT = f"{API_ROOT}/meta"

MASTER_LISTINGS_FIELDS = [
    {"name": "Title", "type": "singleLineText"},
    {"name": "Source", "type": "singleSelect",
     "options": {"choices": [{"name": "mudah"}, {"name": "telegram"}]}},
    {"name": "Location", "type": "singleLineText"},
    {"name": "Price (RM)", "type": "number", "options": {"precision": 0}},
    {"name": "Bedrooms", "type": "singleLineText"},
    {"name": "Bathrooms", "type": "singleLineText"},
    {"name": "Size (sqft)", "type": "singleLineText"},
    {"name": "Land Size", "type": "singleLineText"},
    {"name": "Tenure", "type": "singleSelect",
     "options": {"choices": [{"name": "Freehold"}, {"name": "Leasehold"}]}},
    {"name": "Furnishing", "type": "singleLineText"},
    {"name": "Category", "type": "singleLineText"},
    {"name": "Hero Image", "type": "multipleAttachments"},
    {"name": "Photos", "type": "multipleAttachments"},
    {"name": "Listing URL", "type": "url"},
    {"name": "listId", "type": "singleLineText"},
    {"name": "Description", "type": "multilineText"},
    {"name": "Caption", "type": "multilineText"},
    {"name": "Mark for Marketing", "type": "checkbox",
     "options": {"icon": "check", "color": "greenBright"}},
]

MY_PIPELINE_FIELDS_TEMPLATE = [
    # "Listing" (link to Master Listings) is added after Master Listings
    # exists, since linked-record fields need the target table's ID.
    {"name": "Status", "type": "singleSelect", "options": {"choices": [
        {"name": "New"}, {"name": "Contacted"}, {"name": "Viewing Arranged"},
        {"name": "Offer"}, {"name": "Closed"}, {"name": "Dead"},
    ]}},
    {"name": "Remarks", "type": "multilineText"},
    {"name": "Next Contact Date", "type": "date",
     "options": {"dateFormat": {"name": "local", "format": "M/D/YYYY"}}},
]


def _headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def list_tables(base_id, token):
    r = requests.get(f"{META_ROOT}/bases/{base_id}/tables", headers=_headers(token))
    r.raise_for_status()
    return r.json()["tables"]


def create_table(base_id, token, name, fields, description=None):
    payload = {"name": name, "fields": fields}
    if description:
        payload["description"] = description
    r = requests.post(f"{META_ROOT}/bases/{base_id}/tables",
                       headers=_headers(token), json=payload)
    if r.status_code >= 400:
        print(f"  [error] creating '{name}': {r.status_code} {r.text}", file=sys.stderr)
        r.raise_for_status()
    return r.json()


def add_field(base_id, token, table_id, field):
    r = requests.post(f"{META_ROOT}/bases/{base_id}/tables/{table_id}/fields",
                       headers=_headers(token), json=field)
    if r.status_code >= 400:
        print(f"  [error] adding field '{field['name']}': {r.status_code} {r.text}",
              file=sys.stderr)
        r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-id", required=True)
    args = ap.parse_args()

    token = os.environ.get("AIRTABLE_API_KEY")
    if not token:
        print("AIRTABLE_API_KEY env var not set", file=sys.stderr)
        sys.exit(1)

    existing = {t["name"]: t for t in list_tables(args.base_id, token)}

    if "Master Listings" in existing:
        print("Master Listings already exists - skipping creation.")
        master = existing["Master Listings"]
    else:
        print("Creating Master Listings...")
        master = create_table(
            args.base_id, token, "Master Listings", MASTER_LISTINGS_FIELDS,
            description="Telegram-submitted listings + mudah listings marked "
                        "for marketing. NOT the full daily scrape (see the "
                        "Google Sheet for that).")
        print(f"  -> created, table id {master['id']}")

    if "My Pipeline" in existing:
        print("My Pipeline already exists - skipping creation.")
    else:
        print("Creating My Pipeline...")
        fields = [{
            "name": "Listing",
            "type": "multipleRecordLinks",
            "options": {"linkedTableId": master["id"]},
        }] + MY_PIPELINE_FIELDS_TEMPLATE
        pipeline = create_table(
            args.base_id, token, "My Pipeline", fields,
            description="Your personal follow-up tracker - status, remarks, "
                        "next contact date per listing you're actively working.")
        print(f"  -> created, table id {pipeline['id']}")

    print("""
Schema created. One manual step left (Airtable's API can't create
Automations, only tables/fields):

  1. Open Master Listings in the Airtable UI.
  2. Add a Button field (any name, e.g. "Move to My Pipeline").
  3. Automations tab -> Create automation -> trigger "When a button is
     clicked" (pick the button field you just added) -> action "Create
     record" in My Pipeline, with Listing linked back to the triggering
     record.
  4. In My Pipeline, set the default view to a Kanban grouped by Status, and
     add a filtered view for Next Contact Date <= today (your "stale leads"
     view) if you want the reporting view discussed earlier.
""")


if __name__ == "__main__":
    main()
