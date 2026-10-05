from __future__ import annotations

import math
from pathlib import Path
from threading import Event
from typing import Callable, Iterable

import cv2
import numpy as np

ProgressCallback = Callable[[float, str], None]


def _resize_for_motion(image: np.ndarray, max_width: int = 640) -> tuple[np.ndarray, float]:
    height, width = image.shape[:2]
    if width <= max_width:
        return image, 1.0
    scale = max_width / width
    resized = cv2.resize(
        image,
        (max_width, max(1, int(round(height * scale)))),
        interpolation=cv2.INTER_AREA,
    )
    return resized, scale


def _motion_region(image: np.ndarray, crop_top: int, crop_bottom: int) -> np.ndarray:
    height = image.shape[0]
    if crop_top < 0 or crop_bottom < 0:
        raise ValueError("Los recortes no pueden ser negativos.")
    if crop_top + crop_bottom >= height:
        raise ValueError("El recorte superior + inferior debe dejar una imagen visible.")
    return image[crop_top : height - crop_bottom, :]


def _estimate_translation(
    reference: np.ndarray,
    current: np.ndarray,
) -> tuple[float, float, float]:
    reference_small, scale = _resize_for_motion(reference)
    current_small, _ = _resize_for_motion(current)

    reference_gray = cv2.cvtColor(reference_small, cv2.COLOR_BGR2GRAY)
    current_gray = cv2.cvtColor(current_small, cv2.COLOR_BGR2GRAY)

    reference_gray = cv2.GaussianBlur(reference_gray, (5, 5), 0)
    current_gray = cv2.GaussianBlur(current_gray, (5, 5), 0)

    window = cv2.createHanningWindow(
        (reference_gray.shape[1], reference_gray.shape[0]),
        cv2.CV_32F,
    )
    shift, response = cv2.phaseCorrelate(
        np.float32(reference_gray),
        np.float32(current_gray),
        window,
    )
    return shift[0] / scale, shift[1] / scale, float(response)


def _estimate_affine(
    reference: np.ndarray,
    current: np.ndarray,
    max_shift_px: float,
) -> np.ndarray | None:
    reference_small, scale = _resize_for_motion(reference)
    current_small, _ = _resize_for_motion(current)

    reference_gray = cv2.cvtColor(reference_small, cv2.COLOR_BGR2GRAY)
    current_gray = cv2.cvtColor(current_small, cv2.COLOR_BGR2GRAY)

    orb = cv2.ORB_create(nfeatures=1200)
    ref_keypoints, ref_descriptors = orb.detectAndCompute(reference_gray, None)
    cur_keypoints, cur_descriptors = orb.detectAndCompute(current_gray, None)
    if ref_descriptors is None or cur_descriptors is None:
        return None
    if len(ref_keypoints) < 8 or len(cur_keypoints) < 8:
        return None

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    matches = matcher.knnMatch(cur_descriptors, ref_descriptors, k=2)

    good = [
        first
        for first, second in matches
        if first.distance < 0.75 * second.distance
    ]
    if len(good) < 8:
        return None

    src = np.float32([cur_keypoints[m.queryIdx].pt for m in good])
    dst = np.float32([ref_keypoints[m.trainIdx].pt for m in good])

    matrix, inliers = cv2.estimateAffinePartial2D(
        src,
        dst,
        method=cv2.RANSAC,
        ransacReprojThreshold=3.0,
    )
    if matrix is None or inliers is None:
        return None

    inlier_count = int(inliers.ravel().sum())
    if inlier_count < 6:
        return None

    matrix = matrix.astype(np.float32)
    matrix[:, 2] /= scale

    scale_factor = math.hypot(float(matrix[0, 0]), float(matrix[0, 1]))
    rotation = math.degrees(math.atan2(float(matrix[1, 0]), float(matrix[0, 0])))
    tx = float(matrix[0, 2])
    ty = float(matrix[1, 2])

    if not 0.85 <= scale_factor <= 1.15:
        return None
    if abs(rotation) > 15.0:
        return None
    if max(abs(tx), abs(ty)) > max_shift_px:
        return None

    return matrix


def _write_image(target: Path, image: np.ndarray) -> None:
    if not cv2.imwrite(
        str(target),
        image,
        [cv2.IMWRITE_JPEG_QUALITY, 95],
    ):
        raise RuntimeError(f"No se pudo guardar {target.name}.")


def stabilize_frames(
    frame_paths: Iterable[Path],
    output_dir: Path,
    crop_top: int = 0,
    crop_bottom: int = 0,
    max_shift_px: int = 240,
    min_phase_response: float = 0.05,
    on_progress: ProgressCallback | None = None,
    cancel_event: Event | None = None,
) -> tuple[Path, ...]:
    """
    Corrige desplazamientos usando SOLO la zona útil de la partitura.

    El recorte se utiliza como región de interés para detectar movimiento, pero la
    transformación resultante se aplica al frame completo. Así, el usuario puede
    analizar primero el video, ajustar el recorte y recién después ejecutar el
    seguimiento sobre la zona correcta.

    Se intenta primero correlación de fase para traslaciones. Si la señal es
    débil, se usa ORB + transformación afín como respaldo. Cuando no hay una
    correspondencia confiable, se conserva el frame y se inicia un nuevo segmento.
    """
    paths = list(frame_paths)
    if not paths:
        return ()
    if max_shift_px <= 0:
        raise ValueError("max_shift_px debe ser mayor que 0.")
    if not 0.0 < min_phase_response <= 1.0:
        raise ValueError("min_phase_response debe estar entre 0 y 1.")

    output_dir.mkdir(parents=True, exist_ok=True)
    output: list[Path] = []
    reference: np.ndarray | None = None

    for index, source in enumerate(paths):
        if cancel_event and cancel_event.is_set():
            raise InterruptedError("Proceso cancelado por el usuario.")

        current = cv2.imread(str(source), cv2.IMREAD_COLOR)
        if current is None:
            raise RuntimeError(f"No se pudo leer {source.name}.")

        current_roi = _motion_region(current, crop_top, crop_bottom)
        aligned = current
        message = "Siguiendo movimiento en el recorte…"

        if reference is None:
            reference = current_roi.copy()
        else:
            dx, dy, response = _estimate_translation(reference, current_roi)
            shift_ok = (
                math.isfinite(dx)
                and math.isfinite(dy)
                and max(abs(dx), abs(dy)) <= max_shift_px
                and response >= min_phase_response
            )

            if shift_ok:
                matrix = np.float32([[1.0, 0.0, -dx], [0.0, 1.0, -dy]])
                aligned = cv2.warpAffine(
                    current,
                    matrix,
                    (current.shape[1], current.shape[0]),
                    flags=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_REFLECT101,
                )
            else:
                affine = _estimate_affine(reference, current_roi, max_shift_px)
                if affine is not None:
                    aligned = cv2.warpAffine(
                        current,
                        affine,
                        (current.shape[1], current.shape[0]),
                        flags=cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_REFLECT101,
                    )
                else:
                    reference = current_roi.copy()
                    message = "Nuevo segmento detectado…"

        target = output_dir / source.name
        _write_image(target, aligned)
        output.append(target)

        if on_progress:
            on_progress((index + 1) / len(paths), message)

    return tuple(output)
