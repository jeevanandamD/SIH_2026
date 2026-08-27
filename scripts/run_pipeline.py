from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.models.database import init_db, SessionLocal, Survey, SonarImage, Detection, Anomaly, AcousticFeatures, RiskAssessment
from backend.app.services.ingestion import create_survey, add_images_to_survey, list_surveys
from backend.app.services.pipeline import process_survey
from backend.app.config import RAW_DIR


def create_demo_survey():
    init_db()

    survey_dir = RAW_DIR / "demo_survey"
    survey_dir.mkdir(parents=True, exist_ok=True)

    images = list(survey_dir.glob("*.png")) + list(survey_dir.glob("*.jpg"))
    if not images:
        print(f"No images found in {survey_dir}")
        print("Please add sonar images to data/raw/demo_survey/")
        return

    result = create_survey("Demo Survey", str(survey_dir))
    survey_id = result["survey_id"]

    add_images_to_survey(survey_id, [str(img) for img in images])
    print(f"Created survey {survey_id} with {len(images)} images")

    print("Processing survey...")
    process_survey(survey_id)
    print(f"Survey {survey_id} completed!")

    db = SessionLocal()
    try:
        det_count = db.query(Detection).count()
        risk_count = db.query(RiskAssessment).count()
        high_risk = db.query(RiskAssessment).filter(RiskAssessment.risk_level == "HIGH").count()
        print(f"\nResults:")
        print(f"  Detections: {det_count}")
        print(f"  Risk assessments: {risk_count}")
        print(f"  High risk: {high_risk}")
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
