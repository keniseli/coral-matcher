from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class RulerGeometry:
    center: tuple[float, float]
    angle_degrees: float
    width: float
    height: float
    mask: np.ndarray


@dataclass(frozen=True)
class RotatedRuler:
    """
    Result of rotating and cropping a detected ruler.

    image:
        Cropped original image with the ruler's long axis horizontal.

    mask:
        Cropped binary ruler mask in the same coordinate system as image.

    crop:
        Crop rectangle in the rotated full-image coordinate system:
        (x, y, width, height).
    """
    image: np.ndarray
    mask: np.ndarray
    crop: tuple[int, int, int, int]


@dataclass(frozen=True)
class TickDetection:
    signal: np.ndarray
    threshold: float
    top_signal: np.ndarray
    bottom_signal: np.ndarray


@dataclass(frozen=True)
class TickPositions:
    positions: np.ndarray
    strengths: np.ndarray


@dataclass(frozen=True)
class RulerScale:
    pixels_per_mm: float
    confidence: float
    supporting_ticks: np.ndarray
    spacing_residual: float