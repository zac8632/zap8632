# Visual style guide — reference: @propertyluxemalaysia

Direction: clean, photo-first overlay (NOT an elaborate poster). Modelled on the
@propertyluxemalaysia Instagram style the user chose: the real photo fills the
frame, with a light, elegant text overlay.

## Layout (on the first slide / cover)
- **Full-bleed real photo**, smart-cropped to the target ratio.
- **Vertical project name** down the LEFT edge — the building/project name from the
  owner's Title, uppercase, airy letter-spacing, thin white type (rotated 90°).
- **Bottom-left stack**, over a subtle bottom gradient scrim:
  - **Price** — bold white, large (e.g. `RM 1,830,000`).
  - **Location** — medium white (e.g. `Tanjong Tokong`).
  - **Spec pill** — rounded azure pill: `3 Beds  |  3 Baths  |  2827 sqft`
    (omit any part that's unknown; omit the whole pill if nothing is known).
- **Optional small wordmark** top-centre (off by default — user has no logo; can
  be set to an account name later).
- No phone/handle/link anywhere. No stat bands, no script fonts, no heavy frames.

## Sizes
- **4:5 — 1080 × 1350** (Instagram / Threads feed).
- **9:16 — 1080 × 1920** (Instagram Story / TikTok / WhatsApp status); keep the
  text block clear of the bottom ~330 px UI zone.

## Photos
- Use the **full-resolution** Apollo/mudah source (see build_listing_posts.py —
  the `;s=` size token is upsized). Enhance Tier 1/2 only; never fabricate.
- Carousel body = the remaining real photos (no overlay), cover first.

## Palette (Coastal Luxe)
- Azure pill `#1082BD` / navy scrim `#0A2540` / white text. Bright, premium, clean.

## Do / don't
- DO let the real photo carry the frame; keep the overlay light and legible.
- DON'T build a designed poster, add fake specs, or crowd the frame.
