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
    Estima el solape usando coincidencia de plantillas grandes y consenso.

    Solo se consideran solapes razonables para una partitura que se desplaza
    lateralmente. Una detección de baja confianza se devuelve como sugerencia,
    pero no se aplica automáticamente.
    """
    height, left_width = left.shape[:2]
    right_width = right.shape[1]

    y0 = int(height * 0.12)
    y1 = int(height * 0.88)
    search_start = int(left_width * 0.25)
    search_end = int(left_width * 0.95)
    min_overlap = int(left_width * 0.08)
    max_overlap = int(left_width * 0.70)

    left_gray = cv2.cvtColor(left[y0:y1], cv2.COLOR_BGR2GRAY)
    right_gray = cv2.cvtColor(right[y0:y1], cv2.COLOR_BGR2GRAY)

    left_edges = cv2.Canny(left_gray, 40, 120)
    right_edges = cv2.Canny(right_gray, 40, 120)
    estimates: list[tuple[int, float]] = []

    for template_ratio in (0.20, 0.30, 0.40):
        template_width = max(48, int(right_width * template_ratio))
        if template_width >= right_width:
            continue

        template = right_edges[:, :template_width]
        search = left_edges[:, search_start:search_end]
        if search.shape[1] <= template.shape[1]:
            continue

        response = cv2.matchTemplate(
            search,
            template,
            cv2.TM_CCOEFF_NORMED,
        )
        _, score, _, max_location = cv2.minMaxLoc(response)
        position = search_start + max_location[0]
        overlap = left_width - position

        if min_overlap <= overlap <= max_overlap:
            estimates.append((int(round(overlap)), float(score)))

    if not estimates:
        return max(min_overlap, int(left_width * 0.20)), 0.0

    overlaps = np.array([item[0] for item in estimates], dtype=np.float32)
    scores = np.array([item[1] for item in estimates], dtype=np.float32)
    best_index = int(np.argmax(scores))
    best_overlap = int(estimates[best_index][0])
    best_score = float(scores[best_index])

    spread = float(overlaps.max() - overlaps.min())
    agreement = max(0.0, 1.0 - spread / max(1.0, left_width * 0.12))
    confidence = max(
        0.0,
        min(1.0, 0.75 * max(0.0, best_score) + 0.25 * agreement),
    )

    if len(estimates) < 2 or best_score < 0.45:
        confidence *= 0.75

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
    maximum = max(minimum, int(frame_width * 0.70))
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
