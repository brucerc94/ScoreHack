from pathlib import Path
import tempfile

import cv2
import numpy as np

from app.core.stitcher import stitch_horizontal


def test_horizontal_stitch_reconstructs_overlapping_frames() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        source = root / "frames"
        output = root / "montage.jpg"
        source.mkdir()

        canvas = np.full((220, 900, 3), 255, dtype=np.uint8)
        for x in range(20, 880, 30):
            cv2.line(canvas, (x, 30), (x, 190), (0, 0, 0), 1)
        for y in (80, 110, 140):
            cv2.line(canvas, (20, y), (880, y), (0, 0, 0), 1)
        cv2.putText(
            canvas,
            "SCORE",
            (180, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 0, 0),
            2,
        )
        cv2.putText(
            canvas,
            "Bb7sus4",
            (520, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 0, 0),
            2,
        )

        first = source / "frame_00000.jpg"
        second = source / "frame_00001.jpg"
        assert cv2.imwrite(str(first), canvas[:, 0:600])
        assert cv2.imwrite(str(second), canvas[:, 300:900])

        result = stitch_horizontal([first, second], output)

        stitched = cv2.imread(str(result), cv2.IMREAD_COLOR)
        assert stitched is not None
        assert stitched.shape[0] == 220
        assert 285 <= result.auto_overlaps[0] <= 315
        assert result.effective_overlaps == result.auto_overlaps
        assert 880 <= stitched.shape[1] <= 920


def test_horizontal_stitch_accepts_manual_overlap() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        source = root / "frames"
        output = root / "manual.jpg"
        source.mkdir()

        canvas = np.full((160, 800, 3), 255, dtype=np.uint8)
        for x in range(20, 780, 25):
            cv2.line(canvas, (x, 20), (x, 140), (0, 0, 0), 2)
        cv2.putText(canvas, "PARTITURA", (260, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

        first = source / "frame_00000.jpg"
        second = source / "frame_00001.jpg"
        assert cv2.imwrite(str(first), canvas[:, 0:500])
        assert cv2.imwrite(str(second), canvas[:, 250:750])

        result = stitch_horizontal(
            [first, second],
            output,
            overlap_overrides=(180,),
        )

        stitched = cv2.imread(str(result.output_path), cv2.IMREAD_COLOR)
        assert stitched is not None
        assert result.auto_overlaps[0] > 0
        assert result.effective_overlaps == (180,)
        assert stitched.shape[1] == 820
