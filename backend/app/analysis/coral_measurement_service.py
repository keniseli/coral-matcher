from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
import skimage.morphology as morph
import json

from .measurement.zero_shot_ruler_segmentation_service import (
    ZeroShotRulerSegmentationService,
)


@dataclass(frozen=True)
class RulerScaleEstimate:
    """Estimated physical scale of a ruler."""

    pixels_per_cm: float
    pixels_per_mm: float
    confidence: float
    major_tick_positions: np.ndarray
    all_tick_positions: np.ndarray


@dataclass(frozen=True)
class RulerGeometry:
    """Ruler transformed so that its long axis is horizontal."""

    center: tuple[float, float]
    width: int
    height: int
    angle_degrees: float
    rotation_matrix: np.ndarray


@dataclass(frozen=True)
class TickCandidate:
    """A detected ruler tick."""

    position: float
    strength: float
    depth: float


class CoralMeasurementService:
    """
    Estimate coral dimensions from an image containing a metric ruler.

    The ruler is first segmented, rotated so its long axis is horizontal,
    and then analysed along that axis.

    Important assumption:

        Metric ticks are perpendicular to the ruler's long axis.

    The estimator deliberately does NOT assume that every millimetre tick is
    visible. Centimetre ticks are treated as the primary scale evidence because
    they are consistently present on the ruler.
    """

    # -------------------------------------------------------------------------
    # RULER DETECTION CONSTANTS
    # -------------------------------------------------------------------------

    MIN_RULER_AREA = 1000

    # We deliberately allow relatively weak elongation because the visible
    # ruler can be fragmented by coral/reef occlusion.
    MIN_ELONGATION_RATIO = 1.15

    # Tick detection.
    MIN_TICK_DISTANCE_PX = 2.0

    # A centimetre mark should generally be deeper than a 1 mm / 5 mm mark.
    MAJOR_DEPTH_RATIO = 0.45

    # Candidate centimetre spacing range.
    #
    # This is intentionally broad. We do not know the image scale beforehand.
    MIN_CM_SPACING_PX = 15.0
    MAX_CM_SPACING_PX = 300.0

    # Maximum tolerated relative error when fitting a centimetre grid.
    CM_GRID_TOLERANCE_RATIO = 0.18

    # A valid ruler should have at least this many independent centimetre
    # intervals unless only a very short visible section remains.
    MIN_MAJOR_TICKS = 2

    def __init__(
        self,
        camera_matrix: Optional[np.ndarray] = None,
        dist_coeffs: Optional[np.ndarray] = None,
    ) -> None:
        self.K = camera_matrix
        self.D = dist_coeffs

        self.ruler_segmenter = ZeroShotRulerSegmentationService()

    # =========================================================================
    # RULER GEOMETRY
    # =========================================================================

    def _find_ruler_contour(
        self,
        ruler_mask: np.ndarray,
    ) -> np.ndarray:
        if ruler_mask.ndim != 2:
            raise ValueError(
                "Ruler mask must be a single-channel image."
            )

        binary = (ruler_mask > 0).astype(np.uint8)

        contours, _ = cv2.findContours(
            binary,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        if not contours:
            raise ValueError(
                "Empty ruler mask passed to scale estimator."
            )

        contour = max(
            contours,
            key=cv2.contourArea,
        )

        area = cv2.contourArea(contour)

        if area < self.MIN_RULER_AREA:
            raise ValueError(
                f"Ruler mask is too small: area={area:.1f}px²."
            )

        return contour

    def _estimate_ruler_geometry(
        self,
        ruler_mask: np.ndarray,
    ) -> RulerGeometry:
        """
        Estimate the ruler orientation using PCA.

        PCA is preferable to minAreaRect here because parts of the ruler can
        disappear beneath coral or other reef structures.
        """
        contour = self._find_ruler_contour(ruler_mask)

        points = contour.reshape(-1, 2).astype(np.float64)

        center = points.mean(axis=0)

        centered = points - center
        covariance = np.cov(centered.T)

        eigenvalues, eigenvectors = np.linalg.eigh(
            covariance,
        )

        principal_axis = eigenvectors[
            :, np.argmax(eigenvalues)
        ]

        angle = float(
            np.degrees(
                np.arctan2(
                    principal_axis[1],
                    principal_axis[0],
                )
            )
        )

        # PCA describes an axis, not a direction.
        if angle >= 90.0:
            angle -= 180.0
        elif angle < -90.0:
            angle += 180.0

        h, w = ruler_mask.shape[:2]

        rotation_matrix = cv2.getRotationMatrix2D(
            (
                float(center[0]),
                float(center[1]),
            ),
            -angle,
            1.0,
        )

        rotated_mask = cv2.warpAffine(
            ruler_mask,
            rotation_matrix,
            (w, h),
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
        )

        ys, xs = np.where(rotated_mask > 0)

        if len(xs) == 0:
            raise ValueError(
                "Ruler disappeared during rotation."
            )

        ruler_width = int(
            xs.max() - xs.min() + 1
        )

        ruler_height = int(
            ys.max() - ys.min() + 1
        )

        if ruler_height <= 0:
            raise ValueError(
                "Invalid ruler geometry."
            )

        elongation = (
            ruler_width / ruler_height
        )

        if elongation < self.MIN_ELONGATION_RATIO:
            raise ValueError(
                "Detected ruler is not sufficiently elongated: "
                f"{ruler_width}x{ruler_height} "
                f"(ratio={elongation:.2f})."
            )

        return RulerGeometry(
            center=(
                float(center[0]),
                float(center[1]),
            ),
            width=ruler_width,
            height=ruler_height,
            angle_degrees=angle,
            rotation_matrix=rotation_matrix,
        )

    def _rotate_ruler(
        self,
        image: np.ndarray,
        ruler_mask: np.ndarray,
        geometry: RulerGeometry,
    ) -> tuple[
        np.ndarray,
        np.ndarray,
        tuple[int, int, int, int],
    ]:
        """
        Rotate and tightly crop the ruler.

        Returns:
            rotated image
            rotated mask
            crop rectangle (x, y, width, height)
        """
        h, w = image.shape[:2]

        rotated_image = cv2.warpAffine(
            image,
            geometry.rotation_matrix,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_CONSTANT,
        )

        rotated_mask = cv2.warpAffine(
            ruler_mask,
            geometry.rotation_matrix,
            (w, h),
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
        )

        ys, xs = np.where(rotated_mask > 0)

        if len(xs) == 0:
            raise ValueError(
                "Ruler mask is empty after rotation."
            )

        padding_x = max(
            5,
            int((xs.max() - xs.min()) * 0.015),
        )

        padding_y = max(
            5,
            int((ys.max() - ys.min()) * 0.12),
        )

        x1 = max(
            0,
            int(xs.min()) - padding_x,
        )

        x2 = min(
            w,
            int(xs.max()) + padding_x + 1,
        )

        y1 = max(
            0,
            int(ys.min()) - padding_y,
        )

        y2 = min(
            h,
            int(ys.max()) + padding_y + 1,
        )

        return (
            rotated_image[y1:y2, x1:x2],
            rotated_mask[y1:y2, x1:x2],
            (
                x1,
                y1,
                x2 - x1,
                y2 - y1,
            ),
        )

    # =========================================================================
    # TICK EXTRACTION
    # =========================================================================

    def _build_tick_signals(
        self,
        gray: np.ndarray,
        ruler_mask: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Build signals describing dark ruler markings.

        Returns:

            combined_signal:
                General tick response.

            depth_signal:
                Response measuring how far a dark marking extends into the
                ruler. This is especially useful for distinguishing 1 cm
                marks from 1 mm / 5 mm marks.

            visibility_signal:
                How much of each ruler edge is actually visible.

        We inspect both long edges because either edge can be occluded.
        """
        ys, xs = np.where(ruler_mask > 0)

        if len(xs) == 0:
            raise ValueError(
                "Empty ruler mask."
            )

        top = int(ys.min())
        bottom = int(ys.max())

        ruler_height = (
            bottom - top + 1
        )

        if ruler_height < 10:
            raise ValueError(
                "Ruler is too narrow for tick detection."
            )

        mask = (
            ruler_mask > 0
        )

        gray_float = gray.astype(
            np.float32,
        )

        # Local illumination normalization.
        background = cv2.GaussianBlur(
            gray_float,
            (0, 0),
            sigmaX=4.0,
        )

        darkness = np.maximum(
            background - gray_float,
            0.0,
        )

        # We examine considerably more depth than before. This is important:
        # the distinction between 1 mm and 1 cm marks is primarily their
        # penetration into the ruler.
        max_depth = max(
            6,
            min(
                int(ruler_height * 0.70),
                120,
            ),
        )

        top_region = darkness[
            top : top + max_depth
        ]

        bottom_region = darkness[
            bottom - max_depth + 1 : bottom + 1
        ]

        top_mask = mask[
            top : top + max_depth
        ]

        bottom_mask = mask[
            bottom - max_depth + 1 : bottom + 1
        ]

        top_region = top_region * top_mask
        bottom_region = bottom_region * bottom_mask

        # The outermost pixels are most likely to contain the ruler markings.
        top_weights = np.exp(
            -np.arange(
                max_depth,
                dtype=np.float32,
            )
            / max(
                3.0,
                ruler_height * 0.22,
            )
        )

        bottom_weights = top_weights[::-1]

        top_signal = np.sum(
            top_region * top_weights[:, None],
            axis=0,
        )

        bottom_signal = np.sum(
            bottom_region * bottom_weights[:, None],
            axis=0,
        )

        # Deep response: use a broader interior range. Long centimetre ticks
        # remain visible here whereas short ticks largely disappear.
        deep_start = max(
            2,
            int(ruler_height * 0.12),
        )

        deep_end = max(
            deep_start + 2,
            int(ruler_height * 0.55),
        )

        deep_end = min(
            deep_end,
            max_depth,
        )

        top_deep = top_region[
            deep_start:deep_end
        ]

        bottom_deep = bottom_region[
            deep_start:deep_end
        ]

        top_deep_signal = np.sum(
            top_deep,
            axis=0,
        )

        bottom_deep_signal = np.sum(
            bottom_deep,
            axis=0,
        )

        combined = np.maximum(
            self._normalize_signal(top_signal),
            self._normalize_signal(bottom_signal),
        )

        depth_signal = np.maximum(
            self._normalize_signal(
                top_deep_signal
            ),
            self._normalize_signal(
                bottom_deep_signal
            ),
        )

        # Visibility tells us whether the edge is actually represented by the
        # segmentation mask at a given x-coordinate.
        top_visibility = np.sum(
            top_mask,
            axis=0,
        ).astype(np.float32)

        bottom_visibility = np.sum(
            bottom_mask,
            axis=0,
        ).astype(np.float32)

        visibility_signal = np.maximum(
            top_visibility,
            bottom_visibility,
        )

        visibility_signal = (
            visibility_signal
            / max(
                float(max_depth),
                1.0,
            )
        )

        # Smooth only along the ruler axis.
        combined = cv2.GaussianBlur(
            combined.reshape(1, -1),
            (0, 0),
            sigmaX=1.0,
        ).ravel()

        depth_signal = cv2.GaussianBlur(
            depth_signal.reshape(1, -1),
            (0, 0),
            sigmaX=1.2,
        ).ravel()

        visibility_signal = cv2.GaussianBlur(
            visibility_signal.reshape(1, -1),
            (0, 0),
            sigmaX=1.0,
        ).ravel()

        return (
            combined.astype(np.float32),
            depth_signal.astype(np.float32),
            visibility_signal.astype(np.float32),
        )

    @staticmethod
    def _normalize_signal(
        signal: np.ndarray,
    ) -> np.ndarray:
        if signal.size == 0:
            return np.zeros(
                0,
                dtype=np.float32,
            )

        low, high = np.percentile(
            signal,
            [10, 99],
        )

        if high <= low:
            return np.zeros_like(
                signal,
                dtype=np.float32,
            )

        normalized = (
            signal - low
        ) / (
            high - low
        )

        return np.clip(
            normalized,
            0.0,
            1.0,
        ).astype(np.float32)

    def _detect_tick_candidates(
        self,
        signal: np.ndarray,
        depth_signal: np.ndarray,
        visibility_signal: np.ndarray,
    ) -> list[TickCandidate]:
        """
        Detect individual tick candidates.

        We deliberately keep this stage permissive. Determining whether a
        candidate is a centimetre tick belongs to the scale-fitting stage.
        """
        if len(signal) < 30:
            raise ValueError(
                "Ruler signal is too short."
            )

        # Adaptive threshold based on the upper tail of the signal.
        threshold = max(
            0.18,
            float(
                np.percentile(
                    signal,
                    82,
                )
            ),
        )

        # Find local maxima.
        peaks: list[int] = []

        for i in range(1, len(signal) - 1):
            if signal[i] < threshold:
                continue

            if (
                signal[i] >= signal[i - 1]
                and signal[i] >= signal[i + 1]
            ):
                peaks.append(i)

        if not peaks:
            raise ValueError(
                "Unable to detect ruler tick candidates."
            )

        candidates: list[TickCandidate] = []

        for peak in peaks:
            # Refine the position using a small weighted centroid around the
            # local maximum. This gives sub-pixel-ish stability without
            # pretending the image contains more information than it does.
            left = max(
                0,
                peak - 2,
            )

            right = min(
                len(signal),
                peak + 3,
            )

            local_signal = signal[
                left:right
            ]

            weights = np.maximum(
                local_signal - threshold,
                0.0,
            )

            if np.sum(weights) > 0:
                positions = np.arange(
                    left,
                    right,
                    dtype=np.float32,
                )

                position = float(
                    np.sum(
                        positions * weights
                    )
                    / np.sum(weights)
                )
            else:
                position = float(peak)

            candidates.append(
                TickCandidate(
                    position=position,
                    strength=float(
                        signal[peak]
                    ),
                    depth=float(
                        depth_signal[peak]
                    ),
                )
            )

        # Merge detections that are too close together.
        candidates.sort(
            key=lambda candidate: candidate.position,
        )

        merged: list[TickCandidate] = []

        for candidate in candidates:
            if not merged:
                merged.append(candidate)
                continue

            previous = merged[-1]

            if (
                candidate.position
                - previous.position
                < self.MIN_TICK_DISTANCE_PX
            ):
                # Keep the stronger candidate.
                if (
                    candidate.strength
                    > previous.strength
                ):
                    merged[-1] = candidate
            else:
                merged.append(candidate)

        if len(merged) < 2:
            raise ValueError(
                "Too few ruler tick candidates detected."
            )

        # Candidates occurring in completely invisible areas of the ruler
        # should not influence the scale.
        merged = [
            candidate
            for candidate in merged
            if visibility_signal[
                min(
                    len(visibility_signal) - 1,
                    max(
                        0,
                        int(
                            round(
                                candidate.position
                            )
                        ),
                    ),
                )
            ]
            > 0.05
        ]

        return merged

    # =========================================================================
    # CENTIMETRE SCALE ESTIMATION
    # =========================================================================

    def _estimate_cm_spacing(
        self,
        candidates: list[TickCandidate],
    ) -> tuple[
        float,
        float,
        np.ndarray,
    ]:
        """
        Estimate pixels per centimetre.

        This is the important replacement for the old implementation.

        We do NOT derive centimetre spacing as:

            fundamental_tick_pitch * 8..12

        That approach is vulnerable to false tick detections and missing
        ticks.

        Instead:

        1. Identify candidates likely to be centimetre marks using their
           depth into the ruler.
        2. Search for a repeated spacing among those candidates.
        3. Allow arbitrary missing marks.
        4. Score the candidate by number of supporting marks, residual error,
           and coverage.
        """
        if len(candidates) < 2:
            raise ValueError(
                "Too few ruler ticks for scale estimation."
            )

        positions = np.asarray(
            [
                candidate.position
                for candidate in candidates
            ],
            dtype=np.float64,
        )

        depths = np.asarray(
            [
                candidate.depth
                for candidate in candidates
            ],
            dtype=np.float64,
        )

        strengths = np.asarray(
            [
                candidate.strength
                for candidate in candidates
            ],
            dtype=np.float64,
        )

        # ---------------------------------------------------------------------
        # 1. Identify likely centimetre candidates.
        # ---------------------------------------------------------------------

        depth_threshold = max(
            self.MAJOR_DEPTH_RATIO,
            float(
                np.percentile(
                    depths,
                    65,
                )
            ),
        )

        major_mask = (
            depths >= depth_threshold
        )

        # If depth discrimination is weak, fall back to strength. This is
        # preferable to silently failing on a very low-contrast ruler.
        if np.count_nonzero(major_mask) < 2:
            strength_threshold = float(
                np.percentile(
                    strengths,
                    70,
                )
            )

            major_mask = (
                strengths
                >= strength_threshold
            )

        major_positions = positions[
            major_mask
        ]

        if len(major_positions) < 2:
            raise ValueError(
                "Unable to identify repeated centimetre intervals."
            )

        major_positions = np.sort(
            major_positions,
        )

        print(
            "[RULER DEBUG] "
            f"candidate ticks={len(positions)}, "
            f"major candidates={len(major_positions)}"
        )

        # ---------------------------------------------------------------------
        # 2. Generate spacing candidates.
        #
        # We don't know whether adjacent detected major marks are consecutive
        # centimetres. Therefore every pair can represent 1, 2, 3, ... cm.
        # ---------------------------------------------------------------------

        spacing_candidates: list[float] = []

        for i in range(
            len(major_positions)
        ):
            for j in range(
                i + 1,
                len(major_positions),
            ):
                distance = (
                    major_positions[j]
                    - major_positions[i]
                )

                if (
                    distance
                    < self.MIN_CM_SPACING_PX
                    or distance
                    > self.MAX_CM_SPACING_PX * 8
                ):
                    continue

                # The pair may represent N centimetres. Try a reasonable
                # number of missing intervals.
                max_intervals = min(
                    8,
                    max(
                        1,
                        int(
                            round(
                                distance
                                / self.MIN_CM_SPACING_PX
                            )
                        ),
                    ),
                )

                for intervals in range(
                    1,
                    max_intervals + 1,
                ):
                    spacing = (
                        distance
                        / intervals
                    )

                    if (
                        self.MIN_CM_SPACING_PX
                        <= spacing
                        <= self.MAX_CM_SPACING_PX
                    ):
                        spacing_candidates.append(
                            float(spacing)
                        )

        if not spacing_candidates:
            raise ValueError(
                "Could not construct centimetre spacing candidates."
            )

        # Cluster nearly identical spacing candidates. A correct spacing will
        # receive support from many different pairs.
        spacing_candidates.sort()

        spacing_clusters: list[
            list[float]
        ] = []

        for spacing in spacing_candidates:
            if not spacing_clusters:
                spacing_clusters.append(
                    [spacing]
                )
                continue

            cluster = spacing_clusters[-1]

            cluster_center = float(
                np.median(cluster)
            )

            tolerance = max(
                2.0,
                cluster_center * 0.06,
            )

            if (
                abs(
                    spacing
                    - cluster_center
                )
                <= tolerance
            ):
                cluster.append(spacing)
            else:
                spacing_clusters.append(
                    [spacing]
                )

        candidate_spacings = [
            float(np.median(cluster))
            for cluster in spacing_clusters
            if len(cluster) >= 2
        ]

        if not candidate_spacings:
            # Very short visible rulers can legitimately provide only one
            # useful pair.
            candidate_spacings = [
                float(np.median(spacing_candidates))
            ]

        # ---------------------------------------------------------------------
        # 3. Score each candidate against ALL tick candidates.
        # ---------------------------------------------------------------------

        best_spacing: Optional[
            float
        ] = None

        best_score = -np.inf

        best_major_positions = (
            np.empty(
                0,
                dtype=np.float64,
            )
        )

        best_support = 0

        for spacing in candidate_spacings:
            grid_positions = (
                self._fit_major_grid(
                    major_positions,
                    spacing,
                )
            )

            if len(grid_positions) < 2:
                continue

            residuals = self._grid_residuals(
                major_positions,
                grid_positions,
            )

            tolerance = max(
                3.0,
                spacing
                * self.CM_GRID_TOLERANCE_RATIO,
            )

            support = int(
                np.count_nonzero(
                    residuals <= tolerance
                )
            )

            if support < 2:
                continue

            median_residual = float(
                np.median(residuals)
            )

            residual_score = float(
                np.exp(
                    -median_residual
                    / max(
                        spacing * 0.10,
                        1.0,
                    )
                )
            )

            support_score = min(
                support / 5.0,
                1.0,
            )

            coverage = (
                (
                    grid_positions[-1]
                    - grid_positions[0]
                )
                / max(
                    spacing * 2.0,
                    1.0,
                )
            )

            coverage_score = float(
                np.clip(
                    coverage,
                    0.0,
                    1.0,
                )
            )

            score = (
                0.55 * residual_score
                + 0.35 * support_score
                + 0.10 * coverage_score
            )

            if score > best_score:
                best_score = score
                best_spacing = spacing
                best_major_positions = (
                    grid_positions
                )
                best_support = support

        if (
            best_spacing is None
            or best_support < 2
        ):
            raise ValueError(
                "Unable to identify repeated centimetre intervals."
            )

        confidence = float(
            np.clip(
                best_score,
                0.0,
                1.0,
            )
        )

        print(
            "[RULER DEBUG] "
            f"estimated cm spacing={best_spacing:.3f}px, "
            f"major support={best_support}, "
            f"confidence={confidence:.3f}"
        )

        return (
            float(best_spacing),
            confidence,
            best_major_positions,
        )

    @staticmethod
    def _fit_major_grid(
        major_positions: np.ndarray,
        spacing: float,
    ) -> np.ndarray:
        """
        Fit a periodic centimetre grid to observed major ticks.

        Missing centimetre ticks are explicitly allowed.
        """
        if len(major_positions) < 2:
            return np.empty(
                0,
                dtype=np.float64,
            )

        best_grid = np.empty(
            0,
            dtype=np.float64,
        )

        best_count = 0
        best_error = np.inf

        tolerance = max(
            3.0,
            spacing * 0.18,
        )

        for origin in major_positions:
            min_index = int(
                np.floor(
                    (
                        major_positions.min()
                        - origin
                    )
                    / spacing
                )
            )

            max_index = int(
                np.ceil(
                    (
                        major_positions.max()
                        - origin
                    )
                    / spacing
                )
            )

            indices = np.arange(
                min_index,
                max_index + 1,
            )

            grid = (
                origin
                + indices * spacing
            )

            matches: list[
                float
            ] = []

            errors: list[
                float
            ] = []

            for grid_position in grid:
                distance = float(
                    np.min(
                        np.abs(
                            major_positions
                            - grid_position
                        )
                    )
                )

                if distance <= tolerance:
                    matches.append(
                        grid_position
                    )
                    errors.append(
                        distance
                    )

            if not matches:
                continue

            error = float(
                np.mean(errors)
            )

            if (
                len(matches) > best_count
                or (
                    len(matches)
                    == best_count
                    and error < best_error
                )
            ):
                best_count = len(matches)
                best_error = error
                best_grid = np.asarray(
                    matches,
                    dtype=np.float64,
                )

        return best_grid

    @staticmethod
    def _grid_residuals(
        observed_positions: np.ndarray,
        grid_positions: np.ndarray,
    ) -> np.ndarray:
        distances: list[float] = []

        for position in grid_positions:
            distances.append(
                float(
                    np.min(
                        np.abs(
                            observed_positions
                            - position
                        )
                    )
                )
            )

        return np.asarray(
            distances,
            dtype=np.float64,
        )

    # =========================================================================
    # SCALE ESTIMATION
    # =========================================================================

    def estimate_ruler_scale(
        self,
        img: np.ndarray,
        ruler_mask: np.ndarray,
        name_for_debug: str = "",
    ) -> RulerScaleEstimate:
        """
        Estimate pixels/cm from the metric ruler.
        """
        if img is None or img.size == 0:
            raise ValueError(
                "Empty image passed to scale estimator."
            )

        if (
            ruler_mask is None
            or ruler_mask.size == 0
        ):
            raise ValueError(
                "Empty ruler mask passed to scale estimator."
            )

        if img.shape[:2] != ruler_mask.shape[:2]:
            raise ValueError(
                "Image and ruler mask dimensions do not match."
            )

        if img.ndim == 3:
            gray = cv2.cvtColor(
                img,
                cv2.COLOR_BGR2GRAY,
            )
        else:
            gray = img.copy()

        geometry = (
            self._estimate_ruler_geometry(
                ruler_mask,
            )
        )

        (
            rotated_gray,
            rotated_mask,
            _,
        ) = self._rotate_ruler(
            gray,
            ruler_mask,
            geometry,
        )

        (
            signal,
            depth_signal,
            visibility_signal,
        ) = self._build_tick_signals(
            rotated_gray,
            rotated_mask,
        )

        candidates = (
            self._detect_tick_candidates(
                signal,
                depth_signal,
                visibility_signal,
            )
        )

        tick_positions = np.asarray(
            [
                candidate.position
                for candidate in candidates
            ],
            dtype=np.float64,
        )

        (
            pixels_per_cm,
            confidence,
            major_tick_positions,
        ) = self._estimate_cm_spacing(
            candidates,
        )

        pixels_per_mm = (
            pixels_per_cm / 10.0
        )

        if (
            not np.isfinite(
                pixels_per_cm
            )
            or pixels_per_cm <= 0
        ):
            raise ValueError(
                "Invalid ruler scale estimate."
            )

        if name_for_debug:
            self._save_ruler_debug_image(
                rotated_gray,
                rotated_mask,
                signal,
                depth_signal,
                candidates,
                tick_positions,
                major_tick_positions,
                pixels_per_cm,
                confidence,
                name_for_debug,
            )

        return RulerScaleEstimate(
            pixels_per_cm=pixels_per_cm,
            pixels_per_mm=pixels_per_mm,
            confidence=confidence,
            major_tick_positions=major_tick_positions,
            all_tick_positions=tick_positions,
        )

    # =========================================================================
    # DEBUGGING
    # =========================================================================

    def _save_ruler_debug_image(
        self,
        gray: np.ndarray,
        ruler_mask: np.ndarray,
        signal: np.ndarray,
        depth_signal: np.ndarray,
        candidates: list[TickCandidate],
        tick_positions: np.ndarray,
        major_tick_positions: np.ndarray,
        pixels_per_cm: float,
        confidence: float,
        name: str,
    ) -> None:
        """
        Save a visual diagnostic of the ruler analysis.

        Candidate ticks:
            cyan

        Candidate centimetre ticks:
            green

        Ruler boundary:
            red
        """
        debug = cv2.cvtColor(
            gray,
            cv2.COLOR_GRAY2BGR,
        )

        contours, _ = cv2.findContours(
            ruler_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        if contours:
            cv2.drawContours(
                debug,
                contours,
                -1,
                (0, 0, 255),
                2,
            )

        h = debug.shape[0]

        major_tolerance = max(
            3.0,
            pixels_per_cm * 0.18,
        )

        for candidate in candidates:
            x = int(
                round(
                    candidate.position
                )
            )

            is_major = np.any(
                np.abs(
                    major_tick_positions
                    - candidate.position
                )
                <= major_tolerance
            )

            if is_major:
                cv2.line(
                    debug,
                    (x, 0),
                    (x, h - 1),
                    (0, 255, 0),
                    3,
                )
            else:
                cv2.line(
                    debug,
                    (x, 0),
                    (x, h - 1),
                    (255, 255, 0),
                    1,
                )

        text = (
            f"{pixels_per_cm:.2f} px/cm | "
            f"confidence={confidence:.2f}"
        )

        cv2.putText(
            debug,
            text,
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        output_path = (
            f"ruler_scale_{name}.png"
        )

        cv2.imwrite(
            output_path,
            debug,
        )

        print(
            f"[RULER DEBUG] Saved: {output_path}"
        )
        print(
            "[RULER DEBUG] "
            f"ticks={len(tick_positions)}"
        )
        print(
            "[RULER DEBUG] "
            f"major ticks={len(major_tick_positions)}"
        )
        print(
            "[RULER DEBUG] "
            f"pixels/cm={pixels_per_cm:.3f}"
        )
        print(
            "[RULER DEBUG] "
            f"confidence={confidence:.3f}"
        )

    # =========================================================================
    # UNDISTORTION
    # =========================================================================

    def undistort_image(
        self,
        img: np.ndarray,
        reference_color_img: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Undistort using known camera calibration.

        If calibration is unavailable, return a copy unchanged.
        """
        if (
            self.K is None
            or self.D is None
        ):
            return img.copy()

        h, w = img.shape[:2]

        new_K, _ = (
            cv2.getOptimalNewCameraMatrix(
                self.K,
                self.D,
                (w, h),
                1,
                (w, h),
            )
        )

        return cv2.undistort(
            img,
            self.K,
            self.D,
            None,
            new_K,
        )

    # =========================================================================
    # NUMERICAL DIAGNOSTICS
    # =========================================================================

    def save_ruler_diagnostics(
        self,
        img: np.ndarray,
        ruler_mask: np.ndarray,
        output_path: str | Path,
    ) -> None:
        """
        Save numerical ruler diagnostics as JSON.

        This is intentionally diagnostic only and does not modify the
        measurement pipeline.
        """
        geometry = (
            self._estimate_ruler_geometry(
                ruler_mask,
            )
        )

        gray = (
            img
            if img.ndim == 2
            else cv2.cvtColor(
                img,
                cv2.COLOR_BGR2GRAY,
            )
        )

        (
            rotated_gray,
            rotated_mask,
            crop,
        ) = self._rotate_ruler(
            gray,
            ruler_mask,
            geometry,
        )

        (
            signal,
            depth_signal,
            visibility_signal,
        ) = self._build_tick_signals(
            rotated_gray,
            rotated_mask,
        )

        candidates = (
            self._detect_tick_candidates(
                signal,
                depth_signal,
                visibility_signal,
            )
        )

        tick_positions = np.asarray(
            [
                candidate.position
                for candidate in candidates
            ],
            dtype=np.float64,
        )

        adjacent_diffs = (
            np.diff(tick_positions)
        )

        pairwise_diffs: list[float] = []

        for i in range(
            len(tick_positions)
        ):
            for j in range(
                i + 1,
                min(
                    i + 11,
                    len(tick_positions),
                ),
            ):
                distance = (
                    tick_positions[j]
                    - tick_positions[i]
                )

                if distance > 0:
                    pairwise_diffs.append(
                        float(distance)
                    )

        pairwise_diffs_np = np.asarray(
            pairwise_diffs,
            dtype=np.float64,
        )

        histogram: list[
            dict[str, Any]
        ] = []

        if len(pairwise_diffs_np) > 0:
            min_diff = max(
                0.5,
                float(
                    pairwise_diffs_np.min()
                ),
            )

            max_diff = float(
                pairwise_diffs_np.max()
            )

            if max_diff > min_diff:
                counts, edges = (
                    np.histogram(
                        pairwise_diffs_np,
                        bins=100,
                        range=(
                            min_diff,
                            max_diff,
                        ),
                    )
                )

                for i, count in enumerate(
                    counts
                ):
                    if count == 0:
                        continue

                    histogram.append(
                        {
                            "min": float(
                                edges[i]
                            ),
                            "max": float(
                                edges[i + 1]
                            ),
                            "center": float(
                                (
                                    edges[i]
                                    + edges[i + 1]
                                )
                                / 2
                            ),
                            "count": int(
                                count
                            ),
                        }
                    )

        signal_percentiles = {
            str(p): float(
                np.percentile(
                    signal,
                    p,
                )
            )
            for p in [
                0,
                1,
                5,
                10,
                25,
                50,
                75,
                90,
                95,
                99,
                100,
            ]
        }

        depth_percentiles = {
            str(p): float(
                np.percentile(
                    depth_signal,
                    p,
                )
            )
            for p in [
                0,
                10,
                25,
                50,
                75,
                90,
                95,
                99,
                100,
            ]
        }

        try:
            (
                pixels_per_cm,
                confidence,
                major_tick_positions,
            ) = self._estimate_cm_spacing(
                candidates,
            )

            scale_diagnostics: dict[
                str,
                Any,
            ] = {
                "pixels_per_cm": float(
                    pixels_per_cm
                ),
                "pixels_per_mm": float(
                    pixels_per_cm / 10.0
                ),
                "confidence": float(
                    confidence
                ),
                "major_tick_positions": [
                    float(value)
                    for value
                    in major_tick_positions
                ],
            }
        except ValueError as exc:
            scale_diagnostics = {
                "error": str(exc),
            }

        diagnostics = {
            "image": {
                "width": int(
                    img.shape[1]
                ),
                "height": int(
                    img.shape[0]
                ),
            },

            "ruler_mask": {
                "pixels": int(
                    np.count_nonzero(
                        ruler_mask
                    )
                ),
                "percentage": float(
                    np.count_nonzero(
                        ruler_mask
                    )
                    / ruler_mask.size
                    * 100.0
                ),
            },

            "geometry": {
                "center": [
                    float(
                        geometry.center[0]
                    ),
                    float(
                        geometry.center[1]
                    ),
                ],
                "angle_degrees": float(
                    geometry.angle_degrees
                ),
                "width": int(
                    geometry.width
                ),
                "height": int(
                    geometry.height
                ),
                "elongation_ratio": float(
                    geometry.width
                    / max(
                        geometry.height,
                        1,
                    )
                ),
                "rotation_matrix": (
                    geometry.rotation_matrix.tolist()
                ),
                "crop": [
                    int(value)
                    for value in crop
                ],
            },

            "signal": {
                "length": int(
                    len(signal)
                ),
                "percentiles": (
                    signal_percentiles
                ),
                "values": [
                    float(value)
                    for value in signal
                ],
            },

            "depth_signal": {
                "percentiles": (
                    depth_percentiles
                ),
                "values": [
                    float(value)
                    for value in depth_signal
                ],
            },

            "visibility_signal": {
                "values": [
                    float(value)
                    for value
                    in visibility_signal
                ],
            },

            "ticks": {
                "count": int(
                    len(candidates)
                ),
                "positions": [
                    float(
                        candidate.position
                    )
                    for candidate in candidates
                ],
                "strengths": [
                    float(
                        candidate.strength
                    )
                    for candidate in candidates
                ],
                "depths": [
                    float(
                        candidate.depth
                    )
                    for candidate in candidates
                ],
                "adjacent_differences": [
                    float(value)
                    for value in adjacent_diffs
                ],
            },

            "pairwise_spacing": {
                "count": int(
                    len(pairwise_diffs_np)
                ),
                "values": [
                    float(value)
                    for value
                    in pairwise_diffs_np
                ],
                "histogram": histogram,
            },

            "scale": scale_diagnostics,
        }

        output_path = Path(
            output_path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            json.dumps(
                diagnostics,
                indent=2,
            ),
            encoding="utf-8",
        )

        print(
            "[RULER DEBUG] diagnostics "
            f"written to {output_path}"
        )

    # =========================================================================
    # FULL MEASUREMENT PIPELINE
    # =========================================================================

    def process_frame(
        self,
        img: np.ndarray,
        coral_mask: np.ndarray,
        name_for_debug: str = "",
    ) -> dict[str, Any]:
        if img is None or img.size == 0:
            raise ValueError(
                "Empty image."
            )

        if (
            coral_mask is None
            or coral_mask.size == 0
        ):
            raise ValueError(
                "Empty coral mask."
            )

        # ---------------------------------------------------------------------
        # 1. Detect ruler
        # ---------------------------------------------------------------------

        ruler_mask = (
            self.ruler_segmenter.predict_ruler_mask(
                img,
                "a white measuring ruler . white scale slate",
            )
        )

        if not np.any(ruler_mask):
            raise ValueError(
                "Ruler segmentation produced an empty mask."
            )

        # Save diagnostics, but do not let diagnostic failures obscure the
        # actual production measurement error.
        if name_for_debug:
            try:
                self.save_ruler_diagnostics(
                    img,
                    ruler_mask,
                    Path(
                        "test/debug"
                    )
                    / f"{name_for_debug}.json",
                )
            except Exception as exc:
                print(
                    "[RULER DEBUG] "
                    f"Unable to save diagnostics: {exc}"
                )

        # ---------------------------------------------------------------------
        # 2. Undistort everything using the same transformation
        # ---------------------------------------------------------------------

        img_rect = self.undistort_image(
            img,
        )

        coral_rect = self.undistort_image(
            coral_mask,
            reference_color_img=img,
        )

        ruler_rect = self.undistort_image(
            ruler_mask,
            reference_color_img=img,
        )

        # ---------------------------------------------------------------------
        # 3. Estimate ruler scale
        # ---------------------------------------------------------------------

        scale = self.estimate_ruler_scale(
            img_rect,
            ruler_rect,
            name_for_debug=name_for_debug,
        )

        px_per_cm = (
            scale.pixels_per_cm
        )

        # ---------------------------------------------------------------------
        # 4. Coral geometry
        # ---------------------------------------------------------------------

        binary_mask = (
            coral_rect > 0
        ).astype(np.uint8)

        contours, _ = cv2.findContours(
            binary_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        if not contours:
            raise ValueError(
                "Coral mask contains no contours."
            )

        coral_cnt = max(
            contours,
            key=cv2.contourArea,
        )

        if cv2.contourArea(
            coral_cnt
        ) <= 0:
            raise ValueError(
                "Coral contour has zero area."
            )

        hull = cv2.convexHull(
            coral_cnt,
        )

        pts = hull.reshape(
            -1,
            2,
        )

        if len(pts) < 2:
            raise ValueError(
                "Coral contour contains too few points."
            )

        # Maximum Feret diameter.
        diff = (
            pts[:, None, :]
            - pts[None, :, :]
        )

        distances_squared = np.sum(
            diff.astype(
                np.float64
            ) ** 2,
            axis=2,
        )

        i, j = np.unravel_index(
            np.argmax(
                distances_squared
            ),
            distances_squared.shape,
        )

        feret_px = float(
            np.sqrt(
                distances_squared[
                    i,
                    j,
                ]
            )
        )

        # Skeleton-based geodesic approximation.
        skeleton = morph.skeletonize(
            binary_mask.astype(bool)
        )

        geodesic_px = float(
            np.count_nonzero(
                skeleton
            )
        )

        feret_cm = (
            feret_px / px_per_cm
        )

        geodesic_cm = (
            geodesic_px / px_per_cm
        )

        # ---------------------------------------------------------------------
        # 5. Debug visualization
        # ---------------------------------------------------------------------

        debug_canvas = img_rect.copy()

        coral_indices = (
            coral_rect > 0
        )

        debug_canvas[
            coral_indices
        ] = cv2.addWeighted(
            debug_canvas[
                coral_indices
            ],
            0.6,
            np.full_like(
                debug_canvas[
                    coral_indices
                ],
                (0, 255, 0),
            ),
            0.4,
            0,
        )

        ruler_indices = (
            ruler_rect > 0
        )

        debug_canvas[
            ruler_indices
        ] = cv2.addWeighted(
            debug_canvas[
                ruler_indices
            ],
            0.5,
            np.full_like(
                debug_canvas[
                    ruler_indices
                ],
                (0, 255, 255),
            ),
            0.5,
            0,
        )

        debug_canvas[
            skeleton
        ] = (255, 0, 255)

        p1 = tuple(
            int(v)
            for v in pts[i]
        )

        p2 = tuple(
            int(v)
            for v in pts[j]
        )

        cv2.line(
            debug_canvas,
            p1,
            p2,
            (255, 255, 0),
            2,
        )

        return {
            "feret_cm": feret_cm,
            "geodesic_cm": geodesic_cm,
            "px_per_cm": px_per_cm,
            "px_per_mm": scale.pixels_per_mm,
            "ruler_confidence": scale.confidence,
            "ruler_mask": ruler_rect,
            "debug_image": debug_canvas,
        }