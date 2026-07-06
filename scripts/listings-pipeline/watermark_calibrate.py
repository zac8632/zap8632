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

    Returns (mask, color, confidence):
    - mask: (H, W) bool array of watermark-affected pixels.
    - color: (H, W, 3) per-pixel median - the calibrated estimate of what
      the watermark looks like on top of "average" content there.
    - confidence: (H, W) float in [0, 1], zero outside the mask and rising
      toward 1 the lower a pixel's cross-stack std is relative to the mask
      threshold. Pixels dead-center of the logo/text (near-zero variance
      across totally different photos) get high confidence; pixels near the
      mask's ragged edge (borderline variance) get low confidence. Used to
      taper the blend at the edges instead of a hard on/off cut, which is
      what makes a flat patch visible as a patch.
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
    confidence = np.clip(1.0 - std / (threshold + 1e-6), 0.0, 1.0)
    confidence = np.where(mask, confidence, 0.0)
    return mask, med, confidence


def save_template(mask, color, confidence, out_path):
    np.savez_compressed(out_path, mask=mask, color=color, confidence=confidence)


def load_template(path):
    data = np.load(path)
    return data["mask"], data["color"], data["confidence"]


def suppress_watermark(img_path, mask, color, confidence, strength=0.6,
                        out_path=None, target_mode="local", feather_sigma=15):
    """Soften (not perfectly remove) the calibrated watermark region.

    Two things changed from the original hard-mask/local-blur-only version,
    both aimed at the "still see the word mudah" feedback on real photos:

    1. `target_mode` picks what the masked pixels get blended toward:
       - "local": the old behaviour - a box-blur of THIS photo's own
         neighbourhood. Matches local lighting/color perfectly but a live
         blur still carries some bleed-through from the sharp logo/text
         edges it's blurring, so faint lettering can survive.
       - "calibrated": blend toward `color`, the per-pixel median computed
         across many real photos during calibration. This is a cleaner
         "what's actually here without the stamp" estimate since it's
         built from genuine content elsewhere, not a blur of the same
         contaminated pixels - but it can mismatch this specific photo's
         lighting/color cast since it's a fixed value.
       - "hybrid": average of the two, trading off both risks.
       - "inpaint_telea" / "inpaint_ns": a different mechanism altogether -
         OpenCV's inpainting (Telea or Navier-Stokes algorithm) propagates
         structure/texture inward from the mask boundary instead of
         blending toward one flat/blurred estimate, so it can follow real
         edges and grain instead of reading as a patch.
    2. The blend strength is no longer uniform across the whole mask -
       it's scaled per-pixel by `confidence` (how sure calibration was that
       this exact pixel is watermark, not content) and that confidence map
       is Gaussian-feathered so the transition softens gradually at the
       mask's ragged edge instead of stopping dead. That's what keeps the
       blended region reading as part of the photo rather than a pasted
       patch - a hard binary mask is what made past attempts look like an
       obvious rectangle/blob even when the color matched.
    """
    img = Image.open(img_path).convert("RGB")
    orig_size = img.size
    small = img.resize((mask.shape[1], mask.shape[0]), Image.LANCZOS)
    arr = np.asarray(small, dtype=np.float64)

    from scipy.ndimage import gaussian_filter, uniform_filter  # optional dep; see requirements

    local_avg = np.stack(
        [uniform_filter(arr[..., c], size=41) for c in range(3)], axis=-1
    )
    if target_mode == "local":
        target = local_avg
    elif target_mode == "calibrated":
        target = color
    elif target_mode == "hybrid":
        target = 0.5 * local_avg + 0.5 * color
    elif target_mode in ("inpaint_telea", "inpaint_ns"):
        # Different mechanism entirely: instead of blending toward any single
        # flat/blurred estimate, let OpenCV's inpainting algorithm synthesize
        # texture by propagating structure inward from the mask's boundary -
        # this can follow real edges/gradients (wall lines, floor grain)
        # instead of leaving a flat-looking patch, which is what both the
        # local-blur and calibrated-color blends risk on textured surfaces.
        import cv2
        flag = cv2.INPAINT_TELEA if target_mode == "inpaint_telea" else cv2.INPAINT_NS
        bgr = cv2.cvtColor(np.clip(arr, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
        inpaint_mask = (mask.astype(np.uint8)) * 255
        inpainted_bgr = cv2.inpaint(bgr, inpaint_mask, 7, flag)
        target = cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2RGB).astype(np.float64)
    else:
        raise ValueError(f"unknown target_mode: {target_mode!r}")

    soft_mask = gaussian_filter(confidence, sigma=feather_sigma)
    blend = (strength * soft_mask)[..., None]
    out = arr * (1 - blend) + target * blend
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
    ap.add_argument("--std-percentile", type=float, default=25,
                     help="Higher = wider mask (more of the frame counted as watermark). "
                          "Bumped from the original 15 - the user confirmed the real mudah "
                          "watermark sits centered and spans much of the frame, wider than "
                          "the first real test's mask captured.")
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
    mask, color, confidence = build_template(paths, std_percentile=args.std_percentile)
    save_template(mask, color, confidence, args.out)
    coverage = mask.mean()
    print(f"Saved {args.out} - watermark mask covers {coverage:.1%} of frame.")
    if coverage > 0.35:
        print("WARNING: mask covers a very large share of the frame - this "
              "smells like the old false-positive failure mode (flagging real "
              "content, not just the watermark). Inspect before trusting.",
              file=sys.stderr)
