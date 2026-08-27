import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
WEIGHTS_DIR = BASE_DIR / "backend" / "weights"
MODELS_DIR = BASE_DIR / "models"
DB_PATH = BASE_DIR / "sonaris.db"

try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
except Exception:
    CUDA_AVAILABLE = False

requested_device = os.environ.get("SONARIS_DEVICE", "auto")
if requested_device == "cpu":
    DEVICE = "cpu"
elif requested_device == "cuda":
    DEVICE = "cuda" if CUDA_AVAILABLE else "cpu"
else:  # auto
    DEVICE = "cuda" if CUDA_AVAILABLE else "cpu"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# YOLO settings
YOLO_DETECT_WEIGHTS = WEIGHTS_DIR / "yolov8n_sss.pt"
YOLO_SEG_WEIGHTS = WEIGHTS_DIR / "yolov8n_seg_sss.pt"
YOLO_CONFIDENCE = 0.25
YOLO_IMGSZ = 640

# Anomaly detection
PATCHCORE_BANK = WEIGHTS_DIR / "patchcore_bank.npy"
ANOMALY_THRESHOLD = 0.5

# Evidence fusion weights
FUSION_WEIGHTS = {
    "target": 0.25,
    "shadow": 0.20,
    "seabed": 0.15,
    "anomaly": 0.20,
    "confidence": 0.20,
}

# Risk engine weights
RISK_WEIGHTS = {
    "object_severity": 0.25,
    "anomaly_level": 0.25,
    "evidence_score": 0.25,
    "object_size": 0.10,
    "location_sensitivity": 0.15,
}

# Risk thresholds
RISK_HIGH_THRESHOLD = 0.65
RISK_MEDIUM_THRESHOLD = 0.35

# Object severity mapping
OBJECT_SEVERITY = {
    "fishing_gear": 0.8,
    "container": 0.6,
    "wreckage": 0.7,
    "artificial_object": 0.5,
    "unknown": 0.4,
}

# Preprocessing
CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_SIZE = (8, 8)
GAUSSIAN_KERNEL = (5, 5)
NORMALIZE_RANGE = (0, 255)
