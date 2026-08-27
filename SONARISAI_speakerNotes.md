SONARIS AI – INTERNAL SIH EVALUATION SPEAKER NOTES

AI-POWERED SIDE-SCAN SONAR MARINE DEBRIS &
UNDERWATER ANOMALY DETECTION SYSTEM


============================================================
SLIDE 1 – TITLE
============================================================

SONARIS AI

AI-Powered Side-Scan Sonar Marine Debris & Underwater
Anomaly Detection System

SPEAKER NOTES:

Good morning everyone.

Our project is Sonaris AI, an AI-powered underwater intelligence
system that analyzes Side-Scan Sonar imagery to automatically
identify marine debris and underwater anomalies.

The key difference is that we are not building just another
object-detection system.

Sonaris AI combines:

Known-object detection
Open-set anomaly detection
Acoustic shadow analysis
Acoustic evidence fusion
Uncertainty estimation
Risk assessment
Geo-localization
GIS-based inspection prioritization

Our goal is to convert raw Side-Scan Sonar data into actionable
underwater intelligence.


============================================================
SLIDE 2 – PROBLEM STATEMENT
============================================================

SPEAKER NOTES:

Underwater environments are difficult, expensive and time-consuming
to inspect manually.

Side-Scan Sonar allows large underwater areas to be surveyed, but
the resulting images contain noise, seabed variations, acoustic
shadows and previously unseen objects.

Traditional manual interpretation requires skilled experts to
analyze large volumes of sonar data.

A conventional AI detector also has an important limitation.

Suppose the model is trained on:

Fishing Gear
Containers
Wreckage

If it encounters a completely new underwater object, a closed-set
classifier may incorrectly force that object into one of the known
classes.

Therefore, our problem is not simply:

"Can AI detect an object?"

Our problem is:

"Can AI detect known objects, identify unknown objects, analyze
their acoustic evidence, estimate uncertainty and prioritize them
for inspection?"


============================================================
SLIDE 3 – PROPOSED SOLUTION
============================================================

SPEAKER NOTES:

Sonaris AI solves this problem using a multi-stage AI pipeline.

First, we acquire Side-Scan Sonar imagery together with navigation
information such as GPS, depth, heading and timestamp.

The sonar data is then preprocessed.

After preprocessing, the system uses two parallel AI branches.

The first branch performs known-object detection and segmentation.

The second branch performs open-set anomaly detection.

The outputs from these branches are passed into our Acoustic
Evidence Fusion layer.

This layer analyzes:

Target characteristics
Acoustic shadow
Seabed context
AI confidence
Anomaly score

The system then estimates uncertainty, calculates risk,
geo-localizes the target and displays it on a GIS dashboard.

Our overall concept is:

SENSE → DETECT → VERIFY → ASSESS → PRIORITIZE → MAP → INSPECT


============================================================
SLIDE 4 – END-TO-END ARCHITECTURE
============================================================

SPEAKER NOTES:

This is the complete architecture of Sonaris AI.

At the sensing layer, we have Side-Scan Sonar and potentially an
AUV, USV or survey vessel.

The data-ingestion layer collects sonar imagery and synchronizes
it with navigation metadata.

The preprocessing layer improves the sonar data while preserving
important acoustic information.

The AI layer contains:

Object Detection
Object Segmentation
Open-Set Anomaly Detection

Then we extract acoustic features from the target, acoustic shadow
and surrounding seabed.

These features are passed into the Acoustic Evidence Fusion layer.

The result is used for:

Evidence scoring
Uncertainty estimation
Risk assessment

Finally, the target is geo-localized and prioritized.

The information is displayed through a GIS dashboard and can be
used for ROV/AUV inspection.


============================================================
SLIDE 5 – DATA ACQUISITION
============================================================

SPEAKER NOTES:

The primary input to Sonaris AI is Side-Scan Sonar imagery.

Along with the sonar image, we use available metadata such as:

GPS coordinates
Depth
Heading
Timestamp
Sonar range
Frequency
Ping information

