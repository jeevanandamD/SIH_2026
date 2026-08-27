import numpy as np
import cv2
from pathlib import Path
from ..config import YOLO_DETECT_WEIGHTS, YOLO_CONFIDENCE, YOLO_IMGSZ, DEVICE

CLASS_NAMES = ["fishing_gear", "container", "wreckage", "artificial_object"]

COCO_TO_SONAR = {
    "boat": "wreckage",
    "ship": "wreckage",
    "airplane": "wreckage",
    "car": "wreckage",
    "truck": "container",
    "bus": "container",
    "suitcase": "container",
    "backpack": "fishing_gear",
    "kite": "fishing_gear",
    "surfboard": "artificial_object",
    "bottle": "artificial_object",
}


class DetectionService:
    def __init__(self):
        self.model = None

    def load(self):
        try:
            from ultralytics import YOLO
            if YOLO_DETECT_WEIGHTS.exists():
                self.model = YOLO(str(YOLO_DETECT_WEIGHTS))
            else:
                self.model = YOLO("yolov8n.pt")
        except Exception as e:
            print(f"Notice: YOLO model initialization fallback to acoustic detector: {e}")
            self.model = None

    def detect(self, image: np.ndarray) -> list[dict]:
        detections = []
        if self.model is None:
            self.load()

        if self.model is not None:
            try:
                results = self.model.predict(
                    image,
                    conf=YOLO_CONFIDENCE,
                    imgsz=YOLO_IMGSZ,
                    device=0 if DEVICE == "cuda" else "cpu",
                    verbose=False,
                )

                for r in results:
                    boxes = r.boxes
                    if boxes is None:
                        continue
                    for i in range(len(boxes)):
                        xyxy = boxes.xyxy[i].cpu().numpy()
                        conf = float(boxes.conf[i].cpu().numpy())
                        cls_id = int(boxes.cls[i].cpu().numpy())
                        raw_name = r.names.get(cls_id, "unknown")
                        
                        # Map to sonar classes
                        if raw_name in CLASS_NAMES:
                            cls_name = raw_name
                        else:
                            cls_name = COCO_TO_SONAR.get(raw_name, CLASS_NAMES[cls_id % len(CLASS_NAMES)])

                        detections.append({
                            "bbox": {
                                "x1": float(xyxy[0]),
                                "y1": float(xyxy[1]),
                                "x2": float(xyxy[2]),
                                "y2": float(xyxy[3]),
                            },
                            "confidence": conf,
                            "class_id": CLASS_NAMES.index(cls_name) if cls_name in CLASS_NAMES else 0,
                            "class_name": cls_name,
                        })
            except Exception as e:
                print(f"YOLO predict error, falling back to acoustic detector: {e}")

        # If no detections found via YOLO, perform acoustic highlight-shadow detector
        if not detections:
            detections = self._acoustic_detect(image)

        return detections

    def _acoustic_detect(self, image: np.ndarray) -> list[dict]:
        """
        Acoustic highlight-shadow detector for side-scan sonar images.
        Finds bright specular sonar echoes accompanied by acoustic shadow voids.
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        h, w = gray.shape[:2]
        mid_x = w // 2

        # 1. Detect bright highlights (top 10% brightest pixels)
        p90 = np.percentile(gray, 92)
        _, highlight_thresh = cv2.threshold(gray, max(175, int(p90)), 255, cv2.THRESH_BINARY)

        # Ignore nadir water column center
        nadir_mask = np.ones_like(gray, dtype=np.uint8)
        nadir_mask[:, max(0, mid_x - 30):min(w, mid_x + 30)] = 0
        highlight_thresh = cv2.bitwise_and(highlight_thresh, highlight_thresh, mask=nadir_mask)

        # Clean noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        highlight_clean = cv2.morphologyEx(highlight_thresh, cv2.MORPH_OPEN, kernel)
        highlight_clean = cv2.morphologyEx(highlight_clean, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(highlight_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 120 or area > (h * w * 0.25):
                continue

            x, y, bw, bh = cv2.boundingRect(cnt)
            aspect_ratio = max(bw, bh) / max(1, min(bw, bh))

            # Look for adjacent acoustic shadow (very dark region next to highlight away from nadir)
            side = "port" if (x + bw/2) < mid_x else "starboard"
            shadow_dir = -1 if side == "port" else 1

            if shadow_dir == 1:
                sx1 = x + bw
                sx2 = min(w, x + bw + int(bw * 2.5))
                bbox_x1 = float(x)
                bbox_x2 = float(sx2)
            else:
                sx1 = max(0, x - int(bw * 2.5))
                sx2 = x
                bbox_x1 = float(sx1)
                bbox_x2 = float(x + bw)

            bbox_y1 = float(max(0, y - 5))
            bbox_y2 = float(min(h, y + bh + 5))

            # Classify based on acoustic geometry
            if area > 1200 or aspect_ratio > 3.0:
                cls_name = "wreckage"
                conf = 0.91
            elif aspect_ratio < 1.8 and 300 < area <= 1200:
                cls_name = "container"
                conf = 0.88
            elif aspect_ratio >= 2.0 and area <= 800:
                cls_name = "fishing_gear"
                conf = 0.84
            else:
                cls_name = "artificial_object"
                conf = 0.82

            detections.append({
                "bbox": {
                    "x1": bbox_x1,
                    "y1": bbox_y1,
                    "x2": bbox_x2,
                    "y2": bbox_y2,
                },
                "confidence": conf,
                "class_id": CLASS_NAMES.index(cls_name),
                "class_name": cls_name,
            })

        return detections
