import os
import cv2
from datetime import datetime
from vision import apply_underwater_corrections
from vision import crop_primary_coral
from vision import create_debug_collage
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
    
