from __future__ import annotations

import logging
from pathlib import Path
from threading import Event
from typing import Callable

from .crop import crop_frames
from .deduplicator import remove_consecutive_duplicates
from .downloader import download_youtube, is_youtube_url
from .frame_extractor import extract_frames, inspect_video
from .models import ExtractionSettings, PreparationResult
from .motion_tracker import stabilize_frames
from .overlay_cleaner import remove_transient_overlays
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

        self.video_path = video_path
        self.frame_paths = frames
        result = PreparationResult(video_path, frames, info)
        self._emit("prepared", result)
        return result

    def _selected_frames(
        self,
        settings: ExtractionSettings,
    ) -> tuple[Path, ...]:
        start = settings.start_frame
        end = len(self.frame_paths) - 1 if settings.end_frame is None else min(
            settings.end_frame,
            len(self.frame_paths) - 1,
        )
        candidates = self.frame_paths[start : end + 1]
        if not settings.selected_frames:
            return candidates

        invalid = [index for index in settings.selected_frames if index >= len(self.frame_paths)]
        if invalid:
            raise ValueError("La selección manual contiene frames fuera del video.")
        selected = tuple(
            self.frame_paths[index]
            for index in settings.selected_frames
            if start <= index <= end
        )
        if not selected:
            raise ValueError("Ningún frame seleccionado está dentro del rango.")
        return selected

    def _prepare_images(
        self,
        settings: ExtractionSettings,
        cancel_event: Event | None = None,
    ) -> tuple[Path, ...]:
        candidates = self._selected_frames(settings)

        # En un montaje horizontal conservamos el desplazamiento lateral. Estabilizar
        # contra una referencia global lo eliminaría y arruinaría el stitching.
        working_frames = candidates
        if settings.stabilize_motion and settings.layout_mode == "individual":
            self._emit("status", "Siguiendo movimiento dentro del recorte seleccionado…")
            working_frames = stabilize_frames(
                candidates,
                self.workspace.aligned,
                crop_top=settings.crop_top,
                crop_bottom=settings.crop_bottom,
                on_progress=lambda p, m: self._emit("progress", (p, m)),
                cancel_event=cancel_event,
            )
            self._check_cancel(cancel_event)

        self._emit("status", "Aplicando recorte seleccionado…")
        cropped = crop_frames(
            working_frames,
            self.workspace.crops,
            settings.crop_top,
            settings.crop_bottom,
            start_index=0,
            end_index=None,
            on_progress=lambda p, m: self._emit("progress", (p, m)),
        )
        self._check_cancel(cancel_event)

        if settings.remove_overlays:
            self._emit("status", "Quitando resaltadores y cursores móviles…")
            cropped = remove_transient_overlays(
                cropped,
                self.workspace.cleaned,
                on_progress=lambda p, m: self._emit("progress", (p, m)),
                cancel_event=cancel_event,
            )
            self._check_cancel(cancel_event)

        if settings.layout_mode == "horizontal":
            if len(cropped) < 2:
                raise ValueError("El montaje horizontal necesita al menos 2 frames seleccionados.")
            self._emit("status", "Uniendo frames horizontalmente…")
            montage = stitch_horizontal(
                cropped,
                self.workspace.montages / "montaje_horizontal.jpg",
                on_progress=lambda p, m: self._emit("progress", (p, m)),
            )
            return (montage,)

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
        images = self._prepare_images(settings, cancel_event)
        self._emit("status", "Generando PDF…")
        output = export_pdf(
            images,
            output_pdf,
            sheets_per_page=settings.sheets_per_page,
            page_size=settings.page_size,
            margin_pt=settings.margin_pt,
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

    def close(self) -> None:
        self.workspace.cleanup()
        self.frame_paths = ()
        self.video_path = None

    @staticmethod
    def _check_cancel(cancel_event: Event | None) -> None:
        if cancel_event and cancel_event.is_set():
            raise InterruptedError("Proceso cancelado por el usuario.")
