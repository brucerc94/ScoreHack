from __future__ import annotations

import shutil
import tempfile
from pathlib import Path


class Workspace:
    """Gestiona archivos temporales de una extracción completa."""

    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="extractor_partituras_"))
        self.frames = self.root / "frames"
        self.crops = self.root / "crops"
        self.aligned = self.root / "aligned"
        self.sheets = self.root / "sheets"
        self.preview_pdf = self.root / "preview.pdf"
        self.video = self.root / "video.mp4"
        for directory in (self.frames, self.aligned, self.crops, self.sheets):
            directory.mkdir(parents=True, exist_ok=True)

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def __enter__(self) -> "Workspace":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.cleanup()