This information is important because our final output should not
just say:

"There is an object in this image."

Instead, it should provide:

"There is a potentially high-risk underwater target at this
location and depth."

Therefore, navigation metadata becomes an important part of the
intelligence pipeline.


============================================================
SLIDE 6 – DATASET STRATEGY
============================================================

SPEAKER NOTES:

One of the biggest challenges in underwater AI is the limited
availability of high-quality labeled Side-Scan Sonar datasets.

Our dataset strategy has three components.

First, labeled sonar data for known-object detection.

Second, normal seabed data for learning normal sonar patterns.

Third, unknown or difficult samples for evaluating open-set
anomaly detection.

We can further improve the dataset using:

Data augmentation
Synthetic sonar generation
Transfer learning
Self-supervised learning
Active learning

We will also focus on evaluating generalization instead of
depending only on training-set accuracy.


============================================================
SLIDE 7 – SONAR PREPROCESSING
============================================================

SPEAKER NOTES:

Raw Side-Scan Sonar images contain noise, intensity variations and
different seabed patterns.

Therefore, preprocessing is required before AI inference.

Possible preprocessing techniques include:

Noise reduction
Contrast enhancement
CLAHE
Intensity normalization
Log compression
Slant-range correction
Image rectification

However, we need to be careful.

We should not over-process the image because acoustic shadows
contain important information.

Therefore, our preprocessing pipeline should improve image quality
while preserving target and shadow characteristics.


============================================================
SLIDE 8 – AI OBJECT DETECTION
============================================================

SPEAKER NOTES:

The first AI branch performs known-object detection.

For our initial prototype, we can use a real-time object detector
such as YOLO.

Depending on the available dataset, the model can detect:

Fishing Gear
Containers
Wreckage
Artificial Objects
Other labeled debris categories

The detector produces:

Bounding Box
Object Class
Confidence Score

However, this confidence score is not treated as the final
decision.

A high confidence score does not necessarily guarantee that the
target is actually marine debris.

Therefore, we use additional acoustic and anomaly evidence.


============================================================
SLIDE 9 – OBJECT SEGMENTATION
============================================================

SPEAKER NOTES:

Object detection tells us where the target is.

Segmentation provides the precise shape and boundary of the target.

Possible segmentation models include:

YOLO-Seg
U-Net
SegFormer
Mask R-CNN

From the segmentation mask we can calculate:

Object Area
Width
Height
Aspect Ratio
Orientation
Shape

These features are later used by our Acoustic Evidence Fusion
system.

Therefore, segmentation is not only a visualization feature.


============================================================
SLIDE 10 – OPEN-SET ANOMALY DETECTION
============================================================

SPEAKER NOTES:

Open-set anomaly detection is one of the important components of
Sonaris AI.

Traditional object detection generally assumes that every input
belongs to one of the classes seen during training.

But underwater environments contain unpredictable objects.

Therefore, our system includes a separate anomaly-detection branch.

Possible approaches include:

Autoencoder
Variational Autoencoder
PatchCore
Deep SVDD
Feature-distance methods

The model learns representations of normal and known sonar patterns.

When a target significantly differs from those patterns, it receives
a high anomaly score.

Therefore, an unseen target can be flagged as:

UNKNOWN / HIGH-ANOMALY OBJECT

instead of being incorrectly classified as a known object.


============================================================
SLIDE 11 – ACOUSTIC SHADOW ANALYSIS
============================================================

SPEAKER NOTES:

This is where Sonaris AI becomes specifically focused on
Side-Scan Sonar.

Underwater objects can generate acoustic shadows behind them.

The acoustic shadow can provide useful information about the
target's geometry and relative characteristics.

Therefore, we analyze:

Shadow Length
Shadow Area
Shadow Width
Shadow Geometry
Target-to-Shadow Ratio
Shadow Orientation

This provides information that a normal RGB-based object detector
cannot directly use.

Our hypothesis is that target-plus-shadow analysis can improve
detection reliability.


