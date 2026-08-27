import numpy as np
from ..config import FUSION_WEIGHTS


def normalize(value: float, min_val: float = 0.0, max_val: float = 255.0) -> float:
    if max_val - min_val == 0:
        return 0.0
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


def compute_target_evidence(features: dict) -> float:
    intensity = normalize(features.get("target_intensity", 0), 0, 255)
    area = min(features.get("target_area", 0) / 10000.0, 1.0)
    aspect = min(features.get("aspect_ratio", 0) / 10.0, 1.0)

    return 0.4 * intensity + 0.3 * area + 0.3 * aspect


def compute_shadow_evidence(features: dict) -> float:
    shadow_length = min(features.get("shadow_length", 0) / 200.0, 1.0)
    shadow_area = min(features.get("shadow_area", 0) / 5000.0, 1.0)
    ratio = features.get("target_shadow_ratio", 0)
    ratio_score = 1.0 - min(abs(ratio - 1.0), 1.0)

    return 0.4 * shadow_length + 0.3 * shadow_area + 0.3 * ratio_score


def compute_seabed_evidence(features: dict) -> float:
    texture = normalize(features.get("seabed_texture", 0), 0, 100)
    contrast = normalize(features.get("seabed_contrast", 0), 0, 255)

    return 0.5 * texture + 0.5 * contrast


def fuse_evidence(
    features: dict,
    anomaly_score: float,
    detection_confidence: float,
    weights: dict | None = None,
) -> dict:
    if weights is None:
        weights = FUSION_WEIGHTS

    target_ev = compute_target_evidence(features)
    shadow_ev = compute_shadow_evidence(features)
    seabed_ev = compute_seabed_evidence(features)

    evidence_score = (
        weights["target"] * target_ev
        + weights["shadow"] * shadow_ev
        + weights["seabed"] * seabed_ev
        + weights["anomaly"] * anomaly_score
        + weights["confidence"] * detection_confidence
    )

    evidence_score = max(0.0, min(1.0, evidence_score))

    return {
        "evidence_score": evidence_score,
        "target_evidence": target_ev,
        "shadow_evidence": shadow_ev,
        "seabed_evidence": seabed_ev,
    }
