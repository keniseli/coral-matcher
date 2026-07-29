from dataclasses import dataclass

import cv2
import numpy as np


def coral_mask(image: np.ndarray) -> np.ndarray:
    """
    Returns True for every non-black coral pixel.
    """
    return np.any(image != 0, axis=2)


def lab_image(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image, cv2.COLOR_RGB2LAB)


def valid_pixels(channel: np.ndarray, mask: np.ndarray) -> np.ndarray:
    return channel[mask]


def brightness_metrics(image: np.ndarray) -> dict:

    mask = coral_mask(image)

    L = lab_image(image)[:, :, 0].astype(np.float32)

    pixels = valid_pixels(L, mask)

    metrics = {
        "mean_L": float(np.mean(pixels)),
        "median_L": float(np.median(pixels)),
        "std_L": float(np.std(pixels)),
    }

    for p in [5, 10, 15, 25, 75, 85, 90, 95]:
        metrics[f"p{p}_L"] = float(np.percentile(pixels, p))

    metrics["dynamic_range_L"] = (
        metrics["p95_L"] - metrics["p5_L"]
    )

    return metrics


def brightness_histogram(
    image: np.ndarray,
    bins: int = 20,
):

    mask = coral_mask(image)

    L = lab_image(image)[:, :, 0].astype(np.float32)

    pixels = valid_pixels(L, mask)

    hist, edges = np.histogram(
        pixels,
        bins=bins,
        range=(0, 255),
        density=True,
    )

    return hist, edges


def color_metrics(image: np.ndarray):

    mask = coral_mask(image)

    lab = lab_image(image).astype(np.float32)

    L = lab[:, :, 0][mask]
    A = lab[:, :, 1][mask]
    B = lab[:, :, 2][mask]

    return {

        "mean_a": float(np.mean(A)),
        "mean_b": float(np.mean(B)),

        "std_a": float(np.std(A)),
        "std_b": float(np.std(B)),

        "mean_L": float(np.mean(L)),
        "std_L": float(np.std(L)),
    }


def sobel_image(image: np.ndarray):

    mask = coral_mask(image)

    L = lab_image(image)[:, :, 0].astype(np.float32)

    gx = cv2.Sobel(
        L,
        cv2.CV_32F,
        1,
        0,
        ksize=3,
    )

    gy = cv2.Sobel(
        L,
        cv2.CV_32F,
        0,
        1,
        ksize=3,
    )

    magnitude = cv2.magnitude(gx, gy)

    magnitude *= mask.astype(np.float32)

    return magnitude


def sobel_metrics(image):

    sobel = sobel_image(image)

    pixels = sobel[sobel > 0]

    return {

        "sobel_mean": float(np.mean(pixels)),
        "sobel_std": float(np.std(pixels)),
        "sobel_median": float(np.median(pixels)),
        "sobel_p95": float(np.percentile(pixels, 95)),
    }


def laplacian_image(image):

    mask = coral_mask(image)

    L = lab_image(image)[:, :, 0].astype(np.float32)

    lap = cv2.Laplacian(
        L,
        cv2.CV_32F,
        ksize=3,
    )

    lap *= mask.astype(np.float32)

    return lap


def laplacian_metrics(image):

    lap = laplacian_image(image)

    pixels = lap[lap != 0]

    return {

        "laplacian_variance": float(np.var(pixels))
    }


def shape_metrics(image):

    mask = coral_mask(image)

    return {

        "area_pixels": int(np.count_nonzero(mask))
    }



def compute_metrics(image):

    metrics = {}

    metrics.update(
        brightness_metrics(image)
    )

    metrics.update(
        color_metrics(image)
    )

    metrics.update(
        sobel_metrics(image)
    )

    metrics.update(
        laplacian_metrics(image)
    )

    metrics.update(
        shape_metrics(image)
    )

    return metrics