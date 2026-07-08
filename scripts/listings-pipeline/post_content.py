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


def property_descriptor(listing):
    """A plain-prose one-liner - "3-bedroom Condominium for rent in
    Tanjong Tokong" - built only from fields already on the listing."""
    bd = _clean(listing.get("Bedrooms"))
    ptype = _clean(listing.get("Property Type")) or "property"
    area = _clean(listing.get("Location"))
    action = "for rent" if is_rental(listing) else "for sale"
    lead = f"{bd}-bedroom {ptype}" if bd else ptype
    s = f"{lead} {action}"
    if area:
        s += f" in {area}"
    return s[0].upper() + s[1:]


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


def description_snippet(listing, max_chars=300):
    """A cleaned, contact-scrubbed excerpt of the owner's own description,
    for the longer IG/FB captions. Returns None if nothing usable survives."""
    raw = _clean(listing.get("Description"))
    if not raw:
        return None
    txt = scrub_contact(raw)
    txt = re.sub(r"[•*►▪◆✦✅➤●]+", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip(" -–—·|")
    if len(txt) < 20:
        return None
    if len(txt) > max_chars:
        cut = txt[:max_chars]
        end = max(cut.rfind(". "), cut.rfind("! "))
        if end > 60:
            txt = cut[: end + 1]
        else:
            txt = cut.rsplit(" ", 1)[0].rstrip(",.") + "…"
    return txt


CTA = "DM to arrange a viewing"
SAVE_PROMPT = "Save this for later"
SWIPE_PROMPT = "Swipe for more photos"


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


def build_captions(listing):
    """Per-platform captions, each written in that platform's native voice
    rather than one caption reused everywhere. Every caption leads with the
    condo name + area and states rent vs sale price explicitly. IG/FB get a
    longer, standardized structure; Threads and WhatsApp get shorter,
    direct phrasings. All are contact-free and hashtag-free."""
    title = condo_title(listing)
    descriptor = property_descriptor(listing)
    snippet = description_snippet(listing)
    price_s, approx = price_display(listing)
    specs_e = spec_str_emoji(listing)
    specs_p = specs_plain(listing)
    extras = extras_line(listing)
    price_block = (price_s + (f"  ({approx})" if approx else "")) if price_s else ""

    # ---- Instagram: standardized, longer carousel caption ----
    ig = [f"🏙 {title}", ""]
    ig.append(descriptor + ".")
    if snippet:
        ig += ["", snippet]
    ig.append("")
    if specs_e:
        ig.append(specs_e)
    if extras:
        ig.append(f"🏷 {extras}")
    if price_block:
        ig.append(f"💰 {price_block}")
    ig += ["", f"➡️ {SWIPE_PROMPT}", f"💬 {CTA}", f"📌 {SAVE_PROMPT}"]
    instagram = "\n".join(ig)

    # ---- Facebook: longer, prose intro + a scannable detail list. FB has
    # no practical length limit and its audience skims bulleted specs. ----
    lead = descriptor
    if price_s:
        lead += f" — {price_s}" if is_rental(listing) else f", priced at {price_s}"
    fb = [title, "", lead + "."]
    if snippet:
        fb += ["", snippet]
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
    if details:
        fb += ["", "Details:"] + details
    fb += ["", f"{CTA}."]
    facebook = "\n".join(fb)

    # ---- Threads: short, conversational, no emoji spam ----
    th_lines = [title]
    sub = descriptor + (f" · {price_s}" if price_s else "")
    th_lines.append(sub)
    if specs_p:
        th_lines.append(specs_p)
    th_lines.append(CTA)
    threads = "\n".join(th_lines)

    # ---- WhatsApp / Telegram broadcast: plain, direct, *bold* title ----
    wa = [f"*{title}*"]
    if price_s:
        wa.append(price_s)
    wa_specs = " · ".join([x for x in (specs_p, extras) if x])
    if wa_specs:
        wa.append(wa_specs)
    if snippet:
        wa.append(description_snippet(listing, max_chars=180))
    wa.append(CTA)
    whatsapp = "\n".join(wa)

    # ---- TikTok / Story kept for back-compat (not a focus platform) ----
    tk = [title]
    if price_s:
        tk.append(price_s + (f" · {specs_p}" if specs_p else ""))
    tk += [f"➡️ {SWIPE_PROMPT}", CTA]
    tiktok = "\n".join(tk)
    story = f"{title}\n{price_s}\n{CTA}" if price_s else f"{title}\n{CTA}"

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
