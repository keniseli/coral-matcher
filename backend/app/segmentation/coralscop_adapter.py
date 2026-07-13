from pathlib import Path

import cv2
import numpy as np
import torch

from third_party.coralscop.segment_anything import (
    sam_model_registry,
    SamAutomaticMaskGenerator,
)

class CoralScopAdapter:
    """
    Thin wrapper around CoralSCOP.

    Responsibilities:
        - load the model once
        - generate masks
    """

    def __init__(
        self,
        checkpoint_path=None,
        model_type="vit_b",
    ):

        if checkpoint_path is None:
            checkpoint_path = (
                Path(__file__).resolve().parents[2]
                / "third_party"
                / "coralscop"
                / "checkpoints"
                / "vit_b_coralscop.pth"
            )

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"[CoralSCOP] Using device: {self.device}")

        sam = sam_model_registry[model_type](
            checkpoint=str(checkpoint_path)
        )

        sam.to(device=self.device)

        self.mask_generator = SamAutomaticMaskGenerator(
            model=sam,
            points_per_side=16,
            pred_iou_thresh=0.90,
            stability_score_thresh=0.90,
            crop_n_layers=1,
            crop_n_points_downscale_factor=2,
            min_mask_region_area=100,
        )

    def segment(self, image: np.ndarray):

        if image is None:
            raise ValueError("Image is None.")

        if len(image.shape) != 3:
            raise ValueError("Expected BGR image.")

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        print(rgb.shape)
        print("[CoralSCOP] image shape:", rgb.shape)
        print("[CoralSCOP] image dtype:", rgb.dtype)
        print("[CoralSCOP] image min/max:", rgb.min(), rgb.max())
        masks = self.mask_generator.generate(rgb)

        return masks