import cv2
import numpy as np
import pytest

from vinfast_dms.config import Config
from vinfast_dms.geometry import POSE_LANDMARK_INDICES, POSE_MODEL_POINTS, default_camera_matrix
from vinfast_dms.landmarks import LandmarkResult
from vinfast_dms.pipeline import DMSPipeline
from vinfast_dms.sources import FrameSample
from vinfast_dms.temporal import DMSState


def _valid_face(ear: float = 0.30) -> np.ndarray:
    width, height = 640, 480
    angles = np.linspace(0.0, 2.0 * np.pi, 478, endpoint=False)
    landmarks = np.zeros((478, 3), dtype=np.float64)
    landmarks[:, 0] = 0.5 + 0.20 * np.cos(angles)
    landmarks[:, 1] = 0.5 + 0.35 * np.sin(angles)
    camera = default_camera_matrix(width, height)
    projected, _ = cv2.projectPoints(
        POSE_MODEL_POINTS,
        np.zeros((3, 1)),
        np.asarray([[0.0], [0.0], [1000.0]]),
        camera,
        np.zeros((4, 1)),
    )
    for index, xy in zip(POSE_LANDMARK_INDICES, projected.reshape(-1, 2), strict=True):
        landmarks[index, :2] = xy / [width, height]

    # Gán các mốc quanh hai góc mắt; độ mở được tạo từ EAR hình học.
    for first, second, width_fraction, height_fraction in (
        (33, 133, 0.14, ear),
        (362, 263, 0.14, ear),
    ):
        if first == 33:
            x0 = landmarks[first, 0]
            x1 = x0 + width_fraction
            y = landmarks[first, 1]
        else:
            x1 = landmarks[second, 0]
            x0 = x1 - width_fraction
            y = landmarks[second, 1]
        vertical = height_fraction * width_fraction * width / (2.0 * height)
        if first == 33:
            indices = (33, 160, 158, 133, 153, 144)
        else:
            indices = (362, 385, 387, 263, 373, 380)
        landmarks[list(indices)] = np.asarray(
            [
                [x0, y, 0],
                [x0 + width_fraction / 3, y - vertical, 0],
                [x0 + 2 * width_fraction / 3, y - vertical, 0],
                [x1, y, 0],
                [x0 + 2 * width_fraction / 3, y + vertical, 0],
                [x0 + width_fraction / 3, y + vertical, 0],
            ]
        )
    return landmarks


class FakeLandmarker:
    def __init__(self, results: list[LandmarkResult]) -> None:
        self.results = results
        self.index = 0

    def detect_bgr(self, frame: np.ndarray, timestamp_ms: int) -> LandmarkResult:
        result = self.results[min(self.index, len(self.results) - 1)]
        self.index += 1
        return result

    def close(self) -> None:
        pass


def _sample(index: int, t: float) -> FrameSample:
    return FrameSample(
        np.zeros((480, 640, 3), dtype=np.uint8),
        index,
        t,
        round(t * 1000),
        "video",
        "synthetic-test",
    )


def test_pipeline_returns_valid_features_for_one_face() -> None:
    pipeline = DMSPipeline(FakeLandmarker([LandmarkResult((_valid_face(),))]), Config())
    result = pipeline.process(_sample(0, 0.0))
    assert result.quality_valid
    assert result.eye_metrics is not None and result.eye_metrics.ear_mean == pytest.approx(0.30)
    assert result.head_pose is not None and result.head_pose.valid
    assert result.state == DMSState.NORMAL


def test_pipeline_no_face_is_unknown_and_not_stale() -> None:
    closed = _valid_face(ear=0.10)
    results = [LandmarkResult((closed,))] * 50 + [LandmarkResult((), "no_face")]
    pipeline = DMSPipeline(FakeLandmarker(results), Config())
    final = None
    for index in range(51):
        final = pipeline.process(_sample(index, index / 30.0))
    assert final is not None
    assert final.state == DMSState.UNKNOWN
    assert final.quality_reason == "no_face"


def test_pipeline_multiple_faces_is_unknown() -> None:
    faces = (_valid_face(), _valid_face())
    pipeline = DMSPipeline(FakeLandmarker([LandmarkResult(faces, "multiple_faces")]), Config())
    result = pipeline.process(_sample(0, 0.0))
    assert result.state == DMSState.UNKNOWN
    assert result.quality_reason == "multiple_faces"
