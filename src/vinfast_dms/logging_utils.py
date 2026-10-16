"""Ghi log CSV và video khi người dùng chủ động bật tùy chọn."""

from __future__ import annotations

import csv
import hashlib
import uuid
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np

from vinfast_dms.pipeline import PipelineResult
from vinfast_dms.sources import FrameSample

SCHEMA_VERSION = "1"
CSV_FIELDS = (
    "schema_version",
    "run_id",
    "source_type",
    "frame_idx",
    "source_time_s",
    "wall_time_utc",
    "processing_ms",
    "ear_left",
    "ear_right",
    "ear_mean",
    "yaw_deg",
    "pitch_deg",
    "quality_valid",
    "quality_reason",
    "state",
    "warning",
    "config_hash",
    "model_version",
    "model_sha256",
)
RUNTIME_COLUMNS = frozenset({"run_id", "wall_time_utc", "processing_ms"})


class RecordingError(RuntimeError):
    """Không thể tạo hoặc hoàn tất tệp video đầu ra."""


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def new_run_id() -> str:
    return uuid.uuid4().hex


def private_output_path(output_dir: str | Path, run_id: str, suffix: str) -> Path:
    now = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Path(output_dir) / f"dms_{now}_{run_id[:8]}{suffix}"


class CsvLogger:
    """CSV từng frame; giá trị thiếu được ghi thành ô rỗng theo chuẩn CSV."""

    def __init__(
        self,
        path: str | Path,
        run_id: str,
        config_hash: str,
        model_version: str,
        model_sha256: str,
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._file = self.path.open("w", newline="", encoding="utf-8")
        except OSError as exc:
            raise OSError(f"Không mở được CSV log {self.path}: {exc}") from exc
        self._writer = csv.DictWriter(self._file, fieldnames=CSV_FIELDS, extrasaction="raise")
        self._writer.writeheader()
        self.run_id = run_id
        self.config_hash = config_hash
        self.model_version = model_version
        self.model_sha256 = model_sha256

    def write(self, sample: FrameSample, result: PipelineResult) -> None:
        eyes = result.eye_metrics
        pose = result.head_pose
        reason = result.quality_reason or result.snapshot.reason or ""
        self._writer.writerow(
            {
                "schema_version": SCHEMA_VERSION,
                "run_id": self.run_id,
                "source_type": sample.source_type,
                "frame_idx": sample.index,
                "source_time_s": sample.timestamp_s,
                "wall_time_utc": datetime.now(UTC).isoformat(timespec="milliseconds"),
                "processing_ms": result.processing_ms,
                "ear_left": eyes.ear_left if eyes else None,
                "ear_right": eyes.ear_right if eyes else None,
                "ear_mean": eyes.ear_mean if eyes else None,
                "yaw_deg": pose.yaw_deg if pose else None,
                "pitch_deg": pose.pitch_deg if pose else None,
                "quality_valid": result.quality_valid,
                "quality_reason": reason,
                "state": result.state.value,
                "warning": result.snapshot.warning,
                "config_hash": self.config_hash,
                "model_version": self.model_version,
                "model_sha256": self.model_sha256,
            }
        )
        self._file.flush()

    def close(self) -> None:
        if not self._file.closed:
            self._file.close()

    def __enter__(self) -> CsvLogger:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class VideoRecorder:
    """Ghi frame đã phủ overlay sau khi có lựa chọn tường minh từ người dùng."""

    def __init__(self, path: str | Path, fps: float) -> None:
        self.path = Path(path)
        suffix = self.path.suffix.lower()
        if suffix == ".mp4":
            codec = "mp4v"
        elif suffix in {".avi", ".m4v"}:
            codec = "MJPG" if suffix == ".avi" else "mp4v"
        else:
            raise RecordingError("Chỉ hỗ trợ tệp đầu ra .mp4, .m4v hoặc .avi.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fps = float(fps) if np.isfinite(fps) and fps > 0 else 30.0
        self._codec = codec
        self._writer: cv2.VideoWriter | None = None
        self.frames_written = 0

    def write(self, frame: np.ndarray) -> None:
        if frame.ndim != 3 or frame.shape[2] != 3 or frame.dtype != np.uint8:
            raise RecordingError("Khung hình ghi phải là ảnh BGR uint8.")
        if self._writer is None:
            height, width = frame.shape[:2]
            try:
                self._writer = cv2.VideoWriter(
                    str(self.path),
                    cv2.VideoWriter_fourcc(*self._codec),
                    self._fps,
                    (width, height),
                )
            except cv2.error as exc:
                self.path.unlink(missing_ok=True)
                raise RecordingError(f"Không khởi tạo được codec {self._codec}: {exc}") from exc
            if not self._writer.isOpened():
                self._writer.release()
                self._writer = None
                self.path.unlink(missing_ok=True)
                raise RecordingError(
                    f"Codec {self._codec} không mở được cho {self.path}; "
                    "hãy thử .avi hoặc kiểm tra codec OpenCV."
                )
        try:
            self._writer.write(frame)
        except cv2.error as exc:
            self._writer.release()
            self._writer = None
            self.path.unlink(missing_ok=True)
            raise RecordingError(f"Lỗi ghi khung hình: {exc}") from exc
        self.frames_written += 1

    def close(self) -> None:
        if self._writer is not None:
            self._writer.release()
            self._writer = None
        if self.frames_written and (not self.path.is_file() or self.path.stat().st_size == 0):
            self.path.unlink(missing_ok=True)
            raise RecordingError(f"VideoWriter không tạo được dữ liệu trong {self.path}.")

    def __enter__(self) -> VideoRecorder:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def deterministic_row(row: dict[str, str]) -> tuple[tuple[str, str], ...]:
    """Chữ ký replay bỏ ID lần chạy và các số đo thời gian máy."""
    return tuple(sorted((key, value) for key, value in row.items() if key not in RUNTIME_COLUMNS))
