#!/usr/bin/env python3
"""
Stage 2 content builder for the listing-content-studio skill.

  build_captions(listing)   -> per-platform captions (raw, native, no hashtags,
                               soft CTA, no contact info).
  render_creatives(...)      -> clean overlay creatives in the @propertyluxemalaysia
                               style: full-bleed real photo, vertical project name
                               on the left, location + spec pill bottom-left, subtle
                               bottom scrim, optional small wordmark. Crops to 4:5
                               and 9:16.

Preview captions against the scrape (no photos needed):
    python post_content.py --input penang_owners.xlsx --demo 5
"""

import argparse
import os
import re
import sys

FX = {"usd": 0.213, "sgd": 0.287}

# Optional small wordmark shown top-centre. Empty = nothing (user has no logo).
WORDMARK = ""

# Coastal Luxe
NAVY = (10, 37, 64)
AZURE = (16, 130, 189)
WHITE = (255, 255, 255)


def price_num(v):
    if v in (None, ""):
        return None
    try:
        return float(re.sub(r"[^\d.]", "", str(v)))
    except ValueError:
        return None


def _approx(myr, rate):
    v = myr * rate
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M".replace(".0M", "M")
    return f"{round(v/1000)}k"


def price_lines(myr):
    if not myr:
        return None, None
    myr_s = f"RM {int(myr):,}"
    approx = f"≈ USD {_approx(myr, FX['usd'])} / SGD {_approx(myr, FX['sgd'])} approx."
    return myr_s, approx


def _clean(v):
    if v in (None, ""):
        return None
    s = str(v).strip().strip(",").strip()
    if s.lower() in ("nan", "none", "nat", "<na>"):
        return None
    return s or None


def project_name(listing):
    """The building/project name for the vertical label: the Title minus the
    trailing area. Owner's own words."""
    title = _clean(listing.get("Title")) or ""
    area = _clean(listing.get("Location")) or ""
    if area and title.lower().rstrip(".").endswith(area.lower()):
        title = title[: title.lower().rfind(area.lower())].strip().strip(",")
    return title or area


def spec_str(listing):
    parts = []
    bd = _clean(listing.get("Bedrooms"))
    ba = _clean(listing.get("Bathrooms"))
    sz = _clean(listing.get("Size (sqft)"))
    if bd:
        parts.append(f"{bd} Beds")
    if ba:
        parts.append(f"{ba} Baths")
    if sz:
        parts.append(f"{sz} sqft")
    return "  |  ".join(parts)


def facts_line(listing):
    bits = []
    for label, key in (("", "Location"),):
        pass
    area = _clean(listing.get("Location"))
    bd = _clean(listing.get("Bedrooms"))
    ba = _clean(listing.get("Bathrooms"))
    sz = _clean(listing.get("Size (sqft)"))
    tn = _clean(listing.get("Tenure"))
    out = []
    if area:
        out.append(area)
    if bd:
        out.append(f"{bd} bed")
    if ba:
        out.append(f"{ba} bath")
    if sz:
        out.append(f"{sz} sqft")
    if tn:
        out.append(tn)
    return " · ".join(out)


def is_rental(listing):
    """True if this is a rental listing rather than a sale. Prefers an
    explicit Listing Type (sale/rent, as Subsales sets it), falling back to
    the scraped Category text ("... For Rent")."""
    lt = str(listing.get("Listing Type") or "").strip().lower()
    if lt in ("rent", "sale"):
        return lt == "rent"
    return "for rent" in str(listing.get("Category") or "").lower()


def price_display(listing):
    """Rental-aware headline price. Returns (price_str, approx_or_None).
    Rentals read "For Rent RM X,XXX/mo" (monthly, no FX approx since a
    monthly rent in USD/SGD is meaningless to buyers); sales keep the
    RM figure plus the USD/SGD approximation."""
    myr = price_num(listing.get("Price (RM)"))
    if not myr:
        return None, None
    if is_rental(listing):
        return f"For Rent RM {int(myr):,}/mo", None
    myr_s = f"RM {int(myr):,}"
    approx = f"≈ USD {_approx(myr, FX['usd'])} / SGD {_approx(myr, FX['sgd'])} approx."
    return myr_s, approx


def condo_title(listing):
    """"<Condo Name>, <Area>" - the headline that must always identify the
    project. Falls back to whichever of project name / area is present."""
    proj = project_name(listing)
    area = _clean(listing.get("Location"))
    if proj and area and area.lower() not in proj.lower():
        return f"{proj}, {area}"
    return proj or area or "Property listing"


