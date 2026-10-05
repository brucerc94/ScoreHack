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
        raise ValueError("The URL does not look like a valid YouTube link.")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    def progress_hook(data: dict) -> None:
        if on_progress is None:
            return
        if data.get("status") == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
            downloaded = data.get("downloaded_bytes", 0)
            progress = downloaded / total if total else 0.0
            on_progress(progress, "Downloading YouTube video…")
        elif data.get("status") == "finished":
            on_progress(1.0, "Download completed.")

    options = {
        "format": "best[ext=mp4]/best",
        "outtmpl": str(output_path.with_suffix(".%(ext)s")),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [progress_hook],
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as exc:
        raise RuntimeError(f"Could not download the video: {exc}") from exc

    candidates = sorted(
        output_path.parent.glob(f"{output_path.stem}.*"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    for candidate in candidates:
        if candidate.suffix not in {".part", ".ytdl"} and candidate.is_file():
            return candidate

    raise RuntimeError("yt-dlp finished without producing a video file.")
