"""
Kaggle Dataset Downloader & Ingestion Pipeline for Sonaris AI
Downloads 'yangyuanxu/sonar-flux-synthetic' via kagglehub,
organizes the sonar imagery, and registers it into a Sonaris AI survey mission.
"""
from pathlib import Path
import sys
import shutil
import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.models.database import init_db, SessionLocal, Survey, SonarImage, Detection, RiskAssessment
from backend.app.services.ingestion import create_survey, add_images_to_survey
from backend.app.services.pipeline import process_survey
from backend.app.config import RAW_DIR, DATA_DIR

def download_and_ingest_kaggle_dataset(limit_samples: int = 12, auto_process: bool = True):
    print("=" * 65)
    print("  SONARIS AI — KAGGLE SSS DATASET INGESTION PIPELINE")
    print("  Target Dataset: yangyuanxu/sonar-flux-synthetic")
    print("=" * 65)

    try:
        import kagglehub
    except ImportError:
        print("Installing kagglehub...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "kagglehub"])
        import kagglehub

    print("\n[1/4] Fetching latest version of 'yangyuanxu/sonar-flux-synthetic' via kagglehub...")
    dataset_path = kagglehub.dataset_download("yangyuanxu/sonar-flux-synthetic")
    print(f"  -> Downloaded to cache path: {dataset_path}")

    dataset_dir = Path(dataset_path)
    exts = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
    all_images = [p for p in dataset_dir.rglob("*") if p.suffix.lower() in exts]

    print(f"\n[2/4] Discovered {len(all_images)} side-scan sonar image files in dataset.")
    if not all_images:
        print("  Warning: No image files found in downloaded directory.")
        return

    # Select representative samples
    selected_images = all_images[:limit_samples]
    target_survey_name = "Kaggle Sonar-Flux Synthetic SSS Mission"
    dest_dir = RAW_DIR / "kaggle_sonar_flux"
    dest_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[3/4] Ingesting {len(selected_images)} sonar scan files into '{dest_dir}'...")
    copied_paths = []
    metadata = []
    
    # Real-world coordinates along Goa / Karwar deepwater survey line
    base_lat = 14.8124
    base_lon = 74.0850

    for idx, img_p in enumerate(selected_images):
        dest_filename = f"flux_sss_{idx+1:03d}{img_p.suffix.lower()}"
        dest_file = dest_dir / dest_filename
        shutil.copy2(img_p, dest_file)
        copied_paths.append(str(dest_file))

        metadata.append({
            "latitude": round(base_lat + (idx * 0.0028), 6),
            "longitude": round(base_lon + (idx * 0.0034), 6),
            "depth": round(45.0 + (idx * 2.2), 1),
            "timestamp": f"2026-08-27T11:{10 + idx*5:02d}:00Z",
        })

    init_db()
    survey_info = create_survey(
        name=target_survey_name,
        file_path=str(dest_dir),
        vessel_id="Kaggle Dataset Towfish / INS Investigator",
        area_name="Arabian Sea - Flux Deepwater Survey Grid",
        sonar_type="Synthetic Flux SSS Transceiver (Dual 400/900 kHz)",
        start_time="2026-08-27 11:00:00 UTC",
        end_time="2026-08-27 17:30:00 UTC",
    )
    survey_id = survey_info["survey_id"]
    add_images_to_survey(survey_id, copied_paths, metadata)
    print(f"  -> Created survey mission '{survey_id}' with {len(copied_paths)} images and georeferenced navigation track.")

    if auto_process:
        print(f"\n[4/4] Executing Sonaris AI Multi-Source Evidence Fusion on survey '{survey_id}'...")
        process_survey(survey_id)
        print("  -> Processing complete!")

        db = SessionLocal()
        try:
            total_dets = db.query(Detection).join(SonarImage).filter(SonarImage.survey_id == survey_id).count()
            high_risks = db.query(RiskAssessment).join(Detection).join(SonarImage).filter(
                SonarImage.survey_id == survey_id, RiskAssessment.risk_level == "HIGH"
            ).count()
            print(f"\nSurvey Results:")
            print(f"  Total Targets Detected: {total_dets}")
            print(f"  High Risk Priorities: {high_risks}")
        finally:
            db.close()

    print("\n" + "=" * 65)
    print(" KAGGLE DATASET INGESTION COMPLETED SUCCESSFULLY!")
    print(" View the results on GIS Dashboard: http://localhost:5173")
    print("=" * 65)
    return survey_id

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Download and ingest Kaggle sonar-flux-synthetic dataset")
    parser.add_argument("--samples", type=int, default=12, help="Number of samples to ingest into survey")
    parser.add_argument("--no-process", action="store_true", help="Skip automatic pipeline execution")
    args = parser.parse_args()

    download_and_ingest_kaggle_dataset(limit_samples=args.samples, auto_process=not args.no_process)
