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
    
    def rotate_image(self, image, angle):
        """
        Rotate an OpenCV image by 0, 90, 180, or 270 degrees.
        """

        if angle == 0:
            return image.copy()

        if angle == 90:
            return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)

        if angle == 180:
            return cv2.rotate(image, cv2.ROTATE_180)

        if angle == 270:
            return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

        raise ValueError(f"Unsupported rotation angle: {angle}")
    
    def apply_underwater_corrections(self, img_matrix: np.ndarray) -> np.ndarray:
        """
        Applies CLAHE local contrast enhancement and Gray World color balancing
        to recover lost red channel data signatures underwater.
        """
        if img_matrix is None or img_matrix.size == 0:
            raise ValueError("Empty image matrix passed to processing engine.")
        
        # 1. CLAHE Contrast Equalization
        lab = cv2.cvtColor(img_matrix, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l_channel)
        enhanced_lab = cv2.merge((cl, a_channel, b_channel))
        bgr_enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

        # 2. Gray World Channel Normalization (Red Recovery)
        b, g, r = cv2.split(bgr_enhanced)
        mean_b, mean_g, mean_r = np.mean(b), np.mean(g), np.mean(r)
        mean_gray = (mean_b + mean_g + mean_r) / 3.0
        
        scale_b = mean_gray / mean_b if mean_b > 0 else 1.0
        scale_g = mean_gray / mean_g if mean_g > 0 else 1.0
        scale_r = mean_gray / mean_r if mean_r > 0 else 1.0
        
        b_bal = np.clip((b * scale_b), 0, 255).astype(np.uint8)
        g_bal = np.clip((g * scale_g), 0, 255).astype(np.uint8)
        r_bal = np.clip((r * scale_r), 0, 255).astype(np.uint8)
        
        return cv2.merge((b_bal, g_bal, r_bal))
