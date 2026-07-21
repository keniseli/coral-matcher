from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

import third_party.coralsrt.vision_transformer as vits
import third_party.coralsrt.dvt.models as DVT

from app.domain.models import Segment
from app.segmentation.fixture_provider import FixtureProvider
from app.cropping.cropper import BoundingBoxCropper


# ============================================================================
# Configuration
# ============================================================================

IMAGE_SIZE = 512
PATCH_SIZE = 16

ARCHITECTURE = "vit_base"
FEATURE_DIMENSION = 768

ROTATIONS = [0]

POSITIVE_THRESHOLD = 0.90
NEGATIVE_THRESHOLD = 0.85


# ============================================================================
# Data models
# ============================================================================

@dataclass
class CoralSample:
    dive_site: str
    coral_id: str
    image_filename: str
    image_path: Path
    segment: Segment


# ============================================================================
# Fixture loading
# ============================================================================

def load_fixture_samples(
    fixtures_dir: Path,
) -> list[CoralSample]:

    samples: list[CoralSample] = []

    provider = FixtureProvider(fixtures_dir)

    json_files = sorted(fixtures_dir.rglob("*.json"))

    for json_path in json_files:

        # ------------------------------------------------------------------
        # Read metadata from the fixture JSON
        # ------------------------------------------------------------------

        with json_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        coral_id = payload.get("coralId")

        if not coral_id:
            print(f"Skipping {json_path}: missing coralId")
            continue

        # The directory name is expected to be something like:
        #
        #   islalarga_c001
        #
        # This becomes our colony identity.
        dive_site = json_path.parent.name

        # ------------------------------------------------------------------
        # Find matching image
        #
        # Fixtures may contain .jpg/.JPG/etc.
        # ------------------------------------------------------------------

        image_path: Optional[Path] = None

        for extension in [".jpg", ".JPG", ".jpeg", ".JPEG", ".png", ".PNG"]:

            candidate = json_path.with_suffix(extension)

            if candidate.exists():
                image_path = candidate
                break

        if image_path is None:
            print(f"Skipping {json_path}: matching image not found")
            continue

        # ------------------------------------------------------------------
        # Let the production FixtureProvider parse the segmentation result
        # ------------------------------------------------------------------

        try:

            segmentation = provider.segment(
                image=None,
                image_filename=image_path.name,
            )

        except FileNotFoundError as exc:

            print(
                f"Skipping {json_path}: "
                f"FixtureProvider could not find fixture: {exc}"
            )

            continue

        if not segmentation.segments:
            print(f"Skipping {json_path}: no segments")
            continue

        # ------------------------------------------------------------------
        # Select only the largest segment.
        #
        # This deliberately mirrors the current evaluation assumption:
        # the largest segment is the primary coral colony.
        # ------------------------------------------------------------------

        largest_segment = max(
            segmentation.segments,
            key=lambda segment: segment.bbox.width * segment.bbox.height,
        )

        samples.append(
            CoralSample(
                dive_site=dive_site,
                coral_id=coral_id,
                image_filename=image_path.name,
                image_path=image_path,
                segment=largest_segment,
            )
        )

    return samples


# ============================================================================
# DINO + CoralSRT embedding model
# ============================================================================

