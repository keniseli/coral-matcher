from .models import RotatedRuler, RulerGeometry
import numpy as np

class RulerRotation:
    """
    Rotates a given ruler horizontally for further 1 dimensional processing
    <br />
    <br />
    Produces a debug image with a horizontal ruler axis
    """
    
    def rotate_ruler(
        self,
        image: np.ndarray,
        ruler_mask: np.ndarray,
        geometry: RulerGeometry,
    ) -> RotatedRuler:
        ...