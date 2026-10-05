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


def _join_side_by_side(images: list[np.ndarray], gap: int = 8) -> np.ndarray:
    if not images:
        raise ValueError("No hay imágenes para unir.")

    height = images[0].shape[0]
    normalized = [_resize_height(image, height) for image in images]
    total_width = sum(image.shape[1] for image in normalized)
    total_width += gap * (len(normalized) - 1)

    canvas = np.full(
        (height, total_width, 3),
        255,
        dtype=np.uint8,
    )

    x = 0
    for image in normalized:
        width = image.shape[1]
        canvas[:, x : x + width] = image
        x += width + gap

    return canvas


def stitch_horizontal(
    image_paths: Iterable[Path],
    output_path: Path,
    on_progress: ProgressCallback | None = None,
) -> Path:
    """
    Coloca los frames seleccionados uno al lado del otro, sin alineamiento automático.

    La unión es deliberadamente determinista: cada frame ocupa exactamente una
    posición. Esto permite al usuario controlar visualmente qué zonas de la
    partitura forman la secuencia, en lugar de dejar que ORB decida qué regiones
    deben superponerse.
    """
    paths = list(image_paths)
    if len(paths) < 2:
        raise ValueError("La unión horizontal necesita al menos 2 frames.")

    images = [_read(path) for path in paths]
    total = len(images)

    for index in range(total):
        if on_progress:
            on_progress(
                index / total,
                f"Colocando frame {index + 1}/{total}…",
            )

    result = _join_side_by_side(images)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(
        str(output_path),
        result,
        [cv2.IMWRITE_JPEG_QUALITY, 95],
    ):
        raise RuntimeError(f"No se pudo guardar {output_path.name}.")

    if on_progress:
        on_progress(1.0, "Unión horizontal lista.")

    return output_path
