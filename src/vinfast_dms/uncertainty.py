"""Các cổng chất lượng đầu vào; thiếu bằng chứng luôn thành UNKNOWN."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from vinfast_dms.geometry import EyeMetrics, HeadPose
from vinfast_dms.landmarks import LandmarkResult


class QualityReason(StrEnum):
    NO_FACE = "no_face"
    MULTIPLE_FACES = "multiple_faces"
    INFERENCE_ERROR = "inference_error"
    INVALID_FRAME = "invalid_frame"
    INVALID_FRAME_SIZE = "invalid_frame_size"
    INVALID_LANDMARK_SHAPE = "invalid_landmark_shape"
    NON_FINITE_LANDMARKS = "non_finite_landmarks"
    LANDMARKS_OUT_OF_BOUNDS = "landmarks_out_of_bounds"
    FACE_TOO_SMALL = "face_too_small"
    MISSING_EYE_LANDMARKS = "missing_eye_landmarks"
    INVALID_EYE_LANDMARKS = "invalid_eye_landmarks"
    ZERO_EYE_WIDTH = "zero_eye_width"
    IMPLAUSIBLE_EAR = "implausible_ear"
    PNP_FAILED = "solvepnp_failed"
    POOR_GEOMETRY = "high_reprojection_error"
    INVALID_TIMESTAMP = "invalid_timestamp"
    NON_MONOTONIC_TIMESTAMP = "non_monotonic_timestamp"
    TIME_GAP = "time_gap"


@dataclass(frozen=True, slots=True)
class QualityAssessment:
    valid: bool
    reason: QualityReason | None
    landmarks: np.ndarray | None = None
    face_fraction: float | None = None


def assess_frame(frame: np.ndarray) -> QualityReason | None:
    if not isinstance(frame, np.ndarray):
        return QualityReason.INVALID_FRAME
    if frame.ndim != 3 or frame.shape[2] != 3 or frame.dtype != np.uint8:
        return QualityReason.INVALID_FRAME
    if frame.shape[0] < 1 or frame.shape[1] < 1:
        return QualityReason.INVALID_FRAME_SIZE
    return None


def assess_landmarks(
    result: LandmarkResult,
    width: int,
    height: int,
    min_face_fraction: float,
) -> QualityAssessment:
    if width < 1 or height < 1:
        return QualityAssessment(False, QualityReason.INVALID_FRAME_SIZE)
    if result.face_count == 0:
        if (result.reason or "").startswith("inference_error"):
            reason = QualityReason.INFERENCE_ERROR
        elif result.reason == "invalid_timestamp":
            reason = QualityReason.INVALID_TIMESTAMP
        elif result.reason == "invalid_frame":
            reason = QualityReason.INVALID_FRAME
        else:
            reason = QualityReason.NO_FACE
        return QualityAssessment(False, reason)
    if result.face_count > 1:
        return QualityAssessment(False, QualityReason.MULTIPLE_FACES)
    points = np.asarray(result.faces[0], dtype=np.float64)
    if points.ndim != 2 or points.shape[1] < 2 or len(points) < 478:
        return QualityAssessment(False, QualityReason.INVALID_LANDMARK_SHAPE)
    if not np.isfinite(points).all():
        return QualityAssessment(False, QualityReason.NON_FINITE_LANDMARKS)
    xy = points[:, :2]
    if np.any(xy < -0.1) or np.any(xy > 1.1):
        return QualityAssessment(False, QualityReason.LANDMARKS_OUT_OF_BOUNDS)
    span = np.ptp(xy, axis=0)
    face_fraction = float(span[0] * span[1])
    if face_fraction < min_face_fraction:
        return QualityAssessment(
            False, QualityReason.FACE_TOO_SMALL, points, face_fraction
        )
    return QualityAssessment(True, None, points, face_fraction)


def eye_quality_reason(metrics: EyeMetrics) -> QualityReason | None:
    if metrics.valid:
        return None
    reason = metrics.reason or ""
    if reason.startswith("missing_eye"):
        return QualityReason.MISSING_EYE_LANDMARKS
    if reason == "zero_eye_width":
        return QualityReason.ZERO_EYE_WIDTH
    if reason == "implausible_ear":
        return QualityReason.IMPLAUSIBLE_EAR
    return QualityReason.INVALID_EYE_LANDMARKS


def pose_quality_reason(pose: HeadPose) -> QualityReason | None:
    if pose.valid:
        return None
    if pose.reason == "high_reprojection_error":
        return QualityReason.POOR_GEOMETRY
    return QualityReason.PNP_FAILED
