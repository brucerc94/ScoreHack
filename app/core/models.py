from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExtractionSettings:
    interval_seconds: float = 1.0
    crop_top: int = 0
    crop_bottom: int = 0
    start_frame: int = 0
    end_frame: int | None = None
    duplicate_threshold: float = 0.97
    sheets_per_page: int = 4
    page_size: str = "A4"
    margin_pt: float = 28.0

    def validate(self) -> None:
        if self.interval_seconds <= 0:
            raise ValueError("El intervalo debe ser mayor que 0 segundos.")
        if not 1 <= self.sheets_per_page <= 8:
            raise ValueError("Las partituras por hoja deben estar entre 1 y 8.")
        if not 0.0 < self.duplicate_threshold <= 1.0:
            raise ValueError("El umbral de duplicados debe estar entre 0 y 1.")
        if self.crop_top < 0 or self.crop_bottom < 0:
            raise ValueError("Los recortes no pueden ser negativos.")
        if self.start_frame < 0:
            raise ValueError("El frame inicial no puede ser negativo.")
        if self.end_frame is not None and self.end_frame < self.start_frame:
            raise ValueError("El frame final no puede ser menor que el inicial.")


@dataclass(frozen=True)
class VideoInfo:
    fps: float
    total_frames: int
    width: int
    height: int
    duration_seconds: float


@dataclass(frozen=True)
class PreparationResult:
    video_path: Path
    frame_paths: tuple[Path, ...]
    video_info: VideoInfo
