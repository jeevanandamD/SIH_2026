import os
import uuid
import json
from pathlib import Path
from ..models.database import SessionLocal, Survey, SonarImage, Detection


def create_survey(
    name: str,
    file_path: str | None = None,
    vessel_id: str | None = "INS Nireekshak / Survey AUV-1",
    area_name: str | None = "Arabian Sea - Offshore Sector 4",
    sonar_type: str | None = "EdgeTech 4200 Dual-Frequency SSS (400/900 kHz)",
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict:
    db = SessionLocal()
    try:
        survey_id = f"survey_{uuid.uuid4().hex[:8]}"
        survey = Survey(
            survey_id=survey_id,
            name=name,
            vessel_id=vessel_id,
            area_name=area_name,
            sonar_type=sonar_type,
            start_time=start_time or "2026-08-27 08:30:00 UTC",
            end_time=end_time or "2026-08-27 14:45:00 UTC",
            status="uploaded",
        )
        db.add(survey)
        db.commit()
        return {
            "survey_id": survey_id,
            "name": name,
            "vessel_id": vessel_id,
            "area_name": area_name,
            "sonar_type": sonar_type,
            "status": "uploaded",
        }
    finally:
        db.close()


def add_images_to_survey(survey_id: str, image_paths: list[str], metadata: list[dict] | None = None) -> list[dict]:
    db = SessionLocal()
    try:
        added = []
        for i, path in enumerate(image_paths):
            meta = metadata[i] if metadata and i < len(metadata) else {}
            image_id = f"img_{uuid.uuid4().hex[:8]}"
            img = SonarImage(
                image_id=image_id,
                survey_id=survey_id,
                image_path=path,
                timestamp=meta.get("timestamp"),
                latitude=meta.get("latitude"),
                longitude=meta.get("longitude"),
                depth=meta.get("depth"),
            )
            db.add(img)
            added.append({"image_id": image_id, "image_path": path})
        db.commit()
        return added
    finally:
        db.close()


def get_survey_images(survey_id: str) -> list[dict]:
    db = SessionLocal()
    try:
        images = db.query(SonarImage).filter(SonarImage.survey_id == survey_id).all()
        return [
            {
                "image_id": img.image_id,
                "image_path": img.image_path,
                "latitude": img.latitude,
                "longitude": img.longitude,
                "depth": img.depth,
                "timestamp": img.timestamp,
            }
            for img in images
        ]
    finally:
        db.close()


def list_surveys() -> list[dict]:
    db = SessionLocal()
    try:
        surveys = db.query(Survey).all()
        result = []
        for s in surveys:
            images = db.query(SonarImage).filter(SonarImage.survey_id == s.survey_id).all()
            image_ids = [img.image_id for img in images]
            detection_count = db.query(Detection).filter(Detection.image_id.in_(image_ids)).count() if image_ids else 0

            result.append({
                "survey_id": s.survey_id,
                "name": s.name,
                "vessel_id": s.vessel_id,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "area_name": s.area_name,
                "sonar_type": s.sonar_type,
                "status": s.status,
                "image_count": len(images),
                "detection_count": detection_count,
            })
        return result
    finally:
        db.close()


def get_survey(survey_id: str) -> dict | None:
    db = SessionLocal()
    try:
        survey = db.query(Survey).filter(Survey.survey_id == survey_id).first()
        if not survey:
            return None
        images = db.query(SonarImage).filter(SonarImage.survey_id == survey_id).all()
        image_ids = [img.image_id for img in images]
        detection_count = db.query(Detection).filter(Detection.image_id.in_(image_ids)).count() if image_ids else 0
        return {
            "survey_id": survey.survey_id,
            "name": survey.name,
            "vessel_id": survey.vessel_id,
            "start_time": survey.start_time,
            "end_time": survey.end_time,
            "area_name": survey.area_name,
            "sonar_type": survey.sonar_type,
            "status": survey.status,
            "image_count": len(images),
            "detection_count": detection_count,
        }
    finally:
        db.close()


def update_survey_status(survey_id: str, status: str):
    db = SessionLocal()
    try:
        survey = db.query(Survey).filter(Survey.survey_id == survey_id).first()
        if survey:
            survey.status = status
            db.commit()
    finally:
        db.close()
