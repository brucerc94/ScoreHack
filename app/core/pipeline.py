from __future__ import annotations

import logging
from pathlib import Path
from threading import Event
from typing import Callable

from .crop import crop_frames
from .deduplicator import remove_consecutive_duplicates
from .downloader import download_youtube, is_youtube_url
from .frame_extractor import extract_frames, inspect_video
from .layout import split_panorama
from .models import ExtractionSettings, MontageResult, PreparationResult
from .pdf_exporter import export_pdf
from .stitcher import stitch_horizontal
from .workspace import Workspace

EventCallback = Callable[[str, object], None]
logger = logging.getLogger("scorecapture")


class ExtractionPipeline:
    """Orquestador de alto nivel; no conoce nada de la interfaz gráfica."""

    def __init__(self, on_event: EventCallback | None = None) -> None:
        self.workspace = Workspace()
        self.frame_paths: tuple[Path, ...] = ()
        self.video_path: Path | None = None
        self.on_event = on_event
        self._last_console_progress = -1

    def _emit(self, name: str, payload: object = None) -> None:
        if name == "status":
            logger.info(str(payload))
            self._last_console_progress = -1
        elif name == "progress":
            progress, message = payload
            percent = int(float(progress) * 100)
            if percent == 100 or percent - self._last_console_progress >= 10:
                logger.info("[%3d%%] %s", percent, message)
                self._last_console_progress = percent

        if self.on_event:
            self.on_event(name, payload)

    def prepare(
        self,
        source: str,
        interval_seconds: float,
        cancel_event: Event | None = None,
    ) -> PreparationResult:
        source = source.strip()
        if not source:
            raise ValueError("Selecciona un video o pega una URL de YouTube.")

        video_path = self._resolve_source(source, cancel_event)

        self._check_cancel(cancel_event)
        self._emit("status", "Analizando video…")
        info = inspect_video(video_path)
        frames = extract_frames(
            video_path,
            self.workspace.frames,
            interval_seconds,
            lambda p, m: self._emit("progress", (p, m)),
        )
        self._check_cancel(cancel_event)

        self.video_path = video_path
        self.frame_paths = frames
        result = PreparationResult(video_path, frames, info)
        self._emit("prepared", result)
        return result

    def _resolve_source(self, source: str, cancel_event: Event | None) -> Path:
        if is_youtube_url(source):
            self._emit("status", "Preparando descarga…")
            path = download_youtube(
                source,
                self.workspace.video,
                lambda p, m: self._emit("progress", (p, m)),
            )
            self._check_cancel(cancel_event)
            return path

        path = Path(source)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError("No se encontró el archivo de video seleccionado.")
        return path

    def _selected_frames(
        self,
        settings: ExtractionSettings,
    ) -> tuple[Path, ...]:
        if settings.layout_mode == "horizontal":
            if len(settings.selected_frames) < 2:
                raise ValueError(
                    "Selecciona al menos 2 frames para el montaje horizontal."
                )

            invalid = [
                index
                for index in settings.selected_frames
                if index < 0 or index >= len(self.frame_paths)
            ]
            if invalid:
                raise ValueError("La selección manual contiene frames fuera del video.")

            return tuple(self.frame_paths[index] for index in settings.selected_frames)

        start = settings.start_frame
        end = (
            len(self.frame_paths) - 1
            if settings.end_frame is None
            else min(settings.end_frame, len(self.frame_paths) - 1)
        )
        return self.frame_paths[start : end + 1]

    def _prepare_cropped_frames(
        self,
        settings: ExtractionSettings,
        cancel_event: Event | None = None,
        work_root: Path | None = None,
    ) -> tuple[Path, ...]:
        candidates = self._selected_frames(settings)

        root = work_root or self.workspace.root
        aligned_dir = root / "aligned"
        crops_dir = root / "crops"
        cleaned_dir = root / "cleaned"

        self._emit("status", "Aplicando recorte seleccionado…")
        cropped = crop_frames(
            candidates,
            crops_dir,
            settings.crop_top,
            settings.crop_bottom,
            start_index=0,
            end_index=None,
            on_progress=lambda p, m: self._emit("progress", (p, m)),
            cancel_event=cancel_event,
        )
        self._check_cancel(cancel_event)

        return cropped

    def _build_montage(
        self,
        settings: ExtractionSettings,
        output_path: Path,
        cancel_event: Event | None = None,
        overlap_overrides: tuple[int | None, ...] = (),
    ) -> MontageResult:
        if settings.layout_mode != "horizontal":
            raise ValueError("La reconstrucción horizontal requiere el modo horizontal.")

        cropped = self._prepare_cropped_frames(
            settings,
            cancel_event=cancel_event,
            work_root=output_path.parent / output_path.stem,
        )
        if len(cropped) < 2:
            raise ValueError("Selecciona al menos 2 frames para el montaje horizontal.")

        self._emit("status", "Detectando zonas repetidas entre frames…")
        return stitch_horizontal(
            cropped,
            output_path,
            overlap_overrides=overlap_overrides,
            on_progress=lambda p, m: self._emit("progress", (p, m)),
            cancel_event=cancel_event,
        )

    def _build_unique_images(
        self,
        settings: ExtractionSettings,
        cancel_event: Event | None = None,
    ) -> tuple[Path, ...]:
        if settings.layout_mode == "horizontal":
            montage = self._build_montage(
                settings,
                self.workspace.montages / "montaje_horizontal.jpg",
                cancel_event=cancel_event,
                overlap_overrides=settings.overlap_overrides,
            )
            self._emit("status", "Aplicando división manual de página…")
            segments = split_panorama(
                montage.output_path,
                settings.layout_cuts,
                self.workspace.segments,
                on_progress=lambda p, m: self._emit("progress", (p, m)),
                cancel_event=cancel_event,
            )
            return segments

        cropped = self._prepare_cropped_frames(settings, cancel_event=cancel_event)
        self._emit("status", "Eliminando fotogramas repetidos…")
        unique = remove_consecutive_duplicates(
            cropped,
            settings.duplicate_threshold,
            lambda p, m: self._emit("progress", (p, m)),
        )
        self._check_cancel(cancel_event)
        if not unique:
            raise RuntimeError("No quedaron partituras después de eliminar duplicados.")
        return unique

    def _export(
        self,
        settings: ExtractionSettings,
        output_pdf: Path,
        cancel_event: Event | None = None,
    ) -> Path:
        images = self._build_unique_images(settings, cancel_event)
        self._emit("status", "Generando PDF…")
        output = export_pdf(
            images,
            output_pdf,
            sheets_per_page=settings.sheets_per_page,
            page_size=settings.page_size,
            margin_pt=settings.margin_pt,
            layout_mode=settings.layout_mode,
        )
        self._emit("progress", (1.0, "PDF generado."))
        return output

    def generate(
        self,
        settings: ExtractionSettings,
        output_pdf: Path,
        cancel_event: Event | None = None,
    ) -> Path:
        settings.validate()
        output = self._export(settings, output_pdf, cancel_event)
        self._emit("generated", output)
        return output

    def preview(
        self,
        settings: ExtractionSettings,
        cancel_event: Event | None = None,
    ) -> Path:
        settings.validate()
        output = self._export(settings, self.workspace.preview_pdf, cancel_event)
        self._emit("previewed", output)
        return output

    def preview_montage(
        self,
        settings: ExtractionSettings,
        output_path: Path,
        cancel_event: Event | None = None,
    ) -> MontageResult:
        settings.validate()
        if settings.layout_mode != "horizontal":
            raise ValueError("Activa el modo Unir horizontal para ver el montaje.")

        output = self._build_montage(
            settings,
            output_path,
            cancel_event=cancel_event,
            overlap_overrides=settings.overlap_overrides,
        )
        self._emit("montage_previewed", output)
        return output

    def close(self) -> None:
        self.workspace.cleanup()
        self.frame_paths = ()
        self.video_path = None

    @staticmethod
    def _check_cancel(cancel_event: Event | None) -> None:
        if cancel_event and cancel_event.is_set():
            raise InterruptedError("Proceso cancelado por el usuario.")
