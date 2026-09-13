from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ultralytics import YOLO
import torch

DEVICE_ARG = 0 if torch.cuda.is_available() else "cpu"

# Side-scan sonar images are single-channel (replicated to 3 channels), so
# hue/saturation jitter is meaningless and only adds noise to training.
# Geometric augmentation (rotation, flips, translation, mosaic) suits the
# top-down, orientation-free nature of sonar waterfall imagery, so those are
# kept on. Grazing-angle intensity varies a lot in real sonar, so a bit of
# brightness ("value") jitter is kept.
SONAR_AUGMENTATION = dict(
    hsv_h=0.0,
    hsv_s=0.0,
    hsv_v=0.3,
    degrees=15.0,
    translate=0.1,
    scale=0.3,
    shear=0.0,
    perspective=0.0,
    flipud=0.3,
    fliplr=0.5,
    mosaic=1.0,
    mixup=0.1,
    erasing=0.2,
)


def train_detection(data_yaml: str, epochs: int = 60, imgsz: int = 416, batch: int = 8):
    print(f"Training YOLOv8n detection on {data_yaml}")
    print(f"  Epochs: {epochs}, Image size: {imgsz}, Batch: {batch}, Device: {DEVICE_ARG}")

    model = YOLO("yolov8n.pt")
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=DEVICE_ARG,
        amp=torch.cuda.is_available(),
        patience=15,
        workers=0,
        project="models",
        name="yolov8n_sss",
<<<<<<< HEAD:scripts/train_yolo.py
        **SONAR_AUGMENTATION,
=======
        # --- Sonar-Specific Augmentations ---
        hsv_h=0.0,    # Sonar is grayscale, hue is irrelevant
        hsv_s=0.0,    # Saturation is irrelevant
        hsv_v=0.6,    # High intensity variation (simulates different sonar gains)
        degrees=180.0,# Targets can be oriented in any direction
        translate=0.2,
        scale=0.6,
        fliplr=0.5,
        flipud=0.5,   # Side-scan sonar views are top-down, up/down flip is valid
        mosaic=1.0,
        mixup=0.1,    # Simulates overlapping acoustic returns/noise
        # ------------------------------------
>>>>>>> upstream/main:scripts/training_eval/train_yolo.py
    )

    best = Path("models/yolov8n_sss/weights/best.pt")
    if best.exists():
        import shutil
        dest = Path("backend/weights/yolov8n_sss.pt")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(best, dest)
        print(f"Saved best weights to {dest}")

    return results


def train_segmentation(data_yaml: str, epochs: int = 60, imgsz: int = 416, batch: int = 8):
    print(f"Training YOLOv8n-seg on {data_yaml}")
    print(f"  Epochs: {epochs}, Image size: {imgsz}, Batch: {batch}, Device: {DEVICE_ARG}")

    model = YOLO("yolov8n-seg.pt")
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=DEVICE_ARG,
        amp=torch.cuda.is_available(),
        patience=15,
        workers=0,
        project="models",
        name="yolov8n_seg_sss",
<<<<<<< HEAD:scripts/train_yolo.py
        **SONAR_AUGMENTATION,
=======
        # --- Sonar-Specific Augmentations ---
        hsv_h=0.0,
        hsv_s=0.0,
        hsv_v=0.6,
        degrees=180.0,
        translate=0.2,
        scale=0.6,
        fliplr=0.5,
        flipud=0.5,
        mosaic=1.0,
        mixup=0.1,
        # ------------------------------------
>>>>>>> upstream/main:scripts/training_eval/train_yolo.py
    )

    best = Path("models/yolov8n_seg_sss/weights/best.pt")
    if best.exists():
        import shutil
        dest = Path("backend/weights/yolov8n_seg_sss.pt")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(best, dest)
        print(f"Saved best weights to {dest}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train YOLO models for Sonaris AI")
    parser.add_argument("--data", required=True, help="Path to detection data.yaml")
    parser.add_argument("--seg-data", default=None, help="Path to segmentation data.yaml (defaults to --data)")
    parser.add_argument("--mode", choices=["detect", "segment", "both"], default="both")
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--imgsz", type=int, default=416)
    parser.add_argument("--batch", type=int, default=8)
    args = parser.parse_args()

    if args.mode in ("detect", "both"):
        train_detection(args.data, args.epochs, args.imgsz, args.batch)

    if args.mode in ("segment", "both"):
        train_segmentation(args.seg_data or args.data, args.epochs, args.imgsz, args.batch)
