import cv2
import numpy as np
import pytest

from vinfast_dms.geometry import (
    LEFT_EYE_INDICES,
    POSE_CANONICAL_MODEL_POINTS,
    POSE_LANDMARK_INDICES,
    POSE_MODEL_POINTS,
    RIGHT_EYE_INDICES,
    default_camera_matrix,
    estimate_head_pose,
    measure_eyes,
    rotation_matrix_to_euler,
)


def _eye_points(points: np.ndarray, indices: tuple[int, ...], x0: float) -> None:
    x1 = x0 + 20.0
    points[list(indices)] = np.asarray(
        [
            [x0, 20.0, 0.0],
            [x0 + 5.0, 18.0, 0.0],
            [x0 + 15.0, 18.0, 0.0],
            [x1, 20.0, 0.0],
            [x0 + 15.0, 22.0, 0.0],
            [x0 + 5.0, 22.0, 0.0],
        ]
    )


def _open_eyes() -> np.ndarray:
    points = np.zeros((478, 3), dtype=np.float64)
    _eye_points(points, RIGHT_EYE_INDICES, 20.0)
    _eye_points(points, LEFT_EYE_INDICES, 60.0)
    points[:, 0] /= 640.0
    points[:, 1] /= 480.0
    return points


def _project_face(yaw_deg: float = 0, pitch_deg: float = 0, roll_deg: float = 0) -> np.ndarray:
    width, height = 640, 480
    camera = default_camera_matrix(width, height)
    yaw, pitch, roll = np.deg2rad([yaw_deg, pitch_deg, roll_deg])
    rx = np.asarray(
        [[1, 0, 0], [0, np.cos(pitch), -np.sin(pitch)], [0, np.sin(pitch), np.cos(pitch)]]
    )
    camera_yaw = -yaw
    ry = np.asarray(
        [
            [np.cos(camera_yaw), 0, np.sin(camera_yaw)],
            [0, 1, 0],
            [-np.sin(camera_yaw), 0, np.cos(camera_yaw)],
        ]
    )
    rz = np.asarray(
        [[np.cos(roll), -np.sin(roll), 0], [np.sin(roll), np.cos(roll), 0], [0, 0, 1]]
    )
    rotation = rz @ ry @ rx
    rotation_vector, _ = cv2.Rodrigues(rotation)
    projected, _ = cv2.projectPoints(
        POSE_MODEL_POINTS,
        rotation_vector,
        np.asarray([[0.0], [0.0], [1000.0]]),
        camera,
        np.zeros((4, 1)),
    )
    landmarks = np.zeros((478, 3), dtype=np.float64)
    for index, xy in zip(POSE_LANDMARK_INDICES, projected.reshape(-1, 2), strict=True):
        landmarks[index, :2] = xy / [width, height]
    return landmarks


def test_ear_closed_form_for_both_eyes() -> None:
    result = measure_eyes(_open_eyes(), 640, 480)
    assert result.valid
    assert result.ear_left == pytest.approx(0.2)
    assert result.ear_right == pytest.approx(0.2)
    assert result.ear_mean == pytest.approx(0.2)


def test_ear_is_translation_invariant() -> None:
    original = measure_eyes(_open_eyes(), 640, 480).ear_mean
    shifted = _open_eyes() + [134.0 / 640.0, 77.0 / 480.0, 0.0]
    result = measure_eyes(shifted, 640, 480)
    assert result.ear_mean == pytest.approx(original, abs=1e-12)


def test_ear_is_scale_invariant() -> None:
    original = measure_eyes(_open_eyes(), 640, 480).ear_mean
    scaled = _open_eyes() * 3.5
    result = measure_eyes(scaled, 640, 480)
    assert result.ear_mean == pytest.approx(original, abs=1e-12)


def test_ear_zero_horizontal_denominator_is_invalid() -> None:
    points = _open_eyes()
    points[RIGHT_EYE_INDICES[3]] = points[RIGHT_EYE_INDICES[0]]
    result = measure_eyes(points, 640, 480)
    assert not result.valid
    assert result.reason == "zero_eye_width"


def test_ear_non_finite_eye_point_is_invalid() -> None:
    points = _open_eyes()
    points[LEFT_EYE_INDICES[2], 0] = np.nan
    result = measure_eyes(points, 640, 480)
    assert not result.valid
    assert result.reason == "non_finite_eye_landmarks"


def test_ear_missing_indices_is_invalid() -> None:
    result = measure_eyes(_open_eyes()[:100], 640, 480)
    assert not result.valid
    assert result.reason == "missing_eye_landmarks"


