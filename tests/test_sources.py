from pathlib import Path

import cv2
import numpy as np
import pytest

from vinfast_dms.sources import SourceError, VideoSource


def test_missing_video_fails_with_actionable_error(tmp_path: Path) -> None:
    with pytest.raises(SourceError, match="Không tìm thấy video"):
        with VideoSource(str(tmp_path / "missing.mp4")):
            pass


def test_video_fixture_reads_frames_and_closes(tmp_path: Path) -> None:
    path = tmp_path / "fixture.avi"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (64, 48))
    if not writer.isOpened():
        pytest.skip("OpenCV trên máy này không có codec MJPG cho fixture tạm.")
    for value in (30, 60, 90):
        writer.write(np.full((48, 64, 3), value, dtype=np.uint8))
    writer.release()

    with VideoSource(str(path)) as source:
        samples = list(source)
        assert source.capture is not None
        assert source.capture.isOpened()
    assert source.capture is None
    assert [sample.index for sample in samples] == [0, 1, 2]
    assert all(
        b.timestamp_ms > a.timestamp_ms
        for a, b in zip(samples, samples[1:], strict=False)
    )
    assert samples[0].frame.shape == (48, 64, 3)


def test_camera_capture_is_released_on_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeCapture:
        released = False

        def isOpened(self) -> bool:
            return True

        def set(self, *_: object) -> bool:
            return True

        def release(self) -> None:
            self.released = True

    capture = FakeCapture()
    monkeypatch.setattr(cv2, "VideoCapture", lambda *_: capture)
    with pytest.raises(RuntimeError):
        with VideoSource("camera") as source:
            raise RuntimeError("fixture")
    assert source.capture is None
    assert capture.released
