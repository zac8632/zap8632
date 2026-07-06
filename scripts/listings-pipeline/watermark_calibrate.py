#!/usr/bin/env python3
"""
Watermark calibration - multi-sample template approach (NOT the abandoned
single-image heuristic). See README/context.md for why the first two attempts
failed: detecting "is this pixel a watermark?" from ONE photo alone confused
real content (sky, mirrors, plain walls) with the overlay, because both look
"bright + low-saturation" in isolation.

This is a different mechanism: mudah stamps the SAME watermark pattern at the
SAME relative position on every photo. Across many DIFFERENT real photos, the
watermark is the one thing that stays constant while the actual scene content
varies. So instead of guessing per-image, we look at variance ACROSS a stack
of unrelated photos: pixels where the value barely changes between photos of
completely different rooms/exteriors are the watermark - genuine content does
not hold still across unrelated images, only a stamped overlay does.

Output is not a "perfect recovery" claim - it's a calibrated mask + estimated
color for wherever the watermark consistently sits, used to SOFTEN it (pull it
toward the local neighbourhood so it reads as much fainter/near-transparent)
rather than attempt exact mathematical inversion. This is deliberately the
more conservative of the two options discussed: lower risk of destroying real
content than a full alpha-recovery, at the cost of not being a 100% clean
removal.

Usage:
    python watermark_calibrate.py --photos-dir <dir of many real sample jpgs> \
        --out watermark_template.npz

Then review the printed mask coverage % and the dumped mask.png preview
BEFORE wiring this into the live render pipeline (post_content.py) - same
"test on real output, look at it, then decide" discipline that caught the
LaMa failure last time.
"""
import argparse
import glob
import os
import sys

import numpy as np
from PIL import Image

CANONICAL_SIZE = (1200, 900)  # (W, H) - photos are resized/cropped to this so
                               # pixel positions line up across the stack.


def _load_canonical(path, size=CANONICAL_SIZE):
    """Center-crop to the target aspect ratio, then resize - so a watermark
    tiled at a fixed relative position lines up across different source photos
    regardless of their native resolution/aspect."""
    img = Image.open(path).convert("RGB")
    tw, th = size
    w, h = img.size
    target_ratio = tw / th
    cur_ratio = w / h
    if cur_ratio > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    return np.asarray(img.resize(size, Image.LANCZOS), dtype=np.float64)


def build_template(photo_paths, size=CANONICAL_SIZE, std_percentile=15):
    """Stack many unrelated real photos and find pixels that stay unusually
    constant across the stack (candidate watermark), vs. pixels that vary a
    lot (real scene content, safe to leave alone).

    Returns (mask, color): mask is a (H, W) bool array of watermark-affected
    pixels, color is the (H, W, 3) per-pixel median - the calibrated estimate
    of what the watermark looks like on top of "average" content there.
    """
    if len(photo_paths) < 8:
        raise ValueError(
            "Need at least ~8-10 photos of genuinely different scenes to "
            "calibrate reliably - too few and low variance could just mean "
            "'these photos happen to be similar', not 'this is the watermark'."
        )
    stack = np.stack([_load_canonical(p, size) for p in photo_paths])  # (N,H,W,3)
    med = np.median(stack, axis=0)
    std = np.std(stack, axis=0).mean(axis=-1)  # (H,W) - collapse RGB to one std map

    threshold = np.percentile(std, std_percentile)
    mask = std <= threshold
    return mask, med


def save_template(mask, color, out_path):
    np.savez_compressed(out_path, mask=mask, color=color)


def load_template(path):
    data = np.load(path)
    return data["mask"], data["color"]


def suppress_watermark(img_path, mask, color, strength=0.6, out_path=None):
    """Soften (not perfectly remove) the calibrated watermark region: blend
    each masked pixel toward its local neighbourhood average, proportional to
    `strength`. Never touches pixels outside the calibrated mask, so it can't
    repeat the old failure mode of eating real sky/mirror/wall content."""
    img = Image.open(img_path).convert("RGB")
    orig_size = img.size
    small = img.resize((mask.shape[1], mask.shape[0]), Image.LANCZOS)
    arr = np.asarray(small, dtype=np.float64)

    # Local neighbourhood average via a cheap box blur, used as the "what
    # would this area look like without a stamped overlay" target.
    from scipy.ndimage import uniform_filter  # optional dep; see requirements
    local_avg = np.stack(
        [uniform_filter(arr[..., c], size=41) for c in range(3)], axis=-1
    )

    out = arr.copy()
    m = mask[..., None]
    out = np.where(m, arr * (1 - strength) + local_avg * strength, arr)
    result = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).resize(
        orig_size, Image.LANCZOS
    )
    if out_path:
        result.save(out_path)
    return result


def _self_test():
    """Synthetic proof the calibration math actually isolates a constant
    overlay before trusting it on real mudah photos - same discipline as the
    original alpha-deblend math, which also checked out in isolation but
    failed once the DETECTION step was asked to generalize. Here detection is
    multi-sample variance, not single-image heuristics, so re-verify it here."""
    rng = np.random.default_rng(0)
    h, w = 90, 120
    n = 20
    watermark_region = np.zeros((h, w), dtype=bool)
    watermark_region[30:60, 40:90] = True
    wm_color = np.array([230.0, 230.0, 230.0])
    alpha = 0.45

    stack = []
    for _ in range(n):
        content = rng.integers(0, 255, size=(h, w, 3)).astype(np.float64)
        visible = content.copy()
        visible[watermark_region] = (
            alpha * wm_color + (1 - alpha) * content[watermark_region]
        )
        stack.append(visible)
    stack = np.stack(stack)

    med = np.median(stack, axis=0)
    std = np.std(stack, axis=0).mean(axis=-1)
    threshold = np.percentile(std, 15)
    detected = std <= threshold

    overlap = (detected & watermark_region).sum() / watermark_region.sum()
    false_positive_rate = (detected & ~watermark_region).sum() / (~watermark_region).sum()
    print(f"self-test: watermark region recovered = {overlap:.0%}, "
          f"false-positive rate on real content = {false_positive_rate:.1%}")
    assert overlap > 0.7, "calibration failed to find the synthetic watermark"
    assert false_positive_rate < 0.1, "calibration is flagging real content too broadly"
    print("self-test PASSED - math isolates a constant multi-sample overlay correctly.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--photos-dir", help="Directory of real sample photos to calibrate from")
    ap.add_argument("--out", default="watermark_template.npz")
    ap.add_argument("--self-test", action="store_true",
                     help="Run the synthetic proof only, no real photos needed")
    args = ap.parse_args()

    if args.self_test or not args.photos_dir:
        _self_test()
        if not args.photos_dir:
            sys.exit(0)

    paths = sorted(
        glob.glob(os.path.join(args.photos_dir, "**", "*.jpg"), recursive=True)
        + glob.glob(os.path.join(args.photos_dir, "**", "*.jpeg"), recursive=True)
        + glob.glob(os.path.join(args.photos_dir, "**", "*.png"), recursive=True)
    )
    print(f"Calibrating from {len(paths)} photos...")
    mask, color = build_template(paths)
    save_template(mask, color, args.out)
    coverage = mask.mean()
    print(f"Saved {args.out} - watermark mask covers {coverage:.1%} of frame.")
    if coverage > 0.35:
        print("WARNING: mask covers a very large share of the frame - this "
              "smells like the old false-positive failure mode (flagging real "
              "content, not just the watermark). Inspect before trusting.",
              file=sys.stderr)
