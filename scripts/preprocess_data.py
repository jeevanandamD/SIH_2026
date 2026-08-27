from pathlib import Path
import cv2
import numpy as np
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.services.preprocessing import preprocess_sonar


def preprocess_dataset(raw_dir: str, output_dir: str):
    raw_path = Path(raw_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
    images = [f for f in raw_path.iterdir() if f.suffix.lower() in extensions]

    print(f"Found {len(images)} images in {raw_dir}")

    for i, img_path in enumerate(images):
        raw = cv2.imread(str(img_path))
        if raw is None:
            print(f"  Skipping {img_path.name} (unreadable)")
            continue

        enhanced = preprocess_sonar(raw)
        out_file = out_path / f"enhanced_{img_path.stem}.png"
        cv2.imwrite(str(out_file), enhanced)

        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{len(images)}")

    print(f"Done. Output saved to {output_dir}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Preprocess sonar images")
    parser.add_argument("--raw", default="data/raw", help="Raw images directory")
    parser.add_argument("--output", default="data/processed", help="Output directory")
    args = parser.parse_args()

    preprocess_dataset(args.raw, args.output)
