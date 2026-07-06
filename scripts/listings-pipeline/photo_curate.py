#!/usr/bin/env python3
"""
Photo curation for the listing-content-studio pipeline.

Jobs, all operating on REAL photos only (organizing/restoring what exists,
never inventing content - stays within the no-hallucination rule):

  photo_score(path)                 -> blur (Laplacian variance) + resolution
  classify_rooms(paths)             -> zero-shot room-type labels (CLIP)
  select_representative_photos(...) -> up to k photos: best-quality pick per
                                       room category, covering both condo units
                                       and landed homes (extra categories for
                                       dining room, garden, car porch, etc.)

Watermark removal was attempted (single-box de-blend, then whole-image
heuristic + LaMa inpaint) and removed - see git history / project notes.
Both were too unreliable on real photos (LaMa in particular destroyed sky/
mirror/wall content). Photos ship as originally downloaded.
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
# "scenic view" listed first since it's a real marketing asset for coastal/
# hillside listings (sea view, hill view) - promote to CORE_CATEGORIES if it
# should be guaranteed on every post rather than a fallback fill.
EXTRA_CATEGORIES = [
    "scenic view", "dining room", "garden or compound", "car porch or garage",
    "balcony or patio", "staircase or hallway",
]

ALL_LABELS = CORE_CATEGORIES + EXTRA_CATEGORIES

_LABEL_PROMPTS = {
    "exterior/facade": "the exterior facade of a house or building",
    "living room": "a living room interior",
    "kitchen": "a kitchen interior",
    "bedroom": "a bedroom interior",
    "bathroom": "a bathroom interior",
    "scenic view": "a scenic sea view or hill view seen through a window or from a balcony",
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

