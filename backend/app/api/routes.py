from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pathlib import Path
import uuid
import shutil

from ..services.ingestion import create_survey, add_images_to_survey, list_surveys, get_survey
from ..services.pipeline import process_survey
from ..models.database import SessionLocal, SonarImage, Detection, Anomaly, AcousticFeatures, RiskAssessment, ExpertFeedback
from ..config import RAW_DIR

router = APIRouter()


@router.get("/surveys")
def api_list_surveys():
    return list_surveys()


@router.post("/surveys")
async def api_create_survey(
    file: UploadFile = File(None),
    name: str = Form(""),
):
    survey_name = name or file.filename if file else "Unnamed Survey"
    result = create_survey(survey_name)

    if file:
        survey_dir = RAW_DIR / result["survey_id"]
        survey_dir.mkdir(parents=True, exist_ok=True)

        file_path = survey_dir / file.filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        add_images_to_survey(result["survey_id"], [str(file_path)])

    return result


@router.get("/surveys/{survey_id}")
def api_get_survey(survey_id: str):
    survey = get_survey(survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    return survey


@router.post("/surveys/{survey_id}/process")
def api_process_survey(survey_id: str):
    survey = get_survey(survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    try:
        process_survey(survey_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "completed"}


@router.get("/surveys/{survey_id}/detections")
def api_survey_detections(survey_id: str):
    db = SessionLocal()
    try:
        images = db.query(SonarImage).filter(SonarImage.survey_id == survey_id).all()
        image_ids = [img.image_id for img in images]

        results = []
        for img in images:
            dets = db.query(Detection).filter(Detection.image_id == img.image_id).all()
            for det in dets:
                anomaly = db.query(Anomaly).filter(Anomaly.detection_id == det.detection_id).first()
                features = db.query(AcousticFeatures).filter(AcousticFeatures.detection_id == det.detection_id).first()
                risk = db.query(RiskAssessment).filter(RiskAssessment.detection_id == det.detection_id).first()

                results.append({
                    "detection": {
                        "detection_id": det.detection_id,
                        "image_id": det.image_id,
                        "target_id": det.target_id,
                        "object_class": det.object_class,
                        "confidence": det.confidence,
                        "bbox": {
                            "x1": det.bbox_x1,
                            "y1": det.bbox_y1,
                            "x2": det.bbox_x2,
                            "y2": det.bbox_y2,
                        },
                        "segmentation_mask_path": det.segmentation_mask_path,
                        "latitude": img.latitude,
                        "longitude": img.longitude,
                        "depth": img.depth,
                    },
                    "anomaly": {
                        "anomaly_id": anomaly.anomaly_id,
                        "detection_id": anomaly.detection_id,
                        "anomaly_score": anomaly.anomaly_score,
                        "uncertainty": anomaly.uncertainty,
                    } if anomaly else None,
                    "acoustic_features": {
                        "detection_id": features.detection_id,
                        "target_intensity": features.target_intensity,
                        "target_area": features.target_area,
                        "shadow_area": features.shadow_area,
                        "shadow_length": features.shadow_length,
                        "target_shadow_ratio": features.target_shadow_ratio,
                        "seabed_texture": features.seabed_texture,
                        "seabed_contrast": features.seabed_contrast,
                    } if features else None,
                    "risk_assessment": {
                        "detection_id": risk.detection_id,
                        "evidence_score": risk.evidence_score,
                        "risk_score": risk.risk_score,
                        "risk_level": risk.risk_level,
                        "priority": risk.priority,
                    } if risk else None,
                })
        return results
    finally:
        db.close()


@router.get("/detections/{detection_id}")
def api_get_detection(detection_id: str):
    db = SessionLocal()
    try:
        det = db.query(Detection).filter(Detection.detection_id == detection_id).first()
        if not det:
            raise HTTPException(status_code=404, detail="Detection not found")

        img = db.query(SonarImage).filter(SonarImage.image_id == det.image_id).first()
        anomaly = db.query(Anomaly).filter(Anomaly.detection_id == detection_id).first()
        features = db.query(AcousticFeatures).filter(AcousticFeatures.detection_id == detection_id).first()
        risk = db.query(RiskAssessment).filter(RiskAssessment.detection_id == detection_id).first()

        return {
            "detection": {
                "detection_id": det.detection_id,
                "image_id": det.image_id,
                "target_id": det.target_id,
                "object_class": det.object_class,
                "confidence": det.confidence,
                "bbox": {
                    "x1": det.bbox_x1,
                    "y1": det.bbox_y1,
                    "x2": det.bbox_x2,
                    "y2": det.bbox_y2,
                },
                "segmentation_mask_path": det.segmentation_mask_path,
                "latitude": img.latitude if img else None,
                "longitude": img.longitude if img else None,
                "depth": img.depth if img else None,
            },
            "anomaly": {
                "anomaly_id": anomaly.anomaly_id,
                "detection_id": anomaly.detection_id,
                "anomaly_score": anomaly.anomaly_score,
                "uncertainty": anomaly.uncertainty,
            } if anomaly else None,
            "acoustic_features": {
                "detection_id": features.detection_id,
                "target_intensity": features.target_intensity,
                "target_area": features.target_area,
                "shadow_area": features.shadow_area,
                "shadow_length": features.shadow_length,
                "target_shadow_ratio": features.target_shadow_ratio,
                "seabed_texture": features.seabed_texture,
                "seabed_contrast": features.seabed_contrast,
            } if features else None,
            "risk_assessment": {
                "detection_id": risk.detection_id,
                "evidence_score": risk.evidence_score,
                "risk_score": risk.risk_score,
                "risk_level": risk.risk_level,
                "priority": risk.priority,
            } if risk else None,
        }
    finally:
        db.close()


@router.post("/detections/{detection_id}/verify")
def api_verify_detection(detection_id: str, body: dict):
    db = SessionLocal()
    try:
        det = db.query(Detection).filter(Detection.detection_id == detection_id).first()
        if not det:
            raise HTTPException(status_code=404, detail="Detection not found")

        feedback = ExpertFeedback(
            feedback_id=f"fb_{uuid.uuid4().hex[:8]}",
            detection_id=detection_id,
            expert_label=body.get("expert_label", ""),
            correction=body.get("correction"),
            comments=body.get("comments"),
            verified=1,
        )
        db.add(feedback)
        db.commit()
        return {"feedback_id": feedback.feedback_id, "status": "verified"}
    finally:
        db.close()


@router.get("/targets/geojson")
def api_targets_geojson():
    db = SessionLocal()
    try:
        features = []
        detections = db.query(Detection).all()
        for det in detections:
            risk = db.query(RiskAssessment).filter(RiskAssessment.detection_id == det.detection_id).first()
            anomaly = db.query(Anomaly).filter(Anomaly.detection_id == det.detection_id).first()
            img = db.query(SonarImage).filter(SonarImage.image_id == det.image_id).first()

            lat = img.latitude if img and img.latitude else 0.0
            lon = img.longitude if img and img.longitude else 0.0

            if lat == 0.0 and lon == 0.0:
                continue

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],
                },
                "properties": {
                    "detection_id": det.detection_id,
                    "target_id": det.target_id,
                    "object_class": det.object_class,
                    "confidence": det.confidence,
                    "anomaly_score": anomaly.anomaly_score if anomaly else 0.0,
                    "evidence_score": risk.evidence_score if risk else 0.0,
                    "risk_level": risk.risk_level if risk else "LOW",
                    "risk_score": risk.risk_score if risk else 0.0,
                    "depth": img.depth if img else None,
                    "priority": risk.priority if risk else 999,
                },
            })

        return {"type": "FeatureCollection", "features": features}
    finally:
        db.close()


