from __future__ import annotations

from typing import List
import uuid
from app.orchestration.models import IdentifyRequest, IdentifyResult
import numpy as np
import os

from app.cropping.cropper import BoundingBoxCropper
from app.embedding.embedding import EmbeddingService
from app.segmentation.models import SegmentationResult
from app.segmentation.provider_factory import get_segmentation_provider
from app.domain.observation import Observation
from app.orchestration.models import ConfirmResult
from app.persistence.observation_repository import ObservationRepository
from app.domain.models import Segment, ObservationCandidate
from app.persistence.storage import upload_image_to_bucket


class CoralService:
    """
    Business logic for coral segmentation and identification.

    The HTTP layer should only call this service.
    """
    
    DISTANCE_THRESHOLD = float(os.environ.get("DISTANCE_THRESHOLD", "0.2"))

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

    def find_similar_observations(self, image: np.ndarray, segment: Segment) -> list[ObservationCandidate]:
        """
        Finds similar observations by first detecting the embedding and then comparing it against
        what is stored in the db.
        """
        
        identify_result = self.identify(image, [segment])
        candidates = self.observation_repository.find_similar(identify_result.embedding)
        return [candidate for candidate in candidates if candidate.distance < self.DISTANCE_THRESHOLD]

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

    def confirm_observation(self, image: np.ndarray,
        segments: list[Segment],
        related_observation_id: str,
        dive_site: str,
        coral_name: str) -> ConfirmResult:
        
        if related_observation_id:
            related_observation = self.observation_repository.find_by_id(related_observation_id)
            coral_name = related_observation.coral_name
            dive_site = related_observation.dive_site
        
        observation = Observation()
        observation.coral_name = coral_name
        observation.dive_site = dive_site
        observation.embedding = self.embedding_service.generate_vector_embedding(image)

        directory_in_bucket = f"{dive_site}/{coral_name}"
        image_path = upload_image_to_bucket(image, f"{directory_in_bucket}/{observation.created_at}")
        observation.image_filename = str(observation.created_at)
        height, width = image.shape[:2]
        observation.image_height = height
        observation.image_width = width
        observation.image_path = image_path
        
        crop_result = self.cropper.crop(image, segments)
        observation.cropped_image_path = upload_image_to_bucket(
            crop_result.crop, f"{directory_in_bucket}/cropped_{observation.created_at}"
        )
        
        observation.monitoring_session_id = uuid.UUID("75e06e38-78cd-41bb-aa4e-409ba4fb5c91")

        self.observation_repository.save(observation)

        result = ConfirmResult(observation)
        return result