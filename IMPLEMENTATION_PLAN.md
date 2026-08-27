# SONARIS AI — Implementation Plan

## System Requirements & Hardware Constraints

| Component | Spec | Implication |
|---|---|---|
| CPU | Intel Core i5-12500H (12c/16t) | Good for preprocessing & classical ML |
| RAM | 16GB DDR4 3200MHz | Adequate for MVP; avoid loading everything at once |
| GPU | NVIDIA RTX 3050 Laptop (**4GB VRAM**) | **Main bottleneck** — must use nano/small models |
| Storage | ~164GB free on D: | Manageable; keep datasets under ~20GB |
| OS | Windows 11 Home x64 | Use conda/venv, CUDA 11.8+ |

**Critical constraint:** 4GB VRAM rules out YOLOv8-medium/large, RT-DETR,
Mask R-CNN, SegFormer, and large autoencoders. All models must be
nano/small variants.

---

## Team & Timeline

| Person | Role | Focus |
|---|---|---|
| Person 1 | AI/ML Engineer | Dataset prep, model training, inference pipeline, evidence fusion |
| Person 2 | Backend Dev | FastAPI, pipeline orchestration, API endpoints, database |
| Person 3 | Frontend Dev | React GIS dashboard, Leaflet map, target panels |

**Total time:** 48-72 hours
**Priority:** Working end-to-end pipeline from sonar image to GIS dashboard

---

## Project Structure

```
D:\Hackathon\SIH\SIH\
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry
│   │   ├── config.py                # Settings
│   │   ├── models/                  # DB models (SQLAlchemy)
│   │   ├── api/                     # Route handlers
│   │   ├── services/
│   │   │   ├── ingestion.py         # Data ingestion
│   │   │   ├── preprocessing.py     # SSS preprocessing
│   │   │   ├── detection.py         # YOLO detection
│   │   │   ├── segmentation.py      # YOLO-Seg
│   │   │   ├── anomaly.py           # Open-set anomaly
│   │   │   ├── acoustic_features.py # Target/shadow/seabed features
│   │   │   ├── evidence_fusion.py   # Acoustic evidence fusion
│   │   │   ├── risk_engine.py       # Risk scoring
│   │   │   ├── geo_localization.py  # GPS mapping
│   │   │   └── prioritization.py    # Inspection ranking
│   │   └── utils/
│   ├── weights/                     # Model weights (.pt files)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx        # Main GIS view
│   │   │   ├── SurveyView.tsx       # Survey management
│   │   │   └── TargetDetail.tsx     # Per-target info
│   │   ├── components/
│   │   │   ├── MapView.tsx          # Leaflet map
│   │   │   ├── SonarOverlay.tsx     # Sonar image overlay
│   │   │   ├── Heatmap.tsx          # Anomaly heatmap
│   │   │   ├── TargetPanel.tsx      # Target info sidebar
│   │   │   ├── PriorityQueue.tsx    # Priority list
│   │   │   └── VerifyDialog.tsx     # Human verification
│   │   ├── api/                     # API client
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
├── data/
│   ├── raw/                         # Raw sonar images
│   ├── processed/                   # Preprocessed crops
│   └── sample_survey/               # Demo survey with metadata
├── models/                          # Trained model artifacts
├── scripts/
│   ├── download_datasets.py
│   ├── preprocess_data.py
│   ├── train_yolo.py
│   └── run_pipeline.py              # Full pipeline demo
├── docker-compose.yml
├── SONARISAI.md                     # Architecture document
└── IMPLEMENTATION_PLAN.md           # This file
```

---

## Phase 0: Project Setup & Environment (2 hours)

### Tasks
- [ ] Create project directory structure
- [ ] Set up Python environment (conda recommended):
  ```bash
  conda create -n sonaris python=3.10
  conda activate sonaris
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
  pip install ultralytics opencv-python fastapi uvicorn sqlalchemy pydantic pillow numpy scikit-learn
  ```
- [ ] Set up frontend:
  ```bash
  npm create vite@latest frontend -- --template react-ts
  cd frontend
  npm install tailwindcss @tailwindcss/vite
  npm install react-leaflet leaflet @types/leaflet
  npm install @turf/turf recharts axios
  ```
- [ ] Initialize git repo, create `.gitignore`
- [ ] Verify CUDA is accessible: `python -c "import torch; print(torch.cuda.is_available())"`

