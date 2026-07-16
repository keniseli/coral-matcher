from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from app.domain.models import BoundingBox, Point
import cv2
import numpy as np
from app.domain.models import Segment
from app.storage import save_debug_image

def export_segmentation_fixture(image: np.ndarray, image_filename: str, masks: list[dict[str, Any]]) -> None:
    base_dir = Path(__file__).resolve().parents[2]
    output_dir = base_dir / "dev_fixtures"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    match = re.search(r"(?:^|_)([A-Za-z]+)_T\d+_c(\d+)(?:_[A-Z])?\.(?:jpe?g|png|bmp|tif|tiff)", image_filename, re.I)
    site = match.group(1).lower() if match else "default"
    coral_id = f"c{match.group(2)}" if match else "default"
    fixture_stem = f"{site}_{coral_id}"

    target_image_path = output_dir / f"{fixture_stem}.jpg"
    target_json_path = output_dir / f"{fixture_stem}.json"

    save_debug_image(image, str(target_image_path))

    segments: list[dict[str, Any]] = []
    for index, mask_record in enumerate(masks):
        segmentation = mask_record.get("segmentation")
        bbox = mask_record.get("bbox", [0, 0, 0, 0])
        polygon: list[list[int]] = []
        if isinstance(segmentation, np.ndarray):
            mask = (segmentation > 0).astype(np.uint8) * 255

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            if contours:
                contour = max(contours, key=cv2.contourArea)
                polygon = [[int(x), int(y)] for x, y in contour.reshape(-1, 2)]

        segments.append({
            "id": index,
            "polygon": polygon,
            "bbox": {
                "x": int(bbox[0]),
                "y": int(bbox[1]),
                "width": int(bbox[2]),
                "height": int(bbox[3]),
            },
            "predictedIoU": float(mask_record.get("predicted_iou", 0.0)),
            "stabilityScore": float(mask_record.get("stability_score", 0.0)),
        })

    height, width = image.shape[:2]
    payload = {
        "coralId": coral_id,
        "image": {
            "width": width,
            "height": height,
        },
        "segments": segments,
    }

    target_json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
