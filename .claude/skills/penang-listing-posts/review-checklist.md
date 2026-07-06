# Review checklist (human approval)

Run through this for each listing in the output folder before approving it for
scheduling. Anything unchecked = fix or reject.

## Facts & honesty
- [ ] Price on the creative matches the source listing **exactly** (no rounding).
- [ ] Every stat chip (beds/baths/size/tenure) has a **real** value — none guessed.
- [ ] Area / project name shown actually appears in the listing.
- [ ] No amenity or feature claimed that the owner didn't write.
- [ ] Currency conversions labelled "≈ approx." (USD/SGD).

## Images
- [ ] Photos are the **real unit** from the listing.
- [ ] Any AI-touched photo is Tier 1/2 only (enhance/cleanup) — no fabricated or
      virtually-staged content. `ai_enhanced` items look faithful.
- [ ] Poor photos were dropped rather than over-processed.

## Privacy & shadowban safety
- [ ] NO phone number, WhatsApp, link, or @handle anywhere on the creative.
- [ ] NO phone number, link, or @handle in any caption.
- [ ] CTA is a soft prompt only ("DM to arrange a viewing").

## Format & quality
- [ ] Both 4:5 and 9:16 covers present.
- [ ] Cover is legible on a phone; bright/clean; palette on-brand.
- [ ] Carousel order: cover → real photos → CTA slide; ≤10 slides.
- [ ] Captions read well per platform; hashtags match the listing/area.

## Decision
- Approve → mark approved (later: set Airtable `Status = Approved`).
- Reject → note the reason so the skill can regenerate.
