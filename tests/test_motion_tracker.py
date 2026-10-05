from pathlib import Path
import tempfile

import cv2
import numpy as np

from app.core.motion_tracker import stabilize_frames


def test_motion_stabilization_cancels_translation() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        source = root / "frames"
        output = root / "aligned"
        source.mkdir()

        base = np.zeros((180, 300, 3), dtype=np.uint8)
        for x in range(20, 280, 20):
            cv2.line(base, (x, 20), (x, 160), (255, 255, 255), 2)
        for y in range(20, 170, 20):
            cv2.line(base, (20, y), (280, y), (255, 255, 255), 2)
        cv2.putText(base, "SCORE", (70, 95), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2)

        shifted_matrix = np.float32([[1, 0, 14], [0, 1, -8]])
        shifted = cv2.warpAffine(base, shifted_matrix, (300, 180))

        first = source / "frame_00000.jpg"
        second = source / "frame_00001.jpg"
        assert cv2.imwrite(str(first), base)
        assert cv2.imwrite(str(second), shifted)

        result = stabilize_frames([first, second], output)
        assert len(result) == 2

        aligned = cv2.imread(str(result[1]), cv2.IMREAD_GRAYSCALE)
        reference = cv2.imread(str(result[0]), cv2.IMREAD_GRAYSCALE)
        assert aligned is not None
        assert reference is not None

        shift, response = cv2.phaseCorrelate(
            np.float32(reference),
            np.float32(aligned),
        )
        assert response > 0.4
        assert abs(shift[0]) < 2.0
        assert abs(shift[1]) < 2.0