### Notes
- PyTorch with CUDA 11.8 is the correct version for RTX 3050
- If CUDA fails, fall back to CPU mode (slower but works)
- `ultralytics` installs YOLOv8 automatically

---

## Phase 1: Dataset Preparation (4 hours)

### Data Sources

| Source | Type | Access |
|---|---|---|
| Existing sample data | SSS images + metadata | Already have |
| Kaggle SSS datasets | Labeled sonar imagery | Free download |
| NOAA ocean sonar data | Real survey data | Public domain |
| Custom crops | Normal seabed patches (for anomaly) | Extract from samples |

### Strategy
- Consolidate all sources into `data/raw/`
- Keep total dataset under **20GB**
- Use aggressive augmentation to compensate for limited data
- Store processed crops, not full survey scans

### Annotation Format (YOLO)
```
class_id center_x center_y width height
```
Classes:
- `0`: fishing_gear
- `1`: container
- `2`: wreckage
- `3`: artificial_object

### Dataset Split
- 70% training
- 15% validation
- 15% test

### Tasks
- [ ] Download public SSS datasets
- [ ] Consolidate with existing sample data
- [ ] Annotate/bounding-box label in YOLO format
- [ ] Create "normal seabed" dataset (unlabeled patches for anomaly detection)
- [ ] Split into train/val/test
- [ ] Create `data.yaml` for YOLO training

---

## Phase 2: AI Models (12-16 hours)

### Model Selection (VRAM-Optimized)

| Component | Model | Est. VRAM | Why |
|---|---|---|---|
| Object Detection | **YOLOv8n** (nano) | ~1GB | Fits 4GB, fast inference, good baseline |
| Segmentation | **YOLOv8n-seg** (nano) | ~1.2GB | Combined with detection, single pass |
| Anomaly Detection | **PatchCore** (ResNet-18) | ~0.5GB | Runs mostly on CPU, memory-efficient |
| Evidence Fusion | **Weighted scoring** | 0GB | Pure Python/numpy — core innovation |
| Risk Engine | **Weighted formula** | 0GB | Pure Python |

### Training Constraints
- **Batch size:** 2-4 (VRAM limit)
- **Epochs:** 50-100 with early stopping
- **Mixed precision:** Enable (`amp=True`) — halves VRAM usage
- **Image size:** 640x640 (default) or 416x416 if VRAM is tight
- **Workers:** 4-8 (CPU preprocessing)

### Tasks

#### Person 1: YOLO Detection (4h)
- [ ] Train YOLOv8n on SSS data
  ```python
  from ultralytics import YOLO
  model = YOLO("yolov8n.pt")
  model.train(data="data.yaml", epochs=100, imgsz=640, batch=4, device=0)
  ```
- [ ] Evaluate on test set (mAP, precision, recall, F1)
- [ ] Export best weights to `models/yolov8n_sss.pt`

#### Person 1: YOLO Segmentation (4h)
- [ ] Train YOLOv8n-seg on mask-annotated SSS data
- [ ] Evaluate IoU, Dice score
- [ ] Export best weights to `models/yolov8n_seg_sss.pt`

#### Person 1: Anomaly Detection — PatchCore (4h)
- [ ] Use pretrained ResNet-18 backbone (frozen)
- [ ] Extract 512-d feature vectors from normal seabed patches
- [ ] Build core-set memory bank (coreset subsampling)
- [ ] At inference: compute distance to nearest stored features
- [ ] High distance = high anomaly score
  ```python
  # Conceptual flow
  features = resnet18(normal_sonar_patches)  # [N, 512]
  memory_bank = coreset_subsample(features)   # [M, 512]
  # Inference
  test_feat = resnet18(new_patch)              # [1, 512]
  dist = min(cosine_distance(test_feat, memory_bank))
  anomaly_score = normalize(dist)
  ```
- [ ] Save memory bank to `models/patchcore_bank.npy`

#### Person 1: Acoustic Feature Extraction (2h)
- [ ] **Target features:** intensity stats (mean, max, std), area, width, height, aspect ratio, orientation, edge sharpness
- [ ] **Shadow features:** threshold-based shadow detection, shadow length, shadow area, shadow-to-target ratio
- [ ] **Seabed features:** local texture (LBP), local contrast, mean background intensity, intensity variance

