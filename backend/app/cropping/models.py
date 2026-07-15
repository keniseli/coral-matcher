from dataclasses import dataclass

import numpy as np

@dataclass
class BoundingBox:
    x: int
    y: int
    width: int
    height: int

    @property
    def x2(self) -> int:
        return self.x + self.width

    @property
    def y2(self) -> int:
        return self.y + self.height

    @property
    def center(self) -> tuple[float, float]:
        return (
            self.x + self.width / 2,
            self.y + self.height / 2,
        )


@dataclass
class CropResult:
    crop: np.ndarray

    content_box: BoundingBox
    square_box: BoundingBox

    padding: int