class DinoCoralSRTEmbeddingModel:

    def __init__(
        self,
        dino_weights: Path,
        rectifier_weights: Path,
        device: torch.device,
    ):

        self.device = device

        print(f"Using device: {self.device}")

        # ------------------------------------------------------------------
        # DINO
        # ------------------------------------------------------------------

        print("Loading DINO model...")

        self.dino = vits.__dict__[ARCHITECTURE](
            patch_size=PATCH_SIZE,
            num_classes=0,
        )

        for parameter in self.dino.parameters():
            parameter.requires_grad = False

        self.dino.eval()
        self.dino.to(self.device)

        state_dict = torch.load(
            dino_weights,
            map_location="cpu",
            weights_only=False
        )

        if "teacher" in state_dict:
            state_dict = state_dict["teacher"]

        state_dict = {
            key.replace("module.", ""): value
            for key, value in state_dict.items()
        }

        state_dict = {
            key.replace("backbone.", ""): value
            for key, value in state_dict.items()
        }

        message = self.dino.load_state_dict(
            state_dict,
            strict=False,
        )

        print(
            "DINO weights loaded:"
        )

        print(message)

        # ------------------------------------------------------------------
        # CoralSRT rectifier
        # ------------------------------------------------------------------

        print("Loading CoralSRT rectifier...")

        self.rectifier = DVT.Denoiser(
            noise_map_height=IMAGE_SIZE // PATCH_SIZE,
            noise_map_width=IMAGE_SIZE // PATCH_SIZE,
            feat_dim=FEATURE_DIMENSION,
            vit=None,
            num_blocks=1,
        )

        rectifier_checkpoint = torch.load(
            rectifier_weights,
            map_location="cpu",
            weights_only=False
        )

        rectifier_state_dict = {
            key: value
            for key, value in rectifier_checkpoint["denoiser"].items()
        }

        self.rectifier.load_state_dict(
            rectifier_state_dict,
            strict=True,
        )

        self.rectifier.eval()
        self.rectifier.to(self.device)

        # ------------------------------------------------------------------
        # Same normalization used by DINO / ImageNet pretrained models
        # ------------------------------------------------------------------

        self.transform = transforms.Compose(
            [
                transforms.Resize(
                    (IMAGE_SIZE, IMAGE_SIZE)
                ),

                transforms.ToTensor(),

                transforms.Normalize(
                    mean=[
                        0.485,
                        0.456,
                        0.406,
                    ],
                    std=[
                        0.229,
                        0.224,
                        0.225,
                    ],
                ),
            ]
        )

    # ----------------------------------------------------------------------
    # Image rotation
    # ----------------------------------------------------------------------

    def rotate_image(
        self,
        image: np.ndarray,
        angle: int,
    ) -> np.ndarray:

        if angle == 0:
            return image

        if angle == 90:
            return cv2.rotate(
                image,
                cv2.ROTATE_90_CLOCKWISE,
            )

        if angle == 180:
            return cv2.rotate(
                image,
                cv2.ROTATE_180,
            )

        if angle == 270:
            return cv2.rotate(
                image,
                cv2.ROTATE_90_COUNTERCLOCKWISE,
            )

        raise ValueError(
            f"Unsupported rotation angle: {angle}"
        )

    # ----------------------------------------------------------------------
    # Polygon rotation
    # ----------------------------------------------------------------------

    def rotate_polygon(
        self,
        polygon: list[tuple[int, int]],
        width: int,
        height: int,
        angle: int,
    ) -> list[tuple[int, int]]:

        if angle == 0:
            return polygon

        rotated_polygon = []

        for x, y in polygon:

            if angle == 90:

                new_x = height - 1 - y
                new_y = x

            elif angle == 180:

                new_x = width - 1 - x
                new_y = height - 1 - y

            elif angle == 270:

                new_x = y
                new_y = width - 1 - x

            else:

                raise ValueError(
                    f"Unsupported rotation angle: {angle}"
                )

            rotated_polygon.append(
                (
                    new_x,
                    new_y,
                )
            )

        return rotated_polygon

    # ----------------------------------------------------------------------
    # Generate embedding
    # ----------------------------------------------------------------------

    @torch.inference_mode()
    def generate_embedding(
        self,
        image: np.ndarray,
        polygon: list[tuple[int, int]],
    ) -> np.ndarray:

        if image is None or image.size == 0:
            raise ValueError(
                "Cannot generate embedding from empty image."
            )

        if not polygon:
            raise ValueError(
                "Cannot generate embedding from empty polygon."
            )

        image_height, image_width = image.shape[:2]

        # ------------------------------------------------------------------
        # Sanity check polygon bounds
        # ------------------------------------------------------------------

        polygon_array = np.asarray(
            polygon,
            dtype=np.int32,
        )

        polygon_x_min = int(polygon_array[:, 0].min())
        polygon_x_max = int(polygon_array[:, 0].max())

        polygon_y_min = int(polygon_array[:, 1].min())
        polygon_y_max = int(polygon_array[:, 1].max())

        if (
            polygon_x_max < 0
            or polygon_y_max < 0
            or polygon_x_min >= image_width
            or polygon_y_min >= image_height
        ):

            raise ValueError(
                "Polygon lies entirely outside image. "
                f"Image size: {image_width}x{image_height}. "
                f"Polygon bounds: "
                f"x={polygon_x_min}..{polygon_x_max}, "
                f"y={polygon_y_min}..{polygon_y_max}"
            )

        # ------------------------------------------------------------------
        # Convert BGR → RGB → PIL
        # ------------------------------------------------------------------

        rgb_image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB,
        )

        pil_image = Image.fromarray(
            rgb_image
        )

        tensor_image = self.transform(
            pil_image
        ).unsqueeze(0).to(self.device)

        # ------------------------------------------------------------------
        # DINO patch features
        # ------------------------------------------------------------------

        layers = self.dino.get_intermediate_layers(
            tensor_image,
            1,
        )

        raw_features = layers[0][0, 1:, :]

        feature_grid_size = IMAGE_SIZE // PATCH_SIZE

        raw_features = raw_features.reshape(
            feature_grid_size,
            feature_grid_size,
            FEATURE_DIMENSION,
        )

        raw_features = raw_features.unsqueeze(0).float()

        # ------------------------------------------------------------------
        # CoralSRT feature rectification
        # ------------------------------------------------------------------

        rectified_features = self.rectifier(
            raw_features
        )

        # Shape should be:
        #
        # [1, feature_height, feature_width, feature_dim]
        #
        # depending on the CoralSRT implementation.
        #
        # The repository's Denoiser output is expected to preserve the
        # spatial feature map.
        # ------------------------------------------------------------------

        if rectified_features.ndim != 4:
            raise ValueError(
                "Unexpected CoralSRT output shape: "
                f"{rectified_features.shape}"
            )

        # Convert to:
        #
        # [feature_height, feature_width, feature_dim]
        #
        rectified_features = rectified_features[0]

        # ------------------------------------------------------------------
        # Create mask in ORIGINAL CROP coordinates
        # ------------------------------------------------------------------

        crop_mask = np.zeros(
            (
                image_height,
                image_width,
            ),
            dtype=np.uint8,
        )

        cv2.fillPoly(
            crop_mask,
            [
                polygon_array
            ],
            1,
        )

        mask_pixel_count = int(
            np.count_nonzero(crop_mask)
        )

        if mask_pixel_count == 0:
            raise ValueError(
                "Polygon produced zero mask pixels. "
                f"Image size: {image_width}x{image_height}. "
                f"Polygon bounds: "
                f"x={polygon_x_min}..{polygon_x_max}, "
                f"y={polygon_y_min}..{polygon_y_max}"
            )

        # ------------------------------------------------------------------
        # Downsample mask to DINO feature resolution
        # ------------------------------------------------------------------

        feature_mask = cv2.resize(
            crop_mask,
            (
                feature_grid_size,
                feature_grid_size,
            ),
            interpolation=cv2.INTER_AREA,
        )

        feature_mask = feature_mask > 0

        feature_mask_tensor = torch.from_numpy(
            feature_mask
        ).to(self.device)

        # ------------------------------------------------------------------
        # Sanity check feature-map coverage
        # ------------------------------------------------------------------

        feature_pixel_count = int(
            feature_mask_tensor.sum().item()
        )

        if feature_pixel_count == 0:
            raise ValueError(
                "Coral polygon produced no feature-map pixels. "
                f"Image size: {image_width}x{image_height}. "
                f"Polygon bounds: "
                f"x={polygon_x_min}..{polygon_x_max}, "
                f"y={polygon_y_min}..{polygon_y_max}. "
                f"Mask pixels: {mask_pixel_count}. "
                f"Feature grid: "
                f"{feature_grid_size}x{feature_grid_size}."
            )

        # ------------------------------------------------------------------
        # Extract coral-covered patch features
        # ------------------------------------------------------------------

        #coral_features = rectified_features[
        #    feature_mask_tensor
        #]
        coral_features = raw_features[0][feature_mask]

        if coral_features.numel() == 0:
            raise ValueError(
                "Feature mask selected zero CoralSRT features."
            )

        # ------------------------------------------------------------------
        # Average all coral patch features
        # ------------------------------------------------------------------

        embedding = coral_features.mean(
            dim=0
        )

        # ------------------------------------------------------------------
        # L2 normalize
        # ------------------------------------------------------------------

        embedding = F.normalize(
            embedding,
            dim=0,
        )

        return embedding.cpu().numpy()


