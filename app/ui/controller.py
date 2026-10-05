from __future__ import annotations

from pathlib import Path
from queue import Empty, Queue
from threading import Event, Thread

from PySide6.QtCore import QObject, Property, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from app.core.models import ExtractionSettings, PreparationResult
from app.core.pipeline import ExtractionPipeline


class AppController(QObject):
    """Puente Qt/QML. Los trabajadores nunca modifican directamente la UI."""

    statusChanged = Signal()
    progressChanged = Signal()
    busyChanged = Signal()
    prepared = Signal()
    generated = Signal(str)
    previewed = Signal(str)
    error = Signal(str)
    logMessage = Signal(str)
    frameChanged = Signal()
    rangeChanged = Signal()
    cropChanged = Signal()
    motionCorrectionChanged = Signal()
    removeOverlaysChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._status = "Listo para comenzar"
        self._progress = 0.0
        self._busy = False
        self._interval_seconds = 1.0
        self._source = ""
        self._frame_paths: tuple[Path, ...] = ()
        self._preparation: PreparationResult | None = None
        self._current_frame = 0
        self._range_start = 0
        self._range_end = 0
        self._crop_top = 0
        self._crop_bottom = 0
        self._pipeline: ExtractionPipeline | None = None
        self._cancel_event = Event()
        self._motion_correction = True
        self._remove_overlays = True
        self._events: Queue[tuple[str, object]] = Queue()

        self._event_timer = QTimer(self)
        self._event_timer.setInterval(50)
        self._event_timer.timeout.connect(self._drain_events)
        self._event_timer.start()

    def _set_status(self, value: str) -> None:
        self._status = value
        self.statusChanged.emit()

    def _set_progress(self, value: float) -> None:
        self._progress = max(0.0, min(1.0, value))
        self.progressChanged.emit()

    def _set_busy(self, value: bool) -> None:
        if self._busy != value:
            self._busy = value
            self.busyChanged.emit()

    @Property(str, notify=statusChanged)
    def status(self) -> str:
        return self._status

    @Property(float, notify=progressChanged)
    def progress(self) -> float:
        return self._progress

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(int, notify=prepared)
    def frameCount(self) -> int:
        return len(self._frame_paths)

    @Property(int, notify=frameChanged)
    def currentFrame(self) -> int:
        return self._current_frame

    @Property(str, notify=frameChanged)
    def currentFrameSource(self) -> str:
        if not self._frame_paths:
            return ""
        index = max(0, min(self._current_frame, len(self._frame_paths) - 1))
        return self._frame_paths[index].resolve().as_uri()

    @Property(int, notify=rangeChanged)
    def rangeStart(self) -> int:
        return self._range_start

    @Property(int, notify=rangeChanged)
    def rangeEnd(self) -> int:
        return self._range_end

    @Property(int, notify=cropChanged)
    def cropTop(self) -> int:
        return self._crop_top

    @Property(int, notify=cropChanged)
    def cropBottom(self) -> int:
        return self._crop_bottom

    @Property(int, notify=prepared)
    def videoWidth(self) -> int:
        return self._preparation.video_info.width if self._preparation else 0

    @Property(int, notify=prepared)
    def videoHeight(self) -> int:
        return self._preparation.video_info.height if self._preparation else 0

    @Property(bool, notify=motionCorrectionChanged)
    def motionCorrection(self) -> bool:
        return self._motion_correction

    @Property(bool, notify=removeOverlaysChanged)
    def removeOverlays(self) -> bool:
        return self._remove_overlays

    @Slot(str)
    def setSourceText(self, value: str) -> None:
        self._source = value.strip()

    @Slot(str)
    def setLocalVideo(self, path: str) -> None:
        path = path.strip()
        if not path:
            return
        self._source = path
        self.logMessage.emit(f"Video seleccionado: {Path(path).name}")

    @Slot(bool)
    def setMotionCorrection(self, value: bool) -> None:
        if self._motion_correction != bool(value):
            self._motion_correction = bool(value)
            self.motionCorrectionChanged.emit()

    @Slot(bool)
    def setRemoveOverlays(self, value: bool) -> None:
        if self._remove_overlays != bool(value):
            self._remove_overlays = bool(value)
            self.removeOverlaysChanged.emit()

    @Slot(float)
    def setInterval(self, value: float) -> None:
        if value > 0:
            self._interval_seconds = value

    @Slot()
    def analyze(self) -> None:
        if self._busy:
            return

        source = self._source.strip()
        if not source:
            self.error.emit("Selecciona un video o pega una URL de YouTube.")
            return

        if self._interval_seconds <= 0:
            self.error.emit("El intervalo debe ser mayor que 0.")
            return

        self._close_pipeline()
        self._cancel_event.clear()
        self._set_busy(True)
        self._set_progress(0.0)
        self._set_status("Analizando video…")
        self.logMessage.emit("▶ Analizando fuente…")

        self._pipeline = ExtractionPipeline(self._on_pipeline_event)
        self._run(self._pipeline.prepare, source, self._interval_seconds)

    @Slot()
    def reset(self) -> None:
        if self._busy:
            return
        self._close_pipeline()
        self._preparation = None
        self._frame_paths = ()
        self._current_frame = 0
        self._range_start = 0
        self._range_end = 0
        self._crop_top = 0
        self._crop_bottom = 0
        self.prepared.emit()
        self.frameChanged.emit()
        self.rangeChanged.emit()
        self.cropChanged.emit()
        self._set_progress(0.0)
        self._set_status("Listo para comenzar")

    @Slot(float)
    def setFrameIndex(self, value: float) -> None:
        if not self._frame_paths:
            return
        self._current_frame = max(0, min(int(round(value)), len(self._frame_paths) - 1))
        self.frameChanged.emit()

    @Slot(float)
    def setRangeStart(self, value: float) -> None:
        if not self._frame_paths:
            return
        maximum = len(self._frame_paths) - 1
        self._range_start = max(0, min(int(round(value)), self._range_end, maximum))
        self.rangeChanged.emit()

    @Slot(float)
    def setRangeEnd(self, value: float) -> None:
        if not self._frame_paths:
            return
        maximum = len(self._frame_paths) - 1
        self._range_end = max(self._range_start, min(int(round(value)), maximum))
        self.rangeChanged.emit()

    @Slot(float)
    def setCropTop(self, value: float) -> None:
        self._crop_top = max(0, int(round(value)))
        self.cropChanged.emit()
        self.frameChanged.emit()

    @Slot(float)
    def setCropBottom(self, value: float) -> None:
        self._crop_bottom = max(0, int(round(value)))
        self.cropChanged.emit()
        self.frameChanged.emit()

    def _settings(self, sheets_per_page: int) -> ExtractionSettings:
        settings = ExtractionSettings(
            interval_seconds=self._interval_seconds,
            crop_top=self._crop_top,
            crop_bottom=self._crop_bottom,
            start_frame=self._range_start,
            end_frame=self._range_end,
            sheets_per_page=sheets_per_page,
            stabilize_motion=self._motion_correction,
            remove_overlays=self._remove_overlays,
        )
        settings.validate()
        return settings

    @Slot(int)
    def preview(self, sheets_per_page: int) -> None:
        if self._busy or not self._preparation or not self._pipeline:
            return
        try:
            settings = self._settings(sheets_per_page)
        except ValueError as exc:
            self.error.emit(str(exc))
            return

        self._start_operation("Generando vista previa…", "▶ Generando vista previa…")
        self._run(self._pipeline.preview, settings)

    @Slot(str, int)
    def generateTo(self, output_path: str, sheets_per_page: int) -> None:
        if self._busy or not self._preparation or not self._pipeline:
            return
        try:
            settings = self._settings(sheets_per_page)
        except ValueError as exc:
            self.error.emit(str(exc))
            return

        output = Path(output_path)
        if output.suffix.lower() != ".pdf":
            output = output.with_suffix(".pdf")

        self._start_operation("Generando PDF…", "▶ Generando PDF…")
        self._run(self._pipeline.generate, settings, output)

    @Slot()
    def cancel(self) -> None:
        if self._busy:
            self._cancel_event.set()
            self._set_status("Cancelando…")

    def _start_operation(self, status: str, log: str) -> None:
        self._cancel_event.clear()
        self._set_busy(True)
        self._set_progress(0.0)
        self._set_status(status)
        self.logMessage.emit(log)

    def _run(self, function, *args) -> None:
        def worker() -> None:
            try:
                function(*args, cancel_event=self._cancel_event)
            except InterruptedError:
                self._events.put(("cancelled", None))
            except Exception as exc:
                self._events.put(("error", str(exc)))
            finally:
                self._events.put(("worker_finished", None))

        Thread(target=worker, daemon=True).start()

    def _on_pipeline_event(self, name: str, payload: object) -> None:
        self._events.put((name, payload))

    def _drain_events(self) -> None:
        while True:
            try:
                name, payload = self._events.get_nowait()
            except Empty:
                break

            if name == "status":
                self._set_status(str(payload))
                self.logMessage.emit(str(payload))
            elif name == "progress":
                progress, message = payload
                self._set_progress(float(progress))
                self._set_status(str(message))
            elif name == "prepared":
                self._handle_prepared(payload)
            elif name == "previewed":
                self._handle_previewed(payload)
            elif name == "generated":
                self._handle_generated(payload)
            elif name == "error":
                self._handle_error(str(payload))
            elif name == "cancelled":
                self._set_progress(0.0)
                self._set_status("Proceso cancelado")
                self.logMessage.emit("■ Proceso cancelado.")
                self._set_busy(False)
            elif name == "worker_finished":
                self._set_busy(False)

    def _handle_prepared(self, payload: object) -> None:
        self._preparation = payload
        self._frame_paths = payload.frame_paths
        self._current_frame = 0
        self._range_start = 0
        self._range_end = max(0, len(self._frame_paths) - 1)
        self._crop_top = 0
        self._crop_bottom = 0
        self.prepared.emit()
        self.frameChanged.emit()
        self.rangeChanged.emit()
        self.cropChanged.emit()
        self._set_busy(False)

    def _handle_previewed(self, payload: object) -> None:
        output = Path(payload)
        self._set_progress(1.0)
        self._set_status("Vista previa lista")
        self.logMessage.emit(f"✓ Vista previa: {output}")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(output)))
        self.previewed.emit(str(output))
        self._set_busy(False)

    def _handle_generated(self, payload: object) -> None:
        output = Path(payload)
        self._set_progress(1.0)
        self._set_status("PDF generado correctamente")
        self.logMessage.emit(f"✓ PDF: {output}")
        self.generated.emit(str(output))
        self._set_busy(False)

    def _handle_error(self, message: str) -> None:
        self._set_busy(False)
        self._set_status("Error")
        self.logMessage.emit(f"✕ {message}")
        self.error.emit(message)

    def _close_pipeline(self) -> None:
        if self._pipeline:
            self._pipeline.close()
            self._pipeline = None

    def close(self) -> None:
        self._cancel_event.set()
        self._event_timer.stop()
        if not self._busy and self._pipeline:
            self._pipeline.close()
            self._pipeline = None
