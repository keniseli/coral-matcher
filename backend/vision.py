import cv2
import numpy as np

def apply_underwater_corrections(img_matrix):
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

def crop_primary_coral(img_matrix, padding_ratio=0.15):
    """
    Attempts to isolate the primary coral colony.

    Assumptions:
    - Coral occupies roughly 60-90% of the image.
    - Coral is near the center.
    - If no suitable contour is found, returns the original image.
    """

    if img_matrix is None or img_matrix.size == 0:
        return img_matrix

    height, width = img_matrix.shape[:2]
    image_center = np.array([width / 2, height / 2])

    # Remove small underwater particles
    blurred = cv2.GaussianBlur(img_matrix, (5, 5), 0)

    gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)

    edges = cv2.Canny(gray, 40, 120)

    kernel = np.ones((7, 7), np.uint8)
    closed = cv2.morphologyEx(
        edges,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=2
    )

    contours, _ = cv2.findContours(
        closed,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if len(contours) == 0:
        return img_matrix

    best_score = -1
    best_rect = None

    image_area = width * height

    for contour in contours:

        area = cv2.contourArea(contour)

        if area < image_area * 0.02:
            continue

        x, y, w, h = cv2.boundingRect(contour)

        contour_center = np.array([
            x + w / 2,
            y + h / 2
        ])

        distance = np.linalg.norm(contour_center - image_center)

        distance_score = 1.0 - (
            distance /
            np.linalg.norm(image_center)
        )

        area_score = area / image_area

        score = (
            area_score * 0.7 +
            distance_score * 0.3
        )

        if score > best_score:
            best_score = score
            best_rect = (x, y, w, h)

    if best_rect is None:
        return img_matrix

    x, y, w, h = best_rect

    pad_x = int(w * padding_ratio)
    pad_y = int(h * padding_ratio)

    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)

    x2 = min(width, x + w + pad_x)
    y2 = min(height, y + h + pad_y)

    crop = img_matrix[y1:y2, x1:x2]

    return crop
