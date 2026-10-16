import csv
from pathlib import Path

import pytest

from vinfast_dms.config import ThresholdConfig
from vinfast_dms.metrics import (
    EvaluationError,
    EventSegment,
    evaluate_predictions,
    instant_baseline,
    read_event_labels,
    validate_segments,
    write_event_labels,
)


def _segments() -> list[EventSegment]:
    return [
        EventSegment(0.0, 1.0, "NORMAL", "Đào Gia Bảo"),
        EventSegment(1.0, 2.0, "EYES_CLOSED", "Đào Gia Bảo"),
        EventSegment(2.0, 3.0, "DISTRACTED", "Đào Gia Bảo"),
        EventSegment(3.0, 4.0, "UNKNOWN", "Đào Gia Bảo"),
    ]


def _predictions() -> list[dict[str, str]]:
    values = [
        (0.1, "NORMAL", "True", "0.3", "0"),
        (0.9, "NORMAL", "True", "0.3", "0"),
        (1.1, "EYES_CLOSED", "True", "0.1", "0"),
        (1.9, "UNKNOWN", "False", "", ""),
        (2.1, "DISTRACTED", "True", "0.3", "40"),
        (2.9, "NORMAL", "True", "0.3", "0"),
        (3.1, "UNKNOWN", "False", "", ""),
    ]
    return [
        {
            "source_time_s": str(t),
            "state": state,
            "quality_valid": valid,
            "processing_ms": str(index + 1),
            "ear_mean": ear,
            "yaw_deg": yaw,
            "wall_time_utc": "",
        }
        for index, (t, state, valid, ear, yaw) in enumerate(values)
    ]


def test_confusion_matrix_and_class_metrics_match_exact_fixture() -> None:
    result = evaluate_predictions(_predictions(), _segments())
    assert result["confusion_matrix"] == {
        "NORMAL": {"NORMAL": 2, "EYES_CLOSED": 0, "DISTRACTED": 0, "UNKNOWN": 0},
        "EYES_CLOSED": {"NORMAL": 0, "EYES_CLOSED": 1, "DISTRACTED": 0, "UNKNOWN": 1},
        "DISTRACTED": {"NORMAL": 1, "EYES_CLOSED": 0, "DISTRACTED": 1, "UNKNOWN": 0},
    }
    assert result["known_frame_accuracy"] == pytest.approx(4 / 6)
    assert result["coverage"] == pytest.approx(5 / 6)
    assert result["accuracy_when_covered"] == pytest.approx(4 / 5)
    assert result["abstention_frames_on_known_ground_truth"] == 1
    assert result["abstention_rate_on_known_ground_truth"] == pytest.approx(1 / 6)
    assert result["abstention_rate_on_all_labeled_frames"] == pytest.approx(2 / 7)
    assert result["unknown_ground_truth_frames"] == 1
    assert result["unknown_prediction_frames"] == 2
    assert result["per_class"]["NORMAL"]["precision"] == pytest.approx(2 / 3)
    assert result["per_class"]["NORMAL"]["recall"] == 1.0
    assert result["per_class"]["NORMAL"]["f1"] == pytest.approx(0.8)
    assert result["per_class"]["EYES_CLOSED"]["precision"] == 1.0
    assert result["per_class"]["EYES_CLOSED"]["recall"] == 0.5
    assert result["per_class"]["DISTRACTED"]["f1"] == pytest.approx(2 / 3)
    assert result["source_event_delay"]["EYES_CLOSED"]["mean_delay_s"] == pytest.approx(0.1)
    assert result["processing_latency_ms_p50"] == 4.0
    assert result["processing_latency_ms_p95"] == pytest.approx(6.7)


def test_no_positive_events_and_no_normal_duration_return_na() -> None:
    segments = [EventSegment(0.0, 2.0, "UNKNOWN", "Đào Gia Bảo")]
    predictions = [
        {
            "source_time_s": "0.1",
            "state": "UNKNOWN",
            "quality_valid": "False",
            "processing_ms": "",
        },
        {
            "source_time_s": "1.1",
            "state": "UNKNOWN",
            "quality_valid": "False",
            "processing_ms": "",
        },
    ]
    result = evaluate_predictions(predictions, segments)
    assert result["coverage"] is None
    assert result["false_alarms_per_normal_minute"] is None
    assert result["per_class"]["EYES_CLOSED"]["precision"] is None
    assert result["per_class"]["EYES_CLOSED"]["f1"] is None
    assert result["accuracy_when_covered"] is None
    assert result["fps_runtime"] is None


def test_labels_reject_overlap_and_invalid_duration() -> None:
    with pytest.raises(EvaluationError, match="chồng lấp"):
        validate_segments(
            [
                EventSegment(0, 2, "NORMAL", "A"),
                EventSegment(1, 3, "UNKNOWN", "A"),
            ]
        )
    with pytest.raises(EvaluationError, match="start_s"):
        validate_segments([EventSegment(2, 2, "NORMAL", "A")])


def test_no_ground_truth_is_not_evaluated() -> None:
    with pytest.raises(EvaluationError, match="NOT EVALUATED"):
        evaluate_predictions(_predictions(), [])


def test_no_prediction_frames_matching_labels_is_not_evaluated() -> None:
    outside = [
        {
            "source_time_s": "10",
            "state": "NORMAL",
            "quality_valid": "True",
            "processing_ms": "2",
        }
    ]
    with pytest.raises(EvaluationError, match="(?i)không có frame"):
        evaluate_predictions(outside, _segments())


def test_manual_label_csv_round_trip_and_order(tmp_path: Path) -> None:
    path = tmp_path / "labels.csv"
    write_event_labels(path, list(reversed(_segments())))
    loaded = read_event_labels(path)
    assert [item.start_s for item in loaded] == [0.0, 1.0, 2.0, 3.0]
    with path.open(newline="", encoding="utf-8") as file:
        assert len(list(csv.DictReader(file))) == 4


def test_instant_baseline_uses_same_thresholds_and_unknown_guard() -> None:
    rows = _predictions()[:5]
    baseline = instant_baseline(rows, ThresholdConfig())
    assert [row["state"] for row in baseline] == [
        "NORMAL",
        "NORMAL",
        "EYES_CLOSED",
        "UNKNOWN",
        "DISTRACTED",
    ]


def test_false_alarm_events_reset_at_each_normal_segment() -> None:
    labels = [
        EventSegment(0.0, 2.0, "NORMAL", "Đào Gia Bảo"),
        EventSegment(2.0, 3.0, "DISTRACTED", "Đào Gia Bảo"),
        EventSegment(3.0, 5.0, "NORMAL", "Đào Gia Bảo"),
    ]
    predictions = [
        {
            "source_time_s": str(t),
            "state": state,
            "quality_valid": "True",
            "processing_ms": "1",
        }
        for t, state in [
            (0.5, "DISTRACTED"),
            (1.5, "NORMAL"),
            (2.5, "DISTRACTED"),
            (3.5, "DISTRACTED"),
            (4.5, "NORMAL"),
        ]
    ]
    result = evaluate_predictions(predictions, labels)
    assert result["false_alarm_events_on_normal"] == 2

