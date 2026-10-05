from __future__ import annotations

import logging
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Thread

from PySide6.QtCore import QObject, Property, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from app.core.models import (
    AUTO_OVERLAP_MIN_CONFIDENCE,
    ExtractionSettings,
    MontageResult,
    PreparationResult,
)
from app.core.pipeline import ExtractionPipeline


logger = logging.getLogger("scorecapture")


class AppController(QObject):
    """Puente Qt/QML. La lógica pesada permanece fuera de la interfaz."""

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
    layoutModeChanged = Signal()
    selectionChanged = Signal()
    currentFrameSelectionChanged = Signal()
    montagePreviewChanged = Signal()
    montageBusyChanged = Signal()
    joinChanged = Signal()
    layoutCutsChanged = Signal()

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

        self._montage_pipeline = ExtractionPipeline()
        self._cancel_event = Event()
        self._montage_cancel_event = Event()

        self._motion_correction = True
        self._remove_overlays = True
        self._layout_mode = "individual"

        self._selected_frames: list[int] = []
        self._auto_overlaps: tuple[int, ...] = ()
        self._join_confidences: tuple[float, ...] = ()
        self._manual_overlaps: dict[tuple[int, int], int] = {}
        self._montage_frame_width = 0
        self._montage_preview_source = ""
        self._montage_busy = False
        self._montage_generation = 0
        self._montage_pending = False
        self._layout_cuts: list[float] = []

        self._events: Queue[tuple[str, object]] = Queue()

        self._event_timer = QTimer(self)
        self._event_timer.setInterval(50)
        self._event_timer.timeout.connect(self._drain_events)
        self._event_timer.start()

        self._montage_timer = QTimer(self)
        self._montage_timer.setSingleShot(True)
        self._montage_timer.setInterval(180)
        self._montage_timer.timeout.connect(self._refresh_montage_preview)

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

    def _set_montage_busy(self, value: bool) -> None:
        if self._montage_busy != value:
            self._montage_busy = value
            self.montageBusyChanged.emit()

    @Property(str, notify=statusChanged)
    def status(self) -> str:
        return self._status

    @Property(float, notify=progressChanged)
    def progress(self) -> float:
        return self._progress

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(bool, notify=montageBusyChanged)
    def montageBusy(self) -> bool:
        return self._montage_busy

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

    @Property(str, notify=layoutModeChanged)
    def layoutMode(self) -> str:
        return self._layout_mode

    @Property(int, notify=selectionChanged)
    def selectedFrameCount(self) -> int:
        return len(self._selected_frames)

    @Property(bool, notify=currentFrameSelectionChanged)
    def currentFrameSelected(self) -> bool:
        return self._current_frame in self._selected_frames

    @Property(list, notify=selectionChanged)
    def selectedFrameSources(self) -> list[str]:
        return [
            self._frame_paths[index].resolve().as_uri()
            for index in self._selected_frames
            if 0 <= index < len(self._frame_paths)
        ]

    @Property(str, notify=selectionChanged)
    def selectionSummary(self) -> str:
        if not self._selected_frames:
            return "Sin frames seleccionados"
        numbers = ", ".join(str(index + 1) for index in self._selected_frames)
        return f"{len(self._selected_frames)} frames: {numbers}"

    @Property(str, notify=montagePreviewChanged)
    def montagePreviewSource(self) -> str:
        return self._montage_preview_source

    @Property(int, notify=joinChanged)
    def joinCount(self) -> int:
        return max(0, len(self._selected_frames) - 1)

    @Slot(int, result=str)
    def joinLabel(self, join: int) -> str:
        if not 0 <= join < self.joinCount:
            return ""
        first = self._selected_frames[join] + 1
        second = self._selected_frames[join + 1] + 1
        return f"Frame {first} → Frame {second}"

    @Slot(int, result=int)
    def joinOverlap(self, join: int) -> int:
        if not 0 <= join < self.joinCount:
            return 0

        pair = (
            self._selected_frames[join],
            self._selected_frames[join + 1],
        )
        manual = self._manual_overlaps.get(pair)
        if manual is not None:
            return manual

        if join < len(self._auto_overlaps):
            confidence = self._join_confidences[join]
            if confidence >= AUTO_OVERLAP_MIN_CONFIDENCE:
                return self._auto_overlaps[join]

        return 0

    @Slot(int, result=int)
    def joinAutoOverlap(self, join: int) -> int:
        if 0 <= join < len(self._auto_overlaps):
            return self._auto_overlaps[join]
        return 0

    @Slot(int, result=int)
    def joinConfidencePercent(self, join: int) -> int:
        if 0 <= join < len(self._join_confidences):
            return round(self._join_confidences[join] * 100)
        return 0

    @Slot(int, result=bool)
    def joinIsManual(self, join: int) -> bool:
        if not 0 <= join < self.joinCount:
            return False
        pair = (
            self._selected_frames[join],
            self._selected_frames[join + 1],
        )
        return pair in self._manual_overlaps

    @Slot(int, result=bool)
    def joinAutoReliable(self, join: int) -> bool:
        return (
            0 <= join < len(self._join_confidences)
            and self._join_confidences[join] >= AUTO_OVERLAP_MIN_CONFIDENCE
        )

    @Property(int, notify=joinChanged)
    def montageFrameWidth(self) -> int:
        return self._montage_frame_width

    @Property(int, notify=layoutCutsChanged)
    def layoutCutCount(self) -> int:
        return len(self._layout_cuts)

    @Slot(int, result=float)
    def layoutCutPercent(self, index: int) -> float:
        if not 0 <= index < len(self._layout_cuts):
            return 0.0
        return self._layout_cuts[index] * 100.0

    @Slot(int, result=float)
    def layoutCutPosition(self, index: int) -> float:
        if not 0 <= index < len(self._layout_cuts):
            return 0.0
        return self._layout_cuts[index]


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

    @Slot(str)
    def setLayoutMode(self, value: str) -> None:
        if value not in {"individual", "horizontal"}:
            return
        if self._layout_mode == value:
            return

        self._layout_mode = value
        self.layoutModeChanged.emit()
        if value == "horizontal":
            self._schedule_montage_refresh()
        else:
            self.clearLayoutCuts()
            self._reset_montage_state()

    @Slot()
    def toggleCurrentFrameSelection(self) -> None:
        if not self._frame_paths or self._layout_mode != "horizontal":
            return

        if self._current_frame in self._selected_frames:
            self._selected_frames.remove(self._current_frame)
        else:
            self._selected_frames.append(self._current_frame)

        self._normalize_join_state()
        self.clearLayoutCuts()
        self._emit_selection_state()

    @Slot(int)
    def removeSelectedFrame(self, position: int) -> None:
        if not 0 <= position < len(self._selected_frames):
            return

        removed = self._selected_frames.pop(position)
        self._manual_overlaps = {
            pair: value
            for pair, value in self._manual_overlaps.items()
            if removed not in pair
        }
        self._normalize_join_state()
        self.clearLayoutCuts()
        self._emit_selection_state()

    @Slot()
    def clearFrameSelection(self) -> None:
        if not self._selected_frames:
            return
        self._selected_frames.clear()
        self.clearLayoutCuts()
        self._reset_montage_state()
        self._emit_selection_state()

    @Slot(int, float)
    def setJoinOverlap(self, join: int, value: float) -> None:
        if not 0 <= join < self.joinCount or self._montage_frame_width <= 0:
            return

        first, second = self._selected_frames[join], self._selected_frames[join + 1]
        minimum = 0
        maximum = max(1, int(self._montage_frame_width * 0.70))
        overlap = max(minimum, min(int(round(value)), maximum))
        self._manual_overlaps[(first, second)] = overlap
        self.joinChanged.emit()
        self._schedule_montage_refresh()

    @Slot(int)
    def resetJoinOverlap(self, join: int) -> None:
        if not 0 <= join < self.joinCount:
            return
        pair = (self._selected_frames[join], self._selected_frames[join + 1])
        if pair in self._manual_overlaps:
            del self._manual_overlaps[pair]
            self.joinChanged.emit()
            self._schedule_montage_refresh()

    @Slot(float)
    def addLayoutCut(self, position: float) -> None:
        if self._layout_mode != "horizontal":
            return

        position = max(0.02, min(float(position), 0.98))
        minimum_gap = 0.01

        if any(abs(position - cut) < minimum_gap for cut in self._layout_cuts):
            self.error.emit("Ya existe un corte muy cerca de esa posición.")
            return

        self._layout_cuts.append(position)
        self._layout_cuts.sort()
        self.layoutCutsChanged.emit()

    @Slot(int, float)
    def setLayoutCut(self, index: int, position: float) -> None:
        if not 0 <= index < len(self._layout_cuts):
            return

        lower = self._layout_cuts[index - 1] + 0.01 if index > 0 else 0.02
        upper = self._layout_cuts[index + 1] - 0.01 if index + 1 < len(self._layout_cuts) else 0.98
        self._layout_cuts[index] = max(lower, min(float(position), upper))
        self.layoutCutsChanged.emit()

    @Slot(int)
    def removeLayoutCut(self, index: int) -> None:
        if not 0 <= index < len(self._layout_cuts):
            return
        self._layout_cuts.pop(index)
        self.layoutCutsChanged.emit()

    @Slot()
    def clearLayoutCuts(self) -> None:
        if not self._layout_cuts:
            return
        self._layout_cuts.clear()
        self.layoutCutsChanged.emit()

    @Slot(bool)
    def setRemoveOverlays(self, value: bool) -> None:
        if self._remove_overlays != bool(value):
            self._remove_overlays = bool(value)
            self.removeOverlaysChanged.emit()
            self._schedule_montage_refresh()

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
        self._reset_montage_state()
        self.clearLayoutCuts()
        self._selected_frames.clear()
        self._emit_selection_state()

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
        self._reset_montage_state()
        self.clearLayoutCuts()
        self._preparation = None
        self._frame_paths = ()
        self._current_frame = 0
        self._range_start = 0
        self._range_end = 0
        self._crop_top = 0
        self._crop_bottom = 0
        self._selected_frames.clear()
        self._emit_selection_state()
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
        self._current_frame = max(
            0,
            min(int(round(value)), len(self._frame_paths) - 1),
        )
        self.frameChanged.emit()
        self.currentFrameSelectionChanged.emit()

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
        self._schedule_montage_refresh()

    @Slot(float)
    def setCropBottom(self, value: float) -> None:
        self._crop_bottom = max(0, int(round(value)))
        self.cropChanged.emit()
        self.frameChanged.emit()
        self._schedule_montage_refresh()

    def _settings(self, sheets_per_page: int) -> ExtractionSettings:
        return ExtractionSettings(
            interval_seconds=self._interval_seconds,
            crop_top=self._crop_top,
            crop_bottom=self._crop_bottom,
            start_frame=self._range_start,
            end_frame=self._range_end,
            sheets_per_page=sheets_per_page,
            page_size="A4",
            stabilize_motion=self._motion_correction,
            remove_overlays=self._remove_overlays,
            layout_mode=self._layout_mode,
            selected_frames=tuple(self._selected_frames),
            overlap_overrides=self._effective_overlaps(),
            layout_cuts=tuple(self._layout_cuts),
        )

    def _effective_overlaps(self) -> tuple[int | None, ...]:
        return tuple(
            self._manual_overlaps.get(
                (self._selected_frames[index], self._selected_frames[index + 1])
            )
            for index in range(self.joinCount)
        )

    def _normalize_join_state(self) -> None:
        self._auto_overlaps = ()
        self._join_confidences = ()

    def _emit_selection_state(self) -> None:
        self.selectionChanged.emit()
        self.currentFrameSelectionChanged.emit()
        self.joinChanged.emit()
        self._schedule_montage_refresh()

    def _reset_montage_state(self) -> None:
        self._montage_timer.stop()
        self._montage_generation += 1
        self._montage_cancel_event.set()
        self._montage_pending = False
        self._auto_overlaps = ()
        self._join_confidences = ()
        self._manual_overlaps.clear()
        self._montage_frame_width = 0
        self._montage_preview_source = ""
        self._set_montage_busy(False)
        self.joinChanged.emit()
        self.montagePreviewChanged.emit()

    def _schedule_montage_refresh(self) -> None:
        if self._layout_mode != "horizontal":
            return
        if len(self._selected_frames) < 2:
            self._reset_montage_state()
            return
        if self._montage_busy:
            self._montage_pending = True
            self._montage_cancel_event.set()
            return
        self._montage_pending = False
        self._montage_timer.start()

    def _refresh_montage_preview(self) -> None:
        if self._busy or self._layout_mode != "horizontal":
            return
        if self._montage_busy:
            self._montage_pending = True
            self._montage_cancel_event.set()
            return
        if len(self._selected_frames) < 2:
            return

        try:
            settings = self._settings(1)
        except ValueError as exc:
            self._handle_montage_error(str(exc))
            return

        self._montage_pipeline.frame_paths = self._frame_paths

        self._montage_cancel_event.set()
        montage_cancel_event = Event()
        self._montage_cancel_event = montage_cancel_event

        self._montage_generation += 1
        generation = self._montage_generation

        output = (
            self._montage_pipeline.workspace.montages
            / f"live_montage_{generation:05d}.jpg"
        )

        self._set_montage_busy(True)

        def worker() -> None:
            try:
                result = self._montage_pipeline.preview_montage(
                    settings,
                    output,
                    cancel_event=montage_cancel_event,
                )
            except InterruptedError:
                self._events.put(("montage_cancelled", generation))
            except Exception as exc:
                self._events.put(("montage_error", (generation, str(exc))))
            else:
                self._events.put(("montage_ready", (generation, result)))

        Thread(target=worker, daemon=True).start()

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
                logger.exception("Operación de extracción fallida")
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
            elif name == "montage_ready":
                self._handle_montage_ready(payload)
            elif name == "montage_cancelled":
                self._set_montage_busy(False)
                self._restart_pending_montage()
            elif name == "montage_error":
                generation, message = payload
                if generation == self._montage_generation:
                    self._handle_montage_error(message)

    def _handle_prepared(self, payload: PreparationResult) -> None:
        self._preparation = payload
        self._frame_paths = payload.frame_paths
        self._current_frame = 0
        self._range_start = 0
        self._range_end = max(0, len(self._frame_paths) - 1)
        self._crop_top = 0
        self._crop_bottom = 0
        self._set_busy(False)
        self.prepared.emit()
        self.frameChanged.emit()
        self.rangeChanged.emit()
        self.cropChanged.emit()

    def _handle_montage_ready(self, payload: object) -> None:
        generation, result = payload
        if generation != self._montage_generation:
            return
        if not isinstance(result, MontageResult):
            self._handle_montage_error("La previsualización devolvió un resultado inválido.")
            return

        self._auto_overlaps = result.auto_overlaps
        self._join_confidences = result.confidences
        self._montage_frame_width = result.frame_width
        self._montage_preview_source = result.output_path.resolve().as_uri()
        self.joinChanged.emit()
        self.montagePreviewChanged.emit()
        self._set_montage_busy(False)
        self._restart_pending_montage()

    def _handle_montage_error(self, message: str) -> None:
        logger.error("Reconstrucción: %s", message)
        self._set_montage_busy(False)
        self.logMessage.emit(f"✕ Reconstrucción: {message}")
        self._restart_pending_montage()

    def _restart_pending_montage(self) -> None:
        if self._montage_pending:
            self._montage_pending = False
            self._montage_timer.start()

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
        self._montage_cancel_event.set()
        self._event_timer.stop()
        if not self._busy and self._pipeline:
            self._pipeline.close()
            self._pipeline = None
