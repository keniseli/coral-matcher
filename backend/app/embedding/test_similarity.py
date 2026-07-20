from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.domain.models import (
    BoundingBox,
    Point,
    Segment,
)
from app.embedding.embedding import EmbeddingService
from app.vision.vision import VisionService
from app.cropping.cropper import BoundingBoxCropper


FIXTURES_DIR = Path("dev_fixtures")

POSITIVE_THRESHOLD = 0.90
NEGATIVE_THRESHOLD = 0.85

ROTATION_ANGLES = [0, 90, 180, 270]


@dataclass
class SegmentEmbedding:
    coral_id: str
    image_filename: str
    segment_id: int
    segment_area: int
    embeddings: dict[int, np.ndarray]


def segment_from_payload(
    segment_payload: dict,
) -> Segment:
    polygon = [
        Point(
            x=int(point[0]),
            y=int(point[1]),
        )
        for point in segment_payload["polygon"]
    ]

    bbox_payload = segment_payload["bbox"]

    bbox = BoundingBox(
        x=int(bbox_payload["x"]),
        y=int(bbox_payload["y"]),
        width=int(bbox_payload["width"]),
        height=int(bbox_payload["height"]),
    )

    return Segment(
        id=int(segment_payload["id"]),
        polygon=polygon,
        bbox=bbox,
        predictedIoU=float(
            segment_payload.get(
                "predictedIoU",
                0.0,
            )
        ),
        stabilityScore=float(
            segment_payload.get(
                "stabilityScore",
                0.0,
            )
        ),
    )


def polygon_area(
    segment: Segment,
) -> float:
    polygon = np.array(
        [
            [point.x, point.y]
            for point in segment.polygon
        ],
        dtype=np.float32,
    )

    return float(
        cv2.contourArea(polygon)
    )


def generate_embeddings_for_crop(
    crop: np.ndarray,
    embedding_service: EmbeddingService,
    vision_service: VisionService,
) -> dict[int, np.ndarray]:

    embeddings = {}

    for angle in ROTATION_ANGLES:

        if angle == 0:
            rotated_crop = crop

        else:
            rotated_crop = vision_service.rotate_image(
                crop,
                angle,
            )

        embedding = np.asarray(
            embedding_service.generate_vector_embedding(
                rotated_crop
            ),
            dtype=np.float32,
        )

        embeddings[angle] = embedding

    return embeddings


def load_segment_embeddings() -> list[SegmentEmbedding]:

    embedding_service = EmbeddingService()
    vision_service = VisionService()
    cropper = BoundingBoxCropper()

    records: list[SegmentEmbedding] = []

    json_files = sorted(
        FIXTURES_DIR.rglob("*.json")
    )

    for json_path in json_files:

        coral_id = json_path.parent.name

        with json_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            payload = json.load(handle)

        segment_payloads = payload.get(
            "segments",
            [],
        )

        if not segment_payloads:
            print(
                f"Skipping {json_path}: "
                "no segments found"
            )
            continue

        image_path = json_path.with_suffix(
            ".jpg"
        )

        if not image_path.exists():
            print(
                f"Skipping {json_path}: "
                f"image not found: {image_path}"
            )
            continue

        image = cv2.imread(
            str(image_path)
        )

        if image is None:
            print(
                f"Skipping {image_path}: "
                "could not load image"
            )
            continue

        segments = [
            segment_from_payload(
                segment_payload
            )
            for segment_payload in segment_payloads
        ]

        largest_segment = max(
            segments,
            key=polygon_area,
        )

        largest_area = polygon_area(
            largest_segment
        )

        masked_result = vision_service.mask(
            image=image,
            segments=[largest_segment],
        )

        crop_result = cropper.crop(
            image=masked_result.masked_image,
            segments=[largest_segment],
        )

        embeddings = generate_embeddings_for_crop(
            crop=crop_result.crop,
            embedding_service=embedding_service,
            vision_service=vision_service,
        )

        records.append(
            SegmentEmbedding(
                coral_id=coral_id,
                image_filename=image_path.name,
                segment_id=largest_segment.id,
                segment_area=int(largest_area),
                embeddings=embeddings,
            )
        )

        print(
            f"Loaded {coral_id} / "
            f"{image_path.name} / "
            f"segment {largest_segment.id} / "
            f"area {largest_area:.0f}"
        )

    return records


def cosine_similarity(
    a: np.ndarray,
    b: np.ndarray,
) -> float:

    return float(
        np.dot(a, b)
    )


def rotation_invariant_similarity(
    reference: SegmentEmbedding,
    candidate: SegmentEmbedding,
) -> tuple[float, int, int]:

    best_similarity = -1.0
    best_reference_angle = 0
    best_candidate_angle = 0

    for reference_angle, reference_embedding in (
        reference.embeddings.items()
    ):

        for candidate_angle, candidate_embedding in (
            candidate.embeddings.items()
        ):

            similarity = cosine_similarity(
                reference_embedding,
                candidate_embedding,
            )

            if similarity > best_similarity:

                best_similarity = similarity
                best_reference_angle = reference_angle
                best_candidate_angle = candidate_angle

    return (
        best_similarity,
        best_reference_angle,
        best_candidate_angle,
    )


