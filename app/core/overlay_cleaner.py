from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

import cv2
import numpy as np

ProgressCallback = Callable[[float, str], None]


def _overlay_mask(image: np.ndarray) -> np.ndarray:
    """
    Detecta resaltadores/cursors verticales coloreados superpuestos sobre la partitura.

    El contenido normal de una partitura es mayormente blanco/negro. Un resaltado
    interactivo suele introducir saturación de color y una geometría alta/estrecha.
    """
    height, width = image.shape[:2]
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    saturated = cv2.inRange(
        hsv,
        np.array([75, 28, 70], dtype=np.uint8),
        np.array([115, 255, 255], dtype=np.uint8),
    )

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 9))
    saturated = cv2.morphologyEx(saturated, cv2.MORPH_CLOSE, kernel)
    saturated = cv2.morphologyEx(saturated, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    components, _, stats, _ = cv2.connectedComponentsWithStats(
        saturated,
        connectivity=8,
    )

    mask = np.zeros((height, width), dtype=np.uint8)
    for component in range(1, components):
        x, y, w, h, area = stats[component]
        if h < height * 0.28:
            continue
        if w < 3 or w > width * 0.30:
            continue
        if area < max(80, int(w * h * 0.08)):
            continue
        mask[y : y + h, x : x + w] = 255

    # Amplía ligeramente la máscara para incluir bordes del resaltador.
    mask = cv2.dilate(
        mask,
        cv2.getStructuringElement(cv2.MORPH_RECT, (5, 7)),
        iterations=1,
    )
    return mask.astype(bool)


def _read(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"No se pudo leer {path.name}.")
    return image


def _remove_from_neighbors(
    current: np.ndarray,
    mask: np.ndarray,
    neighbors: list[np.ndarray],
) -> np.ndarray:
    if not neighbors or not mask.any():
        return current

    valid_values: list[np.ndarray] = []
    for neighbor in neighbors:
        neighbor_mask = _overlay_mask(neighbor)
        usable = mask & ~neighbor_mask
        if usable.any():
            values = np.zeros_like(current)
            values[usable] = neighbor[usable]
            valid_values.append(values)

    if not valid_values:
        return current

    stack = np.stack(valid_values, axis=0)
    valid = np.stack(
        [
            mask & ~_overlay_mask(neighbor)
            for neighbor in neighbors
        ],
        axis=0,
    )

    count = valid.sum(axis=0)
    median = np.median(
        np.where(valid[..., None], stack, np.nan),
        axis=0,
    )
    result = current.copy()
    fill = mask & (count > 0)
    result[fill] = np.nan_to_num(median[fill], nan=0.0).astype(np.uint8)
    return result


def remove_transient_overlays(
    image_paths: Iterable[Path],
    output_dir: Path,
    radius: int = 2,
    on_progress: ProgressCallback | None = None,
) -> tuple[Path, ...]:
    """
    Elimina resaltadores/cursors coloreados que cambian de posición entre frames.

    Solo modifica regiones detectadas como overlays verticales coloreados. El
    contenido musical se recupera desde vecinos temporales donde esa región está
    limpia, evitando borrar notas o líneas negras de la partitura.
    """
    paths = list(image_paths)
    if not paths:
        return ()
    if radius < 1:
        raise ValueError("radius debe ser mayor que 0.")

    output_dir.mkdir(parents=True, exist_ok=True)
    result: list[Path] = []

    for index, source in enumerate(paths):
        current = _read(source)
        mask = _overlay_mask(current)

        if mask.any():
            neighbor_paths = [
                paths[j]
                for j in range(
                    max(0, index - radius),
                    min(len(paths), index + radius + 1),
                )
                if j != index
            ]
            neighbors = [_read(path) for path in neighbor_paths]
            current = _remove_from_neighbors(current, mask, neighbors)

        target = output_dir / source.name
        if not cv2.imwrite(
            str(target),
            current,
            [cv2.IMWRITE_JPEG_QUALITY, 95],
        ):
            raise RuntimeError(f"No se pudo guardar {target.name}.")
        result.append(target)

        if on_progress:
            on_progress(
                (index + 1) / len(paths),
                "Eliminando resaltadores móviles…",
            )

    return tuple(result)
