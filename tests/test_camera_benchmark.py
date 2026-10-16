from types import SimpleNamespace

import numpy as np
import pytest
import scripts.benchmark_camera as benchmark_camera
from scripts.benchmark_camera import (
    GUIDED_PHASES,
    INTERACTIVE_SCENARIOS,
    _ascii_cue,
    _draw_cue_banner,
    _measurement_summary,
    _new_scenario_stats,
    _percentile,
    _record_measurement,
    build_parser,
    run_interactive_scenario_check,
)

from vinfast_dms.sources import SourceError


def test_camera_benchmark_defaults_to_builtin_camera() -> None:
    args = build_parser().parse_args([])
    assert args.camera_index == 1
    assert args.duration_seconds == 30.0
    assert args.output is None


def test_camera_benchmark_allows_an_explicit_camera_override() -> None:
    args = build_parser().parse_args(["--camera-index", "0", "--duration-seconds", "5"])
    assert args.camera_index == 0
    assert args.duration_seconds == 5.0


@pytest.mark.parametrize(
    ("values", "percentile", "expected"),
    [([1.0, 2.0, 3.0, 4.0], 50, 2.5), ([1.0, 2.0, 3.0, 4.0], 95, 3.85)],
)
def test_camera_benchmark_percentiles(values, percentile, expected) -> None:
    assert _percentile(values, percentile) == pytest.approx(expected)


def test_camera_benchmark_empty_percentile_is_not_available() -> None:
    assert _percentile([], 95) is None


def test_live_runner_cue_is_renderable_with_opencv_ascii_font() -> None:
    assert _ascii_cue("PHA nhắm mắt · giữ 2 giây") == "PHA nham mat | giu 2 giay"


def test_live_runner_draws_cue_in_separate_bottom_banner() -> None:
    image = np.zeros((100, 200, 3), dtype=np.uint8)
    rendered = _draw_cue_banner(image.copy(), "READY: NORMAL | SPACE")
    assert np.all(rendered[:53] == 0)
    assert np.any(rendered[54:] > 0)
    assert np.all(rendered[54, :, :] == [14, 25, 38])


def test_interactive_scenarios_can_be_selected_for_reproduction() -> None:
    args = build_parser().parse_args(
        ["--interactive-scenarios", "--scenario", "normal", "--scenario", "turn_left"]
    )
    selected = [
        scenario[0]
        for scenario in INTERACTIVE_SCENARIOS
        if scenario[0] in args.scenario
    ]
    assert selected == ["normal", "turn_left"]


def test_interactive_camera_open_failure_returns_partial_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeLandmarker:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            pass

    class UnavailableCamera:
        capture_read_attempts = 0
        capture_failures = 0
        capture = None

        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def __enter__(self):
            raise SourceError("camera unavailable")

        def __exit__(self, *_args) -> None:
            pass

    monkeypatch.setattr(benchmark_camera, "MediaPipeLandmarker", FakeLandmarker)
    monkeypatch.setattr(benchmark_camera, "VideoSource", UnavailableCamera)
    monkeypatch.setattr(benchmark_camera.cv2, "destroyAllWindows", lambda: None)
    args = build_parser().parse_args(["--interactive-scenarios"])
    report = run_interactive_scenario_check(args)
    assert report["measurement_status"] == "PARTIAL"
    assert report["camera_capture"]["failure"] == "camera unavailable"
    assert report["scenarios"] == []


def test_guided_scenarios_cover_one_minute_and_required_cases() -> None:
    assert GUIDED_PHASES[0][0] == 0
    assert GUIDED_PHASES[-1][1] == 60
    assert {phase[2] for phase in GUIDED_PHASES} == {
        "normal",
        "blink",
        "eyes_closed",
        "turn_left",
        "turn_right",
        "out_of_view",
        "cover_eyes",
        "poor_light",
        "recovery",
    }


@pytest.mark.parametrize("scenario", INTERACTIVE_SCENARIOS)
def test_interactive_stage_boundaries_cover_scenario_without_gaps(scenario) -> None:
    stages = benchmark_camera.SCENARIO_STAGES[scenario[0]]
    assert stages[0][0] == 0.0
    assert stages[-1][1] == scenario[2]
    assert all(
        left[1] == right[0]
        for left, right in zip(stages, stages[1:], strict=False)
    )


def test_scenario_stats_record_stage_boundaries_and_quality_counts() -> None:
    stats = _new_scenario_stats()
    result = SimpleNamespace(
        face_detected=True,
        face_landmarks=object(),
        quality_valid=True,
        snapshot=SimpleNamespace(warning=False),
        state=SimpleNamespace(value="NORMAL"),
        quality_reason=None,
        processing_ms=4.0,
        head_pose=None,
    )
    sample = SimpleNamespace(index=10, timestamp_s=1.25)
    _record_measurement(stats, sample, result, "steady_state", 0.5)
    summary = _measurement_summary(stats)
    phase_summary = stats["subphases"]["steady_state"]
    assert summary["frames"] == 1
    assert summary["face_detected_frames"] == 1
    assert phase_summary["first_frame_index"] == 10
    assert phase_summary["last_frame_index"] == 10
    assert phase_summary["observed_phase_offsets_s"] == [0.5]