============================================================
SLIDE 12 – ACOUSTIC FEATURE EXTRACTION
============================================================

SPEAKER NOTES:

We divide the extracted features into three major groups.

TARGET FEATURES:

Target intensity
Object area
Object width
Object height
Shape
Orientation
Aspect ratio

SHADOW FEATURES:

Shadow length
Shadow area
Shadow width
Shadow geometry
Target-to-shadow ratio

SEABED FEATURES:

Local texture
Local contrast
Background intensity
Intensity variance

We also include:

Detection confidence
Anomaly score

Together, these form the acoustic feature vector for each target.


============================================================
SLIDE 13 – ACOUSTIC EVIDENCE FUSION
============================================================

SPEAKER NOTES:

This is the core technical innovation of Sonaris AI.

Instead of relying only on the output of a single AI model, we
combine multiple sources of evidence.

The fusion layer receives:

Target features
Shadow features
Seabed context
Detection confidence
Anomaly score

For the initial prototype, we can implement a weighted fusion
formula.

For example:

Evidence Score =
Target Evidence
+
Shadow Evidence
+
Seabed Evidence
+
Anomaly Score
+
Detection Confidence

with experimentally determined weights.

After establishing the baseline, we can experiment with:

Random Forest
XGBoost
MLP
Attention-based feature fusion

The important research question is:

"Does acoustic evidence fusion reduce false positives and improve
detection reliability compared with a detector-only approach?"


============================================================
SLIDE 14 – UNCERTAINTY ESTIMATION
============================================================

SPEAKER NOTES:

Not every AI prediction has the same reliability.

Therefore, Sonaris AI also estimates uncertainty.

For example:

TARGET A

Class:
Fishing Gear

Confidence:
96%

Anomaly:
Low

Uncertainty:
Low

Decision:
Reliable Detection


TARGET B

Class:
Unknown

Confidence:
62%

Anomaly:
94%

Uncertainty:
High

Decision:
Human Verification Required

This allows the system to distinguish between confident detections
and suspicious detections.


============================================================
SLIDE 15 – RISK INTELLIGENCE
============================================================

SPEAKER NOTES:

After evidence fusion and uncertainty estimation, we calculate a
risk score.

Risk is not based only on object classification.

We can consider:

Object Type
Object Size
Anomaly Level
Evidence Score
Uncertainty
Location
Environmental Sensitivity

The system produces:

LOW RISK
MEDIUM RISK
HIGH RISK

This changes Sonaris AI from a simple object-recognition system
into a decision-support system.


============================================================
SLIDE 16 – GEO-LOCALIZATION
============================================================

SPEAKER NOTES:

After detecting a target, we associate it with geographic
information.

Using available:

GPS
Sonar Range
Heading
Depth
Timestamp

we estimate the target's geographic location.

Each detection can become a structured record containing:

Target ID
Latitude
Longitude
Depth
Timestamp
Object Class
Confidence
Anomaly Score
Evidence Score
Risk Level

Spatial information can be stored using PostgreSQL and PostGIS.


============================================================
SLIDE 17 – GIS INTELLIGENCE DASHBOARD
============================================================

SPEAKER NOTES:

The GIS dashboard is the operational interface of Sonaris AI.

Instead of manually examining thousands of sonar images, an
operator can see detected targets directly on an interactive map.

The dashboard can display:

Survey Tracks
Detected Objects
High-Risk Targets
Anomaly Heatmaps
Risk Zones
Sonar Image Overlays
Target Coordinates

When the operator selects a target, they can view:

Sonar Image
Object Class
Confidence
Anomaly Score
Evidence Score
Risk Score
Depth
Location

The GIS layer converts AI predictions into actionable
underwater intelligence.


============================================================
SLIDE 18 – INSPECTION PRIORITIZATION
============================================================

SPEAKER NOTES:

Imagine that the system detects 200 targets.

It may not be practical to send an ROV or inspection team to all
200 targets.

Therefore, Sonaris AI ranks the targets according to their
importance.

Example:

