import uuid
import cv2
import numpy as np
from pathlib import Path

from ..models.database import SessionLocal, Detection, Anomaly, AcousticFeatures, RiskAssessment, SonarImage
from ..services.preprocessing import preprocess_sonar, extract_bounding_box_crop
from ..services.detection import DetectionService
from ..services.segmentation import SegmentationService
from ..services.anomaly import AnomalyDetector
from ..services.acoustic_features import extract_acoustic_features
from ..services.evidence_fusion import fuse_evidence
from ..services.risk_engine import compute_risk
from ..services.geo_localization import geo_localize_detection
from ..services.prioritization import assign_priorities
from ..services.ingestion import update_survey_status

detection_service = DetectionService()
segmentation_service = SegmentationService()
anomaly_detector = AnomalyDetector()

_detection_counter = 0


def _next_detection_id() -> str:
    global _detection_counter
    _detection_counter += 1
    return f"AS_{_detection_counter:06d}"


def process_survey(survey_id: str):
    db = SessionLocal()
    try:
        update_survey_status(survey_id, "processing")
        db.commit()

        images = db.query(SonarImage).filter(SonarImage.survey_id == survey_id).all()
        if not images:
            update_survey_status(survey_id, "completed")
            db.commit()
            return

        all_detections = []

        for img_record in images:
            img_path = Path(img_record.image_path)
            if not img_path.exists():
                continue

            raw = cv2.imread(str(img_path))
            if raw is None:
                continue

            if len(raw.shape) == 2:
                raw = cv2.cvtColor(raw, cv2.COLOR_GRAY2BGR)

            image_width = raw.shape[1]
            image_height = raw.shape[0]

            enhanced = preprocess_sonar(raw)
            enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

            detections = detection_service.detect(enhanced_bgr)

            masks = segmentation_service.segment(enhanced_bgr, detections) if detections else []

            anomaly_scores = anomaly_detector.score_detections(enhanced, detections) if detections else []

            image_metadata = {
                "latitude": img_record.latitude,
                "longitude": img_record.longitude,
                "depth": img_record.depth,
                "heading": 0.0,
                "sonar_range": 100.0,
                "image_width": image_width,
            }

            for i, det in enumerate(detections):
                bbox = det["bbox"]
                mask = masks[i] if i < len(masks) else np.zeros((image_height, image_width), dtype=np.uint8)
                anomaly_score = anomaly_scores[i] if i < len(anomaly_scores) else 0.5

                target_id = f"T_{uuid.uuid4().hex[:6].upper()}"
                detection_id = _next_detection_id()

                features = extract_acoustic_features(enhanced, mask)

                fusion_result = fuse_evidence(features, anomaly_score, det["confidence"])

                risk_result = compute_risk(
                    object_class=det["class_name"],
                    anomaly_score=anomaly_score,
                    evidence_score=fusion_result["evidence_score"],
                    target_area=features["target_area"],
                    confidence=det["confidence"],
                )

                geo = geo_localize_detection(det, image_metadata)

                det_record = Detection(
                    detection_id=detection_id,
                    image_id=img_record.image_id,
                    target_id=target_id,
                    object_class=det["class_name"],
                    confidence=det["confidence"],
                    bbox_x1=bbox["x1"],
                    bbox_y1=bbox["y1"],
                    bbox_x2=bbox["x2"],
                    bbox_y2=bbox["y2"],
                )
                db.add(det_record)

                anomaly_record = Anomaly(
                    anomaly_id=f"anom_{uuid.uuid4().hex[:8]}",
                    detection_id=detection_id,
                    anomaly_score=anomaly_score,
                    uncertainty=abs(anomaly_score - 0.5) * 2,
                )
                db.add(anomaly_record)

                features_record = AcousticFeatures(
                    detection_id=detection_id,
                    target_intensity=features["target_intensity"],
                    target_area=features["target_area"],
                    shadow_area=features["shadow_area"],
                    shadow_length=features["shadow_length"],
                    target_shadow_ratio=features["target_shadow_ratio"],
                    seabed_texture=features["seabed_texture"],
                    seabed_contrast=features["seabed_contrast"],
                )
                db.add(features_record)

                all_detections.append({
                    "detection_id": detection_id,
                    "target_id": target_id,
                    "object_class": det["class_name"],
                    "risk_level": risk_result["risk_level"],
                    "risk_score": risk_result["risk_score"],
                    "evidence_score": fusion_result["evidence_score"],
                    "confidence": det["confidence"],
                    "latitude": geo["latitude"],
                    "longitude": geo["longitude"],
                    "depth": geo["depth"],
                    "target_area": features["target_area"],
                })

                risk_record = RiskAssessment(
                    detection_id=detection_id,
                    evidence_score=fusion_result["evidence_score"],
                    risk_score=risk_result["risk_score"],
                    risk_level=risk_result["risk_level"],
                    priority=0,
                )
                db.add(risk_record)

        prioritized = assign_priorities(all_detections)
        for p in prioritized:
            risk_rec = db.query(RiskAssessment).filter(RiskAssessment.detection_id == p["detection_id"]).first()
            if risk_rec:
                risk_rec.priority = p["priority"]

        db.commit()
        update_survey_status(survey_id, "completed")
        db.commit()

    except Exception as e:
        db.rollback()
        update_survey_status(survey_id, "failed")
        db.commit()
        raise e
    finally:
        db.close()
