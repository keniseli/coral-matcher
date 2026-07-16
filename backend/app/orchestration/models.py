from app.domain.models import Segment
import numpy as np

from dataclasses import dataclass


@dataclass(slots=True)
class IdentifyResult:
    crop: np.ndarray
    embedding: list[float]
    selected_segments: list[Segment]


@dataclass(slots=True)
class IdentifyRequest:
    image: np.ndarray
    selected_segments: list[Segment]