def _variant_index(listing, n):
    """Deterministic pick in range(n) from a stable per-listing seed, so the
    SAME listing always gets the same phrasing on every rerun (no caption
    flip-flopping day to day) while DIFFERENT listings vary - a feed of
    daily posts shouldn't read like the same sentence copy-pasted."""
    if n <= 1:
        return 0
    seed = str(listing.get("Listing URL") or listing.get("ID")
               or listing.get("Title") or condo_title(listing))
    return sum(seed.encode("utf-8")) % n


# Several ways to say the same facts - picked deterministically per listing
# (see _variant_index) so repeated exposure to the feed doesn't feel
# templated. "{lead}" is "<N>-bedroom <Type>" or bare "<Type>" when no
# bedroom count is known.
_DESCRIPTOR_TEMPLATES = [
    "{lead} {action} in {area}",
    "{lead} {action}, located in {area}",
    "Now {action}: {lead_lower} in {area}",
    "{area} — {lead} {action}",
]
_DESCRIPTOR_TEMPLATES_NO_AREA = [
    "{lead} {action}",
    "Now {action}: {lead_lower}",
]


def property_descriptor(listing):
    """A plain-prose one-liner - "3-bedroom Condominium for rent in
    Tanjong Tokong" - built only from fields already on the listing, with
    the phrasing varied per-listing (see _variant_index) instead of one
    fixed sentence skeleton reused everywhere."""
    bd = _clean(listing.get("Bedrooms"))
    ptype = normalize_property_type(_clean(listing.get("Property Type"))) or "property"
    area = _clean(listing.get("Location"))
    action = "for rent" if is_rental(listing) else "for sale"
    lead = f"{bd}-bedroom {ptype}" if bd else ptype

    templates = _DESCRIPTOR_TEMPLATES if area else _DESCRIPTOR_TEMPLATES_NO_AREA
    tmpl = templates[_variant_index(listing, len(templates))]
    # Lower the whole lead (not just its first letter) for the
    # mid-sentence variant - a multi-word type like "Apartment /
    # Condominium" would otherwise end up inconsistently cased
    # ("apartment / Condominium").
    s = tmpl.format(lead=lead, lead_lower=lead.lower(), action=action, area=area or "")
    return s[0].upper() + s[1:]


def is_new_today(listing):
    v = listing.get("Is New Today")
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes")


def normalize_property_type(ptype):
    """mudah's own category label is sometimes a combined pair like
    "Apartment / Condominium" (it's their category name, not two separate
    facts) - reading that literally into a caption produces an awkward
    "apartment / condominium for sale" everywhere. Pick ONE term: prefer
    "Condominium" when it's one of the options (the more common marketing
    term locally), otherwise the first option."""
    if not ptype:
        return ptype
    if "/" in ptype:
        parts = [p.strip() for p in ptype.split("/") if p.strip()]
        for p in parts:
            if "condo" in p.lower():
                return p
        return parts[0] if parts else ptype
    return ptype


def specs_plain(listing):
    """"3 bed · 2 bath · 800 sqft" - no emoji, for the text-first platforms."""
    bd = _clean(listing.get("Bedrooms"))
    ba = _clean(listing.get("Bathrooms"))
    sz = _clean(listing.get("Size (sqft)"))
    out = []
    if bd:
        out.append(f"{bd} bed")
    if ba:
        out.append(f"{ba} bath")
    if sz:
        out.append(f"{sz} sqft")
    return " · ".join(out)


def spec_str_emoji(listing):
    """"🛏 3 Beds · 🛁 2 Baths · 📐 800 sqft" - for the emoji-friendly IG caption."""
    bd = _clean(listing.get("Bedrooms"))
    ba = _clean(listing.get("Bathrooms"))
    sz = _clean(listing.get("Size (sqft)"))
    out = []
    if bd:
        out.append(f"🛏 {bd} Beds")
    if ba:
        out.append(f"🛁 {ba} Baths")
    if sz:
        out.append(f"📐 {sz} sqft")
    return " · ".join(out)


def extras_line(listing):
    """Tenure + furnishing, whichever are present."""
    tn = _clean(listing.get("Tenure"))
    fn = _clean(listing.get("Furnishing"))
    return " · ".join([x for x in (tn, fn) if x])


_PHONE_RE = re.compile(r"(?:\+?6?0)?\s?1\d[\s\-]?\d{3,4}[\s\-]?\d{3,4}")
_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
_EMAIL_RE = re.compile(r"\b[\w.+\-]+@[\w\-]+\.\w+\b")
_HANDLE_RE = re.compile(r"(?<!\w)@\w+")
_CONTACT_KEYWORD_RE = re.compile(
    r"(?i)\b(call|whatsapp|wasap|wa|contact|hubungi|hp|tel|telephone|phone|"
    r"dm|pm|email|e-mail|mail|reach)\b")


