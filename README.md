<div align="center">

# ScoreCapture

### Reconstruct sheet music from video into printable A4 PDFs

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Qt](https://img.shields.io/badge/Qt-6-41CD52?logo=qt&logoColor=white)](https://www.qt.io/)
[![PySide6](https://img.shields.io/badge/PySide6-6.11-41CD52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-5C3EE8?logo=opencv&logoColor=white)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/brucerc94/ExtractorPartiturasYoutube/tests.yml?branch=main&label=CI)](.github/workflows/tests.yml)

ScoreCapture is a Windows-focused desktop application for turning on-screen sheet music from **YouTube videos or local video files** into clean, printable PDF pages.

It is built for a common real-world case: the score is visible in a video, but the viewport moves as the music progresses. Instead of guessing the final layout, ScoreCapture gives the user precise control over **frame selection, overlap, page cuts, and A4 pagination**.

</div>

---

## Why ScoreCapture?

Many sheet-music videos are not a sequence of ready-to-print pages. The camera or screen viewport can move sideways, frames can overlap, and the useful score area can occupy only part of the video.

ScoreCapture treats the task as a reconstruction workflow:

**Video → Frames → Crop → Select → Reconstruct → Cut → Preview → A4 PDF**

The important decisions remain explicit and editable.

---

## Features

### Capture

- **YouTube input** through yt-dlp
- **Local video input**
- Local video **drag & drop**
- Configurable frame extraction interval
- Frame-by-frame preview

### Reconstruction

- Manual frame selection in the exact order you want
- Horizontal reconstruction for moving scores
- **Independent overlap control for every frame pair**
- Automatic overlap estimation as an assistive suggestion
- Manual override whenever automatic detection is unreliable
- Horizontal preview with navigation

### Page layout

- Manual page-cut editing directly on the reconstruction
- Draggable visual cut markers
- Numeric cut controls
- User-defined segments per page
- **A4 as the final document canvas**
- Consistent system sizing across a page
- Explicit preview before final PDF generation

### Application

- Qt 6 + QML interface
- Background processing
- Progress reporting and runtime logging
- Temporary workspace with no administrator privileges
- Modular Python architecture
- Automated tests with GitHub Actions

---

## Workflow

| Step | What you do | Result |
| --- | --- | --- |
| **1. Source** | Choose YouTube or a local video | Video is loaded |
| **2. Analyze** | Extract frames at the selected interval | Frame timeline becomes available |
| **3. Crop** | Set the top and bottom crop | Only the useful score area is kept |
| **4. Select** | Add the frames that belong to the score | Ordered frame sequence |
| **5. Reconstruct** | Adjust each join's overlap | Continuous horizontal score |
| **6. Cut** | Place page cuts where you want them | User-defined score systems |
| **7. Preview** | Choose the number of systems per A4 page | Review the final document layout |
| **8. Export** | Generate the PDF | Printable A4 score |

---

## The reconstruction model

A moving score typically looks like this:

~~~text
Frame 01      Frame 02      Frame 03      Frame 04
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│         │   │         │   │         │   │         │
│  SCORE  │───│  SCORE  │───│  SCORE  │───│  SCORE  │
│         │   │         │   │         │   │         │
└─────────┘   └─────────┘   └─────────┘   └─────────┘
       ↑             ↑             ↑
     Join 1        Join 2        Join 3
~~~

Each join has its own overlap value:

~~~text
Join 1 → 120 px
Join 2 → 185 px
Join 3 →  96 px
~~~

This is intentional: the correct overlap can change from one frame pair to another.

---

## Manual page layout

The reconstruction is treated as a long horizontal source image. You decide where it should be divided.

~~~text
Horizontal reconstruction
───────────────────────────────────────────────────────────────
                 │                     │                 │
                 │                     │                 │
              Cut 1                 Cut 2             Cut 3
                 │                     │                 │
───────────────────────────────────────────────────────────────
~~~

You can drag the visual cut markers or edit their positions numerically.

Then ScoreCapture places the resulting systems onto fixed **A4 pages**:

~~~text
┌──────────────────────────────┐
│                              │
│  System 1                    │
│                              │
│  System 2                    │
│                              │
│  System 3                    │
│                              │
└──────────────────────────────┘
~~~

The application does not attempt to interpret the music itself. You remain in control of where the score is divided.

---

## Architecture

The codebase follows a separation-of-concerns approach:

~~~text
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
│
├── ui/
│   ├── controller.py
│   ├── launcher.py
│   └── qml/
│       ├── Main.qml
│       └── components/
│
└── main.py

tests/
└── test_core.py
~~~

### Core

The core package contains video acquisition, frame extraction, cropping, duplicate detection, reconstruction, page layout, and PDF generation.

### UI

The interface is built with **Qt 6 + QML** using PySide6. Heavy processing is kept outside the UI layer.

---

## Installation

### Requirements

- Python **3.10 or newer**
- Windows recommended for the packaged workflow
- Internet access only when using a YouTube source

### Run from source

~~~bat
run.bat
~~~

The launcher creates or reuses the virtual environment, installs the required dependencies, and starts ScoreCapture.

### Manual setup

~~~bash
python -m venv venv
~~~

Windows:

~~~bat
venv\Scripts\activate
python -m pip install -r requirements.txt
python -m app.main
~~~

---

## Build

Create the Windows executable with:

~~~bat
build_extractor.bat
~~~

Output:

~~~text
dist\ExtractorPartituras.exe
~~~

The build process bundles the Qt/QML resources and the application dependencies.

---

## Testing

Run the test suite locally:

~~~bash
python -m pytest -q
~~~

GitHub Actions runs the test suite on Python 3.10 and 3.12.

---

## Design decisions

### User-controlled reconstruction

Automatic overlap detection is deliberately assistive rather than authoritative. Dense notation, repeated symbols, and similar musical passages can make purely automatic alignment ambiguous.

### A4-first output

The final document is composed on a fixed A4 canvas. Reconstructed score systems share a consistent width and are scaled together when needed.

### Explicit preview

ScoreCapture does not silently rebuild the final document whenever a setting changes. The user adjusts the reconstruction and layout, presses **Preview**, checks the result, and then exports.

---

## Limitations

- ScoreCapture captures sheet music as raster images.
- It does **not** recognize notes, chords, or musical symbols.
- It does **not** generate MusicXML, MIDI, or other semantic music formats.
- Automatic overlap detection is an assistive estimate and may require manual correction.
- Final quality depends on the resolution, compression, and clarity of the source video.

---

## Legal note

Only download or process video content you are authorized to use. YouTube content remains subject to the rights of its owners and to YouTube's applicable terms.

---

## Release

**Current version:** 3.0.0

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## License

Released under the [MIT License](LICENSE).

---

<div align="center">

**ScoreCapture** · Qt 6 · QML · Python · OpenCV

</div>
