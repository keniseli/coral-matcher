from pathlib import Path
import cv2
import time
from datetime import datetime
from .coralscop_adapter import CoralScopAdapter
from .debug import create_segmentation_collage
from app.vision.vision import apply_underwater_corrections
from PIL import Image
import numpy as np

adapter = CoralScopAdapter()

def segment_image_with_collage(image: np.ndarray, collage_name: str):
    start = time.perf_counter()
    masks = adapter.segment(image)
    elapsed = time.perf_counter() - start

    print(f"Detected {len(masks)} masks")
    print(f"Segmentation took {elapsed:.2f} seconds")
    
    for i, mask in enumerate(masks):
        print(
            f"{i:2d} | "
            f"area={mask['area']:8.0f} | "
            f"iou={mask['predicted_iou']:.3f} | "
            f"stability={mask['stability_score']:.3f}"
        )

    collage_path = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "processing"
        / "collages"
        / collage_name
    )
    
    create_segmentation_collage(image, masks, str(collage_path))


demo = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "segmentation"
    / "test_images"
)

image_paths = []
if demo.is_dir():
    image_paths = sorted(
        p for p in demo.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    )
else:
    image_paths = [demo]

for demo_image in image_paths:
    print(f"Processing {demo_image.name}")
    image = Image.open(str(demo_image)).convert("RGB")
    image = np.array(image)
    collage_name = datetime.now().strftime("%Y%m%d_%H%M") + "_" + demo_image.name

    segment_image_with_collage(image, collage_name)
