from pathlib import Path
import os
import cv2
import tempfile
import numpy as np
from app.vision.vision import VisionService

from app.orchestration.coral_service import CoralService
from app.segmentation.fixture_provider import FixtureProvider
from app.cropping.cropper import BoundingBoxCropper
from app.embedding.embedding import EmbeddingService

def identification_pipeline():
    service = CoralService()
    segmenter = FixtureProvider()
    
    base_dir = Path(__file__).resolve().parents[2]
    fixtures_dir = base_dir / "dev_fixtures"
    coral_images_path = fixtures_dir / "islalarga_c001"
    
    # find all directories within dev_fixtures. one directory represents a coral 
    # and contains multiple images and resp. describing json files
    for dir in fixtures_dir.iterdir():
        
        if not dir.is_dir():
            continue

        for filename in os.listdir(dir):
            
            if not filename.lower().endswith("jpg"):
                continue
                
            print(f"processing {filename}")
            
            coral_image_path = os.path.join(dir, filename)
            coral_image = cv2.imread(coral_image_path)
            
            segmentation_result = segmenter.segment(coral_image, filename)
            
            result = service.identify(coral_image, segmentation_result.segments)
            
            with tempfile.NamedTemporaryFile(prefix=filename, suffix=".jpg", delete=False) as tmp_file:
                cv2.imwrite(tmp_file.name, result.masked_image)
                print(f"file path: {tmp_file.name}")
        

def cosine_similarity(
    embedding_a: list[float],
    embedding_b: list[float],
) -> float:
    a = np.asarray(embedding_a, dtype=np.float32)
    b = np.asarray(embedding_b, dtype=np.float32)

    return float(
        np.dot(a, b)
        / (np.linalg.norm(a) * np.linalg.norm(b))
    )


def cosine_distance(
    embedding_a: list[float],
    embedding_b: list[float],
) -> float:
    return 1.0 - cosine_similarity(
        embedding_a,
        embedding_b,
    )

def embedding_norm(embedding: list[float]) -> float:
    return float(
        np.linalg.norm(
            np.asarray(embedding, dtype=np.float32)
        )
    )

def test_embedding_before_and_after_embedding_and_masking():
    service = CoralService()
    segmenter = FixtureProvider()
    vision_service = VisionService()
    cropper = BoundingBoxCropper()
    embedding_service = EmbeddingService()
    
    base_dir = Path(__file__).resolve().parents[2]
    fixtures_dir = base_dir / "dev_fixtures"
    coral_images_path = fixtures_dir / "islalarga_c001"
    
    # find all directories within dev_fixtures. one directory represents a coral 
    # and contains multiple images and resp. describing json files
    for fixture_dir in fixtures_dir.iterdir():
        
        if not fixture_dir.is_dir():
            continue

        tmp_coral_dir = Path(f"/tmp/{fixture_dir.name}").resolve()
        tmp_coral_dir.mkdir(parents=True, exist_ok=True)

        for filename in os.listdir(fixture_dir):
            
            if not filename.lower().endswith("jpg"):
                continue
                
            print(f"processing {filename}")
            
            coral_image_path = os.path.join(fixture_dir, filename)
            coral_image = cv2.imread(coral_image_path)
            
            segmentation_result = segmenter.segment(coral_image, filename)
            segments = segmentation_result.segments
                        
            # --------------------------------------------------
            # 1. Original full image
            # --------------------------------------------------

            embedding_original = (
                embedding_service.generate_vector_embedding(coral_image)
            )

            # --------------------------------------------------
            # 2. Original image cropped to bounding box
            # --------------------------------------------------

            original_crop_result = cropper.crop(
                image=coral_image,
                segments=segments,
            )
            

            original_crop = original_crop_result.crop
            cv2.imwrite(f"{tmp_coral_dir}/original_crop.jpg", original_crop)
            assertSquareDimension(original_crop)

            embedding_original_crop = (
                embedding_service.generate_vector_embedding(
                    original_crop
                )
            )

            # --------------------------------------------------
            # 3. Masked full image
            # --------------------------------------------------

            mask_result = vision_service.mask(
                image=coral_image,
                segments=segments,
            )

            masked_image = mask_result.masked_image
            cv2.imwrite(f"{tmp_coral_dir}/original_mask.jpg", masked_image)

            embedding_masked = (
                embedding_service.generate_vector_embedding(
                    masked_image
                )
            )

            # --------------------------------------------------
            # 4. Masked image cropped to bounding box
            # --------------------------------------------------

            masked_crop_result = cropper.crop(
                image=masked_image,
                segments=segments,
            )

            masked_crop = masked_crop_result.crop
            cv2.imwrite(f"{tmp_coral_dir}/mask_crop.jpg", masked_crop)
            assertSquareDimension(masked_crop)

            embedding_masked_crop = (
                embedding_service.generate_vector_embedding(
                    masked_crop
                )
            )
            
            print(
                "Original ↔ Original Crop:",
                cosine_distance(
                    embedding_original,
                    embedding_original_crop,
                ),
            )

            print(
                "Original ↔ Masked:",
                cosine_distance(
                    embedding_original,
                    embedding_masked,
                ),
            )

            print(
                "Original Crop ↔ Masked Crop:",
                cosine_distance(
                    embedding_original_crop,
                    embedding_masked_crop,
                ),
            )

            print(
                "Masked ↔ Masked Crop:",
                cosine_distance(
                    embedding_masked,
                    embedding_masked_crop,
                )
            )
            
            print(
                "Original norm:",
                embedding_norm(embedding_original),
            )

            print(
                "Original crop norm:",
                embedding_norm(embedding_original_crop),
            )

            print(
                "Masked norm:",
                embedding_norm(embedding_masked),
            )

            print(
                "Masked crop norm:",
                embedding_norm(embedding_masked_crop),
            )

def assertSquareDimension(original_crop):
    assert original_crop.shape[0] == original_crop.shape[1]
            
            
    
    