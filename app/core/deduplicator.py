from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

import cv2
from skimage.metrics import structural_similarity

ProgressCallback = Callable[[float, str], None]


def _signature(path: Path) -> object:
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise RuntimeError(f"No se pudo leer {path.name}.")
    return cv2.resize(image, (320, 180), interpolation=cv2.INTER_AREA)


def remove_consecutive_duplicates(
    image_paths: Iterable[Path],
    threshold: float = 0.97,
    on_progress: ProgressCallback | None = None,
) -> tuple[Path, ...]:
    if not 0.0 < threshold <= 1.0:
        raise ValueError("El umbral de duplicados debe estar entre 0 y 1.")

    paths = list(image_paths)
    if not paths:
        return ()

    unique: list[Path] = [paths[0]]
    previous = _signature(paths[0])

    for index, path in enumerate(paths[1:], start=1):
        current = _signature(path)
        similarity = float(structural_similarity(previous, current, data_range=255))
        if similarity < threshold:
            unique.append(path)
            previous = current
        if on_progress:
            on_progress((index + 1) / len(paths), "Eliminando fotogramas repetidos…")

    return tuple(unique)
