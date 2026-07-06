# Platform specs

Exact output requirements per platform. Creatives are rendered at these sizes;
captions follow these limits. (See `caption-playbook.md` for tone/structure and
`style-guide.md` for the visual system.)

| Platform            | Creative used | Aspect | Pixels     | Slides / frames        | Caption guidance |
|---------------------|---------------|--------|------------|------------------------|------------------|
| Instagram feed      | Cover 4:5     | 4:5    | 1080×1350  | Carousel, up to **10** | ~2,200 char max; front-load first ~125. No hashtags. |
| Instagram Story     | Cover 9:16    | 9:16   | 1080×1920  | 1+ story frames        | Minimal on-image text; soft CTA sticker |
| TikTok (photo mode) | Cover 9:16    | 9:16   | 1080×1920  | Up to ~35 (keep ≤10)   | Short, punchy; video preferred over photos |
| Threads             | Cover 4:5     | 4:5    | 1080×1350  | Up to 10 images        | ~500 char; conversational |
| WhatsApp status     | Cover 9:16    | 9:16   | 1080×1920  | 1 per status (24h)     | Ultra-short |

## Safe zones (9:16 — Story / TikTok / WhatsApp)
- Keep all text/logos clear of the **top ~250 px** and **bottom ~320 px** — those
  overlap platform UI (profile, caption, buttons).
- Centre the key info (price + hook) in the middle third.

## Carousel rules
- Slide order everywhere: **cover creative → real listing photos → CTA slide**.
- Instagram hard cap = 10 slides. If a listing has >8 photos, pick the strongest
  (exterior/hero, living, kitchen, view, bed) — quality over quantity.

## Rendering
- Produce BOTH a 4:5 and a 9:16 cover per listing so every platform is covered
  from one generation pass.
- Render via HTML/CSS → headless-Chromium screenshot at 1080-wide (fonts + icons
  embedded). See `context.md` → "Rendering approach".

## Notes
- No external link or contact on any creative/caption (privacy + shadowban).
  Instagram link stickers only if the account is eligible; otherwise soft CTA.
- TikTok reach favours video — photo carousels are valid but treat TikTok as
  secondary unless a video variant is added later.
