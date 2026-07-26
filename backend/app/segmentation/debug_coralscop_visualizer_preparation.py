import json
from pathlib import Path

import cv2
import numpy as np
from pycocotools import mask as mask_util

# This file transforms a json from the dev_fixtures into a COCO RLE encoded binary masks


def polygon_to_rle(
    polygon: list[list[int]],
    width: int,
    height: int,
) -> dict:
    """
    Convert a polygon represented as [[x, y], ...]
    into COCO RLE.
    """

    mask = np.zeros(
        (height, width),
        dtype=np.uint8,
    )

    points = np.array(
        polygon,
        dtype=np.int32,
    )

    cv2.fillPoly(
        mask,
        [points],
        1,
    )

    # COCO expects Fortran-contiguous arrays
    rle = mask_util.encode(
        np.asfortranarray(mask)
    )

    # pycocotools returns counts as bytes.
    # JSON needs a string.
    rle["counts"] = rle["counts"].decode("utf-8")

    return rle


def convert_fixture(
    input_path: str | Path,
    output_path: str | Path,
):
    input_path = Path(input_path)
    output_path = Path(output_path)

    with input_path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        source = json.load(handle)

    image = source["image"]

    width = int(image["width"])
    height = int(image["height"])

    annotations = []

    for segment in source["segments"]:
        polygon = segment["polygon"]

        rle = polygon_to_rle(
            polygon=polygon,
            width=width,
            height=height,
        )

        annotations.append(
            {
                "segmentation": rle,
            }
        )

    output = {
        "image": {
            "file_name": image["file_name"],
            "width": width,
            "height": height,
        },
        "annotations": annotations,
    }

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            output,
            handle,
            indent=2,
        )


if __name__ == "__main__":
    convert_fixture(
        input_path="../../dev_fixtures/islalarga_c001/20260718_2042.json",
        output_path="coco_20260718_2042.json",
    )