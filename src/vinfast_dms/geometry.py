"""Đặc trưng mắt EAR và ước lượng tư thế đầu bằng solvePnP."""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np

from vinfast_dms.landmarks import normalized_to_pixels

# Chỉ số topology Face Landmarker 478 điểm, theo hướng nhìn của chủ thể.
RIGHT_EYE_INDICES = (33, 160, 158, 133, 153, 144)
LEFT_EYE_INDICES = (362, 385, 387, 263, 373, 380)

# Sáu đỉnh cùng chỉ số trong canonical_face_model.obj của MediaPipe (468 đỉnh).
# Thứ tự 2D/3D phải tương ứng tuyệt đối. Tọa độ dùng đơn vị canonical cm, không
# phải kích thước đã hiệu chuẩn của người dùng hoặc camera.
# Nguồn: https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model.obj
POSE_LANDMARK_INDICES = (1, 152, 33, 263, 61, 291)
POSE_MODEL_POINTS = np.asarray(
    [
        (0.0, -1.126865, 7.475604),  # 1: chóp mũi
        (0.0, -9.403378, 4.264492),  # 152: cằm
        (-4.445859, 2.663991, 3.173422),  # 33: khóe mắt ở trái ảnh
        (4.445859, 2.663991, 3.173422),  # 263: khóe mắt ở phải ảnh
        (-2.456206, -4.342621, 4.283884),  # 61: khóe miệng trái ảnh
        (2.456206, -4.342621, 4.283884),  # 291: khóe miệng phải ảnh
    ],
    dtype=np.float64,
)


@dataclass(frozen=True, slots=True)
class EyeMetrics:
    ear_left: float | None
    ear_right: float | None
    ear_mean: float | None
    valid: bool
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class HeadPose:
    yaw_deg: float | None
    pitch_deg: float | None
    roll_deg: float | None
    reprojection_error_px: float | None
    valid: bool
    reason: str | None = None


def _eye_aspect_ratio(points: np.ndarray, indices: tuple[int, ...], epsilon: float) -> float:
    if len(indices) != 6 or max(indices) >= len(points):
        raise ValueError("missing_eye_landmarks")
    eye = np.asarray(points[list(indices), :2], dtype=np.float64)
    if not np.isfinite(eye).all():
        raise ValueError("non_finite_eye_landmarks")
    horizontal = float(np.linalg.norm(eye[0] - eye[3]))
    if horizontal <= epsilon:
        raise ValueError("zero_eye_width")
    vertical_a = float(np.linalg.norm(eye[1] - eye[5]))
    vertical_b = float(np.linalg.norm(eye[2] - eye[4]))
    ratio = (vertical_a + vertical_b) / (2.0 * horizontal)
    if not math.isfinite(ratio) or ratio > 1.5:
        raise ValueError("implausible_ear")
    return ratio


def measure_eyes(
    landmarks: np.ndarray,
    width: int,
    height: int,
    epsilon: float = 1e-6,
) -> EyeMetrics:
    """Tính EAR hai mắt từ mốc chuẩn hóa; lỗi một mắt làm cả mẫu không hợp lệ."""
    points = np.asarray(landmarks, dtype=np.float64)
    required = max(*RIGHT_EYE_INDICES, *LEFT_EYE_INDICES)
    if points.ndim != 2 or points.shape[1] < 2:
        return EyeMetrics(None, None, None, False, "invalid_landmark_shape")
    if required >= len(points):
        return EyeMetrics(None, None, None, False, "missing_eye_landmarks")
    if not np.isfinite(points[list(set(RIGHT_EYE_INDICES + LEFT_EYE_INDICES))]).all():
        return EyeMetrics(None, None, None, False, "non_finite_eye_landmarks")
    if width < 1 or height < 1:
        return EyeMetrics(None, None, None, False, "invalid_frame_size")
    pixels = normalized_to_pixels(points, width, height)
    try:
        ear_right = _eye_aspect_ratio(pixels, RIGHT_EYE_INDICES, epsilon)
        ear_left = _eye_aspect_ratio(pixels, LEFT_EYE_INDICES, epsilon)
    except ValueError as exc:
        return EyeMetrics(None, None, None, False, str(exc))
    return EyeMetrics(ear_left, ear_right, (ear_left + ear_right) / 2.0, True)


