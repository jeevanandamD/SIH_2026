# Sonaris AI

**AI-Powered Side-Scan Sonar Marine Debris & Underwater Anomaly Detection System**

Sonaris AI transforms raw Side-Scan Sonar (SSS) imagery into actionable underwater
intelligence. It combines AI object detection, open-set anomaly detection, acoustic
evidence fusion, risk assessment, geo-localization, and inspection prioritization
into a single decision-support pipeline.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [System Pipeline](#system-pipeline)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [Pipeline Deep Dive](#pipeline-deep-dive)
- [Database Schema](#database-schema)
- [Frontend Components](#frontend-components)
- [Scripts](#scripts)
- [Configuration](#configuration)
- [Dataset Strategy](#dataset-strategy)
- [Training Models](#training-models)
- [Known Limitations](#known-limitations)

---

## Architecture Overview

Sonaris AI is a multi-stage intelligent pipeline that goes beyond simple object
detection. Instead of relying only on a detector's confidence score, it combines
multiple sources of acoustic evidence to produce a reliable risk assessment for
every detected underwater target.

```
SIDE-SCAN SONAR IMAGE
         |
    PREPROCESSING
    (CLAHE, Denoise, Normalize)
         |
    +---------+-----------+
    |                     |
  DETECTION            ANOMALY
  (YOLOv8n)          DETECTION
    |               (PatchCore)
  SEGMENTATION           |
  (YOLOv8n-seg)          |
    |                     |
    +----------+----------+
               |
    ACOUSTIC FEATURE EXTRACTION
    (Target, Shadow, Seabed)
               |
    ACOUSTIC EVIDENCE FUSION
    (Weighted Multi-Feature Fusion)
               |
    UNCERTAINTY ESTIMATION
               |
    RISK ASSESSMENT
    (LOW / MEDIUM / HIGH)
               |
    GEO-LOCALIZATION
    (Sonar Offset -> GPS)
               |
    INSPECTION PRIORITIZATION
    (Risk-Ranked Target List)
               |
    GIS DASHBOARD
    (Interactive Map + Target Details)
```

### Core Innovation: Acoustic Evidence Fusion

The central technical contribution is not any single model, but the integration
of multiple sonar-specific evidence sources:

| Evidence Source | What It Measures |
|---|---|
| **Target Features** | Intensity, area, shape, aspect ratio |
| **Acoustic Shadow** | Shadow length, area, target-to-shadow ratio |
| **Seabed Context** | Local texture, contrast, background statistics |
| **Anomaly Score** | Deviation from known sonar patterns |
| **Detection Confidence** | YOLO prediction confidence |

These are combined via weighted fusion:

```
evidence_score = 0.25 * target_evidence
              + 0.20 * shadow_evidence
              + 0.15 * seabed_evidence
              + 0.20 * anomaly_score
              + 0.20 * detection_confidence
```

---

## System Pipeline

### 1. Preprocessing

Raw sonar images are enhanced while preserving acoustic shadow information:

- **Non-Local Means Denoising** — reduces speckle noise (h=10, templateWindowSize=7)
- **CLAHE** — contrast-limited adaptive histogram equalization (clipLimit=2.0, 8x8 tiles)
- **Min-Max Normalization** — standardize to [0, 255] range
- **Unsharp Masking** — sharpen edges via Gaussian blur + weighted addition

### 2. Object Detection

**Model:** YOLOv8-nano (640x640 input, ~1GB VRAM)

| Class | Description |
|---|---|
| `fishing_gear` | Ghost nets, abandoned fishing lines |
| `container` | Shipping containers, cargo debris |
| `wreckage` | Shipwrecks, structural debris |
| `artificial_object` | Other man-made underwater objects |

Output: bounding box, class, confidence score.

### 3. Object Segmentation

**Model:** YOLOv8n-seg (instance segmentation)

Produces pixel-level masks for each detected object, enabling precise
computation of target area, shape, and orientation.

### 4. Open-Set Anomaly Detection

**Model:** PatchCore with ResNet-18 backbone

- Learns representations of normal sonar seabed patterns
- Extracts 512-dimensional feature vectors from detection patches
- Computes minimum cosine distance to a stored memory bank
- High distance = high anomaly score = potentially unseen object

This prevents the system from forcing unknown objects into incorrect
predefined classes.

### 5. Acoustic Feature Extraction

Three categories of features are extracted for each detection:

**Target Features:**
- Mean intensity, area (pixel count), aspect ratio, orientation, perimeter

**Shadow Features:**
- Shadow length, area, width, target-to-shadow ratio
- Shadow region estimated via 45-degree offset from target centroid

**Seabed Features:**
- Local texture (standard deviation), contrast (max-min), mean background intensity
- Computed from a ring region around the target (not overlapping the target)

### 6. Acoustic Evidence Fusion

All features are normalized to [0, 1] and combined with configurable weights.
The fusion layer produces a single `evidence_score` representing the overall
acoustic reliability of the detection.

### 7. Risk Assessment

Risk score is computed from:

```
risk_score = 0.25 * object_severity    (class-specific: fishing_gear=0.8, wreckage=0.7, etc.)
           + 0.25 * anomaly_level      (anomaly score)
           + 0.25 * evidence_score     (fusion output)
           + 0.10 * object_size        (normalized target area)
           + 0.15 * location_sensitivity
```

Thresholds: **>= 0.65 = HIGH**, **>= 0.35 = MEDIUM**, **< 0.35 = LOW**

### 8. Geo-Localization

Converts sonar detection coordinates to real-world GPS positions using:
- Reference GPS position (from image metadata)
- Platform heading
- Sonar range setting
- Target offset from image center (along-track and across-track)

### 9. Inspection Prioritization

All detections across a survey are sorted by:
1. Risk level (HIGH first, then MEDIUM, then LOW)
2. Risk score (descending)
3. Evidence score (descending)

This produces an ordered inspection list for operators.

---

## Tech Stack

### Backend

| Component | Technology | Purpose |
|---|---|---|
| Framework | **FastAPI** | REST API, async support |
| Database | **SQLite** + SQLAlchemy | Data persistence |
| AI/ML | **PyTorch** + **Ultralytics** | YOLOv8 inference |
| Vision | **OpenCV** | Image preprocessing |
| Anomaly | **ResNet-18** + PatchCore | Open-set detection |

### Frontend

| Component | Technology | Purpose |
|---|---|---|
| Framework | **React 19** + TypeScript | UI |
| Build | **Vite 8** | Dev server + bundler |
| Styling | **Tailwind CSS 4** | Dark ocean theme |
| Map | **Leaflet** + react-leaflet | GIS visualization |
| Charts | **Recharts** | Score visualization |
| HTTP | **Axios** | API client |

### Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| CPU | 4 cores | 8+ cores (i5-12500H or better) |
| RAM | 8 GB | 16 GB |
| GPU | None (CPU fallback) | NVIDIA GPU with 4+ GB VRAM (RTX 3050+) |
| Storage | 5 GB | 20 GB |
| CUDA | 11.8+ | 11.8+ |

---

## Project Structure

```
SIH/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entry point, CORS, lifespan
│   │   ├── config.py               # All configuration values
│   │   ├── api/
│   │   │   └── routes.py           # 12 REST API endpoints
│   │   ├── models/
│   │   │   └── database.py         # SQLAlchemy ORM (7 tables)
│   │   └── services/
│   │       ├── preprocessing.py    # CLAHE, denoise, normalize
│   │       ├── detection.py        # YOLOv8n object detection
│   │       ├── segmentation.py     # YOLOv8n-seg instance segmentation
│   │       ├── anomaly.py          # PatchCore anomaly detection
│   │       ├── acoustic_features.py # Target/shadow/seabed extraction
│   │       ├── evidence_fusion.py  # Weighted evidence fusion
│   │       ├── risk_engine.py      # Risk scoring
│   │       ├── geo_localization.py # Sonar-to-GPS conversion
│   │       ├── prioritization.py   # Risk-ranked inspection order
│   │       ├── ingestion.py        # Survey/image CRUD
│   │       └── pipeline.py         # Full pipeline orchestrator
│   ├── weights/                    # Model weight files (.pt, .npy)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx                 # Router, page layout
│   │   ├── api/client.ts           # Axios API client
│   │   ├── types/index.ts          # TypeScript interfaces
│   │   ├── components/
│   │   │   ├── MapView.tsx         # Leaflet map with risk markers
│   │   │   ├── TargetPanel.tsx     # Detection detail sidebar
│   │   │   ├── PriorityQueue.tsx   # Ranked inspection list
│   │   │   ├── VerifyDialog.tsx    # Expert verification modal
│   │   │   ├── SonarOverlay.tsx    # Sonar image viewer
│   │   │   └── Heatmap.tsx         # Anomaly heatmap overlay
│   │   └── pages/
│   │       ├── Dashboard.tsx       # Main GIS view
│   │       └── SurveyView.tsx      # Survey management
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
├── data/
│   ├── raw/                        # Raw sonar images
│   ├── processed/                  # Preprocessed images
│   └── sample_survey/              # Demo survey data
├── scripts/
│   ├── run_pipeline.py             # Run full pipeline on demo data
│   ├── preprocess_data.py          # Batch preprocess sonar images
│   └── train_yolo.py               # Train detection/segmentation models
├── models/                         # Training outputs (weights, logs)
├── sonaris.db                      # SQLite database (auto-created)
├── SONARISAI.md                    # Full architecture document
├── SONARISAI_speakerNotes.md       # SIH presentation speaker notes
└── IMPLEMENTATION_PLAN.md          # Development implementation plan
```

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm
- **CUDA 11.8+** (optional, for GPU acceleration)
- **Git**

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/sonaris-ai.git
cd sonaris-ai
```

### 2. Backend Setup

```bash
# Create conda environment
conda create -n sonaris python=3.10
conda activate sonaris

# Install PyTorch with CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Install backend dependencies
pip install -r backend/requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

### 4. Download Model Weights (if available)

Place the following files in `backend/weights/`:

| File | Description |
|---|---|
| `yolov8n_sss.pt` | Custom-trained YOLOv8n detection model |
| `yolov8n_seg_sss.pt` | Custom-trained YOLOv8n-seg segmentation model |
| `patchcore_bank.npy` | PatchCore memory bank (normal seabed features) |

If custom weights are not available, the system falls back to:
- `yolov8n.pt` (auto-downloaded by Ultralytics)
- `yolov8n-seg.pt` (auto-downloaded by Ultralytics)
- Anomaly detection returns a neutral 0.5 score

### 5. Prepare Demo Data

Place sonar images (PNG/JPG) in `data/raw/demo_survey/`.

If you have metadata (GPS, depth, heading), create a `metadata.json`:

```json
[
  {
    "latitude": 12.9716,
    "longitude": 77.5946,
    "depth": 15.0,
    "heading": 45.0,
    "sonar_range": 100.0
  }
]
```

---

## Running the Application

### Development Mode

**Terminal 1 — Backend:**

```bash
conda activate sonaris
uvicorn backend.app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

### Run the Pipeline via CLI

```bash
# Process demo survey (images in data/raw/demo_survey/)
python scripts/run_pipeline.py --action demo

# Just load images without processing
python scripts/run_pipeline.py --action load
```

### Run Preprocessing

```bash
python scripts/preprocess_data.py --raw data/raw --output data/processed
```

---

## API Reference

All endpoints are prefixed with `/api`.

### Surveys

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/surveys` | List all surveys |
| `POST` | `/api/surveys` | Create survey (multipart: `file`, `name`) |
| `GET` | `/api/surveys/{id}` | Get survey details |
| `POST` | `/api/surveys/{id}/process` | Run full AI pipeline |
| `GET` | `/api/surveys/{id}/detections` | Get all detections for survey |

### Detections

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/detections/{id}` | Get full target record (detection + anomaly + features + risk) |
| `POST` | `/api/detections/{id}/verify` | Submit expert verification |

### Targets

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/targets/geojson` | GeoJSON FeatureCollection for map rendering |
| `GET` | `/api/targets/priority` | Priority-ranked inspection list |
| `GET` | `/api/targets/heatmap` | Heatmap data points (anomaly intensities) |

### System

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/stats` | Dashboard statistics |
| `GET` | `/` | Health check / version info |

### Example: Process a Survey

```bash
curl -X POST http://localhost:8000/api/surveys/survey_abc123/process
# Response: {"status": "completed"}
```

### Example: Get GeoJSON

```bash
curl http://localhost:8000/api/targets/geojson
# Response: {"type": "FeatureCollection", "features": [...]}
```

### Example: Verify a Detection

```bash
curl -X POST http://localhost:8000/api/detections/AS_000001/verify \
  -H "Content-Type: application/json" \
  -d '{"expert_label": "marine_debris", "comments": "Confirmed ghost net"}'
# Response: {"feedback_id": "fb_abc123", "status": "verified"}
```

---

## Pipeline Deep Dive

### Per-Image Processing Flow

For each sonar image in a survey:

```
Raw Image (BGR/Grayscale)
    |
    v
[1] Preprocess
    - Convert to grayscale
    - Non-local means denoising
    - CLAHE contrast enhancement
    - Min-max normalization
    - Unsharp mask sharpening
    |
    v
[2] Object Detection (YOLOv8n)
    - Input: enhanced image
    - Output: list of {bbox, confidence, class_name}
    |
    v
[3] Instance Segmentation (YOLOv8n-seg)
    - Input: enhanced image
    - Output: binary mask per detection
    |
    v
[4] Anomaly Scoring (PatchCore)
    - Input: cropped detection patch
    - Process: ResNet-18 feature extraction -> distance to memory bank
    - Output: anomaly_score [0.0 - 1.0]
    |
    v
[5] Acoustic Feature Extraction
    - Target: intensity, area, aspect_ratio, orientation
    - Shadow: length, area, width, target/shadow ratio
    - Seabed: texture (std), contrast (max-min), mean
    |
    v
[6] Evidence Fusion
    - Input: target_evidence, shadow_evidence, seabed_evidence,
             anomaly_score, detection_confidence
    - Output: evidence_score [0.0 - 1.0]
    |
    v
[7] Risk Assessment
    - Input: object_severity, anomaly_level, evidence_score,
             object_size, location_sensitivity
    - Output: risk_score, risk_level (LOW/MEDIUM/HIGH)
    |
    v
[8] Geo-Localization
    - Input: bbox center, reference GPS, heading, sonar_range
    - Output: latitude, longitude, depth
    |
    v
[9] Store all results in SQLite
```

### Post-Image Processing

After all images in a survey are processed:

```
All detections across all images
    |
    v
[10] Inspection Prioritization
     - Sort by: risk_level > risk_score > evidence_score
     - Assign priority numbers (1, 2, 3, ...)
     - Update risk_assessments.priority in DB
```

---

## Database Schema

SQLite database stored at project root as `sonaris.db`.

### Entity Relationship Diagram

```
Survey (1) ----< (N) SonarImage
SonarImage (1) ----< (N) Detection
Detection (1) ---- (1) Anomaly
Detection (1) ---- (1) AcousticFeatures
Detection (1) ---- (1) RiskAssessment
Detection (1) ---- (1) ExpertFeedback
```

### Tables

**surveys** — Survey metadata
| Column | Type | Description |
|---|---|---|
| survey_id | TEXT PK | Unique identifier |
| name | TEXT | Survey name |
| status | TEXT | uploaded / processing / completed / failed |
| vessel_id | TEXT | Optional vessel identifier |
| area_name | TEXT | Survey area name |
| sonar_type | TEXT | Sonar device type |

**sonar_images** — Individual sonar images
| Column | Type | Description |
|---|---|---|
| image_id | TEXT PK | Unique identifier |
| survey_id | TEXT FK | Parent survey |
| image_path | TEXT | File path on disk |
| latitude | REAL | GPS latitude |
| longitude | REAL | GPS longitude |
| depth | REAL | Depth in meters |

**detections** — Detected objects
| Column | Type | Description |
|---|---|---|
| detection_id | TEXT PK | e.g. AS_000001 |
| target_id | TEXT | e.g. T_A1B2C3 |
| object_class | TEXT | fishing_gear / container / wreckage / artificial_object |
| confidence | REAL | YOLO confidence [0-1] |
| bbox_x1/y1/x2/y2 | REAL | Bounding box coordinates |

**anomalies** — Anomaly scores
| Column | Type | Description |
|---|---|---|
| anomaly_score | REAL | [0-1], higher = more anomalous |
| uncertainty | REAL | |score - 0.5| * 2 |

**acoustic_features** — Sonar-specific features
| Column | Type | Description |
|---|---|---|
| target_intensity | REAL | Mean pixel value in target region |
| target_area | REAL | Target mask pixel count |
| shadow_area | REAL | Shadow region pixel count |
| shadow_length | REAL | Shadow extent in pixels |
| target_shadow_ratio | REAL | target_area / shadow_area |
| seabed_texture | REAL | Background standard deviation |
| seabed_contrast | REAL | Background max - min |

**risk_assessments** — Risk and priority
| Column | Type | Description |
|---|---|---|
| evidence_score | REAL | Fused evidence score [0-1] |
| risk_score | REAL | Combined risk score [0-1] |
| risk_level | TEXT | HIGH / MEDIUM / LOW |
| priority | INTEGER | Inspection rank (1 = highest) |

**expert_feedback** — Human verification
| Column | Type | Description |
|---|---|---|
| expert_label | TEXT | correct / incorrect / marine_debris / wreckage / etc. |
| correction | TEXT | Corrected classification |
| comments | TEXT | Free-text notes |

---

## Frontend Components

### Pages

| Page | Route | Description |
|---|---|---|
| **Dashboard** | `/` | Main GIS view with full-screen Leaflet map, stats bar, priority queue sidebar, target detail panel |
| **SurveyView** | `/surveys` | Upload sonar data, view survey list, trigger processing |

### Components

| Component | Description |
|---|---|
| **MapView** | Leaflet map with CARTO dark basemap. Risk-colored markers (red=HIGH, amber=MEDIUM, green=LOW). Pulse animation on HIGH-risk markers. Fly-to animation on selection. Popups with target details. |
| **TargetPanel** | Right sidebar showing full target record: risk badge, score progress bars, acoustic features grid, Recharts horizontal bar chart, GPS coordinates, depth. Action buttons: View Sonar, Verify. |
| **PriorityQueue** | Scrollable ranked list of all detected targets sorted by inspection priority. Shows priority number, target ID, risk badge, class, confidence %, evidence %. |
| **VerifyDialog** | Modal for expert verification. 6 classification options: Correct, Incorrect, Natural Feature, Marine Debris, Wreckage, New Category. Conditional correction input for incorrect/new. Optional comments. |
| **SonarOverlay** | Full-screen modal displaying the sonar image with bounding box overlay, target metadata, and bbox coordinates. |
| **Heatmap** | Toggleable overlay of CircleMarkers on the map, sized and colored by anomaly intensity. |

### Theme

The frontend uses a dark ocean theme with custom CSS variables:

| Variable | Color | Usage |
|---|---|---|
| `--color-ocean-900` | `#0a1628` | Page background |
| `--color-ocean-800` | `#0f2035` | Panel backgrounds |
| `--color-ocean-700` | `#152d4a` | Borders |
| `--color-ocean-400` | `#3b7dd8` | Interactive elements |
| `--color-risk-high` | `#ef4444` | High risk |
| `--color-risk-medium` | `#f59e0b` | Medium risk |
| `--color-risk-low` | `#22c55e` | Low risk |

---

## Scripts

### `run_pipeline.py`

Run the full AI pipeline on demo data.

```bash
# Process images in data/raw/demo_survey/
python scripts/run_pipeline.py --action demo

# Load images into a survey without processing
python scripts/run_pipeline.py --action load
```

### `preprocess_data.py`

Batch preprocess sonar images through the enhancement pipeline.

```bash
python scripts/preprocess_data.py --raw data/raw --output data/processed
```

### `train_yolo.py`

Train YOLOv8 models on custom sonar data.

```bash
# Train both detection and segmentation
python scripts/train_yolo.py --data path/to/data.yaml --epochs 100

# Train detection only
python scripts/train_yolo.py --data path/to/data.yaml --mode detect --epochs 50

# Train with smaller image size (for 4GB VRAM GPUs)
python scripts/train_yolo.py --data path/to/data.yaml --imgsz 416 --batch 2
```

Training uses:
- Mixed precision (AMP) to halve VRAM usage
- Early stopping (patience=20)
- Best weights automatically copied to `backend/weights/`

---

## Configuration

All configuration is in `backend/app/config.py`. Key values:

| Setting | Default | Description |
|---|---|---|
| `DEVICE` | `"cuda"` | Compute device. Set `SONARIS_DEVICE=cpu` for CPU mode |
| `YOLO_CONFIDENCE` | `0.25` | Minimum detection confidence threshold |
| `YOLO_IMGSZ` | `640` | YOLO input image size |
| `ANOMALY_THRESHOLD` | `0.5` | Anomaly score threshold |
| `RISK_HIGH_THRESHOLD` | `0.65` | Risk score >= this = HIGH |
| `RISK_MEDIUM_THRESHOLD` | `0.35` | Risk score >= this = MEDIUM |
| `CLAHE_CLIP_LIMIT` | `2.0` | CLAHE contrast enhancement limit |
| `FUSION_WEIGHTS` | See below | Evidence fusion coefficients |
| `RISK_WEIGHTS` | See below | Risk scoring coefficients |

### Evidence Fusion Weights

```python
FUSION_WEIGHTS = {
    "target":     0.25,  # Target feature evidence
    "shadow":     0.20,  # Acoustic shadow evidence
    "seabed":     0.15,  # Seabed context evidence
    "anomaly":    0.20,  # Anomaly detection score
    "confidence": 0.20,  # YOLO detection confidence
}
```

### Risk Engine Weights

```python
RISK_WEIGHTS = {
    "object_severity":      0.25,  # Class-specific severity
    "anomaly_level":        0.25,  # Anomaly score
    "evidence_score":       0.25,  # Fused evidence
    "object_size":          0.10,  # Normalized target area
    "location_sensitivity": 0.15,  # Environmental sensitivity
}
```

### Object Severity Mapping

| Class | Severity |
|---|---|
| fishing_gear | 0.8 |
| wreckage | 0.7 |
| container | 0.6 |
| artificial_object | 0.5 |
| unknown | 0.4 |

---

## Dataset Strategy

### Labeled Data (for Detection/Segmentation)

- Existing sample sonar images (manually annotated in YOLO format)
- Public SSS datasets (Kaggle shipwreck detection, NOAA ocean sonar archives)
- Custom annotations using Label Studio or CVAT

### Unlabeled Data (for Anomaly Detection)

- Normal seabed sonar patches (no objects present)
- Used to build the PatchCore memory bank
- Should represent diverse seabed types (sandy, rocky, muddy)

### YOLO Annotation Format

```
class_id  center_x  center_y  width  height
```

Classes: `0`=fishing_gear, `1`=container, `2`=wreckage, `3`=artificial_object

### Data Augmentation

For small datasets, use aggressive augmentation:
- Random rotation (0-360 degrees)
- Horizontal/vertical flipping
- Gaussian noise injection
- Brightness/contrast variation
- Random crop and resize

---

## Training Models

### Training on RTX 3050 (4GB VRAM)

```bash
python scripts/train_yolo.py \
  --data data.yaml \
  --epochs 100 \
  --imgsz 640 \
  --batch 4
```

If you encounter CUDA OOM:
```bash
python scripts/train_yolo.py \
  --data data.yaml \
  --epochs 100 \
  --imgsz 416 \
  --batch 2
```

### Training on CPU (no GPU)

Set `SONARIS_DEVICE=cpu` and use smaller batch size. Training will be
significantly slower (10-50x) but functional.

### Evaluation Metrics

| Task | Metrics |
|---|---|
| Detection | mAP@50, mAP@50:95, Precision, Recall, F1 |
| Segmentation | IoU, Dice Score |
| Anomaly Detection | AUROC, AUPR, False Positive Rate |
| Full Pipeline | Localization Error, Inference Latency, Risk Ranking Quality |

---

## Known Limitations

1. **No custom-trained weights included** — falls back to generic YOLOv8n which
   is not trained on sonar data. Detection accuracy will be lower until custom
   models are trained.

2. **Anomaly detection returns 0.5** without a pre-built memory bank. Run
   `patchcore_bank.npy` generation on normal seabed data first.

3. **Synchronous pipeline processing** — large surveys may take several minutes.
   The API blocks until processing completes.

4. **SQLite limitations** — single-writer, no concurrent processing of multiple
   surveys. Suitable for demo/prototype, not production scale.

5. **No authentication** — all endpoints are publicly accessible. Fine for
   local demo, not for production deployment.

6. **Geo-localization assumes flat seafloor** — no bathymetric correction.
   Accuracy degrades with depth and sonar range.

7. **Shadow detection is approximate** — uses a fixed 45-degree offset model.
   Real shadow geometry depends on sonar altitude and target height.

8. **No real-time streaming** — processes static images, not live sonar feeds.

---

## License

This project was developed for Smart India Hackathon (SIH).

---

## Acknowledgments

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) for object detection
- [PatchCore](https://github.com/amazon-science/patchcore-inspection) for anomaly detection
- [Leaflet](https://leafletjs.com/) for GIS visualization
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
