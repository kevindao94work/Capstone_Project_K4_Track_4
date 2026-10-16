"""Đọc nhãn thủ công và tính metric có quy ước rõ ràng."""

from __future__ import annotations

import csv
import math
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean, median

from vinfast_dms.config import ThresholdConfig
from vinfast_dms.temporal import DMSState

LABELS = tuple(state.value for state in DMSState)
KNOWN_LABELS = (DMSState.NORMAL.value, DMSState.EYES_CLOSED.value, DMSState.DISTRACTED.value)
ALERT_LABELS = {DMSState.EYES_CLOSED.value, DMSState.DISTRACTED.value}
LABEL_FIELDS = ("start_s", "end_s", "label", "annotator", "notes")
PREDICTION_FIELDS = {"source_time_s", "state", "quality_valid", "processing_ms"}


class EvaluationError(ValueError):
    """Đầu vào đánh giá thiếu, sai schema hoặc không có vùng nhãn khớp."""


@dataclass(frozen=True, slots=True)
class EventSegment:
    start_s: float
    end_s: float
    label: str
    annotator: str
    notes: str = ""


def validate_segments(segments: Iterable[EventSegment]) -> list[EventSegment]:
    ordered = sorted(segments, key=lambda item: (item.start_s, item.end_s))
    previous_end = -math.inf
    for item in ordered:
        if not math.isfinite(item.start_s) or not math.isfinite(item.end_s):
            raise EvaluationError("Mốc thời gian nhãn phải là số hữu hạn.")
        if item.start_s < 0.0 or item.end_s <= item.start_s:
            raise EvaluationError("Nhãn cần 0 ≤ start_s < end_s.")
        if item.label not in LABELS:
            raise EvaluationError(f"Nhãn không hợp lệ: {item.label}.")
        if not item.annotator.strip():
            raise EvaluationError("Trường annotator không được để trống.")
        if item.start_s < previous_end:
            raise EvaluationError("Các khoảng nhãn không được chồng lấp.")
        previous_end = item.end_s
    return ordered


def read_event_labels(path: str | Path) -> list[EventSegment]:
    file_path = Path(path)
    if not file_path.is_file():
        raise EvaluationError(f"Không tìm thấy CSV nhãn: {file_path}")
    with file_path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if set(LABEL_FIELDS) - set(reader.fieldnames or ()):
            raise EvaluationError(f"CSV nhãn cần các cột: {', '.join(LABEL_FIELDS)}.")
        segments: list[EventSegment] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                segments.append(
                    EventSegment(
                        start_s=float(row["start_s"]),
                        end_s=float(row["end_s"]),
                        label=(row["label"] or "").strip().upper(),
                        annotator=(row["annotator"] or "").strip(),
                        notes=(row["notes"] or "").strip(),
                    )
                )
            except (TypeError, ValueError) as exc:
                raise EvaluationError(f"Dữ liệu nhãn lỗi ở dòng {row_number}.") from exc
    return validate_segments(segments)


def write_event_labels(path: str | Path, segments: Iterable[EventSegment]) -> None:
    ordered = validate_segments(segments)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=LABEL_FIELDS)
        writer.writeheader()
        for segment in ordered:
            writer.writerow(asdict(segment))


def read_predictions(path: str | Path) -> list[dict[str, str]]:
    file_path = Path(path)
    if not file_path.is_file():
        raise EvaluationError(f"Không tìm thấy CSV dự đoán: {file_path}")
    with file_path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if PREDICTION_FIELDS - set(reader.fieldnames or ()):
            raise EvaluationError(
                "CSV dự đoán cần source_time_s, state, quality_valid và processing_ms."
            )
        rows = list(reader)
    if not rows:
        raise EvaluationError("CSV dự đoán không có frame; NOT EVALUATED.")
    return rows


def _parse_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in {"true", "1", "yes"}


def _prediction_state(row: dict[str, str]) -> str:
    state = (row.get("state") or "").strip().upper()
    if state not in LABELS or not _parse_bool(row.get("quality_valid")):
        return DMSState.UNKNOWN.value
    return state


