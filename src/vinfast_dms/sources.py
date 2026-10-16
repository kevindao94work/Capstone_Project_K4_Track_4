"""Đọc webcam hoặc video và gắn dấu thời gian nguồn tăng đơn điệu."""

from __future__ import annotations

import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


class SourceError(RuntimeError):
    """Nguồn hình không thể mở hoặc bị ngắt ngoài dự kiến."""


DEFAULT_CAMERA_INDEX = 1


@dataclass(frozen=True, slots=True)
class FrameSample:
    frame: np.ndarray
    index: int
    timestamp_s: float
    timestamp_ms: int
    source_type: str
    source_name: str


class VideoSource(Iterator[FrameSample]):
    """Context manager cho webcam hoặc tệp video.

    Video dùng vị trí phát của OpenCV khi hợp lệ, sau đó dùng số khung hình/FPS.
    Webcam dùng đồng hồ monotonic. Mọi timestamp đều được ép tăng ít nhất 1 ms
    để tương thích chế độ VIDEO đồng bộ của MediaPipe Tasks.
    """

    def __init__(
        self,
        source: str = "camera",
        camera_index: int = DEFAULT_CAMERA_INDEX,
        width: int = 640,
        height: int = 480,
        max_frames: int | None = None,
    ) -> None:
        self.source = source
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.max_frames = max_frames
        self.capture: cv2.VideoCapture | None = None
        self.source_type = "camera" if source == "camera" else "video"
        self.source_name = str(camera_index) if source == "camera" else source
        self.fps = 0.0
        self._frame_index = 0
        self._last_timestamp_s = -1.0
        self._last_timestamp_ms = -1
        self._clock_origin_ns: int | None = None
        self.timestamp_fallback = False
        self.capture_read_attempts = 0
        self.capture_failures = 0

    def __enter__(self) -> VideoSource:
        if self.source == "camera":
            capture = self._open_camera()
            try:
                capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            except cv2.error as exc:
                self._release_capture(capture)
                raise SourceError(f"Không cấu hình được webcam: {exc}") from exc
            self.capture = capture
        else:
            path = Path(self.source).expanduser()
            if not path.is_file():
                raise SourceError(f"Không tìm thấy video: {path}")
            capture = cv2.VideoCapture(str(path))
            if not capture.isOpened():
                capture.release()
                raise SourceError(f"Không giải mã được video: {path}")
            self.capture = capture
            fps = float(capture.get(cv2.CAP_PROP_FPS))
            self.fps = fps if np.isfinite(fps) and fps > 0.0 else 0.0
        return self

    def _open_camera(self) -> cv2.VideoCapture:
        backends: list[tuple[int, ...]] = []
        if sys.platform == "darwin" and hasattr(cv2, "CAP_AVFOUNDATION"):
            backends.append((self.camera_index, cv2.CAP_AVFOUNDATION))
        backends.append((self.camera_index,))
        for arguments in backends:
            capture: cv2.VideoCapture | None = None
            try:
                capture = cv2.VideoCapture(*arguments)
                if capture.isOpened():
                    return capture
            except cv2.error:
                pass
            if capture is not None:
                self._release_capture(capture)
        raise SourceError(
            f"Không mở được webcam index {self.camera_index}. Hãy kiểm tra kết nối "
            "và quyền Camera tại System Settings → Privacy & Security → Camera."
        )

    @staticmethod
    def _release_capture(capture: cv2.VideoCapture) -> None:
        try:
            capture.release()
        except cv2.error:
            pass

    def __iter__(self) -> VideoSource:
        return self

    def __next__(self) -> FrameSample:
        if self.capture is None:
            raise SourceError("Nguồn chưa được mở; hãy dùng `with VideoSource(...)`.")
        if self.max_frames is not None and self._frame_index >= self.max_frames:
            raise StopIteration
        self.capture_read_attempts += 1
        try:
            ok, frame = self.capture.read()
        except cv2.error as exc:
            self.capture_failures += 1
            raise SourceError(f"Lỗi khi đọc webcam: {exc}") from exc
        if not ok or frame is None or frame.size == 0:
            if self.source_type == "camera":
                self.capture_failures += 1
                raise SourceError("Webcam ngừng gửi khung hình.")
            raise StopIteration
        now_ns = time.monotonic_ns()
        if self.source_type == "camera":
            if self._clock_origin_ns is None:
                self._clock_origin_ns = now_ns
            candidate_s = (now_ns - self._clock_origin_ns) / 1_000_000_000
        else:
            position_ms = float(self.capture.get(cv2.CAP_PROP_POS_MSEC))
            if np.isfinite(position_ms) and position_ms >= 0.0:
                candidate_s = position_ms / 1000.0
            elif self.fps > 0.0:
                candidate_s = self._frame_index / self.fps
                self.timestamp_fallback = True
            else:
                candidate_s = (now_ns - (self._clock_origin_ns or now_ns)) / 1_000_000_000
                if self._clock_origin_ns is None:
                    self._clock_origin_ns = now_ns
                self.timestamp_fallback = True
        if candidate_s <= self._last_timestamp_s:
            if self.source_type == "video":
                if self.fps > 0.0:
                    candidate_s = self._frame_index / self.fps
                else:
                    if self._clock_origin_ns is None:
                        self._clock_origin_ns = now_ns
                    candidate_s = (now_ns - self._clock_origin_ns) / 1_000_000_000
                self.timestamp_fallback = True
            candidate_s = max(candidate_s, self._last_timestamp_s + 0.001)
        self._last_timestamp_s = candidate_s
        timestamp_ms = max(0, int(round(candidate_s * 1000.0)))
        if timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1
        self._last_timestamp_ms = timestamp_ms
        sample = FrameSample(
            frame=frame,
            index=self._frame_index,
            timestamp_s=candidate_s,
            timestamp_ms=timestamp_ms,
            source_type=self.source_type,
            source_name=self.source_name,
        )
        self._frame_index += 1
        return sample

    def close(self) -> None:
        if self.capture is not None:
            self._release_capture(self.capture)
            self.capture = None

    def __exit__(self, *_: object) -> None:
        self.close()
