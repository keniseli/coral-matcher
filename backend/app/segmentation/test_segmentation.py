from pathlib import Path
import cv2
import time
from datetime import datetime
from .coralscop_adapter import CoralScopAdapter
from .debug import create_segmentation_collage
from PIL import Image
import numpy as np

adapter = CoralScopAdapter()

#image_name = "CR_IslaLarga_T08_c010_C.JPG"
#image_name = "CR_IslaLarga_T08_c014_B.JPG"
image_name = "CR_IslaLarga_T08_c001_A.JPG"
demo = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "segmentation"
    / "test_images"
    / image_name
)

#image = cv2.imread(str(demo))
image = Image.open(str(demo)).convert("RGB")
image.thumbnail((1024, 1024))
image = np.array(image)

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

    collage_name = datetime.now().strftime("%Y%m%d_%H%M") + "_" + image_name
    collage_path = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "processing"
    / "collages"
    / collage_name
)
create_segmentation_collage(
    image,
    masks,
    str(collage_path),
)