def _align(
    predictions: Iterable[dict[str, str]], segments: list[EventSegment]
) -> list[tuple[float, str, str, dict[str, str]]]:
    aligned: list[tuple[float, str, str, dict[str, str]]] = []
    for row_number, row in enumerate(predictions, start=2):
        try:
            timestamp = float(row["source_time_s"])
        except (TypeError, ValueError, KeyError) as exc:
            raise EvaluationError(f"Thiếu source_time_s ở dòng dự đoán {row_number}.") from exc
        if not math.isfinite(timestamp):
            raise EvaluationError(f"source_time_s không hữu hạn ở dòng {row_number}.")
        actual = next(
            (item.label for item in segments if item.start_s <= timestamp < item.end_s),
            None,
        )
        if actual is not None:
            aligned.append((timestamp, actual, _prediction_state(row), row))
    if not aligned:
        raise EvaluationError("Không có frame dự đoán nằm trong đoạn được gắn nhãn; NOT EVALUATED.")
    aligned.sort(key=lambda item: item[0])
    return aligned


def _percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = quantile * (len(ordered) - 1)
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def _wall_timestamp(row: dict[str, str]) -> float | None:
    raw = row.get("wall_time_utc", "")
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.timestamp()


def _measurement(row: dict[str, str], field: str) -> float | None:
    raw = row.get(field, "")
    if raw in {None, ""}:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise EvaluationError(f"Giá trị {field} không hợp lệ trong CSV dự đoán.") from exc
    if not math.isfinite(value) or value < 0.0:
        raise EvaluationError(f"Giá trị {field} phải hữu hạn và không âm.")
    return value


