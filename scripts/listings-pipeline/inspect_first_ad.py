#!/usr/bin/env python3
"""One-off diagnostic: prints the shape of a single ad's JSON (from
debug_{label}_first_ad.json, written by scrape_category() when
--debug-dump is passed) - specifically whatever carries
tenure/furnishing/land size, since those columns are coming back
almost entirely empty in the live sheet despite the rest of the fields
(price, bedrooms, size) extracting fine. The old PARAM_ID_CANDIDATES
lookup (categoryParams/propertyParams) was reverse-engineered against
the pre-rebuild site; this checks whether mudah's App Router rebuild
changed that nested shape too, the same way it changed __NEXT_DATA__
itself (see scrape_penang_owners.py's extract_initial_store).

Temporary - deleted once the real fix lands in scrape_penang_owners.py.
"""
import json
import sys

path = sys.argv[1]
with open(path) as f:
    ad = json.load(f)

attrs = ad.get("attributes", ad) if isinstance(ad, dict) else ad

print("top-level ad keys:", sorted(ad.keys()) if isinstance(ad, dict) else type(ad))
print()
print("attributes keys:", sorted(attrs.keys()) if isinstance(attrs, dict) else type(attrs))
print()

for key in ("categoryParams", "propertyParams", "tenure", "furnishing", "landSize",
            "attr_tenure", "attr_furnishing", "attr_land_size", "subCategoryName",
            "propertyType", "categoryName", "subCategory"):
    if isinstance(attrs, dict) and key in attrs:
        print(f"attributes[{key!r}] =", json.dumps(attrs[key], indent=2)[:2000])
        print()

# Also scan the whole ad recursively for any key that looks tenure/furnishing-ish,
# in case it moved somewhere other than attributes.
def scan(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            lk = k.lower()
            if any(w in lk for w in ("tenure", "furnish", "land", "lot")):
                print(f"found key at {path}.{k!r}:", json.dumps(v, indent=2)[:500])
            scan(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj[:20]):
            scan(item, f"{path}[{i}]")

print("===== recursive scan for tenure/furnish/land/lot-like keys =====")
scan(ad)
