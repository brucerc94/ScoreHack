from __future__ import annotations

from pathlib import Path
from typing import Callable

import cv2

from .models import VideoInfo

ProgressCallback = Callable[[float, str], None]


def inspect_video(video_path: Path) -> VideoInfo:
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"No se pudo abrir el video: {video_path}")

    fps = float(capture.get(cv2.CAP_PROP_FPS))
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    capture.release()

    if fps <= 0 or total_frames <= 0:
        raise RuntimeError("El video no reporta FPS o frames válidos.")

    return VideoInfo(fps, total_frames, width, height, total_frames / fps)


def extract_frames(
    video_path: Path,
    output_dir: Path,
    interval_seconds: float,
    on_progress: ProgressCallback | None = None,
) -> tuple[Path, ...]:
    if interval_seconds <= 0:
        raise ValueError("El intervalo debe ser mayor que 0 segundos.")

    info = inspect_video(video_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    step_frames = max(1, int(round(info.fps * interval_seconds)))

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError("No se pudo abrir el video para extraer frames.")

    paths: list[Path] = []
    frame_index = 0
    next_capture = 0

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index >= next_capture:
                target = output_dir / f"frame_{len(paths):05d}.jpg"
                if not cv2.imwrite(str(target), frame, [cv2.IMWRITE_JPEG_QUALITY, 95]):
                    raise RuntimeError(f"No se pudo guardar el frame {target.name}.")
                paths.append(target)
                next_capture += step_frames

            frame_index += 1
            if on_progress:
                on_progress(frame_index / max(1, info.total_frames), "Extrayendo fotogramas…")
    finally:
        capture.release()

    if not paths:
        raise RuntimeError("No se extrajo ningún fotograma del video.")
    return tuple(paths)
