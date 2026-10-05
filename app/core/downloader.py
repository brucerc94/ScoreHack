from __future__ import annotations

from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import yt_dlp

ProgressCallback = Callable[[float, str], None]


def is_youtube_url(value: str) -> bool:
    try:
        host = urlparse(value).netloc.lower().split(":")[0]
    except ValueError:
        return False
    return host in {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"}


def download_youtube(url: str, output_path: Path, on_progress: ProgressCallback | None = None) -> Path:
    if not is_youtube_url(url):
        raise ValueError("La URL no parece ser un enlace válido de YouTube.")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    def progress_hook(data: dict) -> None:
        if on_progress is None:
            return
        if data.get("status") == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
            downloaded = data.get("downloaded_bytes", 0)
            progress = downloaded / total if total else 0.0
            on_progress(progress, "Descargando video de YouTube…")
        elif data.get("status") == "finished":
            on_progress(1.0, "Descarga completada.")

    options = {
        "format": "best[ext=mp4]/best",
        "outtmpl": str(output_path),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [progress_hook],
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as exc:
        raise RuntimeError(f"No se pudo descargar el video: {exc}") from exc

    if not output_path.exists():
        raise RuntimeError("yt-dlp terminó sin generar el archivo de video.")
    return output_path
