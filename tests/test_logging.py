import csv
from pathlib import Path

import numpy as np
import pytest

import vinfast_dms.logging_utils as logging_utils
from vinfast_dms.geometry import EyeMetrics, HeadPose
from vinfast_dms.logging_utils import (
    CSV_FIELDS,
    RUNTIME_COLUMNS,
    CsvLogger,
    RecordingError,
    VideoRecorder,
    deterministic_row,
    private_output_path,
    sha256_file,
)
from vinfast_dms.pipeline import PipelineResult
from vinfast_dms.sources import FrameSample
from vinfast_dms.temporal import DMSState, StateSnapshot


def _row_sample() -> tuple[FrameSample, PipelineResult]:
    sample = FrameSample(
        np.zeros((32, 32, 3), dtype=np.uint8), 4, 0.2, 200, "video", "fixture.avi"
    )
    snapshot = StateSnapshot(0.2, DMSState.NORMAL, False, None, 0.3, 2.0, 0.0, 0.0)
    result = PipelineResult(
        4,
        0.2,
        None,
        EyeMetrics(0.3, 0.3, 0.3, True),
        HeadPose(2.0, 1.0, 0.0, 0.4, True),
        True,
        None,
        snapshot,
        3.2,
    )
    return sample, result


def test_csv_round_trip_uses_versioned_schema_and_nulls(tmp_path: Path) -> None:
    path = tmp_path / "private" / "run.csv"
    sample, result = _row_sample()
    with CsvLogger(path, "run-a", "config", "MediaPipe test", "model") as logger:
        logger.write(sample, result)
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        row = next(reader)
        assert tuple(reader.fieldnames or ()) == CSV_FIELDS
    assert row["schema_version"] == "1"
    assert row["source_time_s"] == "0.2"
    assert row["ear_mean"] == "0.3"
    assert row["state"] == "NORMAL"
    assert row["quality_valid"] == "True"


def test_csv_missing_values_are_empty_cells(tmp_path: Path) -> None:
    sample, result = _row_sample()
    result = PipelineResult(
        result.frame_index,
        result.timestamp_s,
        None,
        None,
        None,
        False,
        "no_face",
        StateSnapshot(0.2, DMSState.UNKNOWN, False, "no_face", None, None, 0.0, 0.0),
        result.processing_ms,
    )
    path = tmp_path / "run.csv"
    with CsvLogger(path, "run-b", "config", "MediaPipe test", "model") as logger:
        logger.write(sample, result)
    with path.open(newline="", encoding="utf-8") as file:
        row = next(csv.DictReader(file))
    assert row["ear_left"] == ""
    assert row["yaw_deg"] == ""
    assert row["quality_reason"] == "no_face"


def test_private_output_path_uses_private_directory(tmp_path: Path) -> None:
    path = private_output_path(tmp_path / "outputs" / "private", "abcdef0123", ".csv")
    assert path.parent == tmp_path / "outputs" / "private"
    assert path.name.endswith("_abcdef01.csv")


def test_sha256_is_computed_from_file_bytes(tmp_path: Path) -> None:
    path = tmp_path / "model.task"
    path.write_bytes(b"known model bytes")
    assert sha256_file(path) == "e88b6e0d664778236e7603e9453d5414397860c0d395b150f9b98ef3aeed9f08"


def test_deterministic_signature_drops_only_runtime_fields() -> None:
    row_a = {
        "run_id": "a",
        "wall_time_utc": "t1",
        "processing_ms": "2.0",
        "source_time_s": "0.1",
        "state": "NORMAL",
    }
    row_b = {**row_a, "run_id": "b", "wall_time_utc": "t2", "processing_ms": "9.0"}
    assert deterministic_row(row_a) == deterministic_row(row_b)
    assert RUNTIME_COLUMNS == {"run_id", "wall_time_utc", "processing_ms"}


def test_video_recorder_writes_avi_fixture(tmp_path: Path) -> None:
    path = tmp_path / "rendered.avi"
    with VideoRecorder(path, 12.0) as recorder:
        recorder.write(np.zeros((64, 64, 3), dtype=np.uint8))
        recorder.write(np.full((64, 64, 3), 255, dtype=np.uint8))
    assert recorder.frames_written == 2
    assert path.is_file() and path.stat().st_size > 0


def test_video_recorder_bad_extension_is_actionable(tmp_path: Path) -> None:
    with pytest.raises(RecordingError, match="Chỉ hỗ trợ"):
        VideoRecorder(tmp_path / "bad.mkv", 30.0)


def test_video_recorder_removes_empty_file_if_codec_cannot_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class ClosedWriter:
        def isOpened(self) -> bool:
            return False

        def release(self) -> None:
            pass

    monkeypatch.setattr(logging_utils.cv2, "VideoWriter", lambda *_args: ClosedWriter())
    path = tmp_path / "empty.mp4"
    recorder = VideoRecorder(path, 30.0)
    with pytest.raises(RecordingError, match="không mở được"):
        recorder.write(np.zeros((64, 64, 3), dtype=np.uint8))
    assert not path.exists()
