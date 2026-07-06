#!/usr/bin/env python3
"""
Photo curation for the penang-listing-posts pipeline.

Jobs, all operating on REAL photos only (organizing/restoring what exists,
never inventing content - stays within the no-hallucination rule):

  photo_score(path)                 -> blur (Laplacian variance) + resolution
  classify_rooms(paths)             -> zero-shot room-type labels (CLIP)
  select_representative_photos(...) -> up to k photos: best-quality pick per
                                       room category, covering both condo units
                                       and landed homes (extra categories for
                                       dining room, garden, car porch, etc.)
  remove_watermark(path)            -> Tier 2 (rules-and-constraints.md):
                                       un-blends mudah's semi-transparent
                                       watermark by inverting its alpha blend,
                                       recovering real pixels rather than
                                       generating replacement content. Always
                                       flags ai_enhanced=true for review.
"""

import sys

import numpy as np
from PIL import Image

MIN_SIDE = 500       # px; below this a photo is heavily penalised
BLUR_FLOOR = 60.0    # Laplacian-variance below this reads as blurry

# Core five - present for basically any residential listing (condo or landed).
CORE_CATEGORIES = ["exterior/facade", "living room", "kitchen", "bedroom", "bathroom"]

# Landed homes often have MORE distinct spaces than a condo unit - these fill
# extra slots (or replace a missing core category) instead of duplicating
# e.g. two bedroom shots when a dining room or garden photo is available.
EXTRA_CATEGORIES = [
    "dining room", "garden or compound", "car porch or garage",
    "balcony or patio", "staircase or hallway",
]

ALL_LABELS = CORE_CATEGORIES + EXTRA_CATEGORIES

_LABEL_PROMPTS = {
    "exterior/facade": "the exterior facade of a house or building",
    "living room": "a living room interior",
    "kitchen": "a kitchen interior",
    "bedroom": "a bedroom interior",
    "bathroom": "a bathroom interior",
    "dining room": "a dining room interior",
    "garden or compound": "a garden or outdoor compound of a house",
    "car porch or garage": "a car porch or garage",
    "balcony or patio": "a balcony or patio",
    "staircase or hallway": "a staircase or hallway",
}


def laplacian_variance(gray):
    """Blur detection via discrete Laplacian variance - pure numpy, no cv2.
    Sharp images have high edge variance; blurry ones read low."""
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return 0.0
    lap = (-4 * gray[1:-1, 1:-1]
           + gray[:-2, 1:-1] + gray[2:, 1:-1]
           + gray[1:-1, :-2] + gray[1:-1, 2:])
    return float(lap.var())


def photo_score(path):
    """{'sharpness', 'width', 'height', 'min_side', 'quality_ok'}."""
    try:
        img = Image.open(path).convert("L")
    except Exception:
        return {"sharpness": 0.0, "width": 0, "height": 0, "min_side": 0, "quality_ok": False}
    w, h = img.size
    work = img.copy()
    work.thumbnail((600, 600))
    arr = np.asarray(work, dtype=np.float64)
    sharpness = laplacian_variance(arr)
    min_side = min(w, h)
    return {
        "sharpness": sharpness, "width": w, "height": h, "min_side": min_side,
        "quality_ok": (min_side >= MIN_SIDE) and (sharpness >= BLUR_FLOOR),
    }


_clf_cache = {}


def classify_rooms(photo_paths):
    """{path: (label, confidence)} via zero-shot CLIP classification. Lazy
    imports torch/transformers so callers that don't need this (caption demo,
    --filter-only) never pay the dependency cost."""
    if not photo_paths:
        return {}
    try:
        from transformers import pipeline
    except ImportError:
        print("  [curate] transformers not installed - skipping room classification", file=sys.stderr)
        return {}

    if "clf" not in _clf_cache:
        _clf_cache["clf"] = pipeline(
            "zero-shot-image-classification", model="openai/clip-vit-base-patch32")
    clf = _clf_cache["clf"]

    prompts = [_LABEL_PROMPTS[c] for c in ALL_LABELS]
    prompt_to_label = {v: k for k, v in _LABEL_PROMPTS.items()}
    out = {}
    for p in photo_paths:
        try:
            img = Image.open(p).convert("RGB")
            result = clf(img, candidate_labels=prompts)
            top = result[0]
            out[p] = (prompt_to_label[top["label"]], float(top["score"]))
        except Exception as e:
            print(f"  [curate] classify failed for {p}: {e}", file=sys.stderr)
    return out


