#!/usr/bin/env python3
"""One-off diagnostic: mudah.my's site was rebuilt onto (what looks like)
Next.js's App Router - classic Pages Router's single inline
<script id="__NEXT_DATA__"> is gone, replaced by data streamed via
self.__next_f.push([...]) "RSC flight" calls scattered through the body.
Prints those calls from a saved page dump so the new data shape can
actually be seen (see daily-data-sync.yml's debug_dump workflow input -
this is temporary, deleted once scrape_penang_owners.py is updated to
parse whatever this turns out to show).
"""
import re
import sys

path = sys.argv[1]
html = open(path).read()
pushes = re.findall(r"self\.__next_f\.push\(\[.{0,6000}?\]\)", html, re.DOTALL)
print(f"found {len(pushes)} self.__next_f.push(...) calls")
for i, p in enumerate(pushes[:5]):
    print(f"--- push #{i} (first 3000 chars) ---")
    print(p[:3000])
