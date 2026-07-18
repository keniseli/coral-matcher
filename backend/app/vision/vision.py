import numpy as np
import cv2

from app.domain.models import Segment
from app.vision.models import MaskResult

class VisionService:
    """
    Provides vision-related functions
    """
    
    def __init__(self) -> None:
        print("nothing yet")

    
    def mask(self, image: np.ndarray, segments: list[Segment]) -> MaskResult:
        """
        Masks the image with the given segments. The rest of the picture will be black
        """
        
        # create a binary mask for the image
        mask = np.zeros(image.shape[:2], dtype=np.uint8)

        # transform the segments into polygons
        polygons = [
            np.array([(point.x, point.y) for point in segment.polygon],dtype=np.int32)
            for segment in segments
        ]

        # set 1 for all pixels where chosen segments overlay the image
        cv2.fillPoly(mask, polygons, 255)
        
        # mask the image with the polygons-mask. 
        # and-ing will result in only the masked area to "not be black"
        masked = cv2.bitwise_and(image, image, mask=mask)
        
        return MaskResult(masked_image=masked)