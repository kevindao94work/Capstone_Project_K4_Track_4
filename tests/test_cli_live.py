from __future__ import annotations

import numpy as np

import vinfast_dms.cli as cli
from vinfast_dms.landmarks import LandmarkResult
from vinfast_dms.sources import FrameSample


class FakeLandmarker:
    def __init__(self, *_: object, **__: object) -> None:
        pass

    def __enter__(self) -> FakeLandmarker:
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def detect_bgr(self, frame: np.ndarray, timestamp_ms: int) -> LandmarkResult:
        return LandmarkResult((), "no_face")

    def close(self) -> None:
        pass


class FakeSource:
    instances: list[FakeSource] = []

    def __init__(self, *_: object, **__: object) -> None:
        self.yielded = 0
        self.instances.append(self)

    def __enter__(self) -> FakeSource:
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def __iter__(self):
        for index in range(3):
            self.yielded += 1
            yield FrameSample(
                np.zeros((64, 64, 3), dtype=np.uint8),
                index,
                index / 30,
                index * 33,
                "camera",
                "fixture",
            )


def _patch_cli(monkeypatch) -> None:
    FakeSource.instances.clear()
    monkeypatch.setattr(cli, "MediaPipeLandmarker", FakeLandmarker)
    monkeypatch.setattr(cli, "VideoSource", FakeSource)
    monkeypatch.setattr(cli, "draw_overlay", lambda frame, *_args, **_kwargs: frame)
    monkeypatch.setattr(cli.cv2, "destroyAllWindows", lambda: None)


def test_q_key_quits_and_releases_loop(monkeypatch) -> None:
    _patch_cli(monkeypatch)
    monkeypatch.setattr(cli.cv2, "imshow", lambda *_: None)
    monkeypatch.setattr(cli.cv2, "waitKey", lambda *_: ord("q"))
    assert cli.main(["--source", "camera"]) == 0
    assert FakeSource.instances[0].yielded == 1


def test_missing_display_falls_back_to_headless(monkeypatch) -> None:
    _patch_cli(monkeypatch)

    def no_display(*_args):
        raise cli.cv2.error("display unavailable")

    monkeypatch.setattr(cli.cv2, "imshow", no_display)
    assert cli.main(["--source", "camera", "--max-frames", "3"]) == 0
    assert FakeSource.instances[0].yielded == 3
