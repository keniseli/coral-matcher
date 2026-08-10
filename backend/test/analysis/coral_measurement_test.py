import cv2
import numpy as np
from pathlib import Path
from app.analysis.coral_measurement_service import CoralMeasurementService
from app.orchestration.coral_service import CoralService
from datetime import datetime

FIXTURES_DIR = Path("dev_fixtures")

# Initialize Service (Pass K and D if you have camera calibration)
measurement_service = CoralMeasurementService()
coral_service = CoralService()


def test_pocillopora_measurement_with_partial_ruler_partial_cut_ruler():
    coral_name = "unknown_darkpocillopora"
    image, segmentation = segment(coral_name)

    coral_mask = points_to_mask(segmentation.segments[0].polygon, image.shape)
    
    results = measurement_service.process_frame(image, coral_mask, ruler_mask=None)

    print_metrics(coral_name, results)
    
    cv2.imwrite(f"{datetime.now().strftime('%Y%m%d%H%M')}_debug_output_{coral_name}.jpg", results["debug_image"])

    # 0-1cm: 136px, 1-2cm: 133px, 2-3cm: 134px, 3-4cm: 141px, 4-5cm: 146px, 5-6cm: 155px, 6-7cm: 167px
    assert results['px_per_cm'] == 144
    assert results['feret_cm'] == 6.3
    #assert results['geodesic_cm'] == 42.27


def test_porites_with_partial_ruler():
    coral_name = "unknown_greenporites"
    image, segmentation = segment(coral_name)
    
    coral_mask = points_to_mask(segmentation.segments[1].polygon, image.shape)
    
    results = measurement_service.process_frame(image, coral_mask, ruler_mask=None)

    print_metrics(coral_name, results)

    # Display and Save Visual Debug
    cv2.imwrite(f"{datetime.now().strftime('%Y%m%d%H%M')}_debug_output_{coral_name}.jpg", results["debug_image"])

    # 0-1cm: 131px, 1-2cm: 131px, 2-3cm: 135px, 3-4cm: 138px, 4-5cm: 142px, 5-6cm: 153px, 6-7cm: 166px
    assert results['px_per_cm'] == 142
    assert results['feret_cm'] == 6.7
    #assert results['geodesic_cm'] == 42.27


def test_huge_pavona_ruler_under_rock():
    coral_name = "unknown_hugepavona"
    image, segmentation = segment(coral_name)
    
    coral_mask = points_to_mask(segmentation.segments[0].polygon, image.shape)
    
    results = measurement_service.process_frame(image, coral_mask, ruler_mask=None)

    print_metrics(coral_name, results)

    # Display and Save Visual Debug
    cv2.imwrite(f"{datetime.now().strftime('%Y%m%d%H%M')}_debug_output_{coral_name}.jpg", results["debug_image"])

    # 0-1cm: 131px, 1-2cm: 131px, 2-3cm: 135px, 3-4cm: 138px, 4-5cm: 142px, 5-6cm: 153px, 6-7cm: 166px
    assert results['px_per_cm'] == 142
    assert results['feret_cm'] == 6.7
    #assert results['geodesic_cm'] == 42.27


def test_measure_bright_pavona_ruler_hardly_visible_and_readable():
    coral_name = "unknown_brightpavona"
    image, segmentation = segment(coral_name)
    
    coral_mask = points_to_mask(segmentation.segments[0].polygon, image.shape)
    
    results = measurement_service.process_frame(image, coral_mask, ruler_mask=None)

    print_metrics(coral_name, results)

    cv2.imwrite(f"{datetime.now().strftime('%Y%m%d%H%M')}_debug_output_{coral_name}.jpg", results["debug_image"])

    # 0-1cm: 108px, 1-2cm: 100px, 2-3cm: 99px, 3-4cm: 96px, 4-5cm: 97px, 5-6cm: 97px, 6-7cm: 95px
    assert results['px_per_cm'] == 98
    assert results['feret_cm'] == 9.6
    #assert results['geodesic_cm'] == 42.27

def test_measure_bigpocillopora():
    coral_name = "unknown_bigpocillopora"
    image, segmentation = segment(coral_name)
    
    coral_mask = points_to_mask(segmentation.segments[0].polygon, image.shape)
    
    results = measurement_service.process_frame(image, coral_mask, ruler_mask=None)

    print_metrics(coral_name, results)

    cv2.imwrite(f"{datetime.now().strftime('%Y%m%d%H%M')}_debug_output_{coral_name}.jpg", results["debug_image"])

    # 0-1cm: px, 1-2cm: px, 2-3cm: px, 3-4cm: px, 4-5cm: px, 5-6cm: px, 6-7cm: px
    assert results['px_per_cm'] == 98
    assert results['feret_cm'] == 9.6
    #assert results['geodesic_cm'] == 42.27
    
# 0-1cm: px, 1-2cm: px, 2-3cm: px, 3-4cm: px, 4-5cm: px, 5-6cm: px, 6-7cm: px
#    assert results['px_per_cm'] == 111.02
#    assert results['feret_cm'] == 6.7
#    assert results['geodesic_cm'] == 42.27

def segment(coral_name):
    base_dir = Path(__file__).parents[2]
    path = sorted((base_dir / FIXTURES_DIR / coral_name).glob("*.jpg"))
    image = cv2.imread(str(path[0]))

    segmentation = coral_service.segment_image(image, path[0].name)
    return image,segmentation


def print_metrics(coral_name, results):
    print("")
    print("")
    print(f"Results {coral_name}")
    print(f"Detected Scale : {results['px_per_cm']:.2f} pixels/cm")
    print(f"Feret Length   : {results['feret_cm']:.2f} cm")
    print(f"Geodesic Length: {results['geodesic_cm']:.2f} cm")


# AI
def points_to_mask(points, image_shape: tuple) -> np.ndarray:
    """
    Converts a list of Point objects (with .x and .y attributes or dict keys)
    into a binary single-channel uint8 mask (0 and 255).
    
    :param points: List of Point objects (e.g., [Point(x=10, y=20), ...])
    :param image_shape: (height, width) or full image.shape (h, w, c)
    :return: np.ndarray of shape (height, width) with dtype uint8
    """
    # Extract height and width regardless of whether image_shape is (H, W) or (H, W, C)
    h, w = image_shape[:2]
    
    # 1. Extract (x, y) coordinates into an (N, 2) NumPy array
    # Works if Point is an object with .x, .y attributes OR a dict with ['x'], ['y']
    if hasattr(points[0], 'x'):
        coords = np.array([[int(p.x), int(p.y)] for p in points], dtype=np.int32)
    else:
        coords = np.array([[int(p['x']), int(p['y'])] for p in points], dtype=np.int32)
        
    # 2. Create blank black mask
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # 3. Fill the polygon defined by the boundary points
    # Note: cv2.fillPoly expects an array of shape (num_polygons, num_points, 2)
    cv2.fillPoly(mask, [coords], color=255)
    
    return mask