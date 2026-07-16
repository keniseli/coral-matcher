import os
import cv2
from datetime import datetime
from app.vision.vision import apply_underwater_corrections
from app.vision.vision import crop_primary_coral
from app.vision.vision import create_debug_collage
import torch

def test_find_gpu():
    print(torch.cuda.is_available())

def test_generate_debug_collages():
    """
    Processes every image inside INPUT_DIR and writes one comparison image
    per input into OUTPUT_DIR.
    """

    INPUT_DIR = "/mnt/c/Users/kenis/Downloads/Corals Daniek/07-07-2026"
    OUTPUT_DIR = os.path.join(
    "processing/collages", datetime.now().strftime("%Y%m%d_%H%M")
)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    supported_extensions = (
        ".jpg",
        ".jpeg",
        ".png",
        ".tif",
        ".tiff"
    )

    for filename in os.listdir(INPUT_DIR):

        if not filename.lower().endswith(supported_extensions):
            continue

        print(f"Processing {filename}")

        image_path = os.path.join(INPUT_DIR, filename)

        original = cv2.imread(image_path)

        if original is None:
            print(f"Could not load {filename}")
            continue

        corrected = apply_underwater_corrections(original)

        crop_result = crop_primary_coral(corrected)

        collage = create_debug_collage(
            original,
            corrected,
            crop_result["edges"],
            crop_result["contours"],
            crop_result["crop"]
        )

        output_name = os.path.splitext(filename)[0] + "_debug.jpg"

        output_path = os.path.join(
            OUTPUT_DIR,
            output_name
        )

        cv2.imwrite(output_path, collage)

    print("Done.")
    

def test_image_processing_math_extensions():
    """
    Generates a generic dummy 100x100 dark blue pixel array matrix 
    to verify our color spectrum balancing formula functions without crashing.
    """
    # Create an artificial raw deep blue image matrix
    dummy_blue_img = np.zeros((100, 100, 3), dtype=np.uint8)
    dummy_blue_img[:, :, 0] = 180  # Intense Blue Channel
    dummy_blue_img[:, :, 1] = 80   # Moderate Green Channel
    dummy_blue_img[:, :, 2] = 20   # Stripped down weak Red Channel

    # Execute processing execution
    output_matrix = apply_underwater_corrections(dummy_blue_img)

    assert output_matrix is not None
    assert output_matrix.shape == (100, 100, 3)
    
    # Assert that the suppressed red channel (index 2) was lifted by the algorithm
    assert int(output_matrix[50, 50, 2]) > 20

def test_empty_matrix_guards():
    """
    Verifies the engine throws a proper exception validation error when fed null bytes.
    """
    empty_matrix = np.array([], dtype=np.uint8)
    with pytest.raises(ValueError, match="Empty image matrix passed"):
        apply_underwater_corrections(empty_matrix)