Target 17 – HIGH PRIORITY
Target 42 – HIGH PRIORITY
Target 08 – MEDIUM PRIORITY
Target 61 – MEDIUM PRIORITY
Target 91 – LOW PRIORITY

This allows operators to inspect important targets first.

In the future, these prioritized coordinates can be supplied to
an AUV or ROV mission-planning system.


============================================================
SLIDE 19 – HUMAN-IN-THE-LOOP
============================================================

SPEAKER NOTES:

We do not assume that AI will always be correct.

Especially in open-set underwater environments, some detections
will be ambiguous.

Therefore, experts can verify AI predictions.

They can mark a detection as:

Correct
Incorrect
Natural Feature
Marine Debris
Wreckage
New Category

This feedback is stored and can later be used as additional
training data.

This creates a human-AI collaboration system.


============================================================
SLIDE 20 – ACTIVE LEARNING
============================================================

SPEAKER NOTES:

Active learning reduces manual annotation effort.

Instead of asking experts to label thousands of sonar images, the
system identifies the most uncertain or informative samples.

Those samples are sent to experts for verification.

The verified samples are added to the training dataset.

The model is retrained and evaluated.

The cycle becomes:

AI
↓
Uncertainty Detection
↓
Human Feedback
↓
New Training Data
↓
Model Retraining
↓
Improved AI

This allows Sonaris AI to continuously improve.


============================================================
SLIDE 21 – TECHNICAL IMPROVEMENTS
============================================================

SPEAKER NOTES:

There are several technical improvements planned beyond the MVP.

1. TARGET-SHADOW RELATIONSHIP MODELING

Explicitly model the relationship between the target and its
acoustic shadow.

2. SELF-SUPERVISED LEARNING

Use large amounts of unlabeled sonar data to learn useful
representations.

3. SYNTHETIC SONAR GENERATION

Generate different object shapes, orientations, seabeds, noise
levels and shadow patterns.

4. DOMAIN ADAPTATION

Improve model performance across different sonar devices and
underwater environments.

5. MULTI-PING TRACKING

Track the same physical object across multiple sonar frames.

6. UNCERTAINTY ESTIMATION

Identify unreliable AI predictions.

7. EXPLAINABLE AI

Show why a target was classified or flagged as anomalous.

8. EDGE AI

Deploy optimized inference on platforms such as NVIDIA Jetson.


============================================================
SLIDE 22 – TECHNICAL VALIDATION
============================================================

SPEAKER NOTES:

We will not evaluate the system only using accuracy.

For object detection we will measure:

Precision
Recall
mAP
F1-score

For segmentation:

IoU
Dice Score

For anomaly detection:

AUROC
AUPR
False Positive Rate

For the complete system:

Localization Error
Inference Latency
Risk Ranking Quality

We will also perform an ablation study.

We will compare:

MODEL 1:
YOLO alone

MODEL 2:
YOLO + Anomaly Detection

MODEL 3:
YOLO + Anomaly Detection + Acoustic Evidence Fusion

This allows us to quantitatively demonstrate whether our proposed
additional components actually improve the system.


============================================================
SLIDE 23 – DEPLOYMENT ARCHITECTURE
============================================================

SPEAKER NOTES:

For the SIH prototype, AI inference can run on a GPU-enabled
server.

The backend can use:

Python
FastAPI
PostgreSQL
PostGIS

The frontend can use:

React
TypeScript
Tailwind CSS

For GIS visualization we can use:

Mapbox
or
Leaflet

Docker can be used to package the system.

For future deployment, the AI model can be optimized using:

ONNX
TensorRT

and deployed on edge hardware.

This can enable near-real-time processing on AUVs, USVs or survey
vessels.


============================================================
SLIDE 24 – TARGET USERS
============================================================

SPEAKER NOTES:

From a market perspective, the primary users are organizations
that perform underwater inspection and monitoring.

Potential users include:

Marine Environmental Agencies
Ports and Harbors
Offshore Infrastructure Operators
Marine Survey Companies
Research Institutions
Fisheries Organizations
Disaster and Search-and-Rescue Organizations