#### Person 1: Evidence Fusion (1h)
- [ ] Implement weighted fusion formula:
  ```
  evidence_score = (
      w1 * target_evidence +
      w2 * shadow_evidence +
      w3 * seabed_evidence +
      w4 * anomaly_score +
      w5 * detection_confidence
  )
  ```
- [ ] Start with equal weights, tune experimentally
- [ ] Normalize all inputs to [0, 1] range

#### Person 1: Risk Engine (1h)
- [ ] Implement risk scoring:
  ```
  risk_score = (
      w1 * object_severity +
      w2 * anomaly_level +
      w3 * evidence_score +
      w4 * object_size_normalized +
      w5 * location_sensitivity
  )
  ```
- [ ] Threshold into LOW / MEDIUM / HIGH risk levels

### What to Skip for MVP
- Self-supervised pretraining
- Synthetic sonar generation
- Domain adaptation
- Multi-ping tracking (ByteTrack/DeepSORT)
- Advanced neural evidence fusion
- Uncertainty estimation (beyond confidence-based)
- Explainable AI (SHAP/GradCAM)

---

## Phase 3: Backend API (8-10 hours)

### Database: SQLite (not PostgreSQL for hackathon)

```sql
CREATE TABLE surveys (
    survey_id TEXT PRIMARY KEY,
    name TEXT,
    vessel_id TEXT,
    start_time TEXT,
    end_time TEXT,
    area_name TEXT,
    sonar_type TEXT,
    status TEXT DEFAULT 'uploaded'
);

CREATE TABLE sonar_images (
    image_id TEXT PRIMARY KEY,
    survey_id TEXT,
    image_path TEXT,
    timestamp TEXT,
    latitude REAL,
    longitude REAL,
    depth REAL,
    FOREIGN KEY (survey_id) REFERENCES surveys(survey_id)
);

CREATE TABLE detections (
    detection_id TEXT PRIMARY KEY,
    image_id TEXT,
    target_id TEXT,
    object_class TEXT,
    confidence REAL,
    bbox_x1 REAL, bbox_y1 REAL, bbox_x2 REAL, bbox_y2 REAL,
    segmentation_mask_path TEXT,
    FOREIGN KEY (image_id) REFERENCES sonar_images(image_id)
);

CREATE TABLE anomalies (
    anomaly_id TEXT PRIMARY KEY,
    detection_id TEXT,
    anomaly_score REAL,
    uncertainty REAL,
    FOREIGN KEY (detection_id) REFERENCES detections(detection_id)
);

CREATE TABLE acoustic_features (
    detection_id TEXT PRIMARY KEY,
    target_intensity REAL,
    target_area REAL,
    shadow_area REAL,
    shadow_length REAL,
    target_shadow_ratio REAL,
    seabed_texture REAL,
    seabed_contrast REAL,
    FOREIGN KEY (detection_id) REFERENCES detections(detection_id)
);

CREATE TABLE risk_assessments (
    detection_id TEXT PRIMARY KEY,
    evidence_score REAL,
    risk_score REAL,
    risk_level TEXT,
    priority INTEGER,
    FOREIGN KEY (detection_id) REFERENCES detections(detection_id)
);

CREATE TABLE expert_feedback (
    feedback_id TEXT PRIMARY KEY,
    detection_id TEXT,
    expert_label TEXT,
    correction TEXT,
    comments TEXT,
    verified INTEGER DEFAULT 0,
    FOREIGN KEY (detection_id) REFERENCES detections(detection_id)
);
```

### API Endpoints

```
POST   /api/surveys                    # Create/upload survey
GET    /api/surveys                    # List all surveys
GET    /api/surveys/{id}               # Survey details + stats

POST   /api/surveys/{id}/process       # Run full pipeline
GET    /api/surveys/{id}/detections    # All detections for survey

GET    /api/detections/{id}            # Full target record
POST   /api/detections/{id}/verify     # Expert verification

GET    /api/targets/geojson            # GeoJSON for map rendering
GET    /api/targets/priority           # Ranked inspection list
GET    /api/targets/heatmap            # Heatmap point data

GET    /api/stats                      # Dashboard summary stats
```

### Pipeline Service (`run_pipeline.py`)

