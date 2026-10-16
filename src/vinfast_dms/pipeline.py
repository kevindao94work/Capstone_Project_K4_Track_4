"""Ghép landmark, hình học và FSM thành một kết quả cho mỗi khung hình."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter_ns

import numpy as np

from vinfast_dms.config import Config
from vinfast_dms.geometry import EyeMetrics, HeadPose, estimate_head_pose, measure_eyes
from vinfast_dms.landmarks import Landmarker
from vinfast_dms.sources import FrameSample
from vinfast_dms.temporal import (
    DMSState,
    FeatureSample,
    StateSnapshot,
    TemporalStateMachine,
)


@dataclass(frozen=True, slots=True)
class PipelineResult:
    frame_index: int
    timestamp_s: float
    face_landmarks: np.ndarray | None
    eye_metrics: EyeMetrics | None
    head_pose: HeadPose | None
    quality_valid: bool
    quality_reason: str | None
    snapshot: StateSnapshot
    processing_ms: float

    @property
    def state(self) -> DMSState:
        return self.snapshot.state


class DMSPipeline:
    def __init__(self, landmarker: Landmarker, config: Config) -> None:
        self.landmarker = landmarker
        self.config = config
        self.temporal = TemporalStateMachine(config.thresholds)

    def reset(self) -> None:
        self.temporal.reset()

    def process(self, sample: FrameSample) -> PipelineResult:
        start_ns = perf_counter_ns()
        frame = sample.frame
        height, width = frame.shape[:2]
        detected = self.landmarker.detect_bgr(frame, sample.timestamp_ms)
        points: np.ndarray | None = None
        eyes: EyeMetrics | None = None
        pose: HeadPose | None = None
        reason = detected.reason
        valid = False
        if detected.face_count != 1:
            reason = reason or ("no_face" if detected.face_count == 0 else "multiple_faces")
        else:
            points = np.asarray(detected.faces[0], dtype=np.float64)
            if points.ndim != 2 or points.shape[1] < 2 or len(points) < 478:
                reason = "invalid_landmark_shape"
            elif not np.isfinite(points[:, :2]).all():
                reason = "non_finite_landmarks"
            elif np.any(points[:, :2] < -0.1) or np.any(points[:, :2] > 1.1):
                reason = "landmarks_out_of_bounds"
            else:
                span = np.ptp(points[:, :2], axis=0)
                face_fraction = float(span[0] * span[1])
                if face_fraction < self.config.vision.min_face_fraction:
                    reason = "face_too_small"
                else:
                    eyes = measure_eyes(points, width, height)
                    pose = estimate_head_pose(
                        points,
                        width,
                        height,
                        max_reprojection_error_px=self.config.vision.max_reprojection_error_px,
                    )
                    if not eyes.valid:
                        reason = eyes.reason
                    elif not pose.valid:
                        reason = pose.reason
                    else:
                        reason = None
                        valid = True
        sample_features = FeatureSample(
            timestamp_s=sample.timestamp_s,
            ear_left=eyes.ear_left if eyes and eyes.valid else None,
            ear_right=eyes.ear_right if eyes and eyes.valid else None,
            ear_mean=eyes.ear_mean if eyes and eyes.valid else None,
            yaw_deg=pose.yaw_deg if pose and pose.valid else None,
            pitch_deg=pose.pitch_deg if pose and pose.valid else None,
            valid=valid,
            reason=reason,
        )
        snapshot = self.temporal.update(sample_features)
        processing_ms = (perf_counter_ns() - start_ns) / 1_000_000.0
        return PipelineResult(
            frame_index=sample.index,
            timestamp_s=sample.timestamp_s,
            face_landmarks=points,
            eye_metrics=eyes,
            head_pose=pose,
            quality_valid=valid,
            quality_reason=reason,
            snapshot=snapshot,
            processing_ms=processing_ms,
        )
