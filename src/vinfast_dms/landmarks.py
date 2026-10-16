"""Adapter đồng bộ cho MediaPipe Tasks Face Landmarker."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import cv2
import numpy as np


class LandmarkerError(RuntimeError):
    """Không thể khởi tạo hoặc dùng Face Landmarker."""


@dataclass(frozen=True, slots=True)
class LandmarkResult:
    faces: tuple[np.ndarray, ...]
    reason: str | None = None

    @property
    def face_count(self) -> int:
        return len(self.faces)


class Landmarker(Protocol):
    def detect_bgr(self, frame: np.ndarray, timestamp_ms: int) -> LandmarkResult: ...

    def close(self) -> None: ...


def normalized_to_pixels(points: np.ndarray, width: int, height: int) -> np.ndarray:
    """Đổi mốc chuẩn hóa sang pixel; z giữ nguyên dạng chuẩn hóa của model."""
    points = np.asarray(points, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] < 2:
        raise ValueError("Landmark cần có dạng N×2 hoặc N×3.")
    if width < 1 or height < 1:
        raise ValueError("Chiều rộng và chiều cao phải lớn hơn 0.")
    pixels = points.copy()
    pixels[:, 0] *= width
    pixels[:, 1] *= height
    return pixels


class MediaPipeLandmarker:
    """Một phiên FaceLandmarker VIDEO; không giữ ảnh hoặc video trên đĩa."""

    def __init__(
        self,
        model_path: str | Path,
        max_faces: int = 2,
        min_detection_confidence: float = 0.5,
        min_presence_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        path = Path(model_path).expanduser()
        if not path.is_file():
            raise LandmarkerError(
                f"Thiếu model Face Landmarker: {path}. "
                "Tải bằng `python scripts/download_model.py`."
            )
        if max_faces < 1:
            raise ValueError("max_faces phải lớn hơn hoặc bằng 1.")
        try:
            import mediapipe as mp

            options = mp.tasks.vision.FaceLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=str(path)),
                running_mode=mp.tasks.vision.RunningMode.VIDEO,
                num_faces=max_faces,
                min_face_detection_confidence=min_detection_confidence,
                min_face_presence_confidence=min_presence_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )
            self._mp = mp
            self._landmarker = mp.tasks.vision.FaceLandmarker.create_from_options(options)
        except Exception as exc:
            raise LandmarkerError(f"Không khởi tạo được MediaPipe Face Landmarker: {exc}") from exc
        self.model_path = path

    def detect_bgr(self, frame: np.ndarray, timestamp_ms: int) -> LandmarkResult:
        if frame.ndim != 3 or frame.shape[2] != 3 or frame.dtype != np.uint8:
            return LandmarkResult((), "invalid_frame")
        if timestamp_ms < 0:
            return LandmarkResult((), "invalid_timestamp")
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb = np.ascontiguousarray(rgb, dtype=np.uint8)
        try:
            image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
            result = self._landmarker.detect_for_video(image, int(timestamp_ms))
        except Exception as exc:
            return LandmarkResult((), f"inference_error:{type(exc).__name__}")
        faces: list[np.ndarray] = []
        for face in result.face_landmarks:
            points = np.asarray([(point.x, point.y, point.z) for point in face], dtype=np.float64)
            faces.append(points)
        if not faces:
            return LandmarkResult((), "no_face")
        if len(faces) > 1:
            return LandmarkResult(tuple(faces), "multiple_faces")
        return LandmarkResult(tuple(faces))

    def close(self) -> None:
        self._landmarker.close()

    def __enter__(self) -> MediaPipeLandmarker:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