```python
# Full pipeline flow for a single survey
for image_path, metadata in survey:
    # 1. Preprocessing
    enhanced = preprocess(image_path)  # CLAHE, denoise, normalize

    # 2. Object Detection
    detections = yolo_detect(enhanced)  # bboxes, classes, confidence

    # 3. Segmentation
    masks = yolo_segment(enhanced, detections)  # pixel masks

    # 4. Anomaly Detection
    anomaly_scores = patchcore_score(enhanced, detections)  # [0,1]

    # 5. Acoustic Feature Extraction
    features = extract_acoustic_features(enhanced, detections, masks)

    # 6. Evidence Fusion
    evidence_scores = evidence_fusion(features, anomaly_scores, detections)

    # 7. Risk Assessment
    risk_levels = risk_engine(evidence_scores, features, metadata)

    # 8. Geo-Localization
    locations = geo_localize(detections, metadata)  # GPS coords

    # 9. Prioritization
    priorities = prioritize(detections, risk_levels)

    # 10. Store results
    store_results(detections, features, evidence_scores, risk_levels, locations, priorities)
```

### Tasks
- [ ] Person 2: Set up FastAPI project structure
- [ ] Person 2: Implement SQLAlchemy models (matching SQL schema above)
- [ ] Person 2: Implement data ingestion service
- [ ] Person 2: Implement preprocessing service (OpenCV)
- [ ] Person 2: Wire YOLO inference into detection service
- [ ] Person 2: Wire anomaly detection into anomaly service
- [ ] Person 2: Implement acoustic feature extraction service
- [ ] Person 2: Implement evidence fusion service
- [ ] Person 2: Implement risk engine service
- [ ] Person 2: Implement geo-localization service
- [ ] Person 2: Implement prioritization service
- [ ] Person 2: Implement all API endpoints
- [ ] Person 2: Implement GeoJSON generation endpoint
- [ ] Person 2: Test full pipeline with sample data

---

## Phase 4: GIS Dashboard (8-10 hours)

### Tech Stack
- **React 18** + TypeScript + Vite
- **Tailwind CSS** for styling
- **Leaflet** + react-leaflet for mapping (free, no API key)
- **Turf.js** for geospatial calculations
- **Recharts** for score visualizations
- **Axios** for API calls

### Views

#### 1. Main Dashboard
- Interactive Leaflet map as primary view
- Survey track line (GPS points connected)
- Detection markers colored by risk:
  - Red = HIGH risk
  - Yellow = MEDIUM risk
  - Green = LOW risk
- Layer toggles: detections, heatmap, risk zones
- Stats bar: total detections, high-risk count, processed surveys

#### 2. Target Detail Panel (sidebar)
- Opens on marker click
- Shows:
  - Target ID
  - Sonar image crop with bbox overlay
  - Object class + confidence
  - Anomaly score (gauge/bar)
  - Evidence score (gauge/bar)
  - Risk level (colored badge)
  - Depth, GPS coordinates
  - Shadow info (length, ratio)
  - Priority rank
  - Actions: [VIEW SONAR] [VERIFY] [MARK PRIORITY]

#### 3. Priority Queue Panel
- Scrollable ranked list
- Each entry: Target ID, class, risk badge, evidence score
- Click on entry flies map to location and opens detail panel

#### 4. Verify Dialog
- Modal for expert verification
- Options: Correct / Incorrect / Natural Feature / Marine Debris / Wreckage / New Category
- Comments text field
- Saves to `expert_feedback` table

#### 5. Heatmap Layer
- Toggle-able heatmap overlay on map
- Based on anomaly scores across detections

### Tasks
- [ ] Person 3: Set up React + Vite + Tailwind
- [ ] Person 3: Set up Leaflet map component
- [ ] Person 3: Implement survey track rendering
- [ ] Person 3: Implement detection markers (color-coded by risk)
- [ ] Person 3: Implement target detail sidebar panel
- [ ] Person 3: Implement sonar image overlay view
- [ ] Person 3: Implement priority queue panel
- [ ] Person 3: Implement verification dialog
- [ ] Person 3: Implement anomaly heatmap layer
- [ ] Person 3: Wire all components to backend API
- [ ] Person 3: Style with Tailwind (dark theme recommended for sonar context)

---

## Phase 5: Integration & Demo (4-6 hours)

### Tasks
- [ ] Run full pipeline on sample survey data
- [ ] Verify all detections appear correctly on map
- [ ] Test target detail panel with real scores
- [ ] Test priority queue ordering
- [ ] Test verification flow (submit then stored in DB)
- [ ] Generate realistic demo results (5-20 detections with varied risk levels)
- [ ] Create `scripts/run_pipeline.py` for one-command demo
- [ ] Take screenshots / record demo video for presentation
- [ ] Prepare presentation slides showing end-to-end flow

