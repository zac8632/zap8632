#!/usr/bin/env python3
"""
Stage 1 of the social-content pipeline (see .claude/skills/penang-listing-posts/).

Takes the daily scrape output (penang_owners.xlsx), filters it to the
high-value residential listings in the target areas, and for each qualifying
listing downloads its real photos from the mudah.my detail page. Output is a
per-listing folder the `penang-listing-posts` skill then turns into creatives +
captions.

Runs inside the GitHub Action (which can reach mudah.my). Two modes:
    --filter-only         just print/emit the qualifying set (no network) - used
                          to validate the filter against scrape data.
    (default)             filter + fetch each listing's detail page + download
                          its photos into --out.

The qualifying rules and areas mirror
.claude/skills/penang-listing-posts/context.md - keep them in sync.

Usage:
    python build_listing_posts.py --input penang_owners.xlsx --out posts_input --new-only
    python build_listing_posts.py --input penang_owners.xlsx --filter-only
"""

import argparse
import json
import os
import re
import sys
import time
import random

import pandas as pd

# ---- Qualifying criteria (mirror context.md) -----------------------------

PRICE_THRESHOLD = 1_200_000

# Areas that appear as a clean Location value.
LOCATION_AREAS = {"tanjung bungah", "tanjong tokong", "tanjung tokong"}

# Precinct / development names that usually live in the owner's Title/Description
# rather than the Location field. Matched as case-insensitive keywords. "stp"
# uses a word boundary to avoid matching inside other words.
AREA_KEYWORDS = [
    "gurney", "seri tanjung pinang", "andaman",
    "tanjung bungah", "tanjung tokong", "tanjong tokong",
]
STP_RE = re.compile(r"\bstp\b", re.IGNORECASE)


def area_match(row):
    loc = str(row.get("Location", "") or "").strip().lower()
    if loc in LOCATION_AREAS:
        return True
    blob = f"{row.get('Title','')} {row.get('Description','')}".lower()
    if any(k in blob for k in AREA_KEYWORDS):
        return True
    if STP_RE.search(blob):
        return True
    return False


def price_value(row):
    raw = row.get("Price (RM)")
    if raw in (None, ""):
        return None
    try:
        return float(str(raw).replace(",", ""))
    except ValueError:
        return None


def qualifies(row):
    if str(row.get("Asset Type", "")).strip().lower() != "residential":
        return False
    if "for sale" not in str(row.get("Category", "")).lower():
        return False
    p = price_value(row)
    if p is None or p < PRICE_THRESHOLD:
        return False
    if not area_match(row):
        return False
    return True


def extract_list_id(url):
    m = re.search(r"(\d+)(?:\.\w+)?/?$", str(url or ""))
    return m.group(1) if m else None


# ---- Image extraction from the detail page -------------------------------

NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL)
# mudah serves listing photos off its image CDN; capture full-size jpg/webp URLs.
IMG_URL_RE = re.compile(r'https?://[^"\'\\ ]+?\.(?:jpg|jpeg|png|webp)', re.IGNORECASE)


def find_ad_node(obj, list_id, _depth=0):
    if _depth > 12:
        return None
    if isinstance(obj, dict):
        node_id = obj.get("listId") or obj.get("id")
        if node_id is not None and str(node_id) == str(list_id):
            return obj
        for v in obj.values():
            found = find_ad_node(v, list_id, _depth + 1)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_ad_node(item, list_id, _depth + 1)
            if found is not None:
                return found
    return None


def _urls_from(value):
    """Pull image URLs out of whatever shape a media field takes (list of
    strings, list of dicts with url/src/link/original/full keys, or nested)."""
    out = []
    if isinstance(value, str):
        if IMG_URL_RE.fullmatch(value) or IMG_URL_RE.match(value):
            out.append(value)
    elif isinstance(value, dict):
        for k in ("original", "full", "large", "url", "src", "link", "image"):
            if isinstance(value.get(k), str):
                out.append(value[k])
                break
        else:
            for v in value.values():
                out.extend(_urls_from(v))
    elif isinstance(value, list):
        for item in value:
            out.extend(_urls_from(item))
    return out


def extract_image_urls(detail_html, list_id):
    """Best-effort: prefer structured media fields on the ad node; fall back to
    scanning the whole payload for CDN image URLs. Returns de-duped list in
    document order. The first real Action run will confirm which path hits."""
    urls = []
    m = NEXT_DATA_RE.search(detail_html)
    if m:
        try:
            nd = json.loads(m.group(1))
            node = find_ad_node(nd, list_id) or {}
            attrs = node.get("attributes", node) if isinstance(node, dict) else {}
            for key in ("images", "media", "photos", "gallery", "image"):
                if attrs.get(key):
                    urls.extend(_urls_from(attrs[key]))
            if not urls:
                # nothing under the obvious keys - scan the ad node wholesale
                urls.extend(_urls_from(node))
        except Exception as e:
            print(f"  [images] {list_id}: JSON parse failed ({e}); regex fallback", file=sys.stderr)
    if not urls:
        urls = IMG_URL_RE.findall(detail_html)
    # de-dupe preserving order; drop obvious non-listing assets (icons/logos)
    seen, clean = set(), []
    for u in urls:
        if u in seen:
            continue
        if re.search(r"(sprite|logo|icon|placeholder|avatar)", u, re.IGNORECASE):
            continue
        seen.add(u)
        clean.append(u)
    return clean