def scrub_contact(text):
    """Strip contact info from owner-written description text before it goes
    into a PUBLIC caption - these are re-posted owner listings and the
    no-contact-info rule (and basic privacy) means their number/email must
    never leak. Works sentence-by-sentence so one "call me" clause at the
    end doesn't wipe the whole (otherwise fine) description."""
    if not text:
        return ""
    # Remove obvious tokens first (URLs/emails/@handles) everywhere.
    t = _URL_RE.sub(" ", text)
    t = _EMAIL_RE.sub(" ", t)
    t = _HANDLE_RE.sub(" ", t)
    # Then drop any sentence still carrying a phone number or a contact
    # keyword ("call", "whatsapp", "email me", etc), keeping the rest.
    kept = []
    for chunk in re.split(r"(?<=[.!?])\s+|\n+", t):
        stripped = _PHONE_RE.sub(" ", chunk)
        if _PHONE_RE.search(chunk) or _CONTACT_KEYWORD_RE.search(stripped):
            continue
        kept.append(stripped.strip())
    return " ".join(x for x in kept if x)


# Real-estate selling-point phrases to look for in the owner's OWN free
# text - the mudah "Description" field, or (for the Telegram bot) whatever
# text the operator pasted describing the listing. Matches are pulled out
# VERBATIM from that text and reused, never paraphrased or invented, so a
# caption only ever claims something like "sea view" when the owner
# actually wrote it somewhere. Ordered by priority (checked in this order,
# stops once max_n are found) - prestige/luxury signals researched from how
# Singapore luxury listings frame high-end condos (private lift, dual key,
# sky facilities, unblocked view, tenure prestige, MRT connectivity) come
# first, general condition/location phrases after.
_HIGHLIGHT_PATTERNS = [
    re.compile(r"\bprivate\s+lift\b", re.I),
    re.compile(r"\bdual\s*[- ]?key\b", re.I),
    re.compile(r"\bpenthouse\b", re.I),
    re.compile(r"\b(?:sky|infinity|roof-?top)\s*(?:terrace|pool|garden|deck)\b", re.I),
    re.compile(r"\b(?:un(?:blocked|obstructed)|panoramic)\s+(?:sea\s+)?view\b", re.I),
    re.compile(r"\b999[- ]?year\s+leasehold\b", re.I),
    re.compile(r"\bfreehold\b", re.I),
    re.compile(r"\b(?:walk(?:ing)?\s+distance|near(?:by)?|steps?\s+(?:away\s+)?from)\s+(?:to\s+)?(?:the\s+)?(?:mrt|lrt)\b", re.I),
    re.compile(r"\bsmart\s+home\b", re.I),
    re.compile(r"\bwalk-?in\s+wardrobe\b", re.I),
    re.compile(r"\bconcierge\b", re.I),
    re.compile(r"\b(?:sea|pool|city|garden|park|mountain)\s+view\b", re.I),
    re.compile(r"\bcorner\s+(?:unit|lot)\b", re.I),
    re.compile(r"\b(?:fully|newly|recently)\s+renovated\b", re.I),
    re.compile(r"\bmove[- ]?in\s+ready\b", re.I),
    re.compile(r"\bgated\s*(?:&|and)?\s*guarded\b", re.I),
    re.compile(r"\bwalking\s+distance\s+to\s+[A-Za-z][\w &]{2,30}", re.I),
    re.compile(r"\bhigh\s+floor\b", re.I),
    re.compile(r"\blow\s+density\b", re.I),
    re.compile(r"\bfacing\s+(?:the\s+)?(?:sea|pool|park|city)\b", re.I),
    re.compile(r"\brenovated\s+kitchen\b", re.I),
    re.compile(r"\bnear(?:by)?\s+[A-Za-z][\w &]{2,30}", re.I),
]


def extract_highlights(text, max_n=3):
    """Pull up to max_n short, real selling-point phrases straight out of
    the owner's own free text - verbatim substrings, never paraphrased or
    invented (see _HIGHLIGHT_PATTERNS). max_n=3 (was 2) - the luxury segment
    this pipeline targets benefits from a couple more concrete selling
    points than a mass-market listing would need."""
    if not text:
        return []
    found, seen = [], set()
    for pat in _HIGHLIGHT_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        phrase = re.sub(r"\s+", " ", m.group(0)).strip(" ,.-")
        key = phrase.lower()
        if key not in seen:
            seen.add(key)
            found.append(phrase)
        if len(found) >= max_n:
            break
    return found


# Size-driven adjectives - a genuine inference from the listing's own sqft
# figure (the way a real agent would describe it), not an invented claim.
# Several options per band, picked deterministically (see _variant_index).
_SIZE_BANDS = [
    (0, 600, ["cozy", "compact"]),
    (600, 1200, ["comfortable", "well-proportioned"]),
    (1200, 2500, ["spacious", "generously sized"]),
    (2500, float("inf"), ["expansive", "grand"]),
]

