# ScoreCapture — Sheet Music Extractor

ScoreCapture extracts sheet music shown in YouTube videos or local video files and turns the captured frames into clean, printable PDF pages.

The project is designed for videos where a score is displayed on screen and the page or viewport moves as the music progresses. The workflow keeps the important decisions in the user's hands: select the frames, control each overlap, define page cuts, preview the result, then export.

## Features

- YouTube and local video input.
- Local video drag-and-drop.
- Frame extraction at a configurable interval.
- Manual frame selection in the order you want them reconstructed.
- Horizontal score reconstruction with per-join overlap control.
- Automatic overlap estimation as a suggestion, with manual correction available for every join.
- Manual page cuts directly on the reconstruction.
- A4-first PDF layout with consistent system sizing.
- Configurable number of reconstructed segments per page.
- SSIM-based consecutive duplicate removal in the individual-frame workflow.
- Background processing with progress and runtime logging.
- No administrator privileges required.

## Workflow

### 1. Select the source

Choose **YouTube** or **Local video**, provide the source, and click **Analyze video**.

### 2. Prepare the frames

Use the frame slider to inspect the extracted images. Adjust **Top crop** and **Bottom crop** so that the useful score area is visible.

### 3. Reconstruct a moving score

Switch to **Horizontal join**.

Select a frame and click **Add frame**. Continue selecting frames in the order in which they should appear.

For every consecutive pair, ScoreCapture estimates the overlap. The estimate is only a starting point: each join has its own slider so you can correct it independently.

### 4. Define page cuts

Once the horizontal reconstruction looks correct, add page cuts directly on the reconstruction or edit their positions numerically.

The application does not try to guess where a musical system should end. You decide where the reconstructed score is divided.

### 5. Preview and export

Choose how many reconstructed segments should appear on each A4 page and click **Preview**.

Review the generated PDF. Adjust the frame selection, joins, or page cuts and preview again until the layout is correct.

When satisfied, click **Generate PDF** and save the final document.

## Architecture

The project follows a modular, separation-of-concerns architecture:

```text
app/
├── core/
│   ├── crop.py
│   ├── deduplicator.py
│   ├── downloader.py
│   ├── frame_extractor.py
│   ├── layout.py
│   ├── models.py
│   ├── pdf_exporter.py
│   ├── pipeline.py
│   ├── stitcher.py
│   └── workspace.py
├── ui/
│   ├── controller.py
│   ├── launcher.py
│   └── qml/
│       ├── Main.qml
│       └── components/
└── main.py
```

The core package contains video processing and document-generation logic and has no dependency on Qt/QML UI widgets.

The UI uses **Qt 6 + QML** through PySide6.

## Requirements

- Python 3.10–3.14
- Windows is the primary packaged target.
- Internet access is required only when downloading a YouTube source.

## Run from source

### Windows

```bat
run.bat
```

The launcher creates or reuses the local virtual environment, installs missing dependencies, and starts the application.

### Manual setup

```bash
python -m venv venv
# Windows
venv\Scripts\activate

python -m pip install -r requirements.txt
python -m app.main
```

## Build a Windows executable

```bat
build_extractor.bat
```

The build script creates:

```text
dist\ExtractorPartituras.exe
```

The Qt/QML resources and yt-dlp package are collected into the executable.

## Tests

Run the test suite with:

```bash
python -m pytest -q
```

GitHub Actions also runs the test suite on Python 3.10 and 3.12 for pushes and pull requests.

## Design principles

ScoreCapture intentionally favors deterministic, user-controlled reconstruction over opaque automatic editing.

Automatic overlap detection is useful when it works, but it can be ambiguous on dense musical notation. For that reason, the user can override every join.

Page composition is also explicit. A4 is treated as the final document canvas, while the reconstructed score is divided into user-defined systems before export.

## Limitations

- The application captures sheet music as raster images; it does not recognize notes.
- It does not generate MusicXML, MIDI, or other semantic music formats.
- Automatic overlap detection is an assistive estimate, not a guarantee.
- PDF quality depends on the resolution and clarity of the source video.

## Project status

ScoreCapture is a focused desktop utility for reconstructing on-screen sheet music into printable PDFs.

Version: **3.0.0**

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