The primary value proposition is reducing manual sonar-analysis
effort and helping organizations prioritize expensive physical
inspection.


============================================================
SLIDE 25 – MARKET OPPORTUNITY
============================================================

SPEAKER NOTES:

The opportunity comes from increasing use of:

Underwater sensing
AUVs
ROVs
USVs
Digital marine monitoring
Autonomous inspection

However, our initial market should be focused.

Our beachhead market is:

"AI-assisted Side-Scan Sonar analysis for marine debris and
underwater inspection."

The initial product can operate as software that processes
existing sonar datasets.

This means organizations do not necessarily need to purchase
completely new sonar hardware.

Later, Sonaris AI can integrate directly with:

AUVs
USVs
ROVs
Survey vessels


============================================================
SLIDE 26 – COMPETITIVE DIFFERENTIATION
============================================================

SPEAKER NOTES:

Existing research covers individual capabilities such as:

Sonar object detection
Shipwreck detection
Marine debris detection
Ghost-gear detection
Segmentation

Our differentiation is the integration of multiple capabilities
into a single decision-support pipeline.

Our architecture combines:

Known Object Detection
+
Open-Set Anomaly Detection
+
Acoustic Shadow Analysis
+
Acoustic Evidence Fusion
+
Uncertainty Estimation
+
Risk Assessment
+
GIS Prioritization

We are not claiming that every individual component is completely
new.

Our innovation is in combining these capabilities into a
sonar-specific decision-support architecture.


============================================================
SLIDE 27 – BUSINESS / DEPLOYMENT MODEL
============================================================

SPEAKER NOTES:

There are three possible deployment models.

MODEL 1 – SOFTWARE AS A SERVICE

Organizations upload sonar datasets and receive:

Detection
Classification
Risk Analysis
GIS Reports


MODEL 2 – ON-PREMISE DEPLOYMENT

Organizations can deploy the system within their own infrastructure
when data privacy or operational restrictions are important.


MODEL 3 – EDGE DEPLOYMENT

The AI model runs directly on:

AUV
USV
Survey Vessel

We can also provide APIs so that existing marine-survey platforms
can integrate Sonaris AI outputs.


============================================================
SLIDE 28 – IMPLEMENTATION ROADMAP
============================================================

SPEAKER NOTES:

Our implementation will be divided into stages.

PHASE 1:
Dataset preparation and sonar preprocessing.

PHASE 2:
Train baseline object detector.

PHASE 3:
Implement object segmentation.

PHASE 4:
Develop open-set anomaly detection.

PHASE 5:
Implement acoustic target-shadow feature extraction.

PHASE 6:
Develop acoustic evidence fusion.

PHASE 7:
Add uncertainty and risk scoring.

PHASE 8:
Implement geo-localization.

PHASE 9:
Build GIS dashboard.

PHASE 10:
Add human feedback and active learning.

PHASE 11:
Optimize the model for real-time and edge deployment.


============================================================
SLIDE 29 – WHY SONARIS AI IS SIH-WORTHY
============================================================

SPEAKER NOTES:

We believe Sonaris AI has strong SIH potential for four major
reasons.

FIRST:

It addresses a real-world underwater inspection problem.

SECOND:

It combines multiple AI techniques around the unique
characteristics of Side-Scan Sonar.

THIRD:

It produces actionable output rather than only classification
labels.

The output is:

Detection
+
Confidence
+
Anomaly
+
Evidence
+
Risk
+
Location
+
Priority

FOURTH:

The architecture is scalable.

We can begin with public sonar datasets and a software prototype
and progressively integrate:

Real sonar
Edge computing
AUVs
ROVs
Autonomous inspection


============================================================
SLIDE 30 – FINAL PITCH
============================================================

SPEAKER NOTES:

To summarize, Sonaris AI answers five important questions.

QUESTION 1:

What is underwater?

ANSWER:

AI object detection and segmentation.


QUESTION 2:

Could it be something the model has never seen before?

