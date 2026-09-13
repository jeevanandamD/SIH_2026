from pathlib import Path
import random
import cv2
import numpy as np
import yaml
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.app.services.synthetic_sonar import generate_synthetic_sonar_image

CLASSES = ["fishing_gear", "container", "wreckage", "artificial_object"]


def _write_split(count: int, images_dir: Path, det_labels_dir: Path, seg_labels_dir: Path,
                  prefix: str, img_size: int, jpeg_quality: int, seed_offset: int = 0):
    for i in range(count):
        random.seed(seed_offset + i)
        np.random.seed(seed_offset + i)

        img, dets = generate_synthetic_sonar_image(width=img_size, height=img_size)
        img_name = f"{prefix}_{i+1:04d}.jpg"
        cv2.imwrite(str(images_dir / img_name), img, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])

        h, w = img.shape[:2]

        det_lines = []
        seg_lines = []
        for d in dets:
            bx = d["target_bbox"]
            cx = ((bx["x1"] + bx["x2"]) / 2.0) / w
            cy = ((bx["y1"] + bx["y2"]) / 2.0) / h
            bw = (bx["x2"] - bx["x1"]) / w
            bh = (bx["y2"] - bx["y1"]) / h
            cls_id = d["class_id"]
            det_lines.append(f"{cls_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")

            seg = d.get("segmentation")
            if seg:
                coords = " ".join(f"{v:.6f}" for v in seg)
                seg_lines.append(f"{cls_id} {coords}")
            else:
                # Fallback: degenerate polygon from the box corners so every
                # detection still contributes a training mask.
                seg_lines.append(
                    f"{cls_id} {cx-bw/2:.6f} {cy-bh/2:.6f} {cx+bw/2:.6f} {cy-bh/2:.6f} "
                    f"{cx+bw/2:.6f} {cy+bh/2:.6f} {cx-bw/2:.6f} {cy+bh/2:.6f}"
                )

        lbl_name = f"{prefix}_{i+1:04d}.txt"
        (det_labels_dir / lbl_name).write_text("\n".join(det_lines) + ("\n" if det_lines else ""))
        (seg_labels_dir / lbl_name).write_text("\n".join(seg_lines) + ("\n" if seg_lines else ""))


def generate_yolo_dataset(output_dir: str = "data/yolo_dataset", num_train: int = 240,
                           num_val: int = 48, img_size: int = 416, jpeg_quality: int = 90):
    """
    Generates a synthetic side-scan-sonar dataset with BOTH detection
    (bounding box) and instance-segmentation (polygon) labels, sharing the
    same underlying images. Two dataset roots are produced:

      <output_dir>_det/  images/{train,val}, labels/{train,val}   (bbox)
      <output_dir>_seg/  images/{train,val}, labels/{train,val}   (polygon)

    Each root gets its own data.yaml so `train_yolo.py` can point YOLOv8n at
    the detection root and YOLOv8n-seg at the segmentation root.
    """
    det_root = Path(f"{output_dir}_det")
    seg_root = Path(f"{output_dir}_seg")

    for root in (det_root, seg_root):
        for split in ("train", "val"):
            (root / "images" / split).mkdir(parents=True, exist_ok=True)
            (root / "labels" / split).mkdir(parents=True, exist_ok=True)

    print(f"Generating {num_train} training images ({img_size}x{img_size})...")
    _write_split(num_train, det_root / "images" / "train", det_root / "labels" / "train",
                 seg_root / "labels" / "train", "train", img_size, jpeg_quality, seed_offset=0)
    print(f"Generating {num_val} validation images ({img_size}x{img_size})...")
    _write_split(num_val, det_root / "images" / "val", det_root / "labels" / "val",
                 seg_root / "labels" / "val", "val", img_size, jpeg_quality, seed_offset=100000)

    # The segmentation dataset uses the identical images as the detection
    # dataset (only the label format differs), so hardlink/copy them across
    # instead of re-rendering to keep disk usage and generation time down.
    import shutil
    import os
    for split in ("train", "val"):
        src_dir = det_root / "images" / split
        dst_dir = seg_root / "images" / split
        for img_path in src_dir.iterdir():
            dst_path = dst_dir / img_path.name
            try:
                os.link(img_path, dst_path)
            except OSError:
                shutil.copy2(img_path, dst_path)

    for root, name in [(det_root, "detection"), (seg_root, "segmentation")]:
        data_yaml = {
            "path": str(root.resolve()),
            "train": "images/train",
            "val": "images/val",
            "names": {i: cls for i, cls in enumerate(CLASSES)},
        }
        yaml_path = root / "data.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump(data_yaml, f, sort_keys=False)
        print(f"Wrote {name} dataset to {root} ({yaml_path.name})")

    return str(det_root / "data.yaml"), str(seg_root / "data.yaml")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate YOLO SSS training dataset (detect + seg)")
    parser.add_argument("--output", default="data/yolo_dataset", help="Output directory prefix")
    parser.add_argument("--train", type=int, default=240, help="Number of training images")
    parser.add_argument("--val", type=int, default=48, help="Number of validation images")
    parser.add_argument("--imgsz", type=int, default=416, help="Rendered image size")
    parser.add_argument("--quality", type=int, default=90, help="JPEG quality for stored images")
    args = parser.parse_args()

    generate_yolo_dataset(args.output, args.train, args.val, args.imgsz, args.quality)