def polite_sleep(a=1.0, b=2.0):
    time.sleep(random.uniform(a, b))


def fetch_and_download(session, row, out_dir):
    url = row.get("Listing URL", "")
    list_id = extract_list_id(url)
    if not list_id:
        return None
    try:
        r = session.get(url, timeout=20)
    except Exception as e:
        print(f"  [detail] {url}: request failed: {e}", file=sys.stderr)
        return None
    if r.status_code != 200:
        print(f"  [detail] {url}: HTTP {r.status_code}", file=sys.stderr)
        return None

    img_urls = extract_image_urls(r.text, list_id)
    listing_dir = os.path.join(out_dir, list_id)
    photos_dir = os.path.join(listing_dir, "photos")
    os.makedirs(photos_dir, exist_ok=True)

    saved = []
    for i, iu in enumerate(img_urls[:15], 1):
        try:
            ir = session.get(iu, timeout=20)
            if ir.status_code == 200 and ir.content:
                ext = os.path.splitext(iu.split("?")[0])[1] or ".jpg"
                fn = os.path.join(photos_dir, f"{i:02d}{ext}")
                with open(fn, "wb") as f:
                    f.write(ir.content)
                saved.append(os.path.relpath(fn, out_dir))
        except Exception as e:
            print(f"  [img] {iu}: {e}", file=sys.stderr)
        polite_sleep(0.3, 0.8)

    listing = {col: (None if pd.isna(row.get(col)) else row.get(col)) for col in row.index}
    listing.pop("Phone", None)  # never carry the owner's number into post inputs
    listing["listId"] = list_id
    listing["photos"] = saved
    listing["photo_source_urls"] = img_urls[:15]

    # Stage 2: raw-native creatives (crop + minimal tag) and captions.
    try:
        import post_content
        abs_photos = [os.path.join(out_dir, p) for p in saved]
        creatives = post_content.render_creatives(
            abs_photos, row, os.path.join(listing_dir, "creatives"))
        listing["creatives"] = {
            k: [os.path.relpath(p, out_dir) for p in v] for k, v in creatives.items()
        }
        caps = post_content.build_captions(row)
        with open(os.path.join(listing_dir, "captions.md"), "w") as f:
            for plat, txt in caps.items():
                f.write(f"## {plat}\n\n{txt}\n\n")
        listing["captions"] = caps
    except Exception as e:
        print(f"  [content] {list_id}: {e}", file=sys.stderr)

    with open(os.path.join(listing_dir, "listing.json"), "w") as f:
        json.dump(listing, f, indent=2, ensure_ascii=False)
    print(f"  [ok] {list_id}: {len(saved)} photos", file=sys.stderr)
    return list_id


def load_registry(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default="penang_owners.xlsx")
    ap.add_argument("--out", default="posts_input")
    ap.add_argument("--new-only", action="store_true",
                    help="Only listings with Is New Today == True (the daily 'Just Listed' set).")
    ap.add_argument("--registry", default="posts_input/posted_registry.json",
                    help="JSON of already-posted listIds to skip.")
    ap.add_argument("--filter-only", action="store_true",
                    help="Print the qualifying set and exit (no network, no downloads).")
    ap.add_argument("--limit", type=int, default=0, help="Cap listings processed (0 = all).")
    args = ap.parse_args()

    df = pd.read_excel(args.input, sheet_name="All Listings", dtype=str)
    total = len(df)
    q = df[df.apply(qualifies, axis=1)].copy()

    if args.new_only and "Is New Today" in q.columns:
        q = q[q["Is New Today"].astype(str).str.lower().isin(["true", "1"])]

    registry = load_registry(args.registry)
    if registry:
        q = q[~q["Listing URL"].apply(lambda u: (extract_list_id(u) or "") in registry)]

    if args.limit:
        q = q.head(args.limit)

    print(f"{len(q)}/{total} listings qualify "
          f"(residential, For Sale, >= RM{PRICE_THRESHOLD:,}, target areas"
          f"{', new only' if args.new_only else ''}).", file=sys.stderr)
    for _, r in q.iterrows():
        print(f"  - {extract_list_id(r['Listing URL'])} | {r.get('Location')} | "
              f"{r.get('Price')} | {str(r.get('Title'))[:60]}", file=sys.stderr)

    if args.filter_only:
        return

    try:
        from curl_cffi import requests as cffi_requests
    except ImportError:
        print("Missing dependency. Run: pip install curl_cffi", file=sys.stderr)
        sys.exit(1)

    session = cffi_requests.Session(impersonate="chrome124")
    session.headers.update({
        "Accept-Language": "en-MY,en;q=0.9,ms;q=0.8",
        "Referer": "https://www.mudah.my/",
    })

    os.makedirs(args.out, exist_ok=True)
    done = 0
    for _, r in q.iterrows():
        if fetch_and_download(session, r, args.out):
            done += 1
        polite_sleep()
    print(f"Downloaded photos for {done}/{len(q)} qualifying listings into {args.out}/", file=sys.stderr)


if __name__ == "__main__":
    main()
