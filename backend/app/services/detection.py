import numpy as np
import cv2
from pathlib import Path
from ..config import YOLO_DETECT_WEIGHTS, YOLO_CONFIDENCE, YOLO_IMGSZ, DEVICE

CLASS_NAMES = ["fishing_gear", "container", "wreckage", "artificial_object"]


class DetectionService:
    def __init__(self):
        self.model = None
        # True once a sonar-domain-trained checkpoint (backend/weights/yolov8n_sss.pt)
        # is loaded. False means we only have the generic COCO-pretrained
        # yolov8n.pt, whose class vocabulary (boats, backpacks, kites, ...)
        # has no reliable correspondence to sonar target classes.
        self.is_custom = False

    def load(self):
        try:
            from ultralytics import YOLO
            if YOLO_DETECT_WEIGHTS.exists():
                self.model = YOLO(str(YOLO_DETECT_WEIGHTS))
                self.is_custom = True
            else:
                # No sonar-trained weights available. We deliberately do NOT
                # load the generic COCO yolov8n.pt here anymore: previously
                # this code ran COCO inference and remapped arbitrary COCO
                # classes ("boat", "backpack", "kite", ...) onto sonar
                # classes via a hardcoded lookup table. COCO was trained on
                # everyday photographs, not acoustic backscatter imagery, so
                # those detections (and their confidences) were not
                # meaningful for sonar and actively corrupted the downstream
                # evidence-fusion and risk scoring. Falling straight through
                # to the domain-appropriate acoustic detector is more
                # honest than dressing up irrelevant COCO predictions as
                # sonar detections.
                print("Notice: no sonar-trained detection weights found "
                      f"({YOLO_DETECT_WEIGHTS}); using the acoustic "
                      "highlight-shadow detector instead of generic COCO "
                      "YOLO. Run scripts/train_yolo.py to train sonar-"
                      "specific weights.")
                self.model = None
                self.is_custom = False
        except Exception as e:
            print(f"Notice: YOLO model initialization fallback to acoustic detector: {e}")
            self.model = None
            self.is_custom = False

    def detect(self, image: np.ndarray) -> list[dict]:
        detections = []
        if self.model is None and not self.is_custom:
            self.load()

        if self.model is not None and self.is_custom:
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
                        # The sonar-trained model's own class vocabulary IS
                        # the sonar class vocabulary (it was trained on
                        # fishing_gear/container/wreckage/artificial_object
                        # labels directly), so no COCO remapping is needed
                        # or applied.
                        cls_name = r.names.get(cls_id, CLASS_NAMES[cls_id % len(CLASS_NAMES)])

                        detections.append({
                            "bbox": {
                                "x1": float(xyxy[0]),
                                "y1": float(xyxy[1]),
                                "x2": float(xyxy[2]),
                                "y2": float(xyxy[3]),
                            },
                            "confidence": conf,
                            "class_id": CLASS_NAMES.index(cls_name) if cls_name in CLASS_NAMES else cls_id,
                            "class_name": cls_name,
                        })
            except Exception as e:
                print(f"YOLO predict error, falling back to acoustic detector: {e}")

        # If no sonar-trained model is available (or it found nothing),
        # fall back to the acoustic highlight-shadow detector.
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
        background_mean = float(np.mean(gray))
        background_std = float(np.std(gray)) + 1e-6

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
                typical_area, area_tol = 2200.0, 1800.0
                typical_ar, ar_tol = 4.0, 2.5
            elif aspect_ratio < 1.8 and 300 < area <= 1200:
                cls_name = "container"
                typical_area, area_tol = 700.0, 500.0
                typical_ar, ar_tol = 1.3, 0.6
            elif aspect_ratio >= 2.0 and area <= 800:
                cls_name = "fishing_gear"
                typical_area, area_tol = 450.0, 350.0
                typical_ar, ar_tol = 2.6, 1.2
            else:
                cls_name = "artificial_object"
                typical_area, area_tol = 500.0, 400.0
                typical_ar, ar_tol = 1.5, 0.8

            # Confidence is derived from measured evidence rather than a
            # fixed per-class constant: how bright the highlight is versus
            # the local background (acoustic strength), and how closely the
            # blob's area/aspect-ratio match the profile typical of the
            # assigned class. A previous version returned hardcoded values
            # (0.91/0.88/0.84/0.82) regardless of the actual patch, which
            # fed a fake, uninformative "confidence" straight into the
            # evidence-fusion and risk-scoring stages downstream.
            mask = np.zeros_like(gray, dtype=np.uint8)
            cv2.drawContours(mask, [cnt], -1, 255, -1)
            highlight_mean = float(np.mean(gray[mask > 0])) if np.any(mask > 0) else background_mean
            intensity_z = (highlight_mean - background_mean) / background_std
            intensity_score = float(np.clip(intensity_z / 6.0, 0.0, 1.0))

            area_score = float(np.clip(1.0 - abs(area - typical_area) / area_tol, 0.0, 1.0))
            ar_score = float(np.clip(1.0 - abs(aspect_ratio - typical_ar) / ar_tol, 0.0, 1.0))

            conf = 0.45 * intensity_score + 0.30 * area_score + 0.25 * ar_score
            conf = float(np.clip(conf, 0.30, 0.97))

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