# ============================================================================
# Production-like crop preparation
# ============================================================================

def prepare_cropped_sample(
    image: np.ndarray,
    segment: Segment,
    cropper: BoundingBoxCropper,
) -> tuple[np.ndarray, list[tuple[int, int]]]:

    # ----------------------------------------------------------------------
    # Use the production cropper
    # ----------------------------------------------------------------------

    crop_result = cropper.crop(
        image=image,
        segments=[segment],
    )

    crop = crop_result.crop

    square_box = crop_result.square_box

    # ----------------------------------------------------------------------
    # Translate the original-image polygon into crop coordinates
    #
    # The crop is based on square_box:
    #
    # crop_x = original_x - square_box.x
    # crop_y = original_y - square_box.y
    #
    # This is valid even when square_box extends beyond the original image,
    # because BoundingBoxCropper pads the image before extracting the crop.
    # ----------------------------------------------------------------------

    crop_polygon = []

    for point in segment.polygon:

        crop_polygon.append(
            (
                point.x - square_box.x,
                point.y - square_box.y,
            )
        )

    # ----------------------------------------------------------------------
    # Sanity checks
    # ----------------------------------------------------------------------

    crop_height, crop_width = crop.shape[:2]

    polygon_array = np.asarray(
        crop_polygon,
        dtype=np.int32,
    )

    polygon_x_min = int(
        polygon_array[:, 0].min()
    )

    polygon_x_max = int(
        polygon_array[:, 0].max()
    )

    polygon_y_min = int(
        polygon_array[:, 1].min()
    )

    polygon_y_max = int(
        polygon_array[:, 1].max()
    )

    if (
        polygon_x_max < 0
        or polygon_y_max < 0
        or polygon_x_min >= crop_width
        or polygon_y_min >= crop_height
    ):

        raise ValueError(
            "Translated polygon lies entirely outside crop. "
            f"Crop size: {crop_width}x{crop_height}. "
            f"Polygon bounds: "
            f"x={polygon_x_min}..{polygon_x_max}, "
            f"y={polygon_y_min}..{polygon_y_max}. "
            f"Square box: {square_box}"
        )

    # ----------------------------------------------------------------------
    # Explicit mask sanity check
    # ----------------------------------------------------------------------

    debug_mask = np.zeros(
        (
            crop_height,
            crop_width,
        ),
        dtype=np.uint8,
    )

    cv2.fillPoly(
        debug_mask,
        [
            polygon_array
        ],
        255,
    )

    mask_pixels = int(
        np.count_nonzero(debug_mask)
    )

    if mask_pixels == 0:
        raise ValueError(
            "Translated polygon produced zero mask pixels. "
            f"Crop size: {crop_width}x{crop_height}. "
            f"Square box: {square_box}"
        )

    return crop, crop_polygon


