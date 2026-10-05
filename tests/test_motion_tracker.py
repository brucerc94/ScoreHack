from pathlib import Path
import tempfile

import cv2
import numpy as np

from app.core.motion_tracker import stabilize_frames


def test_motion_stabilization_uses_selected_crop_as_roi() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        source = root / "frames"
        output = root / "aligned"
        source.mkdir()

        base = np.zeros((240, 300, 3), dtype=np.uint8)

        # Contenido de la partitura: ROI central (y=60..180).
        for x in range(30, 290, 20):
            cv2.line(base, (x, 60), (x, 180), (255, 255, 255), 2)
        for y in range(60, 181, 20):
            cv2.line(base, (30, y), (290, y), (255, 255, 255), 2)
        cv2.putText(
            base,
            "SCORE",
            (80, 125),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.1,
            (255, 255, 255),
            2,
        )

        # Distractores fuertes fuera del recorte. Tienen un desplazamiento distinto.
        cv2.rectangle(base, (0, 0), (299, 45), (180, 180, 180), 6)
        for x in range(0, 300, 12):
            cv2.line(base, (x, 195), (x, 239), (220, 220, 220), 4)

        score_shift = np.float32([[1, 0, 14], [0, 1, -8]])
        shifted = cv2.warpAffine(base, score_shift, (300, 240))

        # Cambiamos deliberadamente las zonas externas después del desplazamiento.
        top_shift = np.float32([[1, 0, -70], [0, 1, 0]])
        bottom_shift = np.float32([[1, 0, 65], [0, 1, 0]])
        top = cv2.warpAffine(base[0:46], top_shift, (300, 46))
        bottom = cv2.warpAffine(base[194:240], bottom_shift, (300, 46))
        shifted[0:46] = top
        shifted[194:240] = bottom

        first = source / "frame_00000.jpg"
        second = source / "frame_00001.jpg"
        assert cv2.imwrite(str(first), base)
        assert cv2.imwrite(str(second), shifted)

        result = stabilize_frames(
            [first, second],
            output,
            crop_top=50,
            crop_bottom=50,
        )
        assert len(result) == 2

        aligned = cv2.imread(str(result[1]), cv2.IMREAD_GRAYSCALE)
        reference = cv2.imread(str(result[0]), cv2.IMREAD_GRAYSCALE)
        assert aligned is not None
        assert reference is not None

        roi_reference = reference[50:190]
        roi_aligned = aligned[50:190]
        shift, response = cv2.phaseCorrelate(
            np.float32(roi_reference),
            np.float32(roi_aligned),
        )
        assert response > 0.4
        assert abs(shift[0]) < 2.0
        assert abs(shift[1]) < 2.0