### Demo Script
```bash
# 1. Start backend
cd backend && uvicorn app.main:app --reload

# 2. Start frontend
cd frontend && npm run dev

# 3. Process sample survey
curl -X POST http://localhost:8000/api/surveys/survey_01/process

# 4. Open browser to http://localhost:5173
# 5. Navigate map, click detections, show priority queue
```

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Detection model | YOLOv8-**nano** | Fits 4GB VRAM, ~2-3ms inference |
| Segmentation model | YOLOv8-**seg-nano** | Combined with detection, single pass |
| Anomaly detection | **PatchCore** (ResNet-18) | Better than autoencoder, lightweight |
| Evidence fusion | **Weighted scoring** | No training needed, fast, demonstrates concept |
| Database | **SQLite** | Zero setup, sufficient for demo |
| Mapping library | **Leaflet** | Free, no API key required |
| Frontend framework | **React + Vite** | Fast dev, great DX |
| Backend framework | **FastAPI** | Async, auto-docs, Python ecosystem |

---

## Hardware Optimization Notes

### Training on RTX 3050 (4GB VRAM)
```python
# YOLOv8 training with VRAM optimization
model.train(
    data="data.yaml",
    epochs=100,
    imgsz=640,        # or 416 if OOM
    batch=4,          # start with 4, reduce to 2 if OOM
    device=0,
    amp=True,         # mixed precision halves VRAM usage
    patience=20,      # early stopping
    workers=4,
    cache="ram"       # cache images in RAM (if 16GB allows)
)
```

### Inference Pipeline
- Load all 3 models into GPU at startup (total ~2.7GB, fits in 4GB)
- Process images sequentially (not batched)
- Use `torch.no_grad()` for inference
- Keep feature extraction on GPU, classical ML on CPU

---

## What to Skip for MVP

| Feature | Why Skip | When to Add |
|---|---|---|
| PostgreSQL + PostGIS | SQLite is sufficient | Post-MVP / production |
| Self-supervised pretraining | Needs large unlabeled corpus + time | Advanced version |
| Synthetic sonar generation | Complex, not needed for demo | Advanced version |
| Domain adaptation | Needs multiple sonar types | Advanced version |
| Multi-ping tracking | Needs temporal sonar stream | Advanced version |
| Uncertainty estimation | Beyond basic confidence | Advanced version |
| Explainable AI | Visual-only for demo | Advanced version |
| Edge AI deployment | Needs Jetson hardware | Future version |
| Real-time streaming | MVP is offline analysis | Future version |
| Active learning loop | Needs expert interaction over time | Advanced version |
| Docker deployment | Saves time during dev | Final deployment only |

---

## Dataset Recommendations

### For Immediate Use
1. **Existing sample data** — annotate with bounding boxes
2. **Kaggle "Shipwreck Detection"** — labeled sonar imagery
3. **NOAA ocean sonar archives** — real survey data (public domain)
4. **Self-collected seabed patches** — crop normal seabed for anomaly training

### Annotation Tools
- **Label Studio** (free, web-based) — for bounding box + polygon annotation
- **CVAT** (free, web-based) — alternative annotation tool

### Annotation Priority
1. Bounding boxes for YOLO detection (required)
2. Polygon masks for YOLO-Seg (high value but optional)
3. Normal seabed crops for PatchCore (required for anomaly detection)

---

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| CUDA OOM during training | Reduce batch size to 2, use imgsz=416, enable AMP |
| Insufficient dataset | Use heavy augmentation (rotation, flip, noise, brightness) |
| Training too slow on laptop | Use pretrained YOLOv8n.pt, train only 50 epochs |
| Anomaly detection too slow | Limit memory bank to 1000 core-set samples |
| Backend-frontend integration issues | Use well-defined JSON contracts, test endpoints individually |
| Demo fails | Have pre-generated results in DB as fallback |

---

## Success Criteria (MVP)

1. Upload a survey with sonar images
2. Process through full pipeline (detection, anomaly, fusion, risk, geo)
3. View detections on interactive map with color-coded risk markers
4. Click a detection to see full target details (scores, sonar image, location)
5. View priority-ranked inspection list
6. Submit expert verification for a detection
7. All powered by models running on RTX 3050 (4GB VRAM)
