from __future__ import annotations

from pathlib import Path
from threading import Event
from typing import Callable

import cv2

ProgressCallback = Callable[[float, str], None]


def validate_cut_points(cut_points: tuple[float, ...]) -> None:
    previous = 0.0
    for point in cut_points:
        if not 0.0 < point < 1.0:
            raise ValueError("Cuts must be between 0% and 100%.")
        if point <= previous:
            raise ValueError("Cuts must be ordered and unique.")
        previous = point


def split_panorama(
    image_path: Path,
    cut_points: tuple[float, ...],
    output_dir: Path,
    on_progress: ProgressCallback | None = None,
    cancel_event: Event | None = None,
) -> tuple[Path, ...]:
    """
    Divide un panorama horizontal en segmentos usando únicamente cortes elegidos
    por el usuario. No intenta interpretar la música ni mover los cortes.
    """
    validate_cut_points(cut_points)

    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"Could not read {image_path.name}.")

    height, width = image.shape[:2]
    positions = [0, *[int(round(width * point)) for point in cut_points], width]

    output_dir.mkdir(parents=True, exist_ok=True)
    segments: list[Path] = []
    total = len(positions) - 1

    for index, (start, end) in enumerate(zip(positions, positions[1:])):
        if cancel_event and cancel_event.is_set():
            raise InterruptedError("Proceso cancelado por el usuario.")

        start = max(0, min(start, width - 1))
        end = max(start + 1, min(end, width))
        segment = image[:, start:end]

        target = output_dir / f"segment_{index + 1:03d}.jpg"
        if not cv2.imwrite(
            str(target),
            segment,
            [cv2.IMWRITE_JPEG_QUALITY, 95],
        ):
            raise RuntimeError(f"Could not save {target.name}.")

        segments.append(target)

        if on_progress:
            on_progress(
                (index + 1) / total,
                f"Splitting score ({index + 1}/{total})…",
            )

    return tuple(segments)
