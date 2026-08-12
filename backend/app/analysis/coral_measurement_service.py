import cv2
import numpy as np
from scipy.optimize import minimize
from scipy.spatial.distance import cdist
import skimage.morphology as morph
from datetime import datetime
from .zero_shot_ruler_segmentation_service import ZeroShotRulerSegmentationService

class CoralMeasurementService:
    def __init__(self, camera_matrix=None, dist_coeffs=None):
        self.K = camera_matrix
        self.D = dist_coeffs
        self.ruler_segmenter = ZeroShotRulerSegmentationService()

    # -------------------------------------------------------------------------
    # AUTOMATIC RULER SEGMENTATION (HSV + Geometry Filter)
    # -------------------------------------------------------------------------
    def detect_ruler_mask(self, img: np.ndarray) -> np.ndarray:
        """
        Robustly segments the white CM ruler side while rejecting hands/fingers,
        sand, algae, and the pink 'inches' stripe.
        """
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        
        L = lab[:, :, 0]  # Lightness
        S = hsv[:, :, 1]  # Saturation
        
        # -------------------------------------------------------------------------
        # STEP 1: ISOLATE MAGENTA / PINK STRIPE (Inches Side)
        # -------------------------------------------------------------------------
        lower_pink = np.array([135, 70, 80])
        upper_pink = np.array([175, 255, 255])
        pink_mask = cv2.inRange(hsv, lower_pink, upper_pink)
        
        kernel_pink = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        pink_mask_closed = cv2.morphologyEx(pink_mask, cv2.MORPH_CLOSE, kernel_pink)

        # -------------------------------------------------------------------------
        # STEP 2: BRIGHTNESS + SMOOTH TEXTURE (Rejects Sand/Algae)
        # -------------------------------------------------------------------------
        # White plastic is bright (L > 130) and neutral (S < 110)
        bright_mask = (L > 130) & (S < 110)
        bright_mask = (bright_mask * 255).astype(np.uint8)

        # Sand and algae have high local texture variation (std dev).
        # Smooth plastic slate has very low local variance.
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        texture_variance = cv2.absdiff(gray, blur)
        smooth_mask = (texture_variance < 12).astype(np.uint8) * 255

        # Candidate slate area: Must be BOTH bright AND smooth
        slate_candidates = cv2.bitwise_and(bright_mask, smooth_mask)

        # Bridge small gaps (e.g. text/tick marks)
        kernel_slate = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))
        slate_closed = cv2.morphologyEx(slate_candidates, cv2.MORPH_CLOSE, kernel_slate)

        # -------------------------------------------------------------------------
        # STEP 3: GEOMETRIC SHAPING (Rejects Fingers & Curved Organics)
        # -------------------------------------------------------------------------
        contours, _ = cv2.findContours(slate_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        ruler_body_mask = np.zeros_like(gray)

        best_cnt = None
        best_score = -1

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 1000:  # Ignore tiny specks
                continue

            # Fit rotated bounding box
            rect = cv2.minAreaRect(cnt)
            (w, h) = rect[1]
            if w == 0 or h == 0:
                continue

            rect_area = w * h
            extent = area / rect_area  # Rectangularity ratio (1.0 = perfect rectangle)

            # Calculate Solidity (Area / Convex Hull Area)
            # Hands/fingers touching a ruler create concavities (jagged dips), dropping solidity
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            solidity = area / hull_area if hull_area > 0 else 0

            # Score based on high rectangularity (extent) + high solidity
            # A ruler with fingers on it will have lower extent/solidity than a clean rectangle
            score = extent * 2.0 + solidity * 3.0

            if score > best_score and extent > 0.4:
                best_score = score
                best_cnt = cnt

        if best_cnt is not None:
            # Instead of drawing the raw jagged contour (which includes fingers),
            # draw the SOLID CONVEX HULL or MINIMUM AREA RECTANGLE to slice off fingers!
            rect = cv2.minAreaRect(best_cnt)
            box = cv2.boxPoints(rect)
            box = np.int32(box)
            cv2.fillPoly(ruler_body_mask, [box], color=255)

        # -------------------------------------------------------------------------
        # STEP 4: SUBTRACT PINK STRIPE & DIVER FINGER OVERLAPS
        # -------------------------------------------------------------------------
        # Subtract the pink stripe from the straightened slate rectangle
        cm_ruler_mask = cv2.bitwise_and(ruler_body_mask, cv2.bitwise_not(pink_mask_closed))

        # Final cleanup
        kernel_clean = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        cm_ruler_mask = cv2.morphologyEx(cm_ruler_mask, cv2.MORPH_OPEN, kernel_clean)

        return cm_ruler_mask


    # -------------------------------------------------------------------------
    # STAGE 1 (OPTION A): Zero-Shot Edge-Straightening Undistortion
    # -------------------------------------------------------------------------
    def _estimate_undistort_k1(self, img: np.ndarray) -> np.ndarray:
        """
        Optimizes a single radial distortion parameter (k1) by straightening 
        detected long lines in the image.
        """
        # Ensure we have a grayscale image for edge detection
        if len(img.shape) == 3 and img.shape[2] in (3, 4):
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=80, minLineLength=100, maxLineGap=10)
        
        h, w = img.shape[:2]
        center = (w / 2, h / 2)

        if lines is None:
            # Fallback if no lines detected: return original
            return img.copy()

        def objective(k1):
            total_error = 0.0
            k = k1[0] / 1e7  
            
            for line in lines[:15]:
                x1, y1, x2, y2 = line[0]
                mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                r2 = (mx - center[0])**2 + (my - center[1])**2
                dr = 1 + k * r2
                
                dx, dy = x2 - x1, y2 - y1
                line_len = np.hypot(dx, dy)
                if line_len == 0:
                    continue
                distance = abs(dy * mx - dx * my + x2 * y1 - y2 * x1) / line_len
                total_error += distance * dr
            return total_error

        res = minimize(objective, [0.0], method='Nelder-Mead')
        opt_k1 = res.x[0] / 1e7
        
        K = np.array([[w, 0, w/2], [0, w, h/2], [0, 0, 1]], dtype=np.float32)
        D = np.array([opt_k1, 0, 0, 0], dtype=np.float32)
        
        return cv2.undistort(img, K, D)

    def undistort_image(self, img: np.ndarray, reference_color_img: np.ndarray = None) -> np.ndarray:
        """
        Undistorts an image or mask.
        If using Option A (line optimization), pass reference_color_img when undistorting a mask
        so k1 is computed from the color image, not the mask.
        """
        if self.K is not None and self.D is not None:
            # OPTION B: Known Camera Parameters
            h, w = img.shape[:2]
            new_K, _ = cv2.getOptimalNewCameraMatrix(self.K, self.D, (w, h), 1, (w, h))
            return cv2.undistort(img, self.K, self.D, None, new_K)
        else:
            # OPTION A: Line Straightening Fallback
            # If img is a 1-channel mask, compute distortion parameters using reference_color_img
            target_for_k1 = reference_color_img if reference_color_img is not None else img
            
            # Extract k1 using the color image, then apply to 'img'
            return self._apply_k1_undistort(img, target_for_k1)

    def _apply_k1_undistort(self, img_to_transform: np.ndarray, img_for_estimation: np.ndarray) -> np.ndarray:
        """Helper to estimate k1 from one image and apply it to another."""
        # Ensure estimation image is grayscale
        if len(img_for_estimation.shape) == 3 and img_for_estimation.shape[2] in (3, 4):
            gray = cv2.cvtColor(img_for_estimation, cv2.COLOR_BGR2GRAY)
        else:
            gray = img_for_estimation.copy()

        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=80, minLineLength=100, maxLineGap=10)
        
        h, w = img_to_transform.shape[:2]
        center = (w / 2, h / 2)

        if lines is None:
            return img_to_transform.copy()

        def objective(k1):
            total_error = 0.0
            k = k1[0] / 1e7  
            for line in lines[:15]:
                x1, y1, x2, y2 = line[0]
                mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                r2 = (mx - center[0])**2 + (my - center[1])**2
                dr = 1 + k * r2
                dx, dy = x2 - x1, y2 - y1
                line_len = np.hypot(dx, dy)
                if line_len == 0:
                    continue
                distance = abs(dy * mx - dx * my + x2 * y1 - y2 * x1) / line_len
                total_error += distance * dr
            return total_error

        res = minimize(objective, [0.0], method='Nelder-Mead')
        opt_k1 = res.x[0] / 1e7
        
        K = np.array([[w, 0, w/2], [0, w, h/2], [0, 0, 1]], dtype=np.float32)
        D = np.array([opt_k1, 0, 0, 0], dtype=np.float32)
        
        return cv2.undistort(img_to_transform, K, D)

    # -------------------------------------------------------------------------
    # STAGE 2: Extract Metric Scale
    # -------------------------------------------------------------------------
    def estimate_ruler_scale(self, img: np.ndarray, ruler_mask: np.ndarray, name_for_debug: str = "") -> float:
        """
        Direct 1mm fundamental scale estimator.
        Finds the first valid local peak in autocorrelation (always 1mm tick spacing)
        and multiplies by 10.0 to get px/cm.
        """
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 1. Straighten ruler geometrically via minAreaRect
        contours, _ = cv2.findContours(ruler_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            raise ValueError("Empty ruler mask passed to scale estimator.")
        
        cnt = max(contours, key=cv2.contourArea)
        rect = cv2.minAreaRect(cnt)
        (cx, cy), (rw, rh), angle = rect

        if rw > rh:
            angle += 90
            rect_w, rect_h = rh, rw
        else:
            rect_w, rect_h = rw, rh

        # Warp image so ruler stands vertically
        M = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)
        rotated_gray = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC)
        rotated_mask = cv2.warpAffine(ruler_mask, M, (w, h), flags=cv2.INTER_NEAREST)

        # Crop rotated ROI
        ymin, ymax = max(0, int(cy - rect_h / 2)), min(h, int(cy + rect_h / 2))
        xmin, xmax = max(0, int(cx - rect_w / 2)), min(w, int(cx + rect_w / 2))

        roi_gray = rotated_gray[ymin:ymax, xmin:xmax]
        if roi_gray.size == 0 or roi_gray.shape[0] < 30 or roi_gray.shape[1] < 10:
            raise ValueError("Rotated ROI too small for processing.")

        # 2. Isolate tick edge strip (Outer 20% on the metric side)
        roi_w = roi_gray.shape[1]
        left_strip = roi_gray[:, :int(roi_w * 0.22)]
        right_strip = roi_gray[:, int(roi_w * 0.78):]
        
        left_score = np.std(cv2.Sobel(left_strip, cv2.CV_64F, 0, 1, ksize=3))
        right_score = np.std(cv2.Sobel(right_strip, cv2.CV_64F, 0, 1, ksize=3))

        tick_strip = left_strip if left_score > right_score else right_strip

        # 3. Vertical Gradient (Sobel Y)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        tick_strip_enhanced = clahe.apply(tick_strip)
        sobel_y = np.abs(cv2.Sobel(tick_strip_enhanced, cv2.CV_64F, 0, 1, ksize=3))

        # 1D signal along ruler length
        signal = np.mean(sobel_y, axis=1)
        signal = signal - np.mean(signal)
        norm = np.sum(signal**2)
        if norm == 0:
            raise ValueError("Flat gradient signal along tick strip.")

        # 4. Autocorrelation
        autocorr = np.correlate(signal, signal, mode='full')
        autocorr = autocorr[len(signal) - 1:] / norm

        # 5. Find the FIRST local peak (The 1mm Fundamental Frequency)
        min_lag = 3   # Smallest allowable 1mm tick pitch in pixels (~3px)
        max_lag = min(len(autocorr) - 2, 80)
        
        first_peak_idx = None
        for i in range(min_lag, max_lag):
            if autocorr[i] > autocorr[i - 1] and autocorr[i] > autocorr[i + 1]:
                # Prominence check: must be a real peak above baseline noise
                if autocorr[i] > 0.05:
                    first_peak_idx = i
                    break

        if first_peak_idx is None:
            # Fallback if no local peak found in min_lag..max_lag window
            first_peak_idx = int(np.argmax(autocorr[min_lag:max_lag]) + min_lag)

        # 6. Parabolic Sub-Pixel Interpolation
        k = first_peak_idx
        y0, y1, y2 = autocorr[k - 1], autocorr[k], autocorr[k + 1]
        denom = (y0 - 2 * y1 + y2)
        delta = (y0 - y2) / (2.0 * denom) if denom != 0 else 0
        refined_1mm_lag = float(k) + delta

        # Always 1mm tick pitch -> multiply by 10 for px/cm
        px_per_cm = refined_1mm_lag * 10.0
        return px_per_cm

    # -------------------------------------------------------------------------
    # FULL PROCESS PIPELINE
    # -------------------------------------------------------------------------
    def process_frame(self, img: np.ndarray, coral_mask: np.ndarray, name_for_debug: str = ""):
        ruler_mask = self.ruler_segmenter.predict_ruler_mask(img, "a white measuring ruler . white scale slate")

        # 1. Undistort
        img_rect = self.undistort_image(img)
        coral_rect = self.undistort_image(coral_mask, reference_color_img=img)
        ruler_rect = self.undistort_image(ruler_mask, reference_color_img=img)
        
        # 2. Scale
        px_per_cm = self.estimate_ruler_scale(img_rect, ruler_rect, name_for_debug)
        
        # 3. Measures
        binary_mask = (coral_rect > 0).astype(np.uint8)
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        coral_cnt = max(contours, key=cv2.contourArea)
        
        hull = cv2.convexHull(coral_cnt)
        pts = hull.reshape(-1, 2)
        dist_matrix = cdist(pts, pts, metric='euclidean')
        i, j = np.unravel_index(np.argmax(dist_matrix), dist_matrix.shape)
        
        feret_px = dist_matrix[i, j]
        skeleton = morph.skeletonize(binary_mask)
        geodesic_px = np.sum(skeleton)
        
        feret_cm = feret_px / px_per_cm
        geodesic_cm = geodesic_px / px_per_cm
        
        # 4. Debug Visualization
        debug_canvas = img_rect.copy()
        debug_canvas[coral_rect > 0] = cv2.addWeighted(
            debug_canvas[coral_rect > 0], 0.6, 
            np.full_like(debug_canvas[coral_rect > 0], (0, 255, 0)), 0.4, 0
        )
        debug_canvas[ruler_rect > 0] = cv2.addWeighted(
            debug_canvas[ruler_rect > 0], 0.5, 
            np.full_like(debug_canvas[ruler_rect > 0], (0, 255, 255)), 0.5, 0
        )
        debug_canvas[skeleton > 0] = (255, 0, 255)
        
        p1, p2 = tuple(pts[i]), tuple(pts[j])
        cv2.line(debug_canvas, p1, p2, (255, 255, 0), 2)
        
        return {
            "feret_cm": feret_cm,
            "geodesic_cm": geodesic_cm,
            "px_per_cm": px_per_cm,
            "ruler_mask": ruler_rect,
            "debug_image": debug_canvas
        }