# ============================================================================
# Embedding generation
# ============================================================================

def generate_all_embeddings(
    samples: list[CoralSample],
    model: DinoCoralSRTEmbeddingModel,
    cropper: BoundingBoxCropper,
) -> dict:

    embeddings = {}

    total = len(samples)

    for index, sample in enumerate(samples, start=1):

        print(
            f"[{index}/{total}] "
            f"{sample.dive_site} / "
            f"{sample.coral_id} / "
            f"{sample.image_filename}"
        )

        image = cv2.imread(
            str(sample.image_path)
        )

        if image is None:
            print(
                "  WARNING: Could not read image"
            )

            continue

        try:

            crop, crop_polygon = prepare_cropped_sample(
                image=image,
                segment=sample.segment,
                cropper=cropper,
            )

            crop_height, crop_width = crop.shape[:2]

            print(
                f"  crop: "
                f"{crop_width}x{crop_height}"
            )

            # --------------------------------------------------------------
            # Generate embeddings for all four rotations
            # --------------------------------------------------------------

            rotation_embeddings = {}

            embedding = model.generate_embedding(crop, crop_polygon)

            rotation_embeddings[0] = embedding

            key = (
                sample.dive_site,
                sample.coral_id,
                sample.image_filename,
                sample.segment.id,
            )

            embeddings[key] = rotation_embeddings

        except Exception as exc:

            print(
                f"  ERROR: {exc}"
            )

    return embeddings


