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

Handles both For Sale and For Rent listings, output split into separate
tabs/sheets so they can be filtered independently by area/price.

A second persisted memory (--price-history) tracks the price-per-sqft
actually seen for each condo/project over time. A new listing whose
price-per-sqft deviates sharply from that project's own history (or, for a
project with no history yet, from a coarse absolute sanity band) is flagged
and EXCLUDED from the postable output - it goes to a separate "Flagged"
sheet for manual review instead, since we can't safely auto-correct or
auto-trust a price that looks wrong.

Usage:
    python subsales_listing_builder.py --input penang_owners.xlsx \
        --registry subsales_registry.json \
        --price-history subsales_price_history.json \
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
from build_listing_posts import extract_list_id, area_match
from post_content import project_name, price_lines, price_num, _clean

WHATSAPP_PHONE = "60105666924"
REF_PREFIX = "PPM"

SALE_PRICE_THRESHOLD = 1_200_000
# Rent prices are a completely different scale to sale prices - just a low
# floor to exclude obviously bogus/placeholder listings, not a "high-value"
# filter like the sale threshold.
RENT_PRICE_THRESHOLD = 500

# Absolute price-per-sqft sanity band, used only as a fallback when a
# project has no price history yet to compare against.
MIN_PLAUSIBLE_PSF = 200
MAX_PLAUSIBLE_PSF = 5000

# How far a listing's psf can deviate from its project's own historical
# median before it's flagged - e.g. 0.4-2.5x means anything outside 40%-250%
# of the project's usual psf gets flagged for manual review.
PSF_DEVIATION_LOW = 0.4
PSF_DEVIATION_HIGH = 2.5
PRICE_HISTORY_MAX_ENTRIES = 30


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


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


def qualifies_for(row, listing_type):
    """Sale and rent have genuinely different qualifying rules - rent has no
    "high-value" price floor the way sale does, just a low bar to exclude
    placeholder/bogus listings."""
    if str(row.get("Asset Type", "")).strip().lower() != "residential":
        return False
    cat = str(row.get("Category", "")).lower()
    if listing_type == "sale":
        if "for sale" not in cat:
            return False
        p = price_num(row.get("Price (RM)"))
        if p is None or p < SALE_PRICE_THRESHOLD:
            return False
    else:
        if "for rent" not in cat:
            return False
        if "room for rent" in cat:
            # Single-room rentals (shared houses) aren't full subsale
            # property listings - skip them entirely.
            return False
        p = price_num(row.get("Price (RM)"))
        if p is None or p < RENT_PRICE_THRESHOLD:
            return False
    if not area_match(row):
        return False
    return True


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


def _history_key(project, listing_type):
    return f"{listing_type}:{project.strip().lower()}"


