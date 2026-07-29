from pathlib import Path
import argparse
import cv2
import numpy as np

from .metrics import compute_metrics
from .visualization import generate_all_figures
from .report import create_report

def load_image(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """
    Load an RGB image and create a foreground mask.

    Assumes the cropped image has a black background (0,0,0).
    Returns:
        image_rgb : H x W x 3 uint8
        mask      : H x W bool (True = coral pixels)
    """
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)

    if image is None:
        raise FileNotFoundError(path)

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Ignore pure black pixels introduced by masking
    mask = np.any(image != 0, axis=2)

    if mask.sum() == 0:
        raise ValueError(f"No foreground pixels found in {path}")

    return image, mask

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("output")

    args = parser.parse_args()

    image_before, mask_before = load_image(args.before)
    image_after, mask_after = load_image(args.after)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics_before = compute_metrics(image_before)
    metrics_after = compute_metrics(image_after)

    generate_all_figures(
        image_before,
        image_after,
        output_dir,
    )

    create_report(
        image_before,
        image_after,
        output_dir,
    )

    print()
    print("Analysis complete.")
    print(f"Report written to {output_dir / 'report.html'}")


if __name__ == "__main__":
    main()