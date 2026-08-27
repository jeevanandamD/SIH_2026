import cv2
import numpy as np
from ultralytics import YOLO
from ..config import YOLO_SEG_WEIGHTS, YOLO_CONFIDENCE, YOLO_IMGSZ, DEVICE


class SegmentationService:
    def __init__(self):
        self.model = None

    def load(self):
        if YOLO_SEG_WEIGHTS.exists():
            self.model = YOLO(str(YOLO_SEG_WEIGHTS))
        else:
            self.model = YOLO("yolov8n-seg.pt")

    def segment(self, image: np.ndarray, detections: list[dict]) -> list[np.ndarray]:
        if self.model is None:
            self.load()

        results = self.model.predict(
            image,
            conf=YOLO_CONFIDENCE,
            imgsz=YOLO_IMGSZ,
            device=0 if DEVICE == "cuda" else "cpu",
            verbose=False,
        )

        masks = []
        result = results[0] if results else None
        if result is None or result.masks is None:
            for _ in detections:
                masks.append(np.zeros(image.shape[:2], dtype=np.uint8))
            return masks

        seg_masks = result.masks.data.cpu().numpy()
        h, w = image.shape[:2]

        for i, det in enumerate(detections):
            if i < len(seg_masks):
                mask = seg_masks[i]
                mask_resized = cv2.resize(mask.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
                mask_binary = (mask_resized > 0.5).astype(np.uint8)
                masks.append(mask_binary)
            else:
                masks.append(np.zeros((h, w), dtype=np.uint8))

        return masks

    def get_mask_bbox(self, mask: np.ndarray) -> dict | None:
        contours, _ = cv2.findContours(
            mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return None
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        return {"x1": x, "y1": y, "x2": x + w, "y2": y + h}
