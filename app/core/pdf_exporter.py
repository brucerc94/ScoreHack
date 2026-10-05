from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image
from fpdf import FPDF

_PAGE_SIZES = {
    "A4": (595.28, 841.89),
    "A4_LANDSCAPE": (841.89, 595.28),
    "LETTER": (612.0, 792.0),
    "LETTER_LANDSCAPE": (792.0, 612.0),
}


def _fit_size(
    width: int,
    height: int,
    box_width: float,
    box_height: float,
) -> tuple[float, float]:
    scale = min(box_width / width, box_height / height)
    return width * scale, height * scale


def _image_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.size


def _draw_individual_pages(
    pdf: FPDF,
    paths: Sequence[Path],
    sheets_per_page: int,
    page_width: float,
    page_height: float,
    margin_pt: float,
) -> None:
    usable_width = page_width - 2 * margin_pt
    usable_height = page_height - 2 * margin_pt
    slot_height = usable_height / sheets_per_page

    for page_start in range(0, len(paths), sheets_per_page):
        group = paths[page_start : page_start + sheets_per_page]
        pdf.add_page()

        for slot, image_path in enumerate(group):
            width, height = _image_size(image_path)
            draw_width, draw_height = _fit_size(
                width,
                height,
                usable_width,
                max(1.0, slot_height - 8),
            )
            x = margin_pt + (usable_width - draw_width) / 2
            y = margin_pt + slot * slot_height + (slot_height - draw_height) / 2
            pdf.image(
                str(image_path),
                x=x,
                y=y,
                w=draw_width,
                h=draw_height,
            )


def _horizontal_page_scale(
    sizes: Sequence[tuple[int, int]],
    usable_width: float,
    usable_height: float,
) -> float:
    group = sizes[:segments_per_page]
    if not group:
        return 1.0

    natural_heights = [
        usable_width * height / width
        for width, height in group
    ]
    total_height = sum(natural_heights)
    if len(group) > 1:
        total_height += 10.0 * (len(group) - 1)

    return min(1.0, usable_height / max(1.0, total_height))


def _draw_horizontal_pages(
    pdf: FPDF,
    paths: Sequence[Path],
    segments_per_page: int,
    page_width: float,
    page_height: float,
    margin_pt: float,
) -> None:
    """
    Acomoda segmentos de una reconstrucción como sistemas musicales dentro
    de una hoja A4 vertical.

    Cada sistema usa el mismo ancho útil. Si el conjunto no entra en una hoja,
    todos se reducen proporcionalmente para conservar una composición uniforme.
    """
    if not paths:
        return

    usable_width = page_width - 2 * margin_pt
    usable_height = page_height - 2 * margin_pt
    sizes = [_image_size(path) for path in paths]

    for page_start in range(0, len(paths), segments_per_page):
        group = paths[page_start : page_start + segments_per_page]
        group_sizes = sizes[page_start : page_start + segments_per_page]
        scale = _horizontal_page_scale(
            group_sizes,
            usable_width,
            usable_height,
        )

        system_width = usable_width * scale
        natural_heights = [
            system_width * height / width
            for width, height in group_sizes
        ]
        gap = 10.0 * scale
        content_height = sum(natural_heights) + max(0, len(group) - 1) * gap
        top = margin_pt + (usable_height - content_height) / 2

        pdf.add_page()

        for image_path, height in zip(group, natural_heights):
            x = margin_pt + (usable_width - system_width) / 2
            pdf.image(
                str(image_path),
                x=x,
                y=top,
                w=system_width,
                h=height,
            )
            top += height + gap


def export_pdf(
    image_paths: Iterable[Path],
    output_pdf: Path,
    sheets_per_page: int = 4,
    page_size: str = "A4",
    margin_pt: float = 28.0,
    layout_mode: str = "individual",
) -> Path:
    paths = list(image_paths)
    if not paths:
        raise ValueError("No hay partituras únicas para exportar.")
    if not 1 <= sheets_per_page <= 8:
        raise ValueError("Las partituras por página deben estar entre 1 y 8.")
    if layout_mode not in {"individual", "horizontal"}:
        raise ValueError(f"Modo de layout no soportado: {layout_mode}")

    page_key = page_size.upper()
    if page_key not in _PAGE_SIZES:
        raise ValueError(f"Tamaño de página no soportado: {page_size}")

    # ScoreCapture trabaja siempre sobre A4 para que el resultado impreso sea
    # predecible. Los tamaños alternativos se mantienen en la API por compatibilidad.
    page_width, page_height = _PAGE_SIZES[page_key]

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf = FPDF(unit="pt", format=(page_width, page_height))
    pdf.set_auto_page_break(False)

    if layout_mode == "horizontal":
        _draw_horizontal_pages(
            pdf,
            paths,
            sheets_per_page,
            page_width,
            page_height,
            margin_pt,
        )
    else:
        _draw_individual_pages(
            pdf,
            paths,
            sheets_per_page,
            page_width,
            page_height,
            margin_pt,
        )

    pdf.output(str(output_pdf))
    return output_pdf