def test_ear_rejects_bad_frame_size() -> None:
    result = measure_eyes(_open_eyes(), 0, 480)
    assert not result.valid
    assert result.reason == "invalid_frame_size"


def test_ear_extreme_ratio_is_invalid() -> None:
    points = _open_eyes()
    points[RIGHT_EYE_INDICES[1], 1] = -20.0 / 480.0
    points[RIGHT_EYE_INDICES[5], 1] = 60.0 / 480.0
    result = measure_eyes(points, 640, 480)
    assert not result.valid
    assert result.reason == "implausible_ear"


def test_pose_zero_rotation_has_small_reprojection_residual() -> None:
    landmarks = _project_face()
    result = estimate_head_pose(landmarks, 640, 480, max_reprojection_error_px=0.01)
    assert result.valid
    assert result.reprojection_error_px is not None
    assert result.reprojection_error_px < 1e-3
    assert result.yaw_deg == pytest.approx(0.0, abs=1e-4)
    assert result.pitch_deg == pytest.approx(0.0, abs=1e-4)


def test_pose_correspondence_matches_mediapipe_canonical_face_points() -> None:
    assert POSE_LANDMARK_INDICES == (1, 152, 33, 263, 61, 291)
    np.testing.assert_allclose(
        POSE_CANONICAL_MODEL_POINTS,
        [
            (0.0, -1.126865, 7.475604),
            (0.0, -9.403378, 4.264492),
            (-4.445859, 2.663991, 3.173422),
            (4.445859, 2.663991, 3.173422),
            (-2.456206, -4.342621, 4.283884),
            (2.456206, -4.342621, 4.283884),
        ],
        atol=1e-6,
    )
    np.testing.assert_allclose(
        POSE_MODEL_POINTS,
        POSE_CANONICAL_MODEL_POINTS * [1.0, -1.0, -1.0],
        atol=1e-12,
    )


@pytest.mark.parametrize("yaw", [-25.0, 25.0])
def test_pose_yaw_sign_and_magnitude(yaw: float) -> None:
    result = estimate_head_pose(_project_face(yaw_deg=yaw), 640, 480, max_reprojection_error_px=1.0)
    assert result.valid
    assert result.yaw_deg == pytest.approx(yaw, abs=0.1)


def test_positive_yaw_points_nose_to_subject_left_in_unmirrored_frame() -> None:
    frontal = _project_face()
    turned = _project_face(yaw_deg=25.0)
    nose_x_frontal = frontal[POSE_LANDMARK_INDICES[0], 0]
    nose_x_turned = turned[POSE_LANDMARK_INDICES[0], 0]
    assert nose_x_turned > nose_x_frontal
    pose = estimate_head_pose(turned, 640, 480, max_reprojection_error_px=1.0)
    assert pose.yaw_deg is not None and pose.yaw_deg > 0.0


@pytest.mark.parametrize("angles", [(0, 20, 0), (0, 0, 18)])
def test_pose_pitch_and_roll_convention(angles: tuple[float, float, float]) -> None:
    result = estimate_head_pose(
        _project_face(yaw_deg=angles[0], pitch_deg=angles[1], roll_deg=angles[2]),
        640,
        480,
        max_reprojection_error_px=1.0,
    )
    assert result.valid
    assert result.pitch_deg == pytest.approx(angles[1], abs=0.1)
    assert result.roll_deg == pytest.approx(angles[2], abs=0.1)


def test_pose_non_finite_point_is_invalid() -> None:
    landmarks = _project_face()
    landmarks[1, 0] = np.inf
    result = estimate_head_pose(landmarks, 640, 480)
    assert not result.valid
    assert result.reason == "non_finite_pose_landmarks"


def test_pose_rejects_high_reprojection_error() -> None:
    landmarks = _project_face()
    landmarks[152, :2] += [0.04, -0.03]
    result = estimate_head_pose(landmarks, 640, 480, max_reprojection_error_px=0.01)
    assert not result.valid
    assert result.reason == "high_reprojection_error"


def test_pose_rejects_incomplete_landmarks() -> None:
    result = estimate_head_pose(np.zeros((100, 3)), 640, 480)
    assert not result.valid
    assert result.reason == "missing_pose_landmarks"


def test_rotation_matrix_requires_finite_3x3_input() -> None:
    with pytest.raises(ValueError, match="3×3"):
        rotation_matrix_to_euler(np.eye(2))
