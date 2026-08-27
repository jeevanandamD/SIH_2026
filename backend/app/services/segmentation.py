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
        masks = []
        if self.model is None:
            self.load()

        h, w = image.shape[:2]

        if self.model is not None:
            try:
                results = self.model.predict(
                    image,
                    conf=YOLO_CONFIDENCE,
                    imgsz=YOLO_IMGSZ,
                    device=0 if DEVICE == "cuda" else "cpu",
                    verbose=False,
                )
                if results and results[0].masks is not None:
                    seg_masks = results[0].masks.data.cpu().numpy()
                    for i in range(len(detections)):
                        if i < len(seg_masks):
                            m = cv2.resize(seg_masks[i].astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
                            masks.append((m > 0.5).astype(np.uint8))
                        else:
                            masks.append(self._roi_mask(image, detections[i]["bbox"]))
                    return masks
            except Exception as e:
                print(f"Segmentation predict fallback: {e}")

        # Generate acoustic ROI masks for detections
        for det in detections:
            masks.append(self._roi_mask(image, det["bbox"]))

        return masks

    def _roi_mask(self, image: np.ndarray, bbox: dict) -> np.ndarray:
        h, w = image.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        x1 = max(0, int(bbox.get("x1", 0)))
        y1 = max(0, int(bbox.get("y1", 0)))
        x2 = min(w, int(bbox.get("x2", w)))
        y2 = min(h, int(bbox.get("y2", h)))

        if x2 <= x1 or y2 <= y1:
            return mask

        roi = image[y1:y2, x1:x2]
        if len(roi.shape) == 3:
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            roi_gray = roi

        # Threshold top acoustic intensity
        mean_val = np.mean(roi_gray)
        thresh_val = max(140, int(mean_val + 0.5 * np.std(roi_gray)))
        _, roi_binary = cv2.threshold(roi_gray, thresh_val, 1, cv2.THRESH_BINARY)

        mask[y1:y2, x1:x2] = roi_binary
        return mask

    def get_mask_bbox(self, mask: np.ndarray) -> dict | None:
        contours, _ = cv2.findContours(
            mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return None
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        return {"x1": x, "y1": y, "x2": x + w, "y2": y + h}
