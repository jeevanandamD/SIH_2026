import cv2
import numpy as np


def compute_target_intensity(image: np.ndarray, mask: np.ndarray) -> float:
    if mask.sum() == 0:
        return 0.0
    return float(np.mean(image[mask > 0]))


def compute_target_area(mask: np.ndarray) -> float:
    return float(np.sum(mask > 0))


def compute_target_shape(mask: np.ndarray) -> dict:
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return {"aspect_ratio": 0.0, "orientation": 0.0, "perimeter": 0.0}

    largest = max(contours, key=cv2.contourArea)
    rect = cv2.minAreaRect(largest)
    w, h = rect[1]
    if w == 0 or h == 0:
        return {"aspect_ratio": 0.0, "orientation": 0.0, "perimeter": 0.0}

    aspect_ratio = max(w, h) / min(w, h)
    orientation = rect[2]
    perimeter = cv2.arcLength(largest, True)

    return {"aspect_ratio": aspect_ratio, "orientation": orientation, "perimeter": perimeter}


def compute_shadow_features(image: np.ndarray, target_mask: np.ndarray) -> dict:
    h, w = image.shape[:2]
    contours, _ = cv2.findContours(target_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return {"shadow_area": 0.0, "shadow_length": 0.0, "shadow_width": 0.0, "target_shadow_ratio": 0.0}

    largest = max(contours, key=cv2.contourArea)
    M = cv2.moments(largest)
    if M["m00"] == 0:
        return {"shadow_area": 0.0, "shadow_length": 0.0, "shadow_width": 0.0, "target_shadow_ratio": 0.0}

    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])

    x, y, bw, bh = cv2.boundingRect(largest)
    angle_rad = np.radians(45)
    offset_x = int(bh * np.cos(angle_rad))
    offset_y = int(bh * np.sin(angle_rad))

    shadow_pts = largest.copy()
    shadow_pts[:, :, 0] += offset_x
    shadow_pts[:, :, 1] += offset_y
    shadow_pts = np.clip(shadow_pts, [0, 0], [w - 1, h - 1])

    shadow_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(shadow_mask, [shadow_pts], 1)
    shadow_mask = cv2.bitwise_and(shadow_mask, cv2.bitwise_not(target_mask.astype(np.uint8)))

    shadow_area = float(np.sum(shadow_mask > 0))
    target_area = float(np.sum(target_mask > 0))

    sx, sy, sw, sh = cv2.boundingRect(shadow_mask.astype(np.uint8))
    shadow_length = float(max(sw, sh))
    shadow_width = float(min(sw, sh))

    target_shadow_ratio = target_area / max(shadow_area, 1.0)

    return {
        "shadow_area": shadow_area,
        "shadow_length": shadow_length,
        "shadow_width": shadow_width,
        "target_shadow_ratio": target_shadow_ratio,
    }


def compute_seabed_features(image: np.ndarray, mask: np.ndarray, radius: int = 30) -> dict:
    h, w = image.shape[:2]
    dilated = cv2.dilate(mask.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2, radius * 2)))
    seabed_region = cv2.bitwise_and(dilated, cv2.bitwise_not(mask.astype(np.uint8)))

    if seabed_region.sum() == 0:
        background = image
    else:
        background = image[seabed_region > 0]

    if len(background) == 0:
        return {"seabed_texture": 0.0, "seabed_contrast": 0.0, "seabed_mean": 0.0}

    local_texture = float(np.std(background.astype(np.float32)))
    local_contrast = float(np.max(background.astype(np.float32)) - np.min(background.astype(np.float32)))
    seabed_mean = float(np.mean(background.astype(np.float32)))

    return {
        "seabed_texture": local_texture,
        "seabed_contrast": local_contrast,
        "seabed_mean": seabed_mean,
    }


def extract_acoustic_features(image: np.ndarray, mask: np.ndarray) -> dict:
    target_intensity = compute_target_intensity(image, mask)
    target_area = compute_target_area(mask)
    shape_info = compute_target_shape(mask)
    shadow_info = compute_shadow_features(image, mask)
    seabed_info = compute_seabed_features(image, mask)

    return {
        "target_intensity": target_intensity,
        "target_area": target_area,
        "aspect_ratio": shape_info["aspect_ratio"],
        "orientation": shape_info["orientation"],
        "perimeter": shape_info["perimeter"],
        **shadow_info,
        **seabed_info,
    }
