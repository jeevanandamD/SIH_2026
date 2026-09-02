from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, Response
from pathlib import Path
import uuid
import shutil
import cv2
import io
import csv

from ..services.ingestion import create_survey, add_images_to_survey, list_surveys, get_survey
from ..services.pipeline import process_survey
from ..services.synthetic_sonar import generate_synthetic_sonar_image
from ..models.database import SessionLocal, Survey, SonarImage, Detection, Anomaly, AcousticFeatures, RiskAssessment, ExpertFeedback
from ..config import RAW_DIR

router = APIRouter()


@router.get("/surveys")
def api_list_surveys():
    return list_surveys()


@router.post("/surveys")
async def api_create_survey(
    file: UploadFile = File(None),
    name: str = Form(""),
    vessel_id: str = Form("INS Nireekshak / Survey AUV-1"),
    area_name: str = Form("Arabian Sea - Sector 4"),
    sonar_type: str = Form("EdgeTech 4200 Dual-Frequency SSS (400/900 kHz)"),
):
    survey_name = name or (file.filename.replace(".zip", "") if file and file.filename else "Survey Mission")
    result = create_survey(
        name=survey_name,
        vessel_id=vessel_id,
        area_name=area_name,
        sonar_type=sonar_type,
    )

    if file:
        survey_dir = RAW_DIR / result["survey_id"]
        survey_dir.mkdir(parents=True, exist_ok=True)

        file_path = survey_dir / file.filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Check if it's an image or zip
        ext = file_path.suffix.lower()
        if ext in [".png", ".jpg", ".jpeg", ".tif", ".bmp"]:
            add_images_to_survey(
                result["survey_id"],
                [str(file_path)],
                [{"latitude": 15.4208, "longitude": 72.5000, "depth": 38.5, "timestamp": "2026-08-27T10:15:00Z"}]
            )
        elif ext in [".zip"]:
            import zipfile
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(survey_dir)
            
            image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
            extracted_imgs = [str(p) for p in survey_dir.rglob("*") if p.suffix.lower() in image_extensions]
            if extracted_imgs:
                meta = []
                base_lat, base_lon = 15.4208, 72.5000
                for idx in range(len(extracted_imgs)):
                    meta.append({
                        "latitude": base_lat + idx * 0.001,
                        "longitude": base_lon - idx * 0.001,
                        "depth": 35.0 + idx * 1.5,
                        "timestamp": f"2026-08-27T10:{15 + idx:02d}:00Z",
                    })
                add_images_to_survey(result["survey_id"], extracted_imgs, meta)

    return result


