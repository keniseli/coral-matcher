import cv2
from pathlib import Path
from app.analysis.measurement.ruler_detection import RulerDetection
from app.analysis.measurement.models import RulerGeometry

FIXTURES_DIR = Path("dev_fixtures")

ruler_detection = RulerDetection()

def test_measure_algalpavona():
    coral_name = "unknown_algalpavona"
    image = load_image(coral_name)
    
    results = ruler_detection.detect_ruler(image, coral_name.replace("unknown_", ""))

    debug_outputs(results)


def test_measure_bigpocillopora():
    coral_name = "unknown_bigpocillopora"
    image = load_image(coral_name)
    
    results = ruler_detection.detect_ruler(image, coral_name.replace("unknown_", ""))
    
    debug_outputs(results)


def test_measure_bright_pavona_ruler_hardly_visible_and_readable():
    coral_name = "unknown_brightpavona"
    image = load_image(coral_name, "20260809_2100.jpg")

    results = ruler_detection.detect_ruler(image, coral_name.replace("unknown_", ""))

    debug_outputs(results)


def test_measure_bright_pavona_ruler_visible_and_readable():
    coral_name = "unknown_brightpavona"
    image = load_image(coral_name, "20260811_1638.jpg")
    
    results = ruler_detection.detect_ruler(image, coral_name.replace("unknown_", ""))
    
    debug_outputs(results)


def test_measure_branchy_pavona_ruler_bright_hand_visible():
    coral_name = "unknown_branchypavona"
    image = load_image(coral_name)
    
    results = ruler_detection.detect_ruler(image, coral_name.replace("unknown_", ""))
    
    debug_outputs(results)


def test_dark_pocillopora_scale_obscured():
    coral_name = "unknown_darkpocillopora"
    image = load_image(coral_name, "20260809_1943.jpg")
    
    results = ruler_detection.detect_ruler(image, coral_name.replace("unknown_", ""))

    debug_outputs(results)


def test_dark_pocillopora_scale_non_obscured():
    coral_name = "unknown_darkpocillopora"
    image = load_image(coral_name, "20260811_1638_darkpocillopora.jpg")
    
    results = ruler_detection.detect_ruler(image, coral_name.replace("unknown_", ""))

    debug_outputs(results)


def test_dark_pocillopora_scale_non_obscured_two_fingers_visible():
    coral_name = "unknown_darkpocillopora"
    image = load_image(coral_name, "20260811_1639_darkpocillopora.jpg")
    
    results = ruler_detection.detect_ruler(image, coral_name.replace("unknown_", ""))

    debug_outputs(results)


def test_green_porites_with_partial_ruler():
    coral_name = "unknown_greenporites"
    image = load_image(coral_name, "20260809_2053.jpg")
    
    results = ruler_detection.detect_ruler(image, coral_name.replace("unknown_", ""))

    debug_outputs(results)


def test_huge_pavona_ruler_under_rock():
    coral_name = "unknown_hugepavona"
    image = load_image(coral_name, "20260809_2101.jpg")
    
    results = ruler_detection.detect_ruler(image, coral_name.replace("unknown_", ""))

    debug_outputs(results)


def test_leasoned_porites():
    coral_name = "unknown_lesionedporites"
    image = load_image(coral_name)
    
    results = ruler_detection.detect_ruler(image, coral_name.replace("unknown_", ""))

    debug_outputs(results)


def test_tiger_pavona():
    coral_name = "unknown_tigerpavona"
    image = load_image(coral_name, "20260811_1646.jpg")
    
    results = ruler_detection.detect_ruler(image, coral_name.replace("unknown_", ""))

    debug_outputs(results)


def test_octo_pavona():
    coral_name = "unknown_octopavona"
    image = load_image(coral_name)
    
    results = ruler_detection.detect_ruler(image, coral_name.replace("unknown_", ""))

    debug_outputs(results)


def test_snuggly_porites():
    coral_name = "unknown_snugglyporites"
    image = load_image(coral_name)
    
    results = ruler_detection.detect_ruler(image, coral_name.replace("unknown_", ""))

    debug_outputs(results)


def test_darth_porites():
    coral_name = "unknown_darthporites"
    image = load_image(coral_name)
    
    results = ruler_detection.detect_ruler(image, coral_name.replace("unknown_", ""))

    debug_outputs(results)


def test_spongy_pocillopora():
    coral_name = "unknown_spongypocillopora"
    image = load_image(coral_name)
    
    results = ruler_detection.detect_ruler(image, coral_name.replace("unknown_", ""))

    debug_outputs(results)


def load_image(coral_name: str, image_name: str | None = None):
    base_dir = Path(__file__).parents[3]
    if image_name is None:
        path = sorted((base_dir / FIXTURES_DIR / coral_name).glob("*.jpg"))[0]
    else:
        path = base_dir / FIXTURES_DIR / coral_name / image_name
    image = cv2.imread(str(path))
    return image

def debug_outputs(results: RulerGeometry):
    print(f"Angle  : {results.angle_degrees}")
    print(f"Center : {results.center}")
    print(f"Height : {results.height}")
    print(f"Width  : {results.width}")