def select_representative_photos(photo_paths, k=5):
    """Pick up to k photos: best-quality per core category, then landed-home
    extras to fill gaps, then pure quality ranking for any leftover slots.
    Returns [{'path','category','sharpness','min_side','confidence'}, ...],
    exterior first if present."""
    scored = {p: photo_score(p) for p in photo_paths}
    labels = classify_rooms(list(scored.keys()))

    by_category = {}
    for p, s in scored.items():
        if p in labels:
            label, conf = labels[p]
            by_category.setdefault(label, []).append((p, s, conf))

    for cat, items in by_category.items():
        items.sort(key=lambda t: (t[1]["quality_ok"], t[1]["sharpness"] * t[1]["min_side"]),
                   reverse=True)

    chosen, used = [], set()

    def take_best(cat, require_quality_ok=True):
        for p, s, conf in by_category.get(cat, []):
            if p in used:
                continue
            if require_quality_ok and not s["quality_ok"]:
                continue
            used.add(p)
            return {"path": p, "category": cat, "sharpness": s["sharpness"],
                    "min_side": s["min_side"], "confidence": conf}
        return None

    # Quality-gated: only ever take a photo that actually clears the bar. If a
    # listing only has one genuinely good photo, ship one - never pad the set
    # with a blurry/low-res photo just to hit a target count.
    for cat in CORE_CATEGORIES:
        picked = take_best(cat)
        if picked:
            chosen.append(picked)

    if len(chosen) < k:
        for cat in EXTRA_CATEGORIES:
            if len(chosen) >= k:
                break
            picked = take_best(cat)
            if picked:
                chosen.append(picked)

    if len(chosen) < k:
        rest = [(p, s) for p, s in scored.items() if p not in used and s["quality_ok"]]
        rest.sort(key=lambda t: t[1]["sharpness"] * t[1]["min_side"], reverse=True)
        for p, s in rest:
            if len(chosen) >= k:
                break
            chosen.append({"path": p, "category": "uncategorised",
                           "sharpness": s["sharpness"], "min_side": s["min_side"],
                           "confidence": 0.0})
            used.add(p)

    # Last resort only: if literally nothing cleared the quality bar, ship the
    # single best available rather than posting nothing.
    if not chosen and scored:
        best_p = max(scored, key=lambda p: scored[p]["sharpness"] * scored[p]["min_side"])
        s = scored[best_p]
        chosen.append({"path": best_p, "category": "uncategorised",
                       "sharpness": s["sharpness"], "min_side": s["min_side"], "confidence": 0.0})

    def sort_key(c):
        if c["category"] == "exterior/facade":
            return (0,)
        if c["category"] in CORE_CATEGORIES:
            return (1, CORE_CATEGORIES.index(c["category"]))
        return (2,)
    chosen.sort(key=sort_key)
    return chosen[:k]


# Approximate region + blend params for mudah's watermark, from visual
# inspection of real sample photos. box is (x1,y1,x2,y2) as fractions of
# width/height; alpha/color are the platform's translucent-overlay blend.
# These are estimates, not exact calibration - tune here if output looks off.
WATERMARK_BOX = (0.03, 0.38, 0.97, 0.85)
WATERMARK_ALPHA = 0.22
WATERMARK_RGB = (235, 235, 235)
_FEATHER_FRAC = 0.06  # soften the mask edge so there's no visible seam


def _feather_mask(h, w, box, feather_frac):
    x1, y1, x2, y2 = int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)
    mask = np.zeros((h, w), dtype=np.float64)
    mask[y1:y2, x1:x2] = 1.0
    fx = max(1, int((x2 - x1) * feather_frac))
    fy = max(1, int((y2 - y1) * feather_frac))
    # simple separable box-blur feather (no scipy dependency)
    for _ in range(3):
        mask = _box_blur_1d(mask, fx, axis=1)
        mask = _box_blur_1d(mask, fy, axis=0)
    return np.clip(mask, 0.0, 1.0)


def _box_blur_1d(arr, radius, axis):
    if radius < 1:
        return arr
    kernel = np.ones(radius * 2 + 1) / (radius * 2 + 1)
    return np.apply_along_axis(lambda m: np.convolve(m, kernel, mode="same"), axis, arr)