@router.get("/surveys/{survey_id}")
def api_get_survey(survey_id: str):
    survey = get_survey(survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    return survey


@router.delete("/surveys/{survey_id}")
def api_delete_survey(survey_id: str):
    db = SessionLocal()
    try:
        survey = db.query(Survey).filter(Survey.survey_id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")

        images = db.query(SonarImage).filter(SonarImage.survey_id == survey_id).all()
        for img in images:
            dets = db.query(Detection).filter(Detection.image_id == img.image_id).all()
            for d in dets:
                db.query(Anomaly).filter(Anomaly.detection_id == d.detection_id).delete()
                db.query(AcousticFeatures).filter(AcousticFeatures.detection_id == d.detection_id).delete()
                db.query(RiskAssessment).filter(RiskAssessment.detection_id == d.detection_id).delete()
                db.query(ExpertFeedback).filter(ExpertFeedback.detection_id == d.detection_id).delete()
                db.delete(d)
            db.delete(img)

        db.delete(survey)
        db.commit()

        # Remove files if needed
        survey_dir = RAW_DIR / survey_id
        if survey_dir.exists():
            shutil.rmtree(survey_dir, ignore_errors=True)

        return {"status": "deleted", "survey_id": survey_id}
    finally:
        db.close()


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


@router.post("/surveys/demo/generate")
def api_generate_demo_surveys():
    """
    Generates rich, realistic side-scan sonar surveys with synthetic waterfall imagery,
    real geo-coordinates along ocean tracks, and processes them through the full pipeline.
    """
    demo_specs = [
        {
            "name": "Survey Alpha: Arabian Sea Pipeline Corridor",
            "vessel_id": "INS Nireekshak / Autonomous Survey Swarm 01",
            "area_name": "Offshore Mumbai Basin - Pipeline Sector 4",
            "sonar_type": "EdgeTech 4200 Dual-Frequency SSS (400/900 kHz)",
            "start_lat": 18.9220,
            "start_lon": 72.3000,
            "delta_lat": 0.0035,
            "delta_lon": 0.0040,
            "depth_base": 42.0,
            "num_images": 4,
            "targets_plan": [
                [{"class_name": "wreckage"}, {"class_name": "fishing_gear"}],
                [{"class_name": "container"}],
                [{"class_name": "artificial_object"}, {"class_name": "wreckage"}],
                [{"class_name": "fishing_gear"}, {"class_name": "container"}],
            ]
        },
        {
            "name": "Survey Bravo: Palk Strait Ghost Net Clearance",
            "vessel_id": "ICGS Samarth / Autonomous Towfish SSS-2",
            "area_name": "Palk Strait Marine Biosphere Corridor",
            "sonar_type": "Klein 4900 High-Resolution Dual-Beam SSS",
            "start_lat": 9.7876,
            "start_lon": 79.5129,
            "delta_lat": 0.0030,
            "delta_lon": 0.0025,
            "depth_base": 24.5,
            "num_images": 3,
            "targets_plan": [
                [{"class_name": "fishing_gear"}, {"class_name": "fishing_gear"}],
                [{"class_name": "container"}],
                [{"class_name": "wreckage"}, {"class_name": "artificial_object"}],
            ]
        },
        {
            "name": "Survey Charlie: Kochi Port Deepwater Channel",
            "vessel_id": "Survey Vessel Sandhayak (J18)",
            "area_name": "Kochi Harbor Approach & Anchorage Area",
            "sonar_type": "L3Harris SeaBat T50-R / EdgeTech SSS",
            "start_lat": 9.9650,
            "start_lon": 75.8210,
            "delta_lat": 0.0028,
            "delta_lon": 0.0032,
            "depth_base": 32.0,
            "num_images": 3,
            "targets_plan": [
                [{"class_name": "container"}, {"class_name": "artificial_object"}],
                [{"class_name": "wreckage"}],
                [{"class_name": "fishing_gear"}],
            ]
        }
    ]

    created_surveys = []
    for spec in demo_specs:
        survey_res = create_survey(
            name=spec["name"],
            vessel_id=spec["vessel_id"],
            area_name=spec["area_name"],
            sonar_type=spec["sonar_type"],
            start_time="2026-08-27 06:00:00 UTC",
            end_time="2026-08-27 12:30:00 UTC",
        )
        sid = survey_res["survey_id"]
        survey_dir = RAW_DIR / sid
        survey_dir.mkdir(parents=True, exist_ok=True)

        image_paths = []
        metadata_list = []
        for i in range(spec["num_images"]):
            targets = spec["targets_plan"][i] if i < len(spec["targets_plan"]) else None
            sonar_img, _ = generate_synthetic_sonar_image(
                width=640,
                height=640,
                nadir_width=44,
                targets=targets,
            )
            img_filename = f"sss_scan_{i+1:02d}.png"
            img_path = survey_dir / img_filename
            cv2.imwrite(str(img_path), sonar_img)
            image_paths.append(str(img_path))

            lat = spec["start_lat"] + (i * spec["delta_lat"])
            lon = spec["start_lon"] + (i * spec["delta_lon"])
            metadata_list.append({
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "depth": round(spec["depth_base"] + (i * 1.8), 1),
                "timestamp": f"2026-08-27T08:{20 + i*15:02d}:00Z",
            })

        add_images_to_survey(sid, image_paths, metadata_list)
        process_survey(sid)
        created_surveys.append(sid)

    return {"status": "success", "surveys_created": created_surveys}


@router.get("/images/{image_id}")
def api_get_image(image_id: str):
    db = SessionLocal()
    try:
        img = db.query(SonarImage).filter(SonarImage.image_id == image_id).first()
        if not img or not Path(img.image_path).exists():
            raise HTTPException(status_code=404, detail="Sonar image not found")
        return FileResponse(img.image_path, media_type="image/png")
    finally:
        db.close()


@router.get("/detections/{detection_id}/crop")
def api_get_detection_crop(detection_id: str):
    db = SessionLocal()
    try:
        det = db.query(Detection).filter(Detection.detection_id == detection_id).first()
        if not det:
            raise HTTPException(status_code=404, detail="Detection not found")

        img = db.query(SonarImage).filter(SonarImage.image_id == det.image_id).first()
        if not img or not Path(img.image_path).exists():
            raise HTTPException(status_code=404, detail="Sonar image not found")

        image = cv2.imread(img.image_path)
        if image is None:
            raise HTTPException(status_code=500, detail="Could not load image")

        h, w = image.shape[:2]
        pad = 25
        x1 = max(0, int(det.bbox_x1) - pad)
        y1 = max(0, int(det.bbox_y1) - pad)
        x2 = min(w, int(det.bbox_x2) + pad)
        y2 = min(h, int(det.bbox_y2) + pad)

        crop = image[y1:y2, x1:x2].copy()
        # Draw subtle target highlight box
        bx1 = int(det.bbox_x1) - x1
        by1 = int(det.bbox_y1) - y1
        bx2 = int(det.bbox_x2) - x1
        by2 = int(det.bbox_y2) - y1
        cv2.rectangle(crop, (bx1, by1), (bx2, by2), (250, 165, 96), 2)

        _, buf = cv2.imencode(".png", crop)
        return Response(content=buf.tobytes(), media_type="image/png")
    finally:
        db.close()


@router.get("/surveys/{survey_id}/detections")
def api_survey_detections(survey_id: str):
    db = SessionLocal()
    try:
        images = db.query(SonarImage).filter(SonarImage.survey_id == survey_id).all()
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
                        "image_path": f"/api/images/{img.image_id}",
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
                "image_path": f"/api/images/{img.image_id}" if img else None,
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

        # Update or create feedback
        feedback = db.query(ExpertFeedback).filter(ExpertFeedback.detection_id == detection_id).first()
        if not feedback:
            feedback = ExpertFeedback(
                feedback_id=f"fb_{uuid.uuid4().hex[:8]}",
                detection_id=detection_id,
                expert_label=body.get("expert_label", ""),
                correction=body.get("correction"),
                comments=body.get("comments"),
                verified=1,
            )
            db.add(feedback)
        else:
            feedback.expert_label = body.get("expert_label", "")
            feedback.correction = body.get("correction")
            feedback.comments = body.get("comments")
            feedback.verified = 1

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


@router.get("/export/csv")
def api_export_csv():
    db = SessionLocal()
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Priority", "Target ID", "Detection ID", "Class", "Risk Level",
            "Risk Score", "Evidence Score", "Confidence", "Anomaly Score",
            "Latitude", "Longitude", "Depth (m)", "Verification Status"
        ])

        risks = db.query(RiskAssessment).order_by(RiskAssessment.priority).all()
        for r in risks:
            det = db.query(Detection).filter(Detection.detection_id == r.detection_id).first()
            if not det:
                continue
            img = db.query(SonarImage).filter(SonarImage.image_id == det.image_id).first()
            anom = db.query(Anomaly).filter(Anomaly.detection_id == det.detection_id).first()
            fb = db.query(ExpertFeedback).filter(ExpertFeedback.detection_id == det.detection_id).first()

            writer.writerow([
                r.priority,
                det.target_id,
                det.detection_id,
                det.object_class,
                r.risk_level,
                round(r.risk_score, 4),
                round(r.evidence_score, 4),
                round(det.confidence, 4),
                round(anom.anomaly_score, 4) if anom else "N/A",
                round(img.latitude, 6) if img and img.latitude else "N/A",
                round(img.longitude, 6) if img and img.longitude else "N/A",
                img.depth if img and img.depth else "N/A",
                fb.expert_label if fb else "Unverified"
            ])

        output.seek(0)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=sonaris_inspection_priority.csv"}
        )
    finally:
        db.close()


