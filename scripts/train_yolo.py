from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ultralytics import YOLO


def train_detection(data_yaml: str, epochs: int = 100, imgsz: int = 640, batch: int = 4):
    print(f"Training YOLOv8n detection on {data_yaml}")
    print(f"  Epochs: {epochs}, Image size: {imgsz}, Batch: {batch}")

    model = YOLO("yolov8n.pt")
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=0,
        amp=True,
        patience=20,
        workers=4,
        project="models",
        name="yolov8n_sss",
    )

    best = Path("models/yolov8n_sss/weights/best.pt")
    if best.exists():
        import shutil
        dest = Path("backend/weights/yolov8n_sss.pt")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(best, dest)
        print(f"Saved best weights to {dest}")

    return results


def train_segmentation(data_yaml: str, epochs: int = 100, imgsz: int = 640, batch: int = 4):
    print(f"Training YOLOv8n-seg on {data_yaml}")
    print(f"  Epochs: {epochs}, Image size: {imgsz}, Batch: {batch}")

    model = YOLO("yolov8n-seg.pt")
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=0,
        amp=True,
        patience=20,
        workers=4,
        project="models",
        name="yolov8n_seg_sss",
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
    parser.add_argument("--data", required=True, help="Path to data.yaml")
    parser.add_argument("--mode", choices=["detect", "segment", "both"], default="both")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=4)
    args = parser.parse_args()

    if args.mode in ("detect", "both"):
        train_detection(args.data, args.epochs, args.imgsz, args.batch)

    if args.mode in ("segment", "both"):
        train_segmentation(args.data, args.epochs, args.imgsz, args.batch)
