# Stage 3 — Video (SPEC; code later)

Speced now, built after the photo-fetch test confirms Stage 1/2. Video reuses the
**same real photos** already downloaded — no new footage, no new scrape.

## What it is
A clean motion piece assembled from the listing's real stills — NOT a designed
ad. Same "raw native" rule as the photos: gentle motion, no flashy transitions,
no poster frames, no logos.

- **Ken Burns**: slow pan/zoom on each photo + soft crossfades.
- Length ~8–12s, 4–6 photos, ~2s per photo.
- Same minimal price/area tag as the photo creative, on the first segment only,
  small and quiet (toggleable off).
- Sizes: **9:16 — 1080×1920** primary (Reels / TikTok / Story); optional
  **4:5 — 1080×1350** for feed.
- Also export a **poster/thumbnail** frame (the hero photo) for previews.

## Tooling
- **ffmpeg** (free, scriptable, runs in the GitHub Action — no API, no cost).
  `zoompan` for Ken Burns, `xfade` for crossfades, `scale`/`pad` to the target
  size, `drawtext` for the minimal tag.

## Audio (important)
- Export **silent** by default. Third-party music gets muted / taken down by the
  platforms — add licensed audio **in-app at post time** (IG/TikTok both allow
  it), or use a CC0/royalty-free track. Never bake in copyrighted music.

## How video maps to each platform (see platform-specs.md)
- **Instagram**: standalone **Reel** (9:16 video), OR a carousel with the video
  as slide 1 + real photos after (mix allowed, up to 10).
- **TikTok**: a **video** post OR the photo carousel — not mixed. Pick one per
  listing (video usually reaches further).
- **Threads**: like Instagram.
- **WhatsApp status**: single video ≤60s.

## Hero selection
- Slide 1 / first video segment = the strongest real photo (prefer a wide
  exterior or the main living shot). Currently "first downloaded"; Stage 3 adds a
  simple best-photo pick.

## Output (per listing)
```
creatives/
  video_9x16.mp4      # silent Ken Burns reel
  video_4x5.mp4       # optional feed size
  video_poster.jpg    # thumbnail / hero frame
```
Plus a `format` field per listing so review/scheduling knows whether it's a
photo carousel, a video, or both.

## Inherits (non-negotiable)
All of `rules-and-constraints.md`: real photos only (enhance, never fabricate/
stage), no contact info / links / handles anywhere, price exact, approval gate.

## Status
SPEC ONLY. Build order: confirm photo-fetch → enhancement + registry write-back +
video render (all reuse the photos) → Airtable → auto-daily → Publer.
