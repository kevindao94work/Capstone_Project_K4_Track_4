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
from vinfast_dms.uncertainty import (
    QualityAssessment,
    assess_frame,
    assess_landmarks,
    eye_quality_reason,
    pose_quality_reason,
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
    face_detected: bool = False

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
        frame_reason = assess_frame(frame)
        if isinstance(frame, np.ndarray) and frame.ndim >= 2:
            height, width = frame.shape[:2]
        else:
            height, width = 0, 0
        if frame_reason is not None:
            assessment = QualityAssessment(False, frame_reason)
            face_detected = False
        else:
            detected = self.landmarker.detect_bgr(frame, sample.timestamp_ms)
            face_detected = detected.face_count > 0
            assessment = assess_landmarks(
                detected, width, height, self.config.vision.min_face_fraction
            )
        points: np.ndarray | None = None
        eyes: EyeMetrics | None = None
        pose: HeadPose | None = None
        reason: str | None = frame_reason.value if frame_reason is not None else None
        valid = False
        if not assessment.valid:
            reason = (
                assessment.reason.value
                if assessment.reason is not None
                else "invalid_measurement"
            )
        else:
            points = assessment.landmarks
            assert points is not None
            eyes = measure_eyes(points, width, height)
            pose = estimate_head_pose(
                points,
                width,
                height,
                max_reprojection_error_px=self.config.vision.max_reprojection_error_px,
            )
            eye_reason = eye_quality_reason(eyes)
            pose_reason = pose_quality_reason(pose)
            if eye_reason is not None:
                reason = eye_reason.value
            elif pose_reason is not None:
                reason = pose_reason.value
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
            face_detected=face_detected,
        )
