import math
import numpy as np


def sonar_offset_to_gps(
    ref_lat: float,
    ref_lon: float,
    heading_deg: float,
    sonar_range_m: float,
    target_offset_x_px: float,
    target_offset_y_px: float,
    image_width_px: float,
) -> dict:
    heading_rad = math.radians(heading_deg)

    along_track = (target_offset_y_px / image_width_px) * sonar_range_m * 2
    across_track = (target_offset_x_px / image_width_px) * sonar_range_m * 2

    delta_lat = (
        along_track * math.cos(heading_rad)
        + across_track * math.sin(heading_rad)
    ) / 111320.0

    delta_lon = (
        along_track * math.sin(heading_rad)
        - across_track * math.cos(heading_rad)
    ) / (111320.0 * math.cos(math.radians(ref_lat)))

    return {
        "latitude": ref_lat + delta_lat,
        "longitude": ref_lon + delta_lon,
    }


def geo_localize_detection(
    detection: dict,
    image_metadata: dict,
) -> dict:
    ref_lat = image_metadata.get("latitude", 0.0) or 0.0
    ref_lon = image_metadata.get("longitude", 0.0) or 0.0
    heading = image_metadata.get("heading", 0.0) or 0.0
    sonar_range = image_metadata.get("sonar_range", 100.0) or 100.0
    depth = image_metadata.get("depth", 0.0) or 0.0
    image_width = image_metadata.get("image_width", 640)

    bbox = detection.get("bbox", {})
    cx = (bbox.get("x1", 0) + bbox.get("x2", 0)) / 2.0
    cy = (bbox.get("y1", 0) + bbox.get("y2", 0)) / 2.0

    coords = sonar_offset_to_gps(
        ref_lat, ref_lon, heading, sonar_range, cx - image_width / 2, cy, image_width
    )

    return {
        "latitude": coords["latitude"],
        "longitude": coords["longitude"],
        "depth": depth,
    }
