from __future__ import annotations

from pathlib import Path
from threading import Event
from typing import Callable

from .crop import crop_frames
from .deduplicator import remove_consecutive_duplicates
from .downloader import download_youtube, is_youtube_url
from .frame_extractor import extract_frames, inspect_video
from .models import ExtractionSettings, PreparationResult
from .motion_tracker import stabilize_frames
from .pdf_exporter import export_pdf
from .workspace import Workspace

EventCallback = Callable[[str, object], None]


class ExtractionPipeline:
    """Orquestador de alto nivel; no conoce nada de la interfaz gráfica."""

    def __init__(self, on_event: EventCallback | None = None) -> None:
        self.workspace = Workspace()
        self.frame_paths: tuple[Path, ...] = ()
        self.video_path: Path | None = None
        self.on_event = on_event

    def _emit(self, name: str, payload: object = None) -> None:
        if self.on_event:
            self.on_event(name, payload)

    def prepare(
        self,
        source: str,
        interval_seconds: float,
        stabilize_motion: bool = True,
        cancel_event: Event | None = None,
    ) -> PreparationResult:
        source = source.strip()
        if not source:
            raise ValueError("Selecciona un video o pega una URL de YouTube.")

        if is_youtube_url(source):
            self._emit("status", "Preparando descarga…")
            video_path = download_youtube(
                source,
                self.workspace.video,
                lambda p, m: self._emit("progress", (p, m)),
            )
        else:
            video_path = Path(source)
            if not video_path.exists() or not video_path.is_file():
                raise FileNotFoundError("No se encontró el archivo de video seleccionado.")

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

        if stabilize_motion:
            self._emit("status", "Siguiendo movimiento de la partitura…")
            frames = stabilize_frames(
                frames,
                self.workspace.aligned,
                on_progress=lambda p, m: self._emit("progress", (p, m)),
                cancel_event=cancel_event,
            )
            self._check_cancel(cancel_event)

        self.video_path = video_path
        self.frame_paths = frames
        result = PreparationResult(video_path, frames, info)
        self._emit("prepared", result)
        return result

    def generate(self, settings: ExtractionSettings, output_pdf: Path, cancel_event: Event | None = None) -> Path:
        settings.validate()
        if not self.frame_paths:
            raise RuntimeError("Primero debes analizar un video.")

        self._check_cancel(cancel_event)
        cropped = crop_frames(
            self.frame_paths,
            self.workspace.crops,
            settings.crop_top,
            settings.crop_bottom,
            settings.start_frame,
            settings.end_frame,
            lambda p, m: self._emit("progress", (p, m)),
        )
        self._check_cancel(cancel_event)

        unique = remove_consecutive_duplicates(
            cropped,
            settings.duplicate_threshold,
            lambda p, m: self._emit("progress", (p, m)),
        )
        self._check_cancel(cancel_event)
        if not unique:
            raise RuntimeError("No quedaron partituras después de eliminar duplicados.")

        self._emit("status", "Generando PDF…")
        output = export_pdf(
            unique,
            output_pdf,
            sheets_per_page=settings.sheets_per_page,
            page_size=settings.page_size,
            margin_pt=settings.margin_pt,
        )
        self._emit("progress", (1.0, "PDF generado."))
        self._emit("generated", output)
        return output

    def close(self) -> None:
        self.workspace.cleanup()
        self.frame_paths = ()
        self.video_path = None

    @staticmethod
    def _check_cancel(cancel_event: Event | None) -> None:
        if cancel_event and cancel_event.is_set():
            raise InterruptedError("Proceso cancelado por el usuario.")
