#!/usr/bin/env python3
"""One-off diagnostic: prints the full attributes JSON of one or more
debug_{label}_first_ad.json files (written by scrape_category() under
--debug-dump) so the real field names/values for Tenure, Furnishing,
Land Size etc can be read directly, instead of guessing at key names.
mudah's App Router rebuild removed the old categoryParams/propertyParams
nested lists entirely - the first pass of this script (printing just
the top-level key list) showed that - so this prints full values for
every flat field instead.

Temporary - deleted once the real field-mapping fix lands in
scrape_penang_owners.py.
"""
import json
import sys

for path in sys.argv[1:]:
    with open(path) as f:
        ad = json.load(f)
    attrs = ad.get("attributes", ad) if isinstance(ad, dict) else ad
    print(f"===== {path} =====")
    print(json.dumps(attrs, indent=2, ensure_ascii=False)[:4000])
    print()
