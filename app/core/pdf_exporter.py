from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image
from fpdf import FPDF

_PAGE_SIZES = {
    "A4": (595.28, 841.89),
    "A4_LANDSCAPE": (841.89, 595.28),
    "LETTER": (612.0, 792.0),
    "LETTER_LANDSCAPE": (792.0, 612.0),
}


def _fit_size(width: int, height: int, box_width: float, box_height: float) -> tuple[float, float]:
    scale = min(box_width / width, box_height / height)
    return width * scale, height * scale


def export_pdf(
    image_paths: Iterable[Path],
    output_pdf: Path,
    sheets_per_page: int = 4,
    page_size: str = "A4",
    margin_pt: float = 28.0,
) -> Path:
    paths = list(image_paths)
    if not paths:
        raise ValueError("No hay partituras únicas para exportar.")
    if not 1 <= sheets_per_page <= 8:
        raise ValueError("Las partituras por página deben estar entre 1 y 8.")

    page_key = page_size.upper()
    if page_key not in _PAGE_SIZES:
        raise ValueError(f"Tamaño de página no soportado: {page_size}")

    page_width, page_height = _PAGE_SIZES[page_key]
    usable_width = page_width - 2 * margin_pt
    usable_height = page_height - 2 * margin_pt
    slot_height = usable_height / sheets_per_page

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf = FPDF(unit="pt", format=(page_width, page_height))
    pdf.set_auto_page_break(False)

    for page_start in range(0, len(paths), sheets_per_page):
        group = paths[page_start : page_start + sheets_per_page]
        pdf.add_page()
        for slot, image_path in enumerate(group):
            with Image.open(image_path) as image:
                width, height = image.size
            draw_width, draw_height = _fit_size(width, height, usable_width, max(1.0, slot_height - 8))
            x = margin_pt + (usable_width - draw_width) / 2
            y = margin_pt + slot * slot_height + (slot_height - draw_height) / 2
            pdf.image(str(image_path), x=x, y=y, w=draw_width, h=draw_height)

    pdf.output(str(output_pdf))
    return output_pdf
