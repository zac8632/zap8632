---
name: caption-and-cta
description: Write platform-native captions with a CTA that actually drives action. Triggers on "/caption-and-cta", "/caption", "/cta", "write a caption", "caption for this", "caption this post", or any time the creator has a post and needs the caption plus the right call to action. Routes the CTA to the right mechanism per platform (ManyChat keyword on Instagram, link on LinkedIn, reply-bait on X). Reads the voice doc for tone.
---

# Caption + CTA

Writes the caption AND makes the CTA actually convert. Most captions die at the CTA — this skill routes the call to action to the right mechanism for each platform.

## When to run this

- A post is ready, the caption isn't
- The caption needs to drive a specific action (DM, save, click, reply, follow)
- Cross-posting and each platform needs a native caption + native CTA

## Not this skill — use instead

- Dedicated Instagram content (caption + the actual Canva visual, using the 15-template funnel framework and hook bank) → use `penang-ig-templates` instead; that skill owns Instagram end-to-end, including the caption. Use `caption-and-cta` for WhatsApp, LinkedIn, X/Threads, TikTok, or when cross-posting the same content to multiple non-IG platforms at once.

## Inputs

Required:
- The post topic or the content it accompanies
- Platform (Instagram, LinkedIn, X/Threads, TikTok)
- Desired action (lead capture, saves, link click, replies, follows)

Reads if available:
- Voice doc
- The freebie/offer being promoted
- ManyChat keyword (for IG)

## Platform CTA routing

**Instagram:** ManyChat keyword in comments ("Comment WORD"). Caption short for Reels, line-broken for carousels.
**WhatsApp broadcast:** No CTA mechanism needed beyond a direct reply prompt ("Reply YES for the full report") — WhatsApp is a closed channel, the ask can be more direct than on public platforms. Keep it short; this is the highest-intent channel for Malaysian real estate outreach specifically.
**LinkedIn:** Link in caption body (no penalty for relevant links). First line must hook before "see more."
**X/Threads:** Reply-bait or thread continuation. No links in the main post where avoidable.
**TikTok:** Comment-bait or link in bio. Very short caption.

## Output structure

```
## [Platform] caption

[The caption]

CTA mechanism: [What this triggers and how]
[Platform-specific notes]
```

## Process

1. Read voice doc if present
2. Confirm platform and desired action
3. Write the platform-native caption
4. Route the CTA to the right mechanism
5. For IG, suggest the keyword if none supplied

## Critical rules

- The CTA is part of the caption. A caption without one is incomplete.
- Each platform gets its own native caption — never one generic caption relabelled.
- LinkedIn first line must hook before the "see more" cut.
- IG defaults to ManyChat keyword unless told otherwise.
- Match the voice doc's banned-phrase list. No emojis unless the voice doc allows.
