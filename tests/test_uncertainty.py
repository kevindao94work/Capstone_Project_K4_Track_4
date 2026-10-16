import numpy as np
import pytest

from vinfast_dms.geometry import EyeMetrics, HeadPose
from vinfast_dms.landmarks import LandmarkResult
from vinfast_dms.uncertainty import (
    QualityReason,
    assess_frame,
    assess_landmarks,
    eye_quality_reason,
    pose_quality_reason,
)


def _face() -> np.ndarray:
    points = np.zeros((478, 3), dtype=np.float64)
    angle = np.linspace(0, 2 * np.pi, len(points), endpoint=False)
    points[:, 0] = 0.5 + 0.2 * np.cos(angle)
    points[:, 1] = 0.5 + 0.35 * np.sin(angle)
    return points


def test_no_face_is_unknown_reason() -> None:
    result = assess_landmarks(LandmarkResult((), "no_face"), 640, 480, 0.08)
    assert result.reason == QualityReason.NO_FACE


def test_multiple_faces_are_not_selected_implicitly() -> None:
    result = assess_landmarks(LandmarkResult((_face(), _face())), 640, 480, 0.08)
    assert result.reason == QualityReason.MULTIPLE_FACES
    assert result.landmarks is None


def test_bad_landmark_shape_is_rejected() -> None:
    result = assess_landmarks(LandmarkResult((np.zeros((468, 3)),)), 640, 480, 0.08)
    assert result.reason == QualityReason.INVALID_LANDMARK_SHAPE


def test_non_finite_landmark_is_rejected() -> None:
    points = _face()
    points[12, 2] = np.nan
    result = assess_landmarks(LandmarkResult((points,)), 640, 480, 0.08)
    assert result.reason == QualityReason.NON_FINITE_LANDMARKS


def test_out_of_bounds_landmark_is_rejected() -> None:
    points = _face()
    points[12, 0] = 1.2
    result = assess_landmarks(LandmarkResult((points,)), 640, 480, 0.08)
    assert result.reason == QualityReason.LANDMARKS_OUT_OF_BOUNDS


def test_tiny_face_is_rejected() -> None:
    points = np.full((478, 3), 0.5)
    result = assess_landmarks(LandmarkResult((points,)), 640, 480, 0.08)
    assert result.reason == QualityReason.FACE_TOO_SMALL


@pytest.mark.parametrize(
    ("frame", "expected"),
    [
        (np.zeros((480, 640), dtype=np.uint8), QualityReason.INVALID_FRAME),
        (np.zeros((0, 640, 3), dtype=np.uint8), QualityReason.INVALID_FRAME_SIZE),
    ],
)
def test_invalid_frame_is_rejected(frame: np.ndarray, expected: QualityReason) -> None:
    assert assess_frame(frame) == expected


def test_empty_inference_result_has_distinct_reason() -> None:
    result = assess_landmarks(
        LandmarkResult((), "inference_error:RuntimeError"), 640, 480, 0.08
    )
    assert result.reason == QualityReason.INFERENCE_ERROR


def test_missing_eye_landmark_reason_is_explicit() -> None:
    metrics = EyeMetrics(None, None, None, False, "missing_eye_landmarks")
    assert eye_quality_reason(metrics) == QualityReason.MISSING_EYE_LANDMARKS


def test_zero_eye_width_reason_is_explicit() -> None:
    metrics = EyeMetrics(None, None, None, False, "zero_eye_width")
    assert eye_quality_reason(metrics) == QualityReason.ZERO_EYE_WIDTH


def test_pnp_failure_reason_is_explicit() -> None:
    pose = HeadPose(None, None, None, None, False, "solvepnp_failed")
    assert pose_quality_reason(pose) == QualityReason.PNP_FAILED


def test_high_reprojection_error_is_poor_geometry() -> None:
    pose = HeadPose(None, None, None, 19.0, False, "high_reprojection_error")
    assert pose_quality_reason(pose) == QualityReason.POOR_GEOMETRY


def test_valid_face_reports_coverage_fraction() -> None:
    result = assess_landmarks(LandmarkResult((_face(),)), 640, 480, 0.08)
    assert result.valid
    assert result.reason is None
    assert result.face_fraction is not None and result.face_fraction > 0.08
