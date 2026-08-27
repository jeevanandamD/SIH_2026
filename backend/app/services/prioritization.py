from ..config import RISK_HIGH_THRESHOLD, RISK_MEDIUM_THRESHOLD


def assign_priorities(detections: list[dict]) -> list[dict]:
    risk_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    sorted_detections = sorted(
        detections,
        key=lambda d: (
            risk_order.get(d.get("risk_level", "LOW"), 2),
            -d.get("risk_score", 0),
            -d.get("evidence_score", 0),
        ),
    )

    for i, det in enumerate(sorted_detections):
        det["priority"] = i + 1

    return sorted_detections
