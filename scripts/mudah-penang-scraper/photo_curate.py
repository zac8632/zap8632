#!/usr/bin/env python3
"""Photo curation: blur/quality scoring + zero-shot room classification, on REAL photos only."""

import sys

import numpy as np
from PIL import Image

MIN_SIDE = 500
BLUR_FLOOR = 60.0

CORE_CATEGORIES = ["exterior/facade", "living room", "kitchen", "bedroom", "bathroom"]
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
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return 0.0
    lap = (-4 * gray[1:-1, 1:-1]
           + gray[:-2, 1:-1] + gray[2:, 1:-1]
           + gray[1:-1, :-2] + gray[1:-1, 2:])
    return float(lap.var())


def photo_score(path):
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

    def take_best(cat):
        for p, s, conf in by_category.get(cat, []):
            if p not in used:
                used.add(p)
                return {"path": p, "category": cat, "sharpness": s["sharpness"],
                        "min_side": s["min_side"], "confidence": conf}
        return None

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
        rest = [(p, s) for p, s in scored.items() if p not in used]
        rest.sort(key=lambda t: t[1]["sharpness"] * t[1]["min_side"], reverse=True)
        for p, s in rest:
            if len(chosen) >= k:
                break
            chosen.append({"path": p, "category": "uncategorised",
                           "sharpness": s["sharpness"], "min_side": s["min_side"],
                           "confidence": 0.0})
            used.add(p)

    def sort_key(c):
        if c["category"] == "exterior/facade":
            return (0,)
        if c["category"] in CORE_CATEGORIES:
            return (1, CORE_CATEGORIES.index(c["category"]))
        return (2,)
    chosen.sort(key=sort_key)
    return chosen[:k]
