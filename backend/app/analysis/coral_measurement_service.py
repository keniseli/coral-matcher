import cv2
import numpy as np
from scipy.optimize import minimize
from scipy.spatial.distance import cdist
import skimage.morphology as morph
from datetime import datetime

class CoralMeasurementService:
    def __init__(self, camera_matrix=None, dist_coeffs=None):
        self.K = camera_matrix
        self.D = dist_coeffs

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
    def estimate_ruler_scale(self, img: np.ndarray, ruler_mask: np.ndarray) -> float:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ruler_roi = cv2.bitwise_and(gray, gray, mask=ruler_mask)
        
        # 1. Morphological Top-Hat to isolate thin tick lines from background & large numbers
        # A small rectangular kernel aligned with ticks highlights lines and suppresses wide numbers
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 9))
        top_hat = cv2.morphologyEx(ruler_roi, cv2.MORPH_TOPHAT, kernel)
        
        edges = cv2.Canny(top_hat, 30, 100)
        
        # 2. Extract edge point coordinates
        nonzeros = np.where(edges > 0)
        points = np.column_stack((nonzeros[1], nonzeros[0])) # [x, y]
        
        if len(points) < 20:
            raise ValueError("Insufficient tick edges found on ruler ROI.")

        # 3. Determine primary orientation via Principal Component Analysis (PCA)
        # PCA avoids OpenCV's minAreaRect 90-degree angle-swap bugs
        mean = np.mean(points, axis=0)
        pts_centered = points - mean
        cov = np.cov(pts_centered.T)
        evals, evecs = np.linalg.eig(cov)
        
        # Major eigenvector corresponds to the ruler's long axis
        major_axis = evecs[:, np.argmax(evals)]
        
        # 4. Project 2D edge points onto the 1D major axis
        projections = np.dot(pts_centered, major_axis)
        
        # 5. Dynamic 1-Pixel Bin Resolution Histogram
        min_p, max_p = np.min(projections), np.max(projections)
        num_bins = int(np.ceil(max_p - min_p))  # Exactly 1 pixel per bin!
        
        hist, bin_edges = np.histogram(projections, bins=num_bins)
        
        # Smooth histogram signal using 1D Gaussian filter
        kernel_size = 5
        smoothed_hist = np.convolve(hist, np.ones(kernel_size)/kernel_size, mode='same')
        
        # 6. Find density peaks (tick mark positions along the 1D axis)
        threshold = np.mean(smoothed_hist) + 0.5 * np.std(smoothed_hist)
        peak_indices = np.where(smoothed_hist > threshold)[0]
        
        if len(peak_indices) < 2:
            raise ValueError("Could not resolve clear tick mark peaks.")
            
        peak_positions = bin_edges[peak_indices]
        peak_spacings = np.diff(peak_positions)
        
        # 7. Dynamic mm Tick Measurement
        # Peak spacings represent adjacent tick marks (1 mm apart)

        # Filter out 0 or 1-pixel noise (peaks detected on the exact same tick line)
        valid_spacings = peak_spacings[peak_spacings >= 2.0]
        
        if len(valid_spacings) == 0:
            raise ValueError("Could not resolve clear tick spacing.")

        # The dominant/smallest repeating interval is the millimeter spacing
        # Using a low percentile (or median of the lower half) isolates 1mm ticks 
        # and ignores occasional gaps caused by missing/occluded ticks
        px_per_mm = float(np.median(valid_spacings[valid_spacings < np.percentile(valid_spacings, 60)]))
        
        # Calculate final cm scale dynamically
        px_per_cm = px_per_mm * 10.0
        
        return px_per_cm

    # -------------------------------------------------------------------------
    # FULL PROCESS PIPELINE
    # -------------------------------------------------------------------------
    def process_frame(self, img: np.ndarray, coral_mask: np.ndarray, ruler_mask: np.ndarray | None = None):
        # Auto-detect ruler if mask not explicitly passed
        if ruler_mask is None:
            ruler_mask = self.detect_ruler_mask(img)        

        # 1. Undistort
        img_rect = self.undistort_image(img)
        coral_rect = self.undistort_image(coral_mask, reference_color_img=img)
        ruler_rect = self.undistort_image(ruler_mask, reference_color_img=img)
        
        # 2. Scale
        px_per_cm = self.estimate_ruler_scale(img_rect, ruler_rect)
        
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