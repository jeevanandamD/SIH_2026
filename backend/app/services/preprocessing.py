import cv2
import numpy as np
from ..config import CLAHE_CLIP_LIMIT, CLAHE_TILE_SIZE, GAUSSIAN_KERNEL


def preprocess_sonar(image: np.ndarray) -> np.ndarray:
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)

    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP_LIMIT, tileGridSize=CLAHE_TILE_SIZE)
    enhanced = clahe.apply(denoised)

    normalized = cv2.normalize(enhanced, None, 0, 255, cv2.NORM_MINMAX)

    blurred = cv2.GaussianBlur(normalized, GAUSSIAN_KERNEL, 0)
    sharpened = cv2.addWeighted(normalized, 1.5, blurred, -0.5, 0)
    sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)

    return sharpened


def detect_shadow_region(target_mask: np.ndarray, image: np.ndarray, angle_offset_deg: float = 45.0) -> np.ndarray:
    h, w = image.shape[:2]
    contours, _ = cv2.findContours(target_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return np.zeros_like(image, dtype=np.uint8)

    largest = max(contours, key=cv2.contourArea)
    M = cv2.moments(largest)
    if M["m00"] == 0:
        return np.zeros_like(image, dtype=np.uint8)

    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])

    shadow_mask = np.zeros_like(image, dtype=np.uint8)

    kernel_size = max(20, min(h, w) // 5)
    shadow_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))

    angle_rad = np.radians(angle_offset_deg)
    offset_x = int(kernel_size * np.cos(angle_rad))
    offset_y = int(kernel_size * np.sin(angle_rad))

    shifted_mask = np.zeros_like(target_mask, dtype=np.uint8)
    pts = largest + np.array([[[offset_x, offset_y]]], dtype=np.int32)
    pts = np.clip(pts, [0, 0], [w - 1, h - 1])
    cv2.fillPoly(shifted_mask, [pts], 1)

    shadow_region = cv2.bitand(shifted_mask, cv2.bitwise_not(target_mask.astype(np.uint8)))
    shadow_mask = cv2.bitand(shadow_region, cv2.bitwise_not(target_mask.astype(np.uint8)))

    shadow_mask = cv2.dilate(shadow_mask.astype(np.uint8), shadow_kernel, iterations=1)

    return shadow_mask.astype(np.uint8)


def extract_bounding_box_crop(image: np.ndarray, x1: int, y1: int, x2: int, y2: int, padding: int = 20) -> np.ndarray:
    h, w = image.shape[:2]
    px1 = max(0, x1 - padding)
    py1 = max(0, y1 - padding)
    px2 = min(w, x2 + padding)
    py2 = min(h, y2 + padding)
    return image[py1:py2, px1:px2]
