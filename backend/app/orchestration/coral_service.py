from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np

from app.cropping.cropper import BoundingBoxCropper
from app.embedding.embedding import EmbeddingService
from app.segmentation.models import Segment, SegmentationResult
from app.segmentation.provider_factory import get_segmentation_provider

@dataclass(slots=True)
class IdentifyRequest:
    image: np.ndarray
    selected_segments: list[Segment]

@dataclass(slots=True)
class IdentifyResult:
    crop: np.ndarray
    embedding: list[float]
    selected_segments: list[Segment]


class CoralService:
    """
    Business logic for coral segmentation and identification.

    The HTTP layer should only call this service.
    """

    def __init__(self) -> None:
        self.segmenter = get_segmentation_provider()
        self.cropper = BoundingBoxCropper()
        self.embeddingService = EmbeddingService()

    # ------------------------------------------------------------------
    # Segmentation
    # ------------------------------------------------------------------

    def segment_image(
        self,
        image: np.ndarray,
        filename: str,
    ) -> SegmentationResult :
        """
        Runs CoralSCOP (or fixture provider).

        Returns SegmentationResult.
        """

        return self.segmenter.segment(image, filename)

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------

    def identify(self, identifyRequest: IdentifyRequest) -> IdentifyResult:
        """
        Creates one merged crop from the selected segments and
        generates an embedding.
        """
        selected_segments = identifyRequest.selected_segments
        if not identifyRequest.selected_segments:
            raise ValueError("No segments selected.")

        crop_result = self.cropper.crop(image=identifyRequest.image, segments=selected_segments)

        embedding = self.embeddingService.generate_vector_embedding(crop_result.crop)

        return IdentifyResult(
            crop=crop_result.crop,
            embedding=embedding,
            selected_segments=selected_segments,
        )