def default_camera_matrix(width: int, height: int) -> np.ndarray:
    """Ma trận nội tại khởi tạo fx=fy=width; đây chỉ là heuristic."""
    if width < 1 or height < 1:
        raise ValueError("Kích thước ảnh không hợp lệ.")
    return np.asarray(
        [[width, 0.0, width / 2.0], [0.0, width, height / 2.0], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )


def rotation_matrix_to_euler(rotation: np.ndarray) -> tuple[float, float, float]:
    """Phân rã Z-Y-X; trả yaw, pitch, roll theo độ.

    Quy ước trục object của canonical face: X chạy theo chiều ngang ảnh khi nhìn
    thẳng, +Y lên trên, và +Z hướng từ mặt ra phía mũi/camera. Euler theo thứ tự
    R = Rz(roll) @ Ry(yaw) @ Rx(pitch): yaw quanh Y, pitch quanh X, roll quanh Z.
    Với frame camera không mirror, yaw dương quay mũi về phía trái của chủ thể
    (phía phải ảnh); yaw âm quay mũi về phía phải của chủ thể. Chỉ mirror overlay,
    không mirror frame đầu vào PnP.
    """
    r = np.asarray(rotation, dtype=np.float64)
    if r.shape != (3, 3) or not np.isfinite(r).all():
        raise ValueError("Ma trận quay cần là 3×3 hữu hạn.")
    sy = math.sqrt(r[0, 0] ** 2 + r[1, 0] ** 2)
    singular = sy < 1e-8
    if not singular:
        yaw = math.atan2(-r[2, 0], sy)
        pitch = math.atan2(r[2, 1], r[2, 2])
        roll = math.atan2(r[1, 0], r[0, 0])
    else:
        yaw = math.atan2(-r[2, 0], sy)
        pitch = math.atan2(-r[0, 1], r[1, 1])
        roll = 0.0
    return tuple(math.degrees(value) for value in (yaw, pitch, roll))


def estimate_head_pose(
    landmarks: np.ndarray,
    width: int,
    height: int,
    camera_matrix: np.ndarray | None = None,
    distortion: np.ndarray | None = None,
    max_reprojection_error_px: float = 12.0,
) -> HeadPose:
    """Ước lượng yaw/pitch/roll từ correspondence canonical; lỗi/residual lớn invalid.

    Intrinsics mặc định giả định pixel vuông, tâm quang học ở giữa ảnh, tiêu cự
    bằng chiều rộng ảnh và không méo. Đây là heuristic; chưa hiệu chuẩn webcam.
    Reprojection error là căn bậc hai của trung bình bình phương khoảng cách 2D
    Euclid trên sáu correspondence.
    """
    points = np.asarray(landmarks, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] < 2:
        return HeadPose(None, None, None, None, False, "invalid_landmark_shape")
    if width < 1 or height < 1:
        return HeadPose(None, None, None, None, False, "invalid_frame_size")
    if max(POSE_LANDMARK_INDICES) >= len(points):
        return HeadPose(None, None, None, None, False, "missing_pose_landmarks")
    selected = points[list(POSE_LANDMARK_INDICES)]
    if not np.isfinite(selected[:, :2]).all():
        return HeadPose(None, None, None, None, False, "non_finite_pose_landmarks")
    image_points = selected[:, :2].copy()
    if np.max(np.abs(image_points)) <= 2.0:
        image_points[:, 0] *= width
        image_points[:, 1] *= height
    image_points = np.ascontiguousarray(image_points.reshape(-1, 1, 2), dtype=np.float64)
    object_points = np.ascontiguousarray(POSE_MODEL_POINTS.reshape(-1, 1, 3))
    camera = (
        default_camera_matrix(width, height)
        if camera_matrix is None
        else np.asarray(camera_matrix)
    )
    if camera.shape != (3, 3) or not np.isfinite(camera).all():
        return HeadPose(None, None, None, None, False, "invalid_camera_matrix")
    distortion = (
        np.zeros((4, 1), dtype=np.float64)
        if distortion is None
        else np.asarray(distortion, dtype=np.float64)
    )
    try:
        success, rotation_vector, translation = cv2.solvePnP(
            object_points,
            image_points,
            camera.astype(np.float64),
            distortion,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )
        if not success:
            return HeadPose(None, None, None, None, False, "solvepnp_failed")
        projected, _ = cv2.projectPoints(
            object_points, rotation_vector, translation, camera, distortion
        )
        residuals = projected.reshape(-1, 2) - image_points.reshape(-1, 2)
        error = float(np.sqrt(np.mean(np.sum(residuals**2, axis=1))))
        if not math.isfinite(error):
            return HeadPose(None, None, None, None, False, "non_finite_reprojection_error")
        if error > max_reprojection_error_px:
            return HeadPose(None, None, None, error, False, "high_reprojection_error")
        rotation, _ = cv2.Rodrigues(rotation_vector)
        yaw, pitch, roll = rotation_matrix_to_euler(rotation)
    except (cv2.error, ValueError, FloatingPointError) as exc:
        return HeadPose(None, None, None, None, False, f"solvepnp_error:{type(exc).__name__}")
    values = (yaw, pitch, roll)
    if not all(math.isfinite(value) for value in values):
        return HeadPose(None, None, None, error, False, "non_finite_pose")
    return HeadPose(yaw, pitch, roll, error, True)
