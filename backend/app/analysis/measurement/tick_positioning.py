from .models import TickSignals, TickPositions
from dataclasses import dataclass
from collections.abc import Sequence

import cv2
import numpy as np


class TickPositioning:

    def find_tick_positions(
        self,
        detection: TickSignals,
        name_for_debug: str | None = None
    ) -> TickPositions:
        """
        Converts the 1D tick signal into ordered tick positions.

        The detection stage gives us a continuous signal and a relative
        threshold. This stage finds reliable peaks in that signal, estimates
        the dominant spacing between neighbouring ticks, and removes peaks
        that are likely duplicate responses from the same physical tick.

        Missing ticks are deliberately not inferred yet.
        """

        signal = np.asarray(detection.signal, dtype=np.float32)

        if signal.ndim != 1:
            raise ValueError(
                "Tick signal must be a one-dimensional array."
            )

        if signal.size == 0:
            raise ValueError(
                "Tick signal must not be empty."
            )

        if not np.isfinite(signal).all():
            raise ValueError(
                "Tick signal contains non-finite values."
            )

        threshold = float(detection.threshold)

        # ------------------------------------------------------------
        # 1. Find local peaks above the detection threshold
        # ------------------------------------------------------------

        candidate_positions, candidate_strengths = (
            self._find_candidate_peaks(
                signal=signal,
                threshold=threshold,
            )
        )

        if candidate_positions.size == 0:
            return TickPositions(
                positions=np.empty(0, dtype=np.float32),
                strengths=np.empty(0, dtype=np.float32),
            )

        if candidate_positions.size == 1:
            return TickPositions(
                positions=candidate_positions.astype(np.float32),
                strengths=candidate_strengths.astype(np.float32),
            )

        # ------------------------------------------------------------
        # 2. Estimate the dominant tick spacing
        # ------------------------------------------------------------

        spacing = self._estimate_tick_spacing(
            candidate_positions
        )

        if spacing <= 0:
            return TickPositions(
                positions=candidate_positions.astype(np.float32),
                strengths=candidate_strengths.astype(np.float32),
            )

        # ------------------------------------------------------------
        # 3. Remove duplicate peaks belonging to the same tick
        # ------------------------------------------------------------

        positions, strengths = self._remove_duplicate_peaks(
            positions=candidate_positions,
            strengths=candidate_strengths,
            expected_spacing=spacing,
        )

        return TickPositions(
            positions=positions.astype(np.float32),
            strengths=strengths.astype(np.float32),
        )

    # ------------------------------------------------------------------
    # Candidate detection
    # ------------------------------------------------------------------

    @staticmethod
    def _find_candidate_peaks(
        signal: np.ndarray,
        threshold: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Finds local maxima whose signal strength exceeds the threshold.

        A sample is considered a peak when it is:
        1. above the threshold,
        2. at least as high as its left neighbour,
        3. higher than its right neighbour.
        """

        peak_positions: list[int] = []
        peak_strengths: list[float] = []

        for index in range(1, len(signal) - 1):
            value = signal[index]

            if value < threshold:
                continue

            is_higher_than_left = value >= signal[index - 1]
            is_higher_than_right = value > signal[index + 1]

            if is_higher_than_left and is_higher_than_right:
                peak_positions.append(index)
                peak_strengths.append(float(value))

        return (
            np.asarray(peak_positions, dtype=np.int32),
            np.asarray(peak_strengths, dtype=np.float32),
        )

    # ------------------------------------------------------------------
    # Spacing estimation
    # ------------------------------------------------------------------

    @staticmethod
    def _estimate_tick_spacing(
        positions: np.ndarray,
    ) -> float:
        """
        Estimates the dominant spacing between candidate ticks.
        """

        if positions.size < 2:
            return 0.0

        positions = np.sort(positions.astype(np.float32))

        distances = np.diff(positions)

        if distances.size == 0:
            return 0.0

        # Ignore zero-distance duplicates.
        distances = distances[distances > 0]

        if distances.size == 0:
            return 0.0

        # Robust estimate:
        #
        # Duplicate detections from a single tick can create very small
        # distances. The real tick spacing should therefore normally be
        # somewhere in the larger part of the distribution.
        #
        # Start with the median of the upper half of neighbouring distances.
        median_distance = float(np.median(distances))

        if median_distance <= 0:
            return 0.0

        # Keep distances that are reasonably close to the median.
        #
        # This is intentionally permissive. We don't want this stage to
        # reject legitimate spacing variation caused by perspective,
        # distortion, or imperfect detection.
        lower = median_distance * 0.5
        upper = median_distance * 1.5

        plausible = distances[
            (distances >= lower)
            & (distances <= upper)
        ]

        if plausible.size == 0:
            return median_distance

        return float(np.median(plausible))

    # ------------------------------------------------------------------
    # Duplicate removal
    # ------------------------------------------------------------------

    @staticmethod
    def _remove_duplicate_peaks(
        positions: np.ndarray,
        strengths: np.ndarray,
        expected_spacing: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Collapses multiple peaks that are too close to represent separate
        ruler ticks.

        Within each cluster, the strongest peak is retained.
        """

        if positions.size <= 1:
            return positions, strengths

        order = np.argsort(positions)

        positions = positions[order]
        strengths = strengths[order]

        # Anything substantially closer than a normal tick spacing is
        # considered part of the same candidate cluster.
        duplicate_distance = expected_spacing * 0.5

        kept_positions: list[int] = []
        kept_strengths: list[float] = []

        cluster_positions: list[int] = []
        cluster_strengths: list[float] = []

        for position, strength in zip(
            positions,
            strengths,
        ):
            position = int(position)
            strength = float(strength)

            if not cluster_positions:
                cluster_positions.append(position)
                cluster_strengths.append(strength)
                continue

            distance = position - cluster_positions[-1]

            if distance <= duplicate_distance:
                cluster_positions.append(position)
                cluster_strengths.append(strength)
            else:
                strongest_index = int(
                    np.argmax(cluster_strengths)
                )

                kept_positions.append(
                    cluster_positions[strongest_index]
                )
                kept_strengths.append(
                    cluster_strengths[strongest_index]
                )

                cluster_positions = [position]
                cluster_strengths = [strength]

        # Flush final cluster.
        if cluster_positions:
            strongest_index = int(
                np.argmax(cluster_strengths)
            )

            kept_positions.append(
                cluster_positions[strongest_index]
            )
            kept_strengths.append(
                cluster_strengths[strongest_index]
            )

        return (
            np.asarray(kept_positions, dtype=np.int32),
            np.asarray(kept_strengths, dtype=np.float32),
        )