from __future__ import annotations

from pathlib import Path
from threading import Event
from typing import Callable, Iterable

import cv2
import numpy as np

ProgressCallback = Callable[[float, str], None]


def _overlay_mask(image: np.ndarray) -> np.ndarray:
    """Detecta resaltadores/cursos coloreados y altos sobre la partitura."""
    height, width = image.shape[:2]
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    colored = cv2.inRange(
        hsv,
        np.array([75, 28, 70], dtype=np.uint8),
        np.array([115, 255, 255], dtype=np.uint8),
    )
    colored = cv2.morphologyEx(
        colored,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (5, 9)),
    )
    colored = cv2.morphologyEx(
        colored,
        cv2.MORPH_OPEN,
        np.ones((3, 3), np.uint8),
    )

    components, _, stats, _ = cv2.connectedComponentsWithStats(
        colored,
        connectivity=8,
    )

    mask = np.zeros((height, width), dtype=bool)
    for component in range(1, components):
        x, y, w, h, area = stats[component]
        if h < height * 0.28:
            continue
        if w < 3 or w > width * 0.30:
            continue
        if area < max(80, int(w * h * 0.08)):
            continue
        mask[y : y + h, x : x + w] = True

    return cv2.dilate(
        mask.astype(np.uint8),
        cv2.getStructuringElement(cv2.MORPH_RECT, (5, 7)),
        iterations=1,
    ).astype(bool)


def _read(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"No se pudo leer {path.name}.")
    return image


def _restore_from_neighbors(
    current: np.ndarray,
    mask: np.ndarray,
    neighbors: Iterable[np.ndarray],
) -> np.ndarray:
    """
    Rellena el overlay con el primer vecino temporal que no tenga overlay.

    Se evita construir arrays gigantes con np.stack/np.nan, algo que puede
    disparar el consumo de RAM en videos de alta resolución.
    """
    if not mask.any():
        return current

    result = current.copy()
    remaining = mask.copy()

    for neighbor in neighbors:
        if not remaining.any():
            break

        neighbor_mask = _overlay_mask(neighbor)
        usable = remaining & ~neighbor_mask
        if usable.any():
            result[usable] = neighbor[usable]
            remaining[usable] = False

    return result


def remove_transient_overlays(
    image_paths: Iterable[Path],
    output_dir: Path,
    radius: int = 2,
    on_progress: ProgressCallback | None = None,
    cancel_event: Event | None = None,
) -> tuple[Path, ...]:
    """
    Elimina resaltadores/cursos coloreados que cambian de posición entre frames.

    La recuperación se hace desde frames temporales vecinos. Si no existe un
    vecino limpio para una región, se conserva el contenido original.
    """
    paths = list(image_paths)
    if not paths:
        return ()
    if radius < 1:
        raise ValueError("radius debe ser mayor que 0.")

    output_dir.mkdir(parents=True, exist_ok=True)
    result: list[Path] = []

    for index, source in enumerate(paths):
        if cancel_event and cancel_event.is_set():
            raise InterruptedError("Proceso cancelado por el usuario.")

        current = _read(source)
        mask = _overlay_mask(current)

        if mask.any():
            neighbor_indices = [
                j
                for j in range(
                    max(0, index - radius),
                    min(len(paths), index + radius + 1),
                )
                if j != index
            ]
            neighbors = (_read(paths[j]) for j in neighbor_indices)
            current = _restore_from_neighbors(current, mask, neighbors)

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
