from pathlib import Path
import tempfile

import cv2
import numpy as np
from PIL import Image

from app.core.crop import crop_frames
from app.core.deduplicator import remove_consecutive_duplicates
from app.core.pdf_exporter import export_pdf


def _write(path: Path, value: int) -> None:
    image = np.full((120, 200, 3), value, dtype=np.uint8)
    Image.fromarray(image).save(path)


def test_crop_preserves_selected_range() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        frames = root / "frames"
        crops = root / "crops"
        frames.mkdir()
        for i in range(3):
            _write(frames / f"frame_{i:05d}.jpg", 30 + i * 20)
        result = crop_frames(tuple(sorted(frames.glob("*.jpg"))), crops, 10, 20, 1, 2)
        assert len(result) == 2
        assert Image.open(result[0]).size == (200, 90)


def test_duplicate_detection_collapses_consecutive_images() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        a, b, c = root / "a.jpg", root / "b.jpg", root / "c.jpg"
        _write(a, 80)
        _write(b, 80)
        _write(c, 180)
        result = remove_consecutive_duplicates([a, b, c], threshold=0.99)
        assert result == (a, c)


def test_export_pdf_creates_file() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        images = []
        for i in range(2):
            path = root / f"{i}.jpg"
            _write(path, 60 + i * 50)
            images.append(path)
        output = root / "out.pdf"
        export_pdf(images, output, sheets_per_page=2)
        assert output.exists()
        assert output.stat().st_size > 0


def test_moving_highlight_is_removed_from_score() -> None:
    from app.core.overlay_cleaner import remove_transient_overlays

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        source = root / "crops"
        output = root / "cleaned"
        source.mkdir()

        base = np.full((220, 300, 3), 255, dtype=np.uint8)
        cv2.line(base, (20, 70), (280, 70), (0, 0, 0), 2)
        cv2.line(base, (20, 120), (280, 120), (0, 0, 0), 2)

        frames = []
        for index, x in enumerate((70, 140, 210)):
            frame = base.copy()
            cv2.rectangle(frame, (x, 20), (x + 28, 190), (180, 235, 235), -1)
            cv2.rectangle(frame, (x, 20), (x + 28, 190), (80, 100, 100), 1)
            path = source / f"frame_{index:05d}.jpg"
            assert cv2.imwrite(str(path), frame)
            frames.append(path)

        result = remove_transient_overlays(frames, output)
        assert len(result) == 3

        # En el frame intermedio la zona del cursor debe recuperar el fondo blanco
        # de los frames vecinos, conservando las líneas negras de la partitura.
        cleaned = cv2.imread(str(result[1]), cv2.IMREAD_COLOR)
        assert cleaned is not None
        assert int(cleaned[100, 154].mean()) > 220


def test_split_panorama_uses_manual_cut_points() -> None:
    from app.core.layout import split_panorama

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        source = root / "panorama.jpg"
        output = root / "segments"
        image = np.zeros((20, 100, 3), dtype=np.uint8)
        image[:, :40] = 50
        image[:, 40:75] = 120
        image[:, 75:] = 200
        assert cv2.imwrite(str(source), image)

        segments = split_panorama((source), (0.4, 0.75), output)

        assert len(segments) == 3
        assert cv2.imread(str(segments[0]), cv2.IMREAD_COLOR).shape[1] == 40
        assert cv2.imread(str(segments[1]), cv2.IMREAD_COLOR).shape[1] == 35
        assert cv2.imread(str(segments[2]), cv2.IMREAD_COLOR).shape[1] == 25


def test_horizontal_export_uses_a4_layout() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        first = root / "segment_1.jpg"
        second = root / "segment_2.jpg"
        _write(first, 80)
        Image.new("RGB", (500, 80), 160).save(second)

        output = root / "horizontal.pdf"
        export_pdf(
            [first, second],
            output,
            sheets_per_page=2,
            page_size="A4",
            layout_mode="horizontal",
        )

        assert output.exists()
        assert output.stat().st_size > 0
