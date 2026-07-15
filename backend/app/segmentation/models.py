from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class Point:
    x: int
    y: int


@dataclass(slots=True)
class BoundingBox:
    x: int
    y: int
    width: int
    height: int


@dataclass(slots=True)
class Segment:
    id: int
    polygon: List[Point]
    bbox: BoundingBox
    predictedIoU: float
    stabilityScore: float


@dataclass(slots=True)
class SegmentationResult:
    coralId: str | None = None
    image_width: int = 0
    image_height: int = 0
    segments: List[Segment] = field(default_factory=list)
