from __future__ import annotations

import queue
from pathlib import Path
from threading import Event, Thread
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageDraw

from app.core.models import ExtractionSettings, PreparationResult
from app.core.pipeline import ExtractionPipeline


class MainWindow(ctk.CTk):
    """Interfaz moderna y thread-safe; el procesamiento vive en core/."""

    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Extractor de Partituras")
        self.geometry("1160x760")
        self.minsize(1000, 680)

        icon = Path(__file__).resolve().parents[2] / "icon.ico"
        if icon.exists():
            try:
                self.iconbitmap(str(icon))
            except Exception:
                pass

        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.cancel_event = Event()
        self.pipeline: ExtractionPipeline | None = None
        self.preparation: PreparationResult | None = None
        self.preview_image: ctk.CTkImage | None = None

        self.source_mode = "YouTube"
        self.local_video = ""

        self._configure_grid()
        self._build_sidebar()
        self._build_content()
        self._on_source_mode("YouTube")

        self.after(80, self._drain_events)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_grid(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(
            sidebar,
            text="♫  ScoreCapture",
            font=ctk.CTkFont(size=23, weight="bold"),
        ).pack(anchor="w", padx=24, pady=(30, 8))

        ctk.CTkLabel(
            sidebar,
            text="YouTube / Video → PDF",
            text_color=("gray45", "gray70"),
        ).pack(anchor="w", padx=24, pady=(0, 28))

        ctk.CTkButton(
            sidebar,
            text="  Extraer partitura",
            anchor="w",
            height=42,
            command=lambda: None,
        ).pack(fill="x", padx=18, pady=4)

        ctk.CTkLabel(
            sidebar,
            text="FLUJO",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray55",
        ).pack(anchor="w", padx=24, pady=(24, 8))

        for label in ("1  Fuente", "2  Recorte y rango", "3  Exportar PDF"):
            ctk.CTkLabel(
                sidebar,
                text=label,
                anchor="w",
                text_color=("gray40", "gray75"),
            ).pack(fill="x", padx=30, pady=5)

        spacer = ctk.CTkFrame(sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        ctk.CTkLabel(
            sidebar,
            text="No requiere permisos\nde administrador.",
            justify="left",
            text_color=("gray45", "gray65"),
        ).pack(anchor="w", padx=24, pady=(0, 24))

    def _build_content(self) -> None:
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.grid(row=0, column=1, sticky="nsew", padx=24, pady=20)
        root.grid_columnconfigure(0, weight=3)
        root.grid_columnconfigure(1, weight=2)
        root.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(root, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(
            header,
            text="Extraer una partitura",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(anchor="w")
        self.status_label = ctk.CTkLabel(
            header,
            text="Listo para comenzar",
            text_color=("gray45", "gray70"),
        )
        self.status_label.pack(anchor="w", pady=(3, 0))

        self._build_source_card(root)
        self._build_settings_card(root)
        self._build_preview_card(root)
        self._build_log_card(root)

    def _card(
        self,
        parent: ctk.CTkFrame,
        title: str,
        row: int,
        column: int,
        columnspan: int = 1,
    ) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, corner_radius=16)
        frame.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            sticky="nsew",
            padx=6,
            pady=6,
        )
        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=18, pady=(16, 10))
        return frame

    def _build_source_card(self, root: ctk.CTkFrame) -> None:
        card = self._card(root, "Fuente", 1, 0, 2)

        self.source_mode_control = ctk.CTkSegmentedButton(
            card,
            values=["YouTube", "Video local"],
            command=self._on_source_mode,
        )
        self.source_mode_control.set("YouTube")
        self.source_mode_control.pack(fill="x", padx=18, pady=(0, 12))

        self.url_entry = ctk.CTkEntry(
            card,
            placeholder_text="Pega aquí la URL de YouTube",
        )
        self.url_entry.pack(fill="x", padx=18, pady=(0, 9))

        local_row = ctk.CTkFrame(card, fg_color="transparent")
        local_row.pack(fill="x", padx=18, pady=(0, 9))
        local_row.grid_columnconfigure(0, weight=1)

        self.local_label = ctk.CTkLabel(
            local_row,
            text="Ningún video seleccionado",
            anchor="w",
            text_color=("gray45", "gray65"),
        )
        self.local_label.grid(row=0, column=0, sticky="ew")

        self.choose_video_button = ctk.CTkButton(
            local_row,
            text="Subir video",
            width=125,
            command=self._choose_video,
        )
        self.choose_video_button.grid(row=0, column=1, padx=(10, 0))

        self.analyze_button = ctk.CTkButton(
            card,
            text="Analizar video",
            height=40,
            command=self._start_prepare,
        )
        self.analyze_button.pack(fill="x", padx=18, pady=(2, 18))

    def _build_settings_card(self, root: ctk.CTkFrame) -> None:
        card = self._card(root, "Configuración", 2, 1)

        ctk.CTkLabel(card, text="Intervalo entre frames (s)").pack(
            anchor="w", padx=18, pady=(4, 3)
        )
        self.interval_entry = ctk.CTkEntry(card)
        self.interval_entry.insert(0, "1.0")
        self.interval_entry.pack(fill="x", padx=18)

        ctk.CTkLabel(card, text="Partituras por página").pack(
            anchor="w", padx=18, pady=(11, 3)
        )
        self.pages_combo = ctk.CTkComboBox(
            card,
            values=["1", "2", "3", "4", "5", "6", "7", "8"],
        )
        self.pages_combo.set("4")
        self.pages_combo.pack(fill="x", padx=18)

        ctk.CTkLabel(card, text="Recorte superior").pack(
            anchor="w", padx=18, pady=(13, 0)
        )
        self.top_slider = ctk.CTkSlider(
            card,
            from_=0,
            to=700,
            command=lambda _: self._refresh_preview(),
        )
        self.top_slider.pack(fill="x", padx=18, pady=(4, 3))
        self.top_value = ctk.CTkLabel(card, text="0 px")
        self.top_value.pack(anchor="e", padx=18)

        ctk.CTkLabel(card, text="Recorte inferior").pack(
            anchor="w", padx=18, pady=(5, 0)
        )
        self.bottom_slider = ctk.CTkSlider(
            card,
            from_=0,
            to=700,
            command=lambda _: self._refresh_preview(),
        )
        self.bottom_slider.pack(fill="x", padx=18, pady=(4, 3))
        self.bottom_value = ctk.CTkLabel(card, text="0 px")
        self.bottom_value.pack(anchor="e", padx=18)

        self.generate_button = ctk.CTkButton(
            card,
            text="Generar PDF",
            height=44,
            state="disabled",
            command=self._start_generate,
        )
        self.generate_button.pack(fill="x", padx=18, pady=(18, 18))

    def _build_preview_card(self, root: ctk.CTkFrame) -> None:
        card = self._card(root, "Vista previa y rango", 2, 0)
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        self.preview_label = ctk.CTkLabel(
            card,
            text="Analiza un video para mostrar la vista previa.",
            corner_radius=12,
        )
        self.preview_label.pack(fill="both", expand=True, padx=18, pady=12)

        controls = ctk.CTkFrame(card, fg_color="transparent")
        controls.pack(fill="x", padx=18, pady=(0, 14))
        controls.grid_columnconfigure(1, weight=1)

        self.frame_label = ctk.CTkLabel(controls, text="Frame 0 / 0", width=90)
        self.frame_label.grid(row=0, column=0, sticky="w")

        self.frame_slider = ctk.CTkSlider(
            controls,
            from_=0,
            to=1,
            command=self._on_frame_change,
            state="disabled",
        )
        self.frame_slider.grid(row=0, column=1, sticky="ew", padx=10)

        self.range_label = ctk.CTkLabel(
            controls,
            text="Rango: 1 – 0",
            text_color=("gray45", "gray70"),
        )
        self.range_label.grid(row=0, column=2, padx=(8, 0))

        ctk.CTkLabel(controls, text="Desde").grid(row=1, column=0, pady=(8, 0))
        self.range_start = ctk.CTkSlider(
            controls,
            from_=0,
            to=1,
            command=self._on_range_change,
            state="disabled",
        )
        self.range_start.grid(row=1, column=1, sticky="ew", padx=10, pady=(8, 0))

        ctk.CTkLabel(controls, text="Hasta").grid(row=2, column=0, pady=(8, 0))
        self.range_end = ctk.CTkSlider(
            controls,
            from_=0,
            to=1,
            command=self._on_range_change,
            state="disabled",
        )
        self.range_end.grid(row=2, column=1, sticky="ew", padx=10, pady=(8, 0))

    def _build_log_card(self, root: ctk.CTkFrame) -> None:
        card = self._card(root, "Actividad", 3, 0, 2)
        self.log_box = ctk.CTkTextbox(card, height=105, corner_radius=10)
        self.log_box.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        self.progress = ctk.CTkProgressBar(card, height=8)
        self.progress.pack(fill="x", padx=18, pady=(0, 16))
        self.progress.set(0)

    def _on_source_mode(self, mode: str) -> None:
        self.source_mode = mode
        is_url = mode == "YouTube"
        self.url_entry.configure(state="normal" if is_url else "disabled")
        self.choose_video_button.configure(
            state="disabled" if is_url else "normal"
        )
        self._reset_preparation()

    def _choose_video(self) -> None:
        path = filedialog.askopenfilename(
            title="Seleccionar video",
            filetypes=[
                ("Videos", "*.mp4 *.mkv *.avi *.mov *.webm *.m4v"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if path:
            self.local_video = path
            self.local_label.configure(text=Path(path).name)

    def _source_value(self) -> str:
        return self.url_entry.get().strip() if self.source_mode == "YouTube" else self.local_video

    def _start_prepare(self) -> None:
        try:
            interval = float(self.interval_entry.get().strip())
            if interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Dato inválido",
                "El intervalo debe ser un número mayor que 0.",
            )
            return

        source = self._source_value()
        if not source:
            messagebox.showwarning(
                "Falta la fuente",
                "Pega una URL de YouTube o selecciona un video local.",
            )
            return

        if self.pipeline:
            self.pipeline.close()

        self.cancel_event.clear()
        self._set_busy(True)
        self.progress.set(0)
        self._log("▶ Iniciando análisis…")
        self.pipeline = ExtractionPipeline(self._pipeline_event)
        self._run_worker(self.pipeline.prepare, source, interval)

    def _start_generate(self) -> None:
        if not self.preparation or not self.pipeline:
            return

        try:
            interval = float(self.interval_entry.get().strip())
            sheets = int(self.pages_combo.get())
            start = int(round(self.range_start.get()))
            end = int(round(self.range_end.get()))
            settings = ExtractionSettings(
                interval_seconds=interval,
                crop_top=int(round(self.top_slider.get())),
                crop_bottom=int(round(self.bottom_slider.get())),
                start_frame=start,
                end_frame=end,
                sheets_per_page=sheets,
            )
            settings.validate()
        except (ValueError, TypeError) as exc:
            messagebox.showerror("Configuración inválida", str(exc))
            return

        output = filedialog.asksaveasfilename(
            title="Guardar PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="partitura.pdf",
        )
        if not output:
            return

        self.cancel_event.clear()
        self._set_busy(True)
        self.progress.set(0)
        self._log("▶ Generando PDF…")
        self._run_worker(self.pipeline.generate, settings, Path(output))

    def _run_worker(self, func, *args) -> None:
        def worker() -> None:
            try:
                result = func(*args, cancel_event=self.cancel_event)
                self.events.put(("done", result))
            except Exception as exc:
                self.events.put(("error", exc))

        Thread(target=worker, daemon=True).start()

    def _pipeline_event(self, name: str, payload: object) -> None:
        self.events.put((name, payload))

    def _drain_events(self) -> None:
        try:
            while True:
                name, payload = self.events.get_nowait()

                if name == "progress":
                    progress, message = payload
                    self.progress.set(float(progress))
                    self.status_label.configure(text=str(message))

                elif name == "status":
                    self.status_label.configure(text=str(payload))
                    self._log(str(payload))

                elif name == "prepared":
                    self.preparation = payload
                    self._on_prepared(payload)

                elif name == "generated":
                    self._on_generated(payload)

                elif name == "done":
                    self._set_busy(False)

                elif name == "error":
                    self._set_busy(False)
                    self._log(f"✕ {payload}")
                    if not isinstance(payload, InterruptedError):
                        messagebox.showerror("Error", str(payload))

        except queue.Empty:
            pass
        finally:
            self.after(80, self._drain_events)

    def _on_prepared(self, result: PreparationResult) -> None:
        count = len(result.frame_paths)
        maximum = max(0, count - 1)
        max_crop = max(0, result.video_info.height - 2)

        self.top_slider.configure(to=max_crop)
        self.bottom_slider.configure(to=max_crop)
        self.top_slider.set(0)
        self.bottom_slider.set(0)

        for slider in (self.frame_slider, self.range_start, self.range_end):
            slider.configure(to=max(0, maximum), state="normal")

        self.frame_slider.set(0)
        self.range_start.set(0)
        self.range_end.set(maximum)

        self.frame_label.configure(text=f"Frame 1 / {count}")
        self.range_label.configure(text=f"Rango: 1 – {count}")
        self.generate_button.configure(state="normal")
        self.progress.set(1)

        self.status_label.configure(text=f"{count} frames listos")
        self._log(
            f"✓ Video listo: {result.video_info.width}×{result.video_info.height}, "
            f"{result.video_info.duration_seconds:.1f}s, {count} frames."
        )
        self._refresh_preview()

    def _on_generated(self, output: Path) -> None:
        self._set_busy(False)
        self.status_label.configure(text="PDF generado correctamente")
        self._log(f"✓ PDF: {output}")
        messagebox.showinfo("Listo", f"El PDF se guardó en:\n{output}")

    def _on_frame_change(self, value: float) -> None:
        if not self.preparation:
            return
        index = int(round(value))
        self.frame_label.configure(
            text=f"Frame {index + 1} / {len(self.preparation.frame_paths)}"
        )
        self._refresh_preview()

    def _on_range_change(self, _value: float) -> None:
        if not self.preparation:
            return

        start = int(round(self.range_start.get()))
        end = int(round(self.range_end.get()))

        if start > end:
            if self.range_start.get() > self.range_end.get():
                self.range_start.set(end)
                start = end
            else:
                self.range_end.set(start)
                end = start

        self.range_label.configure(text=f"Rango: {start + 1} – {end + 1}")

    def _refresh_preview(self) -> None:
        if not self.preparation:
            return

        index = int(round(self.frame_slider.get()))
        source = self.preparation.frame_paths[index]

        try:
            image = Image.open(source).convert("RGB")
            draw = ImageDraw.Draw(image)
            top = int(round(self.top_slider.get()))
            bottom = int(round(self.bottom_slider.get()))

            if top:
                draw.line(
                    (0, top, image.width, top),
                    fill="#1f9aff",
                    width=max(2, image.height // 300),
                )
            if bottom:
                y = max(0, image.height - bottom)
                draw.line(
                    (0, y, image.width, y),
                    fill="#ff5c7a",
                    width=max(2, image.height // 300),
                )

            max_w, max_h = 620, 330
            ratio = min(max_w / image.width, max_h / image.height)
            display_size = (
                max(1, int(image.width * ratio)),
                max(1, int(image.height * ratio)),
            )
            source_image = image
            if image.width > 1240 or image.height > 660:
                source_image = image.resize(
                    (display_size[0] * 2, display_size[1] * 2),
                    Image.Resampling.LANCZOS,
                )

            self.preview_image = ctk.CTkImage(
                light_image=source_image,
                dark_image=source_image,
                size=display_size,
            )
            self.preview_label.configure(image=self.preview_image, text="")
            self.top_value.configure(text=f"{top} px")
            self.bottom_value.configure(text=f"{bottom} px")

        except Exception as exc:
            self._log(f"⚠ Vista previa: {exc}")

    def _set_busy(self, busy: bool) -> None:
        self.analyze_button.configure(state="disabled" if busy else "normal")
        self.source_mode_control.configure(state="disabled" if busy else "normal")
        self.generate_button.configure(
            state="disabled" if busy or not self.preparation else "normal"
        )
        self.choose_video_button.configure(
            state=(
                "disabled"
                if busy or self.source_mode == "YouTube"
                else "normal"
            )
        )
        if not busy:
            self.progress.set(1 if self.preparation else 0)

    def _reset_preparation(self) -> None:
        if self.pipeline:
            self.pipeline.close()
            self.pipeline = None
        self.preparation = None
        self.preview_image = None
        self.frame_slider.configure(state="disabled", to=1)
        self.range_start.configure(state="disabled", to=1)
        self.range_end.configure(state="disabled", to=1)
        self.generate_button.configure(state="disabled")
        self.preview_label.configure(
            image=None,
            text="Analiza un video para mostrar la vista previa.",
        )
        self.frame_label.configure(text="Frame 0 / 0")
        self.range_label.configure(text="Rango: 1 – 0")
        self.progress.set(0)
        self.status_label.configure(text="Listo para comenzar")

    def _log(self, message: str) -> None:
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")

    def _on_close(self) -> None:
        self.cancel_event.set()
        self.destroy()


def run() -> None:
    MainWindow().mainloop()
