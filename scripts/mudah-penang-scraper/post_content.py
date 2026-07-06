#!/usr/bin/env python3
"""
Stage 2 content builder for the penang-listing-posts skill.

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


def build_captions(listing):
    hook = project_name(listing)
    facts = facts_line(listing)
    myr_s, approx = price_lines(price_num(listing.get("Price (RM)")))
    price_block = myr_s + (f"\n{approx}" if approx else "") if myr_s else ""

    ig = []
    if hook:
        ig.append(hook)
    if facts:
        ig.append(f"📍 {facts}")
    if price_block:
        ig.append(f"💰 {price_block}")
    ig.append(f"💬 {CTA}")
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
    tk.append(CTA)
    tiktok = "\n".join(tk)

    story = f"{hook}\n{CTA}" if hook else CTA

    wa_bits = [b for b in [_clean(listing.get("Location")), myr_s] if b]
    whatsapp = " · ".join(wa_bits) + f"\n{CTA}" if wa_bits else CTA

    return {"instagram": instagram, "threads": threads, "tiktok": tiktok,
            "story": story, "whatsapp": whatsapp}


# ------------------------------ creatives ------------------------------

def _smart_crop(img, rw, rh):
    w, h = img.size
    target = rw / rh
    cur = w / h
    if cur > target:
        nw = int(h * target)
        left = (w - nw) // 2
        return img.crop((left, 0, left + nw, h))
    nh = int(w / target)
    top = int((h - nh) * 0.4)
    return img.crop((0, top, w, top + nh))


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
    sizes = {"4x5": (1080, 1350, 4, 5, 70), "9x16": (1080, 1920, 9, 16, 330)}

    for key, (W, H, rw, rh, bottom_ui) in sizes.items():
        for i, ph in enumerate(photo_paths):
            try:
                img = Image.open(ph).convert("RGB")
            except Exception as e:
                print(f"  [render] skip {ph}: {e}", file=sys.stderr)
                continue
            base = _smart_crop(img, rw, rh).resize((W, H), Image.LANCZOS)

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
