from ..config import RISK_WEIGHTS, RISK_HIGH_THRESHOLD, RISK_MEDIUM_THRESHOLD, OBJECT_SEVERITY


def compute_risk(
    object_class: str,
    anomaly_score: float,
    evidence_score: float,
    target_area: float,
    confidence: float,
) -> dict:
    object_severity = OBJECT_SEVERITY.get(object_class, OBJECT_SEVERITY["unknown"])

    anomaly_level = anomaly_score

    evidence_level = evidence_score

    size_normalized = min(target_area / 10000.0, 1.0)

    location_sensitivity = 0.5

    risk_score = (
        RISK_WEIGHTS["object_severity"] * object_severity
        + RISK_WEIGHTS["anomaly_level"] * anomaly_level
        + RISK_WEIGHTS["evidence_score"] * evidence_level
        + RISK_WEIGHTS["object_size"] * size_normalized
        + RISK_WEIGHTS["location_sensitivity"] * location_sensitivity
    )

    risk_score = max(0.0, min(1.0, risk_score))

    if risk_score >= RISK_HIGH_THRESHOLD:
        risk_level = "HIGH"
    elif risk_score >= RISK_MEDIUM_THRESHOLD:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
    }
