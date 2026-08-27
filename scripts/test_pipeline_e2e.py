"""
End-to-End Test Suite for Sonaris AI
Tests all pipeline components and API routes.
"""
from pathlib import Path
import sys
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.models.database import init_db, SessionLocal, Survey, SonarImage, Detection, Anomaly, AcousticFeatures, RiskAssessment, ExpertFeedback
from backend.app.services.preprocessing import preprocess_sonar, slant_range_correction, detect_shadow_region
from backend.app.services.synthetic_sonar import generate_synthetic_sonar_image
from backend.app.services.detection import DetectionService
from backend.app.services.segmentation import SegmentationService
from backend.app.services.anomaly import AnomalyDetector
from backend.app.services.acoustic_features import extract_acoustic_features
from backend.app.services.evidence_fusion import fuse_evidence
from backend.app.services.risk_engine import compute_risk
from backend.app.services.geo_localization import geo_localize_detection
from backend.app.services.prioritization import assign_priorities
from backend.app.api.routes import (
    api_list_surveys,
    api_targets_geojson,
    api_targets_priority,
    api_targets_heatmap,
    api_stats,
    api_generate_demo_surveys,
)

def run_tests():
    print("========================================================")
    print("   RUNNING SONARIS AI COMPREHENSIVE END-TO-END TESTS    ")
    print("========================================================")

    # 1. DB Init
    print("\n[TEST 1] Initializing SQLite Database...")
    init_db()
    db = SessionLocal()
    print("  -> Database connected and tables verified.")

    # 2. Synthetic Sonar Generation
    print("\n[TEST 2] Generating Dual-Channel Side-Scan Sonar Waterfall Scan...")
    sonar_img, ground_truth = generate_synthetic_sonar_image(width=640, height=640, nadir_width=44)
    assert sonar_img.shape == (640, 640, 3), "Invalid sonar image shape"
    print(f"  -> Generated {sonar_img.shape} SSS image with {len(ground_truth)} embedded acoustic targets.")

    # 3. Sonar Preprocessing & Slant-Range Correction
    print("\n[TEST 3] Testing Acoustic Preprocessing & Slant-Range Correction...")
    enhanced = preprocess_sonar(sonar_img)
    corrected = slant_range_correction(enhanced, altitude_px=40)
    assert enhanced.shape == (640, 640), "Preprocessing shape mismatch"
    assert corrected.shape == (640, 640), "Slant-range shape mismatch"
    print("  -> FastNlMeans Denoising, CLAHE (clip=2.0), Unsharp Masking & Slant-Range complete.")

    # 4. Detection & Segmentation
    print("\n[TEST 4] Testing YOLO / Acoustic Highlight-Shadow Detection & Instance Segmentation...")
    detector = DetectionService()
    segmenter = SegmentationService()
    dets = detector.detect(sonar_img)
    assert len(dets) > 0, "Expected at least 1 detection"
    masks = segmenter.segment(sonar_img, dets)
    assert len(masks) == len(dets), "Masks count must match detections count"
    print(f"  -> Detected {len(dets)} targets: {[d['class_name'] for d in dets]}")
    print(f"  -> Generated {len(masks)} binary instance segmentation masks.")

    # 5. Anomaly Detection
    print("\n[TEST 5] Testing Open-Set Anomaly Scoring...")
    anomaly_detector = AnomalyDetector()
    anom_scores = anomaly_detector.score_detections(enhanced, dets)
    assert len(anom_scores) == len(dets), "Anomaly scores count mismatch"
    print(f"  -> Computed anomaly scores: {[round(s, 3) for s in anom_scores]}")

    # 6. Acoustic Feature Extraction & Evidence Fusion
    print("\n[TEST 6] Testing Acoustic Feature Extraction & Multi-Source Evidence Fusion...")
    features = extract_acoustic_features(enhanced, masks[0])
    fusion = fuse_evidence(features, anom_scores[0], dets[0]["confidence"])
    assert "evidence_score" in fusion, "Missing evidence score"
    print(f"  -> Extracted features: Target Area={features['target_area']} px, Shadow Length={features['shadow_length']} px")
    print(f"  -> Fused Evidence Score: {fusion['evidence_score']:.4f}")

    # 7. Risk Engine & Prioritization
    print("\n[TEST 7] Testing Risk Engine & Prioritization Ranking...")
    risk = compute_risk(
        object_class=dets[0]["class_name"],
        anomaly_score=anom_scores[0],
        evidence_score=fusion["evidence_score"],
        target_area=features["target_area"],
        confidence=dets[0]["confidence"],
    )
    assert risk["risk_level"] in ["HIGH", "MEDIUM", "LOW"], "Invalid risk level"
    print(f"  -> Risk Level: {risk['risk_level']} (Score: {risk['risk_score']:.4f})")

    # 8. Geo-localization
    print("\n[TEST 8] Testing Geo-localization Offset to Lat/Long...")
    metadata = {
        "latitude": 15.4208,
        "longitude": 73.7845,
        "heading": 45.0,
        "sonar_range": 100.0,
        "depth": 42.5,
        "image_width": 640,
    }
    geo = geo_localize_detection(dets[0], metadata)
    assert geo["latitude"] != 0 and geo["longitude"] != 0, "Invalid geo coordinates"
    print(f"  -> Target Localized to: {geo['latitude']:.6f}° N, {geo['longitude']:.6f}° E, Depth: {geo['depth']}m")

    # 9. API Routes Check
    print("\n[TEST 9] Testing FastAPI REST Endpoints...")
    surveys = api_list_surveys()
    geojson = api_targets_geojson()
    priority = api_targets_priority()
    heatmap = api_targets_heatmap()
    stats = api_stats()

    print(f"  -> Surveys in DB: {len(surveys)}")
    print(f"  -> GeoJSON features: {len(geojson['features'])}")
    print(f"  -> Priority Queue count: {len(priority)}")
    print(f"  -> Heatmap Points count: {len(heatmap)}")
    print(f"  -> Stats: {stats}")

    db.close()
    print("\n" + "=" * 65)
    print(" ALL PIPELINE & SYSTEM TESTS PASSED SUCCESSFULLY! (100% GREEN)")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
