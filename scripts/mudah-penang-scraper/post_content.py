#!/usr/bin/env python3
"""
Stage 2 content builder for the penang-listing-posts skill.

Two jobs, both deterministic (no LLM, no API key, no hallucination — every word
comes from the listing's own fields/text):

  build_captions(listing)  -> per-platform captions (raw, native, no hashtags,
                              soft CTA, no contact info).
  render_creatives(...)     -> RAW NATIVE images: smart-crop each real photo to
                              4:5 and 9:16, optionally composite ONE minimal
                              price/area tag on the first photo. No posters.

Run standalone to preview captions against the scrape without any photos:
    python post_content.py --input penang_owners.xlsx --demo 5
"""

import argparse
import os
import re
import sys

# Approx FX (mirror context.md; refresh periodically).
FX = {"usd": 0.213, "sgd": 0.287}


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
    """('RM 1,830,000', '≈ USD 390k / SGD 525k approx.') or (None, None)."""
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


def hook_from(listing):
    """Use the owner's own words: the Title, tidied. Never invented."""
    title = _clean(listing.get("Title")) or ""
    area = _clean(listing.get("Location")) or ""
    # Titles often end with ", <Area>" — drop the redundant tail for the hook.
    if area and title.lower().rstrip(".").endswith(area.lower()):
        title = title[: title.lower().rfind(area.lower())].strip().strip(",")
    return title or area


def facts_line(listing):
    bits = []
    area = _clean(listing.get("Location"))
    if area:
        bits.append(area)
    bd = _clean(listing.get("Bedrooms"))
    ba = _clean(listing.get("Bathrooms"))
    if bd:
        bits.append(f"{bd} bed")
    if ba:
        bits.append(f"{ba} bath")
    sz = _clean(listing.get("Size (sqft)"))
    if sz:
        bits.append(f"{sz} sqft")
    tn = _clean(listing.get("Tenure"))
    if tn:
        bits.append(tn)
    return " · ".join(bits)


CTA = "DM to arrange a viewing"


def build_captions(listing):
    """Return {platform: caption}. Raw/native tone, facts only, no hashtags,
    no contact info. Blank fields are simply omitted."""
    hook = hook_from(listing)
    facts = facts_line(listing)
    myr_s, approx = price_lines(price_num(listing.get("Price (RM)")))
    price_block = myr_s + (f"\n{approx}" if approx else "") if myr_s else ""

    # Instagram feed — a few lines, front-loaded, minimal emoji.
    ig = []
    if hook:
        ig.append(hook)
    if facts:
        ig.append(f"📍 {facts}")
    if price_block:
        ig.append(f"💰 {price_block}")
    ig.append(f"💬 {CTA}")
    instagram = "\n".join(ig)

    # Threads — conversational, no emoji.
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

    # TikTok — punchy, short.
    tk = []
    if hook:
        tk.append(hook)
    if myr_s:
        tk.append(myr_s + (f" · {facts}" if facts else ""))
    tk.append(CTA)
    tiktok = "\n".join(tk)

    # Instagram Story — minimal (creative already shows price).
    story = f"{hook}\n{CTA}" if hook else CTA

    # WhatsApp status — one glance.
    wa_bits = [b for b in [_clean(listing.get("Location")), myr_s] if b]
    whatsapp = " · ".join(wa_bits) + f"\n{CTA}" if wa_bits else CTA

    return {
        "instagram": instagram,
        "threads": threads,
        "tiktok": tiktok,
        "story": story,
        "whatsapp": whatsapp,
    }


# ---- RAW NATIVE creatives (Pillow) — runs in the Action where photos exist ----

def _smart_crop(img, ratio_w, ratio_h):
    from PIL import Image
    w, h = img.size
    target = ratio_w / ratio_h
    cur = w / h
    if cur > target:               # too wide -> crop sides
        new_w = int(h * target)
        left = (w - new_w) // 2
        return img.crop((left, 0, left + new_w, h))
    else:                          # too tall -> crop top/bottom (bias slightly up)
        new_h = int(w / target)
        top = int((h - new_h) * 0.4)
        return img.crop((0, top, w, top + new_h))


def render_creatives(photo_paths, listing, out_dir, tag=True):
    """Crop the real photos to 4:5 and 9:16. On the FIRST photo optionally
    composite one minimal price/area tag (bottom-left). No posters. Returns
    {'4x5': [...], '9x16': [...]}."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow not installed (pip install pillow) — skipping render.", file=sys.stderr)
        return {"4x5": [], "9x16": []}

    os.makedirs(out_dir, exist_ok=True)
    myr_s, _ = price_lines(price_num(listing.get("Price (RM)")))
    area = _clean(listing.get("Location"))
    out = {"4x5": [], "9x16": []}
    specs = {"4x5": (1080, 1350, 4, 5), "9x16": (1080, 1920, 9, 16)}

    def load_font(size):
        for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                  "/Library/Fonts/Arial Bold.ttf"):
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
        return ImageFont.load_default()

    for key, (W, H, rw, rh) in specs.items():
        for i, ph in enumerate(photo_paths):
            try:
                img = Image.open(ph).convert("RGB")
            except Exception as e:
                print(f"  [render] skip {ph}: {e}", file=sys.stderr)
                continue
            crop = _smart_crop(img, rw, rh).resize((W, H), Image.LANCZOS)
            if tag and i == 0 and myr_s:
                draw = ImageDraw.Draw(crop, "RGBA")
                fs = int(H * 0.045)
                font = load_font(fs)
                pad = int(W * 0.04)
                lines = [myr_s] + ([area] if area else [])
                # low-opacity strip behind just the text, not the whole image
                tw = max(draw.textlength(l, font=load_font(fs if j == 0 else int(fs*0.6)))
                         for j, l in enumerate(lines))
                bh = int(fs * (1.5 * len(lines) + 0.6))
                draw.rectangle([0, H - bh - pad, tw + pad*2, H], fill=(10, 37, 64, 150))
                y = H - bh - pad + int(fs*0.3)
                draw.text((pad, y), myr_s, font=font, fill=(255, 255, 255, 255))
                if area:
                    draw.text((pad, y + int(fs*1.4)), area,
                              font=load_font(int(fs*0.6)), fill=(230, 236, 243, 255))
            fn = os.path.join(out_dir, f"{key}_{i+1:02d}.jpg")
            crop.save(fn, quality=90)
            out[key].append(fn)
    return out


def main():
    import pandas as pd
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default="penang_owners.xlsx")
    ap.add_argument("--demo", type=int, default=5, help="Preview captions for N qualifying listings.")
    args = ap.parse_args()

    from build_listing_posts import qualifies  # reuse the Stage 1 filter
    df = pd.read_excel(args.input, sheet_name="All Listings", dtype=str)
    q = df[df.apply(qualifies, axis=1)]
    print(f"{len(q)} qualifying; showing captions for {min(args.demo, len(q))}:\n", file=sys.stderr)
    for _, row in q.head(args.demo).iterrows():
        caps = build_captions(row)
        print("=" * 66)
        print(f"{row.get('Title')}  |  {row.get('Price')}")
        print("-" * 66)
        print("[Instagram]\n" + caps["instagram"])
        print("\n[Threads] " + caps["threads"])
        print("\n[WhatsApp] " + caps["whatsapp"].replace("\n", " / "))
        print()


if __name__ == "__main__":
    main()
