from __future__ import annotations

from pathlib import Path
from threading import Event
from typing import Callable, Iterable

import cv2
import numpy as np

from .models import AUTO_OVERLAP_MIN_CONFIDENCE, MontageResult

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


def _match_overlap(left: np.ndarray, right: np.ndarray) -> tuple[int, float]:
    """
    Busca el solape horizontal usando una banda central de la partitura.

    Se prueban dos anchos de plantilla. Si ambos encuentran prácticamente la
    misma frontera, aumenta la confianza de la detección y se evita depender
    únicamente de coincidencias puntuales de ORB.
    """
    height, left_width = left.shape[:2]
    right_width = right.shape[1]

    y0 = int(height * 0.15)
    y1 = int(height * 0.85)
    search_start = int(left_width * 0.15)
    search_end = int(left_width * 0.95)

    estimates: list[tuple[int, float]] = []

    for template_ratio in (0.12, 0.18):
        template_width = max(32, int(right_width * template_ratio))
        if template_width >= right_width:
            continue

        template = cv2.cvtColor(
            right[y0:y1, :template_width],
            cv2.COLOR_BGR2GRAY,
        )
        search = cv2.cvtColor(
            left[y0:y1, search_start:search_end],
            cv2.COLOR_BGR2GRAY,
        )

        if search.shape[1] <= template.shape[1]:
            continue

        template = cv2.GaussianBlur(template, (5, 5), 0)
        search = cv2.GaussianBlur(search, (5, 5), 0)
        response = cv2.matchTemplate(
            search,
            template,
            cv2.TM_CCOEFF_NORMED,
        )
        _, score, _, max_location = cv2.minMaxLoc(response)
        position = search_start + max_location[0]
        overlap = left_width - position

        if 0.08 * left_width <= overlap <= 0.90 * left_width:
            estimates.append((int(round(overlap)), float(score)))

    if not estimates:
        fallback = max(8, int(left_width * 0.20))
        return fallback, 0.0

    best_overlap, best_score = max(estimates, key=lambda item: item[1])

    if len(estimates) == 2:
        other_overlap = estimates[0][0] if estimates[1][0] == best_overlap else estimates[1][0]
        agreement = 1.0 - abs(best_overlap - other_overlap) / max(1, left_width)
        confidence = max(0.0, min(1.0, 0.7 * best_score + 0.3 * agreement))
    else:
        confidence = max(0.0, min(1.0, best_score))

    if best_score < 0.35 or confidence < 0.45:
        return max(8, int(left_width * 0.20)), 0.0

    return best_overlap, confidence


def _blend_pair(
    left: np.ndarray,
    right: np.ndarray,
    overlap: int,
) -> np.ndarray:
    overlap = max(0, min(overlap, min(left.shape[1], right.shape[1])))
    if overlap == 0:
        return np.hstack((left, right))

    left_end = left.shape[1] - overlap
    output_width = left.shape[1] + right.shape[1] - overlap
    result = np.empty(
        (left.shape[0], output_width, 3),
        dtype=np.uint8,
    )

    result[:, :left_end] = left[:, :left_end]

    # En el solape usamos una transición corta para evitar doble imagen visible.
    fade = np.linspace(0.0, 1.0, overlap, dtype=np.float32)[None, :, None]
    left_part = left[:, left_end:].astype(np.float32)
    right_part = right[:, :overlap].astype(np.float32)
    result[:, left_end:left.shape[1]] = (
        left_part * (1.0 - fade) + right_part * fade
    ).astype(np.uint8)

    result[:, left.shape[1]:] = right[:, overlap:]
    return result


def _normalize_images(images: list[np.ndarray]) -> list[np.ndarray]:
    if not images:
        raise ValueError("No hay imágenes para unir.")
    height = images[0].shape[0]
    return [_resize_height(image, height) for image in images]


def _validate_overrides(
    overrides: tuple[int | None, ...],
    frame_count: int,
    frame_width: int,
) -> None:
    if not overrides:
        return
    if len(overrides) != frame_count - 1:
        raise ValueError(
            f"Se esperaban {frame_count - 1} ajustes de unión y se recibieron {len(overrides)}."
        )
    minimum = max(8, int(frame_width * 0.05))
    maximum = max(minimum, int(frame_width * 0.90))
    if any(
        overlap is not None and (overlap < minimum or overlap > maximum)
        for overlap in overrides
    ):
        raise ValueError("Uno de los solapes manuales está fuera del rango permitido.")


def stitch_horizontal(
    image_paths: Iterable[Path],
    output_path: Path,
    overlap_overrides: tuple[int | None, ...] = (),
    on_progress: ProgressCallback | None = None,
    cancel_event: Event | None = None,
) -> MontageResult:
    """
    Reconstruye una partitura horizontalmente.

    Por defecto detecta el solape entre cada par consecutivo. Cuando el usuario
    entrega ajustes manuales, estos reemplazan únicamente la unión correspondiente.
    """
    paths = list(image_paths)
    if len(paths) < 2:
        raise ValueError("La unión horizontal necesita al menos 2 frames.")

    images = _normalize_images([_read(path) for path in paths])
    frame_width = images[0].shape[1]
    frame_height = images[0].shape[0]
    _validate_overrides(overlap_overrides, len(images), frame_width)

    auto_overlaps: list[int] = []
    confidences: list[float] = []

    for index in range(len(images) - 1):
        if cancel_event and cancel_event.is_set():
            raise InterruptedError("Proceso cancelado por el usuario.")

        overlap, confidence = _match_overlap(images[index], images[index + 1])
        auto_overlaps.append(overlap)
        confidences.append(confidence)

        if on_progress:
            on_progress(
                (index + 1) / (len(images) - 1),
                f"Detectando unión {index + 1}/{len(images) - 1}…",
            )

    effective_overlaps = tuple(
        overlap_overrides[index]
        if overlap_overrides and overlap_overrides[index] is not None
        else (
            auto_overlaps[index]
            if confidences[index] >= AUTO_OVERLAP_MIN_CONFIDENCE
            else 0
        )
        for index in range(len(auto_overlaps))
    )

    panorama = images[0]
    for index, image in enumerate(images[1:]):
        if cancel_event and cancel_event.is_set():
            raise InterruptedError("Proceso cancelado por el usuario.")
        panorama = _blend_pair(
            panorama,
            image,
            effective_overlaps[index],
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(
        str(output_path),
        panorama,
        [cv2.IMWRITE_JPEG_QUALITY, 95],
    ):
        raise RuntimeError(f"No se pudo guardar {output_path.name}.")

    if on_progress:
        on_progress(1.0, "Reconstrucción horizontal lista.")

    return MontageResult(
        output_path=output_path,
        auto_overlaps=tuple(auto_overlaps),
        effective_overlaps=effective_overlaps,
        confidences=tuple(confidences),
        frame_width=frame_width,
        frame_height=frame_height,
    )