def check_price_anomaly(psf, project, listing_type, history):
    """Compares this listing's price-per-sqft against the MEMORY of prices
    previously seen for this same condo/project - catches a unit priced way
    outside its OWN project's usual range, which a single flat threshold
    could miss (a project that's genuinely expensive, or genuinely cheap,
    would false-positive on a flat band). Falls back to a coarse absolute
    sanity band only when there's no history yet for this project."""
    key = _history_key(project, listing_type)
    entries = history.get(key, [])
    if len(entries) >= 2:
        s = sorted(entries)
        median = s[len(s) // 2]
        if median > 0 and (psf < median * PSF_DEVIATION_LOW or psf > median * PSF_DEVIATION_HIGH):
            return True, (f"RM {psf:,.0f}/sqft is {psf / median:.1f}x this project's usual "
                           f"RM {median:,.0f}/sqft (based on {len(entries)} prior listing(s) here)")
        return False, ""
    if listing_type == "sale" and (psf < MIN_PLAUSIBLE_PSF or psf > MAX_PLAUSIBLE_PSF):
        return True, (f"RM {psf:,.0f}/sqft looks implausible for a sale listing "
                       f"(no price history yet for this project to compare against)")
    return False, ""


def record_price(history, project, listing_type, psf):
    """Only ever called for non-anomalous prices, so a bad data point can
    never work its way into the memory and shift future comparisons."""
    key = _history_key(project, listing_type)
    entries = history.setdefault(key, [])
    entries.append(round(psf, 2))
    if len(entries) > PRICE_HISTORY_MAX_ENTRIES:
        del entries[0]


def build_row(row, ref, listing_date, listing_type, price_history):
    myr = price_num(row.get("Price (RM)"))
    sz = price_num(row.get("Size (sqft)"))
    myr_s, approx = price_lines(myr)
    title = subsales_title(row)
    proj = project_name(row) or title

    bd = _clean(row.get("Bedrooms"))
    ba = _clean(row.get("Bathrooms"))
    room_bath_bits = []
    if bd:
        room_bath_bits.append(f"{bd} Bed")
    if ba:
        room_bath_bits.append(f"{ba} Bath")

    anomaly, anomaly_reason = False, ""
    if myr and sz:
        psf = myr / sz
        anomaly, anomaly_reason = check_price_anomaly(psf, proj, listing_type, price_history)
        if not anomaly:
            record_price(price_history, proj, listing_type, psf)

    row_out = {
        "ID": ref,
        "Property Name": title,
        "Property Location": _clean(row.get("Location")) or "",
        "Listing Type": "For Sale" if listing_type == "sale" else "For Rent",
        "Price (RM)": myr if myr else "",
        "Price Approx": approx or "",
        "Builtup Size": _clean(row.get("Size (sqft)")) or "",
        "Room / Bath": " / ".join(room_bath_bits),
        "Furnishing": _clean(row.get("Furnishing")) or "",
        "Property Remarks": simple_description(row),
        "Listing Date": listing_date,
        "Price Anomaly": anomaly_reason,
        "WhatsApp Link": whatsapp_link(ref, title),
        "Mudah URL (internal only)": row.get("Listing URL") or "",
        "Published to Site": "",
        "Publish Date": "",
    }
    return row_out, anomaly


def _sorted_df(rows):
    d = pd.DataFrame(rows)
    if not d.empty:
        d = d.sort_values(["Property Location", "Price (RM)"], ascending=[True, False],
                           na_position="last")
    return d


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default="penang_owners.xlsx")
    ap.add_argument("--registry", default="subsales_registry.json")
    ap.add_argument("--price-history", default="subsales_price_history.json")
    ap.add_argument("--new-only", action="store_true",
                     help="Only listings with Is New Today == True.")
    ap.add_argument("--limit", type=int, default=0,
                     help="Cap qualifying listings PER listing type (0 = all).")
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

    registry = load_json(args.registry)
    price_history = load_json(args.price_history)

    clean_rows = {"sale": [], "rent": []}
    flagged_rows = []

    for listing_type in ("sale", "rent"):
        q = df[df.apply(lambda r: qualifies_for(r, listing_type), axis=1)].copy()
        if args.new_only and "Is New Today" in q.columns:
            q = q[q["Is New Today"].astype(str).str.lower().isin(["true", "1"])]
        if args.limit:
            q = q.head(args.limit)

        label = "For Sale" if listing_type == "sale" else "For Rent"
        print(f"{len(q)}/{total} listings qualify for Subsales ({label}, residential, "
              f"target areas{', new only' if args.new_only else ''}).", file=sys.stderr)

        if args.filter_only:
            for _, r in q.iterrows():
                print(f"  - {extract_list_id(r.get('Listing URL'))} | {r.get('Location')} | "
                      f"{r.get('Price')} | {str(r.get('Title'))[:60]}", file=sys.stderr)
            continue

        for _, r in q.iterrows():
            list_id = extract_list_id(r.get("Listing URL"))
            if not list_id:
                continue
            ref = assign_ref(registry, list_id, r)
            listing_date = registry[list_id].get("first_seen", "")
            row_out, anomaly = build_row(r, ref, listing_date, listing_type, price_history)
            if anomaly:
                print(f"  - {ref}: FLAGGED - {row_out['Property Name']} - "
                      f"{row_out['Price Anomaly']}", file=sys.stderr)
                flagged_rows.append(row_out)
            else:
                print(f"  - {ref}: {row_out['Property Name']}", file=sys.stderr)
                clean_rows[listing_type].append(row_out)

    if args.filter_only:
        return

    save_json(args.registry, registry)
    save_json(args.price_history, price_history)

    print(f"{len(clean_rows['sale'])} sale rows, {len(clean_rows['rent'])} rent rows built, "
          f"{len(flagged_rows)} flagged as price anomalies (excluded from posting), "
          f"{len(registry)} refs ever assigned.", file=sys.stderr)

    sale_df = _sorted_df(clean_rows["sale"])
    rent_df = _sorted_df(clean_rows["rent"])
    flagged_df = _sorted_df(flagged_rows)

    if args.gsheet_id and args.gsheet_key:
        from scrape_penang_owners import sync_to_gsheet
        sync_to_gsheet(sale_df, args.gsheet_id, args.gsheet_key, f"{args.tab} - Sale",
                       preserve_columns=["Published to Site", "Publish Date"], key_column="ID")
        sync_to_gsheet(rent_df, args.gsheet_id, args.gsheet_key, f"{args.tab} - Rent",
                       preserve_columns=["Published to Site", "Publish Date"], key_column="ID")
        sync_to_gsheet(flagged_df, args.gsheet_id, args.gsheet_key, "Flagged - Price Anomaly",
                       key_column="ID")
    else:
        with pd.ExcelWriter(args.out) as writer:
            sale_df.to_excel(writer, sheet_name="Sale", index=False)
            rent_df.to_excel(writer, sheet_name="Rent", index=False)
            flagged_df.to_excel(writer, sheet_name="Flagged", index=False)
        print(f"Wrote {args.out} (no --gsheet-id/--gsheet-key given)", file=sys.stderr)

    # Best-effort Slack ping (no-op unless SLACK_WEBHOOK_URL is set).
    try:
        import slack_notify as sl

        n_sale, n_rent, n_flag = len(clean_rows["sale"]), len(clean_rows["rent"]), len(flagged_rows)
        blocks = [
            sl.header("🧾 Subsales queue built"),
            sl.fields([
                ("🟢 For sale", f"{n_sale}"),
                ("🔵 For rent", f"{n_rent}"),
            ]),
        ]
        if n_flag:
            blocks.append(sl.section(
                f"⚠️  *{n_flag}* flagged as price anomalies — _excluded from posting_, "
                f"see the *Flagged - Price Anomaly* tab"))
        blocks.append(sl.context("Google Sheet · _Subsales Queue - Sale / - Rent_ tabs updated"))
        text = f"Subsales queue built: {n_sale} for sale, {n_rent} for rent"
        sl.notify(text, blocks=blocks)
    except Exception as e:  # noqa: BLE001 - notification is best-effort
        print(f"[slack] skipped: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
