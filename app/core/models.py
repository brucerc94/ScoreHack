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
    stabilize_motion: bool = True
    remove_overlays: bool = True
    layout_mode: str = "individual"
    selected_frames: tuple[int, ...] = ()
    overlap_overrides: tuple[int, ...] = ()

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
        if self.layout_mode not in {"individual", "horizontal"}:
            raise ValueError("El modo de montaje no es válido.")
        if any(index < 0 for index in self.selected_frames):
            raise ValueError("La selección manual contiene frames inválidos.")
        if len(set(self.selected_frames)) != len(self.selected_frames):
            raise ValueError("La selección manual contiene frames repetidos.")
        if any(overlap < 0 for overlap in self.overlap_overrides):
            raise ValueError("Los solapes no pueden ser negativos.")


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


@dataclass(frozen=True)
class MontageResult:
    output_path: Path
    auto_overlaps: tuple[int, ...]
    effective_overlaps: tuple[int, ...]
    confidences: tuple[float, ...]
    frame_width: int
    frame_height: int
