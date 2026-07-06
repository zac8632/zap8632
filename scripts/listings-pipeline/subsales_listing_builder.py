#!/usr/bin/env python3
"""
Text-only "Subsales" listing builder for penangproperty.com.my.

Mudah's photos are too low-res/watermarked to publish (confirmed via live
probing: mudah only ever serves ~360x480/640x480 images per photo, no
alternate size or quality tier exists anywhere on the page - see the
watermark_calibrate.py history for the full investigation). Rather than keep
fighting that, this skips photos entirely and builds a TEXT-ONLY listing per
qualifying mudah scrape row: a freshly composed title (not the owner's literal
listing title), key stats, and a WhatsApp inquiry link pre-filled with an
internal reference number.

The reference number is the whole point: it's assigned ONCE per listing and
persisted in a registry keyed by mudah's listId, so a listing seen again in
tomorrow's re-scrape keeps the SAME ref rather than getting a new one. When a
lead messages the pre-filled WhatsApp link, the message already states the
ref number - so you immediately know which private mudah-sourced record
they're asking about, without the site ever exposing that mudah is the
source.

Usage:
    python subsales_listing_builder.py --input penang_owners.xlsx \
        --registry subsales_registry.json \
        --gsheet-id <id> --gsheet-key gsheet_key.json
    python subsales_listing_builder.py --input penang_owners.xlsx --filter-only
"""
import argparse
import json
import os
import sys
import urllib.parse

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_listing_posts import qualifies, extract_list_id
from post_content import headline, facts_line, price_lines, price_num, _clean

WHATSAPP_PHONE = "60105666924"
REF_PREFIX = "PPM"
DESCRIPTION_MAX_CHARS = 600


def load_registry(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_registry(path, registry):
    with open(path, "w") as f:
        json.dump(registry, f, indent=2)


def next_ref_number(registry):
    """Next sequential ref number - looks at the highest number already
    assigned across the whole registry (not just currently-qualifying rows),
    so refs never collide or get reused even if a listing later drops out of
    the qualifying set and comes back."""
    nums = []
    for entry in registry.values():
        ref = entry.get("ref", "")
        if ref.startswith(f"{REF_PREFIX}-"):
            try:
                nums.append(int(ref.split("-", 1)[1]))
            except (ValueError, IndexError):
                pass
    return (max(nums) + 1) if nums else 1001


def assign_ref(registry, list_id, row):
    """Stable per-listing ref, assigned once and reused on every later run -
    this is the private mapping back to the real mudah record."""
    if list_id in registry:
        return registry[list_id]["ref"]
    ref = f"{REF_PREFIX}-{next_ref_number(registry)}"
    registry[list_id] = {
        "ref": ref,
        "mudah_url": row.get("Listing URL"),
        "title": row.get("Title"),
    }
    return ref


def whatsapp_link(ref, headline_text, phone=WHATSAPP_PHONE):
    text = f"Hi, I'm interested in listing {ref} ({headline_text}). Is it still available?"
    return f"https://wa.me/{phone}?text={urllib.parse.quote(text)}"


def clean_description(v):
    d = _clean(v)
    if not d:
        return ""
    if len(d) > DESCRIPTION_MAX_CHARS:
        d = d[:DESCRIPTION_MAX_CHARS].rsplit(" ", 1)[0] + "..."
    return d


def build_row(row, ref):
    myr = price_num(row.get("Price (RM)"))
    myr_s, approx = price_lines(myr)
    hl = headline(row)
    return {
        "Ref": ref,
        "Title": hl,
        "Price (RM)": myr_s or "",
        "Price Approx": approx or "",
        "Facts": facts_line(row),
        "Property Type": _clean(row.get("Property Type")) or "",
        "Location": _clean(row.get("Location")) or "",
        "Tenure": _clean(row.get("Tenure")) or "",
        "Description": clean_description(row.get("Description")),
        "WhatsApp Link": whatsapp_link(ref, hl),
        "Category": "Subsales",
        "Mudah URL (internal only)": row.get("Listing URL") or "",
        "Published to Site": "",
        "Publish Date": "",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default="penang_owners.xlsx")
    ap.add_argument("--registry", default="subsales_registry.json")
    ap.add_argument("--new-only", action="store_true",
                     help="Only listings with Is New Today == True.")
    ap.add_argument("--limit", type=int, default=0, help="Cap listings processed (0 = all).")
    ap.add_argument("--filter-only", action="store_true",
                     help="Print the qualifying set and exit - no ref assignment, no sheet write.")
    ap.add_argument("--gsheet-id")
    ap.add_argument("--gsheet-key")
    ap.add_argument("--tab", default="Subsales Queue")
    ap.add_argument("--out", default="subsales_queue.xlsx",
                     help="Fallback local file when no --gsheet-id/--gsheet-key given.")
    args = ap.parse_args()

    df = pd.read_excel(args.input, sheet_name="All Listings", dtype=str)
    total = len(df)
    q = df[df.apply(qualifies, axis=1)].copy()

    if args.new_only and "Is New Today" in q.columns:
        q = q[q["Is New Today"].astype(str).str.lower().isin(["true", "1"])]

    if args.limit:
        q = q.head(args.limit)

    print(f"{len(q)}/{total} listings qualify for Subsales "
          f"(residential, For Sale, target areas{', new only' if args.new_only else ''}).",
          file=sys.stderr)

    if args.filter_only:
        for _, r in q.iterrows():
            print(f"  - {extract_list_id(r.get('Listing URL'))} | {r.get('Location')} | "
                  f"{r.get('Price')} | {str(r.get('Title'))[:60]}", file=sys.stderr)
        return

    registry = load_registry(args.registry)
    rows = []
    for _, r in q.iterrows():
        list_id = extract_list_id(r.get("Listing URL"))
        if not list_id:
            continue
        ref = assign_ref(registry, list_id, r)
        rows.append(build_row(r, ref))
    save_registry(args.registry, registry)

    for row in rows:
        print(f"  - {row['Ref']}: {row['Title']}", file=sys.stderr)
    print(f"{len(rows)} Subsales rows built, {len(registry)} refs ever assigned.",
          file=sys.stderr)

    out_df = pd.DataFrame(rows)
    if args.gsheet_id and args.gsheet_key:
        from scrape_penang_owners import sync_to_gsheet
        sync_to_gsheet(out_df, args.gsheet_id, args.gsheet_key, args.tab,
                       preserve_columns=["Published to Site", "Publish Date"],
                       key_column="Ref")
    else:
        out_df.to_excel(args.out, index=False)
        print(f"Wrote {args.out} (no --gsheet-id/--gsheet-key given)", file=sys.stderr)


if __name__ == "__main__":
    main()
