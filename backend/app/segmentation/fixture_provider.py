from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import List

from app.domain.models import BoundingBox, Point, Segment
import numpy as np

from app.segmentation.models import SegmentationResult
from app.segmentation.segmentation_provider import SegmentationProvider

logger = logging.getLogger(__name__)


class FixtureProvider(SegmentationProvider):
    def __init__(self, fixtures_dir: str | os.PathLike[str] | None = None):
        base_dir = Path(__file__).resolve().parents[2]
        self.fixtures_dir = Path(fixtures_dir) if fixtures_dir is not None else base_dir / "dev_fixtures"
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)

    def _fixture_key_for_filename(self, image_filename: str) -> tuple[str, str]:
        if not image_filename:
            return "default", "default"

        match = re.search(r"(?:^|_)([A-Za-z]+)_T\d+_c(\d+)(?:_[A-Z])?\.(?:jpe?g|png|bmp|tif|tiff)", image_filename, re.I)
        if not match:
            return "default", "default"

        site = match.group(1).lower()
        coral_id = f"c{match.group(2)}"
        return site, coral_id

    def _resolve_fixture_path(self, image_filename: str) -> Path:
        site, coral_id = self._fixture_key_for_filename(image_filename)
        candidate_stem = f"{site}_{coral_id}"
        candidate_json = self.fixtures_dir / f"{candidate_stem}.json"
        if candidate_json.exists():
            logger.info(f"[Fixture] Loaded fixture: {candidate_stem}")
            return candidate_json

        default_json = self.fixtures_dir / "default.json"
        if default_json.exists():
            logger.info("[Fixture] Fixture not found, using default fixture.")
            return default_json

        raise FileNotFoundError(f"No fixture found for {image_filename} and no default fixture exists at {default_json}")

    def segment(self, image: np.ndarray | None, image_filename: str) -> SegmentationResult:
        fixture_path = self._resolve_fixture_path(image_filename)
        with fixture_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        image_payload = payload.get("image", {})
        segments_payload = payload.get("segments", [])

        segments: List[Segment] = []
        for segment_payload in segments_payload:
            polygon = [
                Point(x=int(point[0]), y=int(point[1]))
                for point in segment_payload.get("polygon", [])
            ]
            bbox_payload = segment_payload.get("bbox", {})
            bbox = BoundingBox(
                x=int(bbox_payload.get("x", 0)),
                y=int(bbox_payload.get("y", 0)),
                width=int(bbox_payload.get("width", 0)),
                height=int(bbox_payload.get("height", 0)),
            )
            segments.append(
                Segment(
                    id=int(segment_payload.get("id", 0)),
                    polygon=polygon,
                    bbox=bbox,
                    predictedIoU=float(segment_payload.get("predictedIoU", 0.0)),
                    stabilityScore=float(segment_payload.get("stabilityScore", 0.0)),
                )
            )

        return SegmentationResult(
            image_width=int(image_payload.get("width", 0)),
            image_height=int(image_payload.get("height", 0)),
            segments=segments,
        )