@router.get("/targets/priority")
def api_targets_priority():
    db = SessionLocal()
    try:
        risks = db.query(RiskAssessment).order_by(RiskAssessment.priority).all()
        results = []
        for r in risks:
            det = db.query(Detection).filter(Detection.detection_id == r.detection_id).first()
            if not det:
                continue
            img = db.query(SonarImage).filter(SonarImage.image_id == det.image_id).first()
            results.append({
                "target_id": det.target_id,
                "detection_id": det.detection_id,
                "object_class": det.object_class,
                "risk_level": r.risk_level,
                "risk_score": r.risk_score,
                "evidence_score": r.evidence_score,
                "confidence": det.confidence,
                "latitude": img.latitude if img else None,
                "longitude": img.longitude if img else None,
                "priority": r.priority,
            })
        return results
    finally:
        db.close()


@router.get("/targets/heatmap")
def api_targets_heatmap():
    db = SessionLocal()
    try:
        points = []
        anomalies = db.query(Anomaly).all()
        for a in anomalies:
            det = db.query(Detection).filter(Detection.detection_id == a.detection_id).first()
            if not det:
                continue
            img = db.query(SonarImage).filter(SonarImage.image_id == det.image_id).first()
            if img and img.latitude and img.longitude:
                points.append({
                    "latitude": img.latitude,
                    "longitude": img.longitude,
                    "intensity": a.anomaly_score,
                })
        return points
    finally:
        db.close()


@router.get("/stats")
def api_stats():
    db = SessionLocal()
    try:
        total_surveys = db.query(Survey).count()
        total_detections = db.query(Detection).count()
        high_risk = db.query(RiskAssessment).filter(RiskAssessment.risk_level == "HIGH").count()
        medium_risk = db.query(RiskAssessment).filter(RiskAssessment.risk_level == "MEDIUM").count()
        low_risk = db.query(RiskAssessment).filter(RiskAssessment.risk_level == "LOW").count()
        processed = db.query(Survey).filter(Survey.status == "completed").count()

        return {
            "total_surveys": total_surveys,
            "total_detections": total_detections,
            "high_risk_count": high_risk,
            "medium_risk_count": medium_risk,
            "low_risk_count": low_risk,
            "processed_surveys": processed,
        }
    finally:
        db.close()
