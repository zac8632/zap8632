#!/usr/bin/env python3
"""One-off diagnostic: mudah.my's site was rebuilt and classic Pages
Router's single inline <script id="__NEXT_DATA__"> is gone, but the
underlying data (initialStore/ads) is still present somewhere in the
page per earlier grep counts - just wrapped differently. Prints the
raw context around each occurrence of the search terms so the new
wrapper/shape can actually be seen (see daily-data-sync.yml's
debug_dump workflow input - this is temporary, deleted once
scrape_penang_owners.py is updated to parse whatever this turns out to
show).
"""
import sys

path = sys.argv[1]
html = open(path).read()

for term in ("initialStore", "__next_f", '"ads"'):
    print(f"===== occurrences of {term!r} =====")
    start = 0
    n = 0
    while True:
        idx = html.find(term, start)
        if idx == -1 or n >= 3:
            break
        lo = max(0, idx - 300)
        hi = min(len(html), idx + len(term) + 700)
        print(f"--- occurrence at offset {idx} ---")
        print(html[lo:hi])
        print()
        start = idx + len(term)
        n += 1
