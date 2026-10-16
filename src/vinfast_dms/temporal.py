"""Bộ lọc EMA theo thời gian và máy trạng thái cảnh báo."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from vinfast_dms.config import ThresholdConfig


class DMSState(StrEnum):
    NORMAL = "NORMAL"
    EYES_CLOSED = "EYES_CLOSED"
    DISTRACTED = "DISTRACTED"
    UNKNOWN = "UNKNOWN"


STATE_LABELS_VI = {
    DMSState.NORMAL: "BÌNH THƯỜNG",
    DMSState.EYES_CLOSED: "NHẮM MẮT KÉO DÀI",
    DMSState.DISTRACTED: "MẤT TẬP TRUNG",
    DMSState.UNKNOWN: "KHÔNG XÁC ĐỊNH",
}


@dataclass(frozen=True, slots=True)
class FeatureSample:
    timestamp_s: float | None
    ear_left: float | None
    ear_right: float | None
    ear_mean: float | None
    yaw_deg: float | None = None
    pitch_deg: float | None = None
    valid: bool = True
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class StateSnapshot:
    timestamp_s: float | None
    state: DMSState
    warning: bool
    reason: str | None
    ear_ema: float | None
    yaw_ema_deg: float | None
    closed_duration_s: float
    distracted_duration_s: float
    candidate_state: DMSState | None = None


class TemporalStateMachine:
    """Không suy luận bình thường từ dữ liệu lỗi; dwell được tính bằng giây."""

    def __init__(self, config: ThresholdConfig) -> None:
        self.config = config
        self.reset()

    def reset(self) -> None:
        self._last_time: float | None = None
        self._ear_ema: float | None = None
        self._yaw_ema: float | None = None
        self._closed_start: float | None = None
        self._distracted_start: float | None = None

    def _unknown(self, timestamp_s: float | None, reason: str) -> StateSnapshot:
        self.reset()
        return StateSnapshot(timestamp_s, DMSState.UNKNOWN, False, reason, None, None, 0.0, 0.0)

    def update(self, sample: FeatureSample) -> StateSnapshot:
        t = sample.timestamp_s
        if t is None or not math.isfinite(t):
            return self._unknown(t, "invalid_timestamp")
        if not sample.valid:
            return self._unknown(t, sample.reason or "invalid_measurement")
        if sample.ear_mean is None or not math.isfinite(sample.ear_mean):
            return self._unknown(t, sample.reason or "invalid_ear")
        if sample.yaw_deg is not None and not math.isfinite(sample.yaw_deg):
            return self._unknown(t, "invalid_yaw")
        if self._last_time is not None:
            dt = t - self._last_time
            if dt <= 0.0:
                return self._unknown(t, "non_monotonic_timestamp")
            if dt > self.config.max_gap_s:
                self.reset()
                self._last_time = t
                self._ear_ema = sample.ear_mean
                self._yaw_ema = sample.yaw_deg
                return StateSnapshot(t, DMSState.UNKNOWN, False, "time_gap", None, None, 0.0, 0.0)
            alpha = 1.0 - math.exp(-dt / self.config.ema_tau_s)
            self._ear_ema = self._blend(self._ear_ema, sample.ear_mean, alpha)
            self._yaw_ema = self._blend_optional(self._yaw_ema, sample.yaw_deg, alpha)
        else:
            self._ear_ema = sample.ear_mean
            self._yaw_ema = sample.yaw_deg
        self._last_time = t

        assert self._ear_ema is not None
        if self._ear_ema <= self.config.ear_closed:
            if self._closed_start is None:
                self._closed_start = t
        elif self._ear_ema >= self.config.ear_open:
            self._closed_start = None

        if self._yaw_ema is None:
            self._distracted_start = None
        elif abs(self._yaw_ema) >= self.config.yaw_distracted_deg:
            if self._distracted_start is None:
                self._distracted_start = t
        elif abs(self._yaw_ema) <= (
            self.config.yaw_distracted_deg - self.config.yaw_return_hysteresis_deg
        ):
            self._distracted_start = None

        closed_duration = self._duration(t, self._closed_start)
        distracted_duration = self._duration(t, self._distracted_start)
        if closed_duration >= self.config.closed_hold_s:
            state = DMSState.EYES_CLOSED
            reason = "closed_dwell"
            candidate = state
        elif distracted_duration >= self.config.distracted_hold_s:
            state = DMSState.DISTRACTED
            reason = "distracted_dwell"
            candidate = state
        else:
            state = DMSState.NORMAL
            reason = None
            if self._closed_start is not None:
                candidate = DMSState.EYES_CLOSED
            elif self._distracted_start is not None:
                candidate = DMSState.DISTRACTED
            else:
                candidate = None
        return StateSnapshot(
            t,
            state,
            state in {DMSState.EYES_CLOSED, DMSState.DISTRACTED},
            reason,
            self._ear_ema,
            self._yaw_ema,
            closed_duration,
            distracted_duration,
            candidate,
        )

    @staticmethod
    def _duration(now: float, start: float | None) -> float:
        return 0.0 if start is None else max(0.0, now - start)

    @staticmethod
    def _blend(previous: float | None, value: float, alpha: float) -> float:
        return value if previous is None else previous + alpha * (value - previous)

    @classmethod
    def _blend_optional(
        cls, previous: float | None, value: float | None, alpha: float
    ) -> float | None:
        if value is None:
            return None
        return cls._blend(previous, value, alpha)
