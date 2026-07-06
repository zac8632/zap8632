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
    hook = headline(listing)
    facts = facts_line(listing)
    myr_s, approx = price_lines(price_num(listing.get("Price (RM)")))
    price_block = myr_s + (f"\n{approx}" if approx else "") if myr_s else ""

    # Instagram: front-loaded hook, then facts/price, a swipe cue (this is a
    # carousel), CTA, and a save prompt - the last two are pure engagement
    # nudges (not factual claims), both fine under the no-hashtag/no-contact
    # rule since neither is a link, number, or handle.
    ig = []
    if hook:
        ig.append(hook)
    if facts:
        ig.append(f"📍 {facts}")
    if price_block:
        ig.append(f"💰 {price_block}")
    ig.append(f"➡️ {SWIPE_PROMPT}")
    ig.append(f"💬 {CTA}")
    ig.append(f"📌 {SAVE_PROMPT}")
    instagram = "\n".join(ig)

    th = []
    if hook:
        th.append(hook + ".")
    line2 = facts
    if myr_s:
        line2 = (facts + " — " if facts else "") + myr_s
    if line2:
        th.append(line2 + ".")
    th.append(f"{CTA}.")
    threads = " ".join(th)

    tk = []
    if hook:
        tk.append(hook)
    if myr_s:
        tk.append(myr_s + (f" · {facts}" if facts else ""))
    tk.append(f"➡️ {SWIPE_PROMPT}")
    tk.append(CTA)
    tiktok = "\n".join(tk)

    story = f"{hook}\n{CTA}" if hook else CTA

    wa_bits = [b for b in [_clean(listing.get("Location")), myr_s] if b]
    whatsapp = " · ".join(wa_bits) + f"\n{CTA}" if wa_bits else CTA

    return {"instagram": instagram, "threads": threads, "tiktok": tiktok,
            "story": story, "whatsapp": whatsapp}


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
    myr_s, _ = price_lines(price_num(listing.get("Price (RM)")))
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
