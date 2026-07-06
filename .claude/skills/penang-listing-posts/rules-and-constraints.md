# Rules & constraints (HARD)

These are non-negotiable. If a run would violate any of these, stop and ask the
user rather than proceeding.

## 1. No hallucinated facts
Every factual claim in a creative or caption MUST trace to either:
- a scraped structured field (Price, Bedrooms, Bathrooms, Size, Tenure, Asset
  Type, Location, Property Type, Listed Date), or
- text the **owner themselves wrote** in the listing Title or Description.

Specifically:
- **Price**: use the exact scraped `Price (RM)`. Never round up or "start from"
  a lower number. Currency conversions are labelled approximate (see below).
- **Beds / baths / size / tenure**: include a stat chip ONLY if that field has a
  value. If it is blank, omit the chip. Never guess "3 bed" from a photo.
- **Area / project name**: only use an area or project name that appears in the
  Location field or is explicitly written in the Title/Description.
- **Amenities / features** (pool, sea view, renovated, furnished, etc.): only if
  the owner wrote it. Do not infer from photos.
- The stylist/copywriter's job is phrasing, tone, and CTA — not new facts.

If unsure whether something is supported by the source, leave it out.

## 2. Image integrity (three tiers)
The carousel body is the listing's **real photos**. AI tools may enhance a real
photo but never invent one. Three tiers:

- **Tier 1 — always allowed (non-generative):** crop, straighten,
  exposure/white-balance, denoise, mild sharpen, ML upscale/super-resolution.
  These only recover detail already present. No flag needed. Keep it light and
  bright; do not over-process.
- **Tier 2 — allowed, flagged for approval:** removing distractions that are not
  part of the property (trash bin, stray cable, watermark, reflection). Must NOT
  add or remove any actual feature of the space. Set `ai_enhanced = true`.
- **Tier 3 — never:** generating or replacing rooms, views, finishes,
  skies-as-a-feature; **virtual staging** (adding furniture to an empty room);
  or substituting a synthetic hero image. If a photo is too poor to fix within
  Tier 1–2, DROP it and use the listing's better photos instead.
- Rationale: these are real units being marketed to real buyers — a fabricated
  or virtually-staged interior is misrepresentation, not styling.

## 3. No contact info on any output (privacy + shadowban safety)
- NO phone number, WhatsApp number, external link, or @handle appears on any
  creative OR in any caption. This protects the owner's privacy AND avoids
  platform shadowbans (feeds penalise posts that push off-platform contact).
- The CTA is a **soft prompt only** — e.g. "DM to arrange a viewing",
  "Comment INFO", "Save & share". The posting account handles inbound DMs.
- The owner's number may be kept in a PRIVATE internal field for the agent's own
  follow-up only — never on a creative, caption, or anything public-facing.

## 4. Approval gate
- Nothing is scheduled or posted without a human setting `Status = Approved` in
  Airtable.
- This skill's job ends at "pushed to Airtable as Pending Review".

## 5. Accuracy of currency conversion
- MYR is the source of truth. USD and SGD figures are ESTIMATES and must be
  labelled as such (e.g. "≈ USD 255k", "approx."). Rates come from `context.md`
  and are refreshed periodically; never present a converted figure as exact.

## 6. Scope discipline
- Do not pad the qualifying set. If only 2 listings qualify today, produce 2.
- If 0 qualify, report that and stop — do not lower the threshold to find some.
