from __future__ import annotations

from pathlib import Path
from threading import Event
from typing import Callable, Iterable

import cv2

ProgressCallback = Callable[[float, str], None]


def validate_crop(height: int, top: int, bottom: int) -> None:
    if top < 0 or bottom < 0:
        raise ValueError("Crop values cannot be negative.")
    if top + bottom >= height:
        raise ValueError("Top + bottom crop must leave a visible image.")


def crop_frames(
    frame_paths: Iterable[Path],
    output_dir: Path,
    top: int,
    bottom: int,
    start_index: int = 0,
    end_index: int | None = None,
    on_progress: ProgressCallback | None = None,
    cancel_event: Event | None = None,
) -> tuple[Path, ...]:
    paths = list(frame_paths)
    if not paths:
        raise ValueError("There are no frames to crop.")

    end = len(paths) - 1 if end_index is None else min(end_index, len(paths) - 1)
    start = max(0, start_index)
    if start > end:
        raise ValueError("The frame range is invalid.")

    selected = paths[start : end + 1]
    output_dir.mkdir(parents=True, exist_ok=True)
    output: list[Path] = []

    for index, source in enumerate(selected):
        if cancel_event and cancel_event.is_set():
            raise InterruptedError("Process canceled by user.")

        image = cv2.imread(str(source))
        if image is None:
            raise RuntimeError(f"Could not read {source.name}.")
        height = image.shape[0]
        validate_crop(height, top, bottom)
        cropped = image[top : height - bottom, :]
        target = output_dir / source.name
        if not cv2.imwrite(str(target), cropped, [cv2.IMWRITE_JPEG_QUALITY, 95]):
            raise RuntimeError(f"Could not save {target.name}.")
        output.append(target)
        if on_progress:
            on_progress((index + 1) / len(selected), "Cropping score frames…")

    return tuple(output)