# How the fact list is joined onto the lead clause - varied per listing so
# it doesn't always read "featuring X, Y, Z."
_FACT_CONNECTORS = ["with", "featuring", "boasting", "offering"]


def _size_adjective(listing, sz_num):
    for lo, hi, options in _SIZE_BANDS:
        if lo <= sz_num < hi:
            return options[_variant_index(listing, len(options))]
    return None


def generate_description(listing):
    """A short natural-language description that reads like an actual
    listing blurb, not a spec sheet in prose. Built from:
      - the listing's own structured facts (bedrooms/bathrooms/size/tenure/
        furnishing) - stated with varied connectors and a size-driven
        adjective, never a fixed "featuring A, B, C." skeleton
      - real selling-point phrases pulled VERBATIM from the owner's own
        free text (mudah's Description field, or whatever was pasted into
        the Telegram bot), if any exist - see extract_highlights()
    Never invents amenities, condition, or claims not present in one of
    those two real sources. Phrasing varies per-listing (see
    _variant_index) so a feed of these doesn't read like a form letter."""
    ptype = (normalize_property_type(_clean(listing.get("Property Type"))) or "property").lower()
    area = _clean(listing.get("Location"))
    action = "for rent" if is_rental(listing) else "for sale"
    bd = _clean(listing.get("Bedrooms"))
    ba = _clean(listing.get("Bathrooms"))
    sz = _clean(listing.get("Size (sqft)"))
    sz_num = price_num(sz)
    tenure = _clean(listing.get("Tenure"))
    furnishing = _clean(listing.get("Furnishing"))
    highlights = extract_highlights(_clean(listing.get("Description")))

    facts = []
    if bd:
        facts.append(f"{bd} bedroom{'s' if bd != '1' else ''}")
    if ba:
        facts.append(f"{ba} bathroom{'s' if ba != '1' else ''}")
    if sz:
        facts.append(f"{sz} sqft")
    if not facts and not area and not highlights:
        return None  # not enough on this listing to say anything real

    adjective = _size_adjective(listing, sz_num) if sz_num else None
    lead_ptype = f"{adjective} {ptype}" if adjective else ptype
    lead = f"This {lead_ptype} {action}" + (f" in {area}" if area else "")

    if facts:
        connector = _FACT_CONNECTORS[_variant_index(listing, len(_FACT_CONNECTORS))]
        if len(facts) > 1:
            facts_txt = ", ".join(facts[:-1]) + f" and {facts[-1]}"
        else:
            facts_txt = facts[0]
        body = f"{lead}, {connector} {facts_txt}"
    else:
        body = lead

    if highlights:
        # Lowercase each phrase's first letter for the mid-sentence join -
        # they're common noun phrases ("Corner unit" -> "corner unit"), not
        # proper nouns, so this keeps the sentence grammatically consistent
        # regardless of how the owner happened to capitalize their text.
        lowered = [h[0].lower() + h[1:] for h in highlights]
        body += " — " + " and ".join(lowered)
    body += "."

    extras = [x for x in (tenure, furnishing) if x]
    if extras:
        body += " " + " · ".join(extras) + "."
    return body


def description_snippet(listing, max_chars=300):
    """A cleaned, contact-scrubbed excerpt of the owner's own description,
    for the longer IG/FB captions. Falls back to an auto-generated
    fact-based description (generate_description) when the owner left no
    usable text - the caption paragraph is never just silently dropped."""
    raw = _clean(listing.get("Description"))
    txt = ""
    if raw:
        txt = scrub_contact(raw)
        txt = re.sub(r"[•*►▪◆✦✅➤●]+", " ", txt)
        txt = re.sub(r"\s+", " ", txt).strip(" -–—·|")
    if len(txt) < 20:
        txt = generate_description(listing) or ""
        if not txt:
            return None
    if len(txt) > max_chars:
        cut = txt[:max_chars]
        end = max(cut.rfind(". "), cut.rfind("! "))
        if end > 60:
            txt = cut[: end + 1]
        else:
            txt = cut.rsplit(" ", 1)[0].rstrip(",.") + "…"
    return txt


def split_into_paragraphs(text, sentences_per_para=2):
    """Break a longer description into short paragraphs (blank line between
    each) instead of one dense block - easier to read/scan on IG and FB.
    Short text (<= sentences_per_para sentences) is left as a single
    paragraph, so this only kicks in when there's actually enough content
    to benefit from a break."""
    if not text:
        return text
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if len(sentences) <= sentences_per_para:
        return text
    paragraphs = [" ".join(sentences[i:i + sentences_per_para])
                  for i in range(0, len(sentences), sentences_per_para)]
    return "\n\n".join(paragraphs)


def _history_key(project, listing_type):
    return f"{listing_type}:{project.strip().lower()}"


