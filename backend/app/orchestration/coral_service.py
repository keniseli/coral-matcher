from __future__ import annotations

from typing import List

from app.orchestration.models import IdentifyRequest, IdentifyResult
import numpy as np

from app.cropping.cropper import BoundingBoxCropper
from app.embedding.embedding import EmbeddingService
from app.segmentation.models import SegmentationResult
from app.segmentation.provider_factory import get_segmentation_provider
from app.domain.observation import Observation
from app.persistence.observation_repository import ObservationRepository
from app.domain.models import Segment

class CoralService:
    """
    Business logic for coral segmentation and identification.

    The HTTP layer should only call this service.
    """

    def __init__(self) -> None:
        self.segmenter = get_segmentation_provider()
        self.cropper = BoundingBoxCropper()
        self.embedding_service = EmbeddingService()
        self.observation_repository = ObservationRepository()

    def segment_image(
        self,
        image: np.ndarray,
        filename: str,
    ) -> SegmentationResult :
        """
        Runs CoralSCOP (or fixture provider) to find coral segment(s) in the given picture.

        Returns SegmentationResult.
        """

        return self.segmenter.segment(image, filename)

    def find_similar_observations(self, image: np.ndarray, segment: Segment) -> list[Observation]:
        """
        Finds similar observations by first detecting the embedding and then comparing it against
        what is stored in the db.
        """
        
        identify_result = self.identify(image, [segment])
        # TODO: this will always return observations. Should find only actually similar ones
        return self.observation_repository.find_similar(identify_result.embedding)

    def identify(self, image: np.ndarray, segments: list[Segment]) -> IdentifyResult:
        """
        Creates one merged crop from the selected segments and
        generates an embedding.
        """
        if not segments:
            raise ValueError("No segments selected.")

        crop_result = self.cropper.crop(image=image, segments=segments)

        embedding = self.embedding_service.generate_vector_embedding(crop_result.crop)

        return IdentifyResult(
            crop=crop_result.crop,
            embedding=embedding,
            selected_segments=segments,
        )