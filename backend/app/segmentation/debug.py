import random

import cv2
import numpy as np


def create_segmentation_collage(
    original,
    masks,
    output_path,
):
    """
    Creates a 2x3 debug collage.

    Panels:

    Original
    All masks

    Largest mask
    Bounding boxes

    Binary mask
    Final crop (placeholder)
    """

    original = original.copy()

    h, w = original.shape[:2]

    # --------------------------------------------------
    # Panel 1 Original
    # --------------------------------------------------

    panel_original = original.copy()

    # --------------------------------------------------
    # Panel 2 All Masks
    # --------------------------------------------------

    panel_masks = original.copy()

    for i, mask in enumerate(masks):

        color = (
            random.randint(40, 255),
            random.randint(40, 255),
            random.randint(40, 255),
        )

        segmentation = mask["segmentation"]

        panel_masks[segmentation] = (
            panel_masks[segmentation] * 0.4
            + np.array(color) * 0.6
        ).astype(np.uint8)

    # --------------------------------------------------
    # Panel 3 Largest Mask
    # --------------------------------------------------

    panel_best = np.zeros_like(original)

    if len(masks):

        largest = max(masks, key=lambda x: x["area"])

        panel_best[largest["segmentation"]] = (255, 255, 255)

    # --------------------------------------------------
    # Panel 4 Bounding Boxes
    # --------------------------------------------------

    panel_boxes = original.copy()

    for i, mask in enumerate(masks):

        x, y, bw, bh = map(int, mask["bbox"])

        cv2.rectangle(
            panel_boxes,
            (x, y),
            (x + bw, y + bh),
            (0, 0, 255),
            2,
        )

        cv2.putText(
            panel_boxes,
            str(i),
            (x, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
        )

    # --------------------------------------------------
    # Panel 5 Binary Mask
    # --------------------------------------------------

    panel_binary = np.zeros_like(original)

    if len(masks):

        panel_binary[largest["segmentation"]] = (255, 255, 255)

    # --------------------------------------------------
    # Panel 6 Placeholder
    # --------------------------------------------------

    panel_crop = np.full_like(original, 35)

    cv2.putText(
        panel_crop,
        "Crop comes next :)",
        (40, h // 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2,
    )

    # --------------------------------------------------

    def resize(img):

        return cv2.resize(img, (500, 500))

    panels = [
        resize(panel_original),
        resize(panel_masks),
        resize(panel_best),
        resize(panel_boxes),
        resize(panel_binary),
        resize(panel_crop),
    ]

    row1 = np.hstack(panels[:2])
    row2 = np.hstack(panels[2:4])
    row3 = np.hstack(panels[4:6])

    collage = np.vstack((row1, row2, row3))

    cv2.imwrite(output_path, collage)