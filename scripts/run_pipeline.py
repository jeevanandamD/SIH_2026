from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.models.database import init_db, SessionLocal, Survey, SonarImage, Detection, Anomaly, AcousticFeatures, RiskAssessment
from backend.app.services.ingestion import create_survey, add_images_to_survey, list_surveys
from backend.app.services.pipeline import process_survey
from backend.app.config import RAW_DIR


from backend.app.services.synthetic_sonar import generate_synthetic_sonar_image
import cv2


def create_demo_survey():
    init_db()

    survey_dir = RAW_DIR / "demo_survey"
    survey_dir.mkdir(parents=True, exist_ok=True)

    images = list(survey_dir.glob("*.png")) + list(survey_dir.glob("*.jpg"))
    if not images:
        print(f"Synthesizing 4 dual-channel SSS demo images in {survey_dir}...")
        for idx in range(4):
            img, _ = generate_synthetic_sonar_image(width=640, height=640, nadir_width=44)
            out_file = survey_dir / f"sonar_scan_{idx+1:02d}.png"
            cv2.imwrite(str(out_file), img)
        images = list(survey_dir.glob("*.png"))

    result = create_survey(
        name="Demo Autonomous SSS Survey",
        file_path=str(survey_dir),
        vessel_id="AUV Sentinel-1",
        area_name="Goa Offshore Debris Field",
        sonar_type="EdgeTech 4200 (400/900 kHz)",
    )
    survey_id = result["survey_id"]

    metadata = []
    base_lat, base_lon = 15.4208, 73.7845
    for idx in range(len(images)):
        metadata.append({
            "latitude": base_lat + (idx * 0.003),
            "longitude": base_lon + (idx * 0.003),
            "depth": 38.0 + (idx * 1.5),
            "timestamp": f"2026-08-27T10:{idx*15:02d}:00Z",
        })

    add_images_to_survey(survey_id, [str(img) for img in images], metadata)
    print(f"Created survey {survey_id} with {len(images)} images")

    print("Processing multi-source evidence fusion pipeline...")
    process_survey(survey_id)
    print(f"Survey {survey_id} processing completed successfully!")

    db = SessionLocal()
    try:
        det_count = db.query(Detection).count()
        risk_count = db.query(RiskAssessment).count()
        high_risk = db.query(RiskAssessment).filter(RiskAssessment.risk_level == "HIGH").count()
        med_risk = db.query(RiskAssessment).filter(RiskAssessment.risk_level == "MEDIUM").count()
        print(f"\nPipeline Results Summary:")
        print(f"  Total Detections: {det_count}")
        print(f"  Risk Assessments: {risk_count}")
        print(f"  High Risk (Critical Priority): {high_risk}")
        print(f"  Medium Risk: {med_risk}")
    finally:
        db.close()


def load_sample_data():
    init_db()

    survey_dir = RAW_DIR / "sample_survey"
    survey_dir.mkdir(parents=True, exist_ok=True)

    images = list(survey_dir.glob("*.png")) + list(survey_dir.glob("*.jpg"))
    if not images:
        print(f"No images in {survey_dir}")
        return

    result = create_survey("Sample Survey")
    survey_id = result["survey_id"]
    add_images_to_survey(survey_id, [str(img) for img in images])
    print(f"Loaded {len(images)} images into survey {survey_id}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Sonaris AI pipeline")
    parser.add_argument("--action", choices=["demo", "load"], default="demo")
    args = parser.parse_args()

    if args.action == "demo":
        create_demo_survey()
    else:
        load_sample_data()