ANSWER:

Open-set anomaly detection.


QUESTION 3:

How reliable is the detection?

ANSWER:

Acoustic evidence fusion and uncertainty estimation.


QUESTION 4:

How important is the target?

ANSWER:

Risk intelligence and inspection prioritization.


QUESTION 5:

Where is the target?

ANSWER:

Geo-localization and GIS mapping.


Therefore, our complete pipeline is:

RAW SIDE-SCAN SONAR
        ↓
AI ANALYSIS
        ↓
KNOWN + UNKNOWN DETECTION
        ↓
ACOUSTIC FEATURE EXTRACTION
        ↓
ACOUSTIC EVIDENCE FUSION
        ↓
UNCERTAINTY ESTIMATION
        ↓
RISK INTELLIGENCE
        ↓
GEO-LOCALIZATION
        ↓
INSPECTION PRIORITIZATION
        ↓
GIS DASHBOARD
        ↓
ROV / AUV INSPECTION


FINAL STATEMENT:

"Sonaris AI transforms raw Side-Scan Sonar imagery into actionable
underwater intelligence by combining AI detection, open-set anomaly
detection, acoustic evidence fusion, uncertainty estimation,
risk-aware prioritization and geo-referenced inspection planning."


============================================================
IMPORTANT EVALUATOR QUESTIONS & ANSWERS
============================================================


Q1. WHAT IS THE NOVELTY OF SONARIS AI?

ANSWER:

Our core novelty is the Acoustic Evidence Fusion layer.

Instead of relying only on an object detector, we combine target
characteristics, acoustic-shadow geometry, seabed context, anomaly
score and AI confidence to produce an evidence score, uncertainty
estimate and risk priority.


------------------------------------------------------------

Q2. WHY CAN'T YOU JUST USE YOLO?

ANSWER:

YOLO is effective for known classes, but it is not sufficient for
an open underwater environment.

If the model encounters an unseen object, a closed-set detector may
force it into an incorrect class.

Our anomaly-detection branch identifies previously unseen targets,
while acoustic evidence fusion provides additional sonar-specific
verification.


------------------------------------------------------------

Q3. HOW WILL YOU DETECT SOMETHING THAT IS NOT IN YOUR DATASET?

ANSWER:

We do not attempt to classify every unknown object.

The open-set anomaly model learns representations of known and
normal sonar patterns.

When a target significantly deviates from those patterns, it
receives a high anomaly score and is flagged as an unknown target
for human verification.


------------------------------------------------------------

Q4. WHAT IF THE AI MAKES A WRONG PREDICTION?

ANSWER:

We use uncertainty estimation and human-in-the-loop verification.

High-uncertainty detections can be sent to an expert.

The verified result can then be incorporated into the
active-learning pipeline and used to improve future model versions.


------------------------------------------------------------

Q5. WHY WOULD SOMEONE PAY FOR THIS?

ANSWER:

Underwater inspection can require significant vessel, AUV, ROV and
human resources.

Sonaris AI does not initially try to replace these systems.

Instead, it makes them more efficient by identifying and ranking
the targets that deserve physical inspection first.

The initial software can work with existing sonar datasets,
reducing the hardware barrier for adoption.


------------------------------------------------------------

Q6. WHAT IF THE DATASET IS TOO SMALL?

ANSWER:

We can use:

Data Augmentation
Transfer Learning
Self-Supervised Learning
Synthetic Sonar Generation
Active Learning
Domain Adaptation

Our objective is to reduce dependence on manually labeled sonar
data.


------------------------------------------------------------

Q7. HOW IS THIS DIFFERENT FROM EXISTING SONAR AI?

ANSWER:

Existing approaches often focus on individual tasks such as
object detection, segmentation or debris classification.

Sonaris AI combines:

Detection
+
Open-Set Anomaly Detection
+
Acoustic Shadow Analysis
+
Evidence Fusion
+
Uncertainty
+
Risk Assessment
+
GIS Prioritization

Therefore, the final output is decision intelligence rather than
only object classification.