def main():

    records = load_segment_embeddings()

    print()
    print("=" * 80)
    print("CORAL EMBEDDING SIMILARITY EVALUATION")
    print("=" * 80)
    print()

    print(
        f"Loaded {len(records)} representative segments"
    )

    if len(records) < 2:

        print(
            "Not enough embeddings for comparison."
        )

        return

    positive_scores: list[float] = []
    negative_scores: list[float] = []

    positive_pairs = []
    negative_pairs = []

    for i in range(len(records)):

        reference = records[i]

        for j in range(i + 1, len(records)):

            candidate = records[j]

            similarity, reference_angle, candidate_angle = (
                rotation_invariant_similarity(
                    reference,
                    candidate,
                )
            )

            pair = (
                reference,
                candidate,
                similarity,
                reference_angle,
                candidate_angle,
            )

            if (
                reference.coral_id
                == candidate.coral_id
            ):

                positive_scores.append(
                    similarity
                )

                positive_pairs.append(
                    pair
                )

            else:

                negative_scores.append(
                    similarity
                )

                negative_pairs.append(
                    pair
                )

    print()
    print("-" * 80)
    print("ROTATION-INVARIANT POSITIVE MATCHES")
    print("-" * 80)

    if positive_scores:

        positive = np.asarray(
            positive_scores,
            dtype=np.float32,
        )

        print(
            f"Count:   {len(positive)}"
        )

        print(
            f"Min:     {positive.min():.4f}"
        )

        print(
            f"Mean:    {positive.mean():.4f}"
        )

        print(
            f"Median:  {np.median(positive):.4f}"
        )

        print(
            f"Max:     {positive.max():.4f}"
        )

    else:

        print(
            "No positive comparisons found."
        )

    print()
    print("-" * 80)
    print("ROTATION-INVARIANT NEGATIVE MATCHES")
    print("-" * 80)

    if negative_scores:

        negative = np.asarray(
            negative_scores,
            dtype=np.float32,
        )

        print(
            f"Count:   {len(negative)}"
        )

        print(
            f"Min:     {negative.min():.4f}"
        )

        print(
            f"Mean:    {negative.mean():.4f}"
        )

        print(
            f"Median:  {np.median(negative):.4f}"
        )

        print(
            f"Max:     {negative.max():.4f}"
        )

    else:

        print(
            "No negative comparisons found."
        )

    print()
    print("=" * 80)
    print("TARGET EVALUATION")
    print("=" * 80)

    if positive_scores:

        lowest_positive = min(
            positive_scores
        )

        print()
        print(
            f"Lowest positive similarity: "
            f"{lowest_positive:.4f}"
        )

        if (
            lowest_positive
            > POSITIVE_THRESHOLD
        ):

            print(
                f"PASS: All positive matches > "
                f"{POSITIVE_THRESHOLD:.2f}"
            )

        else:

            print(
                f"FAIL: At least one positive match <= "
                f"{POSITIVE_THRESHOLD:.2f}"
            )

    if negative_scores:

        highest_negative = max(
            negative_scores
        )

        print()
        print(
            f"Highest negative similarity: "
            f"{highest_negative:.4f}"
        )

        if (
            highest_negative
            < NEGATIVE_THRESHOLD
        ):

            print(
                f"PASS: All negative matches < "
                f"{NEGATIVE_THRESHOLD:.2f}"
            )

        else:

            print(
                f"FAIL: At least one negative match >= "
                f"{NEGATIVE_THRESHOLD:.2f}"
            )

    print()
    print("=" * 80)
    print("MOST DIFFICULT COMPARISONS")
    print("=" * 80)

    if positive_pairs:

        hardest_positive = min(
            positive_pairs,
            key=lambda pair: pair[2],
        )

        (
            reference,
            candidate,
            similarity,
            reference_angle,
            candidate_angle,
        ) = hardest_positive

        print()
        print(
            "Lowest positive:"
        )

        print(
            f"  {reference.coral_id} / "
            f"{reference.image_filename} / "
            f"segment {reference.segment_id}"
        )

        print(
            f"  {candidate.coral_id} / "
            f"{candidate.image_filename} / "
            f"segment {candidate.segment_id}"
        )

        print(
            f"  similarity: {similarity:.4f}"
        )

        print(
            f"  best rotations: "
            f"{reference_angle}° vs "
            f"{candidate_angle}°"
        )

    if negative_pairs:

        hardest_negative = max(
            negative_pairs,
            key=lambda pair: pair[2],
        )

        (
            reference,
            candidate,
            similarity,
            reference_angle,
            candidate_angle,
        ) = hardest_negative

        print()
        print(
            "Highest negative:"
        )

        print(
            f"  {reference.coral_id} / "
            f"{reference.image_filename} / "
            f"segment {reference.segment_id}"
        )

        print(
            f"  {candidate.coral_id} / "
            f"{candidate.image_filename} / "
            f"segment {candidate.segment_id}"
        )

        print(
            f"  similarity: {similarity:.4f}"
        )

        print(
            f"  best rotations: "
            f"{reference_angle}° vs "
            f"{candidate_angle}°"
        )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()