def remove_watermark(path, out_path=None, box=WATERMARK_BOX,
                      alpha=WATERMARK_ALPHA, watermark_rgb=WATERMARK_RGB):
    """FALLBACK ONLY - superseded by inpaint_watermark() below. Un-blends a
    single fixed-box translucent overlay; doesn't handle mudah's actual
    repeating diagonal tiled watermark, which covers the whole frame. Kept for
    the case where the LaMa inpainting dependency isn't installed."""
    try:
        img = Image.open(path).convert("RGB")
    except Exception:
        return False
    w, h = img.size
    arr = np.asarray(img, dtype=np.float64)
    mask = _feather_mask(h, w, box, _FEATHER_FRAC)[:, :, None]
    W = np.array(watermark_rgb, dtype=np.float64)
    restored = np.clip((arr - alpha * W) / (1 - alpha), 0, 255)
    out_arr = arr * (1 - mask) + restored * mask
    Image.fromarray(out_arr.astype(np.uint8), "RGB").save(out_path or path, quality=95)
    return True


# ---- Whole-image tiled-watermark removal (detect + LaMa inpaint) ----------
#
# mudah's watermark is a repeating diagonal tiled overlay across the ENTIRE
# frame, not one fixed spot - the box/alpha de-blend above only ever touched
# one region. This detects the (semi-transparent, low-saturation, locally-
# brighter-than-surroundings) overlay pixels across the whole photo and
# inpaints just those with LaMa - Tier 2: restoring the real photo behind a
# platform-injected overlay, not generating new scene content. A dilated,
# thin mask (not a solid block) keeps inpainting minimally destructive.

_lama_cache = {}


def detect_watermark_mask(img_rgb, brightness_thresh=10.0, sat_thresh=0.18, blur_radius=15):
    """Heuristic mask: pixels noticeably brighter than their local surroundings
    (a blurred version of the image) AND low-saturation (grayish/white) - the
    signature of a light semi-transparent overlay. Returns a uint8 0/255 mask,
    same H×W as img_rgb. This is a heuristic, not exact detection - expect to
    tune the thresholds against real output."""
    from PIL import ImageFilter

    img = Image.fromarray(img_rgb, "RGB")
    gray = np.asarray(img.convert("L"), dtype=np.float64)
    blurred = np.asarray(img.convert("L").filter(ImageFilter.GaussianBlur(blur_radius)),
                          dtype=np.float64)
    residual = gray - blurred

    r = img_rgb[:, :, 0].astype(np.float64)
    g = img_rgb[:, :, 1].astype(np.float64)
    b = img_rgb[:, :, 2].astype(np.float64)
    maxc = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    sat = np.where(maxc > 0, (maxc - minc) / np.maximum(maxc, 1.0), 0.0)

    mask = (residual > brightness_thresh) & (sat < sat_thresh)
    mask_img = Image.fromarray((mask * 255).astype(np.uint8), "L")
    # dilate slightly so thin watermark strokes are fully covered, then a touch
    # of blur so the inpainted patch blends without a hard-edged seam
    mask_img = mask_img.filter(ImageFilter.MaxFilter(5))
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(2))
    return np.asarray(mask_img)


def inpaint_watermark(path, out_path=None):
    """Detect + inpaint mudah's tiled watermark across the whole photo using
    LaMa (via simple-lama-inpainting). Falls back to remove_watermark() (the
    single-box de-blend) if the dependency isn't installed. Returns True if
    any processing was applied."""
    try:
        img = Image.open(path).convert("RGB")
    except Exception:
        return False

    try:
        from simple_lama_inpainting import SimpleLama
    except ImportError:
        print("  [curate] simple-lama-inpainting not installed - falling back "
              "to box de-blend", file=sys.stderr)
        return remove_watermark(path, out_path)

    if "lama" not in _lama_cache:
        _lama_cache["lama"] = SimpleLama()
    lama = _lama_cache["lama"]

    img_rgb = np.asarray(img)
    mask_arr = detect_watermark_mask(img_rgb)
    if mask_arr.max() == 0:
        # nothing detected - save through unchanged rather than skip, so the
        # rest of the pipeline always finds a file at out_path
        img.save(out_path or path, quality=95)
        return True

    mask_img = Image.fromarray(mask_arr, "L")
    result = lama(img, mask_img)
    result.save(out_path or path, quality=95)
    return True
