#!/usr/bin/env python3
"""One-off diagnostic: extracts and validates the new data shape mudah.my
serves after rebuilding onto Next.js's App Router. Classic Pages Router's
single inline <script id="__NEXT_DATA__"> is gone; the same underlying
data now streams as JSON-escaped string fragments inside React Server
Component "flight" calls: (self.__next_f=self.__next_f||[]).push([id,
"...escaped text..."]). Concatenating those decoded fragments in order
and brace-matching from the first "initialStore": recovers the same
JSON object the old page used to serve directly.

Prints a summary + a couple of sample ads so this can be eyeballed
before scrape_penang_owners.py is rewritten to use the same approach
for real (see daily-data-sync.yml's debug_dump workflow input - this
diagnostic script is temporary, deleted once that rewrite lands).
"""
import json
import re
import sys

PUSH_RE = re.compile(r'self\.__next_f\.push\(\[\d+,("(?:[^"\\]|\\.)*")\]\)')


def extract_flight_text(html):
    """Concatenate every self.__next_f.push(...) string payload, in
    document order, after JSON-unescaping each one."""
    parts = []
    for m in PUSH_RE.finditer(html):
        try:
            parts.append(json.loads(m.group(1)))
        except json.JSONDecodeError as e:
            print(f"  [warn] one push payload failed to JSON-decode: {e}", file=sys.stderr)
    return "".join(parts), len(parts)


def extract_json_object(text, key):
    """Find "<key>":{...} in text and return the matching object via
    brace counting (handles nested objects/strings/escapes)."""
    needle = f'"{key}":'
    idx = text.find(needle)
    if idx == -1:
        return None
    start = text.find("{", idx)
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        c = text[i]
        if in_string:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                in_string = False
            continue
        if c == '"':
            in_string = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def main():
    path = sys.argv[1]
    html = open(path).read()

    flight_text, n_pushes = extract_flight_text(html)
    print(f"decoded {n_pushes} push(...) payloads, {len(flight_text)} chars of flight text total")

    raw = extract_json_object(flight_text, "initialStore")
    if not raw:
        print("initialStore object NOT found in decoded flight text")
        return
    print(f"initialStore object: {len(raw)} chars")

    try:
        store = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"initialStore found but failed to parse as JSON: {e}")
        print("first 500 / last 500 chars of the extracted object:")
        print(raw[:500])
        print("...")
        print(raw[-500:])
        return

    ads = store.get("ads", []) + store.get("featuredAds", [])
    print(f"parsed OK - {len(ads)} ads (ads={len(store.get('ads', []))}, "
          f"featuredAds={len(store.get('featuredAds', []))})")
    for a in ads[:2]:
        attrs = a.get("attributes", a)
        print(f"  sample ad: id={a.get('id')} title={attrs.get('title')!r} "
              f"price={attrs.get('price')!r}")


if __name__ == "__main__":
    main()
