import pytest
import cv2
import numpy as np
from pathlib import Path
from app.analysis.coral_measurement_service import CoralMeasurementService
from app.segmentation.fixture_provider import FixtureProvider
from datetime import datetime

FIXTURES_DIR = Path("dev_fixtures")
PX_PER_CM_ERROR_TOLERANCE=3

# Initialize Service (Pass K and D if you have camera calibration)
measurement_service = CoralMeasurementService()
fixture_segmenter = FixtureProvider()

def test_measure_algalpavona():
    coral_name = "unknown_algalpavona"
    image,coral_mask = prepare_measurement(coral_name)
    
    results = measurement_service.process_frame(image, coral_mask, coral_name.replace("unknown_", ""))

    debug_outputs(coral_name, results)
    
    # 0-1cm: 50px, 1-2cm: 46px, 2-3cm: 47px, 3-4cm: 47px, 4-5cm: 45px, 5-6cm: 47px, 6-7cm: 47px
    assert results['px_per_cm'] == pytest.approx(47, abs=PX_PER_CM_ERROR_TOLERANCE)
    assert results['feret_cm'] == 4.7
    #assert results['geodesic_cm'] == 42.27


def test_measure_bigpocillopora():
    coral_name = "unknown_bigpocillopora"
    image,coral_mask = prepare_measurement(coral_name)
    
    results = measurement_service.process_frame(image, coral_mask, coral_name.replace("unknown_", ""))
    
    debug_outputs(coral_name, results)
    
    # 0-1cm: 104px, 1-2cm: 100px, 2-3cm: 97px, 3-4cm: 97px, 4-5cm: 98px, 5-6cm: 97px, 6-7cm: 97px
    assert results['px_per_cm'] ==  pytest.approx(98, abs=PX_PER_CM_ERROR_TOLERANCE)
    assert results['feret_cm'] == 9.6
    #assert results['geodesic_cm'] == 42.27


def test_measure_bright_pavona_ruler_hardly_visible_and_readable():
    coral_name = "unknown_brightpavona"
    image,coral_mask = prepare_measurement(coral_name, "20260809_2100.jpg")

    results = measurement_service.process_frame(image, coral_mask, coral_name.replace("unknown_", ""))

    debug_outputs(coral_name, results)

    # 0-1cm: 125px, 1-2cm: , 2-3cm: , 3-4cm: , 4-5cm: , 5-6cm: , 6-7cm: 
    assert results['px_per_cm'] == pytest.approx(121, abs=PX_PER_CM_ERROR_TOLERANCE)
    assert results['feret_cm'] == 9.3
    #assert results['geodesic_cm'] == 42.27


def test_measure_bright_pavona_ruler_visible_and_readable():
    coral_name = "unknown_brightpavona"
    image,coral_mask = prepare_measurement(coral_name, "20260811_1638.jpg")
    
    results = measurement_service.process_frame(image, coral_mask, coral_name.replace("unknown_", ""))
    
    debug_outputs(coral_name, results)

    # 0-1cm: 39px, 1-2cm: 38px, 2-3cm: 38px, 3-4cm: 39px, 4-5cm: 41px, 5-6cm: 40px, 6-7cm: 42px
    assert results['px_per_cm'] == pytest.approx(39.5, abs=PX_PER_CM_ERROR_TOLERANCE)
    assert results['feret_cm'] == 9.5
    #assert results['geodesic_cm'] == 42.27


def test_measure_branchy_pavona_ruler_bright_hand_visible():
    coral_name = "unknown_branchypavona"
    image,coral_mask = prepare_measurement(coral_name, segment_index=0)
    
    results = measurement_service.process_frame(image, coral_mask, coral_name.replace("unknown_", ""))
    
    debug_outputs(coral_name, results)

    # 0-1cm: 42px, 1-2cm: 39px, 2-3cm: 39px, 3-4cm: 37px, 4-5cm: 36px, 5-6cm: 36px, 6-7cm: 37px
    assert results['px_per_cm'] == pytest.approx(38, abs=PX_PER_CM_ERROR_TOLERANCE)
    #TODO ideally not feret since this is branching
    assert results['feret_cm'] == 6.4
    #assert results['geodesic_cm'] == 42.27


