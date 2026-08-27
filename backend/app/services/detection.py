import numpy as np
from ultralytics import YOLO
from ..config import YOLO_DETECT_WEIGHTS, YOLO_CONFIDENCE, YOLO_IMGSZ, DEVICE


class DetectionService:
    def __init__(self):
        self.model = None

    def load(self):
        if YOLO_DETECT_WEIGHTS.exists():
            self.model = YOLO(str(YOLO_DETECT_WEIGHTS))
        else:
            self.model = YOLO("yolov8n.pt")

    def detect(self, image: np.ndarray) -> list[dict]:
        if self.model is None:
            self.load()

        results = self.model.predict(
            image,
            conf=YOLO_CONFIDENCE,
            imgsz=YOLO_IMGSZ,
            device=0 if DEVICE == "cuda" else "cpu",
            verbose=False,
        )

        detections = []
        for r in results:
            boxes = r.boxes
            if boxes is None:
                continue
            for i in range(len(boxes)):
                xyxy = boxes.xyxy[i].cpu().numpy()
                conf = float(boxes.conf[i].cpu().numpy())
                cls_id = int(boxes.cls[i].cpu().numpy())
                cls_name = r.names[cls_id]

                detections.append({
                    "bbox": {
                        "x1": float(xyxy[0]),
                        "y1": float(xyxy[1]),
                        "x2": float(xyxy[2]),
                        "y2": float(xyxy[3]),
                    },
                    "confidence": conf,
                    "class_id": cls_id,
                    "class_name": cls_name,
                })

        return detections
