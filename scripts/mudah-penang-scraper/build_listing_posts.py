#!/usr/bin/env python3
"""Stage 1: filter to qualifying listings, fetch full-res photos, curate + render."""

import argparse
import json
import os
import re
import sys
import time
import random

import pandas as pd

PRICE_THRESHOLD = 1_200_000

LOCATION_AREAS = {"tanjung bungah", "tanjong tokong", "tanjung tokong"}

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


NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL)
URL_RE = re.compile(r'https?://[^\s"\'\\<>)]+', re.IGNORECASE)
APOLLO_SIZE_RE = re.compile(r';s=\d+x\d+', re.IGNORECASE)
_BAD = ("sprite", "logo", "icon", ".svg", "placeholder", "avatar", "favicon", "flag", "sprites")


def _is_photo_url(u):
    ul = u.lower()
    if any(b in ul for b in _BAD):
        return False
    return ("apollo" in ul or "akamaized" in ul or ";s=" in ul
            or re.search(r"\.(?:jpg|jpeg|png|webp)(?:\?|;|$)", ul))


def _upsize(u):
    return APOLLO_SIZE_RE.sub(";s=1600x1200", u)


def _base_key(u):
    return APOLLO_SIZE_RE.sub("", u.split("?")[0])


def _all_strings(obj, out, depth=0):
    if depth > 14:
        return
    if isinstance(obj, str):
        if obj.startswith("http"):
            out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _all_strings(v, out, depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            _all_strings(v, out, depth + 1)


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


def extract_image_urls(detail_html, list_id, debug_path=None):
    found, raw_media = [], None
    m = NEXT_DATA_RE.search(detail_html)
    if m:
        try:
            nd = json.loads(m.group(1))
            node = find_ad_node(nd, list_id) or {}
            attrs = node.get("attributes", node) if isinstance(node, dict) else {}
            for key in ("images", "media", "photos", "gallery", "image"):
                if attrs.get(key) is not None and raw_media is None:
                    raw_media = {key: attrs.get(key)}
            strs = []
            _all_strings(node, strs)
            found = [u for u in strs if _is_photo_url(u)]
        except Exception as e:
            print(f"  [images] {list_id}: JSON parse failed ({e}); regex fallback", file=sys.stderr)
    if not found:
        found = [u for u in URL_RE.findall(detail_html) if _is_photo_url(u)]

    seen, ordered = set(), []
    for u in found:
        up = _upsize(u)
        k = _base_key(up)
        if k in seen:
            continue
        seen.add(k)
        ordered.append(up)

    if debug_path:
        try:
            with open(debug_path, "w") as f:
                json.dump({"list_id": list_id, "count": len(ordered),
                           "raw_media_sample": raw_media, "urls": ordered[:20]},
                          f, indent=2, default=str)
        except Exception:
            pass
    return ordered


def polite_sleep(a=1.0, b=2.0):
    time.sleep(random.uniform(a, b))


def _url_variants(u):
    variants = [("as-scraped", u)]
    if APOLLO_SIZE_RE.search(u):
        variants.append(("upsized-1600", APOLLO_SIZE_RE.sub(";s=1600x1600", u)))
        variants.append(("upsized-2400", APOLLO_SIZE_RE.sub(";s=2400x2400", u)))
        variants.append(("no-size-param", APOLLO_SIZE_RE.sub("", u)))
    return variants


def _probe_url_variants(session, url, out_path_prefix):
    try:
        from PIL import Image
    except ImportError:
        return
    for label, vu in _url_variants(url):
        try:
            resp = session.get(vu, timeout=20)
            if resp.status_code != 200 or not resp.content:
                print(f"  [probe] {label}: HTTP {resp.status_code}", file=sys.stderr)
                continue
            tmp = f"{out_path_prefix}_{label}.tmp"
            with open(tmp, "wb") as f:
                f.write(resp.content)
            try:
                with Image.open(tmp) as im:
                    w, h = im.size
            except Exception:
                w = h = 0
            fn = f"{out_path_prefix}_{label}_{w}x{h}.jpg"
            os.replace(tmp, fn)
            print(f"  [probe] {label}: {w}x{h} ({len(resp.content)} bytes) -> {os.path.basename(fn)}",
                  file=sys.stderr)
        except Exception as e:
            print(f"  [probe] {label}: {e}", file=sys.stderr)


def fetch_and_download(session, row, out_dir, debug=False):
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

    listing_dir = os.path.join(out_dir, list_id)
    os.makedirs(listing_dir, exist_ok=True)
    img_urls = extract_image_urls(
        r.text, list_id,
        debug_path=os.path.join(listing_dir, "debug_images.json") if debug else None)
    photos_dir = os.path.join(listing_dir, "photos")
    os.makedirs(photos_dir, exist_ok=True)

    if debug and img_urls:
        probe_dir = os.path.join(listing_dir, "debug_photo_variants")
        os.makedirs(probe_dir, exist_ok=True)
        print(f"  [probe] testing URL variants for photo 1 of {list_id}...", file=sys.stderr)
        _probe_url_variants(session, img_urls[0], os.path.join(probe_dir, "photo1"))

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
    listing.pop("Phone", None)
    listing["listId"] = list_id
    listing["photos"] = saved
    listing["photo_source_urls"] = img_urls[:15]

    try:
        import photo_curate
        import post_content
        abs_photos = [os.path.join(out_dir, p) for p in saved]
        curated = photo_curate.select_representative_photos(abs_photos, k=5)
        listing["curated_photos"] = [
            {"path": os.path.relpath(c["path"], out_dir), "category": c["category"],
             "sharpness": round(c["sharpness"], 1), "confidence": round(c["confidence"], 3)}
            for c in curated
        ]
        curated_paths = [c["path"] for c in curated] or abs_photos[:5]

        dewm_dir = os.path.join(listing_dir, "photos_dewatermarked")
        os.makedirs(dewm_dir, exist_ok=True)
        dewatermarked_paths = []
        for p in curated_paths:
            out_p = os.path.join(dewm_dir, os.path.basename(p))
            if photo_curate.inpaint_watermark(p, out_p):
                dewatermarked_paths.append(out_p)
            else:
                dewatermarked_paths.append(p)
        listing["ai_enhanced"] = True

        creatives = post_content.render_creatives(
            dewatermarked_paths, row, os.path.join(listing_dir, "creatives"))
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
    ap.add_argument("--new-only", action="store_true")
    ap.add_argument("--registry", default="posts_input/posted_registry.json")
    ap.add_argument("--filter-only", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
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

    print(f"{len(q)}/{total} listings qualify.", file=sys.stderr)
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
    for idx, (_, r) in enumerate(q.iterrows()):
        if fetch_and_download(session, r, args.out, debug=(idx == 0)):
            done += 1
        polite_sleep()
    print(f"Downloaded photos for {done}/{len(q)} into {args.out}/", file=sys.stderr)


if __name__ == "__main__":
    main()