# ============================================================================
# Similarity
# ============================================================================

def cosine_similarity(
    embedding_a: np.ndarray,
    embedding_b: np.ndarray,
) -> float:

    return float(
        np.dot(
            embedding_a,
            embedding_b,
        )
    )


def average_rotation_embedding(
    rotation_embeddings: dict[int, np.ndarray],
) -> np.ndarray:

    stacked = np.stack(
        [
            rotation_embeddings[angle]
            for angle in ROTATIONS
        ],
        axis=0,
    )

    average = np.mean(
        stacked,
        axis=0,
    )

    norm = np.linalg.norm(
        average
    )

    if norm == 0:
        raise ValueError(
            "Average embedding has zero norm."
        )

    return average / norm


# ============================================================================
# Evaluation
# ============================================================================

def evaluate_embeddings(
    embeddings: dict,
):

    samples = list(
        embeddings.keys()
    )

    positive_matches = []
    negative_matches = []

    positive_details = []
    negative_details = []

    for index_a in range(
        len(samples)
    ):

        key_a = samples[index_a]

        site_a, coral_a, image_a, segment_a = key_a

        embedding_a = average_rotation_embedding(
            embeddings[key_a]
        )

        for index_b in range(
            index_a + 1,
            len(samples)
        ):

            key_b = samples[index_b]

            site_b, coral_b, image_b, segment_b = key_b

            embedding_b = average_rotation_embedding(
                embeddings[key_b]
            )

            similarity = cosine_similarity(
                embedding_a,
                embedding_b,
            )

            if (
                site_a == site_b
                and coral_a == coral_b
            ):

                positive_matches.append(
                    similarity
                )

                positive_details.append(
                    (
                        similarity,
                        key_a,
                        key_b,
                    )
                )

            else:

                negative_matches.append(
                    similarity
                )

                negative_details.append(
                    (
                        similarity,
                        key_a,
                        key_b,
                    )
                )

    # ----------------------------------------------------------------------
    # Print statistics
    # ----------------------------------------------------------------------

    print()
    print("=" * 80)
    print(
        "CORAL EMBEDDING SIMILARITY EVALUATION"
    )
    print("=" * 80)

    print()
    print(
        f"Loaded {len(samples)} representative segments"
    )

    print()
    print("-" * 80)
    print(
        "ROTATION-AVERAGED POSITIVE MATCHES"
    )
    print("-" * 80)

    if positive_matches:

        print(
            f"Count:   {len(positive_matches)}"
        )

        print(
            f"Min:     {min(positive_matches):.4f}"
        )

        print(
            f"Mean:    {np.mean(positive_matches):.4f}"
        )

        print(
            f"Median:  {np.median(positive_matches):.4f}"
        )

        print(
            f"Max:     {max(positive_matches):.4f}"
        )

    print()
    print("-" * 80)
    print(
        "ROTATION-AVERAGED NEGATIVE MATCHES"
    )
    print("-" * 80)

    if negative_matches:

        print(
            f"Count:   {len(negative_matches)}"
        )

        print(
            f"Min:     {min(negative_matches):.4f}"
        )

        print(
            f"Mean:    {np.mean(negative_matches):.4f}"
        )

        print(
            f"Median:  {np.median(negative_matches):.4f}"
        )

        print(
            f"Max:     {max(negative_matches):.4f}"
        )

    # ----------------------------------------------------------------------
    # Target evaluation
    # ----------------------------------------------------------------------

    print()
    print("=" * 80)
    print(
        "TARGET EVALUATION"
    )
    print("=" * 80)

    if positive_matches:

        lowest_positive = min(
            positive_matches
        )

        print()
        print(
            f"Lowest positive similarity: "
            f"{lowest_positive:.4f}"
        )

        if lowest_positive > POSITIVE_THRESHOLD:

            print(
                f"PASS: All positive matches > "
                f"{POSITIVE_THRESHOLD:.2f}"
            )

        else:

            print(
                f"FAIL: At least one positive match <= "
                f"{POSITIVE_THRESHOLD:.2f}"
            )

    if negative_matches:

        highest_negative = max(
            negative_matches
        )

        print()
        print(
            f"Highest negative similarity: "
            f"{highest_negative:.4f}"
        )

        if highest_negative < NEGATIVE_THRESHOLD:

            print(
                f"PASS: All negative matches < "
                f"{NEGATIVE_THRESHOLD:.2f}"
            )

        else:

            print(
                f"FAIL: At least one negative match >= "
                f"{NEGATIVE_THRESHOLD:.2f}"
            )

    # ----------------------------------------------------------------------
    # Hardest positive
    # ----------------------------------------------------------------------

    if positive_details:

        hardest_positive = min(
            positive_details,
            key=lambda item: item[0],
        )

        similarity, key_a, key_b = hardest_positive

        print()
        print("=" * 80)
        print(
            "MOST DIFFICULT POSITIVE COMPARISON"
        )
        print("=" * 80)

        print(
            f"{key_a[0]} / "
            f"{key_a[1]} / "
            f"{key_a[2]} / "
            f"segment {key_a[3]}"
        )

        print(
            f"{key_b[0]} / "
            f"{key_b[1]} / "
            f"{key_b[2]} / "
            f"segment {key_b[3]}"
        )

        print(
            f"Similarity: "
            f"{similarity:.4f}"
        )

    # ----------------------------------------------------------------------
    # Hardest negative
    # ----------------------------------------------------------------------

    if negative_details:

        hardest_negative = max(
            negative_details,
            key=lambda item: item[0],
        )

        similarity, key_a, key_b = hardest_negative

        print()
        print("=" * 80)
        print(
            "MOST DIFFICULT NEGATIVE COMPARISON"
        )
        print("=" * 80)

        print(
            f"{key_a[0]} / "
            f"{key_a[1]} / "
            f"{key_a[2]} / "
            f"segment {key_a[3]}"
        )

        print(
            f"{key_b[0]} / "
            f"{key_b[1]} / "
            f"{key_b[2]} / "
            f"segment {key_b[3]}"
        )

        print(
            f"Similarity: "
            f"{similarity:.4f}"
        )


