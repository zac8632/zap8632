---
description: Turn one post into a full carousel blueprint using an 11-template library. Supports --template and --lang flags. Hands off to ADAM for Canva-ready spec.
---

You are JOSH running `/repurpose-carousel <post-id> [--template <name>] [--lang <en|zh|bilingual>]`.

## Flow

1. **Read** the source post (from `.claude/content/` or arg), `.claude/brand/brand.md`, `.claude/brand/carousel-templates.md`, `.claude/brand/mandarin-terms.md`.

2. **Auto-pick template** if not specified — based on the source post's pillar:
   - Educational → Math Sheet / 3 Hidden Things / Framework / Comparison / Developer Scorecard / Location Deep-Dive
   - Contrarian → Hot Take / Myth-Buster / Warning Post
   - Personal → My Story / Case Study

3. **Route to ADAM** to build the slide-by-slide blueprint using the chosen template.

4. **ADAM outputs** per slide:
   - Headline (≤8 words, mobile-readable)
   - Body (≤30 words)
   - Visual direction
   - Sticky element
   - Continuity hint

5. **Apply Visual Signature** from brand.md Q7 (colors + non-negotiable).

6. **If bilingual mode:** every slide gets both English + Mandarin versions of headline and body — MEI writes the Mandarin natively (not translated).

7. **Save** to `.claude/content/carousels/YYYY-MM-DD-<slug>.md`.

## Available templates

**Educational:** math-sheet · hidden-3 · framework · comparison · dev-scorecard · location-deep-dive
**Contrarian:** hot-take · myth-buster · warning
**Personal:** my-story · case-study

## Flag examples

```
/repurpose-carousel post-1                              # auto-pick template, English
/repurpose-carousel post-1 --template hot-take          # force template
/repurpose-carousel post-1 --lang zh                    # Mandarin only
/repurpose-carousel post-1 --template math-sheet --lang bilingual   # both, math sheet
```

## Style
ADAM is spec-focused. Every element cited to brand.md Q7 (visual signature) so the agent's grid stays consistent.
