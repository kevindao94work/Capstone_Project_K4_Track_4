import pytest

from vinfast_dms.config import ThresholdConfig
from vinfast_dms.temporal import DMSState, FeatureSample, TemporalStateMachine


def _sample(t: float | None, ear: float = 0.30, yaw: float | None = 0.0) -> FeatureSample:
    return FeatureSample(t, ear, ear, ear, yaw_deg=yaw)


def _close_run(fps: float, duration_s: float = 1.5) -> list:
    machine = TemporalStateMachine(ThresholdConfig())
    outputs = [machine.update(_sample(0.0))]
    step = 1.0 / fps
    count = int(duration_s * fps)
    for index in range(1, count + 1):
        outputs.append(machine.update(_sample(index * step, ear=0.10)))
    return outputs


@pytest.mark.parametrize("fps", [5, 15, 30, 60])
def test_sustained_eye_closure_uses_seconds_across_frame_rates(fps: int) -> None:
    outputs = _close_run(fps, 1.5)
    assert outputs[-1].state == DMSState.EYES_CLOSED
    assert outputs[-1].closed_duration_s >= 1.2


def test_irregular_frame_intervals_still_use_elapsed_seconds() -> None:
    machine = TemporalStateMachine(ThresholdConfig())
    times = [0.0, 0.04, 0.15, 0.31, 0.45, 0.67, 0.74, 0.96, 1.12, 1.31, 1.5]
    outputs = [machine.update(_sample(t, ear=0.10 if t > 0.0 else 0.30)) for t in times]
    assert outputs[-1].state == DMSState.EYES_CLOSED
    assert outputs[-1].closed_duration_s >= 1.2


def test_short_blink_does_not_trigger_warning() -> None:
    machine = TemporalStateMachine(ThresholdConfig())
    states = [machine.update(_sample(0.0)).state]
    for index in range(1, 31):
        t = index / 30
        ear = 0.10 if 0.05 <= t < 0.20 else 0.30
        states.append(machine.update(_sample(t, ear=ear)).state)
    assert DMSState.EYES_CLOSED not in states


def test_hysteresis_keeps_candidate_until_open_threshold_is_crossed() -> None:
    machine = TemporalStateMachine(ThresholdConfig())
    machine.update(_sample(0.0, ear=0.30))
    machine.update(_sample(0.1, ear=0.10))
    intermediate = machine.update(_sample(0.2, ear=0.22))
    assert intermediate.candidate_state == DMSState.EYES_CLOSED
    opened = machine.update(_sample(0.8, ear=0.30))
    assert opened.state == DMSState.NORMAL
    assert opened.candidate_state is None


def test_missing_face_forces_unknown_and_resets_dwell() -> None:
    machine = TemporalStateMachine(ThresholdConfig())
    machine.update(_sample(0.0, ear=0.10))
    machine.update(_sample(0.4, ear=0.10))
    lost = machine.update(
        FeatureSample(0.5, None, None, None, valid=False, reason="no_face")
    )
    assert lost.state == DMSState.UNKNOWN
    reopened = machine.update(_sample(0.6, ear=0.30))
    assert reopened.state == DMSState.NORMAL
    assert reopened.closed_duration_s == 0.0


def test_timestamp_gap_forces_unknown_and_resets_dwell() -> None:
    machine = TemporalStateMachine(ThresholdConfig(max_gap_s=0.5))
    machine.update(_sample(0.0, ear=0.10))
    result = machine.update(_sample(0.6, ear=0.10))
    assert result.state == DMSState.UNKNOWN
    assert result.reason == "time_gap"
    assert machine.update(_sample(0.7, ear=0.10)).closed_duration_s == 0.0


def test_non_monotonic_timestamp_returns_unknown() -> None:
    machine = TemporalStateMachine(ThresholdConfig())
    machine.update(_sample(1.0))
    result = machine.update(_sample(0.9))
    assert result.state == DMSState.UNKNOWN
    assert result.reason == "non_monotonic_timestamp"


def test_no_timestamp_returns_unknown() -> None:
    result = TemporalStateMachine(ThresholdConfig()).update(_sample(None))
    assert result.state == DMSState.UNKNOWN
    assert result.reason == "invalid_timestamp"


def test_long_yaw_has_distinct_distracted_state() -> None:
    machine = TemporalStateMachine(ThresholdConfig())
    machine.update(_sample(0.0, yaw=0.0))
    output = None
    for index in range(1, 31):
        output = machine.update(_sample(index / 20, yaw=40.0))
    assert output is not None
    assert output.state == DMSState.DISTRACTED
    assert output.warning


def test_first_valid_turned_pose_is_not_used_as_neutral_calibration() -> None:
    machine = TemporalStateMachine(ThresholdConfig())
    first = machine.update(_sample(0.0, yaw=40.0))
    assert first.state == DMSState.NORMAL
    assert first.candidate_state == DMSState.DISTRACTED
    assert first.yaw_ema_deg == pytest.approx(40.0)
    assert first.distracted_duration_s == 0.0
    output = first
    for index in range(1, 11):
        output = machine.update(_sample(index / 10, yaw=40.0))
    assert output.state == DMSState.DISTRACTED
    assert output.distracted_duration_s >= 1.0


def test_short_yaw_excursion_does_not_trigger() -> None:
    machine = TemporalStateMachine(ThresholdConfig())
    machine.update(_sample(0.0, yaw=0.0))
    states = [machine.update(_sample(index / 30, yaw=40)).state for index in range(1, 8)]
    assert DMSState.DISTRACTED not in states


def test_eye_closure_has_priority_when_both_conditions_are_sustained() -> None:
    machine = TemporalStateMachine(ThresholdConfig())
    machine.update(_sample(0.0, ear=0.30, yaw=0.0))
    output = None
    for index in range(1, 61):
        output = machine.update(_sample(index / 30, ear=0.10, yaw=40.0))
    assert output is not None
    assert output.state == DMSState.EYES_CLOSED


def test_invalid_feature_values_return_unknown() -> None:
    machine = TemporalStateMachine(ThresholdConfig())
    result = machine.update(_sample(float("nan"), ear=float("nan")))
    assert result.state == DMSState.UNKNOWN
