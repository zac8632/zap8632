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
import datetime
import json
import os
import sys
import urllib.parse

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_listing_posts import qualifies, extract_list_id
from post_content import project_name, price_lines, price_num, _clean

WHATSAPP_PHONE = "60105666924"
REF_PREFIX = "PPM"

# Sanity check on price-per-sqft, not a correction - some sellers type their
# price into the free-text description using periods as thousand-separators
# (e.g. "1593.350.00"), which mudah's own structured price field can then
# misparse as 10x too high. We can't know which number is right from data
# alone, so this only flags implausible listings for a human to check
# instead of silently trusting (or silently "fixing") either number.
MIN_PLAUSIBLE_PSF = 200
MAX_PLAUSIBLE_PSF = 5000


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
    this is the private mapping back to the real mudah record. Also stamps
    "first_seen" (the Listing Date shown on the site) the first time a
    listing is ever seen - never overwritten on later runs, so it reflects
    when it was actually first listed, not the most recent re-scrape."""
    if list_id in registry:
        if "first_seen" not in registry[list_id]:
            # Backfill for refs assigned before this field existed.
            registry[list_id]["first_seen"] = datetime.date.today().isoformat()
        return registry[list_id]["ref"]
    ref = f"{REF_PREFIX}-{next_ref_number(registry)}"
    registry[list_id] = {
        "ref": ref,
        "mudah_url": row.get("Listing URL"),
        "title": row.get("Title"),
        "first_seen": datetime.date.today().isoformat(),
    }
    return ref


def whatsapp_link(ref, title, phone=WHATSAPP_PHONE):
    text = f"Hi, I'm interested in listing {ref} ({title}). Is it still available?"
    return f"https://wa.me/{phone}?text={urllib.parse.quote(text)}"


def subsales_title(row):
    """Condo/project name + area, e.g. "City Of Dreams, Tanjong Tokong" -
    the project name only (project_name() already strips a trailing area
    suffix from the owner's raw Title if present), so the area is added
    back exactly once even if the owner's title didn't include it."""
    proj = project_name(row)
    area = _clean(row.get("Location"))
    if proj and area and not proj.lower().endswith(area.lower()):
        return f"{proj}, {area}"
    return proj or area or "Property"


def simple_description(row):
    """A short composed sentence from known fields only (bedrooms,
    bathrooms, size, tenure, property type, area) - never the owner's raw
    free-text, which can be long, informal, or (as seen with one listing)
    contain a conflicting price typed in a different format."""
    ptype = _clean(row.get("Property Type")) or "Property"
    area = _clean(row.get("Location"))
    bd = _clean(row.get("Bedrooms"))
    ba = _clean(row.get("Bathrooms"))
    sz = _clean(row.get("Size (sqft)"))
    tenure = _clean(row.get("Tenure"))

    lead = ptype
    if area:
        lead += f" in {area}"

    parts = []
    if bd:
        parts.append(f"{bd} bedroom{'s' if bd != '1' else ''}")
    if ba:
        parts.append(f"{ba} bathroom{'s' if ba != '1' else ''}")
    if sz:
        parts.append(f"{sz} sqft")
    if tenure:
        parts.append(tenure)

    return f"{lead} - {', '.join(parts)}." if parts else f"{lead}."


def price_flag(myr, row):
    """Flags (does not correct) implausible price-per-sqft - e.g. a seller
    typing their price into the free-text description with periods as
    thousand-separators, which mudah's own structured price field can then
    misparse as 10x too high. We can't tell which number is right from data
    alone, so this is a "check before publishing" signal for a human, not
    an automatic fix."""
    sz = price_num(row.get("Size (sqft)"))
    if not myr or not sz:
        return ""
    psf = myr / sz
    if psf < MIN_PLAUSIBLE_PSF or psf > MAX_PLAUSIBLE_PSF:
        return f"CHECK PRICE - RM {psf:,.0f}/sqft looks implausible, verify against the source listing"
    return ""


def build_row(row, ref, listing_date):
    myr = price_num(row.get("Price (RM)"))
    myr_s, approx = price_lines(myr)
    title = subsales_title(row)
    return {
        "Listing Date": listing_date,
        "Ref": ref,
        "Title": title,
        "Price (RM)": myr_s or "",
        "Price Approx": approx or "",
        "Price Flag": price_flag(myr, row),
        "Bedrooms": _clean(row.get("Bedrooms")) or "",
        "Bathrooms": _clean(row.get("Bathrooms")) or "",
        "Size (sqft)": _clean(row.get("Size (sqft)")) or "",
        "Property Type": _clean(row.get("Property Type")) or "",
        "Location": _clean(row.get("Location")) or "",
        "Tenure": _clean(row.get("Tenure")) or "",
        "Description": simple_description(row),
        "WhatsApp Link": whatsapp_link(ref, title),
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
        listing_date = registry[list_id].get("first_seen", "")
        rows.append(build_row(r, ref, listing_date))
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