------------------------------------------------------------

Q8. CAN THIS WORK IN REAL TIME?

ANSWER:

The initial SIH prototype will focus on offline sonar analysis.

After validating the architecture, the AI model can be optimized
using ONNX and TensorRT and deployed on edge hardware such as
NVIDIA Jetson.

This enables near-real-time processing on an AUV, USV or survey
platform.


------------------------------------------------------------

Q9. WHAT IS YOUR MVP?

ANSWER:

Our MVP consists of:

SIDE-SCAN SONAR DATA
        ↓
PREPROCESSING
        ↓
YOLO DETECTION
        ↓
SEGMENTATION
        ↓
OPEN-SET ANOMALY DETECTION
        ↓
TARGET + SHADOW FEATURE EXTRACTION
        ↓
ACOUSTIC EVIDENCE FUSION
        ↓
RISK SCORE
        ↓
GEO-LOCALIZATION
        ↓
GIS DASHBOARD


------------------------------------------------------------

Q10. WHAT IS THE MOST IMPORTANT PART OF YOUR PROJECT?

ANSWER:

The most important part is not the individual YOLO detector.

The key component is the Acoustic Evidence Fusion and Risk
Intelligence pipeline.

It converts multiple sonar and AI signals into an actionable
decision about whether a target should be inspected.


------------------------------------------------------------

Q11. WHAT HAPPENS WHEN YOU FIND AN UNKNOWN OBJECT?

ANSWER:

The system does not force the object into an existing class.

The anomaly-detection branch calculates an anomaly score.

If the score is high, the system flags the target as an unknown
anomaly.

The target is then prioritized for human verification.

If the expert identifies it as a new category, that information
can be added to the dataset for future model training.


------------------------------------------------------------

Q12. WHY DO YOU NEED ACOUSTIC SHADOW INFORMATION?

ANSWER:

The acoustic shadow is a characteristic feature of Side-Scan Sonar
and can provide additional information about the target's geometry.

A conventional RGB detector does not have access to this
target-shadow relationship.

Therefore, incorporating shadow information makes our approach more
specific to the sonar domain.


============================================================
30-SECOND ELEVATOR PITCH
============================================================

"Sonaris AI is an AI-powered Side-Scan Sonar intelligence platform
for marine-debris and underwater anomaly detection.

Unlike conventional detectors that only recognize predefined
objects, Sonaris AI combines known-object detection with open-set
anomaly detection and analyzes target shape, acoustic shadows,
seabed context, AI confidence and anomaly scores through an
acoustic evidence-fusion layer.

It then estimates uncertainty, assigns risk, geo-localizes the
target and prioritizes it on a GIS dashboard for inspection.

Our goal is to transform raw sonar imagery into actionable
underwater intelligence and reduce unnecessary manual inspection."


============================================================
ONE-LINE PROJECT DEFINITION
============================================================

"SONARIS AI DOES NOT JUST DETECT WHAT IS UNDERWATER;
IT DETERMINES WHAT IT IS, WHETHER IT IS UNKNOWN,
HOW RELIABLE THE EVIDENCE IS, HOW RISKY IT IS,
WHERE IT IS, AND WHICH TARGET SHOULD BE INSPECTED FIRST."


============================================================
CORE ARCHITECTURE TO REMEMBER
============================================================

SIDE-SCAN SONAR
      ↓
PREPROCESSING
      ↓
DETECTION + SEGMENTATION
      ↓
OPEN-SET ANOMALY DETECTION
      ↓
TARGET + SHADOW + SEABED FEATURES
      ↓
ACOUSTIC EVIDENCE FUSION
      ↓
UNCERTAINTY ESTIMATION
      ↓
RISK INTELLIGENCE
      ↓
GEO-LOCALIZATION
      ↓
INSPECTION PRIORITIZATION
      ↓
GIS DASHBOARD
      ↓
HUMAN VERIFICATION
      ↓
ACTIVE LEARNING
      ↓
MODEL IMPROVEMENT