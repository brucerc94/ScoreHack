from __future__ import annotations

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


def _overlap_score(left: np.ndarray, right: np.ndarray, overlap: int) -> float:
    previous = cv2.cvtColor(left[:, -overlap:], cv2.COLOR_BGR2GRAY)
    current = cv2.cvtColor(right[:, :overlap], cv2.COLOR_BGR2GRAY)

    previous = cv2.GaussianBlur(previous, (5, 5), 0).astype(np.float32)
    current = cv2.GaussianBlur(current, (5, 5), 0).astype(np.float32)

    previous -= previous.mean()
    current -= current.mean()

    denominator = float(np.linalg.norm(previous) * np.linalg.norm(current))
    if denominator <= 1e-6:
        return float("inf")

    return float(np.linalg.norm(previous - current) / denominator)


def _find_overlap(left: np.ndarray, right: np.ndarray) -> int:
    max_overlap = min(left.shape[1], right.shape[1])
    minimum = max(32, int(max_overlap * 0.08))
    maximum = max(minimum, int(max_overlap * 0.75))

    candidates = range(minimum, maximum + 1, max(8, maximum // 24))
    return min(candidates, key=lambda value: _overlap_score(left, right, value))


def _blend_pair(left: np.ndarray, right: np.ndarray, overlap: int) -> np.ndarray:
    output_width = left.shape[1] + right.shape[1] - overlap
    output = np.empty(
        (left.shape[0], output_width, 3),
        dtype=np.uint8,
    )
    output[:, : left.shape[1] - overlap] = left[:, : left.shape[1] - overlap]

    fade = np.linspace(0.0, 1.0, overlap, dtype=np.float32)[None, :, None]
    left_strip = left[:, -overlap:].astype(np.float32)
    right_strip = right[:, :overlap].astype(np.float32)
    output[:, left.shape[1] - overlap : left.shape[1]] = (
        left_strip * (1.0 - fade) + right_strip * fade
    ).astype(np.uint8)
    output[:, left.shape[1] :] = right[:, overlap:]
    return output


def stitch_horizontal(
    image_paths: Iterable[Path],
    output_path: Path,
    on_progress: ProgressCallback | None = None,
) -> Path:
    """
    Une frames consecutivos horizontalmente detectando automáticamente su solape.

    Está pensado para videos donde la cámara recorre lateralmente una partitura:
    cada frame conserva una ventana distinta y parte del contenido se repite.
    """
    paths = list(image_paths)
    if len(paths) < 2:
        raise ValueError("El montaje horizontal necesita al menos 2 frames.")

    images = [_read(path) for path in paths]
    target_height = images[0].shape[0]
    images = [_resize_height(image, target_height) for image in images]

    result = images[0]
    for index, image in enumerate(images[1:], start=1):
        overlap = _find_overlap(result, image)
        result = _blend_pair(result, image, overlap)

        if on_progress:
            on_progress(
                index / (len(images) - 1),
                f"Uniendo frames horizontalmente… ({index}/{len(images) - 1})",
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(
        str(output_path),
        result,
        [cv2.IMWRITE_JPEG_QUALITY, 95],
    ):
        raise RuntimeError(f"No se pudo guardar {output_path.name}.")
    return output_path
