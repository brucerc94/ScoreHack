from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Iterable

import cv2
import numpy as np

ProgressCallback = Callable[[float, str], None]


def _read(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"No se pudo leer {path.name}.")
    return image


def _resize_height(image: np.ndarray, height: int) -> np.ndarray:
    if image.shape[0] == height:
        return image
    width = max(1, int(round(image.shape[1] * height / image.shape[0])))
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)


def _estimate_translation(
    left: np.ndarray,
    right: np.ndarray,
) -> tuple[float, float] | None:
    """Estima dónde cae el frame derecho dentro del panorama izquierdo."""
    left_gray = cv2.cvtColor(left, cv2.COLOR_BGR2GRAY)
    right_gray = cv2.cvtColor(right, cv2.COLOR_BGR2GRAY)

    orb = cv2.ORB_create(nfeatures=1800)
    left_keypoints, left_descriptors = orb.detectAndCompute(left_gray, None)
    right_keypoints, right_descriptors = orb.detectAndCompute(right_gray, None)

    if left_descriptors is None or right_descriptors is None:
        return None
    if len(left_keypoints) < 8 or len(right_keypoints) < 8:
        return None

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    matches = matcher.knnMatch(
        right_descriptors,
        left_descriptors,
        k=2,
    )
    good = [
        first
        for first, second in matches
        if first.distance < 0.75 * second.distance
    ]
    if len(good) < 8:
        return None

    source = np.float32(
        [right_keypoints[m.queryIdx].pt for m in good]
    )
    target = np.float32(
        [left_keypoints[m.trainIdx].pt for m in good]
    )

    matrix, inliers = cv2.estimateAffinePartial2D(
        source,
        target,
        method=cv2.RANSAC,
        ransacReprojThreshold=3.0,
    )
    if matrix is None or inliers is None:
        return None
    if int(inliers.ravel().sum()) < 6:
        return None

    matrix = matrix.astype(np.float32)
    scale = math.hypot(float(matrix[0, 0]), float(matrix[0, 1]))
    rotation = math.degrees(math.atan2(float(matrix[1, 0]), float(matrix[0, 0])))

    if not 0.95 <= scale <= 1.05 or abs(rotation) > 5.0:
        return None

    return float(matrix[0, 2]), float(matrix[1, 2])


def _overlap_width(left_width: int, right_width: int, tx: float) -> float:
    return max(
        0.0,
        min(float(left_width), tx + right_width) - max(0.0, tx),
    )


def _merge(left: np.ndarray, right: np.ndarray, tx: float, ty: float) -> np.ndarray:
    left_height, left_width = left.shape[:2]
    right_height, right_width = right.shape[:2]

    min_x = min(0.0, tx)
    max_x = max(float(left_width), tx + right_width)
    min_y = min(0.0, ty)
    max_y = max(float(left_height), ty + right_height)

    offset_x = int(math.floor(-min_x))
    offset_y = int(math.floor(-min_y))
    width = int(math.ceil(max_x - min_x))
    height = int(math.ceil(max_y - min_y))

    panorama = np.zeros((height, width, 3), dtype=np.uint8)
    panorama_mask = np.zeros((height, width), dtype=np.uint8)

    left_x = offset_x
    left_y = offset_y
    panorama[left_y : left_y + left_height, left_x : left_x + left_width] = left
    panorama_mask[left_y : left_y + left_height, left_x : left_x + left_width] = 255

    matrix = np.float32(
        [
            [1.0, 0.0, tx + offset_x],
            [0.0, 1.0, ty + offset_y],
        ]
    )
    warped_right = cv2.warpAffine(
        right,
        matrix,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
    )
    right_mask = cv2.warpAffine(
        np.full((right_height, right_width), 255, dtype=np.uint8),
        matrix,
        (width, height),
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT,
    )

    only_right = (right_mask > 0) & (panorama_mask == 0)
    overlap = (right_mask > 0) & (panorama_mask > 0)
    panorama[only_right] = warped_right[only_right]

    if overlap.any():
        panorama[overlap] = (
            0.5 * panorama[overlap].astype(np.float32)
            + 0.5 * warped_right[overlap].astype(np.float32)
        ).astype(np.uint8)

    return panorama


def stitch_horizontal(
    image_paths: Iterable[Path],
    output_path: Path,
    on_progress: ProgressCallback | None = None,
) -> Path:
    """
    Une frames seleccionados que muestran zonas consecutivas de una partitura.

    Cada frame se registra contra el panorama acumulado mediante ORB + RANSAC.
    Esto conserva el desplazamiento lateral necesario para reconstruir un scroll.
    """
    paths = list(image_paths)
    if len(paths) < 2:
        raise ValueError("El montaje horizontal necesita al menos 2 frames.")

    images = [_read(path) for path in paths]
    target_height = images[0].shape[0]
    images = [_resize_height(image, target_height) for image in images]

    panorama = images[0]

    for index, image in enumerate(images[1:], start=1):
        transform = _estimate_translation(panorama, image)
        if transform is None:
            raise RuntimeError(
                f"No se pudo encontrar solape entre los frames {index} y {index + 1}."
            )

        tx, ty = transform
        overlap = _overlap_width(panorama.shape[1], image.shape[1], tx)
        if overlap < min(panorama.shape[1], image.shape[1]) * 0.05:
            raise RuntimeError(
                f"El solape entre los frames {index} y {index + 1} es insuficiente."
            )
        if abs(ty) > target_height * 0.20:
            raise RuntimeError(
                f"El desplazamiento vertical entre los frames {index} y {index + 1} es excesivo."
            )

        panorama = _merge(panorama, image, tx, ty)

        if on_progress:
            on_progress(
                index / (len(images) - 1),
                f"Uniendo frames horizontalmente… ({index}/{len(images) - 1})",
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(
        str(output_path),
        panorama,
        [cv2.IMWRITE_JPEG_QUALITY, 95],
    ):
        raise RuntimeError(f"No se pudo guardar {output_path.name}.")
    return output_path