def evaluate_predictions(
    predictions: Iterable[dict[str, str]], segments: Iterable[EventSegment]
) -> dict[str, object]:
    labels = validate_segments(segments)
    if not labels:
        raise EvaluationError("Chưa có ground truth độc lập; NOT EVALUATED.")
    prediction_rows = list(predictions)
    aligned = _align(prediction_rows, labels)
    predicted_labels = (*KNOWN_LABELS, DMSState.UNKNOWN.value)
    matrix = {
        actual: {predicted: 0 for predicted in predicted_labels}
        for actual in KNOWN_LABELS
    }
    known_rows = [item for item in aligned if item[1] in KNOWN_LABELS]
    unknown_actual = sum(item[1] == DMSState.UNKNOWN.value for item in aligned)
    unknown_predicted = sum(item[2] == DMSState.UNKNOWN.value for item in aligned)
    for _timestamp, actual, predicted, _row in known_rows:
        matrix[actual][predicted] += 1

    class_metrics: dict[str, dict[str, float | int | None]] = {}
    for label in KNOWN_LABELS:
        tp = matrix[label][label]
        actual_positive = sum(matrix[label].values())
        predicted_positive = sum(matrix[actual][label] for actual in KNOWN_LABELS)
        fp = predicted_positive - tp
        fn = actual_positive - tp
        precision = tp / predicted_positive if predicted_positive else None
        recall = tp / actual_positive if actual_positive else None
        f1_denominator = 2 * tp + fp + fn
        f1 = 2 * tp / f1_denominator if f1_denominator else None
        class_metrics[label] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

    known_count = len(known_rows)
    known_correct = sum(matrix[label][label] for label in KNOWN_LABELS)
    coverage = (
        sum(predicted != DMSState.UNKNOWN.value for _, _, predicted, _ in known_rows) / known_count
        if known_count
        else None
    )
    covered_rows = [
        item for item in known_rows if item[2] != DMSState.UNKNOWN.value
    ]
    source_times = [item[0] for item in aligned]
    frame_intervals = [
        later - earlier
        for earlier, later in zip(source_times, source_times[1:], strict=False)
        if later > earlier
    ]
    if frame_intervals:
        observed_start = min(source_times)
        observed_end = max(source_times) + median(frame_intervals)
        normal_duration = sum(
            max(
                0.0,
                min(segment.end_s, observed_end) - max(segment.start_s, observed_start),
            )
            for segment in labels
            if segment.label == DMSState.NORMAL.value
        )
    else:
        normal_duration = 0.0
    false_alarm_events = 0
    for segment in labels:
        if segment.label != DMSState.NORMAL.value:
            continue
        previous_alert = False
        for timestamp, _actual, predicted, _row in aligned:
            if not segment.start_s <= timestamp < segment.end_s:
                continue
            alert = predicted in ALERT_LABELS
            if alert and not previous_alert:
                false_alarm_events += 1
            previous_alert = alert
    false_alarm_rate = (
        false_alarm_events / (normal_duration / 60.0) if normal_duration > 0.0 else None
    )

    event_delays: dict[str, list[float]] = {
        DMSState.EYES_CLOSED.value: [],
        DMSState.DISTRACTED.value: [],
    }
    event_totals = {key: 0 for key in event_delays}
    for segment in labels:
        if segment.label not in event_delays:
            continue
        event_totals[segment.label] += 1
        detections = [
            timestamp - segment.start_s
            for timestamp, _actual, predicted, _row in aligned
            if segment.start_s <= timestamp < segment.end_s and predicted == segment.label
        ]
        if detections:
            event_delays[segment.label].append(min(detections))
    delay_metrics: dict[str, dict[str, float | int | None]] = {}
    for label, delays in event_delays.items():
        delay_metrics[label] = {
            "events": event_totals[label],
            "detected": len(delays),
            "missed": event_totals[label] - len(delays),
            "mean_delay_s": mean(delays) if delays else None,
            "median_delay_s": median(delays) if delays else None,
        }

    latencies = [
        value
        for row in prediction_rows
        if (value := _measurement(row, "processing_ms")) is not None
    ]
    wall_times = [
        value
        for value in (_wall_timestamp(row) for row in prediction_rows)
        if value is not None
    ]
    all_source_times = sorted(
        {
            float(row["source_time_s"])
            for row in prediction_rows
            if row.get("source_time_s") not in {None, ""}
        }
    )
    fps_source = (
        (len(all_source_times) - 1) / (all_source_times[-1] - all_source_times[0])
        if len(all_source_times) > 1 and all_source_times[-1] > all_source_times[0]
        else None
    )
    fps_runtime = (
        (len(wall_times) - 1) / (max(wall_times) - min(wall_times))
        if len(wall_times) > 1 and max(wall_times) > min(wall_times)
        else None
    )
    return {
        "prediction_frames": len(prediction_rows),
        "labeled_frames": len(aligned),
        "known_ground_truth_frames": known_count,
        "known_frame_accuracy": known_correct / known_count if known_count else None,
        "accuracy_when_covered": (
            known_correct / len(covered_rows) if covered_rows else None
        ),
        "unknown_ground_truth_frames": unknown_actual,
        "unknown_prediction_frames": unknown_predicted,
        "abstention_frames_on_known_ground_truth": known_count - len(covered_rows),
        "abstention_rate_on_known_ground_truth": (
            1.0 - coverage if coverage is not None else None
        ),
        "abstention_rate_on_all_labeled_frames": (
            unknown_predicted / len(aligned) if aligned else None
        ),
        "coverage": coverage,
        "confusion_matrix": matrix,
        "per_class": class_metrics,
        "false_alarm_events_on_normal": false_alarm_events,
        "normal_labeled_minutes": normal_duration / 60.0,
        "false_alarms_per_normal_minute": false_alarm_rate,
        "source_event_delay": delay_metrics,
        "processing_latency_ms_p50": _percentile(latencies, 0.50),
        "processing_latency_ms_p95": _percentile(latencies, 0.95),
        "fps_source": fps_source,
        "fps_runtime": fps_runtime,
    }


def instant_baseline(
    predictions: Iterable[dict[str, str]], thresholds: ThresholdConfig
) -> list[dict[str, str]]:
    baseline: list[dict[str, str]] = []
    for row in predictions:
        result = dict(row)
        if not _parse_bool(row.get("quality_valid")):
            state = DMSState.UNKNOWN.value
        else:
            try:
                ear = float(row.get("ear_mean", ""))
            except (TypeError, ValueError):
                ear = math.nan
            try:
                yaw = float(row.get("yaw_deg", ""))
            except (TypeError, ValueError):
                yaw = math.nan
            if math.isfinite(ear) and ear <= thresholds.ear_closed:
                state = DMSState.EYES_CLOSED.value
            elif math.isfinite(yaw) and abs(yaw) >= thresholds.yaw_distracted_deg:
                state = DMSState.DISTRACTED.value
            elif math.isfinite(ear):
                state = DMSState.NORMAL.value
            else:
                state = DMSState.UNKNOWN.value
        result["state"] = state
        result["warning"] = str(state in ALERT_LABELS)
        baseline.append(result)
    return baseline

