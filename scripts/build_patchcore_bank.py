"""
Builds the PatchCore anomaly-detection memory bank from clean (target-free)
synthetic side-scan-sonar seabed patches.

Previously the system shipped with NO memory bank at all, so anomaly scoring
always fell back to a crude hand-tuned statistical heuristic (Known
Limitation #2 in the README). This script generates a bank of "normal
seabed" feature vectors so PatchCore's actual neural anomaly scoring path
is exercised at inference time.
"""
from pathlib import Path
import random
import sys

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.services.synthetic_sonar import generate_synthetic_sonar_image
from backend.app.services.anomaly import AnomalyDetector


def generate_normal_patches(num_images: int = 60, patch_size: int = 96, patches_per_image: int = 8,
                             img_size: int = 416, seed: int = 777) -> list[np.ndarray]:
    """
    Renders target-free synthetic sonar scans (passing targets=[] skips
    target/shadow placement) and crops random seabed patches out of them.
    """
    random.seed(seed)
    np.random.seed(seed)

    patches = []
    for i in range(num_images):
        img, _ = generate_synthetic_sonar_image(width=img_size, height=img_size, targets=[])
        h, w = img.shape[:2]
        for _ in range(patches_per_image):
            x = random.randint(0, max(0, w - patch_size))
            y = random.randint(0, max(0, h - patch_size))
            patch = img[y:y + patch_size, x:x + patch_size]
            if patch.shape[0] == patch_size and patch.shape[1] == patch_size:
                patches.append(patch)

    return patches


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build the PatchCore normal-seabed memory bank")
    parser.add_argument("--images", type=int, default=60, help="Number of clean seabed scans to render")
    parser.add_argument("--patches-per-image", type=int, default=8)
    parser.add_argument("--patch-size", type=int, default=96)
    parser.add_argument("--coreset-size", type=int, default=500)
    args = parser.parse_args()

    print(f"Rendering {args.images} target-free seabed scans "
          f"({args.patches_per_image} patches each)...")
    patches = generate_normal_patches(
        num_images=args.images,
        patch_size=args.patch_size,
        patches_per_image=args.patches_per_image,
    )
    print(f"Collected {len(patches)} normal seabed patches.")

    detector = AnomalyDetector()
    detector.build_memory_bank(patches, coreset_size=args.coreset_size)

    if detector.memory_bank is not None:
        print(f"Memory bank built: {detector.memory_bank.shape[0]} entries, "
              f"{detector.memory_bank.shape[1]}-dim features.")
        print(f"Calibrated distance scale (95th percentile normal NN distance): "
              f"{detector.distance_scale:.4f}")
    else:
        print("WARNING: memory bank could not be built (torch/torchvision unavailable).")