# ============================================================================
# Main
# ============================================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--fixtures_dir",
        required=True,
        type=str,
    )

    parser.add_argument(
        "--dino_weights",
        required=True,
        type=str,
    )

    parser.add_argument(
        "--rectifier_weights",
        required=True,
        type=str,
    )

    args = parser.parse_args()

    fixtures_dir = Path(
        args.fixtures_dir
    )

    dino_weights = Path(
        args.dino_weights
    )

    rectifier_weights = Path(
        args.rectifier_weights
    )

    if not fixtures_dir.exists():

        raise FileNotFoundError(
            f"Fixtures directory not found: "
            f"{fixtures_dir}"
        )

    if not dino_weights.exists():

        raise FileNotFoundError(
            f"DINO weights not found: "
            f"{dino_weights}"
        )

    if not rectifier_weights.exists():

        raise FileNotFoundError(
            f"Rectifier weights not found: "
            f"{rectifier_weights}"
        )

    # ----------------------------------------------------------------------
    # Device
    # ----------------------------------------------------------------------

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    # ----------------------------------------------------------------------
    # Load fixture samples
    # ----------------------------------------------------------------------

    print(
        "Loading fixture samples..."
    )

    samples = load_fixture_samples(
        fixtures_dir
    )

    print(
        f"Loaded {len(samples)} samples."
    )

    if not samples:

        raise RuntimeError(
            "No usable fixture samples found."
        )

    # ----------------------------------------------------------------------
    # Production cropper
    # ----------------------------------------------------------------------

    cropper = BoundingBoxCropper()

    # ----------------------------------------------------------------------
    # DINO + CoralSRT
    # ----------------------------------------------------------------------

    model = DinoCoralSRTEmbeddingModel(
        dino_weights=dino_weights,
        rectifier_weights=rectifier_weights,
        device=device,
    )

    # ----------------------------------------------------------------------
    # Generate embeddings
    # ----------------------------------------------------------------------

    embeddings = generate_all_embeddings(
        samples=samples,
        model=model,
        cropper=cropper,
    )

    if not embeddings:

        raise RuntimeError(
            "No embeddings were generated."
        )

    # ----------------------------------------------------------------------
    # Evaluate
    # ----------------------------------------------------------------------

    evaluate_embeddings(
        embeddings
    )


if __name__ == "__main__":

    main()