def test_dark_pocillopora_scale_obscured():
    coral_name = "unknown_darkpocillopora"
    image, coral_mask = prepare_measurement(coral_name, "20260809_1943.jpg")
    
    results = measurement_service.process_frame(image, coral_mask, coral_name.replace("unknown_", ""))

    debug_outputs(coral_name, results)

    # 0-1cm: 136px, 1-2cm: 133px, 2-3cm: 134px, 3-4cm: 141px, 4-5cm: 146px, 5-6cm: 155px, 6-7cm: 167px
    assert results['px_per_cm'] == pytest.approx(143.73, abs=PX_PER_CM_ERROR_TOLERANCE)
    assert results['feret_cm'] == 6.3
    
def test_dark_pocillopora_scale_non_obscured():
    coral_name = "unknown_darkpocillopora"
    image, coral_mask = prepare_measurement(coral_name, "20260811_1638_darkpocillopora.jpg")
    
    results = measurement_service.process_frame(image, coral_mask, coral_name.replace("unknown_", ""))

    debug_outputs(coral_name, results)

    # 0-1cm: 136px, 1-2cm: 133px, 2-3cm: 134px, 3-4cm: 141px, 4-5cm: 146px, 5-6cm: 155px, 6-7cm: 167px
    assert results['px_per_cm'] == pytest.approx(144, abs=PX_PER_CM_ERROR_TOLERANCE)
    assert results['feret_cm'] == 6

def test_dark_pocillopora_scale_non_obscured_two_fingers_visible():
    coral_name = "unknown_darkpocillopora"
    image, coral_mask = prepare_measurement(coral_name, "20260811_1639_darkpocillopora.jpg")
    
    results = measurement_service.process_frame(image, coral_mask, coral_name.replace("unknown_", ""))

    debug_outputs(coral_name, results)

    # 0-1cm: 136px, 1-2cm: 133px, 2-3cm: 134px, 3-4cm: 141px, 4-5cm: 146px, 5-6cm: 155px, 6-7cm: 167px
    assert results['px_per_cm'] == pytest.approx(144, abs=PX_PER_CM_ERROR_TOLERANCE)
    assert results['feret_cm'] == 6


def test_green_porites_with_partial_ruler():
    coral_name = "unknown_greenporites"
    image,coral_mask = prepare_measurement(coral_name, "20260809_2053.jpg", 1)
    
    results = measurement_service.process_frame(image, coral_mask, coral_name.replace("unknown_", ""))

    debug_outputs(coral_name, results)
    
    # 0-1cm: 131px, 1-2cm: 131px, 2-3cm: 135px, 3-4cm: 138px, 4-5cm: 142px, 5-6cm: 153px, 6-7cm: 166px
    assert results['px_per_cm'] == pytest.approx(146.15, abs=PX_PER_CM_ERROR_TOLERANCE)
    assert results['feret_cm'] == 6.7
    #assert results['geodesic_cm'] == 42.27


def test_huge_pavona_ruler_under_rock():
    coral_name = "unknown_hugepavona"
    image,coral_mask = prepare_measurement(coral_name, "20260809_2101.jpg")
    
    results = measurement_service.process_frame(image, coral_mask, coral_name.replace("unknown_", ""))

    debug_outputs(coral_name, results)

    # 0-1cm: 50px, 1-2cm: 48px, 2-3cm: 49px, 3-4cm: 50px, 4-5cm: 48px, 5-6cm: 50px, 6-7cm: 50px
    assert results['px_per_cm'] == 50
    assert results['feret_cm'] == pytest.approx(23.97, abs=PX_PER_CM_ERROR_TOLERANCE)
    #assert results['geodesic_cm'] == 42.27


def prepare_measurement(coral_name, concrete_image_name: str | None = None, segment_index: int = 0):
    image, segmentation = segment(coral_name, concrete_image_name)
    coral_mask = points_to_mask(segmentation.segments[segment_index].polygon, image.shape)
    return image,coral_mask
    #assert results['geodesic_cm'] == 42.27


def segment(coral_name: str, image_name: str | None = None):
    base_dir = Path(__file__).parents[2]
    if image_name is None:
        path = sorted((base_dir / FIXTURES_DIR / coral_name).glob("*.jpg"))[0]
    else:
        path = base_dir / FIXTURES_DIR / coral_name / image_name
    
    image = cv2.imread(str(path))

    segmentation = fixture_segmenter.segment(image, path.name)
    return image,segmentation

def debug_outputs(coral_name, results):
    print_metrics(coral_name, results)
    cv2.imwrite(f"{datetime.now().strftime('%H%M%S')}_debug_output_{coral_name}.jpg", results["debug_image"])


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