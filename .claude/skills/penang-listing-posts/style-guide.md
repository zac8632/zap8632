# Visual style guide — RAW NATIVE (not poster)

Direction: **as raw as possible, platform-native.** The listing's real photos ARE
the content. We do NOT build designed marketing posters (no gradient scrims across
the image, no script fonts, no stat-chip bands, no "JUST LISTED" gold pills, no
logos). Heavily-designed posters read as ads and get throttled organically; raw,
authentic photo content feels native and performs. The details live in the
caption, not on the image.

## What a post is
- **Carousel body = the real listing photos**, enhanced Tier 1/2 only (see
  `rules-and-constraints.md`). Shown as-is — no branding, no overlays on these.
- **Slide 1 (the "cover") = the strongest real photo**, optionally with ONE
  minimal, tasteful price/area tag (see below). That's the only permitted overlay.
- **No separate designed cover slide. No CTA slide.** The CTA lives in the caption.

## The only overlay allowed (optional, slide 1)
A small, restrained tag so a scroller sees the price without reading the caption:
- Bottom-left, inside the safe margin.
- One or two short lines: **price** (e.g. `RM 1,830,000`) and optionally the
  **area** (e.g. `Andaman @ Quayside · Tanjong Tokong`).
- Clean sans (Montserrat), white text with a soft shadow OR a thin, low-opacity
  dark strip behind just that text — NOT a full-image scrim.
- Small (≈ 4–5% of image height for the price line). Unobtrusive. If in doubt,
  smaller. This can be toggled off entirely for the rawest look.
- Never any number/link/handle beyond the price.

## Sizes (crop, don't compose)
- **4:5 — 1080 × 1350** (Instagram / Threads feed).
- **9:16 — 1080 × 1920** (Instagram Story / TikTok / WhatsApp status).
- Produce both by **smart-cropping the real photo** (keep the subject centred),
  not by letterboxing into a designed frame. Minimal quality loss; if a photo
  can't crop to a ratio without cutting the subject, prefer another photo.

## Rendering
- Simple image ops, not a poster engine: crop to ratio + (optional) composite the
  minimal price tag. Pillow is enough — no HTML/Chromium poster templates.

## Do / don't
- DO let the real photo fill the frame and speak for itself.
- DO keep any overlay tiny and quiet.
- DON'T add gradients, frames, badges, logos, script type, or stat bands.
- DON'T over-process a photo — enhancement stays faithful to the real unit.
- DON'T make it look like an ad. Native > polished.