def _area_history_key(area, listing_type):
    # "__area__" prefix namespaces this apart from real project names (a
    # project would need to be literally named "__area__<area>" to collide,
    # which won't happen) so both bucket kinds share the one price_history
    # dict without a separate file/parameter.
    return _history_key(f"__area__{area}", listing_type)


def _psf_ratio_note(psf, entries, label):
    """Shared comparison: psf vs. the median of `entries`, worded as a
    "X% below {label}" note. Returns None when there isn't enough history
    or the listing isn't meaningfully (but plausibly) cheaper."""
    if len(entries) < 2:
        return None
    s = sorted(entries)
    median = s[len(s) // 2]
    if median <= 0:
        return None
    ratio = psf / median
    # Meaningfully cheaper (>=8%) but not so far below that it'd already be
    # caught as a price anomaly (<0.4x median) - that's a data-quality flag
    # to review, not a deal worth advertising.
    if 0.4 <= ratio <= 0.92:
        return f"~{round((1 - ratio) * 100)}% below {label}"
    return None


def value_note(listing, price_history=None):
    """"~15% below {project}'s recent asking psf" - a real, computed signal,
    shown ONLY when the listing is genuinely priced below recent history for
    the SAME project. Falls back to an area-level comparison (still real
    history, just less specific) when this project doesn't have its own 2+
    prior listings to compare against yet - most projects only accumulate a
    couple of listings a month, so project-only comparison left most
    listings with no value signal at all. Reads the SAME persisted memory
    subsales_listing_builder.py's anomaly checker writes to
    (subsales_price_history.json) - never fabricated, and returns None
    whenever there isn't enough history of either kind to compare against."""
    if not price_history:
        return None
    myr = price_num(listing.get("Price (RM)"))
    sz = price_num(listing.get("Size (sqft)"))
    proj = project_name(listing)
    area = _clean(listing.get("Location"))
    if not myr or not sz or (not proj and not area):
        return None
    listing_type = "rent" if is_rental(listing) else "sale"
    psf = myr / sz

    if proj:
        note = _psf_ratio_note(psf, price_history.get(_history_key(proj, listing_type), []),
                                f"{proj}'s recent asking psf")
        if note:
            return note
    if area:
        return _psf_ratio_note(psf, price_history.get(_area_history_key(area, listing_type), []),
                                f"{area}'s recent asking psf")
    return None


def price_drop_note(listing):
    """"Reduced from RM X to RM Y" - a genuinely strong, 100%-factual
    urgency signal when this listing's price has actually dropped since it
    was first tracked. Reads a "Price Change" field precomputed by
    subsales_listing_builder.py (which is the only place with the
    persistent per-listing price history needed to detect a drop) - simply
    returns None for any listing that doesn't have one, so this is a no-op
    outside the Subsales flow rather than a crash."""
    return _clean(listing.get("Price Change"))


CTA = "DM to arrange a viewing"
SAVE_PROMPT = "Save this for later"
SWIPE_PROMPT = "Swipe for more photos"

# Several CTA phrasings in the same register (this pipeline only ever posts
# high-end/luxury-segment listings, so there's no separate "budget" tone to
# switch between) - picked deterministically per listing (see
# _variant_index) so a feed of daily posts doesn't end every single one
# with the exact same sentence.
_CTA_POOL = [
    "DM to arrange a viewing",
    "Message us to arrange a private viewing",
    "Enquire for a private viewing",
    "Reach out to schedule a viewing",
    "Contact us for an exclusive viewing",
]


def cta_for(listing):
    return _CTA_POOL[_variant_index(listing, len(_CTA_POOL))]


def headline(listing):
    """A punchier opener than the bare project name - just a different
    arrangement of fields already on the listing (bedrooms, property type,
    area, "new today" flag), nothing invented. Falls back to project_name()
    when there isn't enough to build one."""
    bits = []
    if listing.get("Is New Today"):
        bits.append("Just Listed:")
    bd = _clean(listing.get("Bedrooms"))
    ptype = _clean(listing.get("Property Type"))
    area = _clean(listing.get("Location"))
    if bd and ptype:
        bits.append(f"{bd}-Bed {ptype}")
    elif ptype:
        bits.append(ptype)
    if area:
        bits.append(f"in {area}")
    text = " ".join(bits).strip()
    return text or project_name(listing)


def build_captions(listing, price_history=None):
    """Per-platform captions, each written in that platform's native voice
    rather than one caption reused everywhere. Every caption leads with the
    condo name + area and states rent vs sale price explicitly. IG/FB get a
    longer, standardized structure; Threads and WhatsApp get shorter,
    direct phrasings. All are contact-free and hashtag-free.

    price_history: optional dict (the same one subsales_listing_builder.py
    persists to subsales_price_history.json) - when passed, a listing
    genuinely priced below its project's recent psf gets a real "X% below"
    callout (see value_note). Omit it and that line is simply skipped."""
    title = condo_title(listing)
    descriptor = property_descriptor(listing)
    snippet = description_snippet(listing)
    # IG/FB are the longer-format captions - split a substantial snippet
    # into short paragraphs instead of one dense block. Threads/WhatsApp
    # stay as a single line by design (they're meant to be short), so they
    # keep using the un-split `snippet` below.
    snippet_long = split_into_paragraphs(snippet) if snippet else None
    price_s, approx = price_display(listing)
    specs_e = spec_str_emoji(listing)
    specs_p = specs_plain(listing)
    extras = extras_line(listing)
    price_block = (price_s + (f"  ({approx})" if approx else "")) if price_s else ""
    value = value_note(listing, price_history)
    drop = price_drop_note(listing)
    fresh = is_new_today(listing)
    cta = cta_for(listing)

    # A single strongest, scroll-stopping fact for the very first line - IG
    # (and most feeds) truncate the caption at ~125-140 characters before
    # "more", so whatever's most compelling needs to be at the very top,
    # not buried after the title and spec list. Priority: a real price cut
    # beats a value callout beats a highlight pulled from the owner's text -
    # each is a genuine, sourced fact, never invented for effect. Whichever
    # one becomes the hook is NOT repeated again lower in the caption.
    top_highlight = (extract_highlights(_clean(listing.get("Description")), max_n=1) or [None])[0]
    hook_source = "drop" if drop else "value" if value else "highlight" if top_highlight else None
    hook = {"drop": drop, "value": value, "highlight": top_highlight}.get(hook_source)

    # ---- Instagram: standardized, longer carousel caption ----
    ig = []
    if hook:
        ig.append(f"🔥 {hook[0].upper()}{hook[1:]}")
    ig.append(("🆕 Just Listed\n" if fresh else "") + f"🏙 {title}")
    ig.append("")
    ig.append(descriptor + ".")
    if snippet_long:
        ig += ["", snippet_long]
    ig.append("")
    if specs_e:
        ig.append(specs_e)
    if extras:
        ig.append(f"🏷 {extras}")
    if price_block:
        ig.append(f"💰 {price_block}")
    if drop and hook_source != "drop":
        ig.append(f"📉 {drop}")
    if value and hook_source != "value":
        ig.append(f"💎 {value}")
    ig += ["", f"➡️ {SWIPE_PROMPT}", f"💬 {cta}", f"📌 {SAVE_PROMPT}"]
    instagram = "\n".join(ig)

    # ---- Facebook: longer, prose intro + a scannable detail list. FB has
    # no practical length limit and its audience skims bulleted specs. ----
    lead = descriptor
    if price_s:
        lead += f" — {price_s}" if is_rental(listing) else f", priced at {price_s}"
    fb_title = ("🆕 Just Listed — " if fresh else "") + title
    fb = [fb_title, "", lead + "."]
    if snippet_long:
        fb += ["", snippet_long]
    details = []
    for label, key in (("Bedrooms", "Bedrooms"), ("Bathrooms", "Bathrooms"),
                        ("Built-up", "Size (sqft)"), ("Tenure", "Tenure"),
                        ("Furnishing", "Furnishing")):
        val = _clean(listing.get(key))
        if val:
            suffix = " sqft" if key == "Size (sqft)" else ""
            details.append(f"• {label}: {val}{suffix}")
    if price_block:
        details.append(f"• Price: {price_block}")
    if drop:
        details.append(f"• Price change: {drop}")
    if value:
        details.append(f"• Value: {value}")
    if details:
        fb += ["", "Details:"] + details
    fb += ["", f"{cta}."]
    facebook = "\n".join(fb)

    # ---- Threads: short, conversational, no emoji spam ----
    th_title = ("New: " if fresh else "") + title
    th_lines = [th_title]
    sub = descriptor + (f" · {price_s}" if price_s else "")
    th_lines.append(sub)
    if specs_p:
        th_lines.append(specs_p)
    if drop:
        th_lines.append(drop.capitalize())
    if value:
        th_lines.append(value.capitalize())
    th_lines.append(cta)
    threads = "\n".join(th_lines)

    # ---- WhatsApp / Telegram broadcast: plain, direct, *bold* title ----
    wa = []
    if fresh:
        wa.append("🆕 *Just Listed*")
    wa.append(f"*{title}*")
    if price_s:
        wa.append(price_s)
    wa_specs = " · ".join([x for x in (specs_p, extras) if x])
    if wa_specs:
        wa.append(wa_specs)
    if drop:
        wa.append(drop.capitalize())
    if value:
        wa.append(value.capitalize())
    if snippet:
        wa.append(description_snippet(listing, max_chars=180))
    wa.append(cta)
    whatsapp = "\n".join(wa)

    # ---- TikTok / Story kept for back-compat (not a focus platform) ----
    tk = [title]
    if price_s:
        tk.append(price_s + (f" · {specs_p}" if specs_p else ""))
    tk += [f"➡️ {SWIPE_PROMPT}", cta]
    tiktok = "\n".join(tk)
    story = f"{title}\n{price_s}\n{cta}" if price_s else f"{title}\n{cta}"

    return {"instagram": instagram, "facebook": facebook, "threads": threads,
            "whatsapp": whatsapp, "tiktok": tiktok, "story": story}


# ------------------------------ creatives ------------------------------

def _smart_crop(img, rw, rh, max_crop_loss=None):
    """Center-crop to the target ratio. If max_crop_loss is set and the crop
    would remove more than that fraction of the image's width/height, returns
    None instead - the caller should letterbox rather than risk cutting off
    real content (common when a 4:5 or landscape photo is forced into a much
    narrower 9:16 Story frame)."""
    w, h = img.size
    target = rw / rh
    cur = w / h
    if cur > target:
        nw = int(h * target)
        if max_crop_loss is not None and (1 - nw / w) > max_crop_loss:
            return None
        left = (w - nw) // 2
        return img.crop((left, 0, left + nw, h))
    nh = int(w / target)
    if max_crop_loss is not None and (1 - nh / h) > max_crop_loss:
        return None
    top = int((h - nh) * 0.4)
    return img.crop((0, top, w, top + nh))


def _letterbox_fill(img, W, H):
    """Used when a hard crop would lose too much of the photo (e.g. a 4:5 or
    landscape photo forced into 9:16): fills the full canvas with a blurred,
    darkened crop of the same photo, then composites the WHOLE original photo
    (scaled to fit, nothing cut off) centered on top. Standard technique for
    turning a wider photo into Story/Reels format without losing content."""
    from PIL import Image, ImageFilter, ImageEnhance
    bg = _smart_crop(img, W, H).resize((W, H), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(40))
    bg = ImageEnhance.Brightness(bg).enhance(0.55)

    scale = W / img.width
    fit_w, fit_h = W, int(img.height * scale)
    if fit_h > H:
        scale = H / img.height
        fit_w, fit_h = int(img.width * scale), H
    fitted = img.resize((fit_w, fit_h), Image.LANCZOS)
    canvas = bg.convert("RGB")
    canvas.paste(fitted, ((W - fit_w) // 2, (H - fit_h) // 2))
    return canvas


def _font(size, bold=False):
    from PIL import ImageFont
    cands = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for p in cands:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _bottom_scrim(base):
    from PIL import Image
    W, H = base.size
    start = int(H * 0.55)
    grad = Image.new("L", (1, H), 0)
    px = grad.load()
    for y in range(H):
        px[0, y] = 0 if y < start else int(205 * (y - start) / max(1, H - start))
    alpha = grad.resize((W, H))
    dark = Image.new("RGBA", (W, H), NAVY + (255,))
    dark.putalpha(alpha)
    return Image.alpha_composite(base.convert("RGBA"), dark)


def _vertical_label(text, size):
    from PIL import Image, ImageDraw
    font = _font(size)
    spaced = " ".join(text.upper())  # airy letter-spacing like the reference
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    b = tmp.textbbox((0, 0), spaced, font=font)
    tw, th = b[2] - b[0], b[3] - b[1]
    layer = Image.new("RGBA", (tw + 20, th + 20), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((10 - b[0], 10 - b[1]), spaced, font=font,
                               fill=(255, 255, 255, 235))
    return layer.rotate(90, expand=True)


def _pill(img, x, y, text, size):
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img, "RGBA")
    font = _font(size, bold=True)
    b = draw.textbbox((0, 0), text, font=font)
    tw, th = b[2] - b[0], b[3] - b[1]
    padx, pady = int(size * 0.7), int(size * 0.5)
    draw.rounded_rectangle([x, y, x + tw + padx * 2, y + th + pady * 2],
                           radius=int((th + pady * 2) / 2), fill=AZURE + (235,))
    draw.text((x + padx - b[0], y + pady - b[1]), text, font=font, fill=WHITE)
    return y + th + pady * 2


def _auto_brighten(img, dark_threshold=95.0, target_mean=130.0):
    """Tier 1 (non-generative, rules-and-constraints.md): gamma-brighten
    photos that read as dark, up to a target mean luminance. Normally-lit
    photos pass through untouched - this only recovers visibility of detail
    already present, never invents anything, so no ai_enhanced flag needed."""
    import numpy as np
    from PIL import Image
    gray = np.asarray(img.convert("L"), dtype=np.float64)
    mean = gray.mean()
    if mean <= 0 or mean >= dark_threshold:
        return img
    gamma = np.log(target_mean / 255.0) / np.log(mean / 255.0)
    gamma = min(max(gamma, 0.35), 1.0)  # only ever brighten, keep it moderate
    arr = np.asarray(img, dtype=np.float64) / 255.0
    arr = np.power(arr, gamma) * 255.0
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def render_creatives(photo_paths, listing, out_dir, tag=True):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Pillow not installed (pip install pillow) — skipping render.", file=sys.stderr)
        return {"4x5": [], "9x16": []}

    os.makedirs(out_dir, exist_ok=True)
    # Rental-aware: "For Rent RM 2,000/mo" for rentals, "RM 350,000" for sales.
    myr_s, _ = price_display(listing)
    area = _clean(listing.get("Location"))
    proj = project_name(listing)
    specs = spec_str(listing)

    out = {"4x5": [], "9x16": []}
    # bottom_ui = clearance kept above the true bottom edge for the price/
    # location/spec text block. 9:16 lowered from 330->220 per visual review
    # (was sitting too high) while staying clear of the ~320px Story/TikTok UI
    # zone documented in platform-specs.md - tune further here if needed.
    sizes = {"4x5": (1080, 1350, 4, 5, 70), "9x16": (1080, 1920, 9, 16, 220)}

    for key, (W, H, rw, rh, bottom_ui) in sizes.items():
        for i, ph in enumerate(photo_paths):
            try:
                img = Image.open(ph).convert("RGB")
            except Exception as e:
                print(f"  [render] skip {ph}: {e}", file=sys.stderr)
                continue
            # Horizontal (landscape) source photos don't belong in a 9:16
            # vertical creative - forcing them in means an ugly letterbox or a
            # heavy crop. Skip the vertical for landscape shots; the 4:5 still
            # gets made. A clearly-landscape frame is width > ~1.1x height.
            if key == "9x16" and img.width > img.height * 1.1:
                continue
            img = _auto_brighten(img)
            # 9:16 is a much narrower target than most real-estate photos are
            # shot in - a plain center-crop risks cutting off real content, so
            # fall back to a letterboxed (blurred-background) fill whenever
            # the crop would lose more than 30% of the frame.
            cropped = _smart_crop(img, rw, rh, max_crop_loss=0.30 if key == "9x16" else None)
            base = (cropped.resize((W, H), Image.LANCZOS) if cropped is not None
                    else _letterbox_fill(img, W, H))

            if tag and i == 0:
                canvas = _bottom_scrim(base)
                margin = int(W * 0.055)
                # vertical project name, left edge
                if proj:
                    vlabel = _vertical_label(proj[:22], int(W * 0.05))
                    canvas.alpha_composite(vlabel, (int(W * 0.015),
                                                    int(H * 0.10)))
                # bottom-left stack: price, location, spec pill
                draw = ImageDraw.Draw(canvas, "RGBA")
                y = H - bottom_ui
                block_h = 0
                if myr_s:
                    block_h += int(W * 0.075) + 12
                if area:
                    block_h += int(W * 0.042) + 10
                if specs:
                    block_h += int(W * 0.07)
                y = H - bottom_ui - block_h
                if myr_s:
                    f = _font(int(W * 0.075), bold=True)
                    draw.text((margin, y), myr_s, font=f, fill=WHITE)
                    y += int(W * 0.075) + 12
                if area:
                    f = _font(int(W * 0.042))
                    draw.text((margin, y), area, font=f, fill=(235, 240, 245, 255))
                    y += int(W * 0.042) + 10
                if specs:
                    _pill(canvas, margin, y, specs, int(W * 0.033))
                if WORDMARK:
                    f = _font(int(W * 0.032), bold=True)
                    b = draw.textbbox((0, 0), WORDMARK, font=f)
                    draw.text(((W - (b[2] - b[0])) / 2, int(H * 0.03)),
                              WORDMARK, font=f, fill=(255, 255, 255, 230))
                base = canvas.convert("RGB")

            fn = os.path.join(out_dir, f"{key}_{i+1:02d}.jpg")
            base.save(fn, quality=92)
            out[key].append(fn)
    return out


def main():
    import pandas as pd
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default="penang_owners.xlsx")
    ap.add_argument("--demo", type=int, default=5)
    args = ap.parse_args()

    from build_listing_posts import qualifies
    df = pd.read_excel(args.input, sheet_name="All Listings", dtype=str)
    q = df[df.apply(qualifies, axis=1)]
    print(f"{len(q)} qualifying; captions for {min(args.demo, len(q))}:\n", file=sys.stderr)
    for _, row in q.head(args.demo).iterrows():
        caps = build_captions(row)
        print("=" * 60)
        print(f"{row.get('Title')}  |  {row.get('Price')}")
        print(caps["instagram"])
        print()


if __name__ == "__main__":
    main()
