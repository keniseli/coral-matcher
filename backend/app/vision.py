import cv2
import numpy as np

def apply_underwater_corrections(img_matrix: np.ndarray):
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

import cv2
import numpy as np


def crop_primary_coral(
    img_matrix: np.ndarray,
    masks: list,
    padding_ratio: float = 0.15,
):
    """
    Crops the highest-confidence coral detected by CoralSCOP.

    Steps:
      1. Select mask with highest predicted IoU
      2. Expand bounding box with padding
      3. Crop original image
      4. Remove background using the segmentation mask
      5. Pad to a square canvas
    """

    if img_matrix is None or img_matrix.size == 0:
        return None

    if not masks:
        return {
            "crop": img_matrix,
            "square_crop": img_matrix,
            "bounding_box": None,
            "mask": None,
        }

    #
    # Select best CoralSCOP mask by finding highest intersection over union (iou).
    # Basically this is CoralSCOP's estimate of 'If a human drew the perfect mask,
    # how much would this mask overlap with it?
    #
    best_mask = max(masks, key=lambda m: (m["predicted_iou"]))

    segmentation = best_mask["segmentation"]
    x, y, w, h = map(int, best_mask["bbox"])

    height, width = img_matrix.shape[:2]

    #
    # Apply padding
    #
    pad_x = int(w * padding_ratio)
    pad_y = int(h * padding_ratio)

    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(width, x + w + pad_x)
    y2 = min(height, y + h + pad_y)

    #
    # Crop image
    #
    crop = img_matrix[y1:y2, x1:x2].copy()

    #
    # Crop mask
    #
    crop_mask = segmentation[y1:y2, x1:x2]

    #
    # Remove background
    #
    crop[~crop_mask] = 0

    #
    # Pad to square
    #
    crop_h, crop_w = crop.shape[:2]
    side = max(crop_h, crop_w)

    square_crop = np.zeros(
        (side, side, 3),
        dtype=crop.dtype,
    )

    offset_y = (side - crop_h) // 2
    offset_x = (side - crop_w) // 2

    square_crop[
        offset_y:offset_y + crop_h,
        offset_x:offset_x + crop_w,
    ] = crop

    return {
        "crop": crop,
        "square_crop": square_crop,
        "bounding_box": (x1, y1, x2, y2),
        "mask": best_mask,
    }

def create_debug_collage(original, corrected, edges, contour_debug, crop):
    if len(edges.shape) == 2:
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
    target_h = 500
    target_w = 500

    def prepare(img):
        h,w = img.shape[:2]
        scale = min(target_w/w,
                    target_h/h)
        resized = cv2.resize(
            img,
            (int(w*scale),
             int(h*scale))
        )

        canvas = np.full(
            (target_h,target_w,3),
            40,
            dtype=np.uint8
        )

        y = (target_h-resized.shape[0])//2
        x = (target_w-resized.shape[1])//2

        canvas[
            y:y+resized.shape[0],
            x:x+resized.shape[1]
        ] = resized

        return canvas

    panels = [
        prepare(original),
        prepare(edges),
        prepare(contour_debug),
        prepare(crop)
    ]

    cv2.putText(
        panels[0],
        "Original",
        (15,35),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255,255,255),
        2
    )

    cv2.putText(
        panels[1],
        "Edges",
        (15,35),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255,255,255),
        2
    )

    cv2.putText(
        panels[2],
        "Contours",
        (15,35),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255,255,255),
        2
    )

    cv2.putText(
        panels[3],
        "Crop",
        (15,35),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255,255,255),
        2
    )

    top = np.hstack((panels[0],panels[1]))
    bottom = np.hstack((panels[2],panels[3]))

    return np.vstack((top,bottom))
