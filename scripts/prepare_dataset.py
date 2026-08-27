from pathlib import Path
import random
import cv2
import numpy as np
import yaml
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.app.services.synthetic_sonar import generate_synthetic_sonar_image

def generate_yolo_dataset(output_dir: str = "data/yolo_dataset", num_train: int = 40, num_val: int = 10):
    root = Path(output_dir)
    images_train = root / "images" / "train"
    images_val = root / "images" / "val"
    labels_train = root / "labels" / "train"
    labels_val = root / "labels" / "val"

    for d in [images_train, images_val, labels_train, labels_val]:
        d.mkdir(parents=True, exist_ok=True)

    classes = ["fishing_gear", "container", "wreckage", "artificial_object"]

    def create_split(count: int, img_dir: Path, lbl_dir: Path, prefix: str):
        for i in range(count):
            img, dets = generate_synthetic_sonar_image(width=640, height=640)
            img_name = f"{prefix}_{i+1:04d}.png"
            lbl_name = f"{prefix}_{i+1:04d}.txt"

            cv2.imwrite(str(img_dir / img_name), img)

            h, w = img.shape[:2]
            with open(lbl_dir / lbl_name, "w") as f:
                for d in dets:
                    bx = d["target_bbox"]
                    cx = ((bx["x1"] + bx["x2"]) / 2.0) / w
                    cy = ((bx["y1"] + bx["y2"]) / 2.0) / h
                    bw = (bx["x2"] - bx["x1"]) / w
                    bh = (bx["y2"] - bx["y1"]) / h
                    cls_id = d["class_id"]
                    f.write(f"{cls_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")

    print(f"Generating {num_train} training samples...")
    create_split(num_train, images_train, labels_train, "train")
    print(f"Generating {num_val} validation samples...")
    create_split(num_val, images_val, labels_val, "val")

    data_yaml = {
        "path": str(root.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": {i: name for i, name in enumerate(classes)}
    }

    yaml_path = root / "data.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(data_yaml, f, sort_keys=False)

    print(f"Successfully created YOLO dataset at {root} with data.yaml")
    return str(yaml_path)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate YOLO SSS training dataset")
    parser.add_argument("--output", default="data/yolo_dataset", help="Output directory")
    parser.add_argument("--train", type=int, default=30, help="Number of training images")
    parser.add_argument("--val", type=int, default=8, help="Number of validation images")
    args = parser.parse_args()

    generate_yolo_dataset(args.output, args.train, args.val)
