import numpy as np

from .ruler_detection import RulerDetection
from .ruler_rotation import RulerRotation

class CoralMeasurementService:
    """
    Estimate coral dimensions from an image containing a metric ruler.

    The ruler is first segmented, rotated so its long axis is horizontal,
    and then analysed along that axis.

    <h3>Assumptions:</h3>
        Relevant parts of the ruler are of a bright gray/silver/slate color.
        Ruler is metric.
        Metric ticks are perpendicular to the ruler's long axis.

    <h3>Stages of measurement:</h3>
    Identify ruler and metric units:
    <ol>
        <li>Detect ruler and its rotation</li>
        <li>Rotate ruler mask</li>
        <li>Detect the signal of the (now) vertical ticks (strength and size)</li>
        <li>Interpret the detected signals of the ticks</li>
        <li>Estimate the ruler scale (px / mm or px / cm)</li>
    </ol>
    Measure coral:
    <ol>
        <li>Find the longest feret diameter</li>
        <li>Approximate geodesic skeleton</li>
        <li>Use metric units to calculate sizes</li>
    <ol>
    """


    def __init__(
        self,
    ) -> None:
        self.ruler_detection = RulerDetection()
        self.ruler_rotation = RulerRotation()
        
    def measure_coral(self, image: np.ndarray):
        self.estimate_px_per_cm(image)


    def estimate_px_per_cm(self, image: np.ndarray):
        geometry = self.ruler_detection.detect_ruler(image)
        rotation = self.ruler_rotation.rotate_ruler(image, geometry.mask, geometry)