@router.get("/export/mission-plan")
def api_export_mission_plan():
    """
    Exports structured ROV/AUV waypoint mission inspection plan in standard JSON format.
    """
    db = SessionLocal()
    try:
        waypoints = []
        risks = db.query(RiskAssessment).order_by(RiskAssessment.priority).all()
        for i, r in enumerate(risks):
            det = db.query(Detection).filter(Detection.detection_id == r.detection_id).first()
            if not det:
                continue
            img = db.query(SonarImage).filter(SonarImage.image_id == det.image_id).first()
            if not img or not img.latitude or not img.longitude:
                continue

            waypoints.append({
                "sequence": i + 1,
                "target_id": det.target_id,
                "detection_id": det.detection_id,
                "action": "INSPECT_AND_SAMPLE" if r.risk_level == "HIGH" else "SCAN_AND_RECORD",
                "coordinates": {
                    "latitude": img.latitude,
                    "longitude": img.longitude,
                    "target_depth_m": img.depth or 30.0,
                },
                "target_class": det.object_class,
                "risk_level": r.risk_level,
                "estimated_dwell_time_mins": 25 if r.risk_level == "HIGH" else 10,
            })

        return {
            "mission_id": f"MISSION_{uuid.uuid4().hex[:6].upper()}",
            "generated_at": "2026-08-27T19:30:00Z",
            "total_waypoints": len(waypoints),
            "mission_type": "AUV_AUTONOMOUS_INTERVENTION",
            "waypoints": waypoints,
        }
    finally:
        db.close()

