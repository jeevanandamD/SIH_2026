import cv2
import numpy as np
from pathlib import Path
import random
import math

def generate_synthetic_sonar_image(
    width: int = 640,
    height: int = 640,
    nadir_width: int = 40,
    targets: list[dict] | None = None,
) -> tuple[np.ndarray, list[dict]]:
    """
    Generates a realistic dual-channel Side-Scan Sonar (SSS) waterfall image.
    Includes:
    - Port & Starboard acoustic backscatter
    - Center nadir water column (low intensity)
    - Realistic speckle noise (Rayleigh / Gamma distribution)
    - Seabed texture with sand ripples / rocky patches
    - Specular high-intensity acoustic target highlights
    - True acoustic shadow zones cast away from nadir based on grazing angle
    """
    # 1. Base seabed reverberation with low-frequency spatial variation
    scale = random.uniform(0.015, 0.035)
    x = np.linspace(0, width * scale, width)
    y = np.linspace(0, height * scale, height)
    xv, yv = np.meshgrid(x, y)
    
    # Sand ripples / wave pattern
    ripple_freq = random.uniform(0.1, 0.3)
    ripple_angle = random.uniform(0, math.pi)
    ripple = np.sin(xv * math.cos(ripple_angle) * ripple_freq + yv * math.sin(ripple_angle) * ripple_freq)
    
    # Low freq background variation
    low_freq = (np.sin(xv * 0.5) * np.cos(yv * 0.5) + np.sin(xv * 0.2 + yv * 0.3)) * 0.5
    
    # Rayleigh / speckle noise for acoustic scattering
    u = np.random.uniform(0.001, 0.999, (height, width))
    rayleigh_noise = np.sqrt(-2.0 * np.log(1.0 - u))
    
    # Combine background: typical SSS mean intensity ~80-120
    base_intensity = 85.0 + 25.0 * ripple + 20.0 * low_freq
    seabed = base_intensity * (0.6 + 0.4 * rayleigh_noise)
    
    # 2. Time-Varying Gain (TVG) curve simulation across port and starboard
    mid_x = width // 2
    dist_from_nadir = np.abs(np.arange(width) - mid_x)
    tvg = 1.0 + 0.3 * (dist_from_nadir / (width / 2.0)) - 0.2 * (dist_from_nadir / (width / 2.0))**2
    seabed = seabed * tvg[np.newaxis, :]

    # 3. Center Nadir / Water Column (acoustic dead zone directly beneath towfish)
    nadir_half = max(10, nadir_width // 2)
    nadir_mask = np.zeros((height, width), dtype=np.float32)
    for w_offset in range(nadir_half):
        factor = (w_offset / max(1, nadir_half)) ** 2
        col_left = mid_x - nadir_half + w_offset
        col_right = mid_x + nadir_half - w_offset
        if 0 <= col_left < width:
            nadir_mask[:, col_left] = 1.0 - factor
        if 0 <= col_right < width:
            nadir_mask[:, col_right] = 1.0 - factor
            
    # Water column has very low acoustic backscatter (~10-25)
    water_col_noise = np.random.uniform(8, 22, (height, width))
    seabed = seabed * (1.0 - nadir_mask * 0.85) + water_col_noise * (nadir_mask * 0.85)

    # First bottom return line (bright acoustic boundary at nadir edge)
    left_br = max(0, mid_x - nadir_half)
    right_br = min(width - 1, mid_x + nadir_half)
    seabed[:, left_br:left_br+2] += np.random.uniform(40, 80, (height, 2))
    seabed[:, right_br-1:right_br+1] += np.random.uniform(40, 80, (height, 2))

    image = np.clip(seabed, 0, 255).astype(np.uint8)

    # 4. Insert Acoustic Targets with Highlight & Shadow
    placed_detections = []
    
    if targets is None:
        num_targets = random.choice([1, 2, 3])
        classes = ["wreckage", "container", "fishing_gear", "artificial_object"]
        targets = []
        for _ in range(num_targets):
            cls = random.choice(classes)
            if random.random() < 0.5:
                tx = random.randint(30, mid_x - nadir_half - 60)
                side = "port"
            else:
                tx = random.randint(mid_x + nadir_half + 30, width - 90)
                side = "starboard"
            ty = random.randint(60, height - 100)
            targets.append({"class_name": cls, "x": tx, "y": ty, "side": side})

    for tgt in targets:
        cls = tgt["class_name"]
        tx = tgt.get("x", random.randint(80, width - 120))
        ty = tgt.get("y", random.randint(80, height - 120))
        side = "port" if tx < mid_x else "starboard"

        if cls == "wreckage":
            tw, th = random.randint(45, 85), random.randint(35, 75)
            shadow_len = random.randint(55, 110)
            intensity = random.randint(220, 255)
        elif cls == "container":
            tw, th = random.randint(35, 60), random.randint(25, 45)
            shadow_len = random.randint(40, 80)
            intensity = random.randint(215, 250)
        elif cls == "fishing_gear":
            tw, th = random.randint(30, 65), random.randint(20, 50)
            shadow_len = random.randint(25, 50)
            intensity = random.randint(180, 225)
        else:  # artificial_object
            tw, th = random.randint(25, 50), random.randint(20, 45)
            shadow_len = random.randint(30, 65)
            intensity = random.randint(200, 245)

        shadow_dir = -1 if side == "port" else 1
        
        sx1 = tx + (0 if shadow_dir == 1 else -shadow_len)
        sx2 = sx1 + shadow_len
        sx1 = max(0, min(width - 1, sx1))
        sx2 = max(0, min(width, sx2))
        sy1 = max(0, ty - 2)
        sy2 = min(height, ty + th + 2)

        shadow_patch = image[sy1:sy2, sx1:sx2]
        shadow_noise = np.random.uniform(2, 18, shadow_patch.shape)
        image[sy1:sy2, sx1:sx2] = shadow_noise.astype(np.uint8)

        tgt_mask = np.zeros((th, tw), dtype=np.uint8)
        if cls == "container":
            cv2.rectangle(tgt_mask, (2, 2), (tw-3, th-3), 255, -1)
        elif cls == "wreckage":
            pts = np.array([
                [tw//4, 2], [tw-4, th//3], [tw*3//4, th-2],
                [tw//5, th-4], [2, th//2]
            ], np.int32)
            cv2.fillPoly(tgt_mask, [pts], 255)
        elif cls == "fishing_gear":
            for _ in range(8):
                pt1 = (random.randint(2, tw-2), random.randint(2, th-2))
                pt2 = (random.randint(2, tw-2), random.randint(2, th-2))
                cv2.line(tgt_mask, pt1, pt2, 255, thickness=random.randint(2, 4))
        else: # artificial_object
            cv2.circle(tgt_mask, (tw//2, th//2), min(tw, th)//2 - 2, 255, -1)

        ty_end = min(height, ty + th)
        tx_end = min(width, tx + tw)
        actual_h = ty_end - ty
        actual_w = tx_end - tx
        if actual_h > 0 and actual_w > 0:
            target_roi = tgt_mask[:actual_h, :actual_w]
            high_intensity_pixels = np.random.uniform(intensity - 20, intensity, (actual_h, actual_w))
            roi_bg = image[ty:ty_end, tx:tx_end]
            image[ty:ty_end, tx:tx_end] = np.where(target_roi > 0, high_intensity_pixels.astype(np.uint8), roi_bg)

            if shadow_dir == 1:
                bbox_x1 = float(tx)
                bbox_x2 = float(min(width - 1, tx + tw + shadow_len))
            else:
                bbox_x1 = float(max(0, tx - shadow_len))
                bbox_x2 = float(tx + tw)

            bbox_y1 = float(ty)
            bbox_y2 = float(min(height - 1, ty + th))

            conf = round(random.uniform(0.78, 0.96), 3)

            placed_detections.append({
                "bbox": {
                    "x1": bbox_x1,
                    "y1": bbox_y1,
                    "x2": bbox_x2,
                    "y2": bbox_y2,
                },
                "target_bbox": {
                    "x1": float(tx),
                    "y1": float(ty),
                    "x2": float(tx + tw),
                    "y2": float(ty + th),
                },
                "confidence": conf,
                "class_id": ["fishing_gear", "container", "wreckage", "artificial_object"].index(cls),
                "class_name": cls,
            })

    image = cv2.GaussianBlur(image, (3, 3), 0.5)
    sonar_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    return sonar_bgr, placed_detections
