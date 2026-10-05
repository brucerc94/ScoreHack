<div align="center">

<img src="./icon.ico" alt="ScoreCapture icon" width="96">

# ScoreCapture

### Reconstruct sheet music from video into printable A4 PDFs

<p><strong>Extract → Select → Reconstruct → Cut → Preview → Export</strong></p>

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Qt](https://img.shields.io/badge/Qt-6-41CD52?logo=qt&logoColor=white)](https://www.qt.io/)
[![PySide6](https://img.shields.io/badge/PySide6-6.11-41CD52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-5C3EE8?logo=opencv&logoColor=white)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/brucerc94/ExtractorPartiturasYoutube/tests.yml?branch=main&label=CI)](.github/workflows/tests.yml)

ScoreCapture is a Windows-focused desktop application for turning sheet music displayed in YouTube videos or local video files into clean, printable PDF pages.

It is designed for videos where the score moves across the screen as the music progresses. The application keeps the important visual decisions in the user's hands: frame selection, overlap, page cuts, and final A4 composition.

</div>

---

## What ScoreCapture Does

Many sheet-music videos do not contain independent pages. Instead, the viewer sees a moving viewport over one long score.

ScoreCapture turns that into a controlled reconstruction workflow:

~~~text
Video
  ↓
Frame extraction
  ↓
Crop the score area
  ↓
Select useful frames
  ↓
Reconstruct horizontally
  ↓
Adjust frame-to-frame joins
  ↓
Place page cuts
  ↓
Preview the A4 document
  ↓
Export PDF
~~~

The result is a raster-based PDF intended for printing or archiving.

---

## Highlights

| Capability | Description |
| --- | --- |
| YouTube input | Download a source video through yt-dlp |
| Local video | Open common video formats directly |
| Frame extraction | Sample the video at a configurable interval |
| Cropping | Control top and bottom crop independently |
| Frame selection | Build the reconstruction manually and in order |
| Reconstruction | Join frames horizontally into one score |
| Join control | Adjust every frame pair independently |
| Auto alignment | Use automatic overlap estimation as a starting point |
| Page cuts | Add and drag manual page boundaries |
| A4 output | Compose the final document on a fixed A4 canvas |
| Preview | Review the document before final export |
| Windows workflow | Run or build with the included batch scripts |

---

# Step-by-Step User Guide

## 1. Start the application

### Windows

Run:

~~~text
run.bat
~~~

The launcher creates or reuses the virtual environment, installs missing dependencies, and starts ScoreCapture.

For developers who prefer to run the project manually:

~~~text
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python -m app.main
~~~

---

## 2. Select your video

At the top of the application you will find the source selector.

### YouTube

1. Select **YouTube**.
2. Paste the video URL.
3. Click **Analyze video**.
4. Wait until the frames are extracted.

### Local video

1. Select **Local video**.
2. Click **Browse**, or drag the video into the drop area.
3. Confirm that the filename is displayed.
4. Click **Analyze video**.

Supported local containers include common formats such as MP4, MKV, AVI, MOV, WEBM, and M4V.

---

## 3. Choose the frame interval

The **Frame interval** determines how often ScoreCapture samples the video.

Examples:

~~~text
0.5 sec → more frames
1.0 sec → balanced starting point
2.0 sec → fewer frames
~~~

Use a smaller interval when the score moves quickly or when each frame contains only a small amount of new information.

Use a larger interval when the score changes slowly and you want fewer frames to review.

---

## 4. Crop the video to the score area

The **Crop** section has two independent controls:

- **Top** — removes pixels from the top.
- **Bottom** — removes pixels from the bottom.

Use them to remove video controls, borders, empty space, or other material that is not part of the score.

The objective is to leave only the useful sheet-music area.

~~~text
┌──────────────────────────────────────┐
│              SHEET MUSIC             │
│                                      │
│       musical notation and score     │
│                                      │
└──────────────────────────────────────┘
~~~

These crop values are applied when the selected frames are processed.

---

## 5. Inspect the extracted frames

Use the frame slider in the main workspace to move through the extracted frames.

Look for frames that:

- contain a useful portion of the score,
- overlap with the previous portion,
- continue the score in the correct direction,
- do not contain unnecessary transitions or unrelated video content.

This is where you decide which frames should form the final reconstruction.

---

## 6. Switch to Horizontal Join

For videos where the score moves sideways, open **Mode** and choose:

**Horizontal join**

The reconstruction workspace becomes available.

This mode is intended for a moving viewport over a longer score, rather than independent complete pages.

---

## 7. Select the frames

Find the first useful frame and click:

**Add frame**

Move to the next useful frame and add it.

Continue in the order in which the score should appear.

Example:

~~~text
Frame 12
   ↓
Frame 18
   ↓
Frame 25
   ↓
Frame 31
   ↓
Frame 39
~~~

The selected frames appear in the frame strip.

### Important

Selection order matters. The reconstruction follows the order you selected.

---

## 8. Adjust the joins

Every adjacent frame pair has its own join.

For example:

~~~text
Frame 12 → Frame 18   Join 1
Frame 18 → Frame 25   Join 2
Frame 25 → Frame 31   Join 3
Frame 31 → Frame 39   Join 4
~~~

Each join has a separate overlap value.

~~~text
Join 1 → 120 px
Join 2 → 185 px
Join 3 →  96 px
Join 4 → 160 px
~~~

This is important because the correct overlap can change from one frame pair to another.

### Automatic overlap

ScoreCapture can estimate the overlap automatically.

Treat that value as a suggestion. Repeated musical notation and similar visual patterns can make image matching ambiguous.

### Manual overlap

Use the slider belonging to the specific join that looks incorrect.

Each join is independent, so correcting Join 3 does not alter Join 1, Join 2, or Join 4.

The join list keeps its scroll position while you edit long sequences.

---

## 9. Verify the horizontal reconstruction

The reconstruction preview shows the selected frames as one continuous score.

Scroll horizontally and inspect the entire result.

Look for:

- duplicated notes,
- doubled clefs,
- visible seams,
- incorrect overlaps,
- missing portions,
- frames that should be removed.

Correct the individual joins until the continuous score looks right.

Do not move to page layout until the reconstruction itself is correct.

---

## 10. Add page cuts

Once the reconstruction is correct, decide where the long score should be divided into printable systems.

Click:

**Add cut here**

A cut marker is added to the reconstruction.

You can drag the marker directly over the score.

~~~text
──────────────────────────────────────────────────────────────
                     │                    │
                   Cut 1                Cut 2
                     │                    │
──────────────────────────────────────────────────────────────
~~~

You can also edit cut positions numerically in the **Score layout** section.

### Why are cuts manual?

ScoreCapture does not try to guess the musical meaning of every system. You decide where each printable section should begin and end.

This makes the final result predictable.

---

## 11. Choose how many systems go on each A4 page

In **Score layout**, choose the number of reconstructed segments per page.

For example:

~~~text
1 system / page
2 systems / page
3 systems / page
4 systems / page
~~~

The final document uses a fixed **A4 canvas**.

Score systems keep their proportions and are scaled together when necessary.

---

## 12. Preview the PDF

Click:

**Preview**

Preview uses the current:

- selected frames,
- crop,
- join overlaps,
- page cuts,
- page distribution,
- A4 layout.

A typical iteration is:

~~~text
Adjust
  ↓
Preview
  ↓
Inspect
  ↓
Adjust again
  ↓
Preview again
~~~

Repeat until the composition looks correct.

---

## 13. Generate the final PDF

When the preview looks correct:

1. Click **Generate PDF**.
2. Select the destination.
3. Save the document.

The exported PDF uses the same reconstruction and layout settings that you reviewed in Preview.

---

# Recommended Workflow

For the most reliable results:

1. Analyze the video.
2. Set the crop.
3. Inspect the frame timeline.
4. Switch to Horizontal join.
5. Select only useful frames.
6. Correct every join.
7. Inspect the complete reconstruction.
8. Add page cuts.
9. Select systems per A4 page.
10. Preview.
11. Fine-tune.
12. Generate the final PDF.

---

# Architecture

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
├── test_core.py
└── test_stitcher.py
~~~

The processing core is independent from the QML presentation layer.

---

# Development

## Requirements

- Python 3.10+
- Windows is the primary packaged target
- Internet access is required only for YouTube downloads

## Run

~~~text
run.bat
~~~

## Build

~~~text
build_extractor.bat
~~~

The generated executable is:

~~~text
dist\ExtractorPartituras.exe
~~~

## Test

~~~text
python -m pytest -q
~~~

GitHub Actions runs the automated test suite on Python 3.10 and 3.12.

---

# Design Principles

### User controlled

Automatic processing assists the workflow but does not make irreversible visual decisions for the user.

### Explicit reconstruction

Every selected frame and every overlap remains visible and editable.

### Explicit page composition

The user decides where the score is divided into systems and how those systems are distributed across A4 pages.

### Predictable export

Preview and final PDF generation use the same current layout configuration.

---

# Limitations

- ScoreCapture extracts sheet music as raster images.
- It does not recognize notes, chords, lyrics, or musical symbols.
- It does not generate MusicXML or MIDI.
- Automatic overlap detection is an assistive estimate and may require manual correction.
- Final quality depends on the source video's resolution, compression, and clarity.

---

# Legal

Only process and download video content you are authorized to use.

YouTube content remains subject to the rights of its owners and to YouTube's applicable terms and policies.

---

# Release

**Version 3.0.0**

See [CHANGELOG.md](CHANGELOG.md) for release notes.

# License

Released under the [MIT License](LICENSE).

---

<div align="center">

**ScoreCapture**  
Qt 6 · QML · Python · OpenCV

</div>
